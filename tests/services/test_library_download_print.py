"""Tests for the library file download + print-existing endpoints (Phase 3b)."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from src.main import app
    f = tmp_path / "out.gcode"
    f.write_text("; hello gcode\n")
    lib = MagicMock()
    lib.library_path = tmp_path
    lib.get_file_by_checksum = AsyncMock(return_value={
        "checksum": "ABC", "filename": "out.gcode", "library_path": "out.gcode",
        "file_type": ".gcode", "role": "printfile"})
    app.state.library_service = lib
    return TestClient(app)


def test_download_returns_bytes(client):
    r = client.get("/api/v1/library/files/ABC/download")
    assert r.status_code == 200
    assert r.content == b"; hello gcode\n"


def test_download_404_when_missing(client):
    client.app.state.library_service.get_file_by_checksum = AsyncMock(return_value=None)
    r = client.get("/api/v1/library/files/NOPE/download")
    assert r.status_code == 404


def _printable_lib(tmp_path):
    f = tmp_path / "out.gcode"
    f.write_text("; g\n")
    lib = MagicMock()
    lib.library_path = tmp_path
    lib.get_file_by_checksum = AsyncMock(return_value={
        "checksum": "ABC", "filename": "out.gcode", "library_path": "out.gcode",
        "file_type": ".gcode", "role": "printfile"})
    return lib


def test_print_existing_calls_printer(client, tmp_path):
    app = client.app
    app.state.library_service = _printable_lib(tmp_path)
    driver = MagicMock()
    driver.start_print = AsyncMock(return_value=True)
    psvc = MagicMock()
    psvc.get_printer_driver = AsyncMock(return_value=driver)
    psvc.upload_file_to_printer = AsyncMock(return_value=True)
    app.state.printer_service = psvc
    r = client.post("/api/v1/library/files/ABC/print", json={"printer_id": "p1"})
    assert r.status_code == 200 and r.json()["status"] == "started"
    psvc.upload_file_to_printer.assert_awaited()
    driver.start_print.assert_awaited()


def test_print_rejects_non_printfile(client, tmp_path):
    app = client.app
    f = tmp_path / "model.stl"
    f.write_text("solid x\n")
    lib = MagicMock()
    lib.library_path = tmp_path
    lib.get_file_by_checksum = AsyncMock(return_value={
        "checksum": "M", "filename": "model.stl", "library_path": "model.stl",
        "file_type": ".stl", "role": "model"})
    app.state.library_service = lib
    app.state.printer_service = MagicMock()
    r = client.post("/api/v1/library/files/M/print", json={"printer_id": "p1"})
    assert r.status_code == 400
