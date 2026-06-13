"""Unit tests for the OpenSCAD Customizer parameter parser."""
from src.models.generator import ScadParameterType
from src.services.scad_parser import parse_parameters


def _by_name(params):
    return {p.name: p for p in params}


def test_number_with_range():
    params = _by_name(parse_parameters("height = 100; // [10:200]"))
    p = params["height"]
    assert p.type == ScadParameterType.NUMBER
    assert p.default == 100
    assert p.min == 10
    assert p.max == 200
    assert p.step is None


def test_number_with_step_range():
    params = _by_name(parse_parameters("wall = 2; // [0.5:0.5:5]"))
    p = params["wall"]
    assert p.type == ScadParameterType.NUMBER
    assert p.min == 0.5
    assert p.step == 0.5
    assert p.max == 5


def test_boolean():
    params = _by_name(parse_parameters("faceted = true;"))
    p = params["faceted"]
    assert p.type == ScadParameterType.BOOLEAN
    assert p.default is True


def test_string():
    params = _by_name(parse_parameters('label = "hello";'))
    p = params["label"]
    assert p.type == ScadParameterType.STRING
    assert p.default == "hello"


def test_string_dropdown():
    params = _by_name(parse_parameters('style = "smooth"; // [smooth, faceted, ribbed]'))
    p = params["style"]
    assert p.type == ScadParameterType.ENUM
    assert p.options == ["smooth", "faceted", "ribbed"]
    assert p.default == "smooth"


def test_numeric_dropdown():
    params = _by_name(parse_parameters("segments = 6; // [3, 6, 12, 24]"))
    p = params["segments"]
    assert p.type == ScadParameterType.ENUM
    assert p.options == [3, 6, 12, 24]


def test_labeled_dropdown():
    params = _by_name(parse_parameters("quality = 10; // [10:Low, 20:Medium, 30:High]"))
    p = params["quality"]
    assert p.type == ScadParameterType.ENUM
    assert p.options == [10, 20, 30]


def test_description_from_line_above():
    src = "// The total height in mm\nheight = 100;"
    p = _by_name(parse_parameters(src))["height"]
    assert p.description == "The total height in mm"


def test_groups():
    src = """
/* [Dimensions] */
height = 100;
width = 50;

/* [Style] */
twist = 30;
"""
    params = _by_name(parse_parameters(src))
    assert params["height"].group == "Dimensions"
    assert params["width"].group == "Dimensions"
    assert params["twist"].group == "Style"


def test_hidden_group_excluded():
    src = """
height = 100;
/* [Hidden] */
internal = 5;
"""
    params = _by_name(parse_parameters(src))
    assert "height" in params
    assert "internal" not in params


def test_ignores_non_top_level_variables():
    src = """
height = 100;
module widget() {
    inner = 5;
    x = inner * 2;
}
function area(r) = 3.14 * r * r;
"""
    params = _by_name(parse_parameters(src))
    assert "height" in params
    assert "inner" not in params
    assert "x" not in params
    assert "area" not in params


def test_ignores_includes():
    src = "include <lib.scad>\nuse <other.scad>\nheight = 10;"
    params = _by_name(parse_parameters(src))
    assert list(params.keys()) == ["height"]


def test_assignment_without_spaces():
    params = _by_name(parse_parameters('style="smooth"; // [smooth, faceted]'))
    p = params["style"]
    assert p.type == ScadParameterType.ENUM
    assert p.options == ["smooth", "faceted"]


def test_redos_inputs_return_quickly():
    import time
    for evil in ("A=" + " " * 30000 + ";",
                 "/*[" + "a" * 30000,
                 "/*" + "a/*" * 15000,
                 "[" + "a" * 30000):
        start = time.time()
        parse_parameters(evil)
        assert time.time() - start < 1.0


def test_block_comment_braces_ignored():
    src = """
/* a comment with { braces } that should not change depth */
height = 100;
"""
    params = _by_name(parse_parameters(src))
    assert "height" in params
    assert params["height"].group is None
