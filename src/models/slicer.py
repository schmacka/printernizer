"""
Models for slicer integration.

Defines data models for slicer configurations, profiles, and slicing jobs.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SlicerType(str, Enum):
    """Supported slicer types."""
    PRUSASLICER = "prusaslicer"
    BAMBUSTUDIO = "bambustudio"
    ORCASLICER = "orcaslicer"
    SUPERSLICER = "superslicer"


class ProfileType(str, Enum):
    """Slicer profile types."""
    PRINT = "print"
    FILAMENT = "filament"
    PRINTER = "printer"
    BUNDLE = "bundle"


class SlicingJobStatus(str, Enum):
    """Slicing job status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SlicerConfig(BaseModel):
    """Slicer configuration model."""
    id: str
    name: str
    slicer_type: SlicerType
    executable_path: str
    version: Optional[str] = None
    config_dir: Optional[str] = None
    is_available: bool = True
    last_verified: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True


class SlicerProfile(BaseModel):
    """Slicer profile model."""
    id: str
    slicer_id: str
    profile_name: str
    profile_type: ProfileType
    profile_path: Optional[str] = None
    settings_json: Optional[str] = None
    compatible_printers: Optional[str] = None
    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True


class SlicingJob(BaseModel):
    """Slicing job model."""
    id: str
    file_checksum: str
    slicer_id: str
    profile_id: str
    target_printer_id: Optional[str] = None
    status: SlicingJobStatus = SlicingJobStatus.QUEUED
    priority: int = Field(default=5, ge=1, le=10)
    progress: int = Field(default=0, ge=0, le=100)
    output_file_path: Optional[str] = None
    output_gcode_checksum: Optional[str] = None
    estimated_print_time: Optional[int] = None
    filament_used: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    auto_upload: bool = False
    auto_start: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True


class SlicingJobRequest(BaseModel):
    """Request model for creating a slicing job."""
    file_checksum: str
    slicer_id: str
    profile_id: str
    target_printer_id: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    auto_upload: bool = False
    auto_start: bool = False


class SlicingJobResponse(BaseModel):
    """Response model for slicing job."""
    id: str
    file_checksum: str
    filename: Optional[str] = None
    slicer_id: str
    slicer_name: Optional[str] = None
    profile_id: str
    profile_name: Optional[str] = None
    target_printer_id: Optional[str] = None
    status: SlicingJobStatus
    priority: int
    progress: int
    output_file_path: Optional[str] = None
    estimated_print_time: Optional[int] = None
    filament_used: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int
    auto_upload: bool
    auto_start: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True


class SliceAndPrintRequest(BaseModel):
    """Request model for slice-and-print operation."""
    file_checksum: str
    slicer_id: str
    profile_id: str
    printer_id: str
    auto_start: bool = True
    priority: int = Field(default=5, ge=1, le=10)
