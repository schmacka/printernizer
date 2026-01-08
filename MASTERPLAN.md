# Printernizer Test Implementation Master Plan

This document tracks skipped and failing tests in the CI/CD pipeline, categorizing them by root cause and priority for implementation.

**Last Updated:** 2026-01-08

## Summary

| Category | Count | Status |
|----------|-------|--------|
| Future API Features | 2 | Planned |
| UI Features Missing | 5 | Planned |
| Infrastructure/Architecture | 3 | Needs Refactoring |
| Conditional Skips (E2E) | 20+ | Working as Designed |
| Example/Template Tests | 1 | N/A |

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

### 3.1 Large Job List Performance Test

**File:** `tests/backend/test_api_jobs.py:782`

```python
@pytest.mark.skip(reason="Integration test - requires database seeding setup. Track in MASTERPLAN.md")
@pytest.mark.integration
def test_large_job_list_performance(self, client, db_connection):
```

**Status:** Needs Integration Test Infrastructure
**Priority:** Medium
**Root Cause:** Test requires pre-seeded database with 500+ jobs
**Implementation Notes:**
- Create a pytest fixture that seeds the database before tests
- Consider using a separate test database for integration tests
- Add `pytest.mark.integration` marker filtering in CI
- Files to modify:
  - `tests/conftest.py` - Add database seeding fixture
  - `.github/workflows/ci-cd.yml` - Add integration test job

---

### 3.2 Job Filtering Performance Test

**File:** `tests/backend/test_api_jobs.py:821`

```python
@pytest.mark.skip(reason="Integration test - requires database seeding setup. Track in MASTERPLAN.md")
@pytest.mark.integration
def test_job_filtering_performance(self, client, db_connection):
```

**Status:** Needs Integration Test Infrastructure
**Priority:** Medium
**Root Cause:** Same as 3.1 - requires seeded database
**Implementation Notes:** Same as 3.1

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

## Implementation Priorities

### High Priority (Should Fix Soon)
1. None currently - all skipped tests are either future features or working as designed

### Medium Priority (Next Sprint)
1. Download Progress Endpoint (Future Feature)
2. Integration Test Infrastructure (Database Seeding)

### Low Priority (Backlog)
1. File Cleanup Endpoint
2. Auto-Refresh Checkbox in debug.html
3. Thumbnail Log Limit Selector in debug.html
4. Database Connection Error Test Architecture

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
| `tests/backend/test_api_jobs.py` | 3 | Infrastructure |
| `tests/e2e/test_debug.py` | 5 | UI Missing |
| `tests/e2e/test_modals.py` | 7+ | Conditional (OK) |
| `tests/e2e/test_jobs.py` | 2 | Conditional (OK) |
| `tests/e2e/test_printers.py` | 5+ | Conditional (OK) |
| `tests/e2e/test_materials.py` | 4+ | Conditional (OK) |
| `tests/e2e/test_examples.py` | 1 | Example |
| `tests/integration/test_printer_interface_conformance.py` | 1 | Optional Dep |
