# OpenPrintTag Integration Proposal

## Overview

This document outlines potential integration strategies for incorporating **OpenPrintTag** NFC technology into Printernizer's material management system.

## What is OpenPrintTag?

**OpenPrintTag** is an open-source NFC standard for 3D printing filament spools announced by Prusa Research in October 2025.

### Key Principles

1. **Writable/Offline-First**: All essential data stored directly on the NFC tag
   - Material type, brand, color
   - Print settings (temperature, speeds)
   - Total weight and remaining filament weight
   - Works locally without Wi-Fi or cloud services

2. **Open-Source**: Free to use and extend
   - No licensing fees
   - Works across brands
   - Fully extensible for custom data (batch numbers, material properties)

3. **Reusable**: Tags can be reprogrammed
   - Update data when depleted
   - Reuse on new spools or refills
   - Donut-shaped stickers for easy application

### Industry Adoption

- **Prusa Research**: All new Prusament spools include OpenPrintTag
- **Manufacturers on board**: 3D Fuel, Numakers, Filament PM, Fillamentum, Polar Filament, Printed Solid
- **Specification**: Available at specs.openprinttag.org

## Current Printernizer Material System

Printernizer already has a comprehensive material management system:

### Database Models

**MaterialSpool** (`src/models/material.py`)
- Physical properties: `material_type`, `brand`, `color`, `diameter`, `weight`
- Inventory tracking: `remaining_weight`, `remaining_percentage`
- Financial: `cost_per_kg`, `remaining_value`, `total_cost`
- Printer assignment: `printer_id` (which printer has it loaded)
- Purchase metadata: `purchase_date`, `vendor`, `batch_number`, `notes`

**MaterialConsumption** (`src/models/material.py`)
- Per-job tracking: `job_id`, `material_id`, `weight_used`, `cost`
- Analytics: `print_time_hours`, `file_name`

**Database Tables** (`src/database/database.py`)
- `materials` - Spool inventory with foreign key to printers
- `material_consumption` - Job-based consumption tracking

### Features

- **Spool Management**: Track individual spools with low-stock alerts (<20%)
- **Consumption Tracking**: Per-job material usage with automatic cost calculation
- **Cost Analysis**: Material costs + power costs for business vs private jobs
- **Reporting**: Consumption by type/brand/color, efficiency metrics, CSV export
- **API Integration**: Bambu Lab extracts filament weight from G-code, Prusa via PrusaLink

## Integration Options

### Option 1: NFC Tag Sync - Bidirectional Updates

**Concept**: Keep OpenPrintTag NFC tags and Printernizer database synchronized

**Features**:
- **Tag Reading**: Scan NFC tags when loading spools to auto-populate material database
- **Tag Writing**: Update tag's remaining weight after each print job
- **Conflict Resolution**: Choose between tag data vs database if they differ
- **Offline-First**: Tag is source of truth, database is cache/analytics layer

**Hardware Requirements**:
- USB NFC reader (PN532, ACR122U, RC522)
- Phone app for tag management
- Or printer-integrated NFC (if supported)

**Workflow**:
```
1. User loads new spool → Scan NFC tag
2. Printernizer reads: material_type, brand, color, diameter, total_weight, remaining_weight, cost_per_kg
3. Creates MaterialSpool in database
4. After print job → Calculate consumption → Update database AND write back to NFC tag
5. Next load → Tag shows current remaining weight
```

**Pros**:
- Physical tag always reflects current state
- Works offline (tag readable by any OpenPrintTag-compatible printer)
- True bidirectional sync

**Cons**:
- Requires NFC write hardware
- Tag write failures need handling
- More complex implementation

---

### Option 2: Printernizer as OpenPrintTag Management Hub

**Concept**: Printernizer becomes the central tool for managing OpenPrintTag spools

**Features**:
- **Tag Programming Interface**: Web UI to write blank NFC tags with material data
- **Bulk Tag Management**: Program multiple tags for spool refills
- **Tag History**: Track tag lifecycle (original spool → refills → decommission)
- **Export Tag Data**: Generate OpenPrintTag JSON for external tools
- **Template System**: Pre-configured templates for common materials

**Use Cases**:
- Print farms preparing tagged spools in advance
- Users with refillable spools can reprogram tags
- Creating custom tags for generic filament
- Standardizing spool data across organization

**Pros**:
- Adds value for print farms and power users
- Centralized management of all spool data
- Can work with both tagged and untagged spools

**Cons**:
- Requires NFC write hardware
- More complex UI/UX for tag programming

---

### Option 3: OpenPrintTag as Import/Export Format

**Concept**: Use OpenPrintTag schema as standard data exchange format

**Features**:
- **Import from Tags**: Scan tags to quickly add materials to inventory
- **Export to Tags**: Generate OpenPrintTag JSON files for physical tagging
- **Integration with Spoolman/OctoPrint**: Import/export with other tools using OpenPrintTag format
- **QR Code Alternative**: Generate QR codes with OpenPrintTag JSON for non-NFC scenarios
- **Batch Import**: Import multiple spools from JSON files

**Workflow**:
```
1. Scan NFC tag or import JSON file
2. Parse OpenPrintTag format
3. Map to Printernizer MaterialSpool model
4. Optionally extend with Printernizer-specific fields (cost_per_kg, business tracking)
```

**Pros**:
- Standards-based interoperability
- Works without dedicated NFC hardware (JSON import/export)
- QR codes as fallback for NFC

**Cons**:
- Less integrated than bidirectional sync
- Manual export step if user wants updated tags

---

### Option 4: Hybrid Manual + NFC System (RECOMMENDED)

**Concept**: Support both manual entry (current system) and NFC reading (optional enhancement)

**Features**:
- **Current System Preserved**: Manual material entry still works
- **NFC Enhancement**: "Scan Tag" button for quick data population
- **Partial Tag Support**: Use tag for initial data, manage consumption in Printernizer
- **Tag Generation**: Export existing materials as OpenPrintTag format for DIY tagging
- **Gradual Adoption**: Users can adopt NFC at their own pace

**Implementation Phases**:

**Phase 1**: NFC Reading (Read-Only)
- Add `nfc_tag_uid` field to MaterialSpool model
- "Scan Tag" button in material creation form
- Parse OpenPrintTag JSON schema
- Auto-populate form fields from tag data
- Keep existing manual workflow intact

**Phase 2**: Tag Writing (Bidirectional)
- Update NFC tags after print jobs complete
- Sync remaining weight back to physical tags
- Low-stock alerts write to tag
- Optional: Auto-write on manual spool updates

**Phase 3**: Tag Management Hub
- Create new tags for refillable spools
- Print farm spool preparation workflow
- Tag history and lifecycle tracking

**Pros**:
- Backwards compatible
- No breaking changes to existing workflows
- Users without NFC hardware unaffected
- Incremental complexity
- Best for enterprise (supports both manual and automated workflows)

**Cons**:
- Feature parity might confuse some users (two ways to do same thing)
- Need clear UI/UX to guide users

---

## Technical Architecture

### Database Schema Changes

**Add to MaterialSpool**:
```python
class MaterialSpool:
    nfc_tag_uid: Optional[str] = None  # Unique NFC tag identifier (e.g., "04:12:34:56:78:90:00")
    openprinttag_version: Optional[str] = None  # OpenPrintTag spec version (e.g., "1.0")
    last_nfc_sync: Optional[datetime] = None  # When tag was last read/written
    tag_data_hash: Optional[str] = None  # Hash of last tag data to detect changes
```

**New Table: nfc_tag_history** (Optional - for advanced tracking)
```sql
CREATE TABLE nfc_tag_history (
    id TEXT PRIMARY KEY,
    tag_uid TEXT NOT NULL,
    material_id TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'read', 'write', 'created', 'reused'
    data_snapshot TEXT,  -- JSON snapshot of tag data
    timestamp TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES materials(id)
)
```

### OpenPrintTag Schema Mapping

**Assumed OpenPrintTag Schema** (to be confirmed from specs.openprinttag.org):
```json
{
  "version": "1.0",
  "manufacturer": "Prusament",
  "material": {
    "type": "PLA",
    "brand": "Prusament",
    "color": "Galaxy Black",
    "colorHex": "#1a1a2e",
    "diameter": 1.75,
    "weight": 1000,
    "remainingWeight": 750
  },
  "settings": {
    "nozzleTemp": 215,
    "bedTemp": 60,
    "printSpeed": 100,
    "retraction": 0.8
  },
  "metadata": {
    "batchNumber": "PLA-2024-11-001",
    "productionDate": "2024-11-01",
    "expiryDate": "2026-11-01"
  }
}
```

**Mapping to Printernizer**:
```python
# OpenPrintTag → Printernizer MaterialSpool
material_type = tag_data['material']['type']  # → MaterialType enum
brand = tag_data['material']['brand']  # → MaterialBrand enum
color = tag_data['material']['color']  # → MaterialColor enum (or custom)
diameter = tag_data['material']['diameter']  # → diameter (mm)
weight = tag_data['material']['weight'] / 1000  # grams → kg
remaining_weight = tag_data['material']['remainingWeight'] / 1000  # grams → kg
batch_number = tag_data['metadata']['batchNumber']  # → batch_number
purchase_date = tag_data['metadata']['productionDate']  # → purchase_date
vendor = tag_data['manufacturer']  # → vendor

# Printernizer-specific (not in OpenPrintTag)
cost_per_kg = None  # User must enter manually
printer_id = None  # Assigned when loaded
notes = f"Imported from OpenPrintTag UID: {tag_uid}"
```

### NFC Hardware Integration

**Supported Readers**:
- **USB NFC Readers**: PN532, ACR122U, RC522
- **Raspberry Pi HATs**: NFC/RFID modules for headless deployments
- **ESPHome NFC**: For Home Assistant integration (PN532 via I2C/SPI)
- **Phone Apps**: Mobile NFC reading → API upload

**Python Libraries**:
- `nfcpy` - Pure Python NFC library (USB readers)
- `pn532` - Raspberry Pi NFC library
- `MFRC522-python` - RC522 module support
- Custom ESPHome → MQTT bridge for HA deployments

**API Endpoints** (new):
```python
# NFC Tag Management
POST /api/materials/nfc/scan          # Scan and parse NFC tag
POST /api/materials/nfc/write         # Write data to NFC tag
GET /api/materials/nfc/readers        # List available NFC readers
GET /api/materials/{id}/nfc-export    # Export material as OpenPrintTag JSON
POST /api/materials/import-tags       # Batch import from JSON files
```

### Multi-Spool Job Handling

**Challenge**: Bambu Lab AMS (4 spools), Prusa MMU (5 spools) use multiple materials per job

**Solution**:
```python
# Extend MaterialConsumption for multi-material jobs
class MaterialConsumption:
    job_id: str
    consumptions: List[SingleMaterialConsumption]  # One per material/color

class SingleMaterialConsumption:
    material_id: str
    weight_used: float  # grams
    cost: Decimal
    color_index: int  # Which AMS slot (0-3) or MMU slot (0-4)
```

**G-code Parsing Enhancement**:
```python
# Bambu Lab G-code includes per-filament data
# ; filament used [g] = 45.2,12.3,0,0  (4 values for AMS slots)
# Parse and create multiple MaterialConsumption records
```

---

## Implementation Roadmap

### Phase 1: Foundation (Read-Only NFC)

**Tasks**:
1. **Research**: Access specs.openprinttag.org for official schema
2. **Database Migration**: Add `nfc_tag_uid`, `openprinttag_version`, `last_nfc_sync` to materials table
3. **NFC Service**: Create `src/services/nfc_service.py`
   - Detect available NFC readers
   - Read NDEF records from tags
   - Parse OpenPrintTag JSON format
4. **API Endpoint**: `POST /api/materials/nfc/scan`
5. **UI Enhancement**: Add "Scan NFC Tag" button to material creation form
6. **Testing**: Support USB readers (ACR122U, PN532)

**Deliverables**:
- Users can scan existing OpenPrintTag spools
- Auto-populate material form from tag data
- Backward compatible (manual entry still works)

### Phase 2: Bidirectional Sync (Tag Writing)

**Tasks**:
1. **Write Support**: Implement NDEF write operations
2. **Auto-Update**: After print job completes, update tag's `remainingWeight`
3. **Conflict Resolution**: Handle tag vs database discrepancies
4. **API Endpoint**: `POST /api/materials/nfc/write`
5. **UI**: "Sync to Tag" button in material detail view
6. **Alerts**: Warn if tag write fails, queue for retry

**Deliverables**:
- Tags reflect current remaining weight
- Seamless offline-first workflow
- Works with any OpenPrintTag-compatible printer

### Phase 3: Tag Management Hub

**Tasks**:
1. **Tag Programming UI**: Create new tags from scratch
2. **Templates**: Pre-configured material templates (common PLA/PETG brands)
3. **Bulk Operations**: Program 10 tags at once for print farm
4. **Tag History**: Track tag lifecycle and reuse
5. **Export**: Generate OpenPrintTag JSON for external tools
6. **QR Codes**: Alternative to NFC for quick mobile scanning

**Deliverables**:
- Full tag lifecycle management
- Print farm workflow optimization
- Integration with Spoolman, OctoPrint, etc.

### Phase 4: Advanced Features

**Tasks**:
1. **Auto-Detection**: Detect when Bambu Lab/Prusa loads tagged spool (if API supports)
2. **Multi-Material**: Track per-color consumption for AMS/MMU jobs
3. **Home Assistant**: ESPHome NFC integration for automated scanning
4. **Mobile App**: Companion app for NFC scanning via phone
5. **AI Prediction**: Predict when spools will run out based on usage patterns

---

## Deployment Considerations

### Python Standalone
- USB NFC reader support
- Direct hardware access via `nfcpy`
- Configuration: `.env` file with `NFC_READER_TYPE=usb`

### Docker Standalone
- USB passthrough for NFC readers
- `docker-compose.yml` device mapping: `/dev/bus/usb`
- Privileged mode may be required

### Home Assistant Add-on
- **ESPHome Integration**: Separate ESP32 with PN532 NFC module
- **MQTT Bridge**: NFC scans → MQTT topic → Printernizer API
- **HA Automations**: Trigger on NFC scan, update entities
- **Ingress Compatibility**: NFC scan button in web UI calls HA service

**Example ESPHome Config**:
```yaml
esphome:
  name: printernizer-nfc

binary_sensor:
  - platform: pn532
    uid: !lambda 'return {0x04, 0x12, 0x34, 0x56, 0x78, 0x90, 0x00};'
    on_press:
      - mqtt.publish:
          topic: "printernizer/nfc/scan"
          payload: !lambda 'return tag.get_uid();'
```

---

## Open Questions

### Hardware & Deployment
1. **Target NFC hardware**: Which readers should be prioritized?
   - USB readers for standalone/Docker?
   - ESPHome for Home Assistant?
   - Phone app for mobile scanning?

2. **Deployment priority**: Which deployment mode gets NFC first?
   - Standalone Python (easiest for USB readers)
   - Home Assistant (best for automation)
   - Docker (enterprise use case)

### Workflow & UX
3. **Primary use case**:
   - Auto-detect spools when loaded on printer? (requires printer-integrated NFC)
   - Manual scan before loading? (USB reader at workstation)
   - Phone app to scan → sync to Printernizer? (mobile-first)

4. **Tag writing priority**:
   - Read-only (consume existing tagged spools)?
   - Bidirectional (update remaining weight back to tags)?
   - Tag programming (create new tags for untagged spools)?

### Data Architecture
5. **Source of truth**:
   - NFC tag is master, database is cache/analytics?
   - Database is master, tags are convenience layer?
   - Hybrid (tag for current state, database for history)?

6. **Consumption tracking**:
   - Update tag after every print? (requires NFC write access)
   - Only read tag initially, track consumption in DB?

### Integration Depth
7. **OpenPrintTag compliance level**:
   - Full spec implementation (requires official schema)?
   - Pragmatic subset (material type, color, weight, remaining)?
   - Extended with Printernizer-specific fields (cost_per_kg, business tracking)?

8. **Multi-spool jobs**:
   - How to handle prints using multiple materials? (Bambu AMS, Prusa MMU)
   - Track per-color consumption separately?
   - Associate multiple tags with one job?

### Future Vision
9. **Printer integration**:
   - Should Printernizer auto-detect when Bambu Lab/Prusa loads a tagged spool?
   - Or remain manual scan-based?
   - API support from printer manufacturers?

10. **Scale**:
    - Single printer, few spools? (simple USB reader)
    - Print farm, dozens of spools? (automated tracking, multiple readers)
    - Multi-location? (cloud sync between Printernizer instances)

---

## Recommendation

**Start with Option 4 (Hybrid Manual + NFC System)**

**Rationale**:
- **Backwards compatible**: Existing users unaffected
- **Incremental adoption**: Users can add NFC at their own pace
- **Enterprise-friendly**: Supports both manual (legacy) and automated (NFC) workflows
- **Low risk**: No breaking changes to existing material management
- **Extensible**: Foundation for future tag writing and management features

**Phase 1 Priority**: Read-only NFC tag scanning with USB reader support

**Phase 2**: Bidirectional sync for power users and print farms

**Phase 3**: Full tag management hub with programming capabilities

---

## References

- **OpenPrintTag Official Site**: https://openprinttag.org
- **Specification**: https://specs.openprinttag.org
- **Prusa Announcement**: https://blog.prusa3d.com/the-openprinttag-is-here-a-brand-new-nfc-tag-standard-for-smart-filament-is-now-shipped-with-a-new-redesigned-prusament-spool_123878/
- **Related Projects**:
  - OpenSpool: https://github.com/spuder/OpenSpool
  - openspoolman: https://github.com/drndos/openspoolman
  - SpoolEase: https://github.com/yanshay/SpoolEase

---

## Version History

- **2025-11-02**: Initial proposal document created
- **Future**: Update with official OpenPrintTag schema once specs.openprinttag.org is accessible
