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
    from bambulabs_api import BambuClient
    from bambulabs_api.models import Device, Job
    BAMBU_AVAILABLE = True
except ImportError:
    BAMBU_AVAILABLE = False
    BambuClient = None
    Device = None
    Job = None

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
        self.client: Optional[BambuClient] = None
        self._device: Optional[Device] = None
        
    async def connect(self) -> bool:
        """Establish MQTT connection to Bambu Lab printer."""
        if self.is_connected:
            logger.info("Already connected to Bambu Lab printer", printer_id=self.printer_id)
            return True
            
        try:
            logger.info("Connecting to Bambu Lab printer", 
                       printer_id=self.printer_id, ip=self.ip_address)
            
            # Initialize Bambu Lab client
            self.client = BambuClient(
                host=self.ip_address,
                access_code=self.access_code,
                serial=self.serial_number
            )
            
            # Establish connection
            await asyncio.wait_for(self.client.connect(), timeout=10.0)
            
            # Get device information
            self._device = await self.client.get_device()
            
            self.is_connected = True
            logger.info("Successfully connected to Bambu Lab printer",
                       printer_id=self.printer_id,
                       model=getattr(self._device, 'model', 'Unknown'))
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
                await self.client.disconnect()
                
            self.is_connected = False
            self.client = None
            self._device = None
            
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
            status_data = await self.client.get_status()
            
            # Map Bambu Lab status to our PrinterStatus
            bambu_status = status_data.get('print', {}).get('gcode_state', 'UNKNOWN')
            printer_status = self._map_bambu_status(bambu_status)
            
            # Extract temperature data
            temp_data = status_data.get('temp', {})
            bed_temp = temp_data.get('bed_temper', 0)
            nozzle_temp = temp_data.get('nozzle_temper', 0)
            
            # Extract job information
            print_data = status_data.get('print', {})
            current_job = print_data.get('subtask_name', '')
            progress = print_data.get('mc_percent', 0)
            
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=printer_status,
                message=f"Bambu Lab status: {bambu_status}",
                temperature_bed=float(bed_temp),
                temperature_nozzle=float(nozzle_temp),
                progress=int(progress),
                current_job=current_job if current_job else None,
                timestamp=datetime.now(),
                raw_data=status_data
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
            status_data = await self.client.get_status()
            print_data = status_data.get('print', {})
            
            if not print_data.get('subtask_name'):
                return None  # No active job
                
            job_name = print_data.get('subtask_name', 'Unknown Job')
            progress = int(print_data.get('mc_percent', 0))
            
            # Map Bambu status to JobStatus
            bambu_status = print_data.get('gcode_state', 'UNKNOWN')
            job_status = self._map_job_status(bambu_status)
            
            # Time information
            remaining_time = print_data.get('mc_remaining_time', 0)
            
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
            # Get file list from Bambu Lab
            files_data = await self.client.get_files()
            printer_files = []
            
            for file_data in files_data:
                file_obj = PrinterFile(
                    filename=file_data.get('name', 'Unknown'),
                    size=file_data.get('size'),
                    modified=datetime.fromtimestamp(file_data.get('modified', 0)) 
                             if file_data.get('modified') else None,
                    path=file_data.get('path', file_data.get('name', ''))
                )
                printer_files.append(file_obj)
                
            logger.info("Retrieved file list from Bambu Lab",
                       printer_id=self.printer_id, file_count=len(printer_files))
            return printer_files
            
        except Exception as e:
            logger.error("Failed to list files from Bambu Lab",
                        printer_id=self.printer_id, error=str(e))
            raise PrinterConnectionError(self.printer_id, f"File listing failed: {str(e)}")
            
    async def download_file(self, filename: str, local_path: str) -> bool:
        """Download a file from Bambu Lab printer."""
        if not self.is_connected or not self.client:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            logger.info("Starting file download from Bambu Lab",
                       printer_id=self.printer_id, filename=filename, local_path=local_path)
                       
            # Download file using Bambu Lab client
            file_content = await self.client.download_file(filename)
            
            # Write to local file
            with open(local_path, 'wb') as f:
                f.write(file_content)
                
            logger.info("Successfully downloaded file from Bambu Lab",
                       printer_id=self.printer_id, filename=filename)
            return True
            
        except Exception as e:
            logger.error("Failed to download file from Bambu Lab",
                        printer_id=self.printer_id, filename=filename, error=str(e))
            return False