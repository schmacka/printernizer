"""
Unit tests for CameraSnapshotService.
Tests snapshot retrieval, caching, and cleanup functionality.

Sprint 2 Phase 2 - Feature Service Test Coverage.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from src.services.camera_snapshot_service import (
    CameraSnapshotService, CachedFrame, detect_image_format
)


class TestDetectImageFormat:
    """Test image format detection from magic bytes."""

    def test_detect_jpeg(self):
        """Test JPEG detection from magic bytes."""
        jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100
        assert detect_image_format(jpeg_data) == 'image/jpeg'

    def test_detect_png(self):
        """Test PNG detection from magic bytes."""
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        assert detect_image_format(png_data) == 'image/png'

    def test_detect_unknown_defaults_to_jpeg(self):
        """Test unknown format defaults to JPEG."""
        unknown_data = b'\x00\x01\x02\x03\x04\x05\x06\x07'
        assert detect_image_format(unknown_data) == 'image/jpeg'

    def test_detect_empty_data(self):
        """Test empty data defaults to JPEG."""
        assert detect_image_format(b'') == 'image/jpeg'


class TestCachedFrame:
    """Test CachedFrame dataclass."""

    def test_cached_frame_creation(self):
        """Test CachedFrame creation."""
        data = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        now = datetime.now()

        frame = CachedFrame(data=data, captured_at=now)

        assert frame.data == data
        assert frame.captured_at == now


class TestCameraSnapshotServiceInitialization:
    """Test CameraSnapshotService initialization."""

    def test_initialization(self):
        """Test service initialization with printer service."""
        mock_printer_service = MagicMock()

        service = CameraSnapshotService(mock_printer_service)

        assert service.printer_service is mock_printer_service
        assert service._running is False
        assert service._cleanup_task is None
        assert len(service._frame_cache) == 0

    def test_repr(self):
        """Test string representation."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        repr_str = repr(service)

        assert "CameraSnapshotService" in repr_str
        assert "running=False" in repr_str


class TestCameraSnapshotServiceLifecycle:
    """Test service start and shutdown lifecycle."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Test start sets running flag."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        await service.start()

        assert service._running is True
        assert service._cleanup_task is not None

        # Cleanup
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_start_when_already_running(self):
        """Test start logs warning when already running."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        await service.start()

        # Second start should warn but not fail
        await service.start()

        assert service._running is True

        # Cleanup
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_stops_service(self):
        """Test shutdown stops service properly."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        await service.start()

        # Add some cache entries
        service._frame_cache["printer_001"] = CachedFrame(b"data", datetime.now())

        await service.shutdown()

        assert service._running is False
        assert len(service._frame_cache) == 0

    @pytest.mark.asyncio
    async def test_shutdown_cancels_cleanup_task(self):
        """Test shutdown cancels cleanup task."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        await service.start()
        cleanup_task = service._cleanup_task

        await service.shutdown()

        assert cleanup_task.cancelled() or cleanup_task.done()


class TestCameraSnapshotServiceCache:
    """Test frame caching functionality."""

    def test_get_cached_frame_not_found(self):
        """Test getting non-existent cached frame."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        result = service._get_cached_frame("nonexistent_printer")

        assert result is None

    def test_get_cached_frame_fresh(self):
        """Test getting fresh cached frame."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        # Add fresh frame
        fresh_frame = CachedFrame(b"fresh data", datetime.now())
        service._frame_cache["printer_001"] = fresh_frame

        result = service._get_cached_frame("printer_001")

        assert result is fresh_frame

    def test_get_cached_frame_expired(self):
        """Test expired cached frame is not returned."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        # Add expired frame (6 seconds ago, TTL is 5 seconds)
        expired_time = datetime.now() - timedelta(seconds=6)
        expired_frame = CachedFrame(b"expired data", expired_time)
        service._frame_cache["printer_001"] = expired_frame

        result = service._get_cached_frame("printer_001")

        assert result is None
        assert "printer_001" not in service._frame_cache


class TestCameraSnapshotServiceSnapshots:
    """Test snapshot retrieval."""

    @pytest.mark.asyncio
    async def test_get_snapshot_by_id_cached(self):
        """Test snapshot returns cached frame."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        # Add cached frame
        jpeg_data = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        service._frame_cache["printer_001"] = CachedFrame(jpeg_data, datetime.now())

        data, content_type = await service.get_snapshot_by_id("printer_001")

        assert data == jpeg_data
        assert content_type == 'image/jpeg'

    @pytest.mark.asyncio
    async def test_get_snapshot_by_id_force_refresh(self):
        """Test force refresh bypasses cache."""
        mock_printer_service = MagicMock()
        mock_driver = AsyncMock()
        mock_driver.take_snapshot = AsyncMock(return_value=b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        mock_printer_service.get_printer_driver = AsyncMock(return_value=mock_driver)

        service = CameraSnapshotService(mock_printer_service)

        # Add cached JPEG
        service._frame_cache["printer_001"] = CachedFrame(
            b'\xff\xd8\xff\xe0' + b'\x00' * 100,
            datetime.now()
        )

        data, content_type = await service.get_snapshot_by_id("printer_001", force_refresh=True)

        # Should get fresh PNG from driver
        assert content_type == 'image/png'
        mock_driver.take_snapshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_snapshot_by_id_printer_not_found(self):
        """Test snapshot raises for unknown printer."""
        mock_printer_service = MagicMock()
        mock_printer_service.get_printer_driver = AsyncMock(
            side_effect=Exception("Printer not found")
        )

        service = CameraSnapshotService(mock_printer_service)

        with pytest.raises(ValueError, match="Printer not found"):
            await service.get_snapshot_by_id("unknown_printer")

    @pytest.mark.asyncio
    async def test_get_snapshot_by_id_no_frame_available(self):
        """Test snapshot raises when no frame available."""
        mock_printer_service = MagicMock()
        mock_driver = AsyncMock()
        mock_driver.take_snapshot = AsyncMock(return_value=None)
        mock_printer_service.get_printer_driver = AsyncMock(return_value=mock_driver)

        service = CameraSnapshotService(mock_printer_service)

        with pytest.raises(ValueError, match="No frame available"):
            await service.get_snapshot_by_id("printer_001")

    @pytest.mark.asyncio
    async def test_get_snapshot_by_id_updates_cache(self):
        """Test successful snapshot updates cache."""
        mock_printer_service = MagicMock()
        mock_driver = AsyncMock()
        jpeg_data = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        mock_driver.take_snapshot = AsyncMock(return_value=jpeg_data)
        mock_printer_service.get_printer_driver = AsyncMock(return_value=mock_driver)

        service = CameraSnapshotService(mock_printer_service)

        await service.get_snapshot_by_id("printer_001", force_refresh=True)

        assert "printer_001" in service._frame_cache
        assert service._frame_cache["printer_001"].data == jpeg_data

    @pytest.mark.asyncio
    async def test_get_snapshot_legacy_interface(self):
        """Test legacy get_snapshot interface."""
        mock_printer_service = MagicMock()
        mock_driver = AsyncMock()
        jpeg_data = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        mock_driver.take_snapshot = AsyncMock(return_value=jpeg_data)
        mock_printer_service.get_printer_driver = AsyncMock(return_value=mock_driver)

        service = CameraSnapshotService(mock_printer_service)

        # Legacy interface with extra parameters
        data = await service.get_snapshot(
            printer_id="printer_001",
            ip_address="192.168.1.100",
            access_code="12345678",
            serial_number="ABC123",
            force_refresh=True
        )

        assert data == jpeg_data

    @pytest.mark.asyncio
    async def test_get_snapshot_uses_cache_by_default(self):
        """Test snapshot uses cache when available."""
        mock_printer_service = MagicMock()
        mock_driver = AsyncMock()
        mock_driver.take_snapshot = AsyncMock(return_value=b'new data')
        mock_printer_service.get_printer_driver = AsyncMock(return_value=mock_driver)

        service = CameraSnapshotService(mock_printer_service)

        # Pre-populate cache
        cached_data = b'\xff\xd8\xff\xe0cached'
        service._frame_cache["printer_001"] = CachedFrame(cached_data, datetime.now())

        data, _ = await service.get_snapshot_by_id("printer_001")

        # Should return cached data without calling driver
        assert data == cached_data
        mock_driver.take_snapshot.assert_not_called()


class TestCameraSnapshotServiceCleanup:
    """Test cache cleanup functionality."""

    @pytest.mark.asyncio
    async def test_cleanup_idle_connections(self):
        """Test cleanup removes expired entries."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        # Add expired entry
        expired_time = datetime.now() - timedelta(seconds=10)
        service._frame_cache["expired_printer"] = CachedFrame(b"expired", expired_time)

        # Add fresh entry
        service._frame_cache["fresh_printer"] = CachedFrame(b"fresh", datetime.now())

        await service._cleanup_idle_connections()

        assert "expired_printer" not in service._frame_cache
        assert "fresh_printer" in service._frame_cache

    @pytest.mark.asyncio
    async def test_cleanup_loop_runs(self):
        """Test cleanup loop starts and runs."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        await service.start()

        # Verify cleanup task is running
        assert service._cleanup_task is not None
        assert not service._cleanup_task.done()

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_cleanup_loop_handles_errors(self):
        """Test cleanup loop handles errors gracefully."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        service._running = True

        # Mock cleanup to raise error
        with patch.object(service, '_cleanup_idle_connections',
                         new_callable=AsyncMock,
                         side_effect=Exception("Cleanup error")):

            # Start cleanup loop
            task = asyncio.create_task(service._cleanup_loop())

            # Let it run briefly
            await asyncio.sleep(0.1)

            # Stop and cancel
            service._running = False
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Should not have crashed


class TestCameraSnapshotServiceStats:
    """Test statistics reporting."""

    def test_get_stats_empty(self):
        """Test stats with no cached frames."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        stats = service.get_stats()

        assert stats['cached_frames'] == 0
        assert stats['running'] is False
        assert stats['cache_entries'] == {}

    def test_get_stats_with_cache(self):
        """Test stats with cached frames."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)
        service._running = True

        # Add cached frame
        frame_data = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        service._frame_cache["printer_001"] = CachedFrame(frame_data, datetime.now())

        stats = service.get_stats()

        assert stats['cached_frames'] == 1
        assert stats['running'] is True
        assert "printer_001" in stats['cache_entries']
        assert stats['cache_entries']['printer_001']['size_bytes'] == len(frame_data)

    def test_get_stats_shows_age(self):
        """Test stats include frame age."""
        mock_printer_service = MagicMock()
        service = CameraSnapshotService(mock_printer_service)

        # Add frame captured 2 seconds ago
        captured_time = datetime.now() - timedelta(seconds=2)
        service._frame_cache["printer_001"] = CachedFrame(b"data", captured_time)

        stats = service.get_stats()

        age_seconds = stats['cache_entries']['printer_001']['age_seconds']
        assert age_seconds >= 2
        assert age_seconds < 5  # Allow some tolerance


class TestCameraSnapshotServiceConcurrency:
    """Test concurrent access handling."""

    @pytest.mark.asyncio
    async def test_concurrent_snapshot_requests(self):
        """Test multiple concurrent snapshot requests."""
        mock_printer_service = MagicMock()
        mock_driver = AsyncMock()

        call_count = 0

        async def mock_take_snapshot():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate network delay
            return b'\xff\xd8\xff\xe0' + bytes([call_count]) * 10

        mock_driver.take_snapshot = mock_take_snapshot
        mock_printer_service.get_printer_driver = AsyncMock(return_value=mock_driver)

        service = CameraSnapshotService(mock_printer_service)

        # Make concurrent requests
        tasks = [
            service.get_snapshot_by_id("printer_001", force_refresh=True)
            for _ in range(3)
        ]

        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 3
        for data, content_type in results:
            assert content_type == 'image/jpeg'

    @pytest.mark.asyncio
    async def test_cache_prevents_duplicate_requests(self):
        """Test cache prevents duplicate driver calls."""
        mock_printer_service = MagicMock()
        mock_driver = AsyncMock()

        call_count = 0

        async def mock_take_snapshot():
            nonlocal call_count
            call_count += 1
            return b'\xff\xd8\xff\xe0' + b'\x00' * 100

        mock_driver.take_snapshot = mock_take_snapshot
        mock_printer_service.get_printer_driver = AsyncMock(return_value=mock_driver)

        service = CameraSnapshotService(mock_printer_service)

        # First request - cache miss
        await service.get_snapshot_by_id("printer_001")

        # Second request - cache hit
        await service.get_snapshot_by_id("printer_001")

        # Third request - cache hit
        await service.get_snapshot_by_id("printer_001")

        # Driver should only be called once
        assert call_count == 1
