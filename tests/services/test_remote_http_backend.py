"""Tests for RemoteHTTPBackend using a dependency-free fake aiohttp session."""
import json
from datetime import datetime

from src.services.slicer_backends.remote_http import RemoteHTTPBackend
from src.models.slicer import SlicerConfig, SlicerProfile, ProfileType


class _Resp:
    def __init__(self, payload=None, data=b""):
        self._payload, self._data, self.status = payload, data, 200

    async def json(self):
        return self._payload

    async def read(self):
        return self._data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _Session:
    """Scripts: POST -> job_id, GET status -> completed, GET result -> bytes."""
    def __init__(self):
        self.gcode = b"; estimated printing time (normal mode) = 0h 40m 39s\n; filament used [g] = 4.0\n"

    def post(self, url, data=None):
        return _Resp(payload={"job_id": "j1"})

    def get(self, url):
        if url.endswith("/result"):
            return _Resp(data=self.gcode)
        return _Resp(payload={"status": "completed", "progress": 100,
                              "estimated_print_time": 2439, "filament_used": 4.0, "error": None})

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def _cfg():
    return SlicerConfig(id="s", name="Remote", slicer_type="orcaslicer",
                        executable_path="", backend_type="remote",
                        endpoint_url="http://slicer:8001",
                        created_at=datetime.now(), updated_at=datetime.now())


async def test_remote_slice_downloads_result(tmp_path):
    prof = SlicerProfile(id="p", slicer_id="s", profile_name="A1",
                         profile_type=ProfileType.PRINT,
                         settings_json=json.dumps({"system_preset": "0.20mm Standard @BBL A1"}),
                         created_at=datetime.now(), updated_at=datetime.now())
    backend = RemoteHTTPBackend(_cfg(), session_factory=lambda: _Session(),
                                poll_interval=0)
    (tmp_path / "in.stl").write_text("solid x\nendsolid x\n")
    out = tmp_path / "o.gcode"
    res = await backend.slice(str(tmp_path / "in.stl"), prof, str(out))
    assert res.success and res.estimated_print_time == 2439
    assert out.exists() and out.read_bytes().startswith(b"; estimated")
