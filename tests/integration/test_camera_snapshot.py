"""
Integration tests for Bambu Lab camera snapshot functionality.

Tests the complete camera snapshot workflow including:
- CameraSnapshotService connection pooling and caching
- Camera API endpoints (capture, list, download)
- Database persistence of snapshots
- Error handling and edge cases
- Frame caching with TTL
- Connection lifecycle management
"""

import pytest
import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from PIL import Image
import io

from src.services.camera_snapshot_service import CameraSnapshotService, CameraConnection, CachedFrame
from src.services.bambu_camera_client import (
    BambuLabCameraClient,
    CameraConnectionError,
    AuthenticationError,
    FrameParsingError
)
from src.database.database import Database
from src.constants import CameraConstants


# =====================================================
# FIXTURES
# =====================================================

@pytest.fixture
def mock_camera_client():
    """Mock BambuLabCameraClient for testing."""
    client = AsyncMock(spec=BambuLabCameraClient)
    client.is_connected = True
    client.printer_id = "test_printer_001"
    client.ip_address = "192.168.1.100"

    # Create a minimal valid JPEG (1x1 pixel)
    img = Image.new('RGB', (1280, 720), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    mock_frame = img_bytes.getvalue()

    client.get_latest_frame = AsyncMock(return_value=mock_frame)
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()

    return client


@pytest.fixture
def sample_snapshot_data():
    """Sample snapshot data for testing."""
    return {
        'printer_id': 'test_printer_001',
        'job_id': None,
        'filename': 'snapshot_test_20250117_120000.jpg',
        'file_size': 125714,
        'content_type': 'image/jpeg',
        'storage_path': '/data/snapshots/snapshot_test_20250117_120000.jpg',
        'captured_at': datetime.now().isoformat(),
        'capture_trigger': 'manual',
        'width': 1280,
        'height': 720,
        'is_valid': True,
        'notes': 'Integration test snapshot'
    }


@pytest.fixture
async def temp_snapshot_dir():
    """Create temporary directory for snapshot storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# =====================================================
# CAMERA SNAPSHOT SERVICE TESTS
# =====================================================

@pytest.mark.asyncio
async def test_camera_service_lifecycle():
    """Test camera snapshot service start and shutdown."""
    service = CameraSnapshotService()

    # Service should not be running initially
    assert not service._running

    # Start service
    await service.start()
    assert service._running
    assert service._cleanup_task is not None

    # Starting again should be idempotent
    await service.start()
    assert service._running

    # Shutdown
    await service.shutdown()
    assert not service._running
    assert len(service._camera_clients) == 0
    assert len(service._frame_cache) == 0


@pytest.mark.asyncio
async def test_camera_service_get_snapshot_with_mock(mock_camera_client):
    """Test getting snapshot through service with mocked camera client."""
    service = CameraSnapshotService()
    await service.start()

    try:
        # Mock the client creation
        with patch.object(
            service,
            '_get_or_create_client',
            return_value=mock_camera_client
        ) as mock_create:

            # Get snapshot
            frame = await service.get_snapshot(
                printer_id="test_printer_001",
                ip_address="192.168.1.100",
                access_code="12345678",
                serial_number="AC12345678",
                force_refresh=True
            )

            # Verify
            assert frame is not None
            assert len(frame) > 0
            assert frame[:2] == b'\xff\xd8'  # JPEG start marker

            # Verify client was created
            mock_create.assert_called_once()

            # Verify frame was cached
            assert "test_printer_001" in service._frame_cache

    finally:
        await service.shutdown()


@pytest.mark.asyncio
async def test_camera_service_frame_caching(mock_camera_client):
    """Test frame caching with TTL."""
    service = CameraSnapshotService()
    await service.start()

    try:
        with patch.object(
            service,
            '_get_or_create_client',
            return_value=mock_camera_client
        ):
            # First request - should call camera
            frame1 = await service.get_snapshot(
                printer_id="test_printer_001",
                ip_address="192.168.1.100",
                access_code="12345678",
                serial_number="AC12345678"
            )
            call_count_1 = mock_camera_client.get_latest_frame.call_count

            # Second request - should use cache
            frame2 = await service.get_snapshot(
                printer_id="test_printer_001",
                ip_address="192.168.1.100",
                access_code="12345678",
                serial_number="AC12345678"
            )
            call_count_2 = mock_camera_client.get_latest_frame.call_count

            # Should be same frame from cache
            assert frame1 == frame2
            # Camera should not have been called again
            assert call_count_1 == call_count_2

            # Force refresh should bypass cache
            frame3 = await service.get_snapshot(
                printer_id="test_printer_001",
                ip_address="192.168.1.100",
                access_code="12345678",
                serial_number="AC12345678",
                force_refresh=True
            )
            call_count_3 = mock_camera_client.get_latest_frame.call_count

            # Camera should have been called again
            assert call_count_3 > call_count_2

    finally:
        await service.shutdown()


@pytest.mark.asyncio
async def test_camera_service_cache_expiry(mock_camera_client):
    """Test cache expiry after TTL."""
    service = CameraSnapshotService()
    await service.start()

    try:
        with patch.object(
            service,
            '_get_or_create_client',
            return_value=mock_camera_client
        ):
            # Get snapshot
            await service.get_snapshot(
                printer_id="test_printer_001",
                ip_address="192.168.1.100",
                access_code="12345678",
                serial_number="AC12345678"
            )

            # Manually expire cache by modifying timestamp
            cached = service._frame_cache["test_printer_001"]
            cached.captured_at = datetime.now() - timedelta(
                seconds=CameraConstants.FRAME_CACHE_TTL_SECONDS + 1
            )

            # Next request should fetch fresh frame
            call_count_before = mock_camera_client.get_latest_frame.call_count

            await service.get_snapshot(
                printer_id="test_printer_001",
                ip_address="192.168.1.100",
                access_code="12345678",
                serial_number="AC12345678"
            )

            call_count_after = mock_camera_client.get_latest_frame.call_count

            # Should have fetched new frame
            assert call_count_after > call_count_before

    finally:
        await service.shutdown()


@pytest.mark.asyncio
async def test_camera_service_connection_pooling(mock_camera_client):
    """Test connection pooling (one client per printer)."""
    service = CameraSnapshotService()
    await service.start()

    try:
        with patch(
            'src.services.camera_snapshot_service.BambuLabCameraClient',
            return_value=mock_camera_client
        ):
            # First request - create client
            await service.get_snapshot(
                printer_id="test_printer_001",
                ip_address="192.168.1.100",
                access_code="12345678",
                serial_number="AC12345678",
                force_refresh=True
            )

            # Verify client was created
            assert "test_printer_001" in service._camera_clients
            connection1 = service._camera_clients["test_printer_001"]
            assert connection1.connection_count == 1

            # Second request - reuse client
            await service.get_snapshot(
                printer_id="test_printer_001",
                ip_address="192.168.1.100",
                access_code="12345678",
                serial_number="AC12345678",
                force_refresh=True
            )

            # Should be same client
            connection2 = service._camera_clients["test_printer_001"]
            assert connection2.client is connection1.client
            assert connection2.connection_count == 2

    finally:
        await service.shutdown()


@pytest.mark.asyncio
async def test_camera_service_connection_error_handling():
    """Test error handling when camera connection fails."""
    service = CameraSnapshotService()
    await service.start()

    try:
        # Mock client that fails to connect
        with patch(
            'src.services.camera_snapshot_service.BambuLabCameraClient'
        ) as MockClient:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock(
                side_effect=CameraConnectionError("Connection failed")
            )
            MockClient.return_value = mock_instance

            # Should raise error
            with pytest.raises(CameraConnectionError):
                await service.get_snapshot(
                    printer_id="test_printer_001",
                    ip_address="192.168.1.100",
                    access_code="12345678",
                    serial_number="AC12345678"
                )

    finally:
        await service.shutdown()


@pytest.mark.asyncio
async def test_camera_service_no_frame_available():
    """Test handling when no frame is available from camera."""
    service = CameraSnapshotService()
    await service.start()

    try:
        # Mock client that returns no frame
        mock_client = AsyncMock(spec=BambuLabCameraClient)
        mock_client.is_connected = True
        mock_client.get_latest_frame = AsyncMock(return_value=None)
        mock_client.connect = AsyncMock()

        with patch.object(
            service,
            '_get_or_create_client',
            return_value=mock_client
        ):
            # Should raise ValueError
            with pytest.raises(ValueError, match="No frame available"):
                await service.get_snapshot(
                    printer_id="test_printer_001",
                    ip_address="192.168.1.100",
                    access_code="12345678",
                    serial_number="AC12345678"
                )

    finally:
        await service.shutdown()


@pytest.mark.asyncio
async def test_camera_service_stats():
    """Test service statistics reporting."""
    service = CameraSnapshotService()
    await service.start()

    try:
        # Initially empty
        stats = service.get_stats()
        assert stats['active_connections'] == 0
        assert stats['cached_frames'] == 0
        assert stats['running'] == True

        # Add mock connection and cache
        mock_client = AsyncMock(spec=BambuLabCameraClient)
        mock_client.is_connected = True

        service._camera_clients["test_printer_001"] = CameraConnection(
            client=mock_client,
            last_accessed=datetime.now(),
            connection_count=5
        )

        service._frame_cache["test_printer_001"] = CachedFrame(
            data=b"fake_jpeg_data",
            captured_at=datetime.now()
        )

        # Check updated stats
        stats = service.get_stats()
        assert stats['active_connections'] == 1
        assert stats['cached_frames'] == 1
        assert "test_printer_001" in stats['connections']
        assert stats['connections']['test_printer_001']['connection_count'] == 5

    finally:
        await service.shutdown()


@pytest.mark.asyncio
async def test_camera_service_idle_connection_cleanup(mock_camera_client):
    """Test automatic cleanup of idle connections."""
    service = CameraSnapshotService()
    await service.start()

    try:
        # Add connection
        service._camera_clients["test_printer_001"] = CameraConnection(
            client=mock_camera_client,
            last_accessed=datetime.now() - timedelta(
                seconds=CameraConstants.CAMERA_IDLE_TIMEOUT_SECONDS + 1
            ),
            connection_count=1
        )

        # Add cache
        service._frame_cache["test_printer_001"] = CachedFrame(
            data=b"fake_jpeg_data",
            captured_at=datetime.now()
        )

        # Run cleanup
        await service._cleanup_idle_connections()

        # Should be removed
        assert "test_printer_001" not in service._camera_clients
        assert "test_printer_001" not in service._frame_cache

        # Verify disconnect was called
        mock_camera_client.disconnect.assert_called_once()

    finally:
        await service.shutdown()


# =====================================================
# DATABASE INTEGRATION TESTS
# =====================================================

@pytest.mark.asyncio
async def test_snapshot_database_create():
    """Test creating snapshot record in database."""
    import tempfile
    import os

    # Create a fresh temporary database (no pre-existing schema)
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db_path = temp_db.name
    temp_db.close()

    db = Database(temp_db_path)
    await db.initialize()

    try:
        # First create a printer
        printer_data = {
            'id': 'test_printer_001',
            'name': 'Test Bambu A1',
            'type': 'bambu_lab',
            'ip_address': '192.168.1.100',
            'is_active': True
        }
        await db.create_printer(printer_data)

        # Create snapshot
        snapshot_data = {
            'printer_id': 'test_printer_001',
            'job_id': None,
            'filename': 'test_snapshot.jpg',
            'file_size': 125714,
            'content_type': 'image/jpeg',
            'storage_path': '/data/snapshots/test_snapshot.jpg',
            'captured_at': datetime.now().isoformat(),
            'capture_trigger': 'manual',
            'width': 1280,
            'height': 720,
            'is_valid': True,
            'notes': 'Test snapshot'
        }

        snapshot_id = await db.create_snapshot(snapshot_data)

        # Verify
        assert snapshot_id is not None
        assert snapshot_id > 0

        # Retrieve and verify
        snapshot = await db.get_snapshot_by_id(snapshot_id)
        assert snapshot is not None
        assert snapshot['filename'] == 'test_snapshot.jpg'
        assert snapshot['printer_id'] == 'test_printer_001'
        assert snapshot['width'] == 1280
        assert snapshot['height'] == 720

    finally:
        await db.close()
        # Cleanup temp file
        try:
            os.unlink(temp_db_path)
        except:
            pass


@pytest.mark.asyncio
async def test_snapshot_database_list():
    """Test listing snapshots with filtering."""
    import tempfile
    import os

    # Create a fresh temporary database (no pre-existing schema)
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db_path = temp_db.name
    temp_db.close()

    db = Database(temp_db_path)
    await db.initialize()

    try:
        # Create printer
        printer_data = {
            'id': 'test_printer_001',
            'name': 'Test Bambu A1',
            'type': 'bambu_lab',
            'ip_address': '192.168.1.100',
            'is_active': True
        }
        await db.create_printer(printer_data)

        # Create multiple snapshots
        for i in range(5):
            snapshot_data = {
                'printer_id': 'test_printer_001',
                'filename': f'snapshot_{i}.jpg',
                'file_size': 100000 + i,
                'content_type': 'image/jpeg',
                'storage_path': f'/data/snapshots/snapshot_{i}.jpg',
                'capture_trigger': 'manual',
                'is_valid': True
            }
            await db.create_snapshot(snapshot_data)

        # List all snapshots
        snapshots = await db.list_snapshots()
        assert len(snapshots) == 5

        # List with limit
        snapshots = await db.list_snapshots(limit=3)
        assert len(snapshots) == 3

        # List with offset
        snapshots = await db.list_snapshots(limit=3, offset=2)
        assert len(snapshots) == 3

        # List for specific printer
        snapshots = await db.list_snapshots(printer_id='test_printer_001')
        assert len(snapshots) == 5
        assert all(s['printer_id'] == 'test_printer_001' for s in snapshots)

    finally:
        await db.close()
        # Cleanup temp file
        try:
            os.unlink(temp_db_path)
        except:
            pass


@pytest.mark.asyncio
async def test_snapshot_with_job_context():
    """Test snapshot with job context (v_snapshots_with_context view)."""
    import tempfile
    import os

    # Create a fresh temporary database (no pre-existing schema)
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db_path = temp_db.name
    temp_db.close()

    db = Database(temp_db_path)
    await db.initialize()

    try:
        # Create printer
        printer_data = {
            'id': 'test_printer_001',
            'name': 'Test Bambu A1',
            'type': 'bambu_lab',
            'ip_address': '192.168.1.100',
            'is_active': True
        }
        await db.create_printer(printer_data)

        # Create job
        import uuid
        job_id = str(uuid.uuid4())
        job_data = {
            'id': job_id,
            'printer_id': 'test_printer_001',
            'printer_type': 'bambu_lab',
            'job_name': 'test_print.3mf',
            'status': 'printing',
            'progress': 50.0
        }
        await db.create_job(job_data)

        # Create snapshot linked to job
        snapshot_data = {
            'printer_id': 'test_printer_001',
            'job_id': job_id,
            'filename': 'snapshot_with_job.jpg',
            'file_size': 125714,
            'content_type': 'image/jpeg',
            'storage_path': '/data/snapshots/snapshot_with_job.jpg',
            'capture_trigger': 'manual',
            'is_valid': True
        }

        snapshot_id = await db.create_snapshot(snapshot_data)

        # Retrieve with context
        snapshot = await db.get_snapshot_by_id(snapshot_id)

        # Verify job context
        assert snapshot['job_id'] == job_id
        assert snapshot['job_name'] == 'test_print.3mf'
        assert snapshot['job_status'] == 'printing'
        assert snapshot['printer_name'] == 'Test Bambu A1'
        assert snapshot['printer_type'] == 'bambu_lab'

    finally:
        await db.close()
        # Cleanup temp file
        try:
            os.unlink(temp_db_path)
        except:
            pass


# =====================================================
# CAMERA CLIENT TESTS
# =====================================================

@pytest.mark.asyncio
async def test_camera_client_initialization():
    """Test camera client initialization."""
    client = BambuLabCameraClient(
        ip_address="192.168.1.100",
        access_code="12345678",
        serial_number="AC12345678",
        printer_id="test_printer_001"
    )

    assert client.ip_address == "192.168.1.100"
    assert client.access_code == "12345678"
    assert client.serial_number == "AC12345678"
    assert client.printer_id == "test_printer_001"
    assert not client.is_connected


@pytest.mark.asyncio
async def test_camera_client_auth_packet():
    """Test authentication packet building."""
    client = BambuLabCameraClient(
        ip_address="192.168.1.100",
        access_code="12345678",
        serial_number="AC12345678",
        printer_id="test_printer_001"
    )

    auth_packet = client._build_auth_packet()

    # Verify packet size
    assert len(auth_packet) == CameraConstants.AUTH_PACKET_SIZE  # 80 bytes

    # Verify header (first 16 bytes)
    assert auth_packet[0:4] != b'\x00\x00\x00\x00'  # Has payload size

    # Verify username field contains "bblp"
    assert b'bblp' in auth_packet[16:48]

    # Verify password field contains access code
    assert b'12345678' in auth_packet[48:80]


@pytest.mark.asyncio
async def test_camera_client_repr():
    """Test camera client string representation."""
    client = BambuLabCameraClient(
        ip_address="192.168.1.100",
        access_code="12345678",
        serial_number="AC12345678",
        printer_id="test_printer_001"
    )

    repr_str = repr(client)
    assert "test_printer_001" in repr_str
    assert "192.168.1.100" in repr_str
    assert "disconnected" in repr_str


# =====================================================
# EDGE CASES AND ERROR HANDLING
# =====================================================

@pytest.mark.asyncio
async def test_camera_service_multiple_printers(mock_camera_client):
    """Test service handling multiple printers concurrently."""
    service = CameraSnapshotService()
    await service.start()

    try:
        with patch(
            'src.services.camera_snapshot_service.BambuLabCameraClient',
            return_value=mock_camera_client
        ):
            # Get snapshots from multiple printers
            tasks = []
            for i in range(3):
                task = service.get_snapshot(
                    printer_id=f"printer_{i:03d}",
                    ip_address=f"192.168.1.{100+i}",
                    access_code="12345678",
                    serial_number=f"AC1234567{i}",
                    force_refresh=True
                )
                tasks.append(task)

            # Execute concurrently
            frames = await asyncio.gather(*tasks)

            # Verify all succeeded
            assert len(frames) == 3
            assert all(f is not None for f in frames)

            # Verify separate clients created
            assert len(service._camera_clients) == 3
            assert "printer_000" in service._camera_clients
            assert "printer_001" in service._camera_clients
            assert "printer_002" in service._camera_clients

    finally:
        await service.shutdown()


@pytest.mark.asyncio
async def test_camera_service_reconnect_dead_connection():
    """Test reconnection when existing connection is dead."""
    service = CameraSnapshotService()
    await service.start()

    try:
        # Create mock client that's disconnected
        dead_client = AsyncMock(spec=BambuLabCameraClient)
        dead_client.is_connected = False
        dead_client.disconnect = AsyncMock()

        # Add to service
        service._camera_clients["test_printer_001"] = CameraConnection(
            client=dead_client,
            last_accessed=datetime.now(),
            connection_count=1
        )

        # Create new mock client for reconnection
        new_client = AsyncMock(spec=BambuLabCameraClient)
        new_client.is_connected = True
        new_client.connect = AsyncMock()

        # Create mock frame
        img = Image.new('RGB', (1280, 720), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        new_client.get_latest_frame = AsyncMock(return_value=img_bytes.getvalue())

        with patch(
            'src.services.camera_snapshot_service.BambuLabCameraClient',
            return_value=new_client
        ):
            # Should detect dead connection and reconnect
            frame = await service.get_snapshot(
                printer_id="test_printer_001",
                ip_address="192.168.1.100",
                access_code="12345678",
                serial_number="AC12345678",
                force_refresh=True
            )

            # Verify
            assert frame is not None

            # Old client should have been disconnected
            dead_client.disconnect.assert_called()

            # New client should be connected
            new_client.connect.assert_called()

    finally:
        await service.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
