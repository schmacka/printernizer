"""API tests for the slicer service using a stub runner (no real OrcaSlicer)."""
import io
import json

from fastapi.testclient import TestClient

from app.main import create_app
from app.runner import BaseRunner, RunnerResult


class StubRunner(BaseRunner):
    async def slice(self, model_path, profile, output_dir):
        p = f"{output_dir}/plate_1.gcode"
        with open(p, "w") as f:
            f.write("; total estimated time: 40m 39s\n; filament used [mm] = 1343.10\n")
        return RunnerResult(True, p, 2439, 4.0, None)


def test_slice_flow():
    client = TestClient(create_app(StubRunner()))
    assert client.get("/health").json()["status"] == "ok"
    r = client.post("/slice",
                    files={"file": ("cube.stl", io.BytesIO(b"solid x\nendsolid x\n"))},
                    data={"profile": json.dumps({"system_preset": "x"})})
    job_id = r.json()["job_id"]
    status = client.get(f"/slice/{job_id}").json()
    assert status["status"] == "completed"
    assert status["estimated_print_time"] == 2439
    result = client.get(f"/slice/{job_id}/result")
    assert result.status_code == 200 and result.content.startswith(b"; total")


def test_unknown_job_404():
    client = TestClient(create_app(StubRunner()))
    assert client.get("/slice/nope").status_code == 404
