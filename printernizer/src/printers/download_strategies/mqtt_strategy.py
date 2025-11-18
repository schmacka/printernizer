"""
MQTT download strategy for Bambu Lab printers.

Note: MQTT protocol does not support file downloads directly.
This strategy exists for completeness but will always fail.
"""

from .base import (
    DownloadStrategy,
    DownloadResult,
    DownloadOptions,
    FatalDownloadError
)


class MQTTDownloadStrategy(DownloadStrategy):
    """MQTT download strategy (not supported).

    MQTT protocol is designed for messaging, not file transfer.
    This strategy exists as a placeholder and will always report unavailable.
    """

    def __init__(self, printer_id: str, printer_ip: str):
        """Initialize MQTT download strategy.

        Args:
            printer_id: Unique identifier for the printer
            printer_ip: IP address of the printer
        """
        super().__init__(printer_id, printer_ip)

    @property
    def name(self) -> str:
        """Return the name of this strategy."""
        return "MQTT"

    async def is_available(self) -> bool:
        """Check if MQTT download is available.

        Returns:
            False (MQTT does not support file downloads)
        """
        return False

    async def download(self, options: DownloadOptions) -> DownloadResult:
        """MQTT download not supported.

        Args:
            options: Download configuration options

        Returns:
            DownloadResult with failure status

        Raises:
            FatalDownloadError: Always, as MQTT cannot download files
        """
        self.logger.warning(
            "File download not supported via MQTT protocol",
            filename=options.filename
        )

        raise FatalDownloadError(
            "MQTT protocol does not support file downloads. "
            "Use FTP or HTTP download strategies instead."
        )
