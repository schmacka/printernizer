# Spike answers — live capture

Run: 2026-09-07 · PrusaSlicer 3.0.0-alpha11 · macOS

## S0 — bundle registers
- `Spike` submenu present: **yes**

## S4 — menu ordering
- Files created in order: zeta → mike → alpha
- Displayed order: **alpha, mike, zeta**
- Verdict: **alphabetical by menu label**, NOT scan/creation order.
- Consequence: ordering is controllable — the bundle generator must prefix menu
  labels with zero-padded ordinals wherever a non-alphabetical order matters
  (e.g. the "Recent" group, which should be newest-first).

## S5 — long dialog title
- 88-character title: **completely readable**, nothing truncated
- Visible characters: **all**
- Both checkbox labels render fully: **yes**
- Consequence: the "detail card" title design in spec §5.2 works as specified.
  Name + size + layer height + print time + last printer/date all fit in one
  heading. No shortening needed.

## S3 — params vs object_params  ★ DECISIVE
- `params` probe: 2 objects appeared (no throw), **none** of the five settings applied
- `object_params` probe: 2 objects appeared, **all five** settings applied:
  layer_height=0.3, fill_density=55%, perimeters=6, fill_pattern=gyroid,
  brim_type=outer_only
- Log: **nothing from our bundle**. `params` is discarded with no error or warning.
  (The 520 `top_one_perimeter_type` errors predate the spike — first seen
  2026-09-05 — and `note_badge.lua "Missing info table"` is Prusa's own shared
  module, benign and self-documented in the log.)

### Verdict
`object_params` is the working key on the top-level object. `params` is silently
ignored. Both enum-string keys (`fill_pattern`, `brim_type`) and the percentage
(`fill_density`) DO write — contradicting the unofficial docs' claim that
ConfigBox:set cannot write strings.

### Consequences
- `printernizer_lib.lua` emits **`object_params` only**. Remove the "set both keys
  until S3 says which" hedge from spec §5.2/§5.3.
- All five settings keys stay in the generated commands; no key needs dropping.
- Silent failure is the norm here, which reinforces the generator-invariants
  approach in §5.8 — nothing surfaces a mistake at runtime.

### Upstream bug (worth reporting to Prusa)
`flow_tower.lua` (shipped in com.prusa3d.slicer.calibration) passes `params=` on
its top-level `add_object`, so its intended `fill_density="0%"`,
`top_solid_layers=0`, `bottom_solid_layers=0`, `perimeters=1` are silently
discarded. `temp_tower.lua` uses `object_params=` and works.

### S3 — brim_type: log error is a red herring (verified by screenshot)
log.txt carries three lines from our bundle:

    [error][ProjectApi.cpp:250] Cannot set volume settings 'brim_type': not found

I initially read that as a rejection. **It is not.** A screenshot of the 25 mm
cube's overrides shows all five applied:

    Layer height  0.3 mm
    Perimeters    6
    Fill density  55 %
    Fill pattern  Gyroid
    Brim type     Outer brim only

The message says *volume* settings; `object_params` writes at **object** scope.
PrusaSlicer apparently also attempts a volume-scope write, which fails harmlessly
for a print-level key like `brim_type` and gets logged. The object-scope write
succeeds.

- **All five keys are writable via `object_params`**, including two enum strings
  (`fill_pattern`, `brim_type`) and a percentage (`fill_density`) — all three of
  which the unofficial docs claimed `ConfigBox:set` could not write.
- Spec §5.2's settings list needs no reduction.
- Verified at BOTH the Part and Object coordinate scopes — the same five values
  show under each.
- Lesson for the generator's dev-time validation: an error in log.txt does NOT
  imply a failed operation. Verify against the UI, not the log.

### Alpha11 crash observed (upstream bug)
    [21:53:47][error][Assert.cpp:16] Panic at ConfigItemPreview.cpp:50:
      All gui types must be explicitly handled here, you apparently missed one.
    (stack: OverrideItemPreviewRow::on_data_update -> OverrideSettingsDialog)
PrusaSlicer hard-panicked while rendering the per-object override list, then
restarted at 21:54:01. Most likely trigger: the `fill_pattern` enum override —
alpha11's settings-preview UI has no handler for that gui type.
Consequence: enum overrides can crash the object-settings panel on this build.
Prefer numeric/percentage overrides until alpha12; keep `fill_pattern` behind a
flag or drop it.

### Incidental
- `PhysicalPrinterStorage.cpp:58 Failed to load Physical Printer Configurations:
  No such file or directory` — subsystem present, no config yet. Relevant to M5.
- `FontUtils.cpp:186 Can not process font ... not valid TTF` — unrelated to the
  spike (font enumeration for emboss).

## S7 — stamp, flat asset load, first_layer_height (partial)
- Objects appeared: **2** → `api.load_stl("probe.stl")` with a FLAT bundle asset
  works. Confirms the flat bundle layout (spec §5.1); no subdirectory needed.
- Both objects landed **centred on the bed, stacked on each other** — same as the
  S3 cubes. Confirms §2's note that `add_object` auto-centres in X/Y, and that a
  per-object `translate` does NOT place separate objects apart.
- `first_layer_height` returns:

      S7 first_layer_height ok=true type=userdata
        value=sol.Slic3r::Domain::FloatOrPercentage: 0xbd48b5898

  Opaque userdata, not a number — matches the known-limitations note that
  ConfigBox:value returns opaque values for float-or-percentage types. The
  probe's `type(v) == "number"` guard correctly fell through to the 0.2 default.

### Consequences
1. **Stamp Z must not come from `first_layer_height`.** Use `layer_height`
   instead — Prusa's `temp_tower.lua` does `local layer_height =
   bed:print_presets():value("layer_height")` and then uses it in arithmetic, so
   it is a plain number. Update `printernizer_lib.lua` in spec §5.3: drop the
   `first_layer_height` read and its fallback chain, read `layer_height`, keep a
   0.2 constant as the last resort.
2. **Multi-object 3MF handling in §5.6 is wrong as written.** It says each object
   becomes its own `add_object`. Because every `add_object` auto-centres, N
   objects from one 3MF would all stack at the bed centre instead of keeping
   their arrangement. Fix: emit **one** `add_object` whose extra parts are passed
   as `other_volumes`, each with its own `translate` — exactly the pattern
   `temp_tower.lua` uses. Relative placement is preserved that way.
- Sliced OK (2.33 g, 8m 35s). **Legend lists a "Custom" feature type in green and
  green geometry is visible on the plate** → the injected custom G-code IS present
  in the sliced result.
- PrusaSlicer raised: *"Conflicts in G-code paths have been detected at print
  height 0.20 mm. Please reposition the conflicting objects."* This is the
  auto-centring problem made visible — the two objects were placed on top of each
  other. Direct confirmation that the §5.6 fix (one add_object + other_volumes) is
  required, not optional.
- Incidental: the right panel offers **Prusa Connect** as a send destination, so
  the print-host stack is live in alpha11 (relevant to M5).

### S7 Q4/Q5 — stamp does NOT survive export  ★ NEGATIVE
Export was ASCII text (binary G-code correctly off). Verified independently by
the controller on the actual files:

    grep -c -i printernizer ~/spike-s7.gcode   -> 0
    grep -c -iE 'spike123|BUSINESS'            -> 0
    unzip -p ~/spike-s7.3mf '*' | grep -c PRINTERNIZER -> 0   (user + controller)

- The 345 KB G-code contains exactly two `;TYPE:Custom` blocks, at lines 1961 and
  9210: the printer's **start** gcode (`M17 ; enable steppers`, nozzle check) and
  its **end** gcode (`; Filament-specific end gcode`). Neither is ours.
- **Correction:** the green "Custom" entry in the sliced-preview Legend was those
  start/end blocks, not our injection. Reading the legend as evidence of our stamp
  was wrong.
- Layer 1 sits at `;LAYER_CHANGE / ;Z:0.2 / ;HEIGHT:0.2` (line 2055) and runs
  straight into `;TYPE:Perimeter` — nothing injected.
- The saved 3MF has no custom-gcode structure at all in
  `Metadata/PrusaSlicer3_project.json`.

### Hypothesis under test (probe S7b)
The probe injected at **z = 0.2, the first layer** — where there is no layer
*change* to hang gcode on, since the start gcode covers that transition. Prusa's
shipped `temp_tower.lua` uses the same call successfully at stacked mid-object
heights, and its Temperature Tower really does emit M104s. So the likely finding
is "the first layer is a dead spot", not "insert_layer_custom_gcode is broken".
`s7b_stamp_midheight.lua` injects at three heights (layer_height, z=2, z=5) on a
10 mm cube to find where it sticks.

## S7b — mid-height stamp probe
- Terminal: `S7b layer_height type=number value=0.2`
  → **`layer_height` IS a plain Lua number.** Confirms the §5.3 fix: read
  `layer_height` (numeric), never `first_layer_height` (opaque userdata).
- Command appeared and ran after installing the new .lua into an already-running
  PrusaSlicer (see S2 for whether that needed Rescan or a restart).

### S7b result — hypothesis REFUTED, stamping does not work at any height
`~/spike-s7b.gcode` (294 KB, ASCII): `grep -ciE "printernizer|_AT="` → **0**.
Only two `;TYPE:Custom` blocks (lines 1950, 6696) — the printer's start and end
gcode again.

Both target heights are genuine layer boundaries, and both carry the layer-change
hooks where custom gcode would appear:

    ;LAYER_CHANGE / ;Z:2 / ;HEIGHT:0.2 / ;BEFORE_LAYER_CHANGE ... ;AFTER_LAYER_CHANGE
    ;LAYER_CHANGE / ;Z:5 / ;HEIGHT:0.2 / ;BEFORE_LAYER_CHANGE ... ;AFTER_LAYER_CHANGE

Nothing from the plugin at either. (The `;2` / `;5` inside those blocks are the
printer preset's own before-layer-change gcode, i.e. `;[layer_num]` — so the
layer-change mechanism itself works fine; it is the plugin API's insert that never
reaches output.)

**Verdict: `api.project:insert_layer_custom_gcode()` produces no output in
exported G-code on 3.0.0-alpha11, at first layer or mid-object.**

Caveat on strength: this shows it does not survive the ordinary
add-object → slice → export flow (with Auto-reslice on). It does not prove no
sequence exists that would work. But the design cannot depend on a mechanism that
fails the normal path.

### Consequences — provenance stamping is CUT from the design
- **Spec §5.4 `tag_project.lua`: remove.** Its whole purpose was stamping.
- **Spec §5.3 `M.stamp()`: remove**, and drop the `tag` bool param from the
  generated per-model commands in §5.2.
- **Spec §8.3 "Ingest stamps": remove from M1/M3 scope.** The G-code analyzer has
  no `; PRINTERNIZER_*` comments to find.
- **M3 shrinks to the hook alone.** Provenance now comes only from what the
  post-processing hook captures from `SLIC3R_*` env vars at export time, which
  means it works **only for exports that go through the companion**. A file that
  reaches the printer by SD card or Prusa Connect carries no link back to its
  library entry — exactly the case §8.3 was designed to cover.
- Revisit if a later alpha fixes it; the community roadmap lists a post-slice hook
  as wanted-but-absent, so Prusa may address this area.

## S2 — rescan without restart  ★ POSITIVE
- A new `.lua` copied into an already-running PrusaSlicer's bundle directory
  appeared after **Plugins ▸ Rescan Plugins**. **No restart required.**
- Consequence: spec §5.7's closing line stands as written — `sync` tells the user
  "Open PrusaSlicer ▸ Plugins ▸ Rescan Plugins to see the changes", not "restart
  PrusaSlicer". Materially better UX for a library that refreshes often.

## S3b — user preset location and format  ★ INVALIDATES THE M4 DESIGN
Saved a custom print preset "Spike Test" via the GUI. Result:

    presets/user/prusa-research-fff/PrusaResearch/print-Spike Test.yaml

```yaml
kind: print
id: 9b25b0f9-247b-49a1-acb0-b3337f41ea83
variants:
  - condition: (((((printer.base_model != "XL") and (tool.nozzle_diameter == 0.4)) and (printer.model =~ /(COREONE|COREONEOAK)/)) and tool.nozzle_high_flow) and not (printer.base_model == "MK3"))
    id: 534c6a47-5265-4a48-9582-776d8d9da137
    name: Spike Test
    unconditional_inherits:
      - VV9Gi9wpQrS5etKWhPj8ag
    features:
      based_id: VV9Gi9wpQrS5etKWhPj8ag
      based_root_id: idf14OqbR4+gNca1bDiZIw
```

Four structural facts, each of which breaks an assumption in the spec:

1. **YAML, not INI.** §4.1's `ini.py`, §7's `import-ini` endpoint and §8.4's "existing
   PrusaSlicer ini parser" do not apply to 3.0 at all.
2. **Vendor-scoped path**, not a flat `print/` directory:
   `presets/user/<vendor>/<bundle>/<kind>-<name>.yaml`.
3. **A preset is a DELTA, not a full document.** The saved file is 11 lines and
   contains no `values:` block whatsoever, because nothing was overridden. Actual
   settings live in a `values:` map (flat key → value, as in the vendor
   `preset-print-common.yaml`) and only overridden keys appear.
4. **Inheritance is by OPAQUE ID, not by name** — `unconditional_inherits:
   [VV9Gi9wpQrS5etKWhPj8ag]`, plus `features.based_id` / `based_root_id`. And each
   preset carries **variants gated by condition expressions** over printer model,
   nozzle diameter and hardware features.

### Consequence for M4 — redesign required, do not port the INI plan
Copying a preset file between machines only works if the target resolves the same
opaque base IDs, which depend on the installed vendor bundle **and its version**
(this machine: PrusaResearch 1.0.14, with 1.0.16 available). A naive file-level
sync will produce presets that reference bases the target does not have.

M4 must therefore either (a) sync only the resolved `values:` map and rebuild the
delta against whatever base exists locally, or (b) sync files plus a vendor-bundle
version check that refuses on mismatch. That is a materially different design from
the INI-era plan and needs its own brainstorm before any plan is written.

## S8 — post-processing scripts  ★ NEGATIVE, AND STRATEGICALLY DECISIVE

### Not exposed in the UI
Print Settings → Output options contains exactly ONE setting ("Output filename
format"). In 2.x this page also carries Post-processing scripts. No vendor preset
in the shipped bundle mentions `post_process` either.

### The key is still real, and is accepted
Set directly in the user preset YAML. First attempt used a scalar string and was
rejected with a precise, useful error:

    [error][PresetEvaluator.cpp:181] Type mismatched for item post_process:
      source type: std::string  dest type: std::vector<std::string>

So `post_process` expects a LIST. Corrected to YAML list syntax, restarted, and
PrusaSlicer accepted it — no new type error, and the exported G-code footer proves
it was loaded and carried all the way through slicing:

    ;       "post_process": ["/Users/.../postprocess_probe.sh"],
    ; post_process = /Users/.../postprocess_probe.sh

### But it is never executed
`~/printernizer-spike-postprocess.txt` was not created. Ruled out on our side: the
script is `-rwxr-xr-x`, has `#!/bin/sh`, and writes the file correctly when invoked
by hand with the same argument.

**Verdict: in 3.0.0-alpha11, `post_process` is configured, validated, and
serialised into output — but never run. The config plumbing survives; the
execution does not. The feature is unported.**

### Consequences — this reshapes the roadmap
1. **M3's post-processing hook does not work on PrusaSlicer 3.0.** The entire push
   mechanism in spec §6 is inert on alpha11.
2. **Combined with S7 (stamping also produces nothing), Printernizer Connect has NO
   automatic push path on 3.0 whatsoever.** Both channels the design relied on are
   dead on this build.
3. **M5 (the OctoPrint-compatible shim) is promoted from "optional" to the only
   viable push mechanism on 3.0.** The print-host stack IS live in alpha11 — the
   binary carries `physical_printer` / `print_host` / `host_type` / `octoprint` /
   `prusalink`, and the UI offers a "Send to Connect" destination — so
   "Send to printer" is the path that actually exists.
4. The hook design is not wasted: post-processing works in PrusaSlicer 2.9, so M3
   remains valid for 2.x users. It should be re-scoped as "2.x today, 3.x when
   Prusa ports it" rather than the primary channel.
5. Re-test on each new alpha. This is plumbing that already half-exists, so it is
   plausible Prusa finishes it before 3.0 ships.

### Incidental: the useful error channel
Unlike a bad `params=` key (silent), preset type errors ARE logged with the exact
expected type. `printernizer-connect` should tail `shared_runtime/log.txt` during
`setup`/`doctor` to validate what it writes.
