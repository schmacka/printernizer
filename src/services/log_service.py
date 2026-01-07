"""
Unified log service for reading and normalizing logs from multiple sources.
"""

import json
import structlog
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.models.logs import (
    LogLevel,
    LogSource,
    NormalizedLogEntry,
    LogQueryFilters,
    LogQueryResult,
    LogPagination,
    LogStatistics,
    LogSourceInfo,
    LogSourcesResponse,
)

logger = structlog.get_logger()


class UnifiedLogService:
    """Service for reading and normalizing logs from multiple sources."""

    # Map backend severity to log level
    SEVERITY_TO_LEVEL = {
        "low": LogLevel.INFO,
        "medium": LogLevel.WARN,
        "high": LogLevel.ERROR,
        "critical": LogLevel.CRITICAL,
    }

    # Log level priority for filtering (higher = more severe)
    LEVEL_PRIORITY = {
        LogLevel.DEBUG: 0,
        LogLevel.INFO: 1,
        LogLevel.WARN: 2,
        LogLevel.ERROR: 3,
        LogLevel.CRITICAL: 4,
    }

    def __init__(self):
        """Initialize the unified log service."""
        self.backend_error_path = Path("data/logs/backend_errors.jsonl")
        self._log_cache: Dict[str, List[NormalizedLogEntry]] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(seconds=30)  # Cache for 30 seconds

    def _is_cache_valid(self) -> bool:
        """Check if the log cache is still valid."""
        if self._cache_timestamp is None:
            return False
        return datetime.now() - self._cache_timestamp < self._cache_ttl

    def _invalidate_cache(self):
        """Invalidate the log cache."""
        self._log_cache = {}
        self._cache_timestamp = None

    def _read_backend_errors(self) -> List[NormalizedLogEntry]:
        """Read and normalize backend error logs from JSONL file."""
        entries = []

        if not self.backend_error_path.exists():
            logger.debug("Backend error log file does not exist", path=str(self.backend_error_path))
            return entries

        try:
            with open(self.backend_error_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = self._normalize_backend_error(data)
                        if entry:
                            entries.append(entry)
                    except json.JSONDecodeError as e:
                        logger.warning(
                            "Failed to parse backend error log line",
                            line_num=line_num,
                            error=str(e)
                        )
        except IOError as e:
            logger.error("Failed to read backend error log", error=str(e))

        return entries

    def _normalize_backend_error(self, data: Dict[str, Any]) -> Optional[NormalizedLogEntry]:
        """Normalize a backend error log entry to the unified format."""
        try:
            # Parse timestamp
            timestamp_str = data.get("timestamp", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                timestamp = datetime.now()

            # Map severity to level
            severity = data.get("severity", "medium")
            level = self.SEVERITY_TO_LEVEL.get(severity, LogLevel.WARN)

            # Build details from traceback and context
            details = {}
            if data.get("traceback"):
                details["traceback"] = data["traceback"]
            if data.get("type"):
                details["exception_type"] = data["type"]
            if data.get("user_message"):
                details["user_message"] = data["user_message"]

            return NormalizedLogEntry(
                id=data.get("id", f"err_{int(timestamp.timestamp())}"),
                source=LogSource.ERRORS,
                timestamp=timestamp,
                level=level,
                category=data.get("category", "UNKNOWN").upper(),
                message=data.get("message", "Unknown error"),
                details=details if details else None,
                context=data.get("context"),
            )
        except Exception as e:
            logger.warning("Failed to normalize backend error", error=str(e))
            return None

    def _get_all_logs(self) -> List[NormalizedLogEntry]:
        """Get all logs from all sources, using cache if valid."""
        if self._is_cache_valid() and "all" in self._log_cache:
            return self._log_cache["all"]

        all_logs = []

        # Read backend errors
        backend_errors = self._read_backend_errors()
        all_logs.extend(backend_errors)

        # Sort by timestamp descending
        all_logs.sort(key=lambda x: x.timestamp, reverse=True)

        # Update cache
        self._log_cache["all"] = all_logs
        self._cache_timestamp = datetime.now()

        return all_logs

    def _apply_filters(
        self, logs: List[NormalizedLogEntry], filters: LogQueryFilters
    ) -> List[NormalizedLogEntry]:
        """Apply filters to a list of log entries."""
        filtered = logs

        # Filter by source
        if filters.source:
            filtered = [log for log in filtered if log.source == filters.source]

        # Filter by minimum level
        if filters.level:
            min_priority = self.LEVEL_PRIORITY.get(filters.level, 0)
            filtered = [
                log for log in filtered
                if self.LEVEL_PRIORITY.get(log.level, 0) >= min_priority
            ]

        # Filter by category
        if filters.category:
            category_lower = filters.category.lower()
            filtered = [
                log for log in filtered
                if log.category.lower() == category_lower
            ]

        # Filter by search text
        if filters.search:
            search_lower = filters.search.lower()
            filtered = [
                log for log in filtered
                if search_lower in log.message.lower()
                or search_lower in log.category.lower()
            ]

        # Filter by date range
        if filters.start_date:
            filtered = [log for log in filtered if log.timestamp >= filters.start_date]
        if filters.end_date:
            filtered = [log for log in filtered if log.timestamp <= filters.end_date]

        # Sort
        reverse = filters.sort_order == "desc"
        filtered.sort(key=lambda x: x.timestamp, reverse=reverse)

        return filtered

    def _paginate(
        self, logs: List[NormalizedLogEntry], page: int, per_page: int
    ) -> tuple[List[NormalizedLogEntry], LogPagination]:
        """Paginate a list of log entries."""
        total = len(logs)
        total_pages = max(1, (total + per_page - 1) // per_page)

        # Ensure page is within bounds
        page = max(1, min(page, total_pages))

        start = (page - 1) * per_page
        end = start + per_page

        paginated = logs[start:end]

        pagination = LogPagination(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        )

        return paginated, pagination

    def _calculate_statistics(self, logs: List[NormalizedLogEntry]) -> LogStatistics:
        """Calculate statistics for a list of log entries."""
        now = datetime.now()
        day_ago = now - timedelta(hours=24)

        by_level: Dict[str, int] = {}
        by_source: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        last_24h = 0

        for log in logs:
            # Count by level
            level_key = log.level.value
            by_level[level_key] = by_level.get(level_key, 0) + 1

            # Count by source
            source_key = log.source.value
            by_source[source_key] = by_source.get(source_key, 0) + 1

            # Count by category
            cat_key = log.category
            by_category[cat_key] = by_category.get(cat_key, 0) + 1

            # Count last 24h
            if log.timestamp >= day_ago:
                last_24h += 1

        return LogStatistics(
            total=len(logs),
            last_24h=last_24h,
            by_level=by_level,
            by_source=by_source,
            by_category=by_category,
        )

    async def query_logs(self, filters: LogQueryFilters) -> LogQueryResult:
        """
        Query logs with filtering and pagination.

        Args:
            filters: Query filters

        Returns:
            Paginated log query result
        """
        # Get all logs
        all_logs = self._get_all_logs()

        # Apply filters
        filtered_logs = self._apply_filters(all_logs, filters)

        # Paginate
        paginated, pagination = self._paginate(
            filtered_logs, filters.page, filters.per_page
        )

        # Calculate statistics for filtered set
        statistics = self._calculate_statistics(filtered_logs)

        return LogQueryResult(
            data=paginated,
            pagination=pagination,
            statistics=statistics,
        )

    async def get_sources(self) -> LogSourcesResponse:
        """Get information about available log sources."""
        all_logs = self._get_all_logs()

        # Count by source
        source_counts: Dict[LogSource, int] = {}
        for log in all_logs:
            source_counts[log.source] = source_counts.get(log.source, 0) + 1

        sources = [
            LogSourceInfo(
                source=LogSource.FRONTEND,
                name="Frontend",
                count=source_counts.get(LogSource.FRONTEND, 0),
                available=True,  # Frontend logs are client-side
            ),
            LogSourceInfo(
                source=LogSource.BACKEND,
                name="Backend",
                count=source_counts.get(LogSource.BACKEND, 0),
                available=True,
            ),
            LogSourceInfo(
                source=LogSource.ERRORS,
                name="Fehler",
                count=source_counts.get(LogSource.ERRORS, 0),
                available=self.backend_error_path.exists(),
            ),
        ]

        return LogSourcesResponse(sources=sources)

    async def get_statistics(self, hours: int = 24) -> LogStatistics:
        """
        Get aggregated statistics across all log sources.

        Args:
            hours: Time range in hours (default 24)

        Returns:
            Aggregated log statistics
        """
        all_logs = self._get_all_logs()
        return self._calculate_statistics(all_logs)

    async def get_categories(self) -> List[str]:
        """Get list of all unique categories."""
        all_logs = self._get_all_logs()
        categories = set(log.category for log in all_logs)
        return sorted(categories)

    async def clear_logs(self, source: Optional[LogSource] = None) -> int:
        """
        Clear logs from specified source or all sources.

        Args:
            source: Optional source to clear (None = all)

        Returns:
            Number of logs cleared
        """
        count = 0

        # Only clear backend errors if source is ERRORS or None
        if source in (None, LogSource.ERRORS):
            if self.backend_error_path.exists():
                try:
                    # Count lines before clearing
                    with open(self.backend_error_path, "r") as f:
                        count = sum(1 for line in f if line.strip())

                    # Clear the file
                    self.backend_error_path.write_text("")
                    logger.info("Cleared backend error logs", count=count)
                except IOError as e:
                    logger.error("Failed to clear backend error logs", error=str(e))

        # Invalidate cache
        self._invalidate_cache()

        return count

    def export_to_csv(self, logs: List[NormalizedLogEntry]) -> str:
        """
        Export logs to CSV format.

        Args:
            logs: List of log entries to export

        Returns:
            CSV string
        """
        rows = ["Timestamp,Source,Level,Category,Message"]

        for log in logs:
            # Escape quotes in message
            message = log.message.replace('"', '""')
            row = f'"{log.timestamp.isoformat()}","{log.source.value}","{log.level.value}","{log.category}","{message}"'
            rows.append(row)

        return "\n".join(rows)

    def export_to_json(self, logs: List[NormalizedLogEntry]) -> str:
        """
        Export logs to JSON format.

        Args:
            logs: List of log entries to export

        Returns:
            JSON string
        """
        data = [log.model_dump(mode="json") for log in logs]
        return json.dumps(data, indent=2, default=str)


# Singleton instance
_log_service: Optional[UnifiedLogService] = None


def get_log_service() -> UnifiedLogService:
    """Get or create the unified log service singleton."""
    global _log_service
    if _log_service is None:
        _log_service = UnifiedLogService()
    return _log_service
