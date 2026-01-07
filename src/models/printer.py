"""
Printer models for Printernizer.
Pydantic models for printer data validation and serialization.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class PrinterType(str, Enum):
    """Supported printer types."""
    BAMBU_LAB = "bambu_lab"
    PRUSA_CORE = "prusa_core"
    UNKNOWN = "unknown"


class PrinterStatus(str, Enum):
    """Printer status states."""
    ONLINE = "online"
    OFFLINE = "offline"
    PRINTING = "printing"
    PAUSED = "paused"
    ERROR = "error"
    UNKNOWN = "unknown"


class Filament(BaseModel):
    """Filament information model."""
    slot: int = Field(..., description="Filament slot/tray number (0-indexed)")
    color: Optional[str] = Field(None, description="Filament color (hex code or name)")
    type: Optional[str] = Field(None, description="Filament material type (PLA, PETG, ABS, etc.)")
    is_active: bool = Field(False, description="Whether this filament is currently selected/active")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Printer(BaseModel):
    """Printer model."""
    id: str = Field(..., description="Unique printer identifier")
    name: str = Field(..., description="Human-readable printer name")
    type: PrinterType = Field(..., description="Printer type")
    ip_address: Optional[str] = Field(None, description="Printer IP address")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    access_code: Optional[str] = Field(None, description="Access code for Bambu Lab")
    serial_number: Optional[str] = Field(None, description="Printer serial number", min_length=8, max_length=20)
    webcam_url: Optional[str] = Field(None, description="External webcam URL (HTTP snapshot or RTSP stream)")
    location: Optional[str] = Field(None, description="Physical location of printer")
    description: Optional[str] = Field(None, description="Printer description")
    is_active: bool = Field(True, description="Whether printer monitoring is active")
    status: PrinterStatus = Field(PrinterStatus.UNKNOWN, description="Current printer status")
    last_seen: Optional[datetime] = Field(None, description="Last successful communication")
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PrinterConfig(BaseModel):
    """Printer configuration model for API updates."""
    name: Optional[str] = None
    ip_address: Optional[str] = None
    api_key: Optional[str] = None
    access_code: Optional[str] = None
    serial_number: Optional[str] = None
    webcam_url: Optional[str] = None
    is_active: Optional[bool] = None


class PrinterStatusUpdate(BaseModel):
    """Printer status update model."""
    printer_id: str
    status: PrinterStatus
    message: Optional[str] = None
    temperature_bed: Optional[float] = None
    temperature_nozzle: Optional[float] = None
    progress: Optional[int] = None
    current_job: Optional[str] = None
    current_job_file_id: Optional[str] = None
    current_job_has_thumbnail: Optional[bool] = None
    # Derived URL for the current job thumbnail (served via files endpoint)
    current_job_thumbnail_url: Optional[str] = None
    remaining_time_minutes: Optional[int] = None
    estimated_end_time: Optional[datetime] = None
    # Direct printer-reported timing (only if available from printer)
    elapsed_time_minutes: Optional[int] = None  # Time since print started
    print_start_time: Optional[datetime] = None  # Actual start time from printer
    # Filament information (color, type, slot)
    filaments: Optional[List[Filament]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    raw_data: Optional[Dict[str, Any]] = None