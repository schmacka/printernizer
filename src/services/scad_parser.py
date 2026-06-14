"""
OpenSCAD Customizer parameter parser.

Extracts the tweakable parameters from an OpenSCAD script by reading top-level
variable assignments and their Customizer annotations, producing a structured
schema that drives a dynamic frontend form. Works for both bundled generator
templates and arbitrary uploaded ``.scad`` files.

Customizer syntax supported (https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Customizer):
    /* [Group Name] */          section header (groups following parameters)
    /* [Hidden] */              hides following parameters from the customizer
    // description              description on the line above a parameter
    var = 10;   // [0:100]      number slider with min/max
    var = 2;    // [0:0.5:10]   number slider with min/step/max
    var = "a";  // [a, b, c]    dropdown of values
    var = 10;   // [10:L, 20:M] labeled dropdown (value:label)
    var = true;                 boolean checkbox
    var = "text";               free string
"""
import re
from typing import Any, List, Optional

from src.models.generator import ScadParameter, ScadParameterType

# Keywords / statement starters that are never parameters.
_NON_PARAM_STARTERS = (
    "module", "function", "include", "use", "for", "if", "else",
    "echo", "assert", "let", "intersection_for",
)

# Top-level assignment: identifier = value ; <rest>
# Linear (non-backtracking) patterns are used throughout so that parsing
# untrusted uploaded .scad files cannot trigger catastrophic regex backtracking.
# Value is everything up to the first ';'; the remainder (incl. any // comment)
# is captured separately and handled in code.
_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*=([^;]*);(.*)$")
# Section header comment: /* [Name] */
_SECTION_RE = re.compile(r"/\*\s*\[([^\]]*)\]\s*\*/")
# Customizer widget bracket inside a trailing comment: [ ... ]
_BRACKET_RE = re.compile(r"\[([^\]]*)\]")


def _is_number(token: str) -> bool:
    try:
        float(token)
        return True
    except (TypeError, ValueError):
        return False


def _coerce_number(token: str) -> float:
    value = float(token)
    return int(value) if value.is_integer() else value


def _parse_default(raw: str) -> Any:
    """Parse an OpenSCAD literal default value into a Python value."""
    raw = raw.strip()
    if raw in ("true", "false"):
        return raw == "true"
    if (len(raw) >= 2) and raw[0] == raw[-1] and raw[0] in ("\"", "'"):
        return raw[1:-1]
    if _is_number(raw):
        return _coerce_number(raw)
    return raw  # vectors/expressions left as-is


def _strip_code(line: str) -> str:
    """
    Return the code portion of a line.

    Drops the trailing ``//`` comment and removes paired inline ``/* */``
    comments. An unterminated ``/*`` is left in place so the caller can detect
    a multi-line block comment. Uses a single linear scan (no regex) to avoid
    backtracking on untrusted input.
    """
    result = []
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if ch == "/" and i + 1 < n and line[i + 1] == "*":
            end = line.find("*/", i + 2)
            if end == -1:
                # Unterminated block comment: keep it for multi-line handling.
                result.append(line[i:])
                break
            i = end + 2
            continue
        if ch == "/" and i + 1 < n and line[i + 1] == "/":
            break  # line comment: drop the remainder
        result.append(ch)
        i += 1
    return "".join(result)


def _parse_bracket(content: str):
    """
    Interpret a Customizer bracket's content.

    Returns a tuple (kind, data) where kind is 'range' or 'enum'.
      range -> {'min','max','step'}
      enum  -> [options]
    """
    content = content.strip()
    if "," not in content:
        # No comma: a numeric range like 0:100 or 0:5:100, otherwise a single option.
        parts = [p.strip() for p in content.split(":")]
        if len(parts) in (2, 3) and all(_is_number(p) for p in parts):
            if len(parts) == 2:
                return "range", {"min": _coerce_number(parts[0]),
                                 "max": _coerce_number(parts[1]), "step": None}
            return "range", {"min": _coerce_number(parts[0]),
                             "step": _coerce_number(parts[1]),
                             "max": _coerce_number(parts[2])}
        return "enum", [_option_value(content)]
    # Comma separated -> dropdown of options (values may be 'value:label').
    return "enum", [_option_value(p.strip()) for p in content.split(",")]


def _option_value(token: str) -> Any:
    """Extract the value from a dropdown option token ('value' or 'value:label')."""
    value = token.split(":", 1)[0].strip()
    return _coerce_number(value) if _is_number(value) else value


def _infer_type(default: Any, bracket_kind: Optional[str]) -> ScadParameterType:
    if bracket_kind == "enum":
        return ScadParameterType.ENUM
    if bracket_kind == "range":
        return ScadParameterType.NUMBER
    if isinstance(default, bool):
        return ScadParameterType.BOOLEAN
    if isinstance(default, (int, float)):
        return ScadParameterType.NUMBER
    return ScadParameterType.STRING


def parse_parameters(source: str) -> List[ScadParameter]:
    """
    Parse OpenSCAD source and return its top-level Customizer parameters.

    Only assignments at brace-depth 0 are considered (variables inside modules
    or functions are ignored, matching OpenSCAD's own Customizer behaviour).
    """
    parameters: List[ScadParameter] = []
    seen: set = set()
    depth = 0
    in_block_comment = False
    current_group: Optional[str] = None
    hidden = False
    pending_description: Optional[str] = None

    for raw_line in source.splitlines():
        line = raw_line.rstrip("\n")

        # Section headers are detected even within block-comment handling.
        section = _SECTION_RE.search(line)
        if section:
            name = section.group(1).strip()
            if name.lower() == "hidden":
                hidden = True
                current_group = None
            else:
                hidden = False
                current_group = name
            pending_description = None
            continue

        # Track multi-line block comments (so braces inside them are ignored).
        if in_block_comment:
            if "*/" in line:
                in_block_comment = False
                line = line.split("*/", 1)[1]
            else:
                continue

        stripped = line.strip()

        # Standalone line comment -> candidate description for the next parameter.
        if stripped.startswith("//"):
            pending_description = stripped[2:].strip() or None
            continue

        code = _strip_code(line)

        if depth == 0 and not hidden:
            match = _ASSIGN_RE.match(line)
            if match:
                name, raw_value, rest = match.group(1), match.group(2), match.group(3)
                # The trailing comment (if any) is the text after '//' in the rest.
                trailing = rest.split("//", 1)[1] if "//" in rest else None
                # Confirm the (comment-stripped) code is genuinely "<name> = ...",
                # robust to spacing (handles both "x = 5" and "x=5").
                code_stripped = code.lstrip()
                looks_like_assignment = (
                    code_stripped.startswith(name)
                    and code_stripped[len(name):].lstrip().startswith("=")
                )
                if name not in _NON_PARAM_STARTERS and looks_like_assignment and name not in seen:
                    bracket_kind, bracket_data = None, None
                    description = pending_description
                    if trailing:
                        bracket_match = _BRACKET_RE.search(trailing)
                        if bracket_match:
                            bracket_kind, bracket_data = _parse_bracket(bracket_match.group(1))
                            # Any text before the bracket is an inline description.
                            inline = trailing[:bracket_match.start()].strip()
                            description = description or (inline or None)
                        else:
                            description = description or (trailing.strip() or None)

                    default = _parse_default(raw_value)
                    param = ScadParameter(
                        name=name,
                        type=_infer_type(default, bracket_kind),
                        default=default,
                        description=description,
                        group=current_group,
                    )
                    if bracket_kind == "range":
                        param.min = bracket_data["min"]
                        param.max = bracket_data["max"]
                        param.step = bracket_data["step"]
                    elif bracket_kind == "enum":
                        param.options = bracket_data

                    parameters.append(param)
                    seen.add(name)

        # Update brace depth using only the code portion (strings approximated).
        if "/*" in code and "*/" not in code:
            in_block_comment = True
            code = code.split("/*", 1)[0]
        depth += code.count("{") - code.count("}")
        if depth < 0:
            depth = 0

        # A non-comment, non-blank line consumes any pending description.
        if stripped:
            pending_description = None

    return parameters
