"""
Tests for API key authentication in the aggregation service.

Tests authentication requirements, header validation, and security
for all protected endpoints.
"""
import pytest


class TestAPIKeyAuthentication:
    """Tests for API key authentication mechanism."""

    def test_valid_api_key_header(self, client, auth_headers, sample_stats_payload):
        """Test that valid API key in header allows access."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_invalid_api_key_header(
        self,
        client,
        invalid_auth_headers,
        sample_stats_payload
    ):
        """Test that invalid API key returns 401."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=invalid_auth_headers
        )

        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_missing_api_key_header(self, client, sample_stats_payload):
        """Test that missing API key returns 403."""
        response = client.post(
            "/submit",
            json=sample_stats_payload
            # No headers
        )

        assert response.status_code == 403

    def test_empty_api_key_header(self, client, sample_stats_payload):
        """Test that empty API key returns 401."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers={"X-API-Key": ""}
        )

        assert response.status_code in [401, 403]

    def test_case_sensitive_header_name(self, client, sample_stats_payload):
        """Test that header name is case-insensitive (HTTP standard)."""
        # HTTP headers should be case-insensitive
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers={"x-api-key": "test-api-key-123"}  # lowercase
        )

        # FastAPI/Starlette handles case-insensitive headers
        assert response.status_code == 200

    def test_api_key_in_wrong_header(self, client, sample_stats_payload):
        """Test that API key in wrong header name fails."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers={"Authorization": "test-api-key-123"}  # Wrong header name
        )

        assert response.status_code == 403


class TestEndpointProtection:
    """Tests that all protected endpoints require authentication."""

    def test_submit_requires_auth(self, client, sample_stats_payload):
        """Test that submit endpoint requires authentication."""
        response = client.post("/submit", json=sample_stats_payload)
        assert response.status_code == 403

    def test_delete_requires_auth(self, client, sample_installation_id):
        """Test that delete endpoint requires authentication."""
        response = client.delete(f"/installation/{sample_installation_id}")
        assert response.status_code == 403

    def test_stats_summary_requires_auth(self, client):
        """Test that stats summary endpoint requires authentication."""
        response = client.get("/stats/summary")
        assert response.status_code == 403

    def test_health_check_no_auth_required(self, client):
        """Test that health check endpoints don't require auth."""
        response1 = client.get("/")
        response2 = client.get("/health")

        assert response1.status_code == 200
        assert response2.status_code == 200


class TestAuthenticationErrorResponses:
    """Tests for authentication error response formats."""

    def test_auth_error_response_format(self, client, sample_stats_payload):
        """Test that auth errors return proper JSON format."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers={"X-API-Key": "wrong-key"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_auth_error_message_clarity(self, client, sample_stats_payload):
        """Test that auth error messages are clear."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers={"X-API-Key": "wrong-key"}
        )

        detail = response.json()["detail"]
        assert "Invalid API key" in detail or "api key" in detail.lower()

    def test_missing_header_error_format(self, client, sample_stats_payload):
        """Test error format when API key header is missing."""
        response = client.post("/submit", json=sample_stats_payload)

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data


class TestAPIKeyValidation:
    """Tests for API key validation logic."""

    def test_whitespace_in_api_key_fails(self, client, sample_stats_payload):
        """Test that API key with whitespace fails."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers={"X-API-Key": "test-api-key-123 "}  # Trailing space
        )

        # Should fail - whitespace matters
        assert response.status_code == 401

    def test_api_key_prefix_not_sufficient(self, client, sample_stats_payload):
        """Test that partial API key match fails."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers={"X-API-Key": "test-api-key"}  # Missing "-123"
        )

        assert response.status_code == 401

    def test_api_key_case_sensitive(self, client, sample_stats_payload):
        """Test that API key is case-sensitive."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers={"X-API-Key": "TEST-API-KEY-123"}  # Wrong case
        )

        assert response.status_code == 401


class TestMultipleAuthenticatedRequests:
    """Tests for multiple requests with authentication."""

    def test_api_key_reusable(self, client, auth_headers, sample_stats_payload):
        """Test that API key can be used multiple times."""
        for _ in range(3):
            response = client.post(
                "/submit",
                json=sample_stats_payload,
                headers=auth_headers
            )
            # Note: May hit rate limit, but auth should work
            assert response.status_code in [200, 429]  # Success or rate limited

    def test_different_endpoints_same_key(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        create_submission
    ):
        """Test that same API key works for all endpoints."""
        # Submit
        response1 = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )
        assert response1.status_code == 200

        # Stats summary
        response2 = client.get("/stats/summary", headers=auth_headers)
        assert response2.status_code == 200

        # Delete
        create_submission(installation_id="test-id")
        response3 = client.delete("/installation/test-id", headers=auth_headers)
        assert response3.status_code == 200


class TestSecurityHeaders:
    """Tests for security-related headers."""

    def test_no_api_key_leakage_in_response(
        self,
        client,
        auth_headers,
        sample_stats_payload
    ):
        """Test that API key is not leaked in responses."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )

        # API key should not appear in response
        response_text = response.text.lower()
        assert "test-api-key" not in response_text
        assert auth_headers["X-API-Key"] not in response.text

    def test_auth_error_no_key_leakage(self, client, sample_stats_payload):
        """Test that auth errors don't leak the expected API key."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers={"X-API-Key": "wrong-key"}
        )

        # Expected key should not be in error message
        response_text = response.text.lower()
        assert "test-api-key-123" not in response_text


class TestAuthenticationBypass:
    """Tests to ensure authentication cannot be bypassed."""

    def test_cannot_bypass_with_query_param(self, client, sample_stats_payload):
        """Test that API key in query param doesn't work."""
        response = client.post(
            "/submit?X-API-Key=test-api-key-123",
            json=sample_stats_payload
        )

        assert response.status_code == 403

    def test_cannot_bypass_with_body_field(self, client, sample_stats_payload):
        """Test that API key in request body doesn't work."""
        payload = sample_stats_payload.copy()
        payload["api_key"] = "test-api-key-123"

        response = client.post("/submit", json=payload)

        assert response.status_code == 403

    def test_cannot_bypass_with_cookie(self, client, sample_stats_payload):
        """Test that API key in cookie doesn't work."""
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            cookies={"X-API-Key": "test-api-key-123"}
        )

        assert response.status_code == 403


class TestAuthWithInvalidRequests:
    """Tests authentication with various invalid request formats."""

    def test_auth_with_invalid_json(self, client, auth_headers):
        """Test that auth check happens before JSON validation."""
        # Valid auth, invalid JSON
        response = client.post(
            "/submit",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )

        # Should fail on validation (422), not auth (401/403)
        # This proves auth check passed
        assert response.status_code == 422

    def test_auth_with_wrong_content_type(self, client, auth_headers):
        """Test authentication with wrong content type."""
        response = client.post(
            "/submit",
            data="some data",
            headers={**auth_headers, "Content-Type": "text/plain"}
        )

        # Should fail on content type/validation, not auth
        assert response.status_code != 401
        assert response.status_code != 403

    def test_no_auth_with_invalid_json(self, client):
        """Test that missing auth fails even with invalid JSON."""
        response = client.post(
            "/submit",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        # Should fail on auth (403), before JSON validation
        assert response.status_code == 403


class TestAuthenticationIntegration:
    """Integration tests for authentication with other features."""

    def test_auth_with_rate_limiting(
        self,
        client,
        auth_headers,
        sample_stats_payload,
        create_rate_limit
    ):
        """Test that auth is checked before rate limiting."""
        # Max out rate limit
        installation_id = sample_stats_payload["installation"]["installation_id"]
        create_rate_limit(
            installation_id=installation_id,
            submission_count=10,
            window_start=datetime.utcnow()
        )

        # Invalid auth should fail with 401, not 429
        response = client.post(
            "/submit",
            json=sample_stats_payload,
            headers={"X-API-Key": "wrong-key"}
        )

        assert response.status_code == 401

    def test_auth_persists_across_requests(
        self,
        client,
        auth_headers,
        sample_stats_payload
    ):
        """Test that authentication state doesn't persist (stateless)."""
        # First request with auth
        response1 = client.post(
            "/submit",
            json=sample_stats_payload,
            headers=auth_headers
        )
        assert response1.status_code == 200

        # Second request without auth should fail
        response2 = client.post(
            "/submit",
            json=sample_stats_payload
            # No headers
        )
        assert response2.status_code == 403


# Import datetime for rate limiting test
from datetime import datetime
