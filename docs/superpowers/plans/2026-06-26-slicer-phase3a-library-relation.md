# Slicer Phase 3a — Library model→printfile relation + API (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the library a model→printfile relation — classify files as `model` vs `printfile`, register slice outputs as printfiles linked to their source model, and expose the derived printfiles via API.

**Architecture:** A pure `classify_role` + a `zipfile`-based 3mf-gcode check decide roles. `library_files` gains `role`/`parent_checksum`. `add_file_to_library` sets them on ingest; a one-time backfill classifies existing rows; `SlicingQueue` registers each slice output as a `role='printfile'` row linked via `parent_checksum` to the source model (and sets `slicing_jobs.output_gcode_checksum`). `GET /files/{checksum}/printfiles` returns the derived printfiles enriched with slicing-job detail.

**Tech Stack:** Python 3.11/3.13, FastAPI, aiosqlite, pytest (`asyncio_mode = auto`).

## Global Constraints

- Work on branch **`feature/slicer-phase3a-library`** (this worktree is already on it). Conventional Commits; end each commit message with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Run tests from the worktree root with the shared venv, output to a file:
  `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest <path> -p no:cacheprovider --timeout=60 -q`
- `asyncio_mode = auto`. **DB tests MUST close the Database** (`await db.close()` in a fixture `finally`) or pytest hangs at exit.
- **SQLite foreign keys are ON.** `slicing_jobs.file_checksum` and `output_gcode_checksum` reference `library_files(checksum)` — referenced rows must exist before insert.
- Next migration is **`036_*.sql`** (highest existing is `035`). `Database.initialize()` runs the `migrations/` folder.
- New DB columns are appended at the **end** of the table.
- API routers: real sub-paths with leading slash are fine (`@router.get("/files/{checksum}/printfiles")`); never a bare `"/"`.
- `role` values are `"model"` | `"printfile"` | `None` (unclassified). Relation source of truth is the printfile's `parent_checksum`.
- English for all code/comments/logging.

---

## File structure
- `src/services/file_role_classifier.py` (NEW) — pure `classify_role` + `threemf_has_gcode`.
- `migrations/036_library_file_roles.sql` (NEW).
- `src/database/repositories/library_repository.py` (MODIFY) — `create_file` persists `role`/`parent_checksum`.
- `src/services/library_service.py` (MODIFY) — `add_file_to_library` role/parent kwargs + classification + `'slicer'` source; `classify_unroled_files()`; `get_printfiles_for_model()`.
- `src/services/slicing_queue.py` (MODIFY) — register slice output + set `output_gcode_checksum` (guarded).
- `src/api/routers/library.py` (MODIFY) — printfiles sub-resource.
- Tests: `tests/services/test_file_role_classifier.py`, `tests/services/test_library_roles.py`, `tests/services/test_printfiles_relation.py`, `tests/services/test_slice_output_registration.py`.

---

### Task 1: Role classifier (pure)

**Files:**
- Create: `src/services/file_role_classifier.py`
- Create: `tests/services/test_file_role_classifier.py`

**Interfaces:**
- Produces: `classify_role(file_type: str, threemf_has_gcode: Optional[bool] = None) -> Optional[str]`; `threemf_has_gcode(path) -> bool`.

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path
import zipfile
from src.services.file_role_classifier import classify_role, threemf_has_gcode


def test_classify_models():
    for ext in ["stl", ".stl", "STEP", "stp", "obj"]:
        assert classify_role(ext) == "model"


def test_classify_printfiles():
    for ext in ["gcode", ".gcode", "gco", "g", "bgcode"]:
        assert classify_role(ext) == "printfile"


def test_classify_3mf_depends_on_gcode():
    assert classify_role("3mf", threemf_has_gcode=True) == "printfile"
    assert classify_role("3mf", threemf_has_gcode=False) == "model"
    assert classify_role("3mf", threemf_has_gcode=None) == "model"


def test_classify_unknown_is_none():
    assert classify_role("txt") is None
    assert classify_role("") is None


def test_threemf_has_gcode(tmp_path):
    sliced = tmp_path / "sliced.3mf"
    with zipfile.ZipFile(sliced, "w") as z:
        z.writestr("Metadata/plate_1.gcode", "; gcode")
    assert threemf_has_gcode(sliced) is True
    model = tmp_path / "model.3mf"
    with zipfile.ZipFile(model, "w") as z:
        z.writestr("3D/3dmodel.model", "<model/>")
    assert threemf_has_gcode(model) is False
    assert threemf_has_gcode(tmp_path / "missing.3mf") is False
```

- [ ] **Step 2: Run, verify fail**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_file_role_classifier.py -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — module missing.

- [ ] **Step 3: Create `src/services/file_role_classifier.py`**

```python
"""Classify library files as a source model vs a printable (sliced) file."""
import zipfile
from pathlib import Path
from typing import Optional

_MODEL_EXT = {"stl", "step", "stp", "obj"}
_PRINTFILE_EXT = {"gcode", "gco", "g", "bgcode"}


def classify_role(file_type: str, threemf_has_gcode: Optional[bool] = None) -> Optional[str]:
    ext = (file_type or "").strip().lower().lstrip(".")
    if ext in _PRINTFILE_EXT:
        return "printfile"
    if ext in _MODEL_EXT:
        return "model"
    if ext == "3mf":
        return "printfile" if threemf_has_gcode else "model"
    return None


def threemf_has_gcode(path) -> bool:
    """True if a .3mf bundles sliced gcode (e.g. Bambu Metadata/plate_*.gcode)."""
    try:
        with zipfile.ZipFile(Path(path)) as z:
            return any(n.lower().endswith(".gcode") for n in z.namelist())
    except Exception:
        return False
```

- [ ] **Step 4: Run, verify pass**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_file_role_classifier.py -p no:cacheprovider --timeout=60 -q`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/services/file_role_classifier.py tests/services/test_file_role_classifier.py
git commit -m "feat: add file role classifier (model vs printfile)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Migration 036 + persist role on ingest

**Files:**
- Create: `migrations/036_library_file_roles.sql`
- Modify: `src/database/repositories/library_repository.py` (`create_file`)
- Modify: `src/services/library_service.py` (`add_file_to_library`)
- Create: `tests/services/test_library_roles.py`

**Interfaces:**
- Consumes: `classify_role`, `threemf_has_gcode`.
- Produces: `add_file_to_library(..., role: Optional[str] = None, parent_checksum: Optional[str] = None)`; persists `role`/`parent_checksum`; accepts `source_info['type'] == 'slicer'`.

- [ ] **Step 1: Write failing test** (`tests/services/test_library_roles.py`)

```python
import pytest
from pathlib import Path
from unittest.mock import Mock
from src.database.database import Database
from src.services.library_service import LibraryService
from src.services.event_service import EventService


def _config(library_dir):
    # LibraryService reads config_service.settings.* (see tests/backend/test_library_service.py)
    config = Mock()
    config.settings = Mock()
    config.settings.library_path = str(library_dir)
    config.settings.library_enabled = True
    config.settings.library_auto_organize = True
    config.settings.library_auto_extract_metadata = False  # no background metadata tasks in tests
    config.settings.library_checksum_algorithm = "sha256"
    config.settings.library_preserve_originals = True
    return config


@pytest.fixture
async def lib(temp_database, tmp_path):
    db = Database(temp_database)
    await db.initialize()
    svc = LibraryService(db, _config(tmp_path / "library"), EventService())
    await svc.initialize()
    try:
        yield svc, tmp_path
    finally:
        await db.close()


async def test_add_file_classifies_model(lib):
    svc, tmp_path = lib
    f = tmp_path / "cube.stl"
    f.write_text("solid x\nendsolid x\n")
    rec = await svc.add_file_to_library(f, {"type": "upload"})
    stored = await svc.get_file_by_checksum(rec["checksum"])
    assert stored["role"] == "model"


async def test_add_file_explicit_role_and_parent(lib):
    svc, tmp_path = lib
    f = tmp_path / "out.gcode"
    f.write_text("; gcode\n")
    rec = await svc.add_file_to_library(
        f, {"type": "slicer"}, role="printfile", parent_checksum="MODELSUM")
    stored = await svc.get_file_by_checksum(rec["checksum"])
    assert stored["role"] == "printfile" and stored["parent_checksum"] == "MODELSUM"
```

(Fixture pattern verified against `tests/backend/test_library_service.py`: `LibraryService` reads `config_service.settings.*`, so a `Mock()` config with `.settings.library_path` etc. is correct. `auto_extract_metadata=False` avoids background metadata tasks during tests.)

- [ ] **Step 2: Run, verify fail**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_library_roles.py -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — `role` not persisted / kwargs missing.

- [ ] **Step 3: Create `migrations/036_library_file_roles.sql`**

```sql
-- Migration: 036_library_file_roles.sql
-- Description: Add role (model|printfile) and parent_checksum to library_files
--              to express the model -> printfile relation.
-- Date: 2026-06-26

ALTER TABLE library_files ADD COLUMN role TEXT;
ALTER TABLE library_files ADD COLUMN parent_checksum TEXT;

CREATE INDEX IF NOT EXISTS idx_library_files_role ON library_files(role);
CREATE INDEX IF NOT EXISTS idx_library_files_parent ON library_files(parent_checksum);
```

- [ ] **Step 4: Persist columns in `LibraryRepository.create_file`**

Extend the INSERT column list, placeholders, and values tuple to include the two new columns (append at the end):

```python
            await self._execute_write(
                """INSERT INTO library_files
                (id, checksum, filename, display_name, library_path, file_size, file_type,
                 sources, status, added_to_library, last_modified, search_index,
                 is_duplicate, duplicate_of_checksum, duplicate_count,
                 role, parent_checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    file_data['id'],
                    file_data['checksum'],
                    file_data['filename'],
                    file_data.get('display_name'),
                    file_data['library_path'],
                    file_data['file_size'],
                    file_data['file_type'],
                    file_data['sources'],
                    file_data.get('status', 'available'),
                    file_data['added_to_library'],
                    file_data.get('last_modified'),
                    file_data.get('search_index', ''),
                    file_data.get('is_duplicate', 0),
                    file_data.get('duplicate_of_checksum'),
                    file_data.get('duplicate_count', 0),
                    file_data.get('role'),
                    file_data.get('parent_checksum'),
                ),
            )
```

(Keep the existing trailing lines after `duplicate_count` — this replaces the column list + values to add the two fields. Verify the placeholder count matches: 17 columns, 17 `?`, 17 values.)

- [ ] **Step 5: Add kwargs + classification + `'slicer'` source in `add_file_to_library`**

In the signature:

```python
    async def add_file_to_library(self, source_path: Path, source_info: Dict[str, Any],
                                  copy_file: bool = True, calculate_hash: bool = True,
                                  role: Optional[str] = None,
                                  parent_checksum: Optional[str] = None) -> Dict[str, Any]:
```

Allow the new source type (the validation line):

```python
            if source_type not in ['printer', 'watch_folder', 'upload', 'slicer']:
                raise ValueError(f"Invalid source type: {source_type}")
```

Where `file_type` is computed (`file_type = library_path.suffix.lower()`), classify if no explicit role was passed, then add both keys to `file_record`. Add near the top of the method: `from src.services.file_role_classifier import classify_role, threemf_has_gcode`. After `file_type` is known and before building `file_record`:

```python
            if role is None:
                has_gcode = threemf_has_gcode(library_path) if file_type.lstrip('.') == '3mf' else None
                role = classify_role(file_type, has_gcode)
```

And add to the `file_record` dict:

```python
                'duplicate_count': 0,
                'role': role,
                'parent_checksum': parent_checksum,
```

- [ ] **Step 6: Run, verify pass**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_library_roles.py -p no:cacheprovider --timeout=60 -q`
Expected: 2 passed.

- [ ] **Step 7: Commit**

```bash
git add migrations/036_library_file_roles.sql src/database/repositories/library_repository.py src/services/library_service.py tests/services/test_library_roles.py
git commit -m "feat: classify and persist library file role on ingest

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: One-time backfill of existing rows

**Files:**
- Modify: `src/services/library_service.py` (`classify_unroled_files`, call from `initialize`)
- Create: `tests/services/test_library_backfill.py`

**Interfaces:**
- Produces: `async LibraryService.classify_unroled_files() -> int` (returns number updated). Called from `LibraryService.initialize()`.

- [ ] **Step 1: Write failing test** (`tests/services/test_library_backfill.py`)

Seed `library_files` rows directly (role NULL) of mixed types + one already-classified, run the backfill, assert roles.

```python
import pytest
from datetime import datetime
from src.database.database import Database
from src.services.library_service import LibraryService
from src.services.event_service import EventService
from unittest.mock import Mock


@pytest.fixture
async def lib(temp_database, tmp_path):
    db = Database(temp_database)
    await db.initialize()
    config = Mock()
    config.settings = Mock()
    config.settings.library_path = str(tmp_path / "library")
    config.settings.library_enabled = True
    config.settings.library_auto_organize = True
    config.settings.library_auto_extract_metadata = False
    config.settings.library_checksum_algorithm = "sha256"
    config.settings.library_preserve_originals = True
    svc = LibraryService(db, config, EventService())
    await svc.initialize()
    try:
        yield svc, db
    finally:
        await db.close()


async def _seed(db, checksum, file_type, role=None):
    async with db.connection() as conn:
        await conn.execute(
            "INSERT INTO library_files (id, checksum, filename, library_path, file_type, role) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (checksum, checksum, f"{checksum}.{file_type}", f"/x/{checksum}", f".{file_type}", role))
        await conn.commit()


async def test_backfill_classifies_only_nulls(lib):
    svc, db = lib
    await _seed(db, "m1", "stl")
    await _seed(db, "p1", "gcode")
    await _seed(db, "keep", "stl", role="printfile")  # deliberately wrong, must be left alone
    n = await svc.classify_unroled_files()
    assert n == 2
    assert (await svc.get_file_by_checksum("m1"))["role"] == "model"
    assert (await svc.get_file_by_checksum("p1"))["role"] == "printfile"
    assert (await svc.get_file_by_checksum("keep"))["role"] == "printfile"  # untouched
```

- [ ] **Step 2: Run, verify fail**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_library_backfill.py -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — `classify_unroled_files` missing.

- [ ] **Step 3: Implement `classify_unroled_files`** (`src/services/library_service.py`)

```python
    async def classify_unroled_files(self) -> int:
        """One-time backfill: classify library_files rows with role IS NULL."""
        from src.services.file_role_classifier import classify_role, threemf_has_gcode
        updated = 0
        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "SELECT checksum, file_type, library_path FROM library_files WHERE role IS NULL")
            rows = await cursor.fetchall()
        for row in rows:
            checksum, file_type, library_path = row[0], row[1], row[2]
            ext = (file_type or "").lstrip(".").lower()
            has_gcode = None
            if ext == "3mf":
                full = self.library_path / library_path if library_path else None
                has_gcode = threemf_has_gcode(full) if full and full.exists() else None
            role = classify_role(file_type or "", has_gcode)
            if role is None:
                continue
            async with self.db.connection() as conn:
                await conn.execute(
                    "UPDATE library_files SET role = ? WHERE checksum = ? AND role IS NULL",
                    (role, checksum))
                await conn.commit()
            updated += 1
        if updated:
            logger.info("Backfilled library file roles", count=updated)
        return updated
```

In `LibraryService.initialize()`, after existing init work, add:

```python
        try:
            await self.classify_unroled_files()
        except Exception as e:  # noqa: BLE001
            logger.warning("Library role backfill failed", error=str(e))
```

- [ ] **Step 4: Run, verify pass**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_library_backfill.py -p no:cacheprovider --timeout=60 -q`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add src/services/library_service.py tests/services/test_library_backfill.py
git commit -m "feat: backfill library file roles on startup

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: get_printfiles_for_model + API endpoint

**Files:**
- Modify: `src/services/library_service.py` (`get_printfiles_for_model`)
- Modify: `src/api/routers/library.py` (printfiles endpoint)
- Create: `tests/services/test_printfiles_relation.py`

**Interfaces:**
- Produces: `async LibraryService.get_printfiles_for_model(model_checksum: str) -> List[Dict]` — each dict is the library_files row plus job fields `profile_id`, `target_printer_id`, `estimated_print_time`, `filament_used`, `sliced_at` (None when no matching job). Endpoint `GET /api/v1/library/files/{checksum}/printfiles`.

- [ ] **Step 1: Write failing test** (`tests/services/test_printfiles_relation.py`)

```python
import pytest
from src.database.database import Database
from src.services.library_service import LibraryService
from src.services.event_service import EventService
from unittest.mock import Mock


@pytest.fixture
async def lib(temp_database, tmp_path):
    db = Database(temp_database)
    await db.initialize()
    config = Mock()
    config.settings = Mock()
    config.settings.library_path = str(tmp_path / "library")
    config.settings.library_enabled = True
    config.settings.library_auto_organize = True
    config.settings.library_auto_extract_metadata = False
    config.settings.library_checksum_algorithm = "sha256"
    config.settings.library_preserve_originals = True
    svc = LibraryService(db, config, EventService())
    await svc.initialize()
    try:
        yield svc, db
    finally:
        await db.close()


async def _file(db, checksum, role=None, parent=None, file_type="stl"):
    async with db.connection() as conn:
        await conn.execute(
            "INSERT INTO library_files (id, checksum, filename, library_path, file_type, role, parent_checksum) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (checksum, checksum, f"{checksum}", f"/x/{checksum}", f".{file_type}", role, parent))
        await conn.commit()


async def test_get_printfiles_for_model(lib):
    svc, db = lib
    await _file(db, "MODEL", role="model")
    await _file(db, "PF1", role="printfile", parent="MODEL", file_type="gcode")
    await _file(db, "PF2", role="printfile", parent="MODEL", file_type="gcode")
    # a slicing job linking MODEL -> PF1 (needs a slicer+profile due to FKs)
    async with db.connection() as conn:
        await conn.execute("INSERT INTO slicer_configs (id, name, slicer_type, executable_path) VALUES ('s','S','orcaslicer','')")
        await conn.execute("INSERT INTO slicer_profiles (id, slicer_id, profile_name, profile_type) VALUES ('pr','s','P','bundle')")
        await conn.execute(
            "INSERT INTO slicing_jobs (id, file_checksum, slicer_id, profile_id, status, output_gcode_checksum, estimated_print_time, filament_used) "
            "VALUES ('j','MODEL','s','pr','completed','PF1', 1200, 9.0)")
        await conn.commit()
    out = await svc.get_printfiles_for_model("MODEL")
    by = {p["checksum"]: p for p in out}
    assert set(by) == {"PF1", "PF2"}
    assert by["PF1"]["estimated_print_time"] == 1200 and by["PF1"]["filament_used"] == 9.0
    assert by["PF2"]["estimated_print_time"] is None  # no job
```

- [ ] **Step 2: Run, verify fail**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_printfiles_relation.py -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — `get_printfiles_for_model` missing.

- [ ] **Step 3: Implement `get_printfiles_for_model`** (`src/services/library_service.py`)

```python
    async def get_printfiles_for_model(self, model_checksum: str) -> List[Dict[str, Any]]:
        """Return printfiles derived from a model, enriched with slicing-job detail."""
        query = """
            SELECT lf.*, sj.profile_id AS profile_id, sj.target_printer_id AS target_printer_id,
                   sj.estimated_print_time AS estimated_print_time, sj.filament_used AS filament_used,
                   sj.created_at AS sliced_at
            FROM library_files lf
            LEFT JOIN slicing_jobs sj ON sj.output_gcode_checksum = lf.checksum
            WHERE lf.parent_checksum = ? AND lf.role = 'printfile'
            ORDER BY lf.added_to_library DESC
        """
        async with self.db.connection() as conn:
            cursor = await conn.execute(query, (model_checksum,))
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]
```

- [ ] **Step 4: Run, verify pass**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_printfiles_relation.py -p no:cacheprovider --timeout=60 -q`
Expected: 1 passed. (If `dict(row)` fails because the pooled connection lacks a Row factory, set `conn.row_factory = aiosqlite.Row` on the connection before executing — check how other LibraryService queries build dicts and mirror that.)

- [ ] **Step 5: Add the API endpoint** (`src/api/routers/library.py`)

Add a response model near the other models:

```python
class PrintfilesResponse(BaseModel):
    printfiles: List[Dict[str, Any]]
    count: int
```

(Ensure `Dict, Any, List` are imported from `typing` and `BaseModel` from `pydantic` — they are already used in this file.) Add the endpoint (place it near `get_library_file`):

```python
@router.get("/files/{checksum}/printfiles", response_model=PrintfilesResponse)
async def get_model_printfiles(
    checksum: str,
    library_service = Depends(get_library_service),
):
    """List print files derived from a library model."""
    model = await library_service.get_file_by_checksum(checksum)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    printfiles = await library_service.get_printfiles_for_model(checksum)
    return PrintfilesResponse(printfiles=printfiles, count=len(printfiles))
```

(`HTTPException` is already imported in this router.)

- [ ] **Step 6: Verify router imports cleanly**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -c "import src.api.routers.library"`
Expected: no error.

- [ ] **Step 7: Commit**

```bash
git add src/services/library_service.py src/api/routers/library.py tests/services/test_printfiles_relation.py
git commit -m "feat: expose model printfiles relation (service + API)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Register slice output as a linked printfile

**Files:**
- Modify: `src/services/slicing_queue.py` (`_execute_job`, after the success UPDATE)
- Create: `tests/services/test_slice_output_registration.py`

**Interfaces:**
- Consumes: `library_service.add_file_to_library(..., role="printfile", parent_checksum=...)` returning a dict with `checksum`.

- [ ] **Step 1: Write failing test** (`tests/services/test_slice_output_registration.py`)

Reuse the Task-6-style harness from Phase 1's `test_slicing_queue_backend.py`: a `_FakeBackend` that writes an output file and returns a `SliceResult`, a real DB with a seeded `library_files` model row, and a fake/real library_service. Here use a fake library_service that records the registration call and returns a checksum, and assert `slicing_jobs.output_gcode_checksum` is set; then a second test where the fake raises and assert the job still ends `completed`.

```python
import asyncio
import pytest
from src.database.database import Database
from src.services.event_service import EventService
from src.services.slicer_service import SlicerService
from src.services.slicing_queue import SlicingQueue
from src.services.slicer_backends.base import SliceResult
from src.models.slicer import SlicingJobRequest


class _FakeBackend:
    async def slice(self, input_path, profile, output_path, progress_cb=None):
        with open(output_path, "w") as f:
            f.write("; sliced\n")
        return SliceResult(True, output_path, 100, 2.0)
    async def verify(self): return True
    async def version(self): return "t"


@pytest.fixture
async def db(temp_database):
    database = Database(temp_database)
    await database.initialize()
    try:
        yield database
    finally:
        await database.close()


async def _setup(db, tmp_path, lib):
    events = EventService()
    slicer_service = SlicerService(db, events)
    cfg = await slicer_service.register_slicer({
        "name": "R", "slicer_type": "orcaslicer", "executable_path": "",
        "backend_type": "remote", "endpoint_url": "http://x"})
    profile = await slicer_service.create_profile(cfg.id, {"profile_name": "P", "profile_type": "bundle"})

    async def _fake_get_backend(sid): return _FakeBackend()
    slicer_service.get_backend = _fake_get_backend

    model = tmp_path / "in.stl"; model.write_text("solid x\nendsolid x\n")
    async with db.connection() as conn:
        await conn.execute(
            "INSERT INTO library_files (id, checksum, filename, library_path, file_size, file_type, role) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)", ("lf", "MODEL", "in.stl", str(model), 10, ".stl", "model"))
        await conn.commit()

    class _Lib:
        async def get_file_by_checksum(self, c): return {"file_path": str(model)}
    queue = SlicingQueue(db, events, slicer_service, library_service=lib(model))
    queue._output_dir = tmp_path / "out"; queue._output_dir.mkdir()
    # patch input resolution to the seeded model
    queue.library_service.get_file_by_checksum = _Lib().get_file_by_checksum
    return queue, cfg, profile


async def _run(queue, job_id):
    for _ in range(100):
        j = await queue.get_job(job_id)
        if j.status in ("completed", "failed"):
            return j
        await asyncio.sleep(0.05)
    return await queue.get_job(job_id)


async def test_slice_output_registered(db, tmp_path):
    recorded = {}
    class _Lib:
        def __init__(self, model): self.model = model
        async def get_file_by_checksum(self, c): return {"file_path": str(self.model)}
        async def add_file_to_library(self, path, info, role=None, parent_checksum=None, **kw):
            recorded["role"] = role; recorded["parent"] = parent_checksum
            return {"checksum": "PFSUM"}
    queue, cfg, profile = await _setup(db, tmp_path, _Lib)
    job = await queue.create_job(SlicingJobRequest(file_checksum="MODEL", slicer_id=cfg.id, profile_id=profile.id))
    j = await _run(queue, job.id)
    assert j.status == "completed"
    assert recorded["role"] == "printfile" and recorded["parent"] == "MODEL"
    async with db.connection() as conn:
        cur = await conn.execute("SELECT output_gcode_checksum FROM slicing_jobs WHERE id=?", (job.id,))
        assert (await cur.fetchone())[0] == "PFSUM"


async def test_registration_failure_keeps_job_completed(db, tmp_path):
    class _Lib:
        def __init__(self, model): self.model = model
        async def get_file_by_checksum(self, c): return {"file_path": str(self.model)}
        async def add_file_to_library(self, *a, **k): raise RuntimeError("boom")
    queue, cfg, profile = await _setup(db, tmp_path, _Lib)
    job = await queue.create_job(SlicingJobRequest(file_checksum="MODEL", slicer_id=cfg.id, profile_id=profile.id))
    j = await _run(queue, job.id)
    assert j.status == "completed"
```

- [ ] **Step 2: Run, verify fail**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_slice_output_registration.py -p no:cacheprovider --timeout=60 -q`
Expected: FAIL — output not registered / `output_gcode_checksum` not set.

- [ ] **Step 3: Implement registration in `_execute_job`** (`src/services/slicing_queue.py`)

Immediately after the success UPDATE block (where `slicing_jobs` is set to COMPLETED with `output_file_path`/metadata) and before the `slicing_job.completed` event emit, add:

```python
            # Register the sliced output in the library, linked to its source model
            if self.library_service and result.output_path:
                try:
                    reg = await self.library_service.add_file_to_library(
                        Path(result.output_path),
                        {"type": "slicer", "slicer_id": job.slicer_id},
                        role="printfile",
                        parent_checksum=job.file_checksum,
                    )
                    output_checksum = reg.get("checksum") if isinstance(reg, dict) else None
                    if output_checksum:
                        async with self.db.connection() as conn:
                            await conn.execute(
                                "UPDATE slicing_jobs SET output_gcode_checksum = ? WHERE id = ?",
                                (output_checksum, job_id))
                            await conn.commit()
                except Exception as e:  # noqa: BLE001
                    logger.warning("Failed to register slice output in library",
                                   job_id=job_id, error=str(e))
```

- [ ] **Step 4: Run, verify pass**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_slice_output_registration.py -p no:cacheprovider --timeout=60 -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/services/slicing_queue.py tests/services/test_slice_output_registration.py
git commit -m "feat: register slice output as a library printfile linked to its model

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: Full-suite verification + PR

- [ ] **Step 1: Run all new Phase 3a tests**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_file_role_classifier.py tests/services/test_library_roles.py tests/services/test_library_backfill.py tests/services/test_printfiles_relation.py tests/services/test_slice_output_registration.py -p no:cacheprovider --timeout=60 -q`
Expected: all passed.

- [ ] **Step 2: Run the existing slicer + library suites (no regressions)**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/test_slicing_queue.py tests/services/test_slicer_backends.py tests/services/ -k "library or slic" -p no:cacheprovider --timeout=120 -q`
Expected: green except the 4 pre-existing `test_printer_service.py` failures (which are not in this selection).

- [ ] **Step 3: Full services dir (catch collection issues, as in Phase 1/2)**

Run: `/projects/printernizer-repos/printernizer/.venv/bin/python -m pytest tests/services/ -p no:cacheprovider --timeout=120 -q`
Expected: only the 4 known pre-existing `test_printer_service.py` failures; everything else green; no collection errors.

- [ ] **Step 4: Push + PR**

```bash
git push -u origin feature/slicer-phase3a-library
gh pr create --base master --title "feat: Slicer Phase 3a — library model->printfile relation + API" --body "Backend half of Phase 3. See docs/superpowers/specs/2026-06-26-slicer-phase3a-library-relation-design.md."
```

---

## Verification (end-to-end, real)
1. With the slicer service running, slice a library STL → a new `role='printfile'` library file appears with `parent_checksum` = the STL's checksum, and `slicing_jobs.output_gcode_checksum` is set.
2. `GET /api/v1/library/files/<stl_checksum>/printfiles` returns the derived printfile(s) with `estimated_print_time`/`filament_used`.
3. On startup with pre-existing library files, `classify_unroled_files` sets roles (STL→model, gcode→printfile); already-classified rows untouched.
4. Full `tests/services/` green except the 4 pre-existing `test_printer_service.py` failures.

## Self-review notes
- Spec coverage: classifier (T1), migration + ingest classification + `'slicer'` source (T2), backfill (T3), `get_printfiles_for_model` + API (T4), slice-output registration guarded (T5). All present.
- `LibraryService` fixture verified against `tests/backend/test_library_service.py` (Mock config + `settings.library_path`).
- One residual risk to watch at run time: `dict(row)` in `get_printfiles_for_model` (T4) depends on the pooled connection having `aiosqlite.Row` as `row_factory`; T4 Step 4 notes the fallback (set it explicitly) if needed.
- Out of scope (3b): the vanilla-JS model-centric UI; cascade-delete semantics (kept independent).
