# Printernizer Connect — PrusaSlicer 3.0 integration design

**Date:** 2026-09-06
**Status:** Approved design, pre-implementation
**Scope:** New repo `printernizer-connect` + server-side changes in `printernizer`

## 1. Summary

Printernizer Connect is a desktop companion for PrusaSlicer that links a slicing
machine to a remote Printernizer instance (Raspberry Pi / Home Assistant / Docker).
It provides three flows:

1. **Pull — library in the slicer.** The Printernizer library appears as a
   navigable tree in PrusaSlicer's *Plugins* menu. Clicking a model loads it onto
   the bed, optionally applies its proven print settings, and stamps the project
   with provenance metadata.
2. **Push — exports to Printernizer.** Every G-code export is uploaded to the
   Printernizer library with full slicer metadata via PrusaSlicer's
   post-processing hook.
3. **Profile sync.** User print/filament/printer profiles are pushed to and
   pulled from Printernizer with conflict detection.

The design is constrained by a verified fact: **PrusaSlicer 3.0's Lua plugin API
is sandboxed with no network, no general filesystem, no persistence, no events,
and no dropdown/enum dialog controls.** The Lua plugin therefore only ever reads
files the companion has generated inside its own bundle directory. All network
and filesystem work is done by the companion CLI, which PrusaSlicer's existing
hooks invoke.

### Goals

- A browse-and-load experience that feels native inside PrusaSlicer, using every
  capability the alpha11 plugin API actually exposes.
- Zero background processes on the slicing machine.
- Push and profile sync keep working when Prusa breaks the Lua API.
- Public, open-source, alpha-labelled; installable with `pipx`.

### Non-goals (v1)

- Live printer status inside the slicer (impossible in the sandbox).
- Thumbnails in the slicer (no image/UI API).
- Global authentication for Printernizer's existing API and frontend.
- A background daemon or tray app (may wrap the CLI later).
- Prusa plugin marketplace packaging/signing (later milestone).
- Support for slicers other than PrusaSlicer (the OctoPrint shim helps them
  incidentally).

### Decisions already taken

| Question | Decision |
|---|---|
| Directions | Push, pull, profile sync (no live status) |
| Topology | Printernizer on a separate box; companion on the slicing machine |
| Pull UX | In-slicer picker via the Lua plugin (menu tree), not a deep link |
| Architecture | CLI driven by PrusaSlicer hooks; no daemon |
| Language | Python 3.11+, `pipx` install |
| Audience | Public open-source, alpha-labelled |

## 2. PrusaSlicer 3.0 plugin API — verified facts (alpha11)

Sources: the unofficial API docs (jedisct1/prusaslicer-lua-plugins-api-doc),
community plugins and DEVINFO (leotrax3d/prusaslicer-plugins-unofficial),
Prusa's 3.0 preview post. Everything below was checked on 2026-09-06; the API is
explicitly experimental and expected to break between alphas.

**Bundle model.** A plugin is a directory under `<datadir>/lua/<bundle-id>/`
containing `manifest.json` (id, name, version, min_slicer_version, author,
license, required_apis; optional description, category, web, repo) plus any
number of `.lua` command files, helper modules and assets. Directory-copy
installation needs no signature; ZIP import does. Filenames are restricted to
`[A-Za-z0-9.-_ ]`.

**Command file.** A file registers a command if it defines a global `info`
table and `execute(opts)` function. `info` = `{id, type="project.plugin",
title, menu, params}`. `menu` is a `/`-separated path of arbitrary depth under
the Plugins menu; identical paths across bundles get a bundle-id suffix.
`title` is the dialog heading. `params` entries are `{name, label, type,
default}` with `type` ∈ `string | float | int | bool` — **exactly four; no enum,
list, tooltip or conditional field** (checked against `PluginDialog.cpp`). The
dialog is shown even with zero params. `execute`'s return value is ignored.

**Two environments.** During scanning every `.lua` file is evaluated in a bare
state with **no `api` and no `require`** — file level may only declare `info`,
functions and constants. On Run, a **fresh Lua state** is created, `api` and a
restricted `require` are registered, and the entry script is re-evaluated. Nothing
survives between runs. `require("x")` resolves `x.lua` relative to the
entry script directory (forward slash would mean a subdirectory; dots are literal).
Prusa's own plugins use bare flat names.

**Discovery.** Bundles are scanned at startup; `Plugins ▸ Rescan Plugins`
rescans without restart (one source says restart — spike item S2). Execution code
is re-read on every Run, so changing an asset or module needs no rescan; adding or
removing command files or changing `info` does.

**API surface used by this design.**

| Call | Notes |
|---|---|
| `api.load_stl(path)` → Mesh | STL only. Path inside the entry directory; parent traversal, absolute paths and symlinks resolving outside are rejected. **Flat filenames at bundle root are the proven pattern** — Prusa's own `temp_tower.lua` calls `api.load_stl("temp_tower-base.stl")`. Subdirectories unverified and not used by this design. |
| `api.project:add_object{mesh, translate?, rotate?, object_params?, other_volumes?}` | Object is auto-centred on the selected bed in X/Y. No naming, no return of a usable handle, no scene listing. |
| `add_object{… params=, object_params=}` / `bed:print_presets():set(key, value)` | Writes numbers, percentages (`"15%"`), number-or-percent and enum strings (`brim_type="outer_only"`) — all confirmed in Prusa's own `flow_tower.lua`/`temp_tower.lua`. Plain booleans/strings are not writable. Unknown keys fail silently. Changes are project-scoped, not saved to presets. Prusa's code uses **both** `params` and `object_params` on `add_object`; which one applies is spike S3. |
| `bed:printer_presets():value(key)`, `bed:printer_config().tools[1]:nozzle_diameter()` | Read active printer preset values and nozzle. |
| `api.project:insert_layer_custom_gcode(bed, z_mm, gcode)` | Appends a custom G-code entry at a height; emitted in exported G-code and saved in the project 3MF. |
| `print(...)` | Goes to process stdout only; no in-app console. `execute` errors are logged, never shown to the user. |

**Not available:** network, `io`/`os`, persistence, events/hooks (no
post-slice), message boxes, custom UI, scene inspection, mesh geometry read-back,
G-code post-processing from Lua.

## 3. Architecture

Two repositories, one HTTP boundary, no background process.

```
┌──────────────── slicing machine ─────────────────┐      ┌──── Printernizer box ────┐
│ PrusaSlicer 3.0                                   │      │ printernizer (FastAPI)   │
│  ├─ Plugins ▸ Printernizer ▸ … (generated bundle) │      │  /api/v1/connect/*  (new)│
│  │     printernizer_lib.lua  ← reads only bundle  │      │  /api/v1/library/*       │
│  └─ post_process ──► printernizer-connect hook ───┼─HTTP─┤  /api/v1/slicing/*  (+2) │
│                                                   │      │  /printhost/* (optional) │
│ printernizer-connect CLI (Python, no daemon)      │      │  API keys           (new)│
│   setup · doctor · sync · hook · profiles         │      └──────────────────────────┘
└───────────────────────────────────────────────────┘
```

**Boundaries.**

1. **The Lua plugin knows nothing about Printernizer.** It reads generated command
   files and assets in its own bundle. It never sees a hostname or key. A breaking
   Lua API change touches `printernizer_lib.lua` and one template; push and profile
   sync are unaffected.
2. **`client.py` is the only module that speaks HTTP.** Every other module takes a
   client object, so the whole tool is testable against a fake transport.
3. **`prusaslicer/` is the only package that touches PrusaSlicer's files** — datadir
   discovery, `.ini` parsing/writing, the plugin folder. All per-OS and per-version
   ugliness lives behind that seam.
4. **The hook is deliberately dumb.** It runs inside PrusaSlicer's export on every
   export; it reads env, streams one file, logs, exits 0.

## 4. `printernizer-connect` — the companion

### 4.1 Repository layout

```
printernizer-connect/
├── pyproject.toml                    # console_script: printernizer-connect
├── src/printernizer_connect/
│   ├── cli.py                        # typer/click: setup doctor sync hook profiles
│   ├── client.py                     # httpx client: typed calls, auth, streaming upload
│   ├── config.py                     # config.toml + state.json (platformdirs)
│   ├── prusaslicer/
│   │   ├── paths.py                  # datadir + lua dir discovery per OS / 3.0 alpha names
│   │   ├── ini.py                    # PrusaSlicer .ini read/write, list-valued keys
│   │   ├── profiles.py               # user profile enumeration (print/filament/printer)
│   │   └── physical_printers.py      # physical_printer/*.ini (shim milestone)
│   ├── bundle/
│   │   ├── generator.py              # library entries → command files + manifest; atomic swap
│   │   ├── scope.py                  # selection: tags, recent N, size budget, grouping
│   │   └── convert.py                # 3MF/OBJ → STL per object (trimesh)
│   └── hooks/
│       └── postprocess.py            # `hook` implementation
├── bundle_template/
│   ├── manifest.json                 # id com.printernizer.library
│   ├── printernizer_lib.lua          # the only hand-written Lua logic
│   ├── tag_project.lua               # static command
│   └── model_command.lua.j2          # per-model command template
└── tests/  (see §10)
```

### 4.2 CLI surface

| Command | Purpose |
|---|---|
| `setup [--server URL] [--api-key KEY] [--datadir PATH] [--profiles all\|NAME…]` | Interactive first run: validate server, store config, locate PrusaSlicer datadir, install bundle skeleton, enable hook in print profiles. Idempotent. |
| `doctor` | Diagnose: server reachable & key valid & version OK; datadir and lua dir found; hook enabled in N/M user profiles; bundle age and entry count; last hook failures from the log; ingress-URL warning. |
| `sync [--dry-run]` | Build the library bundle from the configured scope; atomic swap; print "Plugins ▸ Rescan Plugins" reminder when the command set changed. |
| `hook <gcode-path>` | Post-processing entry point (§6). Not meant to be called by hand. |
| `profiles push\|pull\|status [--for-my-printers] [--force\|--keep-local]` | Profile sync (§7). |

### 4.3 Configuration and state

`~/.config/printernizer-connect/config.toml` (platformdirs equivalent on each OS), mode 0600:

```toml
server_url = "http://printernizer.local:8000"
api_key    = "pk_…"

[prusaslicer]
datadir = ""            # optional override; auto-discovered otherwise

[sync]
tags        = ["prusaslicer"]   # library tags to mirror
recent      = 25                # plus N most recent STL/3MF entries
size_budget_mb = 1024           # stop adding entries beyond this
group_by    = ["collection"]    # menu grouping: collection | printer | tag | recent

[hook]
fail_export_on_error = false
print_after_upload   = false

[hook.printer_map]              # SLIC3R_PRINTER_MODEL → Printernizer printer id
"COREONE" = "prusa-core-one"
```

`state.json` (same dir): last-synced profile hashes, last sync timestamp, last
bundle manifest version. Log file: `printernizer-connect.log` (rotating, 1 MB×3).

### 4.4 PrusaSlicer datadir discovery (`paths.py`)

**PrusaSlicer 3.0 has no `PrusaSlicer.ini`.** Verified on 3.0.0-alpha11: the
application config is `<datadir>/shared_runtime/PrusaSlicer.json`, whose
`app_config_settings.version` field carries the exact slicer version
(`"3.0.0-alpha11"`). The 2.x heuristic of "find the folder containing
`PrusaSlicer.ini`" therefore fails on 3.0 and must not be used.

Discovery order: config override → `--datadir` flag → per-OS candidates. A
candidate is a directory containing **either** `shared_runtime/PrusaSlicer.json`
(3.0) **or** `PrusaSlicer.ini` (2.x):

- macOS: `~/Library/Application Support/{PrusaSlicer3-dev, PrusaSlicer3-alpha, PrusaSlicer3, PrusaSlicer}`
- Linux: `~/.config/{same names}`
- Windows: `%APPDATA%\{same names}`

`PrusaSlicer3-dev` is confirmed as the alpha11 name on macOS. The list is data,
not code. If several exist, `setup` asks. The plugin folder is `<datadir>/lua/`;
it exists (empty) on a fresh alpha install.

## 5. Pull — the library bundle

### 5.1 Generated bundle layout

```
<datadir>/lua/com.printernizer.library/
├── manifest.json                 # version = generator version + sync timestamp
├── printernizer_lib.lua          # copied verbatim from bundle_template
├── tag_project.lua               # copied verbatim
├── <checksum>-<i>.stl            # one per object (multi-object 3MF → several)
└── m_<checksum8>.lua             # one command file per library entry
```

**Flat by design.** Prusa's own calibration bundle keeps its `.stl`, `.svg` and
helper `.lua` files at the bundle root and loads them by bare filename
(`api.load_stl("temp_tower-base.stl")`, `require('note_badge')`). This design
copies that layout exactly rather than relying on unverified subdirectory
support. Asset filenames are `[A-Za-z0-9.-_ ]` only, which checksums satisfy.

### 5.2 Per-model command (rendered from `model_command.lua.j2`)

```lua
info = {
  id = "m_3fa2c9e1", type = "project.plugin",
  title = "Benchy — 12.3 MB · 0.2 mm · 1h 42m · last printed Core One, 2026-08-30",
  menu = "Printernizer/Recent/Benchy",
  params = {
    {name="apply_settings", label="Apply proven settings (0.2 mm · 15% · 3 perimeters)", type="bool", default=true},
    {name="tag",            label="Tag project for Printernizer job tracking",          type="bool", default=true},
  },
}
function execute(opts)
  local lib = require("printernizer_lib")
  lib.load{
    checksum = "3fa2c9e1…",
    stls     = {"3fa2c9e1-0.stl"},
    settings = {layer_height=0.2, fill_density="15%", perimeters=3},
    opts     = opts,
  }
end
```

- `title` is the **detail card**: name, size, and — when Printernizer has
  metadata from a previous print — layer height, estimated time, last printer and
  date. It is the thumbnail substitute.
- `apply_settings` is present only when Printernizer has normalized print
  metadata for the entry; the label lists the values so the user knows what they
  are accepting. Only keys writable by `ConfigBox:set` are emitted (numbers,
  percentages, enums): `layer_height`, `fill_density`, `perimeters`,
  `top_solid_layers`, `bottom_solid_layers`, `fill_pattern`, `brim_type`.
  Booleans (e.g. `support_material`) are never emitted.
- Menu labels have `/` replaced with `∕` (U+2215) and are truncated to 60 chars.
- `id` is `m_` + first 8 hex chars of the checksum, extended on collision.

### 5.3 `printernizer_lib.lua`

```lua
local M = {}
function M.load(spec)
  local bed = api.project:current_bed()
  local params = (spec.opts.apply_settings and spec.settings) or nil
  for _, path in ipairs(spec.stls) do
    -- Prusa's own plugins use both keys; set both until S3 says which applies.
    api.project:add_object{ mesh = api.load_stl(path), params = params, object_params = params }
  end
  if spec.opts.tag then M.stamp(bed, { src = spec.checksum }) end
end
function M.stamp(bed, fields)
  local z = bed:print_presets():value("first_layer_height")   -- number in mm
  local parts = {}
  for k, v in pairs(fields) do parts[#parts+1] = "; PRINTERNIZER_" .. string.upper(k) .. "=" .. tostring(v) end
  api.project:insert_layer_custom_gcode(bed, z, table.concat(parts, "\n"))
end
return M
```

`first_layer_height` may be an opaque percentage value in some presets; the
library falls back to `layer_height` and then to `0.2`. Stamps are comments, so
the cooling-buffer override does not apply.

### 5.4 `tag_project.lua` (static command)

`menu = "Printernizer/Tag this project…"`, params: `business` (bool),
`order_id` (string), `customer` (string), `notes` (string). Calls
`lib.stamp(bed, {business=…, order=…, customer=…, notes=…})`. Empty strings are
omitted. This captures Printernizer's business/private distinction at slicing
time for projects that did not start from the library.

### 5.5 Scope and grouping (`scope.py`)

1. Query `GET /api/v1/library/files` with `file_type` ∈ {`.stl`, `.3mf`} (`.gcode`
   entries have no mesh and are excluded), `tags=<configured>`, then
   `sort_by=created_at desc` for the recent set. Union, dedupe by checksum.
2. Apply the size budget in priority order: tagged entries first, then recent.
   Entries beyond the budget are dropped with a `sync` summary line.
3. Grouping → menu path `Printernizer/<group>/<name>`:
   - `collection`: alphabetically first tag of the entry, else "Library".
   - `printer`: Printernizer's `printer_model` for the entry, else "Any printer".
   - `recent`: the recent set duplicated under `Printernizer/Recent/`.
   Multiple `group_by` values produce multiple entries pointing at the same STL.

### 5.6 Conversion (`convert.py`)

- `.stl` → copied as `<checksum>-0.stl`.
- `.3mf` → each object exported as `<checksum>-<i>.stl` via `trimesh`; the
  command loads all of them as separate objects. Objects with per-object settings
  in the 3MF are not preserved (out of scope).
- Files that fail conversion are skipped and reported; they never produce a
  command file.

### 5.7 Atomic swap and rescan

`generator.py` renders into `com.printernizer.library.new`, verifies every
command file references only assets that exist and passes a Lua syntax check
(`luac -p` if available, else a conservative Python-side check of the rendered
template), then renames `library` → `library.old`, `library.new` → `library`,
deletes `library.old`. STLs unchanged since the last sync are hard-linked or
copied from the old bundle to avoid re-downloading (cache keyed by checksum).

`sync` compares the old and new command-file sets; if they differ it prints
**"Open PrusaSlicer ▸ Plugins ▸ Rescan Plugins to see the changes."**

### 5.8 Failure model

`execute` cannot report errors, so the generator guarantees invariants instead:
every referenced asset exists; every file passed syntax check; no entry is
removed while its command file exists (the swap replaces both together). If
loading still fails inside PrusaSlicer the only symptom is "nothing happened" —
`doctor` therefore validates the installed bundle the same way.

## 6. Push — the post-processing hook

**Confirmed present in 3.0.0-alpha11:** the binary carries the `post_process`
config key, the "A post-processing script has been detected in the config data"
warning, the `SLIC3R_` environment-variable prefix, and the full physical-printer
/ print-host stack (`physical_printer`, `print_host`, `printhost_apikey`,
`host_type`, `octoprint`, `prusalink`). Push and the optional shim are both
viable on 3.0.

`setup` appends `"<path-to-printernizer-connect>" hook` to the `post_process`
key of each selected user print preset. `post_process` is a `;`-separated list;
existing scripts are preserved; the entry is added once. Vendor/system presets
are never modified. **The on-disk preset location and format changed in 3.0**
(see §7) — `prusaslicer/profiles.py` owns that difference, and spike S3b pins it
down on a wizard-completed install.

`hook <gcode-path>`:

1. Collect metadata from environment: `SLIC3R_PRINTER_MODEL`,
   `SLIC3R_PRINTER_SETTINGS_ID`, `SLIC3R_PRINT_SETTINGS_ID`,
   `SLIC3R_FILAMENT_SETTINGS_ID`, `SLIC3R_FILAMENT_TYPE`, `SLIC3R_LAYER_HEIGHT`,
   `SLIC3R_NOZZLE_DIAMETER`, `SLIC3R_PP_OUTPUT_NAME`, `SLIC3R_PRINT_HOST`,
   plus slicer name/version from the G-code header.
2. Scan the first 256 KB of the file for
   `; PRINTERNIZER_<KEY>=<value>` lines → `src`, `business`, `order`, `customer`,
   `notes`.
3. **Stand down** (exit 0, log "delegated to print host") if `SLIC3R_PRINT_HOST`
   is set and matches the configured `server_url` host.
4. Stream `POST /api/v1/connect/exports` (multipart: `file`, `metadata` JSON).
   Timeouts: connect 5 s, read/write stall 60 s, no total cap. One retry on
   connection error.
5. If `print_after_upload` and `printer_map[SLIC3R_PRINTER_MODEL]` resolves, the
   metadata carries `print_on`.
6. **Always exit 0** unless `fail_export_on_error = true`. Errors and the server's
   response go to the log file.

## 7. Profile sync

- **Registration.** On first `profiles` use the companion registers itself via
  `POST /api/v1/slicing` as a `SlicerConfig` with `slicer_type="prusaslicer"`,
  `backend_type="connect"`, `name="PrusaSlicer on <hostname>"`,
  `version=<from PrusaSlicer.ini or binary>`, `executable_path=""`. The id is
  stored in `state.json`.
- **Preset layout and format both changed in 3.0.** Verified on alpha11: there
  are no top-level `print/`, `filament/`, `printer/` or `physical_printer/`
  directories. Presets live under `<datadir>/presets/user/` and
  `<datadir>/presets/local/<vendor>/`, and the shipped vendor presets are
  **YAML, not INI** — `presets/local/prusa-research-fff/PrusaResearch/` contains
  ~326 `preset-*.yaml` files keyed by `kind:` / `inherits:` / `values:`, beside a
  `vendor.yaml`. User presets are very likely YAML too, but a fresh install has
  none, so that is confirmed by spike S3b.

  **Consequence:** the INI assumption elsewhere in this spec is wrong for 3.0.
  `prusaslicer/ini.py` becomes `prusaslicer/presets.py` handling both the 2.x
  INI layout and the 3.0 YAML one; the endpoint below is `import-preset`, not
  `import-ini`; and §8.4's "existing PrusaSlicer ini parser" does not apply to
  3.0 input. M4 is designed after S3b reports, not before.
- **push.** Enumerate user presets in whichever layout was detected. Upload each
  as raw text with `(type, name, sha256)` to
  `POST /api/v1/slicing/{slicer_id}/profiles/import-ini`. Server parses settings
  into `settings_json` and stores `raw_content`.
- **pull.** `GET /api/v1/slicing/{slicer_id}/profiles` + `/profiles/{id}/raw`.
  For each: if the local file is absent → write; if local hash == last-synced hash
  → overwrite; if local changed and remote unchanged → keep local; if both changed
  → **conflict**: report, skip, unless `--force` (take remote) or `--keep-local`.
  `--for-my-printers` restricts to profiles whose `compatible_printers` /
  `printer_model` matches a printer in `/connect/info`.
- **status.** Table of local/remote/last-synced hashes and the resulting action.
- Physical printers are not synced (they contain host credentials).

## 8. Server-side changes (`printernizer` repo)

### 8.1 API keys

- Migration: table `api_keys(id TEXT PK, name TEXT, key_hash TEXT UNIQUE,
  created_at, last_used_at)`. Keys are `pk_` + 32 url-safe bytes, shown once,
  stored as SHA-256.
- Dependency `require_api_key` accepting `X-Api-Key: <key>` or
  `Authorization: Bearer <key>`; 401 with the standard error envelope.
- Endpoints under the existing settings router: `GET/POST/DELETE
  /api/v1/settings/api-keys`. Settings UI section "API keys" (create, copy once,
  revoke).
- **Enforced only on** `/api/v1/connect/*`, the new profile endpoints, and the
  shim. All existing routes stay as they are.

### 8.2 `connect` router — `src/api/routers/connect.py`, prefix `/api/v1/connect`

| Endpoint | Behaviour |
|---|---|
| `GET /info` | `{server_version, min_connect_version, capabilities: {exports, profiles, printhost}, printers: [{id, name, printer_model, manufacturer}]}` |
| `POST /exports` | Multipart `file` + `metadata` JSON. Validates type (`.gcode`, `.bgcode`, `.3mf`), delegates to `FileService.upload_files` (source_type `connect`), then applies: `is_business`, notes/order/customer, `source_checksum` link, and if `print_on` is set calls the same code path as `POST /library/files/{checksum}/print`. Returns the library entry. |

Library browsing and downloads for `sync` reuse the existing unauthenticated
`/api/v1/library/*` endpoints unchanged.

### 8.3 Ingest stamps

The G-code metadata extractor recognises `; PRINTERNIZER_SRC=<checksum>`,
`_BUSINESS=1`, `_ORDER=<text>`, `_CUSTOMER=<text>`, `_NOTES=<text>` and stores them in the file's metadata. On job
creation (any source: connect export, printer download, watch folder) the job is
linked to the source library entry and order, and `is_business` is set. This is
what makes provenance survive SD-card and Prusa Connect routes.

### 8.4 Profiles

- Migration: `slicer_profiles.raw_content TEXT NULL`, `content_hash TEXT NULL`.
- `POST /api/v1/slicing/{slicer_id}/profiles/import-preset` (multipart, one or
  more preset files, form fields `profile_type` and `format` ∈ `ini | yaml`) —
  parses into `settings_json` with the parser matching `format`, stores raw text
  and hash; upsert by `(slicer_id, profile_type, profile_name)`. The 3.0 YAML
  parser is written against whatever S3b reports; the existing INI parser covers
  2.x only.
- `GET /api/v1/slicing/profiles/{profile_id}/raw` → `text/plain`.
- `backend_type="connect"` is accepted by `register_slicer`; `verify_slicer_availability`
  returns true for it without touching the filesystem.

### 8.5 OctoPrint-compatible shim (optional milestone M5)

Mounted at `/printhost/{printer_id}`: `GET api/version` → `{api:"0.1", server:"printernizer-<v>", text:"OctoPrint 1.9 (Printernizer)"}`; `POST api/files/local` (multipart `file`, `print`, `select`) → same path as `/connect/exports` with `print_on=printer_id`. API-key required. `setup --printhost` writes `physical_printer/Printernizer - <name>.ini` with `host_type = octoprint`, `print_host = <server_url>/printhost/<id>`, `printhost_apikey`. Path-prefix support in PrusaSlicer's OctoPrint host is verified in S7 before this milestone starts.

## 9. Cross-cutting

- **Versioning.** Every command calls `/connect/info` first and refuses to run if
  `server_version < MIN_SERVER` or `connect_version < min_connect_version`, with a
  clear upgrade message. The generated manifest carries generator version and
  `min_slicer_version`/`required_apis` (declared even though alpha11 doesn't
  enforce them).
- **Security.** LAN tool; HTTPS supported, not required. The key lives only in
  `config.toml` (0600) — never in the bundle, the Lua, or a G-code comment. The
  hook reads env and sends the one file it was handed; it never executes content.
  Server: keys hashed; `/exports` validates extension and size like `/files/upload`.
- **Logging.** All CLI output is human-readable; `--json` for `doctor`/`status`.
  The hook writes only to the log file.
- **API instability.** The Lua surface is `printernizer_lib.lua` (~40 lines),
  `tag_project.lua` and one template. Everything else is Python and survives an
  API break; if a break lands, `sync` keeps generating for the last known-good API
  version and `doctor` reports the mismatch.
- **Home Assistant.** Ingress URLs cannot be used by a CLI; the add-on must expose
  its port. `doctor` detects `/api/hassio_ingress/` in `server_url` and explains.

## 10. Testing

- **Python unit:** `httpx.MockTransport` fake of Printernizer for `client.py` and
  every command; tmp-datadir fixtures for `ini.py` (round-trip, idempotent
  `post_process` edit, existing scripts preserved); `scope.py` selection and budget;
  `convert.py` with small fixture 3MFs; **snapshot tests of rendered bundles**.
- **Lua:** `printernizer_lib.lua` and `tag_project.lua` run under `lua5.4` in CI
  against a `mock_api.lua` that records `load_stl`/`add_object`/`insert_layer_custom_gcode`
  calls; `luac -p` over the templates and a rendered sample bundle.
- **Integration:** CI service container running `ghcr.io/schmacka/printernizer`;
  end-to-end `setup → sync → hook → profiles push/pull` against it.
- **Server (`printernizer` repo):** pytest for api-key dependency, `/connect/*`,
  stamp ingest, profile import/raw, migrations.
- **Manual acceptance:** `docs/acceptance-prusaslicer-3.md` checklist run against
  the current alpha before each release.

## 11. Spike S0 — verify before building

Five of the eight original questions were answered on 2026-09-06 by reading
PrusaSlicer 3.0.0-alpha11 itself (`/Applications/PrusaSlicer-3.0.0-alpha11.app`)
— its shipped calibration plugins, its data directory, and its binary. Those
answers are folded into §2, §4.4, §5 and §6 above. What remains needs a running
GUI and a human.

**Resolved without a spike** (evidence in §2, §4.4, §5.1, §6, §7):

| Was | Answer |
|---|---|
| S1 subdirectory assets | Not needed — Prusa's own bundle is flat; design is flat |
| S6 datadir name / app config | `PrusaSlicer3-dev`; no `PrusaSlicer.ini`, config is `shared_runtime/PrusaSlicer.json` |
| S6 post-processing exists in 3.0 | Yes — `post_process` key, `SLIC3R_` prefix, warning string all present |
| S7 print host exists in 3.0 | Yes — `physical_printer`, `print_host`, `host_type`, `octoprint`, `prusalink` all present |
| Preset writes from Lua | Numbers, `"15%"` percentages and enum strings all work (Prusa's own plugins do it) |

**Still open — GUI probes (≈ half a day, human at the keyboard):**

| # | Question | If no |
|---|---|---|
| S2 | Does `Plugins ▸ Rescan Plugins` exist, and does it pick up newly added command files without restarting? | `sync` tells the user to restart PrusaSlicer |
| S3 | On `add_object`, does `params`, `object_params`, or both apply per-object settings? | Use whichever works; if neither, fall back to `print_presets():set` and warn that it dirties the preset |
| S3b | On a wizard-completed install, where do user presets land under `presets/user/` and in what format? | Determines `profiles.py`; blocks M4 only |
| S4 | Do menu entries sort alphabetically or in scan order? | Prefix labels with zero-padded ordinals for the Recent group |
| S5 | Does a ~80-char `title` render acceptably as the dialog heading? | Shorten to name + print time |
| S8 | Which `SLIC3R_*` variables reach a post-processing script, and is `SLIC3R_PRINT_HOST` among them? | Stand-down check uses whatever host variable is exported, or is dropped |

Findings are recorded in `docs/superpowers/spikes/2026-09-06-prusaslicer-api/FINDINGS.md`
and the affected sections updated before M2. **M1 does not depend on any of them**
and can proceed in parallel.

## 12. Milestones

| M | Deliverable | Repo |
|---|---|---|
| M0 | Spike S1–S8 + findings doc | connect |
| M1 | API keys, `connect` router (`/info`, `/exports`), settings UI, tests | printernizer |
| M2 | `setup`, `doctor`, `sync`, bundle generator, Lua lib, tag command — **library in the slicer** | connect |
| M3 | `hook`, stamp ingest, `print_after_upload` | both |
| M4 | Profile sync (endpoints + migration, `profiles push/pull/status`) | both |
| M5 | OctoPrint shim + `setup --printhost` (optional) | both |
| M6 | pipx packaging, CI releases, README/docs, acceptance checklist | connect |

Each milestone gets its own implementation plan.

## 13. Risks

- **API churn.** Prusa states the Lua API will break. Mitigated by the tiny Lua
  surface and generator versioning; accepted as the cost of the chosen pull UX.
- **Unported 2.x features in 3.0 alpha** (post-processing, print hosts, profile
  layout). Push and profile sync are verified against 2.9 as well so the project is
  useful while 3.0 matures.
- **Menu size.** Hundreds of entries are fine; thousands are not. The size budget
  and tag scope are the control; `sync` reports counts.
- **Silent failures in Lua.** Mitigated by generator invariants and `doctor`.
- **No global auth in Printernizer.** The companion's own endpoints are protected;
  the rest of the API remains open on the LAN as today.
