# Deprecation Timeline

This document tracks deprecated features, methods, and code that will be removed in future versions.

**Last Updated**: 2025-12-04

---

## Active Deprecations

### 1. Deprecated Printer Service Methods

**Location**: `src/services/printer_service.py`

**Deprecated Method**: `get_printers()` (lines 185-201)

**Status**: ⚠️ Deprecated in v2.7.0

**Reason**: Superseded by more specific methods with better typing

**Replacement**: Use domain-specific methods:
- `get_all_printers()` - Get all printers
- `get_active_printers()` - Get only active printers
- `get_printer(printer_id)` - Get specific printer

**Removal Target**: v3.0.0

**Migration Guide**:
```python
# OLD (deprecated)
printers = await printer_service.get_printers()

# NEW (recommended)
printers = await printer_service.get_all_printers()
# or for active only:
printers = await printer_service.get_active_printers()
```

---

### 2. Deprecated Camera Stream URL Method

**Location**: `src/printers/bambu_lab.py`

**Deprecated Method**: `get_camera_stream_url()` (line 1757)

**Status**: ⚠️ Deprecated

**Reason**: Camera access has been refactored to use snapshot-based approach

**Replacement**: Use `SnapshotService` for camera functionality

**Removal Target**: v3.0.0

**Migration Guide**:
```python
# OLD (deprecated)
url = printer.get_camera_stream_url()

# NEW (recommended)
from src.services.snapshot_service import SnapshotService
snapshot = await snapshot_service.capture_snapshot(printer_id)
```

---

### 3. Legacy Exception Handlers

**Location**: `src/main.py`

**Deprecated Code**: Legacy exception handlers (lines 730-734)

**Status**: ⚠️ Deprecated

**Reason**: Maintained for backward compatibility during error handling consolidation

**Replacement**: All errors now use consolidated `src.utils.errors` module

**Removal Target**: v3.0.0

**Note**: This is an internal implementation detail. No user action required.

---

## Removal Schedule

### Version 3.0.0 (Breaking Changes)

**Target Release**: Q2 2026 (tentative)

**Changes Planned**:
- Remove `printer_service.get_printers()` method
- Remove `bambu_lab.get_camera_stream_url()` method
- Remove legacy exception handlers from main.py
- Possibly remove `PrinternizerException` alias (if analysis shows safe)

**Pre-Release Actions**:
1. Audit all internal code for deprecated usage
2. Update all documentation
3. Add prominent deprecation warnings in v2.9.0
4. Create migration guide
5. Announce in changelog and GitHub discussions

---

## Completed Migrations

### Error Handling Consolidation (Completed 2025-12-04)

**What Changed**:
- Consolidated 3 error modules into single `src/utils/errors.py`
- Removed `src/utils/exceptions.py`
- Removed `src/utils/error_handling.py`

**Backward Compatibility**:
- `PrinternizerException` alias maintained for `PrinternizerError`
- All exception signatures unchanged
- No breaking changes to existing code

**Status**: ✅ Complete

---

## Deprecation Policy

### When to Deprecate

Features, methods, or APIs should be deprecated when:
1. ✅ A better alternative exists
2. ✅ The code is no longer maintained
3. ✅ Security or performance issues cannot be fixed without breaking changes
4. ✅ The feature is rarely used and adds maintenance burden

### Deprecation Process

1. **Mark as Deprecated** (Current Minor Version)
   - Add `DeprecationWarning` to the code
   - Add docstring note: `@deprecated: Use X instead. Will be removed in vX.0.0`
   - Update documentation

2. **Announce Deprecation** (Current Minor Version)
   - Add to CHANGELOG under "Deprecated" section
   - Update API documentation
   - Notify users via GitHub Discussions/Release Notes

3. **Grace Period** (At least 2 minor versions or 6 months)
   - Allow time for users to migrate
   - Provide migration guides and examples
   - Answer questions and provide support

4. **Remove in Major Version** (Next Major Version)
   - Remove deprecated code
   - Update all documentation
   - Create migration guide
   - Announce breaking changes prominently

### Example Timeline

```
v2.7.0 - Feature deprecated, warnings added
v2.8.0 - Continued warnings
v2.9.0 - Final warnings with removal notice
v3.0.0 - Feature removed (breaking change)
```

---

## Deprecation Warnings

### Adding a Deprecation Warning

```python
import warnings

def deprecated_function():
    """Old function that will be removed.

    .. deprecated:: 2.7.0
        Use :func:`new_function` instead.
        Will be removed in version 3.0.0.
    """
    warnings.warn(
        "deprecated_function() is deprecated and will be removed in v3.0.0. "
        "Use new_function() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Function implementation
```

### For Methods

```python
class MyService:
    def old_method(self):
        """
        .. deprecated:: 2.7.0
            Use :meth:`new_method` instead.
        """
        warnings.warn(
            "old_method() is deprecated. Use new_method() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.new_method()
```

---

## Version Planning

### v2.8.0 (Next Minor Release)
- No new deprecations planned
- Continue existing deprecation warnings

### v2.9.0 (Pre-Major Release)
- Add final deprecation warnings
- Create comprehensive migration guide for v3.0.0
- Announce v3.0.0 timeline

### v3.0.0 (Next Major Release)
- Remove all deprecated code listed above
- Clean up backward compatibility layers
- Update all documentation
- Provide detailed upgrade guide

---

## Resources

- **Changelog**: See CHANGELOG.md for version-specific deprecation notices
- **Migration Guides**: See docs/migrations/ for detailed upgrade instructions
- **API Documentation**: Generated from docstrings with deprecation notes
- **GitHub Discussions**: Community support for migrations

---

## Contact

For questions about deprecations or migration assistance:
- GitHub Issues: For bugs or migration problems
- GitHub Discussions: For general questions
- Documentation: Check docs/ for guides and examples

---

**Note**: This timeline is subject to change based on community feedback and project needs. Major version releases will be announced well in advance.
