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
