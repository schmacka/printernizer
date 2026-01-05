# Filament Status Monitoring - Technical Implementation Plan

**Status:** Implementation Ready
**Created:** 2026-01-05
**Estimated Effort:** 23 hours (3-4 days)
**Target Version:** 2.12.0

---

## Executive Summary

This document provides a comprehensive technical implementation plan for adding live filament status monitoring to Printernizer. The feature will support both Bambu Lab's multi-material AMS (Automatic Material System) and Prusa's single-material filament sensors, displaying real-time filament information in the dashboard printer cards.

## Current State Analysis

### What Currently Works

**Manual Material Inventory Management:**
- Complete material spool tracking system (`/src/models/material.py`)
- Material consumption recording per job
- Low stock alerts (<20% threshold)
- Cost tracking and analytics
- Frontend materials page for manual inventory

**File-Based Filament Extraction:**
- G-code/3MF metadata parsing (`/src/services/bambu_parser.py`)
- Filament usage extraction (grams used per job)
- Filament ID mapping (GFL00-GFL53) to colors
- Cost calculation from file metadata

### What's Missing

**Live Printer Filament Status:**
- ❌ Real-time AMS slot status from Bambu Lab MQTT
- ❌ Current filament type/color/remaining displayed in dashboard
- ❌ Filament runout detection from Prusa sensors
- ❌ Active slot indication during multi-material prints
- ❌ Low stock warnings in printer cards

---

## Architecture Overview

### Data Flow

```
┌─────────────────┐
│  Bambu Printer  │
│   (MQTT API)    │
└────────┬────────┘
         │
         ├─→ MQTT Message: device/{serial}/report
         │   └─→ mqtt_data['ams']['tray'][0-3]
         │
         ▼
┌──────────────────────────────────────────┐
│  BambuLabPrinter._extract_ams_status()   │
│  - Parse tray_id, tray_type, tray_color  │
│  - Extract remain (percentage)           │
│  - Identify active slot (tray_now)       │
│  - Map filament_id → color_name          │
└──────────────┬───────────────────────────┘
               │
               ▼
┌─────────────────┐         ┌─────────────────┐
│  Prusa Printer  │         │ PrinterStatus   │
│   (HTTP API)    │         │     Update      │
└────────┬────────┘         │   (Model)       │
         │                  │                 │
         ├─→ GET /api/printer   ├─ status     │
         │   └─→ telemetry.filament  ├─ temps  │
         │       └─→ material        ├─ job    │
         │                  ├─ filament_status │
         ▼                  └─────────┬─────────┘
┌──────────────────────────────────────┐         │
│ PrusaPrinter._extract_filament_status()       │
│ - Check filament.loaded                       │
│ - Detect filament.runout                      │
│ - Extract material.type                       │
└──────────────┬────────────────────────         │
               │                                 │
               └─────────────────────────────────┤
                                                 │
                                                 ▼
                                    ┌──────────────────────┐
                                    │  API Response        │
                                    │  /api/v1/printers    │
                                    │                      │
                                    │  PrinterResponse     │
                                    │  + filament_status   │
                                    └──────────┬───────────┘
                                               │
                                               ▼
                                    ┌──────────────────────┐
                                    │  WebSocket Broadcast │
                                    │  printerStatusUpdate │
                                    └──────────┬───────────┘
                                               │
                                               ▼
                                    ┌──────────────────────┐
                                    │  Frontend Dashboard  │
                                    │  components.js       │
                                    │                      │
                                    │  PrinterCard:        │
                                    │  renderFilamentStatus()│
                                    └──────────────────────┘
```

---

## Phase 1: Backend Data Models

### File: `/src/models/printer.py`

**Location:** After line 78 (before `class Config`)

#### Add FilamentSlot Model

```python
class FilamentSlot(BaseModel):
    """
    Represents a single filament slot/tray.

    Used for both multi-material AMS systems (Bambu Lab) and single-material
    printers (Prusa). AMS systems typically have 4 slots (0-3), while
    single-material printers have one slot (0).
    """

    slot_id: int = Field(
        ...,
        description="Slot identifier (0-3 for AMS, 0 for single-material)",
        ge=0,
        le=15  # Support future expansion to larger AMS units
    )

    tray_id: Optional[str] = Field(
        None,
        description="Tray ID from AMS (Bambu Lab only, e.g., '1', '2')"
    )

    tray_type: Optional[str] = Field(
        None,
        description="Filament material type (PLA, PETG, TPU, ABS, ASA, etc.)"
    )

    tray_color: Optional[str] = Field(
        None,
        description="Color as hex code (#RRGGBB) or color name"
    )

    filament_id: Optional[str] = Field(
        None,
        description="Bambu Lab filament ID (e.g., 'GFL00' for black)"
    )

    color_name: Optional[str] = Field(
        None,
        description="Human-readable color name (e.g., 'Black', 'Red')"
    )

    remaining_percentage: Optional[float] = Field(
        None,
        description="Percentage of filament remaining (0.0-100.0)",
        ge=0.0,
        le=100.0
    )

    is_loaded: Optional[bool] = Field(
        None,
        description="Whether filament is currently loaded in this slot"
    )

    is_runout: Optional[bool] = Field(
        None,
        description="Whether filament runout sensor has been triggered"
    )

    material_name: Optional[str] = Field(
        None,
        description="Material name/brand from printer (e.g., 'Prusament PLA')"
    )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FilamentStatus(BaseModel):
    """
    Complete filament status for a printer.

    Supports both single-material printers (Prusa) and multi-material
    AMS systems (Bambu Lab). For single-material printers, `slots` will
    contain one FilamentSlot. For AMS systems, `slots` will contain
    multiple FilamentSlot objects (typically 4).
    """

    is_multi_material: bool = Field(
        False,
        description="Whether printer has multi-material system (e.g., Bambu AMS)"
    )

    active_slot: Optional[int] = Field(
        None,
        description="Currently active slot ID during printing (null if idle)"
    )

    slots: List[FilamentSlot] = Field(
        default_factory=list,
        description="List of filament slots/trays"
    )

    ams_id: Optional[str] = Field(
        None,
        description="AMS unit identifier (Bambu Lab only, e.g., '0', '1')"
    )

    has_runout_sensor: bool = Field(
        False,
        description="Whether printer has filament runout detection capability"
    )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

#### Extend PrinterStatusUpdate

**Location:** Line 77 (after `estimated_end_time`)

```python
    # Filament status information (optional)
    filament_status: Optional[FilamentStatus] = Field(
        None,
        description="Filament/AMS status information from printer"
    )
```

### Database Schema

**Decision:** No database migration required for Phase 1.

**Rationale:**
- Filament status is real-time data, ephemeral by nature
- Already stored in `printer_status_log` table's generic fields if logging enabled
- No immediate requirement to persist historical filament data
- Keeps implementation focused and reduces complexity

**Future Consideration:** If filament usage history tracking is desired later, create migration `016_add_filament_tracking.sql`:
```sql
ALTER TABLE printer_status_log ADD COLUMN filament_data TEXT;
CREATE INDEX idx_printer_status_log_filament
  ON printer_status_log(printer_id, recorded_at)
  WHERE filament_data IS NOT NULL;
```

---

## Phase 2: Bambu Lab AMS Data Extraction

### File: `/src/printers/bambu_lab.py`

#### Add Helper Method

**Location:** Around line 550 (class-level method)

```python
    def _extract_ams_status(self, mqtt_data: Dict[str, Any]) -> Optional[FilamentStatus]:
        """
        Extract AMS (Automatic Material System) filament status from MQTT data.

        Bambu Lab printers with AMS report filament status via MQTT messages.
        This method parses the AMS data structure to extract:
        - Loaded filament types, colors, and IDs
        - Remaining filament percentages
        - Active slot during printing

        Args:
            mqtt_data: MQTT dump from bambulabs_api.mqtt_dump() or self.latest_data

        Returns:
            FilamentStatus object with AMS slot data, or None if no AMS present

        MQTT Data Structure:
            {
              "ams": {
                "id": "0",
                "tray": [
                  {
                    "tray_id": "1",
                    "tray_type": "PLA",
                    "tray_color": "#000000",
                    "tray_id_name": "GFL00",  # Bambu filament ID
                    "remain": 85,  # Percentage (0-100) or grams
                    "tray_now": 1  # 1 = active, 0 = inactive
                  },
                  # ... slots 1-3
                ]
              }
            }

        Notes:
            - AMS data may be at mqtt_data['ams'] or mqtt_data['print']['ams']
            - 'remain' field: Values 0-100 are percentages, >100 treated as grams
            - Assumes 1000g = 100% for gram-to-percentage conversion
            - Uses filament_colors.py to map filament IDs to color names
        """
        try:
            # Import color mapping utility
            from src.services.filament_colors import extract_color_from_filament_id

            # Locate AMS data in MQTT structure
            ams_data = mqtt_data.get('ams')
            if not ams_data:
                # Try alternate location (some firmware versions)
                print_data = mqtt_data.get('print', {})
                ams_data = print_data.get('ams')

            if not ams_data or not isinstance(ams_data, dict):
                logger.debug(
                    "No AMS data in MQTT dump",
                    printer_id=self.printer_id,
                    mqtt_keys=list(mqtt_data.keys()) if isinstance(mqtt_data, dict) else None
                )
                return None

            # AMS can be single dict or list of units (multi-AMS support)
            ams_list = ams_data if isinstance(ams_data, list) else [ams_data]

            slots = []
            ams_id = None
            active_slot = None

            for ams_unit in ams_list:
                if not isinstance(ams_unit, dict):
                    continue

                # Extract AMS unit ID
                if ams_id is None:
                    ams_id = str(ams_unit.get('id', '0'))

                # Get tray information (typically array of 4 slots)
                trays = ams_unit.get('tray', [])
                if not isinstance(trays, list):
                    logger.warning(
                        "AMS tray data is not a list",
                        printer_id=self.printer_id,
                        tray_type=type(trays).__name__
                    )
                    continue

                for slot_idx, tray in enumerate(trays):
                    if not isinstance(tray, dict):
                        continue

                    # Extract tray fields
                    tray_id = tray.get('tray_id')
                    tray_type = tray.get('tray_type', '').strip()
                    tray_color = tray.get('tray_color', '').strip()
                    filament_id = tray.get('tray_id_name', '').strip()
                    remain = tray.get('remain')

                    # Check if this slot is currently active (printing from it)
                    is_active = tray.get('tray_now', 0) == 1
                    if is_active:
                        active_slot = slot_idx

                    # Map Bambu filament ID to human-readable color name
                    # e.g., "GFL00" → "Black", "GFL02" → "Red"
                    color_name = None
                    if filament_id:
                        try:
                            color_name = extract_color_from_filament_id(filament_id)
                        except Exception as e:
                            logger.debug(
                                "Failed to extract color from filament ID",
                                filament_id=filament_id,
                                error=str(e)
                            )

                    # Convert remaining filament to percentage
                    # MQTT reports either percentage (0-100) or grams (>100)
                    remaining_pct = None
                    if remain is not None:
                        try:
                            remain_float = float(remain)
                            if remain_float <= 100:
                                # Already a percentage
                                remaining_pct = remain_float
                            else:
                                # Assume grams, convert to percentage (1000g = 100%)
                                remaining_pct = min(100.0, (remain_float / 1000.0) * 100)
                        except (ValueError, TypeError) as e:
                            logger.warning(
                                "Invalid remain value",
                                printer_id=self.printer_id,
                                slot_id=slot_idx,
                                remain=remain,
                                error=str(e)
                            )

                    # Only add slot if it contains filament data
                    # (Empty slots may have tray_id but no tray_type)
                    if tray_id or tray_type or filament_id:
                        slot = FilamentSlot(
                            slot_id=slot_idx,
                            tray_id=str(tray_id) if tray_id else None,
                            tray_type=tray_type if tray_type else None,
                            tray_color=tray_color if tray_color else None,
                            filament_id=filament_id if filament_id else None,
                            color_name=color_name,
                            remaining_percentage=remaining_pct,
                            is_loaded=True,  # Presence in AMS indicates loaded
                            is_runout=False,  # AMS doesn't have per-slot runout sensors
                            material_name=tray_type  # Use type as name
                        )
                        slots.append(slot)

            # If no slots found, AMS might be empty or disconnected
            if not slots:
                logger.debug(
                    "No filament slots found in AMS data",
                    printer_id=self.printer_id,
                    ams_id=ams_id
                )
                return None

            logger.info(
                "Extracted AMS status",
                printer_id=self.printer_id,
                slot_count=len(slots),
                ams_id=ams_id,
                active_slot=active_slot
            )

            return FilamentStatus(
                is_multi_material=True,
                active_slot=active_slot,
                slots=slots,
                ams_id=ams_id,
                has_runout_sensor=True  # Bambu Lab AMS has detection capability
            )

        except Exception as e:
            logger.warning(
                "Failed to extract AMS status",
                printer_id=self.printer_id,
                error=str(e),
                exc_info=True
            )
            return None
```

#### Integrate into _get_status_bambu_api()

**Location:** After line 660 (after `mqtt_data = self.bambu_api.mqtt_dump()`)

```python
            # Extract filament/AMS status from MQTT data
            filament_status = None
            if mqtt_data:
                filament_status = self._extract_ams_status(mqtt_data)
```

**Update Return Statement** (around line 750):

```python
        return PrinterStatusUpdate(
            printer_id=self.printer_id,
            status=printer_status,
            message=message,
            temperature_bed=float(bed_temp),
            temperature_nozzle=float(nozzle_temp),
            progress=int(progress),
            current_job=current_job,
            current_job_file_id=current_job_file_id,
            current_job_has_thumbnail=current_job_has_thumbnail,
            current_job_thumbnail_url=(
                file_url(current_job_file_id, 'thumbnail')
                if current_job_file_id and current_job_has_thumbnail
                else None
            ),
            remaining_time_minutes=remaining_time_minutes,
            estimated_end_time=estimated_end_time,
            elapsed_time_minutes=elapsed_time_minutes,
            print_start_time=print_start_time,
            timestamp=datetime.now(),
            filament_status=filament_status,  # ADD THIS LINE
            raw_data=mqtt_data
        )
```

#### Integrate into _get_status_mqtt() Fallback

**Location:** After line 936 (in fallback MQTT parsing)

```python
            # Extract AMS status from MQTT data
            filament_status = self._extract_ams_status(self.latest_data)
```

**Update Return Statement** (around line 937):

```python
        return PrinterStatusUpdate(
            printer_id=self.printer_id,
            status=printer_status,
            message=message,
            temperature_bed=float(bed_temp),
            temperature_nozzle=float(nozzle_temp),
            progress=int(progress),
            current_job=current_job,
            timestamp=datetime.now(),
            filament_status=filament_status,  # ADD THIS LINE
            raw_data=self.latest_data
        )
```

---

## Phase 3: Prusa Filament Sensor Extraction

### File: `/src/printers/prusa.py`

#### Add Helper Method

**Location:** Around line 150 (before `get_status()`)

```python
    def _extract_filament_status(self, status_data: Dict[str, Any]) -> Optional[FilamentStatus]:
        """
        Extract filament sensor status from PrusaLink API response.

        Prusa printers report filament sensor data via the /api/printer endpoint.
        Unlike Bambu Lab's multi-material AMS, Prusa uses a single filament setup
        with basic runout detection.

        Args:
            status_data: Status response from /api/printer endpoint

        Returns:
            FilamentStatus with single slot, or None if no sensor data

        API Data Structure:
            {
              "telemetry": {
                "filament": {
                  "sensor": true,
                  "loaded": true,
                  "runout": false,
                  "type": "PLA"
                },
                "material": {
                  "type": "PLA",
                  "name": "Prusament PLA",
                  "color": "#FF0000"
                }
              }
            }

        Notes:
            - Filament data may be in telemetry.filament, telemetry.material, or both
            - Prusa does NOT report remaining filament amount
            - Only basic load/runout detection available
            - Material color is sometimes provided as hex code
        """
        try:
            # Extract telemetry data
            telemetry = status_data.get('telemetry', {})
            filament_data = telemetry.get('filament', {})
            material_data = telemetry.get('material')

            # Check if printer has filament sensor
            has_sensor = (
                filament_data.get('sensor', False) or
                filament_data.get('loaded') is not None or
                material_data is not None
            )

            if not has_sensor:
                logger.debug(
                    "No filament sensor data available",
                    printer_id=self.printer_id
                )
                return None

            # Extract filament state
            is_loaded = filament_data.get('loaded', False)
            is_runout = filament_data.get('runout', False)
            filament_type = filament_data.get('type')

            # Get material information if available
            material_name = None
            material_color = None
            if material_data and isinstance(material_data, dict):
                material_name = material_data.get('name') or material_data.get('type')
                material_color = material_data.get('color')

            # Fallback: use filament type if material name not set
            if not material_name and filament_type:
                material_name = filament_type

            # Create single slot for Prusa (slot 0 = only slot)
            slot = FilamentSlot(
                slot_id=0,
                tray_id=None,  # Prusa doesn't use tray IDs
                tray_type=material_name,
                tray_color=material_color,
                filament_id=None,  # Prusa doesn't use Bambu filament IDs
                color_name=None,  # Prusa doesn't provide standardized color names
                remaining_percentage=None,  # Prusa doesn't report remaining amount
                is_loaded=is_loaded,
                is_runout=is_runout,
                material_name=material_name
            )

            logger.info(
                "Extracted Prusa filament status",
                printer_id=self.printer_id,
                is_loaded=is_loaded,
                is_runout=is_runout,
                material=material_name
            )

            return FilamentStatus(
                is_multi_material=False,  # Prusa Core One is single-material
                active_slot=0 if is_loaded else None,
                slots=[slot] if (is_loaded or material_name) else [],
                ams_id=None,
                has_runout_sensor=has_sensor
            )

        except Exception as e:
            logger.warning(
                "Failed to extract filament status",
                printer_id=self.printer_id,
                error=str(e),
                exc_info=True
            )
            return None
```

#### Integrate into get_status()

**Location:** After line 211 (after temperature extraction)

```python
            # Extract filament sensor status
            filament_status = self._extract_filament_status(status_data)
```

**Update Return Statement** (around line 340):

```python
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=printer_status,
                message=message,
                temperature_bed=float(bed_temp),
                temperature_nozzle=float(nozzle_temp),
                progress=int(progress),
                current_job=current_job,
                current_job_file_id=current_job_file_id,
                current_job_has_thumbnail=current_job_has_thumbnail,
                current_job_thumbnail_url=(
                    file_url(current_job_file_id, 'thumbnail')
                    if current_job_file_id and current_job_has_thumbnail
                    else None
                ),
                remaining_time_minutes=remaining_time_minutes,
                estimated_end_time=estimated_end_time,
                elapsed_time_minutes=elapsed_time_minutes,
                print_start_time=print_start_time,
                timestamp=datetime.now(),
                filament_status=filament_status,  # ADD THIS LINE
                raw_data=status_data
            )
```

---

## Phase 4: API Layer Updates

### File: `/src/api/routers/printers.py`

#### Update PrinterResponse Model

**Location:** Around line 95 (in `PrinterResponse` class)

```python
    filament_status: Optional[dict] = Field(
        None,
        description="Filament status information from printer (AMS for Bambu, sensor for Prusa)"
    )
```

#### Update Response Converter

**Location:** Around line 137 (in `_printer_to_response()` function)

Add after extracting temperatures:

```python
    # Extract filament status from printer instance
    filament_status = None
    if printer_service:
        try:
            instance = printer_service.printer_instances.get(printer.id)
            if instance and instance.last_status:
                status = instance.last_status

                # ... existing job and temperature extraction ...

                # Extract filament status (ADD THIS BLOCK)
                if status.filament_status:
                    filament_status = status.filament_status.dict()

        except Exception as e:
            logger.warning(
                "Failed to get status details for printer",
                printer_id=printer.id,
                error=str(e)
            )
```

Update return statement:

```python
    return PrinterResponse(
        id=printer.id,
        name=printer.name,
        printer_type=printer.type,
        status=printer.status,
        ip_address=printer.ip_address,
        connection_config={
            "ip_address": printer.ip_address,
            # ... rest of config ...
        },
        location=printer.location,
        description=printer.description,
        is_enabled=printer.is_enabled,
        last_seen=printer.last_seen.isoformat() if printer.last_seen else None,
        current_job=current_job,
        temperatures=temperatures,
        filament_status=filament_status,  # ADD THIS LINE
        created_at=printer.created_at.isoformat(),
        updated_at=printer.updated_at.isoformat()
    )
```

---

## Phase 5: Frontend Display

### File: `/frontend/js/components.js`

#### Add Filament Rendering Methods

**Location:** Around line 360 (after `renderTemperatures()`)

```javascript
/**
 * Render filament status section
 * Displays AMS slots for Bambu Lab or single filament for Prusa
 */
renderFilamentStatus() {
    // Check if printer has filament status data
    if (!this.printer.filament_status ||
        !this.printer.filament_status.slots ||
        this.printer.filament_status.slots.length === 0) {
        return '';  // No filament data available
    }

    const filamentStatus = this.printer.filament_status;
    const isMultiMaterial = filamentStatus.is_multi_material;

    // Render each slot
    const slotsHtml = filamentStatus.slots
        .map(slot => this.renderFilamentSlot(
            slot,
            filamentStatus.active_slot === slot.slot_id
        ))
        .join('');

    // Section title (AMS for multi-material, Filament for single)
    const title = isMultiMaterial ? 'AMS' : 'Filament';

    return `
        <div class="filament-section">
            <div class="section-title">${title}</div>
            <div class="filament-slots ${isMultiMaterial ? 'multi-material' : 'single-material'}">
                ${slotsHtml}
            </div>
        </div>
    `;
}

/**
 * Render individual filament slot
 * @param {Object} slot - FilamentSlot data
 * @param {boolean} isActive - Whether this slot is currently printing
 */
renderFilamentSlot(slot, isActive) {
    // CSS classes based on slot state
    const classes = [
        'filament-slot',
        isActive ? 'active-slot' : '',
        slot.is_runout ? 'runout' : '',
        !slot.is_loaded ? 'empty-slot' : '',
        (slot.remaining_percentage !== null &&
         slot.remaining_percentage < 20) ? 'low-stock' : ''
    ].filter(Boolean).join(' ');

    // Determine display color (prefer tray_color, fallback to color_name mapping)
    const color = slot.tray_color || this.getColorFromName(slot.color_name);
    const colorStyle = color ? `background-color: ${color};` : '';

    // Material label (best available description)
    const materialLabel = slot.color_name ||
                         slot.tray_type ||
                         slot.material_name ||
                         'Unknown';

    // Remaining percentage display (Bambu Lab only)
    const remainingHtml = slot.remaining_percentage !== null
        ? `<div class="filament-remaining">${Math.round(slot.remaining_percentage)}%</div>`
        : '';

    // Warning indicators
    const runoutHtml = slot.is_runout
        ? `<div class="filament-warning runout-warning">⚠️ Runout</div>`
        : '';

    const lowStockHtml = (slot.remaining_percentage !== null &&
                         slot.remaining_percentage < 20 &&
                         !slot.is_runout)
        ? `<div class="filament-warning low-stock-warning">⚠️ Low</div>`
        : '';

    // Empty slot indicator
    const emptyHtml = (!slot.is_loaded && !slot.tray_type)
        ? `<div class="filament-empty-label">Empty</div>`
        : '';

    // Active indicator (pulsing dot for currently printing filament)
    const activeIndicator = isActive
        ? '<span class="active-indicator">●</span>'
        : '';

    return `
        <div class="${classes}" data-slot-id="${slot.slot_id}">
            <div class="filament-color-indicator" style="${colorStyle}">
                ${activeIndicator}
            </div>
            <div class="filament-info">
                <div class="filament-material">${materialLabel}</div>
                ${remainingHtml}
                ${runoutHtml}
                ${lowStockHtml}
                ${emptyHtml}
            </div>
        </div>
    `;
}

/**
 * Map color name to CSS color value
 * @param {string} colorName - Human-readable color name
 * @returns {string|null} - Hex color or null
 */
getColorFromName(colorName) {
    if (!colorName) return null;

    // Standard color mapping (matches Bambu Lab color names)
    const colorMap = {
        'Black': '#000000',
        'White': '#FFFFFF',
        'Red': '#FF0000',
        'Orange': '#FF8800',
        'Yellow': '#FFFF00',
        'Green': '#00FF00',
        'Blue': '#0000FF',
        'Purple': '#800080',
        'Gray': '#808080',
        'Grey': '#808080',
        'Pink': '#FFC0CB',
        'Brown': '#8B4513',
        'Cyan': '#00FFFF',
        'Magenta': '#FF00FF',
        'Lime': '#00FF00',
        'Navy': '#000080',
        'Teal': '#008080',
        'Silver': '#C0C0C0',
        'Gold': '#FFD700',
        'Clear': '#E8E8E8',
        'Natural': '#F5E6D3',
        'Transparent': '#E8E8E8'
    };

    return colorMap[colorName] || null;
}
```

#### Update Main Render Method

**Location:** Around line 200 (in `render()` method)

Add filament section after temperatures:

```javascript
render() {
    this.element.innerHTML = `
        <div class="printer-card ${this.getStatusClass()}">
            <div class="printer-header">
                ${this.renderHeader()}
            </div>

            <div class="printer-body">
                ${this.renderStatusRow()}
                ${this.renderCurrentJob()}
                ${this.renderTemperatures()}
                ${this.renderFilamentStatus()}  <!-- ADD THIS LINE -->
                ${this.renderRealtimeProgress()}
                ${this.renderCameraSection()}
            </div>

            <div class="printer-footer">
                ${this.renderFooter()}
            </div>
        </div>
    `;

    this.attachEventListeners();
}
```

#### Add Real-time Update Method

**Location:** Around line 476 (in or after `updateRealtimeData()`)

```javascript
/**
 * Update filament display without full re-render
 * @param {Object} filamentStatus - FilamentStatus data
 */
updateFilamentDisplay(filamentStatus) {
    if (!filamentStatus || !filamentStatus.slots) return;

    filamentStatus.slots.forEach(slot => {
        const slotElement = this.element.querySelector(
            `[data-slot-id="${slot.slot_id}"]`
        );
        if (!slotElement) return;

        // Update remaining percentage if present
        const remainingElement = slotElement.querySelector('.filament-remaining');
        if (remainingElement && slot.remaining_percentage !== null) {
            remainingElement.textContent = `${Math.round(slot.remaining_percentage)}%`;
        }

        // Update warning states
        const isLowStock = slot.remaining_percentage !== null &&
                          slot.remaining_percentage < 20;
        slotElement.classList.toggle('low-stock', isLowStock);
        slotElement.classList.toggle('runout', slot.is_runout || false);

        // Update active slot highlight
        const isActive = filamentStatus.active_slot === slot.slot_id;
        slotElement.classList.toggle('active-slot', isActive);
    });
}
```

**Integrate into existing `updateRealtimeData()`:**

```javascript
updateRealtimeData(statusData) {
    // ... existing temperature and job updates ...

    // Update filament status (ADD THIS BLOCK)
    if (statusData.filament_status) {
        this.updateFilamentDisplay(statusData.filament_status);
    }
}
```

---

## Phase 6: CSS Styling

### File: `/frontend/css/dashboard.css`

**Location:** After line 283 (after temperature section)

```css
/* ========================================
   Filament Status Display
   ======================================== */

.filament-section {
    margin-top: var(--spacing-4);
    padding-top: var(--spacing-4);
    border-top: 1px solid var(--gray-200);
}

.section-title {
    font-size: var(--font-size-xs);
    color: var(--gray-500);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: var(--spacing-3);
    font-weight: 600;
}

/* Filament Slots Grid */
.filament-slots {
    display: grid;
    gap: var(--spacing-2);
}

.filament-slots.multi-material {
    grid-template-columns: repeat(2, 1fr);
}

.filament-slots.single-material {
    grid-template-columns: 1fr;
}

/* Individual Filament Slot */
.filament-slot {
    display: flex;
    align-items: center;
    padding: var(--spacing-2);
    background: var(--gray-50);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-sm);
    transition: all 0.2s ease;
}

/* Active Slot (currently printing) */
.filament-slot.active-slot {
    border-color: var(--primary-color);
    background: var(--primary-50);
    box-shadow: 0 0 0 1px var(--primary-color);
}

/* Empty Slot */
.filament-slot.empty-slot {
    opacity: 0.5;
    background: var(--gray-100);
}

/* Filament Runout */
.filament-slot.runout {
    border-color: var(--error-color);
    background: var(--error-50);
}

/* Low Stock Warning */
.filament-slot.low-stock {
    border-color: var(--warning-color);
}

/* Color Indicator Circle */
.filament-color-indicator {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 2px solid var(--gray-300);
    margin-right: var(--spacing-2);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

/* Empty Slot Color Indicator */
.filament-slot.empty-slot .filament-color-indicator {
    background: var(--gray-200) !important;
    border-style: dashed;
}

/* Active Indicator (pulsing dot) */
.active-indicator {
    color: white;
    font-size: 24px;
    text-shadow: 0 0 4px rgba(0, 0, 0, 0.5);
    animation: pulse-glow 2s infinite;
}

@keyframes pulse-glow {
    0%, 100% {
        opacity: 1;
        transform: scale(1);
    }
    50% {
        opacity: 0.6;
        transform: scale(1.1);
    }
}

/* Filament Info Container */
.filament-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
}

/* Material Name */
.filament-material {
    font-size: var(--font-size-sm);
    font-weight: 600;
    color: var(--gray-900);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Remaining Percentage */
.filament-remaining {
    font-size: var(--font-size-xs);
    color: var(--gray-600);
    font-weight: 500;
}

.filament-slot.low-stock .filament-remaining {
    color: var(--warning-color);
    font-weight: 700;
}

/* Warning Messages */
.filament-warning {
    font-size: var(--font-size-xs);
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: var(--spacing-1);
}

.runout-warning {
    color: var(--error-color);
}

.low-stock-warning {
    color: var(--warning-color);
}

/* Empty Slot Label */
.filament-empty-label {
    font-size: var(--font-size-xs);
    color: var(--gray-500);
    font-style: italic;
}

/* ========================================
   Responsive Design
   ======================================== */

@media (max-width: 768px) {
    /* Stack AMS slots vertically on mobile */
    .filament-slots.multi-material {
        grid-template-columns: 1fr;
    }

    /* Slightly smaller color indicators on mobile */
    .filament-color-indicator {
        width: 28px;
        height: 28px;
    }

    .active-indicator {
        font-size: 20px;
    }
}

/* Container query support (modern browsers) */
@supports (container-type: inline-size) {
    @container printer-grid (max-width: 500px) {
        .filament-slots.multi-material {
            grid-template-columns: 1fr;
        }
    }
}
```

---

## Testing Plan

### Test Scenarios

#### Bambu Lab AMS Testing

1. **Full AMS (4 slots loaded)**
   - ✅ All 4 slots display correctly
   - ✅ Colors match actual filaments
   - ✅ Remaining percentages shown
   - ✅ Material types labeled

2. **Partial AMS (2 slots loaded)**
   - ✅ Loaded slots show normally
   - ✅ Empty slots grayed out with dashed border
   - ✅ "Empty" label on unloaded slots

3. **Active printing**
   - ✅ Active slot highlighted with border
   - ✅ Pulsing dot indicator visible
   - ✅ Remaining percentage decreases during print

4. **Low filament (<20%)**
   - ✅ Yellow border appears
   - ✅ "⚠️ Low" badge shows
   - ✅ Remaining percentage in yellow

5. **No AMS installed**
   - ✅ Filament section not rendered
   - ✅ No console errors
   - ✅ Card layout unaffected

#### Prusa Testing

1. **Filament loaded**
   - ✅ Single slot displays
   - ✅ Material type shown
   - ✅ No percentage (expected)

2. **Filament runout**
   - ✅ Red border appears
   - ✅ "⚠️ Runout" badge shows
   - ✅ `.runout` class applied

3. **No filament sensor**
   - ✅ Filament section not rendered
   - ✅ No errors logged

#### Real-time Updates

1. **WebSocket updates**
   - ✅ Filament status updates without page refresh
   - ✅ Percentage changes reflected immediately
   - ✅ Active slot switches correctly

2. **Printer state changes**
   - ✅ Idle → Printing: Active slot activates
   - ✅ Printing → Idle: Active indicator disappears
   - ✅ Filament load: Slot appears
   - ✅ Filament unload: Slot empties

#### Cross-browser Testing

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile Safari (iOS)
- ✅ Chrome Mobile (Android)

### Testing Approach

**Manual Testing (Preferred):**
- Test with real Bambu Lab printer (A1, A1 Mini, P1S, or X1C)
- Test with real Prusa Core One
- Observe during actual print jobs
- Trigger runout conditions

**Mock Data Testing:**
- Modify `_extract_ams_status()` to return mock data
- Test edge cases (empty AMS, invalid data, missing fields)
- Simulate low stock conditions
- Test with various color combinations

**Automated Testing (Future):**
```python
# tests/test_filament_extraction.py
def test_bambu_ams_extraction():
    """Test AMS data extraction from MQTT"""
    mock_mqtt_data = {
        "ams": {
            "id": "0",
            "tray": [
                {
                    "tray_id": "1",
                    "tray_type": "PLA",
                    "tray_color": "#000000",
                    "tray_id_name": "GFL00",
                    "remain": 85,
                    "tray_now": 1
                }
            ]
        }
    }

    printer = BambuLabPrinter(...)
    status = printer._extract_ams_status(mock_mqtt_data)

    assert status.is_multi_material == True
    assert len(status.slots) == 1
    assert status.slots[0].remaining_percentage == 85.0
    assert status.active_slot == 0
```

---

## Documentation Updates

### API Specification

**File:** `/docs/architecture/api_specification.md`

Add section:

```markdown
### Filament Status

Printers may include real-time filament status in their responses.

#### FilamentStatus Object

```json
{
  "is_multi_material": true,
  "active_slot": 0,
  "ams_id": "0",
  "has_runout_sensor": true,
  "slots": [
    {
      "slot_id": 0,
      "tray_id": "1",
      "tray_type": "PLA",
      "tray_color": "#000000",
      "filament_id": "GFL00",
      "color_name": "Black",
      "remaining_percentage": 85.5,
      "is_loaded": true,
      "is_runout": false,
      "material_name": "PLA Basic"
    }
  ]
}
```

#### Printer Support

| Manufacturer | Multi-Material | Remaining % | Runout Detection |
|--------------|----------------|-------------|------------------|
| Bambu Lab | ✅ Yes (AMS) | ✅ Yes | ✅ Yes |
| Prusa Core One | ❌ No | ❌ No | ✅ Yes |
```

### User Guide

**File:** `/docs/features/FILAMENT_STATUS.md` (to be created)

See separate user-facing documentation with screenshots and troubleshooting.

### Changelog

**File:** `/CHANGELOG.md`

```markdown
## [2.12.0] - TBD

### Added
- **Live Filament Status Monitoring** - Real-time filament information in dashboard
  - Bambu Lab AMS support: Display all 4 slots with colors, types, and remaining percentages
  - Prusa Core One support: Single filament display with runout detection
  - Color-coded indicators for each filament slot
  - Active slot highlighting during multi-material prints
  - Low stock warnings (<20% remaining)
  - Filament runout alerts
  - Real-time updates via WebSocket
```

---

## Risk Assessment

### High-Risk Items

1. **MQTT Data Structure Variability**
   - **Risk:** AMS data format may differ across Bambu Lab models/firmware versions
   - **Mitigation:**
     - Defensive parsing with try/catch blocks
     - Extensive logging for debugging
     - Handle both list and dict AMS formats
     - Graceful degradation if data missing
   - **Testing:** Test with multiple Bambu Lab models if possible

2. **Backward Compatibility**
   - **Risk:** Breaking existing API consumers
   - **Mitigation:**
     - All new fields optional (Optional[...])
     - Default values where appropriate
     - No database schema changes
     - Pydantic handles missing fields gracefully
   - **Testing:** Verify old API clients still function

### Medium-Risk Items

1. **Frontend Layout Issues**
   - **Risk:** Filament section breaks card layout on small screens
   - **Mitigation:**
     - Responsive grid with media queries
     - Container queries for modern browsers
     - Tested mobile-first approach
   - **Testing:** Manual testing on various screen sizes

2. **Color Mapping Accuracy**
   - **Risk:** Filament IDs not in color database
   - **Mitigation:**
     - Fallback to "Unknown" if no match
     - Use printer-provided hex color when available
     - Log unmapped IDs for future additions
   - **Testing:** Test with custom/third-party filaments

### Low-Risk Items

1. **WebSocket Update Performance**
   - **Risk:** Additional data in WebSocket messages
   - **Mitigation:** Minimal payload size, only changed data
   - **Testing:** Monitor WebSocket traffic volume

2. **API Response Size**
   - **Risk:** Larger JSON payloads
   - **Mitigation:** Filament data is compact (<1KB per printer)
   - **Testing:** Measure payload size increase

---

## Implementation Checklist

### Phase 1: Documentation ✅
- [x] Create this technical plan document
- [ ] Create user guide document

### Phase 2: Backend Models
- [ ] Add `FilamentSlot` model to `/src/models/printer.py`
- [ ] Add `FilamentStatus` model to `/src/models/printer.py`
- [ ] Extend `PrinterStatusUpdate` with `filament_status` field
- [ ] Test models with sample data

### Phase 3: Bambu Lab Extraction
- [ ] Implement `_extract_ams_status()` in `/src/printers/bambu_lab.py`
- [ ] Integrate into `_get_status_bambu_api()`
- [ ] Integrate into `_get_status_mqtt()`
- [ ] Update return statements
- [ ] Test with real Bambu Lab printer or mock data

### Phase 4: Prusa Extraction
- [ ] Implement `_extract_filament_status()` in `/src/printers/prusa.py`
- [ ] Integrate into `get_status()`
- [ ] Update return statement
- [ ] Test with real Prusa printer or mock data

### Phase 5: API Layer
- [ ] Add `filament_status` field to `PrinterResponse`
- [ ] Update `_printer_to_response()` converter
- [ ] Test API endpoints return filament data

### Phase 6: Frontend Display
- [ ] Add `renderFilamentStatus()` to `PrinterCard`
- [ ] Add `renderFilamentSlot()` helper
- [ ] Add `getColorFromName()` utility
- [ ] Update `render()` method
- [ ] Add `updateFilamentDisplay()` for real-time
- [ ] Test UI rendering

### Phase 7: CSS Styling
- [ ] Add filament section styles
- [ ] Add color indicator styles
- [ ] Add warning state styles
- [ ] Add responsive breakpoints
- [ ] Test on multiple screen sizes

### Phase 8: Testing
- [ ] Test Bambu Lab AMS (4 slots, partial, empty)
- [ ] Test Prusa filament sensor
- [ ] Test low stock warnings
- [ ] Test runout detection
- [ ] Test real-time updates
- [ ] Cross-browser testing
- [ ] Mobile testing

### Phase 9: Final Documentation
- [ ] Update API specification
- [ ] Create user guide
- [ ] Update CHANGELOG.md
- [ ] Add inline code comments

---

## Success Metrics

**Implementation Complete When:**

✅ Bambu Lab printers display all AMS slots with colors, types, and percentages
✅ Prusa printers display filament type and runout status
✅ Low stock warnings appear when remaining < 20%
✅ Active slot highlighted with pulsing indicator during printing
✅ Real-time updates work without page refresh
✅ No errors when filament data unavailable
✅ Mobile layout responsive and usable
✅ API documentation updated
✅ User guide created with examples
✅ No breaking changes to existing API consumers

---

## Future Enhancements

**Not Included in Phase 1 (Potential Phase 2):**

1. **Historical Filament Usage Tracking**
   - Database schema for filament consumption history
   - Analytics and reports by material type
   - Cost tracking integration with material inventory

2. **Manual Filament Overrides**
   - UI to manually set filament colors if detection wrong
   - Override printer-reported values
   - Persist user preferences per printer

3. **Alert System**
   - Email notifications for low stock
   - Configurable thresholds (default 20%)
   - Alert history and acknowledgment

4. **Material Inventory Integration**
   - Link loaded filament to material inventory
   - Automatic consumption tracking
   - Inventory depletion warnings

5. **Multi-AMS Support**
   - Support printers with 2+ AMS units
   - 8, 12, 16 slot configurations
   - AMS unit switching UI

6. **Filament Usage Predictions**
   - Estimate remaining print time based on filament
   - Alert if job requires more filament than available
   - Suggest filament changes before starting

---

## Related Documentation

- **User Guide:** `/docs/features/FILAMENT_STATUS.md` (to be created)
- **API Specification:** `/docs/architecture/api_specification.md`
- **Material Inventory:** `/docs/features/MATERIAL_INVENTORY.md`
- **Bambu Lab Integration:** `/docs/printers/bambu_lab.md`
- **Prusa Integration:** `/docs/printers/prusa.md`

---

## Contact & Support

For questions about this implementation:
- **GitHub Issues:** https://github.com/schmacka/printernizer/issues
- **Discussions:** https://github.com/schmacka/printernizer/discussions

---

**Document Version:** 1.0
**Last Updated:** 2026-01-05
**Author:** Claude Code
**Status:** Ready for Implementation
