"""
Usage Statistics Submission Scheduler

Handles automatic periodic submission of usage statistics to the aggregation service.
Implements weekly submission checks with configurable intervals.

Key Features:
    - Automatic weekly submission (every Sunday at 3 AM UTC by default)
    - Checks opt-in status before submitting
    - Respects last_submission_date to avoid duplicates
    - Non-blocking background execution
    - Graceful error handling (never breaks application)

Usage Example:
    ```python
    # In main.py startup
    scheduler = UsageStatisticsScheduler(usage_stats_service)
    await scheduler.start()

    # On shutdown
    await scheduler.stop()
    ```
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import structlog

from src.services.usage_statistics_service import UsageStatisticsService
from src.utils.config import get_settings

logger = structlog.get_logger()


class UsageStatisticsScheduler:
    """
    Scheduler for automatic periodic usage statistics submissions.

    Runs in the background and periodically checks if statistics
    should be submitted based on the configured interval.
    """

    def __init__(self, usage_stats_service: UsageStatisticsService):
        """
        Initialize scheduler.

        Args:
            usage_stats_service: UsageStatisticsService instance for submissions
        """
        self.usage_stats_service = usage_stats_service
        self.settings = get_settings()
        self._task: Optional[asyncio.Task] = None
        self._running = False

        # Check interval (run every hour to check if submission is needed)
        self.check_interval_seconds = 3600  # 1 hour

    async def start(self) -> None:
        """
        Start the scheduler background task.

        The task will check hourly if a submission is due based on
        the configured submission interval.
        """
        if self._running:
            logger.warning("Usage statistics scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())

        logger.info("Usage statistics scheduler started",
                   check_interval_hours=self.check_interval_seconds / 3600,
                   submission_interval_days=self.settings.usage_stats_submission_interval_days)

    async def stop(self) -> None:
        """
        Stop the scheduler background task.

        Waits for any in-progress submission to complete before stopping.
        """
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Usage statistics scheduler stopped")

    async def _run(self) -> None:
        """
        Main scheduler loop.

        Runs continuously, checking periodically if a submission is due.
        """
        # Wait 5 minutes after startup before first check
        # (gives time for printers to connect and jobs to load)
        await asyncio.sleep(300)

        while self._running:
            try:
                await self._check_and_submit()
            except Exception as e:
                # Never let scheduler errors break the application
                logger.error("Error in usage statistics scheduler",
                           error=str(e),
                           error_type=type(e).__name__)

            # Wait for next check
            if self._running:
                await asyncio.sleep(self.check_interval_seconds)

    async def _check_and_submit(self) -> None:
        """
        Check if submission is due and submit if needed.

        Checks:
        1. User opted in
        2. Last submission date > configured interval
        3. Submits if both conditions met
        """
        try:
            # Check if user opted in
            if not await self.usage_stats_service.is_opted_in():
                logger.debug("Skipping scheduled submission - user opted out")
                return

            # Get last submission date
            last_submission_str = await self.usage_stats_service.repository.get_setting(
                "last_submission_date"
            )

            if last_submission_str:
                try:
                    last_submission = datetime.fromisoformat(last_submission_str)
                    days_since_last = (datetime.utcnow() - last_submission).days

                    if days_since_last < self.settings.usage_stats_submission_interval_days:
                        logger.debug("Skipping scheduled submission - too soon",
                                   days_since_last=days_since_last,
                                   interval_days=self.settings.usage_stats_submission_interval_days)
                        return

                    logger.info("Scheduled submission due",
                               days_since_last=days_since_last,
                               interval_days=self.settings.usage_stats_submission_interval_days)

                except (ValueError, TypeError) as e:
                    # Invalid last submission date - submit anyway
                    logger.warning("Invalid last_submission_date - will submit",
                                 value=last_submission_str,
                                 error=str(e))
            else:
                # No previous submission - this is the first one
                logger.info("First scheduled submission (no previous submission found)")

            # Submit statistics
            logger.info("Starting scheduled usage statistics submission")
            success = await self.usage_stats_service.submit_stats()

            if success:
                logger.info("Scheduled usage statistics submission completed successfully")
            else:
                logger.warning("Scheduled usage statistics submission failed",
                             note="Will retry in next scheduled check")

        except Exception as e:
            # Log error but don't propagate (never break application)
            logger.error("Error checking scheduled submission",
                       error=str(e),
                       error_type=type(e).__name__)

    async def trigger_immediate_submission(self) -> bool:
        """
        Trigger an immediate submission (manual trigger).

        Useful for testing or allowing users to manually trigger submission
        from the UI.

        Returns:
            True if submission successful, False otherwise
        """
        try:
            logger.info("Manual usage statistics submission triggered")

            if not await self.usage_stats_service.is_opted_in():
                logger.warning("Manual submission skipped - user opted out")
                return False

            success = await self.usage_stats_service.submit_stats()

            if success:
                logger.info("Manual usage statistics submission completed successfully")
            else:
                logger.warning("Manual usage statistics submission failed")

            return success

        except Exception as e:
            logger.error("Error in manual submission trigger",
                       error=str(e),
                       error_type=type(e).__name__)
            return False
