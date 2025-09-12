"""
Snapshot models for Printernizer camera functionality.
Pydantic models for camera snapshot data validation and serialization.
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CameraTrigger(str, Enum):
    """Camera snapshot trigger types."""
    MANUAL = "manual"
    AUTO = "auto"
    JOB_START = "job_start"
    JOB_COMPLETE = "job_complete"  
    JOB_FAILED = "job_failed"


class Snapshot(BaseModel):
    """Camera snapshot model."""
    id: Optional[int] = Field(None, description="Unique snapshot identifier")
    job_id: Optional[int] = Field(None, description="Associated job ID")
    printer_id: str = Field(..., description="Printer ID that captured snapshot")
    
    # File details
    filename: str = Field(..., description="Generated filename for snapshot")
    original_filename: Optional[str] = Field(None, description="Original filename if provided")
    file_size: int = Field(..., description="Image file size in bytes")
    content_type: str = Field("image/jpeg", description="MIME type of image")
    storage_path: str = Field(..., description="Local filesystem path")
    
    # Capture details
    captured_at: datetime = Field(default_factory=datetime.now, description="When snapshot was captured")
    capture_trigger: CameraTrigger = Field(CameraTrigger.MANUAL, description="What triggered the snapshot")
    
    # Image metadata
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")
    
    # Status
    is_valid: bool = Field(True, description="Whether file exists and is valid")
    validation_error: Optional[str] = Field(None, description="Validation error message")
    last_validated_at: Optional[datetime] = Field(None, description="Last validation check")
    
    # Additional data
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional structured data")
    notes: Optional[str] = Field(None, description="User notes")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SnapshotCreate(BaseModel):
    """Snapshot creation model."""
    printer_id: str = Field(..., description="Printer ID")
    job_id: Optional[int] = Field(None, description="Associated job ID")
    capture_trigger: CameraTrigger = Field(CameraTrigger.MANUAL, description="Trigger type")
    notes: Optional[str] = Field(None, description="User notes")


class SnapshotResponse(BaseModel):
    """API response model for snapshots."""
    id: int
    printer_id: str
    job_id: Optional[int]
    filename: str
    file_size: int
    content_type: str
    captured_at: str
    capture_trigger: CameraTrigger
    width: Optional[int]
    height: Optional[int]
    is_valid: bool
    notes: Optional[str]
    
    # Context data from view
    job_name: Optional[str] = None
    job_status: Optional[str] = None
    printer_name: Optional[str] = None
    printer_type: Optional[str] = None


class CameraStatus(BaseModel):
    """Camera status response model."""
    has_camera: bool
    is_available: bool
    stream_url: Optional[str] = None
    error_message: Optional[str] = None
    last_snapshot_at: Optional[datetime] = None