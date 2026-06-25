"""Tests for SLICER_SERVICE_URL remote-slicer auto-registration."""
import pytest

from src.database.database import Database
from src.services.event_service import EventService
from src.services.slicer_service import SlicerService


@pytest.fixture
async def slicer_service(temp_database):
    db = Database(temp_database)
    await db.initialize()
    try:
        yield SlicerService(db, EventService())
    finally:
        await db.close()


async def test_initialize_registers_remote_slicer(slicer_service, monkeypatch):
    monkeypatch.setenv("SLICER_SERVICE_URL", "http://slicer:8001")
    await slicer_service.register_remote_slicer_from_env()
    remotes = [s for s in await slicer_service.list_slicers() if s.backend_type == "remote"]
    assert remotes and remotes[0].endpoint_url == "http://slicer:8001"
    # idempotent: a second call does not create a duplicate
    await slicer_service.register_remote_slicer_from_env()
    remotes2 = [s for s in await slicer_service.list_slicers() if s.backend_type == "remote"]
    assert len(remotes2) == 1


async def test_no_registration_without_env(slicer_service, monkeypatch):
    monkeypatch.delenv("SLICER_SERVICE_URL", raising=False)
    await slicer_service.register_remote_slicer_from_env()
    remotes = [s for s in await slicer_service.list_slicers() if s.backend_type == "remote"]
    assert remotes == []
