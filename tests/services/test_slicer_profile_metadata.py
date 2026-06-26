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
