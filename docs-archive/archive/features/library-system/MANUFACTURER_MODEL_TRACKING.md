# Library Manufacturer & Model Tracking Enhancement

**Version:** 1.0.4
**Date:** 2025-10-04
**Status:** ✅ Implemented

## Overview

Enhanced library source tracking to include manufacturer and printer model information, enabling better filtering, clearer UI displays, and improved analytics.

---

## Problem Statement

The library system previously tracked files with only generic `type: 'printer'` designation, without distinguishing between:
- **Manufacturers** (Bambu Lab vs Prusa Research)
- **Printer Models** (A1, P1P, Core One, MK4, etc.)

This limited:
- User ability to filter by manufacturer/model
- Clear source identification in UI
- Analytics and reporting capabilities

---

## Solution

### Data Structure Enhancement

#### Source Information (Extended)
```python
source_info = {
    'type': 'printer',                    # Source category
    'printer_id': printer_id,              # UUID
    'printer_name': printer_name,          # User-defined name
    'manufacturer': manufacturer,          # NEW: "bambu_lab" or "prusa_research"
    'printer_model': printer_model,        # NEW: "A1", "Core One", etc.
    'original_filename': filename,
    'original_path': path,
    'discovered_at': timestamp
}
```

#### Manufacturer Mapping
- **Bambu Lab**: `manufacturer: "bambu_lab"` (from `PrinterType.BAMBU_LAB`)
- **Prusa Research**: `manufacturer: "prusa_research"` (from `PrinterType.PRUSA_CORE`)

#### Model Extraction
Extracted from printer name configuration with pattern matching:
- Bambu Lab models: A1, A1 Mini, P1P, P1S, X1C, X1E
- Prusa models: Core One, MK4, MK3S, MK3, MINI, XL
- Fallback: Uses printer name if no pattern matches

---

## Implementation Details

### 1. Database Migration
**File:** [migrations/009_library_manufacturer_model.sql](../../migrations/009_library_manufacturer_model.sql)

```sql
ALTER TABLE library_file_sources ADD COLUMN manufacturer TEXT;
ALTER TABLE library_file_sources ADD COLUMN printer_model TEXT;

CREATE INDEX idx_library_sources_manufacturer
    ON library_file_sources(manufacturer);
CREATE INDEX idx_library_sources_printer_model
    ON library_file_sources(printer_model);
CREATE INDEX idx_library_sources_manufacturer_model
    ON library_file_sources(manufacturer, printer_model);
```

**Backfilling:** Existing records get manufacturer from metadata JSON where available.

### 2. Backend Changes

#### File Service
**File:** [src/services/file_service.py](../../src/services/file_service.py)

**New Method:** `_extract_printer_info(printer: Dict) -> Dict[str, str]`
- Maps `PrinterType` enum to manufacturer string
- Extracts model from printer name via pattern matching
- Returns `{manufacturer, printer_model}`

**Updated:** Download file flow (lines 281-310)
- Calls `_extract_printer_info()` when downloading from printer
- Includes manufacturer and model in `source_info`

#### Library Service
**File:** [src/services/library_service.py](../../src/services/library_service.py)

**Updated:** `add_file_source()` method (lines 442-453)
- Stores `manufacturer` and `printer_model` in database
- Persists to both main record JSON and junction table

#### Database Layer
**File:** [src/database/database.py](../../src/database/database.py)

**Updated:** `list_library_files()` (lines 1166-1277)
- Added JOIN to `library_file_sources` when manufacturer/model filters used
- Uses DISTINCT to avoid duplicates from multiple sources
- Efficient query selection (JOIN only when needed)

**Updated:** `create_library_file_source()` (lines 1279-1302)
- Includes `manufacturer` and `printer_model` columns in INSERT

### 3. API Enhancements

#### Library Router
**File:** [src/api/routers/library.py](../../src/api/routers/library.py)

**New Query Parameters:**
- `manufacturer`: Filter by manufacturer (bambu_lab, prusa_research)
- `printer_model`: Filter by model (A1, Core One, etc.)

**Endpoint:** `GET /api/v1/library/files`
```
?manufacturer=bambu_lab&printer_model=A1
```

### 4. Frontend Updates

#### HTML
**File:** [frontend/index.html](../../frontend/index.html)

**New Filter Controls:**
```html
<select id="filterManufacturer">
    <option value="all">Alle Hersteller</option>
    <option value="bambu_lab">Bambu Lab</option>
    <option value="prusa_research">Prusa Research</option>
</select>

<select id="filterPrinterModel">
    <option value="all">Alle Modelle</option>
    <option value="A1">A1</option>
    <option value="P1P">P1P</option>
    <option value="X1C">X1C</option>
    <option value="Core One">Core One</option>
    <option value="MK4">MK4</option>
</select>
```

#### JavaScript
**File:** [frontend/js/library.js](../../frontend/js/library.js)

**Updated Filter State:**
```javascript
this.filters = {
    manufacturer: null,
    printer_model: null,
    // ... existing filters
}
```

**Enhanced Source Icon Display:**
- Was: `🖨️` (generic)
- Now: `🖨️ Bambu A1` or `🖨️ Prusa Core One`

**Updated Methods:**
- `applyFilters()`: Reads manufacturer/model from UI
- `getSourceIcon()`: Displays manufacturer + model

---

## Usage Examples

### API Filtering

**All Bambu Lab files:**
```bash
GET /api/v1/library/files?manufacturer=bambu_lab
```

**Specific model:**
```bash
GET /api/v1/library/files?printer_model=Core%20One
```

**Combined filters:**
```bash
GET /api/v1/library/files?manufacturer=bambu_lab&printer_model=A1&file_type=.3mf
```

### UI Display

**Before:** `🖨️ Drucker`
**After:** `🖨️ Bambu A1`

**Filter Combinations:**
- Source Type: Printer
- Manufacturer: Bambu Lab
- Model: A1
- File Type: 3MF

---

## Benefits

### 1. Improved User Experience
- **Clear source identification**: "Bambu A1" instead of "Printer"
- **Targeted filtering**: Find all files from specific manufacturer or model
- **Better organization**: Group files by printer type

### 2. Enhanced Analytics
- Track file distribution by manufacturer
- Analyze usage patterns per printer model
- Compare file characteristics across brands

### 3. Future-Proofing
- Easy to add new manufacturers (just add to enum)
- Scalable model detection (pattern-based)
- No breaking changes to existing functionality

### 4. Multi-Printer Workflows
- Quickly find files compatible with specific printers
- Identify which printer produced which files
- Filter by brand for brand-specific slicing profiles

---

## Migration Path

### Existing Data
- Old files without manufacturer/model: Display generic "Drucker" or printer name
- Backfill script updates existing records from metadata JSON
- No data loss or breaking changes

### New Files
- Automatically get manufacturer and model on download
- All future downloads include full tracking

---

## Testing Checklist

- [ ] Database migration runs successfully
- [ ] Manufacturer extracted correctly from Bambu Lab printer
- [ ] Manufacturer extracted correctly from Prusa printer
- [ ] Model detection works for known models
- [ ] Fallback to printer name when model unknown
- [ ] API filters work correctly (manufacturer only)
- [ ] API filters work correctly (model only)
- [ ] API filters work correctly (combined)
- [ ] Frontend displays manufacturer in source badges
- [ ] Frontend filters update correctly
- [ ] Existing files without data still display correctly
- [ ] JOIN query performs efficiently with indexes

---

## Files Modified

### Backend
- ✅ `migrations/009_library_manufacturer_model.sql` (created)
- ✅ `src/services/file_service.py`
- ✅ `src/services/library_service.py`
- ✅ `src/database/database.py`
- ✅ `src/api/routers/library.py`

### Frontend
- ✅ `frontend/index.html`
- ✅ `frontend/js/library.js`

### Documentation
- ✅ `docs/features/MANUFACTURER_MODEL_TRACKING.md` (this file)

---

## Version History

### 1.0.4 (2025-10-04)
- Added manufacturer and printer_model fields
- Implemented extraction logic
- Added API filters
- Updated frontend UI
- Created indexes for performance

---

## Known Limitations

1. **Model Detection:** Relies on printer name containing model identifier
   - Workaround: Standardize printer naming conventions
   - Future: Add explicit model field to printer configuration

2. **Manufacturer Hardcoded:** Only Bambu Lab and Prusa supported
   - Workaround: Falls back to "unknown" for other types
   - Future: Make manufacturer extensible via config

3. **Backfilling:** Partial backfill from JSON metadata
   - Some old records may have NULL values
   - Manual correction may be needed

---

## Future Enhancements

1. **Dynamic Model List:** Populate model dropdown from actual printer configs
2. **Manufacturer Statistics:** Add stats card showing files per manufacturer
3. **Model-Specific Settings:** Store slicing profiles per model
4. **Compatibility Warnings:** Alert if file from incompatible printer model
5. **Export Reports:** Include manufacturer/model in cost reports

---

**End of Document**
