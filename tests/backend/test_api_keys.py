"""Tests for API key management endpoints."""
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.utils.dependencies import get_api_key_service

RECORD = {"id": "key1", "name": "My laptop",
          "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None}


@pytest.fixture
def service(test_app):
    """Stub the API key service on the shared test app."""
    stub = AsyncMock()
    stub.list_keys = AsyncMock(return_value=[])
    stub.create_key = AsyncMock(return_value=("pk_plaintext_value", RECORD))
    stub.delete_key = AsyncMock(return_value=True)
    test_app.dependency_overrides[get_api_key_service] = lambda: stub
    yield stub
    test_app.dependency_overrides.pop(get_api_key_service, None)


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


class TestListApiKeys:
    def test_returns_empty_list_initially(self, client, service):
        response = client.get("/api/v1/settings/api-keys")
        assert response.status_code == 200
        assert response.json()["data"]["keys"] == []

    def test_returns_keys_without_hashes(self, client, service):
        service.list_keys.return_value = [RECORD]
        keys = client.get("/api/v1/settings/api-keys").json()["data"]["keys"]
        assert keys[0]["id"] == "key1"
        assert "key_hash" not in keys[0]


class TestCreateApiKey:
    def test_returns_the_plaintext_key_once(self, client, service):
        response = client.post("/api/v1/settings/api-keys",
                               json={"name": "My laptop"})
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["key"] == "pk_plaintext_value"
        assert data["name"] == "My laptop"
        service.create_key.assert_awaited_once_with("My laptop")

    def test_rejects_empty_name(self, client, service):
        response = client.post("/api/v1/settings/api-keys", json={"name": ""})
        assert response.status_code == 422
        service.create_key.assert_not_awaited()

    def test_rejects_missing_name(self, client, service):
        assert client.post("/api/v1/settings/api-keys", json={}).status_code == 422


class TestDeleteApiKey:
    def test_deletes_an_existing_key(self, client, service):
        response = client.delete("/api/v1/settings/api-keys/key1")
        assert response.status_code == 200
        service.delete_key.assert_awaited_once_with("key1")

    def test_returns_404_for_unknown_key(self, client, service):
        service.delete_key.return_value = False
        assert client.delete("/api/v1/settings/api-keys/ghost").status_code == 404
