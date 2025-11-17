"""
Camera Snapshot Service.

Manages on-demand snapshot retrieval from Bambu Lab cameras with caching
and connection pooling. Handles camera client lifecycle and provides
cached frame access to reduce printer load.

Features:
- Connection pooling (one client per printer)
- Frame caching with TTL (default 5 seconds)
- Lazy client initialization
- Idle connection cleanup
- Graceful error handling

Example:
    service = CameraSnapshotService()
    await service.start()

    # Get snapshot (uses cache if fresh)
    frame = await service.get_snapshot(printer_id)

    await service.shutdown()
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

import structlog

from src.config.constants import PollingIntervals

from src.services.bambu_camera_client import BambuLabCameraClient, CameraConnectionError
from src.constants import CameraConstants


logger = structlog.get_logger(__name__)


@dataclass
class CameraConnection:
    """Represents a camera client connection with metadata."""
    client: BambuLabCameraClient
    last_accessed: datetime
    connection_count: int = 0


@dataclass
class CachedFrame:
    """Represents a cached camera frame with timestamp."""
    data: bytes
    captured_at: datetime


class CameraSnapshotService:
    """
    Service for managing camera snapshot requests with caching.

    Maintains a pool of camera clients (one per printer) and caches
    frames to reduce load on printers. Automatically cleans up idle
    connections.

    Thread-safe for concurrent access.
    """

    def __init__(self):
        """Initialize snapshot service."""
        self._camera_clients: Dict[str, CameraConnection] = {}
        self._frame_cache: Dict[str, CachedFrame] = {}
        self._connection_locks: Dict[str, asyncio.Lock] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running: bool = False

        self._logger = logger.bind(service="camera_snapshot")

    async def start(self):
        """Start the snapshot service and background tasks."""
        if self._running:
            self._logger.warning("Service already running")
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._logger.info("Camera snapshot service started")

    async def shutdown(self):
        """Shutdown service and cleanup all connections."""
        self._logger.info("Shutting down camera snapshot service")
        self._running = False

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Disconnect all camera clients
        for printer_id, connection in list(self._camera_clients.items()):
            try:
                await connection.client.disconnect()
                self._logger.debug("Disconnected camera client", printer_id=printer_id)
            except Exception as e:
                self._logger.warning(
                    "Error disconnecting camera",
                    printer_id=printer_id,
                    error=str(e)
                )

        self._camera_clients.clear()
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
            ip_address: Printer IP address
            access_code: 8-digit LAN access code
            serial_number: Printer serial number
            force_refresh: Skip cache and fetch fresh frame

        Returns:
            JPEG image data

        Raises:
            CameraConnectionError: If camera connection fails
            ValueError: If no frame available
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

        # Get or create camera client
        client = await self._get_or_create_client(
            printer_id=printer_id,
            ip_address=ip_address,
            access_code=access_code,
            serial_number=serial_number
        )

        # Get latest frame
        frame = await client.get_latest_frame()
        if not frame:
            # Wait for camera to start streaming (needs ~3 seconds after connection)
            self._logger.debug("No frame cached, waiting for first frame", printer_id=printer_id)
            await asyncio.sleep(3.0)
            frame = await client.get_latest_frame()

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

    async def _get_or_create_client(
        self,
        printer_id: str,
        ip_address: str,
        access_code: str,
        serial_number: str
    ) -> BambuLabCameraClient:
        """
        Get existing camera client or create new one.

        Thread-safe with per-printer locking.
        """
        # Get or create lock for this printer
        if printer_id not in self._connection_locks:
            self._connection_locks[printer_id] = asyncio.Lock()

        async with self._connection_locks[printer_id]:
            # Check if client exists and is connected
            if printer_id in self._camera_clients:
                connection = self._camera_clients[printer_id]
                connection.last_accessed = datetime.now()
                connection.connection_count += 1

                # Verify connection is still alive
                if connection.client.is_connected:
                    self._logger.debug(
                        "Reusing existing camera client",
                        printer_id=printer_id,
                        connections=connection.connection_count
                    )
                    return connection.client
                else:
                    # Connection died, clean up
                    self._logger.warning(
                        "Existing camera connection is dead, reconnecting",
                        printer_id=printer_id
                    )
                    try:
                        await connection.client.disconnect()
                    except:
                        pass
                    del self._camera_clients[printer_id]

            # Create new camera client
            self._logger.info(
                "Creating new camera client",
                printer_id=printer_id,
                ip=ip_address
            )

            client = BambuLabCameraClient(
                ip_address=ip_address,
                access_code=access_code,
                serial_number=serial_number,
                printer_id=printer_id
            )

            # Connect to camera
            try:
                await client.connect()
            except Exception as e:
                self._logger.error(
                    "Failed to connect to camera",
                    printer_id=printer_id,
                    error=str(e)
                )
                raise

            # Store connection
            self._camera_clients[printer_id] = CameraConnection(
                client=client,
                last_accessed=datetime.now(),
                connection_count=1
            )

            return client

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
        """Close connections that have been idle too long."""
        now = datetime.now()
        idle_threshold = timedelta(seconds=CameraConstants.CAMERA_IDLE_TIMEOUT_SECONDS)

        to_remove = []
        for printer_id, connection in self._camera_clients.items():
            idle_time = now - connection.last_accessed

            if idle_time > idle_threshold:
                to_remove.append(printer_id)

        # Disconnect and remove idle connections
        for printer_id in to_remove:
            connection = self._camera_clients[printer_id]
            self._logger.info(
                "Closing idle camera connection",
                printer_id=printer_id,
                idle_seconds=int((now - connection.last_accessed).total_seconds())
            )

            try:
                await connection.client.disconnect()
            except Exception as e:
                self._logger.warning(
                    "Error disconnecting idle camera",
                    printer_id=printer_id,
                    error=str(e)
                )

            del self._camera_clients[printer_id]

            # Also clean up cache
            if printer_id in self._frame_cache:
                del self._frame_cache[printer_id]

        if to_remove:
            self._logger.info(
                "Cleaned up idle connections",
                count=len(to_remove),
                remaining=len(self._camera_clients)
            )

    def get_stats(self) -> Dict[str, any]:
        """
        Get service statistics.

        Returns:
            Dictionary with service stats
        """
        return {
            "active_connections": len(self._camera_clients),
            "cached_frames": len(self._frame_cache),
            "running": self._running,
            "connections": {
                printer_id: {
                    "connected": conn.client.is_connected,
                    "last_accessed": conn.last_accessed.isoformat(),
                    "connection_count": conn.connection_count
                }
                for printer_id, conn in self._camera_clients.items()
            }
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CameraSnapshotService(running={self._running}, "
            f"active_connections={len(self._camera_clients)}, "
            f"cached_frames={len(self._frame_cache)})"
        )
