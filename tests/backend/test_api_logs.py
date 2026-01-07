"""
API tests for the unified log viewer endpoints.
Tests querying, filtering, exporting, and clearing logs.
"""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def client(test_app):
    """Test client fixture using test_app from conftest."""
    return TestClient(test_app)


@pytest.fixture
def mock_log_file(tmp_path):
    """Create a mock backend error log file for testing."""
    log_file = tmp_path / "data" / "logs" / "backend_errors.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create sample log entries
    now = datetime.now()
    entries = [
        {
            "id": "err_001",
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "category": "PRINTER",
            "severity": "high",
            "type": "ConnectionError",
            "message": "Failed to connect to printer",
            "traceback": "Traceback...",
            "context": {"printer_id": "test123"},
            "user_message": "Printer connection failed"
        },
        {
            "id": "err_002",
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "category": "DATABASE",
            "severity": "medium",
            "type": "QueryError",
            "message": "Database query timeout",
            "traceback": "Traceback...",
            "context": {"query": "SELECT..."},
            "user_message": "Database error"
        },
        {
            "id": "err_003",
            "timestamp": (now - timedelta(days=2)).isoformat(),
            "category": "API",
            "severity": "low",
            "type": "ValidationError",
            "message": "Invalid request parameters",
            "traceback": "",
            "context": {},
            "user_message": "Invalid input"
        },
    ]

    with open(log_file, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    return log_file


class TestLogsQueryEndpoint:
    """Test GET /api/v1/logs endpoint."""

    def test_query_logs_success(self, client):
        """Test basic log query returns 200."""
        response = client.get("/api/v1/logs")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert isinstance(data["data"], list)

    def test_query_logs_pagination(self, client):
        """Test pagination parameters."""
        response = client.get("/api/v1/logs?page=1&per_page=10")

        assert response.status_code == 200
        data = response.json()
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["per_page"] == 10
        assert "total" in pagination
        assert "total_pages" in pagination

    def test_query_logs_filter_by_level(self, client):
        """Test filtering by log level."""
        response = client.get("/api/v1/logs?level=error")

        assert response.status_code == 200
        data = response.json()
        # All returned logs should be error or higher severity
        for log in data["data"]:
            assert log["level"] in ["error", "critical"]

    def test_query_logs_filter_by_source(self, client):
        """Test filtering by log source."""
        response = client.get("/api/v1/logs?source=errors")

        assert response.status_code == 200
        data = response.json()
        # All returned logs should be from errors source
        for log in data["data"]:
            assert log["source"] == "errors"

    def test_query_logs_filter_by_category(self, client):
        """Test filtering by category."""
        response = client.get("/api/v1/logs?category=PRINTER")

        assert response.status_code == 200
        data = response.json()
        for log in data["data"]:
            assert log["category"].upper() == "PRINTER"

    def test_query_logs_search(self, client):
        """Test full-text search in messages."""
        response = client.get("/api/v1/logs?search=error")

        assert response.status_code == 200
        data = response.json()
        # Results should contain search term
        for log in data["data"]:
            assert "error" in log["message"].lower() or "error" in log["category"].lower()

    def test_query_logs_date_range(self, client):
        """Test date range filtering."""
        start = (datetime.now() - timedelta(days=1)).isoformat()
        end = datetime.now().isoformat()

        response = client.get(f"/api/v1/logs?start_date={start}&end_date={end}")

        assert response.status_code == 200
        data = response.json()
        # All logs should be within date range
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        for log in data["data"]:
            log_dt = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
            assert start_dt <= log_dt <= end_dt

    def test_query_logs_sort_order(self, client):
        """Test sorting by timestamp."""
        # Descending (default)
        response = client.get("/api/v1/logs?sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        if len(data["data"]) > 1:
            timestamps = [log["timestamp"] for log in data["data"]]
            assert timestamps == sorted(timestamps, reverse=True)

        # Ascending
        response = client.get("/api/v1/logs?sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        if len(data["data"]) > 1:
            timestamps = [log["timestamp"] for log in data["data"]]
            assert timestamps == sorted(timestamps)

    def test_query_logs_includes_statistics(self, client):
        """Test that query includes statistics."""
        response = client.get("/api/v1/logs")

        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data
        stats = data["statistics"]
        assert "total" in stats
        assert "last_24h" in stats
        assert "by_level" in stats
        assert "by_source" in stats

    def test_query_logs_invalid_page(self, client):
        """Test invalid page number is handled."""
        response = client.get("/api/v1/logs?page=0")
        assert response.status_code == 422  # Validation error

    def test_query_logs_invalid_per_page(self, client):
        """Test invalid per_page is handled."""
        response = client.get("/api/v1/logs?per_page=500")
        assert response.status_code == 422  # Max is 200


class TestLogsSourcesEndpoint:
    """Test GET /api/v1/logs/sources endpoint."""

    def test_get_sources_success(self, client):
        """Test getting available log sources."""
        response = client.get("/api/v1/logs/sources")

        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert isinstance(data["sources"], list)

        # Check expected sources exist
        source_names = [s["source"] for s in data["sources"]]
        assert "frontend" in source_names
        assert "backend" in source_names
        assert "errors" in source_names

    def test_get_sources_includes_counts(self, client):
        """Test sources include count information."""
        response = client.get("/api/v1/logs/sources")

        assert response.status_code == 200
        data = response.json()
        for source in data["sources"]:
            assert "count" in source
            assert "available" in source
            assert isinstance(source["count"], int)
            assert isinstance(source["available"], bool)


class TestLogsStatisticsEndpoint:
    """Test GET /api/v1/logs/statistics endpoint."""

    def test_get_statistics_success(self, client):
        """Test getting log statistics."""
        response = client.get("/api/v1/logs/statistics")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "last_24h" in data
        assert "by_level" in data
        assert "by_source" in data
        assert "by_category" in data

    def test_get_statistics_with_hours(self, client):
        """Test statistics with custom hours parameter."""
        response = client.get("/api/v1/logs/statistics?hours=48")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data


class TestLogsCategoriesEndpoint:
    """Test GET /api/v1/logs/categories endpoint."""

    def test_get_categories_success(self, client):
        """Test getting unique log categories."""
        response = client.get("/api/v1/logs/categories")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Categories should be strings
        for category in data:
            assert isinstance(category, str)


class TestLogsExportEndpoint:
    """Test GET /api/v1/logs/export endpoint."""

    def test_export_json_success(self, client):
        """Test exporting logs as JSON."""
        response = client.get("/api/v1/logs/export?format=json")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert "attachment" in response.headers.get("content-disposition", "")

        # Validate JSON content
        data = response.json()
        assert isinstance(data, list)

    def test_export_csv_success(self, client):
        """Test exporting logs as CSV."""
        response = client.get("/api/v1/logs/export?format=csv")

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers.get("content-disposition", "")

        # Validate CSV has header
        content = response.text
        assert "Timestamp" in content
        assert "Source" in content
        assert "Level" in content

    def test_export_with_filters(self, client):
        """Test export respects filters."""
        response = client.get("/api/v1/logs/export?format=json&level=error")

        assert response.status_code == 200
        data = response.json()
        for log in data:
            assert log["level"] in ["error", "critical"]

    def test_export_filename_includes_date(self, client):
        """Test export filename includes date."""
        response = client.get("/api/v1/logs/export?format=json")

        assert response.status_code == 200
        disposition = response.headers.get("content-disposition", "")
        assert "printernizer_logs_" in disposition
        assert ".json" in disposition


class TestLogsClearEndpoint:
    """Test DELETE /api/v1/logs endpoint."""

    def test_clear_logs_success(self, client):
        """Test clearing all logs."""
        response = client.delete("/api/v1/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "count" in data

    def test_clear_logs_by_source(self, client):
        """Test clearing logs from specific source."""
        response = client.delete("/api/v1/logs?source=errors")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestLogsResponseFormat:
    """Test response format consistency."""

    def test_log_entry_format(self, client):
        """Test log entries follow expected format."""
        response = client.get("/api/v1/logs")

        assert response.status_code == 200
        data = response.json()

        for log in data["data"]:
            # Required fields
            assert "id" in log
            assert "source" in log
            assert "timestamp" in log
            assert "level" in log
            assert "category" in log
            assert "message" in log

            # Valid source
            assert log["source"] in ["frontend", "backend", "errors"]

            # Valid level
            assert log["level"] in ["debug", "info", "warn", "error", "critical"]

    def test_pagination_format(self, client):
        """Test pagination follows expected format."""
        response = client.get("/api/v1/logs?page=1&per_page=25")

        assert response.status_code == 200
        data = response.json()
        pagination = data["pagination"]

        assert isinstance(pagination["page"], int)
        assert isinstance(pagination["per_page"], int)
        assert isinstance(pagination["total"], int)
        assert isinstance(pagination["total_pages"], int)
        assert pagination["page"] >= 1
        assert pagination["per_page"] >= 1
        assert pagination["total"] >= 0
        assert pagination["total_pages"] >= 1


class TestLogsPerformance:
    """Test endpoint performance."""

    def test_query_response_time(self, client):
        """Test query endpoint responds quickly."""
        import time

        start = time.time()
        response = client.get("/api/v1/logs")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0, f"Query too slow: {elapsed:.2f}s"

    def test_statistics_response_time(self, client):
        """Test statistics endpoint responds quickly."""
        import time

        start = time.time()
        response = client.get("/api/v1/logs/statistics")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Statistics too slow: {elapsed:.2f}s"


class TestLogsEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_search(self, client):
        """Test empty search returns all logs."""
        response = client.get("/api/v1/logs?search=")

        assert response.status_code == 200

    def test_no_matching_logs(self, client):
        """Test query with no matching results."""
        response = client.get("/api/v1/logs?search=xyznonexistent123")

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total"] == 0
        assert len(data["data"]) == 0

    def test_special_characters_in_search(self, client):
        """Test search with special characters."""
        response = client.get("/api/v1/logs?search=test%20message")

        assert response.status_code == 200

    def test_future_date_range(self, client):
        """Test date range in the future returns empty."""
        future = (datetime.now() + timedelta(days=365)).isoformat()
        response = client.get(f"/api/v1/logs?start_date={future}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0
