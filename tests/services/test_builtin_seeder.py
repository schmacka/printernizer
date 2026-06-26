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
