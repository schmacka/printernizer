"""Classify library files as a source model vs a printable (sliced) file."""
import zipfile
from pathlib import Path
from typing import Optional

_MODEL_EXT = {"stl", "step", "stp", "obj"}
_PRINTFILE_EXT = {"gcode", "gco", "g", "bgcode"}


def classify_role(file_type: str, threemf_has_gcode: Optional[bool] = None) -> Optional[str]:
    ext = (file_type or "").strip().lower().lstrip(".")
    if ext in _PRINTFILE_EXT:
        return "printfile"
    if ext in _MODEL_EXT:
        return "model"
    if ext == "3mf":
        return "printfile" if threemf_has_gcode else "model"
    return None


def threemf_has_gcode(path) -> bool:
    """True if a .3mf bundles sliced gcode (e.g. Bambu Metadata/plate_*.gcode)."""
    try:
        with zipfile.ZipFile(Path(path)) as z:
            return any(n.lower().endswith(".gcode") for n in z.namelist())
    except Exception:
        return False
