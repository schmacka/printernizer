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
    """Job update model."""
    status: Optional[JobStatus] = None
    progress: Optional[int] = None
    material_used: Optional[float] = None
    end_time: Optional[datetime] = None
    actual_duration: Optional[int] = None