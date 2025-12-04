# Error Handling Consolidation Plan

**Status**: Ready to implement (Phase 1 Task 1.5)
**Estimated Effort**: 3-4 hours
**Priority**: High (completes Phase 1)

## Current State

Three overlapping error handling modules exist:

### 1. `/src/utils/errors.py` (834 lines) ✅ Keep as base
- **Base class**: `PrinternizerError`
- **Features**: FastAPI integrated, comprehensive, well-documented
- **Exception classes** (21+):
  - PrinterNotFoundError
  - PrinterConnectionError
  - PrinterBusyError
  - PrinterAlreadyExistsError
  - PrinterDisconnectedError
  - JobNotFoundError
  - JobAlreadyStartedError
  - JobInvalidStatusError
  - FileNotFoundError
  - FileDownloadError
  - InvalidFileTypeError
  - FileProcessingError
  - MaterialNotFoundError
  - InsufficientMaterialError
  - LibraryItemNotFoundError
  - ValidationError
  - ServiceUnavailableError
  - ConfigurationError
  - ResourceConflictError
  - NotFoundError
- **Used in**: 19+ files (mostly API routers)
- **Also exports**: `success_response()`, `error_response()` helper functions

### 2. `/src/utils/exceptions.py` (121 lines) ❌ Migrate & remove
- **Base class**: `PrinternizerException`
- **Exception classes** (9):
  - ConfigurationError *(duplicate of errors.py)*
  - DatabaseError *(unique - needs migration)*
  - PrinterConnectionError *(duplicate of errors.py)*
  - FileOperationError *(unique - needs migration)*
  - ValidationError *(duplicate of errors.py)*
  - AuthenticationError *(unique - needs migration)*
  - AuthorizationError *(unique - needs migration)*
  - NotFoundError *(duplicate of errors.py)*
- **Used in**: 9 files (services and printer implementations)
  - src/main.py
  - src/printers/prusa.py
  - src/printers/bambu_lab.py
  - src/printers/base.py
  - src/services/printer_control_service.py
  - src/services/file_service.py
  - src/services/printer_connection_service.py
  - src/services/printer_service.py
  - src/services/printer_monitoring_service.py

### 3. `/src/utils/error_handling.py` (408 lines) ⚠️ Partially migrate
- **Classes**:
  - `ErrorSeverity` (Enum) - Migrate to errors.py
  - `ErrorCategory` (Enum) - Migrate to errors.py
  - `ErrorHandler` (class) - Migrate to errors.py
  - `ErrorReportingMixin` - Migrate to errors.py
- **Used in**: 1 file only
  - src/services/monitoring_service.py (imports `error_handler`, `ErrorSeverity`)
- **Features**:
  - Structured error logging
  - File persistence for errors
  - Error statistics and reporting
  - Decorator functions

## Consolidation Strategy

### Phase 1: Prepare errors.py (30 minutes)

1. **Add unique classes from exceptions.py to errors.py**:
   - `DatabaseError` - Add to errors.py
   - `FileOperationError` - Check if can use existing `FileProcessingError` or add new
   - `AuthenticationError` - Add to errors.py
   - `AuthorizationError` - Add to errors.py

2. **Add error handling utilities from error_handling.py**:
   - Import `ErrorSeverity` enum
   - Import `ErrorCategory` enum
   - Import `ErrorHandler` class
   - Import `ErrorReportingMixin` class
   - Create global `error_handler` instance

3. **Add compatibility aliases** (temporary):
   ```python
   # Temporary aliases for smooth migration
   PrinternizerException = PrinternizerError  # Base class alias
   ```

### Phase 2: Update imports - exceptions.py users (1.5 hours)

Update the 9 files importing from `exceptions.py`:

**Files to update**:
```python
# FROM:
from src.utils.exceptions import PrinternizerException, PrinterConnectionError, NotFoundError

# TO:
from src.utils.errors import PrinternizerError as PrinternizerException, PrinterConnectionError, NotFoundError
```

**Update list**:
1. ✅ src/main.py - `PrinternizerException`
2. ✅ src/printers/prusa.py - `PrinterConnectionError`
3. ✅ src/printers/bambu_lab.py - `PrinterConnectionError`
4. ✅ src/printers/base.py - `PrinterConnectionError`
5. ✅ src/services/printer_control_service.py - `PrinterConnectionError`, `NotFoundError`
6. ✅ src/services/file_service.py - `NotFoundError`
7. ✅ src/services/printer_connection_service.py - `PrinterConnectionError`, `NotFoundError`
8. ✅ src/services/printer_service.py - `PrinterConnectionError`, `NotFoundError`
9. ✅ src/services/printer_monitoring_service.py - `NotFoundError`

### Phase 3: Update imports - error_handling.py users (30 minutes)

Update monitoring_service.py:

```python
# FROM:
from src.utils.error_handling import error_handler, ErrorSeverity

# TO:
from src.utils.errors import error_handler, ErrorSeverity
```

**File to update**:
1. ✅ src/services/monitoring_service.py

### Phase 4: Testing (30 minutes)

1. **Run test suite**:
   ```bash
   pytest tests/ -v
   pytest tests/ --cov=src
   ```

2. **Test error handling**:
   - API error responses
   - Service exception handling
   - Printer connection errors
   - Error logging

3. **Integration tests**:
   - Start application
   - Test error scenarios
   - Verify error responses
   - Check error logging

### Phase 5: Cleanup (30 minutes)

1. **Remove old modules**:
   ```bash
   git rm src/utils/exceptions.py
   git rm src/utils/error_handling.py
   ```

2. **Update any documentation**:
   - Check for references in docs/
   - Update ERROR_HANDLING_AUDIT.md if exists
   - Update CLAUDE.md if needed

3. **Remove compatibility aliases**:
   - Remove `PrinternizerException = PrinternizerError` from errors.py
   - Do final search for any remaining references

## Implementation Checklist

### Preparation
- [ ] Read all three modules completely
- [ ] Create backup branch
- [ ] Document all unique classes and functions

### Migration
- [ ] Add unique exception classes to errors.py
- [ ] Add ErrorSeverity enum to errors.py
- [ ] Add ErrorCategory enum to errors.py
- [ ] Add ErrorHandler class to errors.py
- [ ] Add ErrorReportingMixin to errors.py
- [ ] Create error_handler instance in errors.py
- [ ] Add temporary compatibility aliases

### Update Imports - exceptions.py (9 files)
- [ ] src/main.py
- [ ] src/printers/prusa.py
- [ ] src/printers/bambu_lab.py
- [ ] src/printers/base.py
- [ ] src/services/printer_control_service.py
- [ ] src/services/file_service.py
- [ ] src/services/printer_connection_service.py
- [ ] src/services/printer_service.py
- [ ] src/services/printer_monitoring_service.py

### Update Imports - error_handling.py (1 file)
- [ ] src/services/monitoring_service.py

### Testing
- [ ] Run pytest suite
- [ ] Test API error responses
- [ ] Test service exceptions
- [ ] Test printer errors
- [ ] Test error logging
- [ ] Integration testing

### Cleanup
- [ ] Delete src/utils/exceptions.py
- [ ] Delete src/utils/error_handling.py
- [ ] Remove compatibility aliases
- [ ] Update documentation
- [ ] Final grep for old imports

### Verification
- [ ] No imports from exceptions.py
- [ ] No imports from error_handling.py
- [ ] All tests passing
- [ ] Error handling behavior unchanged
- [ ] Git commit with staged changes

## Expected Benefits

1. **Reduced confusion** - Single error handling module
2. **Improved maintainability** - One place to update
3. **Consistent patterns** - All errors follow same structure
4. **Better FastAPI integration** - All errors work with exception handlers
5. **Cleaner codebase** - ~1500 lines reduced to ~1200 in single file

## Rollback Plan

If issues arise:

1. **Revert last commits**:
   ```bash
   git log --oneline  # Find commit hash
   git revert <commit-hash>
   ```

2. **Restore old files** from git history if needed

3. **All changes are in git** - Safe to experiment

## Notes

- **Duplicates resolved**: errors.py versions are more comprehensive
- **API consistency**: errors.py classes are FastAPI-integrated
- **Minimal changes**: Using aliases minimizes code changes
- **Backward compatible**: Can keep aliases temporarily during migration

## Success Criteria

✅ All tests pass
✅ No remaining imports from old modules
✅ Error handling behavior unchanged
✅ All exception types available from errors.py
✅ Error logging still works
✅ API error responses consistent

---

**Ready to implement**: This plan provides step-by-step instructions for completing Phase 1 Task 1.5.
