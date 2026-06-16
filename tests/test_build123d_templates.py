"""
Tests for the bundled build123d templates.

These exercise the real template build() functions and STL export, so they are
skipped when build123d is not installed (e.g. on a non-glibc CI runner).
"""
import importlib
import json
import pathlib

import pytest

pytest.importorskip("build123d")

from build123d import export_stl  # noqa: E402

TEMPLATES_DIR = pathlib.Path("src/build123d_templates")
TEMPLATE_IDS = ["box", "vase"]


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_template_has_metadata(template_id):
    meta = json.loads((TEMPLATES_DIR / f"{template_id}.json").read_text())
    assert meta["name"]
    assert isinstance(meta["parameters"], list) and meta["parameters"]
    for param in meta["parameters"]:
        assert param["name"]
        assert param["type"] in {"number", "boolean", "string", "enum"}


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_template_builds_and_exports(template_id, tmp_path):
    module = importlib.import_module(f"src.build123d_templates.{template_id}")
    # Build with defaults from the JSON sidecar.
    meta = json.loads((TEMPLATES_DIR / f"{template_id}.json").read_text())
    params = {p["name"]: p["default"] for p in meta["parameters"]}

    shape = module.build(**params)
    assert shape is not None

    out = tmp_path / f"{template_id}.stl"
    export_stl(shape, str(out))
    assert out.exists() and out.stat().st_size > 0
