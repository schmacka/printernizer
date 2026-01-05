# Job Update API Implementation Plan

> **Task**: Implement PUT /api/v1/jobs/{id} endpoint
> **Priority**: 🔴 HIGH (Critical user-facing gap)
> **Estimated Effort**: 4-6 hours
> **Status**: Not Started

---

## Problem Statement

### Current Situation

The frontend has a fully functional job edit form that operates in "Demo Mode":
- Users can click "Edit" on any job
- Modal opens with all job fields populated
- Users can modify fields (name, status, business flag, customer info)
- Form submits and shows success toast
- **BUT**: Changes are never persisted to the backend

**Location**: `frontend/js/jobs.js:1088`
```javascript
// TODO: Implement actual API call when backend supports job updates
console.log('Demo-Modus: Job-Update würde hier gesendet werden:', updateData);
showToast('✓ Job aktualisiert (Demo-Modus)', 'success');
```

### User Impact

- **Confusing UX**: Users believe their changes are saved
- **Data Loss**: Edits are lost on page refresh
- **Trust Issue**: Creates false impression of working feature
- **Workaround**: Users must delete and recreate jobs to make changes

---

## Requirements

### Functional Requirements

1. **Endpoint**: `PUT /api/v1/jobs/{id}`
2. **Authentication**: Match existing API auth patterns
3. **Request Body**: Support updating all editable fields
4. **Validation**: Validate all input data
5. **Response**: Return updated job object
6. **Error Handling**: Proper HTTP status codes and error messages

### Editable Fields

Based on frontend form analysis (`frontend/js/jobs.js`):

| Field | Type | Validation | Notes |
|-------|------|------------|-------|
| `job_name` | string | Required, max 200 chars | Display name |
| `status` | enum | One of: pending/running/completed/failed | Job state |
| `is_business` | boolean | Required | Business vs personal |
| `customer_name` | string | Required if is_business=true | Business customer |
| `notes` | string | Optional, max 1000 chars | Additional metadata |
| `file_name` | string | Optional | Associated 3D file |
| `printer_id` | string | Optional, must exist | Associated printer |

### Non-Editable Fields

These should NOT be modifiable via this endpoint:
- `id` - Primary key
- `created_at` - Creation timestamp
- `started_at` - Auto-set by monitoring service
- `completed_at` - Auto-set by monitoring service
- `auto_created` - Set at creation time
- `discovery_time` - Set at creation time

### Validation Rules

1. **Job Name**:
   - Required, non-empty
   - Max length: 200 characters
   - Trim whitespace

2. **Status**:
   - Must be one of: `pending`, `running`, `completed`, `failed`
   - Status transitions should be logical (discussed in separate status update endpoint)

3. **Business Fields**:
   - If `is_business=true`, `customer_name` is required
   - If `is_business=false`, `customer_name` can be null/empty

4. **Printer ID**:
   - If provided, must reference existing printer
   - Can be null (manual job without printer)

5. **File Name**:
   - Optional string
   - No FK constraint (jobs may reference deleted files)

---

## Technical Design

### 1. Database Layer (JobRepository)

**File**: `src/database/repositories/job_repository.py`

**Method**: `async def update(self, job_id: str, updates: dict) -> Optional[Job]`

```python
async def update(self, job_id: str, updates: dict) -> Optional[Job]:
    """
    Update job fields.

    Args:
        job_id: Job UUID
        updates: Dictionary of fields to update

    Returns:
        Updated Job object or None if not found

    Raises:
        ValueError: If updates contain invalid fields
    """
    # Validate allowed fields
    allowed_fields = {
        'job_name', 'status', 'is_business', 'customer_name',
        'notes', 'file_name', 'printer_id'
    }
    invalid_fields = set(updates.keys()) - allowed_fields
    if invalid_fields:
        raise ValueError(f"Cannot update fields: {invalid_fields}")

    # Build UPDATE query
    if not updates:
        return await self.get_by_id(job_id)

    set_clauses = [f"{field} = ?" for field in updates.keys()]
    set_clauses.append("updated_at = ?")

    query = f"""
        UPDATE jobs
        SET {', '.join(set_clauses)}
        WHERE id = ?
    """

    values = list(updates.values())
    values.append(datetime.utcnow().isoformat())
    values.append(job_id)

    async with self.db.pooled_connection() as conn:
        await conn.execute(query, values)
        await conn.commit()

    return await self.get_by_id(job_id)
```

### 2. Service Layer (JobService)

**File**: `src/services/job_service.py`

**Method**: `async def update_job(self, job_id: str, updates: JobUpdateRequest) -> Job`

```python
async def update_job(self, job_id: str, updates: JobUpdateRequest) -> Job:
    """
    Update job with validation.

    Args:
        job_id: Job UUID
        updates: JobUpdateRequest schema with validated data

    Returns:
        Updated Job object

    Raises:
        ValueError: If validation fails
        HTTPException: If job not found or printer doesn't exist
    """
    # Get existing job
    existing_job = await self.job_repo.get_by_id(job_id)
    if not existing_job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Validate business logic
    update_dict = updates.dict(exclude_unset=True)

    # Business validation: if is_business=true, customer_name required
    is_business = update_dict.get('is_business', existing_job.is_business)
    customer_name = update_dict.get('customer_name', existing_job.customer_name)

    if is_business and not customer_name:
        raise ValueError("customer_name is required for business jobs")

    # Validate printer exists if provided
    if 'printer_id' in update_dict and update_dict['printer_id']:
        printer = await self.printer_service.get_printer(update_dict['printer_id'])
        if not printer:
            raise HTTPException(
                status_code=400,
                detail=f"Printer {update_dict['printer_id']} not found"
            )

    # Update job
    updated_job = await self.job_repo.update(job_id, update_dict)

    # Emit WebSocket event
    await self.event_service.emit('job_updated', {
        'job_id': job_id,
        'job': updated_job.dict()
    })

    logger.info(f"Job {job_id} updated: {list(update_dict.keys())}")

    return updated_job
```

### 3. API Schema (Pydantic Models)

**File**: `src/models/job.py`

```python
from pydantic import BaseModel, validator
from typing import Optional
from enum import Enum

class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class JobUpdateRequest(BaseModel):
    """Schema for job update requests"""
    job_name: Optional[str] = None
    status: Optional[JobStatus] = None
    is_business: Optional[bool] = None
    customer_name: Optional[str] = None
    notes: Optional[str] = None
    file_name: Optional[str] = None
    printer_id: Optional[str] = None

    @validator('job_name')
    def validate_job_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("job_name cannot be empty")
            if len(v) > 200:
                raise ValueError("job_name max length is 200 characters")
        return v

    @validator('customer_name')
    def validate_customer_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 200:
                raise ValueError("customer_name max length is 200 characters")
        return v

    @validator('notes')
    def validate_notes(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError("notes max length is 1000 characters")
        return v

    class Config:
        use_enum_values = True
```

### 4. API Router

**File**: `src/api/routers/jobs.py`

```python
@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    updates: JobUpdateRequest,
    job_service: JobService = Depends(get_job_service)
) -> JobResponse:
    """
    Update job fields.

    **Editable Fields**:
    - `job_name`: Display name (required, max 200 chars)
    - `status`: Job status (pending/running/completed/failed)
    - `is_business`: Business vs personal job
    - `customer_name`: Customer name (required if is_business=true)
    - `notes`: Additional notes (max 1000 chars)
    - `file_name`: Associated file name
    - `printer_id`: Associated printer UUID

    **Non-Editable Fields**:
    - Timestamps (created_at, started_at, completed_at) are managed automatically
    - `id` and `auto_created` are immutable

    **Business Logic**:
    - If `is_business=true`, `customer_name` is required
    - `printer_id` must reference an existing printer

    **Returns**: Updated job object

    **Raises**:
    - 404: Job not found
    - 400: Validation error or invalid printer_id
    - 422: Invalid request body
    """
    try:
        updated_job = await job_service.update_job(job_id, updates)
        return JobResponse.from_orm(updated_job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 5. Frontend Integration

**File**: `frontend/js/jobs.js:1088`

**Replace demo code with actual API call**:

```javascript
async function submitJobEdit(jobId) {
    const form = document.getElementById('editJobForm');
    const formData = new FormData(form);

    const updateData = {
        job_name: formData.get('jobName'),
        status: formData.get('status'),
        is_business: formData.get('isBusinessJob') === 'on',
        customer_name: formData.get('customerName') || null,
        notes: formData.get('notes') || null,
        printer_id: formData.get('printerId') || null,
        file_name: formData.get('fileName') || null
    };

    try {
        const response = await fetch(`/api/v1/jobs/${jobId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update job');
        }

        const updatedJob = await response.json();

        showToast('✓ Job successfully updated', 'success');
        closeJobEditModal();

        // Refresh job list to show changes
        await loadJobs();

        logger.info('Job updated successfully', { jobId, updatedJob });
    } catch (error) {
        logger.error('Error updating job:', error);
        showToast(`✗ Error updating job: ${error.message}`, 'error');
    }
}
```

---

## Implementation Steps

### Step 1: Database Migration (if needed)

Check if `jobs` table has `updated_at` column:

```sql
-- Migration: 014_add_jobs_updated_at.sql (if column doesn't exist)
ALTER TABLE jobs ADD COLUMN updated_at TEXT;
UPDATE jobs SET updated_at = created_at WHERE updated_at IS NULL;
```

### Step 2: Update Repository

1. Add `update()` method to `JobRepository`
2. Add unit tests for update method
3. Test edge cases (non-existent job, invalid fields)

### Step 3: Update Service

1. Add `update_job()` method to `JobService`
2. Add business logic validation
3. Add printer existence check
4. Emit WebSocket event for real-time updates
5. Add unit tests

### Step 4: Create Pydantic Schema

1. Create `JobUpdateRequest` schema
2. Add field validators
3. Add to `__init__.py` exports

### Step 5: Add API Endpoint

1. Add `PUT /{job_id}` route to jobs router
2. Add comprehensive docstring
3. Add error handling
4. Test with Swagger UI

### Step 6: Update Frontend

1. Remove "Demo Mode" code
2. Implement actual API call
3. Add error handling
4. Test form submission
5. Verify WebSocket updates work

### Step 7: Testing

1. Write unit tests for repository
2. Write unit tests for service
3. Write API integration tests
4. Write E2E tests for UI workflow
5. Test error scenarios

---

## Testing Strategy

### Unit Tests

**File**: `tests/services/test_job_service.py`

```python
@pytest.mark.asyncio
async def test_update_job_success(job_service, sample_job):
    """Test successful job update"""
    updates = JobUpdateRequest(
        job_name="Updated Job Name",
        status="completed"
    )

    updated = await job_service.update_job(sample_job.id, updates)

    assert updated.job_name == "Updated Job Name"
    assert updated.status == "completed"
    assert updated.id == sample_job.id

@pytest.mark.asyncio
async def test_update_job_not_found(job_service):
    """Test updating non-existent job"""
    updates = JobUpdateRequest(job_name="Test")

    with pytest.raises(HTTPException) as exc:
        await job_service.update_job("nonexistent-id", updates)

    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_update_business_job_requires_customer(job_service, sample_job):
    """Test business job validation"""
    updates = JobUpdateRequest(
        is_business=True,
        customer_name=""  # Invalid
    )

    with pytest.raises(ValueError, match="customer_name is required"):
        await job_service.update_job(sample_job.id, updates)

@pytest.mark.asyncio
async def test_update_invalid_printer(job_service, sample_job):
    """Test printer validation"""
    updates = JobUpdateRequest(printer_id="nonexistent-printer")

    with pytest.raises(HTTPException) as exc:
        await job_service.update_job(sample_job.id, updates)

    assert exc.value.status_code == 400
    assert "Printer" in exc.value.detail
```

### API Integration Tests

**File**: `tests/backend/test_api_jobs.py`

```python
@pytest.mark.asyncio
async def test_update_job_endpoint(client, sample_job):
    """Test PUT /api/v1/jobs/{id} endpoint"""
    response = await client.put(
        f"/api/v1/jobs/{sample_job.id}",
        json={
            "job_name": "Updated Name",
            "status": "completed",
            "notes": "Test notes"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["job_name"] == "Updated Name"
    assert data["status"] == "completed"
    assert data["notes"] == "Test notes"

@pytest.mark.asyncio
async def test_update_job_validation_error(client, sample_job):
    """Test validation errors"""
    response = await client.put(
        f"/api/v1/jobs/{sample_job.id}",
        json={
            "job_name": "",  # Invalid: empty
        }
    )

    assert response.status_code == 400

@pytest.mark.asyncio
async def test_update_job_partial_update(client, sample_job):
    """Test partial updates (only some fields)"""
    original_status = sample_job.status

    response = await client.put(
        f"/api/v1/jobs/{sample_job.id}",
        json={
            "notes": "Only updating notes"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Only updating notes"
    assert data["status"] == original_status  # Unchanged
```

### E2E Tests

**File**: `tests/e2e/test_jobs.py`

```python
@pytest.mark.asyncio
async def test_edit_job_workflow(page):
    """Test complete job edit workflow"""
    # Navigate to jobs page
    await page.goto("http://localhost:8000")
    await page.click("nav a[href='#jobs']")

    # Click edit on first job
    await page.click("button[data-action='edit-job']")

    # Wait for modal
    await page.wait_for_selector("#editJobModal")

    # Update fields
    await page.fill("#jobName", "E2E Updated Job")
    await page.select_option("#jobStatus", "completed")
    await page.fill("#notes", "E2E test notes")

    # Submit
    await page.click("#saveJobBtn")

    # Wait for success toast
    await page.wait_for_selector(".toast.success")

    # Verify job list updated
    job_name = await page.text_content("td:has-text('E2E Updated Job')")
    assert "E2E Updated Job" in job_name
```

---

## Rollout Plan

### Phase 1: Backend Implementation (2-3 hours)
1. ✅ Database migration (if needed)
2. ✅ Repository update method
3. ✅ Service update method
4. ✅ Pydantic schema
5. ✅ API endpoint
6. ✅ Unit tests

### Phase 2: Frontend Integration (1-2 hours)
1. ✅ Remove demo code
2. ✅ Implement API call
3. ✅ Error handling
4. ✅ Testing with real backend

### Phase 3: Testing & QA (1-2 hours)
1. ✅ API integration tests
2. ✅ E2E tests
3. ✅ Manual testing
4. ✅ Edge case validation

### Phase 4: Documentation & Release
1. ✅ Update API documentation
2. ✅ Update CHANGELOG.md
3. ✅ Remove from REMAINING_TASKS.md
4. ✅ Create PR and merge

---

## Success Criteria

- [ ] `PUT /api/v1/jobs/{id}` endpoint exists and works
- [ ] All validation rules enforced
- [ ] Frontend form actually saves changes
- [ ] Changes persist after page refresh
- [ ] WebSocket events fire on update
- [ ] Unit tests pass (100% coverage for new code)
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] API documentation updated
- [ ] No regression in existing job functionality

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing job creation | Low | High | Comprehensive tests before merge |
| Concurrent update conflicts | Medium | Medium | Add optimistic locking with `updated_at` |
| Frontend/backend schema mismatch | Low | Medium | Validate schema matches on both sides |
| Performance impact on job list | Low | Low | `updated_at` is indexed, minimal overhead |

---

## Dependencies

- None - This is a standalone feature
- Complements job status update endpoint (can be implemented in parallel)

---

## Follow-up Work

After this is complete:
1. Consider adding audit log for job changes
2. Add "Last modified by" field if multi-user auth is added
3. Implement optimistic locking for concurrent edits
4. Add bulk update endpoint for batch operations

---

**Status**: Ready for implementation
**Assignee**: TBD
**Target Version**: v2.9.0
