"""
Usage statistics models for Printernizer.
Privacy-first data models for anonymous usage tracking.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    """Types of usage events that can be tracked."""
    APP_START = "app_start"
    APP_SHUTDOWN = "app_shutdown"
    JOB_CREATED = "job_created"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    FILE_DOWNLOADED = "file_downloaded"
    FILE_UPLOADED = "file_uploaded"
    PRINTER_CONNECTED = "printer_connected"
    PRINTER_DISCONNECTED = "printer_disconnected"
    ERROR_OCCURRED = "error_occurred"
    FEATURE_ENABLED = "feature_enabled"
    FEATURE_DISABLED = "feature_disabled"


class UsageEvent(BaseModel):
    """
    Individual usage event model.

    Represents a single trackable action or occurrence in the application.
    All events are stored locally and only submitted if user opts in.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the event occurred (UTC)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Event-specific data (JSON)")
    submitted: bool = Field(default=False, description="Whether this event has been submitted to aggregation service")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the event was recorded locally")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "job_completed",
                "timestamp": "2024-11-20T12:00:00Z",
                "metadata": {
                    "duration_seconds": 3600,
                    "printer_type": "bambu_lab"
                },
                "submitted": False,
                "created_at": "2024-11-20T12:00:00Z"
            }
        }


class UsageSetting(BaseModel):
    """
    Usage statistics setting model.

    Stores configuration and metadata for the usage statistics feature.
    """
    key: str = Field(..., description="Setting key", min_length=1, max_length=100)
    value: str = Field(..., description="Setting value")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InstallationInfo(BaseModel):
    """
    Anonymous installation information.

    Identifies a unique installation without exposing personal data.
    Installation ID is randomly generated and not tied to hardware.
    """
    installation_id: str = Field(..., description="Anonymous installation UUID", min_length=36, max_length=36)
    first_seen: datetime = Field(..., description="First time this installation was recorded")
    app_version: str = Field(..., description="Application version (e.g., '2.7.0')")
    python_version: str = Field(..., description="Python version (e.g., '3.11.0')")
    platform: str = Field(..., description="Operating system platform (linux/windows/darwin)")
    deployment_mode: str = Field(..., description="Deployment mode (homeassistant/docker/standalone/pi)")
    country_code: str = Field(..., description="Country code from timezone (e.g., 'DE')", min_length=2, max_length=2)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TimePeriod(BaseModel):
    """
    Time period for aggregated statistics.

    Represents the time range covered by aggregated data.
    """
    start: datetime = Field(..., description="Period start time (UTC)")
    end: datetime = Field(..., description="Period end time (UTC)")
    duration_days: int = Field(..., description="Duration in days", ge=0)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PrinterFleetStats(BaseModel):
    """
    Anonymous printer fleet composition.

    Aggregate printer information without exposing device identifiers.
    No serial numbers, IP addresses, or printer names included.
    """
    printer_count: int = Field(..., description="Total number of printers", ge=0)
    printer_types: List[str] = Field(default_factory=list, description="List of printer types (e.g., ['bambu_lab', 'prusa'])")
    printer_type_counts: Dict[str, int] = Field(default_factory=dict, description="Count by printer type")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "printer_count": 3,
                "printer_types": ["bambu_lab", "prusa"],
                "printer_type_counts": {
                    "bambu_lab": 2,
                    "prusa": 1
                }
            }
        }


class UsageStats(BaseModel):
    """
    Usage activity statistics.

    Aggregated usage metrics for a time period.
    All counts are anonymous and don't include file names or job details.
    """
    job_count: int = Field(default=0, description="Number of jobs completed", ge=0)
    file_count: int = Field(default=0, description="Number of files downloaded", ge=0)
    upload_count: int = Field(default=0, description="Number of files uploaded", ge=0)
    uptime_hours: int = Field(default=0, description="Total uptime in hours", ge=0)
    feature_usage: Dict[str, bool] = Field(default_factory=dict, description="Feature enable/disable status")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "job_count": 23,
                "file_count": 18,
                "upload_count": 5,
                "uptime_hours": 168,
                "feature_usage": {
                    "library_enabled": True,
                    "timelapse_enabled": False,
                    "auto_job_creation_enabled": True
                }
            }
        }


class AggregatedStats(BaseModel):
    """
    Complete aggregated statistics payload.

    This is the full payload that gets submitted to the aggregation service
    if the user has opted in. Contains only anonymous, aggregated data.
    """
    schema_version: str = Field(default="1.0", description="Schema version for compatibility")
    submission_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When this was submitted")
    installation: InstallationInfo = Field(..., description="Anonymous installation information")
    period: TimePeriod = Field(..., description="Time period covered by these stats")
    printer_fleet: PrinterFleetStats = Field(..., description="Printer fleet composition")
    usage_stats: UsageStats = Field(..., description="Usage activity statistics")
    error_summary: Dict[str, int] = Field(default_factory=dict, description="Error counts by type (anonymous)")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "schema_version": "1.0",
                "submission_timestamp": "2024-11-20T12:00:00Z",
                "installation": {
                    "installation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "first_seen": "2024-11-01T00:00:00Z",
                    "app_version": "2.7.0",
                    "python_version": "3.11.0",
                    "platform": "linux",
                    "deployment_mode": "homeassistant",
                    "country_code": "DE"
                },
                "period": {
                    "start": "2024-11-14T00:00:00Z",
                    "end": "2024-11-21T00:00:00Z",
                    "duration_days": 7
                },
                "printer_fleet": {
                    "printer_count": 3,
                    "printer_types": ["bambu_lab", "prusa"],
                    "printer_type_counts": {
                        "bambu_lab": 2,
                        "prusa": 1
                    }
                },
                "usage_stats": {
                    "job_count": 23,
                    "file_count": 18,
                    "upload_count": 5,
                    "uptime_hours": 168,
                    "feature_usage": {
                        "library_enabled": True,
                        "timelapse_enabled": False
                    }
                },
                "error_summary": {
                    "connection_timeout": 2,
                    "file_download_failed": 1
                }
            }
        }


class LocalStatsResponse(BaseModel):
    """
    Response model for local statistics viewer.

    Human-readable summary of locally collected statistics.
    """
    installation_id: str = Field(..., description="Anonymous installation ID")
    first_seen: Optional[datetime] = Field(None, description="First recorded event")
    opt_in_status: str = Field(..., description="Current opt-in status (enabled/disabled)")
    total_events: int = Field(default=0, description="Total events recorded locally", ge=0)
    this_week: Dict[str, int] = Field(default_factory=dict, description="This week's summary")
    last_submission: Optional[datetime] = Field(None, description="Last successful submission")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "installation_id": "550e8400-e29b-41d4-a716-446655440000",
                "first_seen": "2024-11-01T00:00:00Z",
                "opt_in_status": "disabled",
                "total_events": 1234,
                "this_week": {
                    "job_count": 23,
                    "file_count": 18,
                    "error_count": 2
                },
                "last_submission": None
            }
        }


class OptInResponse(BaseModel):
    """Response model for opt-in/opt-out actions."""
    success: bool = Field(..., description="Whether the action succeeded")
    installation_id: Optional[str] = Field(None, description="Installation ID (only on opt-in)")
    message: str = Field(..., description="Human-readable message")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "installation_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Usage statistics enabled. Thank you for helping improve Printernizer!"
            }
        }
