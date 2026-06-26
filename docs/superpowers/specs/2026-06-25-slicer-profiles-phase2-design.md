# Slicer Profiles (Phase 2) — Design

## Context

Phase 1 shipped in-container slicing via a standalone OrcaSlicer microservice and
pluggable backends (`RemoteHTTPBackend` / `LocalProcessBackend`). Slicing works,
but choosing *how* to slice is still crude: there is no curated set of ready-to-use
profiles and no way for a user to bring their own. Phase 1 deliberately deferred
this ("Richer profile UX is intentionally deferred to Phase 2").

This phase makes profiles usable:
1. **Curated/built-in profiles** so a user can slice for their printer with zero
   configuration.
2. **Upload** so a user can bring an exported OrcaSlicer profile the bundled set
   doesn't cover.

**Key enabling fact:** the OrcaSlicer image already bundles system presets for
*both* tested printers — Bambu **A1** and Prusa **CORE One** (verified in the
image at `resources/profiles/{BBL,Prusa}/{machine,process,filament}`). So the
curated bundle needs **no hand-authored profile files** — it references what
OrcaSlicer already ships.

### Decisions (from brainstorming, 2026-06-25)
- **Curated source:** expose + seed from OrcaSlicer's bundled presets (no
  hand-authored files).
- **Upload handling:** the slicer-service stays **stateless** — the app stores
  uploaded profiles and sends their content with each slice request.
- **Upload formats:** OrcaSlicer preset **JSON** only (PrusaSlicer `.ini` deferred).
- **Scope:** backend + API only; the profile-selection UI lands in Phase 3's
  model-centric view.

### Current state (origin/master)
- Profile API exists: `GET /{slicer_id}/profiles`, `POST /{slicer_id}/profiles/import`,
  `GET /profiles/{id}`, `DELETE /profiles/{id}` (`src/api/routers/slicing.py`).
  **No upload endpoint.**
- `slicer_profiles` columns: `id, slicer_id, profile_name, profile_type,
  profile_path, settings_json, compatible_printers, is_default`. **No
  `source`/`printer_model`/`is_builtin`.**
- The slicer-service (`slicer-service/app/main.py`) exposes `/health`, `/version`,
  `/slice`, `/slice/{id}`, `/slice/{id}/result`. **No `/profiles`**, and `/slice`
  only resolves *bundled preset names*, not uploaded content.

## Profile payload contract (the central abstraction)

A profile's `settings_json` **is** the payload the app sends the slicer-service.
Two shapes, both understood by the service's `/slice`:

- **Built-in** (references bundled presets by name):
  ```json
  {"system_preset": {"machine": "Bambu Lab A1 0.4 nozzle",
                     "process": "0.20mm Standard @BBL A1",
                     "filament": "Bambu PLA Basic @BBL A1"}}
  ```
- **Upload** (full preset JSON inline):
  ```json
  {"inline": {"machine": { …OrcaSlicer machine preset… },
              "process": { …process preset… },
              "filament": { …filament preset… }}}
  ```

`RemoteHTTPBackend._profile_payload` already forwards `settings_json` verbatim, so
no backend change is needed beyond the service learning the `inline` shape.

## Slicer-service changes (stateless)

### `GET /profiles`
Walk `ORCA_PROFILES_ROOT`; return bundled presets grouped by vendor:
```json
{"vendors": {"BBL": {"machine": ["Bambu Lab A1 0.4 nozzle", …],
                     "process": ["0.20mm Standard @BBL A1", …],
                     "filament": ["Bambu PLA Basic @BBL A1", …]},
             "Prusa": { … }}}
```
Used by the app's seeder (to validate curated names) and for discovery. Pure
filesystem read; no slicing.

### `/slice` accepts `inline`
The runner resolves a profile payload to three on-disk JSON paths:
- `system_preset`: resolve names against `ORCA_PROFILES_ROOT` (existing behaviour).
- `inline`: write each provided preset object to a temp `.json` in the job
  workdir and use those paths.
Then build `--load-settings "<process>;<machine>" --load-filaments "<filament>"`
as today. Missing required parts → fail with a clear error.

**Caveat (documented, not solved in v1):** an uploaded preset whose `"inherits"`
names a *system* preset present in the image resolves correctly; a preset that
inherits from a *user* preset not in the image will fail to slice. Phase 2 does
not flatten inheritance.

## App changes

### Migration `035_slicer_profile_metadata.sql`
Append to `slicer_profiles` (column order matters for positional row mappers):
```sql
ALTER TABLE slicer_profiles ADD COLUMN source TEXT NOT NULL DEFAULT 'import';
ALTER TABLE slicer_profiles ADD COLUMN printer_model TEXT;
ALTER TABLE slicer_profiles ADD COLUMN is_builtin INTEGER NOT NULL DEFAULT 0;
```
`SlicerProfile` model gains `source: str = "import"`, `printer_model: Optional[str]`,
`is_builtin: bool = False`; `_row_to_profile` reads the appended indices with a
length guard (same pattern as Phase 1's `slicer_configs` mapper).

### Built-in profile seeder
A small `SlicerProfileSeeder` (or a method on `SlicerService`), invoked from
`SlicerService.initialize` **after** `register_remote_slicer_from_env`, for the
remote slicer only. Idempotent: skip a built-in whose `(slicer_id, profile_name)`
already exists.

Curated set (one process/quality default per printer; extensible later):
| Printer | machine | process | filament |
|---|---|---|---|
| Bambu A1 | `Bambu Lab A1 0.4 nozzle` | `0.20mm Standard @BBL A1` | `Bambu PLA Basic @BBL A1` |
| Prusa CORE One | `Prusa CORE One 0.4 nozzle` | `0.20mm SPEED @CORE One 0.4` | `Prusa Generic PLA @CORE One` |

Each seeded row: `source='builtin'`, `is_builtin=1`, `printer_model` set,
`profile_type='bundle'`, `settings_json = {"system_preset": {machine,process,filament}}`.
**Resilience:** the seeder fetches the service's `/profiles` and only seeds presets
whose names are present; a missing name is logged (warning) and skipped, never
fatal (OrcaSlicer may rename presets across versions). If the service is
unreachable, seeding is skipped and retried on next startup.

### `POST /api/v1/slicing/profiles/upload`
(Follow the trailing-slash rule: `@router.post("/profiles/upload")`.) Accepts one
or more OrcaSlicer preset JSON files plus a `name` (and optional `printer_model`).
Behaviour:
1. Parse each file as JSON; read its `"type"` field (`machine`/`process`/`filament`)
   to categorize; reject unknown/duplicate types.
2. Require all three parts (`machine`, `process`, `filament`) in the upload;
   reject with a 4xx if any are missing (v1 keeps a profile self-contained and
   immediately sliceable — no partial/not-ready state).
3. Assemble `settings_json = {"inline": {machine, process, filament}}`.
4. Parse metadata for display: `printer_model` (from preset `name`/compatible
   condition or the provided field), nozzle diameter, layer height.
5. Insert into `slicer_profiles` with `source='upload'`, `is_builtin=0`,
   `profile_type='bundle'`.

Validation errors return the project's standard error envelope.

## Components & boundaries
- `slicer-service/app/profiles.py` (new): `list_bundled_profiles(root) -> dict`
  (pure, testable) used by the `/profiles` route.
- `slicer-service/app/runner.py`: extend payload resolution to handle `inline`
  (a focused change to `_build_settings`).
- `src/services/slicer_profile_seeder.py` (new) or a `SlicerService` method:
  `seed_builtin_profiles()`.
- `src/services/slicer_service.py`: upload parsing/storage helper; model/mapper
  updates.
- `src/api/routers/slicing.py`: the upload endpoint.

## Error handling
- Upload: invalid JSON, unrecognized `type`, missing required parts → 4xx with a
  clear message; nothing stored on failure.
- Seeder: missing preset name → warn + skip; service unreachable → skip + retry
  next boot; never crashes startup.
- Service `/slice` inline: missing/invalid preset object → fail the job with a
  descriptive `error`.

## Testing
- **Service unit:** `list_bundled_profiles` against a stub profiles tree;
  `GET /profiles` shape; `/slice` with `inline` payload (stub runner writes temp
  files and asserts paths) and with `system_preset`.
- **App unit:** migration adds columns; `SlicerProfile`/mapper round-trip;
  `seed_builtin_profiles` is idempotent and skips missing names (mock `/profiles`);
  upload endpoint categorizes by `type`, assembles `inline`, parses metadata,
  rejects bad input.
- **E2E (real image, manual):** seed runs → built-in A1 + Core One profiles exist;
  upload a tweaked A1 process JSON → slice via the service → gcode produced with
  expected metadata.

## Out of scope (later phases)
- Profile-selection UI and model-centric slicing actions (Phase 3).
- PrusaSlicer `.ini` upload/conversion.
- Flattening user-preset inheritance chains.
- Multiple quality presets per printer / profile editing.
