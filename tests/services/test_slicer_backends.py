"""Tests for the slicer backend abstraction and local/remote backends."""
import json
from datetime import datetime

import pytest

from src.services.slicer_backends.base import SlicerBackend, SliceResult
from src.services.slicer_backends.local_process import LocalProcessBackend, build_command
from src.models.slicer import SlicerConfig, SlicerProfile, ProfileType


def _profile(path="/tmp/p.ini", settings=None):
    return SlicerProfile(id="p", slicer_id="s", profile_name="P",
                         profile_type=ProfileType.PRINT, profile_path=path,
                         settings_json=settings, created_at=datetime.now(),
                         updated_at=datetime.now())


def test_sliceresult_defaults():
    r = SliceResult(success=True, output_path="/x.gcode",
                    estimated_print_time=10, filament_used=1.0)
    assert r.error_message is None and r.success is True


def test_backend_is_abstract():
    with pytest.raises(TypeError):
        SlicerBackend()  # abstract, cannot instantiate


def test_build_command_prusaslicer():
    cmd = build_command("prusaslicer", "/usr/bin/prusa-slicer",
                        "/in.stl", _profile(), "/out/o.gcode")
    assert cmd[0] == "/usr/bin/prusa-slicer"
    assert "--export-gcode" in cmd and "--load" in cmd and "/in.stl" in cmd


def test_build_command_orcaslicer():
    prof = _profile(path=None, settings='{"machine":"/m.json","process":"/p.json","filament":"/f.json"}')
    cmd = build_command("orcaslicer", "/opt/orca/AppRun", "/in.stl", prof, "/out/o.gcode")
    assert "--slice" in cmd and "--load-settings" in cmd and "--load-filaments" in cmd


async def test_local_backend_runs_fake_slicer(tmp_path):
    # Fake slicer: writes a canned gcode then exits 0
    fake = tmp_path / "fakeslicer.sh"
    fake.write_text(
        "#!/bin/bash\n"
        'out=""; while [ $# -gt 0 ]; do [ "$1" = "--output" ] && out="$2"; shift; done\n'
        'printf "; estimated printing time (normal mode) = 1h 0m 0s\\n; filament used [g] = 5.0\\n" > "$out"\n'
    )
    fake.chmod(0o755)
    (tmp_path / "p.ini").write_text("x")
    cfg = SlicerConfig(id="s", name="Fake", slicer_type="prusaslicer",
                       executable_path=str(fake), backend_type="local",
                       created_at=datetime.now(), updated_at=datetime.now())
    backend = LocalProcessBackend(cfg)
    out = tmp_path / "o.gcode"
    res = await backend.slice("/in.stl", _profile(path=str(tmp_path / "p.ini")), str(out))
    assert res.success and res.estimated_print_time == 3600 and res.filament_used == 5.0
