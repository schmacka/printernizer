"""
Test suite for Analytics API endpoints.
Tests printer statistics and related analytics endpoints.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from src.utils.dependencies import get_analytics_service


@pytest.fixture
def client(test_app):
    """Test client fixture using test_app from conftest."""
    return TestClient(test_app)


class TestPrinterStatisticsAPI:
    """Test GET /api/v1/analytics/printers/{printer_id}"""

    def test_get_printer_statistics_success(self, client, test_app):
        """Returns the statistics dict from the analytics service."""
        stats = {
            "printer_id": "printer_001",
            "printer_name": "Test Printer",
            "period": "month",
            "jobs": {
                "total_jobs": 10,
                "completed_jobs": 8,
                "failed_jobs": 2,
                "success_rate": 0.8
            },
            "uptime": {
                "active_hours": 42.5,
                "utilization_percent": 5.9
            },
            "materials": {
                "total_used_kg": 1.234
            }
        }
        mock_service = Mock()
        mock_service.get_printer_statistics = AsyncMock(return_value=stats)
        test_app.dependency_overrides[get_analytics_service] = lambda: mock_service

        response = client.get("/api/v1/analytics/printers/printer_001")

        assert response.status_code == 200
        data = response.json()
        assert data["jobs"]["total_jobs"] == 10
        assert data["jobs"]["success_rate"] == 0.8
        assert data["uptime"]["active_hours"] == 42.5
        assert data["materials"]["total_used_kg"] == 1.234
        mock_service.get_printer_statistics.assert_awaited_once_with("printer_001", "month")

    def test_get_printer_statistics_with_period(self, client, test_app):
        """The period query parameter is forwarded to the service."""
        mock_service = Mock()
        mock_service.get_printer_statistics = AsyncMock(return_value={
            "printer_id": "printer_001", "period": "week",
            "jobs": {}, "uptime": {}, "materials": {}
        })
        test_app.dependency_overrides[get_analytics_service] = lambda: mock_service

        response = client.get("/api/v1/analytics/printers/printer_001?period=week")

        assert response.status_code == 200
        mock_service.get_printer_statistics.assert_awaited_once_with("printer_001", "week")

    def test_get_printer_statistics_not_found(self, client, test_app):
        """Unknown printer IDs return a 404 error."""
        mock_service = Mock()
        mock_service.get_printer_statistics = AsyncMock(return_value=None)
        test_app.dependency_overrides[get_analytics_service] = lambda: mock_service

        response = client.get("/api/v1/analytics/printers/unknown_printer")

        assert response.status_code == 404
