"""Gcode metadata extraction (print time + filament), slicer-agnostic.

Shared by SlicingQueue (app) and vendored into the slicer-service image.
"""
import re
from typing import Optional
import structlog

logger = structlog.get_logger()


class GCodeMetadata:
    def __init__(self):
        self.estimated_print_time: Optional[int] = None  # seconds
        self.filament_used: Optional[float] = None  # grams


# Order matters: most specific / most correct first.
TIME_PATTERNS = [
    # OrcaSlicer/BambuStudio total (must match on same line): "; total estimated time: 40m 39s"
    (r';\s*total estimated time:\s*(.+?)$', 'human'),
    # OrcaSlicer model printing (if no total estimated): "; model printing time: 33m 52s"
    (r';\s*model printing time:\s*(.+?)$', 'human'),
    # PrusaSlicer/OrcaSlicer: "; estimated printing time (normal mode) = 1h 30m 15s"
    # NB: must not match "estimated first layer printing time"
    (r';\s*estimated printing time.*?=\s*(.+?)$', 'human'),
    (r';\s*TIME:\s*(\d+)', 'seconds'),
    (r';\s*total estimated time.*?=\s*(\d+)', 'seconds'),
    (r';\s*print_time\s*=\s*(\d+)', 'seconds'),
]

FILAMENT_PATTERNS = [
    (r';\s*(?:total\s+)?filament used \[g\]\s*=\s*([\d.]+)', 'grams'),
    (r';\s*filament used \[mm\]\s*=\s*([\d.]+)', 'mm'),
    (r';\s*Filament used:\s*([\d.]+)\s*m(?:m)?', 'cura'),
    (r';\s*filament_used\s*=\s*([\d.]+)', 'grams'),
    (r';\s*filament weight\s*=\s*([\d.]+)', 'grams'),
]


def _parse_human_time(time_str: str) -> Optional[int]:
    if not time_str:
        return None
    total = 0
    mult = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
    for value, unit in re.findall(r'(\d+)\s*([dhms])', time_str.strip(), re.IGNORECASE):
        total += int(value) * mult[unit.lower()]
    return total or None


def parse_metadata_from_text(text: str) -> GCodeMetadata:
    md = GCodeMetadata()
    lines = text.splitlines()
    for pattern, fmt in TIME_PATTERNS:
        if md.estimated_print_time is not None:
            break
        for line in lines:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                val = int(m.group(1)) if fmt == 'seconds' else _parse_human_time(m.group(1))
                if val:
                    md.estimated_print_time = val
                    break
    for pattern, fmt in FILAMENT_PATTERNS:
        if md.filament_used is not None:
            break
        for line in lines:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                v = float(m.group(1))
                if fmt == 'grams':
                    md.filament_used = v
                elif fmt == 'mm':
                    md.filament_used = (v / 1000.0) * 2.98
                elif fmt == 'cura':
                    md.filament_used = v * 2.98 if v < 100 else (v / 1000.0) * 2.98
                if md.filament_used is not None:
                    break
    return md


def parse_gcode_metadata(gcode_path: str) -> GCodeMetadata:
    """Read header (first 500 lines) + footer (last 200 lines) and parse."""
    try:
        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            header = [ln for i, ln in zip(range(500), f)]
            f.seek(0, 2)
            size = f.tell()
            if size > 50000:
                f.seek(max(0, size - 50000))
                f.readline()
                footer = f.readlines()[-200:]
            else:
                f.seek(0)
                all_lines = f.readlines()
                footer = all_lines[-200:] if len(all_lines) > 200 else []
        return parse_metadata_from_text("".join(header + footer))
    except Exception as e:
        logger.warning("Failed to parse G-code metadata", path=gcode_path, error=str(e))
        return GCodeMetadata()
