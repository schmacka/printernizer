# Model Generator (browser-side / JSCAD)

The model generator produces parametric, 3D-printable models from bundled
templates and saves the results into the Library for slicing/printing.

Geometry is generated **entirely in the browser** with
[JSCAD](https://openjscad.xyz/) and shown in a three.js viewer. The finished STL
is uploaded to the server only to be stored in the Library. **Nothing CAD-related
runs on the server**, so the feature works on every deployment architecture —
including Raspberry Pi (aarch64) and armv7 Home Assistant hosts.

> Why browser-side? Earlier server-side engines (OpenSCAD binary, then
> build123d/OpenCascade) could not be installed on ARM Linux — no `cadquery-ocp`
> or `lib3mf` wheels for aarch64. Moving generation to the client removes the
> dependency entirely and works everywhere.

## How it works

1. The browser loads `@jscad/modeling` + `@jscad/stl-serializer` (ES modules).
2. A bundled template's `build(params)` produces JSCAD geometry from the
   parameter form.
3. The geometry is rendered in the three.js viewer (orbit to inspect).
4. **Save to Library** serializes the geometry to a binary STL and POSTs it to
   `POST /api/v1/generator/save`, which stores it via the Library.

## Templates

Templates live in the frontend (`frontend/js/generator.js`) as JSCAD build
functions plus a parameter schema (`name`, `type`, `min`/`max`/`step`, `default`,
`group`). Bundled: **box** (parametric box) and **vase** (parametric vase with
taper/twist, a round-or-polygon surface, and a configurable inner diameter),
plus text, QR, Gridfinity, calibration and utility templates. Adding a template
is a small JS function + schema entry.

## API

Base path: `/api/v1/generator`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/status` | Always `{available: true, engine: "jscad"}` |
| POST | `/save` | Multipart STL upload (`file`, `template_id`, `parameters`, `display_name`) → Library |
| GET/POST/DELETE | `/presets` | Manage saved parameter presets |

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `GENERATOR_OUTPUT_DIR` | `/data/printernizer/generator` | Staging dir for uploaded STLs before Library import |

## Notes

- Requires a browser with WebAssembly + WebGL (any modern browser).
- The 3D viewer and JSCAD modules load from a CDN (jsDelivr), like the rest of
  the app's three.js usage.
