from pathlib import Path
import zipfile
from src.services.file_role_classifier import classify_role, threemf_has_gcode


def test_classify_models():
    for ext in ["stl", ".stl", "STEP", "stp", "obj"]:
        assert classify_role(ext) == "model"


def test_classify_printfiles():
    for ext in ["gcode", ".gcode", "gco", "g", "bgcode"]:
        assert classify_role(ext) == "printfile"


def test_classify_3mf_depends_on_gcode():
    assert classify_role("3mf", threemf_has_gcode=True) == "printfile"
    assert classify_role("3mf", threemf_has_gcode=False) == "model"
    assert classify_role("3mf", threemf_has_gcode=None) == "model"


def test_classify_unknown_is_none():
    assert classify_role("txt") is None
    assert classify_role("") is None


def test_threemf_has_gcode(tmp_path):
    sliced = tmp_path / "sliced.3mf"
    with zipfile.ZipFile(sliced, "w") as z:
        z.writestr("Metadata/plate_1.gcode", "; gcode")
    assert threemf_has_gcode(sliced) is True
    model = tmp_path / "model.3mf"
    with zipfile.ZipFile(model, "w") as z:
        z.writestr("3D/3dmodel.model", "<model/>")
    assert threemf_has_gcode(model) is False
    assert threemf_has_gcode(tmp_path / "missing.3mf") is False
