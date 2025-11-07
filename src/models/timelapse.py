"""
Timelapse models for Printernizer.
Pydantic models for timelapse video data validation and serialization.
"""
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, computed_field
from pathlib import Path


class TimelapseStatus(str, Enum):
    """Timelapse status states."""
    DISCOVERED = "discovered"  # Folder found, monitoring for new images
    PENDING = "pending"  # Ready for processing (timeout reached or manual)
    PROCESSING = "processing"  # Currently creating video
    COMPLETED = "completed"  # Video successfully created
    FAILED = "failed"  # Processing error occurred


class Timelapse(BaseModel):
    """Timelapse model."""
    id: str = Field(..., description="Unique timelapse identifier")
    source_folder: str = Field(..., description="Absolute path to image folder")
    output_video_path: Optional[str] = Field(None, description="Path to generated video")
    status: TimelapseStatus = Field(TimelapseStatus.DISCOVERED, description="Current timelapse status")
    job_id: Optional[str] = Field(None, description="Linked job ID (if matched)")

    # Metadata
    folder_name: str = Field(..., description="Folder name (for display)")
    image_count: Optional[int] = Field(None, description="Number of source images")
    video_duration: Optional[float] = Field(None, description="Video duration in seconds")
    file_size_bytes: Optional[int] = Field(None, description="Video file size in bytes")

    # Processing tracking
    processing_started_at: Optional[datetime] = Field(None, description="Processing start time")
    processing_completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    retry_count: int = Field(0, description="Number of retry attempts")

    # Auto-detection
    last_image_detected_at: Optional[datetime] = Field(None, description="Last time new image was found")
    auto_process_eligible_at: Optional[datetime] = Field(None, description="When auto-processing can trigger")

    # Management
    pinned: bool = Field(False, description="User pinned (exempt from cleanup)")
    created_at: datetime = Field(default_factory=datetime.now, description="Discovery timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    @computed_field
    @property
    def age_days(self) -> int:
        """Calculate age in days since creation."""
        return (datetime.now() - self.created_at).days

    @computed_field
    @property
    def video_exists(self) -> bool:
        """Check if video file exists on disk."""
        if not self.output_video_path:
            return False
        return Path(self.output_video_path).exists()

    @computed_field
    @property
    def processing_duration_seconds(self) -> Optional[int]:
        """Calculate processing duration if completed."""
        if self.processing_started_at and self.processing_completed_at:
            return int((self.processing_completed_at - self.processing_started_at).total_seconds())
        return None

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TimelapseCreate(BaseModel):
    """Timelapse creation model."""
    source_folder: str = Field(..., description="Absolute path to image folder")
    folder_name: str = Field(..., description="Folder name (for display)")
    image_count: Optional[int] = None


class TimelapseUpdate(BaseModel):
    """Timelapse update model."""
    status: Optional[TimelapseStatus] = None
    image_count: Optional[int] = None
    last_image_detected_at: Optional[datetime] = None
    auto_process_eligible_at: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    output_video_path: Optional[str] = None
    video_duration: Optional[float] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = None
    job_id: Optional[str] = None
    pinned: Optional[bool] = None


class TimelapseLinkJob(BaseModel):
    """Model for manually linking timelapse to job."""
    job_id: str = Field(..., description="Job ID to link")


class TimelapseStats(BaseModel):
    """Timelapse statistics model."""
    total_videos: int = Field(0, description="Total number of timelapses")
    total_size_bytes: int = Field(0, description="Total storage used by videos")
    discovered_count: int = Field(0, description="Number of discovered timelapses")
    pending_count: int = Field(0, description="Number of pending timelapses")
    processing_count: int = Field(0, description="Number of processing timelapses")
    completed_count: int = Field(0, description="Number of completed timelapses")
    failed_count: int = Field(0, description="Number of failed timelapses")
    cleanup_candidates_count: int = Field(0, description="Number of videos recommended for cleanup")

    @computed_field
    @property
    def total_size_mb(self) -> float:
        """Total size in megabytes."""
        return round(self.total_size_bytes / (1024 * 1024), 2)

    @computed_field
    @property
    def total_size_gb(self) -> float:
        """Total size in gigabytes."""
        return round(self.total_size_bytes / (1024 * 1024 * 1024), 2)


class TimelapseBulkDelete(BaseModel):
    """Model for bulk deletion request."""
    timelapse_ids: list[str] = Field(..., description="List of timelapse IDs to delete")


class TimelapseBulkDeleteResult(BaseModel):
    """Result of bulk deletion operation."""
    deleted: int = Field(0, description="Number of successfully deleted timelapses")
    failed: int = Field(0, description="Number of failed deletions")
    errors: list[str] = Field(default_factory=list, description="Error messages for failed deletions")
