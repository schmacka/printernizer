"""
Bambu Lab Camera Client.

Handles TCP/TLS connection to Bambu Lab A1/P1 series cameras using the proprietary
camera protocol. Supports authentication, frame parsing, and JPEG frame retrieval.

Protocol Specification:
- Port: 6000 (TCP with TLS)
- Authentication: 80-byte binary packet
- Frame Format: 16-byte header + JPEG payload
- Images: 1280x720 JPEG (FF D8 ... FF D9)

References:
- https://github.com/Doridian/OpenBambuAPI/blob/main/video.md
- https://github.com/greghesp/ha-bambulab
"""

import asyncio
import ssl
import struct
from typing import Optional, Tuple
from datetime import datetime

import structlog

from src.config.constants import RetrySettings
from src.constants import PortConstants, CameraConstants
from src.utils.exceptions import PrinterConnectionError


logger = structlog.get_logger(__name__)


# Bambu Lab CA Certificate (from BambuStudio resources/cert/printer.cer)
BAMBU_CA_CERT = """-----BEGIN CERTIFICATE-----
MIIDZTCCAk2gAwIBAgIUV1FckwXElyek1onFnQ9kL7Bk4N8wDQYJKoZIhvcNAQEL
BQAwQjELMAkGA1UEBhMCQ04xIjAgBgNVBAoMGUJCTCBUZWNobm9sb2dpZXMgQ28u
LCBMdGQxDzANBgNVBAMMBkJCTCBDQTAeFw0yMjA0MDQwMzQyMTFaFw0zMjA0MDEw
MzQyMTFaMEIxCzAJBgNVBAYTAkNOMSIwIAYDVQQKDBlCQkwgVGVjaG5vbG9naWVz
IENvLiwgTHRkMQ8wDQYDVQQDDAZCQkwgQ0EwggEiMA0GCSqGSIb3DQEBAQUAA4IB
DwAwggEKAoIBAQDL3pnDdxGOk5Z6vugiT4dpM0ju+3Xatxz09UY7mbj4tkIdby4H
oeEdiYSZjc5LJngJuCHwtEbBJt1BriRdSVrF6M9D2UaBDyamEo0dxwSaVxZiDVWC
eeCPdELpFZdEhSNTaT4O7zgvcnFsfHMa/0vMAkvE7i0qp3mjEzYLfz60axcDoJLk
p7n6xKXI+cJbA4IlToFjpSldPmC+ynOo7YAOsXt7AYKY6Glz0BwUVzSJxU+/+VFy
/QrmYGNwlrQtdREHeRi0SNK32x1+bOndfJP0sojuIrDjKsdCLye5CSZIvqnbowwW
1jRwZgTBR29Zp2nzCoxJYcU9TSQp/4KZuWNVAgMBAAGjUzBRMB0GA1UdDgQWBBSP
NEJo3GdOj8QinsV8SeWr3US+HjAfBgNVHSMEGDAWgBSPNEJo3GdOj8QinsV8SeWr
3US+HjAPBgNVHRMBAf8EBTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQABlBIT5ZeG
fgcK1LOh1CN9sTzxMCLbtTPFF1NGGA13mApu6j1h5YELbSKcUqfXzMnVeAb06Htu
3CoCoe+wj7LONTFO++vBm2/if6Jt/DUw1CAEcNyqeh6ES0NX8LJRVSe0qdTxPJuA
BdOoo96iX89rRPoxeed1cpq5hZwbeka3+CJGV76itWp35Up5rmmUqrlyQOr/Wax6
itosIzG0MfhgUzU51A2P/hSnD3NDMXv+wUY/AvqgIL7u7fbDKnku1GzEKIkfH8hm
Rs6d8SCU89xyrwzQ0PR853irHas3WrHVqab3P+qNwR0YirL0Qk7Xt/q3O1griNg2
Blbjg3obpHo9
-----END CERTIFICATE-----"""


class AuthenticationError(Exception):
    """Camera authentication failed."""
    pass


class CameraConnectionError(Exception):
    """Camera connection failed."""
    pass


class FrameParsingError(Exception):
    """Frame parsing failed."""
    pass


class BambuLabCameraClient:
    """
    TCP/TLS client for Bambu Lab A1/P1 camera protocol.

    Handles connection establishment, authentication, frame parsing,
    and provides access to camera frames.

    Example:
        client = BambuLabCameraClient(
            ip_address="192.168.1.100",
            access_code="12345678",
            serial_number="01S00A123456789",
            printer_id="bambu-a1-001"
        )
        await client.connect()
        frame = await client.read_frame()
        await client.disconnect()
    """

    def __init__(
        self,
        ip_address: str,
        access_code: str,
        serial_number: str,
        printer_id: str,
    ):
        """
        Initialize camera client.

        Args:
            ip_address: Printer IP address
            access_code: 8-character access code from printer LCD
            serial_number: Printer serial number (used for TLS SNI)
            printer_id: Internal printer identifier for logging
        """
        self.ip_address = ip_address
        self.access_code = access_code
        self.serial_number = serial_number
        self.printer_id = printer_id

        # Connection state
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected: bool = False
        self._reconnecting: bool = False

        # Frame management
        self._latest_frame: Optional[bytes] = None
        self._latest_frame_time: Optional[datetime] = None
        self._frame_lock = asyncio.Lock()

        # Background task for continuous reading
        self._reader_task: Optional[asyncio.Task] = None

        self._logger = logger.bind(
            printer_id=printer_id,
            ip=ip_address,
            serial=serial_number[:8] + "..."  # Partial serial for privacy
        )

    def _create_ssl_context(self) -> ssl.SSLContext:
        """
        Create SSL context with Bambu Lab CA certificate.

        Returns:
            Configured SSL context with SNI set to serial number
        """
        context = ssl.create_default_context()
        context.load_verify_locations(cadata=BAMBU_CA_CERT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED

        # Python 3.13+ has stricter SSL validation
        # Bambu Lab CA cert doesn't have keyUsage extension, so we need to relax verification
        # This is safe because we're verifying against a specific known CA certificate
        try:
            # Disable strict key usage checking (Python 3.13+)
            context.verify_flags &= ~ssl.VERIFY_X509_STRICT
        except AttributeError:
            # Python < 3.13 doesn't have this flag
            pass

        return context

    def _build_auth_packet(self) -> bytes:
        """
        Build 80-byte authentication packet.

        Packet Structure:
        - Bytes 0-15: Header (payload size, type, flags, padding)
        - Bytes 16-47: Username ("bblp") null-padded to 32 bytes
        - Bytes 48-79: Access code null-padded to 32 bytes

        Returns:
            80-byte authentication packet
        """
        # Header (16 bytes) - 4 x uint32
        payload_size = CameraConstants.AUTH_PAYLOAD_SIZE  # 0x40 (64 bytes)
        packet_type = CameraConstants.AUTH_PACKET_TYPE     # 0x3000
        flags = 0x00000000
        reserved = 0x00000000

        header = struct.pack('<IIII', payload_size, packet_type, flags, reserved)

        # Username field (32 bytes)
        username = CameraConstants.CAMERA_USERNAME.ljust(
            CameraConstants.AUTH_USERNAME_FIELD_SIZE, '\x00'
        ).encode('ascii')

        # Password field (32 bytes)
        password = self.access_code.ljust(
            CameraConstants.AUTH_PASSWORD_FIELD_SIZE, '\x00'
        ).encode('ascii')

        auth_packet = header + username + password

        if len(auth_packet) != CameraConstants.AUTH_PACKET_SIZE:
            raise ValueError(
                f"Auth packet size mismatch: {len(auth_packet)} != "
                f"{CameraConstants.AUTH_PACKET_SIZE}"
            )

        self._logger.debug(
            "Built authentication packet",
            packet_size=len(auth_packet),
            username=CameraConstants.CAMERA_USERNAME
        )

        return auth_packet

    async def connect(self, timeout: Optional[int] = None) -> None:
        """
        Establish TCP/TLS connection to camera and authenticate.

        Args:
            timeout: Connection timeout in seconds (default: from constants)

        Raises:
            CameraConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        if self._connected:
            self._logger.warning("Already connected to camera")
            return

        timeout = timeout or CameraConstants.CAMERA_CONNECTION_TIMEOUT_SECONDS

        try:
            self._logger.info("Connecting to camera", port=PortConstants.BAMBU_CAMERA_PORT)

            # Create SSL context
            ssl_context = self._create_ssl_context()

            # Connect with TLS
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(
                    host=self.ip_address,
                    port=PortConstants.BAMBU_CAMERA_PORT,
                    ssl=ssl_context,
                    server_hostname=self.serial_number,  # SNI
                ),
                timeout=timeout
            )

            self._logger.info("TLS connection established")

            # Send authentication packet
            await self._authenticate()

            self._connected = True
            self._logger.info("Camera connected and authenticated")

            # Start background frame reader
            self._reader_task = asyncio.create_task(self._frame_reader_loop())

        except asyncio.TimeoutError as e:
            self._logger.error("Camera connection timeout", timeout=timeout)
            raise CameraConnectionError(
                f"Connection timeout after {timeout}s"
            ) from e

        except ssl.SSLError as e:
            self._logger.error("TLS handshake failed", error=str(e))
            raise CameraConnectionError(f"TLS error: {e}") from e

        except OSError as e:
            self._logger.error("Network error", error=str(e))
            raise CameraConnectionError(f"Network error: {e}") from e

        except Exception as e:
            self._logger.error("Unexpected connection error", error=str(e))
            await self.disconnect()
            raise CameraConnectionError(f"Connection failed: {e}") from e

    async def _authenticate(self) -> None:
        """
        Send authentication packet to camera.

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            auth_packet = self._build_auth_packet()

            self._logger.debug("Sending authentication packet")
            self._writer.write(auth_packet)
            await self._writer.drain()

            # Wait briefly for authentication response (or connection close on failure)
            await asyncio.sleep(0.5)

            # Check if connection is still alive
            if self._writer.is_closing():
                raise AuthenticationError("Authentication failed - connection closed by printer")

            self._logger.info("Authentication successful")

        except AuthenticationError:
            raise
        except Exception as e:
            self._logger.error("Authentication error", error=str(e))
            raise AuthenticationError(f"Authentication failed: {e}") from e

    async def _read_frame_header(self) -> Tuple[int, int, int, int]:
        """
        Read and parse 16-byte frame header.

        Returns:
            Tuple of (payload_size, frame_type, flags, reserved)

        Raises:
            FrameParsingError: If header parsing fails
        """
        try:
            header_bytes = await self._reader.readexactly(CameraConstants.FRAME_HEADER_SIZE)
            payload_size, frame_type, flags, reserved = struct.unpack('<IIII', header_bytes)

            self._logger.debug(
                "Frame header received",
                payload_size=payload_size,
                frame_type=frame_type,
                flags=flags
            )

            return payload_size, frame_type, flags, reserved

        except asyncio.IncompleteReadError as e:
            raise FrameParsingError(f"Incomplete header: {e}") from e
        except struct.error as e:
            raise FrameParsingError(f"Header parsing error: {e}") from e

    async def read_frame(self) -> bytes:
        """
        Read and parse a single JPEG frame.

        Returns:
            Complete JPEG image data

        Raises:
            CameraConnectionError: If not connected
            FrameParsingError: If frame parsing fails
        """
        if not self._connected or not self._reader:
            raise CameraConnectionError("Not connected to camera")

        try:
            # Read frame header
            payload_size, frame_type, flags, reserved = await self._read_frame_header()

            # Validate payload size
            if not (CameraConstants.JPEG_MIN_SIZE_BYTES <= payload_size <= CameraConstants.JPEG_MAX_SIZE_BYTES):
                raise FrameParsingError(
                    f"Invalid payload size: {payload_size} bytes "
                    f"(expected {CameraConstants.JPEG_MIN_SIZE_BYTES}-{CameraConstants.JPEG_MAX_SIZE_BYTES})"
                )

            # Read JPEG payload
            jpeg_data = await self._reader.readexactly(payload_size)

            # Validate JPEG markers
            if not (
                jpeg_data[:2] == CameraConstants.JPEG_START_MARKER and
                jpeg_data[-2:] == CameraConstants.JPEG_END_MARKER
            ):
                self._logger.warning(
                    "Invalid JPEG markers",
                    start=jpeg_data[:2].hex(),
                    end=jpeg_data[-2:].hex(),
                    size=len(jpeg_data)
                )
                # Don't raise - some frames may have valid data despite marker issues

            self._logger.debug("Frame received", size=len(jpeg_data))

            return jpeg_data

        except asyncio.IncompleteReadError as e:
            raise FrameParsingError(f"Incomplete frame: {e}") from e
        except FrameParsingError:
            raise
        except Exception as e:
            raise FrameParsingError(f"Frame read error: {e}") from e

    async def _frame_reader_loop(self) -> None:
        """
        Background task to continuously read frames and cache the latest.

        Runs until connection is closed or task is cancelled.
        """
        self._logger.debug("Starting frame reader loop")

        while self._connected:
            try:
                frame = await self.read_frame()

                # Update latest frame (thread-safe)
                async with self._frame_lock:
                    self._latest_frame = frame
                    self._latest_frame_time = datetime.now()

            except FrameParsingError as e:
                self._logger.warning("Frame parsing error - skipping frame", error=str(e))
                continue  # Skip corrupted frame, continue reading

            except CameraConnectionError:
                self._logger.warning("Connection lost in frame reader")
                break

            except asyncio.CancelledError:
                self._logger.debug("Frame reader cancelled")
                break

            except Exception as e:
                self._logger.error("Unexpected error in frame reader", error=str(e))
                await asyncio.sleep(RetrySettings.CAMERA_RETRY_DELAY)  # Brief delay before retry

        self._logger.debug("Frame reader loop stopped")

    async def get_latest_frame(self) -> Optional[bytes]:
        """
        Get the most recently received frame.

        Returns:
            Latest JPEG frame data, or None if no frame available
        """
        async with self._frame_lock:
            return self._latest_frame

    async def get_latest_frame_age(self) -> Optional[float]:
        """
        Get age of latest frame in seconds.

        Returns:
            Age in seconds, or None if no frame available
        """
        async with self._frame_lock:
            if self._latest_frame_time is None:
                return None
            return (datetime.now() - self._latest_frame_time).total_seconds()

    async def disconnect(self) -> None:
        """
        Close camera connection and cleanup resources.
        """
        if not self._connected:
            return

        self._logger.info("Disconnecting from camera")

        self._connected = False

        # Cancel background reader task
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        # Close connection
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception as e:
                self._logger.warning("Error closing writer", error=str(e))
            finally:
                self._writer = None
                self._reader = None

        self._logger.info("Camera disconnected")

    @property
    def is_connected(self) -> bool:
        """Check if camera is currently connected."""
        return self._connected and self._writer is not None and not self._writer.is_closing()

    async def test_connection(self, timeout: int = 5) -> bool:
        """
        Test if camera connection is possible.

        Args:
            timeout: Connection test timeout in seconds

        Returns:
            True if connection successful, False otherwise
        """
        try:
            await self.connect(timeout=timeout)
            await self.disconnect()
            return True
        except (CameraConnectionError, AuthenticationError) as e:
            self._logger.debug("Camera connection test failed", error=str(e))
            return False

    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        return f"BambuLabCameraClient(printer={self.printer_id}, ip={self.ip_address}, status={status})"
