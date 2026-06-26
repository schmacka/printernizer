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
