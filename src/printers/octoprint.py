"""
OctoPrint printer integration for Printernizer.
Handles HTTP API communication and SockJS WebSocket push updates.
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import aiohttp
import structlog

from src.models.printer import PrinterStatus, PrinterStatusUpdate, Filament
from src.utils.errors import PrinterConnectionError
from .base import BasePrinter, JobInfo, JobStatus, PrinterFile
from src.constants import OctoPrintConstants, FileConstants
from src.services.octoprint_sockjs_client import OctoPrintSockJSClient

logger = structlog.get_logger()


class OctoPrintPrinter(BasePrinter):
    """OctoPrint printer implementation using REST API and SockJS push updates."""

    def __init__(
        self,
        printer_id: str,
        name: str,
        ip_address: str,
        api_key: str,
        port: int = 80,
        use_https: bool = False,
        file_service=None,
        **kwargs
    ):
        """
        Initialize OctoPrint printer.

        Args:
            printer_id: Unique identifier for this printer
            name: Human-readable printer name
            ip_address: IP address or hostname of OctoPrint server
            api_key: OctoPrint API key
            port: HTTP port (default 80)
            use_https: Use HTTPS instead of HTTP
            file_service: Optional file service for downloads
        """
        super().__init__(printer_id, name, ip_address, **kwargs)
        self.api_key = api_key
        self.port = port
        self.use_https = use_https
        self.file_service = file_service

        # Build base URL
        protocol = 'https' if use_https else 'http'
        if port in (80, 443):
            self.base_url = f"{protocol}://{ip_address}"
        else:
            self.base_url = f"{protocol}://{ip_address}:{port}"

        self.api_url = f"{self.base_url}/api"

        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None

        # SockJS client for real-time updates
        self.sockjs_client: Optional[OctoPrintSockJSClient] = None

        # Cached webcam settings
        self._webcam_settings: Optional[Dict[str, Any]] = None
        self._webcam_settings_fetched = False

    async def connect(self) -> bool:
        """Establish HTTP and WebSocket connections to OctoPrint."""
        if self.is_connected:
            logger.info("Already connected to OctoPrint",
                       printer_id=self.printer_id)
            return True

        try:
            logger.info("Connecting to OctoPrint",
                       printer_id=self.printer_id, url=self.base_url)

            # Create HTTP session
            headers = {
                OctoPrintConstants.AUTH_HEADER: self.api_key,
                'Content-Type': 'application/json'
            }
            timeout = aiohttp.ClientTimeout(
                total=OctoPrintConstants.REQUEST_TIMEOUT_SECONDS,
                connect=OctoPrintConstants.CONNECT_TIMEOUT_SECONDS
            )
            connector = aiohttp.TCPConnector(
                limit=10,
                enable_cleanup_closed=True
            )
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
                connector=connector
            )

            # Test connection with version endpoint
            max_retries = OctoPrintConstants.MAX_RETRIES
            for attempt in range(max_retries):
                try:
                    async with self.session.get(
                        f"{self.api_url}{OctoPrintConstants.API_VERSION}"
                    ) as response:
                        if response.status == 200:
                            version_data = await response.json()
                            logger.info("Connected to OctoPrint",
                                       printer_id=self.printer_id,
                                       server=version_data.get('server'),
                                       api=version_data.get('api'),
                                       attempt=attempt + 1)
                            break
                        elif response.status == 401:
                            raise aiohttp.ClientError("Authentication failed - check API key")
                        elif response.status == 403:
                            raise aiohttp.ClientError("Access forbidden - check API key permissions")
                        else:
                            raise aiohttp.ClientError(f"HTTP {response.status}")

                except (asyncio.TimeoutError, aiohttp.ClientConnectorError) as e:
                    if attempt < max_retries - 1:
                        wait_time = OctoPrintConstants.RETRY_DELAY_SECONDS * \
                                   (OctoPrintConstants.RETRY_BACKOFF_MULTIPLIER ** attempt)
                        logger.warning("Connection attempt failed, retrying",
                                      printer_id=self.printer_id,
                                      attempt=attempt + 1,
                                      wait_time=wait_time,
                                      error=str(e))
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise

            # Initialize SockJS client for real-time updates
            self.sockjs_client = OctoPrintSockJSClient(
                base_url=self.base_url,
                api_key=self.api_key,
                on_status_update=self._on_sockjs_status_update,
                on_event=self._on_sockjs_event,
                printer_id=self.printer_id
            )

            # Connect SockJS (non-blocking - runs in background)
            asyncio.create_task(self._connect_sockjs())

            self.is_connected = True
            return True

        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as e:
            error_msg = f"Cannot connect to OctoPrint: {str(e)}"
            logger.error("OctoPrint connection failed",
                        printer_id=self.printer_id, url=self.base_url, error=error_msg)
            await self._cleanup_session()
            raise PrinterConnectionError(self.printer_id, error_msg)
        except aiohttp.ClientTimeout as e:
            error_msg = f"Connection timeout: {str(e)}"
            logger.error("OctoPrint connection timeout",
                        printer_id=self.printer_id, url=self.base_url, error=error_msg)
            await self._cleanup_session()
            raise PrinterConnectionError(self.printer_id, error_msg)
        except aiohttp.ClientResponseError as e:
            error_msg = f"HTTP {e.status}: {e.message}"
            logger.error("OctoPrint HTTP error",
                        printer_id=self.printer_id, status=e.status, error=error_msg)
            await self._cleanup_session()
            raise PrinterConnectionError(self.printer_id, error_msg)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}: Connection failed"
            logger.error("Unexpected error connecting to OctoPrint",
                        printer_id=self.printer_id, error=error_msg, exc_info=True)
            await self._cleanup_session()
            raise PrinterConnectionError(self.printer_id, error_msg)

    async def _connect_sockjs(self) -> None:
        """Connect SockJS client in background."""
        try:
            await self.sockjs_client.connect()
        except Exception as e:
            logger.warning("SockJS connection failed, falling back to polling",
                          printer_id=self.printer_id, error=str(e))

    async def _cleanup_session(self) -> None:
        """Cleanup HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def disconnect(self) -> None:
        """Disconnect from OctoPrint."""
        if not self.is_connected:
            return

        try:
            # Disconnect SockJS
            if self.sockjs_client:
                await self.sockjs_client.disconnect()
                self.sockjs_client = None

            # Close HTTP session
            await self._cleanup_session()

            self.is_connected = False
            self._webcam_settings = None
            self._webcam_settings_fetched = False

            logger.info("Disconnected from OctoPrint", printer_id=self.printer_id)

        except Exception as e:
            logger.error("Error disconnecting from OctoPrint",
                        printer_id=self.printer_id, error=str(e), exc_info=True)

    async def _on_sockjs_status_update(self, current: Dict[str, Any]) -> None:
        """Handle status update from SockJS."""
        # This is called by the SockJS client when it receives a 'current' message
        # The data is cached in the SockJS client, we can use it in get_status()
        logger.debug("SockJS status update received", printer_id=self.printer_id)

    async def _on_sockjs_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle event from SockJS."""
        logger.debug("SockJS event received",
                    printer_id=self.printer_id,
                    event_type=event_type)

    def _map_octoprint_status(self, state: Optional[Dict[str, Any]]) -> PrinterStatus:
        """Map OctoPrint state flags to PrinterStatus."""
        if not state:
            return PrinterStatus.UNKNOWN

        flags = state.get('flags', {})
        text = state.get('text', '').lower()

        # Check flags first (more reliable)
        if flags.get('error'):
            return PrinterStatus.ERROR
        if flags.get('printing'):
            return PrinterStatus.PRINTING
        if flags.get('paused') or flags.get('pausing'):
            return PrinterStatus.PAUSED
        if flags.get('operational') or flags.get('ready'):
            return PrinterStatus.ONLINE
        if flags.get('closedOrError') or flags.get('closed'):
            return PrinterStatus.OFFLINE

        # Fallback to text parsing
        if 'error' in text:
            return PrinterStatus.ERROR
        if 'printing' in text:
            return PrinterStatus.PRINTING
        if 'paus' in text:
            return PrinterStatus.PAUSED
        if 'operational' in text or 'ready' in text:
            return PrinterStatus.ONLINE
        if 'offline' in text or 'closed' in text:
            return PrinterStatus.OFFLINE

        return PrinterStatus.UNKNOWN

    def _map_job_status(self, state: Optional[Dict[str, Any]]) -> JobStatus:
        """Map OctoPrint state to JobStatus."""
        if not state:
            return JobStatus.IDLE

        flags = state.get('flags', {})

        if flags.get('printing'):
            return JobStatus.PRINTING
        if flags.get('paused') or flags.get('pausing'):
            return JobStatus.PAUSED
        if flags.get('cancelling'):
            return JobStatus.CANCELLED

        return JobStatus.IDLE

    async def get_status(self) -> PrinterStatusUpdate:
        """Get current printer status."""
        # Try to use cached SockJS data first
        if self.sockjs_client and self.sockjs_client.is_connected:
            cached = self.sockjs_client.get_cached_status()
            if cached:
                return self._build_status_update(cached)

        # Fallback to REST API
        return await self._get_status_via_rest()

    async def _get_status_via_rest(self) -> PrinterStatusUpdate:
        """Get status via REST API."""
        if not self.session:
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=PrinterStatus.OFFLINE,
                message="Not connected",
                timestamp=datetime.now()
            )

        try:
            async with self.session.get(
                f"{self.api_url}{OctoPrintConstants.API_PRINTER}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._build_status_update({
                        'state': data.get('state'),
                        'temps': data.get('temperature'),
                        'job': None,  # Need separate call
                        'progress': None
                    })
                elif response.status == 409:
                    # Printer not connected to OctoPrint
                    return PrinterStatusUpdate(
                        printer_id=self.printer_id,
                        status=PrinterStatus.OFFLINE,
                        message="Printer not connected to OctoPrint",
                        timestamp=datetime.now()
                    )
                else:
                    logger.warning("Failed to get OctoPrint status",
                                  printer_id=self.printer_id,
                                  status=response.status)
                    return PrinterStatusUpdate(
                        printer_id=self.printer_id,
                        status=PrinterStatus.UNKNOWN,
                        message=f"HTTP {response.status}",
                        timestamp=datetime.now()
                    )

        except Exception as e:
            logger.error("Error getting OctoPrint status",
                        printer_id=self.printer_id, error=str(e))
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=PrinterStatus.ERROR,
                message=str(e),
                timestamp=datetime.now()
            )

    def _build_status_update(self, data: Dict[str, Any]) -> PrinterStatusUpdate:
        """Build PrinterStatusUpdate from OctoPrint data."""
        state = data.get('state')
        temps = data.get('temps')
        job = data.get('job')
        progress = data.get('progress')

        status = self._map_octoprint_status(state)

        # Extract temperatures
        temp_bed = None
        temp_nozzle = None
        if temps:
            if isinstance(temps, dict):
                # From REST API: {bed: {actual, target}, tool0: {actual, target}}
                if 'bed' in temps:
                    temp_bed = temps['bed'].get('actual')
                if 'tool0' in temps:
                    temp_nozzle = temps['tool0'].get('actual')
            elif isinstance(temps, list) and temps:
                # From SockJS history
                last_temp = temps[-1] if temps else {}
                if 'bed' in last_temp:
                    temp_bed = last_temp['bed'].get('actual')
                if 'tool0' in last_temp:
                    temp_nozzle = last_temp['tool0'].get('actual')

        # Extract job info
        current_job = None
        progress_pct = None
        remaining_mins = None
        elapsed_mins = None

        if job and job.get('file', {}).get('name'):
            current_job = job['file']['name']

        if progress:
            if progress.get('completion') is not None:
                progress_pct = int(progress['completion'])
            if progress.get('printTimeLeft') is not None:
                remaining_mins = progress['printTimeLeft'] // 60
            if progress.get('printTime') is not None:
                elapsed_mins = progress['printTime'] // 60

        # Extract filament info (if available)
        filaments = self._extract_filaments(job)

        return PrinterStatusUpdate(
            printer_id=self.printer_id,
            status=status,
            message=state.get('text') if state else None,
            temperature_bed=temp_bed,
            temperature_nozzle=temp_nozzle,
            progress=progress_pct,
            current_job=current_job,
            remaining_time_minutes=remaining_mins,
            elapsed_time_minutes=elapsed_mins,
            filaments=filaments if filaments else None,
            timestamp=datetime.now(),
            raw_data=data
        )

    def _extract_filaments(self, job: Optional[Dict[str, Any]]) -> List[Filament]:
        """Extract filament information from job data."""
        filaments = []

        if not job or 'filament' not in job:
            return filaments

        filament_data = job.get('filament', {})
        if not isinstance(filament_data, dict):
            return filaments

        # OctoPrint reports filament per tool: tool0, tool1, etc.
        for tool_key, tool_data in filament_data.items():
            if not tool_key.startswith('tool') or not isinstance(tool_data, dict):
                continue

            try:
                slot = int(tool_key[4:])  # Extract number from 'tool0'
            except (ValueError, IndexError):
                slot = 0

            # OctoPrint provides length and volume, not color/type directly
            # Color/type would come from slicer metadata if available
            filaments.append(Filament(
                slot=slot,
                color=None,
                type=None,
                is_active=(slot == 0)  # First tool is typically active
            ))

        return filaments

    async def get_job_info(self) -> Optional[JobInfo]:
        """Get current job information."""
        if not self.session:
            return None

        try:
            async with self.session.get(
                f"{self.api_url}{OctoPrintConstants.API_JOB}"
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                job = data.get('job', {})
                progress = data.get('progress', {})
                state = data.get('state', '')

                file_info = job.get('file', {})
                if not file_info.get('name'):
                    return None

                job_status = JobStatus.IDLE
                if 'printing' in state.lower():
                    job_status = JobStatus.PRINTING
                elif 'paus' in state.lower():
                    job_status = JobStatus.PAUSED

                return JobInfo(
                    job_id=file_info.get('name', 'unknown'),
                    name=file_info.get('display', file_info.get('name', 'Unknown')),
                    status=job_status,
                    progress=int(progress.get('completion', 0) or 0),
                    estimated_time=job.get('estimatedPrintTime'),
                    elapsed_time=progress.get('printTime')
                )

        except Exception as e:
            logger.error("Error getting OctoPrint job info",
                        printer_id=self.printer_id, error=str(e))
            return None

    async def list_files(self) -> List[PrinterFile]:
        """List files available on OctoPrint."""
        if not self.session:
            return []

        files = []

        try:
            # Get files from both local and SD card
            async with self.session.get(
                f"{self.api_url}{OctoPrintConstants.API_FILES}?recursive=true"
            ) as response:
                if response.status != 200:
                    logger.warning("Failed to list OctoPrint files",
                                  printer_id=self.printer_id,
                                  status=response.status)
                    return []

                data = await response.json()

                # Process local files
                for file_data in data.get('files', []):
                    files.extend(self._extract_files(file_data, 'local'))

        except Exception as e:
            logger.error("Error listing OctoPrint files",
                        printer_id=self.printer_id, error=str(e))

        return files

    def _extract_files(self, file_data: Dict[str, Any], origin: str) -> List[PrinterFile]:
        """Recursively extract files from OctoPrint file data."""
        files = []

        file_type = file_data.get('type', '')

        if file_type == 'folder':
            # Recurse into folder
            for child in file_data.get('children', []):
                files.extend(self._extract_files(child, origin))
        elif file_type in ('machinecode', 'model'):
            # It's a printable file
            name = file_data.get('name', '')
            path = file_data.get('path', name)

            modified = None
            if file_data.get('date'):
                try:
                    modified = datetime.fromtimestamp(file_data['date'])
                except (ValueError, OSError):
                    pass

            files.append(PrinterFile(
                filename=name,
                size=file_data.get('size'),
                modified=modified,
                path=f"{origin}/{path}"
            ))

        return files

    async def download_file(self, filename: str, local_path: str) -> bool:
        """Download a file from OctoPrint."""
        if not self.session:
            return False

        try:
            # Parse filename to get origin and path
            # Format: origin/path or just path (defaults to local)
            if '/' in filename and filename.split('/')[0] in ('local', 'sdcard'):
                parts = filename.split('/', 1)
                origin = parts[0]
                file_path = parts[1]
            else:
                origin = 'local'
                file_path = filename

            # Get file info to find download URL
            async with self.session.get(
                f"{self.api_url}/files/{origin}/{file_path}"
            ) as response:
                if response.status != 200:
                    logger.error("File not found on OctoPrint",
                                printer_id=self.printer_id,
                                filename=filename,
                                status=response.status)
                    return False

                file_info = await response.json()
                download_url = file_info.get('refs', {}).get('download')

                if not download_url:
                    logger.error("No download URL for file",
                                printer_id=self.printer_id,
                                filename=filename)
                    return False

            # Download the file
            async with self.session.get(download_url) as response:
                if response.status != 200:
                    logger.error("Failed to download file",
                                printer_id=self.printer_id,
                                filename=filename,
                                status=response.status)
                    return False

                # Ensure parent directory exists
                Path(local_path).parent.mkdir(parents=True, exist_ok=True)

                # Stream to file
                with open(local_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(
                        FileConstants.DOWNLOAD_CHUNK_SIZE_BYTES
                    ):
                        f.write(chunk)

            logger.info("File downloaded from OctoPrint",
                       printer_id=self.printer_id,
                       filename=filename,
                       local_path=local_path)
            return True

        except Exception as e:
            logger.error("Error downloading file from OctoPrint",
                        printer_id=self.printer_id,
                        filename=filename,
                        error=str(e))
            return False

    async def pause_print(self) -> bool:
        """Pause the current print job."""
        return await self._send_job_command('pause', action='pause')

    async def resume_print(self) -> bool:
        """Resume the paused print job."""
        return await self._send_job_command('pause', action='resume')

    async def stop_print(self) -> bool:
        """Stop/cancel the current print job."""
        return await self._send_job_command('cancel')

    async def _send_job_command(self, command: str, **kwargs) -> bool:
        """Send a command to the job API."""
        if not self.session:
            return False

        try:
            payload = {'command': command}
            payload.update(kwargs)

            async with self.session.post(
                f"{self.api_url}{OctoPrintConstants.API_JOB}",
                json=payload
            ) as response:
                if response.status == 204:
                    logger.info("Job command executed",
                               printer_id=self.printer_id,
                               command=command)
                    return True
                elif response.status == 409:
                    logger.warning("Job command conflict - invalid state",
                                  printer_id=self.printer_id,
                                  command=command)
                    return False
                else:
                    logger.error("Job command failed",
                                printer_id=self.printer_id,
                                command=command,
                                status=response.status)
                    return False

        except Exception as e:
            logger.error("Error sending job command",
                        printer_id=self.printer_id,
                        command=command,
                        error=str(e))
            return False

    async def _get_webcam_settings(self) -> Optional[Dict[str, Any]]:
        """Get webcam settings from OctoPrint."""
        if self._webcam_settings_fetched:
            return self._webcam_settings

        if not self.session:
            return None

        try:
            async with self.session.get(
                f"{self.api_url}{OctoPrintConstants.API_SETTINGS}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._webcam_settings = data.get('webcam', {})
                    self._webcam_settings_fetched = True
                    return self._webcam_settings

        except Exception as e:
            logger.warning("Failed to get webcam settings",
                          printer_id=self.printer_id, error=str(e))

        self._webcam_settings_fetched = True
        return None

    async def has_camera(self) -> bool:
        """Check if printer has camera support."""
        settings = await self._get_webcam_settings()
        if not settings:
            return False

        return settings.get('webcamEnabled', False)

    async def get_camera_stream_url(self) -> Optional[str]:
        """Get camera stream URL if available."""
        settings = await self._get_webcam_settings()
        if not settings:
            return None

        stream_url = settings.get('streamUrl')
        if not stream_url:
            return None

        # Make relative URLs absolute
        if stream_url.startswith('/'):
            stream_url = f"{self.base_url}{stream_url}"

        return stream_url

    async def take_snapshot(self) -> Optional[bytes]:
        """Take a camera snapshot and return image data."""
        settings = await self._get_webcam_settings()
        if not settings:
            return None

        snapshot_url = settings.get('snapshotUrl')
        if not snapshot_url:
            return None

        # Make relative URLs absolute
        if snapshot_url.startswith('/'):
            snapshot_url = f"{self.base_url}{snapshot_url}"

        try:
            # Use a separate session for snapshot (may be external URL)
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(snapshot_url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.warning("Failed to take snapshot",
                                      printer_id=self.printer_id,
                                      status=response.status)
                        return None

        except Exception as e:
            logger.error("Error taking snapshot",
                        printer_id=self.printer_id, error=str(e))
            return None
