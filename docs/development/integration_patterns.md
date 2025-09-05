# Printernizer Integration Patterns

## Overview

This document defines the integration patterns for communicating with different printer types in the Printernizer system. Each printer manufacturer uses different protocols and communication patterns, requiring specialized integration approaches while maintaining a unified internal interface.

## Integration Architecture Principles

### 1. **Protocol Abstraction**
- Unified interface across all printer types
- Protocol-specific implementations behind common abstractions
- Consistent error handling and recovery patterns

### 2. **Event-Driven Communication**
- Real-time status updates via event publishing
- Asynchronous processing for non-blocking operations
- Reliable message delivery with retry mechanisms

### 3. **Connection Management**
- Automatic connection recovery and health monitoring
- Configurable timeouts and retry policies
- Circuit breaker patterns for failing connections

### 4. **Data Normalization**
- Convert manufacturer-specific data formats to internal models
- Standardized status codes and progress reporting
- Unified file listing and metadata extraction

---

## Bambu Lab Integration Pattern (MQTT)

### Protocol Characteristics
- **Communication**: MQTT over TCP/IP
- **Library**: `bambulabs-api` Python library
- **Authentication**: IP Address + Access Code + Serial Number
- **Real-time Updates**: Event-driven via MQTT callbacks
- **Connection**: Persistent MQTT connection with automatic reconnection

### Implementation Pattern

```python
import asyncio
import json
from datetime import datetime
from typing import Dict, Optional, Callable, Any
from bambulabs_api import BambuClient
from bambulabs_api.types import PrinterStatus as BambuStatus

class BambuLabIntegration(BasePrinterIntegration):
    """
    Bambu Lab printer integration using MQTT protocol
    """
    
    def __init__(self, config: BambuLabConfig, event_publisher: EventPublisher):
        super().__init__(config, event_publisher)
        self.client: Optional[BambuClient] = None
        self.connection_state = ConnectionState.DISCONNECTED
        self.last_status: Optional[BambuStatus] = None
        self.callback_handlers: Dict[str, Callable] = {}
        self._setup_callbacks()
    
    async def connect(self) -> ConnectionResult:
        """
        Establish MQTT connection to Bambu Lab printer
        """
        try:
            # Initialize Bambu client with credentials
            self.client = BambuClient(
                host=self.config.ip_address,
                access_code=self.config.access_code,
                serial=self.config.serial_number
            )
            
            # Set up event callbacks
            self.client.on_printer_status = self._on_printer_status
            self.client.on_print_progress = self._on_print_progress
            self.client.on_temperature_update = self._on_temperature_update
            self.client.on_ams_status = self._on_ams_status
            self.client.on_connection_lost = self._on_connection_lost
            self.client.on_error = self._on_error
            
            # Connect to printer
            await self.client.connect()
            self.connection_state = ConnectionState.CONNECTED
            
            # Subscribe to relevant MQTT topics
            await self._subscribe_to_topics()
            
            # Request initial status
            await self.client.request_status()
            
            self._publish_event("printer_connected", {
                "printer_id": self.config.id,
                "connection_type": "mqtt",
                "firmware_version": await self._get_firmware_version()
            })
            
            return ConnectionResult.success("MQTT connection established")
            
        except Exception as e:
            self.connection_state = ConnectionState.ERROR
            self._publish_event("printer_connection_failed", {
                "printer_id": self.config.id,
                "error": str(e)
            })
            return ConnectionResult.error(f"MQTT connection failed: {str(e)}")
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Bambu Lab printer
        """
        try:
            if self.client:
                await self.client.disconnect()
            self.connection_state = ConnectionState.DISCONNECTED
            self._publish_event("printer_disconnected", {
                "printer_id": self.config.id
            })
            return True
        except Exception as e:
            self._logger.error(f"Disconnect error: {e}")
            return False
    
    async def get_status(self) -> PrinterStatus:
        """
        Get current printer status (uses cached data from MQTT updates)
        """
        if not self.last_status:
            # If no cached status, request fresh data
            if self.client and self.connection_state == ConnectionState.CONNECTED:
                await self.client.request_status()
                # Wait briefly for response
                await asyncio.sleep(0.5)
        
        return self._convert_bambu_status(self.last_status) if self.last_status else None
    
    async def get_current_job(self) -> Optional[JobStatus]:
        """
        Get current print job information
        """
        if not self.last_status:
            return None
        
        # Extract job info from Bambu status
        return JobStatus(
            id=self.last_status.job_id or 0,
            name=self.last_status.gcode_file or "Unknown",
            status=self._convert_job_status(self.last_status.gcode_state),
            progress=float(self.last_status.print_percent or 0),
            layer_current=self.last_status.layer_num or 0,
            layer_total=self.last_status.total_layer_num,
            estimated_remaining=self._calculate_remaining_time()
        )
    
    async def list_files(self) -> List[RemoteFile]:
        """
        List files available on printer storage
        """
        try:
            if not self.client or self.connection_state != ConnectionState.CONNECTED:
                raise ConnectionError("Printer not connected")
            
            # Request file list via MQTT
            file_data = await self.client.request_file_list()
            
            files = []
            for file_info in file_data.get("files", []):
                files.append(RemoteFile(
                    name=file_info["name"],
                    path=file_info["path"],
                    size=file_info["size"],
                    modified=datetime.fromisoformat(file_info["time"]),
                    type=self._get_file_type(file_info["name"])
                ))
            
            return files
            
        except Exception as e:
            self._logger.error(f"Failed to list files: {e}")
            return []
    
    async def download_file(self, file_path: str) -> bytes:
        """
        Download file from printer storage
        Note: Bambu Lab may not support direct file downloads via MQTT
        This would require HTTP fallback or alternative method
        """
        try:
            # Bambu Lab doesn't directly support file downloads via MQTT
            # This would need to be implemented via HTTP API or alternative method
            raise NotImplementedError(
                "File downloads from Bambu Lab printers require HTTP API access"
            )
            
        except Exception as e:
            self._logger.error(f"File download failed: {e}")
            raise DownloadError(f"Failed to download {file_path}: {str(e)}")
    
    async def cancel_job(self) -> CancelResult:
        """
        Cancel current print job
        """
        try:
            if not self.client or self.connection_state != ConnectionState.CONNECTED:
                return CancelResult.error("Printer not connected")
            
            await self.client.stop_print()
            
            self._publish_event("job_cancel_requested", {
                "printer_id": self.config.id
            })
            
            return CancelResult.success("Cancel command sent")
            
        except Exception as e:
            return CancelResult.error(f"Cancel failed: {str(e)}")
    
    # MQTT Event Handlers
    
    async def _on_printer_status(self, status: BambuStatus):
        """
        Handle printer status updates from MQTT
        """
        self.last_status = status
        self.last_communication = datetime.now()
        
        # Convert and publish internal status update
        internal_status = self._convert_bambu_status(status)
        self._publish_event("printer_status_updated", {
            "printer_id": self.config.id,
            "status": internal_status.dict()
        })
    
    async def _on_print_progress(self, progress_data: Dict[str, Any]):
        """
        Handle print progress updates
        """
        job_update = {
            "printer_id": self.config.id,
            "progress": float(progress_data.get("print_percent", 0)),
            "layer_current": progress_data.get("layer_num", 0),
            "estimated_remaining": self._calculate_remaining_time()
        }
        
        self._publish_event("job_progress_updated", job_update)
    
    async def _on_temperature_update(self, temp_data: Dict[str, Any]):
        """
        Handle temperature updates
        """
        temps = {
            "printer_id": self.config.id,
            "nozzle_temp": temp_data.get("nozzle_temper"),
            "nozzle_target": temp_data.get("nozzle_target_temper"),
            "bed_temp": temp_data.get("bed_temper"),
            "bed_target": temp_data.get("bed_target_temper"),
            "chamber_temp": temp_data.get("chamber_temper")
        }
        
        self._publish_event("temperature_updated", temps)
    
    async def _on_ams_status(self, ams_data: Dict[str, Any]):
        """
        Handle AMS (Automatic Material System) status updates
        """
        self._publish_event("ams_status_updated", {
            "printer_id": self.config.id,
            "ams_data": ams_data
        })
    
    async def _on_connection_lost(self):
        """
        Handle MQTT connection loss
        """
        self.connection_state = ConnectionState.ERROR
        self._publish_event("printer_connection_lost", {
            "printer_id": self.config.id,
            "timestamp": datetime.now()
        })
        
        # Attempt reconnection
        await self._attempt_reconnection()
    
    async def _on_error(self, error: Exception):
        """
        Handle MQTT communication errors
        """
        self._logger.error(f"MQTT error for printer {self.config.id}: {error}")
        self._publish_event("printer_error", {
            "printer_id": self.config.id,
            "error": str(error),
            "error_type": type(error).__name__
        })
    
    # Helper Methods
    
    async def _subscribe_to_topics(self):
        """
        Subscribe to relevant MQTT topics for the printer
        """
        topics = [
            f"device/{self.config.serial_number}/report",  # Status reports
            f"device/{self.config.serial_number}/print",   # Print progress
            f"device/{self.config.serial_number}/camera",  # Camera updates
            f"device/{self.config.serial_number}/ams"      # AMS status
        ]
        
        for topic in topics:
            await self.client.subscribe(topic)
    
    def _convert_bambu_status(self, status: BambuStatus) -> PrinterStatus:
        """
        Convert Bambu Lab status to internal format
        """
        # Map Bambu states to internal states
        state_mapping = {
            "IDLE": InternalStatus.ONLINE,
            "PREPARE": InternalStatus.BUSY,
            "RUNNING": InternalStatus.BUSY,
            "PAUSE": InternalStatus.BUSY,
            "COMPLETE": InternalStatus.ONLINE,
            "FAILED": InternalStatus.ERROR,
            "OFFLINE": InternalStatus.OFFLINE
        }
        
        internal_status = state_mapping.get(status.gcode_state, InternalStatus.UNKNOWN)
        
        return PrinterStatus(
            printer_id=self.config.id,
            status=internal_status,
            temperatures=PrinterTemperatures(
                nozzle=Temperature(
                    current=status.nozzle_temper or 0,
                    target=status.nozzle_target_temper or 0
                ) if status.nozzle_temper is not None else None,
                bed=Temperature(
                    current=status.bed_temper or 0,
                    target=status.bed_target_temper or 0
                ) if status.bed_temper is not None else None,
                chamber=Temperature(
                    current=status.chamber_temper or 0,
                    target=0  # Bambu doesn't usually have chamber heating
                ) if status.chamber_temper is not None else None
            ),
            current_job_progress=float(status.print_percent or 0),
            firmware_version=status.firmware_version,
            last_updated=datetime.now()
        )
    
    def _convert_job_status(self, gcode_state: str) -> JobStatusEnum:
        """
        Convert Bambu job state to internal job status
        """
        mapping = {
            "IDLE": JobStatusEnum.QUEUED,
            "PREPARE": JobStatusEnum.PREPARING,
            "RUNNING": JobStatusEnum.PRINTING,
            "PAUSE": JobStatusEnum.PAUSED,
            "COMPLETE": JobStatusEnum.COMPLETED,
            "FAILED": JobStatusEnum.FAILED,
            "STOPPED": JobStatusEnum.CANCELLED
        }
        return mapping.get(gcode_state, JobStatusEnum.QUEUED)
    
    async def _attempt_reconnection(self):
        """
        Attempt to reconnect to printer with exponential backoff
        """
        max_retries = 5
        base_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(base_delay * (2 ** attempt))  # Exponential backoff
                result = await self.connect()
                
                if result.success:
                    self._logger.info(f"Reconnection successful for {self.config.id}")
                    return
                    
            except Exception as e:
                self._logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
        
        self._logger.error(f"All reconnection attempts failed for {self.config.id}")
```

---

## Prusa Integration Pattern (HTTP)

### Protocol Characteristics
- **Communication**: HTTP REST API (PrusaLink)
- **Authentication**: API Key header
- **Updates**: Polling-based (30-second intervals)
- **Connection**: Stateless HTTP requests with connection pooling

### Implementation Pattern

```python
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

class PrusaIntegration(BasePrinterIntegration):
    """
    Prusa printer integration using PrusaLink HTTP API
    """
    
    def __init__(self, config: PrusaConfig, event_publisher: EventPublisher):
        super().__init__(config, event_publisher)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = f"http://{config.ip_address}:{config.port or 80}/api"
        self.headers = {"X-Api-Key": config.api_key}
        self.polling_task: Optional[asyncio.Task] = None
        self.poll_interval = 30  # seconds
        self.last_status: Optional[Dict] = None
        self.connection_state = ConnectionState.DISCONNECTED
    
    async def connect(self) -> ConnectionResult:
        """
        Establish HTTP connection and start polling
        """
        try:
            # Create HTTP session with connection pooling
            connector = aiohttp.TCPConnector(
                limit=10,  # Connection pool limit
                ttl_dns_cache=300,  # DNS cache TTL
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                headers=self.headers
            )
            
            # Test connection with version endpoint
            version_info = await self._make_request("GET", "/version")
            
            if not version_info:
                raise ConnectionError("Failed to get printer version")
            
            self.connection_state = ConnectionState.CONNECTED
            
            # Start polling task
            self.polling_task = asyncio.create_task(self._polling_loop())
            
            self._publish_event("printer_connected", {
                "printer_id": self.config.id,
                "connection_type": "http",
                "firmware_version": version_info.get("server"),
                "api_version": version_info.get("api")
            })
            
            return ConnectionResult.success("HTTP connection established")
            
        except Exception as e:
            self.connection_state = ConnectionState.ERROR
            await self._cleanup_session()
            
            self._publish_event("printer_connection_failed", {
                "printer_id": self.config.id,
                "error": str(e)
            })
            
            return ConnectionResult.error(f"HTTP connection failed: {str(e)}")
    
    async def disconnect(self) -> bool:
        """
        Stop polling and close HTTP session
        """
        try:
            # Cancel polling task
            if self.polling_task and not self.polling_task.done():
                self.polling_task.cancel()
                try:
                    await self.polling_task
                except asyncio.CancelledError:
                    pass
            
            # Close HTTP session
            await self._cleanup_session()
            
            self.connection_state = ConnectionState.DISCONNECTED
            
            self._publish_event("printer_disconnected", {
                "printer_id": self.config.id
            })
            
            return True
            
        except Exception as e:
            self._logger.error(f"Disconnect error: {e}")
            return False
    
    async def get_status(self) -> Optional[PrinterStatus]:
        """
        Get current printer status via HTTP API
        """
        try:
            status_data = await self._make_request("GET", "/printer")
            
            if not status_data:
                return None
            
            return self._convert_prusa_status(status_data)
            
        except Exception as e:
            self._logger.error(f"Failed to get status: {e}")
            return None
    
    async def get_current_job(self) -> Optional[JobStatus]:
        """
        Get current print job information
        """
        try:
            job_data = await self._make_request("GET", "/job")
            
            if not job_data or not job_data.get("job"):
                return None
            
            job_info = job_data["job"]
            progress = job_data.get("progress", {})
            
            return JobStatus(
                id=0,  # Prusa doesn't provide job IDs
                name=job_info.get("file", {}).get("name", "Unknown"),
                status=self._convert_job_status(job_data.get("state", "Offline")),
                progress=float(progress.get("completion", 0) or 0),
                estimated_remaining=progress.get("printTimeLeft"),
                file_size=job_info.get("file", {}).get("size")
            )
            
        except Exception as e:
            self._logger.error(f"Failed to get job info: {e}")
            return None
    
    async def list_files(self) -> List[RemoteFile]:
        """
        List files available in printer storage
        """
        try:
            files_data = await self._make_request("GET", "/files")
            
            if not files_data:
                return []
            
            files = []
            self._process_file_tree(files_data.get("files", {}), files)
            
            return files
            
        except Exception as e:
            self._logger.error(f"Failed to list files: {e}")
            return []
    
    async def download_file(self, file_path: str) -> bytes:
        """
        Download file from printer storage
        """
        try:
            # Construct download URL
            download_url = f"/files/local{file_path}"
            
            async with self.session.get(
                f"{self.base_url}{download_url}",
                headers=self.headers
            ) as response:
                
                if response.status != 200:
                    raise DownloadError(f"HTTP {response.status}: {response.reason}")
                
                return await response.read()
                
        except Exception as e:
            self._logger.error(f"File download failed: {e}")
            raise DownloadError(f"Failed to download {file_path}: {str(e)}")
    
    async def cancel_job(self) -> CancelResult:
        """
        Cancel current print job
        """
        try:
            result = await self._make_request("POST", "/job", json={"command": "cancel"})
            
            if result is None:  # Successful POST typically returns nothing
                self._publish_event("job_cancel_requested", {
                    "printer_id": self.config.id
                })
                return CancelResult.success("Cancel command sent")
            else:
                return CancelResult.error("Unexpected response from printer")
                
        except Exception as e:
            return CancelResult.error(f"Cancel failed: {str(e)}")
    
    # HTTP Communication Methods
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """
        Make HTTP request to printer API
        """
        if not self.session:
            raise ConnectionError("No active session")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                
                # Handle authentication errors
                if response.status == 401:
                    self._publish_event("printer_auth_error", {
                        "printer_id": self.config.id,
                        "error": "Invalid API key"
                    })
                    raise AuthenticationError("Invalid API key")
                
                # Handle other HTTP errors
                if response.status >= 400:
                    error_text = await response.text()
                    raise HTTPError(f"HTTP {response.status}: {error_text}")
                
                # Parse JSON response
                if response.content_type == "application/json":
                    return await response.json()
                else:
                    # Some endpoints return no content on success
                    return None
                    
        except aiohttp.ClientError as e:
            self._logger.error(f"HTTP request failed: {e}")
            raise ConnectionError(f"Request failed: {str(e)}")
    
    async def _polling_loop(self):
        """
        Main polling loop for status updates
        """
        consecutive_failures = 0
        max_failures = 5
        
        while True:
            try:
                # Get current status
                status_data = await self._make_request("GET", "/printer")
                
                if status_data:
                    await self._process_status_update(status_data)
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                
                # Check for too many failures
                if consecutive_failures >= max_failures:
                    self._logger.error(f"Too many polling failures for {self.config.id}")
                    self.connection_state = ConnectionState.ERROR
                    self._publish_event("printer_connection_lost", {
                        "printer_id": self.config.id,
                        "reason": "Polling failures"
                    })
                    break
                
            except asyncio.CancelledError:
                # Polling task was cancelled
                break
                
            except Exception as e:
                consecutive_failures += 1
                self._logger.error(f"Polling error: {e}")
                
                if consecutive_failures >= max_failures:
                    self.connection_state = ConnectionState.ERROR
                    break
            
            # Wait for next poll
            try:
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
    
    async def _process_status_update(self, status_data: Dict):
        """
        Process status update from polling
        """
        current_status = self._convert_prusa_status(status_data)
        
        # Check if status changed significantly
        if self._status_changed(current_status):
            self.last_status = status_data
            self.last_communication = datetime.now()
            
            self._publish_event("printer_status_updated", {
                "printer_id": self.config.id,
                "status": current_status.dict() if current_status else None
            })
            
            # Also check for job updates
            await self._check_job_updates()
    
    async def _check_job_updates(self):
        """
        Check for job progress updates
        """
        try:
            job_data = await self._make_request("GET", "/job")
            
            if job_data and job_data.get("progress"):
                progress = job_data["progress"]
                
                job_update = {
                    "printer_id": self.config.id,
                    "progress": float(progress.get("completion", 0) or 0),
                    "estimated_remaining": progress.get("printTimeLeft"),
                    "elapsed_time": progress.get("printTime")
                }
                
                self._publish_event("job_progress_updated", job_update)
                
        except Exception as e:
            self._logger.error(f"Failed to check job updates: {e}")
    
    def _convert_prusa_status(self, status_data: Dict) -> Optional[PrinterStatus]:
        """
        Convert Prusa API status to internal format
        """
        printer_info = status_data.get("state", {})
        temp_info = status_data.get("temperature", {})
        
        # Map Prusa states to internal states
        state_text = printer_info.get("text", "").lower()
        if "operational" in state_text:
            internal_status = InternalStatus.ONLINE
        elif any(word in state_text for word in ["printing", "paused"]):
            internal_status = InternalStatus.BUSY
        elif "error" in state_text:
            internal_status = InternalStatus.ERROR
        elif "offline" in state_text:
            internal_status = InternalStatus.OFFLINE
        else:
            internal_status = InternalStatus.UNKNOWN
        
        # Extract temperatures
        temperatures = None
        if temp_info:
            temperatures = PrinterTemperatures()
            
            if "tool0" in temp_info:
                tool_temp = temp_info["tool0"]
                temperatures.nozzle = Temperature(
                    current=tool_temp.get("actual", 0),
                    target=tool_temp.get("target", 0)
                )
            
            if "bed" in temp_info:
                bed_temp = temp_info["bed"]
                temperatures.bed = Temperature(
                    current=bed_temp.get("actual", 0),
                    target=bed_temp.get("target", 0)
                )
        
        return PrinterStatus(
            printer_id=self.config.id,
            status=internal_status,
            temperatures=temperatures,
            last_updated=datetime.now()
        )
    
    def _process_file_tree(self, tree: Dict, files: List[RemoteFile], path_prefix: str = ""):
        """
        Recursively process Prusa file tree structure
        """
        for name, info in tree.items():
            current_path = f"{path_prefix}/{name}" if path_prefix else f"/{name}"
            
            if info.get("type") == "folder":
                # Recurse into subdirectory
                children = info.get("children", {})
                self._process_file_tree(children, files, current_path)
            else:
                # It's a file
                files.append(RemoteFile(
                    name=name,
                    path=current_path,
                    size=info.get("size", 0),
                    modified=datetime.fromtimestamp(info.get("date", 0)),
                    type=self._get_file_type(name)
                ))
    
    def _convert_job_status(self, state: str) -> JobStatusEnum:
        """
        Convert Prusa job state to internal job status
        """
        state_lower = state.lower()
        
        if "printing" in state_lower:
            return JobStatusEnum.PRINTING
        elif "paused" in state_lower:
            return JobStatusEnum.PAUSED
        elif "finished" in state_lower or "complete" in state_lower:
            return JobStatusEnum.COMPLETED
        elif "cancelled" in state_lower or "stopped" in state_lower:
            return JobStatusEnum.CANCELLED
        elif "error" in state_lower or "failed" in state_lower:
            return JobStatusEnum.FAILED
        else:
            return JobStatusEnum.QUEUED
    
    def _status_changed(self, new_status: Optional[PrinterStatus]) -> bool:
        """
        Check if status has changed significantly since last update
        """
        if not self.last_status or not new_status:
            return True
        
        # Compare key status indicators
        old_converted = self._convert_prusa_status(self.last_status)
        
        if not old_converted:
            return True
        
        return (
            old_converted.status != new_status.status or
            abs((old_converted.last_updated - new_status.last_updated).total_seconds()) > 30
        )
    
    async def _cleanup_session(self):
        """
        Clean up HTTP session
        """
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None
```

---

## Common Integration Patterns

### Base Integration Interface

```python
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

@dataclass
class ConnectionResult:
    success: bool
    message: str
    error_code: Optional[str] = None
    
    @classmethod
    def success(cls, message: str) -> "ConnectionResult":
        return cls(success=True, message=message)
    
    @classmethod
    def error(cls, message: str, error_code: str = None) -> "ConnectionResult":
        return cls(success=False, message=message, error_code=error_code)

@dataclass
class CancelResult:
    success: bool
    message: str
    
    @classmethod
    def success(cls, message: str) -> "CancelResult":
        return cls(success=True, message=message)
    
    @classmethod
    def error(cls, message: str) -> "CancelResult":
        return cls(success=False, message=message)

class BasePrinterIntegration(ABC):
    """
    Abstract base class for all printer integrations
    """
    
    def __init__(self, config: PrinterConfig, event_publisher: EventPublisher):
        self.config = config
        self.event_publisher = event_publisher
        self._logger = get_logger(f"printer.{config.id}")
        self.last_communication: Optional[datetime] = None
    
    @abstractmethod
    async def connect(self) -> ConnectionResult:
        """Establish connection to printer"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from printer"""
        pass
    
    @abstractmethod
    async def get_status(self) -> Optional[PrinterStatus]:
        """Get current printer status"""
        pass
    
    @abstractmethod
    async def get_current_job(self) -> Optional[JobStatus]:
        """Get current print job information"""
        pass
    
    @abstractmethod
    async def list_files(self) -> List[RemoteFile]:
        """List files available on printer"""
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """Download file from printer"""
        pass
    
    @abstractmethod
    async def cancel_job(self) -> CancelResult:
        """Cancel current print job"""
        pass
    
    # Common utility methods
    
    def is_connected(self) -> bool:
        """Check if printer is currently connected"""
        return (
            self.last_communication and
            (datetime.now() - self.last_communication).total_seconds() < 120  # 2 minutes
        )
    
    def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to the event system"""
        try:
            self.event_publisher.publish(SystemEvent(
                type=event_type,
                data=data,
                timestamp=datetime.now(),
                source=f"printer.{self.config.id}"
            ))
        except Exception as e:
            self._logger.error(f"Failed to publish event: {e}")
    
    def _get_file_type(self, filename: str) -> str:
        """Extract file type from filename"""
        return Path(filename).suffix.lower()
```

### Error Handling Patterns

```python
class PrinterIntegrationError(Exception):
    """Base exception for printer integration errors"""
    pass

class ConnectionError(PrinterIntegrationError):
    """Connection-related errors"""
    pass

class AuthenticationError(PrinterIntegrationError):
    """Authentication failures"""
    pass

class DownloadError(PrinterIntegrationError):
    """File download failures"""
    pass

class HTTPError(PrinterIntegrationError):
    """HTTP-specific errors"""
    pass

class MQTTError(PrinterIntegrationError):
    """MQTT-specific errors"""
    pass

# Circuit breaker pattern for failing connections
class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "half-open"
                return True
            return False
        elif self.state == "half-open":
            return True
    
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.state = "closed"
        self.last_failure_time = None
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
```

### Integration Factory Pattern

```python
class PrinterIntegrationFactory:
    """
    Factory for creating printer integration instances
    """
    
    _integration_classes = {
        "bambu_lab": BambuLabIntegration,
        "prusa": PrusaIntegration
    }
    
    @classmethod
    def create_integration(
        cls, 
        printer_config: PrinterConfig, 
        event_publisher: EventPublisher
    ) -> BasePrinterIntegration:
        """
        Create appropriate integration instance based on printer type
        """
        printer_type = printer_config.type.lower()
        
        if printer_type not in cls._integration_classes:
            raise ValueError(f"Unsupported printer type: {printer_type}")
        
        integration_class = cls._integration_classes[printer_type]
        return integration_class(printer_config, event_publisher)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported printer types"""
        return list(cls._integration_classes.keys())
    
    @classmethod
    def register_integration(cls, printer_type: str, integration_class):
        """Register new integration type"""
        cls._integration_classes[printer_type] = integration_class
```

---

## Integration Best Practices

### 1. **Connection Management**
- Implement automatic reconnection with exponential backoff
- Use circuit breaker pattern to prevent cascading failures
- Monitor connection health with heartbeat/ping mechanisms
- Log all connection events for debugging

### 2. **Error Handling**
- Categorize errors (network, authentication, protocol, etc.)
- Implement retry logic with appropriate delays
- Graceful degradation when connections fail
- Clear error messages for troubleshooting

### 3. **Performance Optimization**
- Connection pooling for HTTP integrations
- Efficient MQTT topic subscriptions
- Minimize polling frequency while maintaining responsiveness
- Cache frequently accessed data

### 4. **Security Considerations**
- Secure credential storage and transmission
- Input validation for all API responses
- Network timeout enforcement
- Certificate validation for HTTPS connections

### 5. **Monitoring and Logging**
- Comprehensive logging for all integration events
- Performance metrics collection
- Health monitoring dashboards
- Alert systems for integration failures

This integration pattern design provides a robust foundation for communicating with different printer types while maintaining consistency and reliability across the Printernizer system.