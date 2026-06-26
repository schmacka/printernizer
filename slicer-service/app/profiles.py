"""List OrcaSlicer's bundled system presets from the profiles resource tree."""
from pathlib import Path
from typing import Dict, List

_KINDS = ("machine", "process", "filament")


def list_bundled_profiles(root: str) -> Dict:
    """Return {"vendors": {vendor: {machine:[], process:[], filament:[]}}}."""
    vendors: Dict[str, Dict[str, List[str]]] = {}
    base = Path(root) if root else None
    if not base or not base.is_dir():
        return {"vendors": vendors}
    for vendor_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        kinds: Dict[str, List[str]] = {k: [] for k in _KINDS}
        for kind in _KINDS:
            kdir = vendor_dir / kind
            if kdir.is_dir():
                kinds[kind] = sorted(f.stem for f in kdir.glob("*.json"))
        if any(kinds.values()):
            vendors[vendor_dir.name] = kinds
    return {"vendors": vendors}
