# Library System - Testing Guide

**Version**: v1.2.0-alpha
**Branch**: feature/library-system
**Date**: October 2, 2025

---

## Overview

This guide provides step-by-step instructions for testing the Library System implementation. Follow these procedures to verify all functionality works correctly before merging to master.

---

## Prerequisites

### 1. Start the Application

```bash
# Navigate to project root
cd /path/to/printernizer

# Ensure library is enabled in config
export LIBRARY_ENABLED=true
export LIBRARY_PATH=./data/library

# Start the application
python src/main.py
```

### 2. Verify Library Initialization

```bash
# Check library health
curl http://localhost:8000/api/v1/library/health

# Expected response:
{
  "status": "healthy",
  "enabled": true,
  "library_path": "./data/library",
  "total_files": 0,
  "message": "Library operational"
}
```

### 3. Check Folder Structure

```bash
ls -la data/library/

# Should see:
# models/
# printers/
# uploads/
# .metadata/
```

---

## Test 1: Watch Folder Integration

### Objective
Verify that files added to watch folders are automatically added to library.

### Steps

1. **Configure Watch Folder**
```bash
export WATCH_FOLDERS=/path/to/test/models
```

2. **Add a Test File**
```bash
# Copy a 3MF or STL file to watch folder
cp sample_benchy.3mf /path/to/test/models/
```

3. **Wait for Discovery** (30 seconds max)

4. **Check Library**
```bash
curl http://localhost:8000/api/v1/library/files

# Should return the file in the list
```

5. **Verify File Location**
```bash
# Find the file in library
ls -la data/library/models/

# Should see sharded directories (a3/, b7/, etc.)
# File should be named: {checksum}.3mf
```

### Expected Results
- ✅ File appears in library API
- ✅ File copied to library/models/{shard}/
- ✅ Source type is 'watch_folder'
- ✅ Original file preserved in watch folder

---

## Test 2: Printer File Download

### Objective
Verify that printer downloads are added to library.

### Steps

1. **Add a Printer**
```bash
# Use UI or API to add a test printer
# (Bambu Lab or Prusa)
```

2. **Discover Files on Printer**
```bash
curl http://localhost:8000/api/v1/files?printer_id={printer_id}
```

3. **Download a File**
```bash
curl -X POST http://localhost:8000/api/v1/files/{printer_id}/{filename}/download
```

4. **Check Library**
```bash
curl http://localhost:8000/api/v1/library/files
```

5. **Verify File Location**
```bash
ls -la data/library/printers/{printer_name}/

# Should see file: {checksum}_{original_name}.gcode
```

### Expected Results
- ✅ File appears in library API
- ✅ File copied to library/printers/{printer_name}/{shard}/
- ✅ Source type is 'printer'
- ✅ Original download in downloads/ folder preserved

---

## Test 3: Deduplication

### Objective
Verify that same file from multiple sources creates one library entry.

### Steps

1. **Use Same File from Test 1**
```bash
# Copy the same file (same content) from watch folder to printer
# Or download the same file from printer that exists in watch folder
```

2. **Check Library**
```bash
curl http://localhost:8000/api/v1/library/files

# Should still show only ONE file (not two)
```

3. **Get File Details**
```bash
curl http://localhost:8000/api/v1/library/files/{checksum}

# Check 'sources' field - should have 2 sources:
{
  "sources": "[
    {\"type\": \"watch_folder\", ...},
    {\"type\": \"printer\", ...}
  ]"
}
```

4. **Verify Physical Files**
```bash
# Should be only ONE file in library
# (not duplicated)

# Count files with same checksum:
find data/library -name "*{checksum}*" | wc -l
# Should be 1
```

### Expected Results
- ✅ Only one library entry created
- ✅ Sources array contains both sources
- ✅ Only one physical file in library
- ✅ Both original files preserved

---

## Test 4: File Listing & Filtering

### Objective
Test API filtering and pagination.

### Steps

1. **List All Files**
```bash
curl http://localhost:8000/api/v1/library/files
```

2. **Filter by Source Type**
```bash
curl "http://localhost:8000/api/v1/library/files?source_type=printer"
curl "http://localhost:8000/api/v1/library/files?source_type=watch_folder"
```

3. **Filter by File Type**
```bash
curl "http://localhost:8000/api/v1/library/files?file_type=.3mf"
curl "http://localhost:8000/api/v1/library/files?file_type=.gcode"
```

4. **Search by Name**
```bash
curl "http://localhost:8000/api/v1/library/files?search=benchy"
```

5. **Test Pagination**
```bash
curl "http://localhost:8000/api/v1/library/files?page=1&limit=10"
curl "http://localhost:8000/api/v1/library/files?page=2&limit=10"
```

### Expected Results
- ✅ Filters work correctly
- ✅ Pagination returns correct page
- ✅ Total count accurate
- ✅ Results sorted by date (newest first)

---

## Test 5: File Details

### Objective
Verify file detail endpoint returns complete information.

### Steps

1. **Get File Checksum**
```bash
# From library listing
CHECKSUM=$(curl -s http://localhost:8000/api/v1/library/files | jq -r '.files[0].checksum')
```

2. **Get File Details**
```bash
curl http://localhost:8000/api/v1/library/files/$CHECKSUM
```

3. **Verify Response**
```json
{
  "id": "uuid-here",
  "checksum": "a3f8d...",
  "filename": "benchy.3mf",
  "display_name": "benchy.3mf",
  "library_path": "models/a3/a3f8d....3mf",
  "file_size": 8421376,
  "file_type": ".3mf",
  "sources": "[{...}]",
  "status": "available",
  "added_to_library": "2025-10-02T10:00:00Z",
  ...
}
```

### Expected Results
- ✅ All fields populated
- ✅ Checksum matches
- ✅ Sources JSON valid
- ✅ File size correct

---

## Test 6: File Reprocessing

### Objective
Test metadata extraction trigger.

### Steps

1. **Reprocess a File**
```bash
curl -X POST http://localhost:8000/api/v1/library/files/$CHECKSUM/reprocess
```

2. **Check Response**
```json
{
  "success": true,
  "checksum": "a3f8d...",
  "message": "Metadata extraction scheduled"
}
```

3. **Wait for Processing** (check logs)
```bash
# Watch logs for metadata extraction
tail -f logs/printernizer.log | grep "Metadata extraction"
```

4. **Verify Status Updated**
```bash
curl http://localhost:8000/api/v1/library/files/$CHECKSUM

# Check status field changes:
# processing -> ready (or error if failed)
```

### Expected Results
- ✅ Reprocess endpoint returns success
- ✅ File status changes to 'processing'
- ✅ Metadata extraction runs
- ✅ Status changes to 'ready' or 'error'

---

## Test 7: File Deletion

### Objective
Test file deletion with and without physical file.

### Steps

1. **Delete Database Only**
```bash
curl -X DELETE "http://localhost:8000/api/v1/library/files/$CHECKSUM?delete_physical=false"
```

2. **Verify Database Deletion**
```bash
curl http://localhost:8000/api/v1/library/files/$CHECKSUM
# Should return 404
```

3. **Verify Physical File Preserved**
```bash
ls -la data/library/models/a3/
# File should still exist
```

4. **Delete with Physical File**
```bash
# Add file back first, then:
curl -X DELETE "http://localhost:8000/api/v1/library/files/$CHECKSUM?delete_physical=true"
```

5. **Verify Complete Deletion**
```bash
ls -la data/library/models/a3/
# File should be gone
```

### Expected Results
- ✅ Database deletion works
- ✅ Physical file preserved when delete_physical=false
- ✅ Physical file deleted when delete_physical=true
- ✅ API returns 404 after deletion

---

## Test 8: Library Statistics

### Objective
Verify statistics are calculated correctly.

### Steps

1. **Add Multiple Files** (from previous tests)

2. **Get Statistics**
```bash
curl http://localhost:8000/api/v1/library/statistics
```

3. **Verify Response**
```json
{
  "total_files": 5,
  "total_size": 42103680,
  "files_with_thumbnails": 2,
  "files_analyzed": 3,
  "available_files": 4,
  "processing_files": 1,
  "error_files": 0,
  "unique_file_types": 2,
  "avg_file_size": 8420736,
  "total_material_cost": 5.25
}
```

4. **Verify Counts**
```bash
# Count files manually
curl http://localhost:8000/api/v1/library/files | jq '.pagination.total_items'

# Should match total_files from statistics
```

### Expected Results
- ✅ Total files accurate
- ✅ Total size calculated
- ✅ Statistics update in real-time

---

## Test 9: Checksum Calculation

### Objective
Verify checksum calculation is correct and consistent.

### Steps

1. **Calculate Checksum Manually**
```bash
sha256sum /path/to/test/models/benchy.3mf
```

2. **Get Checksum from Library**
```bash
curl http://localhost:8000/api/v1/library/files | jq -r '.files[] | select(.filename=="benchy.3mf") | .checksum'
```

3. **Compare**
```bash
# Should be identical
```

4. **Test Consistency**
```bash
# Delete and re-add same file
# Checksum should be same
```

### Expected Results
- ✅ Checksums match manual calculation
- ✅ Checksums consistent across additions
- ✅ Different files have different checksums

---

## Test 10: Error Handling

### Objective
Test graceful error handling.

### Tests

### 10a: Insufficient Disk Space
```bash
# (Difficult to test without filling disk)
# Simulated in unit tests
```

### 10b: Invalid File
```bash
# Try to get non-existent file
curl http://localhost:8000/api/v1/library/files/invalid_checksum

# Expected: 404 error
```

### 10c: Invalid Filters
```bash
# Try invalid source type
curl "http://localhost:8000/api/v1/library/files?source_type=invalid"

# Should return empty list (graceful)
```

### 10d: Concurrent Additions
```bash
# Add same file from two sources simultaneously
# (Manual test - check logs for race condition handling)
```

### Expected Results
- ✅ Appropriate HTTP status codes
- ✅ Clear error messages
- ✅ No crashes or undefined behavior

---

## Test 11: Backward Compatibility

### Objective
Ensure old file APIs still work.

### Steps

1. **Test Old Files Endpoint**
```bash
curl http://localhost:8000/api/v1/files
# Should still work
```

2. **Test Old Download**
```bash
# Download via old endpoint
# Should work and also add to library
```

3. **Test Watch Folder Files**
```bash
curl http://localhost:8000/api/v1/files?source=local_watch
# Should return watch folder files
```

### Expected Results
- ✅ Old APIs functional
- ✅ No breaking changes
- ✅ Downloads still work

---

## Test 12: Performance

### Objective
Verify performance meets targets.

### Tests

### 12a: Checksum Speed
```bash
# Time checksum calculation
time sha256sum /path/to/large/file.gcode

# Should be < 5s for 100MB file
```

### 12b: List Performance
```bash
# Add 100 files, then:
time curl -s http://localhost:8000/api/v1/library/files

# Should be < 500ms
```

### 12c: Search Performance
```bash
time curl -s "http://localhost:8000/api/v1/library/files?search=benchy"

# Should be < 300ms
```

### Expected Results
- ✅ Checksum: <1s for 10MB, <5s for 100MB
- ✅ List: <500ms for 100 files
- ✅ Search: <300ms

---

## Test 13: Library Disabled

### Objective
Verify graceful degradation when library disabled.

### Steps

1. **Disable Library**
```bash
export LIBRARY_ENABLED=false

# Restart application
```

2. **Test Watch Folders**
```bash
# Add file to watch folder
# Should be discovered normally (old behavior)
```

3. **Test Printer Downloads**
```bash
# Download file from printer
# Should work normally (old behavior)
```

4. **Test Library API**
```bash
curl http://localhost:8000/api/v1/library/health

# Should return:
{
  "status": "disabled",
  "enabled": false,
  ...
}
```

### Expected Results
- ✅ Application runs normally
- ✅ File discovery works (old way)
- ✅ No library operations attempted
- ✅ No errors in logs

---

## Automated Tests

### Run Unit Tests

```bash
cd tests
pytest backend/test_library_service.py -v

# Expected: All tests pass
```

### Test Coverage

```bash
pytest backend/test_library_service.py --cov=src.services.library_service --cov-report=html

# Expected: >80% coverage
```

---

## Troubleshooting

### Issue: Files Not Appearing in Library

**Check**:
1. LIBRARY_ENABLED=true
2. Watch folders configured
3. Application logs for errors
4. Disk space available
5. Write permissions on library folder

### Issue: Deduplication Not Working

**Check**:
1. Files have identical content (not just same name)
2. Checksums match manually calculated
3. Database shows multiple sources for file

### Issue: Performance Slow

**Check**:
1. Database not growing too large
2. Disk I/O not bottlenecked
3. Too many files in single shard (check distribution)

---

## Test Results Template

```
## Library System Test Results

**Date**: ___________
**Tester**: ___________
**Environment**: ___________

| Test | Status | Notes |
|------|--------|-------|
| 1. Watch Folder Integration | ⬜ Pass ⬜ Fail | |
| 2. Printer Download | ⬜ Pass ⬜ Fail | |
| 3. Deduplication | ⬜ Pass ⬜ Fail | |
| 4. File Listing & Filtering | ⬜ Pass ⬜ Fail | |
| 5. File Details | ⬜ Pass ⬜ Fail | |
| 6. File Reprocessing | ⬜ Pass ⬜ Fail | |
| 7. File Deletion | ⬜ Pass ⬜ Fail | |
| 8. Library Statistics | ⬜ Pass ⬜ Fail | |
| 9. Checksum Calculation | ⬜ Pass ⬜ Fail | |
| 10. Error Handling | ⬜ Pass ⬜ Fail | |
| 11. Backward Compatibility | ⬜ Pass ⬜ Fail | |
| 12. Performance | ⬜ Pass ⬜ Fail | |
| 13. Library Disabled | ⬜ Pass ⬜ Fail | |
| Unit Tests | ⬜ Pass ⬜ Fail | |

**Overall Result**: ⬜ PASS ⬜ FAIL

**Issues Found**:
1.
2.
3.

**Recommendation**: ⬜ Ready to merge ⬜ Needs fixes
```

---

## Next Steps After Testing

1. **If All Tests Pass**:
   - Update LIBRARY_PHASE1_SUMMARY.md with test results
   - Merge feature branch to master
   - Deploy to production
   - Monitor for issues

2. **If Tests Fail**:
   - Document failures
   - Fix issues
   - Re-test
   - Update documentation

---

**Document Version**: 1.0
**Last Updated**: 2025-10-02
**Maintained By**: Development Team
