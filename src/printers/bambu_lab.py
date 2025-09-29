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
from src.services.bambu_ftp_service import BambuFTPService, BambuFTPFile

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

        # Initialize appropriate client
        if self.use_bambu_api:
            self.bambu_client: Optional[BambuClient] = None
            self.latest_status: Optional[Dict[str, Any]] = None
            self.cached_files: List[PrinterFile] = []
            self.last_file_update: Optional[datetime] = None
        else:
            self.client = None  # MQTT client will be initialized in connect
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
            # Initialize direct FTP service if enabled
            if self.use_direct_ftp:
                try:
                    self.ftp_service = BambuFTPService(self.ip_address, self.access_code)
                    # Test FTP connection
                    success, message = await self.ftp_service.test_connection()
                    if success:
                        logger.info("Direct FTP service initialized successfully",
                                   printer_id=self.printer_id, message=message)
                    else:
                        logger.warning("Direct FTP test failed, will use fallback",
                                     printer_id=self.printer_id, message=message)
                        self.ftp_service = None
                except Exception as e:
                    logger.warning("Failed to initialize direct FTP service",
                                 printer_id=self.printer_id, error=str(e))
                    self.ftp_service = None

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

        # Connect to printer (synchronous method)
        self.bambu_client.connect()

        # Request initial status and file information
        if hasattr(self.bambu_client, 'request_status'):
            self.bambu_client.request_status()
            
        # Try to request file listing if supported
        if hasattr(self.bambu_client, 'request_file_list'):
            self.bambu_client.request_file_list()

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

    async def disconnect(self) -> None:
        """Disconnect from Bambu Lab printer."""
        if not self.is_connected:
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
            logger.info("Disconnected from Bambu Lab printer", printer_id=self.printer_id)

        except Exception as e:
            logger.error("Error disconnecting from Bambu Lab printer",
                        printer_id=self.printer_id, error=str(e))

        # Clean up FTP service
        self.ftp_service = None
            
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
                    except:
                        alternative_status.name = 'UNKNOWN'
                        
                # Try to get temperature data
                try:
                    alternative_status.bed_temper = self.bambu_client.get_bed_temperature() or 0.0
                    alternative_status.nozzle_temper = self.bambu_client.get_nozzle_temperature() or 0.0
                except:
                    alternative_status.bed_temper = 0.0
                    alternative_status.nozzle_temper = 0.0
                
                # Try to get progress
                try:
                    alternative_status.print_percent = self.bambu_client.get_percentage() or 0
                except:
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
                except:
                    alternative_status.gcode_file = None
                
                # If we have temperature data, we can infer printing status
                if (hasattr(alternative_status, 'nozzle_temper') and 
                    alternative_status.nozzle_temper > 200 and
                    hasattr(alternative_status, 'bed_temper') and 
                    alternative_status.bed_temper > 50):
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

                        logger.debug("Got data from MQTT dump",
                                   printer_id=self.printer_id,
                                   bed_temp=bed_temp, nozzle_temp=nozzle_temp,
                                   progress=progress, layer_num=layer_num,
                                   remaining_time_minutes=remaining_time_minutes,
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
                if nozzle_temp > 50 or bed_temp > 30:
                    message = f"Print Complete - Cooling down (Nozzle {nozzle_temp}°C, Bed {bed_temp}°C)"
                else:
                    message = "Print Complete - Ready"
            else:
                # Fallback: use temperature as indicator only if status explicitly says PRINTING
                if nozzle_temp > 200 and bed_temp > 50:
                    printer_status = PrinterStatus.PRINTING
                    message = f"Printing - Nozzle {nozzle_temp}°C, Bed {bed_temp}°C"
                else:
                    printer_status = PrinterStatus.ONLINE
                    message = "Ready"
        elif status_name in ['IDLE', 'UNKNOWN']:
            # Printer is idle - check if just completing a print based on temperatures
            if progress == 100:
                printer_status = PrinterStatus.ONLINE
                if nozzle_temp > 50 or bed_temp > 30:
                    message = f"Print Complete - Cooling down (Nozzle {nozzle_temp}°C, Bed {bed_temp}°C)"
                else:
                    message = "Print Complete - Ready"
            elif nozzle_temp > 50:
                message = f"Heating - Nozzle {nozzle_temp}°C"
                printer_status = PrinterStatus.ONLINE
            elif bed_temp > 30:
                message = f"Heating - Bed {bed_temp}°C"
                printer_status = PrinterStatus.ONLINE
            else:
                message = "Ready"
                printer_status = PrinterStatus.ONLINE
        else:
            # Map the status using the mapping function
            printer_status = self._map_bambu_status(status_name)
            # Provide better status messages for other states
            if printer_status == PrinterStatus.ONLINE and (nozzle_temp > 50 or bed_temp > 30):
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
            current_job_thumbnail_url=(f"/api/v1/files/{current_job_file_id}/thumbnail" if current_job_file_id and current_job_has_thumbnail else None),
            remaining_time_minutes=remaining_time_minutes,
            estimated_end_time=estimated_end_time,
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
        if nozzle_temp > 200 and bed_temp > 50:
            printer_status = PrinterStatus.PRINTING
            if progress > 0:
                message = f"Printing - Layer {layer_num}, {progress}%"
            else:
                message = f"Printing - Nozzle {nozzle_temp}°C, Bed {bed_temp}°C"
        elif progress > 0 and nozzle_temp > 100:
            printer_status = PrinterStatus.PRINTING
            message = f"Printing - Layer {layer_num}, {progress}%"
        elif nozzle_temp > 50:
            printer_status = PrinterStatus.ONLINE
            message = f"Heating - Nozzle {nozzle_temp}°C"
        elif bed_temp > 30:
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
            current_job_thumbnail_url=(f"/api/v1/files/{current_job_file_id}/thumbnail" if current_job_file_id and current_job_has_thumbnail else None),
            remaining_time_minutes=remaining_time_minutes,
            estimated_end_time=estimated_end_time,
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
            # Try direct FTP first if available
            if self.ftp_service:
                return await self._list_files_direct_ftp()
            elif self.use_bambu_api:
                return await self._list_files_bambu_api()
            else:
                return await self._list_files_mqtt()

        except Exception as e:
            logger.error("Failed to list files from Bambu Lab",
                        printer_id=self.printer_id, error=str(e))
            raise PrinterConnectionError(self.printer_id, f"File listing failed: {str(e)}")

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
                (datetime.now() - self.last_file_update).seconds < 30):
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
                        # Parse FTP listing line to extract just the filename
                        # Format: "-rw-rw-rw-   1 root  root    445349 Apr 22 01:10 filename.ext"
                        if isinstance(cache_file, str):
                            # Split on whitespace and take the last part as filename
                            parts = cache_file.strip().split()
                            if len(parts) >= 9:  # Standard FTP ls -l format
                                filename = ' '.join(parts[8:])  # filename might contain spaces
                            else:
                                filename = parts[-1] if parts else cache_file
                        else:
                            filename = str(cache_file)
                        
                        if any(filename.lower().endswith(ext) for ext in ['.3mf', '.gcode', '.bgcode']):
                            files.append(PrinterFile(
                                filename=filename,
                                size=0,  # Size unknown
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

    async def _download_file_direct_ftp(self, filename: str, local_path: str) -> bool:
        """Download file using direct FTP connection."""
        if not self.ftp_service:
            logger.warning("Direct FTP service not available, falling back to bambulabs-api",
                          printer_id=self.printer_id)
            return await self._download_file_bambu_api(filename, local_path)

        logger.info("Downloading file via direct FTP",
                   printer_id=self.printer_id, filename=filename, local_path=local_path)

        try:
            # Try to download from cache directory first
            success = await self.ftp_service.download_file(filename, local_path, "/cache")

            if success:
                logger.info("Direct FTP download successful",
                           printer_id=self.printer_id, filename=filename)
                return True
            else:
                logger.warning("Direct FTP download failed, trying bambulabs-api fallback",
                             printer_id=self.printer_id, filename=filename)
                # Fallback to original method
                return await self._download_file_bambu_api(filename, local_path)

        except Exception as e:
            logger.error("Direct FTP download error, trying bambulabs-api fallback",
                        printer_id=self.printer_id, filename=filename, error=str(e))
            # Fallback to original method
            return await self._download_file_bambu_api(filename, local_path)

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
            # Try direct FTP first if available
            if self.ftp_service:
                return await self._download_file_direct_ftp(filename, local_path)
            elif self.use_bambu_api:
                return await self._download_file_bambu_api(filename, local_path)
            else:
                return await self._download_file_mqtt(filename, local_path)

        except Exception as e:
            logger.error("Failed to download file from Bambu Lab",
                        printer_id=self.printer_id, filename=filename, error=str(e))
            return False

    async def _download_file_bambu_api(self, filename: str, local_path: str) -> bool:
        """Download file using bambulabs_api with corrected implementation."""
        if not self.bambu_client:
            raise PrinterConnectionError(self.printer_id, "Bambu client not initialized")

        logger.info("Downloading file from Bambu Lab printer via bambulabs-api",
                   printer_id=self.printer_id, filename=filename, local_path=local_path)

        # Method 1: Use bambulabs_api FTP client directly (this works!)
        if hasattr(self.bambu_client, 'ftp_client') and self.bambu_client.ftp_client:
            try:
                # Use the working bambulabs-api approach
                from pathlib import Path

                # Ensure local directory exists
                Path(local_path).parent.mkdir(parents=True, exist_ok=True)

                logger.debug("Attempting bambulabs-api FTP download",
                           printer_id=self.printer_id, filename=filename)

                # Download using the correct bambulabs-api method
                file_data_io = self.bambu_client.ftp_client.download_file(f"cache/{filename}")

                if file_data_io:
                    file_data = file_data_io.getvalue()
                    if file_data and len(file_data) > 0:
                        # Write file data to local path
                        with open(local_path, 'wb') as f:
                            f.write(file_data)

                        logger.info("bambulabs-api FTP download successful",
                                   printer_id=self.printer_id,
                                   filename=filename,
                                   size=len(file_data))
                        return True
                    else:
                        logger.debug("bambulabs-api FTP returned empty data",
                                    printer_id=self.printer_id, filename=filename)
                else:
                    logger.debug("bambulabs-api FTP returned None",
                                printer_id=self.printer_id, filename=filename)

            except Exception as e:
                logger.debug("bambulabs-api FTP download failed, trying HTTP fallback",
                            printer_id=self.printer_id, filename=filename, error=str(e))

        # Method 2: HTTP fallback download
        try:
            success = await self._download_via_http(filename, local_path)
            if success:
                logger.info("Successfully downloaded file via HTTP",
                           printer_id=self.printer_id, filename=filename)
                return True
        except Exception as e:
            logger.warning("HTTP download also failed",
                          printer_id=self.printer_id, filename=filename, error=str(e))

        logger.warning("All download methods failed for file",
                      printer_id=self.printer_id, filename=filename)
        return False

    async def _download_file_mqtt(self, filename: str, local_path: str) -> bool:
        """Download file using direct MQTT (fallback)."""
        # File download not implemented for direct MQTT approach
        logger.warning("File download not implemented for direct MQTT approach",
                      printer_id=self.printer_id, filename=filename)
        return False

    async def _download_via_ftp(self, filename: str, local_path: str) -> bool:
        """Download file via bambulabs_api FTP client."""
        try:
            ftp = self.bambu_client.ftp_client

            # Ensure local directory exists
            from pathlib import Path
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            # Try multiple possible paths for the file
            possible_paths = [
                f"cache/{filename}",  # Cache directory (most common)
                filename,  # Direct filename
                f"model/{filename}",  # Model directory
                f"timelapse/{filename}",  # Timelapse directory
            ]

            for remote_path in possible_paths:
                try:
                    logger.debug("Attempting FTP download",
                                printer_id=self.printer_id,
                                remote_path=remote_path)
                    
                    # FIXED: Use correct bambulabs-api FTP method
                    # download_file() returns BytesIO object, not (success, data) tuple
                    file_data_io = ftp.download_file(remote_path)
                    
                    if file_data_io:
                        # Get the actual bytes from BytesIO
                        file_data = file_data_io.getvalue()
                        
                        if file_data and len(file_data) > 0:
                            # Write file data to local path
                            with open(local_path, 'wb') as f:
                                f.write(file_data)

                            logger.info("FTP download successful",
                                       printer_id=self.printer_id,
                                       filename=filename,
                                       remote_path=remote_path,
                                       size=len(file_data))
                            return True
                        else:
                            logger.debug("FTP download returned empty data",
                                        printer_id=self.printer_id,
                                        remote_path=remote_path)

                except Exception as e:
                    logger.debug("FTP download failed for path",
                                printer_id=self.printer_id,
                                remote_path=remote_path,
                                error=str(e))
                    continue

            # Enhanced: attempt directory scanning & fuzzy / case-insensitive matching
            try:
                logger.debug("Attempting enhanced FTP search", printer_id=self.printer_id, filename=filename)

                # Helper to list a directory robustly
                def _safe_list(dir_path: str):
                    methods = [
                        'list_dir', 'listdir', 'listfiles', 'list_files'
                    ]
                    for m in methods:
                        if hasattr(ftp, m):
                            try:
                                return getattr(ftp, m)(dir_path)
                            except Exception:
                                continue
                    return []

                # Candidate directories to scan
                scan_dirs = ['', 'cache', 'model', 'timelapse', 'sdcard', 'usb', 'USB', 'gcodes']
                target_lower = filename.lower()
                discovered = []  # (dir, name)

                for d in scan_dirs:
                    try:
                        entries = _safe_list(d) if d != '' else _safe_list('.')
                        if not entries:
                            continue
                        # Normalize entry names depending on structure (str or dict)
                        for entry in entries:
                            if isinstance(entry, dict):
                                name = entry.get('name') or entry.get('filename') or ''
                                path_component = entry.get('path') or name
                            else:
                                name = str(entry)
                                path_component = name
                            if not name:
                                continue
                            discovered.append((d, name, path_component))
                    except Exception as e:
                        logger.debug("Directory scan failed", printer_id=self.printer_id, directory=d, error=str(e))
                        continue

                # First try exact case-insensitive match
                exact_match = next((item for item in discovered if item[1].lower() == target_lower), None)
                if exact_match:
                    dir_part, name_part, path_component = exact_match
                    remote_path = f"{dir_part}/{name_part}" if dir_part and not path_component.startswith(dir_part) else path_component
                    try:
                        logger.debug("Attempting FTP download (enhanced exact match)", printer_id=self.printer_id, remote_path=remote_path)
                        file_data_io = ftp.download_file(remote_path)
                        if file_data_io:
                            data = file_data_io.getvalue()
                            if data:
                                with open(local_path, 'wb') as f:
                                    f.write(data)
                                logger.info("FTP download successful (enhanced exact match)", printer_id=self.printer_id, filename=filename, remote_path=remote_path, size=len(data))
                                return True
                    except Exception as e:
                        logger.debug("Enhanced exact match download failed", printer_id=self.printer_id, remote_path=remote_path, error=str(e))

                # Fuzzy: allow substring match without extension differences
                base_no_ext = target_lower.rsplit('.', 1)[0]
                fuzzy_candidates = []
                for d, name, path_component in discovered:
                    n_lower = name.lower()
                    if base_no_ext in n_lower:
                        fuzzy_candidates.append((d, name, path_component))

                # If multiple, prefer those with same extension or .3mf/.gcode
                if fuzzy_candidates:
                    def rank(item):
                        _, name, _ = item
                        n_lower = name.lower()
                        score = 0
                        if n_lower.endswith('.3mf'): score += 3
                        if n_lower.endswith('.gcode'): score += 2
                        if n_lower.startswith(base_no_ext): score += 1
                        if base_no_ext in n_lower: score += 0.5
                        return -score  # smallest first
                    fuzzy_candidates.sort(key=rank)
                    best = fuzzy_candidates[0]
                    dir_part, name_part, path_component = best
                    remote_path = f"{dir_part}/{name_part}" if dir_part and not path_component.startswith(dir_part) else path_component
                    try:
                        logger.debug("Attempting FTP download (enhanced fuzzy)", printer_id=self.printer_id, remote_path=remote_path)
                        file_data_io = ftp.download_file(remote_path)
                        if file_data_io:
                            data = file_data_io.getvalue()
                            if data:
                                with open(local_path, 'wb') as f:
                                    f.write(data)
                                logger.info("FTP download successful (enhanced fuzzy)", printer_id=self.printer_id, requested=filename, matched=name_part, remote_path=remote_path, size=len(data))
                                return True
                    except Exception as e:
                        logger.debug("Enhanced fuzzy download failed", printer_id=self.printer_id, remote_path=remote_path, error=str(e))

                # Provide diagnostic suggestions
                if discovered:
                    similar = [name for _, name, _ in discovered if target_lower.split('.')[0] in name.lower()][:10]
                    logger.warning("File not found via FTP after enhanced search", printer_id=self.printer_id, filename=filename, similar=similar, scanned_dirs=scan_dirs)
                else:
                    logger.warning("No files discovered during enhanced FTP search (empty listings)", printer_id=self.printer_id, filename=filename)
            except Exception as e:
                logger.debug("Enhanced FTP search failed", printer_id=self.printer_id, filename=filename, error=str(e))

            logger.warning("File not found via FTP in any expected path",
                          printer_id=self.printer_id, filename=filename)
            return False

        except Exception as e:
            logger.error("FTP download method failed",
                        printer_id=self.printer_id, filename=filename, error=str(e))
            return False

    async def _download_via_http(self, filename: str, local_path: str) -> bool:
        """Download file via HTTP from Bambu Lab printer web interface."""
        try:
            import aiohttp
            from pathlib import Path

            # Ensure local directory exists
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            # Try multiple HTTP endpoints that Bambu Lab printers might expose
            possible_urls = [
                f"http://{self.ip_address}/cache/{filename}",
                f"http://{self.ip_address}/model/{filename}",
                f"http://{self.ip_address}/files/{filename}",
                f"http://{self.ip_address}:8080/cache/{filename}",
                f"http://{self.ip_address}:8080/model/{filename}",
                f"http://{self.ip_address}:8080/files/{filename}",
            ]

            timeout = aiohttp.ClientTimeout(total=120)  # 2 minute timeout for large files

            async with aiohttp.ClientSession(timeout=timeout) as session:
                for url in possible_urls:
                    try:
                        logger.debug("Attempting HTTP download",
                                    printer_id=self.printer_id, url=url)

                        # Add basic auth if available
                        auth = None
                        if hasattr(self, 'access_code') and self.access_code:
                            auth = aiohttp.BasicAuth('bblp', self.access_code)

                        async with session.get(url, auth=auth) as response:
                            if response.status == 200:
                                # Get file size for progress tracking
                                content_length = response.headers.get('Content-Length')
                                total_size = int(content_length) if content_length else None

                                downloaded_size = 0
                                with open(local_path, 'wb') as f:
                                    async for chunk in response.content.iter_chunked(8192):
                                        f.write(chunk)
                                        downloaded_size += len(chunk)

                                        # Log progress for large files
                                        if total_size and downloaded_size % (1024 * 1024) == 0:  # Every MB
                                            progress = (downloaded_size / total_size) * 100
                                            logger.debug("Download progress",
                                                        printer_id=self.printer_id,
                                                        filename=filename,
                                                        progress=f"{progress:.1f}%")

                                logger.info("HTTP download successful",
                                           printer_id=self.printer_id,
                                           filename=filename,
                                           url=url,
                                           size=downloaded_size)
                                return True

                            elif response.status == 401:
                                logger.debug("HTTP 401 - authentication required",
                                            printer_id=self.printer_id, url=url)
                            elif response.status == 404:
                                logger.debug("HTTP 404 - file not found at URL",
                                            printer_id=self.printer_id, url=url)
                            else:
                                logger.debug("HTTP error",
                                            printer_id=self.printer_id,
                                            url=url, status=response.status)

                    except aiohttp.ClientError as e:
                        logger.debug("HTTP client error",
                                    printer_id=self.printer_id, url=url, error=str(e))
                        continue
                    except Exception as e:
                        logger.debug("HTTP download attempt failed",
                                    printer_id=self.printer_id, url=url, error=str(e))
                        continue

            logger.warning("File not accessible via HTTP at any expected URL",
                          printer_id=self.printer_id, filename=filename)
            return False

        except Exception as e:
            logger.error("HTTP download method failed",
                        printer_id=self.printer_id, filename=filename, error=str(e))
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