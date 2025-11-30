"""
Tests for API endpoints in the aggregation service.

Tests all REST endpoints including submission, deletion, health checks,
and statistics summary.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns service information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Printernizer Usage Statistics Aggregation"
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_check_endpoint(self, client):
        """Test health check endpoint returns detailed status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["database"] == "connected"

    def test_health_check_timestamp_format(self, client):
        """Test health check returns valid ISO timestamp."""
        response = client.get("/health")
        data = response.json()

        # Should be parseable as ISO datetime
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        assert isinstance(timestamp, datetime)


class TestSubmitEndpoint:
    """Tests for the statistics submission endpoint."""

    def test_submit_valid_statistics(self, client, auth_headers, sample_stats_payload):
        """Test submitting valid statistics returns success."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "submission_id" in data
        assert data["submission_id"] > 0
        assert data["message"] == "Statistics submitted successfully"

    def test_submit_creates_database_record(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        db_session
    ):
        """Test that submission creates a database record."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify database record was created
        from services.aggregation.models import Submission
        submission = db_session.query(Submission).filter(
            Submission.installation_id == sample_stats_payload["installation"]["installation_id"]
        ).first()

        assert submission is not None
        assert submission.app_version == "2.7.0"
        assert submission.platform == "linux"
        assert submission.deployment_mode == "docker"
        assert submission.printer_count == 3
        assert submission.total_jobs_completed == 42

    def test_submit_without_authentication(self, client, sample_stats_payload):
        """Test submission without API key returns 403."""
        response = client.post("/submit", json=sample_stats_payload)

        assert response.status_code == 403

    def test_submit_with_invalid_api_key(
        self,
        client,
        invalid_auth_headers,
        sample_stats_payload
    ):
        """Test submission with invalid API key returns 401."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=invalid_auth_headers
        )

        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_submit_invalid_payload_missing_fields(self, client, auth_headers):
        """Test submission with missing required fields returns 422."""
        invalid_payload = {
            "schema_version": "1.0.0"
            # Missing all other required fields
        }

        response = client.post(
            "/submit",
            json=invalid_payload,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_submit_invalid_payload_wrong_types(
        self,
        client,
        auth_headers,
        sample_stats_payload
    ):
        """Test submission with wrong data types returns 422."""
        invalid_payload = sample_stats_payload.copy()
        invalid_payload["printer_fleet"]["printer_count"] = "not-a-number"

        response = client.post(
            "/submit",
            json=invalid_payload,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_submit_multiple_submissions_same_installation(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        db_session
    ):
        """Test multiple submissions from same installation are stored."""
        # First submission
        response1 = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )
        assert response1.status_code == 200
        id1 = response1.json()["submission_id"]

        # Second submission (different time period)
        payload2 = sample_stats_payload.copy()
        payload2["period"]["start"] = (datetime.utcnow() - timedelta(days=14)).isoformat()
        payload2["period"]["end"] = (datetime.utcnow() - timedelta(days=7)).isoformat()

        # Wait to avoid rate limiting
        from services.aggregation.models import RateLimit
        rate_limit = db_session.query(RateLimit).filter(
            RateLimit.installation_id == sample_stats_payload["installation"]["installation_id"]
        ).first()
        if rate_limit:
            rate_limit.window_start = datetime.utcnow() - timedelta(hours=2)
            db_session.commit()

        response2 = client.post(
            "/submit",
            json=payload2,
            headers=auth_headers
        )
        assert response2.status_code == 200
        id2 = response2.json()["submission_id"]

        # Verify both submissions exist
        assert id1 != id2

        from services.aggregation.models import Submission
        count = db_session.query(Submission).filter(
            Submission.installation_id == sample_stats_payload["installation"]["installation_id"]
        ).count()
        assert count == 2

    def test_submit_different_schema_versions(
        self,
        client,
        auth_headers,
        sample_stats_payload
    ):
        """Test submissions with different schema versions are accepted."""
        payload = sample_stats_payload.copy()
        payload["schema_version"] = "2.0.0"

        response = client.post(
            "/submit",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 200


class TestDeleteEndpoint:
    """Tests for the installation data deletion endpoint (GDPR)."""

    def test_delete_installation_data(
        self,
        client,
        auth_headers,
        sample_installation_id,
        create_submission
    ):
        """Test deleting all data for an installation."""
        # Create test submissions
        create_submission(installation_id=sample_installation_id)
        create_submission(installation_id=sample_installation_id)

        response = client.delete(
            f"/installation/{sample_installation_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["deleted_count"] == 2
        assert sample_installation_id in data["message"]

    def test_delete_removes_submissions(
        self,
        client,
        auth_headers,
        sample_installation_id,
        create_submission,
        db_session
    ):
        """Test that deletion removes all submissions from database."""
        create_submission(installation_id=sample_installation_id)

        response = client.delete(
            f"/installation/{sample_installation_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Verify submissions are deleted
        from services.aggregation.models import Submission
        count = db_session.query(Submission).filter(
            Submission.installation_id == sample_installation_id
        ).count()
        assert count == 0

    def test_delete_removes_rate_limits(
        self,
        client,
        auth_headers,
        sample_installation_id,
        create_submission,
        create_rate_limit,
        db_session
    ):
        """Test that deletion removes rate limit records."""
        create_submission(installation_id=sample_installation_id)
        create_rate_limit(installation_id=sample_installation_id)

        response = client.delete(
            f"/installation/{sample_installation_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Verify rate limit is deleted
        from services.aggregation.models import RateLimit
        count = db_session.query(RateLimit).filter(
            RateLimit.installation_id == sample_installation_id
        ).count()
        assert count == 0

    def test_delete_nonexistent_installation(self, client, auth_headers):
        """Test deleting nonexistent installation returns success with 0 count."""
        response = client.delete(
            "/installation/nonexistent-id",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 0

    def test_delete_without_authentication(self, client, sample_installation_id):
        """Test deletion without API key returns 403."""
        response = client.delete(f"/installation/{sample_installation_id}")

        assert response.status_code == 403

    def test_delete_only_affects_target_installation(
        self,
        client,
        auth_headers,
        create_submission,
        db_session
    ):
        """Test deletion only removes data for specified installation."""
        # Create submissions for two different installations
        create_submission(installation_id="installation-1")
        create_submission(installation_id="installation-2")

        # Delete only installation-1
        response = client.delete(
            "/installation/installation-1",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Verify only installation-1 is deleted
        from services.aggregation.models import Submission
        count_1 = db_session.query(Submission).filter(
            Submission.installation_id == "installation-1"
        ).count()
        count_2 = db_session.query(Submission).filter(
            Submission.installation_id == "installation-2"
        ).count()

        assert count_1 == 0
        assert count_2 == 1


class TestStatsSummaryEndpoint:
    """Tests for the statistics summary endpoint."""

    def test_stats_summary_empty_database(self, client, auth_headers):
        """Test stats summary with no submissions."""
        response = client.get("/stats/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_submissions"] == 0
        assert data["unique_installations"] == 0
        assert data["latest_submission_at"] is None
        assert "timestamp" in data

    def test_stats_summary_with_submissions(
        self,
        client,
        auth_headers,
        create_submission
    ):
        """Test stats summary with multiple submissions."""
        # Create submissions from different installations
        create_submission(installation_id="installation-1")
        create_submission(installation_id="installation-2")
        create_submission(installation_id="installation-1")  # Duplicate installation

        response = client.get("/stats/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_submissions"] == 3
        assert data["unique_installations"] == 2
        assert data["latest_submission_at"] is not None

    def test_stats_summary_latest_submission_timestamp(
        self,
        client,
        auth_headers,
        create_submission
    ):
        """Test that latest_submission_at is the most recent submission."""
        old_time = datetime.utcnow() - timedelta(days=7)
        new_time = datetime.utcnow()

        create_submission(
            installation_id="old",
            submitted_at=old_time
        )
        create_submission(
            installation_id="new",
            submitted_at=new_time
        )

        response = client.get("/stats/summary", headers=auth_headers)
        data = response.json()

        latest = datetime.fromisoformat(data["latest_submission_at"].replace("Z", "+00:00"))

        # Latest should be within 1 second of new_time
        assert abs((latest - new_time.replace(tzinfo=None)).total_seconds()) < 1

    def test_stats_summary_without_authentication(self, client):
        """Test stats summary without API key returns 403."""
        response = client.get("/stats/summary")

        assert response.status_code == 403

    def test_stats_summary_with_invalid_api_key(
        self,
        client,
        invalid_auth_headers
    ):
        """Test stats summary with invalid API key returns 401."""
        response = client.get("/stats/summary", headers=invalid_auth_headers)

        assert response.status_code == 401

    def test_stats_summary_timestamp_is_current(self, client, auth_headers):
        """Test that summary timestamp is current time."""
        response = client.get("/stats/summary", headers=auth_headers)
        data = response.json()

        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        now = datetime.utcnow()

        # Timestamp should be within 2 seconds of now
        assert abs((timestamp - now).total_seconds()) < 2


class TestCORSHeaders:
    """Tests for CORS headers."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.get("/")

        # FastAPI CORS middleware adds these headers
        assert "access-control-allow-origin" in response.headers

    def test_options_request(self, client):
        """Test OPTIONS request for CORS preflight."""
        response = client.options("/submit")

        assert response.status_code in [200, 405]  # Depends on configuration


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_invalid_json_payload(self, client, auth_headers):
        """Test submission with invalid JSON returns 422."""
        response = client.post(
            "/submit",
            data="invalid json {",
            headers={**auth_headers, "Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_endpoint_not_found(self, client):
        """Test accessing nonexistent endpoint returns 404."""
        response = client.get("/nonexistent")

        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test using wrong HTTP method returns 405."""
        response = client.post("/")  # Root only accepts GET

        assert response.status_code == 405
