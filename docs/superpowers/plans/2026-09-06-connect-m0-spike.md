# Printernizer Connect M0 — PrusaSlicer 3.0 API Spike Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Answer the six open questions in spec §11 by building a throwaway probe bundle, running it in PrusaSlicer 3.0.0-alpha11, and recording the answers.

**Architecture:** A single throwaway Lua bundle (`com.printernizer.spike`) installed into PrusaSlicer's user plugin folder, plus one shell script probing the post-processing environment. Each probe is designed so its result is visible **as a change on the 3D plate or as text in a file** — the plugin API has no message boxes and swallows `execute` errors, so "did it work?" must be answerable by looking.

**Tech Stack:** Lua 5.4 (PrusaSlicer sandbox), POSIX shell, Python 3.11 (findings scaffolding only).

**Spec:** `docs/superpowers/specs/2026-09-06-printernizer-connect-design.md`

## Global Constraints

- Target: **PrusaSlicer 3.0.0-alpha11** at `/Applications/PrusaSlicer-3.0.0-alpha11.app`.
- Data directory: `~/Library/Application Support/PrusaSlicer3-dev` (verified). Plugin folder: `<datadir>/lua/`.
- Bundle layout is **flat** — `manifest.json` plus `.lua` and asset files at the bundle root. No subdirectories.
- Bundle id `com.printernizer.spike`; every command file needs a non-empty `menu` (empty menu paths crash registration in alpha11).
- Top-level Lua may only declare `info`, functions and constants. **Never call `api` or `require` at file level** — scanning runs in a state where neither exists, and the failure is silent.
- Directory-copy installation needs no signing. Do not use ZIP import.
- This is throwaway code. It lives in `docs/superpowers/spikes/` and is deleted after M2 starts.

## Human-in-the-loop notice

**Tasks 1, 2 and 6 are agent work. Tasks 3, 4 and 5 require a human at the keyboard** — they involve clicking through a GUI that cannot be automated. An agent executing this plan must stop at Task 3 and hand the checklist to the user, then resume at Task 6 with the user's answers.

## File Structure

| File | Responsibility |
|---|---|
| `docs/superpowers/spikes/2026-09-06-prusaslicer-api/bundle/manifest.json` | Bundle metadata |
| `.../bundle/probe.stl` | Tetrahedron mesh used by the load probe |
| `.../bundle/s3_params.lua` | S3: which key applies per-object settings |
| `.../bundle/s4_alpha.lua`, `s4_mike.lua`, `s4_zeta.lua` | S4: menu ordering |
| `.../bundle/s5_long_title.lua` | S5: long dialog heading |
| `.../bundle/s7_stamp.lua` | Stamp mechanics + `first_layer_height` value type |
| `.../s2_added_later.lua` | S2: copied in mid-session to test rescan |
| `.../postprocess_probe.sh` | S8: dump argv + environment |
| `.../install.sh` | Copy bundle into the datadir |
| `.../CHECKLIST.md` | The human run-through |
| `.../FINDINGS.md` | Answers, filled in at Task 6 |

---

### Task 1: Probe bundle skeleton and mesh asset

**Files:**
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/bundle/manifest.json`
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/bundle/probe.stl`
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/install.sh`

**Interfaces:**
- Consumes: nothing.
- Produces: bundle directory `bundle/` that later tasks add `.lua` files to; `install.sh` copies it to `$DATADIR/lua/com.printernizer.spike`.

- [ ] **Step 1: Create the manifest**

`bundle/manifest.json`:

```json
{
  "id": "com.printernizer.spike",
  "name": "Printernizer API Spike",
  "version": "0.0.1",
  "min_slicer_version": "3.0.0",
  "author": "printernizer",
  "license": "MIT",
  "description": "Throwaway probes for the PrusaSlicer 3.0 Lua plugin API",
  "required_apis": { "project.plugin": "1.0.0" }
}
```

- [ ] **Step 2: Create the probe mesh**

`bundle/probe.stl` — a closed tetrahedron, 10 mm base, ~8 mm tall. ASCII STL so it is diffable:

```
solid probe
facet normal 0 0 -1
  outer loop
    vertex 0 0 0
    vertex 5 8.66 0
    vertex 10 0 0
  endloop
endfacet
facet normal 0 -1 0
  outer loop
    vertex 0 0 0
    vertex 10 0 0
    vertex 5 2.89 8.16
  endloop
endfacet
facet normal 0.87 0.5 0
  outer loop
    vertex 10 0 0
    vertex 5 8.66 0
    vertex 5 2.89 8.16
  endloop
endfacet
facet normal -0.87 0.5 0
  outer loop
    vertex 5 8.66 0
    vertex 0 0 0
    vertex 5 2.89 8.16
  endloop
endfacet
endsolid probe
```

- [ ] **Step 3: Create the installer**

`install.sh`:

```sh
#!/bin/sh
# Copy the spike bundle into PrusaSlicer's user plugin folder.
set -eu
DATADIR="${PRUSA_DATADIR:-$HOME/Library/Application Support/PrusaSlicer3-dev}"
DEST="$DATADIR/lua/com.printernizer.spike"
if [ ! -d "$DATADIR" ]; then
  echo "Data directory not found: $DATADIR" >&2
  echo "Set PRUSA_DATADIR to override." >&2
  exit 1
fi
mkdir -p "$DEST"
cp "$(dirname "$0")"/bundle/* "$DEST/"
echo "Installed to: $DEST"
ls -1 "$DEST"
```

- [ ] **Step 4: Verify the installer runs and lands the files**

```bash
chmod +x docs/superpowers/spikes/2026-09-06-prusaslicer-api/install.sh
docs/superpowers/spikes/2026-09-06-prusaslicer-api/install.sh
```

Expected: prints the destination path and lists `manifest.json` and `probe.stl`.

- [ ] **Step 5: Verify the STL is well-formed**

```bash
python3 -c "
import re,pathlib
t=pathlib.Path('docs/superpowers/spikes/2026-09-06-prusaslicer-api/bundle/probe.stl').read_text()
f=len(re.findall(r'facet normal',t)); v=len(re.findall(r'vertex',t))
assert f==4, f'expected 4 facets, got {f}'
assert v==12, f'expected 12 vertices, got {v}'
print('probe.stl OK: 4 facets, 12 vertices')
"
```

Expected: `probe.stl OK: 4 facets, 12 vertices`

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/spikes/2026-09-06-prusaslicer-api
git commit -m "spike: Add PrusaSlicer 3.0 probe bundle skeleton"
```

---

### Task 2: The probe commands

**Files:**
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/bundle/s3_params.lua`
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/bundle/s4_alpha.lua`
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/bundle/s4_mike.lua`
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/bundle/s4_zeta.lua`
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/bundle/s5_long_title.lua`
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/bundle/s7_stamp.lua`
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/s2_added_later.lua`

**Interfaces:**
- Consumes: `bundle/probe.stl` from Task 1.
- Produces: seven Lua command files. Task 3's checklist refers to them by menu path: `Spike/S3 Params`, `Spike/S4 Order/{alpha,mike,zeta}`, `Spike/S5 Long title`, `Spike/S7 Stamp`, `Spike/S2 Added later`.

**Design note — how each probe reports:** `execute` errors are logged, never shown. So every probe that could abort mid-way **adds a marker cube first**. If the marker appears alone, the call after it failed. Object count on the plate is the signal.

- [ ] **Step 1: Write the S3 params probe**

`bundle/s3_params.lua` — sets the same five keys through `params` on one object and `object_params` on another, so the human can compare them side by side:

```lua
info = {
    id = "s3_params",
    type = "project.plugin",
    title = "S3: params vs object_params",
    menu = "Spike/S3 Params",
}

local SETTINGS = {
    layer_height = 0.3,
    fill_density = "55%",
    perimeters = 6,
    fill_pattern = "gyroid",
    brim_type = "outer_only",
}

function execute(opts)
    -- Left object: settings via `params` (used by Prusa's flow_tower.lua)
    api.project:add_object{
        mesh = api.make_cube(20, 20, 20),
        translate = { x = -15 },
        params = SETTINGS,
    }
    -- Right object: settings via `object_params` (used by Prusa's temp_tower.lua)
    api.project:add_object{
        mesh = api.make_cube(20, 20, 20),
        translate = { x = 15 },
        object_params = SETTINGS,
    }
end
```

- [ ] **Step 2: Write the S4 menu-ordering probes**

Three files, created in an order that is neither alphabetical nor reverse, each adding a differently sized cube so the human can tell which ran.

`bundle/s4_zeta.lua`:

```lua
info = { id = "s4_zeta", type = "project.plugin",
         title = "S4: zeta (file written 1st)", menu = "Spike/S4 Order/zeta" }
function execute(opts)
    api.project:add_object{ mesh = api.make_cube(30, 10, 10) }
end
```

`bundle/s4_mike.lua`:

```lua
info = { id = "s4_mike", type = "project.plugin",
         title = "S4: mike (file written 2nd)", menu = "Spike/S4 Order/mike" }
function execute(opts)
    api.project:add_object{ mesh = api.make_cube(20, 10, 10) }
end
```

`bundle/s4_alpha.lua`:

```lua
info = { id = "s4_alpha", type = "project.plugin",
         title = "S4: alpha (file written 3rd)", menu = "Spike/S4 Order/alpha" }
function execute(opts)
    api.project:add_object{ mesh = api.make_cube(10, 10, 10) }
end
```

Write them in the order zeta → mike → alpha so filesystem creation order differs from alphabetical order.

- [ ] **Step 3: Write the S5 long-title probe**

The title is the detail card in the real design (§5.2), so this probe uses a realistic one — 84 characters:

```lua
info = {
    id = "s5_long_title",
    type = "project.plugin",
    title = "Benchy 3DBenchy v2 final — 12.3 MB · 0.2 mm · 1h 42m · last printed Core One, 2026-08-30",
    menu = "Spike/S5 Long title",
    params = {
        {name = "apply_settings", label = "Apply proven settings (0.2 mm · 15% · 3 perimeters)", type = "bool", default = true},
        {name = "tag", label = "Tag project for Printernizer job tracking", type = "bool", default = true},
    },
}
function execute(opts)
    api.project:add_object{ mesh = api.make_cube(10, 10, 10) }
end
```

- [ ] **Step 4: Write the S7 stamp probe**

Also probes what `first_layer_height` returns, and whether `load_stl` of a flat asset works:

```lua
info = { id = "s7_stamp", type = "project.plugin",
         title = "S7: provenance stamp + load_stl", menu = "Spike/S7 Stamp" }

function execute(opts)
    -- Marker first: proves execute ran even if a later call aborts.
    api.project:add_object{ mesh = api.make_cube(20, 20, 10) }

    -- Flat asset load (Prusa's own plugins do exactly this).
    api.project:add_object{ mesh = api.load_stl("probe.stl"), translate = { x = 30 } }

    local bed = api.project:current_bed()

    -- What type does first_layer_height come back as? print() goes to stdout;
    -- PrusaSlicer must be started from a terminal to see it.
    local ok, v = pcall(function() return bed:print_presets():value("first_layer_height") end)
    print("S7 first_layer_height ok=" .. tostring(ok) .. " type=" .. type(v) .. " value=" .. tostring(v))

    local z = 0.2
    if ok and type(v) == "number" and v > 0 then z = v end

    api.project:insert_layer_custom_gcode(bed, z,
        "; PRINTERNIZER_SRC=spike123\n; PRINTERNIZER_BUSINESS=1")
end
```

- [ ] **Step 5: Write the S2 rescan probe (staged outside the bundle)**

`s2_added_later.lua` lives one level **above** `bundle/` so `install.sh` does not copy it. The human copies it in mid-session.

```lua
info = { id = "s2_added_later", type = "project.plugin",
         title = "S2: added after startup", menu = "Spike/S2 Added later" }
function execute(opts)
    api.project:add_object{ mesh = api.make_cube(40, 5, 5) }
end
```

- [ ] **Step 6: Syntax-check every probe**

PrusaSlicer bundles Lua but exposes no checker, so use the system one if present; otherwise the check is deferred to the GUI run.

```bash
cd docs/superpowers/spikes/2026-09-06-prusaslicer-api
if command -v luac >/dev/null 2>&1; then
  luac -p bundle/*.lua s2_added_later.lua && echo "LUA SYNTAX OK"
else
  echo "luac not installed — run: brew install lua"
fi
```

Expected: `LUA SYNTAX OK`. If `luac` is missing, install Lua and re-run — do not skip this, a syntax error makes a command silently vanish from the menu.

- [ ] **Step 7: Verify no probe touches `api` or `require` at file level**

This is the single most common way a bundle silently fails to register.

```bash
cd docs/superpowers/spikes/2026-09-06-prusaslicer-api
python3 - <<'PY'
import pathlib, re, sys
bad = []
for f in sorted(list(pathlib.Path('bundle').glob('*.lua')) + [pathlib.Path('s2_added_later.lua')]):
    depth, offenders = 0, []
    for n, line in enumerate(f.read_text().splitlines(), 1):
        stripped = line.strip()
        if depth == 0 and re.search(r'\b(api\.|require\s*\()', stripped) and not stripped.startswith('--'):
            offenders.append(n)
        depth += len(re.findall(r'\bfunction\b', line)) - len(re.findall(r'\bend\b', line))
    if offenders:
        bad.append(f"{f}: lines {offenders}")
print("\n".join(bad) if bad else "NO FILE-LEVEL api/require — OK")
sys.exit(1 if bad else 0)
PY
```

Expected: `NO FILE-LEVEL api/require — OK`

- [ ] **Step 8: Reinstall and commit**

```bash
docs/superpowers/spikes/2026-09-06-prusaslicer-api/install.sh
git add docs/superpowers/spikes/2026-09-06-prusaslicer-api
git commit -m "spike: Add PrusaSlicer 3.0 API probe commands"
```

---

### Task 3: The post-processing environment probe

**Files:**
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/postprocess_probe.sh`

**Interfaces:**
- Consumes: nothing.
- Produces: `~/printernizer-spike-postprocess.txt` when PrusaSlicer exports G-code with this script configured. Task 6 reads it to answer S8.

- [ ] **Step 1: Write the probe script**

It must exit 0 unconditionally — a non-zero exit makes PrusaSlicer fail the export with a dialog, which is exactly the behaviour the real hook must avoid.

```sh
#!/bin/sh
# S8 probe: record what PrusaSlicer hands a post-processing script.
# Always exits 0 so a failure here never breaks the user's export.
OUT="$HOME/printernizer-spike-postprocess.txt"
{
  echo "=== invoked $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  echo "ARGC=$#"
  i=1
  for a in "$@"; do echo "ARGV$i=$a"; i=$((i+1)); done
  echo "PWD=$(pwd)"
  echo "--- environment (SLIC3R_* first) ---"
  env | grep '^SLIC3R_' | sort
  echo "--- all other variables ---"
  env | grep -v '^SLIC3R_' | sort
  echo "--- first 40 lines of the g-code it was handed ---"
  [ -n "${1:-}" ] && [ -f "$1" ] && head -40 "$1"
  echo
} >> "$OUT" 2>&1
exit 0
```

- [ ] **Step 2: Verify it runs standalone and exits 0**

```bash
cd docs/superpowers/spikes/2026-09-06-prusaslicer-api
chmod +x postprocess_probe.sh
printf '; test gcode\nG1 X0\n' > /tmp/spike-test.gcode
SLIC3R_LAYER_HEIGHT=0.2 ./postprocess_probe.sh /tmp/spike-test.gcode
echo "exit=$?"
grep -c "SLIC3R_LAYER_HEIGHT=0.2" ~/printernizer-spike-postprocess.txt
```

Expected: `exit=0` and a count of `1`.

- [ ] **Step 3: Reset the output file so the real run starts clean**

```bash
rm -f ~/printernizer-spike-postprocess.txt
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/spikes/2026-09-06-prusaslicer-api/postprocess_probe.sh
git commit -m "spike: Add post-processing environment probe"
```

---

### Task 4: The human run-through checklist

**Files:**
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/CHECKLIST.md`

**Interfaces:**
- Consumes: everything from Tasks 1–3.
- Produces: a filled-in checklist the human hands back; Task 6 turns it into `FINDINGS.md`.

- [ ] **Step 1: Write the checklist**

`CHECKLIST.md`:

````markdown
# PrusaSlicer 3.0 API spike — run-through

Fill in every **Answer:** line. Where a question asks for a count, count objects
in the right-hand object list, not shapes on the plate.

## Setup

1. `docs/superpowers/spikes/2026-09-06-prusaslicer-api/install.sh`
2. Quit PrusaSlicer completely if it is running.
3. Start it **from a terminal** so `print()` output is visible:
   `/Applications/PrusaSlicer-3.0.0-alpha11.app/Contents/MacOS/PrusaSlicer`
4. Complete the configuration wizard if it appears (needed for S3b anyway).
   Pick a Prusa printer and accept the defaults.

## S0 — does the bundle register at all?

Open the **Plugins** menu.

- Is there a `Spike` submenu? **Answer:** ___
- List every entry you see under it. **Answer:** ___

If `Spike` is missing, the bundle failed to register — check the terminal for
scan errors and stop here.

## S4 — menu ordering

Look at `Plugins ▸ Spike ▸ S4 Order`. Files were created zeta → mike → alpha.

- Order shown top to bottom: **Answer:** ___
- Is that alphabetical, creation order, or something else? **Answer:** ___

## S5 — long title

Run `Plugins ▸ Spike ▸ S5 Long title`.

- Is the full 84-character title readable, truncated, or does it stretch the
  dialog off-screen? **Answer:** ___
- Do both checkbox labels render fully? **Answer:** ___
- Roughly how many characters of the title are visible? **Answer:** ___
- Take a screenshot and save it next to this file as `s5-dialog.png`.

Click Run, then **File ▸ New Project** to clear the plate.

## S3 — params vs object_params

Run `Plugins ▸ Spike ▸ S3 Params`. Two 20 mm cubes appear, left and right.

For **each** cube: right-click it → check its per-object settings (the gear /
"Object Settings" entry in the object list).

- Left cube (`params`) — which of these are present and set?
  `layer_height=0.3`, `fill_density=55%`, `perimeters=6`, `fill_pattern=gyroid`,
  `brim_type=outer_only`. **Answer:** ___
- Right cube (`object_params`) — same five keys. **Answer:** ___
- Any errors in the terminal? **Answer:** ___

Then **File ▸ New Project**.

## S7 — stamp, flat asset load, first_layer_height

Run `Plugins ▸ Spike ▸ S7 Stamp`.

- How many objects appear? (2 = `load_stl` of a flat asset works; 1 = it
  failed) **Answer:** ___
- Terminal line starting `S7 first_layer_height` — paste it verbatim:
  **Answer:** ___
- Slice the plate. Does the layer slider show a custom-G-code marker near the
  first layer? **Answer:** ___
- Export the G-code to `~/spike-s7.gcode`, then run:
  `grep -n PRINTERNIZER ~/spike-s7.gcode`
  Paste the output. **Answer:** ___
- Save the project as `~/spike-s7.3mf`, then run:
  `unzip -p ~/spike-s7.3mf '*' 2>/dev/null | grep -c PRINTERNIZER`
  Paste the number. **Answer:** ___

Then **File ▸ New Project**.

## S2 — rescan without restart

Leave PrusaSlicer **running**. In a terminal:

```sh
D="$HOME/Library/Application Support/PrusaSlicer3-dev/lua/com.printernizer.spike"
cp docs/superpowers/spikes/2026-09-06-prusaslicer-api/s2_added_later.lua "$D/"
```

- Does `Plugins ▸ Spike ▸ S2 Added later` appear **without** any action?
  **Answer:** ___
- Is there a `Plugins ▸ Rescan Plugins` menu item? What is it called exactly?
  **Answer:** ___
- After clicking it, does the new entry appear? **Answer:** ___
- Edit `s7_stamp.lua` in the installed bundle — change `spike123` to `spike456`
  — then run `S7 Stamp` again **without** rescanning. Does the exported G-code
  say `spike456`? (Tests whether execution code is re-read per run.)
  **Answer:** ___

## S8 — post-processing environment

1. Print Settings → Output options → **Post-processing scripts**. Enter the
   absolute path to `postprocess_probe.sh`, in quotes.
2. Save the print preset under a custom name (this also serves S3b).
3. Slice and export G-code to `~/spike-s8.gcode`.

- Did the export succeed without a dialog? **Answer:** ___
- Run `cat ~/printernizer-spike-postprocess.txt` and paste the whole
  `SLIC3R_*` block. **Answer:** ___
- Is `SLIC3R_PRINT_HOST` present? **Answer:** ___
- Is `SLIC3R_PP_OUTPUT_NAME` present? **Answer:** ___
- Is `ARGV1` the path to the G-code file? **Answer:** ___

## S3b — where do user presets land?

You saved a custom print preset in S8. Now also save a custom filament preset
and a custom printer preset (change any value, click the save icon, give it a
name starting with `Spike `).

```sh
D="$HOME/Library/Application Support/PrusaSlicer3-dev"
find "$D/presets" -type f | head -40
```

- Paste the output. **Answer:** ___
- Pick one file you saved and paste its first 15 lines
  (`head -15 <path>`) — we need the format, INI or JSON. **Answer:** ___
- Is there a `physical_printer` directory or key anywhere under `$D`?
  (`find "$D" -iname '*physical*'`) **Answer:** ___

## Cleanup

```sh
rm -rf "$HOME/Library/Application Support/PrusaSlicer3-dev/lua/com.printernizer.spike"
```

Remove the post-processing script from the print preset. Leave the custom
presets — M4 will want them.
````

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/spikes/2026-09-06-prusaslicer-api/CHECKLIST.md
git commit -m "spike: Add PrusaSlicer 3.0 spike run-through checklist"
```

- [ ] **Step 3: Hand off to the human**

Tell the user: the probe bundle is installed and the checklist is at
`docs/superpowers/spikes/2026-09-06-prusaslicer-api/CHECKLIST.md`. It needs
about half an hour with PrusaSlicer open, started from a terminal. Stop here and
wait for their answers — Tasks 5 and 6 depend on them.

---

### Task 5: Human executes the checklist

**Files:** none (the human edits `CHECKLIST.md` in place, or replies in chat).

**Interfaces:**
- Consumes: `CHECKLIST.md`, the installed bundle, `postprocess_probe.sh`.
- Produces: answers to S2, S3, S3b, S4, S5, S8, plus the S7 stamp confirmations.

- [ ] **Step 1: The user runs the checklist and returns the answers**

No agent action. Do not guess, infer, or fill in plausible-looking answers — a
wrong finding here silently corrupts M2's design. If the user reports a probe
crashed or a menu entry never appeared, treat that as a finding and record it.

---

### Task 6: Record findings and update the spec

**Files:**
- Create: `docs/superpowers/spikes/2026-09-06-prusaslicer-api/FINDINGS.md`
- Modify: `docs/superpowers/specs/2026-09-06-printernizer-connect-design.md` (§5.1, §5.2, §5.3, §6, §7, §11 as the answers require)

**Interfaces:**
- Consumes: the human's answers from Task 5.
- Produces: a spec whose §5–§7 describe verified behaviour, ready for M2.

- [ ] **Step 1: Write FINDINGS.md**

One section per question, each with: the question, the observed result verbatim,
and the design consequence. Template:

```markdown
# PrusaSlicer 3.0.0-alpha11 spike findings

**Run:** <date> · **Build:** 3.0.0-alpha11 · **Datadir:** ~/Library/Application Support/PrusaSlicer3-dev

## S2 — Rescan without restart
**Observed:** <verbatim>
**Consequence:** <what §5.7 must say>

## S3 — params vs object_params
**Observed:** <verbatim, per key>
**Consequence:** <which key printernizer_lib.lua uses; which of the five keys are emitted>

## S3b — user preset layout
**Observed:** <paths and format>
**Consequence:** <what profiles.py must implement>

## S4 — Menu ordering
## S5 — Long titles
## S7 — Stamp survival
## S8 — Post-processing environment
```

- [ ] **Step 2: Apply each consequence to the spec**

Work through `FINDINGS.md` top to bottom and edit the spec section named in each
consequence. Concretely:

- **S2 negative** (no rescan, or it does not pick up new files): §5.7's closing
  line changes from "Open PrusaSlicer ▸ Plugins ▸ Rescan Plugins" to "Restart
  PrusaSlicer to see the changes."
- **S3**: §5.2's generated template and §5.3's `printernizer_lib.lua` keep only
  the key that worked, and §5.2's settings list keeps only the keys that applied.
- **S3b**: §7's push/pull bullets get the real paths and format.
- **S4 non-alphabetical**: §5.5 gains a rule that the generator prefixes menu
  labels with zero-padded ordinals in the Recent group.
- **S5 truncated**: §5.2's title format shortens to what actually fits.
- **S7 negative** (stamp absent from exported G-code): §5.4's `tag_project.lua`
  and §8.3's stamp ingest are cut from the design; provenance comes only from
  the hook's own metadata. Say so explicitly in §5.3 and §12 (M3 shrinks).
- **S8**: §6 step 1's variable list is replaced with the observed one, and
  step 3's stand-down check uses the host variable that actually exists — or is
  deleted if none does.

- [ ] **Step 3: Re-check the spec for contradictions**

```bash
cd /Users/sebastianseubert/Developer/printernizer
grep -n "unverified\|spike S\|S3b\|not yet verified" docs/superpowers/specs/2026-09-06-printernizer-connect-design.md
```

Every hit must now either be resolved or still be a genuinely open question.
Delete the stale ones.

- [ ] **Step 4: Replace §11 with a results summary**

The spike is done, so §11 stops being a to-do list. Replace its "Still open"
table with a one-line-per-question results table and a pointer to `FINDINGS.md`.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/spikes/2026-09-06-prusaslicer-api/FINDINGS.md \
        docs/superpowers/specs/2026-09-06-printernizer-connect-design.md
git commit -m "spike: Record PrusaSlicer 3.0 API findings and update Connect spec"
```

- [ ] **Step 6: Report to the user**

State plainly which of the six questions were answered, which design decisions
changed as a result, and whether anything found makes M2 harder than the spec
assumed. If a probe was inconclusive, say so — do not present a guess as a
finding.
