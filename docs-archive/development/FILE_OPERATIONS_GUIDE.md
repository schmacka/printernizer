# File Operations Architecture Guide

**Purpose**: Document the canonical file operation patterns in Printernizer
**Date**: 2025-10-04
**Status**: Official Architecture Pattern

---

## Architecture Overview

File operations in Printernizer follow a **layered service architecture**:

```
┌─────────────────────────────────────────────┐
│          API Layer (files.py)               │
│  - HTTP endpoints for file operations       │
│  - Input validation                         │
│  - Response formatting                      │
└────────────────┬────────────────────────────┘
                 │ delegates to
                 ▼
┌─────────────────────────────────────────────┐
│      FileService (file_service.py)          │  ◄── PRIMARY ENTRY POINT
│  - Progress tracking                        │
│  - Destination path management              │
│  - Database updates                         │
│  - File verification                        │
└────────────────┬────────────────────────────┘
                 │ delegates to
                 ▼
┌─────────────────────────────────────────────┐
│   PrinterService (printer_service.py)       │
│  - Printer discovery                        │
│  - Connection management                    │
└────────────────┬────────────────────────────┘
                 │ delegates to
                 ▼
┌─────────────────────────────────────────────┐
│    Printer Drivers (printers/*.py)          │  ◄── IMPLEMENTATION LAYER
│  - BambuLabPrinter                          │
│  - PrusaPrinter                             │
│  - Protocol-specific download logic         │
└─────────────────────────────────────────────┘
```

---

## Canonical Implementations

### ✅ PRIMARY: FileService.download_file()

**Location**: `src/services/file_service.py:192`

**Signature**:
```python
async def download_file(
    self,
    printer_id: str,
    filename: str,
    destination_path: Optional[str] = None
) -> Dict[str, Any]
```

**Responsibilities**:
- ✅ Progress tracking
- ✅ Automatic destination path creation
- ✅ Database updates
- ✅ File verification
- ✅ Error handling
- ✅ Event emission

**When to use**: **ALWAYS** - This is the public API for file downloads

**Example**:
```python
from src.services.file_service import FileService
from src.utils.dependencies import get_file_service

file_service = await get_file_service()
result = await file_service.download_file(
    printer_id="bambu_001",
    filename="benchy.3mf"
)
```

---

### 🔧 IMPLEMENTATION: Printer.download_file()

**Location**:
- `src/printers/base.py:108` (interface)
- `src/printers/bambu_lab.py:1299` (Bambu implementation)
- `src/printers/prusa.py:477` (Prusa implementation)

**Signature**:
```python
async def download_file(self, filename: str, local_path: str) -> bool
```

**Responsibilities**:
- Protocol-specific FTP/HTTP download
- Connection handling
- Low-level file transfer

**When to use**: **NEVER DIRECTLY** - These are implementation details called by PrinterService

**Note**: These methods are `@abstractmethod` and must exist for the printer interface,
but should NEVER be called directly by application code.

---

### 🌐 API Endpoint: POST /files/{file_id}/download

**Location**: `src/api/routers/files.py:167`

**Purpose**: HTTP endpoint that delegates to FileService

**Status**: ✅ Already correctly implemented

**Implementation**:
```python
@router.post("/{file_id}/download")
async def download_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    # Parse file_id
    printer_id, filename = parse_file_id(file_id)

    # Delegate to FileService
    result = await file_service.download_file(printer_id, filename)

    return {"status": "downloaded"}
```

---

## Usage Patterns

### ✅ CORRECT: Use FileService

```python
# In application code
from src.utils.dependencies import get_file_service

async def download_print_file(printer_id: str, filename: str):
    file_service = await get_file_service()
    result = await file_service.download_file(printer_id, filename)
    return result
```

### ❌ INCORRECT: Direct printer access

```python
# DON'T DO THIS!
from src.printers.bambu_lab import BambuLabPrinter

async def download_file_wrong(filename: str):
    printer = BambuLabPrinter(...)
    await printer.download_file(filename, "/tmp/file")  # ❌ Bypasses tracking!
```

### ❌ INCORRECT: Duplicate implementation

```python
# DON'T DO THIS!
async def my_own_download(printer_id: str, filename: str):
    # Reimplementing download logic ❌
    printer = await get_printer(printer_id)
    ftp = connect_ftp(printer.ip)
    ftp.download(filename)  # ❌ No progress tracking, no DB updates!
```

---

## File Operation Inventory

### Download Operations

| Implementation | Location | Status | Usage |
|---------------|----------|--------|-------|
| **FileService.download_file()** | `src/services/file_service.py:192` | ✅ PRIMARY | **Always use this** |
| BambuLabPrinter.download_file() | `src/printers/bambu_lab.py:1299` | 🔧 Implementation | Called by PrinterService |
| PrusaPrinter.download_file() | `src/printers/prusa.py:477` | 🔧 Implementation | Called by PrinterService |
| PrinterInterface.download_file() | `src/printers/base.py:108` | 🔧 Interface | Abstract method |
| API download_file() | `src/api/routers/files.py:167` | ✅ Endpoint | Delegates to FileService |
| BambuFTPService.download_file() | `src/services/bambu_ftp_service.py:296` | 🔧 Low-level | Used by BambuLabPrinter |
| BambuFTP.download_file() | `scripts/working_bambu_ftp.py:127` | 🛠️ Testing | Standalone test utility |
| test download_file() | `tests/backend/test_api_files.py:496` | ✅ Test | Mock for testing |

### List Files Operations

| Implementation | Location | Status | Usage |
|---------------|----------|--------|-------|
| **FileService.discover_printer_files()** | `src/services/file_service.py:~140` | ✅ PRIMARY | **Always use this** |
| Database.list_files() | `src/database/database.py:613` | 🔧 Implementation | Called by FileService |
| BambuLabPrinter.list_files() | `src/printers/bambu_lab.py:840` | 🔧 Implementation | Called by PrinterService |
| PrusaPrinter.list_files() | `src/printers/prusa.py:316` | 🔧 Implementation | Called by PrinterService |
| PrinterInterface.list_files() | `src/printers/base.py:103` | 🔧 Interface | Abstract method |
| API list_files() | `src/api/routers/files.py:61` | ✅ Endpoint | Delegates to FileService |
| BambuFTPService.list_files() | `src/services/bambu_ftp_service.py:194` | 🔧 Low-level | Used by BambuLabPrinter |
| LibraryService.list_files() | `src/services/library_service.py:449` | ✅ Library | Different domain (library vs printer) |

---

## Why This Architecture?

### Benefits

1. **Single Source of Truth**: FileService is the ONLY place that knows about:
   - Progress tracking
   - Database updates
   - File verification
   - Download path management

2. **Separation of Concerns**:
   - **FileService**: Business logic
   - **PrinterService**: Printer management
   - **Printer drivers**: Protocol implementation

3. **Testability**: Can mock FileService without worrying about printer protocols

4. **Consistency**: All downloads follow same pattern, same tracking, same error handling

### Trade-offs

- **More layers**: Have to go through service layer
- **Abstraction overhead**: Can't directly use printer methods
- **Learning curve**: Developers need to understand the layers

**Decision**: Benefits outweigh trade-offs for production code

---

## Migration Guide

### If You Have Code That Bypasses FileService

**Before**:
```python
# Bad: Direct printer access
printer = await printer_service.get_printer(printer_id)
await printer.download_file(filename, "/tmp/file")
```

**After**:
```python
# Good: Use FileService
file_service = await get_file_service()
result = await file_service.download_file(printer_id, filename)
```

### If You're Writing a New Feature

**Always**:
1. Import from `src.services.file_service`
2. Use dependency injection: `Depends(get_file_service)`
3. Call `file_service.download_file()` or `file_service.discover_printer_files()`
4. Never import from `src.printers.*` directly

### For Testing/Scripts

**Standalone utilities** (like `scripts/working_bambu_ftp.py`):
- ✅ OK to have direct implementations
- 🎯 Purpose: Testing, debugging, one-off operations
- ⚠️ Should NOT be used in production code
- 📝 Must document that they bypass the service layer

**Integration tests**:
- ✅ Should test through FileService
- ✅ Can mock printer responses
- ❌ Should NOT test printer methods directly

---

## Code Review Checklist

When reviewing file operation code, check:

- [ ] Uses `FileService.download_file()` (not `Printer.download_file()`)
- [ ] Uses `FileService.discover_printer_files()` (not `Printer.list_files()`)
- [ ] Imports from `src.services.*` (not `src.printers.*`)
- [ ] Uses dependency injection where possible
- [ ] Doesn't reimplement download logic
- [ ] Includes error handling
- [ ] Updates are tracked in database

---

## Future Improvements

Potential enhancements to consider:

1. **Progress callbacks**: Allow callers to subscribe to progress updates
2. **Batch downloads**: Download multiple files efficiently
3. **Resume support**: Resume interrupted downloads
4. **Checksums**: Verify file integrity with MD5/SHA256
5. **Compression**: Compress files during transfer

---

## Related Documentation

- **File Service**: `src/services/file_service.py`
- **Printer Interface**: `src/printers/base.py`
- **API Routes**: `src/api/routers/files.py`
- **Database Schema**: `src/database/database.py`
- **Architecture Overview**: `docs/development/ARCHITECTURE.md` (if it exists)

---

## Questions?

**Q: Why can't I just call `printer.download_file()` directly?**
A: You bypass progress tracking, database updates, and file verification. Always use FileService.

**Q: What about scripts in `scripts/`?**
A: Standalone test utilities can bypass the service layer, but production code cannot.

**Q: Can I add a new printer driver?**
A: Yes! Implement the `PrinterInterface`, and it will automatically work with FileService.

**Q: Why so many layers?**
A: Separation of concerns, testability, and maintainability. Production systems need structure.

---

*Last updated: 2025-10-04 - Action 1.2 File Operations Documentation*
*Status: Official Architecture Pattern*
