"""
Bambu Lab printer integration for Printernizer.
Handles MQTT communication with Bambu Lab A1 printers.
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from models.printer import PrinterStatus, PrinterStatusUpdate
from utils.exceptions import PrinterConnectionError
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
            current_job = self.client.subtask_name if hasattr(self.client, 'subtask_name') else None
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
            
    def _map_bambu_status(self, bambu_status: str) -> PrinterStatus:
        """Map Bambu Lab status to PrinterStatus."""
        status_mapping = {
            'IDLE': PrinterStatus.ONLINE,
            'PREPARE': PrinterStatus.ONLINE,
            'RUNNING': PrinterStatus.PRINTING,
            'PAUSE': PrinterStatus.PAUSED,
            'FINISH': PrinterStatus.ONLINE,
            'FAILED': PrinterStatus.ERROR,
            'UNKNOWN': PrinterStatus.UNKNOWN
        }
        return status_mapping.get(bambu_status.upper(), PrinterStatus.UNKNOWN)
        
    async def get_job_info(self) -> Optional[JobInfo]:
        """Get current job information from Bambu Lab."""
        if not self.is_connected or not self.client:
            return None
            
        try:
            job_name = self.client.subtask_name if hasattr(self.client, 'subtask_name') else None
            
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
            
    def _map_job_status(self, bambu_status: str) -> JobStatus:
        """Map Bambu Lab status to JobStatus."""
        status_mapping = {
            'IDLE': JobStatus.IDLE,
            'PREPARE': JobStatus.PREPARING,
            'RUNNING': JobStatus.PRINTING,
            'PAUSE': JobStatus.PAUSED,
            'FINISH': JobStatus.COMPLETED,
            'FAILED': JobStatus.FAILED
        }
        return status_mapping.get(bambu_status.upper(), JobStatus.IDLE)
        
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