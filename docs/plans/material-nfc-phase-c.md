# Material Management Phase C: NFC Smart Spools

**Status**: Future Implementation (After Phase B)
**Estimated Effort**: 2-3 days
**Dependencies**: Phase A (Basic UI) and Phase B (Integration) must be complete

## Overview

Phase C adds NFC tag reading and writing capabilities to transform ordinary filament spools into "smart spools" that carry their data with them. This enables seamless spool tracking across multiple print farms, automatic data population, and bidirectional sync between physical tags and digital inventory.

## Key Reference

**IMPORTANT**: A comprehensive 518-line specification already exists:
**Location**: `docs/archive/OPENPRINTTAG_INTEGRATION.md`

This document provides a high-level roadmap. For detailed technical specifications, protocol definitions, and implementation details, refer to the complete specification above.

---

## Goals

- **NFC Read Support**: Scan spool tags to auto-populate material data
- **Bidirectional Sync**: Write consumption/weight back to tags
- **OpenPrintTag Compliance**: Follow industry-standard protocol
- **Tag Management**: Bulk writing, health monitoring, import/export
- **Mobile Scanning**: Progressive Web App with NFC support
- **Optional HA Integration**: ESPHome bridge for Home Assistant users

## Non-Goals

- Proprietary tag formats (OpenPrintTag only)
- Desktop NFC readers (mobile/web only initially)
- Real-time tracking during print (async updates only)

---

## Technology Stack

### Web NFC API
- **Browser Support**: Chrome 89+, Edge 89+, Opera 76+
- **Platform**: Android only (iOS doesn't support Web NFC)
- **Spec**: https://w3c.github.io/web-nfc/
- **Tag Types**: NFC Forum Type 2/4/5, ISO-DEP

### OpenPrintTag Protocol
- **Standard**: Open-source filament spool tagging protocol
- **Data Format**: NDEF text records with JSON payload
- **Spec**: See existing doc for full protocol definition
- **Compatibility**: Prusa, Bambu Lab, and other manufacturers

### Optional: ESPHome Bridge
- **Use Case**: Non-Android devices, automated scanning
- **Platform**: ESP32 with PN532 NFC module
- **Integration**: MQTT with Home Assistant
- **Fallback**: Manual web NFC scanning still works

---

## Feature Overview

### Phase C.1: Read-Only NFC Scanning (Day 1)

**Capability**: Scan NFC tags to auto-populate spool data

**User Flow**:
```
1. User clicks [Scan NFC Tag] in add spool modal
2. Browser prompts for NFC permission
3. User taps phone to spool tag
4. Tag data read and parsed
5. Form auto-fills with tag data
6. User can edit and save
```

**UI Integration**:
```
┌─────────────────────────────────────┐
│ Neue Spule hinzufügen          [×] │
├─────────────────────────────────────┤
│                                     │
│ [📱 NFC-Tag scannen]  ← NEW BUTTON  │
│                                     │
│ ─── oder manuell eingeben ───      │
│                                     │
│ Material:     [PLA_ECO        ▼]   │
│ ...rest of form...                  │
└─────────────────────────────────────┘
```

**Supported Tag Data**:
- Material type (PLA, PETG, etc.)
- Brand
- Color
- Weight (initial)
- Cost per kg
- Purchase date
- Batch number
- Vendor
- Notes

### Phase C.2: Bidirectional Sync (Day 2)

**Capability**: Write consumption data back to tags

**Write Operations**:
1. **After Print**: Update remaining weight on tag
2. **Manual Update**: User updates weight → writes to tag
3. **Spool Loaded**: Mark tag as "in use" with printer ID
4. **Spool Unloaded**: Mark tag as "available"

**UI Enhancement**:
```
Material Card:
┌───────────────────────────┐
│ PLA ECO Red           [✏️]│
│ OVERTURE                  │
│ 📱 NFC: Synced ✅         │ ← NEW STATUS
│ Last sync: 2 min ago      │
│ [📱 Sync Now]             │ ← NEW BUTTON
└───────────────────────────┘
```

**Sync States**:
- ✅ **Synced**: Tag data matches database
- ⚠️ **Out of Sync**: Tag older than database
- ❌ **No Tag**: Spool created without tag
- 🔄 **Syncing**: Write in progress

### Phase C.3: Tag Management Hub (Day 2-3)

**Capabilities**:
- Bulk tag writing (provision new spools)
- Tag health monitoring (read/write errors)
- Import/export tag data
- Tag format/erase operations

**New UI Section**:
```
[Spulen] [Verbrauch] [NFC-Tags] ← NEW TAB
```

**Tag Management Interface**:
```
┌──────────────────────────────────────────┐
│ 📱 NFC-Tag Verwaltung                    │
├──────────────────────────────────────────┤
│ [Bulk Write] [Import] [Export]          │
├──────────────────────────────────────────┤
│ Tag ID      | Status   | Material       │
│─────────────|──────────|────────────────│
│ 04:A1:23... | ✅ Synced | PLA ECO Red   │
│ 04:B2:34... | ⚠️ Old    | PETG Blue     │
│ 04:C3:45... | ❌ Error  | TPU Black     │
├──────────────────────────────────────────┤
│ Health: 97% (3 errors in last 30 days)  │
└──────────────────────────────────────────┘
```

### Phase C.4: Advanced Features (Day 3)

#### Multi-Spool Detection (AMS/MMU)
- Detect multiple tags in range
- Map to AMS slots (A, B, C, D)
- Auto-load correct spool per extruder

#### Predictive Alerts
- Track usage rate per spool
- Predict when spool runs out
- Alert: "PLA Red will run out in 3 days (2 more prints)"

#### Home Assistant Integration
- **ESPHome NFC Bridge**: ESP32 with PN532 reader
- **MQTT Discovery**: Auto-create HA sensors
- **Automations**: Trigger actions on spool events
- **Dashboard**: Material inventory card

---

## OpenPrintTag Protocol (Summary)

**Full Specification**: See `docs/archive/OPENPRINTTAG_INTEGRATION.md`

### Data Structure
```json
{
  "version": "1.0",
  "manufacturer": "OVERTURE",
  "material": {
    "type": "PLA",
    "color": "RED",
    "colorHex": "#FF0000",
    "diameter": 1.75
  },
  "spool": {
    "weight": 1000,
    "remaining": 850,
    "purchaseDate": "2024-11-03",
    "batchNumber": "BATCH-2024-10"
  },
  "cost": {
    "perKg": 17.06,
    "total": 17.06,
    "currency": "EUR"
  },
  "vendor": {
    "name": "Amazon.de",
    "url": "https://amazon.de/..."
  },
  "tracking": {
    "lastUpdate": "2024-11-03T14:30:00Z",
    "printerId": "printer789",
    "status": "in_use"
  }
}
```

### NDEF Format
- **Record Type**: `text/json`
- **Language**: `en`
- **Encoding**: UTF-8
- **Max Size**: 888 bytes (NTAG216)

### Read/Write Operations
- **Read**: `navigator.nfc.scan()`
- **Write**: `navigator.nfc.write(records)`
- **Permissions**: Required on first use, cached

---

## Implementation Architecture

### Frontend Components

**File**: `frontend/js/nfc-manager.js` (new, ~400 lines)

```javascript
class NFCManager {
    constructor(materialsManager) {
        this.materialsManager = materialsManager;
        this.isSupported = 'NDEFReader' in window;
    }

    async checkSupport() {
        if (!this.isSupported) {
            throw new Error('NFC not supported on this device');
        }
    }

    async requestPermission() {
        const ndef = new NDEFReader();
        await ndef.scan(); // Triggers permission prompt
        ndef.stop();
    }

    async scanTag() {
        const ndef = new NDEFReader();
        await ndef.scan();

        return new Promise((resolve, reject) => {
            ndef.onreading = event => {
                const record = event.message.records[0];
                const text = new TextDecoder().decode(record.data);
                const data = JSON.parse(text);
                resolve(this.parseOpenPrintTag(data));
                ndef.stop();
            };

            ndef.onreadingerror = () => {
                reject(new Error('Failed to read NFC tag'));
                ndef.stop();
            };
        });
    }

    async writeTag(materialData) {
        const ndef = new NDEFReader();
        const openPrintTagData = this.buildOpenPrintTag(materialData);
        const jsonString = JSON.stringify(openPrintTagData);

        const record = {
            recordType: "text",
            data: jsonString
        };

        await ndef.write({ records: [record] });
    }

    parseOpenPrintTag(tagData) {
        // Convert OpenPrintTag format to MaterialCreate format
        return {
            material_type: this.mapMaterialType(tagData.material.type),
            brand: tagData.manufacturer,
            color: this.mapColor(tagData.material.color),
            diameter: tagData.material.diameter,
            weight: tagData.spool.weight,
            remaining_weight: tagData.spool.remaining || tagData.spool.weight,
            cost_per_kg: tagData.cost.perKg,
            purchase_date: tagData.spool.purchaseDate,
            vendor: tagData.vendor.name,
            batch_number: tagData.spool.batchNumber,
            notes: `NFC Tag ID: ${tagData.tracking?.tagId || 'unknown'}`
        };
    }

    buildOpenPrintTag(materialData) {
        // Convert MaterialSpool to OpenPrintTag format
        return {
            version: "1.0",
            manufacturer: materialData.brand,
            material: {
                type: materialData.material_type.replace('_', ' '),
                color: materialData.color,
                colorHex: this.getColorHex(materialData.color),
                diameter: materialData.diameter
            },
            spool: {
                weight: materialData.weight,
                remaining: materialData.remaining_weight,
                purchaseDate: materialData.purchase_date,
                batchNumber: materialData.batch_number
            },
            cost: {
                perKg: materialData.cost_per_kg,
                total: (materialData.weight / 1000) * materialData.cost_per_kg,
                currency: "EUR"
            },
            vendor: {
                name: materialData.vendor
            },
            tracking: {
                lastUpdate: new Date().toISOString(),
                printerId: materialData.printer_id || null,
                status: materialData.printer_id ? "in_use" : "available"
            }
        };
    }

    // ... helper methods ...
}
```

### Backend Enhancements

**File**: `src/models/material.py` (enhance existing)

Add NFC-related fields:
```python
@dataclass
class MaterialSpool:
    # ... existing fields ...

    # NFC tracking fields
    nfc_tag_id: Optional[str] = None
    nfc_last_sync: Optional[datetime] = None
    nfc_sync_status: str = "none"  # none, synced, out_of_sync, error
```

**File**: `src/api/routers/materials.py` (new endpoints)

```python
@router.post("/{material_id}/sync-nfc")
async def sync_nfc_tag(
    material_id: str,
    tag_data: dict,
    service: MaterialService = Depends(get_material_service)
):
    """Update NFC tag with current material data."""
    material = await service.get_material(material_id)
    if not material:
        raise HTTPException(status_code=404)

    # Update NFC sync status
    await service.update_material(material_id, {
        "nfc_tag_id": tag_data.get("tagId"),
        "nfc_last_sync": datetime.now(),
        "nfc_sync_status": "synced"
    })

    return {"message": "NFC tag synced successfully"}
```

### Database Migration

```sql
-- Add NFC tracking columns
ALTER TABLE materials ADD COLUMN nfc_tag_id TEXT NULL;
ALTER TABLE materials ADD COLUMN nfc_last_sync TIMESTAMP NULL;
ALTER TABLE materials ADD COLUMN nfc_sync_status TEXT DEFAULT 'none';

CREATE INDEX idx_materials_nfc_tag_id ON materials(nfc_tag_id);
```

---

## Progressive Web App (PWA) Enhancement

To enable NFC scanning, Printernizer must be served over HTTPS and optionally installed as a PWA.

### Requirements
- HTTPS (required for Web NFC API)
- Service Worker (for offline support)
- Web App Manifest (for installability)

### manifest.json
```json
{
  "name": "Printernizer",
  "short_name": "Printernizer",
  "description": "3D Printer Management with NFC Spool Tracking",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#007bff",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "permissions": [
    "nfc"
  ]
}
```

---

## Home Assistant Integration (Optional)

### ESPHome NFC Bridge

**Hardware**:
- ESP32 development board
- PN532 NFC module
- USB power supply

**ESPHome Configuration**:
```yaml
esphome:
  name: printernizer-nfc-bridge

esp32:
  board: esp32dev

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

mqtt:
  broker: homeassistant.local

pn532_i2c:
  cs_pin: GPIO5

binary_sensor:
  - platform: pn532
    name: "NFC Tag"
    on_press:
      then:
        - mqtt.publish:
            topic: "printernizer/nfc/tag_detected"
            payload: !lambda 'return x;'
```

### Home Assistant Sensors

Auto-discovered via MQTT:
```yaml
sensor:
  - platform: mqtt
    name: "PLA Red Remaining"
    state_topic: "printernizer/materials/mat456/remaining"
    unit_of_measurement: "g"
    icon: "mdi:printer-3d-nozzle"

  - platform: mqtt
    name: "Total Material Value"
    state_topic: "printernizer/materials/total_value"
    unit_of_measurement: "€"
    icon: "mdi:currency-eur"
```

### Automations
```yaml
automation:
  - alias: "Low Spool Alert"
    trigger:
      platform: mqtt
      topic: "printernizer/events/material_low_stock"
    action:
      service: notify.mobile_app
      data:
        message: "{{ trigger.payload_json.material_name }} is running low ({{ trigger.payload_json.remaining }}%)"
```

---

## Implementation Plan

### Day 1: Read-Only NFC (8 hours)

**Morning** (4 hours):
1. Add Web NFC API support detection
2. Create NFCManager class
3. Implement tag reading
4. Parse OpenPrintTag format

**Afternoon** (4 hours):
5. Add [Scan NFC] button to add modal
6. Auto-fill form from tag data
7. Test with physical NFC tags
8. Handle errors (unsupported browser, no tag found)

### Day 2: Bidirectional Sync (8 hours)

**Morning** (4 hours):
1. Implement tag writing
2. Build OpenPrintTag output format
3. Add database fields for NFC tracking
4. Create sync API endpoints

**Afternoon** (4 hours):
5. Add [Sync Now] button to cards
6. Show sync status indicators
7. Automatic sync after consumption
8. Test bidirectional sync

### Day 3: Tag Management & Polish (8 hours)

**Morning** (4 hours):
1. Create NFC Tags management page
2. Implement bulk write functionality
3. Add import/export features
4. Tag health monitoring

**Afternoon** (4 hours):
5. PWA enhancements (manifest, service worker)
6. Error handling improvements
7. User documentation
8. End-to-end testing

### Optional: Home Assistant Integration (+ 4-8 hours)

- ESPHome bridge setup (hardware + config)
- MQTT discovery implementation
- Sensor creation
- Example automations
- Documentation

**Total: 24-32 hours (3-4 days including HA integration)**

---

## Testing Strategy

### Device Testing
- [ ] Android phone with Chrome
- [ ] Android phone with Edge
- [ ] Various NFC tag types (NTAG213, NTAG216)
- [ ] Multiple tags in sequence
- [ ] Tag read errors
- [ ] Tag write errors

### Integration Testing
- [ ] Scan → Create spool
- [ ] Edit spool → Write tag
- [ ] Job completes → Update tag
- [ ] Load/unload → Update tag status
- [ ] Multiple spools with tags
- [ ] Tags without database records

### Error Scenarios
- [ ] NFC not supported (show message)
- [ ] Permission denied
- [ ] No tag found (timeout)
- [ ] Invalid tag format
- [ ] Tag read error (retry)
- [ ] Tag write error (retry)

### Home Assistant Testing (if implemented)
- [ ] ESPHome bridge connects
- [ ] MQTT messages sent
- [ ] Sensors auto-discovered
- [ ] Sensor values update
- [ ] Automations trigger

---

## User Documentation

### Setup Guide

**Title**: "Using NFC Smart Spools"

**Sections**:
1. Requirements (Android device, NFC enabled)
2. First-time setup (grant permissions)
3. Scanning a spool (step-by-step with screenshots)
4. Writing to tags (auto-sync vs manual)
5. Bulk provisioning new tags
6. Troubleshooting

### Tag Purchase Recommendations

- **NTAG213**: 144 bytes, good for basic data
- **NTAG216**: 888 bytes, recommended (fits full OpenPrintTag)
- **ISO15693**: Compatible but larger, more expensive

**Where to buy**:
- Amazon: "NTAG216 NFC Tags"
- AliExpress: Bulk packs
- Local electronics shops

---

## Success Criteria

### Must Have
- [ ] Read NFC tags on Android
- [ ] Auto-fill form from tag data
- [ ] Write consumption back to tags
- [ ] Sync status indicators
- [ ] Error handling for unsupported devices

### Nice to Have
- [ ] Bulk tag writing
- [ ] Tag health monitoring
- [ ] PWA installation
- [ ] Offline support

### Optional (HA Integration)
- [ ] ESPHome bridge working
- [ ] MQTT sensors created
- [ ] Example automations provided

---

## Future Enhancements (Beyond Phase C)

- **iOS Support**: When/if Apple adds Web NFC API
- **Desktop NFC Readers**: USB NFC readers for desktop use
- **Cloud Sync**: Sync tags across multiple Printernizer instances
- **Tag Encryption**: Encrypt sensitive data on tags
- **Multi-Tag Operations**: Batch read/write operations
- **Tag Analytics**: Track tag read/write statistics

---

## References

### Specifications
- **OpenPrintTag Protocol**: `docs/archive/OPENPRINTTAG_INTEGRATION.md` (full spec)
- **Web NFC API**: https://w3c.github.io/web-nfc/
- **NDEF Format**: https://nfc-forum.org/

### Libraries
- **Web NFC API**: Native browser API (no library needed)
- **ESPHome**: https://esphome.io/
- **PN532 Component**: https://esphome.io/components/pn532.html

### Hardware
- **ESP32 DevKit**: ~$5-10
- **PN532 NFC Module**: ~$10-15
- **NTAG216 Tags**: ~$0.50 each (bulk)

---

## Conclusion

Phase C transforms Printernizer into a truly smart spool management system by leveraging NFC technology. Physical spools become self-describing, carrying their history and status with them. This enables:

- **Effortless Setup**: Scan tag to add spool
- **Automatic Tracking**: Consumption written back to tag
- **Portability**: Move spools between printers/systems
- **Compliance**: OpenPrintTag standard interoperability
- **Optional HA Integration**: Advanced home automation

The Web NFC API makes this accessible without dedicated hardware (Android phones work), while the optional ESPHome bridge extends support to all devices and enables Home Assistant integration.

**Note**: This is a high-level roadmap. For complete technical specifications, data formats, and implementation details, refer to the comprehensive 518-line specification in `docs/archive/OPENPRINTTAG_INTEGRATION.md`.
