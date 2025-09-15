"""
Base printer classes and interfaces for Printernizer.
Provides abstract base classes for all printer integrations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from datetime import datetime
from enum import Enum
import asyncio
import structlog

from src.models.printer import PrinterStatus, PrinterStatusUpdate
from src.utils.exceptions import PrinterConnectionError

logger = structlog.get_logger()


class JobStatus(str, Enum):
    """Job status enumeration."""
    IDLE = "idle"
    PREPARING = "preparing"
    PRINTING = "printing"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PrinterFile:
    """Represents a file on a printer."""
    def __init__(self, filename: str, size: Optional[int] = None, 
                 modified: Optional[datetime] = None, path: Optional[str] = None):
        self.filename = filename
        self.size = size
        self.modified = modified or datetime.now()
        self.path = path or filename
        
    def __repr__(self):
        return f"PrinterFile(filename='{self.filename}', size={self.size})"


class JobInfo:
    """Represents a print job."""
    def __init__(self, job_id: str, name: str, status: JobStatus,
                 progress: Optional[int] = None, estimated_time: Optional[int] = None,
                 elapsed_time: Optional[int] = None):
        self.job_id = job_id
        self.name = name
        self.status = status
        self.progress = progress or 0
        self.estimated_time = estimated_time
        self.elapsed_time = elapsed_time
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
    def __repr__(self):
        return f"JobInfo(id='{self.job_id}', name='{self.name}', status='{self.status}')"


class PrinterInterface(ABC):
    """Abstract interface for printer communication."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the printer."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the printer."""
        pass
        
    @abstractmethod
    async def get_status(self) -> PrinterStatusUpdate:
        """Get current printer status."""
        pass
        
    @abstractmethod
    async def get_job_info(self) -> Optional[JobInfo]:
        """Get current job information."""
        pass
        
    @abstractmethod
    async def list_files(self) -> List[PrinterFile]:
        """List files available on the printer."""
        pass
        
    @abstractmethod
    async def download_file(self, filename: str, local_path: str) -> bool:
        """Download a file from the printer."""
        pass
        
    @abstractmethod
    async def pause_print(self) -> bool:
        """Pause the current print job."""
        pass
        
    @abstractmethod
    async def resume_print(self) -> bool:
        """Resume the paused print job."""
        pass
        
    @abstractmethod
    async def stop_print(self) -> bool:
        """Stop/cancel the current print job."""
        pass

    @abstractmethod
    async def has_camera(self) -> bool:
        """Check if printer has camera support."""
        pass
        
    @abstractmethod
    async def get_camera_stream_url(self) -> Optional[str]:
        """Get camera stream URL if available."""
        pass
        
    @abstractmethod
    async def take_snapshot(self) -> Optional[bytes]:
        """Take a camera snapshot and return image data."""
        pass


class BasePrinter(PrinterInterface):
    """Base class for all printer implementations."""
    
    def __init__(self, printer_id: str, name: str, ip_address: str, **kwargs):
        """Initialize base printer."""
        self.printer_id = printer_id
        self.name = name
        self.ip_address = ip_address
        self.config = kwargs
        self.is_connected = False
        self.last_status: Optional[PrinterStatusUpdate] = None
        self.status_callbacks: List[Callable[[PrinterStatusUpdate], None]] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stop_monitoring = asyncio.Event()
        
    async def start_monitoring(self, interval: int = 30) -> None:
        """Start periodic status monitoring."""
        if self._monitoring_task is not None:
            logger.warning("Monitoring already active", printer_id=self.printer_id)
            return
            
        logger.info("Starting printer monitoring", printer_id=self.printer_id, interval=interval)
        self._stop_monitoring.clear()
        self._monitoring_task = asyncio.create_task(self._monitor_loop(interval))
        
    async def stop_monitoring(self) -> None:
        """Stop status monitoring."""
        if self._monitoring_task is None:
            return
            
        logger.info("Stopping printer monitoring", printer_id=self.printer_id)
        self._stop_monitoring.set()
        
        if not self._monitoring_task.done():
            self._monitoring_task.cancel()
            
        try:
            await self._monitoring_task
        except asyncio.CancelledError:
            pass
            
        self._monitoring_task = None
        
    async def _monitor_loop(self, interval: int) -> None:
        """Internal monitoring loop."""
        while not self._stop_monitoring.is_set():
            try:
                status = await self.get_status()
                self.last_status = status
                
                # Notify callbacks
                for callback in self.status_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(status)
                        else:
                            callback(status)
                    except Exception as e:
                        logger.error("Error in status callback", 
                                   printer_id=self.printer_id, error=str(e))
                        
            except Exception as e:
                logger.error("Error in monitoring loop", 
                           printer_id=self.printer_id, error=str(e))
                
            # Wait for interval or stop signal
            try:
                await asyncio.wait_for(self._stop_monitoring.wait(), timeout=interval)
                break  # Stop signal received
            except asyncio.TimeoutError:
                continue  # Continue monitoring
                
    def add_status_callback(self, callback: Callable[[PrinterStatusUpdate], None]) -> None:
        """Add a status update callback."""
        self.status_callbacks.append(callback)
        
    def remove_status_callback(self, callback: Callable[[PrinterStatusUpdate], None]) -> None:
        """Remove a status update callback."""
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
            
    async def health_check(self) -> bool:
        """Check if printer is healthy and responsive."""
        try:
            status = await self.get_status()
            return status.status != PrinterStatus.ERROR
        except Exception:
            return False
            
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for debugging."""
        return {
            "printer_id": self.printer_id,
            "name": self.name,
            "ip_address": self.ip_address,
            "is_connected": self.is_connected,
            "last_status": self.last_status.dict() if self.last_status else None,
            "monitoring_active": self._monitoring_task is not None
        }
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()