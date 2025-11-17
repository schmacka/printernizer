"""
Download strategies for printer file downloads.

This module provides a strategy pattern implementation for downloading files
from printers using different protocols (FTP, HTTP, MQTT).
"""

from .base import DownloadStrategy, DownloadResult, DownloadError
from .handler import DownloadHandler
from .ftp_strategy import FTPDownloadStrategy
from .http_strategy import HTTPDownloadStrategy
from .mqtt_strategy import MQTTDownloadStrategy

__all__ = [
    "DownloadStrategy",
    "DownloadResult",
    "DownloadError",
    "DownloadHandler",
    "FTPDownloadStrategy",
    "HTTPDownloadStrategy",
    "MQTTDownloadStrategy",
]
