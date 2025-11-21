"""
Usage statistics service for privacy-first telemetry collection.

This service manages the collection, aggregation, and optional submission
of anonymous usage statistics. It ensures user privacy while providing
valuable insights for improving Printernizer.

Key Privacy Principles:
    - Opt-in only (disabled by default)
    - No personally identifiable information (PII)
    - Local-first storage
    - Full transparency (users can view all collected data)
    - Easy data deletion

Core Responsibilities:
    - Record usage events (app start, job completed, etc.)
    - Manage opt-in/opt-out preferences
    - Aggregate statistics for submission
    - Submit to aggregation service (if opted in)
    - Provide local statistics for UI display
    - Handle data export and deletion

Usage Example:
    ```python
    # Initialize service
    stats_service = UsageStatisticsService(db)
    await stats_service.initialize()

    # Record an event
    await stats_service.record_event("job_completed", {
        "printer_type": "bambu_lab",
        "duration_minutes": 60
    })

    # Check opt-in status
    if await stats_service.is_opted_in():
        # User has enabled statistics
        pass

    # Get local statistics for UI
    stats = await stats_service.get_local_stats()
    ```

See Also:
    - src/database/repositories/usage_statistics_repository.py - Data access
    - src/models/usage_statistics.py - Data models
    - docs/development/usage-statistics-plan.md - Feature overview
    - docs/development/usage-statistics-privacy.md - Privacy policy
"""
import uuid
import json
import platform
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import structlog
import aiohttp

from src.database.database import Database
from src.database.repositories.usage_statistics_repository import UsageStatisticsRepository
from src.models.usage_statistics import (
    UsageEvent,
    EventType,
    AggregatedStats,
    InstallationInfo,
    TimePeriod,
    PrinterFleetStats,
    UsageStats,
    LocalStatsResponse,
    OptInResponse
)
from src.services.base_service import BaseService
from src.utils.config import get_settings

logger = structlog.get_logger()


class UsageStatisticsService(BaseService):
    """
    Service for managing usage statistics collection and submission.

    Handles the full lifecycle of usage statistics:
    - Event recording with automatic sanitization
    - Opt-in/opt-out management
    - Weekly aggregation and submission
    - Local statistics viewing
    - Data export and deletion

    The service is designed to never interfere with normal application
    operation. All operations fail silently with error logging only.
    """

    def __init__(
        self,
        database: Database,
        repository: Optional[UsageStatisticsRepository] = None
    ):
        """
        Initialize usage statistics service.

        Args:
            database: Database instance for storage
            repository: Optional repository override for testing
        """
        super().__init__(database)
        self.repository = repository or UsageStatisticsRepository(database._connection)
        self.settings = get_settings()

        # Track initialization timestamp for uptime calculation
        self._init_timestamp: Optional[datetime] = None

        # PrinterService reference for fleet stats (injected after initialization)
        self._printer_service = None

    async def initialize(self) -> None:
        """
        Initialize service.

        Records the initialization timestamp for uptime tracking.
        """
        await super().initialize()
        self._init_timestamp = datetime.utcnow()

        logger.debug("Usage statistics service initialized")

    def set_printer_service(self, printer_service) -> None:
        """
        Set PrinterService reference for accessing fleet statistics.

        This is called after initialization to avoid circular dependencies,
        as UsageStatisticsService is created before PrinterService.

        Args:
            printer_service: PrinterService instance for accessing printer data
        """
        self._printer_service = printer_service
        logger.debug("PrinterService reference injected into UsageStatisticsService")

    async def is_opted_in(self) -> bool:
        """
        Check if user has opted in to usage statistics.

        Returns:
            True if user has enabled statistics, False otherwise

        Example:
            ```python
            if await stats_service.is_opted_in():
                await stats_service.submit_stats()
            ```
        """
        try:
            opt_in_status = await self.repository.get_setting("opt_in_status")
            return opt_in_status == "enabled"

        except Exception as e:
            logger.error("Failed to check opt-in status", error=str(e))
            return False

    async def opt_in(self) -> OptInResponse:
        """
        Enable usage statistics collection and submission.

        Generates an anonymous installation ID if one doesn't exist.
        Records first run date for installation age tracking.

        Returns:
            OptInResponse with success status and installation ID

        Example:
            ```python
            response = await stats_service.opt_in()
            if response.success:
                print(f"Installation ID: {response.installation_id}")
            ```
        """
        try:
            # Enable opt-in
            await self.repository.set_setting("opt_in_status", "enabled")

            # Generate installation ID if not exists
            installation_id = await self.repository.get_setting("installation_id")
            if not installation_id:
                installation_id = str(uuid.uuid4())
                await self.repository.set_setting("installation_id", installation_id)
                await self.repository.set_setting(
                    "first_run_date",
                    datetime.utcnow().isoformat()
                )

            logger.info("User opted in to usage statistics", installation_id=installation_id)

            return OptInResponse(
                success=True,
                installation_id=installation_id,
                message="Usage statistics enabled. Thank you for helping improve Printernizer!"
            )

        except Exception as e:
            logger.error("Failed to opt in", error=str(e))
            return OptInResponse(
                success=False,
                message=f"Failed to enable usage statistics: {str(e)}"
            )

    async def opt_out(self) -> OptInResponse:
        """
        Disable usage statistics submission.

        Local data is preserved but no longer submitted to the aggregation service.
        User can delete local data separately using delete_all_stats().

        Returns:
            OptInResponse with success status

        Example:
            ```python
            response = await stats_service.opt_out()
            if response.success:
                print("Statistics disabled")
            ```
        """
        try:
            await self.repository.set_setting("opt_in_status", "disabled")

            logger.info("User opted out of usage statistics")

            return OptInResponse(
                success=True,
                message="Usage statistics disabled. Your data will remain local."
            )

        except Exception as e:
            logger.error("Failed to opt out", error=str(e))
            return OptInResponse(
                success=False,
                message=f"Failed to disable usage statistics: {str(e)}"
            )

    async def record_event(
        self,
        event_type: str | EventType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UsageEvent]:
        """
        Record a usage event.

        Events are stored locally regardless of opt-in status,
        allowing users to review data before opting in.

        IMPORTANT: Metadata should never contain PII. This service
        trusts the caller to sanitize data. See privacy policy for rules.

        Args:
            event_type: Type of event (from EventType enum or string)
            metadata: Optional event-specific data (must be JSON-serializable, no PII!)

        Returns:
            UsageEvent if successful, None if failed

        Example:
            ```python
            # Good (privacy-safe)
            await stats_service.record_event("job_completed", {
                "printer_type": "bambu_lab",
                "duration_minutes": 60
            })

            # Bad (contains PII - DON'T DO THIS!)
            await stats_service.record_event("job_completed", {
                "file_name": "secret_project.3mf"  # ❌ NO!
            })
            ```

        Privacy Notes:
            - No file names or paths
            - No user names or emails
            - No IP addresses or network info
            - No printer serial numbers
            - Use aggregated data only (counts, averages, etc.)
        """
        try:
            # Convert string to EventType enum if needed
            if isinstance(event_type, str):
                try:
                    event_type = EventType(event_type)
                except ValueError:
                    logger.warning("Unknown event type", event_type=event_type)
                    return None

            # Create event
            event = UsageEvent(
                event_type=event_type,
                metadata=metadata or {}
            )

            # Store event
            success = await self.repository.insert_event(event)

            if success:
                logger.debug("Usage event recorded", event_type=event_type.value)
                return event
            else:
                return None

        except Exception as e:
            # Never let statistics break the application
            logger.error("Failed to record usage event",
                        event_type=str(event_type),
                        error=str(e))
            return None

    async def aggregate_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[AggregatedStats]:
        """
        Aggregate usage statistics for a time period.

        Combines event data with printer fleet information and system details
        into a privacy-safe aggregated payload.

        Args:
            start_date: Period start (defaults to 7 days ago)
            end_date: Period end (defaults to now)

        Returns:
            AggregatedStats model ready for submission, or None if failed

        Example:
            ```python
            # Aggregate last week's stats
            stats = await stats_service.aggregate_stats()
            if stats:
                print(f"Jobs completed: {stats.usage_stats.job_count}")
            ```

        Privacy Note:
            The aggregated payload contains no PII. See the AggregatedStats
            model and privacy policy for details on what is included.
        """
        try:
            # Default to last 7 days
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            # Get installation info
            installation_id = await self.repository.get_setting("installation_id")
            if not installation_id:
                installation_id = str(uuid.uuid4())
                await self.repository.set_setting("installation_id", installation_id)

            first_seen_str = await self.repository.get_setting("first_run_date")
            first_seen = datetime.fromisoformat(first_seen_str) if first_seen_str else datetime.utcnow()

            # Get deployment mode from environment
            deployment_mode = self._get_deployment_mode()

            # Get country code from timezone
            country_code = self._get_country_code_from_timezone()

            # Build installation info
            installation = InstallationInfo(
                installation_id=installation_id,
                first_seen=first_seen,
                app_version=self._get_app_version(),
                python_version=platform.python_version(),
                platform=platform.system().lower(),
                deployment_mode=deployment_mode,
                country_code=country_code
            )

            # Build time period
            period = TimePeriod(
                start=start_date,
                end=end_date,
                duration_days=(end_date - start_date).days
            )

            # Get event counts by type
            event_counts = await self.repository.get_event_counts_by_type(
                start_date=start_date,
                end_date=end_date
            )

            # Get printer fleet stats (from PrinterService)
            printer_fleet = await self._get_printer_fleet_stats()

            # Build usage stats
            usage_stats = UsageStats(
                job_count=event_counts.get("job_completed", 0) + event_counts.get("job_failed", 0),
                file_count=event_counts.get("file_downloaded", 0),
                upload_count=event_counts.get("file_uploaded", 0),
                uptime_hours=self._calculate_uptime_hours(start_date, end_date),
                feature_usage=self._get_feature_usage()
            )

            # Build error summary (counts only, no details)
            error_summary = {
                "total_errors": event_counts.get("error_occurred", 0)
            }

            # Build complete aggregated stats
            aggregated = AggregatedStats(
                installation=installation,
                period=period,
                printer_fleet=printer_fleet,
                usage_stats=usage_stats,
                error_summary=error_summary
            )

            logger.debug("Statistics aggregated",
                        period_days=period.duration_days,
                        job_count=usage_stats.job_count)

            return aggregated

        except Exception as e:
            logger.error("Failed to aggregate statistics", error=str(e))
            return None

    async def submit_stats(self) -> bool:
        """
        Submit aggregated statistics to remote endpoint (Phase 2).

        Includes retry logic with exponential backoff for handling network failures.
        Only submits if user has opted in. Marks submitted events to prevent
        duplicate submissions.

        Returns:
            True if submission successful or not needed, False if all retries failed

        Example:
            ```python
            if await stats_service.is_opted_in():
                success = await stats_service.submit_stats()
            ```
        """
        # Check opt-in status
        if not await self.is_opted_in():
            logger.debug("Skipping stats submission - user opted out")
            return True

        try:
            # Aggregate stats
            stats = await self.aggregate_stats()
            if not stats:
                logger.warning("Failed to aggregate stats for submission")
                return False

            # Prepare payload
            payload = stats.model_dump()
            payload_json = json.dumps(payload, default=str)
            logger.info("Submitting usage statistics",
                       endpoint=self.settings.usage_stats_endpoint,
                       payload_size_bytes=len(payload_json),
                       job_count=stats.usage_stats.job_count)

            # Submit with retry logic
            max_retries = self.settings.usage_stats_retry_count
            timeout_seconds = self.settings.usage_stats_timeout

            for attempt in range(max_retries + 1):
                try:
                    # Calculate exponential backoff (2^attempt seconds)
                    if attempt > 0:
                        backoff_seconds = 2 ** attempt
                        logger.debug(f"Retry attempt {attempt}/{max_retries} after {backoff_seconds}s backoff")
                        await asyncio.sleep(backoff_seconds)

                    # Submit to aggregation service
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            self.settings.usage_stats_endpoint,
                            json=payload,
                            headers={
                                "Content-Type": "application/json",
                                "X-API-Key": self.settings.usage_stats_api_key
                            },
                            timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                        ) as response:
                            response_text = await response.text()

                            if response.status == 200:
                                # Success! Mark events as submitted
                                await self.repository.mark_events_submitted(
                                    stats.period.start,
                                    stats.period.end
                                )
                                # Update last submission date
                                await self.repository.set_setting(
                                    "last_submission_date",
                                    datetime.utcnow().isoformat()
                                )

                                logger.info("Usage statistics submitted successfully",
                                           submission_id=response_text,
                                           attempt=attempt + 1)
                                return True

                            elif response.status == 401:
                                # Authentication failed - don't retry
                                logger.error("Statistics submission failed: Invalid API key",
                                           status=response.status)
                                return False

                            elif response.status == 429:
                                # Rate limited - exponential backoff and retry
                                logger.warning("Statistics submission rate limited",
                                             status=response.status,
                                             attempt=attempt + 1)
                                # Continue to retry with backoff

                            else:
                                # Other error - log and retry
                                logger.warning("Statistics submission failed",
                                             status=response.status,
                                             response=response_text[:200],
                                             attempt=attempt + 1)

                except aiohttp.ClientError as e:
                    # Network error - retry with backoff
                    logger.warning("Statistics submission network error",
                                 error=str(e),
                                 attempt=attempt + 1)

                except asyncio.TimeoutError:
                    # Timeout - retry with backoff
                    logger.warning("Statistics submission timeout",
                                 timeout_seconds=timeout_seconds,
                                 attempt=attempt + 1)

                except Exception as e:
                    # Unexpected error - log and retry
                    logger.error("Statistics submission unexpected error",
                               error=str(e),
                               error_type=type(e).__name__,
                               attempt=attempt + 1)

            # All retries exhausted
            logger.error("Statistics submission failed after all retries",
                        max_retries=max_retries)
            return False

        except Exception as e:
            # Never let statistics break the application
            logger.error("Error submitting usage statistics", error=str(e))
            return False

    async def get_local_stats(self) -> LocalStatsResponse:
        """
        Get local statistics for UI display.

        Provides a human-readable summary of collected statistics
        for the local statistics viewer.

        Returns:
            LocalStatsResponse with summary data

        Example:
            ```python
            stats = await stats_service.get_local_stats()
            print(f"Total events: {stats.total_events}")
            print(f"This week's jobs: {stats.this_week['job_count']}")
            ```
        """
        try:
            # Get installation ID
            installation_id = await self.repository.get_setting("installation_id")
            if not installation_id:
                installation_id = "not_generated"

            # Get first event timestamp
            first_seen = await self.repository.get_first_event_timestamp()

            # Get opt-in status
            opt_in_status = "enabled" if await self.is_opted_in() else "disabled"

            # Get total event count
            total_events = await self.repository.get_total_event_count()

            # Get this week's event counts
            week_start = datetime.utcnow() - timedelta(days=7)
            week_counts = await self.repository.get_event_counts_by_type(start_date=week_start)

            this_week = {
                "job_count": week_counts.get("job_completed", 0) + week_counts.get("job_failed", 0),
                "file_count": week_counts.get("file_downloaded", 0),
                "error_count": week_counts.get("error_occurred", 0)
            }

            # Get last submission date
            last_submission_str = await self.repository.get_setting("last_submission_date")
            last_submission = datetime.fromisoformat(last_submission_str) if last_submission_str else None

            return LocalStatsResponse(
                installation_id=installation_id,
                first_seen=first_seen,
                opt_in_status=opt_in_status,
                total_events=total_events,
                this_week=this_week,
                last_submission=last_submission
            )

        except Exception as e:
            logger.error("Failed to get local stats", error=str(e))
            # Return empty response on error
            return LocalStatsResponse(
                installation_id="error",
                opt_in_status="unknown",
                total_events=0,
                this_week={}
            )

    async def export_stats(self) -> str:
        """
        Export all local statistics as JSON.

        Provides full data transparency by exporting everything
        we've collected locally.

        Returns:
            JSON string with all events and settings

        Example:
            ```python
            json_data = await stats_service.export_stats()
            # Save to file or return to user
            ```
        """
        try:
            # Get all events
            events = await self.repository.get_events()

            # Get all settings
            settings = await self.repository.get_all_settings()

            # Build export data
            export_data = {
                "events": events,
                "settings": settings,
                "exported_at": datetime.utcnow().isoformat(),
                "export_version": "1.0"
            }

            return json.dumps(export_data, indent=2, default=str)

        except Exception as e:
            logger.error("Failed to export stats", error=str(e))
            return json.dumps({"error": str(e)})

    async def delete_all_stats(self) -> bool:
        """
        Delete all local usage statistics.

        This is called when user requests data deletion.
        Preserves settings (opt-in status, installation ID) but
        removes all event data.

        Returns:
            True if deletion succeeded, False otherwise

        Example:
            ```python
            if await stats_service.delete_all_stats():
                print("All local statistics have been deleted")
            ```

        Privacy Note:
            This only deletes local data. If data was previously submitted,
            the user should contact us to delete remote data.
        """
        try:
            success = await self.repository.delete_all_events()

            if success:
                logger.info("All usage statistics deleted")

            return success

        except Exception as e:
            logger.error("Failed to delete stats", error=str(e))
            return False

    # ------------------------------------------------------------------
    # Private helper methods
    # ------------------------------------------------------------------

    def _get_deployment_mode(self) -> str:
        """
        Determine deployment mode from environment.

        Returns:
            "homeassistant", "docker", "standalone", or "pi"
        """
        if self.settings.is_homeassistant_addon:
            return "homeassistant"

        # Check for Docker environment
        import os
        if os.path.exists("/.dockerenv"):
            return "docker"

        # Check for Pi deployment (look for systemd service)
        if os.path.exists("/etc/systemd/system/printernizer.service"):
            return "pi"

        return "standalone"

    def _get_country_code_from_timezone(self) -> str:
        """
        Get country code from configured timezone.

        Uses the timezone setting, not IP geolocation.
        Returns "Unknown" if timezone doesn't map to a country.

        Returns:
            Two-letter country code
        """
        # Simple mapping of common timezones to countries
        # This is privacy-safe as it uses user-configured timezone
        timezone_mapping = {
            "Europe/Berlin": "DE",
            "Europe/London": "GB",
            "America/New_York": "US",
            "America/Los_Angeles": "US",
            "America/Chicago": "US",
            "America/Denver": "US",
            "Asia/Tokyo": "JP",
            "Australia/Sydney": "AU",
            "Europe/Paris": "FR",
            "Europe/Madrid": "ES",
            "Europe/Rome": "IT"
        }

        return timezone_mapping.get(self.settings.timezone, "XX")

    def _get_app_version(self) -> str:
        """
        Get application version.

        Returns version from git tags via get_version() utility,
        which provides runtime version detection for all deployment modes.
        """
        from src.utils.version import get_version
        return get_version(fallback="2.7.0")

    async def _get_printer_fleet_stats(self) -> PrinterFleetStats:
        """
        Get anonymous printer fleet statistics.

        Collects aggregated printer counts and types WITHOUT any PII:
        - NO serial numbers
        - NO IP addresses
        - NO printer names
        - ONLY counts and types (e.g., {"bambu_lab": 2, "prusa_core": 1})

        Returns:
            PrinterFleetStats with counts and types (privacy-safe)
        """
        try:
            # Check if PrinterService is available
            if not self._printer_service:
                logger.debug(
                    "PrinterService not available for fleet stats, returning empty"
                )
                return PrinterFleetStats(
                    printer_count=0,
                    printer_types=[],
                    printer_type_counts={}
                )

            # Get all printers from PrinterService
            printers = await self._printer_service.list_printers()

            # Count printers by type (privacy-safe aggregation)
            type_counts = {}
            for printer in printers:
                # Extract printer type (e.g., "bambu_lab", "prusa_core")
                printer_type = printer.type.value if hasattr(printer.type, 'value') else str(printer.type)
                type_counts[printer_type] = type_counts.get(printer_type, 0) + 1

            return PrinterFleetStats(
                printer_count=len(printers),
                printer_types=list(type_counts.keys()),
                printer_type_counts=type_counts
            )

        except Exception as e:
            logger.error("Failed to get printer fleet stats", error=str(e))
            # Always return empty stats on error (never fail)
            return PrinterFleetStats(
                printer_count=0,
                printer_types=[],
                printer_type_counts={}
            )

    def _calculate_uptime_hours(self, start_date: datetime, end_date: datetime) -> int:
        """
        Calculate uptime hours for the period.

        This is an estimate based on app_start and app_shutdown events.

        Args:
            start_date: Period start
            end_date: Period end

        Returns:
            Estimated uptime in hours
        """
        # Simple estimate: if service is running, count full period
        if self._init_timestamp and self._init_timestamp >= start_date:
            uptime = datetime.utcnow() - self._init_timestamp
            return int(uptime.total_seconds() / 3600)

        # Otherwise estimate from period duration
        period_hours = (end_date - start_date).total_seconds() / 3600
        return int(period_hours * 0.8)  # Assume 80% uptime

    def _get_feature_usage(self) -> Dict[str, bool]:
        """
        Get feature enable/disable status.

        Returns:
            Dictionary mapping feature names to enabled status
        """
        return {
            "library_enabled": self.settings.library_enabled,
            "timelapse_enabled": self.settings.timelapse_enabled,
            "auto_job_creation_enabled": self.settings.job_creation_auto_create,
            "german_compliance_enabled": self.settings.enable_german_compliance,
            "watch_folders_enabled": self.settings.watch_folders_enabled
        }
