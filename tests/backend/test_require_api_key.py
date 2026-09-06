"""Tests for the require_api_key dependency."""
from unittest.mock import AsyncMock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.api.auth import require_api_key
from src.utils.dependencies import get_api_key_service
from src.utils.errors import PrinternizerError, printernizer_exception_handler

VALID = {"id": "key1", "name": "Laptop",
         "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None}


@pytest.fixture
def app_and_service():
    """A minimal app with one protected route and a stubbed key service."""
    app = FastAPI()
    # Without this, an AuthenticationError propagates out of the route and
    # TestClient re-raises it instead of producing a 401 response.
    app.add_exception_handler(PrinternizerError, printernizer_exception_handler)

    @app.get("/protected")
    async def protected(key=Depends(require_api_key)):
        return {"key_id": key["id"]}

    service = AsyncMock()
    service.verify = AsyncMock(return_value=None)
    app.dependency_overrides[get_api_key_service] = lambda: service
    return app, service


class TestRequireApiKey:
    def test_rejects_request_with_no_key(self, app_and_service):
        app, _ = app_and_service
        response = TestClient(app).get("/protected")
        assert response.status_code == 401

    def test_rejects_unknown_key(self, app_and_service):
        app, service = app_and_service
        service.verify.return_value = None
        response = TestClient(app).get(
            "/protected", headers={"X-Api-Key": "pk_wrong"}
        )
        assert response.status_code == 401

    def test_accepts_valid_x_api_key_header(self, app_and_service):
        app, service = app_and_service
        service.verify.return_value = VALID
        response = TestClient(app).get(
            "/protected", headers={"X-Api-Key": "pk_right"}
        )
        assert response.status_code == 200
        assert response.json()["key_id"] == "key1"
        service.verify.assert_awaited_once_with("pk_right")

    def test_accepts_valid_bearer_token(self, app_and_service):
        app, service = app_and_service
        service.verify.return_value = VALID
        response = TestClient(app).get(
            "/protected", headers={"Authorization": "Bearer pk_right"}
        )
        assert response.status_code == 200
        service.verify.assert_awaited_once_with("pk_right")

    def test_ignores_non_bearer_authorization_scheme(self, app_and_service):
        app, service = app_and_service
        response = TestClient(app).get(
            "/protected", headers={"Authorization": "Basic dXNlcjpwYXNz"}
        )
        assert response.status_code == 401
        service.verify.assert_not_awaited()

    def test_x_api_key_wins_over_authorization_header(self, app_and_service):
        app, service = app_and_service
        service.verify.return_value = VALID
        TestClient(app).get(
            "/protected",
            headers={"X-Api-Key": "pk_primary",
                     "Authorization": "Bearer pk_secondary"},
        )
        service.verify.assert_awaited_once_with("pk_primary")

    def test_error_body_uses_the_project_envelope(self, app_and_service):
        app, _ = app_and_service
        body = TestClient(app).get("/protected").json()
        assert body["status"] == "error"
        assert "message" in body
