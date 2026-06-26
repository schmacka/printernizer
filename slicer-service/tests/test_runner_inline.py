import json
from pathlib import Path
from app.runner import OrcaSlicerRunner


def test_build_settings_inline_writes_temp_files(tmp_path):
    runner = OrcaSlicerRunner("/nonexistent/AppRun", "/nonexistent/profiles")
    profile = {"inline": {
        "machine": {"type": "machine", "name": "M"},
        "process": {"type": "process", "name": "P"},
        "filament": {"type": "filament", "name": "F"},
    }}
    process, machine, filament = runner._build_settings(profile, str(tmp_path))
    assert Path(process).exists() and json.loads(Path(process).read_text())["name"] == "P"
    assert Path(machine).exists() and Path(filament).exists()
