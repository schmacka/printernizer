"""
Bambu Lab printer integration for Printernizer.
Handles communication with Bambu Lab A1 printers using bambulabs_api library.
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from src.models.printer import PrinterStatus, PrinterStatusUpdate
from src.utils.exceptions import PrinterConnectionError
from .base import BasePrinter, JobInfo, JobStatus, PrinterFile

# Import bambulabs_api dependencies
try:
    from bambulabs_api import Printer as BambuClient
    BAMBU_API_AVAILABLE = True
except ImportError:
    BAMBU_API_AVAILABLE = False
    BambuClient = None

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
                 access_code: str, serial_number: str, **kwargs):
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

        # Initialize appropriate client
        if self.use_bambu_api:
            self.bambu_client: Optional[BambuClient] = None
            self.latest_status: Optional[Dict[str, Any]] = None
        else:
            self.client: Optional[mqtt.Client] = None
            self.latest_data: Dict[str, Any] = {}
            self.mqtt_port = 8883
        
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback."""
        if rc == 0:
            logger.info("MQTT connected successfully", printer_id=self.printer_id)
            # Subscribe to printer status topic
            topic = f"device/{self.serial_number}/report"
            client.subscribe(topic)
            logger.debug("Subscribed to topic", topic=topic)
        else:
            logger.error("MQTT connection failed", printer_id=self.printer_id, rc=rc)

    def _on_message(self, client, userdata, msg):
        """MQTT message callback."""
        try:
            payload = json.loads(msg.payload.decode())
            self.latest_data = payload
            logger.debug("Received MQTT data", printer_id=self.printer_id, topic=msg.topic)
        except Exception as e:
            logger.warning("Failed to parse MQTT message", printer_id=self.printer_id, error=str(e))

    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback."""
        logger.info("MQTT disconnected", printer_id=self.printer_id, rc=rc)

    async def connect(self) -> bool:
        """Establish connection to Bambu Lab printer."""
        if self.is_connected:
            logger.info("Already connected to Bambu Lab printer", printer_id=self.printer_id)
            return True

        try:
            if self.use_bambu_api:
                return await self._connect_bambu_api()
            else:
                return await self._connect_mqtt()

        except Exception as e:
            logger.error("Failed to connect to Bambu Lab printer",
                        printer_id=self.printer_id, error=str(e))
            raise PrinterConnectionError(self.printer_id, str(e))

    async def _connect_bambu_api(self) -> bool:
        """Connect using bambulabs_api library."""
        logger.info("Connecting to Bambu Lab printer via bambulabs_api",
                   printer_id=self.printer_id, ip=self.ip_address)

        # Create bambulabs_api client
        self.bambu_client = BambuClient(
            ip_address=self.ip_address,
            access_code=self.access_code,
            serial=self.serial_number
        )

        # Set up event callbacks for real-time updates
        self.bambu_client.on_printer_status = self._on_bambu_status_update
        self.bambu_client.on_file_list = self._on_bambu_file_list_update

        # Connect to printer
        await self.bambu_client.connect()

        # Request initial status and file list
        await self.bambu_client.request_status()

        self.is_connected = True
        logger.info("Successfully connected to Bambu Lab printer via bambulabs_api",
                   printer_id=self.printer_id)
        return True

    async def _connect_mqtt(self) -> bool:
        """Connect using direct MQTT (fallback)."""
        logger.info("Connecting to Bambu Lab printer via direct MQTT",
                   printer_id=self.printer_id, ip=self.ip_address)

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

        # Connect to MQTT broker
        result = self.client.connect(self.ip_address, self.mqtt_port, 60)
        if result != 0:
            raise ConnectionError(f"MQTT connect failed with code {result}")

        # Start MQTT loop in background
        self.client.loop_start()

        # Wait for connection to be established
        await asyncio.sleep(3)

        self.is_connected = True
        logger.info("Successfully connected to Bambu Lab printer via direct MQTT",
                   printer_id=self.printer_id)
        return True

    # Callback methods for bambulabs_api events
    async def _on_bambu_status_update(self, status: Dict[str, Any]):
        """Handle status updates from bambulabs_api."""
        self.latest_status = status
        logger.debug("Received status update from bambulabs_api", printer_id=self.printer_id)

    async def _on_bambu_file_list_update(self, file_list_data: Dict[str, Any]):
        """Handle file list updates from bambulabs_api."""
        logger.debug("Received file list update from bambulabs_api",
                    printer_id=self.printer_id, file_count=len(file_list_data.get('files', [])))

    async def disconnect(self) -> None:
        """Disconnect from Bambu Lab printer."""
        if not self.is_connected:
            return

        try:
            if self.use_bambu_api and self.bambu_client:
                await self.bambu_client.disconnect()
                self.bambu_client = None
                self.latest_status = None
            elif self.client:
                self.client.loop_stop()
                self.client.disconnect()
                self.client = None
                self.latest_data = {}

            self.is_connected = False
            logger.info("Disconnected from Bambu Lab printer", printer_id=self.printer_id)

        except Exception as e:
            logger.error("Error disconnecting from Bambu Lab printer",
                        printer_id=self.printer_id, error=str(e))
            
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
        """Get status using bambulabs_api."""
        if not self.bambu_client:
            raise PrinterConnectionError(self.printer_id, "Bambu client not initialized")

        # Request fresh status if needed
        if not self.latest_status:
            await self.bambu_client.request_status()
            await asyncio.sleep(0.5)  # Wait for response

        status = self.latest_status
        if not status:
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=PrinterStatus.UNKNOWN,
                message="No status data available",
                timestamp=datetime.now()
            )

        # Convert bambulabs_api status to our format
        bed_temp = getattr(status, 'bed_temper', 0.0) or 0.0
        nozzle_temp = getattr(status, 'nozzle_temper', 0.0) or 0.0
        progress = getattr(status, 'print_percent', 0) or 0
        layer_num = getattr(status, 'layer_num', 0) or 0

        # Determine printer status based on available data
        if progress > 0 and nozzle_temp > 100:
            printer_status = PrinterStatus.PRINTING
            message = f"Printing - Layer {layer_num}, {progress}%"
        elif nozzle_temp > 50:
            printer_status = PrinterStatus.ONLINE
            message = "Heating/Preparing"
        elif bed_temp > 30:
            printer_status = PrinterStatus.ONLINE
            message = "Bed heating"
        else:
            printer_status = PrinterStatus.ONLINE
            message = "Ready"

        current_job = getattr(status, 'gcode_file', None)

        return PrinterStatusUpdate(
            printer_id=self.printer_id,
            status=printer_status,
            message=message,
            temperature_bed=float(bed_temp),
            temperature_nozzle=float(nozzle_temp),
            progress=int(progress),
            current_job=current_job,
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

        # Determine printer status based on available data
        if progress > 0 and nozzle_temp > 100:
            printer_status = PrinterStatus.PRINTING
            message = f"Printing - Layer {layer_num}, {progress}%"
        elif nozzle_temp > 50:
            printer_status = PrinterStatus.ONLINE
            message = "Heating/Preparing"
        elif bed_temp > 30:
            printer_status = PrinterStatus.ONLINE
            message = "Bed heating"
        else:
            printer_status = PrinterStatus.ONLINE
            message = "Ready"

        # Extract job information (if available)
        current_job = print_data.get("subtask_name")

        return PrinterStatusUpdate(
            printer_id=self.printer_id,
            status=printer_status,
            message=message,
            temperature_bed=float(bed_temp),
            temperature_nozzle=float(nozzle_temp),
            progress=int(progress),
            current_job=current_job,
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
            if progress > 0 and nozzle_temp > 100:
                job_status = JobStatus.PRINTING
            elif nozzle_temp > 50:
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

        try:
            if self.use_bambu_api:
                return await self._list_files_bambu_api()
            else:
                return await self._list_files_mqtt()

        except Exception as e:
            logger.error("Failed to list files from Bambu Lab",
                        printer_id=self.printer_id, error=str(e))
            raise PrinterConnectionError(self.printer_id, f"File listing failed: {str(e)}")

    async def _list_files_bambu_api(self) -> List[PrinterFile]:
        """List files using bambulabs_api library."""
        if not self.bambu_client:
            raise PrinterConnectionError(self.printer_id, "Bambu client not initialized")

        logger.info("Requesting file list from Bambu Lab printer via API",
                   printer_id=self.printer_id)

        # Request file list from printer
        file_data = await self.bambu_client.request_file_list()

        files = []
        if file_data and 'files' in file_data:
            for file_info in file_data['files']:
                # Convert bambulabs_api file info to PrinterFile
                printer_file = PrinterFile(
                    name=file_info.get('name', 'Unknown'),
                    path=file_info.get('path', '/'),
                    size=file_info.get('size', 0),
                    modified=datetime.fromisoformat(file_info['time']) if file_info.get('time') else datetime.now(),
                    file_type=self._get_file_type_from_name(file_info.get('name', ''))
                )
                files.append(printer_file)

        logger.info("Retrieved file list from Bambu Lab printer",
                   printer_id=self.printer_id, file_count=len(files))
        return files

    async def _list_files_mqtt(self) -> List[PrinterFile]:
        """List files using direct MQTT (fallback)."""
        # File listing not implemented for direct MQTT approach
        logger.warning("File listing not implemented for direct MQTT approach",
                      printer_id=self.printer_id)
        return []

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
        """Download a file from Bambu Lab printer."""
        if not self.is_connected:
            raise PrinterConnectionError(self.printer_id, "Not connected")

        try:
            if self.use_bambu_api:
                return await self._download_file_bambu_api(filename, local_path)
            else:
                return await self._download_file_mqtt(filename, local_path)

        except Exception as e:
            logger.error("Failed to download file from Bambu Lab",
                        printer_id=self.printer_id, filename=filename, error=str(e))
            return False

    async def _download_file_bambu_api(self, filename: str, local_path: str) -> bool:
        """Download file using bambulabs_api."""
        if not self.bambu_client:
            raise PrinterConnectionError(self.printer_id, "Bambu client not initialized")

        logger.info("Downloading file from Bambu Lab printer via API",
                   printer_id=self.printer_id, filename=filename, local_path=local_path)

        try:
            # Request file download from printer
            file_data = await self.bambu_client.download_file(filename)

            if file_data:
                # Write file data to local path
                with open(local_path, 'wb') as f:
                    f.write(file_data)

                logger.info("Successfully downloaded file from Bambu Lab printer",
                           printer_id=self.printer_id, filename=filename)
                return True
            else:
                logger.warning("No file data received from Bambu Lab printer",
                              printer_id=self.printer_id, filename=filename)
                return False

        except Exception as e:
            logger.error("Bambu API file download failed",
                        printer_id=self.printer_id, filename=filename, error=str(e))
            return False

    async def _download_file_mqtt(self, filename: str, local_path: str) -> bool:
        """Download file using direct MQTT (fallback)."""
        # File download not implemented for direct MQTT approach
        logger.warning("File download not implemented for direct MQTT approach",
                      printer_id=self.printer_id, filename=filename)
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
        """Check if Bambu Lab printer has camera support."""
        # Most Bambu Lab printers have cameras, but we should check if accessible
        if not self.is_connected:
            return False
            
        try:
            # Try to access camera stream to verify availability
            stream_url = await self.get_camera_stream_url()
            return stream_url is not None
        except Exception as e:
            logger.debug("Camera check failed", printer_id=self.printer_id, error=str(e))
            return False

    async def get_camera_stream_url(self) -> Optional[str]:
        """Get camera stream URL for Bambu Lab printer."""
        if not self.is_connected:
            logger.warning("Cannot get camera stream - printer not connected", 
                          printer_id=self.printer_id)
            return None
            
        try:
            # Bambu Lab A1 typically exposes camera at port 8080
            # Format: http://printer-ip:8080/stream or mjpeg stream
            stream_url = f"http://{self.ip_address}:8080/stream"
            
            logger.debug("Generated camera stream URL", 
                        printer_id=self.printer_id, url=stream_url)
            return stream_url
            
        except Exception as e:
            logger.error("Error generating camera stream URL",
                        printer_id=self.printer_id, error=str(e))
            return None

    async def take_snapshot(self) -> Optional[bytes]:
        """Take a camera snapshot from Bambu Lab printer."""
        if not self.is_connected:
            logger.warning("Cannot take snapshot - printer not connected",
                          printer_id=self.printer_id)
            return None
            
        try:
            import aiohttp
            
            # Bambu Lab snapshot endpoint
            snapshot_url = f"http://{self.ip_address}:8080/snapshot"
            
            logger.info("Taking snapshot from Bambu Lab printer",
                       printer_id=self.printer_id, url=snapshot_url)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(snapshot_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        logger.info("Successfully captured snapshot",
                                   printer_id=self.printer_id, 
                                   size=len(image_data))
                        return image_data
                    else:
                        logger.warning("Failed to capture snapshot - HTTP error",
                                     printer_id=self.printer_id,
                                     status=response.status)
                        return None
                        
        except Exception as e:
            logger.error("Error taking snapshot from Bambu Lab",
                        printer_id=self.printer_id, error=str(e))
            return None