# CI/CD Test Fix Plan - Remaining Work

**Status:** Partially Complete (5/5 targeted tests passing, ~164 issues remaining)
**Date Created:** 2025-11-11
**Last Updated:** 2025-11-11

## Executive Summary

The CI/CD pipeline environment configuration issues have been **resolved** (environment variable, branch triggers, AsyncMock setup). However, **test failures remain** due to incorrect module import paths throughout the test suite.

**Current State:**
- ✅ CI/CD workflow configuration fixed
- ✅ AsyncMock properly configured in conftest.py
- ✅ 5 file API tests passing (endpoint URLs corrected)
- ❌ ~164 incorrect `backend.*` imports across 8 test files
- ❌ Pipeline fails at `--maxfail=5` (stops after 5 failures)

---

## Completed Work (Session 1)

### ✅ What We Fixed

1. **Environment Variable Validation**
   - Changed `ENVIRONMENT: test` → `ENVIRONMENT: testing` in workflow
   - Changed conftest.py mock from `"test"` → `"testing"`
   - Matches validation in [src/utils/config.py:351](src/utils/config.py#L351)

2. **AsyncMock Configuration**
   - Fixed `file_service` async methods in [tests/conftest.py:732-744](tests/conftest.py#L732-L744)
   - Fixed `config_service` async methods in [tests/conftest.py:719-722](tests/conftest.py#L719-L722)
   - All service methods now use `AsyncMock` instead of `MagicMock`

3. **API Endpoint URLs**
   - Fixed `/api/v1/files/unified` → `/api/v1/files` in test_api_files.py
   - 5 tests now passing locally and in CI

4. **Workflow Resilience**
   - Removed deprecated `actions/create-release@v1`
   - Added conditional checks for optional K8s files
   - Added conditional checks for performance tests
   - Added `master` branch to workflow triggers

### 📦 Commits Pushed

1. **78b2512** - `fix(ci): Fix CI/CD pipeline failures and enhance deployment resilience`
2. **f9ae5d4** - `fix(ci): Add master branch to CI/CD workflow triggers`
3. **348009a** - `fix(tests): Fix test mock configuration and API endpoint URLs`

---

## Problem Analysis

### Issue Overview

**Root Cause:** Tests were written using `backend.*` module paths, but the actual project uses `src.*` structure.

**Scope:**
- **8 test files affected**
- **~169 incorrect import references**
- **Current failure:** `ModuleNotFoundError: No module named 'backend'`

### Files Requiring Fixes

| File | Wrong Imports | Status |
|------|---------------|--------|
| `test_api_files.py` | 12 occurrences | 5 tests passing, 5+ failing |
| `test_api_jobs.py` | 16 occurrences | Not tested yet |
| `test_api_printers.py` | 1+ occurrences | Not tested yet |
| `test_end_to_end.py` | Unknown | Not analyzed |
| `test_error_handling.py` | Unknown | Not analyzed |
| `test_german_business.py` | Unknown | Not analyzed |
| `test_integration.py` | Unknown | Not analyzed |
| `test_performance.py` | Unknown | Not analyzed |

---

## Detailed Fix Plan

### Phase 1: Module Import Corrections

#### Pattern Recognition

**Incorrect Patterns → Correct Patterns:**

```python
# Database imports
'backend.database.get_connection' → 'src.database.database.Database.get_connection'

# Printer imports (VERIFY CLASS NAMES FIRST!)
'backend.printers.bambu.BambuLabAPI' → 'src.printers.bambu_lab.BambuLabPrinter' (?)
'backend.printers.prusa.PrusaLinkAPI' → 'src.printers.prusa.PrusaPrinter' (?)

# File/service imports (these may not exist as standalone)
'backend.files.*' → Remove or mock at service level
'backend.printers.get_printer_api' → Mock via file_service instead
```

#### Critical: Verify Actual Structure First

Before mass-replacing, run these checks:

```bash
# Check printer class names
grep "^class " src/printers/bambu_lab.py
grep "^class " src/printers/prusa.py

# Check what FileService actually exposes
grep "def " src/services/file_service.py | grep -E "(download|delete|cleanup)"

# Check if these helper functions exist
grep -r "def get_download_directory" src/
grep -r "def check_disk_space" src/
grep -r "def get_local_file_path" src/
```

**Expected Result:** Most `backend.files.*` helpers don't exist - tests need refactoring, not just import fixes.

---

### Phase 2: Test Refactoring Strategy

#### Problem: Over-Mocking Internal Implementation

Many tests mock implementation details that don't exist or shouldn't be exposed:

**Non-Existent Functions Being Mocked:**
- `backend.files.get_download_directory()`
- `backend.files.check_disk_space()`
- `backend.files.get_local_file_path()`
- `backend.files.get_download_progress()`
- `backend.files.cleanup_old_files()`

**Options:**

**Option A (Recommended): Simplify Test Strategy**
- Remove deep implementation mocks
- Test through public API (FileService methods only)
- Accept that some edge cases need different test approaches

**Option B: Create Missing Utilities**
- Implement these as actual utility functions if valuable
- Update tests to use correct paths

**Option C: Mock at Correct Internal Level**
- Mock within FileService implementation
- More brittle, harder to maintain

---

### Phase 3: Implementation Steps

#### Step 1: Create Import Mapping (15 min)

```bash
# Generate complete inventory
cd tests/backend
grep -rn "backend\." . > /tmp/backend_imports.txt

# Analyze patterns
cat /tmp/backend_imports.txt | cut -d: -f3 | sort | uniq -c | sort -rn
```

Create `IMPORT_MAPPING.md` with complete before/after table.

#### Step 2: Fix test_api_files.py (20 min)

**File:** [tests/backend/test_api_files.py](tests/backend/test_api_files.py)

**Changes Required:**

1. **Line 94:** `'backend.printers.bambu.BambuLabAPI'` → Verify actual class name, update
2. **Line 97:** `'backend.files.get_download_directory'` → Remove or refactor test
3. **Line 121:** `'backend.printers.prusa.PrusaLinkAPI'` → Verify actual class name, update
4. **Line 124:** `'backend.files.get_download_directory'` → Remove or refactor test
5. **Line 154:** `'backend.printers.get_printer_api'` → Remove or mock file_service method
6. **Lines 170, 195:** Same as above
7. **Lines 174, 220, 246, 288:** Remove or refactor helper function mocks

**Test Command:**
```bash
pytest tests/backend/test_api_files.py -v --maxfail=20
```

#### Step 3: Fix test_api_jobs.py (10 min)

**File:** [tests/backend/test_api_jobs.py](tests/backend/test_api_jobs.py)

Simple find/replace (all 16 occurrences):
```python
'backend.database.get_connection' → 'src.database.database.Database.get_connection'
```

**Test Command:**
```bash
pytest tests/backend/test_api_jobs.py -v
```

#### Step 4: Fix test_api_printers.py (15 min)

**File:** [tests/backend/test_api_printers.py](tests/backend/test_api_printers.py)

**Changes Required:**
- Line 188: Update printer class import
- Verify printer API structure matches test expectations

#### Step 5: Fix Remaining Files (45 min)

Apply same patterns to:
- `test_end_to_end.py`
- `test_error_handling.py`
- `test_german_business.py`
- `test_integration.py`
- `test_performance.py`

#### Step 6: Update conftest.py If Needed (10 min)

Check if any fixtures need updating:
- `mock_bambu_api` - verify structure
- `mock_prusa_api` - verify structure
- `populated_database` - verify schema

#### Step 7: Full Test Run (30 min)

```bash
# Remove maxfail to see all issues
pytest tests/backend/ -v --maxfail=50 -x

# Once passing, run full suite
pytest tests/backend/ -v

# Check coverage
pytest tests/backend/ --cov=src --cov-report=html
```

---

## Alternative: Quick Fix Approach

If pressed for time, consider this tactical approach:

### Option: Skip Problematic Tests Temporarily

Add skip markers to failing tests while fixing systematically:

```python
import pytest

@pytest.mark.skip(reason="Needs module path fix - tracked in CI_CD_TEST_FIX_PLAN.md")
def test_post_file_download_bambu_lab(...):
    ...
```

**Pros:**
- Unblocks CI/CD pipeline immediately
- Can fix systematically over time
- Documents what needs work

**Cons:**
- Reduces test coverage
- Easy to forget to re-enable
- Masks real issues

---

## Success Criteria

### Definition of Done

- [ ] All `backend.*` imports replaced with `src.*` or removed
- [ ] Zero `ModuleNotFoundError: No module named 'backend'` errors
- [ ] Zero `AttributeError: 'NoneType' object` from incorrect mocks
- [ ] All tests in `tests/backend/` pass locally
- [ ] CI/CD pipeline fully green (no `--maxfail` needed)
- [ ] Test coverage maintained or improved

### Validation Commands

```bash
# Local validation
pytest tests/backend/ -v
pytest tests/backend/ --cov=src --cov-report=term-missing

# Check for remaining backend imports
grep -r "backend\." tests/backend/ || echo "All fixed!"

# Verify CI/CD
git push origin master
gh run watch --repo schmacka/printernizer
```

---

## Risk Assessment

### High Risk Areas

1. **Printer Class Names**
   - Tests assume `BambuLabAPI` and `PrusaLinkAPI`
   - Actual classes might be `BambuLabPrinter` and `PrusaPrinter`
   - **Mitigation:** Check actual class names before replacing

2. **Non-Existent Helper Functions**
   - Many `backend.files.*` functions don't exist
   - Tests might break when mocks removed
   - **Mitigation:** Refactor tests to use FileService API

3. **FileService API Changes**
   - Tests expect certain method signatures
   - Actual API might differ
   - **Mitigation:** Check FileService implementation, update mocks

4. **Circular Import Issues**
   - Mocking at wrong level can cause circular imports
   - **Mitigation:** Mock at dependency injection level, not import level

### Estimated Effort

| Phase | Time | Complexity |
|-------|------|------------|
| Analysis & Planning | 15 min | Low |
| test_api_files.py | 20 min | Medium |
| test_api_jobs.py | 10 min | Low |
| test_api_printers.py | 15 min | Medium |
| Remaining 5 files | 45 min | Medium |
| Testing & Debugging | 30 min | High |
| **Total** | **~2.5 hours** | **Medium** |

---

## Resources

### Key Files

- **Workflow:** [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml)
- **Test Config:** [tests/conftest.py](tests/conftest.py)
- **Main Test:** [tests/backend/test_api_files.py](tests/backend/test_api_files.py)
- **Config Validation:** [src/utils/config.py:351](src/utils/config.py#L351)
- **FileService:** [src/services/file_service.py](src/services/file_service.py)

### Recent CI/CD Runs

- **Latest:** https://github.com/schmacka/printernizer/actions/runs/19268823943
- **Result:** Failure (5 passed, 5 failed at --maxfail=5)

### Commands

```bash
# Run specific test file
pytest tests/backend/test_api_files.py -v

# Run with more failures shown
pytest tests/backend/ -v --maxfail=20

# Find all backend imports
grep -rn "backend\." tests/backend/

# Count occurrences
grep -r "backend\." tests/backend/ | wc -l

# Watch CI/CD
gh run watch --repo schmacka/printernizer --exit-status
```

---

## Next Session Prompt

Use this prompt to continue:

```
I'm continuing work on fixing the Printernizer CI/CD test failures.

**Context:**
- Previous session fixed CI/CD workflow config issues (environment vars, AsyncMock, branch triggers)
- 5 tests now passing in test_api_files.py, but ~164 incorrect `backend.*` imports remain across 8 test files
- Current CI/CD failure: ModuleNotFoundError: No module named 'backend'
- Full plan documented in: CI_CD_TEST_FIX_PLAN.md

**Current Status:**
- ✅ Workflow configuration fixed
- ✅ AsyncMock setup correct
- ✅ 5/5 targeted tests passing
- ❌ Need to replace all `backend.*` → `src.*` imports
- ❌ Need to verify printer class names
- ❌ Need to refactor tests mocking non-existent helper functions

**Next Steps:**
1. Verify actual class names in src/printers/bambu_lab.py and src/printers/prusa.py
2. Fix remaining import errors in test_api_files.py (lines 94, 97, 121, 124, 154, 170, 174, 195, 220, 246, 288)
3. Apply same fixes to test_api_jobs.py (16 occurrences) and remaining 6 test files

**Goal:** Get all backend tests passing and CI/CD pipeline green.

Please continue from Step 1 in Phase 3 of the plan: verify printer class names and start fixing test_api_files.py
```

---

## Notes

- Original issue: https://github.com/schmacka/printernizer/blob/master/.github/workflows/ci-cd.yml
- Test failure logs show clear pattern: all failing tests mock `backend.*` modules
- The 5 passing tests use `src.*` imports correctly
- Project follows standard Python package structure with `src/` as root
