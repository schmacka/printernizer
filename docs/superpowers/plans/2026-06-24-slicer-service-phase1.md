# Slicer Service (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make STL→gcode slicing actually run for container/Home-Assistant deployments by shipping a standalone multi-arch slicer microservice and wiring Printernizer to it through a pluggable backend, without changing the main app image.

**Architecture:** A new `slicer-service/` FastAPI microservice (own image, Ubuntu-24.04/trixie base) wraps the OrcaSlicer CLI. Printernizer's `SlicingQueue` stops shelling out directly and instead delegates to a `SlicerBackend` resolved from the slicer config — `RemoteHTTPBackend` (the service) or `LocalProcessBackend` (a slicer installed on the host). The main `docker/Dockerfile` is untouched.

**Tech Stack:** Python 3.11, FastAPI, aiosqlite, aiohttp (app→service HTTP), OrcaSlicer v2.4.0 aarch64/x86_64 AppImage, pytest (`asyncio_mode = auto`), Docker buildx.

## Global Constraints

- Work on a feature branch off `master` (repo rule): `feature/slicer-service-phase1`. Never commit to `master` directly.
- Conventional Commits for messages (`feat:`, `test:`, `refactor:`, `chore:`).
- API routers: use `@router.post("")` / `@router.get("")` for root paths — **never** `"/"` (project has `redirect_slashes=False`).
- Services inherit `BaseService`; new DB columns are added **at the end** of the table (positional `_row_to_*` mappers rely on column order).
- Next migration file is **`034_*.sql`** (highest existing is `033`). Migrations run sorted by filename via `MigrationService`.
- Tests use `asyncio_mode = auto` (plain `async def test_...`, no `@pytest.mark.asyncio` needed). App service tests live in `tests/services/`; use the `temp_database` fixture + `Database(temp_database)` + `await database.initialize()`.
- The **slicer-service image base must be Ubuntu 24.04 / Debian trixie (glibc ≥ 2.38)** — the OrcaSlicer binary needs `GLIBC_2.38` and bundles no libc. The main app image stays `python:3.11-slim-bookworm`.
- OrcaSlicer AppImage extraction must be **FUSE-free**: locate the appended squashfs (`grep -abom1 hsqs <file>`) and `unsquashfs -o <offset>`, then run the inner `squashfs-root/AppRun` under `xvfb-run -a`.
- Engine CLI is OrcaSlicer-native: `AppRun --load-settings "<process>;<machine>" --load-filaments "<filament>" --slice 0 --outputdir <dir> <model>`; success is signalled by `result.json` `return_code: 0`.
- Language: English for all logging, comments, copy.

---

## File structure

**Main app (image unchanged):**
- `src/utils/gcode_metadata.py` (NEW) — extracted + extended gcode metadata parser.
- `src/services/slicing_queue.py` (MODIFY) — import parser from new util; delegate `_execute_job` to a backend.
- `migrations/034_slicer_backends.sql` (NEW) — `backend_type`, `endpoint_url` on `slicer_configs`.
- `src/models/slicer.py` (MODIFY) — `backend_type`, `endpoint_url` on `SlicerConfig`.
- `src/services/slicer_backends/__init__.py`, `base.py`, `local_process.py`, `remote_http.py` (NEW).
- `src/services/slicer_service.py` (MODIFY) — `get_backend()`, register remote slicer on startup, updated row mapper.
- `docker/docker-compose.yml` (MODIFY) — add `slicer` service + `SLICER_SERVICE_URL`.

**Slicer microservice (new deployable):**
- `slicer-service/app/main.py` (NEW) — FastAPI app + routes.
- `slicer-service/app/runner.py` (NEW) — `BaseRunner`, `OrcaSlicerRunner`.
- `slicer-service/app/jobs.py` (NEW) — in-memory job store + background slice task.
- `slicer-service/app/gcode_metadata.py` (NEW) — vendored copy of the parser (separate deployable, intentional duplication).
- `slicer-service/requirements.txt`, `slicer-service/Dockerfile` (NEW).
- `slicer-service/tests/test_api.py`, `slicer-service/tests/test_runner.py` (NEW).
- `ha-addon/printernizer-slicer/config.yaml` + `Dockerfile` (NEW, documented for the printernizer-ha repo).

**Tests (app):**
- `tests/services/test_gcode_metadata.py`, `tests/services/test_slicer_backends.py`, `tests/services/test_slicing_queue_backend.py` (NEW).

---

### Task 0: Create feature branch

- [ ] **Step 1: Branch off master**

```bash
cd /projects/printernizer-repos/printernizer
git checkout master && git pull origin master
git checkout -b feature/slicer-service-phase1
```

- [ ] **Step 2: Verify clean state**

Run: `git status`
Expected: `On branch feature/slicer-service-phase1`, nothing to commit.

---

### Task 1: Extract + fix the gcode metadata parser

**Why:** The spike proved the current `parse_gcode_metadata` returns `None` for OrcaSlicer print time (`; total estimated time: 40m 39s` / `; model printing time: 33m 52s` match nothing). Extract it to a shared util and add OrcaSlicer/Bambu patterns.

**Files:**
- Create: `src/utils/gcode_metadata.py`
- Create: `tests/services/test_gcode_metadata.py`
- Modify: `src/services/slicing_queue.py` (remove the local `GCodeMetadata`/`parse_gcode_metadata`/`_parse_human_time`, import from util)

**Interfaces:**
- Produces: `class GCodeMetadata` (attrs `estimated_print_time: Optional[int]`, `filament_used: Optional[float]`); `def parse_gcode_metadata(gcode_path: str) -> GCodeMetadata`; `def parse_metadata_from_text(text: str) -> GCodeMetadata`.

- [ ] **Step 1: Write failing tests** (`tests/services/test_gcode_metadata.py`)

```python
from src.utils.gcode_metadata import parse_metadata_from_text

ORCA_SAMPLE = "\n".join([
    "; model printing time: 33m 52s; total estimated time: 40m 39s",
    "; estimated first layer printing time (normal mode) = 6m 46s",
    "; filament used [mm] = 1343.10",
    "; filament used [cm3] = 3.23",
])
PRUSA_SAMPLE = "\n".join([
    "; estimated printing time (normal mode) = 1h 30m 15s",
    "; filament used [g] = 15.23",
])

def test_orca_total_estimated_time_parsed():
    md = parse_metadata_from_text(ORCA_SAMPLE)
    assert md.estimated_print_time == 40 * 60 + 39  # 2439s, NOT the first-layer 6m46s

def test_orca_filament_converted_from_mm():
    md = parse_metadata_from_text(ORCA_SAMPLE)
    assert md.filament_used is not None
    assert round(md.filament_used, 1) == 4.0

def test_prusa_still_parses():
    md = parse_metadata_from_text(PRUSA_SAMPLE)
    assert md.estimated_print_time == 3600 + 30 * 60 + 15
    assert md.filament_used == 15.23
```

- [ ] **Step 2: Run, verify fail**

Run: `pytest tests/services/test_gcode_metadata.py -v`
Expected: FAIL — `ModuleNotFoundError: src.utils.gcode_metadata`.

- [ ] **Step 3: Create `src/utils/gcode_metadata.py`**

Move the existing `GCodeMetadata`, `parse_gcode_metadata`, `_parse_human_time` from `src/services/slicing_queue.py` verbatim, then (a) add a `parse_metadata_from_text(text)` helper and have `parse_gcode_metadata` read the file and call it, and (b) prepend two OrcaSlicer time patterns. Full file:

```python
"""Gcode metadata extraction (print time + filament), slicer-agnostic.

Shared by SlicingQueue (app) and vendored into the slicer-service image.
"""
import re
from typing import Optional
import structlog

logger = structlog.get_logger()


class GCodeMetadata:
    def __init__(self):
        self.estimated_print_time: Optional[int] = None  # seconds
        self.filament_used: Optional[float] = None  # grams


# Order matters: most specific / most correct first.
TIME_PATTERNS = [
    # OrcaSlicer/BambuStudio total: "; total estimated time: 40m 39s"
    (r';\s*(?:model printing|total estimated) time:\s*(.+?)$', 'human'),
    # PrusaSlicer/OrcaSlicer: "; estimated printing time (normal mode) = 1h 30m 15s"
    # NB: must not match "estimated first layer printing time"
    (r';\s*estimated printing time.*?=\s*(.+?)$', 'human'),
    (r';\s*TIME:\s*(\d+)', 'seconds'),
    (r';\s*total estimated time.*?=\s*(\d+)', 'seconds'),
    (r';\s*print_time\s*=\s*(\d+)', 'seconds'),
]

FILAMENT_PATTERNS = [
    (r';\s*(?:total\s+)?filament used \[g\]\s*=\s*([\d.]+)', 'grams'),
    (r';\s*filament used \[mm\]\s*=\s*([\d.]+)', 'mm'),
    (r';\s*Filament used:\s*([\d.]+)\s*m(?:m)?', 'cura'),
    (r';\s*filament_used\s*=\s*([\d.]+)', 'grams'),
    (r';\s*filament weight\s*=\s*([\d.]+)', 'grams'),
]


def _parse_human_time(time_str: str) -> Optional[int]:
    if not time_str:
        return None
    total = 0
    mult = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
    for value, unit in re.findall(r'(\d+)\s*([dhms])', time_str.strip(), re.IGNORECASE):
        total += int(value) * mult[unit.lower()]
    return total or None


def parse_metadata_from_text(text: str) -> GCodeMetadata:
    md = GCodeMetadata()
    lines = text.splitlines()
    for pattern, fmt in TIME_PATTERNS:
        if md.estimated_print_time is not None:
            break
        for line in lines:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                val = int(m.group(1)) if fmt == 'seconds' else _parse_human_time(m.group(1))
                if val:
                    md.estimated_print_time = val
                    break
    for pattern, fmt in FILAMENT_PATTERNS:
        if md.filament_used is not None:
            break
        for line in lines:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                v = float(m.group(1))
                if fmt == 'grams':
                    md.filament_used = v
                elif fmt == 'mm':
                    md.filament_used = (v / 1000.0) * 2.98
                elif fmt == 'cura':
                    md.filament_used = v * 2.98 if v < 100 else (v / 1000.0) * 2.98
                if md.filament_used is not None:
                    break
    return md


def parse_gcode_metadata(gcode_path: str) -> GCodeMetadata:
    """Read header (first 500 lines) + footer (last 200 lines) and parse."""
    try:
        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            header = [ln for i, ln in zip(range(500), f)]
            f.seek(0, 2)
            size = f.tell()
            if size > 50000:
                f.seek(max(0, size - 50000))
                f.readline()
                footer = f.readlines()[-200:]
            else:
                f.seek(0)
                all_lines = f.readlines()
                footer = all_lines[-200:] if len(all_lines) > 200 else []
        return parse_metadata_from_text("".join(header + footer))
    except Exception as e:
        logger.warning("Failed to parse G-code metadata", path=gcode_path, error=str(e))
        return GCodeMetadata()
```

- [ ] **Step 4: Update `src/services/slicing_queue.py` to import from the util**

Delete the in-module `GCodeMetadata`, `parse_gcode_metadata`, `_parse_human_time` definitions (lines ~32–224) and add near the top imports:

```python
from src.utils.gcode_metadata import GCodeMetadata, parse_gcode_metadata
```

- [ ] **Step 5: Run tests + import check**

Run: `pytest tests/services/test_gcode_metadata.py -v && python -c "import src.services.slicing_queue"`
Expected: 3 passed; import OK.

- [ ] **Step 6: Commit**

```bash
git add src/utils/gcode_metadata.py tests/services/test_gcode_metadata.py src/services/slicing_queue.py
git commit -m "fix: extract gcode parser to util and support OrcaSlicer print-time"
```

---

### Task 2: Migration 034 + SlicerConfig backend fields

**Files:**
- Create: `migrations/034_slicer_backends.sql`
- Modify: `src/models/slicer.py` (`SlicerConfig`)
- Modify: `src/services/slicer_service.py` (`_row_to_slicer_config`, `register_slicer`, `update_slicer` allowed_fields)
- Create: `tests/services/test_slicer_backend_fields.py`

**Interfaces:**
- Produces: `SlicerConfig.backend_type: str = "local"`, `SlicerConfig.endpoint_url: Optional[str] = None`.

- [ ] **Step 1: Write failing test** (`tests/services/test_slicer_backend_fields.py`)

```python
from src.database.database import Database
from src.services.slicer_service import SlicerService
from src.services.event_service import EventService


async def _service(temp_database):
    db = Database(temp_database)
    await db.initialize()
    return SlicerService(db, EventService())


async def test_register_remote_slicer_persists_backend_fields(temp_database):
    svc = await _service(temp_database)
    cfg = await svc.register_slicer({
        "name": "Remote Orca", "slicer_type": "orcaslicer",
        "executable_path": "", "backend_type": "remote",
        "endpoint_url": "http://slicer:8001",
    })
    assert cfg.backend_type == "remote"
    assert cfg.endpoint_url == "http://slicer:8001"
    again = await svc.get_slicer(cfg.id)
    assert again.endpoint_url == "http://slicer:8001"
```

- [ ] **Step 2: Run, verify fail**

Run: `pytest tests/services/test_slicer_backend_fields.py -v`
Expected: FAIL — column/attr `backend_type` missing.

- [ ] **Step 3: Create `migrations/034_slicer_backends.sql`**

```sql
-- Migration: 034_slicer_backends.sql
-- Description: Add pluggable backend fields to slicer_configs (remote slicer service)
-- Date: 2026-06-24

ALTER TABLE slicer_configs ADD COLUMN backend_type TEXT NOT NULL DEFAULT 'local';
ALTER TABLE slicer_configs ADD COLUMN endpoint_url TEXT;

CREATE INDEX IF NOT EXISTS idx_slicer_configs_backend ON slicer_configs(backend_type);
```

- [ ] **Step 4: Add fields to `SlicerConfig`** (`src/models/slicer.py`, after `config_dir`)

```python
    config_dir: Optional[str] = None
    backend_type: str = "local"
    endpoint_url: Optional[str] = None
    is_available: bool = True
```

- [ ] **Step 5: Update `slicer_service.py`**

In `register_slicer`, extend the INSERT to include the two new columns (append them after `config_dir`):

```python
            await conn.execute(
                """
                INSERT INTO slicer_configs (
                    id, name, slicer_type, executable_path, version, config_dir,
                    backend_type, endpoint_url,
                    is_available, last_verified, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slicer_id, slicer_data["name"], slicer_data["slicer_type"],
                    slicer_data["executable_path"], slicer_data.get("version"),
                    slicer_data.get("config_dir"),
                    slicer_data.get("backend_type", "local"),
                    slicer_data.get("endpoint_url"),
                    True, now, now, now,
                ),
            )
```

Update `_row_to_slicer_config` (columns appended after index 5, so old 6–9 shift to 8–11):

```python
    def _row_to_slicer_config(self, row) -> SlicerConfig:
        return SlicerConfig(
            id=row[0], name=row[1], slicer_type=row[2], executable_path=row[3],
            version=row[4], config_dir=row[5],
            backend_type=row[6] or "local", endpoint_url=row[7],
            is_available=bool(row[8]),
            last_verified=datetime.fromisoformat(row[9]) if row[9] else None,
            created_at=datetime.fromisoformat(row[10]),
            updated_at=datetime.fromisoformat(row[11]),
        )
```

Add `"backend_type"`, `"endpoint_url"` to `update_slicer`'s `allowed_fields`.

- [ ] **Step 6: Run test**

Run: `pytest tests/services/test_slicer_backend_fields.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add migrations/034_slicer_backends.sql src/models/slicer.py src/services/slicer_service.py tests/services/test_slicer_backend_fields.py
git commit -m "feat: add backend_type/endpoint_url to slicer config"
```

---

### Task 3: SlicerBackend abstraction + SliceResult

**Files:**
- Create: `src/services/slicer_backends/__init__.py`
- Create: `src/services/slicer_backends/base.py`
- Create: `tests/services/test_slicer_backends.py`

**Interfaces:**
- Produces: `@dataclass SliceResult(success: bool, output_path: Optional[str], estimated_print_time: Optional[int], filament_used: Optional[float], error_message: Optional[str] = None)`; `class SlicerBackend(ABC)` with `async def slice(self, input_path: str, profile: SlicerProfile, output_path: str, progress_cb: Optional[Callable[[int], Awaitable[None]]] = None) -> SliceResult`, `async def verify(self) -> bool`, `async def version(self) -> Optional[str]`.

- [ ] **Step 1: Write failing test**

```python
import pytest
from src.services.slicer_backends.base import SlicerBackend, SliceResult


def test_sliceresult_defaults():
    r = SliceResult(success=True, output_path="/x.gcode",
                    estimated_print_time=10, filament_used=1.0)
    assert r.error_message is None and r.success is True


def test_backend_is_abstract():
    with pytest.raises(TypeError):
        SlicerBackend()  # abstract, cannot instantiate
```

- [ ] **Step 2: Run, verify fail**

Run: `pytest tests/services/test_slicer_backends.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Create `__init__.py` (empty) and `base.py`**

```python
"""Slicer backend abstraction: how a slicing job is actually executed."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable

from src.models.slicer import SlicerProfile

ProgressCb = Optional[Callable[[int], Awaitable[None]]]


@dataclass
class SliceResult:
    success: bool
    output_path: Optional[str]
    estimated_print_time: Optional[int]
    filament_used: Optional[float]
    error_message: Optional[str] = None


class SlicerBackend(ABC):
    @abstractmethod
    async def slice(self, input_path: str, profile: SlicerProfile,
                    output_path: str, progress_cb: ProgressCb = None) -> SliceResult:
        ...

    @abstractmethod
    async def verify(self) -> bool:
        ...

    @abstractmethod
    async def version(self) -> Optional[str]:
        ...
```

- [ ] **Step 4: Run, verify pass**

Run: `pytest tests/services/test_slicer_backends.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/services/slicer_backends/__init__.py src/services/slicer_backends/base.py tests/services/test_slicer_backends.py
git commit -m "feat: add SlicerBackend abstraction and SliceResult"
```

---

### Task 4: LocalProcessBackend (host-installed slicer)

**Why:** Preserves "use a slicer already on this box" and isolates per-engine CLI command building (OrcaSlicer ≠ PrusaSlicer).

**Files:**
- Create: `src/services/slicer_backends/local_process.py`
- Modify: `tests/services/test_slicer_backends.py` (append)

**Interfaces:**
- Consumes: `SlicerBackend`, `SliceResult`, `SlicerConfig`, `parse_gcode_metadata`.
- Produces: `class LocalProcessBackend(SlicerBackend)` constructed as `LocalProcessBackend(slicer: SlicerConfig)`; classmethod-free; uses `asyncio.create_subprocess_exec`. Static helper `build_command(slicer_type, executable, input_path, profile, output_path) -> list[str]`.

- [ ] **Step 1: Write failing tests** (append)

```python
from src.services.slicer_backends.local_process import LocalProcessBackend, build_command
from src.models.slicer import SlicerConfig, SlicerProfile, ProfileType
from datetime import datetime


def _profile(path="/tmp/p.ini", settings=None):
    return SlicerProfile(id="p", slicer_id="s", profile_name="P",
                         profile_type=ProfileType.PRINT, profile_path=path,
                         settings_json=settings, created_at=datetime.now(),
                         updated_at=datetime.now())


def test_build_command_prusaslicer():
    cmd = build_command("prusaslicer", "/usr/bin/prusa-slicer",
                        "/in.stl", _profile(), "/out/o.gcode")
    assert cmd[0] == "/usr/bin/prusa-slicer"
    assert "--export-gcode" in cmd and "--load" in cmd and "/in.stl" in cmd


def test_build_command_orcaslicer():
    prof = _profile(path=None, settings='{"machine":"/m.json","process":"/p.json","filament":"/f.json"}')
    cmd = build_command("orcaslicer", "/opt/orca/AppRun", "/in.stl", prof, "/out/o.gcode")
    assert "--slice" in cmd and "--load-settings" in cmd and "--load-filaments" in cmd


async def test_local_backend_runs_fake_slicer(tmp_path):
    # Fake slicer: writes a canned gcode then exits 0
    fake = tmp_path / "fakeslicer.sh"
    fake.write_text(
        "#!/bin/bash\n"
        'out=""; while [ $# -gt 0 ]; do [ "$1" = "--output" ] && out="$2"; shift; done\n'
        'printf "; estimated printing time (normal mode) = 1h 0m 0s\\n; filament used [g] = 5.0\\n" > "$out"\n'
    )
    fake.chmod(0o755)
    cfg = SlicerConfig(id="s", name="Fake", slicer_type="prusaslicer",
                       executable_path=str(fake), backend_type="local",
                       created_at=datetime.now(), updated_at=datetime.now())
    backend = LocalProcessBackend(cfg)
    out = tmp_path / "o.gcode"
    res = await backend.slice("/in.stl", _profile(path=str(tmp_path / "p.ini")), str(out))
    assert res.success and res.estimated_print_time == 3600 and res.filament_used == 5.0
```

(Create the dummy profile file in the test if needed: `(tmp_path / "p.ini").write_text("x")` before slicing.)

- [ ] **Step 2: Run, verify fail**

Run: `pytest tests/services/test_slicer_backends.py -v`
Expected: FAIL — `local_process` missing.

- [ ] **Step 3: Implement `local_process.py`**

```python
"""Backend that runs a slicer binary installed on the same host."""
import asyncio
import json
from pathlib import Path
from typing import Optional, List
import structlog

from src.models.slicer import SlicerConfig, SlicerProfile
from src.services.slicer_backends.base import SlicerBackend, SliceResult, ProgressCb
from src.utils.gcode_metadata import parse_gcode_metadata

logger = structlog.get_logger()


def build_command(slicer_type: str, executable: str, input_path: str,
                  profile: SlicerProfile, output_path: str) -> List[str]:
    if slicer_type in ("orcaslicer", "bambustudio"):
        s = json.loads(profile.settings_json or "{}")
        settings = ";".join(p for p in (s.get("process"), s.get("machine")) if p)
        cmd = [executable, "--slice", "0", "--outputdir", str(Path(output_path).parent)]
        if settings:
            cmd += ["--load-settings", settings]
        if s.get("filament"):
            cmd += ["--load-filaments", s["filament"]]
        cmd.append(input_path)
        return cmd
    # PrusaSlicer / SuperSlicer
    cmd = [executable, "--export-gcode", "--output", output_path]
    if profile.profile_path and Path(profile.profile_path).exists():
        cmd += ["--load", profile.profile_path]
    cmd.append(input_path)
    return cmd


class LocalProcessBackend(SlicerBackend):
    def __init__(self, slicer: SlicerConfig):
        self.slicer = slicer

    async def slice(self, input_path: str, profile: SlicerProfile,
                    output_path: str, progress_cb: ProgressCb = None) -> SliceResult:
        cmd = build_command(self.slicer.slicer_type, self.slicer.executable_path,
                            input_path, profile, output_path)
        logger.info("Local slice", cmd=cmd)
        if progress_cb:
            await progress_cb(20)
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            return SliceResult(False, None, None, None,
                               stderr.decode("utf-8", "ignore")[:2000])
        if not Path(output_path).exists():
            return SliceResult(False, None, None, None, "Output file was not created")
        md = parse_gcode_metadata(output_path)
        if progress_cb:
            await progress_cb(100)
        return SliceResult(True, output_path, md.estimated_print_time, md.filament_used)

    async def verify(self) -> bool:
        return bool(self.slicer.executable_path and Path(self.slicer.executable_path).exists())

    async def version(self) -> Optional[str]:
        return self.slicer.version
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/services/test_slicer_backends.py -v`
Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add src/services/slicer_backends/local_process.py tests/services/test_slicer_backends.py
git commit -m "feat: add LocalProcessBackend with per-engine command building"
```

---

### Task 5: RemoteHTTPBackend (talks to the slicer service)

**Files:**
- Create: `src/services/slicer_backends/remote_http.py`
- Create: `tests/services/test_remote_http_backend.py`

**Interfaces:**
- Consumes: `SlicerBackend`, `SliceResult`, `SlicerConfig`.
- Produces: `class RemoteHTTPBackend(SlicerBackend)` constructed as `RemoteHTTPBackend(slicer: SlicerConfig, session_factory=aiohttp.ClientSession)`. Contract with the service: `POST {endpoint}/slice` (multipart `file`, form `profile` = JSON) → `{"job_id": ...}`; `GET {endpoint}/slice/{id}` → `{"status","progress","estimated_print_time","filament_used","error"}`; `GET {endpoint}/slice/{id}/result` → gcode bytes. Terminal statuses: `completed`, `failed`.

- [ ] **Step 1: Write failing test** (uses a fake session — no network, no extra deps)

```python
import json
from datetime import datetime
from src.services.slicer_backends.remote_http import RemoteHTTPBackend
from src.models.slicer import SlicerConfig, SlicerProfile, ProfileType


class _Resp:
    def __init__(self, payload=None, data=b""):
        self._payload, self._data, self.status = payload, data, 200
    async def json(self): return self._payload
    async def read(self): return self._data
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False


class _Session:
    """Scripts: POST->job_id, GET status->completed, GET result->bytes."""
    def __init__(self):
        self.gcode = b"; estimated printing time (normal mode) = 0h 40m 39s\n; filament used [g] = 4.0\n"
    def post(self, url, data=None): return _Resp(payload={"job_id": "j1"})
    def get(self, url):
        if url.endswith("/result"):
            return _Resp(data=self.gcode)
        return _Resp(payload={"status": "completed", "progress": 100,
                              "estimated_print_time": 2439, "filament_used": 4.0, "error": None})
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False


def _cfg():
    return SlicerConfig(id="s", name="Remote", slicer_type="orcaslicer",
                        executable_path="", backend_type="remote",
                        endpoint_url="http://slicer:8001",
                        created_at=datetime.now(), updated_at=datetime.now())


async def test_remote_slice_downloads_result(tmp_path):
    prof = SlicerProfile(id="p", slicer_id="s", profile_name="A1",
                         profile_type=ProfileType.PRINT,
                         settings_json=json.dumps({"system_preset": "0.20mm Standard @BBL A1"}),
                         created_at=datetime.now(), updated_at=datetime.now())
    backend = RemoteHTTPBackend(_cfg(), session_factory=lambda: _Session(),
                                poll_interval=0)
    (tmp_path / "in.stl").write_text("solid x\nendsolid x\n")
    out = tmp_path / "o.gcode"
    res = await backend.slice(str(tmp_path / "in.stl"), prof, str(out))
    assert res.success and res.estimated_print_time == 2439
    assert out.exists() and out.read_bytes().startswith(b"; estimated")
```

- [ ] **Step 2: Run, verify fail**

Run: `pytest tests/services/test_remote_http_backend.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Implement `remote_http.py`**

```python
"""Backend that delegates slicing to the standalone slicer microservice."""
import asyncio
import json
from pathlib import Path
from typing import Optional, Callable
import aiohttp
import structlog

from src.models.slicer import SlicerConfig, SlicerProfile
from src.services.slicer_backends.base import SlicerBackend, SliceResult, ProgressCb

logger = structlog.get_logger()

TERMINAL = {"completed", "failed"}


class RemoteHTTPBackend(SlicerBackend):
    def __init__(self, slicer: SlicerConfig,
                 session_factory: Callable[[], aiohttp.ClientSession] = aiohttp.ClientSession,
                 poll_interval: float = 2.0, timeout_s: int = 3600):
        self.slicer = slicer
        self.base = (slicer.endpoint_url or "").rstrip("/")
        self._session_factory = session_factory
        self._poll = poll_interval
        self._timeout = timeout_s

    def _profile_payload(self, profile: SlicerProfile) -> str:
        return profile.settings_json or json.dumps({"profile_name": profile.profile_name})

    async def slice(self, input_path: str, profile: SlicerProfile,
                    output_path: str, progress_cb: ProgressCb = None) -> SliceResult:
        async with self._session_factory() as session:
            form = aiohttp.FormData()
            form.add_field("profile", self._profile_payload(profile))
            form.add_field("file", open(input_path, "rb"),
                           filename=Path(input_path).name,
                           content_type="application/octet-stream")
            async with session.post(f"{self.base}/slice", data=form) as r:
                job_id = (await r.json())["job_id"]

            waited = 0.0
            while True:
                async with session.get(f"{self.base}/slice/{job_id}") as r:
                    st = await r.json()
                if progress_cb and st.get("progress") is not None:
                    await progress_cb(int(st["progress"]))
                if st["status"] in TERMINAL:
                    break
                if waited >= self._timeout:
                    return SliceResult(False, None, None, None, "Remote slice timed out")
                await asyncio.sleep(self._poll)
                waited += self._poll

            if st["status"] == "failed":
                return SliceResult(False, None, None, None, st.get("error") or "Remote slice failed")

            async with session.get(f"{self.base}/slice/{job_id}/result") as r:
                data = await r.read()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(data)
            return SliceResult(True, output_path, st.get("estimated_print_time"),
                               st.get("filament_used"))

    async def verify(self) -> bool:
        try:
            async with self._session_factory() as session:
                async with session.get(f"{self.base}/health") as r:
                    return r.status == 200
        except Exception:
            return False

    async def version(self) -> Optional[str]:
        try:
            async with self._session_factory() as session:
                async with session.get(f"{self.base}/version") as r:
                    return (await r.json()).get("version")
        except Exception:
            return None
```

- [ ] **Step 4: Run test**

Run: `pytest tests/services/test_remote_http_backend.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/services/slicer_backends/remote_http.py tests/services/test_remote_http_backend.py
git commit -m "feat: add RemoteHTTPBackend talking to slicer service"
```

---

### Task 6: SlicerService.get_backend() + SlicingQueue delegation

**Files:**
- Modify: `src/services/slicer_service.py` (add `get_backend`)
- Modify: `src/services/slicing_queue.py` (`_execute_job` delegates)
- Create: `tests/services/test_slicing_queue_backend.py`

**Interfaces:**
- Consumes: `LocalProcessBackend`, `RemoteHTTPBackend`, `SliceResult`.
- Produces: `SlicerService.get_backend(slicer_id: str) -> SlicerBackend` (returns `RemoteHTTPBackend` when `backend_type == "remote"`, else `LocalProcessBackend`).

- [ ] **Step 1: Write failing test** (`tests/services/test_slicing_queue_backend.py`)

Tests that `_execute_job` uses the resolved backend and writes results. Inject a fake backend by monkeypatching `slicer_service.get_backend`.

```python
from datetime import datetime
from src.database.database import Database
from src.services.event_service import EventService
from src.services.slicer_service import SlicerService
from src.services.slicing_queue import SlicingQueue
from src.services.slicer_backends.base import SliceResult
from src.models.slicer import SlicerProfile, ProfileType, SlicingJobRequest


class _FakeBackend:
    async def slice(self, input_path, profile, output_path, progress_cb=None):
        with open(output_path, "w") as f:
            f.write("; sliced\n")
        if progress_cb:
            await progress_cb(100)
        return SliceResult(True, output_path, 1234, 7.5)
    async def verify(self): return True
    async def version(self): return "test"


async def test_execute_job_uses_backend(temp_database, tmp_path, monkeypatch):
    db = Database(temp_database); await db.initialize()
    events = EventService()
    slicer_service = SlicerService(db, events)
    cfg = await slicer_service.register_slicer({
        "name": "Remote", "slicer_type": "orcaslicer", "executable_path": "",
        "backend_type": "remote", "endpoint_url": "http://x"})
    profile = await slicer_service.create_profile(cfg.id, {
        "profile_name": "A1", "profile_type": "print",
        "settings_json": '{"system_preset":"x"}'})

    async def _fake_get_backend(sid):  # get_backend is async
        return _FakeBackend()
    monkeypatch.setattr(slicer_service, "get_backend", _fake_get_backend)

    # library file with a real input path (FK enforcement is ON, so the row must exist)
    model = tmp_path / "in.stl"; model.write_text("solid x\nendsolid x\n")
    async with db.connection() as conn:
        await conn.execute(
            "INSERT INTO library_files (id, checksum, filename, library_path, file_size, file_type) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("lf1", "abc", "in.stl", str(model), 10, ".stl"))
        await conn.commit()

    class _Lib:
        async def get_file_by_checksum(self, c): return {"file_path": str(model)}
    queue = SlicingQueue(db, events, slicer_service, library_service=_Lib())
    queue._output_dir = tmp_path / "out"; queue._output_dir.mkdir()

    job = await queue.create_job(SlicingJobRequest(
        file_checksum="abc", slicer_id=cfg.id, profile_id=profile.id))
    # let the queued task finish
    import asyncio
    for _ in range(50):
        j = await queue.get_job(job.id)
        if j.status in ("completed", "failed"):
            break
        await asyncio.sleep(0.05)
    j = await queue.get_job(job.id)
    assert j.status == "completed"
    assert j.estimated_print_time == 1234 and j.filament_used == 7.5
```

- [ ] **Step 2: Run, verify fail**

Run: `pytest tests/services/test_slicing_queue_backend.py -v`
Expected: FAIL — `get_backend` missing / `_execute_job` still shells out.

- [ ] **Step 3: Add `get_backend` to `slicer_service.py`**

```python
    async def get_backend(self, slicer_id: str):
        from src.services.slicer_backends.local_process import LocalProcessBackend
        from src.services.slicer_backends.remote_http import RemoteHTTPBackend
        slicer = await self.get_slicer(slicer_id)
        if slicer.backend_type == "remote":
            return RemoteHTTPBackend(slicer)
        return LocalProcessBackend(slicer)
```

- [ ] **Step 4: Refactor `SlicingQueue._execute_job`**

Replace the command-building + subprocess + metadata block (the body between "Get input file from library" and the DB update) so it resolves a backend and calls it. **Also remove the old local-detector check** `is_available = await self.slicer_service.verify_slicer_availability(job.slicer_id)` (it wrongly fails remote slicers, whose `executable_path` is empty) and verify through the backend instead. Keep the surrounding status/progress/retry/auto-upload logic and the `get_profile` call. The new core:

```python
            input_file = Path(library_file["file_path"])
            if not input_file.exists():
                raise Exception(f"Input file not found: {input_file}")

            output_filename = f"{input_file.stem}_{job_id[:8]}.gcode"
            output_file = self._output_dir / output_filename
            await self._update_job_progress(job_id, 10)

            backend = await self.slicer_service.get_backend(job.slicer_id)
            if not await backend.verify():
                raise Exception("Slicer backend is not available")

            async def _progress(p: int):
                await self._update_job_progress(job_id, max(10, min(99, p)))

            result = await backend.slice(
                str(input_file), profile, str(output_file), progress_cb=_progress)

            if not result.success:
                raise Exception(result.error_message or "Slicing failed")

            async with self.db.connection() as conn:
                await conn.execute(
                    """
                    UPDATE slicing_jobs
                    SET output_file_path = ?, status = ?, progress = ?,
                        estimated_print_time = ?, filament_used = ?,
                        completed_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (result.output_path, SlicingJobStatus.COMPLETED.value, 100,
                     result.estimated_print_time, result.filament_used,
                     datetime.now(), datetime.now(), job_id),
                )
                await conn.commit()
```

Remove the now-dead local `cmd = [...]`, `create_subprocess_exec`, manual progress-loop, and `parse_gcode_metadata(...)` call inside `_execute_job` (parsing now lives in the backend). Keep `verify_slicer_availability`, the `library_service` guard, `event_service.emit("slicing_job.completed", ...)`, and the `auto_upload` branch.

- [ ] **Step 5: Run tests**

Run: `pytest tests/services/test_slicing_queue_backend.py tests/services/test_gcode_metadata.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/services/slicer_service.py src/services/slicing_queue.py tests/services/test_slicing_queue_backend.py
git commit -m "feat: delegate SlicingQueue execution to resolved SlicerBackend"
```

---

### Task 7: Slicer microservice (FastAPI app + runner)

**Why:** The actual slicing engine, in its own deployable. Tested with a stub runner (the real OrcaSlicer binary is exercised in Task 8's build smoke test, not in unit tests).

**Files:**
- Create: `slicer-service/app/__init__.py`, `slicer-service/app/main.py`, `slicer-service/app/runner.py`, `slicer-service/app/jobs.py`
- Create: `slicer-service/app/gcode_metadata.py` (copy of `src/utils/gcode_metadata.py`)
- Create: `slicer-service/requirements.txt`
- Create: `slicer-service/tests/test_api.py`

**Interfaces:**
- Produces (HTTP, consumed by `RemoteHTTPBackend`): `GET /health` → `{"status":"ok"}`; `GET /version` → `{"version": str}`; `GET /profiles` → `{"profiles": [...]}`; `POST /slice` (multipart `file`, form `profile`) → `{"job_id": str}`; `GET /slice/{job_id}` → `{"status","progress","estimated_print_time","filament_used","error"}`; `GET /slice/{job_id}/result` → gcode file.
- Produces (Python): `class BaseRunner` with `async def slice(self, model_path: str, profile: dict, output_dir: str) -> RunnerResult`; `@dataclass RunnerResult(success, gcode_path, estimated_print_time, filament_used, error)`; `create_app(runner: BaseRunner) -> FastAPI`.

- [ ] **Step 1: `slicer-service/requirements.txt`**

```
fastapi>=0.110
uvicorn[standard]>=0.27
python-multipart>=0.0.9
structlog>=23.2.0
```

- [ ] **Step 2: Copy the parser** — copy `src/utils/gcode_metadata.py` to `slicer-service/app/gcode_metadata.py` verbatim (it only imports `re`, `structlog`).

- [ ] **Step 3: Write failing API test** (`slicer-service/tests/test_api.py`)

```python
import io, json
from fastapi.testclient import TestClient
from app.main import create_app
from app.runner import BaseRunner, RunnerResult


class StubRunner(BaseRunner):
    async def slice(self, model_path, profile, output_dir):
        p = f"{output_dir}/plate_1.gcode"
        with open(p, "w") as f:
            f.write("; total estimated time: 40m 39s\n; filament used [mm] = 1343.10\n")
        return RunnerResult(True, p, 2439, 4.0, None)


def test_slice_flow():
    client = TestClient(create_app(StubRunner()))
    assert client.get("/health").json()["status"] == "ok"
    r = client.post("/slice",
                    files={"file": ("cube.stl", io.BytesIO(b"solid x\nendsolid x\n"))},
                    data={"profile": json.dumps({"system_preset": "x"})})
    job_id = r.json()["job_id"]
    status = client.get(f"/slice/{job_id}").json()
    assert status["status"] == "completed"
    assert status["estimated_print_time"] == 2439
    result = client.get(f"/slice/{job_id}/result")
    assert result.status_code == 200 and result.content.startswith(b"; total")
```

- [ ] **Step 4: Run, verify fail**

Run: `cd slicer-service && python -m pytest tests/test_api.py -v`
Expected: FAIL — `app` missing.

- [ ] **Step 5: Implement `runner.py`**

```python
"""Slicer runners: a stub for tests, OrcaSlicer for production."""
import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import structlog

from app.gcode_metadata import parse_gcode_metadata

logger = structlog.get_logger()


@dataclass
class RunnerResult:
    success: bool
    gcode_path: Optional[str]
    estimated_print_time: Optional[int]
    filament_used: Optional[float]
    error: Optional[str]


class BaseRunner:
    async def slice(self, model_path: str, profile: dict, output_dir: str) -> RunnerResult:
        raise NotImplementedError

    def version(self) -> str:
        return "stub"


class OrcaSlicerRunner(BaseRunner):
    """Runs the extracted OrcaSlicer AppRun headless under xvfb."""

    def __init__(self, apprun: str, profiles_root: str):
        self.apprun = apprun                # e.g. /opt/orca/squashfs-root/AppRun
        self.profiles_root = profiles_root  # .../resources/profiles

    def _resolve_preset(self, name: str, kind: str) -> Optional[str]:
        # kind in {machine, process, filament}; search vendor dirs for "<name>.json"
        root = Path(self.profiles_root)
        for path in root.glob(f"*/{kind}/{name}.json"):
            return str(path)
        return None

    def _build_settings(self, profile: dict):
        sp = profile.get("system_preset", {})
        if isinstance(sp, str):
            sp = {"process": sp}
        process = self._resolve_preset(sp.get("process", ""), "process") if sp.get("process") else None
        machine = self._resolve_preset(sp.get("machine", ""), "machine") if sp.get("machine") else None
        filament = self._resolve_preset(sp.get("filament", ""), "filament") if sp.get("filament") else None
        return process, machine, filament

    def version(self) -> str:
        return os.environ.get("ORCA_VERSION", "orca")

    async def slice(self, model_path, profile, output_dir) -> RunnerResult:
        process, machine, filament = self._build_settings(profile)
        settings = ";".join(p for p in (process, machine) if p)
        cmd = ["xvfb-run", "-a", self.apprun, "--debug", "2"]
        if settings:
            cmd += ["--load-settings", settings]
        if filament:
            cmd += ["--load-filaments", filament]
        cmd += ["--slice", "0", "--outputdir", output_dir, model_path]
        logger.info("orca slice", cmd=cmd)
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
        result_json = Path(output_dir) / "result.json"
        if result_json.exists():
            rc = json.loads(result_json.read_text()).get("return_code", 1)
            if rc != 0:
                return RunnerResult(False, None, None, None, f"return_code={rc}")
        gcodes = sorted(Path(output_dir).glob("*.gcode"))
        if proc.returncode != 0 or not gcodes:
            return RunnerResult(False, None, None, None,
                                stderr.decode("utf-8", "ignore")[:2000] or "no gcode produced")
        md = parse_gcode_metadata(str(gcodes[0]))
        return RunnerResult(True, str(gcodes[0]), md.estimated_print_time, md.filament_used, None)
```

- [ ] **Step 6: Implement `jobs.py`**

```python
"""In-memory job store + background slice execution."""
import asyncio
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict

from app.runner import BaseRunner


@dataclass
class Job:
    id: str
    status: str = "queued"           # queued|running|completed|failed
    progress: int = 0
    estimated_print_time: Optional[int] = None
    filament_used: Optional[float] = None
    error: Optional[str] = None
    gcode_path: Optional[str] = None
    workdir: str = ""


class JobStore:
    def __init__(self, runner: BaseRunner):
        self.runner = runner
        self._jobs: Dict[str, Job] = {}

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    async def submit(self, model_bytes: bytes, model_name: str, profile: dict) -> str:
        job = Job(id=str(uuid.uuid4()))
        job.workdir = tempfile.mkdtemp(prefix="slice_")
        model_path = str(Path(job.workdir) / model_name)
        with open(model_path, "wb") as f:
            f.write(model_bytes)
        self._jobs[job.id] = job
        asyncio.create_task(self._run(job, model_path, profile))
        return job.id

    async def _run(self, job: Job, model_path: str, profile: dict):
        job.status, job.progress = "running", 20
        try:
            res = await self.runner.slice(model_path, profile, job.workdir)
            if res.success:
                job.status, job.progress = "completed", 100
                job.estimated_print_time = res.estimated_print_time
                job.filament_used = res.filament_used
                job.gcode_path = res.gcode_path
            else:
                job.status, job.error = "failed", res.error
        except Exception as e:  # noqa: BLE001
            job.status, job.error = "failed", str(e)
```

- [ ] **Step 7: Implement `main.py`**

```python
"""FastAPI app for the Printernizer Slicer Service."""
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from app.runner import BaseRunner
from app.jobs import JobStore


def create_app(runner: BaseRunner) -> FastAPI:
    app = FastAPI(title="Printernizer Slicer Service")
    store = JobStore(runner)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/version")
    async def version():
        return {"version": runner.version()}

    @app.post("/slice")
    async def slice_endpoint(file: UploadFile = File(...), profile: str = Form("{}")):
        data = await file.read()
        job_id = await store.submit(data, file.filename or "model.stl", json.loads(profile))
        return {"job_id": job_id}

    @app.get("/slice/{job_id}")
    async def job_status(job_id: str):
        job = store.get(job_id)
        if not job:
            raise HTTPException(404, "job not found")
        return {"status": job.status, "progress": job.progress,
                "estimated_print_time": job.estimated_print_time,
                "filament_used": job.filament_used, "error": job.error}

    @app.get("/slice/{job_id}/result")
    async def job_result(job_id: str):
        job = store.get(job_id)
        if not job or job.status != "completed" or not job.gcode_path:
            raise HTTPException(404, "result not ready")
        return FileResponse(job.gcode_path, filename="output.gcode")

    return app
```

Add a module-level `app` for uvicorn at the bottom of `main.py` (built only when the real runner env is present):

```python
import os
def _default_app():
    apprun = os.environ.get("EMBEDDED_SLICER_PATH")
    profiles = os.environ.get("ORCA_PROFILES_ROOT", "")
    if apprun:
        from app.runner import OrcaSlicerRunner
        return create_app(OrcaSlicerRunner(apprun, profiles))
    from app.runner import BaseRunner
    return create_app(BaseRunner())
app = _default_app()
```

- [ ] **Step 8: Run service tests**

Run: `cd slicer-service && PYTHONPATH=. python -m pytest tests/ -v`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add slicer-service/app slicer-service/tests slicer-service/requirements.txt
git commit -m "feat: add slicer microservice (FastAPI + OrcaSlicer runner)"
```

---

### Task 8: Slicer-service multi-arch Dockerfile + build smoke test

**Why:** Package OrcaSlicer into the service image for amd64 + arm64 using the validated FUSE-free extraction, and prove an end-to-end real slice.

**Files:**
- Create: `slicer-service/Dockerfile`
- Create: `slicer-service/entrypoint.sh`

**Interfaces:**
- Produces: image exposing port `8001`; env `EMBEDDED_SLICER_PATH` (AppRun), `ORCA_PROFILES_ROOT`, `ORCA_VERSION`.

- [ ] **Step 1: Create `slicer-service/Dockerfile`**

```dockerfile
# Printernizer Slicer Service — OrcaSlicer (glibc >= 2.38 required)
FROM ubuntu:24.04

ARG TARGETARCH
ARG ORCA_VERSION=2.4.0
ENV DEBIAN_FRONTEND=noninteractive ORCA_VERSION=${ORCA_VERSION}

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv curl ca-certificates squashfs-tools \
      xvfb libopengl0 libglu1-mesa libgl1-mesa-dri libgl1 libegl1 \
      libgtk-3-0t64 libwebkit2gtk-4.1-0 libgstreamer1.0-0 \
      libgstreamer-plugins-base1.0-0 libfontconfig1 libsm6 libdbus-1-3 \
      libnss3 libxss1 libosmesa6 \
    && rm -rf /var/lib/apt/lists/*

# Download + FUSE-free extraction of the arch-specific AppImage
RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) A="OrcaSlicer_Linux_AppImage_Ubuntu2404_V${ORCA_VERSION}.AppImage" ;; \
      arm64) A="OrcaSlicer_Linux_AppImage_Ubuntu2404_aarch64_V${ORCA_VERSION}.AppImage" ;; \
      *) echo "unsupported arch ${TARGETARCH}"; exit 1 ;; \
    esac; \
    curl -fSL -o /tmp/orca.AppImage \
      "https://github.com/SoftFever/OrcaSlicer/releases/download/v${ORCA_VERSION}/${A}"; \
    OFF="$(grep -abom1 hsqs /tmp/orca.AppImage | cut -d: -f1)"; \
    mkdir -p /opt/orca; \
    unsquashfs -o "${OFF}" -d /opt/orca/squashfs-root /tmp/orca.AppImage; \
    rm /tmp/orca.AppImage

ENV EMBEDDED_SLICER_PATH=/opt/orca/squashfs-root/AppRun \
    ORCA_PROFILES_ROOT=/opt/orca/squashfs-root/resources/profiles \
    PYTHONPATH=/app

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8001
ENTRYPOINT ["/entrypoint.sh"]
```

- [ ] **Step 2: Create `slicer-service/entrypoint.sh`**

```bash
#!/bin/bash
set -e
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
```

- [ ] **Step 3: Build for arm64 + amd64**

Run:
```bash
cd slicer-service
docker buildx build --platform linux/arm64 -t printernizer-slicer:arm64 --load .
docker buildx build --platform linux/amd64 -t printernizer-slicer:amd64 --load .
```
Expected: both builds succeed; the `unsquashfs` step prints `created ... files`.

- [ ] **Step 4: Smoke-slice a real cube (arm64) end-to-end**

Run (uses the cube generated during the spike, or regenerate a 20mm cube STL):
```bash
docker run --rm --platform linux/arm64 -d --name slicetest -p 18001:8001 printernizer-slicer:arm64
sleep 8
curl -s -F "file=@cube.stl" \
     -F 'profile={"system_preset":{"machine":"Bambu Lab A1 0.4 nozzle","process":"0.20mm Standard @BBL A1","filament":"Bambu PLA Basic @BBL A1"}}' \
     http://localhost:18001/slice
# poll /slice/<job_id> until completed, then GET /slice/<job_id>/result
docker stop slicetest
```
Expected: status reaches `completed`, `estimated_print_time` ≈ 2439, result is non-empty gcode.

- [ ] **Step 5: Commit**

```bash
git add slicer-service/Dockerfile slicer-service/entrypoint.sh
git commit -m "feat: multi-arch slicer-service image with OrcaSlicer"
```

---

### Task 9: Deployment wiring (compose + app config + HA companion add-on)

**Files:**
- Modify: `docker/docker-compose.yml` (add `slicer` service + `SLICER_SERVICE_URL`)
- Modify: `src/services/slicer_service.py` (`initialize` registers the remote slicer from `SLICER_SERVICE_URL`)
- Create: `ha-addon/printernizer-slicer/config.yaml`, `ha-addon/printernizer-slicer/Dockerfile` (documented for the printernizer-ha repo)

**Interfaces:**
- Consumes: env `SLICER_SERVICE_URL` (default `http://slicer:8001`).
- Produces: a registered `slicer_configs` row with `backend_type='remote'` on startup when `SLICER_SERVICE_URL` is set and no remote slicer exists yet.

- [ ] **Step 1: Write failing test** (`tests/services/test_remote_registration.py`)

```python
import os
from src.database.database import Database
from src.services.event_service import EventService
from src.services.slicer_service import SlicerService


async def test_initialize_registers_remote_slicer(temp_database, monkeypatch):
    monkeypatch.setenv("SLICER_SERVICE_URL", "http://slicer:8001")
    db = Database(temp_database); await db.initialize()
    svc = SlicerService(db, EventService())
    await svc.register_remote_slicer_from_env()
    remotes = [s for s in await svc.list_slicers() if s.backend_type == "remote"]
    assert remotes and remotes[0].endpoint_url == "http://slicer:8001"
    # idempotent
    await svc.register_remote_slicer_from_env()
    remotes2 = [s for s in await svc.list_slicers() if s.backend_type == "remote"]
    assert len(remotes2) == 1
```

- [ ] **Step 2: Run, verify fail**

Run: `pytest tests/services/test_remote_registration.py -v`
Expected: FAIL — method missing.

- [ ] **Step 3: Add `register_remote_slicer_from_env` and call it from `initialize`**

```python
    async def register_remote_slicer_from_env(self) -> None:
        import os
        url = os.environ.get("SLICER_SERVICE_URL")
        if not url:
            return
        for s in await self.list_slicers():
            if s.backend_type == "remote" and s.endpoint_url == url:
                return  # already registered (idempotent)
        await self.register_slicer({
            "name": "Slicer Service", "slicer_type": "orcaslicer",
            "executable_path": "", "backend_type": "remote", "endpoint_url": url,
        })
        logger.info("Registered remote slicer service", url=url)
```

In `initialize`, after `detect_and_register_slicers()`:

```python
        await self.register_remote_slicer_from_env()
```

- [ ] **Step 4: Run test**

Run: `pytest tests/services/test_remote_registration.py -v`
Expected: PASS.

- [ ] **Step 5: Add the `slicer` service to `docker/docker-compose.yml`**

```yaml
  slicer:
    build:
      context: ../slicer-service
    image: ghcr.io/schmacka/printernizer-slicer:latest
    restart: unless-stopped
    expose:
      - "8001"
```

And add to the `printernizer` service `environment:` block:

```yaml
      - SLICER_SERVICE_URL=http://slicer:8001
```

- [ ] **Step 6: Create the HA companion add-on files**

`ha-addon/printernizer-slicer/config.yaml`:

```yaml
name: Printernizer Slicer
version: "0.1.0"
slug: printernizer_slicer
description: OrcaSlicer-based slicing service for Printernizer
arch:
  - aarch64
  - amd64
init: false
ports:
  8001/tcp: 8001
ports_description:
  8001/tcp: Slicer service API
```

`ha-addon/printernizer-slicer/Dockerfile`:

```dockerfile
ARG BUILD_FROM
FROM ghcr.io/schmacka/printernizer-slicer:latest
# BUILD_FROM is ignored; the slicer image is self-contained (Ubuntu 24.04 base).
```

Add a `README.md` in that dir noting: these files belong in the **printernizer-ha** repo as a second add-on; Printernizer's add-on gains a `slicer_service_url` option defaulting to `http://<slicer-addon-host>:8001`.

- [ ] **Step 7: Commit**

```bash
git add docker/docker-compose.yml src/services/slicer_service.py tests/services/test_remote_registration.py ha-addon/
git commit -m "feat: wire slicer service into compose, app startup, and HA add-on"
```

---

### Task 10: Full suite + branch wrap-up

- [ ] **Step 1: Run the app test suite**

Run: `pytest tests/services/ -v`
Expected: all new tests pass; no regressions in touched files.

- [ ] **Step 2: Run the slicer-service tests**

Run: `cd slicer-service && PYTHONPATH=. python -m pytest tests/ -v`
Expected: PASS.

- [ ] **Step 3: Push branch**

```bash
git push origin feature/slicer-service-phase1
```

- [ ] **Step 4: Open PR to master** (per repo workflow) summarizing: parser fix, backend abstraction, slicer microservice, deployment wiring. Note Phase 2 (profiles) and Phase 3 (library relation) follow.

---

## Verification (end-to-end)

1. `docker compose -f docker/docker-compose.yml up --build` → both `printernizer` and `slicer` start; app logs "Registered remote slicer service".
2. Upload an STL via the library, create a slicing job against the auto-registered "Slicer Service" slicer + an A1 profile → job reaches `completed`, gcode produced, `estimated_print_time`/`filament_used` populated (proves the parser fix end-to-end).
3. Auto-upload path: with `auto_upload`/`target_printer_id`, the existing `_handle_auto_upload` uploads to a (mock or real) printer — unchanged behavior.
4. `pytest tests/services/ -v` and the slicer-service suite both green.
5. Real-hardware check before release: run Task 8 Step 4 on an actual Raspberry Pi.

## Self-review notes
- Spec coverage: slicer service (Task 7–8), RemoteHTTP + LocalProcess backends (Task 4–5), SlicingQueue delegation (Task 6), parser fix (Task 1), migration/model (Task 2), deployment incl. HA companion add-on (Task 9) — all present.
- The OrcaSlicer 3-file profile model is represented as `SlicerProfile.settings_json` carrying `{"system_preset": {...}}`; the service resolves preset names against bundled `resources/profiles`. Richer profile UX (upload/curate) is intentionally deferred to Phase 2.
- Parser is duplicated in `slicer-service/app/gcode_metadata.py` on purpose (separate deployable, no shared import path).
