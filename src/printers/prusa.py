"""
Prusa Core One printer integration for Printernizer.
Handles HTTP API communication with PrusaLink.
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import aiohttp
import structlog

from models.printer import PrinterStatus, PrinterStatusUpdate
from utils.exceptions import PrinterConnectionError
from .base import BasePrinter, JobInfo, JobStatus, PrinterFile

logger = structlog.get_logger()


class PrusaPrinter(BasePrinter):
    """Prusa Core One printer implementation using PrusaLink HTTP API."""
    
    def __init__(self, printer_id: str, name: str, ip_address: str, 
                 api_key: str, **kwargs):
        """Initialize Prusa printer."""
        super().__init__(printer_id, name, ip_address, **kwargs)
        self.api_key = api_key
        self.base_url = f"http://{ip_address}/api"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def connect(self) -> bool:
        """Establish HTTP connection to Prusa printer."""
        if self.is_connected:
            logger.info("Already connected to Prusa printer", printer_id=self.printer_id)
            return True
            
        try:
            logger.info("Connecting to Prusa printer", 
                       printer_id=self.printer_id, ip=self.ip_address)
            
            # Create HTTP session with API key
            headers = {
                'X-Api-Key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
                connector=aiohttp.TCPConnector(keepalive_timeout=30)
            )
            
            # Test connection with version endpoint
            async with self.session.get(f"{self.base_url}/version") as response:
                if response.status == 200:
                    version_data = await response.json()
                    logger.info("Successfully connected to Prusa printer",
                               printer_id=self.printer_id,
                               version=version_data.get('server', 'Unknown'))
                    self.is_connected = True
                    return True
                else:
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                    
        except Exception as e:
            logger.error("Failed to connect to Prusa printer",
                        printer_id=self.printer_id, error=str(e))
            if self.session:
                await self.session.close()
                self.session = None
            raise PrinterConnectionError(self.printer_id, str(e))
            
    async def disconnect(self) -> None:
        """Disconnect from Prusa printer."""
        if not self.is_connected:
            return
            
        try:
            if self.session:
                await self.session.close()
                
            self.is_connected = False
            self.session = None
            
            logger.info("Disconnected from Prusa printer", printer_id=self.printer_id)
            
        except Exception as e:
            logger.error("Error disconnecting from Prusa printer",
                        printer_id=self.printer_id, error=str(e))
            
    async def get_status(self) -> PrinterStatusUpdate:
        """Get current printer status from Prusa."""
        if not self.is_connected or not self.session:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            # Get printer status from PrusaLink
            async with self.session.get(f"{self.base_url}/printer") as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                    
                status_data = await response.json()
                
            # Get job information
            job_data = {}
            try:
                async with self.session.get(f"{self.base_url}/job") as job_response:
                    if job_response.status == 200:
                        job_data = await job_response.json()
            except Exception as e:
                logger.warning("Failed to get job data from Prusa",
                              printer_id=self.printer_id, error=str(e))
            
            # Map Prusa status to our PrinterStatus
            prusa_state = status_data.get('state', {}).get('text', 'Unknown')
            printer_status = self._map_prusa_status(prusa_state)
            
            # Extract temperature data
            temp_data = status_data.get('temperature', {})
            bed_temp = temp_data.get('bed', {}).get('actual', 0)
            nozzle_temp = temp_data.get('tool0', {}).get('actual', 0)
            
            # Extract job information
            current_job = job_data.get('job', {}).get('file', {}).get('display', '')
            progress = int(job_data.get('progress', {}).get('completion', 0) or 0)
            
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=printer_status,
                message=f"Prusa status: {prusa_state}",
                temperature_bed=float(bed_temp),
                temperature_nozzle=float(nozzle_temp),
                progress=progress,
                current_job=current_job if current_job else None,
                timestamp=datetime.now(),
                raw_data={**status_data, 'job': job_data}
            )
            
        except Exception as e:
            logger.error("Failed to get Prusa status",
                        printer_id=self.printer_id, error=str(e))
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=PrinterStatus.ERROR,
                message=f"Status check failed: {str(e)}",
                timestamp=datetime.now()
            )
            
    def _map_prusa_status(self, prusa_state: str) -> PrinterStatus:
        """Map Prusa state to PrinterStatus."""
        state_lower = prusa_state.lower()
        
        if 'operational' in state_lower or 'ready' in state_lower:
            return PrinterStatus.ONLINE
        elif 'printing' in state_lower:
            return PrinterStatus.PRINTING
        elif 'paused' in state_lower:
            return PrinterStatus.PAUSED
        elif 'error' in state_lower or 'offline' in state_lower:
            return PrinterStatus.ERROR
        else:
            return PrinterStatus.UNKNOWN
            
    async def get_job_info(self) -> Optional[JobInfo]:
        """Get current job information from Prusa."""
        if not self.is_connected or not self.session:
            return None
            
        try:
            async with self.session.get(f"{self.base_url}/job") as response:
                if response.status != 200:
                    return None
                    
                job_data = await response.json()
                
            job_info_data = job_data.get('job', {})
            if not job_info_data.get('file', {}).get('name'):
                return None  # No active job
                
            file_info = job_info_data.get('file', {})
            progress_info = job_data.get('progress', {})
            
            job_name = file_info.get('display', file_info.get('name', 'Unknown Job'))
            progress = int(progress_info.get('completion', 0) or 0)
            
            # Get state and map to JobStatus
            state = job_data.get('state', 'Unknown')
            job_status = self._map_job_status(state)
            
            # Time information
            print_time = progress_info.get('printTime', 0)
            print_time_left = progress_info.get('printTimeLeft', 0)
            
            job_info = JobInfo(
                job_id=f"{self.printer_id}_{job_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name=job_name,
                status=job_status,
                progress=progress,
                estimated_time=print_time_left if print_time_left > 0 else None,
                elapsed_time=print_time if print_time > 0 else None
            )
            
            return job_info
            
        except Exception as e:
            logger.error("Failed to get Prusa job info",
                        printer_id=self.printer_id, error=str(e))
            return None
            
    def _map_job_status(self, prusa_state: str) -> JobStatus:
        """Map Prusa state to JobStatus."""
        state_lower = prusa_state.lower()
        
        if 'operational' in state_lower or 'ready' in state_lower:
            return JobStatus.IDLE
        elif 'printing' in state_lower:
            return JobStatus.PRINTING
        elif 'paused' in state_lower:
            return JobStatus.PAUSED
        elif 'cancelling' in state_lower or 'cancelled' in state_lower:
            return JobStatus.CANCELLED
        elif 'error' in state_lower:
            return JobStatus.FAILED
        else:
            return JobStatus.IDLE
            
    async def list_files(self) -> List[PrinterFile]:
        """List files available on Prusa printer."""
        if not self.is_connected or not self.session:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            # Get file list from PrusaLink
            async with self.session.get(f"{self.base_url}/files") as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                    
                files_data = await response.json()
                
            printer_files = []
            
            # Process local files
            local_files = files_data.get('files', [])
            for file_data in local_files:
                if file_data.get('type') == 'model':  # Only 3D model files
                    file_obj = PrinterFile(
                        filename=file_data.get('display', file_data.get('name', 'Unknown')),
                        size=file_data.get('size'),
                        modified=datetime.fromtimestamp(file_data.get('date', 0)) 
                                 if file_data.get('date') else None,
                        path=file_data.get('path', file_data.get('name', ''))
                    )
                    printer_files.append(file_obj)
                    
            # Process SD card files if available
            if 'sdcard' in files_data and files_data['sdcard'].get('ready'):
                sd_files = files_data.get('sdcard', {}).get('files', [])
                for file_data in sd_files:
                    if file_data.get('type') == 'model':
                        file_obj = PrinterFile(
                            filename=f"[SD] {file_data.get('display', file_data.get('name', 'Unknown'))}",
                            size=file_data.get('size'),
                            modified=datetime.fromtimestamp(file_data.get('date', 0)) 
                                     if file_data.get('date') else None,
                            path=f"sdcard/{file_data.get('path', file_data.get('name', ''))}"
                        )
                        printer_files.append(file_obj)
                        
            logger.info("Retrieved file list from Prusa",
                       printer_id=self.printer_id, file_count=len(printer_files))
            return printer_files
            
        except Exception as e:
            logger.error("Failed to list files from Prusa",
                        printer_id=self.printer_id, error=str(e))
            raise PrinterConnectionError(self.printer_id, f"File listing failed: {str(e)}")
            
    async def download_file(self, filename: str, local_path: str) -> bool:
        """Download a file from Prusa printer."""
        if not self.is_connected or not self.session:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            logger.info("Starting file download from Prusa",
                       printer_id=self.printer_id, filename=filename, local_path=local_path)
                       
            # Construct download URL - handle SD card files
            if filename.startswith('[SD]'):
                # Remove [SD] prefix and use sdcard path
                clean_filename = filename[5:].strip()
                download_url = f"{self.base_url}/files/sdcard/{clean_filename}"
            else:
                download_url = f"{self.base_url}/files/local/{filename}"
                
            # Download file
            async with self.session.get(download_url) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                    
                # Ensure local directory exists
                Path(local_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Write file content
                with open(local_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        
            logger.info("Successfully downloaded file from Prusa",
                       printer_id=self.printer_id, filename=filename)
            return True
            
        except Exception as e:
            logger.error("Failed to download file from Prusa",
                        printer_id=self.printer_id, filename=filename, error=str(e))
            return False
            
    async def pause_print(self) -> bool:
        """Pause the current print job on Prusa printer."""
        if not self.is_connected or not self.session:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            logger.info("Pausing print on Prusa printer", printer_id=self.printer_id)
            
            # Send pause command to PrusaLink
            async with self.session.post(f"{self.base_url}/job", 
                                       json={"command": "pause", "action": "pause"}) as response:
                if response.status == 204:
                    logger.info("Successfully paused print", printer_id=self.printer_id)
                    return True
                else:
                    logger.warning("Failed to pause print", 
                                 printer_id=self.printer_id, status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Error pausing print on Prusa",
                        printer_id=self.printer_id, error=str(e))
            return False
            
    async def resume_print(self) -> bool:
        """Resume the paused print job on Prusa printer."""
        if not self.is_connected or not self.session:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            logger.info("Resuming print on Prusa printer", printer_id=self.printer_id)
            
            # Send resume command to PrusaLink
            async with self.session.post(f"{self.base_url}/job", 
                                       json={"command": "pause", "action": "resume"}) as response:
                if response.status == 204:
                    logger.info("Successfully resumed print", printer_id=self.printer_id)
                    return True
                else:
                    logger.warning("Failed to resume print", 
                                 printer_id=self.printer_id, status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Error resuming print on Prusa",
                        printer_id=self.printer_id, error=str(e))
            return False
            
    async def stop_print(self) -> bool:
        """Stop/cancel the current print job on Prusa printer."""
        if not self.is_connected or not self.session:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            logger.info("Stopping print on Prusa printer", printer_id=self.printer_id)
            
            # Send cancel command to PrusaLink
            async with self.session.post(f"{self.base_url}/job", 
                                       json={"command": "cancel"}) as response:
                if response.status == 204:
                    logger.info("Successfully stopped print", printer_id=self.printer_id)
                    return True
                else:
                    logger.warning("Failed to stop print", 
                                 printer_id=self.printer_id, status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Error stopping print on Prusa",
                        printer_id=self.printer_id, error=str(e))
            return False