"""Tests for the build123d GeneratorService (engine mocked)."""
import pathlib
from types import SimpleNamespace
from unittest.mock import AsyncMock

import aiosqlite
import pytest

from src.services.generator_service import GeneratorService
from src.services.build123d_service import Build123dService

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

    # Engine with build123d forced "available"; the actual build/export is
    # stubbed to write a fake STL so the tests don't require build123d/OCP.
    engine = Build123dService()
    engine._available = True

    async def fake_render_stl(build_fn, params, stl_path):
        stl_path.write_bytes(b"solid model\nendsolid model\n")

    engine.render_stl = fake_render_stl
    engine.render_preview = AsyncMock(return_value=False)

    library_service = SimpleNamespace(
        add_file_to_library=AsyncMock(return_value={"id": "lib_1", "status": "ready"})
    )

    svc = GeneratorService(database, event_service, engine, library_service=library_service)
    # Avoid importing the real (build123d-dependent) template modules.
    svc._resolve_build_fn = lambda template_id: (lambda **kwargs: object())
    await svc.initialize()
    yield svc
    await conn.close()
    config_module.reload_settings()


async def test_bundled_templates_loaded(service):
    ids = {t.id for t in service.list_templates()}
    assert "vase" in ids
    assert "box" in ids
    box = service.get_template("box")
    assert any(p.name == "width" for p in box.parameters)


async def test_template_not_found(service):
    from src.utils.errors import GeneratorTemplateNotFoundError
    with pytest.raises(GeneratorTemplateNotFoundError):
        service.get_template("does_not_exist")


async def test_param_coercion_clamps_and_types(service):
    box = service.get_template("box")
    clean = service._coerce_params(box, {
        "width": 9999,          # above max -> clamped to 300
        "wall_thickness": "0",  # below min -> clamped to 1
        "closed_bottom": "false",
        "unknown": 5,           # ignored
    })
    assert clean["width"] == 300
    assert clean["wall_thickness"] == 1
    assert clean["closed_bottom"] is False
    assert "unknown" not in clean


async def test_render_and_save_to_library(service):
    result = await service.render("box", {"width": 50}, fmt="stl")
    assert result.status == "completed"
    assert result.model_url.endswith("/model.stl")

    path = await service.get_artifact_path(result.render_id, "model")
    assert path is not None and path.exists()

    saved = await service.save_to_library(result.render_id, display_name="My Box")
    assert saved["id"] == "lib_1"
    service.library_service.add_file_to_library.assert_awaited_once()
    assert service.event_service.emit_event.await_count >= 2


async def test_unsafe_render_id_rejected(service):
    assert await service.get_artifact_path("../../etc/passwd", "model") is None
    from src.utils.errors import GeneratorTemplateNotFoundError
    with pytest.raises(GeneratorTemplateNotFoundError):
        await service.save_to_library("../../etc/passwd")


async def test_presets_roundtrip(service):
    preset = await service.save_preset("box", "Tall", {"height": 250})
    presets = await service.list_presets("box")
    assert any(p.id == preset.id and p.name == "Tall" for p in presets)
    await service.delete_preset(preset.id)
    assert await service.list_presets("box") == []
