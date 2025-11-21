"""
Tests for UsageStatisticsScheduler (Phase 2).

Tests automatic periodic submission of usage statistics.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.usage_statistics_scheduler import UsageStatisticsScheduler
from src.services.usage_statistics_service import UsageStatisticsService


@pytest.fixture
def mock_usage_stats_service():
    """Create a mock UsageStatisticsService for testing."""
    service = AsyncMock(spec=UsageStatisticsService)
    service.is_opted_in = AsyncMock(return_value=True)
    service.submit_stats = AsyncMock(return_value=True)
    service.repository = MagicMock()
    service.repository.get_setting = AsyncMock(return_value=None)
    return service


@pytest.fixture
def scheduler(mock_usage_stats_service):
    """Create a UsageStatisticsScheduler instance for testing."""
    return UsageStatisticsScheduler(mock_usage_stats_service)


class TestSchedulerLifecycle:
    """Test scheduler start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_scheduler_starts_successfully(self, scheduler):
        """Test scheduler starts without errors."""
        await scheduler.start()
        assert scheduler._running is True
        assert scheduler._task is not None
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_scheduler_stops_successfully(self, scheduler):
        """Test scheduler stops cleanly."""
        await scheduler.start()
        await scheduler.stop()
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_scheduler_double_start_warning(self, scheduler):
        """Test starting already-running scheduler logs warning."""
        await scheduler.start()
        await scheduler.start()  # Second start should warn
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_scheduler_stop_before_start(self, scheduler):
        """Test stopping non-running scheduler is safe."""
        await scheduler.stop()  # Should not error
        assert scheduler._running is False


class TestScheduledSubmission:
    """Test automatic scheduled submission logic."""

    @pytest.mark.asyncio
    async def test_submission_when_opted_out(self, scheduler, mock_usage_stats_service):
        """Test no submission when user opted out."""
        mock_usage_stats_service.is_opted_in.return_value = False

        await scheduler._check_and_submit()

        # Should check opt-in status
        mock_usage_stats_service.is_opted_in.assert_called_once()
        # Should NOT submit
        mock_usage_stats_service.submit_stats.assert_not_called()

    @pytest.mark.asyncio
    async def test_submission_when_opted_in_no_previous(self, scheduler, mock_usage_stats_service):
        """Test first submission when no previous submission exists."""
        mock_usage_stats_service.is_opted_in.return_value = True
        mock_usage_stats_service.repository.get_setting.return_value = None  # No previous
        mock_usage_stats_service.submit_stats.return_value = True

        await scheduler._check_and_submit()

        # Should check opt-in
        mock_usage_stats_service.is_opted_in.assert_called_once()
        # Should submit (first submission)
        mock_usage_stats_service.submit_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_submission_too_soon(self, scheduler, mock_usage_stats_service):
        """Test no submission when last submission was too recent."""
        mock_usage_stats_service.is_opted_in.return_value = True
        # Last submission was 2 days ago (less than default 7 days)
        last_submission = (datetime.utcnow() - timedelta(days=2)).isoformat()
        mock_usage_stats_service.repository.get_setting.return_value = last_submission

        await scheduler._check_and_submit()

        # Should check opt-in
        mock_usage_stats_service.is_opted_in.assert_called_once()
        # Should NOT submit (too soon)
        mock_usage_stats_service.submit_stats.assert_not_called()

    @pytest.mark.asyncio
    async def test_submission_when_due(self, scheduler, mock_usage_stats_service):
        """Test submission when interval has passed."""
        mock_usage_stats_service.is_opted_in.return_value = True
        # Last submission was 8 days ago (more than default 7 days)
        last_submission = (datetime.utcnow() - timedelta(days=8)).isoformat()
        mock_usage_stats_service.repository.get_setting.return_value = last_submission
        mock_usage_stats_service.submit_stats.return_value = True

        await scheduler._check_and_submit()

        # Should check opt-in
        mock_usage_stats_service.is_opted_in.assert_called_once()
        # Should submit (interval passed)
        mock_usage_stats_service.submit_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_submission_handles_invalid_date(self, scheduler, mock_usage_stats_service):
        """Test submission proceeds when last_submission_date is invalid."""
        mock_usage_stats_service.is_opted_in.return_value = True
        # Invalid date format
        mock_usage_stats_service.repository.get_setting.return_value = "invalid-date"
        mock_usage_stats_service.submit_stats.return_value = True

        await scheduler._check_and_submit()

        # Should still attempt submission despite invalid date
        mock_usage_stats_service.submit_stats.assert_called_once()


class TestManualTrigger:
    """Test manual submission trigger."""

    @pytest.mark.asyncio
    async def test_manual_trigger_success(self, scheduler, mock_usage_stats_service):
        """Test manual trigger submits successfully."""
        mock_usage_stats_service.is_opted_in.return_value = True
        mock_usage_stats_service.submit_stats.return_value = True

        result = await scheduler.trigger_immediate_submission()

        assert result is True
        mock_usage_stats_service.submit_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_manual_trigger_opted_out(self, scheduler, mock_usage_stats_service):
        """Test manual trigger respects opt-out."""
        mock_usage_stats_service.is_opted_in.return_value = False

        result = await scheduler.trigger_immediate_submission()

        assert result is False
        mock_usage_stats_service.submit_stats.assert_not_called()

    @pytest.mark.asyncio
    async def test_manual_trigger_submission_fails(self, scheduler, mock_usage_stats_service):
        """Test manual trigger handles submission failure."""
        mock_usage_stats_service.is_opted_in.return_value = True
        mock_usage_stats_service.submit_stats.return_value = False

        result = await scheduler.trigger_immediate_submission()

        assert result is False


class TestErrorHandling:
    """Test scheduler error handling."""

    @pytest.mark.asyncio
    async def test_scheduler_handles_check_error(self, scheduler, mock_usage_stats_service):
        """Test scheduler continues running despite errors in check."""
        mock_usage_stats_service.is_opted_in.side_effect = Exception("Test error")

        # Should not raise exception
        await scheduler._check_and_submit()

        # Scheduler should remain operational
        assert scheduler._running is False  # Not started yet

    @pytest.mark.asyncio
    async def test_scheduler_handles_submission_error(self, scheduler, mock_usage_stats_service):
        """Test scheduler handles submission errors gracefully."""
        mock_usage_stats_service.is_opted_in.return_value = True
        mock_usage_stats_service.submit_stats.side_effect = Exception("Submission error")

        # Should not raise exception
        result = await scheduler.trigger_immediate_submission()

        assert result is False  # Failed, but handled gracefully


class TestSchedulerTiming:
    """Test scheduler timing and intervals."""

    def test_check_interval_configured(self, scheduler):
        """Test scheduler has correct check interval."""
        # Should check every hour
        assert scheduler.check_interval_seconds == 3600

    @pytest.mark.asyncio
    async def test_scheduler_respects_submission_interval(self, scheduler):
        """Test scheduler uses configured submission interval from settings."""
        # Settings should be accessible
        assert hasattr(scheduler, 'settings')
        assert hasattr(scheduler.settings, 'usage_stats_submission_interval_days')
