"""
Notification models for Printernizer.
Pydantic models for multi-channel notification system (Discord, Slack, ntfy.sh).
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class ChannelType(str, Enum):
    """Supported notification channel types."""
    DISCORD = "discord"
    SLACK = "slack"
    NTFY = "ntfy"


class NotificationEventType(str, Enum):
    """Notification event types that can trigger notifications."""
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_PAUSED = "job_paused"
    PRINTER_ONLINE = "printer_online"
    PRINTER_OFFLINE = "printer_offline"
    PRINTER_ERROR = "printer_error"
    MATERIAL_LOW_STOCK = "material_low_stock"
    FILE_DOWNLOADED = "file_downloaded"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"


class NotificationChannel(BaseModel):
    """Notification channel configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100, description="Display name for the channel")
    channel_type: ChannelType = Field(..., description="Type of notification channel")
    webhook_url: str = Field(..., description="Webhook URL (Discord/Slack) or server URL (ntfy)")
    topic: Optional[str] = Field(None, description="ntfy topic (required for ntfy channels)")
    is_enabled: bool = Field(True, description="Whether the channel is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationSubscription(BaseModel):
    """Event subscription for a notification channel."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    channel_id: str = Field(..., description="Reference to the notification channel")
    event_type: NotificationEventType = Field(..., description="Event type to subscribe to")
    is_enabled: bool = Field(True, description="Whether this subscription is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationHistory(BaseModel):
    """Notification delivery history record."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    channel_id: str = Field(..., description="Reference to the notification channel")
    event_type: str = Field(..., description="Event type that triggered the notification")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Event payload data")
    status: NotificationStatus = Field(..., description="Delivery status")
    error_message: Optional[str] = Field(None, description="Error message if delivery failed")
    sent_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Request/Response models for API

class ChannelCreate(BaseModel):
    """Request model for creating a notification channel."""
    name: str = Field(..., min_length=1, max_length=100, description="Display name for the channel")
    channel_type: ChannelType = Field(..., description="Type of notification channel")
    webhook_url: str = Field(..., description="Webhook URL or server URL")
    topic: Optional[str] = Field(None, description="ntfy topic (required for ntfy channels)")
    is_enabled: bool = Field(True, description="Whether the channel is active")
    subscribed_events: List[NotificationEventType] = Field(
        default_factory=list,
        description="Events to subscribe to initially"
    )


class ChannelUpdate(BaseModel):
    """Request model for updating a notification channel."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    webhook_url: Optional[str] = None
    topic: Optional[str] = None
    is_enabled: Optional[bool] = None


class SubscriptionUpdate(BaseModel):
    """Request model for updating event subscriptions."""
    subscribed_events: List[NotificationEventType] = Field(
        ...,
        description="Complete list of events to subscribe to"
    )


class TestNotificationRequest(BaseModel):
    """Request model for sending a test notification."""
    channel_id: str = Field(..., description="Channel to send test notification to")


class ChannelResponse(BaseModel):
    """Response model for a notification channel with subscriptions."""
    id: str
    name: str
    channel_type: ChannelType
    webhook_url: str
    topic: Optional[str] = None
    is_enabled: bool
    subscribed_events: List[NotificationEventType] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChannelListResponse(BaseModel):
    """Response model for listing notification channels."""
    channels: List[ChannelResponse]
    total: int


class NotificationHistoryResponse(BaseModel):
    """Response model for notification history."""
    history: List[NotificationHistory]
    total: int


class TestNotificationResponse(BaseModel):
    """Response model for test notification result."""
    success: bool
    message: str
    channel_id: str
    channel_name: str


# Event type metadata for UI
EVENT_TYPE_METADATA = {
    NotificationEventType.JOB_STARTED: {
        "label": "Job Started",
        "icon": "play",
        "description": "When a print job begins"
    },
    NotificationEventType.JOB_COMPLETED: {
        "label": "Job Completed",
        "icon": "check",
        "description": "When a print job finishes successfully"
    },
    NotificationEventType.JOB_FAILED: {
        "label": "Job Failed",
        "icon": "x",
        "description": "When a print job fails"
    },
    NotificationEventType.JOB_PAUSED: {
        "label": "Job Paused",
        "icon": "pause",
        "description": "When a print job is paused"
    },
    NotificationEventType.PRINTER_ONLINE: {
        "label": "Printer Online",
        "icon": "wifi",
        "description": "When a printer comes online"
    },
    NotificationEventType.PRINTER_OFFLINE: {
        "label": "Printer Offline",
        "icon": "wifi-off",
        "description": "When a printer goes offline"
    },
    NotificationEventType.PRINTER_ERROR: {
        "label": "Printer Error",
        "icon": "alert-triangle",
        "description": "When a printer reports an error"
    },
    NotificationEventType.MATERIAL_LOW_STOCK: {
        "label": "Material Low Stock",
        "icon": "package",
        "description": "When material inventory is low"
    },
    NotificationEventType.FILE_DOWNLOADED: {
        "label": "File Downloaded",
        "icon": "download",
        "description": "When a file is downloaded from a printer"
    },
}
