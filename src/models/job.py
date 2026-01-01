"""
Job models for Printernizer.
Pydantic models for print job data validation and serialization.
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    """Job status states."""
    PENDING = "pending"
    RUNNING = "running"
    PRINTING = "printing"  # Added for Bambu Lab printers
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class Job(BaseModel):
    """Print job model."""
    id: str = Field(..., description="Unique job identifier")
    printer_id: str = Field(..., description="Printer ID where job is running")
    printer_type: str = Field(..., description="Type of printer")
    job_name: str = Field(..., description="Human-readable job name")
    filename: Optional[str] = Field(None, description="Original filename")
    status: JobStatus = Field(JobStatus.PENDING, description="Current job status")
    start_time: Optional[datetime] = Field(None, description="Job start time")
    end_time: Optional[datetime] = Field(None, description="Job completion time")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")
    actual_duration: Optional[int] = Field(None, description="Actual duration in seconds")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    material_used: Optional[float] = Field(None, description="Material used in grams")
    material_cost: Optional[float] = Field(None, description="Material cost in EUR")
    power_cost: Optional[float] = Field(None, description="Power cost in EUR")
    is_business: bool = Field(False, description="Whether this is a business job")
    customer_info: Optional[Dict[str, Any]] = Field(None, description="Customer information")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('progress', mode='before')
    def convert_progress_to_int(cls, v):
        """Convert float progress values to integers."""
        if v is not None and isinstance(v, float):
            return int(v)
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class JobCreate(BaseModel):
    """Job creation model."""
    printer_id: str
    job_name: str
    filename: Optional[str] = None
    estimated_duration: Optional[int] = None
    is_business: bool = False
    customer_info: Optional[Dict[str, Any]] = None


class JobUpdate(BaseModel):
    """Job update model (legacy - use JobUpdateRequest for new code)."""
    status: Optional[JobStatus] = None
    progress: Optional[int] = None
    material_used: Optional[float] = None
    end_time: Optional[datetime] = None
    actual_duration: Optional[int] = None


class JobUpdateRequest(BaseModel):
    """Schema for job update requests (PUT /api/v1/jobs/{id})."""
    job_name: Optional[str] = None
    status: Optional[JobStatus] = None
    is_business: Optional[bool] = None
    customer_name: Optional[str] = None
    notes: Optional[str] = None
    file_name: Optional[str] = None
    printer_id: Optional[str] = None

    @field_validator('job_name')
    @classmethod
    def validate_job_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("job_name cannot be empty")
            if len(v) > 200:
                raise ValueError("job_name max length is 200 characters")
        return v

    @field_validator('customer_name')
    @classmethod
    def validate_customer_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 200:
                raise ValueError("customer_name max length is 200 characters")
        return v

    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError("notes max length is 1000 characters")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class JobStatusUpdateRequest(BaseModel):
    """Request schema for job status updates (PUT /api/v1/jobs/{id}/status)."""
    status: JobStatus
    completion_notes: Optional[str] = None
    force: bool = False

    @field_validator('completion_notes')
    @classmethod
    def validate_notes(cls, v):
        if v and len(v) > 500:
            raise ValueError("completion_notes max length is 500 characters")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class JobStatusUpdateResponse(BaseModel):
    """Response schema for status updates."""
    id: str
    status: JobStatus
    previous_status: JobStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        use_enum_values = True