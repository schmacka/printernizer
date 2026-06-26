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
