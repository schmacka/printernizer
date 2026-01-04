# Sprint 1B Implementation Plan - Printer CRUD Operations
**Date**: 2026-01-01
**Session**: `claude/continue-masterplan-zD4wr`
**Based on**: docs/MASTERPLAN.md Sprint 1B
**Previous Sprint**: Sprint 1A - COMPLETE ✅

---

## Executive Summary

Similar to Sprint 1A, initial investigation reveals that **Printer CRUD operations are already fully implemented** in the codebase. The 13 skipped tests exist because they were written before the implementation was complete, but the implementation now exists.

### Key Findings

1. ✅ **Printer CRUD Service Methods** - **FULLY IMPLEMENTED**
   - `create_printer()` - `printer_service.py:688-771`
   - `update_printer()` - `printer_service.py:773-840`
   - `delete_printer()` - `printer_service.py:842-865`

2. ✅ **Printer CRUD API Endpoints** - **FULLY IMPLEMENTED**
   - `POST /api/v1/printers` - `printers.py:378-419`
   - `GET /api/v1/printers/{id}` - `printers.py:422-431`
   - `PUT /api/v1/printers/{id}` - `printers.py:434-445`
   - `DELETE /api/v1/printers/{id}` - `printers.py:448-456`

3. ⚠️ **13 Skipped Tests** - Need enabling and verification
   - Filtering tests (2)
   - Create printer tests (2)
   - Get printer details tests (3)
   - Update printer tests (2)
   - Delete printer tests (2)
   - Test connection tests (2)

**Estimated Sprint Time**: 4-6 hours (vs original 8-10h estimate)
**Primary Work**: Test verification and fixture updates (not implementation)

---

## Sprint 1B Objectives

### Primary Goals
1. Verify all Printer CRUD operations work correctly
2. Fix test fixtures to properly test existing functionality
3. Enable all 13 skipped tests
4. Ensure test pass rate reaches 90%+
5. Document any missing features (if any)

### Success Criteria
- ✅ All printer CRUD endpoints verified functional
- ✅ At least 11/13 skipped tests enabled and passing
- ✅ Test pass rate >85%
- ✅ No critical bugs discovered
- ✅ Documentation updated

---

## Skipped Tests Analysis

### Category 1: List Filtering (2 tests) - **Likely Already Working**

**Location**: `test_api_printers.py:86-100`

**Tests**:
1. Line 86: `test_get_printers_filter_by_type`
2. Line 99: `test_get_printers_filter_by_active_status`

**Skip Reason**: "Requires filtering implementation in printer_service.list_printers"

**Investigation Needed**:
- Check if `list_printers()` already supports filtering
- Review endpoint implementation for filter support
- May just need query parameter handling in router

**Estimated Effort**: 1-2 hours (add query params if needed, enable tests)

---

### Category 2: Create Printer (2 tests) - **Endpoint EXISTS**

**Location**: `test_api_printers.py:112-142`

**Tests**:
1. Line 112: `test_create_printer_bambu`
2. Line 142: `test_create_printer_prusa`

**Skip Reason**: "Requires printer_service.create_printer implementation and database service integration"

**Actual Status**: ✅ **FULLY IMPLEMENTED**
- Endpoint: `POST /api/v1/printers` exists
- Service method: `create_printer()` exists and complete
- Database integration: Already implemented

**Work Needed**:
- Update test fixtures to work with actual implementation
- Enable tests
- Verify tests pass

**Estimated Effort**: 1 hour

---

### Category 3: Get Printer Details (3 tests) - **Endpoint EXISTS**

**Location**: `test_api_printers.py:202-260`

**Tests**:
1. Line 202: `test_get_printer_by_id`
2. Line 235: `test_get_printer_status_details`
3. Line 260: `test_get_printer_error_handling`

**Skip Reason**: "Requires printer instance mocking and printer_service.printer_instances integration"

**Actual Status**: ✅ **FULLY IMPLEMENTED**
- Endpoint: `GET /api/v1/printers/{id}` exists
- Service method: `get_printer()` exists
- Instance integration: Working

**Work Needed**:
- Fix test fixtures to properly mock printer instances
- Enable tests
- Verify tests pass

**Estimated Effort**: 1-2 hours

---

### Category 4: Update Printer (2 tests) - **Endpoint EXISTS**

**Location**: `test_api_printers.py:293-317`

**Tests**:
1. Line 293: `test_update_printer_connection_config`
2. Line 317: `test_update_printer_with_validation`

**Skip Reason**: "Requires printer_service.update_printer implementation (with validation)"

**Actual Status**: ✅ **FULLY IMPLEMENTED**
- Endpoint: `PUT /api/v1/printers/{id}` exists
- Service method: `update_printer()` exists
- Validation: Implemented via Pydantic models

**Work Needed**:
- Enable tests
- Verify validation works correctly
- May need to add edge case validation

**Estimated Effort**: 30 minutes - 1 hour

---

### Category 5: Delete Printer (2 tests) - **Endpoint EXISTS**

**Location**: `test_api_printers.py:342-363`

**Tests**:
1. Line 342: `test_delete_printer_success`
2. Line 363: `test_delete_printer_with_active_jobs`

**Skip Reason**: "Requires printer_service.delete_printer implementation with active job validation"

**Actual Status**: ⚠️ **PARTIALLY IMPLEMENTED**
- Endpoint: `DELETE /api/v1/printers/{id}` exists
- Service method: `delete_printer()` exists
- **Missing**: Active job validation (similar to job deletion protection from Sprint 1A)

**Work Needed**:
- Add active job check to `delete_printer()` (similar to Sprint 1A job deletion)
- Prevent deletion if printer has active jobs
- Enable tests
- Verify both tests pass

**Estimated Effort**: 1-2 hours

---

### Category 6: Test Connection (2 tests) - **Endpoint Mismatch**

**Location**: `test_api_printers.py:379-397`

**Tests**:
1. Line 379: `test_test_connection_success`
2. Line 397: `test_test_connection_failure`

**Skip Reason**: "Test uses wrong endpoint: /test-connection instead of /connect"

**Actual Status**: ⚠️ **ENDPOINT MISMATCH**
- Endpoint exists: `POST /api/v1/printers/test-connection` (line 350)
- Tests expect: `/test-connection` (without `/api/v1/printers` prefix?)
- Or: Tests should use `POST /api/v1/printers/{id}/connect`?

**Work Needed**:
- Investigate actual endpoint path
- Update tests to use correct endpoint
- Enable tests

**Estimated Effort**: 30 minutes

---

## Implementation Plan

### Phase 1: Verification & Quick Wins (1-2 hours)

#### Task 1.1: Verify Existing Endpoints Work
**Time**: 30 minutes

Run manual tests of all CRUD endpoints:

```bash
# Create printer (POST)
curl -X POST http://localhost:8080/api/v1/printers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Bambu A1",
    "printer_type": "bambu_lab",
    "connection_config": {
      "ip_address": "192.168.1.100",
      "access_code": "12345678",
      "serial_number": "AC123456"
    }
  }'

# Get printer (GET)
curl http://localhost:8080/api/v1/printers/{printer_id}

# Update printer (PUT)
curl -X PUT http://localhost:8080/api/v1/printers/{printer_id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'

# Delete printer (DELETE)
curl -X DELETE http://localhost:8080/api/v1/printers/{printer_id}
```

**Deliverable**: Confirmation that all CRUD operations work

---

#### Task 1.2: Fix Test Connection Endpoint Tests
**Time**: 30 minutes

1. Check actual endpoint path in router
2. Update test paths to match
3. Enable both tests
4. Verify tests pass

**Deliverable**: +2 passing tests

---

#### Task 1.3: Enable Create Printer Tests
**Time**: 1 hour

1. Review test fixture setup
2. Update mocks to work with current implementation
3. Enable both tests (Bambu + Prusa)
4. Fix any assertion mismatches
5. Verify tests pass

**Deliverable**: +2 passing tests

---

### Phase 2: Test Fixtures & Instance Mocking (1-2 hours)

#### Task 2.1: Fix Get Printer Tests
**Time**: 1-2 hours

**Issue**: Tests need proper printer instance mocking

**Implementation**:
```python
# In tests/backend/conftest.py or test file
@pytest.fixture
def mock_printer_instance():
    """Create mock printer instance with status."""
    from unittest.mock import MagicMock
    from src.models.printer import PrinterStatus

    instance = MagicMock()
    instance.is_connected = True
    instance.name = "Test Printer"
    instance.ip_address = "192.168.1.100"
    instance.last_status = MagicMock(
        status=PrinterStatus.IDLE,
        progress=0,
        current_job=None,
        temperature_bed=60.0,
        temperature_nozzle=200.0,
        timestamp=datetime.now()
    )
    return instance

def test_get_printer_by_id(client, test_app, mock_printer_instance):
    """Test GET /api/v1/printers/{id}"""
    from unittest.mock import AsyncMock

    # Setup mocks
    test_app.state.printer_service.get_printer = AsyncMock(return_value=sample_printer)
    test_app.state.printer_service.printer_instances = {
        'printer_123': mock_printer_instance
    }

    response = client.get("/api/v1/printers/printer_123")
    assert response.status_code == 200
    # ... assertions
```

**Deliverable**: +3 passing tests

---

### Phase 3: Missing Features (1-2 hours)

#### Task 3.1: Add Active Job Protection to Delete Printer
**Time**: 1-2 hours

**Implementation**: Similar to Sprint 1A job deletion protection

**Service Layer** (`src/services/printer_service.py`):
```python
async def delete_printer(self, printer_id: str, force: bool = False) -> bool:
    """
    Delete a printer configuration.

    Args:
        printer_id: Printer identifier
        force: If True, skip active job validation

    Returns:
        True if deletion successful

    Raises:
        ValueError: If printer has active jobs and force=False
    """
    printer_id_str = printer_id

    # Check for active jobs (unless force=True)
    if not force:
        # Import here to avoid circular dependency
        from src.services.job_service import JobService
        # Assume we can access job_service somehow
        # This may require refactoring to pass job_service to printer_service

        # For now, simple implementation:
        # Check if printer has any running/pending/paused jobs
        # This will need coordination with job_service
        pass

    # Disconnect if connected
    if printer_id_str in self.connection.printer_instances:
        instance = self.connection.printer_instances[printer_id_str]
        if instance.is_connected:
            await instance.disconnect()
        del self.connection.printer_instances[printer_id_str]

    # Remove from configuration
    return self.config_service.remove_printer(printer_id_str)
```

**API Layer** (`src/api/routers/printers.py`):
```python
@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_printer(
    printer_id: str,
    force: bool = Query(False, description="Force deletion even with active jobs"),
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Delete a printer configuration."""
    try:
        success = await printer_service.delete_printer(printer_id, force=force)
        if not success:
            raise PrinterNotFoundError(printer_id)
    except ValueError as e:
        # Handle active job deletion attempt
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
```

**Challenge**: `PrinterService` needs access to `JobService` to check for active jobs. This may require:
1. Dependency injection of `JobService` into `PrinterService`
2. Or: Add `job_service` parameter to `delete_printer()` method
3. Or: Database query directly for active jobs

**Deliverable**: +2 passing tests, active job protection feature

---

#### Task 3.2: Add Filtering Support (if needed)
**Time**: 1 hour

**Check Current Implementation**:
```python
# src/services/printer_service.py:140-181
async def list_printers(self) -> List[Printer]:
    """Get list of all configured printers."""
    # Currently returns ALL printers
    # Need to add filter parameters
```

**Implementation** (if needed):
```python
async def list_printers(
    self,
    printer_type: Optional[PrinterType] = None,
    is_active: Optional[bool] = None,
    status: Optional[PrinterStatus] = None
) -> List[Printer]:
    """Get list of all configured printers with optional filters."""
    printers = []

    for printer_id, instance in self.connection.printer_instances.items():
        # ... existing code to create printer object ...

        # Apply filters
        if printer_type is not None and printer.type != printer_type:
            continue
        if is_active is not None and printer.is_active != is_active:
            continue
        if status is not None and printer.status != status:
            continue

        printers.append(printer)

    return printers
```

**Router Update** (`src/api/routers/printers.py`):
```python
@router.get("", response_model=PrinterListResponse)
async def list_printers(
    printer_type: Optional[PrinterType] = Query(None, description="Filter by printer type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    status: Optional[PrinterStatus] = Query(None, description="Filter by printer status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    printer_service: PrinterService = Depends(get_printer_service)
):
    """List all printers with optional filters and pagination."""
    printers = await printer_service.list_printers(
        printer_type=printer_type,
        is_active=is_active,
        status=status
    )

    # ... existing pagination code ...
```

**Deliverable**: +2 passing tests, filtering feature

---

### Phase 4: Update & Documentation (30 minutes)

#### Task 4.1: Update Documentation
**Time**: 30 minutes

**Files to Update**:
1. `docs/MASTERPLAN.md`
   - Mark Sprint 1B as complete
   - Update Printer CRUD section
   - Update test coverage stats

2. `docs/REMAINING_TASKS.md`
   - Mark Printer CRUD as complete
   - Update effort estimates

3. Create `docs/plans/SPRINT_1B_FINAL_REPORT.md`
   - Document discoveries
   - List all enabled tests
   - Show before/after metrics

**Deliverable**: Updated documentation

---

## Execution Strategy

### Option A: Full Sprint (4-6 hours)
Complete all phases in order, enable all tests.

**Timeline**:
- Phase 1: Verification & Quick Wins (1-2h)
- Phase 2: Test Fixtures (1-2h)
- Phase 3: Missing Features (1-2h)
- Phase 4: Documentation (30min)

**Result**: All 13 tests enabled, Sprint 1B 100% complete

---

### Option B: Prioritized Sprint (3-4 hours)
Focus on high-value tests first, defer low-priority items.

**High Priority**:
- Create printer tests (2 tests)
- Get printer tests (3 tests)
- Update printer tests (2 tests)
- Delete printer tests (2 tests)

**Low Priority** (defer):
- Filtering tests (2 tests) - feature may not be needed yet
- Test connection tests (2 tests) - endpoint confusion

**Result**: 9/13 tests enabled, core functionality verified

---

### Option C: Investigation First (1 hour)
Run all tests with skips removed to see what actually fails.

**Process**:
1. Comment out all `@pytest.mark.skip` decorators
2. Run full test suite
3. Categorize failures:
   - Actual bugs
   - Test fixture issues
   - Missing features
4. Fix based on findings

**Result**: Data-driven approach, may discover different issues

---

## Recommended Approach

**Recommendation**: **Option C** (Investigation First) followed by **Option A** (Full Sprint)

**Reasoning**:
1. Sprint 1A taught us that "skipped tests" doesn't mean "missing features"
2. May discover that most tests already pass with minor fixes
3. Efficient use of time - fix what's actually broken
4. Could complete sprint in 2-3 hours instead of 4-6 hours

**Execution Plan**:
1. **Hour 1**: Investigation
   - Remove skip markers
   - Run tests
   - Categorize failures
   - Create priority fix list

2. **Hours 2-3**: Focused Fixes
   - Fix test fixtures (highest impact)
   - Add missing validations
   - Enable tests incrementally

3. **Hour 4**: Documentation
   - Update all planning docs
   - Create final report
   - Commit and push

---

## Risk Assessment

### Low Risk Items ✅
- Create printer tests - Endpoint exists
- Update printer tests - Endpoint exists
- Get printer tests - Endpoint exists

### Medium Risk Items ⚠️
- Filtering tests - May need implementation
- Test connection tests - Endpoint confusion

### Higher Risk Items 🔴
- Delete printer with active jobs - Requires job service integration
  - **Mitigation**: Similar to Sprint 1A, add ValueError exception
  - **Fallback**: Skip this validation for now, implement in Sprint 2

---

## Test Execution Checklist

Before marking Sprint 1B complete:

### Printer CRUD Endpoints
- [ ] POST /api/v1/printers (create) works
- [ ] GET /api/v1/printers (list) works
- [ ] GET /api/v1/printers/{id} (get) works
- [ ] PUT /api/v1/printers/{id} (update) works
- [ ] DELETE /api/v1/printers/{id} (delete) works

### Test Suite
- [ ] At least 11/13 skipped tests enabled
- [ ] All enabled tests passing
- [ ] Test pass rate >85%
- [ ] No test fixture errors

### Features
- [ ] Create printer (Bambu Lab)
- [ ] Create printer (Prusa)
- [ ] Get printer details with status
- [ ] Update printer configuration
- [ ] Delete printer (basic)
- [ ] Delete printer (with active job protection)
- [ ] Test connection endpoint

### Documentation
- [ ] MASTERPLAN.md updated
- [ ] REMAINING_TASKS.md updated
- [ ] Sprint 1B final report created
- [ ] Git commits created

---

## Expected Outcomes

### Best Case Scenario (2-3 hours) 🎯
- All 13 tests already working with minor fixes
- Only test fixtures need updates
- Sprint 1B complete in half estimated time
- Similar to Sprint 1A success

### Realistic Scenario (4-5 hours) ✅
- 11/13 tests enabled and passing
- 2-3 minor features need implementation
- Some test fixture work needed
- Sprint 1B complete within estimate

### Worst Case Scenario (6-8 hours) ⚠️
- Several missing features discovered
- Complex test fixture issues
- Integration problems between services
- Need to defer some work to Sprint 2

**Most Likely**: **Realistic Scenario** based on Sprint 1A pattern

---

## Next Steps After Sprint 1B

Upon completion of Sprint 1B, Sprint 1 (all Priority 1 tasks) will be complete:
- ✅ Sprint 1A: Job API & Material Consumption
- ✅ Sprint 1B: Printer CRUD Operations

**Options for Next Work**:
1. **Sprint 2**: Core Service Test Coverage (20-30 hours)
2. **Sprint 3**: User-Facing Polish (9-12 hours)
3. **Sprint 4**: Feature Completion (12-17 hours)

**Recommendation**: Start **Sprint 2** (Test Coverage) to build solid foundation before adding new features.

---

## Appendix: Code Locations

### Service Layer
- `src/services/printer_service.py`
  - Line 140-181: `list_printers()`
  - Line 688-771: `create_printer()`
  - Line 773-840: `update_printer()`
  - Line 842-865: `delete_printer()`

### API Layer
- `src/api/routers/printers.py`
  - Line 166: GET "" (list printers)
  - Line 378-419: POST "" (create printer)
  - Line 422-431: GET "/{id}" (get printer)
  - Line 434-445: PUT "/{id}" (update printer)
  - Line 448-456: DELETE "/{id}" (delete printer)
  - Line 350: POST "/test-connection"

### Tests
- `tests/backend/test_api_printers.py`
  - Lines 86-100: Filtering tests
  - Lines 112-142: Create printer tests
  - Lines 202-260: Get printer tests
  - Lines 293-317: Update printer tests
  - Lines 342-363: Delete printer tests
  - Lines 379-397: Test connection tests

---

**End of Sprint 1B Plan**

**Status**: Ready to execute
**Next Action**: Begin Phase 1 (Investigation) or start with Option C approach
**Estimated Completion**: 2-6 hours depending on findings
