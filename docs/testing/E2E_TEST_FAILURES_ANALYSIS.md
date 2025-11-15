# E2E Playwright Test Failures Analysis

**Date:** November 13, 2025  
**CI/CD Run:** [19339499506](https://github.com/schmacka/printernizer/actions/runs/19339499506)  
**Status:** 10 tests failing, 18 passing, 1 skipped

---

## Executive Summary

The Printernizer E2E Playwright test suite has 10 failing tests, all related to **missing frontend page implementations** for the Jobs and Materials management features. The backend services are fully functional, but the vanilla JavaScript frontend lacks the HTML structure and JavaScript logic to render these pages.

**Root Cause:** Missing `#page-jobs` and `#page-materials` HTML sections and their associated JavaScript controllers.

**Impact:** E2E tests timeout waiting for page elements that don't exist in the DOM.

---

## Test Failure Details

### Failed Tests Summary

| Test File | Test Name | Failure Reason |
|-----------|-----------|----------------|
| `test_jobs.py` | `test_jobs_page_loads` | Timeout waiting for `#page-jobs` selector |
| `test_jobs.py` | `test_jobs_table_display` | Timeout waiting for `#page-jobs` selector |
| `test_jobs.py` | `test_create_job_button_exists` | Timeout waiting for `#page-jobs` selector |
| `test_jobs.py` | `test_create_job_modal_opens` | Timeout waiting for `#page-jobs` selector |
| `test_jobs.py` | `test_business_job_fields` | Timeout waiting for `#page-jobs` selector |
| `test_jobs.py` | `test_vat_calculation_display` | Timeout waiting for `#page-jobs` selector |
| `test_jobs.py` | `test_job_status_updates` | Timeout waiting for `#page-jobs` selector |
| `test_jobs.py` | `test_job_form_validation` | Timeout waiting for `#page-jobs` selector |
| `test_examples.py` | `test_complete_workflow_example` | Timeout waiting for `#page-jobs` selector |
| `test_materials.py` | `test_materials_page_loads` | Timeout waiting for `#page-materials` selector |

### Error Pattern

All failing tests exhibit the same error:
```
playwright._impl._errors.TimeoutError: Page.wait_for_selector: Timeout 5000ms exceeded.
Call log:
  - waiting for locator("#page-jobs") to be visible
```

Or for materials:
```
playwright._impl._errors.TimeoutError: Page.wait_for_selector: Timeout 5000ms exceeded.
Call log:
  - waiting for locator("#page-materials") to be visible
```

---

## Missing Implementation Details

### 1. Jobs Page (`#page-jobs`)

#### Required HTML Structure

The frontend needs a `<section id="page-jobs">` container in `/frontend/index.html` with:

```html
<section id="page-jobs" class="page-section" style="display: none;">
    <div class="page-header">
        <h1>Aufträge</h1>
        <button id="createJobBtn" class="btn-primary">Create Job</button>
    </div>
    
    <table id="jobsTable" class="jobs-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Drucker</th>
                <th>Datei</th>
                <th>Status</th>
                <th>Aktionen</th>
            </tr>
        </thead>
        <tbody id="jobsTableBody">
            <!-- Job rows will be inserted here -->
        </tbody>
    </table>
    
    <!-- Job creation modal -->
    <div id="jobModal" class="modal job-modal" style="display: none;">
        <div class="modal-content">
            <h2>Neuen Auftrag erstellen</h2>
            <form id="jobForm">
                <input type="text" id="jobName" name="job_name" placeholder="Auftragsname" required>
                <select id="fileSelect" name="file" required>
                    <option value="">Datei auswählen</option>
                </select>
                <select id="printerSelect" name="printer" required>
                    <option value="">Drucker auswählen</option>
                </select>
                
                <!-- Business job checkbox -->
                <label>
                    <input type="checkbox" id="isBusiness" name="is_business">
                    Geschäftsauftrag
                </label>
                
                <!-- Conditional business fields -->
                <div id="businessFields" style="display: none;">
                    <input type="text" id="customerName" name="customer_name" placeholder="Kundenname">
                    
                    <!-- VAT calculation display -->
                    <div class="vat-calculation">
                        <p>Netto: <span id="netAmount">0,00 EUR</span></p>
                        <p>MwSt (19%): <span id="vatAmount">0,00 EUR</span></p>
                        <p>Brutto: <span id="grossAmount">0,00 EUR</span></p>
                    </div>
                </div>
                
                <button type="submit" class="btn-primary submit-job-btn">Erstellen</button>
                <button type="button" class="btn-secondary" onclick="closeJobModal()">Abbrechen</button>
            </form>
        </div>
    </div>
</section>
```

#### Required Selectors (Per Page Object Model)

From `/tests/e2e/pages/jobs_page.py`:

| Element | Selector(s) | Purpose |
|---------|-------------|---------|
| Page section | `#page-jobs` | Main container |
| Jobs table | `.jobs-table`, `#jobsTable` | Table displaying jobs |
| Job row | `.job-row`, `tr.job` | Individual job rows |
| Create button | `button:has-text('Create Job')`, `#createJobBtn` | Opens creation modal |
| Job modal | `#jobModal`, `.job-modal` | Modal dialog |
| Job name input | `input[name='job_name']`, `#jobName` | Job name field |
| File select | `select[name='file']`, `#fileSelect` | File dropdown |
| Printer select | `select[name='printer']`, `#printerSelect` | Printer dropdown |
| Business checkbox | `input[name='is_business']`, `#isBusiness` | Business mode toggle |
| Customer name | `input[name='customer_name']`, `#customerName` | Customer field (conditional) |
| Submit button | `button[type='submit']`, `.submit-job-btn` | Form submission |
| Job status | `.job-status` | Status badge in table |

#### Required JavaScript (`/frontend/js/jobs.js`)

```javascript
class JobsPage {
    constructor() {
        this.jobs = [];
        this.init();
    }
    
    async init() {
        this.attachEventListeners();
        await this.loadJobs();
    }
    
    attachEventListeners() {
        // Create job button
        document.getElementById('createJobBtn')?.addEventListener('click', () => this.openModal());
        
        // Business checkbox toggle
        document.getElementById('isBusiness')?.addEventListener('change', (e) => {
            document.getElementById('businessFields').style.display = 
                e.target.checked ? 'block' : 'none';
        });
        
        // Form submission
        document.getElementById('jobForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitJob();
        });
    }
    
    async loadJobs() {
        try {
            const response = await fetch('/api/v1/jobs');
            this.jobs = await response.json();
            this.renderJobsTable();
        } catch (error) {
            console.error('Failed to load jobs:', error);
        }
    }
    
    renderJobsTable() {
        const tbody = document.getElementById('jobsTableBody');
        tbody.innerHTML = this.jobs.map(job => `
            <tr class="job-row job">
                <td>${job.id}</td>
                <td class="job-name">${job.name}</td>
                <td>${job.printer_name || '-'}</td>
                <td>${job.file_name || '-'}</td>
                <td><span class="job-status">${job.status}</span></td>
                <td>
                    <button onclick="jobsPage.deleteJob(${job.id})">Löschen</button>
                </td>
            </tr>
        `).join('');
    }
    
    openModal() {
        document.getElementById('jobModal').style.display = 'block';
        this.populateDropdowns();
    }
    
    closeModal() {
        document.getElementById('jobModal').style.display = 'none';
        document.getElementById('jobForm').reset();
    }
    
    async populateDropdowns() {
        // Load files and printers for dropdowns
        const [files, printers] = await Promise.all([
            fetch('/api/v1/files').then(r => r.json()),
            fetch('/api/v1/printers').then(r => r.json())
        ]);
        
        // Populate file select
        const fileSelect = document.getElementById('fileSelect');
        fileSelect.innerHTML = '<option value="">Datei auswählen</option>' +
            files.map(f => `<option value="${f.id}">${f.name}</option>`).join('');
            
        // Populate printer select
        const printerSelect = document.getElementById('printerSelect');
        printerSelect.innerHTML = '<option value="">Drucker auswählen</option>' +
            printers.printers.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    }
    
    async submitJob() {
        const formData = new FormData(document.getElementById('jobForm'));
        const jobData = Object.fromEntries(formData);
        
        // Form validation
        if (!jobData.job_name || !jobData.file || !jobData.printer) {
            alert('Bitte alle erforderlichen Felder ausfüllen');
            return;
        }
        
        try {
            const response = await fetch('/api/v1/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(jobData)
            });
            
            if (response.ok) {
                this.closeModal();
                await this.loadJobs();
            } else {
                alert('Fehler beim Erstellen des Auftrags');
            }
        } catch (error) {
            console.error('Failed to create job:', error);
        }
    }
    
    async deleteJob(jobId) {
        if (!confirm('Auftrag wirklich löschen?')) return;
        
        try {
            await fetch(`/api/v1/jobs/${jobId}`, { method: 'DELETE' });
            await this.loadJobs();
        } catch (error) {
            console.error('Failed to delete job:', error);
        }
    }
}

// Initialize when page is shown
let jobsPage;
window.showJobsPage = () => {
    if (!jobsPage) {
        jobsPage = new JobsPage();
    }
};
```

#### German Business Compliance Features

**VAT Calculation (19% MwSt):**
- Display net, VAT, and gross amounts in EUR
- Use German number formatting: `1.234,56 EUR`
- Implement real-time calculation when cost fields change
- Store VAT-related data in backend via Jobs API

**Business Mode Toggle:**
- Show/hide `#businessFields` div based on `#isBusiness` checkbox
- Customer name field becomes required when business mode is enabled
- VAT calculation panel only visible for business jobs

**Example VAT Calculation:**
```javascript
function calculateVAT(netAmount) {
    const vatRate = 0.19; // 19% German VAT
    const vatAmount = netAmount * vatRate;
    const grossAmount = netAmount + vatAmount;
    
    return {
        net: formatEUR(netAmount),
        vat: formatEUR(vatAmount),
        gross: formatEUR(grossAmount)
    };
}

function formatEUR(amount) {
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
}
```

---

### 2. Materials Page (`#page-materials`)

#### Required HTML Structure

The frontend needs a `<section id="page-materials">` container in `/frontend/index.html` with:

```html
<section id="page-materials" class="page-section" style="display: none;">
    <div class="page-header">
        <h1>Filamente</h1>
        <button id="addMaterialBtn" class="btn-primary">Add Material</button>
    </div>
    
    <table id="materialsTable" class="materials-table">
        <thead>
            <tr>
                <th>Name</th>
                <th>Typ</th>
                <th>Farbe</th>
                <th>Gewicht</th>
                <th>Kosten</th>
                <th>Aktionen</th>
            </tr>
        </thead>
        <tbody id="materialsTableBody">
            <!-- Material rows will be inserted here -->
        </tbody>
    </table>
    
    <!-- Material modal -->
    <div id="materialModal" class="modal material-modal" style="display: none;">
        <div class="modal-content">
            <h2>Filament hinzufügen</h2>
            <form id="materialForm">
                <input type="text" id="materialName" name="material_name" placeholder="Name" required>
                <select id="materialType" name="material_type" required>
                    <option value="PLA">PLA</option>
                    <option value="PETG">PETG</option>
                    <option value="ABS">ABS</option>
                    <option value="TPU">TPU</option>
                    <option value="Nylon">Nylon</option>
                </select>
                <input type="text" id="materialColor" name="color" placeholder="Farbe">
                <input type="number" id="materialWeight" name="weight" placeholder="Gewicht (g)" step="0.01">
                <input type="number" id="materialCost" name="cost" placeholder="Kosten (EUR)" step="0.01">
                
                <button type="submit" class="btn-primary submit-material-btn">Hinzufügen</button>
                <button type="button" class="btn-secondary" onclick="closeMaterialModal()">Abbrechen</button>
            </form>
        </div>
    </div>
</section>
```

#### Required Selectors (Per Page Object Model)

From `/tests/e2e/pages/materials_page.py`:

| Element | Selector(s) | Purpose |
|---------|-------------|---------|
| Page section | `#page-materials` | Main container |
| Materials table | `.materials-table`, `#materialsTable` | Table displaying materials |
| Material row | `.material-row`, `tr.material` | Individual material rows |
| Add button | `button:has-text('Add Material')`, `#addMaterialBtn` | Opens creation modal |
| Material modal | `#materialModal`, `.material-modal` | Modal dialog |
| Material name | `input[name='material_name']`, `#materialName` | Name field |
| Material type | `select[name='material_type']`, `#materialType` | Type dropdown |
| Color input | `input[name='color']`, `#materialColor` | Color field |
| Weight input | `input[name='weight']`, `#materialWeight` | Weight field |
| Cost input | `input[name='cost']`, `#materialCost` | Cost field |
| Submit button | `button[type='submit']`, `.submit-material-btn` | Form submission |

#### Required JavaScript Updates (`/frontend/js/materials.js`)

The file exists but needs to ensure proper page rendering with the expected selectors.

---

### 3. Frontend Routing

#### Hash-Based Navigation

The SPA uses hash-based routing. The router must detect:
- `/#jobs` → Show `#page-jobs`, hide others, call `showJobsPage()`
- `/#materials` → Show `#page-materials`, hide others, call `showMaterialsPage()`

#### Router Implementation (`/frontend/js/main.js` or router)

```javascript
// Page routing
function showPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page-section').forEach(page => {
        page.style.display = 'none';
    });
    
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show requested page
    const pageElement = document.getElementById(`page-${pageName}`);
    if (pageElement) {
        pageElement.style.display = 'block';
        
        // Mark nav link as active
        const navLink = document.querySelector(`[data-page="${pageName}"]`);
        if (navLink) navLink.classList.add('active');
        
        // Initialize page if needed
        if (pageName === 'jobs' && typeof showJobsPage === 'function') {
            showJobsPage();
        } else if (pageName === 'materials' && typeof showMaterialsPage === 'function') {
            showMaterialsPage();
        }
    }
}

// Handle hash changes
window.addEventListener('hashchange', () => {
    const hash = window.location.hash.slice(1) || 'dashboard';
    showPage(hash);
});

// Initial page load
document.addEventListener('DOMContentLoaded', () => {
    const hash = window.location.hash.slice(1) || 'dashboard';
    showPage(hash);
});
```

---

## Implementation Checklist

### Files to Create/Modify

- [ ] `/frontend/index.html`
  - [ ] Add `<section id="page-jobs">` with complete structure
  - [ ] Add `<section id="page-materials">` with complete structure
  
- [ ] `/frontend/js/jobs.js` (create new file)
  - [ ] JobsPage class with table rendering
  - [ ] Modal management (open/close)
  - [ ] Form validation
  - [ ] API integration (GET, POST, DELETE jobs)
  - [ ] Business mode toggle logic
  - [ ] VAT calculation for business jobs
  
- [ ] `/frontend/js/materials.js` (update existing)
  - [ ] Ensure proper page rendering with expected selectors
  - [ ] Modal and form handling
  - [ ] API integration
  
- [ ] `/frontend/js/main.js` or `/frontend/js/router.js`
  - [ ] Add hash routing for `#jobs` and `#materials`
  - [ ] Page initialization functions
  - [ ] Navigation state management

- [ ] `/frontend/css/jobs.css` (optional, if needed)
  - [ ] Jobs page specific styling
  - [ ] Modal styling
  - [ ] Business fields styling

### Testing After Implementation

1. **Manual Browser Testing:**
   - Navigate to `http://localhost:8000/#jobs`
   - Verify `#page-jobs` is visible
   - Click "Create Job" button, verify modal opens
   - Toggle business checkbox, verify customer fields appear
   - Fill form, verify validation works
   - Navigate to `http://localhost:8000/#materials`
   - Verify `#page-materials` is visible

2. **E2E Test Execution:**
   ```bash
   pytest tests/e2e/test_jobs.py -v
   pytest tests/e2e/test_materials.py -v
   ```

3. **Expected Results:**
   - All 10 failing tests should pass
   - Tests should complete within 5-second timeout
   - No new test failures introduced

---

## Backend API Validation

The backend APIs are already functional. Tests confirm:

### Jobs API (`/api/v1/jobs`)

- ✅ `GET /api/v1/jobs` - List all jobs
- ✅ `POST /api/v1/jobs` - Create new job
- ✅ `GET /api/v1/jobs/{id}` - Get job details
- ✅ `PUT /api/v1/jobs/{id}` - Update job
- ✅ `DELETE /api/v1/jobs/{id}` - Delete job

### Materials API (`/api/v1/materials`)

- ✅ `GET /api/v1/materials` - List all materials
- ✅ `POST /api/v1/materials` - Create new material
- ✅ `GET /api/v1/materials/{id}` - Get material details
- ✅ `PUT /api/v1/materials/{id}` - Update material
- ✅ `DELETE /api/v1/materials/{id}` - Delete material

**Note:** Backend implementation is complete. Frontend just needs to consume these APIs.

---

## Architecture Compliance

### Printernizer Frontend Standards

✅ **Vanilla JavaScript** - No frameworks (React, Vue, etc.)  
✅ **Hash-based SPA routing** - `/#page` navigation  
✅ **German language** - UI text in German  
✅ **German business compliance** - 19% VAT, EUR formatting  
✅ **Existing patterns** - Follow `dashboard.js`, `printers.js` structure  
✅ **API integration** - Use existing `/frontend/js/api.js` patterns  

### German Locale Requirements

- **Currency:** EUR with German formatting (`1.234,56 EUR`)
- **VAT Rate:** 19% (MwSt/Mehrwertsteuer)
- **Timezone:** Europe/Berlin
- **Date Format:** DD.MM.YYYY
- **Decimal Separator:** Comma (,)
- **Thousands Separator:** Period (.)

---

## Timeline and Effort Estimate

| Task | Estimated Time |
|------|----------------|
| HTML structure for Jobs page | 1 hour |
| HTML structure for Materials page | 30 minutes |
| Jobs page JavaScript logic | 2-3 hours |
| Materials page JavaScript updates | 1 hour |
| Router implementation | 30 minutes |
| VAT calculation logic | 1 hour |
| Testing and refinement | 1-2 hours |
| **Total** | **7-9 hours** |

---

## References

### Test Files
- `/tests/e2e/test_jobs.py` - Jobs page E2E tests
- `/tests/e2e/test_materials.py` - Materials page E2E tests
- `/tests/e2e/pages/jobs_page.py` - JobsPage object model
- `/tests/e2e/pages/materials_page.py` - MaterialsPage object model

### Existing Frontend Files
- `/frontend/index.html` - Main HTML file
- `/frontend/js/main.js` - Application initialization
- `/frontend/js/dashboard.js` - Reference implementation pattern
- `/frontend/js/printers.js` - Reference implementation pattern
- `/frontend/js/materials.js` - Existing file to update
- `/frontend/css/materials.css` - Existing materials styling

### CI/CD Logs
- [GitHub Actions Run #19339499506](https://github.com/schmacka/printernizer/actions/runs/19339499506)
- Job: "E2E Tests (Playwright)"
- Duration: 118.33s (0:01:58)
- Results: 10 failed, 18 passed, 1 skipped

---

## Conclusion

The E2E test failures are **entirely frontend-related** and require implementing missing HTML structure and JavaScript logic for the Jobs and Materials pages. The backend services are fully operational. Once the frontend implementation is complete, all 10 failing tests should pass, bringing the E2E test suite to near-100% pass rate.

**Priority:** High - These are core features required for production readiness.

**Risk:** Low - No backend changes needed, isolated frontend work.

**Impact:** Enables full CRUD functionality for Jobs and Materials management in the UI.
