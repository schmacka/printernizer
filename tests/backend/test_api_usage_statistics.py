"""
Comprehensive tests for Usage Statistics API endpoints.

Tests cover all API routes: local stats, opt-in/opt-out, export, delete, and status.
"""
import pytest
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from src.models.usage_statistics import (
    LocalStatsResponse,
    OptInResponse
)


@pytest.fixture
def mock_usage_stats_service():
    """Create mock UsageStatisticsService for API testing"""
    service = MagicMock()

    # Mock repository
    service.repository = MagicMock()
    service.repository.get_total_event_count = AsyncMock(return_value=100)

    # Mock service methods
    service.get_local_stats = AsyncMock(return_value=LocalStatsResponse(
        installation_id=str(uuid.uuid4()),
        first_seen=datetime.utcnow() - timedelta(days=30),
        opt_in_status="disabled",
        total_events=100,
        this_week={"job_count": 10, "file_count": 5, "error_count": 1},
        last_submission=None
    ))

    service.opt_in = AsyncMock(return_value=OptInResponse(
        success=True,
        installation_id=str(uuid.uuid4()),
        message="Usage statistics enabled. Thank you for helping improve Printernizer!"
    ))

    service.opt_out = AsyncMock(return_value=OptInResponse(
        success=True,
        message="Usage statistics disabled. Your data will remain local."
    ))

    service.export_stats = AsyncMock(return_value=json.dumps({
        "events": [],
        "settings": {},
        "exported_at": datetime.utcnow().isoformat(),
        "export_version": "1.0"
    }))

    service.delete_all_stats = AsyncMock(return_value=True)

    service.is_opted_in = AsyncMock(return_value=False)

    return service


@pytest.fixture
def client_with_usage_stats(test_app, mock_usage_stats_service):
    """Create test client with usage statistics service"""
    test_app.state.usage_statistics_service = mock_usage_stats_service
    return TestClient(test_app)


# =====================================================
# GET /local Tests
# =====================================================

class TestGetLocalStatistics:
    """Tests for GET /api/v1/usage-stats/local endpoint"""

    def test_get_local_stats_success(self, client_with_usage_stats):
        """Test successful retrieval of local statistics"""
        response = client_with_usage_stats.get("/api/v1/usage-stats/local")

        assert response.status_code == 200
        data = response.json()

        assert "installation_id" in data
        assert "opt_in_status" in data
        assert "total_events" in data
        assert "this_week" in data
        assert data["opt_in_status"] in ["enabled", "disabled"]
        assert isinstance(data["total_events"], int)

    def test_get_local_stats_includes_this_week_summary(self, client_with_usage_stats):
        """Test that local stats include this week's summary"""
        response = client_with_usage_stats.get("/api/v1/usage-stats/local")

        assert response.status_code == 200
        data = response.json()

        assert "this_week" in data
        assert "job_count" in data["this_week"]
        assert "file_count" in data["this_week"]
        assert "error_count" in data["this_week"]

    def test_get_local_stats_when_service_unavailable(self, test_app):
        """Test GET /local when service is not available"""
        test_app.state.usage_statistics_service = None
        client = TestClient(test_app)

        response = client.get("/api/v1/usage-stats/local")

        assert response.status_code == 503
        assert "not available" in response.json()["detail"].lower()

    def test_get_local_stats_handles_service_error(self, client_with_usage_stats, mock_usage_stats_service):
        """Test GET /local handles service errors gracefully"""
        mock_usage_stats_service.get_local_stats.side_effect = Exception("Database error")

        response = client_with_usage_stats.get("/api/v1/usage-stats/local")

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


# =====================================================
# POST /opt-in Tests
# =====================================================

class TestOptInStatistics:
    """Tests for POST /api/v1/usage-stats/opt-in endpoint"""

    def test_opt_in_success(self, client_with_usage_stats):
        """Test successful opt-in"""
        response = client_with_usage_stats.post("/api/v1/usage-stats/opt-in")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "installation_id" in data
        assert "message" in data
        assert "enabled" in data["message"].lower() or "thank" in data["message"].lower()

    def test_opt_in_generates_installation_id(self, client_with_usage_stats):
        """Test that opt-in returns an installation ID"""
        response = client_with_usage_stats.post("/api/v1/usage-stats/opt-in")

        assert response.status_code == 200
        data = response.json()

        assert "installation_id" in data
        installation_id = data["installation_id"]
        # Verify UUID format
        assert len(installation_id) == 36
        assert installation_id.count('-') == 4

    def test_opt_in_when_service_unavailable(self, test_app):
        """Test POST /opt-in when service is not available"""
        test_app.state.usage_statistics_service = None
        client = TestClient(test_app)

        response = client.post("/api/v1/usage-stats/opt-in")

        assert response.status_code == 503

    def test_opt_in_handles_service_failure(self, client_with_usage_stats, mock_usage_stats_service):
        """Test POST /opt-in handles service failures"""
        mock_usage_stats_service.opt_in.return_value = OptInResponse(
            success=False,
            message="Failed to enable statistics"
        )

        response = client_with_usage_stats.post("/api/v1/usage-stats/opt-in")

        assert response.status_code == 500

    def test_opt_in_handles_exceptions(self, client_with_usage_stats, mock_usage_stats_service):
        """Test POST /opt-in handles exceptions gracefully"""
        mock_usage_stats_service.opt_in.side_effect = Exception("Database error")

        response = client_with_usage_stats.post("/api/v1/usage-stats/opt-in")

        assert response.status_code == 500


# =====================================================
# POST /opt-out Tests
# =====================================================

class TestOptOutStatistics:
    """Tests for POST /api/v1/usage-stats/opt-out endpoint"""

    def test_opt_out_success(self, client_with_usage_stats):
        """Test successful opt-out"""
        response = client_with_usage_stats.post("/api/v1/usage-stats/opt-out")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "message" in data
        assert "disabled" in data["message"].lower() or "local" in data["message"].lower()

    def test_opt_out_when_service_unavailable(self, test_app):
        """Test POST /opt-out when service is not available"""
        test_app.state.usage_statistics_service = None
        client = TestClient(test_app)

        response = client.post("/api/v1/usage-stats/opt-out")

        assert response.status_code == 503

    def test_opt_out_handles_service_failure(self, client_with_usage_stats, mock_usage_stats_service):
        """Test POST /opt-out handles service failures"""
        mock_usage_stats_service.opt_out.return_value = OptInResponse(
            success=False,
            message="Failed to disable statistics"
        )

        response = client_with_usage_stats.post("/api/v1/usage-stats/opt-out")

        assert response.status_code == 500

    def test_opt_out_handles_exceptions(self, client_with_usage_stats, mock_usage_stats_service):
        """Test POST /opt-out handles exceptions gracefully"""
        mock_usage_stats_service.opt_out.side_effect = Exception("Database error")

        response = client_with_usage_stats.post("/api/v1/usage-stats/opt-out")

        assert response.status_code == 500


# =====================================================
# GET /export Tests
# =====================================================

class TestExportStatistics:
    """Tests for GET /api/v1/usage-stats/export endpoint"""

    def test_export_success(self, client_with_usage_stats):
        """Test successful statistics export"""
        response = client_with_usage_stats.get("/api/v1/usage-stats/export")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Verify it's valid JSON
        data = response.json()
        assert "events" in data
        assert "settings" in data
        assert "exported_at" in data
        assert "export_version" in data

    def test_export_returns_downloadable_file(self, client_with_usage_stats):
        """Test that export returns a downloadable file"""
        response = client_with_usage_stats.get("/api/v1/usage-stats/export")

        assert response.status_code == 200
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        assert "filename=usage-statistics-export.json" in response.headers["Content-Disposition"]

    def test_export_when_service_unavailable(self, test_app):
        """Test GET /export when service is not available"""
        test_app.state.usage_statistics_service = None
        client = TestClient(test_app)

        response = client.get("/api/v1/usage-stats/export")

        assert response.status_code == 503

    def test_export_handles_service_error(self, client_with_usage_stats, mock_usage_stats_service):
        """Test GET /export handles service errors"""
        mock_usage_stats_service.export_stats.side_effect = Exception("Export failed")

        response = client_with_usage_stats.get("/api/v1/usage-stats/export")

        assert response.status_code == 500


# =====================================================
# DELETE / Tests
# =====================================================

class TestDeleteStatistics:
    """Tests for DELETE /api/v1/usage-stats endpoint"""

    def test_delete_success(self, client_with_usage_stats, mock_usage_stats_service):
        """Test successful deletion of statistics"""
        mock_usage_stats_service.repository.get_total_event_count.return_value = 100

        response = client_with_usage_stats.delete("/api/v1/usage-stats")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "deleted_events" in data
        assert data["deleted_events"] == 100
        assert "message" in data

    def test_delete_returns_event_count(self, client_with_usage_stats, mock_usage_stats_service):
        """Test that delete returns count of deleted events"""
        mock_usage_stats_service.repository.get_total_event_count.return_value = 250

        response = client_with_usage_stats.delete("/api/v1/usage-stats")

        assert response.status_code == 200
        data = response.json()

        assert data["deleted_events"] == 250

    def test_delete_when_no_events(self, client_with_usage_stats, mock_usage_stats_service):
        """Test deletion when no events exist"""
        mock_usage_stats_service.repository.get_total_event_count.return_value = 0

        response = client_with_usage_stats.delete("/api/v1/usage-stats")

        assert response.status_code == 200
        data = response.json()

        assert data["deleted_events"] == 0

    def test_delete_when_service_unavailable(self, test_app):
        """Test DELETE / when service is not available"""
        test_app.state.usage_statistics_service = None
        client = TestClient(test_app)

        response = client.delete("/api/v1/usage-stats")

        assert response.status_code == 503

    def test_delete_handles_service_failure(self, client_with_usage_stats, mock_usage_stats_service):
        """Test DELETE / handles service failures"""
        mock_usage_stats_service.delete_all_stats.return_value = False

        response = client_with_usage_stats.delete("/api/v1/usage-stats")

        assert response.status_code == 500

    def test_delete_handles_exceptions(self, client_with_usage_stats, mock_usage_stats_service):
        """Test DELETE / handles exceptions gracefully"""
        mock_usage_stats_service.repository.get_total_event_count.side_effect = Exception("Database error")

        response = client_with_usage_stats.delete("/api/v1/usage-stats")

        assert response.status_code == 500


# =====================================================
# GET /status Tests
# =====================================================

class TestGetStatisticsStatus:
    """Tests for GET /api/v1/usage-stats/status endpoint"""

    def test_get_status_success(self, client_with_usage_stats):
        """Test successful status retrieval"""
        response = client_with_usage_stats.get("/api/v1/usage-stats/status")

        assert response.status_code == 200
        data = response.json()

        assert "service_available" in data
        assert "opted_in" in data
        assert "total_events" in data
        assert "collection_active" in data

    def test_get_status_when_opted_in(self, client_with_usage_stats, mock_usage_stats_service):
        """Test status when user is opted in"""
        mock_usage_stats_service.is_opted_in.return_value = True

        response = client_with_usage_stats.get("/api/v1/usage-stats/status")

        assert response.status_code == 200
        data = response.json()

        assert data["service_available"] is True
        assert data["opted_in"] is True

    def test_get_status_when_opted_out(self, client_with_usage_stats, mock_usage_stats_service):
        """Test status when user is opted out"""
        mock_usage_stats_service.is_opted_in.return_value = False

        response = client_with_usage_stats.get("/api/v1/usage-stats/status")

        assert response.status_code == 200
        data = response.json()

        assert data["opted_in"] is False

    def test_get_status_when_service_unavailable(self, test_app):
        """Test GET /status when service is not available"""
        test_app.state.usage_statistics_service = None
        client = TestClient(test_app)

        response = client.get("/api/v1/usage-stats/status")

        assert response.status_code == 200  # Status endpoint returns 200 even if unavailable
        data = response.json()

        assert data["service_available"] is False
        assert data["opted_in"] is False
        assert data["total_events"] == 0
        assert data["collection_active"] is False

    def test_get_status_handles_errors_gracefully(self, client_with_usage_stats, mock_usage_stats_service):
        """Test GET /status handles errors gracefully"""
        mock_usage_stats_service.is_opted_in.side_effect = Exception("Database error")

        response = client_with_usage_stats.get("/api/v1/usage-stats/status")

        assert response.status_code == 200  # Status endpoint doesn't fail
        data = response.json()

        assert data["service_available"] is False
        assert "error" in data


# =====================================================
# Integration Tests
# =====================================================

class TestAPIIntegration:
    """Integration tests for usage statistics API flow"""

    def test_complete_opt_in_flow(self, client_with_usage_stats):
        """Test complete opt-in workflow"""
        # 1. Check initial status
        response = client_with_usage_stats.get("/api/v1/usage-stats/status")
        assert response.status_code == 200

        # 2. Opt in
        response = client_with_usage_stats.post("/api/v1/usage-stats/opt-in")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 3. Check local stats
        response = client_with_usage_stats.get("/api/v1/usage-stats/local")
        assert response.status_code == 200

    def test_complete_opt_out_flow(self, client_with_usage_stats):
        """Test complete opt-out workflow"""
        # 1. Opt out
        response = client_with_usage_stats.post("/api/v1/usage-stats/opt-out")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 2. Verify status
        response = client_with_usage_stats.get("/api/v1/usage-stats/status")
        assert response.status_code == 200

    def test_export_and_delete_flow(self, client_with_usage_stats):
        """Test export followed by delete"""
        # 1. Export data
        response = client_with_usage_stats.get("/api/v1/usage-stats/export")
        assert response.status_code == 200
        export_data = response.json()

        # 2. Delete data
        response = client_with_usage_stats.delete("/api/v1/usage-stats")
        assert response.status_code == 200
        assert response.json()["success"] is True


# =====================================================
# Error Handling Tests
# =====================================================

class TestAPIErrorHandling:
    """Tests for API error handling"""

    def test_endpoints_handle_missing_service(self, test_app):
        """Test that all endpoints handle missing service gracefully"""
        test_app.state.usage_statistics_service = None
        client = TestClient(test_app)

        endpoints = [
            ("GET", "/api/v1/usage-stats/local", 503),
            ("POST", "/api/v1/usage-stats/opt-in", 503),
            ("POST", "/api/v1/usage-stats/opt-out", 503),
            ("GET", "/api/v1/usage-stats/export", 503),
            ("DELETE", "/api/v1/usage-stats", 503),
            ("GET", "/api/v1/usage-stats/status", 200),  # Status returns 200 with service_available=False
        ]

        for method, endpoint, expected_status in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint)
            elif method == "DELETE":
                response = client.delete(endpoint)

            assert response.status_code == expected_status, f"Failed for {method} {endpoint}"

    def test_endpoints_return_proper_error_messages(self, test_app):
        """Test that endpoints return helpful error messages"""
        test_app.state.usage_statistics_service = None
        client = TestClient(test_app)

        response = client.get("/api/v1/usage-stats/local")
        assert response.status_code == 503
        assert "detail" in response.json()
        assert len(response.json()["detail"]) > 0


# =====================================================
# Response Model Tests
# =====================================================

class TestAPIResponseModels:
    """Tests for API response model validation"""

    def test_local_stats_response_format(self, client_with_usage_stats):
        """Test that local stats response matches expected format"""
        response = client_with_usage_stats.get("/api/v1/usage-stats/local")

        data = response.json()
        required_fields = [
            "installation_id",
            "opt_in_status",
            "total_events",
            "this_week"
        ]

        for field in required_fields:
            assert field in data

    def test_opt_in_response_format(self, client_with_usage_stats):
        """Test that opt-in response matches expected format"""
        response = client_with_usage_stats.post("/api/v1/usage-stats/opt-in")

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)

    def test_delete_response_format(self, client_with_usage_stats):
        """Test that delete response matches expected format"""
        response = client_with_usage_stats.delete("/api/v1/usage-stats")

        data = response.json()
        assert "success" in data
        assert "deleted_events" in data
        assert "message" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["deleted_events"], int)
        assert isinstance(data["message"], str)

    def test_status_response_format(self, client_with_usage_stats):
        """Test that status response matches expected format"""
        response = client_with_usage_stats.get("/api/v1/usage-stats/status")

        data = response.json()
        required_fields = [
            "service_available",
            "opted_in",
            "total_events",
            "collection_active"
        ]

        for field in required_fields:
            assert field in data
            # All fields should be boolean or int
            assert isinstance(data[field], (bool, int))
