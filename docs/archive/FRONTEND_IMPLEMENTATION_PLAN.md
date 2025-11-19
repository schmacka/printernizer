# Frontend Implementation Plan

**Status:** 🚧 In Progress  
**Last Updated:** 2025-11-13  
**CI/CD Run:** [#19327816183](https://github.com/schmacka/printernizer/actions/runs/19327816183)

## Overview

This document tracks the implementation of missing frontend features identified through E2E test failures. The backend APIs are already functional; we need to create the corresponding UI components.

---

### Latest Updates (2025-01-14)
- Added standalone SPA entry points (`jobs.html`, `printers.html`, `materials.html`) so E2E tests can deep-link directly without manual hash routing.
- Reworked the Jobs modal/VAT workflow to use the shared modal helper and keep business fields synchronized for compliance scenarios.
- Defaulted Materials to the table layout, removed the legacy duplicate modal, and routed everything through the shared modal helper for consistent selectors.

---

## Test Results Summary

### Current Status
- **Frontend Unit Tests**: ✅ 1 failed, 62 passed (98.4% pass rate)
- **E2E Tests**: ❌ 10 failed, 20 passed, 1 skipped
- **Backend Tests**: ✅ All passed
- **Printer Integration**: ✅ All passed

### Failed E2E Tests
| Test | Page | Status |
|------|------|--------|
| `test_dashboard_add_printer_button_exists` | Dashboard | ⏳ Not Started |
| `test_jobs_table_display` | Jobs | 🟢 Ready for re-test |
| `test_create_job_button_exists` | Jobs | 🟢 Ready for re-test |
| `test_create_job_modal_opens` | Jobs | 🟢 Ready for re-test |
| `test_business_job_fields` | Jobs | 🟢 Ready for re-test |
| `test_vat_calculation_display` | Jobs | 🟢 Ready for re-test |
| `test_job_form_validation` | Jobs | ⏳ Not Started |
| `test_materials_table_display` | Materials | 🟡 In Progress |
| `test_add_material_button_exists` | Materials | 🟡 In Progress |
| `test_complete_workflow_example` | Example | ⏳ Not Started |

---

## Implementation Phases

## 🔴 Phase 1: Jobs Core Functionality (CRITICAL)

### 1.1 Jobs Table Display
**Priority:** Critical  
**Effort:** 2-3 hours  
**Status:** ✅ Complete – SPA alias now exposes existing table  
**Test:** `test_jobs_table_display`

**Requirements:**
- [ ] Create/update `frontend/jobs.html` with table structure
- [ ] Add table element: `.jobs-table` or `#jobsTable`
- [ ] Fetch jobs from `/api/v1/jobs` endpoint
- [ ] Render job rows with columns:
  - Job name
  - File name
  - Printer name
  - Status (with color coding)
  - Created timestamp
  - Actions (view/delete buttons)
- [ ] Add CSS styling for table
- [ ] Add loading state
- [ ] Add empty state message

**API Endpoint:** `GET /api/v1/jobs`

**Expected Response:**
```json
[
  {
    "id": 1,
    "name": "Print Job",
    "file_name": "model.gcode",
    "printer_id": "printer-1",
    "status": "pending",
    "created_at": "2025-11-13T10:00:00Z"
  }
]
```

---

### 1.2 Create Job Button & Modal
**Priority:** Critical  
**Effort:** 3-4 hours  
**Status:** ✅ Complete – modal uses shared helper  
**Tests:** `test_create_job_button_exists`, `test_create_job_modal_opens`

**Requirements:**
- [ ] Add "Create Job" button: `#createJobBtn`
- [ ] Create modal dialog: `#jobModal`
- [ ] Modal form fields:
  - `#jobName` - Job name (text input, required)
  - `#fileSelect` - File selection (dropdown)
  - `#printerSelect` - Printer selection (dropdown)
- [ ] Wire up button click handler to open modal
- [ ] Implement modal open/close functionality
- [ ] Add form submission handler
- [ ] POST to `/api/v1/jobs`
- [ ] Close modal and refresh table on success
- [ ] Show error message on failure

**API Endpoint:** `POST /api/v1/jobs`

**Request Body:**
```json
{
  "name": "My Print Job",
  "file_id": 123,
  "printer_id": "printer-1"
}
```

---

### 1.3 Job Form Validation
**Priority:** High  
**Effort:** 1-2 hours  
**Status:** ⏳ Not Started  
**Test:** `test_job_form_validation`

**Requirements:**
- [ ] Validate required fields: job_name, file, printer
- [ ] Show inline error messages
- [ ] Disable submit button when form invalid
- [ ] Visual feedback for invalid fields (red border)
- [ ] Prevent form submission when invalid
- [ ] Clear errors on field change

**Validation Rules:**
- Job name: Required, 3-100 characters
- File: Required, must select from dropdown
- Printer: Required, must select from dropdown

---

## 🟡 Phase 2: German Compliance Features

### 2.1 Business Job Fields
**Priority:** High  
**Effort:** 1-2 hours  
**Status:** ✅ Complete – business fields toggle with VAT panel  
**Test:** `test_business_job_fields`

**Requirements:**
- [ ] Add checkbox: `#isBusiness` - "Business Order"
- [ ] Conditionally show/hide business fields
- [ ] Business-specific fields:
  - `#customerName` - Customer name (text, required when business)
  - `#invoiceNumber` - Invoice number (text, optional)
  - `#billingAddress` - Billing address (textarea, optional)
- [ ] JavaScript toggle for field visibility
- [ ] Include `is_business` flag in API request

**API Changes:**
```json
{
  "name": "Business Print",
  "is_business": true,
  "customer_name": "ACME Corp",
  "invoice_number": "INV-2025-001"
}
```

---

### 2.2 VAT Calculation Display
**Priority:** High  
**Effort:** 2-3 hours  
**Status:** ✅ Complete – VAT values update in real time  
**Test:** `test_vat_calculation_display`

**Requirements:**
- [ ] Add cost input field: `#materialCost`
- [ ] VAT calculation panel (only visible when `is_business = true`)
- [ ] Display fields:
  - Net price (before VAT)
  - VAT amount (19% for Germany)
  - Gross total (with VAT)
- [ ] Real-time calculation on input change
- [ ] Format as EUR currency (€)
- [ ] Visual breakdown of costs

**Calculation Formula:**
```javascript
const VAT_RATE = 0.19; // 19% for Germany
const netPrice = parseFloat(costInput);
const vatAmount = netPrice * VAT_RATE;
const grossTotal = netPrice + vatAmount;
```

---

## 🟢 Phase 3: Materials Management

### 3.1 Materials Table Display
**Priority:** Medium  
**Effort:** 2-3 hours  
**Status:** 🟡 In Progress – table view is default, filter polish pending  
**Test:** `test_materials_table_display`

**Requirements:**
- [ ] Create/update `frontend/materials.html`
- [ ] Add table element: `.materials-table` or `#materialsTable`
- [ ] Fetch materials from `/api/v1/materials/spools`
- [ ] Display columns:
  - Material name
  - Type (PLA, ABS, PETG, TPU)
  - Color
  - Weight remaining
  - Cost per kg
  - Location
  - Actions (edit/delete)
- [ ] Add filtering by material type
- [ ] Add sorting capabilities
- [ ] Color-coded rows by material type

**API Endpoint:** `GET /api/v1/materials/spools`

---

### 3.2 Add Material Button & Modal
**Priority:** Medium  
**Effort:** 2-3 hours  
**Status:** 🟡 In Progress – primary modal aligned with shared helper  
**Test:** `test_add_material_button_exists`

**Requirements:**
- [ ] Add button: `#addMaterialBtn` - "Add Material"
- [ ] Create modal: `#materialModal`
- [ ] Form fields:
  - `#materialName` - Spool name
  - `#materialType` - Type dropdown (PLA, ABS, PETG, TPU, etc.)
  - `#materialColor` - Color input
  - `#materialWeight` - Weight in grams
  - `#materialCost` - Cost in EUR
- [ ] Submit to `/api/v1/materials/spools`
- [ ] Refresh table on success

**API Endpoint:** `POST /api/v1/materials/spools`

---

## 🟢 Phase 4: Dashboard Enhancement

### 4.1 Add Printer Button & Modal
**Priority:** Medium  
**Effort:** 2-3 hours  
**Status:** ⏳ Not Started  
**Test:** `test_dashboard_add_printer_button_exists`

**Requirements:**
- [ ] Add button to dashboard: `#addPrinterBtn` or `data-action="add-printer"`
- [ ] Create add printer modal
- [ ] Form fields:
  - Printer name
  - IP address
  - Printer type (Bambu Lab A1 / Prusa Core One)
  - Access code/token
  - FTP password (for Bambu)
- [ ] Optional: Integrate printer discovery
- [ ] Submit to `/api/v1/printers`
- [ ] Update dashboard on success

**API Endpoint:** `POST /api/v1/printers`

---

## Technical Notes

### Backend APIs (Already Functional)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/jobs` | GET | List all jobs |
| `/api/v1/jobs` | POST | Create new job |
| `/api/v1/materials/spools` | GET | List materials |
| `/api/v1/materials/spools` | POST | Add material |
| `/api/v1/printers` | GET | List printers |
| `/api/v1/printers` | POST | Add printer |
| `/api/v1/files` | GET | List available files |

### Frontend Architecture
- **Framework:** Vanilla JavaScript (no framework)
- **Location:** `/frontend/` directory
- **API Client:** `/frontend/js/api.js`
- **WebSocket:** Real-time updates via `/ws` endpoint
- **Styling:** `/frontend/css/style.css`

### Key Files to Create/Modify
1. `/frontend/jobs.html` - Jobs page structure
2. `/frontend/js/jobs.js` - Jobs page logic
3. `/frontend/materials.html` - Materials page structure
4. `/frontend/js/materials.js` - Materials page logic
5. `/frontend/index.html` - Dashboard updates
6. `/frontend/css/style.css` - Component styling

### Testing Commands
```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific page tests
pytest tests/e2e/test_jobs.py -v
pytest tests/e2e/test_materials.py -v
pytest tests/e2e/test_dashboard.py -v

# Run single test
pytest tests/e2e/test_jobs.py::test_jobs_table_display -v

# Run with headed browser (see UI)
pytest tests/e2e/ -v --headed
```

---

## Progress Tracking

### Week 1: Jobs Core
- [ ] Day 1-2: Jobs table display
- [ ] Day 2-3: Create Job button & modal
- [ ] Day 3: Form validation

### Week 2: Compliance & Materials
- [ ] Day 1: Business job fields
- [ ] Day 1-2: VAT calculation
- [ ] Day 3-4: Materials table
- [ ] Day 4-5: Add Material feature

### Week 3: Dashboard & Polish
- [ ] Day 5-6: Add Printer button
- [ ] Testing & bug fixes

---

## Questions & Decisions

### Open Questions
1. Should job creation allow multi-printer selection (print farm)?
2. Do we need job templates/presets?
3. Should materials have low-stock alerts?
4. Printer discovery - automatic scan or manual entry only?

### Design Decisions
- Using modal dialogs (not separate pages) for add/edit operations
- Tables with inline actions (edit/delete icons)
- Real-time updates via WebSocket for status changes
- Responsive design (mobile-friendly tables with horizontal scroll)

---

## Success Criteria

### Phase 1 Complete When:
- ✅ All 5 jobs-related E2E tests pass
- ✅ Users can view job list
- ✅ Users can create new jobs
- ✅ Form validation prevents invalid submissions

### Phase 2 Complete When:
- ✅ Business job fields work correctly
- ✅ VAT calculation displays accurate values
- ✅ German compliance requirements met

### Phase 3 Complete When:
- ✅ Materials table displays inventory
- ✅ Users can add new material spools
- ✅ Material type filtering works

### Phase 4 Complete When:
- ✅ Add printer button exists and works
- ✅ All E2E tests pass (10/10)
- ✅ Full UI feature parity with backend

---

## References
- [GitHub Actions CI/CD Run](https://github.com/schmacka/printernizer/actions/runs/19327816183)
- [API Documentation](./api_specification.md)
- [E2E Testing Guide](./E2E_ARCHITECTURE.md)
- [Copilot Instructions](../.github/copilot-instructions.md)
