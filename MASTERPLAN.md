# Printernizer Test Implementation Master Plan

This document tracks skipped and failing tests in the CI/CD pipeline, categorizing them by root cause and priority for implementation.

**Last Updated:** 2026-01-09

## Current Test Status

| Metric | Count | Percentage |
|--------|-------|------------|
| **Passed** | 855 | 82.4% |
| **Failed** | 113 | 10.9% |
| **Errors** | 39 | 3.8% |
| **Skipped** | 31 | 3.0% |
| **Pass Rate** | - | **84.9%** |

**CI/CD Threshold:** 45% (PASSING ✓)

## Summary

| Category | Count | Status |
|----------|-------|--------|
| Future API Features | 2 | Planned |
| UI Features Missing | 5 | Planned |
| Infrastructure/Architecture | 1 | Needs Refactoring |
| Conditional Skips (E2E) | 20+ | Working as Designed |
| Example/Template Tests | 1 | N/A |
| **Recently Completed** | 6 | Done |

---

## Category 1: Future API Features

These tests are correctly written but test endpoints that haven't been implemented yet.

### 1.1 Download Progress Endpoint

**File:** `tests/backend/test_api_files.py:233`

```python
@pytest.mark.skip(reason="Download progress endpoint not yet implemented - future feature")
def test_get_file_download_progress(self, client):
    """Test GET /api/v1/files/downloads/{download_id}/progress"""
```

**Status:** Not Implemented
**Priority:** Medium
**Implementation Notes:**
- Endpoint: `GET /api/v1/files/downloads/{download_id}/progress`
- Should return: `{ "download_id": "...", "progress": 45.5, "status": "downloading", "bytes_downloaded": 1024000, "total_bytes": 2048000 }`
- Requires: Background download task tracking, WebSocket or polling support
- Files to modify:
  - `src/api/routers/files.py` - Add endpoint
  - `src/services/file_service.py` - Add progress tracking
  - Database: Consider `download_progress` table

---

### 1.2 File Cleanup Endpoint

**File:** `tests/backend/test_api_files.py:250`

```python
@pytest.mark.skip(reason="File cleanup endpoint not yet implemented - future feature")
def test_post_file_cleanup(self, client):
    """Test POST /api/v1/files/cleanup - Clean up old downloaded files"""
```

**Status:** Not Implemented
**Priority:** Low
**Implementation Notes:**
- Endpoint: `POST /api/v1/files/cleanup`
- Parameters: `{ "older_than_days": 30, "dry_run": false }`
- Should return: `{ "deleted_count": 15, "freed_bytes": 500000000 }`
- Files to modify:
  - `src/api/routers/files.py` - Add endpoint
  - `src/services/file_service.py` - Add cleanup logic

---

## Category 2: UI Features Missing in debug.html

These E2E tests are correctly written but test UI elements that don't exist in the current `debug.html`.

### 2.1 Auto-Refresh Checkbox

**File:** `tests/e2e/test_debug.py:142,150`

```python
@pytest.mark.skip(reason="Auto-refresh checkbox not present in current debug.html")
def test_auto_refresh_checkbox_visible(...)
def test_auto_refresh_toggle(...)
```

**Status:** UI Not Implemented
**Priority:** Low
**Implementation Notes:**
- Add checkbox to debug.html: `<input type="checkbox" id="autoRefresh">`
- Add JavaScript to enable periodic refresh (e.g., every 5 seconds)
- Files to modify:
  - `frontend/debug.html` - Add checkbox UI
  - `frontend/static/js/debug.js` - Add auto-refresh logic

---

### 2.2 Thumbnail Log Limit Selector

**Files:** `tests/e2e/test_debug.py:204,212,223`

```python
@pytest.mark.skip(reason="Thumbnail log limit selector not present in current debug.html")
def test_thumbnail_log_limit_visible(...)
def test_thumbnail_log_limit_options(...)
def test_thumbnail_log_limit_change(...)
```

**Status:** UI Not Implemented
**Priority:** Low
**Implementation Notes:**
- Add select element: `<select id="thumbnailLogLimit"><option value="10">10</option>...</select>`
- Options: 10, 20, 50, 100
- Files to modify:
  - `frontend/debug.html` - Add selector in thumbnail section
  - `frontend/static/js/debug.js` - Wire up limit change handler

---

## Category 3: Infrastructure/Architecture Issues

These tests are correctly written but require infrastructure changes to run properly.

### ~~3.1 Large Job List Performance Test~~ COMPLETED

**File:** `tests/backend/test_api_jobs.py:813`

**Status:** IMPLEMENTED (2026-01-08)
**Resolution:** Refactored to use mocked services with large dataset fixture. Now tests API layer performance (serialization, response handling) with 550 jobs.

New tests added:
- `test_large_job_list_performance` - Tests response time with 550 jobs
- `test_pagination_performance` - Tests pagination with different page sizes

---

### ~~3.2 Job Filtering Performance Test~~ COMPLETED

**File:** `tests/backend/test_api_jobs.py:842`

**Status:** IMPLEMENTED (2026-01-08)
**Resolution:** Refactored to use mocked services. Tests multiple filter combinations (status, is_business, printer_id, material_type) with large dataset.

---

### 3.3 Database Connection Error Handling Test

**File:** `tests/backend/test_api_jobs.py:849`

```python
@pytest.mark.skip(reason="TestClient lifecycle reinitializes services - requires test architecture refactoring")
def test_job_api_database_connection_error(self, test_app):
```

**Status:** Test Architecture Issue
**Priority:** Low
**Root Cause:** FastAPI's TestClient re-initializes app state between requests, making it difficult to test error injection scenarios
**Implementation Notes:**
- Consider using dependency injection override for testing
- Alternative: Use `app.dependency_overrides` to inject mock services
- Files to modify:
  - `tests/conftest.py` - Refactor `test_app` fixture
  - Potentially use `httpx.AsyncClient` directly instead of `TestClient`

---

## Category 4: Conditional E2E Skips (Working as Designed)

These tests use `pytest.skip()` at runtime to handle situations where UI elements may not be present. This is intentional defensive testing.

### 4.1 Modal Tests (`tests/e2e/test_modals.py`)

| Line | Skip Condition | Reason |
|------|----------------|--------|
| 109 | Add printer button not available | UI may not have button |
| 119 | Add printer button not available | UI may not have button |
| 134 | Add printer button not available | UI may not have button |
| 151 | New idea button not available | Ideas page may vary |
| 161 | Import URL button not available | Feature may not be present |
| 170 | Import URL button not available | Feature may not be present |
| 190 | Add material button not available | UI may not have button |

**Status:** Working as Designed
**Note:** These are defensive skips - tests attempt actions and skip gracefully if UI differs from expected. No action required.

---

### 4.2 Jobs Tests (`tests/e2e/test_jobs.py`)

| Line | Skip Condition | Reason |
|------|----------------|--------|
| 84 | Business checkbox not present | Feature may not be in current UI |
| 105 | Business checkbox not present | Feature may not be in current UI |

**Status:** Working as Designed
**Note:** Business job features may be toggled on/off. Tests skip gracefully.

---

### 4.3 Printers Tests (`tests/e2e/test_printers.py`)

| Line | Skip Condition | Reason |
|------|----------------|--------|
| 140 | Search input not present | Page version may differ |
| 149 | Could not seed printers via API | Backend may not be running |
| Additional | Various seeding/search skips | Backend availability |

**Status:** Working as Designed
**Note:** E2E tests gracefully handle missing backend.

---

### 4.4 Materials Tests (`tests/e2e/test_materials.py`)

| Skip Condition | Reason |
|----------------|--------|
| Refresh button not present | UI variation |
| View toggle not present | UI variation |
| Search input not present | UI variation |
| Type filter not available | UI variation |

**Status:** Working as Designed

---

### 4.5 Seeded Data Tests (Various E2E files)

Tests using `seeded_printers`, `seeded_materials`, `seeded_jobs` fixtures skip if:
- Backend API is not available
- Seeding requests fail
- No data was created despite seeding

**Status:** Working as Designed
**Note:** These are integration tests that require a running backend. In CI, the E2E job starts the server first.

---

## Category 5: Example/Template Tests

### 5.1 Conditional Skip Example

**File:** `tests/e2e/test_examples.py:213`

```python
@pytest.mark.skipif(
    condition=True,  # Change to False to run this test
    reason="Example test - requires specific test data"
)
def test_conditional_skip_example(app_page: Page, base_url: str):
```

**Status:** Example Code
**Note:** This is intentionally skipped as a template for conditional testing.

---

## Category 6: Printer Integration Tests

### 6.1 BambuLabs API Conformance

**File:** `tests/integration/test_printer_interface_conformance.py`

```python
pytest.skip("bambulabs-api not installed; skipping BambuLabPrinter conformance test")
```

**Status:** Optional Dependency
**Note:** Skipped when `bambulabs-api` package is not installed. This is expected behavior.

---

## Category 7: Remaining Test Failures (113 failures, 39 errors)

These tests are failing due to mock configuration issues or service implementation mismatches.

### 7.1 JobService Tests (~24 failures)

**File:** `tests/services/test_job_service.py`

**Root Cause:** Mock database configuration issues - tests mock database but service expects different attribute structure
**Priority:** Medium
**Fix Required:**
- Update mock fixtures to match actual Database class interface
- Ensure `mock_db.config` returns proper configuration object

### 7.2 Auto Job Creation Tests (~28 errors)

**File:** `tests/services/test_auto_job_creation.py`

**Root Cause:** Mock attribute errors - mocks missing required attributes/methods
**Priority:** Medium
**Fix Required:**
- Review AutoJobCreationService dependencies
- Update mock fixtures to include all required attributes

### 7.3 Integration Tests (~14 failures)

**File:** `tests/integration/test_integration.py`

**Root Cause:** Missing service methods - tests call methods that don't exist or have different signatures
**Priority:** Low
**Fix Required:**
- Review service method signatures
- Update tests to match current API

### 7.4 Analytics Service Tests (~9 failures)

**File:** `tests/services/test_analytics_service.py`

**Root Cause:** Service method signature mismatches
**Priority:** Low
**Fix Required:**
- Update test mocks to match current service interface

---

## Implementation Priorities

### High Priority (Should Fix Soon)
1. JobService test mocks (affects 24 tests)
2. AutoJobCreation test mocks (affects 28 tests)

### Medium Priority (Next Sprint)
1. Download Progress Endpoint (Future Feature)
2. ~~Integration Test Infrastructure (Database Seeding)~~ **COMPLETED 2026-01-08**
3. Integration tests service method alignment

### Low Priority (Backlog)
1. File Cleanup Endpoint
2. Auto-Refresh Checkbox in debug.html
3. Thumbnail Log Limit Selector in debug.html
4. Database Connection Error Test Architecture
5. Analytics Service test fixes

### Recently Completed
- **2026-01-09**: OctoPrint printer integration (v2.25.0):
  - New `OctoPrintPrinter` class implementing full BasePrinter interface
  - SockJS WebSocket client for real-time push updates
  - REST API integration for status, job control, file operations
  - Unit tests added: `tests/printers/test_octoprint.py` (~500 lines)
- **2026-01-08**: Performance tests refactored - `test_large_job_list_performance`, `test_job_filtering_performance`, `test_pagination_performance` now working with mocked services
- **2026-01-08**: Added `async_db_connection` fixture to global conftest.py - Fixes 11 fixture setup ERRORs:
  - `tests/backend/test_api_pagination_optimizations.py::TestRepositoryCountOptimization` - 2 tests now PASS
  - `tests/services/test_analytics_service.py` - 9 tests now run (fixture works, tests have other issues)
- **2026-01-09**: Fixed PrinterControlService tests - 28 tests now PASS (was 26 failures):
  - Fixed `connection_service` fixture to use `get_printer_instance()` method
  - Fixed all "not found" tests to use correct error message format
  - Updated monitoring tests to match actual implementation behavior
- **2026-01-09**: Fixed PrinterConnectionService tests - 18 tests now PASS (was hanging):
  - Root cause: `async_database` fixture didn't close connection pool properly
  - Fix: Changed `db._connection.close()` to `db.close()` to close all pool connections
  - Fixed `test_connect_printer_connection_fails` assertion to check `details["printer_id"]`

---

## CI/CD Test Status

Current test pass rate thresholds in `.github/workflows/ci-cd.yml`:
- Backend Tests: 45% minimum
- Frontend Tests: 95% minimum
- E2E Tests: No hard threshold (informational)

### Recommendations
1. Keep conditional skips in E2E tests - they handle UI variations gracefully
2. Implement database seeding fixtures for integration tests
3. Consider separate CI job for integration tests with higher timeout

---

## How to Track Progress

When implementing a feature from this list:
1. Update the **Status** field in this document
2. Add the implementation date
3. Remove the `@pytest.mark.skip` decorator from the test
4. Verify the test passes in CI

---

## Appendix: Quick Reference

### Files with Skipped Tests

| File | Skip Count | Category |
|------|------------|----------|
| `tests/backend/test_api_files.py` | 2 | Future Features |
| `tests/backend/test_api_jobs.py` | 1 | Infrastructure |
| `tests/e2e/test_debug.py` | 5 | UI Missing |
| `tests/e2e/test_modals.py` | 7+ | Conditional (OK) |
| `tests/e2e/test_jobs.py` | 2 | Conditional (OK) |
| `tests/e2e/test_printers.py` | 5+ | Conditional (OK) |
| `tests/e2e/test_materials.py` | 4+ | Conditional (OK) |
| `tests/e2e/test_examples.py` | 1 | Example |
| `tests/integration/test_printer_interface_conformance.py` | 1 | Optional Dep |

### Recently Fixed Tests

| File | Tests Fixed | Date |
|------|-------------|------|
| `tests/printers/test_octoprint.py` | New file - OctoPrint printer unit tests (~25 tests) | 2026-01-09 |
| `tests/backend/test_api_jobs.py` | `test_large_job_list_performance`, `test_job_filtering_performance`, `test_pagination_performance` | 2026-01-08 |
| `tests/backend/test_api_pagination_optimizations.py` | `test_job_repository_count_method`, `test_file_repository_count_method` | 2026-01-08 |
| `tests/conftest.py` | Added `async_db_connection` fixture (global) | 2026-01-08 |
| `tests/services/test_printer_control_service.py` | All 28 tests fixed (mock fixtures, error messages, implementation alignment) | 2026-01-09 |
| `tests/services/test_printer_connection_service.py` | All 18 tests fixed (async_database fixture cleanup, error assertion) | 2026-01-09 |
| `tests/conftest.py` | Fixed `async_database` fixture to properly close connection pool | 2026-01-09 |

### New Features Added

| Feature | Files | Version |
|---------|-------|---------|
| OctoPrint Integration | `src/printers/octoprint.py`, `src/services/octoprint_sockjs_client.py` | v2.25.0 |
