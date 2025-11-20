"""
Usage statistics repository for managing usage tracking data.

This module provides data access methods for usage statistics collection,
including event recording, settings management, and data aggregation queries.

Database Schema:
    The usage_events table stores individual usage events:
    - id (TEXT PRIMARY KEY): Unique event identifier (UUID)
    - event_type (TEXT): Type of event (app_start, job_completed, etc.)
    - timestamp (DATETIME): When the event occurred (UTC)
    - metadata (TEXT): JSON string with event-specific data
    - submitted (BOOLEAN): Whether event was submitted to aggregation service
    - created_at (DATETIME): When the event was recorded locally

    The usage_settings table stores configuration:
    - key (TEXT PRIMARY KEY): Setting key
    - value (TEXT): Setting value
    - updated_at (DATETIME): Last update timestamp

    Indexes:
    - idx_usage_events_type: Fast filtering by event type
    - idx_usage_events_timestamp: Time-range queries
    - idx_usage_events_submitted: Find unsubmitted events

Usage Examples:
    ```python
    from src.database.repositories import UsageStatisticsRepository
    from src.models.usage_statistics import UsageEvent, EventType

    # Initialize
    usage_repo = UsageStatisticsRepository(db.connection)

    # Record an event
    event = UsageEvent(
        event_type=EventType.JOB_COMPLETED,
        metadata={"printer_type": "bambu_lab", "duration_seconds": 3600}
    )
    await usage_repo.insert_event(event)

    # Get events for a time period
    from datetime import datetime, timedelta
    start = datetime.utcnow() - timedelta(days=7)
    events = await usage_repo.get_events(start_date=start)

    # Check opt-in status
    opt_in = await usage_repo.get_setting("opt_in_status")

    # Mark events as submitted
    await usage_repo.mark_events_submitted(start, datetime.utcnow())
    ```

Privacy Note:
    This repository handles anonymous usage statistics only. All data stored
    is privacy-first and contains no personally identifiable information (PII).
    See docs/development/usage-statistics-privacy.md for details.

See Also:
    - src/services/usage_statistics_service.py - Business logic
    - src/models/usage_statistics.py - Data models
    - docs/development/usage-statistics-technical-spec.md - Technical spec
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import structlog

from .base_repository import BaseRepository
from src.models.usage_statistics import UsageEvent

logger = structlog.get_logger()


class UsageStatisticsRepository(BaseRepository):
    """
    Repository for usage statistics database operations.

    Provides CRUD operations for usage events and settings management.
    Handles event recording, querying, and submission tracking.

    Key Features:
        - Event recording with automatic JSON metadata serialization
        - Time-range queries for event aggregation
        - Settings management (opt-in status, installation ID, etc.)
        - Event submission tracking
        - Bulk operations for efficiency
    """

    async def insert_event(self, event: UsageEvent) -> bool:
        """
        Insert a usage event into the database.

        Args:
            event: UsageEvent model with event details

        Returns:
            True if event was recorded successfully, False otherwise

        Example:
            ```python
            event = UsageEvent(
                event_type=EventType.APP_START,
                metadata={"app_version": "2.7.0", "platform": "linux"}
            )
            success = await repo.insert_event(event)
            ```

        Privacy Note:
            Metadata should never contain PII. The service layer is responsible
            for sanitizing data before calling this method.
        """
        try:
            # Serialize metadata to JSON
            metadata_json = json.dumps(event.metadata) if event.metadata else None

            await self._execute_write(
                """INSERT INTO usage_events (id, event_type, timestamp, metadata, submitted, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    event.id,
                    event.event_type.value,
                    event.timestamp.isoformat(),
                    metadata_json,
                    event.submitted,
                    event.created_at.isoformat()
                )
            )

            logger.debug("Usage event recorded", event_id=event.id, event_type=event.event_type.value)
            return True

        except Exception as e:
            # Never let statistics break the application
            logger.error("Failed to insert usage event",
                        event_type=event.event_type.value,
                        error=str(e))
            return False

    async def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None,
        submitted: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get usage events matching the given filters.

        Args:
            start_date: Filter events after this timestamp (inclusive)
            end_date: Filter events before this timestamp (inclusive)
            event_type: Filter by specific event type
            submitted: Filter by submission status (True/False/None for all)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries with parsed JSON metadata

        Example:
            ```python
            # Get last week's job completion events
            from datetime import datetime, timedelta
            start = datetime.utcnow() - timedelta(days=7)
            events = await repo.get_events(
                start_date=start,
                event_type="job_completed",
                submitted=False
            )
            ```
        """
        try:
            # Build query dynamically based on filters
            query = "SELECT * FROM usage_events WHERE 1=1"
            params: List[Any] = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            if submitted is not None:
                query += " AND submitted = ?"
                params.append(1 if submitted else 0)

            query += " ORDER BY timestamp DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            rows = await self._fetch_all(query, params)

            # Parse JSON metadata for each row
            for row in rows:
                if row.get('metadata'):
                    try:
                        row['metadata'] = json.loads(row['metadata'])
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse event metadata",
                                      event_id=row.get('id'))
                        row['metadata'] = {}

            return rows

        except Exception as e:
            logger.error("Failed to fetch usage events", error=str(e))
            return []

    async def get_event_counts_by_type(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Get event counts grouped by type for a time period.

        Args:
            start_date: Count events after this timestamp (inclusive)
            end_date: Count events before this timestamp (inclusive)

        Returns:
            Dictionary mapping event_type to count

        Example:
            ```python
            from datetime import datetime, timedelta
            start = datetime.utcnow() - timedelta(days=7)
            counts = await repo.get_event_counts_by_type(start_date=start)
            # Returns: {"job_completed": 23, "file_downloaded": 18, ...}
            ```
        """
        try:
            query = """
                SELECT event_type, COUNT(*) as count
                FROM usage_events
                WHERE 1=1
            """
            params: List[Any] = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())

            query += " GROUP BY event_type"

            rows = await self._fetch_all(query, params)

            # Convert to dictionary
            return {row['event_type']: row['count'] for row in rows}

        except Exception as e:
            logger.error("Failed to get event counts", error=str(e))
            return {}

    async def mark_events_submitted(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> bool:
        """
        Mark events as submitted for a time period.

        This is called after successfully submitting aggregated stats
        to prevent re-submission of the same data.

        Args:
            start_date: Start of submission period
            end_date: End of submission period

        Returns:
            True if update succeeded, False otherwise

        Example:
            ```python
            # After successful submission
            await repo.mark_events_submitted(period_start, period_end)
            ```
        """
        try:
            await self._execute_write(
                """UPDATE usage_events
                   SET submitted = 1
                   WHERE timestamp >= ? AND timestamp <= ? AND submitted = 0""",
                (start_date.isoformat(), end_date.isoformat())
            )

            logger.debug("Marked events as submitted",
                        start=start_date.isoformat(),
                        end=end_date.isoformat())
            return True

        except Exception as e:
            logger.error("Failed to mark events as submitted", error=str(e))
            return False

    async def get_setting(self, key: str) -> Optional[str]:
        """
        Get a usage statistics setting value.

        Args:
            key: Setting key (e.g., "opt_in_status", "installation_id")

        Returns:
            Setting value as string, or None if not found

        Example:
            ```python
            opt_in = await repo.get_setting("opt_in_status")
            if opt_in == "enabled":
                # User has opted in
                pass
            ```

        Common Settings:
            - opt_in_status: "enabled" or "disabled"
            - installation_id: UUID string
            - first_run_date: ISO 8601 timestamp
            - last_submission_date: ISO 8601 timestamp
            - submission_count: Number as string
        """
        try:
            row = await self._fetch_one(
                "SELECT value FROM usage_settings WHERE key = ?",
                [key]
            )
            return row['value'] if row else None

        except Exception as e:
            logger.error("Failed to get setting", key=key, error=str(e))
            return None

    async def set_setting(self, key: str, value: str) -> bool:
        """
        Set a usage statistics setting value.

        Uses INSERT OR REPLACE to create or update the setting atomically.

        Args:
            key: Setting key
            value: Setting value (will be converted to string)

        Returns:
            True if setting was saved, False otherwise

        Example:
            ```python
            # Enable usage statistics
            await repo.set_setting("opt_in_status", "enabled")

            # Store installation ID
            import uuid
            install_id = str(uuid.uuid4())
            await repo.set_setting("installation_id", install_id)
            ```
        """
        try:
            await self._execute_write(
                """INSERT OR REPLACE INTO usage_settings (key, value, updated_at)
                   VALUES (?, ?, ?)""",
                (key, str(value), datetime.utcnow().isoformat())
            )

            logger.debug("Setting updated", key=key)
            return True

        except Exception as e:
            logger.error("Failed to set setting", key=key, error=str(e))
            return False

    async def get_all_settings(self) -> Dict[str, str]:
        """
        Get all usage statistics settings.

        Returns:
            Dictionary mapping setting keys to values

        Example:
            ```python
            settings = await repo.get_all_settings()
            print(f"Installation ID: {settings.get('installation_id')}")
            print(f"Opt-in status: {settings.get('opt_in_status')}")
            ```
        """
        try:
            rows = await self._fetch_all("SELECT key, value FROM usage_settings")
            return {row['key']: row['value'] for row in rows}

        except Exception as e:
            logger.error("Failed to get all settings", error=str(e))
            return {}

    async def delete_all_events(self) -> bool:
        """
        Delete all usage events from the database.

        This is called when the user requests data deletion.
        Settings (opt-in status, installation ID) are preserved.

        Returns:
            True if deletion succeeded, False otherwise

        Example:
            ```python
            # User requests data deletion
            success = await repo.delete_all_events()
            if success:
                print("All local statistics have been deleted")
            ```

        Privacy Note:
            This method only deletes local data. If data was previously
            submitted, the user must contact us to delete remote data.
        """
        try:
            await self._execute_write("DELETE FROM usage_events")
            logger.info("All usage events deleted")
            return True

        except Exception as e:
            logger.error("Failed to delete events", error=str(e))
            return False

    async def get_total_event_count(self) -> int:
        """
        Get total number of events recorded locally.

        Returns:
            Total event count

        Example:
            ```python
            total = await repo.get_total_event_count()
            print(f"Total events recorded: {total}")
            ```
        """
        try:
            row = await self._fetch_one("SELECT COUNT(*) as count FROM usage_events")
            return row['count'] if row else 0

        except Exception as e:
            logger.error("Failed to get event count", error=str(e))
            return 0

    async def get_first_event_timestamp(self) -> Optional[datetime]:
        """
        Get timestamp of the first recorded event.

        Useful for displaying "First seen" date in the UI.

        Returns:
            Timestamp of first event, or None if no events

        Example:
            ```python
            first_seen = await repo.get_first_event_timestamp()
            if first_seen:
                print(f"Statistics collection started: {first_seen}")
            ```
        """
        try:
            row = await self._fetch_one(
                "SELECT MIN(timestamp) as first_timestamp FROM usage_events"
            )

            if row and row['first_timestamp']:
                return datetime.fromisoformat(row['first_timestamp'])

            return None

        except Exception as e:
            logger.error("Failed to get first event timestamp", error=str(e))
            return None

    async def cleanup_old_events(self, days: int = 90) -> int:
        """
        Delete events older than specified number of days.

        Optional cleanup to prevent database growth. Only needed if the
        user has statistics enabled for a very long time.

        Args:
            days: Delete events older than this many days (default: 90)

        Returns:
            Number of events deleted

        Example:
            ```python
            # Clean up events older than 90 days
            deleted = await repo.cleanup_old_events(days=90)
            logger.info(f"Cleaned up {deleted} old events")
            ```

        Note:
            This is optional and not part of the MVP. Consider adding as a
            background task if database size becomes an issue.
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            cursor = await self._execute_write(
                "DELETE FROM usage_events WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )

            # Get number of deleted rows (SQLite doesn't return this from cursor)
            row = await self._fetch_one("SELECT changes() as deleted_count")
            deleted_count = row['deleted_count'] if row else 0

            logger.info("Cleaned up old usage events",
                       days=days,
                       deleted_count=deleted_count)

            return deleted_count

        except Exception as e:
            logger.error("Failed to cleanup old events", error=str(e))
            return 0
