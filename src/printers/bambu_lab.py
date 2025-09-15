"""
Bambu Lab printer integration for Printernizer.
Handles MQTT communication with Bambu Lab A1 printers.
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from src.models.printer import PrinterStatus, PrinterStatusUpdate
from src.utils.exceptions import PrinterConnectionError
from .base import BasePrinter, JobInfo, JobStatus, PrinterFile

# Import will be handled gracefully if bambulabs-api is not installed
try:
    from bambulabs_api import Printer, PrinterMQTTClient
    BAMBU_AVAILABLE = True
except ImportError:
    BAMBU_AVAILABLE = False
    Printer = None
    PrinterMQTTClient = None

logger = structlog.get_logger()


class BambuLabPrinter(BasePrinter):
    """Bambu Lab printer implementation using MQTT."""
    
    def __init__(self, printer_id: str, name: str, ip_address: str, 
                 access_code: str, serial_number: str, **kwargs):
        """Initialize Bambu Lab printer."""
        super().__init__(printer_id, name, ip_address, **kwargs)
        
        if not BAMBU_AVAILABLE:
            raise ImportError("bambulabs-api library is not installed. "
                            "Install with: pip install bambulabs-api")
            
        self.access_code = access_code
        self.serial_number = serial_number
        self.client: Optional[Printer] = None
        
    async def connect(self) -> bool:
        """Establish MQTT connection to Bambu Lab printer."""
        if self.is_connected:
            logger.info("Already connected to Bambu Lab printer", printer_id=self.printer_id)
            return True
            
        try:
            logger.info("Connecting to Bambu Lab printer", 
                       printer_id=self.printer_id, ip=self.ip_address)
            
            # Initialize Bambu Lab client
            self.client = Printer(
                ip_address=self.ip_address,
                access_code=self.access_code,
                serial=self.serial_number
            )
            
            # Connection is established automatically when client is created
            
            self.is_connected = True
            logger.info("Successfully connected to Bambu Lab printer",
                       printer_id=self.printer_id)
            return True
            
        except Exception as e:
            logger.error("Failed to connect to Bambu Lab printer",
                        printer_id=self.printer_id, error=str(e))
            raise PrinterConnectionError(self.printer_id, str(e))
            
    async def disconnect(self) -> None:
        """Disconnect from Bambu Lab printer."""
        if not self.is_connected:
            return
            
        try:
            if self.client:
                # Note: bambulabs_api Printer doesn't have async disconnect method
                self.client = None
                
            self.is_connected = False
            
            logger.info("Disconnected from Bambu Lab printer", printer_id=self.printer_id)
            
        except Exception as e:
            logger.error("Error disconnecting from Bambu Lab printer",
                        printer_id=self.printer_id, error=str(e))
            
    async def get_status(self) -> PrinterStatusUpdate:
        """Get current printer status from Bambu Lab."""
        if not self.is_connected or not self.client:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            # Get current status from Bambu Lab API
            bambu_status = self.client.get_current_state()
            printer_status = self._map_bambu_status(bambu_status)
            
            # Extract temperature data
            bed_temp = self.client.get_bed_temperature()
            nozzle_temp = self.client.get_nozzle_temperature()
            
            # Extract job information
            current_job = None
            if hasattr(self.client, 'subtask_name'):
                try:
                    current_job = self.client.subtask_name()
                except:
                    current_job = None
            progress = self.client.get_percentage()
            
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=printer_status,
                message=f"Bambu Lab status: {bambu_status}",
                temperature_bed=float(bed_temp) if bed_temp else 0.0,
                temperature_nozzle=float(nozzle_temp) if nozzle_temp else 0.0,
                progress=int(progress) if progress else 0,
                current_job=current_job if current_job else None,
                timestamp=datetime.now(),
                raw_data={"state": bambu_status, "bed_temp": bed_temp, "nozzle_temp": nozzle_temp}
            )
            
        except Exception as e:
            logger.error("Failed to get Bambu Lab status",
                        printer_id=self.printer_id, error=str(e))
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=PrinterStatus.ERROR,
                message=f"Status check failed: {str(e)}",
                timestamp=datetime.now()
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
            job_name = None
            if hasattr(self.client, 'subtask_name'):
                try:
                    job_name = self.client.subtask_name()
                except:
                    job_name = None
            
            if not job_name:
                return None  # No active job
                
            progress = self.client.get_percentage()
            
            # Map Bambu status to JobStatus
            bambu_status = self.client.get_current_state()
            job_status = self._map_job_status(bambu_status)
            
            # Time information (not directly available in this API version)
            remaining_time = 0
            
            job_info = JobInfo(
                job_id=f"{self.printer_id}_{job_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name=job_name,
                status=job_status,
                progress=progress,
                estimated_time=remaining_time * 60 if remaining_time > 0 else None  # Convert to seconds
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
        if not self.is_connected or not self.client:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            # File listing not yet implemented for this API version
            # Return empty list for now
            logger.info("File listing not yet implemented for Bambu Lab API",
                       printer_id=self.printer_id)
            return []
            
        except Exception as e:
            logger.error("Failed to list files from Bambu Lab",
                        printer_id=self.printer_id, error=str(e))
            raise PrinterConnectionError(self.printer_id, f"File listing failed: {str(e)}")
            
    async def download_file(self, filename: str, local_path: str) -> bool:
        """Download a file from Bambu Lab printer."""
        if not self.is_connected or not self.client:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            # File download not yet implemented for this API version
            logger.info("File download not yet implemented for Bambu Lab API",
                       printer_id=self.printer_id, filename=filename)
            return False
            
        except Exception as e:
            logger.error("Failed to download file from Bambu Lab",
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