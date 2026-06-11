# Metadata & Thumbnail Extraction for STL, G-code, and BGCode Files

**Feature Branch**: `feature/stl-gcode-bgcode-metadata`
**Status**: ✅ Implemented
**Version Target**: v1.2.0

## Overview

This feature adds comprehensive metadata extraction and automatic thumbnail generation for STL, G-code, and BGCode files in the library system. Previously, only 3MF files had full metadata support.

## Problem Solved

**Before**: STL, gcode, and bgcode files showed no metadata or thumbnails in the library:
- No dimensions, volume, or physical properties
- No thumbnails or preview images
- No quality metrics or complexity information

**After**: All file types now display rich metadata:
- ✅ STL files: geometric metadata + generated thumbnails
- ✅ G-code files: print settings + embedded/generated thumbnails
- ✅ BGCode files: embedded thumbnails + basic metadata

## Implementation Details

### New Components

#### 1. STLAnalyzer Service (`src/services/stl_analyzer.py`)

Extracts geometric metadata from STL files using Trimesh:

**Extracted Metadata:**
- **Physical Properties**:
  - Dimensions (width × depth × height in mm)
  - Bounding box coordinates
  - Volume (cm³)
  - Surface area (cm²)
  - Center of mass

- **Geometry Information**:
  - Vertex count
  - Face/triangle count
  - Edge count

- **Quality Metrics**:
  - Watertight/manifold status
  - Complexity score (1-10)
  - Difficulty level (Beginner/Intermediate/Advanced/Expert)
  - Hole detection

**Usage:**
```python
from src.services.stl_analyzer import STLAnalyzer

analyzer = STLAnalyzer()
result = await analyzer.analyze_file(Path("model.stl"))

if result['success']:
    physical = result['physical_properties']
    print(f"Dimensions: {physical['model_width']} × {physical['model_depth']} × {physical['model_height']} mm")
    print(f"Volume: {physical['model_volume']} cm³")
    print(f"Complexity: {result['quality_metrics']['complexity_score']}/10")
```

#### 2. Enhanced LibraryService

**Changes to `src/services/library_service.py`:**

1. **Added STL file support** (line 719):
   ```python
   if file_type in ['.3mf', '.gcode', '.bgcode', '.stl']:
   ```

2. **Integrated STLAnalyzer** for geometric metadata extraction

3. **Added PreviewRenderService** for automatic thumbnail generation:
   - Generates 512×512 PNG thumbnails
   - Caches generated thumbnails
   - Stores thumbnails as base64 in database

4. **New mapping function** `_map_stl_metadata_to_db()`:
   - Converts STL analyzer output to database fields
   - Handles physical properties and quality metrics

### Metadata Extraction Workflow

```
File Added to Library
         ↓
   Parse File (BambuParser)
         ↓
    ┌────┴────┐
    │ STL?    │
    └────┬────┘
         ↓ Yes
   Extract Geometry (STLAnalyzer)
         ↓
   Needs Thumbnail?
         ↓ Yes
   Generate Preview (PreviewRenderService)
         ↓
   Store in Database
```

## Supported File Types & Metadata

### STL Files

| Metadata Field | Source | Available |
|----------------|--------|-----------|
| Dimensions | STL geometry | ✅ |
| Volume | STL geometry | ✅ |
| Surface Area | STL geometry | ✅ |
| Complexity Score | Calculated | ✅ |
| Difficulty Level | Calculated | ✅ |
| Thumbnails | Generated | ✅ |
| Print Settings | N/A (geometry only) | ❌ |
| Material Info | N/A (geometry only) | ❌ |

### G-code Files

| Metadata Field | Source | Available |
|----------------|--------|-----------|
| Dimensions | Gcode comments | ✅ |
| Print Settings | Gcode comments | ✅ |
| Layer Info | Gcode comments | ✅ |
| Material Usage | Gcode comments | ✅ |
| Print Time | Gcode comments | ✅ |
| Thumbnails | Embedded or generated | ✅ |

### BGCode Files

| Metadata Field | Source | Available |
|----------------|--------|-----------|
| Thumbnails | Embedded PNG | ✅ |
| File Size | Binary data | ✅ |
| Metadata | Limited (binary format) | ⚠️ |

## Database Schema

All metadata is stored in the `library_files` table:

```sql
-- Physical properties (STL, 3MF, gcode)
model_width DECIMAL(8,3)
model_depth DECIMAL(8,3)
model_height DECIMAL(8,3)
model_volume DECIMAL(10,3)
surface_area DECIMAL(10,3)

-- Quality metrics (STL, calculated for all)
complexity_score INTEGER
difficulty_level VARCHAR(20)

-- Thumbnails (all types)
has_thumbnail BOOLEAN
thumbnail_data TEXT           -- Base64 encoded PNG
thumbnail_width INTEGER
thumbnail_height INTEGER
thumbnail_format TEXT
```

## Testing

### Unit Tests

```python
# Test STL analyzer
pytest tests/test_stl_analyzer.py

# Test library service integration
pytest tests/test_library_service.py -k "test_metadata_extraction"
```

### Manual Testing

1. **Add STL file to library**:
```python
from pathlib import Path
from src.services.library_service import LibraryService

# Add STL file
file_record = await library_service.add_file_to_library(
    source_path=Path("test.stl"),
    source_info={'type': 'upload'},
    copy_file=True
)

# Check metadata was extracted
assert file_record['model_width'] is not None
assert file_record['has_thumbnail'] == 1
```

2. **Verify thumbnail generation**:
   - Check `data/library/.metadata/preview-cache/` for cached thumbnails
   - Verify base64 thumbnail data in database

3. **Check logs**:
```
2025-10-06 20:00:00 [info] Metadata extraction started file_type=.stl
2025-10-06 20:00:01 [info] Metadata extracted from file parser
2025-10-06 20:00:01 [info] STL geometric metadata extracted stl_fields_added=7
2025-10-06 20:00:02 [info] Generating preview thumbnail
2025-10-06 20:00:03 [info] Preview thumbnail generated successfully size_bytes=45231
2025-10-06 20:00:03 [info] Metadata extraction completed metadata_count=12
```

## Dependencies

Required Python packages (already in requirements.txt):
```
trimesh>=3.20.0      # For STL geometry analysis
numpy>=1.24.0        # Required by trimesh
matplotlib>=3.7.0    # For thumbnail rendering
```

## Configuration

No additional configuration required. The system automatically:
- Detects file types
- Extracts appropriate metadata
- Generates thumbnails when needed
- Caches results for performance

## Performance Considerations

### STL Analysis Performance

| File Size | Vertices | Analysis Time | Thumbnail Time |
|-----------|----------|---------------|----------------|
| 1 MB | 10K | ~100ms | ~500ms |
| 10 MB | 100K | ~500ms | ~1s |
| 50 MB | 500K | ~2s | ~3s |

### Optimization Features

1. **Async Processing**: Metadata extraction runs in background
2. **Thread Pool**: CPU-intensive operations use executor
3. **Caching**: Thumbnails cached on disk
4. **Lazy Loading**: Metadata extracted only when needed

## Migration Guide

### Existing Files

To extract metadata for existing library files without metadata:

```python
# Re-analyze all STL files
stl_files = await library_service.list_files(
    filters={'file_type': '.stl', 'has_thumbnail': False}
)

for file in stl_files[0]:
    await library_service.reprocess_file(file['checksum'])
```

Or use the bulk re-analysis endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/library/bulk-reanalyze \
  -H "Content-Type: application/json" \
  -d '{"file_type": ".stl"}'
```

## Known Limitations

1. **STL Files**:
   - No print settings (pure geometry format)
   - No material information
   - Estimated weights assume 100% solid PLA

2. **BGCode Files**:
   - Limited metadata extraction (binary format)
   - Would require full BGCode binary parser for comprehensive data

3. **Large Files**:
   - STL files >100MB may take 5-10 seconds to analyze
   - Consider timeout settings for very large files

## Future Enhancements

- [ ] Support for OBJ file format
- [ ] Enhanced BGCode binary parser
- [ ] Material estimation based on volume + infill settings
- [ ] Print time estimation for STL files
- [ ] Multi-part STL assembly detection
- [ ] Automatic orientation suggestions
- [ ] Support analysis improvements

## Changelog

### v1.2.0 - 2025-10-06

**Added:**
- STLAnalyzer service for geometric metadata extraction
- Automatic thumbnail generation for STL files
- Integrated PreviewRenderService with library system
- Enhanced metadata extraction for all file types

**Changed:**
- LibraryService now processes `.stl` files
- Metadata extraction workflow supports multiple analyzers
- Database stores geometric properties for all file types

**Fixed:**
- STL files now show metadata and thumbnails
- Gcode files properly extract embedded thumbnails
- BGCode files display preview images

## Related Documentation

- [Library System Implementation](LIBRARY_SYSTEM_IMPLEMENTATION.md)
- [Enhanced Metadata Specification](ENHANCED_3D_MODEL_METADATA.md)
- [Preview Rendering Guide](../PREVIEW_RENDERING.md)

## Support

For issues or questions:
- Check logs for error messages
- Verify Trimesh installation: `pip install trimesh`
- Ensure file permissions allow read access
- Review database schema for metadata fields
