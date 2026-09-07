# PrusaSlicer 3.0.0-alpha11 spike — findings

**Run:** 2026-09-07 · **Build:** PrusaSlicer-3.0.0-alpha11 (macOS)
**Data dir:** `~/Library/Application Support/PrusaSlicer3-dev`
**Raw evidence:** [ANSWERS.md](ANSWERS.md) · **Plan:** [M0 spike plan](../../plans/2026-09-06-connect-m0-spike.md)

---

## Summary

| # | Question | Result |
|---|---|---|
| S0 | Does a copied bundle register? | ✅ yes |
| S2 | Rescan without restarting? | ✅ **yes** — `Plugins ▸ Rescan Plugins` picks up new command files |
| S3 | `params` or `object_params`? | ✅ **`object_params`** — all five keys apply; `params` is silently ignored |
| S4 | Menu ordering | ✅ **alphabetical**, not scan order |
| S5 | Long dialog titles | ✅ full 88 characters render |
| S7 | Provenance stamping | ❌ **emits nothing**, at any height |
| S8 | Post-processing hook | ❌ **accepted and serialised, never executed** |
| S3b | User preset format | ⚠️ **YAML deltas with opaque inheritance IDs** |

**The headline:** S7 and S8 fail together, and they were the design's only two
provenance/push channels. **Printernizer Connect has no automatic push path on
PrusaSlicer 3.0.** M2 (library in the slicer) is unaffected and remains buildable.

---

## S2 — Rescan works · POSITIVE

A `.lua` copied into a running PrusaSlicer's bundle directory appeared after
**Plugins ▸ Rescan Plugins**; no restart needed.

**Consequence:** spec §5.7 stands. `sync` ends with "open Plugins ▸ Rescan Plugins",
not "restart PrusaSlicer" — materially better for a library that refreshes often.

## S3 — `object_params` is the working key · POSITIVE

Two probes, identical but for the key. `params` → object added, **zero** settings
applied, **no error anywhere**. `object_params` → all five applied, confirmed by
screenshot at both Part and Object scope:

```
layer_height 0.3 · perimeters 6 · fill_density 55 % · fill_pattern Gyroid · brim_type Outer brim only
```

Two enum strings and a percentage all wrote — contradicting the unofficial docs'
claim that `ConfigBox:set` cannot write strings.

A `Cannot set volume settings 'brim_type': not found` line in `log.txt` is a red
herring: it reports a failed *volume*-scope attempt while the *object*-scope write
succeeded. **A logged error here does not imply a failed operation.**

**Consequences:** §5.2/§5.3 emit `object_params` only — drop the "set both keys"
hedge. Settings list needs no reduction.

**Upstream bug:** Prusa's shipped `flow_tower.lua` passes `params=` on its
top-level `add_object`, so its intended `fill_density="0%"`, `top_solid_layers=0`,
`perimeters=1` are silently discarded. `temp_tower.lua` uses `object_params=` and
works. Worth reporting.

## S4 — alphabetical ordering · POSITIVE

Files created zeta → mike → alpha display as alpha, mike, zeta.

**Consequence:** ordering is predictable and therefore controllable. The generator
must prefix menu labels with zero-padded ordinals wherever a non-alphabetical order
matters (the "Recent" group, which should read newest-first).

## S5 — long titles render · POSITIVE

The full 88-character title and both checkbox labels render without truncation.

**Consequence:** the "detail card" title in §5.2 works as designed — name, size,
layer height, print time and last-printed printer all fit. This matters because the
title is the *only* detail surface the API offers; there is no image support.

## S7 — stamping produces nothing · NEGATIVE

`api.project:insert_layer_custom_gcode()` was called at the first layer, then at
z=2 and z=5 on a 10 mm cube. In every case the exported G-code contains **zero**
occurrences of the injected text, and the saved 3MF has no custom-gcode structure
at all.

Both target heights are genuine layer boundaries carrying `;BEFORE_LAYER_CHANGE` /
`;AFTER_LAYER_CHANGE` hooks — exactly where such gcode belongs. The only
`;TYPE:Custom` blocks in the file are the printer's own start and end gcode.

*(An earlier reading of the sliced-preview Legend as evidence of our stamp was
wrong — that green "Custom" entry was the start/end gcode.)*

**Consequences — provenance stamping is CUT:**
- §5.4 `tag_project.lua` — **remove**
- §5.3 `M.stamp()` — **remove**; drop the `tag` bool from generated commands in §5.2
- §8.3 "Ingest stamps" — **remove from scope**; there are no `; PRINTERNIZER_*`
  comments for the analyzer to find

**Caveat:** this shows it does not survive the ordinary add-object → slice → export
flow. It does not prove no sequence works. But the design cannot rely on a
mechanism that fails the normal path.

## S8 — post-processing accepted but not executed · NEGATIVE

Three layers of evidence:

1. **Not in the UI.** Print Settings → Output options holds exactly one setting
   ("Output filename format"). In 2.x this page also carries Post-processing
   scripts. No shipped vendor preset mentions `post_process`.
2. **The key is real and is accepted.** Setting it as a scalar in the user preset
   YAML produced a precise rejection:
   ```
   Type mismatched for item post_process:
     source type: std::string   dest type: std::vector<std::string>
   ```
   Corrected to a YAML list and restarted, PrusaSlicer accepted it with no error
   and carried it end-to-end — the exported footer proves it:
   ```
   ;       "post_process": ["/Users/.../postprocess_probe.sh"],
   ; post_process = /Users/.../postprocess_probe.sh
   ```
3. **It never runs.** The probe's output file was never created. Ruled out on our
   side: the script is `-rwxr-xr-x`, has `#!/bin/sh`, and writes correctly when
   invoked by hand with the same argument.

**Verdict: the config plumbing survives; the execution does not. Unported, not
broken** — which makes it plausible Prusa finishes it before 3.0 ships.

**Consequences:**
- §6's post-processing hook is **inert on 3.0**. It remains valid for 2.9.
- With S7 also failing, **there is no automatic push path on 3.0 at all**.
- **M5 (OctoPrint shim) is promoted from optional to the only viable push
  mechanism on 3.0.** The print-host stack is live: the binary carries
  `physical_printer`, `print_host`, `host_type`, `octoprint`, `prusalink`, and the
  UI offers a send destination.
- Re-test on each new alpha.

## S3b — preset format · INVALIDATES M4

A GUI-saved print preset lands at
`presets/user/prusa-research-fff/PrusaResearch/print-Spike Test.yaml`:

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

Four structural facts, each breaking a spec assumption:

1. **YAML, not INI** — §4.1's `ini.py`, §7's `import-ini`, §8.4's "existing ini
   parser" do not apply to 3.0.
2. **Vendor-scoped path** — `presets/user/<vendor>/<bundle>/<kind>-<name>.yaml`,
   not a flat `print/` directory.
3. **A preset is a DELTA** — 11 lines, no `values:` block at all, because nothing
   was overridden. Settings live in a flat `values:` map; only overrides appear.
4. **Inheritance is by opaque ID**, not name, with **variants gated by condition
   expressions** over printer model, nozzle diameter and hardware features.

**Consequence — M4 needs a fresh brainstorm, not a port.** Copying a preset file
between machines only works if the target resolves the same opaque base IDs, which
depend on the installed vendor bundle *and its version* (this machine:
PrusaResearch 1.0.14, 1.0.16 available). M4 must either sync the resolved `values:`
map and rebuild the delta locally, or sync files behind a bundle-version check that
refuses on mismatch.

---

## Incidental findings

- **Objects auto-centre, and `translate` does not separate them.** Two objects from
  one command stacked at the bed centre and PrusaSlicer raised *"Conflicts in G-code
  paths detected at print height 0.20 mm."* §5.6 says a multi-object 3MF becomes one
  `add_object` per object — that would collapse every part into a stack. **Fix: one
  `add_object` with the rest as `other_volumes`, each with its own `translate`** —
  the pattern `temp_tower.lua` uses.
- **`first_layer_height` is opaque userdata** (`FloatOrPercentage`), unusable as a
  number. **`layer_height` is a plain number** (`type=number value=0.2`). §5.3 must
  read `layer_height`.
- **alpha11 crash:** `Panic at ConfigItemPreview.cpp:50: All gui types must be
  explicitly handled here` while rendering the per-object override list — likely the
  `fill_pattern` enum. PrusaSlicer hard-restarted. Enum overrides can crash the
  settings panel on this build.
- **Errors are logged with exact expected types** (unlike a bad `params=` key, which
  is silent). `printernizer-connect` should tail `shared_runtime/log.txt` during
  `setup`/`doctor` to validate what it writes.
- `Failed to load Physical Printer Configurations: No such file or directory` —
  subsystem present, no config yet. Relevant to M5.

## Cleanup still owed on the test machine

- Delete the `Spike Test` print preset (it still carries `post_process`), or remove
  that key. Backup at `print-Spike Test.yaml.bak`.
- `rm -rf "$HOME/Library/Application Support/PrusaSlicer3-dev/lua/com.printernizer.spike"`
- Stray exports: `~/spike-s7.gcode`, `~/spike-s7.3mf`, `~/spike-s7b.gcode`,
  `~/Downloads/spike-s8.gcode`
