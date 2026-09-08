# PrusaSlicer 3.0 API spike — run-through

**Time:** ~30 minutes. Fill in every **Answer:** line — paste output verbatim rather
than summarising. Where a question asks for a count, count entries in the right-hand
object list, not shapes on the plate.

The bundle is already installed at
`~/Library/Application Support/PrusaSlicer3-dev/lua/com.printernizer.spike`.

---

## Setup

1. Quit PrusaSlicer completely if it is running.
2. Start it **from a terminal** so `print()` output is visible:
   ```sh
   /Applications/PrusaSlicer-3.0.0-alpha11.app/Contents/MacOS/PrusaSlicer
   ```
3. In a second terminal, tail the plugin log — scan and registration errors go here,
   **not** to stdout:
   ```sh
   tail -f "$HOME/Library/Application Support/PrusaSlicer3-dev/shared_runtime/log.txt"
   ```
4. Complete the configuration wizard if it appears (S3b needs it — there are currently
   no user presets). Pick a Prusa printer and accept the defaults.
5. **Turn off binary G-code:** Printer Settings → General → untick "Supports binary
   G-code". Core One profiles default it on, which makes the S7/S8 `grep`s useless.
   If you leave it on, say so in the answers.

---

## S0 — does the bundle register at all?

Open the **Plugins** menu.

- Is there a `Spike` submenu? **Answer:** ___
- List every entry under it. **Answer:** ___

> If `Spike` is missing, the bundle failed to register. Check `log.txt` for a
> `PluginBundle.cpp` line naming the offending file, paste it here, and stop.
> (A Lua syntax error makes a command vanish silently. `brew install lua` then
> `luac -p bundle/*.lua` from this directory would catch it.)

---

## S4 — menu ordering

Look at `Plugins ▸ Spike ▸ S4 Order`. The files were created **zeta → mike → alpha**,
so creation order and alphabetical order differ.

- Order shown, top to bottom: **Answer:** ___
- Is that alphabetical, creation order, or something else? **Answer:** ___

*Why it matters: decides whether the generator must prefix menu labels with
zero-padded ordinals to control ordering.*

---

## S5 — long dialog title

Run `Plugins ▸ Spike ▸ S5 Long title`.

- Is the full 88-character title readable, truncated, or does it stretch the dialog
  off-screen? **Answer:** ___
- Do both checkbox labels render fully? **Answer:** ___
- Roughly how many characters of the title are visible? **Answer:** ___
- Screenshot it and save next to this file as `s5-dialog.png`.

*Why it matters: the title is the only "detail card" the API allows — there are no
thumbnails. If it truncates hard, the library entries need much shorter labels.*

Click Run, then **File ▸ New Project** to clear the plate.

---

## S3 — `params` vs `object_params`

Prusa's own plugins use both keys, inconsistently. This decides which one the
generator emits.

Run `Plugins ▸ Spike ▸ S3 Params`. Expect a 5 mm marker cube and a 20 mm cube.

- How many objects appeared? (1 = the settings call threw) **Answer:** ___
- Right-click the **20 mm** cube → its per-object settings (the gear entry in the
  object list). Which of these are present and set?
  `layer_height=0.3`, `fill_density=55%`, `perimeters=6`, `fill_pattern=gyroid`,
  `brim_type=outer_only` **Answer:** ___

**File ▸ New Project**, then run `Plugins ▸ Spike ▸ S3 Object params`. Expect a 5 mm
marker and a **25 mm** cube.

- How many objects appeared? **Answer:** ___
- Right-click the **25 mm** cube → same five keys. **Answer:** ___
- Anything in the terminal or `log.txt`? **Answer:** ___

Then **File ▸ New Project**.

---

## S7 — stamp, flat asset load, `first_layer_height`

Run `Plugins ▸ Spike ▸ S7 Stamp`.

- How many objects appear? (2 = `load_stl` of a flat asset works; 1 = it failed)
  **Answer:** ___
- Paste the terminal line starting `S7 first_layer_height`: **Answer:** ___
- Slice the plate. Does the layer slider show a custom-G-code marker near the first
  layer? **Answer:** ___
- Export G-code to `~/spike-s7.gcode`, then run:
  ```sh
  file ~/spike-s7.gcode && grep -na PRINTERNIZER ~/spike-s7.gcode
  ```
  Paste the output. (If `file` says binary, binary G-code is still on — see Setup 5.)
  **Answer:** ___
- Save the project as `~/spike-s7.3mf`, then:
  ```sh
  unzip -p ~/spike-s7.3mf '*' 2>/dev/null | grep -c PRINTERNIZER
  ```
  **Answer:** ___

*Why it matters: if the stamp does not survive export, the whole provenance design
(M3) is cut and `tag_project.lua` disappears.*

Then **File ▸ New Project**.

---

## S2 — rescan without restart

Leave PrusaSlicer **running**. In a terminal:

```sh
cd ~/Developer/printernizer/docs/superpowers/spikes/2026-09-06-prusaslicer-api
cp s2_added_later.lua "$HOME/Library/Application Support/PrusaSlicer3-dev/lua/com.printernizer.spike/"
```

- Does `Plugins ▸ Spike ▸ S2 Added later` appear **without** any action?
  **Answer:** ___
- Is there a `Plugins ▸ Rescan Plugins` item? What is it called exactly?
  **Answer:** ___
- After clicking it, does the new entry appear? **Answer:** ___
- Now edit the installed `s7_stamp.lua` — change `spike123` to `spike456` — and run
  `S7 Stamp` again **without** rescanning. Does the exported G-code say `spike456`?
  (Tests whether execution code is re-read per run.) **Answer:** ___

*Why it matters: decides whether `printernizer-connect sync` can say "Rescan Plugins"
or has to say "restart PrusaSlicer".*

---

## S8 — post-processing environment

1. Print Settings → Output options → **Post-processing scripts**. Enter, in quotes:
   ```
   "/Users/sebastianseubert/Developer/printernizer/docs/superpowers/spikes/2026-09-06-prusaslicer-api/postprocess_probe.sh"
   ```
2. Save the print preset under a custom name starting with `Spike ` (this also serves S3b).
3. Slice and export G-code to `~/spike-s8.gcode`.

- Did the export succeed without an error dialog? **Answer:** ___
- Run `cat ~/printernizer-spike-postprocess.txt` and paste the whole `SLIC3R_*`
  block. **Answer:** ___
- Is `SLIC3R_PRINT_HOST` present? **Answer:** ___
- Is `SLIC3R_PP_OUTPUT_NAME` present? **Answer:** ___
- Is `ARGV1` the path to the G-code file? **Answer:** ___
- Is `ARGV1` the **final export path**, or a temp file PrusaSlicer moves afterwards?
  (Compare the `ARGV1=` line against `~/spike-s8.gcode`.) M3's uploader depends on
  this. **Answer:** ___
- What does the `file "$1"` line say — ASCII text or binary? **Answer:** ___

---

## S3b — where do user presets land, and in what format?

You saved a custom print preset in S8. Now also save a custom **filament** preset and
a custom **printer** preset (change any value, click the save icon, name each starting
with `Spike `).

> **Heads-up:** the vendor presets shipped with alpha11 are **YAML**, not INI —
> `presets/local/prusa-research-fff/PrusaResearch/` holds ~326 `preset-*.yaml` files
> with `kind:` / `inherits:` / `values:` keys. User presets are very likely YAML too.
> The spec still assumes INI in §4.1, §7 and §8.4; this question settles it and M4
> gets designed afterwards, not before.

```sh
D="$HOME/Library/Application Support/PrusaSlicer3-dev"
find "$D/presets/user" -type f | head -40
```

- Paste the output. **Answer:** ___
- Pick one preset you saved and paste its first 20 lines (`head -20 <path>`).
  **Answer:** ___
- Is the format YAML, INI, or JSON? **Answer:** ___
- Does a saved user preset record its parent via an `inherits:` key? **Answer:** ___
- Is there a `physical_printer` directory or key anywhere under `$D`?
  (`find "$D" -iname '*physical*'`) **Answer:** ___

---

## Cleanup

```sh
rm -rf "$HOME/Library/Application Support/PrusaSlicer3-dev/lua/com.printernizer.spike"
```

Remove the post-processing script from the print preset. **Leave the custom presets** —
M4 will want them.

---

When you're done, paste the filled-in answers back and I'll write `FINDINGS.md` and
fold each consequence into the spec.
