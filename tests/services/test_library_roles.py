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
