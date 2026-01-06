"""
Bambu Lab printer integration for Printernizer.
Handles communication with Bambu Lab A1 printers using bambulabs_api library.
"""
import asyncio
import json
import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
from io import BytesIO
import structlog

from src.config.constants import file_url
from src.models.printer import PrinterStatus, PrinterStatusUpdate, Filament
from src.utils.exceptions import PrinterConnectionError
from .base import BasePrinter, JobInfo, JobStatus, PrinterFile
from .download_strategies import (
    DownloadHandler,
    FTPDownloadStrategy,
    HTTPDownloadStrategy,
    MQTTDownloadStrategy
)
from src.services.bambu_ftp_service import BambuFTPService, BambuFTPFile
from src.constants import (
    PortConstants,
    NetworkConstants,
    TemperatureConstants,
    FileConstants
)

# Import bambulabs_api dependencies
try:
    from bambulabs_api import Printer as BambuClient
    from bambulabs_api import PrinterFTPClient
    BAMBU_API_AVAILABLE = True
except ImportError:
    BAMBU_API_AVAILABLE = False
    BambuClient = None
    PrinterFTPClient = None

# Fallback to paho.mqtt if bambulabs_api is not available
try:
    import paho.mqtt.client as mqtt
    import ssl
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    mqtt = None

logger = structlog.get_logger()


class BambuLabPrinter(BasePrinter):
    """Bambu Lab printer implementation using bambulabs_api library."""

    def __init__(self, printer_id: str, name: str, ip_address: str,
                 access_code: str, serial_number: str, file_service=None, **kwargs):
        """Initialize Bambu Lab printer."""
        super().__init__(printer_id, name, ip_address, **kwargs)

        # Prefer bambulabs_api over direct MQTT
        if BAMBU_API_AVAILABLE:
            self.use_bambu_api = True
            logger.info("Using bambulabs_api library for Bambu Lab integration")
        elif MQTT_AVAILABLE:
            self.use_bambu_api = False
            logger.warning("bambulabs_api not available, falling back to direct MQTT")
        else:
            raise ImportError("Neither bambulabs_api nor paho-mqtt library is available. "
                            "Install with: pip install bambulabs-api")

        self.access_code = access_code
        self.serial_number = serial_number
        self.file_service = file_service

        # Direct FTP service for file operations
        self.ftp_service: Optional[BambuFTPService] = None
        self.use_direct_ftp = True  # Flag to enable direct FTP

        # Download handler for file downloads (initialized in connect())
        self.download_handler: Optional[DownloadHandler] = None

        # Initialize appropriate client
        if self.use_bambu_api:
            self.bambu_client: Optional[BambuClient] = None
            self.latest_status: Optional[Dict[str, Any]] = None
            self.cached_files: List[PrinterFile] = []
            self.last_file_update: Optional[datetime] = None
        else:
            self.client = None  # MQTT client will be initialized in connect
            self.latest_data: Dict[str, Any] = {}
            self.mqtt_port = PortConstants.BAMBU_MQTT_PORT

        # MQTT retry and reconnection settings
        self.mqtt_retry_count = NetworkConstants.MQTT_RETRY_COUNT
        self.mqtt_retry_delay = NetworkConstants.MQTT_RETRY_DELAY_SECONDS
        self.mqtt_retry_backoff = NetworkConstants.MQTT_RETRY_BACKOFF_MULTIPLIER
        self.mqtt_retry_max_delay = NetworkConstants.MQTT_RETRY_MAX_DELAY_SECONDS
        self.mqtt_auto_reconnect_delay = NetworkConstants.MQTT_AUTO_RECONNECT_DELAY_SECONDS
        self.mqtt_keepalive_seconds = 60  # MQTT keepalive interval
        self.mqtt_reconnect_cooldown_seconds = 10.0  # Minimum time between reconnect attempts
        self._reconnect_task: Optional[asyncio.Task] = None
        self._should_reconnect = True  # Flag to control auto-reconnect behavior
        self._last_reconnect_attempt: Optional[float] = None  # Timestamp of last reconnect attempt
        self._connection_state = "disconnected"  # Track connection state for debugging
        
    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection event.

        Called when the client connects to the MQTT broker. Subscribes to the
        printer's status report topic on successful connection.

        Args:
            client: MQTT client instance.
            userdata: User-defined data passed to callbacks.
            flags: Response flags from the broker.
            rc: Connection result code (0 = success).
        """
        if rc == 0:
            self._connection_state = "connected"
            logger.info("MQTT connected successfully",
                       printer_id=self.printer_id,
                       connection_state=self._connection_state)
            # Subscribe to printer status topic
            topic = f"device/{self.serial_number}/report"
            client.subscribe(topic)
            logger.debug("Subscribed to topic", topic=topic)
        else:
            self._connection_state = "connection_failed"
            # Map RC codes to human-readable messages
            rc_messages = {
                1: "incorrect protocol version",
                2: "invalid client identifier",
                3: "server unavailable",
                4: "bad username or password",
                5: "not authorized"
            }
            rc_msg = rc_messages.get(rc, f"unknown error code {rc}")
            logger.error("MQTT connection failed",
                        printer_id=self.printer_id,
                        rc=rc,
                        reason=rc_msg,
                        connection_state=self._connection_state)

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages from printer.

        Parses and stores the latest printer status data from MQTT messages.

        Args:
            client: MQTT client instance.
            userdata: User-defined data passed to callbacks.
            msg: MQTT message containing printer status.
        """
        try:
            payload = json.loads(msg.payload.decode())
            self.latest_data = payload
            logger.debug("Received MQTT data", printer_id=self.printer_id, topic=msg.topic)
        except Exception as e:
            logger.warning("Failed to parse MQTT message", printer_id=self.printer_id, error=str(e))

    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection event with automatic reconnection.

        Implements cooldown to prevent reconnection storms.

        Args:
            client: MQTT client instance.
            userdata: User-defined data passed to callbacks.
            rc: Disconnection result code (0 = clean disconnect).
        """
        self.is_connected = False
        self._connection_state = "disconnected"

        if rc == 0:
            logger.info("MQTT disconnected cleanly",
                       printer_id=self.printer_id,
                       connection_state=self._connection_state)
        else:
            # Map disconnect RC codes to human-readable messages
            disconnect_reasons = {
                1: "connection lost",
                7: "keepalive timeout"
            }
            reason = disconnect_reasons.get(rc, f"unexpected disconnect (rc={rc})")

            logger.warning("MQTT disconnected unexpectedly",
                         printer_id=self.printer_id,
                         rc=rc,
                         reason=reason,
                         will_reconnect=self._should_reconnect,
                         connection_state=self._connection_state)

            # Check cooldown before scheduling reconnection
            now = time.time()
            if self._last_reconnect_attempt is not None:
                time_since_last = now - self._last_reconnect_attempt
                if time_since_last < self.mqtt_reconnect_cooldown_seconds:
                    logger.debug("Reconnect cooldown active, skipping auto-reconnect",
                               printer_id=self.printer_id,
                               cooldown_remaining=round(self.mqtt_reconnect_cooldown_seconds - time_since_last, 1))
                    return

            # Schedule automatic reconnection if enabled and not already reconnecting
            if self._should_reconnect and self._reconnect_task is None:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        self._reconnect_task = loop.create_task(
                            self._auto_reconnect()
                        )
                except RuntimeError:
                    # No event loop available - reconnection will happen on next connect() call
                    logger.debug("No event loop available for auto-reconnect",
                               printer_id=self.printer_id)

    async def _auto_reconnect(self):
        """Automatically reconnect to MQTT broker after unexpected disconnect.

        Implements cooldown tracking to prevent reconnection storms.
        """
        try:
            self._connection_state = "reconnecting"
            logger.info("Starting auto-reconnect sequence",
                       printer_id=self.printer_id,
                       initial_delay=self.mqtt_auto_reconnect_delay,
                       connection_state=self._connection_state)

            await asyncio.sleep(self.mqtt_auto_reconnect_delay)

            for attempt in range(self.mqtt_retry_count):
                if not self._should_reconnect:
                    self._connection_state = "disconnected"
                    logger.info("Auto-reconnect cancelled",
                              printer_id=self.printer_id,
                              connection_state=self._connection_state)
                    return

                try:
                    # Track reconnect attempt time for cooldown
                    self._last_reconnect_attempt = time.time()

                    logger.info("Auto-reconnect attempt",
                              printer_id=self.printer_id,
                              attempt=attempt + 1,
                              max_attempts=self.mqtt_retry_count,
                              connection_state=self._connection_state)

                    success = await self.connect()
                    if success:
                        logger.info("Auto-reconnect successful",
                                  printer_id=self.printer_id,
                                  attempt=attempt + 1,
                                  connection_state=self._connection_state)
                        return

                except Exception as e:
                    retry_delay = self._calculate_mqtt_retry_delay(attempt)
                    logger.warning("Auto-reconnect attempt failed",
                                 printer_id=self.printer_id,
                                 attempt=attempt + 1,
                                 max_attempts=self.mqtt_retry_count,
                                 retry_delay_seconds=round(retry_delay, 2),
                                 error=str(e),
                                 error_type=type(e).__name__,
                                 connection_state=self._connection_state)

                    if attempt < self.mqtt_retry_count - 1:
                        await asyncio.sleep(retry_delay)

            self._connection_state = "failed"
            logger.error("Auto-reconnect failed after all attempts",
                        printer_id=self.printer_id,
                        total_attempts=self.mqtt_retry_count,
                        connection_state=self._connection_state)

        finally:
            self._reconnect_task = None

    def _calculate_mqtt_retry_delay(self, attempt: int) -> float:
        """Calculate delay for MQTT retry attempt using exponential backoff with jitter.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds with jitter applied
        """
        # Exponential backoff: base_delay * (multiplier ^ attempt)
        delay = self.mqtt_retry_delay * (self.mqtt_retry_backoff ** attempt)

        # Cap at maximum delay
        delay = min(delay, self.mqtt_retry_max_delay)

        # Add jitter (±10%)
        jitter = delay * 0.1 * (2 * random.random() - 1)
        delay = max(0.5, delay + jitter)  # Ensure minimum 500ms delay

        return delay

    async def connect(self) -> bool:
        """Establish connection to Bambu Lab printer with retry support."""
        if self.is_connected:
            logger.info("Already connected to Bambu Lab printer", printer_id=self.printer_id)
            return True

        # Re-enable auto-reconnect when connecting
        self._should_reconnect = True

        try:
            # Initialize direct FTP service if enabled (lazy initialization - test on first use)
            if self.use_direct_ftp:
                try:
                    self.ftp_service = BambuFTPService(self.ip_address, self.access_code)
                    logger.info("Direct FTP service created (will test on first use)",
                               printer_id=self.printer_id)
                except Exception as e:
                    logger.warning("Failed to initialize direct FTP service",
                                 printer_id=self.printer_id, error=str(e))
                    self.ftp_service = None

            if self.use_bambu_api:
                result = await self._connect_bambu_api()

                # Initialize download handler after connection
                if result:
                    self._initialize_download_handler()

                return result
            else:
                result = await self._connect_mqtt()

                # Initialize download handler after connection
                if result:
                    self._initialize_download_handler()

                return result

        except Exception as e:
            logger.error("Failed to connect to Bambu Lab printer",
                        printer_id=self.printer_id, error=str(e))
            raise PrinterConnectionError(self.printer_id, str(e))

    async def _connect_bambu_api(self) -> bool:
        """Connect using bambulabs_api library."""
        start_time = time.time()
        self._connection_state = "connecting"
        logger.info("Connecting to Bambu Lab printer via bambulabs_api",
                   printer_id=self.printer_id,
                   ip=self.ip_address,
                   connection_state=self._connection_state)

        try:
            # Create bambulabs_api client
            self.bambu_client = BambuClient(
                ip_address=self.ip_address,
                access_code=self.access_code,
                serial=self.serial_number
            )

            # Set up event callbacks for real-time updates
            self.bambu_client.on_printer_status = self._on_bambu_status_update
            self.bambu_client.on_file_list = self._on_bambu_file_list_update

            # Connect to printer (synchronous method) - wrap in executor to prevent blocking
            connect_start = time.time()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.bambu_client.connect)
            connect_duration = time.time() - connect_start
            logger.info("[TIMING] Bambu API client connect completed",
                       printer_id=self.printer_id,
                       duration_seconds=round(connect_duration, 2))

            # Request initial status and file information
            if hasattr(self.bambu_client, 'request_status'):
                self.bambu_client.request_status()

            # Try to request file listing if supported
            if hasattr(self.bambu_client, 'request_file_list'):
                self.bambu_client.request_file_list()

            # Create PrinterFTPClient for file operations
            if PrinterFTPClient:
                try:
                    self.bambu_ftp_client = PrinterFTPClient(
                        server_ip=self.ip_address,
                        access_code=self.access_code
                    )
                    logger.info("Created PrinterFTPClient for file operations",
                               printer_id=self.printer_id)
                except Exception as e:
                    logger.warning("Failed to create PrinterFTPClient",
                                 printer_id=self.printer_id, error=str(e))
                    self.bambu_ftp_client = None
            else:
                self.bambu_ftp_client = None

            # Initialize direct FTP service as fallback
            if self.use_direct_ftp and not self.ftp_service:
                try:
                    from src.services.bambu_ftp_service import BambuFTPService
                    self.ftp_service = BambuFTPService(
                        ip_address=self.ip_address,
                        access_code=self.access_code
                    )
                    logger.info("Initialized direct FTP service",
                               printer_id=self.printer_id)
                except Exception as e:
                    logger.warning("Failed to initialize FTP service",
                                 printer_id=self.printer_id, error=str(e))
                    self.ftp_service = None

            self.is_connected = True
            self._connection_state = "connected"

            total_duration = time.time() - start_time
            logger.info("[TIMING] Bambu API connection successful",
                       printer_id=self.printer_id,
                       total_duration_seconds=round(total_duration, 2),
                       status="success",
                       connection_state=self._connection_state)
            return True

        except Exception as e:
            duration = time.time() - start_time
            self._connection_state = "failed"
            logger.error("[TIMING] Bambu API connection failed",
                        printer_id=self.printer_id,
                        duration_seconds=round(duration, 2),
                        status="failure",
                        error=str(e),
                        error_type=type(e).__name__,
                        connection_state=self._connection_state)
            raise

    async def _connect_mqtt(self) -> bool:
        """Connect using direct MQTT (fallback)."""
        start_time = time.time()
        self._connection_state = "connecting"
        logger.info("Connecting to Bambu Lab printer via direct MQTT",
                   printer_id=self.printer_id,
                   ip=self.ip_address,
                   connection_state=self._connection_state)

        try:
            # Create MQTT client
            self.client = mqtt.Client()
            self.client.username_pw_set("bblp", self.access_code)

            # Setup SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.client.tls_set_context(context)

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect

            # Connect to MQTT broker (synchronous) - wrap in executor to prevent blocking
            connect_start = time.time()
            loop = asyncio.get_event_loop()

            def _mqtt_connect():
                # Use keepalive parameter for connection health monitoring
                result = self.client.connect(
                    self.ip_address,
                    self.mqtt_port,
                    keepalive=self.mqtt_keepalive_seconds
                )
                if result != 0:
                    raise ConnectionError(f"MQTT connect failed with code {result}")
                return result

            await loop.run_in_executor(None, _mqtt_connect)
            connect_duration = time.time() - connect_start
            logger.info("[TIMING] MQTT broker connect completed",
                       printer_id=self.printer_id,
                       duration_seconds=round(connect_duration, 2),
                       keepalive_seconds=self.mqtt_keepalive_seconds)

            # Start MQTT loop in background
            self.client.loop_start()

            # Wait for connection to be established
            sleep_start = time.time()
            await asyncio.sleep(NetworkConstants.MQTT_CONNECTION_WAIT_SECONDS)
            sleep_duration = time.time() - sleep_start
            logger.debug("[TIMING] MQTT connection establishment wait",
                        printer_id=self.printer_id,
                        duration_seconds=round(sleep_duration, 2))

            self.is_connected = True
            self._connection_state = "connected"

            total_duration = time.time() - start_time
            logger.info("[TIMING] MQTT connection successful",
                       printer_id=self.printer_id,
                       total_duration_seconds=round(total_duration, 2),
                       status="success",
                       connection_state=self._connection_state)
            return True

        except Exception as e:
            duration = time.time() - start_time
            self._connection_state = "failed"
            logger.error("[TIMING] MQTT connection failed",
                        printer_id=self.printer_id,
                        duration_seconds=round(duration, 2),
                        status="failure",
                        error=str(e),
                        error_type=type(e).__name__,
                        connection_state=self._connection_state)
            raise

    # Callback methods for bambulabs_api events
    async def _on_bambu_status_update(self, status: Dict[str, Any]):
        """Handle status updates from bambulabs_api."""
        self.latest_status = status
        logger.debug("Received status update from bambulabs_api", printer_id=self.printer_id)

    async def _on_bambu_file_list_update(self, file_list_data: Dict[str, Any]):
        """Handle file list updates from bambulabs_api."""
        try:
            files = []
            if isinstance(file_list_data, dict) and 'files' in file_list_data:
                file_list = file_list_data['files']
                if isinstance(file_list, list):
                    for file_info in file_list:
                        if isinstance(file_info, dict):
                            filename = file_info.get('name', '')
                            if filename:
                                files.append(PrinterFile(
                                    filename=filename,
                                    size=file_info.get('size', 0),
                                    path=file_info.get('path', filename),
                                    modified=None,  # Usually not provided
                                    file_type=self._get_file_type_from_name(filename)
                                ))
            
            self.cached_files = files
            self.last_file_update = datetime.now()
            
            logger.info("Updated cached file list from bambulabs_api",
                       printer_id=self.printer_id, file_count=len(files))
                       
        except Exception as e:
            logger.warning("Failed to process file list update",
                          printer_id=self.printer_id, error=str(e))

    def _initialize_download_handler(self) -> None:
        """Initialize download handler with available strategies.

        Creates and configures download strategies based on available clients
        and services. Strategies are tried in priority order: FTP, HTTP, MQTT.
        """
        strategies = []

        # Priority 1: FTP download (most reliable)
        ftp_client = None
        if self.use_bambu_api and self.bambu_client and hasattr(self.bambu_client, 'ftp_client'):
            ftp_client = self.bambu_client.ftp_client

        ftp_strategy = FTPDownloadStrategy(
            printer_id=self.printer_id,
            printer_ip=self.ip_address,
            ftp_client=ftp_client,
            ftp_service=self.ftp_service
        )
        strategies.append(ftp_strategy)

        # Priority 2: HTTP download (fallback)
        http_strategy = HTTPDownloadStrategy(
            printer_id=self.printer_id,
            printer_ip=self.ip_address,
            access_code=self.access_code
        )
        strategies.append(http_strategy)

        # Priority 3: MQTT (placeholder - not supported)
        mqtt_strategy = MQTTDownloadStrategy(
            printer_id=self.printer_id,
            printer_ip=self.ip_address
        )
        strategies.append(mqtt_strategy)

        # Create download handler
        self.download_handler = DownloadHandler(
            printer_id=self.printer_id,
            strategies=strategies
        )

        logger.info(
            "Download handler initialized",
            printer_id=self.printer_id,
            strategies=[s.name for s in strategies]
        )

    async def disconnect(self) -> None:
        """Disconnect from Bambu Lab printer."""
        # Disable auto-reconnect during intentional disconnect
        self._should_reconnect = False
        self._connection_state = "disconnecting"

        # Cancel any pending reconnection task
        if self._reconnect_task is not None:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None

        if not self.is_connected:
            self._connection_state = "disconnected"
            return

        try:
            if self.use_bambu_api and self.bambu_client:
                self.bambu_client.disconnect()
                self.bambu_client = None
                self.latest_status = None
            elif self.client:
                self.client.loop_stop()
                self.client.disconnect()
                self.client = None
                self.latest_data = {}

            self.is_connected = False
            self._connection_state = "disconnected"
            logger.info("Disconnected from Bambu Lab printer",
                       printer_id=self.printer_id,
                       connection_state=self._connection_state)

        except Exception as e:
            self._connection_state = "disconnected"
            logger.error("Error disconnecting from Bambu Lab printer",
                        printer_id=self.printer_id,
                        error=str(e),
                        connection_state=self._connection_state)

        # Clean up FTP service
        self.ftp_service = None
            
    def _extract_filaments_from_mqtt(self, mqtt_data: Dict[str, Any]) -> List[Filament]:
        """Extract filament information from MQTT data (AMS system).

        Args:
            mqtt_data: Full MQTT data dump from bambulabs_api

        Returns:
            List of Filament objects with color, type, and slot information
        """
        filaments = []

        try:
            # Bambu Lab AMS (Automatic Material System) structure:
            # mqtt_data['ams']['ams'][ams_index]['tray'][tray_index]
            # For A1 and printers without AMS, external spool is in 'vt_tray' at root level
            if not isinstance(mqtt_data, dict):
                logger.debug("mqtt_data is not a dict", printer_id=self.printer_id)
                return filaments

            # Log available keys for debugging
            logger.debug("MQTT data keys for filament extraction",
                       printer_id=self.printer_id,
                       keys=list(mqtt_data.keys()),
                       has_ams='ams' in mqtt_data,
                       has_vt_tray='vt_tray' in mqtt_data)

            ams_data = mqtt_data.get('ams', {})
            if not isinstance(ams_data, dict):
                return filaments

            # Get current active tray info
            active_tray_id = ams_data.get('tray_now', '')  # Format: "0" or "254" (external spool)

            # Process AMS units
            ams_units = ams_data.get('ams', [])
            if isinstance(ams_units, list):
                for ams_idx, ams_unit in enumerate(ams_units):
                    if not isinstance(ams_unit, dict):
                        continue

                    # Each AMS unit can have multiple trays (typically 4)
                    trays = ams_unit.get('tray', [])
                    if isinstance(trays, list):
                        for tray_idx, tray in enumerate(trays):
                            if not isinstance(tray, dict):
                                continue

                            # Calculate global slot number (AMS unit * 4 + tray index)
                            slot = ams_idx * 4 + tray_idx

                            # Extract filament information
                            filament_type = tray.get('tray_type', '').upper() or None
                            filament_color = tray.get('tray_color', '') or None

                            # Convert color from RRGGBBAA hex to #RRGGBB format
                            if filament_color and len(filament_color) >= 6:
                                filament_color = f"#{filament_color[:6]}"

                            # Determine if this tray is currently active
                            tray_id_str = str(slot)
                            is_active = (active_tray_id == tray_id_str)

                            # Only add filament if it has some information
                            if filament_type or filament_color:
                                filaments.append(Filament(
                                    slot=slot,
                                    color=filament_color,
                                    type=filament_type,
                                    is_active=is_active
                                ))

                                logger.debug("Extracted filament from AMS",
                                           printer_id=self.printer_id,
                                           slot=slot,
                                           type=filament_type,
                                           color=filament_color,
                                           active=is_active)

            # Handle external spool (vt_tray) - used by A1 and other printers without AMS
            # The vt_tray data is at the root level of MQTT data, not inside 'ams'
            vt_tray = mqtt_data.get('vt_tray', {})
            if isinstance(vt_tray, dict) and vt_tray:
                # Extract filament info from virtual tray (external spool)
                vt_filament_type = vt_tray.get('tray_type', '').upper() or None
                vt_filament_color = vt_tray.get('tray_color', '') or None

                # Convert color from RRGGBBAA hex to #RRGGBB format
                if vt_filament_color and len(vt_filament_color) >= 6:
                    # Skip if color is all zeros (no filament configured)
                    if vt_filament_color[:6] != '000000':
                        vt_filament_color = f"#{vt_filament_color[:6]}"
                    else:
                        vt_filament_color = None

                is_vt_active = (active_tray_id == "254")

                # Add external spool if it has filament info
                if vt_filament_type or vt_filament_color:
                    filaments.append(Filament(
                        slot=254,
                        color=vt_filament_color,
                        type=vt_filament_type,
                        is_active=is_vt_active
                    ))
                    logger.debug("Extracted external spool filament from vt_tray",
                               printer_id=self.printer_id,
                               type=vt_filament_type,
                               color=vt_filament_color,
                               active=is_vt_active)
            elif active_tray_id == "254":
                # External spool is active, but no vt_tray data available
                # Add it as a generic filament
                filaments.append(Filament(
                    slot=254,
                    color=None,
                    type="External",
                    is_active=True
                ))
                logger.debug("External spool active (no vt_tray data)", printer_id=self.printer_id)

        except Exception as e:
            logger.warning("Failed to extract filament data from MQTT",
                         printer_id=self.printer_id, error=str(e))

        return filaments

    async def get_status(self) -> PrinterStatusUpdate:
        """Get current printer status from Bambu Lab."""
        if not self.is_connected:
            raise PrinterConnectionError(self.printer_id, "Not connected")

        try:
            if self.use_bambu_api:
                return await self._get_status_bambu_api()
            else:
                return await self._get_status_mqtt()

        except Exception as e:
            logger.error("Failed to get Bambu Lab status",
                        printer_id=self.printer_id, error=str(e))
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=PrinterStatus.ERROR,
                message=f"Status check failed: {str(e)}",
                timestamp=datetime.now()
            )

    async def _get_status_bambu_api(self) -> PrinterStatusUpdate:
        """Get status using bambulabs_api with improved timeout handling."""
        if not self.bambu_client:
            raise PrinterConnectionError(self.printer_id, "Bambu client not initialized")

        # Get current status from bambulabs_api with timeout handling
        try:
            current_state = self.bambu_client.get_current_state()
            if current_state:
                self.latest_status = current_state
        except Exception as e:
            logger.debug("Timeout getting current state, trying alternative methods", 
                        printer_id=self.printer_id, error=str(e))
            
            # If current_state fails, try to get specific data directly
            try:
                # Try to get basic status info even if current_state fails
                alternative_status = type('Status', (), {})()
                
                # Try to get status from individual methods
                if hasattr(self.bambu_client, 'get_state'):
                    try:
                        state = self.bambu_client.get_state()
                        alternative_status.name = state if state else 'UNKNOWN'
                    except (AttributeError, KeyError, TypeError) as e:
                        logger.debug("Failed to get printer state", printer_id=self.printer_id, error=str(e))
                        alternative_status.name = 'UNKNOWN'
                    except Exception as e:
                        logger.warning("Unexpected error getting printer state", printer_id=self.printer_id, error=str(e), exc_info=True)
                        alternative_status.name = 'UNKNOWN'
                        
                # Try to get temperature data
                try:
                    alternative_status.bed_temper = self.bambu_client.get_bed_temperature() or 0.0
                    alternative_status.nozzle_temper = self.bambu_client.get_nozzle_temperature() or 0.0
                except (AttributeError, KeyError, TypeError, ValueError) as e:
                    logger.debug("Failed to get temperature data", printer_id=self.printer_id, error=str(e))
                    alternative_status.bed_temper = 0.0
                    alternative_status.nozzle_temper = 0.0
                except Exception as e:
                    logger.warning("Unexpected error getting temperature data", printer_id=self.printer_id, error=str(e), exc_info=True)
                    alternative_status.bed_temper = 0.0
                    alternative_status.nozzle_temper = 0.0
                
                # Try to get progress
                try:
                    alternative_status.print_percent = self.bambu_client.get_percentage() or 0
                except (AttributeError, KeyError, TypeError, ValueError) as e:
                    logger.debug("Failed to get print progress", printer_id=self.printer_id, error=str(e))
                    alternative_status.print_percent = 0
                except Exception as e:
                    logger.warning("Unexpected error getting print progress", printer_id=self.printer_id, error=str(e), exc_info=True)
                    alternative_status.print_percent = 0
                    
                # Try to get filename
                try:
                    filename_methods = ['get_file_name', 'gcode_file', 'subtask_name']
                    for method_name in filename_methods:
                        if hasattr(self.bambu_client, method_name):
                            method = getattr(self.bambu_client, method_name)
                            result = method()
                            if result and isinstance(result, str) and result.strip() and result != "UNKNOWN":
                                alternative_status.gcode_file = result.strip()
                                break
                    if not hasattr(alternative_status, 'gcode_file'):
                        alternative_status.gcode_file = None
                except (AttributeError, KeyError, TypeError) as e:
                    logger.debug("Failed to get filename", printer_id=self.printer_id, error=str(e))
                    alternative_status.gcode_file = None
                except Exception as e:
                    logger.warning("Unexpected error getting filename", printer_id=self.printer_id, error=str(e), exc_info=True)
                    alternative_status.gcode_file = None
                
                # If we have temperature data, we can infer printing status
                if (hasattr(alternative_status, 'nozzle_temper') and
                    alternative_status.nozzle_temper > TemperatureConstants.NOZZLE_TEMP_PRINTING_THRESHOLD_C and
                    hasattr(alternative_status, 'bed_temper') and
                    alternative_status.bed_temper > TemperatureConstants.BED_TEMP_PRINTING_THRESHOLD_C):
                    alternative_status.name = 'PRINTING'
                    logger.info("Inferred PRINTING status from temperature data",
                              printer_id=self.printer_id,
                              nozzle_temp=alternative_status.nozzle_temper,
                              bed_temp=alternative_status.bed_temper)
                
                self.latest_status = alternative_status
                
            except Exception as inner_e:
                logger.debug("Alternative status methods also failed", 
                           printer_id=self.printer_id, error=str(inner_e))

        status = self.latest_status
        if not status:
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=PrinterStatus.UNKNOWN,
                message="No status data available",
                current_job_thumbnail_url=None,
                timestamp=datetime.now()
            )

        # Extract data from bambulabs_api status
        # The status.name contains the actual printer state
        status_name = getattr(status, 'name', 'UNKNOWN')
        status_value = getattr(status, 'value', 0)
        
        # Map bambulabs_api status names to our printer status
        printer_status = self._map_bambu_status(status_name)
        
        # Get temperature and progress data using bambulabs_api methods and MQTT data
        bed_temp = 0.0
        nozzle_temp = 0.0
        progress = 0
        layer_num = 0
        current_job = None
        remaining_time_minutes = None
        estimated_end_time = None
        elapsed_time_minutes = None
        print_start_time = None

        try:
            # First, try to get data from MQTT dump which is most reliable
            if hasattr(self.bambu_client, 'mqtt_dump'):
                mqtt_data = self.bambu_client.mqtt_dump()
                if isinstance(mqtt_data, dict) and 'print' in mqtt_data:
                    print_data = mqtt_data['print']
                    if isinstance(print_data, dict):
                        # Extract temperature data from MQTT (correct field names)
                        bed_temp = float(print_data.get('bed_temper', 0.0) or 0.0)
                        nozzle_temp = float(print_data.get('nozzle_temper', 0.0) or 0.0)

                        # Get layer information from MQTT
                        layer_num = int(print_data.get('layer_num', 0) or 0)

                        # Look for progress data in MQTT (various possible field names)
                        progress_fields = ['mc_percent', 'print_percent', 'percent', 'progress']
                        for field in progress_fields:
                            if field in print_data and print_data[field] is not None:
                                progress = int(print_data[field])
                                break

                        # Extract remaining time information
                        remaining_time_fields = ['mc_remaining_time', 'remaining_time', 'print_time_left', 'time_left']
                        for field in remaining_time_fields:
                            if field in print_data and print_data[field] is not None:
                                # Convert to minutes - assuming the field is in seconds
                                remaining_time_seconds = int(print_data[field])
                                if remaining_time_seconds > 0:
                                    remaining_time_minutes = remaining_time_seconds // 60
                                    # Calculate estimated end time
                                    from datetime import timedelta
                                    estimated_end_time = datetime.now() + timedelta(minutes=remaining_time_minutes)
                                break

                        # Extract elapsed time and start time from MQTT
                        # Try direct elapsed time field (in seconds)
                        elapsed_time_fields = ['mc_print_time', 'print_time', 'elapsed_time']
                        for field in elapsed_time_fields:
                            if field in print_data and print_data[field] is not None:
                                elapsed_seconds = int(print_data[field])
                                if elapsed_seconds > 0:
                                    elapsed_time_minutes = elapsed_seconds // 60
                                    from datetime import timedelta
                                    print_start_time = datetime.now() - timedelta(seconds=elapsed_seconds)
                                    logger.debug("Extracted Bambu elapsed time",
                                               printer_id=self.printer_id,
                                               field=field,
                                               elapsed_minutes=elapsed_time_minutes)
                                    break

                        # Try direct start timestamp (Unix timestamp) if elapsed time not found
                        if not elapsed_time_minutes:
                            timestamp_fields = ['gcode_start_time', 'start_time']
                            for field in timestamp_fields:
                                if field in print_data and print_data[field]:
                                    try:
                                        start_timestamp = int(print_data[field])
                                        if start_timestamp > 0:
                                            print_start_time = datetime.fromtimestamp(start_timestamp)
                                            elapsed = (datetime.now() - print_start_time).total_seconds()
                                            elapsed_time_minutes = int(elapsed // 60)
                                            logger.debug("Extracted Bambu start timestamp",
                                                       printer_id=self.printer_id,
                                                       field=field,
                                                       start_time=print_start_time.isoformat())
                                            break
                                    except Exception as e:
                                        logger.debug("Failed to parse timestamp field",
                                                   printer_id=self.printer_id,
                                                   field=field,
                                                   error=str(e))

                        logger.debug("Got data from MQTT dump",
                                   printer_id=self.printer_id,
                                   bed_temp=bed_temp, nozzle_temp=nozzle_temp,
                                   progress=progress, layer_num=layer_num,
                                   remaining_time_minutes=remaining_time_minutes,
                                   elapsed_time_minutes=elapsed_time_minutes,
                                   mqtt_keys=list(print_data.keys()))

            # If MQTT didn't provide data, use direct method calls
            if bed_temp == 0.0 and hasattr(self.bambu_client, 'get_bed_temperature'):
                bed_temp = float(self.bambu_client.get_bed_temperature() or 0.0)
            
            if nozzle_temp == 0.0 and hasattr(self.bambu_client, 'get_nozzle_temperature'):
                nozzle_temp = float(self.bambu_client.get_nozzle_temperature() or 0.0)
            
            if progress == 0 and hasattr(self.bambu_client, 'get_percentage'):
                progress = int(self.bambu_client.get_percentage() or 0)
            
            # Get layer information
            if hasattr(self.bambu_client, 'current_layer_num'):
                layer_num = int(self.bambu_client.current_layer_num() or 0)
            
            # Get current job name
            if hasattr(self.bambu_client, 'subtask_name'):
                subtask = self.bambu_client.subtask_name()
                if subtask and isinstance(subtask, str) and subtask.strip():
                    current_job = subtask.strip()
            
            if not current_job and hasattr(self.bambu_client, 'gcode_file'):
                gcode = self.bambu_client.gcode_file()
                if gcode and isinstance(gcode, str) and gcode.strip():
                    current_job = gcode.strip()
                    # Clean up cache/ prefix if present
                    if current_job.startswith('cache/'):
                        current_job = current_job[6:]
            
        except Exception as e:
            logger.debug("Failed to get bambulabs_api data", 
                        printer_id=self.printer_id, error=str(e))
            
            # Final fallback to status object attributes
            bed_temp = getattr(status, 'bed_temper', 0.0) or 0.0
            nozzle_temp = getattr(status, 'nozzle_temper', 0.0) or 0.0
            progress = getattr(status, 'print_percent', 0) or 0
            layer_num = getattr(status, 'layer_num', 0) or 0
        
        # Improved status detection based on printer status, progress and temperature data
        # First check the actual printer status from the API
        if status_name == 'PRINTING':
            # Only consider as printing if we have actual progress or confirmed printing status
            if progress > 0 and progress < 100:
                printer_status = PrinterStatus.PRINTING
                message = f"Printing - Layer {layer_num}, {progress}%"
            elif progress == 100:
                # Print completed but printer might still be cooling down
                printer_status = PrinterStatus.ONLINE
                if nozzle_temp > TemperatureConstants.NOZZLE_TEMP_COOLING_THRESHOLD_C or bed_temp > TemperatureConstants.BED_TEMP_COOLING_THRESHOLD_C:
                    message = f"Print Complete - Cooling down (Nozzle {nozzle_temp}°C, Bed {bed_temp}°C)"
                else:
                    message = "Print Complete - Ready"
            else:
                # Fallback: use temperature as indicator only if status explicitly says PRINTING
                if nozzle_temp > TemperatureConstants.NOZZLE_TEMP_PRINTING_THRESHOLD_C and bed_temp > TemperatureConstants.BED_TEMP_PRINTING_THRESHOLD_C:
                    printer_status = PrinterStatus.PRINTING
                    message = f"Printing - Nozzle {nozzle_temp}°C, Bed {bed_temp}°C"
                else:
                    printer_status = PrinterStatus.ONLINE
                    message = "Ready"
        elif status_name in ['IDLE', 'UNKNOWN']:
            # Printer is idle - check if just completing a print based on temperatures
            if progress == 100:
                printer_status = PrinterStatus.ONLINE
                if nozzle_temp > TemperatureConstants.NOZZLE_TEMP_COOLING_THRESHOLD_C or bed_temp > TemperatureConstants.BED_TEMP_COOLING_THRESHOLD_C:
                    message = f"Print Complete - Cooling down (Nozzle {nozzle_temp}°C, Bed {bed_temp}°C)"
                else:
                    message = "Print Complete - Ready"
            elif nozzle_temp > TemperatureConstants.NOZZLE_TEMP_COOLING_THRESHOLD_C:
                message = f"Heating - Nozzle {nozzle_temp}°C"
                printer_status = PrinterStatus.ONLINE
            elif bed_temp > TemperatureConstants.BED_TEMP_COOLING_THRESHOLD_C:
                message = f"Heating - Bed {bed_temp}°C"
                printer_status = PrinterStatus.ONLINE
            else:
                message = "Ready"
                printer_status = PrinterStatus.ONLINE
        else:
            # Map the status using the mapping function
            printer_status = self._map_bambu_status(status_name)
            # Provide better status messages for other states
            if printer_status == PrinterStatus.ONLINE and (nozzle_temp > TemperatureConstants.NOZZLE_TEMP_COOLING_THRESHOLD_C or bed_temp > TemperatureConstants.BED_TEMP_COOLING_THRESHOLD_C):
                message = f"{status_name} - Nozzle {nozzle_temp}°C, Bed {bed_temp}°C"
            else:
                message = f"Status: {status_name}"

        # If we're printing but don't have a job name, create a generic one
        if printer_status == PrinterStatus.PRINTING and not current_job:
            current_job = f"Print Job (via MQTT)"

        # Lookup file information for current job
        current_job_file_id = None
        current_job_has_thumbnail = None
        if current_job and self.file_service:
            try:
                # Clean up cache/ prefix if present for matching
                clean_filename = current_job
                if clean_filename.startswith('cache/'):
                    clean_filename = clean_filename[6:]

                file_record = await self.file_service.find_file_by_name(clean_filename, self.printer_id)
                if file_record:
                    current_job_file_id = file_record.get('id')
                    current_job_has_thumbnail = file_record.get('has_thumbnail', False)
                    logger.debug("Found file record for current job",
                                printer_id=self.printer_id,
                                filename=clean_filename,
                                file_id=current_job_file_id,
                                has_thumbnail=current_job_has_thumbnail)
            except Exception as e:
                logger.debug("Failed to lookup file for current job",
                            printer_id=self.printer_id,
                            filename=current_job,
                            error=str(e))

        # Enhance the message with filename if available and printing
        if printer_status == PrinterStatus.PRINTING and current_job and current_job != "Print Job (via MQTT)":
            if progress > 0:
                message = f"Printing '{current_job}' - Layer {layer_num}, {progress}%"
            else:
                message = f"Printing '{current_job}'"

        # Extract filament information from MQTT data
        filaments = []
        try:
            if hasattr(self.bambu_client, 'mqtt_dump'):
                mqtt_data = self.bambu_client.mqtt_dump()
                if mqtt_data:
                    filaments = self._extract_filaments_from_mqtt(mqtt_data)
                    logger.debug("Extracted filaments from MQTT",
                               printer_id=self.printer_id,
                               filament_count=len(filaments))
        except Exception as e:
            logger.debug("Failed to extract filaments",
                        printer_id=self.printer_id, error=str(e))

        logger.debug("Parsed Bambu status",
                    printer_id=self.printer_id,
                    status_name=status_name,
                    printer_status=printer_status.value,
                    bed_temp=bed_temp,
                    nozzle_temp=nozzle_temp,
                    progress=progress)

        return PrinterStatusUpdate(
            printer_id=self.printer_id,
            status=printer_status,
            message=message,
            temperature_bed=float(bed_temp),
            temperature_nozzle=float(nozzle_temp),
            progress=int(progress),
            current_job=current_job,
            current_job_file_id=current_job_file_id,
            current_job_has_thumbnail=current_job_has_thumbnail,
            current_job_thumbnail_url=(file_url(current_job_file_id, 'thumbnail') if current_job_file_id and current_job_has_thumbnail else None),
            remaining_time_minutes=remaining_time_minutes,
            estimated_end_time=estimated_end_time,
            elapsed_time_minutes=elapsed_time_minutes,
            print_start_time=print_start_time,
            filaments=filaments if filaments else None,
            timestamp=datetime.now(),
            raw_data=status.__dict__ if hasattr(status, '__dict__') else {}
        )

    async def _get_status_mqtt(self) -> PrinterStatusUpdate:
        """Get status using direct MQTT."""
        if not self.client:
            raise PrinterConnectionError(self.printer_id, "MQTT client not initialized")

        # Extract data from latest MQTT message
        print_data = self.latest_data.get("print", {})

        # Extract temperature data
        bed_temp = print_data.get("bed_temper", 0.0)
        nozzle_temp = print_data.get("nozzle_temper", 0.0)
        progress = print_data.get("mc_percent", 0)
        layer_num = print_data.get("layer_num", 0)

        # Extract time information
        remaining_time_minutes = None
        estimated_end_time = None
        remaining_time_fields = ['mc_remaining_time', 'remaining_time', 'print_time_left', 'time_left']
        for field in remaining_time_fields:
            if field in print_data and print_data[field] is not None:
                # Convert to minutes - assuming the field is in seconds
                remaining_time_seconds = int(print_data[field])
                if remaining_time_seconds > 0:
                    remaining_time_minutes = remaining_time_seconds // 60
                    # Calculate estimated end time
                    from datetime import timedelta
                    estimated_end_time = datetime.now() + timedelta(minutes=remaining_time_minutes)
                break

        # Improved status detection for printing
        # High temperatures usually indicate printing activity
        if nozzle_temp > TemperatureConstants.NOZZLE_TEMP_PRINTING_THRESHOLD_C and bed_temp > TemperatureConstants.BED_TEMP_PRINTING_THRESHOLD_C:
            printer_status = PrinterStatus.PRINTING
            if progress > 0:
                message = f"Printing - Layer {layer_num}, {progress}%"
            else:
                message = f"Printing - Nozzle {nozzle_temp}°C, Bed {bed_temp}°C"
        elif progress > 0 and nozzle_temp > TemperatureConstants.NOZZLE_TEMP_ACTIVE_THRESHOLD_C:
            printer_status = PrinterStatus.PRINTING
            message = f"Printing - Layer {layer_num}, {progress}%"
        elif nozzle_temp > TemperatureConstants.NOZZLE_TEMP_COOLING_THRESHOLD_C:
            printer_status = PrinterStatus.ONLINE
            message = f"Heating - Nozzle {nozzle_temp}°C"
        elif bed_temp > TemperatureConstants.BED_TEMP_COOLING_THRESHOLD_C:
            printer_status = PrinterStatus.ONLINE
            message = f"Heating - Bed {bed_temp}°C"
        else:
            printer_status = PrinterStatus.ONLINE
            message = "Ready"

        # Extract job information (if available)
        current_job = print_data.get("subtask_name")
        
        # If no job name from MQTT but we have MQTT client, try API methods
        if not current_job and hasattr(self, 'bambu_client') and self.bambu_client:
            try:
                # Try bambulabs_api methods for filename
                filename_methods = ['get_file_name', 'gcode_file', 'subtask_name']
                for method_name in filename_methods:
                    if hasattr(self.bambu_client, method_name):
                        method = getattr(self.bambu_client, method_name)
                        result = method()
                        if result and isinstance(result, str) and result.strip() and result != "UNKNOWN":
                            current_job = result.strip()
                            # Clean up cache/ prefix if present
                            if current_job.startswith('cache/'):
                                current_job = current_job[6:]
                            logger.debug(f"Got filename from {method_name} (MQTT fallback): {current_job}")
                            break
            except Exception as e:
                logger.debug(f"Failed to get filename via API methods from MQTT: {e}")
        
        # If we're printing but don't have a job name, create a generic one
        if printer_status == PrinterStatus.PRINTING and not current_job:
            current_job = f"Active Print Job"

        # Lookup file information for current job
        current_job_file_id = None
        current_job_has_thumbnail = None
        if current_job and current_job != "Active Print Job" and self.file_service:
            try:
                # Clean up cache/ prefix if present for matching
                clean_filename = current_job
                if clean_filename.startswith('cache/'):
                    clean_filename = clean_filename[6:]

                file_record = await self.file_service.find_file_by_name(clean_filename, self.printer_id)
                if file_record:
                    current_job_file_id = file_record.get('id')
                    current_job_has_thumbnail = file_record.get('has_thumbnail', False)
                    logger.debug("Found file record for current job (MQTT)",
                                printer_id=self.printer_id,
                                filename=clean_filename,
                                file_id=current_job_file_id,
                                has_thumbnail=current_job_has_thumbnail)
            except Exception as e:
                logger.debug("Failed to lookup file for current job (MQTT)",
                            printer_id=self.printer_id,
                            filename=current_job,
                            error=str(e))

        # Enhance the message with filename if available and printing
        if printer_status == PrinterStatus.PRINTING and current_job and current_job != "Active Print Job":
            message = f"Printing '{current_job}'"

        # Extract filament information from MQTT data
        filaments = []
        try:
            if self.latest_data:
                filaments = self._extract_filaments_from_mqtt(self.latest_data)
                logger.debug("Extracted filaments from direct MQTT",
                           printer_id=self.printer_id,
                           filament_count=len(filaments))
        except Exception as e:
            logger.debug("Failed to extract filaments from MQTT",
                        printer_id=self.printer_id, error=str(e))

        logger.debug("Parsed MQTT status",
                    printer_id=self.printer_id,
                    bed_temp=bed_temp,
                    nozzle_temp=nozzle_temp,
                    progress=progress,
                    status=printer_status.value)

        return PrinterStatusUpdate(
            printer_id=self.printer_id,
            status=printer_status,
            message=message,
            temperature_bed=float(bed_temp),
            temperature_nozzle=float(nozzle_temp),
            progress=int(progress),
            current_job=current_job,
            current_job_file_id=current_job_file_id,
            current_job_has_thumbnail=current_job_has_thumbnail,
            current_job_thumbnail_url=(file_url(current_job_file_id, 'thumbnail') if current_job_file_id and current_job_has_thumbnail else None),
            remaining_time_minutes=remaining_time_minutes,
            estimated_end_time=estimated_end_time,
            filaments=filaments if filaments else None,
            timestamp=datetime.now(),
            raw_data=self.latest_data
        )
            
    def _map_bambu_status(self, bambu_status) -> PrinterStatus:
        """Map Bambu Lab status to PrinterStatus."""
        # Handle both string and enum types
        if hasattr(bambu_status, 'name'):
            status_str = bambu_status.name
        else:
            status_str = str(bambu_status)
            
        status_mapping = {
            'IDLE': PrinterStatus.ONLINE,
            'PRINTING': PrinterStatus.PRINTING,
            'PAUSED_USER': PrinterStatus.PAUSED,
            'PAUSED_FILAMENT_RUNOUT': PrinterStatus.PAUSED,
            'PAUSED_FRONT_COVER_FALLING': PrinterStatus.PAUSED,
            'PAUSED_NOZZLE_TEMPERATURE_MALFUNCTION': PrinterStatus.ERROR,
            'PAUSED_HEAT_BED_TEMPERATURE_MALFUNCTION': PrinterStatus.ERROR,
            'PAUSED_SKIPPED_STEP': PrinterStatus.ERROR,
            'PAUSED_AMS_LOST': PrinterStatus.ERROR,
            'PAUSED_LOW_FAN_SPEED_HEAT_BREAK': PrinterStatus.ERROR,
            'PAUSED_CHAMBER_TEMPERATURE_CONTROL_ERROR': PrinterStatus.ERROR,
            'PAUSED_USER_GCODE': PrinterStatus.PAUSED,
            'PAUSED_NOZZLE_FILAMENT_COVERED_DETECTED': PrinterStatus.ERROR,
            'PAUSED_CUTTER_ERROR': PrinterStatus.ERROR,
            'PAUSED_FIRST_LAYER_ERROR': PrinterStatus.ERROR,
            'PAUSED_NOZZLE_CLOG': PrinterStatus.ERROR,
            'AUTO_BED_LEVELING': PrinterStatus.ONLINE,
            'HEATBED_PREHEATING': PrinterStatus.ONLINE,
            'SWEEPING_XY_MECH_MODE': PrinterStatus.ONLINE,
            'CHANGING_FILAMENT': PrinterStatus.ONLINE,
            'M400_PAUSE': PrinterStatus.PAUSED,
            'HEATING_HOTEND': PrinterStatus.ONLINE,
            'CALIBRATING_EXTRUSION': PrinterStatus.ONLINE,
            'SCANNING_BED_SURFACE': PrinterStatus.ONLINE,
            'INSPECTING_FIRST_LAYER': PrinterStatus.ONLINE,
            'IDENTIFYING_BUILD_PLATE_TYPE': PrinterStatus.ONLINE,
            'CALIBRATING_MICRO_LIDAR': PrinterStatus.ONLINE,
            'HOMING_TOOLHEAD': PrinterStatus.ONLINE,
            'CLEANING_NOZZLE_TIP': PrinterStatus.ONLINE,
            'CHECKING_EXTRUDER_TEMPERATURE': PrinterStatus.ONLINE,
            'CALIBRATING_LIDAR': PrinterStatus.ONLINE,
            'CALIBRATING_EXTRUSION_FLOW': PrinterStatus.ONLINE,
            'FILAMENT_UNLOADING': PrinterStatus.ONLINE,
            'FILAMENT_LOADING': PrinterStatus.ONLINE,
            'CALIBRATING_MOTOR_NOISE': PrinterStatus.ONLINE,
            'COOLING_CHAMBER': PrinterStatus.ONLINE,
            'MOTOR_NOISE_SHOWOFF': PrinterStatus.ONLINE,
            'UNKNOWN': PrinterStatus.UNKNOWN
        }
        return status_mapping.get(status_str.upper(), PrinterStatus.UNKNOWN)
        
    async def get_job_info(self) -> Optional[JobInfo]:
        """Get current job information from Bambu Lab."""
        if not self.is_connected or not self.client:
            return None

        try:
            print_data = self.latest_data.get("print", {})
            progress = print_data.get("mc_percent", 0)

            # Only return job info if actively printing
            if progress <= 0:
                return None  # No active job

            # Extract job information
            job_name = print_data.get("subtask_name", f"Bambu Job {datetime.now().strftime('%H:%M')}")
            layer_num = print_data.get("layer_num", 0)

            # Determine job status
            nozzle_temp = print_data.get("nozzle_temper", 0)
            if progress > 0 and nozzle_temp > TemperatureConstants.NOZZLE_TEMP_ACTIVE_THRESHOLD_C:
                job_status = JobStatus.PRINTING
            elif nozzle_temp > TemperatureConstants.NOZZLE_TEMP_COOLING_THRESHOLD_C:
                job_status = JobStatus.PREPARING
            else:
                job_status = JobStatus.IDLE

            job_info = JobInfo(
                job_id=f"{self.printer_id}_{job_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name=job_name,
                status=job_status,
                progress=progress,
                estimated_time=None  # Not available in MQTT data
            )

            return job_info

        except Exception as e:
            logger.error("Failed to get Bambu Lab job info",
                        printer_id=self.printer_id, error=str(e))
            return None
            
    def _map_job_status(self, bambu_status) -> JobStatus:
        """Map Bambu Lab status to JobStatus."""
        # Handle both string and enum types
        if hasattr(bambu_status, 'name'):
            status_str = bambu_status.name
        else:
            status_str = str(bambu_status)
            
        status_mapping = {
            'IDLE': JobStatus.IDLE,
            'PRINTING': JobStatus.PRINTING,
            'PAUSED_USER': JobStatus.PAUSED,
            'PAUSED_FILAMENT_RUNOUT': JobStatus.PAUSED,
            'PAUSED_FRONT_COVER_FALLING': JobStatus.PAUSED,
            'PAUSED_NOZZLE_TEMPERATURE_MALFUNCTION': JobStatus.FAILED,
            'PAUSED_HEAT_BED_TEMPERATURE_MALFUNCTION': JobStatus.FAILED,
            'PAUSED_SKIPPED_STEP': JobStatus.FAILED,
            'PAUSED_AMS_LOST': JobStatus.FAILED,
            'PAUSED_LOW_FAN_SPEED_HEAT_BREAK': JobStatus.FAILED,
            'PAUSED_CHAMBER_TEMPERATURE_CONTROL_ERROR': JobStatus.FAILED,
            'PAUSED_USER_GCODE': JobStatus.PAUSED,
            'PAUSED_NOZZLE_FILAMENT_COVERED_DETECTED': JobStatus.FAILED,
            'PAUSED_CUTTER_ERROR': JobStatus.FAILED,
            'PAUSED_FIRST_LAYER_ERROR': JobStatus.FAILED,
            'PAUSED_NOZZLE_CLOG': JobStatus.FAILED,
            'AUTO_BED_LEVELING': JobStatus.PREPARING,
            'HEATBED_PREHEATING': JobStatus.PREPARING,
            'SWEEPING_XY_MECH_MODE': JobStatus.PREPARING,
            'CHANGING_FILAMENT': JobStatus.PREPARING,
            'M400_PAUSE': JobStatus.PAUSED,
            'HEATING_HOTEND': JobStatus.PREPARING,
            'CALIBRATING_EXTRUSION': JobStatus.PREPARING,
            'SCANNING_BED_SURFACE': JobStatus.PREPARING,
            'INSPECTING_FIRST_LAYER': JobStatus.PREPARING,
            'IDENTIFYING_BUILD_PLATE_TYPE': JobStatus.PREPARING,
            'CALIBRATING_MICRO_LIDAR': JobStatus.PREPARING,
            'HOMING_TOOLHEAD': JobStatus.PREPARING,
            'CLEANING_NOZZLE_TIP': JobStatus.PREPARING,
            'CHECKING_EXTRUDER_TEMPERATURE': JobStatus.PREPARING,
            'CALIBRATING_LIDAR': JobStatus.PREPARING,
            'CALIBRATING_EXTRUSION_FLOW': JobStatus.PREPARING,
            'FILAMENT_UNLOADING': JobStatus.PREPARING,
            'FILAMENT_LOADING': JobStatus.PREPARING,
            'CALIBRATING_MOTOR_NOISE': JobStatus.PREPARING,
            'COOLING_CHAMBER': JobStatus.PREPARING,
            'MOTOR_NOISE_SHOWOFF': JobStatus.PREPARING
        }
        return status_mapping.get(status_str.upper(), JobStatus.IDLE)
        
    async def list_files(self) -> List[PrinterFile]:
        """List files available on Bambu Lab printer."""
        if not self.is_connected:
            raise PrinterConnectionError(self.printer_id, "Not connected")

        # Try methods in order: Direct FTP -> PrinterFTPClient -> bambulabs_api -> MQTT
        # Direct FTP is prioritized as it has proper implicit TLS implementation
        last_error = None

        # Initialize FTP service on-demand if not already done
        if self.use_direct_ftp and not self.ftp_service:
            try:
                logger.info("Lazy-initializing FTP service for file listing",
                           printer_id=self.printer_id)
                self.ftp_service = BambuFTPService(self.ip_address, self.access_code)
            except Exception as e:
                logger.warning("Failed to initialize FTP service on-demand",
                             printer_id=self.printer_id, error=str(e))

        # Try direct FTP FIRST (has proper implicit TLS fixes)
        if self.ftp_service:
            try:
                logger.info("Attempting file list via direct FTP", printer_id=self.printer_id)
                return await self._list_files_direct_ftp()
            except Exception as e:
                logger.warning("Direct FTP file listing failed, trying fallback methods",
                             printer_id=self.printer_id, error=str(e))
                last_error = e

        # Try PrinterFTPClient as fallback
        if hasattr(self, 'bambu_ftp_client') and self.bambu_ftp_client:
            try:
                logger.info("Attempting file list via PrinterFTPClient", printer_id=self.printer_id)
                return await self._list_files_printer_ftp_client()
            except Exception as e:
                logger.warning("PrinterFTPClient file listing failed, trying fallback methods",
                             printer_id=self.printer_id, error=str(e))
                last_error = e

        # Fallback to bambulabs_api
        if self.use_bambu_api:
            try:
                logger.info("Attempting file list via bambulabs_api", printer_id=self.printer_id)
                return await self._list_files_bambu_api()
            except Exception as e:
                logger.warning("bambulabs_api file listing failed, trying MQTT fallback",
                             printer_id=self.printer_id, error=str(e))
                last_error = e

        # Final fallback to MQTT
        try:
            logger.info("Attempting file list via MQTT", printer_id=self.printer_id)
            return await self._list_files_mqtt()
        except Exception as e:
            logger.error("All file listing methods failed",
                        printer_id=self.printer_id, error=str(e))
            last_error = e

        # If we get here, all methods failed
        raise PrinterConnectionError(self.printer_id, f"File listing failed: {str(last_error)}")

    async def _list_files_printer_ftp_client(self) -> List[PrinterFile]:
        """List files using PrinterFTPClient from bambulabs_api."""
        logger.info("Listing files from /cache using PrinterFTPClient",
                   printer_id=self.printer_id)

        files = []

        try:
            # Run in executor since PrinterFTPClient methods are synchronous
            loop = asyncio.get_event_loop()
            ftp_lines = await loop.run_in_executor(None, self.bambu_ftp_client.list_cache_dir)

            if not ftp_lines:
                logger.info("No files found in /cache", printer_id=self.printer_id)
                return files

            # ftp_lines is typically ['226 ', [list of file lines]]
            # Extract the actual file list
            file_list = []
            if isinstance(ftp_lines, list) and len(ftp_lines) >= 2:
                file_list = ftp_lines[1] if isinstance(ftp_lines[1], list) else []

            # Parse FTP LIST format: -rw-rw-rw-   1 root  root   3081365 Sep 28 03:57 filename.3mf
            for line in file_list:
                if not isinstance(line, str) or not line.strip():
                    continue

                parts = line.split()
                if len(parts) < 9:  # Need at least permissions, links, user, group, size, month, day, time/year, filename
                    continue

                try:
                    permissions = parts[0]
                    size = int(parts[4])
                    # Filename is everything after the time/year (index 8 onwards)
                    filename = ' '.join(parts[8:])

                    # Only include 3D printing files
                    if filename.endswith(('.3mf', '.gcode', '.bgcode', '.stl')):
                        files.append(PrinterFile(
                            filename=filename,
                            size=size,
                            path=f"/cache/{filename}",
                            modified=None,  # Could parse date if needed
                            file_type=self._get_file_type_from_name(filename)
                        ))
                except (ValueError, IndexError) as e:
                    logger.debug("Failed to parse FTP line", line=line, error=str(e))
                    continue

            logger.info("Retrieved files from PrinterFTPClient",
                       printer_id=self.printer_id, file_count=len(files))

        except Exception as e:
            logger.error("PrinterFTPClient file listing failed",
                        printer_id=self.printer_id, error=str(e))
            raise

        return files

    async def _list_files_bambu_api(self) -> List[PrinterFile]:
        """List files using bambulabs_api library with enhanced discovery."""
        if not self.bambu_client:
            raise PrinterConnectionError(self.printer_id, "Bambu client not initialized")

        logger.info("Requesting file list from Bambu Lab printer via API",
                   printer_id=self.printer_id)

        files = []

        try:
            # Method 0: Use cached files if recently updated
            if (hasattr(self, 'cached_files') and self.cached_files and
                hasattr(self, 'last_file_update') and self.last_file_update and
                (datetime.now() - self.last_file_update).seconds < FileConstants.BAMBU_FILE_CACHE_VALIDITY_SECONDS):
                logger.info("Using cached file list from recent update",
                           printer_id=self.printer_id, file_count=len(self.cached_files))
                return self.cached_files
            
            # Method 1: Try direct get_files API if available
            if hasattr(self.bambu_client, 'get_files'):
                try:
                    api_files = self.bambu_client.get_files()
                    if api_files:
                        for f in api_files:
                            files.append(PrinterFile(
                                filename=f.get('name', ''),
                                size=f.get('size', 0),
                                path=f.get('path', ''),
                                modified=None,
                                file_type=self._get_file_type_from_name(f.get('name', ''))
                            ))
                        logger.info("Retrieved files via get_files API",
                                   printer_id=self.printer_id, file_count=len(files))
                        return files
                except Exception as e:
                    logger.debug("get_files API failed, trying FTP methods", 
                                printer_id=self.printer_id, error=str(e))

            # Method 2: Try FTP client methods if available
            if hasattr(self.bambu_client, 'ftp_client'):
                try:
                    ftp_files = await self._discover_files_via_ftp()
                    files.extend(ftp_files)
                except Exception as e:
                    logger.debug("FTP file discovery failed", 
                                printer_id=self.printer_id, error=str(e))

            # Method 3: Try to access the printer's file system via MQTT dump
            if len(files) == 0:
                try:
                    mqtt_files = await self._discover_files_via_mqtt_dump()
                    files.extend(mqtt_files)
                except Exception as e:
                    logger.debug("MQTT dump file discovery failed", 
                                printer_id=self.printer_id, error=str(e))

            # Method 4: Check for uploaded files via internal tracking
            if hasattr(self.bambu_client, 'uploaded_files') and self.bambu_client.uploaded_files:
                try:
                    for uploaded_file in self.bambu_client.uploaded_files:
                        if uploaded_file not in [f.filename for f in files]:
                            files.append(PrinterFile(
                                filename=uploaded_file,
                                size=0,  # Size unknown
                                path=uploaded_file,
                                modified=None,
                                file_type=self._get_file_type_from_name(uploaded_file)
                            ))
                except Exception as e:
                    logger.debug("Uploaded files tracking failed", 
                                printer_id=self.printer_id, error=str(e))

        except Exception as e:
            logger.warning("All file discovery methods failed", 
                          printer_id=self.printer_id, error=str(e))

        # If no files found, provide a helpful message
        if len(files) == 0:
            logger.info("No files discovered - this may be normal if no files are uploaded or SD card is empty", 
                       printer_id=self.printer_id)
        else:
            logger.info("Retrieved file list from Bambu Lab printer",
                       printer_id=self.printer_id, file_count=len(files))
        
        return files

    async def _discover_files_via_ftp(self) -> List[PrinterFile]:
        """Discover files using FTP client methods."""
        files = []
        
        if not hasattr(self.bambu_client, 'ftp_client'):
            return files
            
        ftp = self.bambu_client.ftp_client
        
        try:
            # Check various FTP directories for files
            # Note: The bambulabs_api FTP client mainly provides access to logs, images, etc.
            # Actual 3D print files (3mf, gcode) are typically on SD card or internal storage
            
            # Try to get image files (could indicate recent prints)
            if hasattr(ftp, 'list_images_dir'):
                try:
                    result, image_files = ftp.list_images_dir()
                    for img_file in image_files or []:
                        if img_file.lower().endswith(('.jpg', '.png', '.jpeg')):
                            # Extract potential model name from preview images
                            model_name = img_file.replace('_preview.jpg', '').replace('_plate_1.jpg', '')
                            if model_name and model_name != img_file:
                                # This suggests there might be a corresponding 3mf file
                                potential_file = f"{model_name}.3mf"
                                files.append(PrinterFile(
                                    filename=potential_file,
                                    size=0,  # Size unknown from preview
                                    path=f"inferred/{potential_file}",
                                    modified=None,
                                    file_type='3mf'
                                ))
                except Exception as e:
                    logger.debug("Failed to list image directory", error=str(e))
            
            # Try cache directory (might contain temporary files)
            if hasattr(ftp, 'list_cache_dir'):
                try:
                    result, cache_files = ftp.list_cache_dir()
                    for cache_file in cache_files or []:
                        # Parse FTP listing line to extract filename and size
                        # Format: "-rw-rw-rw-   1 root  root    445349 Apr 22 01:10 filename.ext"
                        file_size = None
                        if isinstance(cache_file, str):
                            # Split on whitespace and take the last part as filename
                            parts = cache_file.strip().split()
                            if len(parts) >= 9:  # Standard FTP ls -l format
                                filename = ' '.join(parts[8:])  # filename might contain spaces
                                # Extract file size (5th column in ls -l format)
                                try:
                                    file_size = int(parts[4])
                                except (ValueError, IndexError):
                                    file_size = None
                            else:
                                filename = parts[-1] if parts else cache_file
                        else:
                            filename = str(cache_file)

                        if any(filename.lower().endswith(ext) for ext in ['.3mf', '.gcode', '.bgcode']):
                            files.append(PrinterFile(
                                filename=filename,
                                size=file_size,
                                path=f"cache/{filename}",
                                modified=None,
                                file_type=self._get_file_type_from_name(filename)
                            ))
                except Exception as e:
                    logger.debug("Failed to list cache directory", error=str(e))
                    
        except Exception as e:
            logger.debug("FTP file discovery error", error=str(e))
            
        return files

    async def _discover_files_via_mqtt_dump(self) -> List[PrinterFile]:
        """Discover files using MQTT dump data."""
        files = []
        
        try:
            if hasattr(self.bambu_client, 'mqtt_dump'):
                mqtt_data = self.bambu_client.mqtt_dump()
                
                # Look for file-related information in the MQTT data
                if isinstance(mqtt_data, dict):
                    # Check for current print job file
                    if 'print' in mqtt_data:
                        print_data = mqtt_data['print']
                        if isinstance(print_data, dict):
                            # Current file being printed
                            if 'file' in print_data:
                                current_file = print_data['file']
                                if isinstance(current_file, str) and current_file:
                                    files.append(PrinterFile(
                                        filename=current_file,
                                        size=0,
                                        path=f"current/{current_file}",
                                        modified=None,
                                        file_type=self._get_file_type_from_name(current_file)
                                    ))
                            
                            # Task name might indicate file name
                            if 'task_name' in print_data:
                                task_name = print_data['task_name']
                                if isinstance(task_name, str) and task_name and task_name != current_file:
                                    # Try to infer file extension
                                    if not any(task_name.lower().endswith(ext) for ext in ['.3mf', '.gcode', '.bgcode']):
                                        task_name += '.3mf'  # Most common format
                                    files.append(PrinterFile(
                                        filename=task_name,
                                        size=0,
                                        path=f"task/{task_name}",
                                        modified=None,
                                        file_type=self._get_file_type_from_name(task_name)
                                    ))
                    
                    # Check for SD card or storage information
                    if 'system' in mqtt_data:
                        system_data = mqtt_data['system']
                        if isinstance(system_data, dict):
                            # Look for storage or file system info
                            for key in ['sdcard', 'storage', 'files']:
                                if key in system_data:
                                    storage_info = system_data[key]
                                    if isinstance(storage_info, dict) and 'files' in storage_info:
                                        file_list = storage_info['files']
                                        if isinstance(file_list, list):
                                            for file_info in file_list:
                                                if isinstance(file_info, dict) and 'name' in file_info:
                                                    filename = file_info['name']
                                                    files.append(PrinterFile(
                                                        filename=filename,
                                                        size=file_info.get('size', 0),
                                                        path=f"{key}/{filename}",
                                                        modified=None,
                                                        file_type=self._get_file_type_from_name(filename)
                                                    ))
                                                    
        except Exception as e:
            logger.debug("MQTT dump file discovery error", error=str(e))
            
        return files

    async def _list_files_mqtt(self) -> List[PrinterFile]:
        """List files using direct MQTT (fallback)."""
        # If we're using bambu_api, we should use the bambu_client's MQTT data
        if self.use_bambu_api:
            return await self._list_files_mqtt_from_bambu_api()
        
        # Direct MQTT mode
        if not self.client:
            raise PrinterConnectionError(self.printer_id, "MQTT client not initialized")
        
        logger.info("Requesting file list from Bambu Lab printer via MQTT",
                   printer_id=self.printer_id)
        
        files = []
        
        try:
            # Extract file information from latest MQTT data
            if self.latest_data and isinstance(self.latest_data, dict):
                # Check for current print job information
                print_data = self.latest_data.get('print', {})
                if isinstance(print_data, dict):
                    # Current file being printed
                    current_file = print_data.get('file', '')
                    if current_file and isinstance(current_file, str):
                        files.append(PrinterFile(
                            filename=current_file,
                            size=0,  # Size not available via MQTT
                            path=f"current/{current_file}",
                            modified=None,
                            file_type=self._get_file_type_from_name(current_file)
                        ))
                    
                    # Task name might be different from filename
                    task_name = print_data.get('task_name', '')
                    if (task_name and isinstance(task_name, str) 
                        and task_name != current_file and task_name not in [f.filename for f in files]):
                        # Infer file extension if missing
                        if not any(task_name.lower().endswith(ext) for ext in ['.3mf', '.gcode', '.bgcode']):
                            task_name += '.3mf'
                        files.append(PrinterFile(
                            filename=task_name,
                            size=0,
                            path=f"task/{task_name}",
                            modified=None,
                            file_type=self._get_file_type_from_name(task_name)
                        ))
                
                # Look for any file system information
                # Note: Bambu Lab MQTT doesn't typically provide file listing
                # but may contain references to recently uploaded files
                for key in ['system', 'info', 'status']:
                    if key in self.latest_data:
                        data_section = self.latest_data[key]
                        if isinstance(data_section, dict):
                            # Look for file references in various fields
                            for subkey, value in data_section.items():
                                if (isinstance(value, str) and 
                                    any(value.lower().endswith(ext) for ext in ['.3mf', '.gcode', '.bgcode']) and
                                    value not in [f.filename for f in files]):
                                    files.append(PrinterFile(
                                        filename=value,
                                        size=0,
                                        path=f"{key}/{value}",
                                        modified=None,
                                        file_type=self._get_file_type_from_name(value)
                                    ))
            
            # If no files found, provide informative logging
            if len(files) == 0:
                logger.info("No files found in MQTT data - this is normal as Bambu Lab doesn't provide file listing via MQTT",
                           printer_id=self.printer_id)
                logger.debug("MQTT data keys available", keys=list(self.latest_data.keys()) if self.latest_data else [])
            else:
                logger.info("Extracted file references from MQTT data",
                           printer_id=self.printer_id, file_count=len(files))
                           
        except Exception as e:
            logger.warning("Failed to extract files from MQTT data", 
                          printer_id=self.printer_id, error=str(e))
        
        return files

    async def _list_files_mqtt_from_bambu_api(self) -> List[PrinterFile]:
        """Extract file references from bambulabs_api MQTT data."""
        files = []
        
        try:
            # Get MQTT dump from bambulabs_api client
            if hasattr(self.bambu_client, 'mqtt_dump'):
                mqtt_data = self.bambu_client.mqtt_dump()
                
                if isinstance(mqtt_data, dict):
                    # Look for print information
                    if 'print' in mqtt_data:
                        print_data = mqtt_data['print']
                        if isinstance(print_data, dict):
                            # Current file being printed
                            if 'gcode_file' in print_data:
                                current_file = print_data['gcode_file']
                                if isinstance(current_file, str) and current_file:
                                    files.append(PrinterFile(
                                        filename=current_file,
                                        size=0,
                                        path=f"current/{current_file}",
                                        modified=None,
                                        file_type=self._get_file_type_from_name(current_file)
                                    ))
                            
                            # Task name
                            if 'subtask_name' in print_data:
                                task_name = print_data['subtask_name']
                                if (isinstance(task_name, str) and task_name and
                                    task_name not in [f.filename for f in files]):
                                    if not any(task_name.lower().endswith(ext) for ext in ['.3mf', '.gcode', '.bgcode']):
                                        task_name += '.3mf'
                                    files.append(PrinterFile(
                                        filename=task_name,
                                        size=0,
                                        path=f"task/{task_name}",
                                        modified=None,
                                        file_type=self._get_file_type_from_name(task_name)
                                    ))
                    
                    logger.info("Extracted files from bambulabs_api MQTT data",
                               printer_id=self.printer_id, file_count=len(files))
                    
        except Exception as e:
            logger.debug("Failed to extract files from bambulabs_api MQTT data", 
                        printer_id=self.printer_id, error=str(e))
        
        return files

    async def _list_files_direct_ftp(self) -> List[PrinterFile]:
        """List files using direct FTP connection."""
        if not self.ftp_service:
            raise PrinterConnectionError(self.printer_id, "Direct FTP service not available")

        logger.info("Listing files via direct FTP",
                   printer_id=self.printer_id)

        try:
            # Get files from cache directory (primary location for 3D files)
            ftp_files = await self.ftp_service.list_files("/cache")

            # Convert BambuFTPFile objects to PrinterFile objects
            printer_files = []
            for ftp_file in ftp_files:
                printer_file = PrinterFile(
                    filename=ftp_file.name,
                    size=ftp_file.size,
                    path=f"cache/{ftp_file.name}",
                    modified=ftp_file.modified,
                    file_type=ftp_file.file_type
                )
                printer_files.append(printer_file)

            logger.info("Direct FTP file listing successful",
                       printer_id=self.printer_id,
                       file_count=len(printer_files))

            return printer_files

        except Exception as e:
            logger.error("Direct FTP file listing failed",
                        printer_id=self.printer_id, error=str(e))
            raise


    def _get_file_type_from_name(self, filename: str) -> str:
        """Extract file type from filename extension."""
        from pathlib import Path
        ext = Path(filename).suffix.lower()
        type_map = {
            '.3mf': '3mf',
            '.stl': 'stl',
            '.obj': 'obj',
            '.gcode': 'gcode',
            '.bgcode': 'bgcode',
            '.ply': 'ply'
        }
        return type_map.get(ext, 'unknown')
            
    async def download_file(self, filename: str, local_path: str) -> bool:
        """Download a file from Bambu Lab printer using download strategy pattern.

        Args:
            filename: Name of the file to download
            local_path: Local filesystem path to save the file

        Returns:
            True if download succeeded, False otherwise

        Raises:
            PrinterConnectionError: If printer is not connected
        """
        if not self.is_connected:
            raise PrinterConnectionError(self.printer_id, "Not connected")

        if not self.download_handler:
            logger.error(
                "Download handler not initialized",
                printer_id=self.printer_id
            )
            return False

        try:
            logger.info(
                "Downloading file using download handler",
                printer_id=self.printer_id,
                filename=filename,
                local_path=local_path
            )

            # Use download handler with automatic retry and fallback
            result = await self.download_handler.download(filename, local_path)

            if result.success:
                logger.info(
                    "File download successful",
                    printer_id=self.printer_id,
                    filename=filename,
                    strategy=result.strategy_used,
                    size=result.size_bytes,
                    attempts=result.attempts
                )
                return True
            else:
                logger.error(
                    "File download failed",
                    printer_id=self.printer_id,
                    filename=filename,
                    error=result.error,
                    attempts=result.attempts
                )
                return False

        except Exception as e:
            logger.error(
                "Unexpected error during file download",
                printer_id=self.printer_id,
                filename=filename,
                error=str(e)
            )
            return False

    async def pause_print(self) -> bool:
        """Pause the current print job on Bambu Lab printer."""
        if not self.is_connected or not self.client:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            logger.info("Pausing print on Bambu Lab printer", printer_id=self.printer_id)
            
            # Send pause command using bambulabs-api
            result = self.client.pause()
            
            if result:
                logger.info("Successfully paused print", printer_id=self.printer_id)
                return True
            else:
                logger.warning("Failed to pause print", printer_id=self.printer_id)
                return False
                
        except Exception as e:
            logger.error("Error pausing print on Bambu Lab",
                        printer_id=self.printer_id, error=str(e))
            return False
            
    async def resume_print(self) -> bool:
        """Resume the paused print job on Bambu Lab printer."""
        if not self.is_connected or not self.client:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            logger.info("Resuming print on Bambu Lab printer", printer_id=self.printer_id)
            
            # Send resume command using bambulabs-api
            result = self.client.resume()
            
            if result:
                logger.info("Successfully resumed print", printer_id=self.printer_id)
                return True
            else:
                logger.warning("Failed to resume print", printer_id=self.printer_id)
                return False
                
        except Exception as e:
            logger.error("Error resuming print on Bambu Lab",
                        printer_id=self.printer_id, error=str(e))
            return False
            
    async def stop_print(self) -> bool:
        """Stop/cancel the current print job on Bambu Lab printer."""
        if not self.is_connected or not self.client:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            logger.info("Stopping print on Bambu Lab printer", printer_id=self.printer_id)
            
            # Send stop command using bambulabs-api
            result = self.client.stop()
            
            if result:
                logger.info("Successfully stopped print", printer_id=self.printer_id)
                return True
            else:
                logger.warning("Failed to stop print", printer_id=self.printer_id)
                return False
                
        except Exception as e:
            logger.error("Error stopping print on Bambu Lab",
                        printer_id=self.printer_id, error=str(e))
            return False

    async def has_camera(self) -> bool:
        """Check if Bambu Lab printer has camera support.

        All Bambu Lab A1 and P1 series printers have built-in cameras.
        Camera functionality is now handled by CameraSnapshotService.
        """
        # All Bambu Lab A1/P1 series printers have cameras
        # Connection to camera is managed by CameraSnapshotService via TCP/TLS
        return True

    async def get_camera_stream_url(self) -> Optional[str]:
        """Get camera stream URL for Bambu Lab printer.

        DEPRECATED: Live streaming not yet implemented.
        Bambu Lab cameras use proprietary TCP/TLS protocol on port 6000.
        Use CameraSnapshotService for snapshot functionality.
        Live MJPEG streaming planned for future implementation.
        """
        logger.warning(
            "get_camera_stream_url is deprecated - live streaming not yet implemented",
            printer_id=self.printer_id
        )
        return None

    async def take_snapshot(self) -> Optional[bytes]:
        """Take a camera snapshot from Bambu Lab printer using bambulabs-api library.

        Returns:
            JPEG image data as bytes, or None if camera unavailable

        Raises:
            Exception: If camera access fails
        """
        if not self.bambu_client:
            logger.error(
                "Cannot take snapshot - Bambu client not connected",
                printer_id=self.printer_id
            )
            return None

        try:
            logger.debug("Requesting camera snapshot", printer_id=self.printer_id)

            # Run blocking camera call in executor to maintain async compatibility
            loop = asyncio.get_event_loop()
            image = await loop.run_in_executor(
                None,
                self.bambu_client.get_camera_image
            )

            if not image:
                logger.warning(
                    "No camera image available from printer",
                    printer_id=self.printer_id
                )
                return None

            # Convert PIL Image to JPEG bytes
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            jpeg_bytes = buffer.getvalue()

            logger.info(
                "Camera snapshot captured successfully",
                printer_id=self.printer_id,
                size_bytes=len(jpeg_bytes)
            )

            return jpeg_bytes

        except AttributeError as e:
            logger.error(
                "bambulabs-api camera method not available - may not support A1 series",
                printer_id=self.printer_id,
                error=str(e)
            )
            return None

        except Exception as e:
            logger.error(
                "Camera snapshot failed",
                printer_id=self.printer_id,
                error=str(e),
                error_type=type(e).__name__
            )
            return None