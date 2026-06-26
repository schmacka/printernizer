import json
from fastapi.testclient import TestClient
from app.profiles import list_bundled_profiles
from app.main import create_app
from app.runner import BaseRunner, RunnerResult


def _stub_tree(tmp_path):
    for vendor, kind, name in [
        ("BBL", "machine", "Bambu Lab A1 0.4 nozzle"),
        ("BBL", "process", "0.20mm Standard @BBL A1"),
        ("BBL", "filament", "Bambu PLA Basic @BBL A1"),
        ("Prusa", "machine", "Prusa CORE One 0.4 nozzle"),
    ]:
        d = tmp_path / vendor / kind
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.json").write_text(json.dumps({"type": kind, "name": name}))
    return str(tmp_path)


def test_list_bundled_profiles(tmp_path):
    out = list_bundled_profiles(_stub_tree(tmp_path))
    assert "Bambu Lab A1 0.4 nozzle" in out["vendors"]["BBL"]["machine"]
    assert "0.20mm Standard @BBL A1" in out["vendors"]["BBL"]["process"]
    assert "Prusa CORE One 0.4 nozzle" in out["vendors"]["Prusa"]["machine"]


class _StubRunner(BaseRunner):
    async def slice(self, model_path, profile, output_dir):
        return RunnerResult(True, None, 1, 1.0, None)


def test_profiles_endpoint(tmp_path):
    runner = _StubRunner()
    runner.profiles_root = _stub_tree(tmp_path)
    client = TestClient(create_app(runner))
    r = client.get("/profiles")
    assert r.status_code == 200
    assert "BBL" in r.json()["vendors"]
