"""Tests for the OpenSCAD GeneratorService (OpenSCAD binary mocked)."""
import pathlib
from types import SimpleNamespace
from unittest.mock import AsyncMock

import aiosqlite
import pytest

from src.services.generator_service import GeneratorService
from src.services.openscad_service import OpenSCADService

MIGRATION = pathlib.Path("migrations/032_add_openscad_tables.sql").read_text()


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
    openscad = OpenSCADService()
    # Force "available" and stub the actual render to write a fake artifact.
    openscad._available = True
    openscad._binary = "/usr/bin/openscad"

    async def fake_render(scad_path, output_path, params=None, fmt="stl", camera=None):
        output_path.write_bytes(b"solid model\nendsolid model\n")
        return output_path

    openscad.render = fake_render

    library_service = SimpleNamespace(
        add_file_to_library=AsyncMock(return_value={"id": "lib_1", "status": "ready"})
    )

    svc = GeneratorService(database, event_service, openscad, library_service=library_service)
    await svc.initialize()
    yield svc
    await conn.close()
    config_module.reload_settings()


async def test_bundled_templates_loaded(service):
    templates = service.list_templates()
    ids = {t.id for t in templates}
    assert "vase" in ids
    assert "box" in ids
    # List view omits source but includes parameters.
    vase = next(t for t in templates if t.id == "vase")
    assert vase.source is None
    assert any(p.name == "height" for p in vase.parameters)


async def test_get_template_includes_source(service):
    vase = service.get_template("vase")
    assert vase.source and "linear_extrude" in vase.source


def test_serialize_value():
    assert OpenSCADService.serialize_value(True) == "true"
    assert OpenSCADService.serialize_value(False) == "false"
    assert OpenSCADService.serialize_value(5) == "5"
    assert OpenSCADService.serialize_value("smooth") == '"smooth"'
    assert OpenSCADService.serialize_value([1, 2, 3]) == "[1,2,3]"


async def test_render_and_save_to_library(service):
    result = await service.render("vase", {"height": 100}, fmt="stl")
    assert result.status == "completed"
    assert result.model_url.endswith("/model.stl")

    # Artifact is retrievable.
    path = await service.get_artifact_path(result.render_id, "model")
    assert path is not None and path.exists()

    # Save hands the file to the library service.
    saved = await service.save_to_library(result.render_id, display_name="My Vase")
    assert saved["id"] == "lib_1"
    service.library_service.add_file_to_library.assert_awaited_once()

    # Generation events were emitted.
    assert service.event_service.emit_event.await_count >= 2


async def test_unsafe_render_id_rejected(service):
    # Path-traversal style ids must never reach the filesystem.
    assert await service.get_artifact_path("../../etc/passwd", "model") is None
    import pytest as _pytest
    from src.utils.errors import GeneratorTemplateNotFoundError
    with _pytest.raises(GeneratorTemplateNotFoundError):
        await service.save_to_library("../../etc/passwd")


async def test_presets_roundtrip(service):
    preset = await service.save_preset("vase", "Tall", {"height": 250})
    presets = await service.list_presets("vase")
    assert any(p.id == preset.id and p.name == "Tall" for p in presets)
    await service.delete_preset(preset.id)
    assert await service.list_presets("vase") == []


async def test_upload_roundtrip(service):
    template = service.store_upload("height = 10; // [1:20]\n", filename="thing.scad")
    assert template.id.startswith("upload:")
    assert any(p.name == "height" for p in template.parameters)
    # Uploaded source resolves for rendering.
    result = await service.render(template.id, {"height": 12}, fmt="stl")
    assert result.status == "completed"
