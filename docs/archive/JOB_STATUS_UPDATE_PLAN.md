# Job Status Update Endpoint Implementation Plan

> **Task**: Implement PUT /api/v1/jobs/{id}/status endpoint
> **Priority**: 🔴 HIGH (Critical user-facing gap)
> **Estimated Effort**: 3-4 hours
> **Status**: Not Started

---

## Problem Statement

### Current Situation

Multiple skipped tests indicate a planned but unimplemented feature:
- Dedicated status update endpoint missing
- Users cannot manually override job status
- Auto-created jobs stuck in "running" if printer goes offline
- No way to mark failed jobs as completed manually
- No validation for status transitions

**Location**: `tests/backend/test_api_jobs.py`
- Lines: 305, 331, 366, 394, 621, 687 (6 skipped tests)

### User Impact

- **No Manual Status Control**: Cannot manually mark jobs as completed/failed
- **Stuck Jobs**: Jobs remain "running" forever if printer crashes
- **Data Accuracy**: No way to correct auto-detected status errors
- **Workflow Blocker**: Cannot close out jobs that finished abnormally

---

## Relationship to Job Update API

This endpoint is a **specialized subset** of the general job update endpoint:

| Feature | PUT /api/v1/jobs/{id} | PUT /api/v1/jobs/{id}/status |
|---------|----------------------|------------------------------|
| Purpose | Update any editable field | Update status only |
| Fields | All editable fields | Status + timestamps |
| Validation | Field-level validation | Status transition logic |
| Use Case | Edit job details | Mark job complete/failed |
| Complexity | General purpose | Specialized workflow |

**Design Decision**: Implement both endpoints
- **General update** (PUT /jobs/{id}): For editing job metadata
- **Status update** (PUT /jobs/{id}/status): For workflow state management

This follows REST best practices for specialized actions on resources.

---

## Requirements

### Functional Requirements

1. **Endpoint**: `PUT /api/v1/jobs/{id}/status`
2. **Request Body**: New status + optional completion data
3. **Status Validation**: Enforce valid status transitions
4. **Timestamp Management**: Auto-update completion timestamps
5. **Error Handling**: Clear error messages for invalid transitions
6. **Idempotency**: Safe to call multiple times with same status

### Status State Machine

```
┌─────────┐
│ PENDING │ ──────┐
└─────────┘       │
     │            │
     │ start      │ manual
     ▼            │
┌─────────┐       │
│ RUNNING │       │
└─────────┘       │
     │            │
     ├────────────┤
     │            │
     │ complete   │ manual
     ▼            ▼
┌───────────┐  ┌────────┐
│ COMPLETED │  │ FAILED │
└───────────┘  └────────┘
```

**Valid Transitions**:
- `pending → running`: Job started (auto or manual)
- `pending → completed`: Manually mark as done (skip running)
- `pending → failed`: Manually mark as failed
- `running → completed`: Job finished successfully
- `running → failed`: Job failed or cancelled
- `completed → failed`: Correct status after completion (rare)
- `failed → completed`: Retry succeeded (rare)
- `completed → completed`: Idempotent (no-op)
- `failed → failed`: Idempotent (no-op)

**Invalid Transitions**:
- `completed → running`: Cannot restart completed job
- `failed → running`: Cannot restart failed job
- `completed → pending`: Cannot un-complete a job
- `failed → pending`: Cannot reset to pending
- `running → pending`: Cannot go backwards to pending

### Request Schema

```json
{
  "status": "completed",
  "completion_notes": "Manually marked as complete",
  "force": false
}
```

**Fields**:
- `status` (required): New status value
- `completion_notes` (optional): Reason for manual status change
- `force` (optional): Skip validation checks (admin only)

---

## Technical Design

### 1. Pydantic Schema

**File**: `src/models/job.py`

```python
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class JobStatusUpdateRequest(BaseModel):
    """Request schema for job status updates"""
    status: JobStatus
    completion_notes: Optional[str] = None
    force: bool = False

    @validator('completion_notes')
    def validate_notes(cls, v):
        if v and len(v) > 500:
            raise ValueError("completion_notes max length is 500 characters")
        return v

    class Config:
        use_enum_values = True

class JobStatusUpdateResponse(BaseModel):
    """Response schema for status updates"""
    id: str
    status: JobStatus
    previous_status: JobStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True
```

### 2. Service Layer

**File**: `src/services/job_service.py`

```python
async def update_job_status(
    self,
    job_id: str,
    new_status: str,
    completion_notes: Optional[str] = None,
    force: bool = False
) -> Job:
    """
    Update job status with transition validation.

    Args:
        job_id: Job UUID
        new_status: Target status (pending/running/completed/failed)
        completion_notes: Optional notes explaining manual status change
        force: Skip validation (admin override)

    Returns:
        Updated Job object

    Raises:
        HTTPException: If job not found or invalid transition
        ValueError: If status transition is not allowed
    """
    # Get existing job
    job = await self.job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    old_status = job.status

    # Check if status actually changed
    if old_status == new_status:
        logger.info(f"Job {job_id} already in status {new_status} (no-op)")
        return job

    # Validate transition (unless forced)
    if not force:
        self._validate_status_transition(old_status, new_status)

    # Build update dict
    updates = {
        'status': new_status
    }

    # Update timestamps based on status
    now = datetime.utcnow()

    if new_status == 'running' and not job.started_at:
        updates['started_at'] = now.isoformat()

    if new_status in ('completed', 'failed'):
        if not job.started_at:
            # Job went straight to completion without starting
            updates['started_at'] = now.isoformat()
        updates['completed_at'] = now.isoformat()

    # Add completion notes if provided
    if completion_notes:
        # Append to existing notes or create new
        existing_notes = job.notes or ""
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        status_note = f"[{timestamp}] Status changed: {old_status} → {new_status}: {completion_notes}"

        if existing_notes:
            updates['notes'] = f"{existing_notes}\n{status_note}"
        else:
            updates['notes'] = status_note

    # Perform update
    updated_job = await self.job_repo.update(job_id, updates)

    # Emit WebSocket event
    await self.event_service.emit('job_status_changed', {
        'job_id': job_id,
        'old_status': old_status,
        'new_status': new_status,
        'job': updated_job.dict()
    })

    logger.info(
        f"Job {job_id} status updated: {old_status} → {new_status}" +
        (f" (forced)" if force else "")
    )

    return updated_job

def _validate_status_transition(self, old_status: str, new_status: str) -> None:
    """
    Validate status transition is allowed.

    Raises:
        ValueError: If transition is not allowed
    """
    # Define valid transitions
    valid_transitions = {
        'pending': {'running', 'completed', 'failed'},
        'running': {'completed', 'failed'},
        'completed': {'failed'},  # Rare: correct completion to failure
        'failed': {'completed'},  # Rare: retry succeeded
    }

    allowed = valid_transitions.get(old_status, set())

    if new_status not in allowed:
        raise ValueError(
            f"Invalid status transition: {old_status} → {new_status}. "
            f"Allowed transitions from {old_status}: {', '.join(sorted(allowed)) or 'none'}"
        )
```

### 3. API Router

**File**: `src/api/routers/jobs.py`

```python
@router.put("/{job_id}/status", response_model=JobStatusUpdateResponse)
async def update_job_status(
    job_id: str,
    request: JobStatusUpdateRequest,
    job_service: JobService = Depends(get_job_service)
) -> JobStatusUpdateResponse:
    """
    Update job status with transition validation.

    This endpoint manages job workflow state transitions and automatically
    updates relevant timestamps (started_at, completed_at).

    **Valid Status Transitions**:
    - `pending → running`: Job started
    - `pending → completed`: Manually mark as done (skip running)
    - `pending → failed`: Manually mark as failed
    - `running → completed`: Job finished successfully
    - `running → failed`: Job failed or cancelled
    - `completed → failed`: Correct status (rare)
    - `failed → completed`: Retry succeeded (rare)

    **Invalid Transitions**:
    - Cannot restart completed/failed jobs (→ running)
    - Cannot reset to pending from any state

    **Timestamp Behavior**:
    - Setting status to `running` sets `started_at` if not already set
    - Setting status to `completed` or `failed` sets `completed_at`
    - Timestamps are immutable once set (unless using force=true)

    **Completion Notes**:
    - Optional notes explaining manual status change
    - Appended to job notes with timestamp
    - Useful for audit trail

    **Force Flag**:
    - Bypasses transition validation
    - Use with caution (admin only)
    - Allows any status change

    **Returns**: Updated job with new status and timestamps

    **Raises**:
    - 404: Job not found
    - 400: Invalid status transition
    - 422: Invalid request body
    """
    try:
        # Store previous status for response
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        previous_status = job.status

        # Update status
        updated_job = await job_service.update_job_status(
            job_id=job_id,
            new_status=request.status,
            completion_notes=request.completion_notes,
            force=request.force
        )

        # Build response
        return JobStatusUpdateResponse(
            id=updated_job.id,
            status=updated_job.status,
            previous_status=previous_status,
            started_at=updated_job.started_at,
            completed_at=updated_job.completed_at,
            updated_at=updated_job.updated_at or datetime.utcnow()
        )

    except ValueError as e:
        # Invalid transition
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job status {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Implementation Steps

### Step 1: Create Pydantic Schemas
1. Add `JobStatusUpdateRequest` to `src/models/job.py`
2. Add `JobStatusUpdateResponse` to `src/models/job.py`
3. Add validators and config
4. Export from `__init__.py`

### Step 2: Update Service Layer
1. Add `update_job_status()` method to `JobService`
2. Add `_validate_status_transition()` helper method
3. Add timestamp management logic
4. Add completion notes handling
5. Emit WebSocket events

### Step 3: Add API Endpoint
1. Add `PUT /{job_id}/status` route to jobs router
2. Add comprehensive docstring
3. Add error handling
4. Test with Swagger UI

### Step 4: Enable Skipped Tests
1. Review all 6 skipped tests in `test_api_jobs.py`
2. Remove `@pytest.mark.skip` decorators
3. Update test expectations to match implementation
4. Add new test cases for edge cases

### Step 5: Add Additional Tests
1. Test all valid transitions
2. Test all invalid transitions
3. Test timestamp updates
4. Test completion notes
5. Test force flag
6. Test idempotency (same status twice)

---

## Testing Strategy

### Unit Tests

**File**: `tests/services/test_job_service.py`

```python
@pytest.mark.asyncio
async def test_update_status_pending_to_running(job_service, pending_job):
    """Test valid transition: pending → running"""
    updated = await job_service.update_job_status(
        pending_job.id,
        'running'
    )

    assert updated.status == 'running'
    assert updated.started_at is not None

@pytest.mark.asyncio
async def test_update_status_running_to_completed(job_service, running_job):
    """Test valid transition: running → completed"""
    updated = await job_service.update_job_status(
        running_job.id,
        'completed',
        completion_notes="Test completion"
    )

    assert updated.status == 'completed'
    assert updated.completed_at is not None
    assert "Test completion" in updated.notes

@pytest.mark.asyncio
async def test_invalid_transition_completed_to_running(job_service, completed_job):
    """Test invalid transition: completed → running"""
    with pytest.raises(ValueError, match="Invalid status transition"):
        await job_service.update_job_status(
            completed_job.id,
            'running'
        )

@pytest.mark.asyncio
async def test_force_flag_bypasses_validation(job_service, completed_job):
    """Test force flag allows any transition"""
    updated = await job_service.update_job_status(
        completed_job.id,
        'pending',
        force=True
    )

    assert updated.status == 'pending'

@pytest.mark.asyncio
async def test_idempotent_status_update(job_service, running_job):
    """Test updating to same status is no-op"""
    original_updated_at = running_job.updated_at

    updated = await job_service.update_job_status(
        running_job.id,
        'running'
    )

    assert updated.status == 'running'
    # Should not trigger unnecessary updates
```

### API Integration Tests

**File**: `tests/backend/test_api_jobs.py`

Enable and update these skipped tests:

```python
# Line 305 - CURRENTLY SKIPPED
@pytest.mark.asyncio
async def test_update_job_status_endpoint(client, running_job):
    """Test PUT /api/v1/jobs/{id}/status endpoint"""
    response = await client.put(
        f"/api/v1/jobs/{running_job.id}/status",
        json={"status": "completed"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["previous_status"] == "running"
    assert data["completed_at"] is not None

# Line 331 - CURRENTLY SKIPPED
@pytest.mark.asyncio
async def test_update_status_invalid_transition(client, completed_job):
    """Test invalid status transition returns 400"""
    response = await client.put(
        f"/api/v1/jobs/{completed_job.id}/status",
        json={"status": "running"}
    )

    assert response.status_code == 400
    assert "Invalid status transition" in response.json()["detail"]

# Line 366 - CURRENTLY SKIPPED
@pytest.mark.asyncio
async def test_update_status_with_notes(client, running_job):
    """Test status update with completion notes"""
    response = await client.put(
        f"/api/v1/jobs/{running_job.id}/status",
        json={
            "status": "failed",
            "completion_notes": "Printer error"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"

# Add 3 more tests for lines 394, 621, 687...
```

### E2E Tests

**File**: `tests/e2e/test_jobs.py`

```python
@pytest.mark.asyncio
async def test_manual_job_completion(page):
    """Test manually marking job as completed"""
    await page.goto("http://localhost:8000")
    await page.click("nav a[href='#jobs']")

    # Find running job
    await page.click("tr:has-text('Running') button[data-action='complete-job']")

    # Confirm dialog
    await page.click("button#confirmComplete")

    # Wait for success
    await page.wait_for_selector(".toast.success")

    # Verify status updated
    status = await page.text_content("tr:first-child .job-status")
    assert "Completed" in status
```

---

## Frontend Integration (Optional)

Add quick-action buttons to job list:

**File**: `frontend/js/jobs.js`

```javascript
async function markJobComplete(jobId) {
    if (!confirm('Mark this job as completed?')) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/jobs/${jobId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                status: 'completed',
                completion_notes: 'Manually completed by user'
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        showToast('✓ Job marked as completed', 'success');
        await loadJobs();
    } catch (error) {
        showToast(`✗ Error: ${error.message}`, 'error');
    }
}

async function markJobFailed(jobId) {
    const reason = prompt('Why did this job fail?');
    if (!reason) return;

    try {
        const response = await fetch(`/api/v1/jobs/${jobId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                status: 'failed',
                completion_notes: reason
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        showToast('✓ Job marked as failed', 'success');
        await loadJobs();
    } catch (error) {
        showToast(`✗ Error: ${error.message}`, 'error');
    }
}
```

---

## Success Criteria

- [ ] `PUT /api/v1/jobs/{id}/status` endpoint exists
- [ ] All valid status transitions work
- [ ] Invalid transitions return 400 with clear error
- [ ] Timestamps update correctly
- [ ] Completion notes append to job notes
- [ ] Force flag bypasses validation
- [ ] All 6 skipped tests enabled and passing
- [ ] Additional test coverage for edge cases
- [ ] WebSocket events fire on status change
- [ ] API documentation updated

---

## Rollout Plan

### Phase 1: Backend (2 hours)
1. ✅ Create Pydantic schemas
2. ✅ Add service method with validation
3. ✅ Add API endpoint
4. ✅ Test with Swagger UI

### Phase 2: Testing (1-2 hours)
1. ✅ Enable skipped tests
2. ✅ Add new test cases
3. ✅ Verify all tests pass

### Phase 3: Frontend (Optional, 1 hour)
1. ✅ Add quick-action buttons
2. ✅ Test manual completion workflow

---

## Dependencies

- Can be implemented in parallel with Job Update API
- Both share the same `update()` repository method
- No conflicts between the two endpoints

---

## Follow-up Work

After implementation:
1. Add bulk status update endpoint (multiple jobs)
2. Add status change history/audit log
3. Add automated status transitions based on printer events
4. Add notifications for status changes

---

**Status**: Ready for implementation
**Assignee**: TBD
**Target Version**: v2.9.0
