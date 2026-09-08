# Printernizer Connect M2 — Library in the Slicer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Printernizer model library browsable from inside PrusaSlicer — a navigable tree in the Plugins menu where clicking a model loads it onto the bed with its proven print settings.

**Architecture:** A new Python CLI (`printernizer-connect`) runs on the slicing machine. It talks to Printernizer over HTTP, mirrors a curated slice of the library into PrusaSlicer's own plugin directory, and generates **one Lua command file per model**. The Lua plugin itself is ~30 lines and knows nothing about Printernizer — it only loads files the CLI already put next to it. This is forced by the sandbox: plugins have no network access whatsoever.

**Tech Stack:** Python 3.11+, `httpx`, `typer`, `platformdirs`, `jinja2`, `trimesh` (3MF→STL), `pytest` + `httpx.MockTransport`. Lua 5.4 for the plugin (tested against a mock `api` in CI).

**Spec:** `docs/superpowers/specs/2026-09-06-printernizer-connect-design.md` — §4 (companion), §5 (pull), §11 (spike results). Read §5 in full before starting.

**Spike findings that shaped this plan:** `docs/superpowers/spikes/2026-09-06-prusaslicer-api/FINDINGS.md`

## Global Constraints

- **New repository:** `~/Developer/printernizer-connect`. Create it **locally only** — do not create a GitHub repo or push. That's the user's call, later.
- **Bundle layout is FLAT.** `manifest.json` plus `.lua` and `.stl` files at the bundle root, no subdirectories. Prusa's own plugins do this and subdirectory support is unverified.
- **Lua: never call `api` or `require` at file level.** Both are absent during the scan pass; the failure is silent and the command vanishes from the menu with no error. Everything goes inside `execute()`.
- **Per-object settings use `object_params=`, never `params=`.** Spike S3: a top-level `params=` is silently ignored. Prusa's own `flow_tower.lua` has this bug.
- **One `add_object` per model, extra parts as `other_volumes`.** Every `add_object` auto-centres on the bed, so N calls stack N parts on top of each other.
- **Dialog params: only `string`, `float`, `int`, `bool`.** No enum, no list, no tooltip. The menu path is the only hierarchy available.
- **No stamping, no post-processing hook in M2.** Both were cut/deferred by the spike (§5.4, §6). M2 is pull-only.
- **Test command:** `.venv/bin/python -m pytest` in the new repo (create its own venv).
- **Commits:** Conventional Commits. End every message with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. Never push.

## Live API facts — verified 2026-09-08 against the real server

The plan was written against `http://printernizer.local:8000` running **2.42.0** (M1 not yet deployed there). **19 files: 14 × 3mf, 4 × stl, 1 × gcode.**

**Three traps, each verified by probing the live API:**

1. **`file_type` is asymmetric.** The *filter* wants a leading dot (`?file_type=.stl` → 4 items); the *field* comes back without one (`"file_type": "stl"`). Querying `?file_type=stl` silently returns **zero** items — no error. Always send the dot; never compare the field to a dotted value.
2. **`tags` and `printer_model` are NOT in the list or detail response.** They are documented as query filters but never returned. Grouping by tag therefore needs one query per tag (`?tags=<id>`); grouping by printer is **not implementable** and is out of scope for M2.
3. **Nothing is tagged yet** — every tag reports `usage_count: 0`. So tag grouping produces nothing today; `recent` is the only grouping that yields a useful menu on this data.

Other confirmed fields on a library file: `checksum`, `filename`, `display_name`, `file_size`, `file_type`, `role` (`model` | `printfile`), `object_count`, `layer_height` (often `null`), `first_layer_height`, `infill_density`, `infill_pattern`, `total_layer_count`, `profile_name`, `slicer_name`, `model_width/depth/height`, `added_to_library`, `last_modified`, `sources`.

Endpoints M2 uses:
- `GET /api/v1/connect/info` — auth check + version gate (**M1; returns 404 until the server is on 2.43.0**)
- `GET /api/v1/library/files?file_type=.stl&limit=&page=&sort_by=&sort_order=` — listing
- `GET /api/v1/library/files/{checksum}/download` — bytes
- `GET /api/v1/tags` — tag list, for tag grouping

---

## File Structure

| File | Responsibility |
|---|---|
| `pyproject.toml` | Package metadata, deps, `printernizer-connect` console script |
| `src/printernizer_connect/config.py` | `config.toml` + `state.json` read/write, platformdirs paths |
| `src/printernizer_connect/client.py` | **The only module that speaks HTTP.** Typed calls, auth header, paging, streaming download |
| `src/printernizer_connect/prusaslicer/paths.py` | **The only module that knows PrusaSlicer's on-disk layout.** Datadir + lua dir discovery |
| `src/printernizer_connect/bundle/scope.py` | Which library entries to mirror; menu grouping |
| `src/printernizer_connect/bundle/convert.py` | 3MF/STL → per-part STL + offsets |
| `src/printernizer_connect/bundle/generator.py` | Render the bundle, validate invariants, atomic swap |
| `bundle_template/manifest.json` | Bundle metadata |
| `bundle_template/printernizer_lib.lua` | The only hand-written Lua (~30 lines) |
| `bundle_template/model_command.lua.j2` | Per-model command template |
| `src/printernizer_connect/cli.py` | `setup`, `doctor`, `sync` |

---

### Task 1: Repo scaffold, config module

**Files:**
- Create: `~/Developer/printernizer-connect/{pyproject.toml,.gitignore,README.md}`
- Create: `src/printernizer_connect/{__init__.py,config.py}`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `config_dir() -> Path`, `load_config() -> Config`, `save_config(Config)`, `load_state() -> dict`, `save_state(dict)`. `Config` is a dataclass with `server_url: str`, `api_key: str`, `datadir: str | None`, `sync_recent: int`, `sync_tags: list[str]`, `size_budget_mb: int`, `group_by: list[str]`.

- [ ] **Step 1: Create the repo**

```bash
mkdir -p ~/Developer/printernizer-connect/{src/printernizer_connect/{prusaslicer,bundle},bundle_template,tests}
cd ~/Developer/printernizer-connect && git init -q && git branch -m main
python3 -m venv .venv && .venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q httpx typer platformdirs jinja2 trimesh pytest
printf '.venv/\n__pycache__/\n*.egg-info/\n.pytest_cache/\ndist/\n' > .gitignore
touch src/printernizer_connect/__init__.py src/printernizer_connect/prusaslicer/__init__.py src/printernizer_connect/bundle/__init__.py
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "printernizer-connect"
version = "0.1.0"
description = "Browse your Printernizer model library from inside PrusaSlicer"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27", "typer>=0.12", "platformdirs>=4", "jinja2>=3.1", "trimesh>=4"]

[project.scripts]
printernizer-connect = "printernizer_connect.cli:app"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 3: Write the failing test**

`tests/test_config.py`:

```python
import tomllib
from printernizer_connect.config import Config, load_config, save_config, load_state, save_state


def test_roundtrip_preserves_every_field(tmp_path, monkeypatch):
    monkeypatch.setenv("PRINTERNIZER_CONNECT_CONFIG_DIR", str(tmp_path))
    original = Config(
        server_url="http://printernizer.local:8000",
        api_key="pk_secret",
        datadir="/tmp/ps",
        sync_recent=25,
        sync_tags=["prusaslicer"],
        size_budget_mb=1024,
        group_by=["recent"],
    )
    save_config(original)
    assert load_config() == original


def test_config_file_is_owner_only(tmp_path, monkeypatch):
    """It holds an API key; other users on the machine must not read it."""
    monkeypatch.setenv("PRINTERNIZER_CONNECT_CONFIG_DIR", str(tmp_path))
    save_config(Config(server_url="http://x", api_key="pk_secret"))
    assert oct((tmp_path / "config.toml").stat().st_mode)[-3:] == "600"


def test_missing_config_returns_defaults_not_an_error(tmp_path, monkeypatch):
    monkeypatch.setenv("PRINTERNIZER_CONNECT_CONFIG_DIR", str(tmp_path))
    cfg = load_config()
    assert cfg.server_url == "" and cfg.api_key == ""
    assert cfg.sync_recent == 25 and cfg.group_by == ["recent"]


def test_api_key_is_not_written_when_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("PRINTERNIZER_CONNECT_CONFIG_DIR", str(tmp_path))
    save_config(Config(server_url="http://x", api_key=""))
    assert "api_key" not in tomllib.loads((tmp_path / "config.toml").read_text())


def test_state_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("PRINTERNIZER_CONNECT_CONFIG_DIR", str(tmp_path))
    save_state({"last_sync": "2026-09-08T10:00:00Z", "entries": 12})
    assert load_state()["entries"] == 12


def test_missing_state_is_an_empty_dict(tmp_path, monkeypatch):
    monkeypatch.setenv("PRINTERNIZER_CONNECT_CONFIG_DIR", str(tmp_path))
    assert load_state() == {}
```

- [ ] **Step 4: Run it and confirm it fails**

```bash
cd ~/Developer/printernizer-connect && .venv/bin/python -m pytest tests/test_config.py -q
```
Expected: `ModuleNotFoundError: No module named 'printernizer_connect.config'`

- [ ] **Step 5: Implement `config.py`**

```python
"""Configuration and state for printernizer-connect.

The config file holds an API key, so it is written 0600. The
PRINTERNIZER_CONNECT_CONFIG_DIR environment variable overrides the location —
tests rely on it, and it lets a user keep the config elsewhere.
"""
import json
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_config_dir

APP = "printernizer-connect"


@dataclass
class Config:
    server_url: str = ""
    api_key: str = ""
    datadir: str | None = None
    sync_recent: int = 25
    sync_tags: list[str] = field(default_factory=list)
    size_budget_mb: int = 1024
    group_by: list[str] = field(default_factory=lambda: ["recent"])


def config_dir() -> Path:
    override = os.environ.get("PRINTERNIZER_CONNECT_CONFIG_DIR")
    path = Path(override) if override else Path(user_config_dir(APP))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _config_path() -> Path:
    return config_dir() / "config.toml"


def load_config() -> Config:
    path = _config_path()
    if not path.exists():
        return Config()
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    sync = raw.get("sync", {})
    return Config(
        server_url=raw.get("server_url", ""),
        api_key=raw.get("api_key", ""),
        datadir=raw.get("prusaslicer", {}).get("datadir") or None,
        sync_recent=sync.get("recent", 25),
        sync_tags=sync.get("tags", []),
        size_budget_mb=sync.get("size_budget_mb", 1024),
        group_by=sync.get("group_by", ["recent"]),
    )


def save_config(cfg: Config) -> None:
    lines = [f'server_url = "{cfg.server_url}"']
    if cfg.api_key:
        lines.append(f'api_key    = "{cfg.api_key}"')
    lines += ["", "[prusaslicer]", f'datadir = "{cfg.datadir or ""}"', "", "[sync]",
              f"recent         = {cfg.sync_recent}",
              f"tags           = {json.dumps(cfg.sync_tags)}",
              f"size_budget_mb = {cfg.size_budget_mb}",
              f"group_by       = {json.dumps(cfg.group_by)}", ""]
    path = _config_path()
    path.write_text("\n".join(lines), encoding="utf-8")
    path.chmod(0o600)


def load_state() -> dict:
    path = config_dir() / "state.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(state: dict) -> None:
    (config_dir() / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
```

- [ ] **Step 6: Run and confirm pass**

```bash
.venv/bin/python -m pytest tests/test_config.py -q
```
Expected: 6 passed.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat: Scaffold printernizer-connect with config and state

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: HTTP client

**Files:**
- Create: `src/printernizer_connect/client.py`
- Test: `tests/test_client.py`

**Interfaces:**
- Consumes: `Config` from Task 1.
- Produces: `Client(server_url: str, api_key: str)` with `info() -> dict`, `list_library(file_types: list[str], limit: int, sort_by: str = "created_at", tag: str | None = None) -> list[dict]`, `download(checksum: str, dest: Path) -> None`, `tags() -> list[dict]`. Raises `ConnectError(message: str)` on any failure.

- [ ] **Step 1: Write the failing test**

`tests/test_client.py`:

```python
import json
import httpx
import pytest
from printernizer_connect.client import Client, ConnectError


def make(handler) -> Client:
    c = Client("http://server:8000", "pk_test")
    c._http = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://server:8000")
    return c


def test_sends_the_api_key_header():
    seen = {}

    def handler(request):
        seen["key"] = request.headers.get("X-Api-Key")
        return httpx.Response(200, json={"data": {"server_version": "2.43.0"}})

    make(handler).info()
    assert seen["key"] == "pk_test"


def test_info_unwraps_the_data_envelope():
    handler = lambda r: httpx.Response(200, json={"status": "success", "data": {"server_version": "2.43.0"}})
    assert make(handler).info()["server_version"] == "2.43.0"


def test_404_on_info_says_the_server_is_too_old():
    """M1 landed in 2.43.0; older servers 404 here and the message must say so."""
    handler = lambda r: httpx.Response(404)
    with pytest.raises(ConnectError, match="2.43.0"):
        make(handler).info()


def test_401_says_the_key_is_wrong():
    handler = lambda r: httpx.Response(401, json={"message": "Invalid API key"})
    with pytest.raises(ConnectError, match="API key"):
        make(handler).info()


def test_list_library_sends_dotted_file_types():
    """The filter needs a leading dot; without it the server returns zero rows."""
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"files": [], "pagination": {"has_next": False}})

    make(handler).list_library([".stl"], limit=10)
    assert "file_type=.stl" in seen["url"]


def test_list_library_follows_pagination():
    pages = [
        {"files": [{"checksum": "a"}], "pagination": {"has_next": True}},
        {"files": [{"checksum": "b"}], "pagination": {"has_next": False}},
    ]
    calls = {"n": 0}

    def handler(request):
        body = pages[calls["n"]]
        calls["n"] += 1
        return httpx.Response(200, json=body)

    got = make(handler).list_library([".stl"], limit=100)
    assert [f["checksum"] for f in got] == ["a", "b"]


def test_list_library_stops_at_limit():
    handler = lambda r: httpx.Response(200, json={
        "files": [{"checksum": str(i)} for i in range(50)],
        "pagination": {"has_next": True}})
    assert len(make(handler).list_library([".stl"], limit=10)) == 10


def test_download_writes_the_bytes(tmp_path):
    handler = lambda r: httpx.Response(200, content=b"solid probe\nendsolid probe\n")
    dest = tmp_path / "m.stl"
    make(handler).download("abc", dest)
    assert dest.read_bytes().startswith(b"solid")


def test_download_does_not_leave_a_partial_file_on_error(tmp_path):
    handler = lambda r: httpx.Response(500)
    dest = tmp_path / "m.stl"
    with pytest.raises(ConnectError):
        make(handler).download("abc", dest)
    assert not dest.exists()
```

- [ ] **Step 2: Run and confirm it fails**

```bash
.venv/bin/python -m pytest tests/test_client.py -q
```
Expected: `ModuleNotFoundError: No module named 'printernizer_connect.client'`

- [ ] **Step 3: Implement `client.py`**

```python
"""The only module that speaks HTTP to Printernizer.

Everything else takes a Client instance, which is what makes the rest of the
package testable against httpx.MockTransport.
"""
from pathlib import Path

import httpx

API = "/api/v1"


class ConnectError(Exception):
    """Anything that stops us talking to Printernizer. Message is user-facing."""


class Client:
    def __init__(self, server_url: str, api_key: str, timeout: float = 15.0):
        self.server_url = server_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self.server_url,
            headers={"X-Api-Key": api_key},
            timeout=httpx.Timeout(timeout, connect=5.0),
            follow_redirects=True,
        )

    def _get(self, path: str, **params):
        try:
            r = self._http.get(f"{API}{path}", params=params or None)
        except httpx.RequestError as exc:
            raise ConnectError(f"Cannot reach {self.server_url}: {exc}") from exc
        if r.status_code == 401:
            raise ConnectError("Rejected: check the API key (Settings → Integrations).")
        if r.status_code == 404 and path == "/connect/info":
            raise ConnectError(
                "This server has no /connect API. It needs Printernizer 2.43.0 or newer."
            )
        if r.status_code >= 400:
            raise ConnectError(f"{self.server_url}{API}{path} returned HTTP {r.status_code}")
        return r

    def info(self) -> dict:
        body = self._get("/connect/info").json()
        return body.get("data", body)

    def tags(self) -> list[dict]:
        body = self._get("/tags").json()
        return body.get("tags", body.get("data", {}).get("tags", []))

    def list_library(self, file_types: list[str], limit: int,
                     sort_by: str = "created_at", tag: str | None = None) -> list[dict]:
        """List library entries, newest first by default.

        file_types MUST carry a leading dot ('.stl'). The server's filter expects
        it; without it the query silently matches nothing.
        """
        out: list[dict] = []
        for ft in file_types:
            page = 1
            while len(out) < limit:
                params = {"file_type": ft, "page": page, "limit": min(200, limit - len(out)),
                          "sort_by": sort_by, "sort_order": "desc"}
                if tag:
                    params["tags"] = tag
                body = self._get("/library/files", **params).json()
                files = body.get("files", [])
                out.extend(files)
                if not body.get("pagination", {}).get("has_next") or not files:
                    break
                page += 1
        return out[:limit]

    def download(self, checksum: str, dest: Path) -> None:
        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            with self._http.stream("GET", f"{API}/library/files/{checksum}/download") as r:
                if r.status_code >= 400:
                    raise ConnectError(f"Download of {checksum[:8]} failed: HTTP {r.status_code}")
                with tmp.open("wb") as fh:
                    for chunk in r.iter_bytes():
                        fh.write(chunk)
        except httpx.RequestError as exc:
            tmp.unlink(missing_ok=True)
            raise ConnectError(f"Download of {checksum[:8]} failed: {exc}") from exc
        except ConnectError:
            tmp.unlink(missing_ok=True)
            raise
        tmp.replace(dest)
```

- [ ] **Step 4: Run and confirm pass**

```bash
.venv/bin/python -m pytest tests/test_client.py -q
```
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: Add typed Printernizer HTTP client

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: PrusaSlicer datadir discovery

**Files:**
- Create: `src/printernizer_connect/prusaslicer/paths.py`
- Test: `tests/test_paths.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `find_datadirs() -> list[Path]` (all candidates that exist, most-likely first), `lua_dir(datadir: Path) -> Path`, `slicer_version(datadir: Path) -> str | None`.

**Why this is its own module:** it is the only place that knows PrusaSlicer's on-disk layout, and that layout changed completely in 3.0.

- [ ] **Step 1: Write the failing test**

`tests/test_paths.py`:

```python
import json
from printernizer_connect.prusaslicer.paths import find_datadirs, lua_dir, slicer_version


def make_30(root, name="PrusaSlicer3-dev", version="3.0.0-alpha11"):
    """A 3.0 datadir: no PrusaSlicer.ini, config lives in shared_runtime/*.json."""
    d = root / name
    (d / "shared_runtime").mkdir(parents=True)
    (d / "shared_runtime" / "PrusaSlicer.json").write_text(
        json.dumps({"app_config_settings": {"version": version}}))
    return d


def make_2x(root, name="PrusaSlicer"):
    d = root / name
    d.mkdir(parents=True)
    (d / "PrusaSlicer.ini").write_text("[app]\nversion = 2.9.0\n")
    return d


def test_finds_a_30_datadir_by_its_json(tmp_path, monkeypatch):
    d = make_30(tmp_path)
    monkeypatch.setattr("printernizer_connect.prusaslicer.paths._roots", lambda: [tmp_path])
    assert find_datadirs() == [d]


def test_finds_a_2x_datadir_by_its_ini(tmp_path, monkeypatch):
    d = make_2x(tmp_path)
    monkeypatch.setattr("printernizer_connect.prusaslicer.paths._roots", lambda: [tmp_path])
    assert find_datadirs() == [d]


def test_prefers_30_over_2x_when_both_exist(tmp_path, monkeypatch):
    make_2x(tmp_path)
    d30 = make_30(tmp_path)
    monkeypatch.setattr("printernizer_connect.prusaslicer.paths._roots", lambda: [tmp_path])
    assert find_datadirs()[0] == d30


def test_ignores_a_directory_with_neither_marker(tmp_path, monkeypatch):
    (tmp_path / "PrusaSlicer").mkdir()
    monkeypatch.setattr("printernizer_connect.prusaslicer.paths._roots", lambda: [tmp_path])
    assert find_datadirs() == []


def test_reads_the_version_from_the_30_json(tmp_path):
    assert slicer_version(make_30(tmp_path)) == "3.0.0-alpha11"


def test_version_is_none_when_unreadable(tmp_path):
    d = make_30(tmp_path)
    (d / "shared_runtime" / "PrusaSlicer.json").write_text("{not json")
    assert slicer_version(d) is None


def test_lua_dir_is_under_the_datadir(tmp_path):
    assert lua_dir(make_30(tmp_path)).name == "lua"
```

- [ ] **Step 2: Run and confirm it fails**

```bash
.venv/bin/python -m pytest tests/test_paths.py -q
```
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `paths.py`**

```python
"""Locating PrusaSlicer's data directory.

PrusaSlicer 3.0 has NO PrusaSlicer.ini — the 2.x heuristic of looking for that
file fails on every 3.0 install. Its app config is shared_runtime/PrusaSlicer.json,
and the directory is named PrusaSlicer3-dev on the alphas. Both layouts are
recognised here; 3.0 wins when both are present.
"""
import json
import sys
from pathlib import Path

# Most-likely first. 3.0 alpha names come before the 2.x name.
DIR_NAMES = ["PrusaSlicer3-dev", "PrusaSlicer3-alpha", "PrusaSlicer3", "PrusaSlicer"]


def _roots() -> list[Path]:
    home = Path.home()
    if sys.platform == "darwin":
        return [home / "Library" / "Application Support"]
    if sys.platform.startswith("win"):
        import os
        return [Path(os.environ.get("APPDATA", home))]
    return [home / ".config"]


def _is_datadir(path: Path) -> bool:
    return (path / "shared_runtime" / "PrusaSlicer.json").exists() or (path / "PrusaSlicer.ini").exists()


def find_datadirs() -> list[Path]:
    """Every plausible datadir that exists, most-likely first."""
    found = []
    for root in _roots():
        for name in DIR_NAMES:
            candidate = root / name
            if candidate.is_dir() and _is_datadir(candidate):
                found.append(candidate)
    return found


def slicer_version(datadir: Path) -> str | None:
    """The version PrusaSlicer records for itself, or None if unreadable."""
    cfg = datadir / "shared_runtime" / "PrusaSlicer.json"
    if cfg.exists():
        try:
            return json.loads(cfg.read_text(encoding="utf-8")).get("app_config_settings", {}).get("version")
        except (json.JSONDecodeError, OSError):
            return None
    ini = datadir / "PrusaSlicer.ini"
    if ini.exists():
        for line in ini.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("version"):
                return line.split("=", 1)[-1].strip()
    return None


def lua_dir(datadir: Path) -> Path:
    return datadir / "lua"
```

- [ ] **Step 4: Run and confirm pass**

```bash
.venv/bin/python -m pytest tests/test_paths.py -q
```
Expected: 7 passed.

- [ ] **Step 5: Verify against the real install on this machine**

```bash
.venv/bin/python -c "
from printernizer_connect.prusaslicer.paths import find_datadirs, slicer_version, lua_dir
for d in find_datadirs():
    print(d, '| version:', slicer_version(d), '| lua:', lua_dir(d).exists())"
```
Expected: finds `~/Library/Application Support/PrusaSlicer3-dev`, version `3.0.0-alpha11`, lua dir exists. If it prints nothing, the discovery is wrong — fix before moving on.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: Discover PrusaSlicer data directories for 2.x and 3.0

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Scope selection and menu grouping

**Files:**
- Create: `src/printernizer_connect/bundle/scope.py`
- Test: `tests/test_scope.py`

**Interfaces:**
- Consumes: `Client.list_library` (Task 2, **already shipped** — read it first).
- Produces: `Entry(checksum, name, file_type, file_size, menu_path, settings, title)` and `select(client, recent, tags, size_budget_mb, group_by) -> tuple[list[Entry], list[str]]`.

> **REVISED after the pre-execution plan review.** Four corrections, each verified:
>
> 1. **`list_library`'s `limit` is PER FILE TYPE**, not a total — that was changed
>    when Task 2's own review found the total-bounded version silently starved
>    `.3mf` (14 of 19 files). So `list_library(LOADABLE, limit=recent)` can return
>    up to `2 × recent` entries, arriving as an `.stl` block then a `.3mf` block —
>    **not** merged newest-first. `select` must re-sort the union and truncate.
> 2. **The size budget measured the compressed source**, not the STL written to
>    disk. A 24 MB 3MF can expand to hundreds of MB. Budget against bytes actually
>    written — which means the budget belongs in the generator (Task 7), not here.
>    This task now applies only a **count** limit and passes size through.
> 3. **No recency ordering existed.** Spike finding S4 says menu entries sort
>    alphabetically, so "Recent" must carry zero-padded ordinal prefixes or it
>    renders alphabetically — starting with `the oldest library file`.
> 4. **`fill_pattern` is dropped.** FINDINGS records an alpha11 hard crash
>    (`Panic at ConfigItemPreview.cpp:50`) while rendering a per-object enum
>    override. Not worth shipping a known crash vector for a field that is null on
>    every real entry anyway.
>
> **Also note:** every print-metadata field is null across all 19 real entries, so
> `build_settings` returns `{}` in practice today. The code stays — metadata may
> populate later — but do not expect a non-empty result against the live server.

- [ ] **Step 1: Write the failing test**

`tests/test_scope.py`:

```python
from printernizer_connect.bundle.scope import select, build_title, build_settings, Entry


class FakeClient:
    """Mimics the SHIPPED list_library: `limit` is a cap per file type."""

    def __init__(self, by_type=None, tags=None):
        self.by_type = by_type or {}
        self._tags = tags or []
        self.queried = []

    def list_library(self, file_types, limit, sort_by="created_at", tag=None):
        out = []
        for ft in file_types:
            self.queried.append(ft)
            out.extend(self.by_type.get(ft, [])[:limit])
        return out

    def tags(self):
        return self._tags


def f(cs, name, ftype="stl", size=1000, added="2026-01-01", **kw):
    return {"checksum": cs, "display_name": name, "filename": name, "file_type": ftype,
            "file_size": size, "role": "model", "added_to_library": added, **kw}


def test_queries_only_loadable_types_with_a_leading_dot():
    c = FakeClient({".stl": [f("a", "A")]})
    select(c, recent=10, tags=[], size_budget_mb=100, group_by=["recent"])
    assert set(c.queried) == {".stl", ".3mf"}


def test_the_union_is_truncated_to_recent_not_to_twice_recent():
    """list_library caps PER TYPE, so 2 types x recent can arrive. Cap the union."""
    c = FakeClient({".stl": [f(f"s{i}", f"S{i}") for i in range(5)],
                    ".3mf": [f(f"m{i}", f"M{i}", "3mf") for i in range(5)]})
    entries, _ = select(c, recent=5, tags=[], size_budget_mb=100, group_by=["recent"])
    assert len(entries) == 5


def test_the_union_is_sorted_newest_first_across_types():
    """Results arrive as an .stl block then a .3mf block; that is not date order."""
    c = FakeClient({".stl": [f("old", "Old", added="2026-01-01")],
                    ".3mf": [f("new", "New", "3mf", added="2026-09-01")]})
    entries, _ = select(c, recent=5, tags=[], size_budget_mb=100, group_by=["recent"])
    assert entries[0].checksum == "new", "newest entry must come first"


def test_recent_entries_carry_an_ordinal_prefix():
    """Menus sort alphabetically (spike S4), so Recent needs an explicit order."""
    c = FakeClient({".stl": [f("a", "Zebra", added="2026-09-02"),
                             f("b", "Alpha", added="2026-09-01")]})
    entries, _ = select(c, recent=5, tags=[], size_budget_mb=100, group_by=["recent"])
    leaves = [e.menu_path.rsplit("/", 1)[1] for e in entries]
    assert leaves[0].startswith("01 ") and "Zebra" in leaves[0]
    assert leaves[1].startswith("02 ") and "Alpha" in leaves[1]


def test_printfiles_are_excluded():
    c = FakeClient({".stl": [f("a", "A"), dict(f("b", "B"), role="printfile")]})
    entries, _ = select(c, recent=10, tags=[], size_budget_mb=100, group_by=["recent"])
    assert [e.checksum for e in entries] == ["a"]


def test_duplicate_checksums_are_collapsed():
    c = FakeClient({".stl": [f("a", "A")], ".3mf": [f("a", "A", "3mf")]})
    entries, _ = select(c, recent=10, tags=[], size_budget_mb=100, group_by=["recent"])
    assert len(entries) == 1


def test_menu_labels_never_contain_a_path_separator():
    c = FakeClient({".stl": [f("a", "Left/Right bracket.stl")]})
    entries, _ = select(c, recent=10, tags=[], size_budget_mb=100, group_by=["recent"])
    assert entries[0].menu_path.count("/") == 2  # Printernizer/Recent/<leaf>


def test_two_long_names_do_not_collide_on_one_menu_path():
    """Truncation must not merge two distinct models into one menu entry."""
    long_a = "X" * 80 + "-alpha"
    long_b = "X" * 80 + "-beta"
    c = FakeClient({".stl": [f("a", long_a), f("b", long_b)]})
    entries, _ = select(c, recent=10, tags=[], size_budget_mb=100, group_by=["recent"])
    assert len({e.menu_path for e in entries}) == 2


def test_title_carries_size_and_settings():
    t = build_title({"display_name": "Benchy.stl", "file_size": 12_300_000,
                     "layer_height": 0.2, "total_layer_count": 250})
    assert "Benchy" in t and "11.7 MB" in t and "0.2" in t


def test_title_omits_absent_metadata_rather_than_printing_none():
    t = build_title({"display_name": "Benchy.stl", "file_size": 1024, "layer_height": None})
    assert "None" not in t


def test_settings_exclude_fill_pattern_and_booleans():
    """fill_pattern crashed alpha11's override panel; booleans are unwritable."""
    s = build_settings({"layer_height": 0.3, "infill_density": 55,
                        "infill_pattern": "gyroid", "wall_count": 6,
                        "support_used": True})
    assert s["layer_height"] == 0.3 and s["fill_density"] == "55%" and s["perimeters"] == 6
    assert "fill_pattern" not in s
    assert "support_material" not in s


def test_settings_are_empty_when_metadata_is_absent():
    """True of every entry in the real library today."""
    assert build_settings({"layer_height": None, "infill_density": None}) == {}
```

- [ ] **Step 2: Run and confirm it fails**

```bash
cd ~/Developer/printernizer-connect && .venv/bin/python -m pytest tests/test_scope.py -q
```

- [ ] **Step 3: Implement `scope.py`**

```python
"""Choosing which library entries become menu commands, and where they sit.

Three live-API facts drive this module:

  * the file_type FILTER needs a leading dot ('.stl'); the returned field has none,
    and a dotless query returns zero rows with no error.
  * `Client.list_library` caps results PER FILE TYPE, so the union arrives as an
    .stl block then a .3mf block. That is not date order — re-sort here.
  * tags and printer_model are never returned by the library API, so grouping by
    printer is not implementable and tag grouping needs one query per tag.

Menu entries sort alphabetically (spike S4), so the Recent group carries explicit
zero-padded ordinals; without them "Recent" is alphabetical, which is useless.
"""
from dataclasses import dataclass

LOADABLE = [".stl", ".3mf"]          # .gcode has no mesh to load
MENU_ROOT = "Printernizer"
MAX_LABEL = 60

# Keys ConfigBox:set accepts on an object: numbers, percentages, enum strings.
# fill_pattern is deliberately ABSENT: alpha11 hard-crashes rendering an enum
# override (FINDINGS: "Panic at ConfigItemPreview.cpp:50"). Booleans are not
# writable at all, so support_material and friends are never emitted.
SETTING_MAP = {
    "layer_height": ("layer_height", lambda v: float(v)),
    "infill_density": ("fill_density", lambda v: f"{int(round(float(v)))}%"),
    "wall_count": ("perimeters", lambda v: int(v)),
}


@dataclass
class Entry:
    checksum: str
    name: str
    file_type: str
    file_size: int
    menu_path: str
    settings: dict
    title: str


def _label(text: str) -> str:
    """A menu label. '/' would create a bogus submenu level."""
    clean = str(text).replace("/", "\u2215").strip()
    return clean[:MAX_LABEL] if len(clean) > MAX_LABEL else clean


def _human_size(n: int) -> str:
    mb = n / (1024 * 1024)
    return f"{mb:.1f} MB" if mb >= 1 else f"{n / 1024:.0f} KB"


def build_title(rec: dict) -> str:
    """The dialog heading — the only detail surface the plugin API offers.

    An 88-character title renders in full (spike S5). Absent metadata is omitted,
    never printed as None; today that means most titles are just name and size.
    """
    parts = [_label(rec.get("display_name") or rec.get("filename") or rec["checksum"][:8])]
    if rec.get("file_size"):
        parts.append(_human_size(rec["file_size"]))
    if rec.get("layer_height"):
        parts.append(f"{float(rec['layer_height'])} mm")
    if rec.get("total_layer_count"):
        parts.append(f"{rec['total_layer_count']} layers")
    return " \u00b7 ".join(parts)


def build_settings(rec: dict) -> dict:
    out = {}
    for src, (dest, cast) in SETTING_MAP.items():
        value = rec.get(src)
        if value in (None, "", 0):
            continue
        try:
            out[dest] = cast(value)
        except (TypeError, ValueError):
            continue
    return out


def select(client, recent: int, tags: list[str], size_budget_mb: int,
           group_by: list[str]) -> tuple[list[Entry], list[str]]:
    """Pick the library entries to mirror, newest first.

    The size budget is NOT applied here: `file_size` is the compressed source, and
    what lands on disk is decompressed STL, routinely several times larger. The
    generator budgets against bytes actually written.
    """
    notes: list[str] = []
    records: dict[str, dict] = {}

    for rec in client.list_library(LOADABLE, limit=recent):
        if rec.get("role") != "printfile":
            records.setdefault(rec["checksum"], rec)

    for tag_id in tags:
        for rec in client.list_library(LOADABLE, limit=recent, tag=tag_id):
            if rec.get("role") != "printfile":
                records.setdefault(rec["checksum"], rec)

    # list_library caps per type, so the union is neither bounded by `recent` nor
    # in date order. Sort and truncate here.
    ordered = sorted(records.values(),
                     key=lambda r: str(r.get("added_to_library") or ""), reverse=True)
    if len(ordered) > recent:
        notes.append(f"{len(ordered) - recent} older entries not included (recent={recent}).")
        ordered = ordered[:recent]

    entries: list[Entry] = []
    for index, rec in enumerate(ordered, start=1):
        name = _label(rec.get("display_name") or rec.get("filename") or rec["checksum"][:8])
        for group in group_by or ["recent"]:
            if group == "recent":
                # Menus sort alphabetically, so carry the order explicitly.
                leaf = f"{index:02d} {name}"
                folder = "Recent"
            else:
                leaf = f"{name} [{rec['checksum'][:6]}]"   # keep truncated names distinct
                folder = "Library"
            entries.append(Entry(
                checksum=rec["checksum"], name=name,
                file_type=str(rec.get("file_type", "")).lstrip("."),
                file_size=rec.get("file_size") or 0,
                menu_path=f"{MENU_ROOT}/{folder}/{leaf}",
                settings=build_settings(rec), title=build_title(rec)))

    if not entries:
        notes.append("No loadable models found (.stl/.3mf). The library may hold only G-code.")
    return entries, notes
```

- [ ] **Step 4: Run and confirm pass**

```bash
.venv/bin/python -m pytest tests/test_scope.py -q
```
Expected: 12 passed.

- [ ] **Step 5: Check it against the real server**

```bash
cd ~/Developer/printernizer-connect
.venv/bin/python -c "
from printernizer_connect.client import Client
from printernizer_connect.bundle.scope import select
c = Client('http://printernizer.local:8000', 'unused-for-library')
entries, notes = select(c, recent=25, tags=[], size_budget_mb=1024, group_by=['recent'])
print(len(entries), 'entries')
for e in entries[:5]: print(' ', e.menu_path, '|', e.title)
print('with settings:', sum(1 for e in entries if e.settings), '(expect 0 today)')
for n in notes: print('note:', n)"
```
Expected: 18 entries (14 × 3mf + 4 × stl; the one `.gcode` is also the one
`role=printfile`), ordinal-prefixed and newest-first, and **0 with settings** —
that last number is the live confirmation that metadata is absent.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: Select library entries and build ordered menu paths

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

### Task 5: The Lua plugin and its template

**Files:**
- Create: `bundle_template/manifest.json`
- Create: `bundle_template/printernizer_lib.lua`
- Create: `bundle_template/model_command.lua.j2`
- Create: `tests/lua/mock_api.lua`, `tests/lua/test_lib.lua`
- Test: `tests/test_lua.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the bundle template files that `generator.py` (Task 6) renders and copies. `printernizer_lib.lua` exposes `M.load(spec)` where `spec = {stls = {…}, offsets = {…}, settings = {…} | nil, opts = {apply_settings = bool}}`.

- [ ] **Step 1: Write the manifest**

`bundle_template/manifest.json`:

```json
{
  "id": "com.printernizer.library",
  "name": "Printernizer Library",
  "version": "0.1.0",
  "min_slicer_version": "3.0.0",
  "author": "printernizer",
  "license": "MIT",
  "description": "Your Printernizer model library, in the Plugins menu",
  "required_apis": { "project.plugin": "1.0.0" }
}
```

- [ ] **Step 2: Write the Lua library**

`bundle_template/printernizer_lib.lua` — the ONLY hand-written Lua. Note what it does **not** do: no stamping (that mechanism emits nothing), no `params=` (silently ignored), and no separate `add_object` per part (they would stack).

```lua
-- Printernizer library loader.
--
-- Constraints this file exists to respect, all verified against 3.0.0-alpha11:
--   * `api` and `require` do not exist during the scan pass, so nothing may be
--     called at file level. Everything happens inside M.load, which runs only
--     when the user picks a command.
--   * add_object auto-centres on the bed. Loading N parts with N calls stacks
--     them all at the centre, so extra parts ride as other_volumes with their
--     own translate.
--   * per-object settings must go in `object_params`. A top-level `params` is
--     accepted and then silently discarded.
local M = {}

function M.load(spec)
  local settings = nil
  if spec.opts and spec.opts.apply_settings and spec.settings then
    settings = spec.settings
  end

  local extra = {}
  for i = 2, #spec.stls do
    local offset = (spec.offsets and spec.offsets[i]) or { x = 0, y = 0, z = 0 }
    extra[#extra + 1] = { mesh = api.load_stl(spec.stls[i]), translate = offset }
  end

  api.project:add_object{
    mesh = api.load_stl(spec.stls[1]),
    other_volumes = extra,
    object_params = settings,
  }
end

return M
```

- [ ] **Step 3: Write the per-model command template**

`bundle_template/model_command.lua.j2`:

```jinja
info = {
    id = "{{ id }}",
    type = "project.plugin",
    title = {{ title }},
    menu = {{ menu }},
{%- if settings %}
    params = {
        {name = "apply_settings", label = {{ settings_label }}, type = "bool", default = true},
    },
{%- endif %}
}

function execute(opts)
    local lib = require("printernizer_lib")
    lib.load{
        stls = { {{ stls }} },
        offsets = { {{ offsets }} },
        settings = {{ settings or "nil" }},
        opts = opts,
    }
end
```

- [ ] **Step 4: Write the Lua mock and unit test**

`tests/lua/mock_api.lua`:

```lua
-- Records what the plugin asks PrusaSlicer to do, so the library can be tested
-- without a running slicer.
local calls = { loaded = {}, objects = {} }
api = {
  load_stl = function(path) calls.loaded[#calls.loaded + 1] = path; return { stl = path } end,
  project = {
    add_object = function(_, spec) calls.objects[#calls.objects + 1] = spec end,
  },
}
setmetatable(api.project, { __index = function() return function() end end })
return calls
```

`tests/lua/test_lib.lua`:

```lua
package.path = "./bundle_template/?.lua;./tests/lua/?.lua;" .. package.path
local calls = require("mock_api")
local M = require("printernizer_lib")

-- one part, settings applied
M.load{ stls = {"a.stl"}, offsets = {}, settings = {layer_height = 0.3},
        opts = {apply_settings = true} }
assert(#calls.loaded == 1, "expected one load_stl")
assert(calls.objects[1].object_params.layer_height == 0.3, "settings must go in object_params")
assert(calls.objects[1].params == nil, "must NOT use params= (silently ignored)")

-- settings declined
M.load{ stls = {"b.stl"}, offsets = {}, settings = {layer_height = 0.3},
        opts = {apply_settings = false} }
assert(calls.objects[2].object_params == nil, "settings must be omitted when declined")

-- three parts => ONE add_object with two other_volumes
M.load{ stls = {"c1.stl", "c2.stl", "c3.stl"},
        offsets = {nil, {x=10,y=0,z=0}, {x=20,y=0,z=0}},
        settings = nil, opts = {} }
assert(#calls.objects == 3, "each load must add exactly one object")
assert(#calls.objects[3].other_volumes == 2, "extra parts must ride as other_volumes")

print("LUA OK")
```

- [ ] **Step 5: Wire the Lua test into pytest**

`tests/test_lua.py`:

```python
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.skipif(shutil.which("lua") is None,
                                reason="lua not installed (brew install lua)")


def test_lua_library_behaves(tmp_path):
    r = subprocess.run(["lua", "tests/lua/test_lib.lua"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "LUA OK" in r.stdout


def test_no_file_level_api_or_require():
    """The scan pass has neither; touching them there kills the command silently."""
    import re
    from pathlib import Path
    for path in Path("bundle_template").glob("*.lua"):
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if line[:1] not in (" ", "\t", "", "-") and re.search(r"\b(api\.|require\s*\()", line):
                pytest.fail(f"{path}:{n} calls api/require at file level: {line.strip()}")
```

- [ ] **Step 6: Install lua and run**

```bash
command -v lua >/dev/null 2>&1 || brew install lua
.venv/bin/python -m pytest tests/test_lua.py -q
```
Expected: 2 passed. If lua cannot be installed, the first test skips — the second still runs and is the one that catches the silent-failure mode.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat: Add the Lua plugin library and command template

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Mesh conversion

**Files:**
- Create: `src/printernizer_connect/bundle/convert.py`
- Test: `tests/test_convert.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `to_stl_parts(src: Path, dest_dir: Path, checksum: str) -> tuple[list[str], list[dict]]` — flat bundle-root filenames and per-part offsets `{"x":…, "y":…, "z":…}`. Raises `ConvertError`.

> **REVISED after the pre-execution plan review.** The original version of this task
> was wrong in three ways, all verified against the real library:
>
> 1. `trimesh` **cannot read 3MF** without `networkx` and `lxml`, neither of which
>    was declared. That is 14 of 19 files. **Already fixed in the repo** (commit
>    `9cb0cbb`); no action needed here beyond not regressing it.
> 2. It iterated `scene.geometry`, but 3MF stores *instances*: a two-part model can
>    be **1 geometry with 2 nodes**. Iterating geometry would emit one STL and
>    silently drop the second part. Iterate `scene.graph.nodes_geometry` instead.
> 3. It took each part's offset from `mesh.bounds.mean(axis=0)` — the *local* centre,
>    which is identical for every instance. Placement lives in the scene-graph
>    transform. Verified: two parts 50 mm apart both report local centre `[5,4,4]`,
>    while the graph gives `[0,0,0]` and `[50,0,0]`.
>
> A real library 3MF is single-object but carries a bed-position translate
> (`[130,130,24]`), so offsets must be **relative to the first part**, not absolute.

- [ ] **Step 1: Write the failing test**

`tests/test_convert.py`:

```python
import zipfile
import pytest
from printernizer_connect.bundle.convert import to_stl_parts, ConvertError

TETRA = """solid p
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
endsolid p
"""

_MESH = """<vertices><vertex x="0" y="0" z="0"/><vertex x="10" y="0" z="0"/>
<vertex x="5" y="8" z="0"/><vertex x="5" y="4" z="8"/></vertices>
<triangles><triangle v1="0" v2="2" v3="1"/><triangle v1="0" v2="1" v3="3"/>
<triangle v1="1" v2="2" v3="3"/><triangle v1="2" v2="0" v3="3"/></triangles>"""


def write_3mf(path, items):
    """items: list of (x, y, z) translations. One shared mesh, N instances."""
    build = "".join(
        f'<item objectid="1" transform="1 0 0 0 1 0 0 0 1 {x} {y} {z}"/>' for x, y, z in items)
    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources><object id="1" type="model"><mesh>{_MESH}</mesh></object></resources>'
             f'<build>{build}</build></model>')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("3D/3dmodel.model", model)
    return path


def test_stl_is_copied_to_a_flat_checksum_name(tmp_path):
    src = tmp_path / "in.stl"; src.write_text(TETRA)
    out = tmp_path / "bundle"; out.mkdir()
    names, offsets = to_stl_parts(src, out, "abc12345")
    assert names == ["abc12345-0.stl"]
    assert (out / "abc12345-0.stl").exists()
    assert offsets == [{"x": 0.0, "y": 0.0, "z": 0.0}]


def test_names_have_no_directory_separator(tmp_path):
    """Bundle assets are flat; subdirectory support is unverified."""
    src = tmp_path / "in.stl"; src.write_text(TETRA)
    out = tmp_path / "b"; out.mkdir()
    names, _ = to_stl_parts(src, out, "abc")
    assert all("/" not in n for n in names)


def test_single_object_3mf_yields_one_part_at_the_origin(tmp_path):
    """Real library 3MFs are single-object but carry a bed-position translate;
    the first part's offset must be zero regardless of where it sits."""
    src = write_3mf(tmp_path / "one.3mf", [(130, 130, 24)])
    out = tmp_path / "b"; out.mkdir()
    names, offsets = to_stl_parts(src, out, "cs")
    assert names == ["cs-0.stl"] and (out / "cs-0.stl").exists()
    assert offsets == [{"x": 0.0, "y": 0.0, "z": 0.0}]


def test_multi_instance_3mf_emits_every_part(tmp_path):
    """A 3MF may hold ONE geometry with N instances. Iterating scene.geometry
    would emit a single STL and silently lose the other parts."""
    src = write_3mf(tmp_path / "two.3mf", [(0, 0, 0), (50, 0, 0)])
    out = tmp_path / "b"; out.mkdir()
    names, offsets = to_stl_parts(src, out, "cs")
    assert len(names) == 2, f"expected 2 parts, got {names}"
    assert all((out / n).exists() for n in names)


def test_multi_part_offsets_are_relative_to_the_first_part(tmp_path):
    """Placement lives in the scene graph, not in local mesh bounds — which are
    identical for every instance of a shared mesh."""
    src = write_3mf(tmp_path / "two.3mf", [(0, 0, 0), (50, 0, 0)])
    out = tmp_path / "b"; out.mkdir()
    _, offsets = to_stl_parts(src, out, "cs")
    assert offsets[0] == {"x": 0.0, "y": 0.0, "z": 0.0}
    assert offsets[1]["x"] == pytest.approx(50.0), offsets


def test_offsets_stay_relative_when_the_model_sits_off_origin(tmp_path):
    src = write_3mf(tmp_path / "two.3mf", [(130, 130, 24), (180, 130, 24)])
    out = tmp_path / "b"; out.mkdir()
    _, offsets = to_stl_parts(src, out, "cs")
    assert offsets[0] == {"x": 0.0, "y": 0.0, "z": 0.0}
    assert offsets[1]["x"] == pytest.approx(50.0)


def test_unreadable_file_raises_convert_error(tmp_path):
    src = tmp_path / "broken.stl"; src.write_text("this is not an stl")
    out = tmp_path / "b"; out.mkdir()
    with pytest.raises(ConvertError):
        to_stl_parts(src, out, "abc")


def test_unsupported_extension_raises(tmp_path):
    src = tmp_path / "x.gcode"; src.write_text("G1 X0")
    out = tmp_path / "b"; out.mkdir()
    with pytest.raises(ConvertError, match="gcode"):
        to_stl_parts(src, out, "abc")


def test_a_file_with_no_extension_raises_a_clear_error(tmp_path):
    """The cache used to store files under a bare checksum, which made every
    entry fail here. The message must name the problem, not say 'this file'."""
    src = tmp_path / "0badc0ffee"; src.write_text(TETRA)
    out = tmp_path / "b"; out.mkdir()
    with pytest.raises(ConvertError, match="extension"):
        to_stl_parts(src, out, "abc")
```

- [ ] **Step 2: Run and confirm it fails**

```bash
cd ~/Developer/printernizer-connect && .venv/bin/python -m pytest tests/test_convert.py -q
```
Expected: `ModuleNotFoundError: No module named 'printernizer_connect.bundle.convert'`

- [ ] **Step 3: Implement `convert.py`**

```python
"""Turning a library file into flat STL parts the Lua plugin can load.

Two things about 3MF drive the design, both verified against real files:

  * It stores INSTANCES. One geometry can appear as several parts, so the unit of
    iteration is `scene.graph.nodes_geometry`, not `scene.geometry`. Iterating
    geometry silently drops every instance after the first.
  * Placement lives in the scene-graph transform, NOT in the mesh's own bounds —
    every instance of a shared mesh reports the same local centre. A real library
    3MF also carries a bed-position translate, so offsets are taken RELATIVE to
    the first part.

PrusaSlicer auto-centres the object it is given, so only the relative arrangement
of the parts matters; the absolute position is discarded either way.
"""
import shutil
from pathlib import Path

MESH_SUFFIXES = (".stl", ".3mf")


class ConvertError(Exception):
    """The file could not be turned into loadable STL parts. User-facing."""


def to_stl_parts(src: Path, dest_dir: Path, checksum: str) -> tuple[list[str], list[dict]]:
    suffix = src.suffix.lower()

    if not suffix:
        raise ConvertError(
            f"{src.name} has no file extension, so its type cannot be determined "
            f"(expected one of {', '.join(MESH_SUFFIXES)})")

    if suffix == ".stl":
        name = f"{checksum}-0.stl"
        try:
            shutil.copyfile(src, dest_dir / name)
        except OSError as exc:
            raise ConvertError(f"Could not copy {src.name}: {exc}") from exc
        _validate(dest_dir / name)
        return [name], [{"x": 0.0, "y": 0.0, "z": 0.0}]

    if suffix == ".3mf":
        return _split_3mf(src, dest_dir, checksum)

    raise ConvertError(
        f"Cannot load {suffix.lstrip('.')}: only {', '.join(MESH_SUFFIXES)} hold meshes")


def _validate(path: Path) -> None:
    import trimesh
    try:
        mesh = trimesh.load(path, force="mesh")
    except Exception as exc:
        raise ConvertError(f"{path.name} is not a readable mesh: {exc}") from exc
    if getattr(mesh, "is_empty", True) or len(getattr(mesh, "faces", [])) == 0:
        raise ConvertError(f"{path.name} contains no geometry")


def _split_3mf(src: Path, dest_dir: Path, checksum: str) -> tuple[list[str], list[dict]]:
    import trimesh
    try:
        scene = trimesh.load(src, force="scene")
    except ImportError as exc:  # networkx / lxml missing -> every 3MF would fail
        raise ConvertError(
            f"Cannot read 3MF: a trimesh dependency is missing ({exc}). "
            f"Install networkx and lxml.") from exc
    except Exception as exc:
        raise ConvertError(f"Could not read {src.name}: {exc}") from exc

    nodes = list(getattr(getattr(scene, "graph", None), "nodes_geometry", []) or [])
    if not nodes:
        raise ConvertError(f"{src.name} contains no placed geometry")

    names, translations = [], []
    for i, node in enumerate(nodes):
        transform, geom_name = scene.graph[node]
        mesh = scene.geometry.get(geom_name)
        if mesh is None or len(getattr(mesh, "faces", [])) == 0:
            continue
        name = f"{checksum}-{len(names)}.stl"
        try:
            mesh.export(dest_dir / name)
        except Exception as exc:
            raise ConvertError(f"Could not export part {i} of {src.name}: {exc}") from exc
        names.append(name)
        translations.append([float(v) for v in transform[:3, 3]])

    if not names:
        raise ConvertError(f"{src.name} contains no usable geometry")

    origin = translations[0]
    offsets = [{"x": round(t[0] - origin[0], 4),
                "y": round(t[1] - origin[1], 4),
                "z": round(t[2] - origin[2], 4)} for t in translations]
    return names, offsets
```

- [ ] **Step 4: Run and confirm pass**

```bash
.venv/bin/python -m pytest tests/test_convert.py -q
```
Expected: 9 passed.

- [ ] **Step 5: Verify against a REAL library file**

The unit tests use synthetic 3MFs. Confirm the module handles what the server
actually serves:

```bash
cd ~/Developer/printernizer-connect
CS=$(curl -s "http://printernizer.local:8000/api/v1/library/files?file_type=.3mf&limit=1" \
     | .venv/bin/python -c "import json,sys;print(json.load(sys.stdin)['files'][0]['checksum'])")
curl -s "http://printernizer.local:8000/api/v1/library/files/$CS/download" -o /tmp/real.3mf
.venv/bin/python -c "
from pathlib import Path
import tempfile
from printernizer_connect.bundle.convert import to_stl_parts
out = Path(tempfile.mkdtemp())
names, offsets = to_stl_parts(Path('/tmp/real.3mf'), out, 'real')
print('parts:', names); print('offsets:', offsets)
print('bytes:', [(out/n).stat().st_size for n in names])"
```
Expected: at least one part, offsets starting `{x:0,y:0,z:0}`, non-zero byte sizes.
If this raises, stop — the unit tests are passing against a fiction.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: Convert library files to flat STL parts with relative offsets

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

### Task 7: Bundle generator with atomic swap

**Files:**
- Create: `src/printernizer_connect/bundle/generator.py`
- Test: `tests/test_generator.py`

**Interfaces:**
- Consumes: `Entry` (Task 4), `to_stl_parts` (Task 6), the templates (Task 5), `Client.download` (Task 2).
- Produces: `generate(entries, lua_dir, client, template_dir, cache_dir, size_budget_mb=1024) -> GenResult` with `GenResult(written: int, skipped: list[str], changed: bool, bytes_written: int)`; `BUNDLE_ID`; `TMP_NAME`; and `referenced_assets(text: str) -> list[str]`, which Task 8's `doctor` reuses so both read a command file the same way.

**Why the invariants matter:** `execute` errors are logged and never shown, so a bad bundle looks like "nothing happened". The generator therefore refuses to publish a bundle it cannot prove is consistent.

> **REVISED after the pre-execution plan review.** As written this task shipped an
> empty menu and reported success. Six corrections, each verified against the real
> library:
>
> 1. **The cache file needs an extension.** `cached = cache_dir / entry.checksum`
>    has none, and `to_stl_parts` switches on `src.suffix` — so it raised
>    "has no file extension" for **every** entry, all 18 got skipped, and (with the
>    Task 8 defect below) sync printed `✓ 0 model command(s) written` in green and
>    exited 0. `Entry.file_type` is dotless, so the path is
>    `cache_dir / f"{entry.checksum}.{entry.file_type}"`.
> 2. **`_verify` scraped every `"`-delimited token ending in `.stl`.** All four real
>    `.stl` entries are literally named `something.stl`, and three of them survive
>    the 60-character label truncation with that suffix intact — so their *menu
>    path* ends in `.stl`, `_verify` demanded a file called
>    `Printernizer/Recent/01 gen_….stl`, and the sync aborted **after** the live
>    bundle had already been renamed away. `_verify` now reads only the
>    `stls = { … }` block and additionally requires each name to look like an asset
>    (`<checksum>-<n>.stl`).
> 3. **The test fixture never wrote the file it claimed to create**, so `_verify`
>    would have failed and all 8 tests failed as written. The fake now writes into
>    `dest`.
> 4. **Staging and rollback lived inside the directory PrusaSlicer scans** —
>    `…library.new` and `…library.old` both carry a manifest with the same bundle
>    id, which is an undefined state — and nothing removed staging when `_verify`
>    raised. Both now live in a sibling of `lua_dir`, inside a `try/finally`, and a
>    failed second rename rolls the old bundle back.
> 5. **The size budget moved here.** Task 4 now caps only the *count*: `file_size`
>    is the compressed source, and a 24 MB 3MF expands to hundreds of MB of STL
>    (the largest real entry is 128 MB compressed). The budget is measured against
>    bytes **actually written into staging**; an entry that would blow it is dropped
>    and reported, and a smaller later entry can still land.
> 6. **Lua literals, not Python reprs.** `_lua_table` emitted `True` and `None` —
>    both undefined Lua globals, which read as `nil` and silently change behaviour —
>    and `inf`/`nan`, which are Lua **syntax errors**, so the command file would
>    simply never appear in the menu. It now emits `true`/`false`/`nil` and refuses
>    non-finite floats.
>
> Also: `except (ConvertError, Exception)` is redundant — catch `Exception` and put
> the exception type in the skip line so programming errors are visible in the
> report. Do **not** `cached.unlink()` on failure: `Client.download` writes to
> `.part` and only `os.replace`s on success, so a cached file is never truncated,
> and deleting it re-downloads 100 MB on every retry. Duplicate `_command_id`s
> silently overwrote each other while `written` counted both; they are now skipped.

- [ ] **Step 1: Write the failing test**

`tests/test_generator.py`:

```python
from pathlib import Path

import pytest

from printernizer_connect.bundle.generator import (
    BUNDLE_ID, TMP_NAME, _verify, generate, referenced_assets,
)
from printernizer_connect.bundle.scope import Entry

TEMPLATES = Path("bundle_template")


class FakeClient:
    def __init__(self, payload=b"solid p\nendsolid p\n", fail=(), payloads=None):
        self.payload = payload
        self.payloads = payloads or {}
        self.fail = set(fail)
        self.downloads = []

    def download(self, checksum, dest):
        self.downloads.append(checksum)
        if checksum in self.fail:
            raise RuntimeError("boom")
        dest.write_bytes(self.payloads.get(checksum, self.payload))


def fake_to_stl_parts(src, dest, cs):
    """Stand in for real mesh conversion — and actually WRITE the file.

    The previous version returned a filename without creating it, so `_verify`
    refused to publish and every test in this file failed. Copying the bytes also
    makes the staged size controllable from FakeClient's payload, which is what
    the budget test needs.
    """
    name = f"{cs}-0.stl"
    (dest / name).write_bytes(src.read_bytes())
    return [name], [{"x": 0.0, "y": 0.0, "z": 0.0}]


def entry(cs="abc", name="Benchy", settings=None):
    return Entry(checksum=cs, name=name, file_type="stl", file_size=100,
                 menu_path=f"Printernizer/Recent/{name}", settings=settings or {},
                 title=f"{name} · 1 KB")


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    # lua lives under a datadir, because staging is a SIBLING of the lua dir.
    lua = tmp_path / "datadir" / "lua"
    lua.mkdir(parents=True)
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr("printernizer_connect.bundle.generator.to_stl_parts",
                        fake_to_stl_parts)
    return lua, cache


def test_writes_a_command_file_and_the_manifest(dirs):
    lua, cache = dirs
    res = generate([entry()], lua, FakeClient(), TEMPLATES, cache)
    bundle = lua / BUNDLE_ID
    assert (bundle / "manifest.json").exists()
    assert (bundle / "printernizer_lib.lua").exists()
    assert list(bundle.glob("m_*.lua"))
    assert res.written == 1


def test_the_cache_file_keeps_the_source_extension(dirs):
    """A cache file named after the bare checksum has no suffix, and to_stl_parts
    switches on src.suffix — so every single entry was rejected."""
    lua, cache = dirs
    generate([entry()], lua, FakeClient(), TEMPLATES, cache)
    assert [p.name for p in cache.iterdir()] == ["abc.stl"]


def test_an_entry_with_no_file_type_is_skipped_not_crashed(dirs):
    lua, cache = dirs
    e = entry()
    e.file_type = ""
    res = generate([e], lua, FakeClient(), TEMPLATES, cache)
    assert res.written == 0
    assert any("file type" in s for s in res.skipped)


def test_command_uses_object_params_not_params(dirs):
    lua, cache = dirs
    generate([entry(settings={"layer_height": 0.3})], lua, FakeClient(), TEMPLATES, cache)
    text = next((lua / BUNDLE_ID).glob("m_*.lua")).read_text()
    assert "apply_settings" in text
    assert "params = {" in text          # the dialog param block
    assert "object_params" not in text   # that lives in the lib, not the command


def test_booleans_and_none_render_as_lua_not_python(dirs):
    """True/None are undefined Lua globals: they read as nil and silently change
    behaviour instead of erroring."""
    lua, cache = dirs
    generate([entry(settings={"perimeters": 6, "support_material": True,
                              "brim_width": None})],
             lua, FakeClient(), TEMPLATES, cache)
    text = next((lua / BUNDLE_ID).glob("m_*.lua")).read_text()
    assert "support_material = true" in text
    assert "brim_width = nil" in text
    assert "True" not in text and "None" not in text


def test_a_non_finite_setting_skips_the_entry(dirs):
    """inf and nan are Lua SYNTAX errors — the command file would silently vanish
    from the menu rather than fail visibly."""
    lua, cache = dirs
    res = generate([entry(settings={"layer_height": float("inf")})],
                   lua, FakeClient(), TEMPLATES, cache)
    assert res.written == 0
    assert any("inf" in s.lower() for s in res.skipped)


def test_a_failed_download_skips_the_entry_but_publishes_the_rest(dirs):
    lua, cache = dirs
    res = generate([entry("bad", "Bad"), entry("good", "Good")], lua,
                   FakeClient(fail={"bad"}), TEMPLATES, cache)
    assert res.written == 1 and any("Bad" in s for s in res.skipped)


def test_a_conversion_failure_keeps_the_cached_download(dirs, monkeypatch):
    """Client.download replaces atomically, so a cached file is never truncated.
    Deleting it just re-downloads 100 MB on the next attempt."""
    lua, cache = dirs

    def boom(src, dest, cs):
        raise RuntimeError("nope")

    monkeypatch.setattr("printernizer_connect.bundle.generator.to_stl_parts", boom)
    generate([entry()], lua, FakeClient(), TEMPLATES, cache)
    assert (cache / "abc.stl").exists()


def test_a_conversion_failure_leaves_no_orphan_assets(dirs, monkeypatch):
    """A multi-part conversion can write part 0 and then fail on part 1."""
    lua, cache = dirs

    def half_then_fail(src, dest, cs):
        (dest / f"{cs}-0.stl").write_bytes(b"partial")
        raise RuntimeError("mesh exploded")

    monkeypatch.setattr("printernizer_connect.bundle.generator.to_stl_parts",
                        half_then_fail)
    res = generate([entry()], lua, FakeClient(), TEMPLATES, cache)
    assert res.written == 0
    assert not list((lua / BUNDLE_ID).glob("*.stl"))


def test_an_entry_over_the_size_budget_is_dropped_and_reported(dirs):
    """The budget counts bytes written into staging, not the compressed source."""
    lua, cache = dirs
    client = FakeClient(payloads={"big": b"x" * 2_000_000, "small": b"y" * 1000})
    res = generate([entry("big", "Big"), entry("small", "Small")], lua, client,
                   TEMPLATES, cache, size_budget_mb=1)
    assert res.written == 1, res.skipped
    assert any("Big" in s and "budget" in s for s in res.skipped)
    assert not list((lua / BUNDLE_ID).glob("big-*.stl"))
    assert res.bytes_written == 1000


def test_duplicate_entries_are_written_once(dirs):
    lua, cache = dirs
    res = generate([entry("a", "A"), entry("a", "A")], lua, FakeClient(),
                   TEMPLATES, cache)
    assert res.written == 1
    assert len(list((lua / BUNDLE_ID).glob("m_*.lua"))) == 1
    assert any("duplicate" in s for s in res.skipped)


def test_every_command_references_an_asset_that_exists(dirs):
    lua, cache = dirs
    generate([entry()], lua, FakeClient(), TEMPLATES, cache)
    bundle = lua / BUNDLE_ID
    for cmd in bundle.glob("m_*.lua"):
        names = referenced_assets(cmd.read_text(encoding="utf-8"))
        assert names, f"{cmd.name} names no asset"
        for name in names:
            assert (bundle / name).exists(), f"{cmd.name} references missing {name}"


def test_a_menu_path_ending_in_stl_does_not_abort_the_publish(dirs):
    """Three of the four real .stl entries are named '<something>.stl', so their
    menu path ends in .stl. Scraping every quoted '.stl' token aborted the sync
    mid-swap on live data."""
    lua, cache = dirs
    res = generate([entry(cs="abc", name="gen_39e295e1.stl")], lua, FakeClient(),
                   TEMPLATES, cache)
    assert res.written == 1
    assert (lua / BUNDLE_ID / "manifest.json").exists()


def test_verify_rejects_a_command_naming_a_missing_asset(tmp_path):
    bundle = tmp_path / "b"
    bundle.mkdir()
    (bundle / "manifest.json").write_text('{"id": "x"}')
    (bundle / "printernizer_lib.lua").write_text("return {}")
    (bundle / "m_dead.lua").write_text(
        'function execute()\n    lib.load{\n        stls = { "abc-0.stl" },\n    }\nend\n')
    with pytest.raises(RuntimeError, match="missing asset"):
        _verify(bundle)


def test_the_previous_bundle_is_replaced_not_merged(dirs):
    lua, cache = dirs
    generate([entry("a", "Old")], lua, FakeClient(), TEMPLATES, cache)
    generate([entry("b", "New")], lua, FakeClient(), TEMPLATES, cache)
    names = [p.read_text() for p in (lua / BUNDLE_ID).glob("m_*.lua")]
    assert any("New" in n for n in names) and not any("Old" in n for n in names)


def test_no_temporary_directories_survive_anywhere(dirs):
    """Staging inside the lua dir would put a SECOND manifest with the same bundle
    id in front of PrusaSlicer's scanner."""
    lua, cache = dirs
    generate([entry()], lua, FakeClient(), TEMPLATES, cache)
    assert [p.name for p in lua.iterdir()] == [BUNDLE_ID]
    assert not (lua.parent / TMP_NAME).exists()


def test_a_verification_failure_leaves_the_previous_bundle_live(dirs, monkeypatch):
    lua, cache = dirs
    generate([entry("a", "Good")], lua, FakeClient(), TEMPLATES, cache)

    def explode(bundle):
        raise RuntimeError("simulated invariant breach")

    monkeypatch.setattr("printernizer_connect.bundle.generator._verify", explode)
    with pytest.raises(RuntimeError, match="simulated"):
        generate([entry("b", "Broken")], lua, FakeClient(), TEMPLATES, cache)

    assert any("Good" in p.read_text() for p in (lua / BUNDLE_ID).glob("m_*.lua"))
    assert not (lua.parent / TMP_NAME).exists()


def test_changed_is_false_when_the_command_set_is_identical(dirs):
    lua, cache = dirs
    generate([entry()], lua, FakeClient(), TEMPLATES, cache)
    second = generate([entry()], lua, FakeClient(), TEMPLATES, cache)
    assert second.changed is False


def test_cached_assets_are_not_downloaded_twice(dirs):
    lua, cache = dirs
    c = FakeClient()
    generate([entry()], lua, c, TEMPLATES, cache)
    generate([entry()], lua, c, TEMPLATES, cache)
    assert len(c.downloads) == 1
```

- [ ] **Step 2: Run and confirm it fails**

```bash
cd ~/Developer/printernizer-connect && .venv/bin/python -m pytest tests/test_generator.py -q
```
Expected: `ModuleNotFoundError: No module named 'printernizer_connect.bundle.generator'`.

- [ ] **Step 3: Implement `generator.py`**

```python
"""Rendering the plugin bundle and publishing it atomically.

A plugin that errors at runtime says nothing — the user just sees a command that
does nothing. So this module refuses to publish a bundle whose invariants it
cannot verify: every referenced asset exists, and every command file was
rendered from the template. The swap is atomic so a half-written bundle is never
what PrusaSlicer scans.

Four rules that are easy to get wrong, each of which fails silently:

  * The download cache is keyed `<checksum>.<file_type>`. The EXTENSION IS LOAD
    BEARING: to_stl_parts switches on `src.suffix`, so a file named after the bare
    checksum is rejected for every entry in the library.
  * PrusaSlicer scans `lua_dir` itself, so staging and rollback copies must NOT
    live inside it — two directories there holding a manifest with the same bundle
    id is an undefined state. Both live in a sibling directory removed in a
    `finally`.
  * `_verify` inspects only the `stls = { … }` block. Real models are named
    "something.stl", so their menu path ends in ".stl" too; a naive scan for
    quoted ".stl" tokens demands assets that were never meant to exist.
  * The size budget counts bytes actually WRITTEN INTO STAGING. `file_size` from
    the API is the compressed source; a 24 MB 3MF routinely expands to hundreds of
    MB of STL.

Not handled yet: the download cache in `config_dir()/cache` grows without bound —
nothing prunes files for entries that have left the library. `doctor` reports its
size so it is at least visible; real pruning is deferred to M3.
"""
import hashlib
import json
import math
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Template

from .convert import to_stl_parts

BUNDLE_ID = "com.printernizer.library"
TMP_NAME = ".printernizer-connect.tmp"   # sibling of lua_dir; never scanned

# An asset name as convert.py emits it: "<checksum>-<index>.stl".
ASSET_NAME = re.compile(r"^[A-Za-z0-9_.\-]+-\d+\.stl$")
# Anchored at line start, and stops at the first "}" — the stls list holds no braces.
_STLS_BLOCK = re.compile(r"^\s*stls\s*=\s*\{([^}]*)\}", re.M)
_QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"')
_LUA_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class GenResult:
    written: int = 0
    skipped: list[str] = field(default_factory=list)
    changed: bool = False
    bytes_written: int = 0


def _lua_str(text) -> str:
    """A Lua double-quoted literal. Names come from the server, so escape them."""
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def _lua_value(value) -> str:
    """One Lua literal.

    Python reprs are not Lua. `True` and `None` are undefined Lua globals, which
    evaluate to nil and quietly change behaviour; `inf` and `nan` are Lua SYNTAX
    errors, and a command file that fails to parse simply never appears in the
    menu. Both failures are invisible, so they are rejected here.
    """
    if value is None:
        return "nil"
    if isinstance(value, bool):          # before int — bool IS an int in Python
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{value!r} cannot be written as a Lua number")
        return repr(value)
    if isinstance(value, str):
        return _lua_str(value)
    raise ValueError(f"cannot represent {type(value).__name__} in Lua")


def _lua_table(mapping: dict) -> str:
    parts = []
    for key, value in mapping.items():
        if not _LUA_KEY.match(str(key)):
            raise ValueError(f"{key!r} is not a valid Lua table key")
        parts.append(f"{key} = {_lua_value(value)}")
    return "{" + ", ".join(parts) + "}"


def _label_value(value) -> str:
    """How a setting reads to a human in the checkbox label.

    Not `str(value)`: that puts "True" and "None" in front of the user, which is
    Python leaking into a 3D-printing UI.
    """
    if isinstance(value, bool):
        return "on" if value else "off"
    if value is None:
        return "-"
    return str(value)


def _command_id(checksum: str, menu_path: str) -> str:
    digest = hashlib.sha256(f"{checksum}:{menu_path}".encode()).hexdigest()[:8]
    return f"m_{digest}"


def referenced_assets(text: str) -> list[str]:
    """The STL names one command file asks the Lua library to load.

    Reads ONLY the `stls = { … }` block. Everything else in the file — the title,
    the menu path — routinely contains ".stl" because that is what the models are
    called. Shared with `doctor` so both read a command file identically.
    """
    block = _STLS_BLOCK.search(text)
    if block is None:
        return []
    return _QUOTED.findall(block.group(1))


def _drop_assets(staging: Path, checksum: str) -> None:
    """Remove every asset this entry wrote, including a half-finished conversion."""
    for path in staging.glob(f"{checksum}-*.stl"):
        path.unlink(missing_ok=True)


def generate(entries, lua_dir: Path, client, template_dir: Path, cache_dir: Path,
             size_budget_mb: int = 1024) -> GenResult:
    lua_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    tmp_root = lua_dir.parent / TMP_NAME
    shutil.rmtree(tmp_root, ignore_errors=True)
    staging = tmp_root / "staging"
    old = tmp_root / "old"
    staging.mkdir(parents=True)

    try:
        shutil.copyfile(template_dir / "manifest.json", staging / "manifest.json")
        shutil.copyfile(template_dir / "printernizer_lib.lua",
                        staging / "printernizer_lib.lua")
        template = Template(
            (template_dir / "model_command.lua.j2").read_text(encoding="utf-8"))

        result = GenResult()
        budget = max(0, int(size_budget_mb)) * 1024 * 1024
        seen: set[str] = set()

        for entry in entries:
            command_id = _command_id(entry.checksum, entry.menu_path)
            if command_id in seen:
                # Without this the second write silently overwrites the first while
                # `written` counts both, so the reported number is a lie.
                result.skipped.append(
                    f"{entry.name}: duplicate of an entry already written")
                continue

            suffix = str(entry.file_type or "").lstrip(".")
            if not suffix:
                result.skipped.append(f"{entry.name}: the server reported no file type")
                continue
            cached = cache_dir / f"{entry.checksum}.{suffix}"

            try:
                if not cached.exists():
                    client.download(entry.checksum, cached)
                names, offsets = to_stl_parts(cached, staging, entry.checksum)

                size = sum((staging / n).stat().st_size for n in names)
                if budget and result.bytes_written + size > budget:
                    _drop_assets(staging, entry.checksum)
                    result.skipped.append(
                        f"{entry.name}: {size / 1048576:.1f} MB of STL would exceed the "
                        f"{size_budget_mb} MB budget (raise size_budget_mb in config.toml)")
                    continue

                settings_lua = _lua_table(entry.settings) if entry.settings else None
                label = "Apply proven settings"
                if entry.settings:
                    label += " (" + ", ".join(
                        f"{k} {_label_value(v)}" for k, v in entry.settings.items()) + ")"
                text = template.render(
                    id=command_id,
                    title=_lua_str(entry.title),
                    menu=_lua_str(entry.menu_path),
                    settings=settings_lua,
                    settings_label=_lua_str(label),
                    stls=", ".join(_lua_str(n) for n in names),
                    offsets=", ".join(_lua_table(o) for o in offsets),
                ) + "\n"
            except Exception as exc:  # noqa: BLE001 — one bad entry must not sink the bundle
                # The cached download is deliberately kept: Client.download writes to
                # a .part file and only os.replace()s on success, so a cached file is
                # never truncated. Deleting it re-downloads 100 MB on every retry.
                # The exception TYPE goes in the report so a programming error here
                # is visible rather than disguised as a bad model.
                _drop_assets(staging, entry.checksum)
                result.skipped.append(f"{entry.name}: {type(exc).__name__}: {exc}")
                continue

            (staging / f"{command_id}.lua").write_text(text, encoding="utf-8")
            seen.add(command_id)
            result.written += 1
            result.bytes_written += size

        _verify(staging)

        live = lua_dir / BUNDLE_ID
        previous = ({p.name: p.read_text(encoding="utf-8") for p in live.glob("m_*.lua")}
                    if live.is_dir() else {})
        current = {p.name: p.read_text(encoding="utf-8") for p in staging.glob("m_*.lua")}
        result.changed = previous != current

        if live.exists():
            live.rename(old)
        try:
            staging.rename(live)
        except OSError:
            if old.exists() and not live.exists():
                old.rename(live)     # put the working bundle back before re-raising
            raise
        return result
    finally:
        # Runs on the happy path too: after the rename, tmp_root holds only `old`.
        # If _verify raised, this is what stops a duplicate-id bundle being left on
        # disk — and it is outside lua_dir, so PrusaSlicer never saw it either way.
        shutil.rmtree(tmp_root, ignore_errors=True)


def _verify(bundle: Path) -> None:
    """Refuse to publish a bundle that cannot possibly work."""
    json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if not (bundle / "printernizer_lib.lua").exists():
        raise RuntimeError("bundle is missing printernizer_lib.lua")
    for command in sorted(bundle.glob("m_*.lua")):
        text = command.read_text(encoding="utf-8")
        if _STLS_BLOCK.search(text) is None:
            raise RuntimeError(f"{command.name} has no stls = {{ ... }} block")
        assets = referenced_assets(text)
        if not assets:
            raise RuntimeError(f"{command.name} names no STL to load")
        for name in assets:
            if not ASSET_NAME.match(name):
                raise RuntimeError(f"{command.name} names a non-asset {name!r}")
            if not (bundle / name).exists():
                raise RuntimeError(f"{command.name} references missing asset {name}")
```

- [ ] **Step 4: Run and confirm pass**

```bash
.venv/bin/python -m pytest tests/test_generator.py -q
```
Expected: 19 passed.

- [ ] **Step 5: Generate a real bundle from the real server**

The unit tests run against a fake converter. This step is the one that would have
caught the cache-extension and `_verify` defects, because it uses real filenames
and real meshes. It writes to a throwaway directory, **not** to PrusaSlicer.

```bash
cd ~/Developer/printernizer-connect
.venv/bin/python - <<'PY'
import tempfile
from pathlib import Path
from printernizer_connect.client import Client
from printernizer_connect.bundle.scope import select
from printernizer_connect.bundle.generator import (
    BUNDLE_ID, TMP_NAME, generate, referenced_assets)

root = Path(tempfile.mkdtemp())
lua = root / "datadir" / "lua"; lua.mkdir(parents=True)
cache = root / "cache"; cache.mkdir()

client = Client("http://printernizer.local:8000", "unused-for-library")
entries, notes = select(client, recent=3, tags=[], size_budget_mb=1024,
                        group_by=["recent"])
res = generate(entries, lua, client, Path("bundle_template"), cache,
               size_budget_mb=1024)

print("written:", res.written, "| MB:", round(res.bytes_written / 1048576, 1),
      "| changed:", res.changed)
for s in res.skipped:
    print("skipped:", s)
print("cache files:", sorted(p.suffix for p in cache.iterdir()))
bundle = lua / BUNDLE_ID
for cmd in sorted(bundle.glob("m_*.lua")):
    names = referenced_assets(cmd.read_text(encoding="utf-8"))
    print(cmd.name, names, "all present:", all((bundle / n).exists() for n in names))
print("lua dir holds:", sorted(p.name for p in lua.iterdir()))
print("tmp left behind:", (lua.parent / TMP_NAME).exists())
PY
```

Expected, and **stop if any of these is wrong**:
- `written: 3`, no `skipped:` lines;
- `cache files:` shows real suffixes (`.3mf` / `.stl`) — **not** empty strings;
- every command prints `all present: True`;
- `lua dir holds: ['com.printernizer.library']` — nothing else;
- `tmp left behind: False`.

- [ ] **Step 6: Check the generated Lua parses**

A Lua syntax error is exactly the failure mode that makes a command vanish from
the menu with no message, so parse what Step 5 produced:

```bash
cd ~/Developer/printernizer-connect
command -v luac >/dev/null 2>&1 || brew install lua

OUT=/tmp/pc-bundle-check
rm -rf "$OUT" && mkdir -p "$OUT/datadir/lua" "$OUT/cache"
.venv/bin/python - "$OUT" <<'PY'
import sys
from pathlib import Path
from printernizer_connect.client import Client
from printernizer_connect.bundle.scope import select
from printernizer_connect.bundle.generator import generate

out = Path(sys.argv[1])
client = Client("http://printernizer.local:8000", "unused-for-library")
entries, _ = select(client, recent=3, tags=[], size_budget_mb=1024, group_by=["recent"])
res = generate(entries, out / "datadir" / "lua", client, Path("bundle_template"),
               out / "cache", size_budget_mb=1024)
print("written:", res.written, "skipped:", res.skipped)
PY

luac -p "$OUT"/datadir/lua/com.printernizer.library/*.lua && echo "LUA SYNTAX OK"
```
Expected: `written: 3 skipped: []` then `LUA SYNTAX OK`. Keep `$OUT` — Task 9 does
not need it, but it is the fastest thing to re-inspect if the real sync misbehaves.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat: Generate the plugin bundle with an atomic swap

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: CLI — setup, doctor, sync

**Files:**
- Create: `src/printernizer_connect/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything from Tasks 1–7, including `ConfigError` (Task 1, **already shipped**) and `referenced_assets` / `GenResult.bytes_written` (Task 7).
- Produces: the `printernizer-connect` console script with `setup`, `doctor`, `sync`.

> **REVISED after the pre-execution plan review.** Five corrections plus a
> packaging decision:
>
> 1. **`ConfigError` is not caught.** Task 1's shipped `load_config` raises it on a
>    corrupt file — deliberately, so `doctor` cannot mistake "corrupt" for "not
>    configured". As written, every command answers a hand-edited `config.toml`
>    with a Python traceback instead of the message Task 1 went to trouble to
>    write. Caught in `_require_config` and in `setup`.
> 2. **`sync` reported success when it wrote nothing.** `✓ 0 model command(s)
>    written` in green, exit 0, empty menu. Combined with the Task 7 cache-extension
>    defect that was the *actual* user-visible failure of this milestone. It now
>    exits 1 in red when there were entries and none of them made it.
> 3. **Two tests were unsound.** `test_doctor_warns_about_a_home_assistant_ingress_url`
>    monkeypatched nothing, so it made a real network call and read the user's real
>    PrusaSlicer install — both forbidden by CONTEXT.md. And
>    `test_dry_run_writes_nothing` was vacuous: `--dry-run` returns before
>    `_lua_dir` is ever called, so the assertion could not fail. It now proves
>    `generate` is not reached.
> 4. **The API key prompt echoed the key.** Task 1 stores it 0600 and writes it
>    atomically so it is never world-readable for an instant; printing it into the
>    terminal scrollback undoes that. `hide_input=True`.
> 5. **Small truths.** `_lua_dir` told the user to "Pass `--datadir`" on commands
>    that have no such option — the message now names `setup --datadir`, and a
>    dedicated `NoDatadir` exception replaces `typer.BadParameter`, which is for
>    parameters. `setup --datadir` now checks the path exists. `doctor` now checks
>    the plugin directory exists before printing ✓, reuses Task 7's
>    `referenced_assets` (so it does not re-invent the `.stl`-scraping bug), and
>    reports the download cache size, which nothing prunes. `sync` merges into the
>    existing state instead of replacing it, and records `last_sync`.
>
> **Packaging ruling: editable install only, for now.**
> `TEMPLATE_DIR = …parent.parent.parent / "bundle_template"` resolves correctly for
> a source checkout and for `pip install -e .`, and **not at all** for a wheel — the
> templates live at the repo root, so a wheel built from this tree does not contain
> them. Moving them to `src/printernizer_connect/bundle_template/` is the real fix,
> but that is Task 5's file layout and Task 5 is already frozen. So M2 supports the
> editable install only; `_template_dir()` below raises one clear sentence instead
> of a `FileNotFoundError` from inside `generate`, `doctor` checks it, and Task 9's
> README says so. Packaging the templates as package data is an M3 item.

- [ ] **Step 1: Write the failing test**

`tests/test_cli.py`:

```python
import typer.main
from typer.testing import CliRunner

import pytest

from printernizer_connect.bundle.generator import GenResult
from printernizer_connect.cli import app
from printernizer_connect.config import Config, config_dir, load_state, save_config

runner = CliRunner()


class FakeClient:
    """No network. `sync` and `doctor` only ever need these three."""

    def info(self):
        return {"server_version": "2.43.0", "min_connect_version": "0.1.0"}

    def list_library(self, file_types, limit, sort_by="created_at", tag=None):
        return [{"checksum": "a", "display_name": "Benchy.stl", "file_type": "stl",
                 "file_size": 1024, "role": "model",
                 "added_to_library": "2026-09-01T10:00:00"}]

    def tags(self):
        return []


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """No real config dir, no real network, no real PrusaSlicer install.

    CONTEXT.md forbids a unit test touching either. `_lua_dir` is patched here for
    EVERY test so that a command which reaches it cannot silently fall through to
    the user's own ~/Library/Application Support.
    """
    monkeypatch.setenv("PRINTERNIZER_CONNECT_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr("printernizer_connect.cli._client", lambda cfg: FakeClient())
    monkeypatch.setattr("printernizer_connect.cli._lua_dir",
                        lambda cfg: tmp_path / "datadir" / "lua")
    return tmp_path


def test_doctor_reports_missing_config_without_crashing():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code != 0
    assert "setup" in result.output.lower()


def test_a_corrupt_config_reports_the_file_instead_of_a_traceback():
    """load_config raises ConfigError by design (Task 1) so that 'corrupt' is never
    mistaken for 'not configured'. Every command must catch it."""
    cfg_file = config_dir() / "config.toml"
    cfg_file.write_text('server_url = "http://x\n')          # unterminated string
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "config.toml" in result.output
    assert "not valid TOML" in result.output


def test_doctor_warns_about_a_home_assistant_ingress_url():
    save_config(Config(server_url="http://ha.local/api/hassio_ingress/abc", api_key="pk"))
    result = runner.invoke(app, ["doctor"])
    assert "ingress" in result.output.lower()
    assert result.exit_code == 1


def test_doctor_reports_a_plugin_directory_that_does_not_exist(tmp_path):
    save_config(Config(server_url="http://x", api_key="pk"))
    result = runner.invoke(app, ["doctor"])
    assert "does not exist yet" in result.output


def test_sync_without_config_tells_you_to_run_setup():
    result = runner.invoke(app, ["sync"])
    assert result.exit_code != 0 and "setup" in result.output.lower()


def test_dry_run_never_reaches_the_generator(monkeypatch, tmp_path):
    """The old version of this test asserted a directory was absent that the
    dry-run path never creates in the first place — it could not fail."""
    save_config(Config(server_url="http://x", api_key="pk"))

    def must_not_run(*args, **kwargs):
        raise AssertionError("generate() was called during --dry-run")

    monkeypatch.setattr("printernizer_connect.cli.generate", must_not_run)
    result = runner.invoke(app, ["sync", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "dry run" in result.output.lower()
    assert not (tmp_path / "datadir").exists()


def test_sync_fails_loudly_when_every_entry_was_skipped(monkeypatch):
    """Green '0 model command(s) written' + exit 0 was the real-world failure of
    this milestone: an empty menu that looked like a success."""
    save_config(Config(server_url="http://x", api_key="pk"))
    monkeypatch.setattr(
        "printernizer_connect.cli.generate",
        lambda *a, **k: GenResult(written=0, skipped=["Benchy.stl: boom"], changed=True))
    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 1, result.output
    assert "0 of 1" in result.output


def test_sync_records_last_sync_in_the_state_file(monkeypatch):
    save_config(Config(server_url="http://x", api_key="pk"))
    monkeypatch.setattr(
        "printernizer_connect.cli.generate",
        lambda *a, **k: GenResult(written=1, skipped=[], changed=True,
                                  bytes_written=2048))
    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 0, result.output
    state = load_state()
    assert state["entries"] == 1 and state["last_sync"]


def test_setup_rejects_a_datadir_that_does_not_exist(tmp_path):
    result = runner.invoke(app, ["setup", "--server", "http://x", "--api-key", "pk",
                                 "--datadir", str(tmp_path / "nope")])
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_the_api_key_prompt_is_hidden():
    """Task 1 stores the key 0600; echoing it into the scrollback undoes that."""
    command = typer.main.get_command(app).commands["setup"]
    option = next(p for p in command.params if p.name == "api_key")
    assert option.hide_input is True
```

- [ ] **Step 2: Run and confirm it fails**

```bash
.venv/bin/python -m pytest tests/test_cli.py -q
```
Expected: `ModuleNotFoundError: No module named 'printernizer_connect.cli'`.

- [ ] **Step 3: Implement `cli.py`**

```python
"""printernizer-connect — browse your Printernizer library inside PrusaSlicer."""
from datetime import datetime, timezone
from pathlib import Path

import typer

from .bundle.generator import BUNDLE_ID, generate, referenced_assets
from .bundle.scope import select
from .client import Client, ConnectError
from .config import (
    Config, ConfigError, config_dir, load_config, load_state, save_config, save_state,
)
from .prusaslicer.paths import find_datadirs, lua_dir, slicer_version

app = typer.Typer(add_completion=False, help=__doc__)


class NoDatadir(Exception):
    """PrusaSlicer's data directory could not be located, or no longer exists."""


class NoTemplates(Exception):
    """The bundle templates are not on disk where this install can reach them."""


def _client(cfg: Config) -> Client:
    return Client(cfg.server_url, cfg.api_key)


def _template_dir() -> Path:
    """Where the bundle templates live.

    They sit at the REPOSITORY ROOT, not inside the package, so this resolves for a
    source checkout and for `pip install -e .` — and not for a plain wheel, which
    contains no bundle_template/ at all. Editable install is therefore the only
    supported installation in M2 (packaging them as package data is an M3 item).
    The check below turns that into one sentence instead of a FileNotFoundError
    thrown from deep inside generate().
    """
    path = Path(__file__).resolve().parent.parent.parent / "bundle_template"
    if not (path / "manifest.json").exists():
        raise NoTemplates(
            f"Bundle templates not found at {path}. printernizer-connect currently "
            f"supports only an editable install — run `pip install -e .` from a "
            f"checkout of the repository.")
    return path


def _lua_dir(cfg: Config) -> Path:
    if cfg.datadir:
        datadir = Path(cfg.datadir).expanduser()
        if not datadir.is_dir():
            raise NoDatadir(
                f"The configured PrusaSlicer data directory {datadir} does not exist. "
                f"Re-run: printernizer-connect setup --datadir <path>")
    else:
        found = find_datadirs()
        if not found:
            raise NoDatadir(
                "No PrusaSlicer data directory found. "
                "Re-run: printernizer-connect setup --datadir <path>")
        datadir = found[0]
    return lua_dir(datadir)


def _require_config() -> Config:
    try:
        cfg = load_config()
    except ConfigError as exc:
        # Task 1 raises this rather than falling back to defaults, precisely so a
        # corrupt file is never reported as "not configured".
        typer.secho(f"✗ {exc}", fg="red")
        raise typer.Exit(1)
    if not cfg.server_url:
        typer.secho("Not configured yet. Run: printernizer-connect setup", fg="red")
        raise typer.Exit(1)
    return cfg


def _cache_mb() -> float:
    cache = config_dir() / "cache"
    if not cache.is_dir():
        return 0.0
    return sum(p.stat().st_size for p in cache.iterdir() if p.is_file()) / 1048576


@app.command()
def setup(server: str = typer.Option(..., prompt="Printernizer URL"),
          api_key: str = typer.Option(..., prompt="API key (Settings → Integrations)",
                                      hide_input=True),
          datadir: str = typer.Option("", help="Override the PrusaSlicer data directory")):
    """Store the server URL and key, and locate PrusaSlicer."""
    try:
        cfg = load_config()
    except ConfigError as exc:
        typer.secho(f"✗ {exc}", fg="red")
        raise typer.Exit(1)
    cfg.server_url, cfg.api_key = server.rstrip("/"), api_key

    try:
        info = _client(cfg).info()
    except ConnectError as exc:
        typer.secho(f"✗ {exc}", fg="red")
        raise typer.Exit(1)
    typer.secho(f"✓ Printernizer {info.get('server_version')} reachable", fg="green")

    if datadir:
        chosen = Path(datadir).expanduser()
        if not chosen.is_dir():
            typer.secho(f"✗ {chosen} does not exist, or is not a directory.", fg="red")
            raise typer.Exit(1)
        cfg.datadir = str(chosen)
    else:
        found = find_datadirs()
        if not found:
            typer.secho("✗ No PrusaSlicer data directory found. "
                        "Re-run with --datadir <path>.", fg="red")
            raise typer.Exit(1)
        cfg.datadir = str(found[0])
        if len(found) > 1:
            typer.secho(f"  ({len(found)} found; using {found[0].name})", fg="yellow")
    version = slicer_version(Path(cfg.datadir)) or "?"
    typer.secho(f"✓ PrusaSlicer {version} at {cfg.datadir}", fg="green")
    if version == "?":
        typer.secho("  (no version marker there — check this is really a datadir)",
                    fg="yellow")

    save_config(cfg)
    typer.secho(f"✓ Config written to {config_dir() / 'config.toml'}", fg="green")
    typer.echo("\nNow run: printernizer-connect sync")


@app.command()
def doctor():
    """Check that everything Connect needs is in place."""
    cfg = _require_config()
    problems = 0

    if "/api/hassio_ingress/" in cfg.server_url:
        typer.secho("✗ That is a Home Assistant ingress URL. Ingress needs a browser "
                    "session, so a CLI cannot use it — expose the add-on's port and "
                    "use that address instead.", fg="red")
        problems += 1

    try:
        info = _client(cfg).info()
        typer.secho(f"✓ Server {info.get('server_version')} reachable, key accepted",
                    fg="green")
    except ConnectError as exc:
        typer.secho(f"✗ {exc}", fg="red")
        problems += 1

    try:
        templates = _template_dir()
        typer.secho(f"✓ Bundle templates at {templates}", fg="green")
    except NoTemplates as exc:
        typer.secho(f"✗ {exc}", fg="red")
        problems += 1

    target = None
    try:
        target = _lua_dir(cfg)
    except NoDatadir as exc:
        typer.secho(f"✗ {exc}", fg="red")
        problems += 1

    if target is not None:
        if target.is_dir():
            typer.secho(f"✓ Plugin directory {target}", fg="green")
        else:
            typer.secho(f"• Plugin directory {target} does not exist yet — "
                        f"sync creates it", fg="yellow")
        bundle = target / BUNDLE_ID
        if bundle.is_dir():
            commands = sorted(bundle.glob("m_*.lua"))
            typer.secho(f"✓ Bundle installed with {len(commands)} model command(s)",
                        fg="green")
            missing = [name for cmd in commands
                       for name in referenced_assets(cmd.read_text(encoding="utf-8"))
                       if not (bundle / name).exists()]
            if missing:
                typer.secho(f"✗ {len(missing)} command(s) reference missing assets — "
                            f"re-run sync", fg="red")
                problems += 1
        else:
            typer.secho("• No bundle yet — run sync", fg="yellow")

    typer.echo(f"  Download cache: {_cache_mb():.0f} MB in {config_dir() / 'cache'} "
               f"(nothing prunes it yet — delete it by hand if it grows)")

    raise typer.Exit(1 if problems else 0)


@app.command()
def sync(dry_run: bool = typer.Option(False, "--dry-run", help="Show what would change")):
    """Mirror the library into PrusaSlicer's plugin directory."""
    cfg = _require_config()
    client = _client(cfg)
    try:
        client.info()
        entries, notes = select(client, recent=cfg.sync_recent, tags=cfg.sync_tags,
                                size_budget_mb=cfg.size_budget_mb, group_by=cfg.group_by)
    except ConnectError as exc:
        typer.secho(f"✗ {exc}", fg="red")
        raise typer.Exit(1)
    for note in notes:
        typer.secho(f"• {note}", fg="yellow")

    if dry_run:
        for entry in entries:
            typer.echo(f"  {entry.menu_path}")
        typer.echo(f"\n{len(entries)} entries would be written "
                   f"(dry run — nothing changed).")
        return

    try:
        target = _lua_dir(cfg)
        templates = _template_dir()
    except (NoDatadir, NoTemplates) as exc:
        typer.secho(f"✗ {exc}", fg="red")
        raise typer.Exit(1)

    try:
        result = generate(entries, target, client, templates, config_dir() / "cache",
                          size_budget_mb=cfg.size_budget_mb)
    except Exception as exc:  # noqa: BLE001 — the generator refuses to publish a bad bundle
        typer.secho(f"✗ Bundle not published: {type(exc).__name__}: {exc}", fg="red")
        typer.secho("  The previously installed bundle, if any, is untouched.", fg="red")
        raise typer.Exit(1)

    for skipped in result.skipped:
        typer.secho(f"• skipped {skipped}", fg="yellow")

    state = load_state()
    state.update({
        "last_sync": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "entries": result.written,
        "bytes_written": result.bytes_written,
        "skipped": len(result.skipped),
    })
    save_state(state)

    if not entries:
        typer.secho("• Nothing to write — the library holds no loadable models.",
                    fg="yellow")
        return
    if result.written == 0:
        # Green "0 written" + exit 0 is how this milestone shipped an empty menu
        # that looked like a success. Never again.
        typer.secho(f"✗ 0 of {len(entries)} model(s) could be written — "
                    f"the Plugins menu will be empty.", fg="red")
        typer.secho("  The skipped lines above say why; "
                    "`printernizer-connect doctor` re-checks the install.", fg="red")
        raise typer.Exit(1)

    typer.secho(f"✓ {result.written} model command(s) written "
                f"({result.bytes_written / 1048576:.0f} MB of STL)", fg="green")

    if result.changed:
        typer.secho("\nOpen PrusaSlicer ▸ Plugins ▸ Rescan Plugins to see the changes.",
                    fg="cyan", bold=True)
    else:
        typer.echo("\nNo change since the last sync.")


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run and confirm pass**

```bash
.venv/bin/python -m pytest tests/test_cli.py -q
```
Expected: 10 passed.

- [ ] **Step 5: Run the whole suite**

```bash
.venv/bin/python -m pytest -q
```
Expected: all green, no failures.

- [ ] **Step 6: Check `doctor` against the real install, with no config**

This is cheap and uses the real machine, which is where `_lua_dir` and
`_template_dir` actually have to work:

```bash
cd ~/Developer/printernizer-connect
PRINTERNIZER_CONNECT_CONFIG_DIR=/tmp/pc-empty .venv/bin/printernizer-connect doctor; echo "exit=$?"
```
Expected: `Not configured yet. Run: printernizer-connect setup`, `exit=1`, and **no
traceback**. Then confirm the templates resolve through the console script (not just
through `python -m`, which has a different `sys.path`):

```bash
.venv/bin/python -c "
from printernizer_connect.cli import _template_dir
print('templates:', _template_dir())"
```

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat: Add setup, doctor and sync commands

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: End-to-end against the real server and slicer

**Files:**
- Create: `README.md` (replace the stub)
- Test: manual, recorded in `docs/acceptance.md`

**Interfaces:**
- Consumes: the whole package.
- Produces: a verified working install and the acceptance record.

**This is the task that proves M2 actually works.** Everything before it is tested against fakes.

> **REVISED after the pre-execution plan review.** Three corrections:
>
> 1. **The commands could not run.** Nothing in the plan ever installed the
>    package, so `python -m printernizer_connect.cli` raised `ModuleNotFoundError`
>    (the sources live under `src/`). The editable install and its dependencies
>    **are already in the repo** as of commit `9cb0cbb`, so this task now drives
>    the real console script, `.venv/bin/printernizer-connect`, and Step 2 verifies
>    it resolves before anything depends on it.
> 2. **Three of the six acceptance criteria were unverifiable.** Every
>    print-metadata field is null across all 19 real library entries
>    (`layer_height`, `infill_density`, `wall_count`, `total_layer_count`; and
>    `GET /library/files/{cs}/metadata` returns `print_settings: null`). So
>    `build_settings()` returns `{}` for everything, no command gets the
>    `apply_settings` checkbox, and the `object_params` path — the spike's single
>    most important finding — cannot be reached by clicking. Step 7 now hand-edits
>    one generated command to carry real settings so that path is genuinely
>    exercised in the real slicer. Likewise Step 8 finds out, offline, whether any
>    real 3MF actually has more than one part, and says what to do when none does
>    rather than leaving criterion 5 hanging.
> 3. **The `.gcode` file and the `role=printfile` entry are the same entry** —
>    verified: the library holds `14 × (3mf, model)`, `4 × (stl, model)` and
>    `1 × (gcode, printfile)`. The old wording read as two exclusions and implied
>    17. **18 is the right number.**

- [ ] **Step 1: Check the server has M1**

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://printernizer.local:8000/api/v1/connect/info
```
`401` means M1 is deployed and the endpoint wants a key — proceed. `404` means the server is still on 2.42.0 and **must be updated to 2.43.0 first**; stop and tell the user. (Verified `401` on 2026-09-08.)

- [ ] **Step 2: Confirm the package is installed and the console script resolves**

Everything below runs the installed entry point, not a module path — `src/` layout
means `python -m printernizer_connect.cli` only works once the package is installed.

```bash
cd ~/Developer/printernizer-connect
.venv/bin/pip install -e . >/dev/null && echo "editable install ok"
.venv/bin/printernizer-connect --help | head -20
.venv/bin/python -c "
import printernizer_connect, importlib.metadata as md
print('package:', printernizer_connect.__file__)
print('entry points:', [e.name for e in md.distribution('printernizer-connect').entry_points])"
```
Expected: the help text lists `setup`, `doctor`, `sync`; the package resolves to
`~/Developer/printernizer-connect/src/printernizer_connect/__init__.py`; and the
entry points include `printernizer-connect`. If `--help` fails, stop — nothing
after this can work.

- [ ] **Step 3: Create an API key**

In Printernizer's web UI: **Settings → Integrations → Create key**. Copy it — it is shown only once.

- [ ] **Step 4: Run setup, then doctor**

```bash
cd ~/Developer/printernizer-connect
.venv/bin/printernizer-connect setup \
  --server http://printernizer.local:8000 --api-key 'pk_...'
.venv/bin/printernizer-connect doctor; echo "exit=$?"
```
Expected from `setup`: server 2.43.0 reachable, `PrusaSlicer3-dev` found with
version `3.0.0-alpha11`, config written. Expected from `doctor`: server reachable,
templates found, plugin directory found, `• No bundle yet — run sync`, `exit=0`.

Then confirm the key really is private:

```bash
ls -l "$(.venv/bin/python -c 'from printernizer_connect.config import config_dir; print(config_dir())')/config.toml"
```
Expected: mode `-rw-------`.

- [ ] **Step 5: Dry run, then sync**

```bash
.venv/bin/printernizer-connect sync --dry-run
.venv/bin/printernizer-connect sync; echo "exit=$?"
```

Expected from the dry run: **18** menu paths. The library holds 19 files, and the
single excluded one is the `.gcode` — which *is* the only `role=printfile` entry,
not a second exclusion.

Expected from `sync`: `exit=0` and a green `✓ N model command(s) written` with a
non-zero N, then the "Rescan Plugins" reminder. If it prints
`✗ 0 of 18 model(s) could be written`, read the skipped lines — that is the failure
this milestone shipped last time and the exit code now says so.

Note the default `size_budget_mb = 1024`: the real library is 269 MB **compressed**
and its STL expansion may well exceed 1 GB, so some entries can legitimately be
dropped with a "would exceed the budget" line. That is correct behaviour — raise
`size_budget_mb` in `config.toml` and re-run if you want all 18.

- [ ] **Step 6: Verify the bundle on disk**

```bash
B="$HOME/Library/Application Support/PrusaSlicer3-dev/lua/com.printernizer.library"
ls "$B" | head; echo "commands: $(ls "$B"/m_*.lua | wc -l)"
command -v luac >/dev/null 2>&1 || brew install lua
luac -p "$B"/*.lua && echo "LUA SYNTAX OK"

# Nothing may be left beside the bundle in the scanned directory.
ls -a "$(dirname "$B")"
ls -a "$(dirname "$(dirname "$B")")" | grep -i printernizer || echo "no staging left behind"
```
Every `m_*.lua` must parse; the lua directory must contain exactly one
`com.printernizer.library` and no `*.new` / `*.old`; and no
`.printernizer-connect.tmp` may survive in the datadir.

- [ ] **Step 7: Give one command real settings, by hand**

No real entry has print metadata, so nothing generated carries an `apply_settings`
checkbox and the `object_params` path — spike finding S3, the most important
result of the whole spike — is otherwise never executed. Patch one command file:

```bash
B="$HOME/Library/Application Support/PrusaSlicer3-dev/lua/com.printernizer.library"
cd ~/Developer/printernizer-connect
.venv/bin/python - "$B" <<'PY'
import sys
from pathlib import Path

bundle = Path(sys.argv[1])
target = None
for cmd in sorted(bundle.glob("m_*.lua")):
    text = cmd.read_text(encoding="utf-8")
    if "settings = nil" in text:
        target, original = cmd, text
        break
if target is None:
    raise SystemExit("every command already carries settings — nothing to patch")

lines = []
for line in original.splitlines():
    lines.append(line)
    if line.strip().startswith("menu ="):
        lines.append("    params = {")
        lines.append('        {name = "apply_settings", label = "Apply proven '
                     'settings (layer_height 0.3, perimeters 6)", type = "bool", '
                     "default = true},")
        lines.append("    },")
patched = "\n".join(lines).replace(
    "settings = nil", "settings = {layer_height = 0.3, perimeters = 6}")
target.write_text(patched + "\n", encoding="utf-8")

print("patched:", target.name)
print("menu:", next(l.strip() for l in patched.splitlines() if l.strip().startswith("menu =")))
PY

luac -p "$B"/*.lua && echo "LUA SYNTAX OK"
```

Note the menu path it printed — that is the command to click in Step 9. **Re-running
`sync` rebuilds the bundle and discards this patch**, which is exactly what the
atomic swap is supposed to do; re-apply it if you sync again.

- [ ] **Step 8: Find out whether any real 3MF has more than one part**

Criterion 5 (multi-part loading) needs a model with at least two parts. Run the
converter over every 3MF the sync already downloaded — no network, no slicer:

```bash
cd ~/Developer/printernizer-connect
.venv/bin/python - <<'PY'
import tempfile
from pathlib import Path
from printernizer_connect.config import config_dir
from printernizer_connect.bundle.convert import to_stl_parts, ConvertError

cache = config_dir() / "cache"
out = Path(tempfile.mkdtemp())
multi = []
files = sorted(cache.glob("*.3mf"))
print(f"{len(files)} cached 3MF files")
for src in files:
    try:
        names, offsets = to_stl_parts(src, out, src.stem[:8])
    except ConvertError as exc:
        print(f"  SKIP {src.stem[:12]}: {exc}")
        continue
    print(f"  {src.stem[:12]}  parts={len(names)}  offsets={offsets}")
    if len(names) > 1:
        multi.append(src.name)
print("\nmulti-part files:", multi or "NONE")
PY
```

- **If it lists a multi-part file:** note its checksum prefix, find the matching
  command (`grep -l "<prefix>-1.stl" "$B"/m_*.lua`) and click that one for
  criterion 5.
- **If it prints `NONE`** (the likely outcome — every real 3MF probed so far is
  single-object): fabricate the multi-part case from a real asset, so the
  `other_volumes` + `translate` path is still executed by the real slicer.

```bash
B="$HOME/Library/Application Support/PrusaSlicer3-dev/lua/com.printernizer.library"
cd ~/Developer/printernizer-connect
.venv/bin/python - "$B" <<'PY'
import shutil, sys
from pathlib import Path
from printernizer_connect.bundle.generator import referenced_assets

bundle = Path(sys.argv[1])
ZERO = "offsets = { {x = 0.0, y = 0.0, z = 0.0} }"
for cmd in sorted(bundle.glob("m_*.lua")):
    text = cmd.read_text(encoding="utf-8")
    if "apply_settings" in text:
        continue        # leave Step 7's command alone: keep criteria 4 and 5 apart
    names = referenced_assets(text)
    if len(names) == 1 and ZERO in text:
        first = names[0]
        second = first.replace("-0.stl", "-1.stl")
        shutil.copyfile(bundle / first, bundle / second)
        text = text.replace(f'stls = {{ "{first}" }}',
                            f'stls = {{ "{first}", "{second}" }}')
        text = text.replace(
            ZERO, "offsets = { {x = 0.0, y = 0.0, z = 0.0}, {x = 60.0, y = 0.0, z = 0.0} }")
        cmd.write_text(text, encoding="utf-8")
        print("patched:", cmd.name, "->", first, second)
        print("menu:", next(l.strip() for l in text.splitlines()
                            if l.strip().startswith("menu =")))
        break
else:
    raise SystemExit("no single-part command with a zero offset found — "
                     "inspect the bundle by hand")
PY

luac -p "$B"/*.lua && echo "LUA SYNTAX OK"
```
That command must now load **one** object with **two** parts, 60 mm apart. Record
in `docs/acceptance.md` which route was used — a real multi-part 3MF or this
fabricated one — so the record does not overstate what was tested.

- [ ] **Step 9: Verify in PrusaSlicer**

Start PrusaSlicer from a terminal (so its stdout is visible), then
**Plugins ▸ Rescan Plugins**. Confirm each of these and record the answer in
`docs/acceptance.md`:

1. `Plugins ▸ Printernizer ▸ Recent` lists the models, **in sync order** — `01 …`,
   `02 …` — not alphabetically.
2. Clicking one opens a dialog whose title shows name · size (metadata is null on
   every real entry, so expect no layer height or layer count).
3. Clicking **Run** puts the model on the bed.
4. **The command patched in Step 7** shows an "Apply proven settings" checkbox;
   with it ticked, the loaded object's per-object overrides list
   `layer_height 0.3` and `perimeters 6`. With it unticked, no overrides appear.
   *(This is the `object_params` path. If the overrides are absent while the
   checkbox is ticked, the Lua library is using `params=` somewhere — spike S3.)*
5. **The multi-part command from Step 8** arrives as **one** object with several
   parts — *not* several objects stacked at the bed centre — and with **no**
   "Conflicts in G-code paths" warning.
6. `tail -50 "$HOME/Library/Application Support/PrusaSlicer3-dev/shared_runtime/log.txt"`
   shows no errors naming our bundle.

If a command does not appear in the menu at all, that is the silent-failure mode:
check `luac -p` on that file and check nothing calls `api` or `require` at file
level.

- [ ] **Step 10: Re-sync and confirm the bundle is rebuilt cleanly**

The hand patches from Steps 7 and 8 make a good final test of the atomic swap:

```bash
.venv/bin/printernizer-connect sync; echo "exit=$?"
.venv/bin/printernizer-connect doctor; echo "exit=$?"
```
Expected: `sync` reports the same number of commands and `changed` is reported
(the patched files differ from what it renders), the fabricated `-1.stl` asset is
gone, `doctor` exits 0, and no `.printernizer-connect.tmp` is left in the datadir.

- [ ] **Step 11: Write the README**

Cover: what it does; **install — editable only for now** (`python -m venv .venv &&
.venv/bin/pip install -e .`), with an explicit note that a plain wheel does not yet
carry `bundle_template/` and that packaging it is an M3 item; the three commands;
that the server needs **2.43.0 or newer**; that Home Assistant users must expose the
add-on's port rather than using an ingress URL; that print settings are currently
null for every library entry, so no command offers the settings checkbox yet; and
that the download cache under the config directory is not pruned automatically.

- [ ] **Step 12: Commit**

```bash
git add -A && git commit -m "docs: Add README and end-to-end acceptance record

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-review

**Spec coverage.** §4.1 layout → Tasks 1–8 (`hooks/`, `presets.py`, `profiles.py`, `physical_printers.py` are deliberately absent — M3/M4/M5). §4.2 CLI → Task 8 (`hook` and `profiles` are out of scope). §4.3 config/state → Task 1. §4.4 datadir → Task 3. §5.1 flat bundle → Tasks 5, 7. §5.2 command template → Tasks 5, 7. §5.3 Lua lib → Task 5. §5.5 scope/grouping → Task 4. §5.6 conversion → Task 6. §5.7 atomic swap → Task 7. §5.8 failure model → Task 7 `_verify` + Task 8 `doctor`.

**Deliberate gaps, with reasons.** `printer` grouping is dropped — `printer_model` is never returned by the library API. Tag grouping is implemented but yields nothing until entries are tagged (every tag is at `usage_count: 0`). Hard-linking unchanged assets is simplified to a checksum-keyed download cache, and that cache is **never pruned** — `doctor` reports its size so it is at least visible; pruning is M3. Installation is **editable-only**: `bundle_template/` lives at the repo root, so a wheel built from this tree does not carry it; moving the templates into the package is M3. Print settings are null on every real library entry today, so the `apply_settings` checkbox and the `object_params` path appear on no generated command — Task 9 exercises that path with a hand-edited command instead.

**Type consistency.** `Entry` fields are identical in Tasks 4, 7 and their tests. `GenResult(written, skipped, changed, bytes_written)` matches its uses in Task 8. `generate(entries, lua_dir, client, template_dir, cache_dir, size_budget_mb)` is called with the same arguments in Task 8 as Task 7 defines. `to_stl_parts` returns `(names, offsets)` in Tasks 6 and 7. `Client` method names match across Tasks 2, 4, 7, 8. `BUNDLE_ID`, `TMP_NAME` and `referenced_assets` are defined once in Task 7 and imported by Task 8 (and by Task 9's helper scripts). `ConfigError` is defined in the shipped Task 1 module and caught in Task 8.
