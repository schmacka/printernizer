# Data Flow Audit Report

> **Generated**: 2026-01-07
> **Updated**: 2026-01-07 - All issues resolved
> **Purpose**: Identify frontend fields that are not properly persisted through backend layers

## Overview

This audit traces user-editable fields from frontend forms through the complete backend stack to identify broken data flows where fields are accepted but not stored.

## Status: ALL ISSUES RESOLVED

All 8 identified issues have been fixed as of 2026-01-07.

| Form | Field | Issue | Priority | Status |
|------|-------|-------|----------|--------|
| Printer | `location` | Accepted by API but not stored in DB | Medium | **FIXED** |
| Printer | `description` | Accepted by API but not stored in DB | Medium | **FIXED** |
| Job | `file_id` | Frontend sends but backend doesn't handle | High | **FIXED** |
| Job | `customer_name` | Only works on update, not create | Medium | **FIXED** |
| Job | `material_cost` | Frontend sends but API doesn't accept | High | **FIXED** |
| Material | `color_hex` | Frontend sends but not stored | Low | **FIXED** |
| Material | `location` | Frontend sends but not stored | Medium | **FIXED** |
| Material | `is_active` | Frontend sends but not stored | Medium | **FIXED** |

### Migrations Applied
- `024_add_printer_metadata.sql` - Added `location`, `description` columns to printers table
- `025_add_job_file_id.sql` - Added `file_id` column to jobs table
- `026_add_material_fields.sql` - Added `color_hex`, `location`, `is_active` columns to materials table

---

## 1. Printer Form Audit

### Form Locations
- **Add Form**: `frontend/index.html` lines 1869-1948
- **Edit Form**: `frontend/index.html` lines 1968-2049
- **Handler**: `frontend/js/printer-form.js`

### Field Status

| Frontend Field | Backend Field | Router | Service | Database | Config | Model | Status |
|----------------|---------------|--------|---------|----------|--------|-------|--------|
| printerType | printer_type/type | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| printerName | name | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| printerIP | ip_address | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| printerWebcamUrl | webcam_url | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** (fixed 2026-01-07) |
| printerActive | is_enabled/is_active | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| accessCode | access_code | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| serialNumber | serial_number | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| ipaKey | api_key | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| location | location | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** (fixed 2026-01-07) |
| description | description | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** (fixed 2026-01-07) |

### Fixed Flows (2026-01-07)

#### `location` - FIXED
- **Migration**: `024_add_printer_metadata.sql` added column
- **Model**: `Printer.location` field added
- **Config**: `PrinterConfig.location` field added
- **Service**: `create_printer()` and `update_printer()` now persist location

#### `description` - FIXED
- **Migration**: `024_add_printer_metadata.sql` added column
- **Model**: `Printer.description` field added
- **Config**: `PrinterConfig.description` field added
- **Service**: `create_printer()` and `update_printer()` now persist description

---

## 2. Job Form Audit

### Form Locations
- **Create Form**: `frontend/index.html` lines 2655-2710
- **Edit Form**: Dynamic in `frontend/js/jobs.js` lines 1007-1074
- **Handler**: `frontend/js/jobs.js`

### Field Status

| Frontend Field | Backend Field | Router | Service | Repository | Database | Model | Status |
|----------------|---------------|--------|---------|------------|----------|-------|--------|
| jobName | job_name | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| printerSelect | printer_id | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| isBusiness | is_business | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| fileSelect | file_id | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** (fixed 2026-01-07) |
| customerName | customer_name | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** (fixed 2026-01-07) |
| materialCost | material_cost | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** (fixed 2026-01-07) |

### Fixed Flows (2026-01-07)

#### `file_id` - FIXED
- **Migration**: `025_add_job_file_id.sql` added column
- **Model**: `JobCreate.file_id` field added
- **Service**: `create_job()` now persists file_id
- **Repository**: `job_repository.create()` includes file_id in INSERT

#### `customer_name` - FIXED
- **Model**: `JobCreate.customer_name` field added
- **Service**: `create_job()` merges customer_name into customer_info JSON

#### `material_cost` - FIXED
- **Model**: `JobCreate.material_cost` and `JobUpdateRequest.material_cost` fields added
- **Service**: `create_job()` now persists material_cost

---

## 3. Material Form Audit

### Form Location
- **Form**: `frontend/index.html` lines 2449-2541
- **Handler**: `frontend/js/materials.js`

### Field Status

| Frontend Field | Backend Field | Router | Service | Database | Model | Status |
|----------------|---------------|--------|---------|----------|-------|--------|
| materialType | material_type | ✓ | ✓ | ✓ | ✓ | **OK** |
| materialBrand | brand/vendor | ✓ | ✓ | ✓ | ✓ | **OK** |
| materialColor | color | ✓ | ✓ | ✓ | ✓ | **OK** |
| materialSpoolWeight | weight | ✓ | ✓ | ✓ | ✓ | **OK** |
| materialRemainingWeight | remaining_weight | ✓ | ✓ | ✓ | ✓ | **OK** |
| materialPricePerKg | cost_per_kg | ✓ | ✓ | ✓ | ✓ | **OK** |
| materialDiameter | diameter | ✓ | ✓ | ✓ | ✓ | **OK** |
| materialNotes | notes | ✓ | ✓ | ✓ | ✓ | **OK** |
| materialColorHex | color_hex | ✓ | ✓ | ✓ | ✓ | **OK** (fixed 2026-01-07) |
| materialLocation | location | ✓ | ✓ | ✓ | ✓ | **OK** (fixed 2026-01-07) |
| materialIsActive | is_active | ✓ | ✓ | ✓ | ✓ | **OK** (fixed 2026-01-07) |

### Fixed Flows (2026-01-07)

#### `color_hex` - FIXED
- **Migration**: `026_add_material_fields.sql` added column
- **Model**: `MaterialSpool.color_hex`, `MaterialCreate.color_hex`, `MaterialUpdate.color_hex` fields added
- **Service**: `create_material()` and `update_material()` now persist color_hex
- **Router**: `MaterialResponse.color_hex` included in API responses
- **Frontend**: `saveMaterial()` extracts color_hex from form

#### `location` - FIXED
- **Migration**: `026_add_material_fields.sql` added column
- **Model**: `MaterialSpool.location`, `MaterialCreate.location`, `MaterialUpdate.location` fields added
- **Service**: `create_material()` and `update_material()` now persist location
- **Router**: `MaterialResponse.location` included in API responses
- **Frontend**: `saveMaterial()` extracts location from form

#### `is_active` - FIXED
- **Migration**: `026_add_material_fields.sql` added column with DEFAULT 1
- **Model**: `MaterialSpool.is_active`, `MaterialCreate.is_active`, `MaterialUpdate.is_active` fields added
- **Service**: `create_material()` and `update_material()` now persist is_active
- **Router**: `MaterialResponse.is_active` included in API responses
- **Frontend**: `saveMaterial()` extracts is_active from checkbox

---

## Root Cause Analysis

### Why These Issues Occurred

1. **Multi-layer architecture**: Adding a field requires changes to 4-6 files:
   - Frontend form (HTML)
   - Frontend handler (JS)
   - API request model
   - Service layer
   - Database schema/migration
   - Domain model

2. **Silent failures**: Using `getattr(obj, 'field', None)` in responses masks missing fields

3. **No end-to-end field validation**: No automated check that frontend fields reach the database

4. **Incremental additions**: Fields added to API without completing the full stack

### Prevention Strategies

1. **Field addition checklist**: Document all files that need updating for new fields
2. **Integration tests**: Add tests that verify field persistence round-trip
3. **API response validation**: Ensure returned data matches what was submitted
4. **Database migrations**: Always pair API changes with migrations

---

## Files Modified in Fix

### Phase 1: Printer location/description
- `migrations/024_add_printer_metadata.sql` - NEW
- `src/models/printer.py` - Added location, description fields
- `src/services/config_service.py` - Added to PrinterConfig
- `src/services/printer_service.py` - Persist in create/update
- `src/api/routers/printers.py` - Removed getattr() fallbacks

### Phase 2: Job file_id/material_cost/customer_name
- `migrations/025_add_job_file_id.sql` - NEW
- `src/models/job.py` - Added to JobCreate/JobUpdateRequest
- `src/services/job_service.py` - Handle in create/update
- `src/database/repositories/job_repository.py` - Add file_id to INSERT

### Phase 3: Material color_hex/location/is_active
- `migrations/026_add_material_fields.sql` - NEW
- `src/models/material.py` - Added to MaterialSpool/Create/Update
- `src/services/material_service.py` - Persist fields
- `src/api/routers/materials.py` - Added to MaterialResponse
- `frontend/js/materials.js` - Extract fields in saveMaterial()

---

## Verification Checklist

When adding a new field, verify:

- [x] HTML form input exists with correct name attribute
- [x] JavaScript collects and sends the field
- [x] API request model includes the field
- [x] API router extracts the field
- [x] Service layer accepts and passes the field
- [x] Repository/Database layer persists the field
- [x] Database column exists (run migration)
- [x] Domain model includes the field
- [x] API response includes the field
- [x] Frontend displays the saved value on edit
