"""Tests for the Printernizer Connect API (/api/v1/connect)."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.utils.dependencies import get_api_key_service, get_printer_service

VALID_KEY = {"id": "key1", "name": "Laptop",
             "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None}
AUTH = {"X-Api-Key": "pk_valid"}


@pytest.fixture
def key_service(test_app):
    stub = AsyncMock()
    stub.verify = AsyncMock(return_value=VALID_KEY)
    test_app.dependency_overrides[get_api_key_service] = lambda: stub
    yield stub
    test_app.dependency_overrides.pop(get_api_key_service, None)


@pytest.fixture
def printer_service(test_app):
    stub = MagicMock()
    stub.list_printers = AsyncMock(return_value=[])
    test_app.dependency_overrides[get_printer_service] = lambda: stub
    yield stub
    test_app.dependency_overrides.pop(get_printer_service, None)


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


class TestConnectInfoAuth:
    def test_requires_an_api_key(self, client, key_service, printer_service):
        assert client.get("/api/v1/connect/info").status_code == 401

    def test_rejects_an_invalid_api_key(self, client, key_service, printer_service):
        key_service.verify.return_value = None
        response = client.get("/api/v1/connect/info",
                              headers={"X-Api-Key": "pk_wrong"})
        assert response.status_code == 401


class TestConnectInfo:
    def test_reports_server_and_minimum_connect_version(
        self, client, key_service, printer_service
    ):
        data = client.get("/api/v1/connect/info", headers=AUTH).json()["data"]
        assert data["server_version"]
        assert data["min_connect_version"] == "0.1.0"

    def test_reports_capabilities(self, client, key_service, printer_service):
        caps = client.get("/api/v1/connect/info",
                          headers=AUTH).json()["data"]["capabilities"]
        assert caps["exports"] is True
        assert caps["profiles"] is False   # M4
        assert caps["printhost"] is False  # M5

    def test_lists_printers(self, client, key_service, printer_service):
        printer = MagicMock()
        printer.id = "printer-1"
        printer.name = "Core One"
        printer.type = MagicMock(value="prusa_core")
        printer.is_active = True
        printer_service.list_printers.return_value = [printer]

        printers = client.get("/api/v1/connect/info",
                              headers=AUTH).json()["data"]["printers"]
        assert printers == [{
            "id": "printer-1", "name": "Core One",
            "type": "prusa_core", "is_active": True,
        }]

    def test_returns_empty_printer_list_when_none_configured(
        self, client, key_service, printer_service
    ):
        data = client.get("/api/v1/connect/info", headers=AUTH).json()["data"]
        assert data["printers"] == []
