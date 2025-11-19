# Bambu Lab Camera Testing Strategy

**Date**: November 14, 2025
**Status**: Planning Phase
**Related Document**: [BAMBU_LAB_CAMERA_IMPLEMENTATION_PLAN.md](BAMBU_LAB_CAMERA_IMPLEMENTATION_PLAN.md)

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Unit Testing Requirements](#unit-testing-requirements)
3. [Integration Testing Requirements](#integration-testing-requirements)
4. [Manual Testing Checklist](#manual-testing-checklist)
5. [Test Data and Fixtures](#test-data-and-fixtures)
6. [Success Criteria Verification](#success-criteria-verification)
7. [Test Environment Setup](#test-environment-setup)
8. [Performance Testing](#performance-testing)
9. [Security Testing](#security-testing)
10. [CI/CD Integration](#cicd-integration)

## Testing Overview

### Testing Philosophy
- **Test Pyramid**: 70% Unit, 20% Integration, 10% E2E/Manual
- **Coverage Target**: Minimum 80% code coverage for camera modules
- **Performance Baseline**: < 2 second latency for snapshots, < 500ms frame delivery for streams
- **Security Focus**: TLS validation, access code protection, connection security

### Testing Scope

**In Scope:**
- TCP camera client connection and authentication
- Binary packet parsing and frame reassembly
- Snapshot caching service
- MJPEG stream generation
- API endpoint functionality
- Error handling and reconnection logic
- Concurrent viewer management

**Out of Scope:**
- Physical printer hardware testing (mocked)
- Network infrastructure testing
- Browser compatibility testing (manual only)
- X1 series RTSP implementation (future phase)

---

## Unit Testing Requirements

### 1. BambuLabCameraClient Unit Tests
**File**: `tests/unit/services/test_bambu_camera_client.py`

#### Test Categories

##### 1.1 Connection and Authentication Tests

```python
class TestBambuCameraClientConnection:
    """Test camera client connection lifecycle."""

    async def test_connect_success(self, mock_ssl_context, mock_socket):
        """Test successful TLS connection to camera."""
        client = BambuLabCameraClient("192.168.1.100", "12345678", "ABC123")
        result = await client.connect()

        assert result is True
        assert client.is_connected
        mock_socket.connect.assert_called_once_with(("192.168.1.100", 6000))

    async def test_connect_with_invalid_ip(self):
        """Test connection failure with invalid IP address."""
        client = BambuLabCameraClient("invalid_ip", "12345678", "ABC123")

        with pytest.raises(ConnectionError):
            await client.connect()

    async def test_connect_timeout(self, mock_socket):
        """Test connection timeout handling."""
        mock_socket.connect.side_effect = asyncio.TimeoutError()
        client = BambuLabCameraClient("192.168.1.100", "12345678", "ABC123")

        with pytest.raises(asyncio.TimeoutError):
            await client.connect()

    async def test_tls_certificate_validation(self, mock_ssl_context):
        """Test TLS certificate is properly configured."""
        client = BambuLabCameraClient("192.168.1.100", "12345678", "ABC123")
        await client.connect()

        # Verify SNI is set to serial number
        assert mock_ssl_context.server_hostname == "ABC123"
        # Verify Bambu CA certificate is loaded
        assert mock_ssl_context.check_hostname is False  # Bambu uses self-signed

    async def test_disconnect(self, connected_client):
        """Test graceful disconnection."""
        await connected_client.disconnect()

        assert not connected_client.is_connected
        assert connected_client.socket is None
```

##### 1.2 Authentication Packet Tests

```python
class TestAuthenticationPacket:
    """Test authentication packet construction."""

    def test_build_auth_packet_structure(self):
        """Test 80-byte authentication packet structure."""
        client = BambuLabCameraClient("192.168.1.100", "12345678", "ABC123")
        packet = client._build_auth_packet()

        # Verify packet size
        assert len(packet) == 80

        # Verify header (bytes 0-15)
        payload_size = struct.unpack('<I', packet[0:4])[0]
        assert payload_size == 0x40  # 64 bytes payload

        packet_type = struct.unpack('<H', packet[4:6])[0]
        assert packet_type == 0x3000

    def test_auth_packet_username(self):
        """Test username field is correctly set to 'bblp'."""
        client = BambuLabCameraClient("192.168.1.100", "12345678", "ABC123")
        packet = client._build_auth_packet()

        # Extract username (bytes 16-47, null-padded)
        username = packet[16:48].rstrip(b'\x00').decode('ascii')
        assert username == "bblp"

    def test_auth_packet_access_code(self):
        """Test access code field is correctly set."""
        client = BambuLabCameraClient("192.168.1.100", "12345678", "ABC123")
        packet = client._build_auth_packet()

        # Extract access code (bytes 48-79, null-padded)
        access_code = packet[48:80].rstrip(b'\x00').decode('ascii')
        assert access_code == "12345678"

    def test_auth_packet_with_long_access_code(self):
        """Test handling of maximum length access code."""
        # Access code can be up to 32 bytes
        long_code = "A" * 32
        client = BambuLabCameraClient("192.168.1.100", long_code, "ABC123")
        packet = client._build_auth_packet()

        access_code = packet[48:80].rstrip(b'\x00').decode('ascii')
        assert access_code == long_code

    async def test_send_authentication(self, mock_socket):
        """Test authentication packet is sent correctly."""
        client = BambuLabCameraClient("192.168.1.100", "12345678", "ABC123")
        await client.connect()
        await client.authenticate()

        # Verify 80-byte packet was sent
        sent_data = mock_socket.send.call_args[0][0]
        assert len(sent_data) == 80
```

##### 1.3 Frame Parsing Tests

```python
class TestFrameParsing:
    """Test JPEG frame parsing and reassembly."""

    async def test_read_frame_header(self, connected_client, mock_socket):
        """Test reading 16-byte frame header."""
        # Mock header: 4-byte size + 12-byte metadata
        header = struct.pack('<I', 12345) + b'\x00' * 12
        mock_socket.recv.return_value = header

        frame_size = await connected_client._read_frame_header()
        assert frame_size == 12345

    async def test_read_complete_jpeg_frame(self, connected_client, mock_socket):
        """Test reading complete JPEG frame."""
        # Mock JPEG data (FF D8 start, FF D9 end)
        jpeg_data = b'\xff\xd8' + b'\x00' * 1000 + b'\xff\xd9'

        mock_socket.recv.side_effect = [
            struct.pack('<I', len(jpeg_data)) + b'\x00' * 12,  # Header
            jpeg_data  # JPEG data
        ]

        frame = await connected_client.read_frame()

        assert frame.startswith(b'\xff\xd8')
        assert frame.endswith(b'\xff\xd9')
        assert len(frame) == len(jpeg_data)

    async def test_read_frame_in_chunks(self, connected_client, mock_socket):
        """Test reassembling frame from multiple chunks."""
        jpeg_data = b'\xff\xd8' + b'\x00' * 5000 + b'\xff\xd9'

        # Simulate receiving in 4096-byte chunks
        chunks = [jpeg_data[i:i+4096] for i in range(0, len(jpeg_data), 4096)]

        mock_socket.recv.side_effect = [
            struct.pack('<I', len(jpeg_data)) + b'\x00' * 12,  # Header
            *chunks  # Data in chunks
        ]

        frame = await connected_client.read_frame()
        assert frame == jpeg_data

    async def test_invalid_jpeg_markers(self, connected_client, mock_socket):
        """Test handling of invalid JPEG markers."""
        invalid_data = b'\x00\x00' + b'\x00' * 1000 + b'\x00\x00'

        mock_socket.recv.side_effect = [
            struct.pack('<I', len(invalid_data)) + b'\x00' * 12,
            invalid_data
        ]

        with pytest.raises(ValueError, match="Invalid JPEG frame"):
            await connected_client.read_frame()

    async def test_corrupted_frame_skip(self, connected_client, mock_socket):
        """Test skipping corrupted frames without disconnecting."""
        # First frame corrupted, second frame valid
        corrupt_frame = b'\xff\xd8' + b'\x00' * 100  # Missing end marker
        valid_frame = b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9'

        mock_socket.recv.side_effect = [
            struct.pack('<I', len(corrupt_frame)) + b'\x00' * 12,
            corrupt_frame,
            struct.pack('<I', len(valid_frame)) + b'\x00' * 12,
            valid_frame
        ]

        # Should skip corrupted frame and return valid one
        frame = await connected_client.read_frame()
        assert frame == valid_frame
```

##### 1.4 Connection Resilience Tests

```python
class TestConnectionResilience:
    """Test connection error handling and reconnection."""

    async def test_reconnect_on_connection_lost(self, connected_client):
        """Test automatic reconnection after connection loss."""
        connected_client.socket.recv.side_effect = ConnectionResetError()

        # Should attempt reconnection
        result = await connected_client.reconnect()
        assert result is True

    async def test_reconnect_with_exponential_backoff(self, client, mock_socket):
        """Test reconnection uses exponential backoff."""
        mock_socket.connect.side_effect = [
            ConnectionRefusedError(),
            ConnectionRefusedError(),
            None  # Success on third attempt
        ]

        start_time = time.time()
        result = await client.connect_with_retry(max_attempts=3)
        duration = time.time() - start_time

        # Should wait 1s + 2s = 3s total (exponential backoff)
        assert duration >= 3.0
        assert result is True

    async def test_max_reconnect_attempts(self, client, mock_socket):
        """Test max reconnection attempts are respected."""
        mock_socket.connect.side_effect = ConnectionRefusedError()

        with pytest.raises(ConnectionError, match="Max reconnect attempts"):
            await client.connect_with_retry(max_attempts=3)

    async def test_is_alive_check(self, connected_client):
        """Test connection liveness check."""
        assert await connected_client.is_alive() is True

        connected_client.socket.recv.side_effect = OSError()
        assert await connected_client.is_alive() is False
```

### 2. CameraSnapshotService Unit Tests
**File**: `tests/unit/services/test_camera_snapshot_service.py`

```python
class TestCameraSnapshotService:
    """Test snapshot caching service."""

    async def test_get_snapshot_cache_miss(self, snapshot_service, mock_camera_client):
        """Test fetching snapshot when cache is empty."""
        mock_frame = b'\xff\xd8' + b'\x00' * 1000 + b'\xff\xd9'
        mock_camera_client.read_frame.return_value = mock_frame

        snapshot = await snapshot_service.get_snapshot("printer_123")

        assert snapshot == mock_frame
        mock_camera_client.read_frame.assert_called_once()

    async def test_get_snapshot_cache_hit(self, snapshot_service, mock_camera_client):
        """Test returning cached snapshot within TTL."""
        mock_frame = b'\xff\xd8' + b'\x00' * 1000 + b'\xff\xd9'
        mock_camera_client.read_frame.return_value = mock_frame

        # First call - cache miss
        snapshot1 = await snapshot_service.get_snapshot("printer_123")

        # Second call within TTL - cache hit
        snapshot2 = await snapshot_service.get_snapshot("printer_123")

        assert snapshot1 == snapshot2
        mock_camera_client.read_frame.assert_called_once()  # Only called once

    async def test_cache_expiration(self, snapshot_service, mock_camera_client):
        """Test cache expires after TTL."""
        mock_frame = b'\xff\xd8' + b'\x00' * 1000 + b'\xff\xd9'
        mock_camera_client.read_frame.return_value = mock_frame

        # First call
        await snapshot_service.get_snapshot("printer_123")

        # Wait for cache to expire (mock time advance)
        await asyncio.sleep(6)  # TTL is 5 seconds

        # Second call - cache expired
        await snapshot_service.get_snapshot("printer_123")

        assert mock_camera_client.read_frame.call_count == 2

    async def test_start_camera_connection(self, snapshot_service):
        """Test starting camera connection."""
        result = await snapshot_service.start_camera("printer_123")

        assert result is True
        assert "printer_123" in snapshot_service.active_connections

    async def test_stop_camera_connection(self, snapshot_service):
        """Test stopping camera connection."""
        await snapshot_service.start_camera("printer_123")
        result = await snapshot_service.stop_camera("printer_123")

        assert result is True
        assert "printer_123" not in snapshot_service.active_connections

    async def test_cleanup_idle_connections(self, snapshot_service):
        """Test cleanup of idle connections."""
        await snapshot_service.start_camera("printer_123")

        # Simulate idle timeout (no requests for 10 minutes)
        snapshot_service.last_request["printer_123"] = time.time() - 601

        await snapshot_service.cleanup_idle_connections()

        assert "printer_123" not in snapshot_service.active_connections
```

### 3. CameraStreamService Unit Tests
**File**: `tests/unit/services/test_camera_stream_service.py`

```python
class TestCameraStreamService:
    """Test MJPEG stream generation service."""

    async def test_generate_mjpeg_stream(self, stream_service, mock_camera_client):
        """Test MJPEG stream generation."""
        mock_frames = [
            b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9',
            b'\xff\xd8' + b'\x00' * 150 + b'\xff\xd9',
        ]
        mock_camera_client.read_frame.side_effect = mock_frames

        stream_gen = stream_service.generate_stream("printer_123")

        # Read first frame
        chunk = await stream_gen.__anext__()
        assert b'--frame' in chunk
        assert b'Content-Type: image/jpeg' in chunk
        assert mock_frames[0] in chunk

    async def test_multiple_concurrent_viewers(self, stream_service):
        """Test multiple viewers can watch same stream."""
        viewer1 = stream_service.add_viewer("printer_123", "viewer_1")
        viewer2 = stream_service.add_viewer("printer_123", "viewer_2")

        assert viewer1 is True
        assert viewer2 is True
        assert stream_service.get_viewer_count("printer_123") == 2

    async def test_max_viewers_limit(self, stream_service):
        """Test maximum viewer limit is enforced."""
        # Add max viewers (default: 5)
        for i in range(5):
            stream_service.add_viewer("printer_123", f"viewer_{i}")

        # Attempt to add 6th viewer
        result = stream_service.add_viewer("printer_123", "viewer_6")
        assert result is False

    async def test_remove_viewer(self, stream_service):
        """Test viewer cleanup."""
        stream_service.add_viewer("printer_123", "viewer_1")
        stream_service.remove_viewer("printer_123", "viewer_1")

        assert stream_service.get_viewer_count("printer_123") == 0

    async def test_stream_cleanup_on_last_viewer(self, stream_service):
        """Test stream is stopped when last viewer disconnects."""
        stream_service.add_viewer("printer_123", "viewer_1")
        stream_service.add_viewer("printer_123", "viewer_2")

        # Remove first viewer - stream continues
        stream_service.remove_viewer("printer_123", "viewer_1")
        assert "printer_123" in stream_service.active_streams

        # Remove last viewer - stream stops
        stream_service.remove_viewer("printer_123", "viewer_2")
        assert "printer_123" not in stream_service.active_streams
```

---

## Integration Testing Requirements

### 1. Camera API Endpoint Tests
**File**: `tests/integration/api/test_camera_endpoints.py`

```python
class TestCameraAPIEndpoints:
    """Integration tests for camera API endpoints."""

    async def test_get_snapshot_endpoint(self, test_client, mock_printer_service):
        """Test GET /api/v1/printers/{id}/camera/snapshot."""
        mock_snapshot = b'\xff\xd8' + b'\x00' * 1000 + b'\xff\xd9'
        mock_printer_service.get_camera_snapshot.return_value = mock_snapshot

        response = await test_client.get("/api/v1/printers/test_printer/camera/snapshot")

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/jpeg"
        assert response.content == mock_snapshot

    async def test_get_snapshot_printer_not_found(self, test_client):
        """Test snapshot endpoint with invalid printer ID."""
        response = await test_client.get("/api/v1/printers/invalid_id/camera/snapshot")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_snapshot_camera_unavailable(self, test_client, mock_printer_service):
        """Test snapshot when camera is unavailable."""
        mock_printer_service.get_camera_snapshot.side_effect = ConnectionError()

        response = await test_client.get("/api/v1/printers/test_printer/camera/snapshot")

        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()

    async def test_get_stream_endpoint(self, test_client, mock_stream_service):
        """Test GET /api/v1/printers/{id}/camera/stream."""
        response = await test_client.get(
            "/api/v1/printers/test_printer/camera/stream",
            stream=True
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "multipart/x-mixed-replace; boundary=frame"

    async def test_stream_concurrent_viewers(self, test_client):
        """Test multiple concurrent stream connections."""
        # Start 3 concurrent streams
        streams = []
        for i in range(3):
            response = await test_client.get(
                "/api/v1/printers/test_printer/camera/stream",
                stream=True
            )
            streams.append(response)

        # All should succeed
        for stream in streams:
            assert stream.status_code == 200

    async def test_stream_max_viewers_exceeded(self, test_client, mock_stream_service):
        """Test stream rejection when max viewers exceeded."""
        mock_stream_service.add_viewer.return_value = False

        response = await test_client.get("/api/v1/printers/test_printer/camera/stream")

        assert response.status_code == 503
        assert "max viewers" in response.json()["detail"].lower()
```

### 2. End-to-End Camera Flow Tests
**File**: `tests/integration/test_camera_e2e.py`

```python
class TestCameraE2E:
    """End-to-end camera flow tests."""

    async def test_snapshot_complete_flow(
        self,
        test_client,
        camera_client,
        snapshot_service,
        printer_service
    ):
        """Test complete snapshot flow from API to camera client."""
        # Setup printer
        await printer_service.connect_printer("test_printer")

        # Request snapshot
        response = await test_client.get("/api/v1/printers/test_printer/camera/snapshot")

        assert response.status_code == 200
        assert len(response.content) > 0

        # Verify JPEG format
        assert response.content.startswith(b'\xff\xd8')
        assert response.content.endswith(b'\xff\xd9')

    async def test_stream_complete_flow(
        self,
        test_client,
        camera_client,
        stream_service,
        printer_service
    ):
        """Test complete stream flow from API to camera client."""
        await printer_service.connect_printer("test_printer")

        # Start stream
        async with test_client.stream(
            "GET",
            "/api/v1/printers/test_printer/camera/stream"
        ) as response:
            assert response.status_code == 200

            # Read first frame
            chunks = []
            async for chunk in response.aiter_bytes():
                chunks.append(chunk)
                if len(chunks) >= 5:  # Read 5 chunks
                    break

            # Verify MJPEG format
            combined = b''.join(chunks)
            assert b'--frame' in combined
            assert b'Content-Type: image/jpeg' in combined

    async def test_reconnection_after_disconnect(
        self,
        test_client,
        camera_client,
        snapshot_service
    ):
        """Test camera reconnects after network interruption."""
        # Take initial snapshot
        response1 = await test_client.get("/api/v1/printers/test_printer/camera/snapshot")
        assert response1.status_code == 200

        # Simulate connection loss
        await camera_client.disconnect()

        # Request snapshot again - should reconnect
        response2 = await test_client.get("/api/v1/printers/test_printer/camera/snapshot")
        assert response2.status_code == 200
```

### 3. Connection Pool Management Tests
**File**: `tests/integration/test_camera_connection_pool.py`

```python
class TestCameraConnectionPool:
    """Test camera connection pooling and management."""

    async def test_connection_reuse(self, snapshot_service):
        """Test same connection is reused for multiple snapshots."""
        snapshot1 = await snapshot_service.get_snapshot("printer_123")
        connection_id1 = id(snapshot_service.active_connections["printer_123"])

        snapshot2 = await snapshot_service.get_snapshot("printer_123")
        connection_id2 = id(snapshot_service.active_connections["printer_123"])

        # Same connection object should be reused
        assert connection_id1 == connection_id2

    async def test_multiple_printer_connections(self, snapshot_service):
        """Test managing connections to multiple printers."""
        await snapshot_service.start_camera("printer_1")
        await snapshot_service.start_camera("printer_2")
        await snapshot_service.start_camera("printer_3")

        assert len(snapshot_service.active_connections) == 3
        assert "printer_1" in snapshot_service.active_connections
        assert "printer_2" in snapshot_service.active_connections
        assert "printer_3" in snapshot_service.active_connections

    async def test_connection_cleanup_on_error(self, snapshot_service, mock_camera_client):
        """Test connection is cleaned up after persistent errors."""
        mock_camera_client.read_frame.side_effect = ConnectionError()

        # Multiple failed attempts
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await snapshot_service.get_snapshot("printer_123")

        # Connection should be removed from pool
        assert "printer_123" not in snapshot_service.active_connections
```

---

## Manual Testing Checklist

### Phase 1: Basic Connectivity Tests

#### Camera Connection Tests
- [ ] **Test 1.1**: Connect to Bambu Lab A1 printer camera on port 6000
  - Expected: TLS connection established successfully
  - Verify: Check logs for successful connection

- [ ] **Test 1.2**: Verify SNI is set to printer serial number
  - Expected: TLS handshake succeeds with correct SNI
  - Verify: Network capture shows correct SNI in TLS ClientHello

- [ ] **Test 1.3**: Test authentication with correct access code
  - Expected: 80-byte auth packet sent, connection accepted
  - Verify: No authentication error in logs

- [ ] **Test 1.4**: Test authentication with incorrect access code
  - Expected: Authentication failure, connection closed
  - Verify: Error logged with "authentication failed"

- [ ] **Test 1.5**: Test connection timeout
  - Expected: Connection attempt times out after 10 seconds
  - Verify: Timeout error logged, no hanging connections

#### Frame Reception Tests
- [ ] **Test 2.1**: Receive single JPEG frame
  - Expected: Complete JPEG image received (FF D8 ... FF D9)
  - Verify: Frame size matches header, valid JPEG markers

- [ ] **Test 2.2**: Receive 100 consecutive frames
  - Expected: All frames received successfully
  - Verify: No dropped frames, consistent frame rate

- [ ] **Test 2.3**: Verify frame resolution
  - Expected: 1280x720 JPEG images
  - Verify: Decode JPEG and check dimensions

- [ ] **Test 2.4**: Test frame reassembly from chunks
  - Expected: Large frames reassembled correctly from 4KB chunks
  - Verify: Complete JPEG files after reassembly

### Phase 2: Snapshot API Tests

#### Snapshot Endpoint Tests
- [ ] **Test 3.1**: GET /api/v1/printers/{id}/camera/snapshot
  - Expected: HTTP 200, Content-Type: image/jpeg
  - Verify: Valid JPEG image returned

- [ ] **Test 3.2**: Snapshot with printer offline
  - Expected: HTTP 503, error message
  - Verify: "Camera unavailable" in response

- [ ] **Test 3.3**: Snapshot with invalid printer ID
  - Expected: HTTP 404, "Printer not found"
  - Verify: Proper error response

- [ ] **Test 3.4**: Multiple rapid snapshot requests
  - Expected: Cached snapshot returned within TTL
  - Verify: Same image returned, no multiple camera reads

- [ ] **Test 3.5**: Snapshot after cache expiration
  - Expected: Fresh snapshot fetched after 5 seconds
  - Verify: New frame retrieved from camera

### Phase 3: Live Stream Tests

#### Stream Endpoint Tests
- [ ] **Test 4.1**: GET /api/v1/printers/{id}/camera/stream
  - Expected: HTTP 200, MJPEG stream starts
  - Verify: Content-Type: multipart/x-mixed-replace

- [ ] **Test 4.2**: Display stream in browser (Chrome)
  - Expected: Live video feed displays in <img> tag
  - Verify: Smooth playback, minimal lag

- [ ] **Test 4.3**: Display stream in browser (Firefox)
  - Expected: Live video feed displays
  - Verify: Cross-browser compatibility

- [ ] **Test 4.4**: Display stream in browser (Safari)
  - Expected: Live video feed displays
  - Verify: Safari MJPEG support works

- [ ] **Test 4.5**: Mobile browser test (iOS Safari)
  - Expected: Stream displays on mobile
  - Verify: Responsive, acceptable performance

- [ ] **Test 4.6**: Mobile browser test (Android Chrome)
  - Expected: Stream displays on mobile
  - Verify: Performance acceptable

#### Concurrent Viewer Tests
- [ ] **Test 5.1**: Open 2 concurrent viewers
  - Expected: Both streams work simultaneously
  - Verify: No frame drops, synchronized

- [ ] **Test 5.2**: Open 5 concurrent viewers (max limit)
  - Expected: All 5 streams work
  - Verify: Performance acceptable

- [ ] **Test 5.3**: Attempt 6th viewer (exceed limit)
  - Expected: HTTP 503, "Max viewers reached"
  - Verify: Existing streams unaffected

- [ ] **Test 5.4**: Close viewer, reopen immediately
  - Expected: New connection succeeds
  - Verify: Viewer count properly updated

### Phase 4: Error Handling Tests

#### Connection Error Tests
- [ ] **Test 6.1**: Disconnect printer during stream
  - Expected: Stream ends gracefully, error displayed
  - Verify: No frontend crash, error message shown

- [ ] **Test 6.2**: Network interruption during snapshot
  - Expected: Reconnection attempted, snapshot retried
  - Verify: Exponential backoff used

- [ ] **Test 6.3**: Printer power off during active stream
  - Expected: Stream stops, "Camera unavailable" message
  - Verify: Connection cleaned up

- [ ] **Test 6.4**: Printer restart during monitoring
  - Expected: Reconnection succeeds after printer boots
  - Verify: Stream resumes automatically

#### Resource Cleanup Tests
- [ ] **Test 7.1**: Idle connection timeout (10 minutes)
  - Expected: Unused connections closed
  - Verify: Resources freed, no memory leaks

- [ ] **Test 7.2**: All viewers close stream
  - Expected: Camera connection closed after last viewer
  - Verify: Connection pool updated

- [ ] **Test 7.3**: Application shutdown with active streams
  - Expected: All connections gracefully closed
  - Verify: No hanging sockets, clean shutdown

### Phase 5: Performance Tests

#### Latency Tests
- [ ] **Test 8.1**: Snapshot request latency
  - Expected: < 2 seconds from request to response
  - Verify: Measure with browser dev tools

- [ ] **Test 8.2**: Stream frame latency
  - Expected: < 500ms per frame delivery
  - Verify: Compare timestamp on printer vs. browser

- [ ] **Test 8.3**: Cache hit latency
  - Expected: < 100ms for cached snapshots
  - Verify: Second request much faster than first

#### Throughput Tests
- [ ] **Test 9.1**: Stream frame rate
  - Expected: 10-15 FPS sustained
  - Verify: Count frames received per second

- [ ] **Test 9.2**: Multiple printer streams simultaneously
  - Expected: 3 printers streaming without degradation
  - Verify: All streams maintain acceptable FPS

#### Resource Usage Tests
- [ ] **Test 10.1**: CPU usage during single stream
  - Expected: < 10% CPU increase
  - Verify: Monitor system resources

- [ ] **Test 10.2**: Memory usage over 1 hour
  - Expected: Stable, no memory leaks
  - Verify: Memory usage doesn't grow continuously

- [ ] **Test 10.3**: Network bandwidth usage
  - Expected: ~500 KB/s per stream
  - Verify: Monitor network traffic

### Phase 6: Security Tests

#### Authentication Tests
- [ ] **Test 11.1**: Access without authentication
  - Expected: Camera endpoints require valid printer access
  - Verify: Unauthorized access denied

- [ ] **Test 11.2**: TLS encryption verification
  - Expected: All camera traffic encrypted
  - Verify: Network capture shows encrypted packets

- [ ] **Test 11.3**: Access code validation
  - Expected: Invalid codes rejected
  - Verify: Error logged, connection closed

#### API Security Tests
- [ ] **Test 12.1**: CORS headers on camera endpoints
  - Expected: Proper CORS headers set
  - Verify: Browser allows cross-origin requests

- [ ] **Test 12.2**: CSP headers allow camera content
  - Expected: CSP permits camera streams
  - Verify: No CSP violations in browser console

### Phase 7: Edge Cases

#### Network Condition Tests
- [ ] **Test 13.1**: Slow network (simulate with throttling)
  - Expected: Graceful degradation, longer latency
  - Verify: No crashes, acceptable UX

- [ ] **Test 13.2**: Packet loss (10% loss rate)
  - Expected: Frame reassembly handles missing chunks
  - Verify: Retries occur, eventual success

- [ ] **Test 13.3**: High latency network (500ms RTT)
  - Expected: Delayed frames but functional stream
  - Verify: Buffering if needed

#### Printer State Tests
- [ ] **Test 14.1**: Camera access during active print
  - Expected: Stream works while printing
  - Verify: No interference with print job

- [ ] **Test 14.2**: Camera access while idle
  - Expected: Stream shows idle printer
  - Verify: Camera still functional

- [ ] **Test 14.3**: Camera access during firmware update
  - Expected: Camera unavailable during update
  - Verify: Graceful error message

---

## Test Data and Fixtures

### 1. Mock TLS Socket
**File**: `tests/fixtures/mock_tls_socket.py`

```python
import asyncio
from unittest.mock import AsyncMock, MagicMock

class MockTLSSocket:
    """Mock TLS socket for testing camera client."""

    def __init__(self, frames=None):
        self.frames = frames or []
        self.frame_index = 0
        self.connected = False
        self.sent_data = []

    async def connect(self, address):
        """Mock connection."""
        self.connected = True
        self.address = address

    async def send(self, data):
        """Mock send."""
        self.sent_data.append(data)
        return len(data)

    async def recv(self, buffer_size):
        """Mock receive - returns pre-configured frames."""
        if self.frame_index >= len(self.frames):
            raise ConnectionResetError("No more frames")

        frame = self.frames[self.frame_index]
        self.frame_index += 1
        return frame

    async def close(self):
        """Mock close."""
        self.connected = False

@pytest.fixture
def mock_socket():
    """Fixture providing mock TLS socket."""
    return MockTLSSocket()

@pytest.fixture
def mock_socket_with_frames():
    """Fixture providing mock socket with sample JPEG frames."""
    frames = [
        # Frame 1 header
        struct.pack('<I', 1024) + b'\x00' * 12,
        # Frame 1 data
        b'\xff\xd8' + b'\x00' * 1020 + b'\xff\xd9',
        # Frame 2 header
        struct.pack('<I', 2048) + b'\x00' * 12,
        # Frame 2 data (chunked)
        b'\xff\xd8' + b'\x00' * 2040,
        b'\xff\xd9',
    ]
    return MockTLSSocket(frames=frames)
```

### 2. Sample JPEG Frames
**File**: `tests/fixtures/sample_frames.py`

```python
import io
from PIL import Image

def create_test_jpeg(width=1280, height=720, color=(128, 128, 128)):
    """Create a test JPEG image."""
    img = Image.new('RGB', (width, height), color)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()

@pytest.fixture
def sample_jpeg_frame():
    """Fixture providing sample JPEG frame."""
    return create_test_jpeg()

@pytest.fixture
def sample_jpeg_frames():
    """Fixture providing multiple sample JPEG frames with different colors."""
    return [
        create_test_jpeg(color=(255, 0, 0)),    # Red
        create_test_jpeg(color=(0, 255, 0)),    # Green
        create_test_jpeg(color=(0, 0, 255)),    # Blue
        create_test_jpeg(color=(255, 255, 0)),  # Yellow
    ]
```

### 3. Mock Camera Client
**File**: `tests/fixtures/mock_camera_client.py`

```python
class MockBambuCameraClient:
    """Mock camera client for testing services."""

    def __init__(self, frames=None):
        self.frames = frames or []
        self.frame_index = 0
        self.is_connected = False
        self.auth_calls = 0

    async def connect(self):
        """Mock connect."""
        self.is_connected = True
        return True

    async def disconnect(self):
        """Mock disconnect."""
        self.is_connected = False

    async def authenticate(self):
        """Mock authenticate."""
        self.auth_calls += 1
        return True

    async def read_frame(self):
        """Mock read frame - returns pre-configured frames."""
        if not self.frames:
            return create_test_jpeg()

        if self.frame_index >= len(self.frames):
            self.frame_index = 0  # Loop frames

        frame = self.frames[self.frame_index]
        self.frame_index += 1
        return frame

    async def is_alive(self):
        """Mock is_alive check."""
        return self.is_connected

@pytest.fixture
def mock_camera_client(sample_jpeg_frames):
    """Fixture providing mock camera client."""
    return MockBambuCameraClient(frames=sample_jpeg_frames)
```

### 4. Printer Service Mock
**File**: `tests/fixtures/mock_printer_service.py`

```python
@pytest.fixture
def mock_printer_service(mock_camera_client):
    """Mock printer service with camera support."""
    service = AsyncMock()
    service.get_printer_driver.return_value = MagicMock(
        camera_client=mock_camera_client,
        ip_address="192.168.1.100",
        access_code="12345678",
        serial_number="ABC123"
    )
    return service
```

### 5. Test Configuration
**File**: `tests/fixtures/test_config.py`

```python
@pytest.fixture
def camera_test_config():
    """Configuration for camera tests."""
    return {
        "camera": {
            "snapshot_cache_ttl": 5,
            "connection_timeout": 10,
            "max_viewers_per_printer": 5,
            "frame_chunk_size": 4096,
            "reconnect_delay": 1,
            "max_reconnect_attempts": 3,
        },
        "test_printer": {
            "ip_address": "192.168.1.100",
            "access_code": "12345678",
            "serial_number": "ABC123",
        }
    }
```

---

## Success Criteria Verification

### MVP Success Criteria Verification

#### Criterion 1: Authenticate to Bambu Lab A1 Camera
**Verification Method:**
```python
async def verify_authentication_mvp():
    """Verify MVP criterion: successful authentication."""
    client = BambuLabCameraClient("192.168.1.100", "12345678", "ABC123")

    # Test connection
    connected = await client.connect()
    assert connected, "Failed to connect to camera"

    # Test authentication
    authenticated = await client.authenticate()
    assert authenticated, "Failed to authenticate to camera"

    # Verify connection is alive
    alive = await client.is_alive()
    assert alive, "Connection not alive after authentication"

    await client.disconnect()
    return True
```

**Success Metrics:**
- Connection established: YES/NO
- Authentication packet sent: YES/NO
- No authentication errors: YES/NO

#### Criterion 2: Retrieve Single Snapshot via API
**Verification Method:**
```python
async def verify_snapshot_api_mvp(test_client):
    """Verify MVP criterion: snapshot API works."""
    response = await test_client.get("/api/v1/printers/test_printer/camera/snapshot")

    assert response.status_code == 200, "Snapshot endpoint failed"
    assert response.headers["Content-Type"] == "image/jpeg", "Wrong content type"

    # Verify valid JPEG
    assert response.content.startswith(b'\xff\xd8'), "Invalid JPEG start marker"
    assert response.content.endswith(b'\xff\xd9'), "Invalid JPEG end marker"
    assert len(response.content) > 1000, "JPEG too small"

    return True
```

**Success Metrics:**
- HTTP 200 response: YES/NO
- Valid JPEG returned: YES/NO
- Correct content-type header: YES/NO

#### Criterion 3: Display Snapshot in Frontend
**Verification Method:** (Manual)
```markdown
1. Open Printernizer web UI
2. Navigate to printer card with Bambu Lab A1
3. Click "View Camera" or snapshot button
4. Verify:
   - [ ] Snapshot loads within 2 seconds
   - [ ] Image displays correctly
   - [ ] No browser console errors
   - [ ] Refresh button works
```

**Success Metrics:**
- Image displays: YES/NO
- Load time < 2s: YES/NO
- No errors: YES/NO

#### Criterion 4: Handle Connection Errors Gracefully
**Verification Method:**
```python
async def verify_error_handling_mvp(test_client, mock_printer_service):
    """Verify MVP criterion: error handling works."""
    # Test 1: Printer offline
    mock_printer_service.get_camera_snapshot.side_effect = ConnectionError()
    response = await test_client.get("/api/v1/printers/test_printer/camera/snapshot")
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()

    # Test 2: Invalid printer
    response = await test_client.get("/api/v1/printers/invalid/camera/snapshot")
    assert response.status_code == 404

    # Test 3: Authentication failure
    mock_printer_service.get_camera_snapshot.side_effect = PermissionError()
    response = await test_client.get("/api/v1/printers/test_printer/camera/snapshot")
    assert response.status_code == 403

    return True
```

**Success Metrics:**
- Proper HTTP error codes: YES/NO
- Descriptive error messages: YES/NO
- No crashes: YES/NO

#### Criterion 5: Documentation for Troubleshooting
**Verification Method:** (Manual)
```markdown
1. Check docs/BAMBU_LAB_CAMERA_TROUBLESHOOTING.md exists
2. Verify documentation includes:
   - [ ] Common error messages and solutions
   - [ ] Network requirements (port 6000, TLS)
   - [ ] Access code configuration
   - [ ] Connection troubleshooting steps
   - [ ] Performance tuning guidance
```

**Success Metrics:**
- Documentation exists: YES/NO
- Covers common issues: YES/NO
- Clear troubleshooting steps: YES/NO

### Full Feature Set Verification

#### Criterion 1: Live MJPEG Stream in Browser
**Verification Method:**
```python
async def verify_live_stream(test_client):
    """Verify live stream criterion."""
    async with test_client.stream(
        "GET",
        "/api/v1/printers/test_printer/camera/stream"
    ) as response:
        assert response.status_code == 200
        assert "multipart/x-mixed-replace" in response.headers["Content-Type"]

        # Collect frames for 10 seconds
        start_time = time.time()
        frame_count = 0

        async for chunk in response.aiter_bytes():
            if b'--frame' in chunk:
                frame_count += 1

            if time.time() - start_time > 10:
                break

        # Should receive at least 80 frames in 10s (8 FPS minimum)
        assert frame_count >= 80, f"Too few frames: {frame_count}"

        return True
```

**Success Metrics:**
- Stream starts: YES/NO
- Frame rate ≥ 8 FPS: YES/NO
- MJPEG format correct: YES/NO

#### Criterion 2: Multiple Concurrent Viewers
**Verification Method:**
```python
async def verify_concurrent_viewers(test_client):
    """Verify concurrent viewer criterion."""
    streams = []

    # Start 5 concurrent streams
    for i in range(5):
        response = await test_client.get(
            "/api/v1/printers/test_printer/camera/stream",
            stream=True
        )
        assert response.status_code == 200
        streams.append(response)

    # All streams should be active
    assert len(streams) == 5

    # Clean up
    for stream in streams:
        await stream.aclose()

    return True
```

**Success Metrics:**
- 5 viewers supported: YES/NO
- No performance degradation: YES/NO
- All streams synchronized: YES/NO

#### Criterion 3: Automatic Reconnection
**Verification Method:**
```python
async def verify_auto_reconnection(camera_client):
    """Verify automatic reconnection criterion."""
    # Initial connection
    await camera_client.connect()
    assert camera_client.is_connected

    # Simulate connection loss
    camera_client.socket.close()

    # Attempt to read frame - should trigger reconnection
    try:
        frame = await camera_client.read_frame()
        assert frame is not None, "Failed to get frame after reconnection"
    except Exception as e:
        pytest.fail(f"Reconnection failed: {e}")

    assert camera_client.is_connected, "Not reconnected"
    return True
```

**Success Metrics:**
- Reconnection triggered: YES/NO
- Reconnection succeeds: YES/NO
- Exponential backoff used: YES/NO

#### Criterion 4: Latency < 2 Seconds
**Verification Method:**
```python
async def verify_latency(test_client):
    """Verify latency criterion."""
    # Test snapshot latency
    start = time.time()
    response = await test_client.get("/api/v1/printers/test_printer/camera/snapshot")
    snapshot_latency = time.time() - start

    assert response.status_code == 200
    assert snapshot_latency < 2.0, f"Snapshot latency too high: {snapshot_latency}s"

    # Test stream frame latency
    async with test_client.stream(
        "GET",
        "/api/v1/printers/test_printer/camera/stream"
    ) as stream_response:
        frame_times = []

        async for chunk in stream_response.aiter_bytes():
            if b'--frame' in chunk:
                frame_times.append(time.time())
                if len(frame_times) >= 10:
                    break

        # Calculate average inter-frame delay
        delays = [frame_times[i+1] - frame_times[i] for i in range(len(frame_times)-1)]
        avg_delay = sum(delays) / len(delays)

        assert avg_delay < 0.5, f"Frame delay too high: {avg_delay}s"

    return True
```

**Success Metrics:**
- Snapshot latency < 2s: YES/NO
- Stream frame delay < 500ms: YES/NO
- Consistent performance: YES/NO

#### Criterion 5: Stable for 24+ Hours
**Verification Method:**
```python
async def verify_stability_24h():
    """Verify 24-hour stability criterion (long-running test)."""
    start_time = time.time()
    duration = 24 * 60 * 60  # 24 hours

    error_count = 0
    frame_count = 0

    camera_client = BambuLabCameraClient("192.168.1.100", "12345678", "ABC123")
    await camera_client.connect()

    while time.time() - start_time < duration:
        try:
            frame = await camera_client.read_frame()
            frame_count += 1

            # Log progress every hour
            if frame_count % (3600 * 10) == 0:  # ~10 FPS * 3600s
                hours_elapsed = (time.time() - start_time) / 3600
                logger.info(f"Stability test: {hours_elapsed:.1f}h elapsed, "
                          f"{frame_count} frames, {error_count} errors")

        except Exception as e:
            error_count += 1
            logger.error(f"Frame error: {e}")

            # Allow up to 1% error rate
            error_rate = error_count / max(frame_count, 1)
            if error_rate > 0.01:
                pytest.fail(f"Error rate too high: {error_rate*100:.2f}%")

    await camera_client.disconnect()

    # Final verification
    total_hours = (time.time() - start_time) / 3600
    error_rate = error_count / max(frame_count, 1)

    assert total_hours >= 24, f"Test ended early: {total_hours:.1f}h"
    assert error_rate < 0.01, f"Error rate too high: {error_rate*100:.2f}%"

    return True
```

**Success Metrics:**
- Runs for 24+ hours: YES/NO
- Error rate < 1%: YES/NO
- No memory leaks: YES/NO

#### Criterion 6: Performance Monitoring
**Verification Method:**
```python
async def verify_performance_monitoring(monitoring_service):
    """Verify performance monitoring criterion."""
    # Check metrics are collected
    metrics = monitoring_service.get_camera_metrics("test_printer")

    assert "snapshot_latency" in metrics
    assert "stream_frame_rate" in metrics
    assert "active_viewers" in metrics
    assert "connection_errors" in metrics

    # Verify metrics are reasonable
    assert metrics["snapshot_latency"] < 2000  # ms
    assert metrics["stream_frame_rate"] > 8    # FPS
    assert metrics["active_viewers"] >= 0

    return True
```

**Success Metrics:**
- Metrics collected: YES/NO
- Metrics exported: YES/NO
- Alerting configured: YES/NO

---

## Test Environment Setup

### Development Environment

#### Prerequisites
```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock
pip install pillow  # For JPEG generation in tests
```

#### Mock Environment (No Real Printer)
```yaml
# tests/config/test_config.yaml
camera:
  use_mock: true
  mock_frame_rate: 10
  mock_resolution: [1280, 720]

printers:
  - id: test_printer
    type: bambu_lab
    ip_address: "127.0.0.1"
    access_code: "mock_code"
    serial_number: "MOCK123"
```

#### Running Tests (Mock)
```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with coverage
pytest --cov=src/services/camera tests/

# Run specific test file
pytest tests/unit/services/test_bambu_camera_client.py -v
```

### Testing with Real Bambu Lab Printer

#### Hardware Setup
```markdown
1. Bambu Lab A1 printer connected to network
2. Printer IP address: 192.168.1.100 (example)
3. Access code configured on printer LCD
4. Serial number noted from printer settings
5. Printer on same network as test machine
```

#### Network Configuration
```bash
# Verify printer is reachable
ping 192.168.1.100

# Check port 6000 is accessible
nc -zv 192.168.1.100 6000

# Optional: Capture TLS handshake
tcpdump -i en0 -w bambu_camera.pcap host 192.168.1.100 and port 6000
```

#### Real Printer Test Configuration
```yaml
# tests/config/real_printer_config.yaml
camera:
  use_mock: false

printers:
  - id: real_bambu_a1
    type: bambu_lab
    ip_address: "192.168.1.100"  # Your printer IP
    access_code: "12345678"       # Your access code
    serial_number: "ABC123XYZ"    # Your serial number
```

#### Running Tests (Real Printer)
```bash
# Set environment variable to use real printer
export USE_REAL_PRINTER=true
export PRINTER_IP=192.168.1.100
export PRINTER_ACCESS_CODE=12345678
export PRINTER_SERIAL=ABC123XYZ

# Run integration tests with real printer
pytest tests/integration/ --real-printer -v

# Run camera-specific tests
pytest tests/integration/test_camera_e2e.py --real-printer -v

# Run with verbose logging
pytest tests/ --real-printer -v --log-cli-level=DEBUG
```

### Continuous Integration Environment

#### GitHub Actions Workflow
```yaml
# .github/workflows/camera-tests.yml
name: Camera Tests

on:
  push:
    paths:
      - 'src/services/bambu_camera_client.py'
      - 'src/services/camera_*.py'
      - 'tests/**'
  pull_request:
    paths:
      - 'src/services/bambu_camera_client.py'
      - 'src/services/camera_*.py'
      - 'tests/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src/services/camera

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run integration tests (mock)
        run: pytest tests/integration/ -v --mock-printer
```

---

## Performance Testing

### Load Testing Strategy

#### Test Scenarios

**Scenario 1: Snapshot Load Test**
```python
# tests/performance/test_snapshot_load.py
import asyncio
import time
from locust import HttpUser, task, between

class SnapshotLoadTest(HttpUser):
    """Load test for snapshot endpoint."""
    wait_time = between(1, 3)

    @task
    def get_snapshot(self):
        """Repeatedly request snapshots."""
        with self.client.get(
            "/api/v1/printers/test_printer/camera/snapshot",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Verify JPEG format
                if response.content.startswith(b'\xff\xd8'):
                    response.success()
                else:
                    response.failure("Invalid JPEG")
            else:
                response.failure(f"HTTP {response.status_code}")

# Run with: locust -f tests/performance/test_snapshot_load.py
```

**Expected Results:**
- 100 users: < 2s response time (95th percentile)
- 500 users: < 5s response time (95th percentile)
- No errors at 100 concurrent users

**Scenario 2: Stream Load Test**
```python
# tests/performance/test_stream_load.py
class StreamLoadTest(HttpUser):
    """Load test for stream endpoint."""
    wait_time = between(10, 30)

    @task
    def watch_stream(self):
        """Watch stream for 30 seconds."""
        with self.client.get(
            "/api/v1/printers/test_printer/camera/stream",
            stream=True,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                start_time = time.time()
                frame_count = 0

                for chunk in response.iter_content(chunk_size=4096):
                    if b'--frame' in chunk:
                        frame_count += 1

                    # Watch for 30 seconds
                    if time.time() - start_time > 30:
                        break

                # Should get at least 240 frames in 30s (8 FPS)
                if frame_count >= 240:
                    response.success()
                else:
                    response.failure(f"Low frame rate: {frame_count/30} FPS")
            else:
                response.failure(f"HTTP {response.status_code}")
```

**Expected Results:**
- 5 concurrent viewers per printer: stable
- 10 viewers across 2 printers: stable
- Frame rate maintained ≥ 8 FPS

### Benchmark Tests

#### Snapshot Latency Benchmark
```python
# tests/performance/benchmark_snapshot.py
import pytest
import time

@pytest.mark.benchmark
async def test_snapshot_latency(benchmark, test_client):
    """Benchmark snapshot latency."""

    async def get_snapshot():
        response = await test_client.get("/api/v1/printers/test_printer/camera/snapshot")
        assert response.status_code == 200
        return response

    result = benchmark(get_snapshot)

    # Assert performance requirements
    assert result.stats.mean < 2.0  # Mean < 2s
    assert result.stats.max < 5.0   # Max < 5s
```

#### Frame Processing Benchmark
```python
@pytest.mark.benchmark
def test_frame_parsing_performance(benchmark, sample_jpeg_frame):
    """Benchmark frame parsing performance."""

    def parse_frame():
        # Simulate frame parsing
        header = sample_jpeg_frame[:16]
        payload_size = struct.unpack('<I', header[:4])[0]
        jpeg_data = sample_jpeg_frame[16:16+payload_size]

        # Validate JPEG markers
        assert jpeg_data.startswith(b'\xff\xd8')
        assert jpeg_data.endswith(b'\xff\xd9')

        return jpeg_data

    result = benchmark(parse_frame)

    # Should parse frames very quickly
    assert result.stats.mean < 0.001  # Mean < 1ms
```

### Resource Usage Testing

#### Memory Leak Test
```python
# tests/performance/test_memory_leak.py
import tracemalloc
import gc

@pytest.mark.slow
async def test_camera_memory_leak():
    """Test for memory leaks in camera service over 1 hour."""
    tracemalloc.start()

    camera_client = BambuLabCameraClient("192.168.1.100", "12345678", "ABC123")
    await camera_client.connect()

    # Baseline memory
    gc.collect()
    snapshot1 = tracemalloc.take_snapshot()

    # Run for 1 hour
    start_time = time.time()
    frame_count = 0

    while time.time() - start_time < 3600:
        frame = await camera_client.read_frame()
        frame_count += 1

        # Periodically check memory
        if frame_count % 1000 == 0:
            gc.collect()
            snapshot2 = tracemalloc.take_snapshot()

            # Compare memory usage
            top_stats = snapshot2.compare_to(snapshot1, 'lineno')
            total_diff = sum(stat.size_diff for stat in top_stats)

            # Memory should not grow significantly (< 10 MB per 1000 frames)
            assert total_diff < 10 * 1024 * 1024, f"Memory leak detected: {total_diff / (1024*1024):.2f} MB"

    await camera_client.disconnect()
    tracemalloc.stop()
```

---

## Security Testing

### TLS Security Tests

#### Certificate Validation Test
```python
# tests/security/test_tls_security.py
import ssl

async def test_tls_certificate_validation():
    """Verify TLS certificate is properly validated."""
    client = BambuLabCameraClient("192.168.1.100", "12345678", "ABC123")

    # Check SSL context configuration
    ssl_context = client._create_ssl_context()

    # Verify Bambu CA is loaded
    assert ssl_context.check_hostname is False  # Bambu uses self-signed
    assert ssl_context.verify_mode == ssl.CERT_NONE  # Or CERT_REQUIRED with CA

    # Verify SNI is set correctly
    # (SNI is set during connection, check in connection test)
```

#### Access Code Protection Test
```python
async def test_access_code_not_logged():
    """Verify access code is not logged in plaintext."""
    with LogCapture() as logs:
        client = BambuLabCameraClient("192.168.1.100", "secret123", "ABC123")
        await client.connect()

    # Check logs don't contain access code
    log_text = '\n'.join([str(record) for record in logs.records])
    assert "secret123" not in log_text, "Access code leaked in logs"
```

### Authentication Security Tests

#### Invalid Access Code Test
```python
async def test_invalid_access_code_rejected():
    """Verify invalid access codes are rejected."""
    client = BambuLabCameraClient("192.168.1.100", "wrong_code", "ABC123")

    with pytest.raises(PermissionError):
        await client.connect()
        await client.authenticate()
```

#### Brute Force Protection Test
```python
async def test_brute_force_protection():
    """Verify rate limiting on authentication attempts."""
    # Attempt multiple failed authentications
    for i in range(10):
        client = BambuLabCameraClient("192.168.1.100", f"wrong_{i}", "ABC123")

        with pytest.raises(PermissionError):
            await client.connect()
            await client.authenticate()

    # Should be rate limited or blocked after multiple failures
    # (Implementation-dependent)
```

### API Security Tests

#### Unauthorized Access Test
```python
async def test_unauthorized_camera_access(test_client):
    """Verify camera endpoints require authentication."""
    # Attempt access without valid printer credentials
    response = await test_client.get(
        "/api/v1/printers/unknown_printer/camera/snapshot"
    )

    assert response.status_code in [401, 404]
```

#### CORS Security Test
```python
async def test_cors_headers(test_client):
    """Verify CORS headers are properly configured."""
    response = await test_client.options(
        "/api/v1/printers/test_printer/camera/snapshot",
        headers={"Origin": "http://malicious-site.com"}
    )

    # Should have proper CORS restrictions
    if "Access-Control-Allow-Origin" in response.headers:
        # If CORS is allowed, should not be wildcard
        assert response.headers["Access-Control-Allow-Origin"] != "*"
```

---

## CI/CD Integration

### Automated Test Pipeline

#### Test Stages
```yaml
stages:
  - lint
  - unit-test
  - integration-test
  - performance-test
  - security-test
  - deployment-test

# Stage 1: Code Quality
lint:
  stage: lint
  script:
    - flake8 src/services/camera_*.py
    - mypy src/services/camera_*.py
    - black --check src/services/camera_*.py

# Stage 2: Unit Tests
unit-test:
  stage: unit-test
  script:
    - pytest tests/unit/ -v --cov=src/services/camera --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

# Stage 3: Integration Tests
integration-test:
  stage: integration-test
  script:
    - pytest tests/integration/ -v --mock-printer

# Stage 4: Performance Tests
performance-test:
  stage: performance-test
  script:
    - pytest tests/performance/ -v --benchmark-only
  artifacts:
    paths:
      - benchmark-results.json

# Stage 5: Security Tests
security-test:
  stage: security-test
  script:
    - bandit -r src/services/camera_*.py
    - safety check -r requirements.txt

# Stage 6: Deployment Test
deployment-test:
  stage: deployment-test
  script:
    - docker build -t printernizer-camera-test .
    - docker run --rm printernizer-camera-test pytest tests/integration/
```

### Quality Gates

#### Coverage Requirements
```yaml
# .coveragerc
[run]
source = src/services/camera

[report]
fail_under = 80
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

#### Performance Requirements
```yaml
# pytest.ini
[pytest]
markers =
    benchmark: performance benchmark tests
    slow: tests that take > 1 minute

benchmark:
  max_time: 2.0  # seconds
```

### Test Result Reporting

#### Test Report Template
```markdown
# Camera Feature Test Report

**Date**: {date}
**Version**: {version}
**Environment**: {environment}

## Test Summary
- Total Tests: {total}
- Passed: {passed}
- Failed: {failed}
- Skipped: {skipped}
- Coverage: {coverage}%

## Unit Tests
- BambuLabCameraClient: {client_tests} passed
- CameraSnapshotService: {snapshot_tests} passed
- CameraStreamService: {stream_tests} passed

## Integration Tests
- API Endpoints: {api_tests} passed
- E2E Flows: {e2e_tests} passed
- Connection Pool: {pool_tests} passed

## Performance Tests
- Snapshot Latency: {snapshot_latency}ms (target: < 2000ms)
- Stream Frame Rate: {frame_rate} FPS (target: > 8 FPS)
- Memory Usage: {memory_mb} MB stable

## Security Tests
- TLS Validation: {tls_result}
- Authentication: {auth_result}
- API Security: {api_security_result}

## Issues Found
{issues_list}

## Recommendations
{recommendations_list}
```

---

## Test Execution Summary

### Quick Test Commands

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run with real printer
pytest tests/ --real-printer -v

# Run performance tests
pytest tests/performance/ --benchmark-only

# Run security tests
pytest tests/security/ -v

# Generate coverage report
pytest tests/ --cov=src/services/camera --cov-report=html

# Run specific test file
pytest tests/unit/services/test_bambu_camera_client.py -v

# Run tests matching pattern
pytest tests/ -k "snapshot" -v
```

### Test Execution Schedule

**During Development:**
- Unit tests: Every commit
- Integration tests: Every PR
- Performance tests: Weekly
- Security tests: Every release

**Before Release:**
- Full test suite
- 24-hour stability test
- Real printer validation
- Load testing

**Post-Release:**
- Smoke tests
- Performance monitoring
- Error rate tracking

---

## Appendices

### A. Common Test Issues and Solutions

**Issue**: Mock TLS connection fails
**Solution**: Ensure `mock_ssl_context` fixture is properly configured

**Issue**: JPEG validation fails
**Solution**: Check for correct start (FF D8) and end (FF D9) markers

**Issue**: Stream test hangs
**Solution**: Use `asyncio.wait_for()` with timeout

**Issue**: Performance test fails on CI
**Solution**: Adjust thresholds for CI environment (slower hardware)

### B. Test Data Generation Scripts

See `tests/fixtures/` directory for:
- `generate_sample_frames.py` - Create test JPEG images
- `mock_camera_server.py` - Mock TCP camera server for testing
- `load_test_data.py` - Load test data generator

### C. Debugging Test Failures

```bash
# Run with verbose logging
pytest tests/ -v --log-cli-level=DEBUG

# Run with pdb on failure
pytest tests/ --pdb

# Run single test with full output
pytest tests/unit/services/test_bambu_camera_client.py::test_connect_success -vv -s

# Capture all logs
pytest tests/ -v --log-file=test.log --log-file-level=DEBUG
```

---

**Document Version**: 1.0
**Last Updated**: November 14, 2025
**Next Review**: After Phase 1 implementation
