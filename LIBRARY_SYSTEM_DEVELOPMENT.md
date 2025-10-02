# Library System Development Log

**Feature**: Unified Library System
**Branch**: `feature/library-system`
**Target Version**: v1.2.0
**Started**: 2025-10-02
**Status**: 🚧 In Development

---

## Overview

Transforming the file management system from separate "printer files" and "local files" sections into a unified **Library System** with content-based file identification (checksums), intelligent deduplication, and comprehensive metadata management.

---

## Implementation Progress

### Phase 1: Core Library Foundation ⏳ IN PROGRESS

#### ✅ Completed Tasks

1. **Database Migration Created** (2025-10-02)
   - File: `migrations/007_library_system.sql`
   - Created tables:
     - `library_files` - Main library files table with checksum-based identity
     - `library_file_sources` - Track multiple sources per file
     - `collections` - File collections/groups
     - `collection_members` - Many-to-many for collections
   - Added comprehensive indexes for performance
   - Created views: `library_stats`, `library_files_with_sources`

#### 🔄 In Progress

2. **LibraryService Implementation**
   - Create `src/services/library_service.py`
   - Implement checksum calculation (SHA-256)
   - File copy/move to library structure
   - Source tracking
   - Deduplication logic

#### 📋 Pending Tasks

3. **Configuration Updates**
   - Add library settings to `src/utils/config.py`
   - Environment variables:
     - `LIBRARY_PATH`
     - `LIBRARY_ENABLED`
     - `LIBRARY_AUTO_ORGANIZE`
     - `LIBRARY_AUTO_EXTRACT_METADATA`

4. **Database Integration**
   - Add library methods to `src/database/database.py`
   - CRUD operations for library_files
   - Source management
   - Collection operations

5. **API Endpoints**
   - Create `src/api/routers/library.py`
   - Endpoints:
     - `GET /api/v1/library/files` - List with filters
     - `GET /api/v1/library/files/{checksum}` - Get details
     - `POST /api/v1/library/files/{checksum}/reprocess`
     - `DELETE /api/v1/library/files/{checksum}`

6. **File Discovery Integration**
   - Update `FileWatcherService` to use library
   - Update printer file discovery
   - Auto-process new files into library

7. **Library Folder Initialization**
   - Create folder structure on startup
   - Verify permissions
   - Handle cross-platform paths

---

## Architecture Decisions

### File Identification: Checksum-Based

**Decision**: Use SHA-256 checksums as primary file identifier instead of filename-based IDs.

**Rationale**:
- Content-based identity enables automatic deduplication
- Same file from different sources = one library entry
- Filenames can change, content hash remains constant
- Industry standard for file integrity verification

**Implementation**:
```python
checksum = hashlib.sha256()
with open(file_path, 'rb') as f:
    for chunk in iter(lambda: f.read(8192), b''):
        checksum.update(chunk)
return checksum.hexdigest()
```

### Storage Structure: Organized by Source Type

**Decision**: Separate folders for different sources (printers, models, uploads).

**Rationale**:
- Clear organization
- Easy backup/restore by source type
- Printer files can maintain original names
- Watch folder files organized in flat structure

**Structure**:
```
library/
├── models/              # Watch folder files
│   └── {checksum[:2]}/  # Sharded by first 2 chars
│       └── {checksum}.3mf
├── printers/
│   ├── bambu_a1/
│   │   └── {checksum[:2]}/
│   │       └── {checksum}_OriginalName.gcode
│   └── prusa_core_one/
└── .metadata/
    ├── thumbnails/
    └── previews/
```

### Multiple Sources: Junction Table

**Decision**: Use separate `library_file_sources` table instead of JSON array in main table.

**Rationale**:
- Better query performance for source filtering
- Easier to add/remove sources
- Can add indexes for fast lookups
- More normalized database design

**Consideration**: JSON in `sources` column still maintained for quick access, synchronized with junction table.

---

## Technical Challenges & Solutions

### Challenge 1: Large File Checksum Performance

**Issue**: Calculating SHA-256 for large G-code files (100MB+) blocks async loop.

**Solution**:
- Use `asyncio.to_thread()` for CPU-bound operation
- Process in chunks (8KB) to keep memory low
- Show progress indicator for files >10MB
- Consider caching checksums in file extended attributes (future)

### Challenge 2: Cross-Filesystem File Moves

**Issue**: Moving files between different filesystems (e.g., network drive to local) fails with `OSError`.

**Solution**:
- Detect cross-filesystem moves with `os.stat().st_dev`
- Fall back to copy + verify + delete for cross-filesystem operations
- Use atomic renames within same filesystem
- Verify checksum after copy before deleting source

### Challenge 3: Concurrent File Processing

**Issue**: Multiple sources discovering same file simultaneously could cause race conditions.

**Solution**:
- Use database-level UNIQUE constraint on checksum
- Catch `IntegrityError` and retry as "add source" operation
- File lock during processing
- Queue-based processing with single worker (Phase 1)

---

## Database Schema Notes

### Why `library_files` instead of extending `files`?

**Rationale**:
- Clean separation allows parallel operation during migration
- Old system remains functional during transition
- Can easily roll back if issues found
- Clear migration path with feature flag

### Foreign Keys vs. String References

**Decision**: Use string references for `printer_id` and `folder_path` instead of proper foreign keys.

**Rationale**:
- Printers and folders managed in application layer
- More flexible for configuration changes
- Simplifies deletion logic
- No cascade delete complications

---

## API Design Decisions

### Checksum in URL Path

**Decision**: Use checksum as primary identifier in API URLs: `/api/v1/library/files/{checksum}`

**Rationale**:
- Checksum is globally unique identifier
- RESTful design (resource identified by its content)
- Enables cross-reference with external systems
- No ambiguity with filename-based IDs

**Alternative**: Could use database UUID, but checksum is more meaningful.

### Pagination Strategy

**Decision**: Offset-based pagination with configurable page size.

**Implementation**:
```
GET /api/v1/library/files?page=1&limit=50
```

**Future**: Consider cursor-based pagination for large libraries (>10k files).

---

## Testing Strategy

### Unit Tests

**Files to create**:
- `tests/test_library_service.py`
  - Checksum calculation
  - File organization logic
  - Deduplication detection
  - Source tracking

### Integration Tests

**Scenarios**:
1. Watch folder file discovered → added to library
2. Printer file downloaded → deduplicated if exists
3. Same file from multiple sources → single entry with multiple sources
4. File deleted from library → sources updated, file removed if no sources

### Performance Tests

**Benchmarks**:
- Checksum calculation: <1s for 50MB file
- Library listing: <500ms for 1000 files
- Search query: <300ms
- Metadata extraction: <5s per file

---

## Migration Plan

### Step 1: Deploy with Feature Flag OFF

- Deploy code with `LIBRARY_ENABLED=false`
- Verify no regressions in existing file system
- Monitor logs for any issues

### Step 2: Test Migration Script

- Run migration on copy of production database
- Verify all files migrated successfully
- Check checksum calculations
- Validate source attribution

### Step 3: Enable Library for New Files Only

- Set `LIBRARY_ENABLED=true`
- New file discoveries go to library
- Existing files remain in old system
- Both systems operational

### Step 4: Migrate Existing Files

- Run background migration job
- Batch process: 100 files at a time
- Monitor disk space and performance
- Pause if errors exceed threshold

### Step 5: Switch to Library-Only

- Update UI to use library endpoints
- Deprecate old files endpoints
- Keep old system for 1 release cycle (rollback safety)

---

## Configuration

### Environment Variables Added

```bash
# Library System Configuration
LIBRARY_PATH=/app/data/library              # Root library folder
LIBRARY_ENABLED=true                        # Enable library system
LIBRARY_AUTO_ORGANIZE=true                  # Auto-organize files
LIBRARY_AUTO_EXTRACT_METADATA=true          # Auto-extract metadata
LIBRARY_AUTO_DEDUPLICATE=true               # Auto-merge duplicates
LIBRARY_PROCESSING_WORKERS=2                # Parallel processing
LIBRARY_CHECKSUM_ALGORITHM=sha256           # Hash algorithm
LIBRARY_PRESERVE_ORIGINALS=true             # Keep source files

# Search Configuration
LIBRARY_SEARCH_ENABLED=true
LIBRARY_SEARCH_MIN_LENGTH=3
```

---

## Known Issues & Limitations

### Current Limitations

1. **Single Library Path**: Only one library folder supported (multi-library planned for v1.3.0)
2. **No File Versioning**: File modifications create new entry (versioning planned for Phase 4)
3. **Limited Search**: Basic filename search only (full-text search in Phase 3)
4. **No Bulk Operations**: Must process files one at a time (bulk ops in Phase 3)

### Potential Issues

1. **Disk Space**: Library duplication could temporarily double storage during migration
   - **Mitigation**: Monitor disk space, pause migration if <10% free

2. **Checksum Collisions**: SHA-256 collisions theoretically possible (probability: ~10^-60)
   - **Mitigation**: Log collision events, provide manual resolution UI

3. **Large File Performance**: Files >500MB may take >5s to checksum
   - **Mitigation**: Async processing, progress indicators, consider MD5 for initial detection

---

## Performance Benchmarks

### Target Performance (Phase 1)

| Operation | Target | Measured | Status |
|-----------|--------|----------|--------|
| Checksum (10MB file) | <1s | TBD | ⏳ |
| Checksum (100MB file) | <5s | TBD | ⏳ |
| Library list (100 files) | <500ms | TBD | ⏳ |
| File detail | <200ms | TBD | ⏳ |
| Search | <300ms | TBD | ⏳ |
| Add to library | <2s | TBD | ⏳ |

*Benchmarks will be updated as implementation progresses.*

---

## Code Review Checkpoints

### Before Phase 1 Completion

- [ ] Database migration tested on empty database
- [ ] Database migration tested on production-like data
- [ ] LibraryService unit tests passing
- [ ] Checksum calculation verified against known hashes
- [ ] File organization logic reviewed
- [ ] Error handling comprehensive
- [ ] Logging appropriate (info/warning/error)
- [ ] Memory usage acceptable (<100MB overhead)

### Before Phase 2 (UI) Kickoff

- [ ] API endpoints tested with Postman/curl
- [ ] API response times meet targets
- [ ] Documentation updated
- [ ] Integration tests passing
- [ ] Edge cases handled (large files, special characters, etc.)

---

## Future Enhancements (Post-v1.2.0)

### Smart Features (v1.3.0)

- AI-powered tag suggestions
- Similar file recommendations
- Optimal printer selection
- Print success prediction

### Advanced Organization (v1.3.0)

- File versioning system
- Multi-library support
- Folder hierarchies within library
- Shared libraries (multi-user)

### Integration Features (v1.4.0)

- Cloud backup (S3, GDrive, Dropbox)
- External slicer integration
- Print analytics and tracking
- Community file sharing

### Performance Optimizations (v1.3.0)

- Incremental checksum calculation (for modified files)
- Parallel file processing (worker pool)
- Database sharding for large libraries (>50k files)
- CDN for thumbnail delivery

---

## Resources & References

### Documentation
- Main spec: [CLAUDE.md - Library System Plan](#)
- Enhanced Metadata: `docs/features/ENHANCED_3D_MODEL_METADATA.md`
- API spec: `docs/api_specification.md`

### External Resources
- SHA-256: [Wikipedia](https://en.wikipedia.org/wiki/SHA-2)
- Content-addressable storage: [Git internals](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)
- File deduplication: [ZFS dedup](https://www.freebsd.org/cgi/man.cgi?query=zfs)

---

## Team Notes

### Questions for Review

1. Should library support external storage (NAS, cloud) in Phase 1 or defer to later?
   - **Decision**: Defer to v1.3.0, focus on local storage first

2. How to handle files deleted from source (printer/watch folder)?
   - **Decision**: Keep in library, mark source as "unavailable"

3. Should we preserve original file modification times?
   - **Decision**: Yes, use `shutil.copy2()` to preserve metadata

4. Migration rollback strategy if critical bug found?
   - **Decision**: Feature flag instant disable, manual script to revert database

---

## Changelog

### 2025-10-02
- ✅ Created feature branch `feature/library-system`
- ✅ Created database migration `007_library_system.sql`
- ✅ Created development log `LIBRARY_SYSTEM_DEVELOPMENT.md`
- 🔄 Started LibraryService implementation

---

## Next Steps

1. ✅ Database migration created
2. 🔄 Implement LibraryService class
3. ⏳ Add configuration for library system
4. ⏳ Create API endpoints
5. ⏳ Integrate with file discovery
6. ⏳ Test with sample files
7. ⏳ Create Files2 UI (Phase 2)

---

**Last Updated**: 2025-10-02
**Last Updated By**: Claude (AI Assistant)
