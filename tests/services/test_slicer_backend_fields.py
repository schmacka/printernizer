"""Tests for slicer backend fields (backend_type/endpoint_url) on SlicerConfig."""
import pytest

from src.database.database import Database
from src.services.slicer_service import SlicerService
from src.services.event_service import EventService


@pytest.fixture
async def slicer_service(temp_database):
    db = Database(temp_database)
    await db.initialize()
    try:
        yield SlicerService(db, EventService())
    finally:
        await db.close()


async def test_register_remote_slicer_persists_backend_fields(slicer_service):
    cfg = await slicer_service.register_slicer({
        "name": "Remote Orca", "slicer_type": "orcaslicer",
        "executable_path": "", "backend_type": "remote",
        "endpoint_url": "http://slicer:8001",
    })
    assert cfg.backend_type == "remote"
    assert cfg.endpoint_url == "http://slicer:8001"
    again = await slicer_service.get_slicer(cfg.id)
    assert again.endpoint_url == "http://slicer:8001"


async def test_register_local_slicer_defaults_backend(slicer_service):
    cfg = await slicer_service.register_slicer({
        "name": "Local Prusa", "slicer_type": "prusaslicer",
        "executable_path": "/usr/bin/prusa-slicer",
    })
    assert cfg.backend_type == "local"
    assert cfg.endpoint_url is None
