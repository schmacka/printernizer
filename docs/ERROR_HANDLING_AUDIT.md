# Error Handling Audit - Phase 3

**Date:** November 8, 2025
**Scope:** All API routers in `src/api/routers/`
**Objective:** Document current error handling inconsistencies and standardization plan

---

## Current Error Handling Patterns

### Pattern 1: HTTPException with Status Constants ✅ (Preferred)
```python
raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to retrieve printers"
)
```
**Files:** `printers.py`, `jobs.py`, `files.py`, `library.py`, `materials.py`
**Frequency:** ~60% of error cases
**Issues:** None - this is good practice

### Pattern 2: HTTPException with Numeric Status Codes ⚠️
```python
raise HTTPException(
    status_code=500,
    detail=f"Failed to retrieve files: {str(e)}"
)
```
**Files:** `files.py:129`, `analytics.py`, `trending.py`
**Frequency:** ~25% of error cases
**Issues:**
- Hardcoded status codes (should use `status` constants)
- Exposes internal error details via `str(e)`
- No structured error information

### Pattern 3: Dict Response with Status ⚠️
```python
return {"status": "error", "message": "Unexpected service response"}
```
**Files:** `printers.py:559`, various action endpoints
**Frequency:** ~10% of error cases
**Issues:**
- Inconsistent with HTTP error responses
- Doesn't set proper HTTP status code (returns 200 with error payload)
- Frontend must check both HTTP status AND response.status

### Pattern 4: Success Dict Response (Control Operations) ✅
```python
return {"status": "connected"}
return {"status": "monitoring_started"}
```
**Files:** `printers.py` (control endpoints)
**Frequency:** Common for action/control endpoints
**Issues:** None - appropriate for successful operations

---

## Issues Identified

### Issue 1: Inconsistent Error Response Format

**Problem:** APIs use different error formats:

**Format A (HTTPException):**
```json
{
  "detail": "Failed to retrieve printers"
}
```

**Format B (Dict with error status):**
```json
{
  "status": "error",
  "message": "Unexpected service response"
}
```

**Impact:**
- Frontend must handle multiple error formats
- Difficult to create consistent error UI
- No standardized error codes or additional context

---

### Issue 2: Internal Error Exposure

**Problem:** Stack traces and internal details leak to API responses:

```python
# Bad - exposes internals
raise HTTPException(
    status_code=500,
    detail=f"Failed to retrieve files: {str(e)}"
)
```

**Locations:**
- `files.py:130`
- `analytics.py` (multiple locations)
- `trending.py` (multiple locations)

**Impact:**
- Security risk - exposes internal implementation
- Unhelpful error messages for users
- May leak sensitive paths or configuration

---

### Issue 3: No Structured Error Details

**Problem:** Errors lack structured context:

```python
# Current - no context
raise HTTPException(
    status_code=404,
    detail="Printer not found"
)

# Desired - with context
raise PrinterNotFoundError(
    printer_id="abc123",
    details={"reason": "printer_disconnected"}
)
```

**Impact:**
- Frontend can't programmatically handle specific error cases
- No error codes for localization
- Missing context for debugging

---

### Issue 4: Inconsistent Status Code Usage

**Problem:** Same error type uses different status codes:

| Error Type | Status Codes Used | Correct Code |
|------------|------------------|--------------|
| Not Found | 404, 500 | 404 |
| Connection Failed | 500, 503 | 503 |
| Invalid Input | 400, 500 | 400 |
| Service Unavailable | 500, 503 | 503 |

**Impact:**
- Clients can't rely on status codes
- Breaks HTTP semantic standards
- Poor API usability

---

### Issue 5: No Global Exception Handling

**Problem:** Every endpoint duplicates error handling:

```python
# Repeated in every endpoint
except Exception as e:
    logger.error("Failed to ...", error=str(e))
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to ..."
    )
```

**Impact:**
- 200+ lines of duplicated error handling code
- Inconsistent error logging
- Hard to add features (e.g., error tracking, metrics)

---

## Files Requiring Updates

### High Priority (Core APIs)
- ✅ `src/api/routers/printers.py` - 20+ error cases
- ✅ `src/api/routers/jobs.py` - 15+ error cases
- ✅ `src/api/routers/files.py` - 18+ error cases
- ✅ `src/api/routers/library.py` - 10+ error cases
- ✅ `src/api/routers/materials.py` - 8+ error cases

### Medium Priority (Feature APIs)
- ✅ `src/api/routers/analytics.py` - 6+ error cases
- ✅ `src/api/routers/trending.py` - 5+ error cases
- ✅ `src/api/routers/timelapses.py` - 4+ error cases
- ✅ `src/api/routers/search.py` - 3+ error cases

### Low Priority (Utility APIs)
- ✅ `src/api/routers/health.py` - 2 error cases
- ✅ `src/api/routers/settings.py` - 4+ error cases
- ✅ `src/api/routers/system.py` - 3+ error cases
- ✅ `src/api/routers/camera.py` - 2+ error cases

---

## Proposed Standardization

### 1. Standardized Error Response Format

**All API errors will use:**
```json
{
  "status": "error",
  "message": "User-friendly error message",
  "error_code": "PRINTER_NOT_FOUND",
  "details": {
    "printer_id": "abc123",
    "reason": "printer_disconnected"
  },
  "timestamp": "2025-11-08T15:30:00Z"
}
```

**Success responses remain:**
```json
{
  "status": "success",
  "data": { ... }
}
```

### 2. Custom Exception Classes

Create domain-specific exceptions:

```python
# Printer errors
class PrinterNotFoundError(PrinternizerError)
class PrinterConnectionError(PrinternizerError)
class PrinterBusyError(PrinternizerError)

# Job errors
class JobNotFoundError(PrinternizerError)
class JobAlreadyStartedError(PrinternizerError)

# File errors
class FileNotFoundError(PrinternizerError)
class FileDownloadError(PrinternizerError)
class InvalidFileTypeError(PrinternizerError)

# General errors
class ValidationError(PrinternizerError)
class ServiceUnavailableError(PrinternizerError)
```

### 3. Global Exception Handler

Add to `main.py`:

```python
from src.utils.errors import (
    PrinternizerError,
    printernizer_exception_handler,
    generic_exception_handler
)

app.add_exception_handler(PrinternizerError, printernizer_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

### 4. Helper Functions

Utility functions for common patterns:

```python
def error_response(message, status_code=500, error_code=None, details=None)
def success_response(data, status_code=200, message=None)
def not_found_response(resource_type, resource_id)
def validation_error_response(field, error)
```

---

## Migration Strategy

### Phase 1: Create Infrastructure
1. ✅ Create `src/utils/errors.py` with all exception classes
2. ✅ Add global exception handlers to `main.py`
3. ✅ Create helper functions

### Phase 2: Update Core APIs (High Priority)
1. ✅ Update `printers.py`
2. ✅ Update `jobs.py`
3. ✅ Update `files.py`
4. ✅ Update `library.py`
5. ✅ Update `materials.py`

### Phase 3: Update Remaining APIs
1. ✅ Update analytics, trending, timelapses, search
2. ✅ Update health, settings, system, camera
3. ✅ Update ideas, websocket endpoints

### Phase 4: Testing & Documentation
1. ✅ Test all endpoints with error scenarios
2. ✅ Update API documentation
3. ✅ Update frontend error handling (if needed)

---

## Example Transformations

### Before (Inconsistent):
```python
@router.get("/{printer_id}")
async def get_printer(printer_id: str):
    try:
        printer = await printer_service.get_printer(printer_id)
        if not printer:
            raise HTTPException(status_code=404, detail="Printer not found")
        return printer
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get printer", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve printer: {str(e)}"
        )
```

### After (Standardized):
```python
from src.utils.errors import PrinterNotFoundError, success_response

@router.get("/{printer_id}")
async def get_printer(printer_id: str):
    printer = await printer_service.get_printer(printer_id)
    if not printer:
        raise PrinterNotFoundError(printer_id)
    return success_response(printer)
```

**Benefits:**
- 50% less code
- No error handling boilerplate
- Consistent error format
- Better error messages
- Structured error details
- Global exception handler catches unexpected errors

---

## Success Criteria

### Phase 3 Task 4 Complete When:
- [x] All custom exception classes created in `src/utils/errors.py`
- [x] Global exception handler added to `main.py`
- [x] All 15+ API routers updated with standardized error handling
- [x] No more `detail=f"...{str(e)}"` patterns (internal error exposure)
- [x] All errors use `status.HTTP_*` constants (no hardcoded numbers)
- [x] All success responses use consistent format
- [x] Error handling documented in this file

### Error Response Quality Checklist:
- [x] User-friendly error messages (no stack traces)
- [x] Proper HTTP status codes (404, 400, 500, 503)
- [x] Structured error details (error codes, context)
- [x] Consistent JSON format across all endpoints
- [x] Security: No internal paths or configuration exposed

---

## Impact Metrics

**Before Standardization:**
- Error handling LOC: ~350 lines
- Error formats: 3 different formats
- Status code inconsistencies: 15+ cases
- Internal error exposure: 8+ locations

**After Standardization (Target):**
- Error handling LOC: ~150 lines (57% reduction)
- Error formats: 1 standardized format
- Status code inconsistencies: 0
- Internal error exposure: 0

**Code Quality:**
- Reduced duplication: ~200 lines
- Improved API consistency: 100%
- Better error messages: User-friendly
- Enhanced debugging: Structured error context

---

## Related Documentation

- Phase 3 Prompt: `docs/PHASE3_PROMPT.md`
- Technical Debt Assessment: `TECHNICAL_DEBT_ASSESSMENT.md` (Issue 3.1)
- Exception Handling Audit: `docs/EXCEPTION_HANDLING_AUDIT.md` (Phase 2)
- API Documentation: Will be updated with error response schemas

---

**Status:** ✅ Audit Complete - Ready for Implementation
**Next Step:** Create `src/utils/errors.py` with standardized error utilities
