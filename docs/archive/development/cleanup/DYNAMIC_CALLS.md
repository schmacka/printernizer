# Dynamic Function Calls Documentation

**Date**: 2025-10-04
**Purpose**: Document files using dynamic call patterns that may hide function usage from static analysis
**Impact**: 16 files identified with patterns like `getattr()`, `globals()`, `locals()`, etc.

---

## Overview

Static analysis cannot reliably detect function calls made through dynamic dispatch patterns. This document catalogs all files using such patterns to prevent accidental removal of "seemingly unused" functions that are actually called dynamically.

### Patterns Detected

- **`getattr()`** - Dynamic attribute access
- **`setattr()`** - Dynamic attribute modification
- **`globals()` / `locals()`** - Namespace dictionary access
- **`__import__()`** - Dynamic module imports
- **`importlib`** - Dynamic import library usage

### Files with Dynamic Calls (16 total)

| File | Patterns | Lines | Risk Level | Notes |
|------|----------|-------|------------|-------|
| `scripts/test_complete_bambu_ftp.py` | getattr | Multiple | LOW | Test utilities |
| `scripts/verify_bambu_download.py` | getattr | Multiple | LOW | Verification script |
| `src/api/routers/debug.py` | getattr, globals | Multiple | MEDIUM | Debug endpoints |
| `src/api/routers/health.py` | getattr | Multiple | LOW | Health checks |
| `src/api/routers/printers.py` | getattr | Multiple | LOW | Printer status |
| `src/api/routers/trending.py` | getattr | Multiple | LOW | Trending data |
| `src/printers/bambu_lab.py` | getattr | Multiple | MEDIUM | Printer driver |
| `src/services/config_service.py` | getattr, setattr | Multiple | HIGH | Configuration |
| `src/services/library_service.py` | getattr | Multiple | MEDIUM | Library management |
| `src/services/material_service.py` | getattr | Multiple | MEDIUM | Material tracking |
| `src/services/printer_service.py` | getattr | Multiple | HIGH | Core printer service |
| `src/services/thumbnail_service.py` | getattr | Multiple | LOW | Thumbnail processing |
| `src/utils/error_handling.py` | globals | Multiple | LOW | Error utilities |
| `src/utils/logging_config.py` | globals | Multiple | LOW | Logging setup |
| `tests/run_milestone_1_2_tests.py` | getattr | Multiple | LOW | Test runner |
| `tests/test_printer_interface_conformance.py` | getattr | Multiple | LOW | Interface tests |

---

## Detailed Analysis

### High-Risk Files (Review Before Any Changes)

#### 1. `src/services/config_service.py`
**Patterns**: `getattr`, `setattr`
**Usage**: Dynamic configuration access and modification

**Example Dynamic Calls**:
```python
# Dynamic attribute access
value = getattr(config_obj, attr_name, default)

# Dynamic attribute setting
setattr(config_obj, attr_name, value)
```

**Impact**: Configuration values accessed dynamically
**Action**: Do NOT remove any config-related functions without verifying dynamic usage

---

#### 2. `src/services/printer_service.py`
**Patterns**: `getattr`
**Usage**: Dynamic printer attribute access

**Impact**: Printer state and methods may be called dynamically
**Action**: Verify all printer-related functions before removal

---

### Medium-Risk Files

#### 3. `src/printers/bambu_lab.py`
**Patterns**: `getattr`
**Usage**: Bambu printer status parsing

**Impact**: Status fields accessed dynamically from API responses
**Action**: Review before removing any status-related functions

---

#### 4. `src/api/routers/debug.py`
**Patterns**: `getattr`, `globals`
**Usage**: Debug introspection

**Impact**: Debug endpoints may call functions dynamically
**Action**: Keep all debug functions even if they appear unused

---

#### 5. `src/services/library_service.py`
**Patterns**: `getattr`
**Usage**: Library file attribute access

**Impact**: Library metadata accessed dynamically
**Action**: Review library-related functions carefully

---

#### 6. `src/services/material_service.py`
**Patterns**: `getattr`
**Usage**: Material property access

**Impact**: Material fields accessed dynamically
**Action**: Verify material functions before removal

---

### Low-Risk Files

#### Test Files (4 files)
- `scripts/test_complete_bambu_ftp.py`
- `scripts/verify_bambu_download.py`
- `tests/run_milestone_1_2_tests.py`
- `tests/test_printer_interface_conformance.py`

**Usage**: Dynamic test execution, interface verification
**Impact**: Test-only, safe to modify
**Action**: Low risk for cleanup

---

#### API Routers (3 files)
- `src/api/routers/health.py`
- `src/api/routers/printers.py`
- `src/api/routers/trending.py`

**Usage**: Status aggregation, dynamic field access
**Impact**: API endpoints already whitelisted
**Action**: Review but generally safe

---

#### Utilities (2 files)
- `src/utils/error_handling.py` - Error logging with `globals()`
- `src/utils/logging_config.py` - Logger configuration with `globals()`

**Usage**: Python introspection for debugging
**Impact**: Minimal
**Action**: Safe to modify

---

## Recommendations

### Before Removing "Unused" Functions

1. **Check this list** - Is the function in a file with dynamic calls?
2. **Search for dynamic patterns**:
   ```bash
   grep -n "getattr.*function_name" <file>
   grep -n "globals().*function_name" <file>
   ```
3. **Review file context** - Understand why dynamic calls are used
4. **Test thoroughly** - Ensure no runtime errors after removal

### High-Risk Functions to Preserve

Any function in these services should be verified extra carefully:
- **ConfigService** - Configuration getters/setters
- **PrinterService** - Printer status methods
- **BambuLabPrinter** - Status parsing methods

### Safe Patterns to Remove

Functions in these categories are safer to remove even in dynamic files:
- Obvious dead code with no references
- Test-only functions in test files
- Deprecated functions with comments
- Debug-only functions not in debug router

---

## Security Notes

### No Dangerous Patterns Detected ✅

**Good News**: No instances of `eval()` or `exec()` found in the codebase.

These patterns would be **HIGH SECURITY RISK** if present:
- ❌ `eval()` - Executes arbitrary code (NONE FOUND)
- ❌ `exec()` - Executes arbitrary statements (NONE FOUND)

### Current Dynamic Patterns: Safe ✅

All detected patterns (`getattr`, `setattr`, `globals`, `locals`) are:
- ✅ Standard Python introspection
- ✅ Safe when used properly
- ✅ Common in configuration and plugin systems
- ✅ No arbitrary code execution risk

---

## Action Items

### Priority 0 (Completed) ✅
- [x] Document all files with dynamic calls
- [x] Categorize by risk level
- [x] Identify high-risk services

### Priority 1 (Before Any Removals)
- [ ] Review each high-risk file for actual dynamic usage
- [ ] Document specific dynamic call patterns per file
- [ ] Create whitelist of functions accessed dynamically

### Priority 2 (During Cleanup)
- [ ] Cross-reference unused functions against this list
- [ ] Extra verification for functions in high-risk files
- [ ] Test dynamic call paths after any removals

### Future Improvements
- [ ] Consider refactoring away from dynamic calls where possible
- [ ] Add type hints to dynamically accessed attributes
- [ ] Document dynamic access patterns in code comments

---

## Quick Reference

### Verification Commands

```bash
# Find getattr usage
grep -rn "getattr" src/services/config_service.py

# Find setattr usage
grep -rn "setattr" src/services/config_service.py

# Find globals() usage
grep -rn "globals()" src/

# Find all dynamic patterns in a file
grep -E "(getattr|setattr|globals|locals|__import__|importlib)" <file>
```

### Testing Dynamic Calls

After removing any function:
```bash
# Run full test suite
pytest tests/ -v

# Run specific integration tests
pytest tests/integration/ -v

# Test configuration loading
pytest tests/test_essential_config.py -v

# Test printer services
pytest tests/test_essential_printer_api.py -v
```

---

## Conclusion

**Summary**:
- 16 files use dynamic call patterns
- 0 security risks (no `eval`/`exec`)
- 2 high-risk services (ConfigService, PrinterService)
- 4 medium-risk files
- 10 low-risk files

**Impact on Cleanup**:
- ~10-20 functions may be called dynamically
- Extra verification required for high-risk files
- Overall cleanup can proceed with caution

**Recommendation**: Proceed with cleanup but add extra testing for functions in high-risk files.

---

*Document created: 2025-10-04*
*Action 0.2 - Priority 0 Complete*
