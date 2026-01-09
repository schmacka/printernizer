"""
Notification management API endpoints.

Provides CRUD operations for notification channels, event subscriptions,
test notifications, and delivery history.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request
import structlog

from src.services.notification_service import NotificationService
from src.models.notification import (
    ChannelCreate,
    ChannelUpdate,
    ChannelResponse,
    ChannelListResponse,
    SubscriptionUpdate,
    TestNotificationResponse,
    NotificationHistoryResponse,
    NotificationHistory,
    NotificationEventType,
    EVENT_TYPE_METADATA,
)
from src.utils.errors import (
    NotFoundError,
    ValidationError as PrinternizerValidationError,
    success_response
)

logger = structlog.get_logger()
router = APIRouter()


def get_notification_service(request: Request) -> NotificationService:
    """Get notification service from app state."""
    return request.app.state.notification_service


# =========================================================================
# Channel Management
# =========================================================================

@router.get("", response_model=ChannelListResponse)
async def list_channels(
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    List all notification channels.

    Returns all configured notification channels with their subscriptions.
    """
    channels = await notification_service.list_channels()
    return ChannelListResponse(
        channels=channels,
        total=len(channels)
    )


@router.post("", response_model=ChannelResponse)
async def create_channel(
    request: ChannelCreate,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Create a new notification channel.

    Supports Discord webhooks, Slack webhooks, and ntfy.sh.
    """
    # Validate ntfy requires topic
    if request.channel_type.value == 'ntfy' and not request.topic:
        raise PrinternizerValidationError(
            message="ntfy channels require a topic",
            field="topic"
        )

    channel = await notification_service.create_channel(request)

    if not channel:
        raise PrinternizerValidationError(
            message="Failed to create notification channel"
        )

    return channel


@router.get("/events")
async def list_event_types():
    """
    List available notification event types.

    Returns all event types that can be subscribed to,
    with labels and descriptions for UI display.
    """
    events = []
    for event_type in NotificationEventType:
        metadata = EVENT_TYPE_METADATA.get(event_type, {})
        events.append({
            "id": event_type.value,
            "label": metadata.get("label", event_type.value),
            "icon": metadata.get("icon", "bell"),
            "description": metadata.get("description", "")
        })
    return {"events": events}


@router.get("/history")
async def get_notification_history(
    channel_id: Optional[str] = Query(None, description="Filter by channel ID"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Get notification delivery history.

    Returns recent notifications with delivery status.
    Optionally filter by channel ID.
    """
    result = await notification_service.get_history(
        channel_id=channel_id,
        limit=limit,
        offset=offset
    )

    return {
        "history": result['history'],
        "total": result['total']
    }


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: str,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Get a notification channel by ID.

    Returns channel configuration and subscribed events.
    """
    channel = await notification_service.get_channel(channel_id)

    if not channel:
        raise NotFoundError(
            resource_type="NotificationChannel",
            resource_id=channel_id
        )

    return channel


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: str,
    request: ChannelUpdate,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Update a notification channel.

    Updates channel configuration (name, webhook URL, enabled status).
    Use the subscriptions endpoint to update event subscriptions.
    """
    # Check channel exists
    existing = await notification_service.get_channel(channel_id)
    if not existing:
        raise NotFoundError(
            resource_type="NotificationChannel",
            resource_id=channel_id
        )

    success = await notification_service.update_channel(channel_id, request)

    if not success:
        raise PrinternizerValidationError(
            message="Failed to update notification channel"
        )

    # Return updated channel
    return await notification_service.get_channel(channel_id)


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: str,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Delete a notification channel.

    Removes the channel and all its subscriptions.
    """
    # Check channel exists
    existing = await notification_service.get_channel(channel_id)
    if not existing:
        raise NotFoundError(
            resource_type="NotificationChannel",
            resource_id=channel_id
        )

    success = await notification_service.delete_channel(channel_id)

    if not success:
        raise PrinternizerValidationError(
            message="Failed to delete notification channel"
        )

    return success_response(
        message=f"Channel '{existing.name}' deleted successfully"
    )


# =========================================================================
# Subscriptions
# =========================================================================

@router.get("/{channel_id}/subscriptions")
async def get_subscriptions(
    channel_id: str,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Get event subscriptions for a channel.

    Returns list of event types the channel is subscribed to.
    """
    channel = await notification_service.get_channel(channel_id)

    if not channel:
        raise NotFoundError(
            resource_type="NotificationChannel",
            resource_id=channel_id
        )

    return {
        "channel_id": channel_id,
        "subscribed_events": [e.value for e in channel.subscribed_events]
    }


@router.put("/{channel_id}/subscriptions")
async def update_subscriptions(
    channel_id: str,
    request: SubscriptionUpdate,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Update event subscriptions for a channel.

    Replaces all current subscriptions with the provided list.
    """
    # Check channel exists
    channel = await notification_service.get_channel(channel_id)
    if not channel:
        raise NotFoundError(
            resource_type="NotificationChannel",
            resource_id=channel_id
        )

    success = await notification_service.update_subscriptions(
        channel_id,
        request.subscribed_events
    )

    if not success:
        raise PrinternizerValidationError(
            message="Failed to update subscriptions"
        )

    return success_response(
        message="Subscriptions updated successfully",
        data={
            "channel_id": channel_id,
            "subscribed_events": [e.value for e in request.subscribed_events]
        }
    )


# =========================================================================
# Test Notification
# =========================================================================

@router.post("/{channel_id}/test", response_model=TestNotificationResponse)
async def test_channel(
    channel_id: str,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Send a test notification to a channel.

    Verifies that the channel configuration is correct
    and notifications can be delivered.
    """
    # Check channel exists
    channel = await notification_service.get_channel(channel_id)
    if not channel:
        raise NotFoundError(
            resource_type="NotificationChannel",
            resource_id=channel_id
        )

    result = await notification_service.test_channel(channel_id)

    return TestNotificationResponse(
        success=result['success'],
        message=result['message'],
        channel_id=result['channel_id'],
        channel_name=result['channel_name']
    )
