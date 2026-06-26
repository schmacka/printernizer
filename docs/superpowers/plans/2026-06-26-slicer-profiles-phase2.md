# Slicer Profiles (Phase 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give users ready-to-use curated slicer profiles (Bambu A1 + Prusa CORE One, from OrcaSlicer's own bundled presets) and the ability to upload their own OrcaSlicer profiles, backend/API only.

**Architecture:** A profile's `settings_json` is the payload sent to the stateless slicer-service: `{"system_preset": {...names}}` for built-ins or `{"inline": {...full preset JSON}}` for uploads. The service gains `GET /profiles` (lists bundled presets) and `/slice` learns the `inline` shape. The app adds profile metadata columns, an idempotent built-in seeder, and an upload endpoint.

**Tech Stack:** Python 3.11/3.13, FastAPI, aiosqlite, aiohttp, OrcaSlicer presets (JSON), pytest (`asyncio_mode = auto`).

## Global Constraints

- Work on branch **`feature/slicer-phase2-profiles`** (this worktree is already on it). Conventional Commits; end each commit message with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Run app tests from the worktree root with the shared venv, output to a file, never bare:
  `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest <path> -p no:cacheprovider --timeout=60 -q`
- Run slicer-service tests from `slicer-service/` with `PYTHONPATH=.` and that same venv python.
- Tests use `asyncio_mode = auto` (plain `async def test_...`).
- **DB tests MUST close the Database** (`await db.close()` in a fixture `finally`) or the pytest process hangs at exit (leaked aiosqlite threads).
- **SQLite foreign keys are ON**; rows referenced by FKs must exist before insert.
- Next migration file is **`035_*.sql`** (highest existing is `034`). `Database.initialize()` runs the `migrations/` folder, so tests pick up new migrations.
- New DB columns are appended at the **end** of the table; positional `_row_to_*` mappers read appended indices with a `len(row)` guard.
- API routers: `@router.post("/profiles/upload")` etc. — never a bare `"/"`.
- OrcaSlicer preset JSON has `"type": "machine" | "process" | "filament"` and a `"name"`. `nozzle_diameter` is a JSON array (e.g. `["0.4"]`).
- Profile payload shapes (verbatim):
  - built-in: `{"system_preset": {"machine": "<name>", "process": "<name>", "filament": "<name>"}}`
  - upload: `{"inline": {"machine": {<preset>}, "process": {<preset>}, "filament": {<preset>}}}`
- English for all code/comments/logging.

---

## File structure

**Slicer-service (new deployable, already shipped in Phase 1):**
- `slicer-service/app/profiles.py` (NEW) — `list_bundled_profiles(root) -> dict` (pure).
- `slicer-service/app/main.py` (MODIFY) — add `GET /profiles`.
- `slicer-service/app/runner.py` (MODIFY) — `BaseRunner.profiles_root` attr; `_build_settings` handles `inline`.
- `slicer-service/tests/test_profiles.py`, `slicer-service/tests/test_runner_inline.py` (NEW).

**App (image unchanged):**
- `migrations/035_slicer_profile_metadata.sql` (NEW).
- `src/models/slicer.py` (MODIFY) — `SlicerProfile` gains `source`/`printer_model`/`is_builtin`.
- `src/services/slicer_service.py` (MODIFY) — `create_profile` writes new columns; `_row_to_profile` reads them; `seed_builtin_profiles()` + `_fetch_service_profiles()`; `create_uploaded_profile()`; call seeder from `initialize`.
- `src/api/routers/slicing.py` (MODIFY) — `POST /profiles/upload`.
- `tests/services/test_slicer_profile_metadata.py`, `test_builtin_seeder.py`, `test_profile_upload.py` (NEW).

---

### Task 0: Confirm branch

- [ ] **Step 1: Verify worktree branch**

Run: `git -C /projects/printernizer-repos/printernizer-phase2-wt branch --show-current`
Expected: `feature/slicer-phase2-profiles`. All work happens in this worktree.

---

### Task 1: Migration 035 + SlicerProfile metadata fields

**Files:**
- Create: `migrations/035_slicer_profile_metadata.sql`
- Modify: `src/models/slicer.py` (`SlicerProfile`)
- Modify: `src/services/slicer_service.py` (`create_profile`, `_row_to_profile`)
- Create: `tests/services/test_slicer_profile_metadata.py`

**Interfaces:**
- Produces: `SlicerProfile.source: str = "import"`, `SlicerProfile.printer_model: Optional[str] = None`, `SlicerProfile.is_builtin: bool = False`. `create_profile` accepts `source`/`printer_model`/`is_builtin` keys in `profile_data`.

- [ ] **Step 1: Write failing test** (`tests/services/test_slicer_profile_metadata.py`)

```python
import pytest
from src.database.database import Database
from src.services.slicer_service import SlicerService
from src.services.event_service import EventService


@pytest.fixture
async def svc(temp_database):
    db = Database(temp_database)
    await db.initialize()
    try:
        yield SlicerService(db, EventService())
    finally:
        await db.close()


async def _slicer(svc):
    return await svc.register_slicer({
        "name": "Svc", "slicer_type": "orcaslicer", "executable_path": "",
        "backend_type": "remote", "endpoint_url": "http://x"})


async def test_profile_metadata_roundtrip(svc):
    s = await _slicer(svc)
    p = await svc.create_profile(s.id, {
        "profile_name": "P", "profile_type": "bundle",
        "settings_json": '{"system_preset":{}}',
        "source": "builtin", "printer_model": "Bambu Lab A1", "is_builtin": True})
    assert p.source == "builtin" and p.printer_model == "Bambu Lab A1" and p.is_builtin is True
    again = await svc.get_profile(p.id)
    assert again.is_builtin is True and again.source == "builtin"


async def test_profile_defaults(svc):
    s = await _slicer(svc)
    p = await svc.create_profile(s.id, {"profile_name": "Q", "profile_type": "print"})
    assert p.source == "import" and p.is_builtin is False and p.printer_model is None
```

- [ ] **Step 2: Run, verify fail**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_slicer_profile_metadata.py -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — `source`/`is_builtin` attributes or columns missing.

- [ ] **Step 3: Create `migrations/035_slicer_profile_metadata.sql`**

```sql
-- Migration: 035_slicer_profile_metadata.sql
-- Description: Add source/printer_model/is_builtin to slicer_profiles for
--              curated (built-in) and uploaded profiles.
-- Date: 2026-06-26

ALTER TABLE slicer_profiles ADD COLUMN source TEXT NOT NULL DEFAULT 'import';
ALTER TABLE slicer_profiles ADD COLUMN printer_model TEXT;
ALTER TABLE slicer_profiles ADD COLUMN is_builtin INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_slicer_profiles_source ON slicer_profiles(source);
```

- [ ] **Step 4: Add fields to `SlicerProfile`** (`src/models/slicer.py`, after `is_default`)

```python
    is_default: bool = False
    source: str = "import"
    printer_model: Optional[str] = None
    is_builtin: bool = False
```

- [ ] **Step 5: Update `create_profile` INSERT and `_row_to_profile`** (`src/services/slicer_service.py`)

In `create_profile`, extend the INSERT (append the three columns):

```python
            await conn.execute(
                """
                INSERT INTO slicer_profiles (
                    id, slicer_id, profile_name, profile_type, profile_path,
                    settings_json, compatible_printers, is_default,
                    created_at, updated_at,
                    source, printer_model, is_builtin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id, slicer_id, profile_data["profile_name"],
                    profile_data["profile_type"], profile_data.get("profile_path"),
                    profile_data.get("settings_json"),
                    profile_data.get("compatible_printers"),
                    profile_data.get("is_default", False),
                    now, now,
                    profile_data.get("source", "import"),
                    profile_data.get("printer_model"),
                    profile_data.get("is_builtin", False),
                ),
            )
```

Update `_row_to_profile` (appended columns are indices 10/11/12; original through index 9):

```python
    def _row_to_profile(self, row) -> SlicerProfile:
        return SlicerProfile(
            id=row[0], slicer_id=row[1], profile_name=row[2], profile_type=row[3],
            profile_path=row[4], settings_json=row[5], compatible_printers=row[6],
            is_default=bool(row[7]),
            created_at=datetime.fromisoformat(row[8]),
            updated_at=datetime.fromisoformat(row[9]),
            source=(row[10] if len(row) > 10 else None) or "import",
            printer_model=row[11] if len(row) > 11 else None,
            is_builtin=bool(row[12]) if len(row) > 12 else False,
        )
```

- [ ] **Step 6: Run, verify pass**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_slicer_profile_metadata.py -p no:cacheprovider --timeout=60 -q`
Expected: 2 passed.

- [ ] **Step 7: Commit**

```bash
git add migrations/035_slicer_profile_metadata.sql src/models/slicer.py src/services/slicer_service.py tests/services/test_slicer_profile_metadata.py
git commit -m "feat: add source/printer_model/is_builtin to slicer profiles

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Slicer-service `GET /profiles`

**Files:**
- Create: `slicer-service/app/profiles.py`
- Modify: `slicer-service/app/main.py`, `slicer-service/app/runner.py`
- Create: `slicer-service/tests/test_profiles.py`

**Interfaces:**
- Produces: `list_bundled_profiles(root: str) -> dict` returning `{"vendors": {vendor: {"machine": [names], "process": [names], "filament": [names]}}}`. `BaseRunner.profiles_root: str = ""`. Route `GET /profiles` → that dict.

- [ ] **Step 1: Write failing test** (`slicer-service/tests/test_profiles.py`)

```python
import json
from fastapi.testclient import TestClient
from app.profiles import list_bundled_profiles
from app.main import create_app
from app.runner import BaseRunner, RunnerResult


def _stub_tree(tmp_path):
    for vendor, kind, name in [
        ("BBL", "machine", "Bambu Lab A1 0.4 nozzle"),
        ("BBL", "process", "0.20mm Standard @BBL A1"),
        ("BBL", "filament", "Bambu PLA Basic @BBL A1"),
        ("Prusa", "machine", "Prusa CORE One 0.4 nozzle"),
    ]:
        d = tmp_path / vendor / kind
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.json").write_text(json.dumps({"type": kind, "name": name}))
    return str(tmp_path)


def test_list_bundled_profiles(tmp_path):
    out = list_bundled_profiles(_stub_tree(tmp_path))
    assert "Bambu Lab A1 0.4 nozzle" in out["vendors"]["BBL"]["machine"]
    assert "0.20mm Standard @BBL A1" in out["vendors"]["BBL"]["process"]
    assert "Prusa CORE One 0.4 nozzle" in out["vendors"]["Prusa"]["machine"]


class _StubRunner(BaseRunner):
    async def slice(self, model_path, profile, output_dir):
        return RunnerResult(True, None, 1, 1.0, None)


def test_profiles_endpoint(tmp_path):
    runner = _StubRunner()
    runner.profiles_root = _stub_tree(tmp_path)
    client = TestClient(create_app(runner))
    r = client.get("/profiles")
    assert r.status_code == 200
    assert "BBL" in r.json()["vendors"]
```

- [ ] **Step 2: Run, verify fail**

Run: `cd slicer-service && PYTHONPATH=. /projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/test_profiles.py -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — `app.profiles` missing.

- [ ] **Step 3: Create `slicer-service/app/profiles.py`**

```python
"""List OrcaSlicer's bundled system presets from the profiles resource tree."""
from pathlib import Path
from typing import Dict, List

_KINDS = ("machine", "process", "filament")


def list_bundled_profiles(root: str) -> Dict:
    """Return {"vendors": {vendor: {machine:[], process:[], filament:[]}}}."""
    vendors: Dict[str, Dict[str, List[str]]] = {}
    base = Path(root) if root else None
    if not base or not base.is_dir():
        return {"vendors": vendors}
    for vendor_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        kinds: Dict[str, List[str]] = {k: [] for k in _KINDS}
        for kind in _KINDS:
            kdir = vendor_dir / kind
            if kdir.is_dir():
                kinds[kind] = sorted(f.stem for f in kdir.glob("*.json"))
        if any(kinds.values()):
            vendors[vendor_dir.name] = kinds
    return {"vendors": vendors}
```

- [ ] **Step 4: Add `profiles_root` to `BaseRunner`** (`slicer-service/app/runner.py`)

In `class BaseRunner:` add a class attribute at the top of the body:

```python
class BaseRunner:
    profiles_root: str = ""

    async def slice(self, model_path: str, profile: dict, output_dir: str) -> RunnerResult:
        raise NotImplementedError
```

(`OrcaSlicerRunner.__init__` already sets `self.profiles_root`, which shadows the class attr — no change needed there.)

- [ ] **Step 5: Add the route** (`slicer-service/app/main.py`)

Add the import at top: `from app.profiles import list_bundled_profiles`. Add inside `create_app`, after `/version`:

```python
    @app.get("/profiles")
    async def profiles():
        return list_bundled_profiles(getattr(runner, "profiles_root", ""))
```

- [ ] **Step 6: Run, verify pass**

Run: `cd slicer-service && PYTHONPATH=. /projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/test_profiles.py -p no:cacheprovider --timeout=60 -q`
Expected: 2 passed.

- [ ] **Step 7: Commit**

```bash
git add slicer-service/app/profiles.py slicer-service/app/main.py slicer-service/app/runner.py slicer-service/tests/test_profiles.py
git commit -m "feat: slicer-service exposes GET /profiles (bundled presets)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Slicer-service `/slice` accepts `inline` payload

**Files:**
- Modify: `slicer-service/app/runner.py` (`OrcaSlicerRunner._build_settings`, `slice`)
- Create: `slicer-service/tests/test_runner_inline.py`

**Interfaces:**
- Consumes: payload `{"inline": {"machine": {...}, "process": {...}, "filament": {...}}}`.
- Produces: `OrcaSlicerRunner._build_settings(profile: dict, workdir: str) -> (process_path, machine_path, filament_path)` — for `inline`, writes each preset object to `<workdir>/_<kind>.json` and returns those paths.

- [ ] **Step 1: Write failing test** (`slicer-service/tests/test_runner_inline.py`)

```python
import json
from pathlib import Path
from app.runner import OrcaSlicerRunner


def test_build_settings_inline_writes_temp_files(tmp_path):
    runner = OrcaSlicerRunner("/nonexistent/AppRun", "/nonexistent/profiles")
    profile = {"inline": {
        "machine": {"type": "machine", "name": "M"},
        "process": {"type": "process", "name": "P"},
        "filament": {"type": "filament", "name": "F"},
    }}
    process, machine, filament = runner._build_settings(profile, str(tmp_path))
    assert Path(process).exists() and json.loads(Path(process).read_text())["name"] == "P"
    assert Path(machine).exists() and Path(filament).exists()
```

- [ ] **Step 2: Run, verify fail**

Run: `cd slicer-service && PYTHONPATH=. /projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/test_runner_inline.py -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — `_build_settings` takes one arg / no `inline` handling.

- [ ] **Step 3: Update `_build_settings` and its caller** (`slicer-service/app/runner.py`)

Replace the existing `_build_settings` with the `workdir`-aware version that handles `inline` first:

```python
    def _build_settings(self, profile: dict, workdir: str):
        if "inline" in profile:
            inl = profile["inline"]
            paths = {}
            for kind in ("machine", "process", "filament"):
                if inl.get(kind):
                    p = Path(workdir) / f"_{kind}.json"
                    p.write_text(json.dumps(inl[kind]))
                    paths[kind] = str(p)
            return paths.get("process"), paths.get("machine"), paths.get("filament")
        sp = profile.get("system_preset", {})
        if isinstance(sp, str):
            sp = {"process": sp}
        process = self._resolve_preset(sp["process"], "process") if sp.get("process") else None
        machine = self._resolve_preset(sp["machine"], "machine") if sp.get("machine") else None
        filament = self._resolve_preset(sp["filament"], "filament") if sp.get("filament") else None
        return process, machine, filament
```

In `slice(...)`, update the call from `self._build_settings(profile)` to:

```python
        process, machine, filament = self._build_settings(profile, output_dir)
```

- [ ] **Step 4: Run, verify pass**

Run: `cd slicer-service && PYTHONPATH=. /projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/test_runner_inline.py tests/ -p no:cacheprovider --timeout=60 -q`
Expected: all passed (new test + existing service tests).

- [ ] **Step 5: Commit**

```bash
git add slicer-service/app/runner.py slicer-service/tests/test_runner_inline.py
git commit -m "feat: slicer-service /slice accepts inline profile content

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Built-in profile seeder

**Files:**
- Modify: `src/services/slicer_service.py` (`CURATED_BUILTINS`, `seed_builtin_profiles`, `_fetch_service_profiles`, call from `initialize`)
- Create: `tests/services/test_builtin_seeder.py`

**Interfaces:**
- Consumes: `create_profile`, `list_slicers`, `list_profiles`.
- Produces: `async SlicerService.seed_builtin_profiles(fetch_profiles=None)` where `fetch_profiles(endpoint_url) -> dict` (the `/profiles` JSON). Idempotent; resilient to missing names / unreachable service.

- [ ] **Step 1: Write failing test** (`tests/services/test_builtin_seeder.py`)

```python
import pytest
from src.database.database import Database
from src.services.slicer_service import SlicerService
from src.services.event_service import EventService

FULL = {"vendors": {
    "BBL": {"machine": ["Bambu Lab A1 0.4 nozzle"],
            "process": ["0.20mm Standard @BBL A1"],
            "filament": ["Bambu PLA Basic @BBL A1"]},
    "Prusa": {"machine": ["Prusa CORE One 0.4 nozzle"],
              "process": ["0.20mm SPEED @CORE One 0.4"],
              "filament": ["Prusa Generic PLA @CORE One"]}}}


@pytest.fixture
async def svc(temp_database):
    db = Database(temp_database)
    await db.initialize()
    try:
        yield SlicerService(db, EventService())
    finally:
        await db.close()


async def _remote(svc):
    return await svc.register_slicer({
        "name": "Svc", "slicer_type": "orcaslicer", "executable_path": "",
        "backend_type": "remote", "endpoint_url": "http://x"})


async def test_seeds_both_and_idempotent(svc):
    s = await _remote(svc)
    async def fetch(url): return FULL
    await svc.seed_builtin_profiles(fetch_profiles=fetch)
    names = {p.profile_name for p in await svc.list_profiles(slicer_id=s.id) if p.is_builtin}
    assert len(names) == 2
    await svc.seed_builtin_profiles(fetch_profiles=fetch)  # idempotent
    assert len({p.profile_name for p in await svc.list_profiles(slicer_id=s.id) if p.is_builtin}) == 2


async def test_skips_missing_presets(svc):
    s = await _remote(svc)
    partial = {"vendors": {"BBL": FULL["vendors"]["BBL"]}}  # no Prusa
    async def fetch(url): return partial
    await svc.seed_builtin_profiles(fetch_profiles=fetch)
    builtins = [p for p in await svc.list_profiles(slicer_id=s.id) if p.is_builtin]
    assert len(builtins) == 1 and builtins[0].printer_model == "Bambu Lab A1"


async def test_no_remote_slicer_is_noop(svc):
    async def fetch(url): raise AssertionError("should not fetch")
    await svc.seed_builtin_profiles(fetch_profiles=fetch)  # no slicer registered
```

- [ ] **Step 2: Run, verify fail**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_builtin_seeder.py -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — `seed_builtin_profiles` missing.

- [ ] **Step 3: Implement seeder** (`src/services/slicer_service.py`)

Add `import json` if not present at the top (it is). Add a module-level constant and the methods (place the methods near `register_remote_slicer_from_env`):

```python
CURATED_BUILTINS = [
    {"printer_model": "Bambu Lab A1", "profile_name": "A1 — 0.20mm Standard PLA",
     "machine": "Bambu Lab A1 0.4 nozzle", "process": "0.20mm Standard @BBL A1",
     "filament": "Bambu PLA Basic @BBL A1"},
    {"printer_model": "Prusa CORE One", "profile_name": "CORE One — 0.20mm PLA",
     "machine": "Prusa CORE One 0.4 nozzle", "process": "0.20mm SPEED @CORE One 0.4",
     "filament": "Prusa Generic PLA @CORE One"},
]
```

```python
    async def _fetch_service_profiles(self, endpoint_url: str) -> dict:
        import aiohttp
        base = (endpoint_url or "").rstrip("/")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base}/profiles") as r:
                return await r.json()

    async def seed_builtin_profiles(self, fetch_profiles=None) -> None:
        """Seed curated built-in profiles for the remote slicer (idempotent)."""
        remotes = [s for s in await self.list_slicers() if s.backend_type == "remote"]
        if not remotes:
            return
        slicer = remotes[0]
        fetch = fetch_profiles or self._fetch_service_profiles
        try:
            data = await fetch(slicer.endpoint_url)
        except Exception as e:  # noqa: BLE001
            logger.warning("Could not fetch slicer profiles for seeding", error=str(e))
            return
        available = {"machine": set(), "process": set(), "filament": set()}
        for v in (data or {}).get("vendors", {}).values():
            for kind in available:
                available[kind].update(v.get(kind, []))
        existing = {p.profile_name for p in await self.list_profiles(slicer_id=slicer.id)}
        for c in CURATED_BUILTINS:
            if c["profile_name"] in existing:
                continue
            missing = [c[k] for k in ("machine", "process", "filament") if c[k] not in available[k]]
            if missing:
                logger.warning("Skipping builtin profile; presets missing",
                               profile=c["profile_name"], missing=missing)
                continue
            await self.create_profile(slicer.id, {
                "profile_name": c["profile_name"], "profile_type": "bundle",
                "source": "builtin", "is_builtin": True, "printer_model": c["printer_model"],
                "settings_json": json.dumps({"system_preset": {
                    "machine": c["machine"], "process": c["process"], "filament": c["filament"]}}),
            })
            logger.info("Seeded builtin profile", profile=c["profile_name"])
```

In `initialize`, after `await self.register_remote_slicer_from_env()`:

```python
        await self.seed_builtin_profiles()
```

- [ ] **Step 4: Run, verify pass**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_builtin_seeder.py -p no:cacheprovider --timeout=60 -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/services/slicer_service.py tests/services/test_builtin_seeder.py
git commit -m "feat: seed curated built-in slicer profiles (A1, Core One)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Profile upload endpoint

**Files:**
- Modify: `src/services/slicer_service.py` (`create_uploaded_profile`)
- Modify: `src/api/routers/slicing.py` (`POST /profiles/upload`)
- Create: `tests/services/test_profile_upload.py`

**Interfaces:**
- Produces: `async SlicerService.create_uploaded_profile(slicer_id: str, name: str, files: list[tuple[str, bytes]], printer_model: Optional[str] = None) -> SlicerProfile`. Raises `ValueError` on invalid input. Endpoint `POST /api/v1/slicing/profiles/upload` (multipart: `slicer_id`, `name`, optional `printer_model`, `files`).

- [ ] **Step 1: Write failing test** (`tests/services/test_profile_upload.py`)

```python
import json
import pytest
from src.database.database import Database
from src.services.slicer_service import SlicerService
from src.services.event_service import EventService


@pytest.fixture
async def svc(temp_database):
    db = Database(temp_database)
    await db.initialize()
    try:
        yield SlicerService(db, EventService())
    finally:
        await db.close()


async def _remote(svc):
    return await svc.register_slicer({
        "name": "Svc", "slicer_type": "orcaslicer", "executable_path": "",
        "backend_type": "remote", "endpoint_url": "http://x"})


def _files():
    return [
        ("m.json", json.dumps({"type": "machine", "name": "Bambu Lab A1 0.4 nozzle"}).encode()),
        ("p.json", json.dumps({"type": "process", "name": "My 0.16 fine"}).encode()),
        ("f.json", json.dumps({"type": "filament", "name": "My PLA"}).encode()),
    ]


async def test_upload_assembles_inline_profile(svc):
    s = await _remote(svc)
    p = await svc.create_uploaded_profile(s.id, "My A1 profile", _files(), printer_model="Bambu Lab A1")
    assert p.source == "upload" and p.is_builtin is False
    payload = json.loads(p.settings_json)
    assert set(payload["inline"].keys()) == {"machine", "process", "filament"}
    assert payload["inline"]["process"]["name"] == "My 0.16 fine"


async def test_upload_rejects_missing_part(svc):
    s = await _remote(svc)
    only_two = _files()[:2]  # no filament
    with pytest.raises(ValueError):
        await svc.create_uploaded_profile(s.id, "incomplete", only_two)


async def test_upload_rejects_bad_json(svc):
    s = await _remote(svc)
    with pytest.raises(ValueError):
        await svc.create_uploaded_profile(s.id, "bad", [("x.json", b"not json")])
```

- [ ] **Step 2: Run, verify fail**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_profile_upload.py -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — `create_uploaded_profile` missing.

- [ ] **Step 3: Implement `create_uploaded_profile`** (`src/services/slicer_service.py`)

```python
    async def create_uploaded_profile(self, slicer_id, name, files, printer_model=None):
        """Assemble an uploaded OrcaSlicer profile (machine+process+filament JSON)."""
        import json
        parts = {}
        for filename, content in files:
            try:
                obj = json.loads(content)
            except (ValueError, TypeError):
                raise ValueError(f"{filename}: not valid JSON")
            ptype = obj.get("type")
            if ptype not in ("machine", "process", "filament"):
                raise ValueError(f"{filename}: unrecognized preset type {ptype!r}")
            if ptype in parts:
                raise ValueError(f"duplicate {ptype} preset")
            parts[ptype] = obj
        missing = [k for k in ("machine", "process", "filament") if k not in parts]
        if missing:
            raise ValueError(f"missing required presets: {', '.join(missing)}")
        if not printer_model:
            printer_model = parts["machine"].get("name")
        return await self.create_profile(slicer_id, {
            "profile_name": name, "profile_type": "bundle",
            "source": "upload", "is_builtin": False, "printer_model": printer_model,
            "settings_json": json.dumps({"inline": {
                "machine": parts["machine"], "process": parts["process"],
                "filament": parts["filament"]}}),
        })
```

- [ ] **Step 4: Run, verify pass**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_profile_upload.py -p no:cacheprovider --timeout=60 -q`
Expected: 3 passed.

- [ ] **Step 5: Add the endpoint** (`src/api/routers/slicing.py`)

Add `UploadFile, File, Form` to the FastAPI import line:

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
```

Add the endpoint (place it near the other profile endpoints):

```python
@router.post("/profiles/upload", response_model=SlicerProfile)
async def upload_profile(
    slicer_id: str = Form(...),
    name: str = Form(...),
    printer_model: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    slicer_service: SlicerService = Depends(get_slicer_service),
):
    """Upload OrcaSlicer preset JSON files (machine + process + filament) as one profile."""
    try:
        payload = [(f.filename or "file.json", await f.read()) for f in files]
        return await slicer_service.create_uploaded_profile(
            slicer_id, name, payload, printer_model=printer_model)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PrinternizerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:  # noqa: BLE001
        logger.error("Profile upload failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Upload failed: {str(e)}")
```

- [ ] **Step 6: Verify router imports cleanly**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -c "import src.api.routers.slicing"`
Expected: no error.

- [ ] **Step 7: Commit**

```bash
git add src/services/slicer_service.py src/api/routers/slicing.py tests/services/test_profile_upload.py
git commit -m "feat: add OrcaSlicer profile upload endpoint

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: Full-suite verification + PR

- [ ] **Step 1: Run all new app tests**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_slicer_profile_metadata.py tests/services/test_builtin_seeder.py tests/services/test_profile_upload.py -p no:cacheprovider --timeout=60 -q`
Expected: all passed.

- [ ] **Step 2: Run the existing slicer suite (no regressions)**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_slicing_queue.py tests/services/test_slicer_backends.py tests/services/test_remote_http_backend.py tests/services/test_slicer_backend_fields.py tests/services/test_remote_registration.py -p no:cacheprovider --timeout=60 -q`
Expected: all passed.

- [ ] **Step 3: Run the slicer-service suite**

Run: `cd slicer-service && PYTHONPATH=. /projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/ -p no:cacheprovider --timeout=60 -q`
Expected: all passed.

- [ ] **Step 4: Push + PR**

```bash
git push -u origin feature/slicer-phase2-profiles
gh pr create --base master --title "feat: Slicer integration Phase 2 — curated + uploadable profiles" --body "Phase 2 of slicer integration. See docs/superpowers/specs/2026-06-25-slicer-profiles-phase2-design.md."
```

---

## Verification (end-to-end, real image)
1. Rebuild/run the slicer-service image; `GET /profiles` lists BBL + Prusa presets.
2. Start the app with `SLICER_SERVICE_URL` set → on boot, two built-in profiles (A1, Core One) appear (`GET /api/v1/slicing/<slicer_id>/profiles`, `is_builtin=true`).
3. `POST /api/v1/slicing/profiles/upload` with a tweaked A1 process + the A1 machine + a PLA filament → a `source=upload` profile is created; slicing a cube with it produces gcode (exercises the `inline` path through the service).
4. `pytest tests/services/ -q` (full services dir) stays green aside from the 4 pre-existing `test_printer_service.py` failures noted in Phase 1.

## Self-review notes
- Spec coverage: `/profiles` (Task 2), `inline` slice (Task 3), migration/model (Task 1), built-in seeder w/ resilience+idempotency (Task 4), upload w/ type-categorization + all-three rule (Task 5). Payload contract used consistently.
- Deliberately omitted (per spec out-of-scope): UI, `.ini` upload, inheritance flattening, persisting nozzle/layer (no column — only `printer_model` persisted; nozzle/layer can be added with a future metadata column).
