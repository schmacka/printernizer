# Material Management (Filamente) - Phase A Design

**Date**: 2025-11-03
**Status**: Approved for Implementation
**Phase**: A - Quick Activation (UI Only)
**Estimated Effort**: 6-9 hours

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Design Decisions](#design-decisions)
4. [Backend Architecture](#backend-architecture)
5. [Frontend UI Design](#frontend-ui-design)
6. [Data Flow](#data-flow)
7. [Error Handling](#error-handling)
8. [Implementation Details](#implementation-details)
9. [Testing Strategy](#testing-strategy)
10. [Future Phases](#future-phases)

---

## Executive Summary

### Problem
Printernizer has a **complete but dormant** material management backend. All infrastructure exists (models, services, API endpoints, database schemas), but:
- The API router is not registered in the main application
- There is no frontend UI for spool management
- The system is completely isolated from the rest of the application

### Solution
**Phase A**: Activate the backend (3 lines of code) and build a full-featured spool inventory UI with CRUD operations, filtering, and two view modes (cards/table).

### Goals
- Enable spool inventory tracking for 3D printing businesses
- Provide intuitive UI for managing filament spools
- Track costs, remaining weight, and low-stock alerts
- Foundation for future integration with printers and jobs (Phase B/C)

### Non-Goals (Future Phases)
- Printer-spool association → Phase B
- Automatic job consumption tracking → Phase B
- NFC tag integration → Phase C
- Analytics integration → Phase B

---

## Current State Analysis

### Backend Status: ✅ Complete (100%)

#### Existing Components

**Models** (`src/models/material.py`):
- `MaterialType` enum: 12 types (PLA, PLA_ECO, PETG, TPU, ABS, ASA, etc.)
- `MaterialBrand` enum: 6 brands (OVERTURE, PRUSAMENT, BAMBU, POLYMAKER, ESUN, OTHER)
- `MaterialColor` enum: 13 colors (BLACK, WHITE, RED, BLUE, etc.)
- `MaterialSpool` dataclass: Complete with physical properties, costs, tracking
- Pydantic models: MaterialCreate, MaterialUpdate, MaterialConsumption, MaterialStats, MaterialReport

**Service Layer** (`src/services/material_service.py`):
- Full CRUD operations
- Database table creation (materials, material_consumption)
- Consumption tracking with automatic cost calculation
- Low-stock alerts (<20% triggers event)
- Statistics aggregation (by type, brand, color)
- Consumption reports with business/private breakdown
- CSV export functionality
- In-memory caching for performance

**API Endpoints** (`src/api/routers/materials.py`):
```
GET    /api/materials              - List all materials (with filters)
GET    /api/materials/stats        - Get inventory statistics
GET    /api/materials/types        - Get available enums
GET    /api/materials/report       - Generate consumption report
GET    /api/materials/export       - Export to CSV/Excel
GET    /api/materials/{id}         - Get specific material
POST   /api/materials              - Create new material
PATCH  /api/materials/{id}         - Update material
POST   /api/materials/consumption  - Record consumption
DELETE /api/materials/{id}         - Delete material (501 placeholder)
```

**Database Schema**:
```sql
CREATE TABLE materials (
    id TEXT PRIMARY KEY,
    material_type TEXT NOT NULL,
    brand TEXT NOT NULL,
    color TEXT NOT NULL,
    diameter REAL NOT NULL,
    weight REAL NOT NULL,
    remaining_weight REAL NOT NULL,
    cost_per_kg DECIMAL(10,2) NOT NULL,
    purchase_date TIMESTAMP NOT NULL,
    vendor TEXT NOT NULL,
    batch_number TEXT,
    notes TEXT,
    printer_id TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE material_consumption (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    material_id TEXT NOT NULL,
    weight_used REAL NOT NULL,
    cost DECIMAL(10,2) NOT NULL,
    timestamp TIMESTAMP,
    printer_id TEXT NOT NULL,
    file_name TEXT,
    print_time_hours REAL
);
```

#### Missing Integration
- Router not registered in `src/main.py`
- Service not initialized in app lifespan
- No dependency injection in `src/utils/dependencies.py`
- Tables not created (service never instantiated)

### Frontend Status: ❌ None (0%)

**Current State**:
- Zero UI components for spool management
- Only read-only material displays (3MF metadata, job details)
- No navigation menu item

**What's Needed**:
- Full inventory management UI
- CRUD forms (add, edit, delete)
- Two view modes (cards, table)
- Filtering, sorting, search
- Low-stock indicators

---

## Design Decisions

### Decision 1: Navigation & Placement

**Question**: Where should material management live in the UI?

**Options Considered**:
1. Sub-section under "Drucker" (materials tied to printers)
2. Sub-section under "Aufträge" (materials consumed by jobs)
3. **Top-level tab** between "Drucker-Dateien" and "Library"

**Decision**: Top-level tab ✅

**Rationale**:
- Materials bridge printers and jobs (both relationships matter)
- Inventory management is a distinct business function
- Consistent with other major features (Dashboard, Drucker, Aufträge)
- Room for expansion (Phase B will add printer/job integration)

### Decision 2: Naming Convention

**Question**: What should we call it in the German UI?

**Options Considered**:
1. "Materialien" (formal, generic)
2. "Spulen" (colloquial, specific)
3. **"Filamente"** (technical, industry-standard)

**Decision**: "Filamente" ✅

**Rationale**:
- Specific to 3D printing context
- Matches industry terminology
- Clear and unambiguous
- Aligns with technical nature of application

### Decision 3: Feature Scope (Phase A)

**Must Have**:
- ✅ View all spools (list/grid)
- ✅ Add new spool (full form)
- ✅ Edit spool (update remaining weight, costs, notes)
- ✅ Delete spool (with confirmation)
- ✅ Basic stats (total count, low stock, total value)

**Nice to Have** (included):
- ✅ Filter by type/brand/color/status
- ✅ Sort by any field
- ✅ Search by vendor/batch
- ✅ Low stock indicators
- ✅ View toggle (cards/table)

**Deferred to Phase B**:
- ❌ Assign to specific printer
- ❌ View consumption history
- ❌ Cost per print calculations
- ❌ CSV export UI

### Decision 4: Display Format

**Question**: How should spools be displayed?

**Options Considered**:
1. Card/Grid view only (visual, colorful)
2. Table view only (dense, spreadsheet)
3. **Hybrid with toggle** (user choice)

**Decision**: Hybrid (default cards, toggle to table) ✅

**Rationale**:
- Best of both worlds
- Cards better for visual inventory (color matters!)
- Table better for scanning many spools
- User preference saved in localStorage
- Matches existing file management pattern

### Decision 5: Add/Edit Workflow

**Question**: How should users add or edit spools?

**Options Considered**:
1. **Modal dialog** (overlay popup)
2. Slide-out panel (drawer from side)
3. In-page form (expands on same page)

**Decision**: Modal dialog ✅

**Rationale**:
- Consistent with existing UI patterns (printer add/edit uses modals)
- Clean, focused interaction
- Adequate space for ~10 form fields
- Familiar pattern for users

---

## Backend Architecture

### Activation Steps

**File 1: `src/main.py`** (3 changes):

```python
# 1. Add import at top
from src.api.routers.materials import router as materials_router

# 2. In lifespan manager, add service initialization:
material_service = MaterialService(database, event_service)
await material_service.initialize()
app.state.material_service = material_service

# 3. Register router with other routers:
app.include_router(materials_router, prefix="/api/v1", tags=["Materials"])
```

**File 2: `src/utils/dependencies.py`** (1 function):

```python
from src.services.material_service import MaterialService

async def get_material_service(request: Request) -> MaterialService:
    """Get material service instance from app state."""
    return request.app.state.material_service
```

**Testing**:
- Start server: `python src/main.py`
- Access Swagger UI: `http://localhost:8000/docs`
- Test endpoints: Try `GET /api/v1/materials` (should return `[]`)
- Verify tables: Check database for `materials` and `material_consumption` tables

### API Endpoints to Use

**Primary Operations**:
```
GET /api/v1/materials
→ Returns list of all spools with optional filters
→ Query params: material_type, brand, color, low_stock, printer_id

POST /api/v1/materials
→ Creates new spool
→ Body: MaterialCreate (type, brand, color, weight, cost, vendor, etc.)

PATCH /api/v1/materials/{id}
→ Updates existing spool
→ Body: MaterialUpdate (remaining_weight, cost_per_kg, notes, printer_id)

DELETE /api/v1/materials/{id}
→ Deletes spool (soft delete)
→ Currently returns 501 - will implement as part of this phase
```

**Supporting Operations**:
```
GET /api/v1/materials/stats
→ Returns statistics: total spools, low stock count, total value

GET /api/v1/materials/types
→ Returns available enums for dropdowns
→ Response: { material_types: [...], brands: [...], colors: [...] }

GET /api/v1/materials/{id}
→ Get single spool details (for edit form pre-fill)
```

**Not Used in Phase A**:
```
POST /api/v1/materials/consumption  → Phase B (job integration)
GET /api/v1/materials/report        → Phase B (analytics)
GET /api/v1/materials/export        → Phase B (export UI)
```

---

## Frontend UI Design

### Navigation Structure

**Main Navigation**:
```
[Dashboard] [Drucker] [Aufträge] [Drucker-Dateien] [Filamente] [Library] [Ideas] [Analytics]
                                                         ^^^ NEW
```

**Position**: Between "Drucker-Dateien" and "Library"
**Icon**: 🧵 (spool/coil emoji or similar)
**Active State**: Blue underline (matching existing pattern)

### Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Filamente                                  [+ Neue Spule]   │
├─────────────────────────────────────────────────────────────┤
│ 📊 Stats Bar:                                               │
│    12 Spulen | 3 Fast leer | 456,78 € Gesamtwert          │
├─────────────────────────────────────────────────────────────┤
│ Filters & Controls:                                         │
│    Material: [Alle ▼] Marke: [Alle ▼] Farbe: [Alle ▼]     │
│    Status: [Alle ▼]  Sortieren: [Name ▼]                   │
│    Ansicht: [Cards 🔲] [Table ☰]                           │
├─────────────────────────────────────────────────────────────┤
│ Main Content Area:                                          │
│    [Spool cards in grid OR table view]                     │
└─────────────────────────────────────────────────────────────┘
```

### Card View Design

```
┌───────────────────────────┐
│ 🔴 RED                [✏️]│  ← Color circle + edit button
│ PLA ECO                   │  ← Material type (bold, 16px)
│ OVERTURE                  │  ← Brand (14px)
├───────────────────────────┤
│ ▓▓▓▓▓▓▓▓▓▓░░░░ 85%       │  ← Progress bar + percentage
│ 850g / 1000g              │  ← Remaining / Total weight
├───────────────────────────┤
│ 💶 14,50 € (17,06 €/kg)   │  ← Current value (cost/kg)
│ 📦 Amazon.de              │  ← Vendor
│ 🗓️ 15.10.2024             │  ← Purchase date
└───────────────────────────┘
```

**Card States**:
- **Normal (>20%)**: White background, green progress bar
- **Low stock (<20%)**: Light yellow background, orange progress bar, ⚠️ icon
- **Empty (0%)**: Light gray background, red bar, grayed text

**Grid Layout**:
- Desktop (>1024px): 4 cards per row
- Tablet (768-1024px): 2 cards per row
- Mobile (<768px): 1 card per row (stacked)
- CSS Grid with `gap: 1rem`

**Interactions**:
- Click card: Open edit modal
- Hover: Subtle shadow lift effect
- Edit button: Quick access (also opens edit modal)

### Table View Design

```
+----------+-----------+-------+--------------+--------+---------+---------+
| Material | Marke     | Farbe | Verbleibend  | Status | Kosten  | Aktionen|
+----------+-----------+-------+--------------+--------+---------+---------+
| PLA ECO  | OVERTURE  | 🔴    | 850g / 1kg   | ✅ 85% | 14,50€  | ✏️ 🗑️  |
| PETG     | PRUSAMENT | 🔵    | 200g / 1kg   | ⚠️ 20% | 8,00€   | ✏️ 🗑️  |
| TPU      | BAMBU     | ⚫    | 950g / 1kg   | ✅ 95% | 42,75€  | ✏️ 🗑️  |
+----------+-----------+-------+--------------+--------+---------+---------+
```

**Table Features**:
- Sortable columns (click header to toggle asc/desc)
- Color column: Emoji circle representing color
- Status column: Percentage + emoji (✅ normal, ⚠️ low stock)
- Action column: Edit (pencil) + Delete (trash) icons
- Sticky header on scroll
- Alternating row colors (white/light gray)
- Responsive: Horizontal scroll on mobile

### Modal Form Design

**Add New Spool Modal**:
```
┌─────────────────────────────────────────┐
│ Neue Spule hinzufügen              [×]  │
├─────────────────────────────────────────┤
│                                         │
│ Material:     [PLA_ECO            ▼]   │
│ Marke:        [OVERTURE           ▼]   │
│ Farbe:        [RED                ▼]   │
│ Durchmesser:  [1.75mm             ▼]   │
│                                         │
│ Gewicht (g):           [1000      ]    │
│ Verbleibendes Gewicht: [1000      ]    │
│   (defaults to full weight)            │
│                                         │
│ Kosten pro kg (€):     [17.06     ]    │
│ Gesamtkosten (€):      [17.06     ]    │
│   (auto-calculated)                    │
│                                         │
│ Kaufdatum:    [2024-11-03   ]          │
│   (date picker, defaults to today)     │
│                                         │
│ Lieferant:    [Amazon.de    ]          │
│ Chargennummer: [BATCH-2024-10] (opt.)  │
│ Notizen:      [              ] (opt.)  │
│               [              ]          │
│                                         │
│         [Abbrechen] [Speichern]        │
│                                         │
└─────────────────────────────────────────┘
```

**Form Fields**:

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| Material | Dropdown | ✅ | None | Must select |
| Marke | Dropdown | ✅ | None | Must select |
| Farbe | Dropdown | ✅ | None | Must select |
| Durchmesser | Dropdown | ✅ | 1.75mm | 1.75 or 2.85 |
| Gewicht | Number | ✅ | None | > 0 |
| Verbleibendes Gewicht | Number | ✅ | = Gewicht | 0 to Gewicht |
| Kosten pro kg | Number | ✅ | None | > 0 |
| Gesamtkosten | Calculated | N/A | Auto | weight/1000 × cost_per_kg |
| Kaufdatum | Date | ✅ | Today | Valid date |
| Lieferant | Text | ✅ | None | Non-empty |
| Chargennummer | Text | ❌ | Empty | Any |
| Notizen | Textarea | ❌ | Empty | Any |

**Edit Spool Modal**:
- Identical layout to "Add"
- Title: "Spule bearbeiten"
- All fields pre-filled with current values
- Most common edit: Update "Verbleibendes Gewicht" after changing spool

**Form Behavior**:
- Dropdowns populated from `GET /api/v1/materials/types`
- Real-time cost calculation: `total_cost = (weight / 1000) × cost_per_kg`
- Validation on submit: Show errors below fields in red
- Success: Close modal, refresh list, show toast
- Cancel: Close modal without saving

### Filtering & Sorting

**Filter Controls**:
```
Material: [Alle ▼]  → Multi-select (PLA, PETG, TPU, etc.)
Marke:    [Alle ▼]  → Multi-select (OVERTURE, PRUSAMENT, etc.)
Farbe:    [Alle ▼]  → Multi-select (RED, BLUE, BLACK, etc.)
Status:   [Alle ▼]  → Single-select (Alle | Ausreichend | Fast leer | Leer)

[Clear Filters] button (appears when filters active)
"3 aktive Filter" indicator
```

**Sort Control**:
```
Sortieren: [Name ▼]
Options:
  - Name (A-Z / Z-A)
  - Marke (A-Z / Z-A)
  - Farbe (A-Z / Z-A)
  - Verbleibend % (aufsteigend / absteigend)
  - Kaufdatum (neueste / älteste)
  - Kosten (niedrig → hoch / hoch → niedrig)
```

**Filter Behavior**:
- Client-side filtering (fast, no server calls)
- Multi-select: Show spools matching ANY selected option
- Status filter:
  - "Ausreichend": > 20% remaining
  - "Fast leer": 5-20% remaining
  - "Leer": < 5% remaining
- Persist filter state in localStorage

### Statistics Bar

**Display**:
```
📊 12 Spulen | 3 Fast leer | 456,78 € Gesamtwert
```

**Data Source**: `GET /api/v1/materials/stats`

**Breakdown**:
- Total spools: Count of all active spools
- Low stock: Count where remaining < 20%
- Total value: Sum of (remaining_weight / 1000) × cost_per_kg for all spools

**Styling**:
- Light background (light blue/gray)
- Padding: 1rem
- Font size: 14px
- Icons: Emoji or Font Awesome

### Empty States

**No Spools Yet**:
```
┌─────────────────────────────────────┐
│                                     │
│          📦                         │
│                                     │
│   Noch keine Filamente vorhanden   │
│                                     │
│   Fügen Sie Ihre erste Spule       │
│   hinzu, um loszulegen!            │
│                                     │
│        [+ Neue Spule]               │
│                                     │
└─────────────────────────────────────┘
```

**No Filter Results**:
```
┌─────────────────────────────────────┐
│          🔍                         │
│                                     │
│   Keine Spulen gefunden.           │
│   Filter anpassen?                 │
│                                     │
│        [Clear Filters]              │
└─────────────────────────────────────┘
```

### Low Stock Alert Banner

**When**: Any spool < 20% remaining

**Display**:
```
┌─────────────────────────────────────────────────────┐
│ ⚠️ 3 Filamente fast leer - [Ansehen]               │
└─────────────────────────────────────────────────────┘
```

**Behavior**:
- Yellow background, darker yellow border
- Persistent (stays until clicked or dismissed)
- Click "Ansehen": Applies filter "Status: Fast leer"
- Dismissible with [×] button
- Reappears on page reload if condition still true

---

## Data Flow

### Page Load Sequence

```
1. User clicks "Filamente" tab
   ↓
2. Frontend: Show loading spinner
   ↓
3. Parallel API calls:
   - GET /api/v1/materials             → Fetch all spools
   - GET /api/v1/materials/stats       → Fetch statistics
   - GET /api/v1/materials/types       → Fetch enums (for dropdowns)
   ↓
4. Store data in MaterialsManager state
   ↓
5. Apply saved filters/sort from localStorage (if any)
   ↓
6. Render UI:
   - Stats bar
   - Filter controls (populate dropdowns)
   - Cards or table (based on saved view preference)
   ↓
7. Check for low stock alerts
   ↓
8. Hide loading spinner, show content
```

### Create New Spool Flow

```
1. User clicks [+ Neue Spule]
   ↓
2. Open modal with empty form
   ↓
3. Populate dropdowns from cached enums
   ↓
4. User fills form:
   - Select material, brand, color, diameter
   - Enter weight, cost, vendor
   - Optionally: batch number, notes
   ↓
5. User clicks [Speichern]
   ↓
6. Frontend validation:
   - Required fields filled?
   - Weight > 0?
   - Cost > 0?
   - Remaining ≤ Total weight?
   ↓
7. POST /api/v1/materials
   Body: {
     material_type: "PLA_ECO",
     brand: "OVERTURE",
     color: "RED",
     diameter: 1.75,
     weight: 1000,
     remaining_weight: 1000,
     cost_per_kg: 17.06,
     vendor: "Amazon.de",
     purchase_date: "2024-11-03",
     batch_number: "BATCH-2024-10",
     notes: ""
   }
   ↓
8. Backend:
   - Validates data
   - Creates database record
   - Returns created spool with ID
   ↓
9. Success:
   - Close modal
   - Refresh spool list (GET /api/v1/materials)
   - Refresh stats (GET /api/v1/materials/stats)
   - Show success toast: "Spule erfolgreich hinzugefügt"
   ↓
10. Error (validation):
   - Keep modal open
   - Show errors below relevant fields
   - Example: "Gewicht muss größer als 0 sein"
   ↓
11. Error (network/server):
   - Close modal
   - Show error toast: "Fehler beim Hinzufügen"
```

### Edit Spool Flow

```
1. User clicks [✏️] on card/table row
   ↓
2. Fetch current data: GET /api/v1/materials/{id}
   ↓
3. Open modal with pre-filled form
   ↓
4. User modifies fields (commonly: remaining_weight)
   ↓
5. User clicks [Speichern]
   ↓
6. Frontend validation (same as create)
   ↓
7. PATCH /api/v1/materials/{id}
   Body: {
     remaining_weight: 850,
     notes: "Updated after print"
   }
   (only changed fields sent)
   ↓
8. Backend updates record
   ↓
9. Success:
   - Close modal
   - Update spool in list (no full refresh needed)
   - Update stats if low stock status changed
   - Show toast: "Spule aktualisiert"
   ↓
10. Error handling (same as create)
```

### Delete Spool Flow

```
1. User clicks [🗑️] on card/table row
   ↓
2. Show confirmation dialog:
   "Spule wirklich löschen?"
   [Abbrechen] [Löschen]
   ↓
3. User confirms
   ↓
4. DELETE /api/v1/materials/{id}
   ↓
5. Backend soft-deletes record
   (Note: Currently returns 501, we'll implement)
   ↓
6. Success:
   - Remove from list (smooth animation)
   - Update stats
   - Show toast: "Spule gelöscht"
   ↓
7. Error (404):
   - Toast: "Spule nicht gefunden"
   - Refresh list (may have been deleted elsewhere)
   ↓
8. Error (network/server):
   - Toast: "Fehler beim Löschen"
   - Don't modify UI
```

### Filter/Sort Flow (Client-Side)

```
1. User changes filter or sort option
   ↓
2. Update state:
   - store.filters.material_type = ["PLA", "PETG"]
   - store.sort = { field: "remaining", order: "asc" }
   ↓
3. Apply filters:
   filtered = spools.filter(s => {
     return (
       filters.material_type.includes(s.material_type) &&
       filters.brand.includes(s.brand) &&
       filters.color.includes(s.color) &&
       filters.status.matches(s.remaining_percentage)
     );
   })
   ↓
4. Apply sorting:
   sorted = filtered.sort((a, b) => {
     if (sort.field === "remaining") {
       return sort.order === "asc"
         ? a.remaining_percentage - b.remaining_percentage
         : b.remaining_percentage - a.remaining_percentage;
     }
     // ... other fields
   })
   ↓
5. Re-render view (cards or table) with sorted/filtered data
   ↓
6. Save filter/sort state to localStorage
   ↓
7. Update URL query params (optional, for sharing)
```

---

## Error Handling

### Success Feedback (Toast Notifications)

**Location**: Top-right corner
**Duration**: 3 seconds auto-dismiss
**Dismissible**: Yes (click [×])

**Messages**:
- ✅ "Spule erfolgreich hinzugefügt" (green)
- ℹ️ "Spule aktualisiert" (blue)
- 🗑️ "Spule gelöscht" (gray)

### Validation Errors (400 Bad Request)

**Display**: Inline below form fields in modal
**Behavior**: Keep modal open for correction

**Examples**:
```
Gewicht (g): [0      ]
             ⚠️ Gewicht muss größer als 0 sein

Verbleibendes Gewicht: [1500   ]
                       ⚠️ Kann nicht größer als Gesamtgewicht sein

Lieferant: [     ]
           ⚠️ Lieferant ist erforderlich
```

### Not Found (404)

**Scenario**: Spool deleted by another user/session

**Response**:
- Toast: "Spule nicht gefunden - möglicherweise bereits gelöscht"
- Automatically refresh list
- Remove stale item from UI

### Server Errors (500 Internal Server Error)

**Response**:
- Toast: "Serverfehler - bitte später erneut versuchen"
- Log full error to console for debugging
- Don't modify UI state (keep showing old data)
- Allow retry

### Network Errors (No Connection)

**Response**:
- Toast: "Netzwerkfehler - Verbindung zum Server fehlgeschlagen"
- Show [Retry] button in toast
- Gray out UI with semi-transparent overlay
- Prevent user actions until connection restored

### Low Stock Alerts

**Trigger**: Spool remaining < 20%

**Backend**: Emits `material_low_stock` event (already implemented)

**Frontend**:
- Listen for event (if WebSocket connected)
- OR check on every list refresh
- Show persistent banner at top:
  ```
  ⚠️ 3 Filamente fast leer - [Ansehen] [×]
  ```
- Yellow background (#FFF3CD)
- Click "Ansehen": Apply filter "Status: Fast leer"
- Click [×]: Dismiss until next reload

### Empty States

**No Spools Yet**:
- Friendly message with prominent [+ Neue Spule] button
- Center of page
- Light illustration or icon

**No Filter Results**:
- Message: "Keine Spulen gefunden"
- Suggest: "Filter anpassen?"
- Show [Clear Filters] button

---

## Implementation Details

### File Structure

**New Files**:
```
frontend/
├── js/
│   └── materials.js           (~500 lines)
└── css/
    └── (styles.css updated)   (+100 lines)

docs/
└── plans/
    ├── 2025-11-03-material-management-design.md (this file)
    ├── material-integration-phase-b.md
    └── material-nfc-phase-c.md
```

**Modified Files**:
```
src/
├── main.py                    (+10 lines)
└── utils/
    └── dependencies.py        (+5 lines)

frontend/
└── index.html                 (+30 lines)
```

### materials.js Module Structure

```javascript
/**
 * MaterialsManager - Manages spool inventory UI
 */
class MaterialsManager {
    constructor() {
        this.materials = [];        // All spools from API
        this.filteredMaterials = []; // After filters applied
        this.stats = {};            // Summary statistics
        this.enums = {};            // Available types/brands/colors
        this.currentView = 'cards'; // 'cards' or 'table'
        this.filters = {
            material_types: [],
            brands: [],
            colors: [],
            status: 'all' // 'all', 'sufficient', 'low', 'empty'
        };
        this.sort = {
            field: 'name',
            order: 'asc' // 'asc' or 'desc'
        };
    }

    /**
     * Initialize on page load
     */
    async initialize() {
        // Load saved preferences
        this.loadPreferences();

        // Fetch data
        await Promise.all([
            this.loadMaterials(),
            this.loadStats(),
            this.loadEnums()
        ]);

        // Setup UI
        this.setupEventListeners();
        this.applyFilters();
        this.render();
        this.checkLowStockAlerts();
    }

    /**
     * API Calls
     */
    async loadMaterials() {
        const response = await fetch('/api/v1/materials');
        this.materials = await response.json();
    }

    async loadStats() {
        const response = await fetch('/api/v1/materials/stats');
        this.stats = await response.json();
    }

    async loadEnums() {
        const response = await fetch('/api/v1/materials/types');
        this.enums = await response.json();
    }

    /**
     * Rendering
     */
    render() {
        this.renderStats();
        this.renderFilters();

        if (this.currentView === 'cards') {
            this.renderCardView();
        } else {
            this.renderTableView();
        }
    }

    renderStats() {
        // Display: "📊 12 Spulen | 3 Fast leer | 456,78 € Wert"
    }

    renderFilters() {
        // Populate filter dropdowns with enums
    }

    renderCardView() {
        // Generate grid of spool cards
    }

    renderTableView() {
        // Generate sortable table
    }

    /**
     * Filtering & Sorting
     */
    applyFilters() {
        this.filteredMaterials = this.materials.filter(m => {
            // Apply all active filters
        }).sort((a, b) => {
            // Apply sorting
        });
    }

    /**
     * Modal Management
     */
    openAddModal() {
        // Show modal with empty form
    }

    openEditModal(materialId) {
        // Fetch material data and show pre-filled form
    }

    closeModal() {
        // Hide modal and reset form
    }

    /**
     * CRUD Operations
     */
    async saveMaterial(formData, materialId = null) {
        if (materialId) {
            // PATCH /api/v1/materials/{id}
        } else {
            // POST /api/v1/materials
        }
    }

    async deleteMaterial(materialId) {
        // Show confirmation
        // DELETE /api/v1/materials/{id}
    }

    /**
     * UI Helpers
     */
    showToast(message, type = 'success') {
        // Display toast notification
    }

    toggleView(viewType) {
        this.currentView = viewType;
        this.savePreferences();
        this.render();
    }

    checkLowStockAlerts() {
        const lowStock = this.materials.filter(m =>
            m.remaining_percentage < 20
        );
        if (lowStock.length > 0) {
            this.showLowStockBanner(lowStock.length);
        }
    }

    /**
     * Persistence
     */
    savePreferences() {
        localStorage.setItem('materials_view', this.currentView);
        localStorage.setItem('materials_filters', JSON.stringify(this.filters));
        localStorage.setItem('materials_sort', JSON.stringify(this.sort));
    }

    loadPreferences() {
        this.currentView = localStorage.getItem('materials_view') || 'cards';
        this.filters = JSON.parse(localStorage.getItem('materials_filters')) || this.filters;
        this.sort = JSON.parse(localStorage.getItem('materials_sort')) || this.sort;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('materials-section')) {
        window.materialsManager = new MaterialsManager();
        window.materialsManager.initialize();
    }
});
```

### CSS Styling Approach

**New Classes** (add to `frontend/css/styles.css`):

```css
/* Materials Section */
#materials-section {
    padding: 2rem;
}

/* Stats Bar */
.materials-stats {
    background: #f0f4f8;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    font-size: 14px;
}

/* Filter Controls */
.materials-filters {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.materials-filters select {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
}

/* View Toggle */
.view-toggle {
    display: flex;
    gap: 0.5rem;
}

.view-toggle button {
    padding: 0.5rem 1rem;
    border: 1px solid #ddd;
    background: white;
    cursor: pointer;
}

.view-toggle button.active {
    background: #007bff;
    color: white;
    border-color: #007bff;
}

/* Card View */
.materials-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
}

.material-card {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: box-shadow 0.2s;
}

.material-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.material-card.low-stock {
    background: #fff3cd;
    border-color: #ffc107;
}

.material-card.empty {
    background: #f8f9fa;
    opacity: 0.7;
}

/* Card Content */
.material-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.material-color-indicator {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: inline-block;
}

.material-card-type {
    font-size: 16px;
    font-weight: bold;
    margin: 0.5rem 0;
}

.material-card-brand {
    font-size: 14px;
    color: #666;
    margin-bottom: 1rem;
}

/* Progress Bar */
.material-progress {
    width: 100%;
    height: 20px;
    background: #e9ecef;
    border-radius: 10px;
    overflow: hidden;
    margin: 0.5rem 0;
}

.material-progress-bar {
    height: 100%;
    background: #28a745;
    transition: width 0.3s;
}

.material-progress-bar.low {
    background: #ffc107;
}

.material-progress-bar.empty {
    background: #dc3545;
}

/* Table View */
.materials-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
}

.materials-table th {
    background: #f8f9fa;
    padding: 0.75rem;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #dee2e6;
    cursor: pointer;
}

.materials-table th:hover {
    background: #e9ecef;
}

.materials-table td {
    padding: 0.75rem;
    border-bottom: 1px solid #dee2e6;
}

.materials-table tr:nth-child(even) {
    background: #f8f9fa;
}

.materials-table tr:hover {
    background: #e9ecef;
}

/* Modal */
.material-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.material-modal-content {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
}

.material-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.material-modal-form .form-group {
    margin-bottom: 1rem;
}

.material-modal-form label {
    display: block;
    margin-bottom: 0.25rem;
    font-weight: 500;
}

.material-modal-form input,
.material-modal-form select,
.material-modal-form textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.material-modal-form .error {
    color: #dc3545;
    font-size: 12px;
    margin-top: 0.25rem;
}

/* Low Stock Banner */
.low-stock-banner {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Toast Notifications */
.toast {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 1rem;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    z-index: 1001;
    animation: slideIn 0.3s;
}

.toast.success {
    border-left: 4px solid #28a745;
}

.toast.error {
    border-left: 4px solid #dc3545;
}

.toast.info {
    border-left: 4px solid #007bff;
}

@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Responsive */
@media (max-width: 768px) {
    .materials-grid {
        grid-template-columns: 1fr;
    }

    .materials-filters {
        flex-direction: column;
    }

    .materials-table {
        font-size: 14px;
    }
}
```

### Backend Implementation (Delete Endpoint)

Currently `DELETE /api/materials/{id}` returns 501 (Not Implemented).

**Add to `src/api/routers/materials.py`**:

```python
@router.delete("/{material_id}")
async def delete_material(
    material_id: str,
    service: MaterialService = Depends(get_material_service)
):
    """Delete a material spool (soft delete)."""
    try:
        # In MaterialService, implement soft delete:
        # UPDATE materials SET deleted_at = NOW() WHERE id = material_id
        await service.delete_material(material_id)
        return {"message": "Material deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Add to `src/services/material_service.py`**:

```python
async def delete_material(self, material_id: str):
    """Soft delete a material spool."""
    async with self.database.execute(
        "UPDATE materials SET deleted_at = ? WHERE id = ? AND deleted_at IS NULL",
        (datetime.now(), material_id)
    ) as cursor:
        if cursor.rowcount == 0:
            raise ValueError(f"Material {material_id} not found")

    await self.database.commit()

    # Clear cache
    if material_id in self._cache:
        del self._cache[material_id]
```

**Add column to schema** (migration):
```sql
ALTER TABLE materials ADD COLUMN deleted_at TIMESTAMP NULL;
```

---

## Testing Strategy

### Backend Testing

**Manual API Testing** (via Swagger UI at `/docs`):

1. **Test Service Initialization**:
   - Start server
   - Check logs for "MaterialService initialized"
   - Verify no errors

2. **Test GET /api/v1/materials**:
   - Should return `[]` (empty array) on first run
   - Status: 200 OK

3. **Test POST /api/v1/materials** (Create):
   ```json
   {
     "material_type": "PLA_ECO",
     "brand": "OVERTURE",
     "color": "RED",
     "diameter": 1.75,
     "weight": 1000,
     "remaining_weight": 1000,
     "cost_per_kg": 17.06,
     "vendor": "Amazon.de",
     "purchase_date": "2024-11-03"
   }
   ```
   - Should return created object with `id`
   - Status: 200 OK

4. **Test GET /api/v1/materials/{id}**:
   - Use ID from previous step
   - Should return full object
   - Status: 200 OK

5. **Test PATCH /api/v1/materials/{id}** (Update):
   ```json
   {
     "remaining_weight": 850,
     "notes": "Test update"
   }
   ```
   - Should return updated object
   - Status: 200 OK

6. **Test DELETE /api/v1/materials/{id}**:
   - Should soft delete
   - Status: 200 OK
   - GET should return 404 after delete

7. **Test GET /api/v1/materials/stats**:
   - Should return statistics
   - Status: 200 OK

8. **Test GET /api/v1/materials/types**:
   - Should return enums
   - Status: 200 OK

### Frontend Testing

**Manual UI Testing**:

1. **Navigation**:
   - [ ] "Filamente" tab visible in nav
   - [ ] Clicking tab switches to materials section
   - [ ] Active state (blue underline) works

2. **Empty State**:
   - [ ] Shows friendly message when no spools
   - [ ] [+ Neue Spule] button prominent

3. **Add Spool**:
   - [ ] Modal opens with empty form
   - [ ] Dropdowns populated with options
   - [ ] Required field validation works
   - [ ] Cost calculation updates live
   - [ ] Success toast shows after save
   - [ ] New spool appears in list

4. **View Modes**:
   - [ ] Card view displays correctly
   - [ ] Table view displays correctly
   - [ ] Toggle button switches views
   - [ ] View preference saved (refresh page test)

5. **Card View**:
   - [ ] Color indicator shows correct color
   - [ ] Progress bar fills correctly
   - [ ] Low stock shows yellow background
   - [ ] Hover effect works
   - [ ] Click opens edit modal

6. **Table View**:
   - [ ] All columns display correctly
   - [ ] Click header sorts ascending/descending
   - [ ] Edit/delete icons clickable
   - [ ] Hover highlights row

7. **Edit Spool**:
   - [ ] Modal opens with pre-filled data
   - [ ] Changes save correctly
   - [ ] Toast shows after save
   - [ ] List updates without full refresh

8. **Delete Spool**:
   - [ ] Confirmation dialog appears
   - [ ] Cancel keeps spool
   - [ ] Confirm removes spool
   - [ ] Toast shows after delete

9. **Filters**:
   - [ ] Material type filter works
   - [ ] Brand filter works
   - [ ] Color filter works
   - [ ] Status filter works (sufficient/low/empty)
   - [ ] Multiple filters combine correctly
   - [ ] Clear filters button appears when active
   - [ ] Clear filters resets to all spools

10. **Sorting**:
    - [ ] Sort by name works
    - [ ] Sort by remaining % works
    - [ ] Sort by cost works
    - [ ] Sort by date works
    - [ ] Ascending/descending toggle works

11. **Stats Bar**:
    - [ ] Total count correct
    - [ ] Low stock count correct
    - [ ] Total value calculated correctly

12. **Low Stock Alert**:
    - [ ] Banner shows when spool < 20%
    - [ ] "Ansehen" filters to low stock
    - [ ] Dismiss button hides banner
    - [ ] Banner reappears on reload if still low

13. **Responsive**:
    - [ ] Desktop (4 cards per row)
    - [ ] Tablet (2 cards per row)
    - [ ] Mobile (1 card, table scrolls)

14. **Error Handling**:
    - [ ] Validation errors show inline
    - [ ] Network error shows toast
    - [ ] Server error shows toast
    - [ ] 404 error refreshes list

### Edge Cases

- [ ] Add spool with minimal data (required only)
- [ ] Add spool with all optional fields
- [ ] Edit spool to reduce remaining to 0
- [ ] Edit spool to increase remaining (refill)
- [ ] Delete last spool (returns to empty state)
- [ ] Filter with no results
- [ ] Very long vendor name
- [ ] Very long notes
- [ ] Multiple rapid edits
- [ ] Network disconnect during operation

### Browser Testing

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Chrome (Android)
- [ ] Mobile Safari (iOS)

---

## Future Phases

### Phase B: Full Integration (1-2 days)

**Overview**: Connect materials to printers and jobs for automatic consumption tracking.

**Key Features**:
1. **Printer-Spool Association**:
   - Add "Spule laden" button to printer cards
   - Track which spool is loaded on which printer
   - Show loaded spool in printer status
   - Update material `printer_id` field

2. **Job-Material Consumption**:
   - Auto-link jobs to loaded spool
   - Record consumption when job completes
   - Create `material_consumption` records
   - Show material cost in job details

3. **Analytics Integration**:
   - Add material costs to cost analysis
   - Consumption trends over time
   - Material efficiency metrics
   - Top consuming job types

4. **Consumption History**:
   - Implement `GET /api/materials/consumption/history`
   - Show per-spool consumption history
   - Filter by date range, printer, job

5. **Export Integration**:
   - Add material data to analytics exports
   - Include in business reports
   - CSV/Excel with consumption breakdown

**Technical Changes**:
- Modify `JobService` to record consumption on completion
- Update printer status API to include loaded spool
- Add consumption history UI component
- Extend analytics service with material metrics

**Documentation**: `docs/plans/material-integration-phase-b.md`

### Phase C: NFC Smart Spools (2-3 days)

**Overview**: Integrate NFC tag reading/writing for OpenPrintTag standard compliance.

**Existing Specification**: `docs/archive/OPENPRINTTAG_INTEGRATION.md` (518 lines)

**Key Features**:
1. **NFC Read Support**:
   - Web NFC API integration (Chrome/Android)
   - Read OpenPrintTag data from NFC chips
   - Auto-populate form from tag
   - Mobile scanning interface

2. **Bidirectional Sync**:
   - Write consumption back to tags
   - Update remaining weight on tag
   - Sync tag ↔ database automatically

3. **Tag Management Hub**:
   - Bulk tag writing for new spools
   - Tag health monitoring
   - Import/export tag data

4. **Advanced Features**:
   - AMS/MMU multi-spool detection
   - Predictive alerts (runs out in X days)
   - Home Assistant ESPHome integration
   - Mobile app for NFC scanning

**Technical Stack**:
- Web NFC API (browser-based)
- OpenPrintTag protocol compliance
- Optional: ESPHome bridge for HA
- Optional: React Native mobile app

**Documentation**: `docs/plans/material-nfc-phase-c.md`

---

## Appendix

### Color Mapping (for UI)

```javascript
const COLOR_HEX = {
    'BLACK': '#000000',
    'WHITE': '#FFFFFF',
    'RED': '#FF0000',
    'BLUE': '#0000FF',
    'GREEN': '#00FF00',
    'YELLOW': '#FFFF00',
    'ORANGE': '#FFA500',
    'PURPLE': '#800080',
    'GRAY': '#808080',
    'BROWN': '#8B4513',
    'PINK': '#FFC0CB',
    'TRANSPARENT': '#00000000',
    'OTHER': '#CCCCCC'
};
```

### Material Type Display Names

```javascript
const MATERIAL_NAMES = {
    'PLA': 'PLA',
    'PLA_ECO': 'PLA ECO',
    'PLA_MATTE': 'PLA Matte',
    'PLA_SILK': 'PLA Silk',
    'PLA_TURBO': 'PLA Turbo',
    'PETG': 'PETG',
    'TPU': 'TPU',
    'ABS': 'ABS',
    'ASA': 'ASA',
    'NYLON': 'Nylon',
    'PC': 'Polycarbonat',
    'OTHER': 'Andere'
};
```

### German Translations

```javascript
const TRANSLATIONS = {
    // Actions
    'add': 'Hinzufügen',
    'edit': 'Bearbeiten',
    'delete': 'Löschen',
    'save': 'Speichern',
    'cancel': 'Abbrechen',
    'close': 'Schließen',

    // Fields
    'material': 'Material',
    'brand': 'Marke',
    'color': 'Farbe',
    'diameter': 'Durchmesser',
    'weight': 'Gewicht',
    'remaining_weight': 'Verbleibendes Gewicht',
    'cost_per_kg': 'Kosten pro kg',
    'total_cost': 'Gesamtkosten',
    'purchase_date': 'Kaufdatum',
    'vendor': 'Lieferant',
    'batch_number': 'Chargennummer',
    'notes': 'Notizen',

    // Status
    'sufficient': 'Ausreichend',
    'low': 'Fast leer',
    'empty': 'Leer',

    // Messages
    'no_materials': 'Noch keine Filamente vorhanden',
    'no_results': 'Keine Spulen gefunden',
    'add_first_spool': 'Fügen Sie Ihre erste Spule hinzu',
    'confirm_delete': 'Spule wirklich löschen?',
    'spool_added': 'Spule erfolgreich hinzugefügt',
    'spool_updated': 'Spule aktualisiert',
    'spool_deleted': 'Spule gelöscht',
    'error_adding': 'Fehler beim Hinzufügen',
    'error_updating': 'Fehler beim Aktualisieren',
    'error_deleting': 'Fehler beim Löschen',
    'network_error': 'Netzwerkfehler - Verbindung zum Server fehlgeschlagen',
    'server_error': 'Serverfehler - bitte später erneut versuchen',

    // Validation
    'required': 'Dieses Feld ist erforderlich',
    'must_be_positive': 'Muss größer als 0 sein',
    'remaining_too_high': 'Kann nicht größer als Gesamtgewicht sein'
};
```

---

## Conclusion

This design provides a complete blueprint for implementing Phase A of the material management system. The backend is already fully implemented and just needs activation. The frontend requires new code but follows existing patterns and conventions in the Printernizer codebase.

**Estimated Implementation Time**: 6-9 hours
**Next Steps**:
1. Review and approve this design
2. Create git feature branch
3. Implement backend activation (15 min)
4. Build frontend UI (4-6 hours)
5. Test thoroughly (1-2 hours)
6. Merge to master

**Future Work**: Phases B and C will build on this foundation to add printer/job integration and NFC tag support.
