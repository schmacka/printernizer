"""
OctoPrint SockJS WebSocket client for real-time printer updates.
Handles push-based status updates from OctoPrint's SockJS API.
"""
import asyncio
import json
import random
import string
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime
import aiohttp
import structlog

from src.constants import OctoPrintConstants

logger = structlog.get_logger()


class OctoPrintSockJSClient:
    """
    SockJS WebSocket client for OctoPrint real-time updates.

    Connects to OctoPrint's SockJS endpoint and receives push notifications
    for printer state, job progress, and events.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        on_status_update: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        on_event: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None,
        printer_id: str = "unknown"
    ):
        """
        Initialize SockJS client.

        Args:
            base_url: OctoPrint base URL (e.g., http://192.168.1.100)
            api_key: OctoPrint API key for authentication
            on_status_update: Callback for status updates (current/history messages)
            on_event: Callback for event notifications
            printer_id: Printer identifier for logging
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.on_status_update = on_status_update
        self.on_event = on_event
        self.printer_id = printer_id

        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._connected = False
        self._stop_event = asyncio.Event()
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        # Latest cached data from push updates
        self.latest_state: Optional[Dict[str, Any]] = None
        self.latest_temps: Optional[Dict[str, Any]] = None
        self.latest_job: Optional[Dict[str, Any]] = None
        self.latest_progress: Optional[Dict[str, Any]] = None

        # Reconnection state
        self._reconnect_attempts = 0
        self._last_connect_time: Optional[datetime] = None

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected and self._ws is not None and not self._ws.closed

    def _generate_session_id(self) -> str:
        """Generate random session ID for SockJS."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    def _generate_server_id(self) -> str:
        """Generate random server ID for SockJS (3 digits)."""
        return str(random.randint(100, 999))

    async def connect(self) -> bool:
        """
        Connect to OctoPrint SockJS endpoint.

        Returns:
            True if connection established successfully.
        """
        if self.is_connected:
            logger.debug("SockJS already connected", printer_id=self.printer_id)
            return True

        try:
            logger.info("Connecting to OctoPrint SockJS",
                       printer_id=self.printer_id, base_url=self.base_url)

            # Create session if needed
            if self._session is None or self._session.closed:
                timeout = aiohttp.ClientTimeout(
                    total=OctoPrintConstants.REQUEST_TIMEOUT_SECONDS,
                    connect=OctoPrintConstants.CONNECT_TIMEOUT_SECONDS
                )
                self._session = aiohttp.ClientSession(timeout=timeout)

            # Build SockJS WebSocket URL
            # Format: /sockjs/{server_id}/{session_id}/websocket
            server_id = self._generate_server_id()
            session_id = self._generate_session_id()
            ws_url = f"{self.base_url}/sockjs/{server_id}/{session_id}/websocket"

            # Convert http to ws for WebSocket
            if ws_url.startswith('https://'):
                ws_url = ws_url.replace('https://', 'wss://', 1)
            elif ws_url.startswith('http://'):
                ws_url = ws_url.replace('http://', 'ws://', 1)

            logger.debug("Connecting to SockJS WebSocket",
                        printer_id=self.printer_id, url=ws_url)

            # Connect with API key header
            headers = {OctoPrintConstants.AUTH_HEADER: self.api_key}
            self._ws = await self._session.ws_connect(
                ws_url,
                headers=headers,
                heartbeat=OctoPrintConstants.SOCKJS_HEARTBEAT_MS / 1000
            )

            self._connected = True
            self._reconnect_attempts = 0
            self._last_connect_time = datetime.now()
            self._stop_event.clear()

            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_loop())

            logger.info("SockJS connected successfully", printer_id=self.printer_id)
            return True

        except aiohttp.ClientError as e:
            logger.error("SockJS connection failed",
                        printer_id=self.printer_id, error=str(e))
            self._connected = False
            return False
        except Exception as e:
            logger.error("Unexpected error connecting to SockJS",
                        printer_id=self.printer_id, error=str(e), exc_info=True)
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from SockJS and cleanup resources."""
        logger.info("Disconnecting SockJS client", printer_id=self.printer_id)

        self._stop_event.set()
        self._connected = False

        # Cancel receive task
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        # Cancel reconnect task
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None

        # Close WebSocket
        if self._ws and not self._ws.closed:
            await self._ws.close()
        self._ws = None

        # Close session
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

        logger.info("SockJS client disconnected", printer_id=self.printer_id)

    async def _receive_loop(self) -> None:
        """Main loop for receiving and processing SockJS messages."""
        while not self._stop_event.is_set() and self._ws and not self._ws.closed:
            try:
                msg = await self._ws.receive(timeout=30)

                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.warning("SockJS connection closed by server",
                                  printer_id=self.printer_id)
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error("SockJS WebSocket error",
                                printer_id=self.printer_id,
                                error=str(self._ws.exception()))
                    break

            except asyncio.TimeoutError:
                # No message received, continue loop
                continue
            except asyncio.CancelledError:
                logger.debug("SockJS receive loop cancelled", printer_id=self.printer_id)
                raise
            except Exception as e:
                logger.error("Error in SockJS receive loop",
                            printer_id=self.printer_id, error=str(e))
                break

        # Connection lost, attempt reconnection if not stopping
        if not self._stop_event.is_set():
            self._connected = False
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _handle_message(self, raw_message: str) -> None:
        """
        Parse and handle a SockJS message.

        SockJS messages have specific framing:
        - 'o' = open frame
        - 'h' = heartbeat
        - 'c' = close frame
        - 'a[...]' = array of JSON messages
        """
        if not raw_message:
            return

        frame_type = raw_message[0]

        if frame_type == 'o':
            # Open frame - connection established
            logger.debug("SockJS open frame received", printer_id=self.printer_id)
            # Send auth message
            await self._send_auth()

        elif frame_type == 'h':
            # Heartbeat frame
            logger.debug("SockJS heartbeat received", printer_id=self.printer_id)

        elif frame_type == 'c':
            # Close frame
            logger.info("SockJS close frame received", printer_id=self.printer_id)
            self._connected = False

        elif frame_type == 'a':
            # Array of messages
            try:
                messages = json.loads(raw_message[1:])
                for msg_str in messages:
                    try:
                        msg = json.loads(msg_str) if isinstance(msg_str, str) else msg_str
                        await self._process_message(msg)
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in SockJS message",
                                      printer_id=self.printer_id, message=msg_str[:100])
            except json.JSONDecodeError:
                logger.warning("Invalid SockJS array frame",
                              printer_id=self.printer_id, data=raw_message[:100])
        else:
            logger.debug("Unknown SockJS frame type",
                        printer_id=self.printer_id, frame=frame_type)

    async def _send_auth(self) -> None:
        """Send authentication message to OctoPrint."""
        if not self._ws or self._ws.closed:
            return

        # OctoPrint expects auth in format: {"auth": "user:session"}
        # For API key auth, we can use a simplified format
        auth_msg = json.dumps({"auth": f"{self.api_key}:"})

        # SockJS requires message to be wrapped in array
        await self._ws.send_str(json.dumps([auth_msg]))
        logger.debug("SockJS auth message sent", printer_id=self.printer_id)

    async def _process_message(self, msg: Dict[str, Any]) -> None:
        """
        Process an OctoPrint push message.

        Message types:
        - connected: Initial connection confirmation
        - current: Periodic state update
        - history: Full history on connect
        - event: Event notification
        - plugin: Plugin-specific message
        """
        if not isinstance(msg, dict):
            return

        # Handle different message types
        if 'connected' in msg:
            logger.info("OctoPrint SockJS authenticated",
                       printer_id=self.printer_id,
                       version=msg.get('connected', {}).get('version'))

        elif 'current' in msg:
            # Most common message - periodic state update
            current = msg['current']
            await self._handle_current_update(current)

        elif 'history' in msg:
            # Full history on initial connect
            history = msg['history']
            if history:
                # Process most recent state
                await self._handle_current_update(history)

        elif 'event' in msg:
            # Event notification
            event = msg['event']
            event_type = event.get('type', 'unknown')
            event_payload = event.get('payload', {})

            logger.debug("OctoPrint event received",
                        printer_id=self.printer_id,
                        event_type=event_type)

            if self.on_event:
                try:
                    await self.on_event(event_type, event_payload)
                except Exception as e:
                    logger.error("Error in event callback",
                                printer_id=self.printer_id, error=str(e))

        elif 'plugin' in msg:
            # Plugin-specific message - log but don't process
            logger.debug("OctoPrint plugin message",
                        printer_id=self.printer_id,
                        plugin=msg.get('plugin'))

    async def _handle_current_update(self, current: Dict[str, Any]) -> None:
        """Handle 'current' state update from OctoPrint."""
        # Cache the data
        self.latest_state = current.get('state')
        self.latest_temps = current.get('temps', [{}])[-1] if current.get('temps') else None
        self.latest_job = current.get('job')
        self.latest_progress = current.get('progress')

        # Invoke callback
        if self.on_status_update:
            try:
                await self.on_status_update(current)
            except Exception as e:
                logger.error("Error in status update callback",
                            printer_id=self.printer_id, error=str(e))

    async def _reconnect_loop(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        while not self._stop_event.is_set():
            self._reconnect_attempts += 1

            if self._reconnect_attempts > OctoPrintConstants.SOCKJS_MAX_RECONNECT_ATTEMPTS:
                logger.error("SockJS max reconnection attempts exceeded",
                            printer_id=self.printer_id,
                            attempts=self._reconnect_attempts)
                break

            # Calculate backoff delay with jitter
            delay = min(
                OctoPrintConstants.SOCKJS_RECONNECT_DELAY_SECONDS *
                (OctoPrintConstants.SOCKJS_RECONNECT_BACKOFF_MULTIPLIER ** (self._reconnect_attempts - 1)),
                OctoPrintConstants.SOCKJS_MAX_RECONNECT_DELAY_SECONDS
            )
            # Add jitter (±10%)
            delay *= 1 + random.uniform(-0.1, 0.1)

            logger.info("Attempting SockJS reconnection",
                       printer_id=self.printer_id,
                       attempt=self._reconnect_attempts,
                       delay=f"{delay:.1f}s")

            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                break

            if self._stop_event.is_set():
                break

            # Attempt reconnection
            if await self.connect():
                logger.info("SockJS reconnection successful",
                           printer_id=self.printer_id)
                break

    def get_cached_status(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest cached status from push updates.

        Returns:
            Dict with state, temps, job, progress or None if no data.
        """
        if not any([self.latest_state, self.latest_temps,
                    self.latest_job, self.latest_progress]):
            return None

        return {
            'state': self.latest_state,
            'temps': self.latest_temps,
            'job': self.latest_job,
            'progress': self.latest_progress
        }
