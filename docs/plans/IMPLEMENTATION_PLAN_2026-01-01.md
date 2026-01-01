# Implementation Plan - Priority 1 Tasks
**Date**: 2026-01-01
**Session**: claude/plan-implementation-CZNeq
**Based on**: docs/MASTERPLAN.md (v1.0, 2026-01-01)

---

## Executive Summary

This implementation plan addresses the **Critical Priority (P1)** tasks from the masterplan. After reviewing the codebase, the actual state differs from the masterplan in several areas:

### Key Findings

1. ✅ **Material Consumption History Endpoint** - **ALREADY IMPLEMENTED**
   - Masterplan Status: "Returns 501 Not Implemented"
   - Actual Status: Fully functional in `material_service.py:402-486`
   - Action: Verify endpoint works, mark as complete

2. ⚠️ **Job Status Update Tests** - **6 SKIPPED TESTS FOUND**
   - Masterplan lists tests at lines 305, 331, 366, 394, 621, 687
   - Actual skipped tests at lines 647, 771, 809, 836, 848, 907
   - Reason: Test fixture and implementation gaps
   - Action: Enable tests after implementing requirements

3. ⚠️ **Printer CRUD Tests** - **13 SKIPPED TESTS FOUND**
   - More extensive than masterplan indicated
   - Missing: filtering, create, update, delete implementations
   - Action: Implement service methods and enable tests

4. 📝 **Documentation Cleanup** - **TODO REMOVAL NEEDED**
   - Outdated TODO comments to remove
   - REMAINING_TASKS.md to update
   - Action: Clean up documentation

---

## Current Status Assessment

### Test Environment Status

**Issue**: Test collection errors prevent running tests
```
ImportError while importing test module 'tests/backend/test_api_jobs.py'
ImportError while importing test module 'tests/backend/test_api_printers.py'
```

**Impact**: Cannot validate current test status
**Resolution Needed**: Fix import errors before proceeding with test work

---

## Task 1: Material Consumption History Endpoint

### Status: ✅ COMPLETE (Masterplan Outdated)

### Evidence of Completion

**Endpoint**: `GET /api/v1/materials/consumption/history`
**Location**: `src/api/routers/materials.py:310-338`

```python
@router.get("/consumption/history", response_model=ConsumptionHistoryResponse)
async def get_consumption_history(
    material_id: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    printer_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=1000),
    page: int = Query(1, ge=1)
) -> ConsumptionHistoryResponse:
    """Get material consumption history with optional filters and pagination."""
    items, total_count = await material_service.get_consumption_history(...)
    # Returns paginated consumption history
```

**Service Implementation**: `src/services/material_service.py:402-486`

Features implemented:
- ✅ Time-based filtering (days parameter)
- ✅ Material filtering
- ✅ Job filtering
- ✅ Printer filtering
- ✅ Pagination (limit + page)
- ✅ Total count for pagination
- ✅ Joins with materials table for type/brand/color
- ✅ Ordered by timestamp DESC

### Verification Steps

1. **Manual API Test**:
   ```bash
   # Test basic endpoint
   curl http://localhost:8080/api/v1/materials/consumption/history

   # Test with filters
   curl "http://localhost:8080/api/v1/materials/consumption/history?days=7&limit=10&page=1"

   # Test with material filter
   curl "http://localhost:8080/api/v1/materials/consumption/history?material_id=xyz123"
   ```

2. **Check Response Model**:
   - Verify `ConsumptionHistoryResponse` model exists
   - Verify `ConsumptionHistoryItem` model exists
   - Check response includes: items, total_count, page, limit, total_pages

3. **Integration Test**:
   - Create test consumption records
   - Query with various filters
   - Verify pagination works correctly
   - Verify date range filtering

### Action Items

- [ ] Verify endpoint returns 200 OK (not 501)
- [ ] Test all filter combinations
- [ ] Update masterplan to mark as complete
- [ ] Remove from P1 task list

**Estimated Effort**: 1 hour (verification only)

---

## Task 2: Job Status Update Validation Tests

### Status: ⚠️ PARTIALLY IMPLEMENTED

### Skipped Tests Found

**Location**: `tests/backend/test_api_jobs.py`

| Line | Test Name | Skip Reason |
|------|-----------|-------------|
| 647 | `test_delete_job_with_active_status` | Error handling for active job deletion not fully implemented in router |
| 771 | (Unknown) | Test fixture doesn't properly mock database - needs refactoring |
| 809 | (Unknown) | Test fixture doesn't properly mock database - needs refactoring |
| 836 | (Unknown) | Mock not correctly intercepting service layer - needs refactoring |
| 848 | (Unknown) | Endpoint validation logic needs implementation |
| 907 | (Unknown) | Job deletion safety checks need implementation |

### Current Endpoint Status

**Endpoint**: `PUT /api/v1/jobs/{id}/status`
**Status**: EXISTS AND WORKS (tests at lines 305-393 suggest implementation)

Evidence from test code:
```python
def test_update_job_status_endpoint(self, client, test_app):
    """Test PUT /api/v1/jobs/{id}/status - Update job status"""
    response = client.put(
        f"/api/v1/jobs/{job_id}/status",
        json={'status': 'running'}
    )
    assert response.status_code == 200
```

### Issues to Address

#### Issue 1: Active Job Deletion Protection (Line 647)
**Requirement**: Prevent deletion of jobs in active states
**Implementation Needed**:
```python
# In src/api/routers/jobs.py or src/services/job_service.py
async def delete_job(job_id: str, force: bool = False):
    job = await self.get_job(job_id)

    if not force and job.status in ['running', 'paused', 'pending']:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete job in '{job.status}' status. Use force=true to override."
        )

    # Proceed with deletion
```

**Test to Enable**: Line 647

#### Issue 2: Test Fixture Database Mocking (Lines 771, 809, 836)
**Requirement**: Fix test fixtures to properly mock database
**Implementation Needed**:
- Review test fixture setup in `conftest.py`
- Ensure AsyncMock properly intercepts service calls
- Fix database connection mocking

**Tests to Enable**: Lines 771, 809, 836

#### Issue 3: Endpoint Validation Logic (Line 848)
**Requirement**: Implement validation for job status transitions
**Implementation Needed**:
```python
# Valid state transitions
VALID_TRANSITIONS = {
    'pending': ['running', 'cancelled', 'failed', 'completed'],
    'running': ['paused', 'completed', 'failed', 'cancelled'],
    'paused': ['running', 'cancelled', 'failed'],
    'completed': [],  # Terminal state
    'failed': [],     # Terminal state
    'cancelled': []   # Terminal state
}

async def validate_status_transition(current: str, new: str, force: bool = False):
    if force:
        return True

    if new not in VALID_TRANSITIONS.get(current, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from '{current}' to '{new}'"
        )
```

**Test to Enable**: Line 848

#### Issue 4: Job Deletion Safety Checks (Line 907)
**Requirement**: Additional safety checks for job deletion
**Implementation Needed**:
- Check for associated files
- Check for business jobs (require confirmation)
- Emit deletion event before actual deletion

**Test to Enable**: Line 907

### Implementation Plan

#### Step 1: Fix Test Fixtures (2-3 hours)
1. Review `tests/backend/conftest.py`
2. Fix database mocking in test_app fixture
3. Ensure service layer mocks work correctly
4. Run tests to verify fixtures work

#### Step 2: Implement Active Job Deletion Protection (1 hour)
1. Add validation in `job_service.delete_job()`
2. Add `force` parameter support
3. Enable test at line 647
4. Verify test passes

#### Step 3: Implement Status Transition Validation (2 hours)
1. Define `VALID_TRANSITIONS` constant
2. Add `validate_status_transition()` method
3. Integrate into `update_job_status()` endpoint
4. Add `force` flag support
5. Enable test at line 848
6. Verify test passes

#### Step 4: Implement Job Deletion Safety Checks (1 hour)
1. Add pre-deletion validation
2. Check for associated resources
3. Emit deletion event
4. Enable test at line 907
5. Verify test passes

#### Step 5: Enable Remaining Tests (30 min)
1. Enable tests at lines 771, 809, 836
2. Fix any remaining issues
3. Verify all 6 tests pass

**Total Estimated Effort**: 6.5-7.5 hours

---

## Task 3: Printer CRUD Operations Tests

### Status: ⚠️ MULTIPLE IMPLEMENTATIONS NEEDED

### Skipped Tests Found

**Location**: `tests/backend/test_api_printers.py`

| Lines | Count | Test Category | Skip Reason |
|-------|-------|---------------|-------------|
| 86, 99 | 2 | List with filtering | Requires filtering implementation in `printer_service.list_printers` |
| 112, 142 | 2 | Create printer | Requires `printer_service.create_printer` implementation and database service integration |
| 202, 235 | 2 | Get printer details | Requires printer instance mocking and `printer_service.printer_instances` integration |
| 260 | 1 | Get printer errors | Requires printer instance mocking and error handling integration |
| 293, 317 | 2 | Update printer | Requires `printer_service.update_printer` implementation (with validation) |
| 342, 363 | 2 | Delete printer | Requires `printer_service.delete_printer` implementation (with active job validation) |
| 379, 397 | 2 | Test connection | Test uses wrong endpoint: `/test-connection` instead of `/connect` |

**Total**: 13 skipped tests

### Current Printer Service Status

Need to review `src/services/printer_service.py` to understand:
- What CRUD methods exist
- What's missing
- How to integrate with database service

### Implementation Requirements

#### Requirement 1: List Printers with Filtering
**Missing**: Filter support in `list_printers()`
**Implementation**:
```python
async def list_printers(
    self,
    printer_type: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List printers with optional filters."""
    printers = list(self.printer_instances.values())

    # Apply filters
    if printer_type:
        printers = [p for p in printers if p.printer_type == printer_type]
    if status:
        printers = [p for p in printers if p.status == status]
    if location:
        printers = [p for p in printers if p.location == location]

    return [self._printer_to_dict(p) for p in printers]
```

**Tests to Enable**: Lines 86, 99
**Effort**: 1 hour

#### Requirement 2: Create Printer
**Missing**: `create_printer()` method and database integration
**Implementation**:
```python
async def create_printer(self, printer_data: PrinterCreate) -> Dict[str, Any]:
    """Create a new printer configuration."""
    printer_id = str(uuid4())

    # Validate printer type
    if printer_data.printer_type not in ['bambu_lab', 'prusa']:
        raise ValueError(f"Unsupported printer type: {printer_data.printer_type}")

    # Save to database
    async with self.db.connection() as conn:
        await conn.execute('''
            INSERT INTO printers (id, printer_type, name, ip_address, config, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            printer_id,
            printer_data.printer_type,
            printer_data.name,
            printer_data.ip_address,
            json.dumps(printer_data.config),
            datetime.now().isoformat()
        ))
        await conn.commit()

    # Initialize printer instance
    printer = await self._initialize_printer(printer_id, printer_data)
    self.printer_instances[printer_id] = printer

    return self._printer_to_dict(printer)
```

**Tests to Enable**: Lines 112, 142
**Effort**: 2-3 hours

#### Requirement 3: Update Printer
**Missing**: `update_printer()` method with validation
**Implementation**:
```python
async def update_printer(self, printer_id: str, update_data: PrinterUpdate) -> Dict[str, Any]:
    """Update printer configuration."""
    if printer_id not in self.printer_instances:
        raise ValueError(f"Printer {printer_id} not found")

    printer = self.printer_instances[printer_id]

    # Validate updates
    if update_data.ip_address and not self._validate_ip(update_data.ip_address):
        raise ValueError("Invalid IP address")

    # Update database
    update_dict = update_data.model_dump(exclude_unset=True)
    set_clauses = [f"{k} = ?" for k in update_dict.keys()]
    values = list(update_dict.values()) + [printer_id]

    async with self.db.connection() as conn:
        await conn.execute(
            f"UPDATE printers SET {', '.join(set_clauses)} WHERE id = ?",
            values
        )
        await conn.commit()

    # Reconnect if connection details changed
    if 'ip_address' in update_dict or 'config' in update_dict:
        await printer.disconnect()
        await printer.connect()

    return self._printer_to_dict(printer)
```

**Tests to Enable**: Lines 293, 317
**Effort**: 2 hours

#### Requirement 4: Delete Printer
**Missing**: `delete_printer()` method with active job validation
**Implementation**:
```python
async def delete_printer(self, printer_id: str, force: bool = False) -> bool:
    """Delete printer configuration."""
    if printer_id not in self.printer_instances:
        return False

    # Check for active jobs
    if not force:
        active_jobs = await self.job_service.get_active_jobs_for_printer(printer_id)
        if active_jobs:
            raise ValueError(
                f"Cannot delete printer with {len(active_jobs)} active jobs. "
                "Use force=true to override."
            )

    # Disconnect printer
    printer = self.printer_instances[printer_id]
    await printer.disconnect()

    # Delete from database
    async with self.db.connection() as conn:
        await conn.execute("DELETE FROM printers WHERE id = ?", (printer_id,))
        await conn.commit()

    # Remove from instances
    del self.printer_instances[printer_id]

    return True
```

**Tests to Enable**: Lines 342, 363
**Effort**: 2 hours

#### Requirement 5: Get Printer Details with Instance Integration
**Missing**: Proper mocking of printer instances in tests
**Implementation**: Fix test fixtures, not production code
**Tests to Enable**: Lines 202, 235, 260
**Effort**: 1-2 hours

#### Requirement 6: Fix Test Connection Endpoint
**Issue**: Tests use wrong endpoint `/test-connection` instead of `/connect`
**Fix**: Update test code or add endpoint alias
**Tests to Enable**: Lines 379, 397
**Effort**: 30 minutes

### Implementation Plan

#### Step 1: List Printers Filtering (1 hour)
1. Add filter parameters to `list_printers()`
2. Implement filtering logic
3. Enable tests at lines 86, 99
4. Verify tests pass

#### Step 2: Create Printer (2-3 hours)
1. Define `PrinterCreate` Pydantic model
2. Implement `create_printer()` method
3. Add database integration
4. Add printer instance initialization
5. Enable tests at lines 112, 142
6. Verify tests pass

#### Step 3: Update Printer (2 hours)
1. Define `PrinterUpdate` Pydantic model
2. Implement `update_printer()` method
3. Add validation logic
4. Handle reconnection for IP/config changes
5. Enable tests at lines 293, 317
6. Verify tests pass

#### Step 4: Delete Printer (2 hours)
1. Implement `delete_printer()` method
2. Add active job validation
3. Add `force` flag support
4. Handle cleanup (disconnect, database, cache)
5. Enable tests at lines 342, 363
6. Verify tests pass

#### Step 5: Fix Test Fixtures (1-2 hours)
1. Update test fixtures for printer instance mocking
2. Enable tests at lines 202, 235, 260
3. Verify tests pass

#### Step 6: Fix Test Connection Endpoint (30 min)
1. Either update tests or add endpoint alias
2. Enable tests at lines 379, 397
3. Verify tests pass

**Total Estimated Effort**: 8.5-10.5 hours

---

## Task 4: Documentation Cleanup

### Status: ⚠️ PENDING

### 4.1 Remove Outdated TODO Comments

#### Location: `frontend/js/jobs.js:1088`
**TODO**: "TODO: Implement actual API call"
**Status**: Backend fully implemented since v2.11+
**Action**: Remove comment

#### Search for Additional TODOs
**Command**:
```bash
grep -r "TODO.*Implement.*API" frontend/js/
grep -r "TODO.*implement" frontend/js/ -i
grep -r "TODO" src/ | grep -i "implement"
```

**Action**: Review and remove outdated TODOs

### 4.2 Update REMAINING_TASKS.md

**Changes Needed**:
1. Mark Job Update API as ✅ Complete
2. Update Material Consumption History as ✅ Complete
3. Update test coverage statistics
4. Add completion dates
5. Archive completed items

### 4.3 Update MASTERPLAN.md

**Changes Needed**:
1. Update Material Consumption History status to ✅ Complete
2. Update actual test line numbers for Job Status tests
3. Expand Printer CRUD section with all 13 skipped tests
4. Update project health metrics after task completion

### Implementation Plan

#### Step 1: Remove Outdated TODOs (1 hour)
1. Search for TODOs related to completed features
2. Remove or update TODO comments
3. Create git commit

#### Step 2: Update Documentation (1 hour)
1. Update REMAINING_TASKS.md
2. Update MASTERPLAN.md
3. Add completion notes
4. Create git commit

**Total Estimated Effort**: 2 hours

---

## Overall Implementation Plan

### Phase 1: Verification & Quick Wins (2-3 hours)

1. ✅ **Verify Material Consumption History** (1 hour)
   - Test endpoint manually
   - Verify all filters work
   - Update documentation

2. 📝 **Documentation Cleanup** (2 hours)
   - Remove outdated TODOs
   - Update REMAINING_TASKS.md
   - Update MASTERPLAN.md

**Total**: 3 hours

### Phase 2: Test Infrastructure Fixes (2-4 hours)

1. 🔧 **Fix Test Import Errors** (1 hour)
   - Resolve ImportError in test modules
   - Verify tests can run

2. 🔧 **Fix Test Fixtures** (2-3 hours)
   - Fix database mocking (Job tests)
   - Fix printer instance mocking (Printer tests)
   - Verify fixtures work

**Total**: 3-4 hours

### Phase 3: Job Status Update Tests (4-5 hours)

1. Implement active job deletion protection (1 hour)
2. Implement status transition validation (2 hours)
3. Implement job deletion safety checks (1 hour)
4. Enable and verify all 6 tests (1 hour)

**Total**: 5 hours

### Phase 4: Printer CRUD Operations (8-10 hours)

1. List printers filtering (1 hour)
2. Create printer (2-3 hours)
3. Update printer (2 hours)
4. Delete printer (2 hours)
5. Fix test fixtures (1-2 hours)
6. Fix test connection endpoint (30 min)

**Total**: 8.5-10.5 hours

---

## Summary

### Updated Task List

| Task | Masterplan Estimate | Actual Estimate | Status |
|------|-------------------|----------------|--------|
| Material Consumption History | 3-4 hours | 1 hour (verify) | ✅ Complete |
| Job Status Update Tests | 2-3 hours | 5 hours | ⚠️ Needs work |
| Printer CRUD Tests | 3-4 hours | 8.5-10.5 hours | ⚠️ Extensive work needed |
| Documentation Cleanup | 1-2 hours | 2 hours | ⚠️ Pending |
| **Sprint 1 Total** | **9-13 hours** | **16.5-18.5 hours** | ⚠️ +60% scope |

### Key Differences from Masterplan

1. **Material Consumption History**: Already done ✅
2. **Printer CRUD**: More extensive than expected (13 tests vs "multiple")
3. **Test Infrastructure**: Import errors need fixing first
4. **Overall Scope**: 60% larger than masterplan estimated

### Recommendations

#### Option A: Full Sprint (16-19 hours)
Complete all P1 tasks as expanded

#### Option B: Split Sprint
**Sprint 1A** (8 hours):
- Verify Material Consumption History ✅
- Documentation cleanup
- Fix test infrastructure
- Job Status Update tests

**Sprint 1B** (10 hours):
- Printer CRUD operations
- Enable all remaining tests

#### Option C: Prioritize by Impact
1. Documentation (2h) - Quick win
2. Material verification (1h) - Quick win
3. Job Status tests (5h) - Medium impact
4. Defer Printer CRUD to Sprint 2

### Next Steps

1. **Decide on approach** (A, B, or C)
2. **Fix test import errors** (blocking issue)
3. **Start with quick wins** (documentation + material verification)
4. **Proceed to implementation** based on chosen approach

---

## Test Execution Checklist

Before marking tasks complete:

### Material Consumption History
- [ ] Endpoint returns 200 OK
- [ ] Filters work (material_id, job_id, printer_id, days)
- [ ] Pagination works (limit, page)
- [ ] Response includes total_count, total_pages
- [ ] Documentation updated

### Job Status Update Tests
- [ ] All 6 skipped tests enabled
- [ ] All 6 tests passing
- [ ] Active job deletion protection works
- [ ] Status transition validation works
- [ ] Force flag works correctly
- [ ] Integration tests pass

### Printer CRUD Tests
- [ ] All 13 skipped tests enabled
- [ ] All 13 tests passing
- [ ] List filtering works
- [ ] Create printer works
- [ ] Update printer works
- [ ] Delete printer works
- [ ] Test fixtures properly mock services
- [ ] Test connection endpoint fixed

### Documentation
- [ ] Outdated TODOs removed
- [ ] REMAINING_TASKS.md updated
- [ ] MASTERPLAN.md updated
- [ ] Completion dates added
- [ ] Git commits created

---

## Appendix: Code Locations

### Files to Modify

**Job Status Updates**:
- `src/services/job_service.py` - Add validation methods
- `src/api/routers/jobs.py` - Update endpoints
- `tests/backend/conftest.py` - Fix fixtures
- `tests/backend/test_api_jobs.py` - Enable tests

**Printer CRUD**:
- `src/services/printer_service.py` - Add CRUD methods
- `src/api/routers/printers.py` - Add/update endpoints
- `src/models/printer.py` - Add Pydantic models
- `tests/backend/conftest.py` - Fix fixtures
- `tests/backend/test_api_printers.py` - Enable tests

**Documentation**:
- `frontend/js/jobs.js` - Remove TODO
- `docs/REMAINING_TASKS.md` - Update status
- `docs/MASTERPLAN.md` - Update plan
- Search and update other TODOs

---

**End of Implementation Plan**

*Next Action*: Review plan and decide on execution approach (Option A, B, or C)
