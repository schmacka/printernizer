# Slicer Phase 3b — Model-centric detail view (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A model-centric detail view in the library that shows a model's derived print files and lets the user slice / re-slice / slice-and-print (with inline progress), download a print file, and print an existing print file — surfacing all of Phases 1–3a in the UI.

**Architecture:** Two small file-scoped backend endpoints (download + print-existing) added to the library router, plus a new vanilla-JS `ModelDetailView` module that renders a dedicated view inside the `#library` page (view-swap; the library grid hides while the detail shows, Back restores it).

**Tech Stack:** FastAPI (backend, pytest), vanilla JS/HTML/CSS (frontend, browser-verified via Playwright — no JS unit-test framework exists).

## Global Constraints

- Work on branch **`feature/slicer-phase3b-ui`** (this worktree is already on it). Conventional Commits; end each commit message with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Backend tests from the worktree root with the shared venv:
  `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest <path> -p no:cacheprovider --timeout=60 -q`. `asyncio_mode = auto`; DB tests close the Database (`await db.close()`).
- API routers: real sub-paths with a leading slash are fine; never a bare `"/"`. Use the project error envelope (`LibraryItemNotFoundError`, `HTTPException` mapped by the global handler).
- Services resolve from `app.state`: the library router already defines a local `get_library_service` (reads `src.main.app.state.library_service`); for printers use `from src.utils.dependencies import get_printer_service`.
- Verified printer path: `driver = await printer_service.get_printer_driver(printer_id)` (returns `BasePrinter|None`), `await printer_service.upload_file_to_printer(printer_id, local_path, remote_name)` (→ bool), `await driver.start_print(remote_name)` (→ bool).
- Slicing API contracts (verbatim): `POST /api/v1/slicing/library/{checksum}/slice` body = `SlicingJobRequest` (`file_checksum` overridden from URL; needs `slicer_id`, `profile_id`, optional `target_printer_id`); `POST /api/v1/slicing/slice-and-print` body = `SliceAndPrintRequest` (`file_checksum, slicer_id, profile_id, printer_id, auto_start`); `GET /api/v1/slicing/jobs/{id}` → `SlicingJobResponse` (has `status`, `progress`, `error_message`).
- Frontend: SPA in `frontend/index.html`; library page is `<div id="library" class="page">`, file grid `#libraryFilesGrid`. Use `CONFIG.API_BASE_URL` for fetch and `showToast(type, title, message)` (frontend/js/utils.js) for feedback. New scripts go in `index.html` before the closing body, after existing page scripts.
- Frontend verification is **browser-based** (Playwright via the `webapp-testing` skill / Playwright MCP): start the app, navigate, interact, assert via snapshot/screenshot. There is no jest/JS unit harness.
- English for all code/comments/UI copy.

---

## File structure
- `src/api/routers/library.py` (MODIFY) — `GET /files/{checksum}/download`, `POST /files/{checksum}/print`.
- `tests/services/test_library_download_print.py` (NEW) — endpoint tests via FastAPI app.
- `frontend/js/model-detail.js` (NEW) — `ModelDetailView`.
- `frontend/js/library.js` (MODIFY) — route `role='model'` clicks to the view; role badge.
- `frontend/index.html` (MODIFY) — `#modelDetailView` container + `<script>`.
- `frontend/css/components.css` (MODIFY) — view styles.

---

### Task 1: Library file download endpoint

**Files:**
- Modify: `src/api/routers/library.py`
- Create: `tests/services/test_library_download_print.py`

**Interfaces:**
- Produces: `GET /api/v1/library/files/{checksum}/download` → `FileResponse` of the file; 404 if missing.

- [ ] **Step 1: Write failing test** (`tests/services/test_library_download_print.py`)

Use FastAPI's `TestClient` against the real app with `app.state.library_service` set to a small fake that returns a known file path.

```python
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from src.main import app
    f = tmp_path / "out.gcode"
    f.write_text("; hello gcode\n")
    lib = MagicMock()
    lib.library_path = tmp_path
    lib.get_file_by_checksum = AsyncMock(return_value={
        "checksum": "ABC", "filename": "out.gcode", "library_path": "out.gcode",
        "file_type": ".gcode", "role": "printfile"})
    app.state.library_service = lib
    return TestClient(app)


def test_download_returns_bytes(client):
    r = client.get("/api/v1/library/files/ABC/download")
    assert r.status_code == 200
    assert r.content == b"; hello gcode\n"


def test_download_404_when_missing(client):
    client.app.state.library_service.get_file_by_checksum = AsyncMock(return_value=None)
    r = client.get("/api/v1/library/files/NOPE/download")
    assert r.status_code == 404
```

- [ ] **Step 2: Run, verify fail**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_library_download_print.py::test_download_returns_bytes -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — 404/route missing.

- [ ] **Step 3: Implement the download endpoint** (`src/api/routers/library.py`)

Add `from fastapi.responses import FileResponse` to the imports. Add the endpoint (near the other `/files/{checksum}` routes):

```python
@router.get("/files/{checksum}/download")
async def download_library_file(
    checksum: str,
    library_service = Depends(get_library_service),
):
    """Download the raw bytes of a library file."""
    row = await library_service.get_file_by_checksum(checksum)
    if not row:
        raise LibraryItemNotFoundError(checksum)
    abs_path = Path(library_service.library_path) / row["library_path"]
    if not abs_path.exists():
        raise LibraryItemNotFoundError(checksum, details={"reason": "file_missing"})
    return FileResponse(str(abs_path), filename=row.get("filename") or abs_path.name)
```

(`Path` is already imported in this router; if not, add `from pathlib import Path`.)

- [ ] **Step 4: Run, verify pass**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_library_download_print.py -k download -p no:cacheprovider --timeout=60 -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/api/routers/library.py tests/services/test_library_download_print.py
git commit -m "feat: add library file download endpoint

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Print-existing-printfile endpoint

**Files:**
- Modify: `src/api/routers/library.py`
- Modify: `tests/services/test_library_download_print.py` (append)

**Interfaces:**
- Produces: `POST /api/v1/library/files/{checksum}/print` body `{"printer_id": str}` → `{"status": "started", "filename": str}`; 404 missing; 400 non-printable.

- [ ] **Step 1: Write failing tests** (append)

```python
from unittest.mock import AsyncMock, MagicMock


def _printable_lib(tmp_path):
    f = tmp_path / "out.gcode"; f.write_text("; g\n")
    lib = MagicMock(); lib.library_path = tmp_path
    lib.get_file_by_checksum = AsyncMock(return_value={
        "checksum": "ABC", "filename": "out.gcode", "library_path": "out.gcode",
        "file_type": ".gcode", "role": "printfile"})
    return lib


def test_print_existing_calls_printer(client, tmp_path):
    app = client.app
    app.state.library_service = _printable_lib(tmp_path)
    driver = MagicMock(); driver.start_print = AsyncMock(return_value=True)
    psvc = MagicMock()
    psvc.get_printer_driver = AsyncMock(return_value=driver)
    psvc.upload_file_to_printer = AsyncMock(return_value=True)
    app.state.printer_service = psvc
    r = client.post("/api/v1/library/files/ABC/print", json={"printer_id": "p1"})
    assert r.status_code == 200 and r.json()["status"] == "started"
    psvc.upload_file_to_printer.assert_awaited()
    driver.start_print.assert_awaited()


def test_print_rejects_non_printfile(client, tmp_path):
    app = client.app
    f = tmp_path / "model.stl"; f.write_text("solid x\n")
    lib = MagicMock(); lib.library_path = tmp_path
    lib.get_file_by_checksum = AsyncMock(return_value={
        "checksum": "M", "filename": "model.stl", "library_path": "model.stl",
        "file_type": ".stl", "role": "model"})
    app.state.library_service = lib
    app.state.printer_service = MagicMock()
    r = client.post("/api/v1/library/files/M/print", json={"printer_id": "p1"})
    assert r.status_code == 400
```

- [ ] **Step 2: Run, verify fail**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_library_download_print.py -k print -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — route missing.

- [ ] **Step 3: Implement the print endpoint** (`src/api/routers/library.py`)

Add imports: `from src.utils.dependencies import get_printer_service`. Add a request model near the other models and the endpoint:

```python
class PrintFileRequest(BaseModel):
    printer_id: str


_PRINTABLE_EXT = {".gcode", ".gco", ".g", ".bgcode", ".3mf"}


@router.post("/files/{checksum}/print")
async def print_library_file(
    checksum: str,
    request: PrintFileRequest,
    library_service = Depends(get_library_service),
    printer_service = Depends(get_printer_service),
):
    """Upload an existing library print file to a printer and start the print."""
    row = await library_service.get_file_by_checksum(checksum)
    if not row:
        raise LibraryItemNotFoundError(checksum)
    file_type = (row.get("file_type") or "").lower()
    if row.get("role") != "printfile" and file_type not in _PRINTABLE_EXT:
        raise HTTPException(status_code=400, detail="File is not a printable print file")
    abs_path = Path(library_service.library_path) / row["library_path"]
    if not abs_path.exists():
        raise LibraryItemNotFoundError(checksum, details={"reason": "file_missing"})
    filename = row.get("filename") or abs_path.name
    driver = await printer_service.get_printer_driver(request.printer_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Printer not found")
    uploaded = await printer_service.upload_file_to_printer(request.printer_id, str(abs_path), filename)
    if not uploaded:
        raise HTTPException(status_code=502, detail="Failed to upload file to printer")
    started = await driver.start_print(filename)
    if not started:
        raise HTTPException(status_code=502, detail="Uploaded but failed to start print")
    return {"status": "started", "filename": filename}
```

- [ ] **Step 4: Run, verify pass**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_library_download_print.py -p no:cacheprovider --timeout=60 -q`
Expected: 4 passed (2 download + 2 print).

- [ ] **Step 5: Commit**

```bash
git add src/api/routers/library.py tests/services/test_library_download_print.py
git commit -m "feat: add endpoint to print an existing library print file

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: ModelDetailView scaffold + routing + header

**Files:**
- Create: `frontend/js/model-detail.js`
- Modify: `frontend/index.html` (container + script)
- Modify: `frontend/js/library.js` (route model clicks)
- Modify: `frontend/css/components.css` (view styles)

**Interfaces:**
- Produces (global): `window.modelDetailView` — `ModelDetailView` with `open(checksum)` and `close()`.

- [ ] **Step 1: Add the container + script to `index.html`**

Inside `<div id="library" class="page">`, after `#libraryFilesGrid` (and its surrounding container), add a sibling detail container:

```html
        <div id="modelDetailView" class="model-detail" style="display:none"></div>
```

Before `</body>` (with the other page scripts), add:

```html
    <script src="js/model-detail.js"></script>
```

- [ ] **Step 2: Create `frontend/js/model-detail.js`**

```javascript
/** Model-centric detail view: shows a model's print files + a slice panel. */
class ModelDetailView {
    constructor() {
        this.el = null;
        this.checksum = null;
        this._poll = null;
    }

    _container() {
        if (!this.el) this.el = document.getElementById('modelDetailView');
        return this.el;
    }

    async open(checksum) {
        this.checksum = checksum;
        const grid = document.getElementById('libraryFilesGrid');
        if (grid) grid.style.display = 'none';
        const stats = document.getElementById('libraryStats');
        if (stats) stats.style.display = 'none';
        const c = this._container();
        c.style.display = 'block';
        c.innerHTML = '<div class="loading">Loading…</div>';
        try {
            const res = await fetch(`${CONFIG.API_BASE_URL}/library/files/${checksum}`);
            if (!res.ok) throw new Error('not found');
            const model = await res.json();
            c.innerHTML = this._renderShell(model);
            c.querySelector('[data-act="back"]').addEventListener('click', () => this.close());
            await this.refreshPrintfiles();      // Task 4
            await this.renderSlicePanel();        // Task 5
        } catch (e) {
            c.innerHTML = '<div class="error">Failed to load model.</div>';
        }
    }

    close() {
        if (this._poll) { clearInterval(this._poll); this._poll = null; }
        const c = this._container();
        c.style.display = 'none';
        c.innerHTML = '';
        const grid = document.getElementById('libraryFilesGrid');
        if (grid) grid.style.display = '';
        const stats = document.getElementById('libraryStats');
        if (stats) stats.style.display = '';
    }

    _renderShell(model) {
        const name = model.display_name || model.filename || model.checksum;
        const dims = (model.model_width && model.model_height)
            ? `${Math.round(model.model_width)}×${Math.round(model.model_depth || 0)}×${Math.round(model.model_height)} mm` : '';
        return `
          <div class="model-detail-header">
            <button class="btn btn-secondary" data-act="back">← Library</button>
            <img class="model-detail-thumb" src="${CONFIG.API_BASE_URL}/library/files/${model.checksum}/thumbnail" onerror="this.style.display='none'"/>
            <div class="model-detail-title">
              <h2>${name}</h2>
              <div class="model-detail-meta">${dims}${dims ? ' · ' : ''}${model.file_type || ''}</div>
            </div>
          </div>
          <section class="model-detail-printfiles"><h3>Print files</h3><div id="mdPrintfiles"></div></section>
          <section class="model-detail-slice"><h3>Slice</h3><div id="mdSlice"></div></section>`;
    }

    // Filled in by later tasks:
    async refreshPrintfiles() { /* Task 4 */ }
    async renderSlicePanel() { /* Task 5 */ }
}
window.modelDetailView = new ModelDetailView();
```

- [ ] **Step 3: Route model clicks in `library.js`**

Find where a file card click calls `this.showFileDetail(file)` (the click handler set in `renderFiles`). Change it to route models to the view:

```javascript
            // existing: open detail on click
            if (file.role === 'model') {
                window.modelDetailView.open(file.checksum);
            } else {
                this.showFileDetail(file);
            }
```

Also, in the per-file card markup in `renderFiles`, add a small role badge when `file.role` is set, e.g. append to the card's meta line:

```javascript
            const roleBadge = file.role ? `<span class="role-badge role-${file.role}">${file.role}</span>` : '';
```

(Insert `${roleBadge}` into the existing card template near the filename/meta.)

- [ ] **Step 4: Add styles** (`frontend/css/components.css`, appended)

```css
.model-detail-header { display:flex; align-items:center; gap:16px; margin-bottom:20px; }
.model-detail-thumb { width:96px; height:96px; object-fit:contain; background:var(--surface-2,#f4f4f5); border-radius:8px; }
.model-detail-title h2 { margin:0; }
.model-detail-meta { color:var(--text-muted,#71717a); font-size:0.9rem; }
.model-detail section { margin-top:24px; }
.role-badge { font-size:0.7rem; padding:1px 6px; border-radius:10px; margin-left:6px; }
.role-badge.role-model { background:#dbeafe; color:#1e40af; }
.role-badge.role-printfile { background:#dcfce7; color:#166534; }
.md-table { width:100%; border-collapse:collapse; }
.md-table th, .md-table td { text-align:left; padding:8px; border-bottom:1px solid var(--border,#e4e4e7); font-size:0.9rem; }
.md-progress { height:8px; background:#e4e4e7; border-radius:4px; overflow:hidden; margin-top:8px; }
.md-progress > div { height:100%; background:#16a34a; width:0; transition:width .3s; }
```

- [ ] **Step 5: Browser verification**

Start the app (`webapp-testing` skill / project run) with a library containing at least one `role='model'` file. Navigate to `#library`, click the model card. Verify: the grid hides, the detail view shows the header (name, thumbnail, meta) and empty "Print files" / "Slice" sections, and the **← Library** button restores the grid. Capture a screenshot.

- [ ] **Step 6: Commit**

```bash
git add frontend/js/model-detail.js frontend/index.html frontend/js/library.js frontend/css/components.css
git commit -m "feat: model detail view scaffold + routing + header

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Print-files table (list + download + print)

**Files:**
- Modify: `frontend/js/model-detail.js` (`refreshPrintfiles`, download, print)

**Interfaces:**
- Consumes: `GET /library/files/{checksum}/printfiles`, `GET /library/files/{checksum}/download`, `POST /library/files/{checksum}/print`, `GET /printers`.

- [ ] **Step 1: Implement `refreshPrintfiles` + actions** (replace the stub)

```javascript
    async _printers() {
        if (this._printerCache) return this._printerCache;
        try {
            const r = await fetch(`${CONFIG.API_BASE_URL}/printers`);
            const d = await r.json();
            this._printerCache = d.printers || d || [];
        } catch (e) { this._printerCache = []; }
        return this._printerCache;
    }

    async refreshPrintfiles() {
        const host = document.getElementById('mdPrintfiles');
        if (!host) return;
        host.innerHTML = '<div class="loading">Loading…</div>';
        let printfiles = [];
        try {
            const r = await fetch(`${CONFIG.API_BASE_URL}/library/files/${this.checksum}/printfiles`);
            printfiles = (await r.json()).printfiles || [];
        } catch (e) { /* fallthrough to empty */ }
        if (!printfiles.length) {
            host.innerHTML = '<div class="empty">No print files yet. Slice this model below.</div>';
            return;
        }
        const printers = await this._printers();
        const rows = printfiles.map(p => {
            const t = p.estimated_print_time ? `${Math.round(p.estimated_print_time/60)} min` : '—';
            const fil = p.filament_used ? `${Number(p.filament_used).toFixed(1)} g` : '—';
            const pr = (printers.length)
                ? `<select class="md-printer">${printers.map(x => `<option value="${x.id}">${x.name}</option>`).join('')}</select>` : '';
            return `<tr data-cs="${p.checksum}">
              <td>${p.target_printer_id || '—'}</td><td>${p.profile_id || '—'}</td>
              <td>${t}</td><td>${fil}</td>
              <td><button class="btn btn-sm" data-dl="${p.checksum}">Download</button>
                  ${pr} <button class="btn btn-sm" data-print="${p.checksum}">Print</button></td></tr>`;
        }).join('');
        host.innerHTML = `<table class="md-table"><thead><tr><th>Printer</th><th>Profile</th><th>Time</th><th>Filament</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table>`;
        host.querySelectorAll('[data-dl]').forEach(b => b.addEventListener('click', () => {
            window.open(`${CONFIG.API_BASE_URL}/library/files/${b.dataset.dl}/download`, '_blank');
        }));
        host.querySelectorAll('[data-print]').forEach(b => b.addEventListener('click', async () => {
            const tr = b.closest('tr');
            const sel = tr.querySelector('.md-printer');
            const printerId = sel ? sel.value : null;
            if (!printerId) { showToast('error', 'Print', 'No printer available'); return; }
            try {
                const r = await fetch(`${CONFIG.API_BASE_URL}/library/files/${b.dataset.print}/print`, {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({printer_id: printerId})});
                if (!r.ok) throw new Error((await r.json()).detail || 'failed');
                showToast('success', 'Print', 'Sent to printer');
            } catch (e) { showToast('error', 'Print', e.message); }
        }));
    }
```

- [ ] **Step 2: Browser verification**

With a model that has ≥1 print file (slice one first, or seed), open the model view → the Print files table lists rows with Time/Filament; **Download** opens the file; **Print** (with a printer present) POSTs and shows a success toast. Screenshot the table.

- [ ] **Step 3: Commit**

```bash
git add frontend/js/model-detail.js
git commit -m "feat: model detail print-files table with download and print

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Slice panel + inline progress

**Files:**
- Modify: `frontend/js/model-detail.js` (`renderSlicePanel`, slice + poll)

**Interfaces:**
- Consumes: `GET /slicing`, `GET /slicing/{slicer_id}/profiles`, `POST /slicing/library/{checksum}/slice`, `POST /slicing/slice-and-print`, `GET /slicing/jobs/{id}`.

- [ ] **Step 1: Implement `renderSlicePanel` + slicing** (replace the stub)

```javascript
    async renderSlicePanel() {
        const host = document.getElementById('mdSlice');
        if (!host) return;
        // find a slicer + its profiles
        let slicer = null, profiles = [];
        try {
            const sl = await (await fetch(`${CONFIG.API_BASE_URL}/slicing`)).json();
            const slicers = sl.slicers || [];
            slicer = slicers.find(s => s.is_available) || slicers[0];
            if (slicer) {
                const pf = await (await fetch(`${CONFIG.API_BASE_URL}/slicing/${slicer.id}/profiles`)).json();
                profiles = pf.profiles || [];
            }
        } catch (e) { /* none */ }
        if (!slicer || !profiles.length) {
            host.innerHTML = '<div class="empty">No slicer/profile available. Add one in slicer settings.</div>';
            return;
        }
        this._slicerId = slicer.id;
        const printers = await this._printers();
        host.innerHTML = `
          <div class="md-slice-form">
            <label>Profile <select id="mdProfile">${profiles.map(p => `<option value="${p.id}">${p.profile_name}</option>`).join('')}</select></label>
            <label>Printer <select id="mdSlicePrinter"><option value="">— none —</option>${printers.map(x => `<option value="${x.id}">${x.name}</option>`).join('')}</select></label>
            <button class="btn btn-primary" id="mdSliceBtn">Slice</button>
            <button class="btn" id="mdSlicePrintBtn">Slice &amp; Print</button>
          </div>
          <div id="mdSliceStatus"></div>`;
        host.querySelector('#mdSliceBtn').addEventListener('click', () => this._slice(false));
        host.querySelector('#mdSlicePrintBtn').addEventListener('click', () => this._slice(true));
    }

    async _slice(andPrint) {
        const profileId = document.getElementById('mdProfile').value;
        const printerId = document.getElementById('mdSlicePrinter').value;
        if (andPrint && !printerId) { showToast('error', 'Slice', 'Pick a printer for Slice & Print'); return; }
        const status = document.getElementById('mdSliceStatus');
        status.innerHTML = '<div class="md-progress"><div></div></div><div class="md-status">Queued…</div>';
        try {
            let job;
            if (andPrint) {
                const r = await fetch(`${CONFIG.API_BASE_URL}/slicing/slice-and-print`, {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file_checksum: this.checksum, slicer_id: this._slicerId,
                        profile_id: profileId, printer_id: printerId, auto_start: true})});
                job = await r.json();
            } else {
                const body = {file_checksum: this.checksum, slicer_id: this._slicerId, profile_id: profileId};
                if (printerId) body.target_printer_id = printerId;
                const r = await fetch(`${CONFIG.API_BASE_URL}/slicing/library/${this.checksum}/slice`, {
                    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
                job = await r.json();
            }
            if (!job.id) throw new Error(job.detail || 'slice failed to start');
            this._pollJob(job.id);
        } catch (e) {
            status.innerHTML = `<div class="error">${e.message}</div>`;
        }
    }

    _pollJob(jobId) {
        if (this._poll) clearInterval(this._poll);
        const status = document.getElementById('mdSliceStatus');
        this._poll = setInterval(async () => {
            try {
                const j = await (await fetch(`${CONFIG.API_BASE_URL}/slicing/jobs/${jobId}`)).json();
                const bar = status.querySelector('.md-progress > div');
                if (bar) bar.style.width = `${j.progress || 0}%`;
                const lbl = status.querySelector('.md-status');
                if (lbl) lbl.textContent = `${j.status} (${j.progress || 0}%)`;
                if (j.status === 'completed') {
                    clearInterval(this._poll); this._poll = null;
                    showToast('success', 'Slice', 'Slicing complete');
                    status.innerHTML = '';
                    await this.refreshPrintfiles();
                } else if (j.status === 'failed') {
                    clearInterval(this._poll); this._poll = null;
                    status.innerHTML = `<div class="error">${j.error_message || 'Slicing failed'}</div>`;
                }
            } catch (e) { /* keep polling */ }
        }, 1500);
    }
```

- [ ] **Step 2: Browser verification (end-to-end)**

With the slicer service running and a built-in profile present (Phase 2), open a model → the Slice panel shows the profile + printer selects → click **Slice** → the progress bar advances and on completion a new print file appears in the table. Try **Slice & Print** with a (mock/real) printer. Screenshot the progress + the resulting table.

- [ ] **Step 3: Commit**

```bash
git add frontend/js/model-detail.js
git commit -m "feat: model detail slice panel with inline progress

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: Verification + PR

- [ ] **Step 1: Backend tests**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_library_download_print.py -p no:cacheprovider --timeout=60 -q`
Expected: 4 passed.

- [ ] **Step 2: Full services dir (no regressions / collection errors)**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/ -p no:cacheprovider --timeout=120 -q`
Expected: only the 4 pre-existing `test_printer_service.py` failures; everything else green.

- [ ] **Step 3: Browser walkthrough (recorded)**

Using the `webapp-testing` skill: model list → open model → see print files → slice (progress → new printfile) → download → print. Capture screenshots of the detail view and a completed slice.

- [ ] **Step 4: Push + PR**

```bash
git push -u origin feature/slicer-phase3b-ui
gh pr create --base master --title "feat: Slicer Phase 3b — model-centric detail view" --body "Frontend finale of the slicer epic + 2 small endpoints. See docs/superpowers/specs/2026-06-27-slicer-phase3b-ui-design.md."
```

---

## Verification (end-to-end)
1. `pytest tests/services/test_library_download_print.py` → 4 passed; full `tests/services/` green except the 4 pre-existing printer failures.
2. Browser: open a model → print files render with time/filament; slice → progress → new print file appears; Download serves bytes; Print sends to a printer.
3. Role badges appear in the library list; non-model files still open the existing modal.

## Self-review notes
- Spec coverage: download endpoint (T1), print-existing endpoint (T2), view scaffold + routing + header (T3), print-files table + download/print actions (T4), slice panel + inline progress (T5), verification + PR (T6). All present.
- Frontend tasks are browser-verified (no JS unit framework) — each has an explicit Playwright/manual verification step rather than a unit test.
- Risks the executor should watch: the exact shape of `GET /printers` (`{printers:[...]}` vs a bare list — the code handles both) and `GET /slicing` (`{slicers:[...]}`); the exact file-card click handler location in `library.js` (search for `showFileDetail(` and route there). Confirm against the real files at implementation time.
