# Material Management Phase B: Full Integration

**Status**: Future Implementation (After Phase A)
**Estimated Effort**: 1-2 days
**Dependencies**: Phase A (Basic UI) must be complete

## Overview

Phase B adds deep integration between the material management system and existing Printernizer features (printers, jobs, analytics). This phase transforms materials from standalone inventory tracking into an active part of the printing workflow with automatic consumption tracking and cost calculations.

## Goals

- **Printer-Material Association**: Track which spool is loaded on which printer
- **Automatic Consumption Tracking**: Record material usage when jobs complete
- **Cost Integration**: Show material costs in job details and analytics
- **Consumption History**: View detailed usage history per spool
- **Export Enhancement**: Include material data in business reports

## Non-Goals (Phase C)

- NFC tag integration
- Multi-material job support (AMS/MMU)
- Predictive analytics
- Home Assistant integration

---

## Feature 1: Printer-Spool Association

### Problem
Currently, materials and printers are independent. Users manually track which spool is loaded on which printer, leading to:
- No automatic consumption tracking
- Manual weight updates after prints
- No cost allocation per printer
- No warning when spool runs out mid-print

### Solution
Add bidirectional association between printers and materials with "Load Spool" workflow.

### UI Changes

#### Printer Card Enhancement
```
┌─────────────────────────────┐
│ Bambu Lab A1 #1         [⚙️]│
├─────────────────────────────┤
│ Status: Printing            │
│ Temperature: 200°C / 60°C   │
│ Progress: 45%               │
├─────────────────────────────┤
│ 🧵 Loaded Spool:            │ ← NEW SECTION
│    PLA ECO Red (OVERTURE)   │
│    850g remaining (85%)     │
│    [Change Spool]           │ ← NEW BUTTON
└─────────────────────────────┘
```

**When no spool loaded:**
```
│ 🧵 No spool loaded          │
│    [Load Spool]             │
```

#### Load Spool Modal
```
┌─────────────────────────────────────┐
│ Spule laden: Bambu Lab A1 #1   [×] │
├─────────────────────────────────────┤
│                                     │
│ Wählen Sie eine Spule:              │
│                                     │
│ ┌─────────────────────────────┐   │
│ │ ● PLA ECO Red (OVERTURE)    │   │
│ │   850g / 1000g (85%)        │   │
│ │   14,50 € remaining         │   │
│ └─────────────────────────────┘   │
│                                     │
│ ┌─────────────────────────────┐   │
│ │ ○ PETG Blue (PRUSAMENT)     │   │
│ │   200g / 1000g (20%) ⚠️     │   │
│ │   8,00 € remaining          │   │
│ └─────────────────────────────┘   │
│                                     │
│ [Filter: Ausreichend ▼]            │
│                                     │
│         [Abbrechen] [Laden]         │
└─────────────────────────────────────┘
```

#### Unload/Change Workflow
```
User clicks [Change Spool]
  ↓
Confirmation: "Aktuelle Spule (PLA ECO Red) entladen?"
  ↓
[Abbrechen] [Entladen] [Wechseln]
  ↓
"Entladen": Unloads current, no new spool
"Wechseln": Shows load spool modal
```

### API Changes

#### New Endpoints
```
POST /api/v1/printers/{id}/load-spool
Body: { "material_id": "abc123" }
Response: Updated printer object with loaded_material

POST /api/v1/printers/{id}/unload-spool
Body: {} (empty)
Response: Updated printer object with loaded_material = null
```

#### Modified Endpoints
```
GET /api/v1/printers/{id}
Response: {
  ...existing fields...,
  "loaded_material": {  ← NEW FIELD
    "id": "abc123",
    "material_type": "PLA_ECO",
    "brand": "OVERTURE",
    "color": "RED",
    "remaining_weight": 850,
    "remaining_percentage": 85
  } | null
}
```

### Database Changes

**Existing field utilized:**
- `materials.printer_id` (already exists, currently unused)
- When spool loaded: `UPDATE materials SET printer_id = ? WHERE id = ?`
- When unloaded: `UPDATE materials SET printer_id = NULL WHERE id = ?`

**No new tables needed!**

### Backend Implementation

**File**: `src/services/printer_service.py`

```python
async def load_spool(self, printer_id: str, material_id: str):
    """Load a spool onto a printer."""
    # Verify printer exists
    printer = await self.get_printer(printer_id)
    if not printer:
        raise ValueError(f"Printer {printer_id} not found")

    # Verify material exists and not already loaded
    material = await self.material_service.get_material(material_id)
    if not material:
        raise ValueError(f"Material {material_id} not found")
    if material.printer_id:
        raise ValueError(f"Material already loaded on printer {material.printer_id}")

    # Unload any currently loaded spool
    if printer.loaded_material_id:
        await self.unload_spool(printer_id)

    # Load new spool
    await self.material_service.update_material(material_id, {
        "printer_id": printer_id
    })

    # Update printer cache
    printer.loaded_material_id = material_id
    self._cache[printer_id] = printer

    # Emit event
    await self.event_service.emit("printer_spool_loaded", {
        "printer_id": printer_id,
        "material_id": material_id
    })

    return await self.get_printer(printer_id)

async def unload_spool(self, printer_id: str):
    """Unload current spool from printer."""
    printer = await self.get_printer(printer_id)
    if not printer or not printer.loaded_material_id:
        return  # Nothing to unload

    # Unload spool
    await self.material_service.update_material(printer.loaded_material_id, {
        "printer_id": None
    })

    # Update printer cache
    printer.loaded_material_id = None
    self._cache[printer_id] = printer

    # Emit event
    await self.event_service.emit("printer_spool_unloaded", {
        "printer_id": printer_id
    })
```

---

## Feature 2: Automatic Job Consumption Tracking

### Problem
Currently, when a print job completes:
- Material consumption is not recorded
- Users must manually update remaining weight
- No historical consumption data
- No cost tracking per job

### Solution
Automatically create consumption records when jobs complete, linking job → material → cost.

### UI Changes

#### Job Details Enhancement
```
┌─────────────────────────────────────┐
│ Job: benchy.3mf                     │
├─────────────────────────────────────┤
│ Status: Completed ✅                 │
│ Duration: 2h 34m                    │
│ File Size: 1.2 MB                   │
├─────────────────────────────────────┤
│ 💰 Costs:                           │ ← ENHANCED
│    Material: 2,56 € (15g @ 17,06€/kg)│ ← NEW
│    Power: 0,15 € (0.3 kWh)          │
│    Total: 2,71 €                    │ ← UPDATED
├─────────────────────────────────────┤
│ 🧵 Material Used:                   │ ← NEW SECTION
│    PLA ECO Red (OVERTURE)           │
│    15g consumed                     │
│    Remaining: 835g → 820g           │
│    [View Spool]                     │ ← Link to materials page
└─────────────────────────────────────┘
```

#### Material Spool Details
```
┌─────────────────────────────────┐
│ PLA ECO Red (OVERTURE)      [✏️]│
├─────────────────────────────────┤
│ ...existing card content...     │
├─────────────────────────────────┤
│ 📊 Consumption History:         │ ← NEW SECTION
│    Last 5 prints:               │
│    • benchy.3mf - 15g (heute)   │
│    • vase.3mf - 25g (gestern)   │
│    • bracket.3mf - 10g (2d ago) │
│    [View All History]           │
└─────────────────────────────────┘
```

### Workflow

```
Job completes
  ↓
Check if printer has loaded spool
  ↓
If yes:
  1. Get job metadata (weight used from 3MF)
  2. Calculate cost (weight × cost_per_kg)
  3. Create consumption record
  4. Update material remaining weight
  5. Check if low stock (< 20%)
  6. Emit events
  ↓
If no:
  Log warning (job completed without loaded spool)
```

### API Changes

**Modified Endpoint** (already exists, enhance behavior):
```
POST /api/v1/materials/consumption
Body: {
  "job_id": "job123",
  "material_id": "mat456",
  "weight_used": 15.0,
  "printer_id": "printer789",
  "file_name": "benchy.3mf",
  "print_time_hours": 2.57
}

This endpoint exists but is never called automatically.
We'll call it from JobService when job completes.
```

**New Endpoint**:
```
GET /api/v1/materials/{id}/consumption/history
Query params: limit (default 10), offset (default 0)
Response: [
  {
    "id": "cons123",
    "job_id": "job123",
    "file_name": "benchy.3mf",
    "weight_used": 15.0,
    "cost": 2.56,
    "timestamp": "2024-11-03T14:30:00Z",
    "printer_id": "printer789",
    "printer_name": "Bambu Lab A1 #1"
  },
  ...
]
```

### Backend Implementation

**File**: `src/services/job_service.py`

```python
async def on_job_complete(self, job: Job):
    """Handle job completion - record material consumption."""
    # Get printer
    printer = await self.printer_service.get_printer(job.printer_id)
    if not printer or not printer.loaded_material_id:
        logger.warning(f"Job {job.id} completed but no spool loaded")
        return

    # Get material usage from job metadata
    weight_used = job.material_actual_usage or job.material_estimated_usage
    if not weight_used:
        logger.warning(f"Job {job.id} has no material usage data")
        return

    # Record consumption
    try:
        await self.material_service.record_consumption({
            "job_id": job.id,
            "material_id": printer.loaded_material_id,
            "weight_used": weight_used,
            "printer_id": job.printer_id,
            "file_name": job.file_name,
            "print_time_hours": job.print_time / 3600.0
        })
        logger.info(f"Recorded {weight_used}g consumption for job {job.id}")
    except Exception as e:
        logger.error(f"Failed to record consumption: {e}")
```

**File**: `src/services/material_service.py`

```python
async def record_consumption(self, consumption_data: dict):
    """Record material consumption and update remaining weight."""
    material_id = consumption_data["material_id"]
    weight_used = consumption_data["weight_used"]

    # Get current material
    material = await self.get_material(material_id)
    if not material:
        raise ValueError(f"Material {material_id} not found")

    # Calculate cost
    cost = (weight_used / 1000.0) * material.cost_per_kg

    # Create consumption record
    consumption_id = str(uuid.uuid4())
    await self.database.execute(
        """INSERT INTO material_consumption
           (id, job_id, material_id, weight_used, cost, timestamp,
            printer_id, file_name, print_time_hours)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            consumption_id,
            consumption_data["job_id"],
            material_id,
            weight_used,
            cost,
            datetime.now(),
            consumption_data["printer_id"],
            consumption_data["file_name"],
            consumption_data["print_time_hours"]
        )
    )

    # Update remaining weight
    new_remaining = material.remaining_weight - weight_used
    await self.update_material(material_id, {
        "remaining_weight": max(0, new_remaining)
    })

    # Check low stock
    if (new_remaining / material.weight) < 0.20:
        await self.event_service.emit("material_low_stock", {
            "material_id": material_id,
            "remaining_percentage": (new_remaining / material.weight) * 100
        })

    await self.database.commit()

    # Clear cache
    del self._cache[material_id]

    return consumption_id
```

---

## Feature 3: Analytics Integration

### Problem
Current analytics don't include material costs, making business reporting incomplete.

### Solution
Add material consumption data to analytics dashboards and reports.

### UI Changes

#### Analytics Dashboard Enhancement

**Cost Analysis Section** (existing, enhance):
```
┌─────────────────────────────────────┐
│ 💰 Kostenanalyse (30 Tage)         │
├─────────────────────────────────────┤
│ Material: 145,67 €    ← NEW        │
│ Strom: 12,34 €                      │
│ Arbeitszeit: 89,50 €                │
│ ────────────────────                │
│ Gesamt: 247,51 €                    │
└─────────────────────────────────────┘
```

**New Section**: Material Consumption Breakdown
```
┌─────────────────────────────────────┐
│ 🧵 Materialverbrauch (30 Tage)     │
├─────────────────────────────────────┤
│ Gesamt: 1,245 kg (145,67 €)        │
│                                     │
│ Nach Typ:                           │
│  PLA: 850g (102,00 €)     ████████ │
│  PETG: 295g (35,40 €)     ███      │
│  TPU: 100g (8,27 €)       █        │
│                                     │
│ Nach Drucker:                       │
│  Bambu A1 #1: 745g (89,40 €) ████  │
│  Prusa Core: 500g (60,00 €) ███    │
│                                     │
│ Effizienz:                          │
│  Erfolgsrate: 92%                   │
│  Verschwendung: 8% (100g)           │
└─────────────────────────────────────┘
```

### API Changes

**Enhanced Endpoint**:
```
GET /api/v1/analytics/summary
Query: date_from, date_to

Response: {
  ...existing fields...,
  "materials": {  ← NEW
    "total_weight_kg": 1.245,
    "total_cost": 145.67,
    "by_type": [
      { "type": "PLA", "weight_kg": 0.850, "cost": 102.00 },
      { "type": "PETG", "weight_kg": 0.295, "cost": 35.40 },
      { "type": "TPU", "weight_kg": 0.100, "cost": 8.27 }
    ],
    "by_printer": [
      { "printer_id": "p1", "name": "Bambu A1 #1", "weight_kg": 0.745, "cost": 89.40 },
      { "printer_id": "p2", "name": "Prusa Core", "weight_kg": 0.500, "cost": 60.00 }
    ],
    "efficiency": {
      "successful_jobs": 45,
      "failed_jobs": 4,
      "success_rate": 0.92,
      "waste_weight_kg": 0.100
    }
  }
}
```

---

## Feature 4: Consumption History UI

### Problem
Users can't see where/when material was consumed.

### Solution
Add consumption history page and per-spool consumption details.

### UI Design

**New Tab in Materials Section**:
```
[Spulen] [Verbrauch] ← NEW TAB
```

**Consumption History Table**:
```
┌──────────────────────────────────────────────────────────────┐
│ 🧵 Materialverbrauch                                         │
├──────────────────────────────────────────────────────────────┤
│ Filter: [Alle Spulen ▼] [Alle Drucker ▼] [30 Tage ▼]       │
├──────────────────────────────────────────────────────────────┤
│ Date       | Material       | Job         | Used  | Cost    │
│────────────|───────────────|─────────────|───────|─────────│
│ 03.11.2024 | PLA ECO Red   | benchy.3mf  | 15g   | 2,56 €  │
│ 02.11.2024 | PLA ECO Red   | vase.3mf    | 25g   | 4,27 €  │
│ 02.11.2024 | PETG Blue     | bracket.3mf | 10g   | 1,20 €  │
│ 01.11.2024 | PLA ECO Red   | test.3mf    | 5g    | 0,85 €  │
├──────────────────────────────────────────────────────────────┤
│ Gesamt (30 Tage): 1,245 kg | 145,67 €                       │
└──────────────────────────────────────────────────────────────┘
```

**Click row**: Opens job details
**Export button**: Download as CSV/Excel

### API Endpoint

```
GET /api/v1/materials/consumption/history
Query params:
  - material_id (optional)
  - printer_id (optional)
  - date_from (optional)
  - date_to (optional)
  - limit (default 50)
  - offset (default 0)

Response: [
  {
    "id": "cons123",
    "date": "2024-11-03T14:30:00Z",
    "material": {
      "id": "mat456",
      "type": "PLA_ECO",
      "brand": "OVERTURE",
      "color": "RED"
    },
    "job": {
      "id": "job123",
      "file_name": "benchy.3mf"
    },
    "printer": {
      "id": "printer789",
      "name": "Bambu Lab A1 #1"
    },
    "weight_used": 15.0,
    "cost": 2.56,
    "print_time_hours": 2.57
  },
  ...
]
```

---

## Feature 5: Export Enhancement

### Problem
Material data not included in business reports and exports.

### Solution
Enhance existing export functionality to include material consumption.

### Changes

**File**: `src/services/analytics_service.py`

Enhance `export_summary()` method to include material data in CSV/Excel exports.

**CSV Structure**:
```
Date,Job,Printer,Material,Weight(g),Material Cost,Power Cost,Labor Cost,Total Cost
2024-11-03,benchy.3mf,Bambu A1,PLA ECO Red,15,2.56,0.15,5.00,7.71
2024-11-02,vase.3mf,Bambu A1,PLA ECO Red,25,4.27,0.20,8.00,12.47
...
```

---

## Implementation Plan

### Phase B.1: Printer-Spool Association (4-6 hours)

1. **Backend** (2 hours):
   - Add `load_spool()` and `unload_spool()` to PrinterService
   - Add API endpoints
   - Add events

2. **Frontend** (2-3 hours):
   - Add "Loaded Spool" section to printer cards
   - Create "Load Spool" modal
   - Add change/unload workflow
   - Update printer status displays

3. **Testing** (1 hour):
   - Test load/unload workflow
   - Test multiple printers
   - Test edge cases (loading already-loaded spool)

### Phase B.2: Automatic Consumption Tracking (4-6 hours)

1. **Backend** (2 hours):
   - Add `on_job_complete()` hook to JobService
   - Enhance `record_consumption()` in MaterialService
   - Add automatic weight updates
   - Add low-stock checks

2. **Frontend** (2 hours):
   - Enhance job details with material cost
   - Add material consumption section
   - Link to material details

3. **Testing** (1-2 hours):
   - Run test prints
   - Verify consumption recorded
   - Verify weight updated
   - Test low-stock alerts

### Phase B.3: Consumption History (3-4 hours)

1. **Backend** (1 hour):
   - Implement `GET /api/materials/consumption/history` endpoint
   - Add filtering logic

2. **Frontend** (2 hours):
   - Add "Verbrauch" tab to materials section
   - Create consumption history table
   - Add filters and date range selector
   - Add export button

3. **Testing** (1 hour):
   - Test filtering
   - Test sorting
   - Test export

### Phase B.4: Analytics Integration (4-6 hours)

1. **Backend** (2-3 hours):
   - Enhance AnalyticsService with material queries
   - Add consumption aggregations
   - Update export functionality

2. **Frontend** (2 hours):
   - Add material cost to analytics dashboard
   - Create material consumption breakdown section
   - Update cost analysis displays

3. **Testing** (1 hour):
   - Verify data accuracy
   - Test different date ranges
   - Test export with material data

### Total Estimated Time: 15-22 hours (2-3 days)

---

## Dependencies

### Required Before Phase B

- ✅ Phase A: Basic UI complete
- ✅ Materials backend activated
- ✅ At least one spool in database
- ✅ At least one printer configured

### External Dependencies

- Job completion events (already implemented)
- Printer status API (already implemented)
- Material service (already implemented)

---

## Success Criteria

### Must Have
- [ ] Load spool on printer via UI
- [ ] Unload/change spool via UI
- [ ] Automatic consumption tracking on job completion
- [ ] Material costs shown in job details
- [ ] Consumption history viewable
- [ ] Material data in analytics dashboard

### Nice to Have
- [ ] Bulk load spools (load multiple printers at once)
- [ ] Spool swap alerts (notify when spool needs changing mid-print)
- [ ] Material efficiency metrics
- [ ] Waste tracking (failed prints)

### Quality Criteria
- [ ] No manual weight updates needed
- [ ] Accurate cost calculations
- [ ] Real-time spool status updates
- [ ] Reliable event handling
- [ ] No performance degradation

---

## Risks & Mitigation

### Risk 1: Job Metadata Missing
**Problem**: Some jobs may not have material usage data (old jobs, manually started)

**Mitigation**:
- Fall back to estimated usage from 3MF metadata
- Log warning for manual review
- Allow manual consumption entry

### Risk 2: Spool Changed Mid-Print
**Problem**: User physically changes spool during print without updating system

**Mitigation**:
- Accept reality - track based on loaded spool at job start
- Future: Add "Spool Changed" button during print (Phase C)
- Document this limitation

### Risk 3: Multiple Materials (AMS/MMU)
**Problem**: Jobs may use multiple spools simultaneously

**Mitigation**:
- Phase B: Only track primary loaded spool
- Phase C: Implement multi-spool support with AMS integration
- Document as known limitation

---

## Future Enhancements (Beyond Phase B)

- **Spool Change Alerts**: Notify user when spool will run out before job finishes
- **Predictive Analytics**: Estimate when spools will run out based on usage patterns
- **Multi-Material Support**: Track multiple spools per job (AMS/MMU)
- **Waste Tracking**: Separate failed print consumption from successful
- **Material Recommendations**: Suggest optimal spools based on job requirements

---

## Conclusion

Phase B transforms materials from passive inventory into an active part of the printing workflow. By linking spools to printers and automatically tracking consumption, users gain:
- Accurate cost tracking per print
- Historical consumption data
- No manual weight updates
- Business reporting with material costs
- Foundation for advanced features (Phase C)

This phase requires careful integration with existing job and printer services but leverages the robust backend infrastructure already built in Phase A.
