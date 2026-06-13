# OpenSCAD Model Generator

The generator module turns parametric [OpenSCAD](https://openscad.org/) scripts
into printable models. It renders STL geometry and PNG previews, shows results
in an interactive 3D viewer, and hands finished models to the Library so they
flow straight into slicing and printing.

There are two ways to use it:

1. **Bundled generators** — curated templates (e.g. *Parametric Vase*,
   *Parametric Box*) with friendly forms.
2. **Upload any `.scad` file** — parameters are auto-discovered and rendered.

## Requirements

OpenSCAD is an **optional dependency**. The module auto-detects the binary at
startup:

- If OpenSCAD is found, the **Generator** entry appears in the navigation.
- If not, the module is disabled and the nav entry is hidden — the rest of the
  app is unaffected.

Install OpenSCAD:

```bash
# Debian/Ubuntu (incl. Raspberry Pi / Docker base images)
apt-get install -y openscad

# For PNG previews on a headless host, also install xvfb
apt-get install -y xvfb
```

STL rendering runs headless out of the box. PNG previews need an X server, so on
headless hosts the service automatically wraps OpenSCAD with `xvfb-run` when it
is available.

### Configuration

| Environment variable | Default | Description |
|----------------------|---------|-------------|
| `OPENSCAD_BINARY_PATH` | _(auto-detect on `PATH`)_ | Explicit path to the OpenSCAD binary. |
| `OPENSCAD_RENDER_TIMEOUT` | `120` | Max seconds for a single render. |
| `OPENSCAD_MAX_OUTPUT_MB` | `100` | Max size of a render artifact (guards against runaway uploads). |
| `GENERATOR_OUTPUT_DIR` | `/data/printernizer/generator` | Working dir for uploads and render artifacts. |

## Parameters (Customizer syntax)

Parameters are top-level variables annotated with OpenSCAD's Customizer comment
syntax. The parser produces the form controls automatically:

```openscad
/* [Dimensions] */
// Total height in mm          <- description (line above)
height = 120;        // [40:300]      number slider (min:max)
wall = 2;            // [0.8:0.2:6]   number slider (min:step:max)

/* [Style] */
style = "smooth";    // [smooth, faceted, ribbed]   dropdown
sides = 6;           // [3, 6, 12, 24]               numeric dropdown
closed = true;                                       boolean checkbox

/* [Hidden] */
internal = 5;        // excluded from the form
```

Variables declared inside `module`/`function` bodies are ignored — only
top-level assignments become parameters, matching OpenSCAD's own Customizer.

## Adding a bundled generator

Drop two files into [`src/scad_templates/`](../src/scad_templates):

- `my_generator.scad` — the OpenSCAD source (using the Customizer syntax above).
- `my_generator.json` — optional metadata:

```json
{
  "name": "My Generator",
  "description": "What it makes",
  "category": "Containers",
  "default_camera": "0,0,60,60,0,30,420"
}
```

`default_camera` is the OpenSCAD `--camera` string
(`translate_x,translate_y,translate_z,rot_x,rot_y,rot_z,distance`) used for PNG
previews. The template is picked up automatically on startup.

## API

Base path: `/api/v1/generator`

| Method & path | Purpose |
|---------------|---------|
| `GET /status` | OpenSCAD availability + version |
| `GET /templates` | List bundled templates with parameter schemas |
| `GET /templates/{id}` | Template detail incl. source |
| `POST /parse` | Parse parameters from raw source `{ "source": "..." }` |
| `POST /upload` | Upload a `.scad` file (multipart) → id + schema |
| `POST /render` | Render `{ source_ref, parameters, format }` (`stl`/`png`) |
| `GET /render/{id}/model.stl` | Download STL artifact |
| `GET /render/{id}/preview.png` | Download PNG preview |
| `POST /render/{id}/save` | Save STL into the Library |
| `GET/POST /presets`, `DELETE /presets/{id}` | Manage parameter presets |

Render lifecycle events (`openscad.generation.started/completed/failed`) are
emitted over the existing WebSocket channel for live UI feedback.

## Security note

Uploaded `.scad` files are executed by OpenSCAD. OpenSCAD has no `system()`
call, but `import`/`include`/`use` can read files. The module applies a render
timeout, an output-size cap, and an isolated working directory per render as
best-effort sandboxing. Only allow uploads from trusted users.
