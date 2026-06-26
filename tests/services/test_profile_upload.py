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
