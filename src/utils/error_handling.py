"""
Comprehensive error handling and logging utilities for backend services.

Includes GDPR-compliant log retention with automatic cleanup of old entries.
"""

import structlog
import traceback
import functools
import asyncio
import os
import shutil
import tempfile
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import sys

logger = structlog.get_logger()

# Default retention period in days (GDPR recommends limiting data retention)
DEFAULT_LOG_RETENTION_DAYS = 90


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification."""
    DATABASE = "database"
    API = "api"
    PRINTER = "printer"
    FILE_OPERATION = "file_operation"
    NETWORK = "network"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ErrorHandler:
    """
    Centralized error handling and logging system.

    Features:
    - Structured error logging with categories and severity levels
    - GDPR-compliant log retention with automatic cleanup
    - Error statistics and reporting
    - Critical error alerting

    Log Retention Policy:
    - Default retention: 90 days (configurable via LOG_RETENTION_DAYS env var)
    - Automatic cleanup runs on initialization and can be triggered manually
    - Old entries are removed while preserving recent logs
    """

    def __init__(self, retention_days: Optional[int] = None):
        """
        Initialize the error handler.

        Args:
            retention_days: Number of days to retain logs. Defaults to
                           LOG_RETENTION_DAYS env var or 90 days.
        """
        self.error_log_path = Path("data/logs/backend_errors.jsonl")
        self.retention_days = retention_days or int(
            os.getenv("LOG_RETENTION_DAYS", DEFAULT_LOG_RETENTION_DAYS)
        )
        self.ensure_log_directory()
        # Run cleanup on initialization (non-blocking, logs any errors)
        self._safe_cleanup_old_logs()

    def ensure_log_directory(self):
        """Ensure the error log directory exists.

        Creates the directory structure for error logs if it doesn't exist.
        """
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        should_log_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        Handle an error with comprehensive logging and context.
        
        Args:
            error: The exception that occurred
            category: Category of the error
            severity: Severity level
            context: Additional context information
            user_message: User-friendly error message
            should_log_to_file: Whether to log to file
            
        Returns:
            Dict containing error information
        """
        error_info = {
            "id": self._generate_error_id(),
            "timestamp": datetime.now().isoformat(),
            "category": category.value,
            "severity": severity.value,
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "user_message": user_message or self._generate_user_message(category, error)
        }
        
        # Log to structured logger
        log_level = self._get_log_level(severity)
        getattr(logger, log_level)(
            f"{category.value.title()} error occurred",
            error_id=error_info["id"],
            error_type=error_info["type"],
            error_message=error_info["message"],
            severity=severity.value,
            context=context or {}
        )
        
        # Log to file for critical/high severity errors
        if should_log_to_file and severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            self._log_to_file(error_info)
        
        # Alert for critical errors
        if severity == ErrorSeverity.CRITICAL:
            self._handle_critical_error(error_info)
        
        return error_info
    
    def _generate_error_id(self) -> str:
        """Generate unique error identifier.

        Returns:
            Unique error ID combining timestamp and object ID.
        """
        return f"err_{int(datetime.now().timestamp())}_{id(object())}"
    
    def _get_log_level(self, severity: ErrorSeverity) -> str:
        """Map error severity to appropriate logging level.

        Args:
            severity: Error severity level.

        Returns:
            Log level string (info, warning, error, or critical).
        """
        mapping = {
            ErrorSeverity.LOW: "info",
            ErrorSeverity.MEDIUM: "warning",
            ErrorSeverity.HIGH: "error",
            ErrorSeverity.CRITICAL: "critical"
        }
        return mapping.get(severity, "warning")
    
    def _generate_user_message(self, category: ErrorCategory, error: Exception) -> str:
        """Generate user-friendly error message based on category.

        Args:
            category: Error category.
            error: The exception that occurred.

        Returns:
            User-friendly error message string.
        """
        messages = {
            ErrorCategory.DATABASE: "Database operation failed. Please try again later.",
            ErrorCategory.API: "Service request failed. Please check your input and try again.",
            ErrorCategory.PRINTER: "Printer operation failed. Please check printer status.",
            ErrorCategory.FILE_OPERATION: "File operation failed. Please check file permissions.",
            ErrorCategory.NETWORK: "Network operation failed. Please check your connection.",
            ErrorCategory.VALIDATION: "Invalid input provided. Please check your data.",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please log in again.",
            ErrorCategory.AUTHORIZATION: "Access denied. You don't have permission for this operation.",
            ErrorCategory.CONFIGURATION: "Configuration error. Please contact support.",
            ErrorCategory.SYSTEM: "System error occurred. Please try again later.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again."
        }
        return messages.get(category, "An error occurred. Please try again.")
    
    def _log_to_file(self, error_info: Dict[str, Any]):
        """Persist error information to JSON log file.

        Args:
            error_info: Error information dictionary to log.
        """
        try:
            with open(self.error_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_info) + '\n')
        except Exception as e:
            logger.error("Failed to log error to file", file_error=str(e))
    
    def _handle_critical_error(self, error_info: Dict[str, Any]):
        """Handle critical errors with special logging and alerting.

        Args:
            error_info: Error information dictionary for critical error.
        """
        logger.critical(
            "CRITICAL ERROR DETECTED",
            error_id=error_info["id"],
            error_type=error_info["type"],
            error_message=error_info["message"],
            context=error_info["context"]
        )
        
        # Here you could add alerting mechanisms like:
        # - Send email notifications
        # - Post to Slack/Discord
        # - Trigger monitoring alerts
        # - Write to special alert file
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics from log file."""
        try:
            if not self.error_log_path.exists():
                return self._empty_stats(hours)
            
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            errors = []
            
            with open(self.error_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        error_data = json.loads(line.strip())
                        error_time = datetime.fromisoformat(error_data['timestamp']).timestamp()
                        if error_time >= cutoff_time:
                            errors.append(error_data)
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            return self._calculate_statistics(errors, hours)
            
        except Exception as e:
            logger.error("Failed to calculate error statistics", error=str(e))
            return self._empty_stats(hours)
    
    def _empty_stats(self, hours: int) -> Dict[str, Any]:
        """Return empty statistics structure.

        Args:
            hours: Time period for statistics.

        Returns:
            Empty statistics dictionary with default values.
        """
        return {
            "period_hours": hours,
            "total_errors": 0,
            "by_category": {},
            "by_severity": {},
            "by_type": {},
            "recent_errors": []
        }
    
    def _calculate_statistics(self, errors: list, hours: int) -> Dict[str, Any]:
        """Calculate error statistics from error list.

        Args:
            errors: List of error dictionaries.
            hours: Time period for statistics.

        Returns:
            Statistics dictionary with counts by category, severity, and type.
        """
        by_category = {}
        by_severity = {}
        by_type = {}
        
        for error in errors:
            # Count by category
            category = error.get('category', 'unknown')
            by_category[category] = by_category.get(category, 0) + 1
            
            # Count by severity
            severity = error.get('severity', 'unknown')
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # Count by type
            error_type = error.get('type', 'unknown')
            by_type[error_type] = by_type.get(error_type, 0) + 1
        
        return {
            "period_hours": hours,
            "total_errors": len(errors),
            "by_category": by_category,
            "by_severity": by_severity,
            "by_type": by_type,
            "recent_errors": errors[-10:]  # Last 10 errors
        }

    def _safe_cleanup_old_logs(self):
        """Run log cleanup safely, catching and logging any errors."""
        try:
            result = self.cleanup_old_logs()
            if result["removed_count"] > 0:
                logger.info(
                    "Log retention cleanup completed",
                    removed_entries=result["removed_count"],
                    retained_entries=result["retained_count"],
                    retention_days=self.retention_days
                )
        except Exception as e:
            logger.error("Failed to cleanup old logs", error=str(e))

    def cleanup_old_logs(self, retention_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Remove log entries older than the retention period.

        This implements GDPR-compliant data retention by removing old error logs.
        Uses atomic file operations to prevent data loss.

        Args:
            retention_days: Override the default retention period.
                           If None, uses the instance's retention_days.

        Returns:
            Dict with cleanup statistics:
            - removed_count: Number of entries removed
            - retained_count: Number of entries retained
            - cutoff_date: The cutoff date used
            - retention_days: The retention period used
        """
        days = retention_days if retention_days is not None else self.retention_days
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_timestamp = cutoff_date.timestamp()

        if not self.error_log_path.exists():
            return {
                "removed_count": 0,
                "retained_count": 0,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": days
            }

        removed_count = 0
        retained_entries = []

        try:
            # Read and filter entries
            with open(self.error_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entry_time = datetime.fromisoformat(
                            entry.get('timestamp', '')
                        ).timestamp()

                        if entry_time >= cutoff_timestamp:
                            retained_entries.append(line)
                        else:
                            removed_count += 1
                    except (json.JSONDecodeError, ValueError, KeyError):
                        # Keep malformed entries to avoid data loss
                        # They might be manually inspected
                        retained_entries.append(line)

            # Write retained entries atomically using a temp file
            if removed_count > 0:
                # Create temp file in same directory for atomic rename
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=self.error_log_path.parent,
                    suffix='.tmp'
                )
                try:
                    with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                        for entry in retained_entries:
                            f.write(entry + '\n')

                    # Atomic replace
                    shutil.move(temp_path, self.error_log_path)
                except Exception:
                    # Clean up temp file on error
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise

            return {
                "removed_count": removed_count,
                "retained_count": len(retained_entries),
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": days
            }

        except Exception as e:
            logger.error(
                "Failed to cleanup old logs",
                error=str(e),
                retention_days=days
            )
            raise

    def get_log_retention_info(self) -> Dict[str, Any]:
        """
        Get information about log retention settings and current log state.

        Returns:
            Dict with retention information:
            - retention_days: Current retention period
            - log_file_path: Path to the log file
            - log_file_exists: Whether the log file exists
            - log_file_size_bytes: Size of the log file
            - total_entries: Total number of log entries
            - oldest_entry_date: Date of the oldest entry
            - newest_entry_date: Date of the newest entry
            - entries_by_age: Count of entries by age bracket
        """
        info = {
            "retention_days": self.retention_days,
            "log_file_path": str(self.error_log_path),
            "log_file_exists": self.error_log_path.exists(),
            "log_file_size_bytes": 0,
            "total_entries": 0,
            "oldest_entry_date": None,
            "newest_entry_date": None,
            "entries_by_age": {
                "last_24_hours": 0,
                "last_7_days": 0,
                "last_30_days": 0,
                "older": 0
            }
        }

        if not self.error_log_path.exists():
            return info

        info["log_file_size_bytes"] = self.error_log_path.stat().st_size

        now = datetime.now()
        one_day_ago = (now - timedelta(days=1)).timestamp()
        seven_days_ago = (now - timedelta(days=7)).timestamp()
        thirty_days_ago = (now - timedelta(days=30)).timestamp()

        oldest_ts = None
        newest_ts = None

        try:
            with open(self.error_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entry_ts = datetime.fromisoformat(
                            entry.get('timestamp', '')
                        ).timestamp()

                        info["total_entries"] += 1

                        # Track oldest/newest
                        if oldest_ts is None or entry_ts < oldest_ts:
                            oldest_ts = entry_ts
                        if newest_ts is None or entry_ts > newest_ts:
                            newest_ts = entry_ts

                        # Count by age bracket
                        if entry_ts >= one_day_ago:
                            info["entries_by_age"]["last_24_hours"] += 1
                        elif entry_ts >= seven_days_ago:
                            info["entries_by_age"]["last_7_days"] += 1
                        elif entry_ts >= thirty_days_ago:
                            info["entries_by_age"]["last_30_days"] += 1
                        else:
                            info["entries_by_age"]["older"] += 1

                    except (json.JSONDecodeError, ValueError, KeyError):
                        info["total_entries"] += 1
                        info["entries_by_age"]["older"] += 1

            if oldest_ts:
                info["oldest_entry_date"] = datetime.fromtimestamp(
                    oldest_ts
                ).isoformat()
            if newest_ts:
                info["newest_entry_date"] = datetime.fromtimestamp(
                    newest_ts
                ).isoformat()

        except Exception as e:
            logger.error("Failed to get log retention info", error=str(e))

        return info


# Global error handler instance
error_handler = ErrorHandler()


def handle_exceptions(
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    user_message: Optional[str] = None,
    reraise: bool = True
):
    """
    Decorator to automatically handle exceptions in functions.
    
    Args:
        category: Error category
        severity: Error severity
        user_message: User-friendly message
        reraise: Whether to re-raise the exception
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    error=e,
                    category=category,
                    severity=severity,
                    context={
                        "function": func.__name__,
                        "args": str(args)[:200],  # Limit length
                        "kwargs": str(kwargs)[:200]
                    },
                    user_message=user_message
                )
                if reraise:
                    raise
                return None
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    error=e,
                    category=category,
                    severity=severity,
                    context={
                        "function": func.__name__,
                        "args": str(args)[:200],  # Limit length
                        "kwargs": str(kwargs)[:200]
                    },
                    user_message=user_message
                )
                if reraise:
                    raise
                return None
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


class ErrorReportingMixin:
    """Mixin class to add error reporting capabilities to service classes."""
    
    def report_error(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Report an error through the global error handler."""
        return error_handler.handle_error(
            error=error,
            category=category,
            severity=severity,
            context=context,
            user_message=user_message
        )


# Convenience functions for common error types
def handle_database_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle database-related errors."""
    return error_handler.handle_error(
        error=error,
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.HIGH,
        context=context
    )


def handle_api_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle API-related errors."""
    return error_handler.handle_error(
        error=error,
        category=ErrorCategory.API,
        severity=ErrorSeverity.MEDIUM,
        context=context
    )


def handle_printer_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle printer-related errors."""
    return error_handler.handle_error(
        error=error,
        category=ErrorCategory.PRINTER,
        severity=ErrorSeverity.HIGH,
        context=context
    )


def handle_file_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle file operation errors."""
    return error_handler.handle_error(
        error=error,
        category=ErrorCategory.FILE_OPERATION,
        severity=ErrorSeverity.MEDIUM,
        context=context
    )


def handle_validation_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle validation errors."""
    return error_handler.handle_error(
        error=error,
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        context=context
    )