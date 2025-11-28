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

from src.config.constants import file_url
from src.models.printer import PrinterStatus, PrinterStatusUpdate
from src.utils.exceptions import PrinterConnectionError
from .base import BasePrinter, JobInfo, JobStatus, PrinterFile
from src.constants import NetworkConstants, FileConstants

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
            timeout = aiohttp.ClientTimeout(total=NetworkConstants.THUMBNAIL_DOWNLOAD_TIMEOUT_SECONDS, connect=NetworkConstants.PRUSA_CONNECT_TIMEOUT_SECONDS)
            connector = aiohttp.TCPConnector(
                keepalive_timeout=NetworkConstants.PRUSA_KEEPALIVE_TIMEOUT_SECONDS,
                ttl_dns_cache=NetworkConstants.PRUSA_DNS_CACHE_TTL_SECONDS,
                use_dns_cache=True,
                limit=NetworkConstants.PRUSA_CONNECTION_LIMIT,
                enable_cleanup_closed=True
            )

            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
                connector=connector
            )

            # Test connection with version endpoint with retries
            max_retries = NetworkConstants.PRUSA_MAX_RETRIES
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
                        wait_time = (attempt + 1) * NetworkConstants.PRUSA_RETRY_BACKOFF_MULTIPLIER  # Exponential backoff
                        logger.warning("Connection attempt failed, retrying",
                                     printer_id=self.printer_id,
                                     attempt=attempt + 1,
                                     wait_time=wait_time,
                                     error=str(e))
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise

        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as e:
            error_msg = f"Cannot connect to Prusa printer: {str(e)}"
            logger.error("Prusa printer connection failed - check IP address and network",
                        printer_id=self.printer_id, ip=self.ip_address, error=error_msg)
            if self.session:
                await self.session.close()
                self.session = None
            raise PrinterConnectionError(self.printer_id, error_msg)
        except aiohttp.ClientTimeout as e:
            error_msg = f"Connection timeout: {str(e)}"
            logger.error("Prusa printer connection timeout - check network and IP address",
                        printer_id=self.printer_id, ip=self.ip_address, error=error_msg)
            if self.session:
                await self.session.close()
                self.session = None
            raise PrinterConnectionError(self.printer_id, error_msg)
        except aiohttp.ClientResponseError as e:
            error_msg = f"HTTP {e.status}: {e.message}"
            if e.status in (401, 403):
                logger.error("Prusa printer authentication error - check API key",
                            printer_id=self.printer_id, status=e.status, error=error_msg)
            else:
                logger.error("Prusa printer HTTP error",
                            printer_id=self.printer_id, status=e.status, error=error_msg)
            if self.session:
                await self.session.close()
                self.session = None
            raise PrinterConnectionError(self.printer_id, error_msg)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}: Connection failed"
            logger.error("Unexpected error connecting to Prusa printer",
                        printer_id=self.printer_id, error=error_msg, exc_info=True)
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

        except (aiohttp.ClientError, OSError) as e:
            logger.warning("Non-fatal error disconnecting from Prusa printer",
                          printer_id=self.printer_id, error=str(e))
        except Exception as e:
            logger.error("Unexpected error disconnecting from Prusa printer",
                        printer_id=self.printer_id, error=str(e), exc_info=True)
            
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
            except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as e:
                logger.warning("Failed to connect to Prusa for job data",
                              printer_id=self.printer_id, error=str(e))
            except aiohttp.ClientTimeout as e:
                logger.warning("Timeout getting job data from Prusa",
                              printer_id=self.printer_id, error=str(e))
            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON in Prusa job response",
                              printer_id=self.printer_id, error=str(e))
            except Exception as e:
                logger.warning("Unexpected error getting job data from Prusa",
                              printer_id=self.printer_id, error=str(e), exc_info=True)
            
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
            elapsed_time_minutes = None
            print_start_time = None

            if job_data:
                # PrusaLink API returns filename directly, not nested in 'job'
                # Try PrusaLink structure first, then fall back to OctoPrint structure
                current_job = job_data.get('display_name', '')
                if not current_job:
                    # Fall back to OctoPrint structure
                    job_info = job_data.get('job', {})
                    if job_info and job_info.get('file'):
                        file_info = job_info.get('file', {})
                        current_job = file_info.get('display_name', file_info.get('name', ''))

                # Extract progress - PrusaLink returns progress as dict with completion field
                # OctoPrint may return it as direct number or nested
                # Handle both dict and direct number formats
                progress_value = job_data.get('progress')
                if progress_value is not None:
                    if isinstance(progress_value, dict):
                        # Dict format: extract completion field
                        completion = progress_value.get('completion')
                        if completion is not None:
                            # completion is usually 0.0-1.0, convert to percentage
                            progress = int(completion * 100) if completion <= 1.0 else int(completion)
                            logger.debug("Prusa print progress detected (dict)",
                                       printer_id=self.printer_id,
                                       progress=progress,
                                       raw_completion=completion)
                    elif isinstance(progress_value, (int, float)):
                        # Direct number: already a percentage
                        progress = int(progress_value)
                        logger.debug("Prusa print progress detected (direct)",
                                       printer_id=self.printer_id,
                                       progress=progress,
                                       raw_progress=progress_value)

                # Extract time information
                # PrusaLink uses: time_remaining (seconds), time_printing (seconds)
                # OctoPrint uses: printTimeLeft (seconds), printTime (seconds)

                # Try PrusaLink field names first
                time_remaining = job_data.get('time_remaining')
                if time_remaining is not None and time_remaining > 0:
                    remaining_time_minutes = int(time_remaining // 60)
                    from datetime import timedelta
                    estimated_end_time = datetime.now() + timedelta(minutes=remaining_time_minutes)
                else:
                    # Fall back to OctoPrint field names
                    progress_info = job_data.get('progress', {})
                    if isinstance(progress_info, dict):
                        print_time_left = progress_info.get('printTimeLeft')
                        if print_time_left is not None and print_time_left > 0:
                            remaining_time_minutes = int(print_time_left // 60)
                            from datetime import timedelta
                            estimated_end_time = datetime.now() + timedelta(minutes=remaining_time_minutes)

                # Extract elapsed time
                time_printing = job_data.get('time_printing')
                if time_printing is not None and time_printing > 0:
                    elapsed_time_minutes = int(time_printing // 60)
                    from datetime import timedelta
                    print_start_time = datetime.now() - timedelta(seconds=time_printing)
                else:
                    # Fall back to OctoPrint field names
                    progress_info = job_data.get('progress', {})
                    if isinstance(progress_info, dict):
                        print_time = progress_info.get('printTime', 0)
                        if print_time and print_time > 0:
                            elapsed_time_minutes = int(print_time // 60)
                            from datetime import timedelta
                            print_start_time = datetime.now() - timedelta(seconds=print_time)

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
                current_job_thumbnail_url=(file_url(current_job_file_id, 'thumbnail') if current_job_file_id and current_job_has_thumbnail else None),
                remaining_time_minutes=remaining_time_minutes,
                estimated_end_time=estimated_end_time,
                elapsed_time_minutes=elapsed_time_minutes,
                print_start_time=print_start_time,
                timestamp=datetime.now(),
                raw_data={**status_data, 'job': job_data or {}}
            )

        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as e:
            logger.error("Cannot connect to Prusa printer for status",
                        printer_id=self.printer_id, ip=self.ip_address, error=str(e))
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=PrinterStatus.ERROR,
                message=f"Connection failed: {str(e)}",
                timestamp=datetime.now()
            )
        except aiohttp.ClientTimeout as e:
            logger.error("Timeout getting Prusa status",
                        printer_id=self.printer_id, error=str(e))
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=PrinterStatus.ERROR,
                message=f"Status check timeout: {str(e)}",
                timestamp=datetime.now()
            )
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in Prusa status response",
                        printer_id=self.printer_id, error=str(e))
            return PrinterStatusUpdate(
                printer_id=self.printer_id,
                status=PrinterStatus.ERROR,
                message=f"Invalid response format: {str(e)}",
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error("Unexpected error getting Prusa status",
                        printer_id=self.printer_id, error=str(e), exc_info=True)
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
                
            # PrusaLink API returns job data directly, not nested in 'job'
            # Try PrusaLink structure first
            job_name = job_data.get('display_name', '')
            if not job_name:
                # Fall back to OctoPrint structure
                job_info_data = job_data.get('job', {})
                if not job_info_data.get('file', {}).get('name'):
                    return None  # No active job
                file_info = job_info_data.get('file', {})
                job_name = file_info.get('display_name', file_info.get('name', 'Unknown Job'))

            if not job_name:
                return None  # No active job

            # Extract progress - Handle both dict and direct number formats
            progress = 0
            progress_value = job_data.get('progress')
            if progress_value is not None:
                if isinstance(progress_value, dict):
                    # Dict format: extract completion field
                    completion = progress_value.get('completion')
                    if completion is not None:
                        # completion is usually 0.0-1.0, convert to percentage
                        progress = int(completion * 100) if completion <= 1.0 else int(completion)
                elif isinstance(progress_value, (int, float)):
                    # Direct number: already a percentage
                    progress = int(progress_value)

            # Get state and map to JobStatus
            state = job_data.get('state', 'Unknown')
            job_status = self._map_job_status(state)

            # Time information - PrusaLink uses time_printing, time_remaining
            # OctoPrint uses printTime, printTimeLeft
            print_time = job_data.get('time_printing', 0)
            print_time_left = job_data.get('time_remaining', 0)

            # Fall back to OctoPrint field names if PrusaLink fields not present
            if print_time == 0 or print_time_left == 0:
                progress_info = job_data.get('progress', {})
                if isinstance(progress_info, dict):
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

        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as e:
            logger.warning("Cannot connect to Prusa printer to list files",
                          printer_id=self.printer_id, error=str(e))
            return []
        except aiohttp.ClientTimeout as e:
            logger.warning("Timeout listing files from Prusa",
                          printer_id=self.printer_id, error=str(e))
            return []
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON in Prusa files response",
                          printer_id=self.printer_id, error=str(e))
            return []
        except Exception as e:
            logger.warning("Unexpected error listing files from Prusa - returning empty list",
                          printer_id=self.printer_id, error=str(e), exc_info=True)
            return []
    
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

        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as e:
            logger.warning("Cannot connect to Prusa printer to get files",
                          printer_id=self.printer_id, error=str(e))
            return []
        except aiohttp.ClientTimeout as e:
            logger.warning("Timeout getting files from Prusa",
                          printer_id=self.printer_id, error=str(e))
            return []
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON in Prusa files response",
                          printer_id=self.printer_id, error=str(e))
            return []
        except Exception as e:
            logger.warning("Unexpected error getting files from Prusa - returning empty list",
                          printer_id=self.printer_id, error=str(e), exc_info=True)
            return []
            
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

            # IMPORTANT: PrusaLink Binary Download Endpoint
            # ==============================================
            # The PrusaLink API provides file metadata via refs.download field,
            # but this path alone is NOT sufficient for authentication.
            #
            # CORRECT ENDPOINT: /api/v1/files/{storage}/{path}
            #   - Requires X-Api-Key header (already set in self.session)
            #   - Returns binary content (application/octet-stream)
            #   - Supports: usb, local, sdcard storage types
            #
            # INCORRECT: Using refs.download directly (e.g., /usb/FILE)
            #   - Returns 401 Unauthorized (no auth context)
            #   - May return JSON metadata instead of binary
            #
            # Example: refs.download="/usb/FILENAME.BGC"
            #   Parse to: storage="usb", path="FILENAME.BGC"
            #   Full URL: http://{ip}/api/v1/files/usb/FILENAME.BGC

            # Get the download reference from the file info
            download_ref = file_info.get('refs', {}).get('download')
            if not download_ref:
                logger.error("No download reference found for file",
                           printer_id=self.printer_id, filename=filename)
                return False

            logger.debug(f"Raw file_info for debugging: {file_info}",
                        printer_id=self.printer_id)
            logger.debug(f"Download reference: '{download_ref}'",
                        printer_id=self.printer_id)

            # Parse storage type and path from download_ref
            # Expected formats: "/usb/FILE", "usb/FILE", "/local/path/FILE"
            download_ref_clean = download_ref.lstrip('/')  # Remove leading slash
            path_parts = download_ref_clean.split('/', 1)  # Split on first / only

            if len(path_parts) != 2:
                logger.error("Invalid download reference format",
                           printer_id=self.printer_id,
                           filename=filename,
                           download_ref=download_ref,
                           expected_format="storage/path")
                return False

            storage_type = path_parts[0]  # e.g., "usb", "local", "sdcard"
            file_path = path_parts[1]      # e.g., "FILENAME.BGC" or "subdir/file.gcode"

            # Construct the correct PrusaLink API endpoint for binary download
            download_url = f"http://{self.ip_address}/api/v1/files/{storage_type}/{file_path}"

            logger.info("Constructed binary download URL",
                       printer_id=self.printer_id,
                       filename=filename,
                       storage=storage_type,
                       path=file_path,
                       download_url=download_url)

            logger.info("Downloading file using API reference",
                       printer_id=self.printer_id,
                       filename=filename,
                       download_url=download_url)

            # Download the file
            async with self.session.get(download_url) as response:
                if response.status == 200:
                    # Ensure local directory exists
                    Path(local_path).parent.mkdir(parents=True, exist_ok=True)

                    # Read first chunk to validate content type
                    first_chunk = None
                    chunks = []

                    async for chunk in response.content.iter_chunked(FileConstants.DOWNLOAD_CHUNK_SIZE_BYTES):
                        if first_chunk is None:
                            first_chunk = chunk
                            # Validate that this is not JSON metadata
                            if chunk.startswith(b'{') or chunk.startswith(b'['):
                                # This looks like JSON, not a binary file
                                try:
                                    json_preview = chunk[:200].decode('utf-8', errors='ignore')
                                    logger.error("Downloaded JSON metadata instead of binary file",
                                               printer_id=self.printer_id,
                                               filename=filename,
                                               download_url=download_url,
                                               storage=storage_type,
                                               path=file_path,
                                               content_preview=json_preview)
                                    return False
                                except Exception:
                                    pass
                        chunks.append(chunk)

                    # Write file content
                    with open(local_path, 'wb') as f:
                        for chunk in chunks:
                            f.write(chunk)

                    file_size = Path(local_path).stat().st_size
                    logger.info("Successfully downloaded file from Prusa",
                               printer_id=self.printer_id, filename=filename,
                               local_path=local_path, size_bytes=file_size)
                    return True
                elif response.status == 404:
                    logger.error("File not found on printer",
                                 printer_id=self.printer_id,
                                 filename=filename,
                                 storage=storage_type,
                                 path=file_path,
                                 download_url=download_url,
                                 status=response.status)
                    return False
                elif response.status == 401 or response.status == 403:
                    logger.error("Authentication/authorization failed for file download",
                                 printer_id=self.printer_id,
                                 filename=filename,
                                 download_url=download_url,
                                 status=response.status,
                                 reason=response.reason,
                                 hint="Check API key permissions in PrusaLink settings")
                    return False
                else:
                    logger.error("Download failed with HTTP status",
                               printer_id=self.printer_id,
                               filename=filename,
                               download_url=download_url,
                               storage=storage_type,
                               path=file_path,
                               status=response.status,
                               reason=response.reason)
                    return False

        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as e:
            logger.error("Cannot connect to Prusa printer to download file",
                        printer_id=self.printer_id, filename=filename, error=str(e))
            return False
        except aiohttp.ClientTimeout as e:
            logger.error("Timeout downloading file from Prusa",
                        printer_id=self.printer_id, filename=filename, error=str(e))
            return False
        except OSError as e:
            logger.error("File system error saving downloaded file",
                        printer_id=self.printer_id, filename=filename, local_path=local_path, error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error downloading file from Prusa",
                        printer_id=self.printer_id, filename=filename, error=str(e), exc_info=True)
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

        except (AttributeError, KeyError, TypeError) as e:
            logger.warning("Error processing file list during search",
                          printer_id=self.printer_id,
                          display_name=display_name,
                          error=str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error searching for file",
                        printer_id=self.printer_id,
                        display_name=display_name,
                        error=str(e), exc_info=True)
            return None

    async def download_thumbnail(self, filename: str, size: str = 'l') -> Optional[bytes]:
        """
        Download thumbnail for a file from Prusa printer.

        Args:
            filename: Display name of the file
            size: Thumbnail size - 's' (small/icon) or 'l' (large/thumbnail)

        Returns:
            PNG thumbnail data as bytes, or None if not available
        """
        if not self.is_connected or not self.session:
            logger.warning("Cannot download thumbnail - not connected",
                         printer_id=self.printer_id)
            return None

        try:
            # Find the file to get thumbnail reference
            file_info = await self._find_file_by_display_name(filename)
            if not file_info:
                logger.warning("Cannot download thumbnail - file not found",
                             printer_id=self.printer_id, filename=filename)
                return None

            # Get thumbnail reference from file info
            refs = file_info.get('refs', {})
            thumb_ref = refs.get('thumbnail') if size == 'l' else refs.get('icon')

            if not thumb_ref:
                logger.debug("No thumbnail reference in file metadata",
                           printer_id=self.printer_id, filename=filename, size=size)
                return None

            # Construct thumbnail URL
            base_host = f"http://{self.ip_address}"
            if thumb_ref.startswith('/api/'):
                thumb_url = f"{base_host}{thumb_ref}"
            elif thumb_ref.startswith('/thumb/'):
                # Direct thumbnail path - convert to API endpoint
                thumb_url = f"{base_host}{thumb_ref}"
            else:
                logger.warning("Unexpected thumbnail reference format",
                             printer_id=self.printer_id, thumb_ref=thumb_ref)
                return None

            logger.info("Downloading thumbnail from Prusa",
                       printer_id=self.printer_id, filename=filename,
                       size=size, url=thumb_url)

            # Download the thumbnail
            async with self.session.get(thumb_url) as response:
                if response.status == 200:
                    thumbnail_data = await response.read()
                    logger.info("Successfully downloaded thumbnail",
                               printer_id=self.printer_id, filename=filename,
                               size_bytes=len(thumbnail_data))
                    return thumbnail_data
                else:
                    logger.warning("Failed to download thumbnail",
                                 printer_id=self.printer_id, filename=filename,
                                 status=response.status)
                    return None

        except Exception as e:
            logger.error("Error downloading thumbnail from Prusa",
                        printer_id=self.printer_id, filename=filename, error=str(e))
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

        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as e:
            logger.error("Cannot connect to Prusa printer to pause print",
                        printer_id=self.printer_id, error=str(e))
            return False
        except aiohttp.ClientTimeout as e:
            logger.error("Timeout pausing print on Prusa",
                        printer_id=self.printer_id, error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error pausing print on Prusa",
                        printer_id=self.printer_id, error=str(e), exc_info=True)
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

        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as e:
            logger.error("Cannot connect to Prusa printer to resume print",
                        printer_id=self.printer_id, error=str(e))
            return False
        except aiohttp.ClientTimeout as e:
            logger.error("Timeout resuming print on Prusa",
                        printer_id=self.printer_id, error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error resuming print on Prusa",
                        printer_id=self.printer_id, error=str(e), exc_info=True)
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

        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as e:
            logger.error("Cannot connect to Prusa printer to stop print",
                        printer_id=self.printer_id, error=str(e))
            return False
        except aiohttp.ClientTimeout as e:
            logger.error("Timeout stopping print on Prusa",
                        printer_id=self.printer_id, error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error stopping print on Prusa",
                        printer_id=self.printer_id, error=str(e), exc_info=True)
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