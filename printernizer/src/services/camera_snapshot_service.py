"""
Camera Snapshot Service.

Manages on-demand snapshot retrieval from Bambu Lab cameras with frame caching.
Delegates camera access to printer drivers via PrinterService.

Features:
- Frame caching with TTL (default 5 seconds)
- Automatic cache expiration cleanup
- Graceful error handling

Example:
    service = CameraSnapshotService(printer_service)
    await service.start()

    # Get snapshot (uses cache if fresh)
    frame = await service.get_snapshot(printer_id)

    await service.shutdown()
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, TYPE_CHECKING
from dataclasses import dataclass

import structlog

from src.config.constants import PollingIntervals
from src.constants import CameraConstants

if TYPE_CHECKING:
    from src.services.printer_service import PrinterService


logger = structlog.get_logger(__name__)


@dataclass
class CachedFrame:
    """Represents a cached camera frame with timestamp."""
    data: bytes
    captured_at: datetime


class CameraSnapshotService:
    """
    Service for managing camera snapshot requests with caching.

    Caches frames to reduce load on printers. Camera access is delegated
    to printer drivers via PrinterService.

    Thread-safe for concurrent access.
    """

    def __init__(self, printer_service: 'PrinterService'):
        """Initialize snapshot service.

        Args:
            printer_service: PrinterService instance for accessing printer drivers
        """
        self.printer_service = printer_service
        self._frame_cache: Dict[str, CachedFrame] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running: bool = False

        self._logger = logger.bind(service="camera_snapshot")

    async def start(self) -> None:
        """Start the snapshot service and background tasks."""
        if self._running:
            self._logger.warning("Service already running")
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._logger.info("Camera snapshot service started")

    async def shutdown(self) -> None:
        """Shutdown service and cleanup resources."""
        self._logger.info("Shutting down camera snapshot service")
        self._running = False

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Clear cache
        self._frame_cache.clear()
        self._logger.info("Camera snapshot service shutdown complete")

    async def get_snapshot(
        self,
        printer_id: str,
        ip_address: str,
        access_code: str,
        serial_number: str,
        force_refresh: bool = False
    ) -> bytes:
        """
        Get camera snapshot for a printer.

        Args:
            printer_id: Unique printer identifier
            ip_address: Printer IP address (kept for interface compatibility)
            access_code: 8-digit LAN access code (kept for interface compatibility)
            serial_number: Printer serial number (kept for interface compatibility)
            force_refresh: Skip cache and fetch fresh frame

        Returns:
            JPEG image data

        Raises:
            ValueError: If no frame available or printer not found
        """
        self._logger.debug(
            "Snapshot requested",
            printer_id=printer_id,
            force_refresh=force_refresh
        )

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = self._get_cached_frame(printer_id)
            if cached:
                self._logger.debug(
                    "Serving cached snapshot",
                    printer_id=printer_id,
                    age_seconds=(datetime.now() - cached.captured_at).total_seconds()
                )
                return cached.data

        # Get printer driver via PrinterService
        try:
            printer_driver = await self.printer_service.get_printer_driver(printer_id)
        except Exception as e:
            self._logger.error(
                "Failed to get printer driver",
                printer_id=printer_id,
                error=str(e)
            )
            raise ValueError(f"Printer not found: {printer_id}") from e

        # Get snapshot from printer driver
        frame = await printer_driver.take_snapshot()

        if not frame:
            raise ValueError("No frame available from camera")

        # Update cache
        self._frame_cache[printer_id] = CachedFrame(
            data=frame,
            captured_at=datetime.now()
        )

        self._logger.info(
            "Snapshot captured",
            printer_id=printer_id,
            size=len(frame)
        )

        return frame

    def _get_cached_frame(self, printer_id: str) -> Optional[CachedFrame]:
        """
        Get cached frame if it's still fresh.

        Returns:
            Cached frame if fresh, None otherwise
        """
        if printer_id not in self._frame_cache:
            return None

        cached = self._frame_cache[printer_id]
        age = (datetime.now() - cached.captured_at).total_seconds()

        if age > CameraConstants.FRAME_CACHE_TTL_SECONDS:
            # Cache expired
            self._logger.debug(
                "Cache expired",
                printer_id=printer_id,
                age_seconds=age,
                ttl_seconds=CameraConstants.FRAME_CACHE_TTL_SECONDS
            )
            del self._frame_cache[printer_id]
            return None

        return cached

    async def _cleanup_loop(self):
        """Background task to cleanup idle connections."""
        self._logger.debug("Starting cleanup loop")

        while self._running:
            try:
                await asyncio.sleep(PollingIntervals.CAMERA_SNAPSHOT_INTERVAL)  # Run every 30 seconds
                await self._cleanup_idle_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("Error in cleanup loop", error=str(e))

        self._logger.debug("Cleanup loop stopped")

    async def _cleanup_idle_connections(self):
        """Clean up expired cache entries."""
        now = datetime.now()
        cache_ttl = timedelta(seconds=CameraConstants.FRAME_CACHE_TTL_SECONDS)

        to_remove = []
        for printer_id, cached_frame in self._frame_cache.items():
            age = now - cached_frame.captured_at

            if age > cache_ttl:
                to_remove.append(printer_id)

        # Remove expired cache entries
        for printer_id in to_remove:
            del self._frame_cache[printer_id]

        if to_remove:
            self._logger.debug(
                "Cleaned up expired cache entries",
                count=len(to_remove),
                remaining=len(self._frame_cache)
            )

    def get_stats(self) -> Dict[str, any]:
        """
        Get service statistics.

        Returns:
            Dictionary with service stats
        """
        return {
            "cached_frames": len(self._frame_cache),
            "running": self._running,
            "cache_entries": {
                printer_id: {
                    "captured_at": frame.captured_at.isoformat(),
                    "age_seconds": (datetime.now() - frame.captured_at).total_seconds(),
                    "size_bytes": len(frame.data)
                }
                for printer_id, frame in self._frame_cache.items()
            }
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CameraSnapshotService(running={self._running}, "
            f"cached_frames={len(self._frame_cache)})"
        )
