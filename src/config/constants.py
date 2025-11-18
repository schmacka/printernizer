"""Application-wide configuration constants.

This module centralizes all hardcoded values that were previously scattered
throughout the codebase, making them easier to maintain and configure.
"""

from typing import Final


class PollingIntervals:
    """Configurable polling intervals for various services (in seconds).

    These values control how frequently background tasks check for updates
    from printers, jobs, and the file system.
    """

    # Printer monitoring intervals
    PRINTER_STATUS_CHECK: Final[int] = 30
    """Check printer status every 30 seconds"""

    PRINTER_STATUS_ERROR_BACKOFF: Final[int] = 60
    """Wait 60 seconds before retrying after printer error"""

    # Job monitoring intervals
    JOB_STATUS_CHECK: Final[int] = 10
    """Check active job status every 10 seconds"""

    JOB_STATUS_ERROR_BACKOFF: Final[int] = 30
    """Wait 30 seconds before retrying after job error"""

    # File discovery intervals
    FILE_DISCOVERY_CHECK: Final[int] = 300
    """Check for new files every 5 minutes (300 seconds)"""

    FILE_DISCOVERY_ERROR_BACKOFF: Final[int] = 600
    """Wait 10 minutes (600 seconds) before retrying after file discovery error"""

    # Camera and snapshot intervals
    CAMERA_SNAPSHOT_INTERVAL: Final[int] = 30
    """Capture camera snapshots every 30 seconds"""

    TIMELAPSE_FRAME_INTERVAL: Final[int] = 10
    """Capture timelapse frames every 10 seconds"""

    TIMELAPSE_CHECK_INTERVAL: Final[int] = 30
    """Check for timelapse job completion every 30 seconds"""

    # Monitoring and analytics intervals
    TRENDING_SERVICE_RETRY: Final[int] = 60
    """Wait 60 seconds before retrying trending service operations"""

    MONITORING_SERVICE_DAILY: Final[int] = 86400
    """Run daily monitoring tasks every 24 hours (86400 seconds)"""

    MONITORING_SERVICE_ERROR_BACKOFF: Final[int] = 3600
    """Wait 1 hour (3600 seconds) after monitoring error"""

    MONITORING_SERVICE_RETRY: Final[int] = 60
    """Wait 60 seconds before retrying monitoring operations"""


class RetrySettings:
    """Retry configuration for various operations.

    These values control retry behavior for operations that may fail
    transiently (network requests, file operations, etc.).
    """

    # Download retry settings
    MAX_DOWNLOAD_RETRIES: Final[int] = 3
    """Maximum number of download retry attempts"""

    DOWNLOAD_RETRY_DELAY: Final[int] = 2
    """Initial delay between download retries (seconds), uses exponential backoff"""

    # Camera retry settings
    CAMERA_RETRY_DELAY: Final[int] = 1
    """Delay between camera snapshot retry attempts (seconds)"""

    MAX_CAMERA_RETRIES: Final[int] = 3
    """Maximum number of camera retry attempts"""

    # Network timeout settings
    DEFAULT_TIMEOUT: Final[int] = 30
    """Default timeout for network operations (seconds)"""

    FTP_TIMEOUT: Final[int] = 60
    """Timeout for FTP operations (seconds)"""

    HTTP_TIMEOUT: Final[int] = 30
    """Timeout for HTTP operations (seconds)"""


class APIConfig:
    """API configuration constants.

    These values are used to construct API URLs and configure API behavior.
    """

    VERSION: Final[str] = "v1"
    """Current API version"""

    BASE_PATH: Final[str] = "/api"
    """Base path for all API endpoints"""

    # API endpoint prefixes
    PRINTERS_PREFIX: Final[str] = "printers"
    FILES_PREFIX: Final[str] = "files"
    JOBS_PREFIX: Final[str] = "jobs"
    ANALYTICS_PREFIX: Final[str] = "analytics"
    LIBRARY_PREFIX: Final[str] = "library"
    TRENDING_PREFIX: Final[str] = "trending"
    IDEAS_PREFIX: Final[str] = "ideas"


def api_url(endpoint: str, version: str = APIConfig.VERSION) -> str:
    """Generate a versioned API URL.

    This helper function ensures consistent API URL formatting across
    the application and makes it easy to update the API version.

    Args:
        endpoint: The API endpoint path (e.g., "printers", "files/123")
        version: Optional API version (defaults to current version)

    Returns:
        Formatted API URL (e.g., "/api/v1/printers")

    Examples:
        >>> api_url("printers")
        '/api/v1/printers'
        >>> api_url("files/abc123/thumbnail")
        '/api/v1/files/abc123/thumbnail'
        >>> api_url("/printers/123")  # Leading slash is handled
        '/api/v1/printers/123'
    """
    # Strip leading slashes from endpoint
    clean_endpoint = endpoint.lstrip("/")
    return f"{APIConfig.BASE_PATH}/{version}/{clean_endpoint}"


# Convenience functions for common API endpoints
def printer_url(printer_id: str = "") -> str:
    """Generate URL for printer endpoints.

    Args:
        printer_id: Optional printer ID

    Returns:
        URL for printer endpoint
    """
    if printer_id:
        return api_url(f"{APIConfig.PRINTERS_PREFIX}/{printer_id}")
    return api_url(APIConfig.PRINTERS_PREFIX)


def file_url(file_id: str = "", suffix: str = "") -> str:
    """Generate URL for file endpoints.

    Args:
        file_id: Optional file ID
        suffix: Optional suffix (e.g., "thumbnail", "download")

    Returns:
        URL for file endpoint
    """
    parts = [APIConfig.FILES_PREFIX]
    if file_id:
        parts.append(file_id)
    if suffix:
        parts.append(suffix)
    return api_url("/".join(parts))


def job_url(job_id: str = "") -> str:
    """Generate URL for job endpoints.

    Args:
        job_id: Optional job ID

    Returns:
        URL for job endpoint
    """
    if job_id:
        return api_url(f"{APIConfig.JOBS_PREFIX}/{job_id}")
    return api_url(APIConfig.JOBS_PREFIX)
