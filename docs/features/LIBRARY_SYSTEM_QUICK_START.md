# Library System - Quick Start Guide

**Version:** 1.0
**Last Updated:** 2025-10-03

## Overview

The Library System is a unified file management solution that replaces the traditional "Files" section with a content-addressable storage system featuring deduplication, multi-source tracking, and comprehensive metadata management.

---

## Key Concepts

### Content-Addressable Storage
- Files are uniquely identified by **SHA-256 checksum** (not filename)
- Same file from different sources = one physical copy
- Automatic deduplication saves disk space

### Multi-Source Tracking
- One file can come from multiple sources:
  - **Printers** (Bambu Lab, Prusa)
  - **Watch Folders** (monitored directories)
  - **Uploads** (manual uploads)
- All sources are tracked and displayed

### Sharded Storage
- Files organized in 256 buckets (by first 2 hex digits of checksum)
- Prevents filesystem performance issues with 10,000+ files
- Example: `library/printers/A1/3f/3f2a9b... .3mf`

---

## Using the Library

### Accessing the Library

1. Click **"🗄️ Bibliothek"** in the main navigation
2. The Library page displays:
   - **Statistics cards** (total files, size, thumbnails, analyzed)
   - **Filter bar** (source type, file type, status, metadata, sort)
   - **Files grid** with thumbnails and metadata
   - **Pagination** controls

### Viewing Files

**File Cards Show:**
- Thumbnail (or file type icon)
- Status badge (Available/Downloaded/Local/Error)
- Filename
- Source icon (🖨️ Printer / 📁 Watch Folder / ⬆️ Upload)
- File size
- Print time (if available)
- Quick metadata (layer height, temperature, filament)

**Click a file card** to open the detail modal with 3 tabs:
1. **Übersicht (Overview)** - Print settings, materials, model properties
2. **Metadaten (Metadata)** - All extracted metadata fields
3. **Quellen (Sources)** - All sources where this file came from

### Filtering Files

**Available Filters:**
- **Source Type:** All / Printer / Watch Folder / Upload
- **File Type:** All / 3MF / G-code / STL / OBJ
- **Status:** All / Available / Downloaded / Local / Error
- **Metadata:** All / With Thumbnails / Analyzed
- **Sort By:** Date / Name / Size / Print Time (ascending/descending)

**Search:** Type in the search box (300ms debounce)

### File Actions

From the **file detail modal**, you can:

1. **🔄 Neu analysieren (Reprocess)**
   - Re-extracts metadata from the file
   - Useful if metadata extraction was previously failed

2. **⬇️ Herunterladen (Download)**
   - Downloads the file to your computer
   - Opens in new tab/downloads directly

3. **🗑️ Löschen (Delete)**
   - Removes file from library
   - Deletes physical file and all database entries
   - Confirmation dialog shown

---

## Automatic File Management

### Files from Printers

When you download a file from a printer (Bambu Lab or Prusa):
1. File is downloaded to `/app/data/downloads/` (temporary)
2. Checksum is calculated
3. If duplicate found, source is added (no duplicate copy)
4. If new, file is copied to `library/printers/{printer_name}/{shard}/`
5. Metadata is automatically extracted
6. File appears in Library immediately

### Files from Watch Folders

When a file is discovered in a watch folder:
1. File is detected by the FileWatcherService
2. Checksum is calculated
3. If duplicate found, source is added
4. If new, file is copied to `library/models/{shard}/`
5. Metadata is extracted
6. File appears in Library immediately

**Note:** Original files in watch folders are **not deleted**, they're copied to the library.

---

## API Endpoints

### List Files
```
GET /api/v1/library/files?page=1&limit=50&source_type=printer&file_type=3mf
```

**Query Parameters:**
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 50, max: 200)
- `source_type` - Filter by source (printer/watch_folder/upload)
- `file_type` - Filter by type (3mf/gcode/stl/obj)
- `status` - Filter by status (available/downloaded/local/error)
- `has_thumbnail` - Filter files with thumbnails (true/false)
- `has_metadata` - Filter analyzed files (true/false)
- `search` - Search in filename
- `sort_by` - Sort field (created_at/filename/file_size/print_time)
- `sort_order` - Sort direction (asc/desc)

**Response:**
```json
{
  "files": [
    {
      "checksum": "3f2a9b...",
      "filename": "model.3mf",
      "file_size": 1048576,
      "file_type": "3mf",
      "status": "downloaded",
      "has_thumbnail": true,
      "sources": [
        {
          "type": "printer",
          "printer_name": "A1",
          "printer_id": "printer_123"
        }
      ],
      "layer_height": 0.2,
      "print_time": 7200,
      ...
    }
  ],
  "pagination": {
    "current_page": 1,
    "page_size": 50,
    "total_items": 150,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

### Get File Details
```
GET /api/v1/library/files/{checksum}
```

Returns full file details including all metadata and sources.

### Get Thumbnail
```
GET /api/v1/library/files/{checksum}/thumbnail
```

Returns PNG thumbnail image (if available).

### Download File
```
GET /api/v1/library/files/{checksum}/download
```

Streams the file for download.

### Reprocess Metadata
```
POST /api/v1/library/files/{checksum}/reprocess
```

Re-extracts metadata from the file.

### Delete File
```
DELETE /api/v1/library/files/{checksum}
```

Removes file from library (physical file and database entries).

### Get Statistics
```
GET /api/v1/library/statistics
```

Returns library statistics:
```json
{
  "total_files": 150,
  "total_size": 524288000,
  "files_with_thumbnails": 120,
  "files_analyzed": 145,
  "by_source_type": {
    "printer": 100,
    "watch_folder": 50
  },
  "by_file_type": {
    "3mf": 100,
    "gcode": 40,
    "stl": 10
  }
}
```

---

## Configuration

### Environment Variables

```bash
# Enable/disable library system
LIBRARY_ENABLED=true

# Library storage path
LIBRARY_PATH=/app/data/library

# Automatically organize files into sharded structure
LIBRARY_AUTO_ORGANIZE=true

# Checksum algorithm (sha256 recommended)
LIBRARY_CHECKSUM_ALGORITHM=sha256

# Enable automatic deduplication
LIBRARY_DEDUP_ENABLED=true

# Thumbnail size for generation (pixels)
LIBRARY_THUMBNAIL_SIZE=512

# Minimum free disk space required (GB)
LIBRARY_MIN_DISK_SPACE_GB=10

# Automatically cleanup orphaned files
LIBRARY_CLEANUP_ORPHANED=true

# Cleanup interval (hours)
LIBRARY_CLEANUP_INTERVAL_HOURS=24
```

---

## Directory Structure

```
/app/data/library/
├── printers/               # Files from printers
│   ├── A1/                 # Printer name
│   │   ├── 00/
│   │   ├── 01/
│   │   ├── ...
│   │   ├── 3f/
│   │   │   └── 3f2a9b12...abc.3mf
│   │   └── ff/
│   └── Prusa_Core_One/
│       └── (same structure)
├── models/                 # Files from watch folders
│   ├── 00/
│   ├── 01/
│   └── ...
└── uploads/                # Files from manual uploads
    ├── 00/
    └── ...
```

**Sharding:** First 2 hex characters of checksum = subdirectory
- Example checksum: `3f2a9b12...`
- Shard: `3f`
- Path: `library/printers/A1/3f/3f2a9b12...abc.3mf`

---

## Real-Time Updates

The Library page receives real-time updates via WebSocket:
- **library_file_added** - New file added
- **library_file_updated** - File metadata updated
- **library_file_deleted** - File removed

**Behavior:**
- Statistics update immediately
- File grid refreshes if on page 1
- Current filters/search are preserved

---

## Deduplication Example

**Scenario:** Same 3MF file on printer and in watch folder

1. **File discovered on Printer A1**
   - Checksum: `3f2a9b12...`
   - Copied to: `library/printers/A1/3f/3f2a9b12...abc.3mf`
   - Database entry created
   - Source added: `{type: "printer", printer_name: "A1"}`

2. **Same file found in watch folder `/models/projects/`**
   - Checksum calculated: `3f2a9b12...` (match!)
   - Physical file **not copied** (already exists)
   - Source added: `{type: "watch_folder", folder_path: "/models/projects/"}`
   - Database entry updated with new source

3. **In Library UI**
   - **One file card** displayed
   - Sources tab shows **both sources**:
     - 🖨️ Printer A1
     - 📁 /models/projects/

**Result:** One physical file, one database entry, two tracked sources.

---

## Troubleshooting

### File not appearing in Library

**Check:**
1. Is `LIBRARY_ENABLED=true` in config?
2. Was file successfully downloaded/discovered?
3. Check backend logs for errors
4. Verify disk space (must have `LIBRARY_MIN_DISK_SPACE_GB` free)
5. Check file permissions on library directory

### Duplicate files showing

**Possible causes:**
1. Files have different content (checksums differ)
2. Deduplication disabled (`LIBRARY_DEDUP_ENABLED=false`)
3. Files added before Library system was enabled

### Metadata not extracted

**Actions:**
1. Click **🔄 Neu analysieren** to retry
2. Check if file type is supported (3MF, G-code)
3. Check backend logs for parser errors
4. Verify file is not corrupted

### Slow performance with many files

**Optimizations:**
1. Verify sharding is enabled (`LIBRARY_AUTO_ORGANIZE=true`)
2. Check database indexes exist (run migration)
3. Reduce page size (`limit` parameter)
4. Use filters to narrow results

---

## Migration from Old Files System

### Backward Compatibility

The old files system **continues to work** alongside the Library:
- Old "Dateien" page still accessible
- Old API endpoints still functional
- Old file downloads work

### Gradual Migration

Files are added to Library automatically:
1. **New printer downloads** - Added to Library immediately
2. **Watch folder files** - Added when discovered/rescanned
3. **Old files** - Not automatically migrated

### Manual Migration (Optional)

To migrate old files to Library:
```python
# Future feature - not yet implemented
# Will provide a migration script or UI button
```

---

## Best Practices

### Storage Management
- Monitor disk space regularly
- Enable cleanup of orphaned files
- Use collections to organize related files
- Archive old/unused files

### Performance
- Use filters instead of searching when possible
- Keep page size reasonable (50-100)
- Enable sharding for 1000+ files
- Let metadata extraction happen in background

### Organization
- Use descriptive filenames (helps search)
- Create collections for projects
- Tag files with metadata
- Review and clean up regularly

---

## Support

For issues, feature requests, or questions:
- Check logs in `/app/data/logs/`
- Review GitHub issues
- Consult API documentation
- Contact development team

---

**End of Quick Start Guide**
