"""Tests that SlicingQueue delegates execution to the resolved SlicerBackend."""
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
        if progress_cb:
            await progress_cb(100)
        return SliceResult(True, output_path, 1234, 7.5)

    async def verify(self):
        return True

    async def version(self):
        return "test"


@pytest.fixture
async def db(temp_database):
    database = Database(temp_database)
    await database.initialize()
    try:
        yield database
    finally:
        await database.close()


async def test_execute_job_uses_backend(db, tmp_path, monkeypatch):
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
    model = tmp_path / "in.stl"
    model.write_text("solid x\nendsolid x\n")
    async with db.connection() as conn:
        await conn.execute(
            "INSERT INTO library_files (id, checksum, filename, library_path, file_size, file_type) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("lf1", "abc", "in.stl", str(model), 10, ".stl"))
        await conn.commit()

    class _Lib:
        async def get_file_by_checksum(self, c):
            return {"file_path": str(model)}

    queue = SlicingQueue(db, events, slicer_service, library_service=_Lib())
    queue._output_dir = tmp_path / "out"
    queue._output_dir.mkdir()

    job = await queue.create_job(SlicingJobRequest(
        file_checksum="abc", slicer_id=cfg.id, profile_id=profile.id))

    for _ in range(100):
        j = await queue.get_job(job.id)
        if j.status in ("completed", "failed"):
            break
        await asyncio.sleep(0.05)

    j = await queue.get_job(job.id)
    assert j.status == "completed", f"job ended as {j.status}: {j.error_message}"
    assert j.estimated_print_time == 1234 and j.filament_used == 7.5
