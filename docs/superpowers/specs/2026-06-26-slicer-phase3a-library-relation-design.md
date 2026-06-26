# Slicer Phase 3a — Library model→printfile relation + API (Design)

## Context

Phases 1–2 made slicing work in-container (standalone OrcaSlicer microservice +
pluggable backends) and added curated + uploadable profiles. But the library still
treats every file as a flat blob: there is no notion that a sliced `.gcode` came
*from* a particular STL, and slice outputs aren't even added to the library. The
original slicer brainstorm reserved this for Phase 3 — "register the sliced output
as a library printfile linked to its source model, plus a model-centric view."

Phase 3 is split: **3a (this spec) is backend only** — the data relation and API.
The vanilla-JS **model-centric UI is 3b** (separate spec/plan/PR).

### Decisions (from brainstorming, 2026-06-26)
- Sequence: **3a backend first**, 3b frontend after.
- Classification covers **new + sliced outputs AND a one-time backfill** of existing
  `library_files` rows.
- (3b will target the existing vanilla-JS app, not React — out of scope here.)

### Current state (master)
- `library_files` has `checksum` (UNIQUE), `file_type`, `library_path`, `metadata`
  (JSON), thumbnail + rich print-metadata columns. **No `role`/`parent_checksum`.**
- `LibraryService.add_file_to_library(source_path, source_info, …)` is the ingest
  entry point (checksum dedup, copy into library, metadata/thumbnail extraction).
  `get_file_by_checksum`, `list_files(filters)` exist.
- `slicing_jobs` already links `file_checksum` (source model) → `output_file_path`
  / `output_gcode_checksum`. **But `SlicingQueue` does not register the output in
  the library** (Phase 1 deferred it), and `output_gcode_checksum` is never set.
- `ThreeMFAnalyzer` (`src/services/threemf_analyzer.py`) can inspect a `.3mf`.
- Library router (`src/api/routers/library.py`): `GET /files`, `GET /files/{checksum}`,
  `/reprocess`, `/metadata`, `/reanalyze-all`, etc. **No printfiles sub-resource.**

## Data model

**Migration `036_library_file_roles.sql`** — append to `library_files`:
```sql
ALTER TABLE library_files ADD COLUMN role TEXT;            -- 'model' | 'printfile' | NULL (unclassified)
ALTER TABLE library_files ADD COLUMN parent_checksum TEXT; -- source model's checksum, for a printfile
CREATE INDEX IF NOT EXISTS idx_library_files_role ON library_files(role);
CREATE INDEX IF NOT EXISTS idx_library_files_parent ON library_files(parent_checksum);
```
`role` is nullable so existing rows are "unclassified" until the backfill runs.
The relation's source of truth is `parent_checksum` on the printfile row;
`slicing_jobs` supplies the "how it was sliced" detail.

## Role classifier (`src/services/file_role_classifier.py`)

```python
def classify_role(file_type: str, threemf_has_gcode: Optional[bool] = None) -> Optional[str]:
    ...
```
- Normalize `file_type` (strip leading `.`, lowercase).
- `gcode`, `gco`, `g`, `bgcode` → `"printfile"`.
- `stl`, `step`, `stp`, `obj` → `"model"`.
- `3mf` → `"printfile"` if `threemf_has_gcode` is True, `"model"` if False/None.
- anything else → `None` (leave unclassified; never raise).

Pure and table-testable. The **caller** decides `threemf_has_gcode` for `.3mf`
files using `ThreeMFAnalyzer` (embedded gcode/plate ⇒ True). On analyzer failure,
the caller passes `None` (→ classified as `model`).

## Wiring

### Ingest (`add_file_to_library`)
- Add explicit optional kwargs `role: Optional[str] = None`,
  `parent_checksum: Optional[str] = None`. If `role` is not passed, classify from
  `file_type` (running the 3mf check for `.3mf`). Persist both columns on insert.
  The method's checksum (its existing return value / the computed checksum) is what
  callers use to set up the relation.

### One-time backfill (`LibraryService.classify_unroled_files()`)
- Called from `LibraryService.initialize()`. Selects rows `WHERE role IS NULL`,
  classifies each (by `file_type`, with the 3mf analyzer where applicable), and
  `UPDATE`s `role`. Idempotent — only touches NULLs; a row that classifies to
  `None` stays NULL (re-evaluated on next run, cheap). Logs a one-line summary.

### Slice-output registration (`SlicingQueue`)
On a successful slice, after the job row is updated:
1. `checksum = await library_service.add_file_to_library(Path(output_path),
   {"source_type": "slicer", "source_id": job.slicer_id}, role="printfile",
   parent_checksum=job.file_checksum)` (metadata/thumbnail extraction happens
   inside `add_file_to_library` as for any file).
2. `UPDATE slicing_jobs SET output_gcode_checksum = ? WHERE id = ?`.
3. Wrap in try/except: a registration failure is **logged, not fatal** — the gcode
   already exists on disk and (if `auto_upload`) was sent to the printer.

### Query (`LibraryService.get_printfiles_for_model(model_checksum)`)
- Returns the derived printfiles: `library_files` rows `WHERE parent_checksum =
  model_checksum AND role = 'printfile'`, each enriched with its `slicing_jobs`
  row (matched on `output_gcode_checksum = library_files.checksum`) to add
  `profile_id`/`target_printer_id`/`estimated_print_time`/`filament_used`/`created_at`.
  Printfiles with no matching job (e.g. imported) still appear, with job fields null.

## API

**`GET /api/v1/library/files/{checksum}/printfiles`** → `{ "printfiles": [...], "count": n }`.
Returns `get_printfiles_for_model(checksum)`. 404 if the model checksum is unknown.
(The model itself is the existing `GET /files/{checksum}`; "slice from model" reuses
the existing `POST /api/v1/slicing/jobs`.)

## Components & boundaries
- `src/services/file_role_classifier.py` (NEW) — pure `classify_role`.
- `migrations/036_library_file_roles.sql` (NEW).
- `src/services/library_service.py` (MODIFY) — `role`/`parent_checksum` on insert;
  `classify_unroled_files()`; `get_printfiles_for_model()`; a small 3mf helper.
- `src/services/slicing_queue.py` (MODIFY) — register output + set
  `output_gcode_checksum` (guarded).
- `src/api/routers/library.py` (MODIFY) — printfiles sub-resource.

## Error handling
- Classifier never raises; unknown types → `None`.
- 3mf analysis failure → treat as `model` (caller passes `None`).
- Slice-output registration failure → log + continue (job stays completed).
- Backfill failure on one row → log + skip, continue with the rest.

## Testing
- **Classifier:** table test over stl/step/obj/gcode/bgcode/g + 3mf (gcode True/False/None) + unknown → None.
- **Ingest:** `add_file_to_library` persists an explicitly-passed `role`/`parent_checksum`; classifies when not passed.
- **Backfill:** seed rows with `role` NULL of mixed types → `classify_unroled_files()` sets the right roles and leaves already-set roles untouched.
- **Query:** seed a model + two printfiles (one with a matching slicing_job, one without) → `get_printfiles_for_model` returns both, job fields populated only where matched.
- **Slice registration:** on slice completion the output is registered with
  `role='printfile'` + `parent_checksum`, and `slicing_jobs.output_gcode_checksum`
  is set; a thrown registration error leaves the job `completed` (not failed).
- **API:** `GET /files/{checksum}/printfiles` returns the list; 404 for unknown checksum.

## Out of scope (3b / later)
- The vanilla-JS model-centric detail view + Slice/Re-slice/Upload+Print/Download actions.
- Re-deriving thumbnails specifically for gcode previews (handled by existing extraction).
- Cascading delete semantics between a model and its printfiles (kept simple: deletes are independent in 3a).
