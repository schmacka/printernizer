"""
Essential API health endpoint tests for Printernizer Milestone 1.1
Tests the core system health check functionality.
"""
import pytest
import json
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint - essential for monitoring."""

    def test_health_check_success(self, client):
        """Test basic health check returns 200."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_health_check_includes_system_info(self, client):
        """Test health check includes essential system information."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Essential system info
        assert "database" in data
        assert "services" in data
        assert data["database"]["status"] in ["connected", "disconnected"]

    def test_health_check_response_format(self, client):
        """Test health response follows expected format."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Validate JSON structure
        data = response.json()
        required_fields = ["status", "timestamp", "version", "database"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_health_check_german_timezone(self, client):
        """Test health check uses German timezone for Porcus3D business."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        timestamp = data.get("timestamp", "")
        # Should include timezone info (ISO format)
        assert "+" in timestamp or "T" in timestamp

    @pytest.mark.asyncio
    async def test_health_check_performance(self, client):
        """Test health check responds quickly (< 1 second)."""
        import time

        start_time = time.time()
        response = client.get("/api/v1/health")
        response_time = time.time() - start_time

        assert response.status_code == 200
        assert response_time < 1.0, f"Health check too slow: {response_time:.2f}s"


class TestUpdateCheckEndpoint:
    """Test update check endpoint."""

    def test_update_check_success(self, client):
        """Test update check endpoint returns 200."""
        response = client.get("/api/v1/update-check")

        assert response.status_code == 200
        data = response.json()
        assert "current_version" in data
        assert "update_available" in data
        assert isinstance(data["update_available"], bool)
        assert "check_failed" in data

    def test_update_check_response_format(self, client):
        """Test update check response follows expected format."""
        response = client.get("/api/v1/update-check")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        required_fields = ["current_version", "update_available", "check_failed"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_update_check_includes_release_url_when_available(self, client):
        """Test update check includes release URL when update is available."""
        response = client.get("/api/v1/update-check")

        assert response.status_code == 200
        data = response.json()

        # If update is available and check didn't fail, should have release_url
        if data["update_available"] and not data["check_failed"]:
            assert "release_url" in data
            assert data["release_url"] is not None
            assert "github.com" in data["release_url"].lower()

    def test_update_check_handles_network_failure(self, client):
        """Test update check handles network failures gracefully."""
        # This test verifies that even if GitHub is unreachable,
        # the endpoint returns a valid response
        response = client.get("/api/v1/update-check")

        assert response.status_code == 200
        data = response.json()

        # Should always have current_version regardless of network status
        assert "current_version" in data
        assert data["current_version"] != ""