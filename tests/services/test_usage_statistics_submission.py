"""
Tests for usage statistics submission (Phase 2).

Tests HTTP submission logic, retry mechanism, and error handling.
"""
import pytest
import asyncio
import aiohttp
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.usage_statistics_service import UsageStatisticsService
from src.database.database import Database
from src.models.usage_statistics import AggregatedStats, InstallationInfo, TimePeriod, PrinterFleetStats, UsageStats
from contextlib import asynccontextmanager


def create_mock_aiohttp_session(mock_response):
    """Create a properly mocked aiohttp.ClientSession with async context manager support."""
    # Create mock for the response context manager (session.post() result)
    mock_response_cm = MagicMock()
    mock_response_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response_cm.__aexit__ = AsyncMock(return_value=None)

    # Create mock session instance with post method
    mock_session_instance = MagicMock()
    mock_session_instance.post = MagicMock(return_value=mock_response_cm)

    # Create mock for the session context manager (ClientSession() result)
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session_instance)
    mock_session_cm.__aexit__ = AsyncMock(return_value=None)

    # Create mock for ClientSession class
    mock_client_session = MagicMock(return_value=mock_session_cm)

    return mock_client_session, mock_session_instance


@pytest.fixture
def mock_database():
    """Create a mock database for testing."""
    db = MagicMock(spec=Database)
    db._connection = MagicMock()
    return db


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    repo = MagicMock()
    repo.get_setting = AsyncMock()
    repo.set_setting = AsyncMock()
    repo.mark_events_submitted = AsyncMock()
    repo.get_events = AsyncMock(return_value=[])
    repo.get_event_counts_by_type = AsyncMock(return_value={})
    repo.get_first_event_timestamp = AsyncMock(return_value=datetime.utcnow())
    return repo


@pytest.fixture
def mock_aggregated_stats():
    """Create mock aggregated statistics for testing."""
    return AggregatedStats(
        schema_version="1.0.0",
        period=TimePeriod(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 7),
            duration_days=6
        ),
        installation=InstallationInfo(
            installation_id="a1234567-89ab-cdef-0123-456789abcdef",
            first_seen=datetime(2024, 1, 1),
            app_version="2.7.0",
            python_version="3.11.0",
            platform="linux",
            deployment_mode="docker",
            country_code="DE"
        ),
        printer_fleet=PrinterFleetStats(
            printer_count=2,
            printer_types=["bambu_lab", "prusa_core"],
            printer_type_counts={"bambu_lab": 1, "prusa_core": 1}
        ),
        usage_stats=UsageStats(
            job_count=8,
            file_count=15,
            upload_count=5,
            uptime_hours=168,
            feature_usage={
                "library_enabled": True,
                "timelapse_enabled": True
            }
        )
    )


@pytest.fixture
def usage_stats_service(mock_database, mock_repository):
    """Create UsageStatisticsService instance for testing."""
    service = UsageStatisticsService(mock_database, mock_repository)
    service._init_timestamp = datetime.utcnow()
    return service


class TestSubmissionOptIn:
    """Test submission respects opt-in status."""

    @pytest.mark.asyncio
    async def test_no_submission_when_opted_out(self, usage_stats_service, mock_repository):
        """Test submission is skipped when user opted out."""
        mock_repository.get_setting.return_value = "disabled"

        result = await usage_stats_service.submit_stats()

        assert result is True  # Returns True (no error, just skipped)
        # Should not attempt to aggregate or submit
        mock_repository.mark_events_submitted.assert_not_called()

    @pytest.mark.asyncio
    async def test_submission_when_opted_in(self, usage_stats_service, mock_repository, mock_aggregated_stats):
        """Test submission proceeds when user opted in."""
        mock_repository.get_setting.return_value = "enabled"

        # Create properly mocked response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"status":"success"}')

        mock_client_session, mock_session_instance = create_mock_aiohttp_session(mock_response)

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=mock_aggregated_stats):
            with patch('aiohttp.ClientSession', mock_client_session):
                result = await usage_stats_service.submit_stats()

                assert result is True


class TestHttpSubmission:
    """Test HTTP submission logic."""

    @pytest.mark.asyncio
    async def test_successful_submission(self, usage_stats_service, mock_repository, mock_aggregated_stats):
        """Test successful HTTP submission."""
        mock_repository.get_setting.return_value = "enabled"

        # Create properly mocked response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"submission_id": 123}')

        mock_client_session, mock_session_instance = create_mock_aiohttp_session(mock_response)

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=mock_aggregated_stats):
            with patch('aiohttp.ClientSession', mock_client_session):
                result = await usage_stats_service.submit_stats()

                assert result is True
                # Should mark events as submitted
                mock_repository.mark_events_submitted.assert_called_once()
                # Should update last submission date
                assert mock_repository.set_setting.call_count >= 1

    @pytest.mark.asyncio
    async def test_submission_authentication(self, usage_stats_service, mock_repository, mock_aggregated_stats):
        """Test submission includes API key authentication."""
        mock_repository.get_setting.return_value = "enabled"

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{}')

        mock_client_session, mock_session_instance = create_mock_aiohttp_session(mock_response)

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=mock_aggregated_stats):
            with patch('aiohttp.ClientSession', mock_client_session):
                await usage_stats_service.submit_stats()

                # Verify API key header was included
                call_kwargs = mock_session_instance.post.call_args[1]
                assert 'headers' in call_kwargs
                assert 'X-API-Key' in call_kwargs['headers']

    @pytest.mark.asyncio
    async def test_submission_timeout_configured(self, usage_stats_service, mock_repository, mock_aggregated_stats):
        """Test submission uses configured timeout."""
        mock_repository.get_setting.return_value = "enabled"

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{}')

        mock_client_session, mock_session_instance = create_mock_aiohttp_session(mock_response)

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=mock_aggregated_stats):
            with patch('aiohttp.ClientSession', mock_client_session):
                await usage_stats_service.submit_stats()

                # Verify timeout was configured
                call_kwargs = mock_session_instance.post.call_args[1]
                assert 'timeout' in call_kwargs


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self, usage_stats_service, mock_repository, mock_aggregated_stats):
        """Test retries on network error."""
        mock_repository.get_setting.return_value = "enabled"

        # Create a mock session that raises network error on post
        mock_session_instance = MagicMock()
        mock_session_instance.post = MagicMock(side_effect=aiohttp.ClientError("Network error"))

        mock_session_cm = MagicMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_cm.__aexit__ = AsyncMock(return_value=None)

        mock_client_session = MagicMock(return_value=mock_session_cm)

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=mock_aggregated_stats):
            with patch('aiohttp.ClientSession', mock_client_session):
                result = await usage_stats_service.submit_stats()

                assert result is False  # Failed after all retries
                # Should have tried multiple times (default: 3 retries = 4 total attempts)
                assert mock_session_instance.post.call_count == 4

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, usage_stats_service, mock_repository, mock_aggregated_stats):
        """Test retries on timeout."""
        mock_repository.get_setting.return_value = "enabled"

        # Create a mock session that raises timeout on post
        mock_session_instance = MagicMock()
        mock_session_instance.post = MagicMock(side_effect=asyncio.TimeoutError())

        mock_session_cm = MagicMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_cm.__aexit__ = AsyncMock(return_value=None)

        mock_client_session = MagicMock(return_value=mock_session_cm)

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=mock_aggregated_stats):
            with patch('aiohttp.ClientSession', mock_client_session):
                result = await usage_stats_service.submit_stats()

                assert result is False
                # Should have retried
                assert mock_session_instance.post.call_count > 1

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, usage_stats_service, mock_repository, mock_aggregated_stats):
        """Test retries on 429 rate limit."""
        mock_repository.get_setting.return_value = "enabled"

        mock_response = MagicMock()
        mock_response.status = 429  # Rate limited
        mock_response.text = AsyncMock(return_value='Rate limit exceeded')

        mock_client_session, mock_session_instance = create_mock_aiohttp_session(mock_response)

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=mock_aggregated_stats):
            with patch('aiohttp.ClientSession', mock_client_session):
                result = await usage_stats_service.submit_stats()

                assert result is False
                # Should have retried
                assert mock_session_instance.post.call_count > 1

    @pytest.mark.asyncio
    async def test_no_retry_on_auth_error(self, usage_stats_service, mock_repository, mock_aggregated_stats):
        """Test no retry on 401 authentication error."""
        mock_repository.get_setting.return_value = "enabled"

        mock_response = MagicMock()
        mock_response.status = 401  # Authentication failed
        mock_response.text = AsyncMock(return_value='Invalid API key')

        mock_client_session, mock_session_instance = create_mock_aiohttp_session(mock_response)

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=mock_aggregated_stats):
            with patch('aiohttp.ClientSession', mock_client_session):
                result = await usage_stats_service.submit_stats()

                assert result is False
                # Should NOT retry on auth error
                assert mock_session_instance.post.call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retry(self, usage_stats_service, mock_repository, mock_aggregated_stats):
        """Test successful submission after retry."""
        mock_repository.get_setting.return_value = "enabled"

        # Create responses for fail then success
        mock_response_fail = MagicMock()
        mock_response_fail.status = 500
        mock_response_fail.text = AsyncMock(return_value='Server error')

        mock_response_success = MagicMock()
        mock_response_success.status = 200
        mock_response_success.text = AsyncMock(return_value='Success')

        # Create response context managers for each attempt
        mock_response_cm_fail = MagicMock()
        mock_response_cm_fail.__aenter__ = AsyncMock(return_value=mock_response_fail)
        mock_response_cm_fail.__aexit__ = AsyncMock(return_value=None)

        mock_response_cm_success = MagicMock()
        mock_response_cm_success.__aenter__ = AsyncMock(return_value=mock_response_success)
        mock_response_cm_success.__aexit__ = AsyncMock(return_value=None)

        # Create mock session instance with post method that returns different responses
        mock_session_instance = MagicMock()
        mock_session_instance.post = MagicMock(side_effect=[mock_response_cm_fail, mock_response_cm_success])

        mock_session_cm = MagicMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_cm.__aexit__ = AsyncMock(return_value=None)

        mock_client_session = MagicMock(return_value=mock_session_cm)

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=mock_aggregated_stats):
            with patch('aiohttp.ClientSession', mock_client_session):
                result = await usage_stats_service.submit_stats()

                assert result is True
                assert mock_session_instance.post.call_count == 2  # Failed once, succeeded second time


class TestAggregationFailure:
    """Test handling when aggregation fails."""

    @pytest.mark.asyncio
    async def test_submission_fails_if_no_stats(self, usage_stats_service, mock_repository):
        """Test submission fails gracefully if aggregation returns None."""
        mock_repository.get_setting.return_value = "enabled"

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=None):
            result = await usage_stats_service.submit_stats()

            assert result is False


class TestEventMarking:
    """Test events are properly marked as submitted."""

    @pytest.mark.asyncio
    async def test_events_marked_on_success(self, usage_stats_service, mock_repository, mock_aggregated_stats):
        """Test events are marked as submitted on successful submission."""
        mock_repository.get_setting.return_value = "enabled"

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='Success')

        mock_client_session, mock_session_instance = create_mock_aiohttp_session(mock_response)

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=mock_aggregated_stats):
            with patch('aiohttp.ClientSession', mock_client_session):
                await usage_stats_service.submit_stats()

                # Should mark events within the period
                mock_repository.mark_events_submitted.assert_called_once_with(
                    mock_aggregated_stats.period.start,
                    mock_aggregated_stats.period.end
                )

    @pytest.mark.asyncio
    async def test_events_not_marked_on_failure(self, usage_stats_service, mock_repository, mock_aggregated_stats):
        """Test events are NOT marked when submission fails."""
        mock_repository.get_setting.return_value = "enabled"

        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value='Server error')

        mock_client_session, mock_session_instance = create_mock_aiohttp_session(mock_response)

        with patch.object(usage_stats_service, 'aggregate_stats', return_value=mock_aggregated_stats):
            with patch('aiohttp.ClientSession', mock_client_session):
                await usage_stats_service.submit_stats()

                # Should NOT mark events
                mock_repository.mark_events_submitted.assert_not_called()
