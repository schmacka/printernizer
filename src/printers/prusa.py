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

from src.models.printer import PrinterStatus, PrinterStatusUpdate
from src.utils.exceptions import PrinterConnectionError
from .base import BasePrinter, JobInfo, JobStatus, PrinterFile

logger = structlog.get_logger()


class PrusaPrinter(BasePrinter):
    """Prusa Core One printer implementation using PrusaLink HTTP API."""
    
    def __init__(self, printer_id: str, name: str, ip_address: str,
                 api_key: str, file_service=None, **kwargs):
        """Initialize Prusa printer."""
        super().__init__(printer_id, name, ip_address, **kwargs)
        self.api_key = api_key
        self.base_url = f"http://{ip_address}/api"
        self.session: Optional[aiohttp.ClientSession] = None
        self.file_service = file_service
        
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

            # Increase timeout and add retries for better connectivity
            timeout = aiohttp.ClientTimeout(total=15, connect=10)
            connector = aiohttp.TCPConnector(
                keepalive_timeout=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
                limit=10,
                enable_cleanup_closed=True
            )

            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
                connector=connector
            )

            # Test connection with version endpoint with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    async with self.session.get(f"{self.base_url}/version") as response:
                        if response.status == 200:
                            version_data = await response.json()
                            logger.info("Successfully connected to Prusa printer",
                                       printer_id=self.printer_id,
                                       version=version_data.get('server', 'Unknown'),
                                       attempt=attempt + 1)
                            self.is_connected = True
                            return True
                        elif response.status == 401:
                            raise aiohttp.ClientError(f"Authentication failed - check API key")
                        elif response.status == 403:
                            raise aiohttp.ClientError(f"Access forbidden - check API key permissions")
                        else:
                            raise aiohttp.ClientError(f"HTTP {response.status}")

                except (asyncio.TimeoutError, aiohttp.ClientConnectorError) as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # Exponential backoff
                        logger.warning("Connection attempt failed, retrying",
                                     printer_id=self.printer_id,
                                     attempt=attempt + 1,
                                     wait_time=wait_time,
                                     error=str(e))
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}: Connection failed"
            if "Authentication failed" in error_msg or "Access forbidden" in error_msg:
                logger.error("Prusa printer authentication error",
                            printer_id=self.printer_id, error=error_msg)
            elif "timeout" in error_msg.lower() or isinstance(e, asyncio.TimeoutError):
                logger.error("Prusa printer connection timeout - check network and IP address",
                            printer_id=self.printer_id, ip=self.ip_address, error=error_msg)
            else:
                logger.error("Failed to connect to Prusa printer",
                            printer_id=self.printer_id, error=error_msg,
                            error_type=type(e).__name__)

            if self.session:
                await self.session.close()
                self.session = None
            raise PrinterConnectionError(self.printer_id, error_msg)
            
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
            
            # Extract job information - handle case where job_data might be None
            current_job = ''
            progress = 0
            remaining_time_minutes = None
            estimated_end_time = None

            if job_data:
                job_info = job_data.get('job', {})
                if job_info and job_info.get('file'):
                    file_info = job_info.get('file', {})
                    # Try 'display_name' first (long filename), then fall back to 'name' (short filename)
                    current_job = file_info.get('display_name', file_info.get('name', ''))

                progress_info = job_data.get('progress', {})
                if progress_info:
                    progress = int(progress_info.get('completion', 0) or 0)

                    # Extract remaining time from Prusa API
                    print_time_left = progress_info.get('printTimeLeft')
                    if print_time_left is not None and print_time_left > 0:
                        # printTimeLeft is in seconds, convert to minutes
                        remaining_time_minutes = int(print_time_left // 60)
                        # Calculate estimated end time
                        from datetime import timedelta
                        estimated_end_time = datetime.now() + timedelta(minutes=remaining_time_minutes)

            # Lookup file information for current job
            current_job_file_id = None
            current_job_has_thumbnail = None
            if current_job and self.file_service:
                try:
                    file_record = await self.file_service.find_file_by_name(current_job, self.printer_id)
                    if file_record:
                        current_job_file_id = file_record.get('id')
                        current_job_has_thumbnail = file_record.get('has_thumbnail', False)
                        logger.debug("Found file record for current job (Prusa)",
                                    printer_id=self.printer_id,
                                    filename=current_job,
                                    file_id=current_job_file_id,
                                    has_thumbnail=current_job_has_thumbnail)
                except Exception as e:
                    logger.debug("Failed to lookup file for current job (Prusa)",
                                printer_id=self.printer_id,
                                filename=current_job,
                                error=str(e))

            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=printer_status,
                message=f"Prusa status: {prusa_state}",
                temperature_bed=float(bed_temp),
                temperature_nozzle=float(nozzle_temp),
                progress=progress,
                current_job=current_job if current_job else None,
                current_job_file_id=current_job_file_id,
                current_job_has_thumbnail=current_job_has_thumbnail,
                current_job_thumbnail_url=(f"/api/v1/files/{current_job_file_id}/thumbnail" if current_job_file_id and current_job_has_thumbnail else None),
                remaining_time_minutes=remaining_time_minutes,
                estimated_end_time=estimated_end_time,
                timestamp=datetime.now(),
                raw_data={**status_data, 'job': job_data or {}}
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
            
            job_name = file_info.get('display_name', file_info.get('name', 'Unknown Job'))
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
                if response.status == 403:
                    logger.warning("Access denied to Prusa files API - check API key permissions",
                                  printer_id=self.printer_id, status_code=response.status)
                    return []  # Return empty list instead of raising exception
                elif response.status != 200:
                    logger.warning("Failed to get files from Prusa API", 
                                  printer_id=self.printer_id, status_code=response.status)
                    return []  # Return empty list for other HTTP errors too
                    
                files_data = await response.json()
                
            printer_files = []
            
            # Process files from PrusaLink response
            # PrusaLink structure: files may contain folders with children arrays
            def extract_files_from_structure(items, prefix=""):
                """Recursively extract files from PrusaLink folder structure."""
                extracted = []
                
                for item in items:
                    item_type = item.get('type', '')
                    
                    if item_type == 'folder' and 'children' in item:
                        # This is a folder (like USB), process its children
                        folder_name = item.get('display', item.get('name', ''))
                        folder_prefix = f"[{folder_name}] " if prefix == "" else f"{prefix}{folder_name}/"
                        
                        # Recursively process children
                        children_files = extract_files_from_structure(
                            item['children'], 
                            folder_prefix
                        )
                        extracted.extend(children_files)
                        
                    elif item_type != 'folder':
                        # This is likely a file (PrusaLink doesn't always set type for files)
                        # Check if it has common printable file extensions or references
                        name = item.get('name', '')
                        display_name = item.get('display', name)
                        
                        # Check if this looks like a printable file
                        if (name.lower().endswith(('.gcode', '.bgcode', '.stl')) or 
                            display_name.lower().endswith(('.gcode', '.bgcode', '.stl')) or
                            'refs' in item):  # Files with refs are usually printable
                            
                            file_obj = PrinterFile(
                                filename=f"{prefix}{display_name}",
                                size=item.get('size'),
                                modified=datetime.fromtimestamp(item.get('date', 0)) 
                                         if item.get('date') else None,
                                path=item.get('path', name)
                            )
                            extracted.append(file_obj)
                        
                return extracted
            
            # Extract files from the main files array
            local_files = files_data.get('files', [])
            printer_files.extend(extract_files_from_structure(local_files))
                    
            # Process SD card files if available (alternative structure)
            if 'sdcard' in files_data and files_data['sdcard'].get('ready'):
                sd_files = files_data.get('sdcard', {}).get('files', [])
                sd_extracted = extract_files_from_structure(sd_files, "[SD] ")
                printer_files.extend(sd_extracted)
                        
            logger.info("Retrieved file list from Prusa",
                       printer_id=self.printer_id, file_count=len(printer_files))
            return printer_files
            
        except Exception as e:
            logger.warning("Failed to list files from Prusa - returning empty list",
                          printer_id=self.printer_id, error=str(e))
            return []  # Return empty list instead of raising exception
    
    async def get_files(self) -> List[dict]:
        """Get raw file data from Prusa printer API (for download references)."""
        if not self.is_connected or not self.session:
            raise PrinterConnectionError(self.printer_id, "Not connected")
            
        try:
            # Get file list from PrusaLink
            async with self.session.get(f"{self.base_url}/files") as response:
                if response.status == 403:
                    logger.warning("Access denied to Prusa files API - check API key permissions",
                                  printer_id=self.printer_id, status_code=response.status)
                    return []  # Return empty list instead of raising exception
                elif response.status != 200:
                    logger.warning("Failed to get files from Prusa API", 
                                  printer_id=self.printer_id, status_code=response.status)
                    return []  # Return empty list for other HTTP errors too
                    
                files_data = await response.json()
                
            raw_files = []
            
            # Process files from PrusaLink response and flatten structure
            def extract_raw_files_from_structure(items, prefix=""):
                """Recursively extract raw file data from PrusaLink folder structure."""
                extracted = []
                
                for item in items:
                    item_type = item.get('type', '')
                    
                    if item_type == 'folder' and 'children' in item:
                        # This is a folder (like USB), process its children
                        folder_name = item.get('display', item.get('name', ''))
                        folder_prefix = f"[{folder_name}] " if prefix == "" else f"{prefix}{folder_name}/"
                        
                        # Recursively process children
                        children_files = extract_raw_files_from_structure(
                            item['children'], 
                            folder_prefix
                        )
                        extracted.extend(children_files)
                        
                    elif item_type != 'folder':
                        # This is likely a file (PrusaLink doesn't always set type for files)
                        # Check if it has common printable file extensions or references
                        name = item.get('name', '')
                        display_name = item.get('display', name)
                        
                        # Check if this looks like a printable file
                        if (name.lower().endswith(('.gcode', '.bgcode', '.stl')) or 
                            display_name.lower().endswith(('.gcode', '.bgcode', '.stl')) or
                            'refs' in item):  # Files with refs are usually printable
                            
                            # Create a copy with prefixed display name but preserve all raw data
                            raw_file = dict(item)
                            raw_file['display'] = f"{prefix}{display_name}"
                            extracted.append(raw_file)
                        
                return extracted
            
            # Extract files from the main files array
            local_files = files_data.get('files', [])
            raw_files.extend(extract_raw_files_from_structure(local_files))
                    
            # Process SD card files if available (alternative structure)
            if 'sdcard' in files_data and files_data['sdcard'].get('ready'):
                sd_files = files_data.get('sdcard', {}).get('files', [])
                sd_extracted = extract_raw_files_from_structure(sd_files, "[SD] ")
                raw_files.extend(sd_extracted)
                        
            logger.info("Retrieved raw file data from Prusa",
                       printer_id=self.printer_id, file_count=len(raw_files))
            return raw_files
            
        except Exception as e:
            logger.warning("Failed to get raw files from Prusa - returning empty list",
                          printer_id=self.printer_id, error=str(e))
            return []  # Return empty list instead of raising exception
            
    async def download_file(self, filename: str, local_path: str) -> bool:
        """Download a file from Prusa printer."""
        if not self.is_connected or not self.session:
            raise PrinterConnectionError(self.printer_id, "Not connected")

        try:
            logger.info("Starting file download from Prusa",
                       printer_id=self.printer_id, filename=filename, local_path=local_path)

            # First, get the file list to find the actual download path
            file_info = await self._find_file_by_display_name(filename)
            if not file_info:
                logger.error("File not found in printer file list",
                           printer_id=self.printer_id, filename=filename)
                return False

            # Get the download reference from the file info
            download_ref = file_info.get('refs', {}).get('download')
            if not download_ref:
                logger.error("No download reference found for file",
                           printer_id=self.printer_id, filename=filename)
                return False

            logger.info(f"Raw file_info for debugging: {file_info}",
                        printer_id=self.printer_id)
            logger.info(f"Download reference: '{download_ref}'",
                        printer_id=self.printer_id)

            # Construct the full download URL
            # Fix PrusaLink API path based on the actual format returned
            base_host = f"http://{self.ip_address}"  # Get just the host without /api
            
            if download_ref.startswith('/api/'):
                # Modern API format - use as is
                download_url = f"{self.base_url}{download_ref}"
                logger.info(f"Using modern API path: {download_url}", printer_id=self.printer_id)
            elif download_ref.startswith('/apiusb/'):
                # Legacy format with leading slash
                filename_part = download_ref[8:]  # Remove '/apiusb/'
                download_url = f"{base_host}/api/v1/files/usb/{filename_part}"
                logger.info(f"Converted legacy /apiusb/ path: {download_ref} -> {download_url}", printer_id=self.printer_id)
            elif download_ref.startswith('/apisd/'):
                # Legacy format with leading slash
                filename_part = download_ref[7:]  # Remove '/apisd/'
                download_url = f"{base_host}/api/v1/files/sdcard/{filename_part}"
                logger.info(f"Converted legacy /apisd/ path: {download_ref} -> {download_url}", printer_id=self.printer_id)
            elif download_ref.startswith('usb/'):
                # Modern format without leading slash - convert to proper API path
                filename_part = download_ref[4:]  # Remove 'usb/'
                download_url = f"{base_host}/api/v1/files/usb/{filename_part}"
                logger.info(f"Converted modern usb/ path: {download_ref} -> {download_url}", printer_id=self.printer_id)
            elif download_ref.startswith('sdcard/'):
                # Modern format without leading slash - convert to proper API path
                filename_part = download_ref[7:]  # Remove 'sdcard/'
                download_url = f"{base_host}/api/v1/files/sdcard/{filename_part}"
                logger.info(f"Converted modern sdcard/ path: {download_ref} -> {download_url}", printer_id=self.printer_id)
            else:
                # Try legacy format construction as fallback
                download_url = f"{base_host}/apiusb/{download_ref}"
                logger.info(f"Using legacy fallback path: {download_url}", printer_id=self.printer_id)

            logger.info("Downloading file using API reference",
                       printer_id=self.printer_id,
                       filename=filename,
                       download_url=download_url)

            # Download the file
            async with self.session.get(download_url) as response:
                if response.status == 200:
                    # Ensure local directory exists
                    Path(local_path).parent.mkdir(parents=True, exist_ok=True)

                    # Write file content
                    with open(local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

                    logger.info("Successfully downloaded file from Prusa",
                               printer_id=self.printer_id, filename=filename, local_path=local_path)
                    return True
                else:
                    logger.error("Download failed with HTTP status",
                               printer_id=self.printer_id,
                               filename=filename,
                               status=response.status)
                    return False

        except Exception as e:
            logger.error("Failed to download file from Prusa",
                        printer_id=self.printer_id, filename=filename, error=str(e))
            return False

    async def _find_file_by_display_name(self, display_name: str) -> Optional[dict]:
        """Find a file in the printer's file list by its display name."""
        try:
            files = await self.get_files()
            
            logger.debug(f"Searching for file: '{display_name}' among {len(files)} files",
                        printer_id=self.printer_id)

            # First try exact matches
            for file_info in files:
                file_display = file_info.get('display', '')
                file_name = file_info.get('name', '')
                
                if file_display == display_name or file_name == display_name:
                    logger.debug(f"Found exact match: display='{file_display}', name='{file_name}'",
                               printer_id=self.printer_id)
                    return file_info
            
            # If no exact match, try partial matches (case-insensitive)
            display_name_lower = display_name.lower()
            for file_info in files:
                file_display = file_info.get('display', '')
                file_name = file_info.get('name', '')
                
                if (display_name_lower in file_display.lower() or 
                    display_name_lower in file_name.lower() or
                    file_display.lower() in display_name_lower or
                    file_name.lower() in display_name_lower):
                    
                    logger.info(f"Found partial match for '{display_name}': display='{file_display}', name='{file_name}'",
                               printer_id=self.printer_id)
                    return file_info
            
            # Log all available files for debugging
            logger.warning(f"No match found for '{display_name}'. Available files:",
                          printer_id=self.printer_id)
            for i, file_info in enumerate(files[:10]):  # Log first 10 files
                logger.warning(f"  [{i}] display='{file_info.get('display', '')}', name='{file_info.get('name', '')}'",
                              printer_id=self.printer_id)
            if len(files) > 10:
                logger.warning(f"  ... and {len(files) - 10} more files", printer_id=self.printer_id)

            return None

        except Exception as e:
            logger.error("Failed to search for file",
                        printer_id=self.printer_id,
                        display_name=display_name,
                        error=str(e))
            return None
            
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

    async def has_camera(self) -> bool:
        """Check if Prusa printer has camera support."""
        # Prusa Core One typically doesn't have integrated camera support
        # This could be extended in the future if camera support is added
        return False

    async def get_camera_stream_url(self) -> Optional[str]:
        """Get camera stream URL for Prusa printer."""
        # Prusa Core One doesn't have integrated camera support
        logger.debug("Camera not supported on Prusa printer", printer_id=self.printer_id)
        return None

    async def take_snapshot(self) -> Optional[bytes]:
        """Take a camera snapshot from Prusa printer."""
        # Prusa Core One doesn't have integrated camera support
        logger.debug("Camera not supported on Prusa printer", printer_id=self.printer_id)
        return None