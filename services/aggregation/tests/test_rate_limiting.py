"""
Tests for rate limiting functionality in the aggregation service.

Tests the rate limiting enforcement to prevent abuse, including
per-installation limits, time window resets, and rate limit tracking.
"""
import pytest
from datetime import datetime, timedelta
from services.aggregation.models import RateLimit


class TestRateLimitBasics:
    """Basic rate limiting tests."""

    def test_first_submission_creates_rate_limit(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        db_session
    ):
        """Test that first submission creates a rate limit record."""
        installation_id = sample_stats_payload["installation"]["installation_id"]

        # Verify no rate limit exists initially
        rate_limit = db_session.query(RateLimit).filter(
            RateLimit.installation_id == installation_id
        ).first()
        assert rate_limit is None

        # Submit statistics
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )
        assert response.status_code == 200

        # Verify rate limit record was created
        rate_limit = db_session.query(RateLimit).filter(
            RateLimit.installation_id == installation_id
        ).first()
        assert rate_limit is not None
        assert rate_limit.submission_count == 1

    def test_rate_limit_enforcement(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        db_session
    ):
        """Test that rate limit is enforced (10 submissions per hour)."""
        # Submit 10 times (should all succeed)
        for i in range(10):
            response = client.post(
                "/submit",
                json=sample_stats_payload,
                headers=auth_headers
            )
            if i < 10:  # First 10 should succeed
                assert response.status_code == 200
            else:  # 11th should be rate limited
                assert response.status_code == 429

        # 11th submission should be rate limited
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    def test_rate_limit_increments_count(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        db_session
    ):
        """Test that each submission increments the rate limit count."""
        installation_id = sample_stats_payload["installation"]["installation_id"]

        # Submit 3 times
        for i in range(3):
            response = client.post(
                "/submit",
                json=sample_stats_payload,
                headers=auth_headers
            )
            assert response.status_code == 200

            # Check count after each submission
            rate_limit = db_session.query(RateLimit).filter(
                RateLimit.installation_id == installation_id
            ).first()
            assert rate_limit.submission_count == i + 1

    def test_rate_limit_updates_last_submission_time(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        db_session
    ):
        """Test that last_submission_at is updated on each submission."""
        installation_id = sample_stats_payload["installation"]["installation_id"]

        # First submission
        response1 = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )
        assert response1.status_code == 200

        rate_limit = db_session.query(RateLimit).filter(
            RateLimit.installation_id == installation_id
        ).first()
        first_time = rate_limit.last_submission_at

        # Wait a moment (in test, we'll manually update the time)
        import time
        time.sleep(0.1)

        # Second submission
        response2 = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )
        assert response2.status_code == 200

        db_session.refresh(rate_limit)
        second_time = rate_limit.last_submission_at

        # Second time should be after first time
        assert second_time > first_time


class TestRateLimitWindowReset:
    """Tests for rate limit window resets."""

    def test_window_reset_after_one_hour(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        create_rate_limit,
        db_session
    ):
        """Test that rate limit resets after 1 hour window expires."""
        installation_id = sample_stats_payload["installation"]["installation_id"]

        # Create rate limit at max count (10) with window_start 2 hours ago
        old_window = datetime.utcnow() - timedelta(hours=2)
        create_rate_limit(
            installation_id=installation_id,
            submission_count=10,
            window_start=old_window
        )

        # New submission should succeed (new window)
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )
        assert response.status_code == 200

        # Verify count was reset to 1
        rate_limit = db_session.query(RateLimit).filter(
            RateLimit.installation_id == installation_id
        ).first()
        assert rate_limit.submission_count == 1

        # Verify window_start was updated
        assert rate_limit.window_start > old_window

    def test_window_not_reset_within_hour(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        create_rate_limit,
        db_session
    ):
        """Test that rate limit persists within 1 hour window."""
        installation_id = sample_stats_payload["installation"]["installation_id"]

        # Create rate limit at count 5 with window_start 30 minutes ago
        recent_window = datetime.utcnow() - timedelta(minutes=30)
        create_rate_limit(
            installation_id=installation_id,
            submission_count=5,
            window_start=recent_window
        )

        # New submission should increment (same window)
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )
        assert response.status_code == 200

        # Verify count was incremented, not reset
        rate_limit = db_session.query(RateLimit).filter(
            RateLimit.installation_id == installation_id
        ).first()
        assert rate_limit.submission_count == 6

        # Verify window_start unchanged
        assert abs((rate_limit.window_start - recent_window).total_seconds()) < 1

    def test_exact_window_boundary(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        create_rate_limit,
        db_session
    ):
        """Test behavior at exact 1 hour boundary."""
        installation_id = sample_stats_payload["installation"]["installation_id"]

        # Create rate limit exactly 1 hour and 1 second ago
        boundary_time = datetime.utcnow() - timedelta(hours=1, seconds=1)
        create_rate_limit(
            installation_id=installation_id,
            submission_count=10,
            window_start=boundary_time
        )

        # Should reset and allow submission
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )
        assert response.status_code == 200


class TestRateLimitPerInstallation:
    """Tests for per-installation rate limiting."""

    def test_different_installations_independent_limits(
        self,
        client,
        auth_headers,
        sample_stats_payload
    ):
        """Test that different installations have independent rate limits."""
        # Create two different payloads with different installation IDs
        payload1 = sample_stats_payload.copy()
        payload1["installation"] = payload1["installation"].copy()
        payload1["installation"]["installation_id"] = "installation-1"

        payload2 = sample_stats_payload.copy()
        payload2["installation"] = payload2["installation"].copy()
        payload2["installation"]["installation_id"] = "installation-2"

        # Submit 10 times for each installation
        for i in range(10):
            response1 = client.post("/submit", json=payload1, headers=auth_headers)
            response2 = client.post("/submit", json=payload2, headers=auth_headers)

            assert response1.status_code == 200
            assert response2.status_code == 200

        # Both should be rate limited on 11th submission
        response1 = client.post("/submit", json=payload1, headers=auth_headers)
        response2 = client.post("/submit", json=payload2, headers=auth_headers)

        assert response1.status_code == 429
        assert response2.status_code == 429

    def test_rate_limit_isolation(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        create_rate_limit
    ):
        """Test that rate limiting one installation doesn't affect others."""
        # Rate limit installation-1
        create_rate_limit(
            installation_id="installation-1",
            submission_count=10,
            window_start=datetime.utcnow()
        )

        # Submission from installation-2 should still succeed
        payload = sample_stats_payload.copy()
        payload["installation"] = payload["installation"].copy()
        payload["installation"]["installation_id"] = "installation-2"

        response = client.post("/submit", json=payload, headers=auth_headers)
        assert response.status_code == 200


class TestRateLimitErrorMessages:
    """Tests for rate limit error messages."""

    def test_rate_limit_error_message(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        create_rate_limit
    ):
        """Test that rate limit error includes helpful message."""
        installation_id = sample_stats_payload["installation"]["installation_id"]

        # Max out rate limit
        create_rate_limit(
            installation_id=installation_id,
            submission_count=10,
            window_start=datetime.utcnow()
        )

        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )

        assert response.status_code == 429
        detail = response.json()["detail"]
        assert "Rate limit exceeded" in detail
        assert "10" in detail  # Should mention the limit
        assert "hour" in detail

    def test_rate_limit_status_code(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        create_rate_limit
    ):
        """Test that rate limit returns correct HTTP status code."""
        installation_id = sample_stats_payload["installation"]["installation_id"]

        create_rate_limit(
            installation_id=installation_id,
            submission_count=10,
            window_start=datetime.utcnow()
        )

        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )

        # Should be 429 Too Many Requests
        assert response.status_code == 429


class TestRateLimitDatabaseOperations:
    """Tests for rate limit database operations."""

    def test_rate_limit_unique_constraint(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        db_session
    ):
        """Test that only one rate limit record exists per installation."""
        installation_id = sample_stats_payload["installation"]["installation_id"]

        # Submit multiple times
        for _ in range(3):
            response = client.post(
                "/submit",
                json=sample_stats_payload,
                headers=auth_headers
            )
            assert response.status_code == 200

        # Verify only one rate limit record exists
        count = db_session.query(RateLimit).filter(
            RateLimit.installation_id == installation_id
        ).count()
        assert count == 1

    def test_rate_limit_cleanup_on_deletion(
        self,
        client,
        auth_headers,
        sample_installation_id,
        create_submission,
        create_rate_limit,
        db_session
    ):
        """Test that rate limits are deleted with installation data."""
        create_submission(installation_id=sample_installation_id)
        create_rate_limit(installation_id=sample_installation_id)

        # Delete installation data
        response = client.delete(
            f"/installation/{sample_installation_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Verify rate limit is also deleted
        count = db_session.query(RateLimit).filter(
            RateLimit.installation_id == sample_installation_id
        ).count()
        assert count == 0


class TestRateLimitEdgeCases:
    """Tests for rate limiting edge cases."""

    def test_concurrent_submissions_same_installation(
        self,
        client,
        auth_headers,
        sample_stats_payload
    ):
        """Test handling of concurrent submissions (simplified test)."""
        # Note: True concurrency testing requires threading/asyncio
        # This test verifies sequential rapid submissions work correctly

        responses = []
        for _ in range(5):
            response = client.post(
                "/submit",
                json=sample_stats_payload,
                headers=auth_headers
            )
            responses.append(response)

        # All should succeed (within rate limit)
        for response in responses:
            assert response.status_code == 200

    def test_submission_after_rate_limit_reached(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        create_rate_limit,
        db_session
    ):
        """Test that submissions fail consistently after rate limit reached."""
        installation_id = sample_stats_payload["installation"]["installation_id"]

        # Max out rate limit
        create_rate_limit(
            installation_id=installation_id,
            submission_count=10,
            window_start=datetime.utcnow()
        )

        # Multiple submissions should all fail
        for _ in range(3):
            response = client.post(
                "/submit",
                json=sample_stats_payload,
                headers=auth_headers
            )
            assert response.status_code == 429

        # Count should still be 10 (not incrementing failed attempts)
        rate_limit = db_session.query(RateLimit).filter(
            RateLimit.installation_id == installation_id
        ).first()
        assert rate_limit.submission_count == 10

    def test_rate_limit_with_very_old_window(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        create_rate_limit,
        db_session
    ):
        """Test rate limit reset with very old window_start."""
        installation_id = sample_stats_payload["installation"]["installation_id"]

        # Create rate limit with window_start 30 days ago
        old_window = datetime.utcnow() - timedelta(days=30)
        create_rate_limit(
            installation_id=installation_id,
            submission_count=10,
            window_start=old_window
        )

        # Should reset and allow submission
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )
        assert response.status_code == 200

        # Verify window was updated
        rate_limit = db_session.query(RateLimit).filter(
            RateLimit.installation_id == installation_id
        ).first()
        assert rate_limit.window_start > old_window
        assert rate_limit.submission_count == 1
