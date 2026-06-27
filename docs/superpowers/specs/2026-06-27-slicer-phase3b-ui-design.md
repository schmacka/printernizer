# Slicer Phase 3b — Model-centric detail view (Design)

## Context

Phases 1–3a built the whole slicing backend: in-container OrcaSlicer, pluggable
backends, curated + uploadable profiles, and a library model→printfile relation
with a `GET /files/{checksum}/printfiles` API. **None of it is visible in the UI.**
Phase 3b is the finale: a model-centric detail view that surfaces a model's derived
print files and lets the user slice, re-slice, print, and download — making the
prior three phases usable.

### Decisions (brainstorming, 2026-06-27)
- **Actions:** full set — Slice / Re-slice / Slice & Print (already backed) **plus
  Download and Print-existing-printfile**, which need two small backend endpoints.
- **Progress:** inline in the view, by polling `GET /slicing/jobs/{id}`.
- **UI:** a **dedicated model-detail view** (not the existing modal).

### Current state (master)
- Frontend is a **hash-routed SPA in `frontend/index.html`** (nav uses
  `href="#library"`, `data-page="library"`). The library page is driven by
  `frontend/js/library.js` (`LibraryManager`, ~1600 lines), which already has a
  file-detail **modal** (`showFileDetail` → `renderFileDetail`).
- Slicing API: `GET /api/v1/slicing` (list slicers), `GET /slicing/{slicer_id}/profiles`,
  `POST /slicing/library/{checksum}/slice` (slice a library file → SlicingJobResponse),
  `POST /slicing/slice-and-print`, `GET /slicing/jobs/{id}` (status/progress).
- Library API: `GET /library/files`, `GET /library/files/{checksum}`,
  `GET /library/files/{checksum}/printfiles` (Phase 3a). **No download endpoint.**
- Printers: `printer_service.upload_file_to_printer(printer_id, local_path, remote_name)`
  and driver `start_print(filename)` exist. **No "print an existing library file" endpoint.**

## Backend additions (small)

### `GET /api/v1/library/files/{checksum}/download`
Stream the library file's bytes. Resolve the row via `get_file_by_checksum`; the
on-disk path is `library_service.library_path / row['library_path']`. Return a
`FileResponse` with the original `filename`. 404 if the checksum or file is missing.

### `POST /api/v1/library/files/{checksum}/print`
Body: `{ "printer_id": str }`. Print an already-sliced library printfile:
1. Resolve the library file; 404 if missing.
2. 400 if the file is not a printable type (`role != 'printfile'` and extension not
   in gcode/bgcode/3mf) — guard against trying to "print" an STL.
3. `await printer_service.upload_file_to_printer(printer_id, abs_path, filename)`,
   then start the print on the driver (`get_printer_instance(printer_id).start_print(filename)`).
4. Return `{ "status": "started", "filename": ... }`; map failures to a 502/400 with
   a clear message.

Both live in `src/api/routers/library.py` (file-scoped) and delegate to the
services; the print endpoint depends on `printer_service` (added via the router's
existing dependency wiring).

## Frontend: the model-detail view

A new module **`frontend/js/model-detail.js`** (`ModelDetailView`) renders a
dedicated detail view inside the library page area. `library.js` routes a click on
a `role='model'` file to it (other files keep the existing modal). **Default
navigation: a view-swap within the `#library` page** — the view hides the library
list/grid and shows the detail container, with a Back-to-library control that
restores the list. (A real `#library/<checksum>` hash route is optional polish and
not required for 3b — chosen to avoid surgery on the SPA router.)

**Layout (top → bottom):**
- **Header**: thumbnail (existing `/library/files/{checksum}/thumbnail`), display
  name, key metadata (dimensions, file size, object count), and a Back-to-library button.
- **Print files** section: a table from `GET /library/files/{checksum}/printfiles`.
  Columns: *target printer · profile · est. print time · filament · created*. Per-row
  actions: **Download** (→ the download endpoint) and **Print** (a printer picker →
  the print endpoint). Empty-state message when there are none yet.
- **Slice** panel: a **profile** `<select>` (options from the registered slicer's
  profiles — fetch `GET /slicing` to find the slicer, then `GET /slicing/{id}/profiles`;
  show built-in and uploaded), an optional **target printer** `<select>`, and two
  buttons: **Slice** (`POST /slicing/library/{checksum}/slice` with slicer_id +
  profile_id) and **Slice & Print** (`POST /slicing/slice-and-print` with printer +
  auto_start). **Re-slice** is just running this panel again.
- **Progress**: after a job is created, poll `GET /slicing/jobs/{id}` (~1.5s) and
  show a progress bar + status; on `completed`, refresh the Print-files table (the
  new printfile appears) and clear the progress; on `failed`, show the error.

**Data flow:** the view fetches the model (`/library/files/{checksum}`), its
printfiles, the slicer + profiles, and the printer list (`/printers`) on open. All
calls use the existing `CONFIG.API_BASE_URL` + `fetch` pattern and the app's
error/toast helpers.

## Components & boundaries
- `src/api/routers/library.py` (MODIFY) — download + print endpoints.
- `frontend/js/model-detail.js` (NEW) — `ModelDetailView` (open/close, render header,
  render printfiles, render slice panel, slice + poll, download, print).
- `frontend/js/library.js` (MODIFY) — route `role='model'` clicks to the view; small
  role badge in the list.
- `frontend/index.html` (MODIFY) — a `#model-detail` container + the new script tag.
- `frontend/css/*` (MODIFY) — styles for the view (reuse existing card/table classes
  where possible).

## Error handling
- Download/print endpoints: 404 missing file, 400 wrong type, 502/clear message on
  printer failure — using the project's standard error envelope.
- Frontend: failed fetches show the app's error toast; a failed slice surfaces the
  job's `error`; printer-less environments disable the Print / Slice & Print controls.

## Testing
- **Backend (pytest):** download returns the bytes + correct filename and 404s on a
  missing checksum; print calls `upload_file_to_printer` + `start_print` (mocked
  printer service), 400s on a non-printable file, 404s on a missing one.
- **Frontend (browser via the `webapp-testing`/Playwright skill):** open a seeded
  model → its printfiles render; run a slice → progress shows and the new printfile
  appears; Download triggers a file response; Print calls the endpoint. Capture a
  screenshot of the view for confirmation.

## Out of scope
- Editing/duplicating profiles from this view (Phase 2 covers creation/upload).
- Bulk actions across multiple models.
- A standalone `model.html` page (the view lives in the SPA's library area).
- Cascade delete between a model and its printfiles (kept independent, per 3a).
