"""Tests for the browser-side GeneratorService (presets + STL library hand-off).

Geometry is generated client-side (JSCAD), so the server no longer runs a CAD
engine. The service only reports status, persists named parameter presets, and
saves a finished STL into the Library.
"""
import pathlib
from types import SimpleNamespace
from unittest.mock import AsyncMock

import aiosqlite
import pytest

from src.services.generator_service import GeneratorService

MIGRATION = pathlib.Path("migrations/033_add_generator_tables.sql").read_text()


@pytest.fixture
async def service(tmp_path, monkeypatch):
    # Point generator output at a temp dir.
    monkeypatch.setenv("GENERATOR_OUTPUT_DIR", str(tmp_path / "generator"))
    from src.utils import config as config_module
    config_module.reload_settings()

    conn = await aiosqlite.connect(":memory:")
    await conn.executescript(MIGRATION)
    database = SimpleNamespace(_connection=conn)

    event_service = SimpleNamespace(emit_event=AsyncMock())
    library_service = SimpleNamespace(
        add_file_to_library=AsyncMock(return_value={"id": "lib_1", "status": "ready"})
    )

    svc = GeneratorService(database, event_service, library_service=library_service)
    await svc.initialize()
    yield svc
    await conn.close()
    config_module.reload_settings()


async def test_status_reports_browser_engine(service):
    status = service.get_status()
    assert status.available is True
    assert status.engine == "jscad"


async def test_save_stl_to_library(service):
    saved = await service.save_stl_to_library(
        stl_bytes=b"solid model\nendsolid model\n",
        template_id="box",
        parameters={"width": 50},
        display_name="My Box",
    )
    assert saved["id"] == "lib_1"

    service.library_service.add_file_to_library.assert_awaited_once()
    call = service.library_service.add_file_to_library.await_args
    # The staged file is server-named and carries the JSCAD source info.
    source_info = call.kwargs["source_info"]
    assert source_info["generator"] == "jscad"
    assert source_info["template_id"] == "box"
    assert source_info["parameters"] == {"width": 50}
    assert source_info["display_name"] == "My_Box.stl"

    # Staged temp file is cleaned up after hand-off.
    assert list(service.staging_dir.glob("*.stl")) == []
    service.event_service.emit_event.assert_awaited_once()


async def test_save_stl_without_library_service_raises(service):
    from src.utils.errors import GeneratorError
    service.library_service = None
    with pytest.raises(GeneratorError):
        await service.save_stl_to_library(b"solid\n", "box", {})


async def test_presets_roundtrip(service):
    preset = await service.save_preset("box", "Tall", {"height": 250})
    assert preset.template_id == "box"
    assert preset.parameters == {"height": 250}

    presets = await service.list_presets("box")
    assert any(p.id == preset.id and p.name == "Tall" for p in presets)

    await service.delete_preset(preset.id)
    assert await service.list_presets("box") == []


async def test_list_presets_filters_by_template(service):
    await service.save_preset("box", "B1", {"width": 10})
    await service.save_preset("vase", "V1", {"height": 100})

    box_presets = await service.list_presets("box")
    assert {p.name for p in box_presets} == {"B1"}
    assert len(await service.list_presets()) == 2
