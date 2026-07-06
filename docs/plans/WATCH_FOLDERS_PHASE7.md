# Watch Folders Enhancement (Phase 7)

**Status**: 7a / 7b / 7c complete — merged via PR #375, released as **v2.42.0**. 7d deferred.
**Last Updated**: 2026-07-05

This document records what shipped in Phase 7 and the concrete follow-up
work that was intentionally left out, so it can be picked up later without
re-deriving the context.

---

## What shipped

### 7a — Foundation (bug fixes + hardening)

Before this work the real-time half of watch folders never functioned.

- **Thread → event-loop bridge**: watchdog delivers events on its own
  observer thread, where the old code called `asyncio.create_task()` — no
  running loop, so every created/modified/deleted/moved event raised
  `RuntimeError` and was lost. Events are now scheduled onto the captured
  main loop via `asyncio.run_coroutine_threadsafe()`.
- **Write-stability check**: ingest waits until a file's size/mtime stop
  changing before processing, so a file still being copied is no longer
  stored truncated with a wrong checksum. An in-flight guard suppresses
  duplicate processing during event bursts.
- **Library reconciliation**: delete removes the watch-folder source from
  the library record, cross-folder moves swap the source, content changes
  refresh it (`LibraryService.remove_file_source`).
- **Deterministic file IDs** (sha1 of path) instead of Python's salted
  `hash()`, which changed every restart.
- `.bgcode` support, `POST /api/v1/files/watch-folders/rescan`, periodic
  fallback rescan when the observer can't start, and `file_count` /
  `last_scan_at` statistics maintained in the `watch_folders` table.

### 7b — Per-folder processing rules (migration 038)

- **Auto-tagging** from first-level subfolder (`vases/spiral.stl` → tag
  `vases`), via `LibraryService.assign_tag_by_name()`.
- **Business/private classification** tag on ingest.
- **Default printer / profile** stored per folder (consumed by 7c).
- Settings UI: per-folder cards with status, scan stats, rescan button,
  auto-tag toggle, classification select.

### 7c — Auto-slice workflow (migration 039)

- New model files ingested into an `auto_slice` folder with a default
  profile are automatically queued for slicing; the gcode registers in
  the library linked to its source model (Phase 3a relation).
- **Safety invariant — never auto-prints.** The queued job always has
  `auto_upload=False` and `auto_start=False`. There is a test asserting
  this (`test_auto_slice_queues_new_model_and_never_prints`); keep it.
- Fires only on the first ingest of new content (not rescans/duplicates);
  gcode / already-sliced files are skipped.
- New notification events `slicing_completed` / `slicing_failed`
  (subscribable per channel); slicing events enriched with filename,
  output file, profile, target printer.
- UI: auto-slice toggle + default profile/printer pickers on folder cards.

---

## Follow-up work

### 7d — External sources (deferred / stretch)

Goal: "save a Thingiverse/Printables URL → library", reusing the ingest
pipeline 7a–7c built.

- Reuse `url_parser_service` (already exists for the Ideas/trending
  features) for URL classification and metadata.
- Add a download step that fetches the model bytes to a temp path, then
  routes them through the same `LibraryService.add_file_to_library()` +
  `_apply_folder_rules()` path so tagging/classification/auto-slice all
  apply identically to a dropped file.
- Licensing metadata: capture and store the source license where the
  platform exposes it (Printables/Thingiverse APIs do). This is the main
  reason it was split out — it's a different problem shape (HTTP auth,
  rate limits, licensing) than local folder watching.
- Likely surfaces as a "Import from URL" action on the Library page, not
  a watch-folder concept — revisit whether it belongs under Phase 7 at
  all or as its own small feature.

### Release checklist for Phase 7 — done ✅

Released as **v2.42.0** (2026-07-05): `CHANGELOG.md` moved under the
`[2.42.0]` heading, `src/main.py` fallback bumped, tagged `v2.42.0`,
pushed. GitHub Actions handles the GitHub release + HA-repo sync.

**Migrations 038 and 039** apply cleanly on top of 031 and are guarded
by the migration runner's duplicate-column tolerance; `WatchFolder`'s
`from_db_row` also tolerates pre-migration rows (defaults for the new
columns). No manual DB steps required.

### Testing gaps to close later

- **No integration test exercises the full watchdog path** (drop a real
  file → observer fires → ingest → library). 7a is covered by unit tests
  that call the handlers directly; an end-to-end test with a real
  `Observer` would catch thread-bridge regressions the unit tests can't.
- **No notification-service test file exists at all** (`tests/services/`
  has none). The new `slicing_completed`/`slicing_failed` subscriptions
  are only covered indirectly. Worth adding a focused test that emits
  `slicing_job.completed` and asserts a dispatch.
- **Manual UI verification pending**: the folder-card auto-slice pickers
  were not exercised in a running browser (backend + JS syntax validated
  only). Verify the pickers populate and persist against a live slicer.

---

## Next epic — Advanced Home Assistant Integration (Phase 6)

Deliberately set up by 7c: the pipeline emits stable, well-named events
through `EventService`:

- `watch_folder.auto_slice_queued`
- `slicing_job.completed` / `slicing_job.failed` (enriched payloads)
- plus the existing `file_watcher` and job/printer events.

The HA epic can largely **republish these over MQTT** (discovery +
sensor entities + automation triggers) rather than inventing new event
semantics — e.g. "flash a light when a hot-folder file finishes slicing"
becomes a thin transport layer over events that already exist. Start
there rather than retrofitting event plumbing.
