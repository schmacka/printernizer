from src.utils.gcode_metadata import parse_metadata_from_text

ORCA_SAMPLE = "\n".join([
    "; model printing time: 33m 52s; total estimated time: 40m 39s",
    "; estimated first layer printing time (normal mode) = 6m 46s",
    "; filament used [mm] = 1343.10",
    "; filament used [cm3] = 3.23",
])
PRUSA_SAMPLE = "\n".join([
    "; estimated printing time (normal mode) = 1h 30m 15s",
    "; filament used [g] = 15.23",
])

def test_orca_total_estimated_time_parsed():
    md = parse_metadata_from_text(ORCA_SAMPLE)
    assert md.estimated_print_time == 40 * 60 + 39  # 2439s, NOT the first-layer 6m46s

def test_orca_filament_converted_from_mm():
    md = parse_metadata_from_text(ORCA_SAMPLE)
    assert md.filament_used is not None
    assert round(md.filament_used, 1) == 4.0

def test_prusa_still_parses():
    md = parse_metadata_from_text(PRUSA_SAMPLE)
    assert md.estimated_print_time == 3600 + 30 * 60 + 15
    assert md.filament_used == 15.23
