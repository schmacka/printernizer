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


class Printer(BaseModel):
    """Printer model."""
    id: str = Field(..., description="Unique printer identifier")
    name: str = Field(..., description="Human-readable printer name")
    type: PrinterType = Field(..., description="Printer type")
    ip_address: Optional[str] = Field(None, description="Printer IP address")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    access_code: Optional[str] = Field(None, description="Access code for Bambu Lab")
    serial_number: Optional[str] = Field(None, description="Printer serial number", min_length=8, max_length=20)
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
    timestamp: datetime = Field(default_factory=datetime.now)
    raw_data: Optional[Dict[str, Any]] = None


class FilamentSlot(BaseModel):
    """
    Represents a single filament slot/tray.

    Used for both multi-material AMS systems (Bambu Lab) and single-material
    printers (Prusa). AMS systems typically have 4 slots (0-3), while
    single-material printers have one slot (0).
    """

    slot_id: int = Field(
        ...,
        description="Slot identifier (0-3 for AMS, 0 for single-material)",
        ge=0,
        le=15  # Support future expansion to larger AMS units
    )

    tray_id: Optional[str] = Field(
        None,
        description="Tray ID from AMS (Bambu Lab only, e.g., '1', '2')"
    )

    tray_type: Optional[str] = Field(
        None,
        description="Filament material type (PLA, PETG, TPU, ABS, ASA, etc.)"
    )

    tray_color: Optional[str] = Field(
        None,
        description="Color as hex code (#RRGGBB) or color name"
    )

    filament_id: Optional[str] = Field(
        None,
        description="Bambu Lab filament ID (e.g., 'GFL00' for black)"
    )

    color_name: Optional[str] = Field(
        None,
        description="Human-readable color name (e.g., 'Black', 'Red')"
    )

    remaining_percentage: Optional[float] = Field(
        None,
        description="Percentage of filament remaining (0.0-100.0)",
        ge=0.0,
        le=100.0
    )

    is_loaded: Optional[bool] = Field(
        None,
        description="Whether filament is currently loaded in this slot"
    )

    is_runout: Optional[bool] = Field(
        None,
        description="Whether filament runout sensor has been triggered"
    )

    material_name: Optional[str] = Field(
        None,
        description="Material name/brand from printer (e.g., 'Prusament PLA')"
    )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FilamentStatus(BaseModel):
    """
    Complete filament status for a printer.

    Supports both single-material printers (Prusa) and multi-material
    AMS systems (Bambu Lab). For single-material printers, `slots` will
    contain one FilamentSlot. For AMS systems, `slots` will contain
    multiple FilamentSlot objects (typically 4).
    """

    is_multi_material: bool = Field(
        False,
        description="Whether printer has multi-material system (e.g., Bambu AMS)"
    )

    active_slot: Optional[int] = Field(
        None,
        description="Currently active slot ID during printing (null if idle)"
    )

    slots: List[FilamentSlot] = Field(
        default_factory=list,
        description="List of filament slots/trays"
    )

    ams_id: Optional[str] = Field(
        None,
        description="AMS unit identifier (Bambu Lab only, e.g., '0', '1')"
    )

    has_runout_sensor: bool = Field(
        False,
        description="Whether printer has filament runout detection capability"
    )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


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
    # Filament status information (optional)
    filament_status: Optional[FilamentStatus] = Field(
        None,
        description="Filament/AMS status information from printer"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    raw_data: Optional[Dict[str, Any]] = None