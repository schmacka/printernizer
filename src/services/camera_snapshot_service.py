"""
Camera Snapshot Service.

Manages on-demand snapshot retrieval from printer cameras and external webcams with frame caching.
Delegates camera access to printer drivers via PrinterService.

Features:
- Frame caching with TTL (default 5 seconds)
- Automatic cache expiration cleanup
- External webcam support (HTTP snapshots, RTSP streams)
- Graceful error handling

Example:
    service = CameraSnapshotService(printer_service)
    await service.start()

    # Get snapshot (uses cache if fresh)
    frame = await service.get_snapshot(printer_id)

    # Get external webcam snapshot
    frame = await service.get_snapshot_by_id(printer_id, source='external')

    await service.shutdown()
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Literal, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

import structlog

from src.config.constants import PollingIntervals
from src.constants import CameraConstants
from src.services.external_camera_service import ExternalCameraService


def detect_image_format(data: bytes) -> str:
    """Detect image format from magic bytes.
    
    Args:
        data: Image data bytes
        
    Returns:
        MIME type string (image/jpeg, image/png, or image/jpeg as fallback)
    """
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    elif data[:2] == b'\xff\xd8':
        return 'image/jpeg'
    else:
        # Default to JPEG for unknown formats
        return 'image/jpeg'

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
        self._external_cache: Dict[str, CachedFrame] = {}  # Separate cache for external webcams
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._external_camera_service = ExternalCameraService()

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

        # Close external camera service
        await self._external_camera_service.close()

        # Clear caches
        self._frame_cache.clear()
        self._external_cache.clear()
        self._logger.info("Camera snapshot service shutdown complete")

    async def get_snapshot_by_id(
        self,
        printer_id: str,
        force_refresh: bool = False,
        source: Literal['auto', 'builtin', 'external'] = 'auto'
    ) -> Tuple[bytes, str]:
        """
        Get camera snapshot for a printer by ID.

        This is a simplified interface that works with any printer type
        (Bambu Lab, Prusa, etc.) by delegating to the printer driver,
        and also supports external webcam URLs.

        Args:
            printer_id: Unique printer identifier
            force_refresh: Skip cache and fetch fresh frame
            source: Camera source preference:
                - 'auto': Try external webcam first if configured, fall back to built-in
                - 'builtin': Only use built-in printer camera
                - 'external': Only use external webcam URL

        Returns:
            Tuple of (image data bytes, MIME type string)

        Raises:
            ValueError: If no frame available or printer not found
        """
        self._logger.debug(
            "Snapshot requested (by ID)",
            printer_id=printer_id,
            force_refresh=force_refresh,
            source=source
        )

        # Handle external webcam source
        if source == 'external':
            return await self._get_external_snapshot(printer_id, force_refresh)

        # For 'auto' mode, check if external webcam is configured
        if source == 'auto':
            webcam_url = await self._get_printer_webcam_url(printer_id)
            if webcam_url:
                try:
                    return await self._get_external_snapshot(printer_id, force_refresh)
                except ValueError:
                    # Fall back to built-in camera if external fails
                    self._logger.debug(
                        "External webcam failed, falling back to built-in",
                        printer_id=printer_id
                    )

        # Built-in camera: Check cache first (unless force refresh)
        if not force_refresh:
            cached = self._get_cached_frame(printer_id)
            if cached:
                self._logger.debug(
                    "Serving cached snapshot",
                    printer_id=printer_id,
                    age_seconds=(datetime.now() - cached.captured_at).total_seconds()
                )
                content_type = detect_image_format(cached.data)
                return cached.data, content_type

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

        # Detect content type
        content_type = detect_image_format(frame)

        self._logger.info(
            "Snapshot captured",
            printer_id=printer_id,
            size=len(frame),
            content_type=content_type
        )

        return frame, content_type

    async def _get_printer_webcam_url(self, printer_id: str) -> Optional[str]:
        """Get the webcam_url configured for a printer, if any."""
        try:
            printer = await self.printer_service.get_printer(printer_id)
            if printer:
                return getattr(printer, 'webcam_url', None)
        except Exception as e:
            self._logger.debug(
                "Failed to get printer webcam_url",
                printer_id=printer_id,
                error=str(e)
            )
        return None

    async def _get_external_snapshot(
        self,
        printer_id: str,
        force_refresh: bool = False
    ) -> Tuple[bytes, str]:
        """
        Get snapshot from external webcam URL.

        Args:
            printer_id: Printer ID to get webcam URL for
            force_refresh: Skip cache and fetch fresh frame

        Returns:
            Tuple of (image data bytes, MIME type string)

        Raises:
            ValueError: If no webcam URL configured or fetch failed
        """
        # Get webcam URL from printer config
        webcam_url = await self._get_printer_webcam_url(printer_id)
        if not webcam_url:
            raise ValueError(f"No external webcam URL configured for printer {printer_id}")

        # Use external cache key
        cache_key = f"external_{printer_id}"

        # Check external cache first (unless force refresh)
        if not force_refresh and cache_key in self._external_cache:
            cached = self._external_cache[cache_key]
            age = (datetime.now() - cached.captured_at).total_seconds()
            if age <= CameraConstants.FRAME_CACHE_TTL_SECONDS:
                self._logger.debug(
                    "Serving cached external webcam snapshot",
                    printer_id=printer_id,
                    age_seconds=age
                )
                content_type = detect_image_format(cached.data)
                return cached.data, content_type

        # Fetch from external webcam
        frame, content_type = await self._external_camera_service.fetch_snapshot(
            webcam_url, printer_id
        )

        if not frame:
            raise ValueError("No frame available from external webcam")

        # Update external cache
        self._external_cache[cache_key] = CachedFrame(
            data=frame,
            captured_at=datetime.now()
        )

        self._logger.info(
            "External webcam snapshot captured",
            printer_id=printer_id,
            size=len(frame),
            content_type=content_type
        )

        return frame, content_type

    async def get_snapshot(
        self,
        printer_id: str,
        ip_address: str,
        access_code: str,
        serial_number: str,
        force_refresh: bool = False
    ) -> bytes:
        """
        Get camera snapshot for a printer (legacy interface for Bambu Lab).

        Args:
            printer_id: Unique printer identifier
            ip_address: Printer IP address (kept for interface compatibility)
            access_code: 8-digit LAN access code (kept for interface compatibility)
            serial_number: Printer serial number (kept for interface compatibility)
            force_refresh: Skip cache and fetch fresh frame

        Returns:
            Image data bytes (JPEG or PNG)

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
