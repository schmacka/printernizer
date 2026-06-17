# Model Generator (build123d)

The model generator produces parametric, 3D-printable models from bundled
templates and saves the results into the Library for slicing/printing.

It is built on [build123d](https://build123d.readthedocs.io/), a pure-Python CAD
library on top of OpenCascade. Models are defined as Python templates and
rendered to STL **in-process** — there is no external CAD binary.

## Availability

build123d requires **glibc + x86_64 (amd64)**. It cannot be installed on Linux
ARM: its pinned `cadquery-ocp` 7.8.x has no linux-arm64 wheel (the arm64-capable
7.9.x is pinned out), and build123d imports `lib3mf`, which also has no
linux-arm64 wheel. There is no musllinux (Alpine) build either.

- **Standalone Docker** and the **Home Assistant add-on** use a Debian (glibc)
  base; the generator is available on **amd64** hosts.
- On **aarch64 / armv7** Home Assistant hosts (e.g. Raspberry Pi) the generator
  is **unavailable** — everything else in the add-on works normally.
- **Local development**: `pip install -r requirements.txt` on an x86_64 glibc
  Linux (or macOS) host.

When build123d cannot be imported the generator degrades gracefully: the API
reports `available: false` and the navigation entry stays hidden.

## Templates

Each bundled template lives in `src/build123d_templates/` as a pair:

- `<id>.py` — a module exposing `build(**params)` that returns a build123d shape.
- `<id>.json` — a sidecar describing the template metadata and parameters
  (`name`, `type`, `min`/`max`/`step`, `default`, `group`, `options`).

Bundled templates ship with the app: `box` (parametric box) and `vase`
(parametric vase). Templates are **not** uploadable, because build123d templates
are executable Python — running uploaded code would be a remote-code-execution
risk.

### Adding a template

1. Create `src/build123d_templates/my_thing.py` with a `build(**params)` function.
2. Create `src/build123d_templates/my_thing.json` describing its parameters.
3. Restart — the template is auto-discovered.

## API

Base path: `/api/v1/generator`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/status` | Engine availability |
| GET | `/templates` | List templates + parameter schemas |
| GET | `/templates/{id}` | Single template schema |
| POST | `/render` | Render `{template_id, parameters, format}` → STL (+ best-effort PNG) |
| GET | `/render/{id}/model.stl` | Download rendered STL |
| GET | `/render/{id}/preview.png` | Preview thumbnail (if produced) |
| POST | `/render/{id}/save` | Save the STL into the Library |
| GET/POST/DELETE | `/presets` | Manage saved parameter presets |

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `GENERATOR_OUTPUT_DIR` | `/data/printernizer/generator` | Working files and render artifacts |
| `GENERATOR_RENDER_TIMEOUT` | `120` | Per-render timeout (seconds) |

PNG thumbnails reuse the optional matplotlib preview pipeline and degrade
gracefully when matplotlib is absent.
