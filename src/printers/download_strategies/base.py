"""
Base classes for download strategy pattern.

Defines the interface and common types for file download strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List
import structlog

logger = structlog.get_logger()


class DownloadError(Exception):
    """Base exception for download errors."""

    def __init__(self, message: str, retryable: bool = True):
        """Initialize download error.

        Args:
            message: Error description
            retryable: Whether the operation can be retried
        """
        super().__init__(message)
        self.retryable = retryable


class FatalDownloadError(DownloadError):
    """Non-retryable download error."""

    def __init__(self, message: str):
        super().__init__(message, retryable=False)


class RetryableDownloadError(DownloadError):
    """Retryable download error."""

    def __init__(self, message: str):
        super().__init__(message, retryable=True)


@dataclass
class DownloadResult:
    """Result of a download operation."""

    success: bool
    """Whether the download succeeded"""

    file_path: Optional[str] = None
    """Local path where file was saved"""

    size_bytes: Optional[int] = None
    """Size of downloaded file in bytes"""

    remote_path: Optional[str] = None
    """Remote path/URL that was used"""

    strategy_used: Optional[str] = None
    """Name of the strategy that succeeded"""

    error: Optional[str] = None
    """Error message if failed"""

    attempts: int = 1
    """Number of attempts made"""


@dataclass
class DownloadOptions:
    """Configuration options for downloads."""

    filename: str
    """Name of the file to download"""

    local_path: str
    """Local filesystem path to save the file"""

    remote_paths: Optional[List[str]] = None
    """List of remote paths to try (strategy-specific)"""

    max_retries: int = 3
    """Maximum number of retry attempts per path"""

    timeout_seconds: int = 60
    """Timeout for download operation"""

    chunk_size_bytes: int = 8192
    """Size of chunks for streaming downloads"""

    auth_username: Optional[str] = None
    """Authentication username if required"""

    auth_password: Optional[str] = None
    """Authentication password/access code if required"""


class DownloadStrategy(ABC):
    """Abstract base class for download strategies.

    Each strategy implements a specific protocol (FTP, HTTP, etc.)
    for downloading files from printers.
    """

    def __init__(self, printer_id: str, printer_ip: str):
        """Initialize download strategy.

        Args:
            printer_id: Unique identifier for the printer
            printer_ip: IP address of the printer
        """
        self.printer_id = printer_id
        self.printer_ip = printer_ip
        self.logger = logger.bind(
            printer_id=printer_id,
            strategy=self.__class__.__name__
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this strategy."""
        pass

    @abstractmethod
    async def download(self, options: DownloadOptions) -> DownloadResult:
        """Download a file using this strategy.

        Args:
            options: Download configuration options

        Returns:
            DownloadResult with success status and details

        Raises:
            DownloadError: If download fails and cannot be retried
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this strategy is available/supported.

        Returns:
            True if strategy can be used, False otherwise
        """
        pass

    def _ensure_directory(self, file_path: str) -> None:
        """Ensure the parent directory of a file exists.

        Args:
            file_path: Path to the file
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    def _write_file_chunk(self, file_path: str, data: bytes, mode: str = 'wb') -> int:
        """Write data to a file.

        Args:
            file_path: Path to write to
            data: Data to write
            mode: File open mode ('wb' for binary write, 'ab' for append)

        Returns:
            Number of bytes written
        """
        with open(file_path, mode) as f:
            f.write(data)
        return len(data)

    def _get_file_size(self, file_path: str) -> Optional[int]:
        """Get the size of a file.

        Args:
            file_path: Path to the file

        Returns:
            File size in bytes, or None if file doesn't exist
        """
        try:
            return Path(file_path).stat().st_size
        except FileNotFoundError:
            return None

    def _log_progress(self, downloaded: int, total: Optional[int], filename: str) -> None:
        """Log download progress.

        Args:
            downloaded: Bytes downloaded so far
            total: Total bytes to download (if known)
            filename: Name of the file being downloaded
        """
        if total:
            progress = (downloaded / total) * 100
            self.logger.debug(
                "Download progress",
                filename=filename,
                downloaded=downloaded,
                total=total,
                progress=f"{progress:.1f}%"
            )
        else:
            self.logger.debug(
                "Download progress",
                filename=filename,
                downloaded=downloaded
            )
