"""
Notification service for Printernizer.

Manages multi-channel notifications (Discord, Slack, ntfy.sh) and
dispatches notifications based on subscribed events.
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from src.database.database import Database
from src.database.repositories.notification_repository import NotificationRepository
from src.services.base_service import BaseService
from src.services.event_service import EventService
from src.services.notification_adapters import (
    BaseNotificationAdapter,
    DiscordAdapter,
    SlackAdapter,
    NtfyAdapter,
)
from src.models.notification import (
    ChannelType,
    NotificationEventType,
    NotificationChannel,
    NotificationSubscription,
    NotificationHistory,
    ChannelCreate,
    ChannelUpdate,
    ChannelResponse,
    NotificationStatus,
)

logger = structlog.get_logger()


# Event mappings from EventService events to NotificationEventType
EVENT_MAPPINGS = {
    'job_started': NotificationEventType.JOB_STARTED,
    'job_completed': NotificationEventType.JOB_COMPLETED,
    'job_status_changed': None,  # Handled specially based on status
    'printer_connected': NotificationEventType.PRINTER_ONLINE,
    'printer_disconnected': NotificationEventType.PRINTER_OFFLINE,
    'material_low_stock': NotificationEventType.MATERIAL_LOW_STOCK,
    'file_download_complete': NotificationEventType.FILE_DOWNLOADED,
}


class NotificationService(BaseService):
    """
    Service for managing multi-channel notifications.

    Handles:
    - Channel configuration (CRUD)
    - Event subscriptions
    - Notification dispatch
    - Delivery history
    """

    def __init__(
        self,
        database: Database,
        event_service: Optional[EventService] = None
    ):
        """
        Initialize the notification service.

        Args:
            database: Database instance
            event_service: EventService for subscribing to events
        """
        super().__init__(database)
        self.event_service = event_service
        self.repository: Optional[NotificationRepository] = None
        self._adapters: Dict[str, BaseNotificationAdapter] = {}

    async def initialize(self) -> None:
        """Initialize service and subscribe to events."""
        if self._initialized:
            return

        await super().initialize()

        # Initialize repository
        if self.db.connection:
            self.repository = NotificationRepository(self.db.connection)

        # Subscribe to events
        if self.event_service:
            self._subscribe_to_events()

        # Load existing channels and create adapters
        await self._load_channels()

        logger.info("NotificationService initialized")

    async def shutdown(self) -> None:
        """Cleanup service resources."""
        self._adapters.clear()
        await super().shutdown()
        logger.info("NotificationService shutdown")

    def _subscribe_to_events(self) -> None:
        """Subscribe to relevant events from EventService."""
        if not self.event_service:
            return

        # Subscribe to job events
        self.event_service.subscribe('job_started', self._on_job_started)
        self.event_service.subscribe('job_completed', self._on_job_completed)
        self.event_service.subscribe('job_status_changed', self._on_job_status_changed)

        # Subscribe to printer events
        self.event_service.subscribe('printer_connected', self._on_printer_connected)
        self.event_service.subscribe('printer_disconnected', self._on_printer_disconnected)

        # Subscribe to material events
        self.event_service.subscribe('material_low_stock', self._on_material_low_stock)

        # Subscribe to file events
        self.event_service.subscribe('file_download_complete', self._on_file_downloaded)

        logger.info("NotificationService subscribed to events")

    async def _load_channels(self) -> None:
        """Load existing channels and create adapters."""
        if not self.repository:
            return

        try:
            channels = await self.repository.get_all_channels(enabled_only=True)

            for channel in channels:
                self._create_adapter(channel)

            logger.info("Loaded notification channels", count=len(channels))

        except Exception as e:
            logger.error("Failed to load notification channels", error=str(e))

    def _create_adapter(self, channel: Dict[str, Any]) -> Optional[BaseNotificationAdapter]:
        """
        Create an adapter for a channel.

        Args:
            channel: Channel configuration dictionary

        Returns:
            Created adapter or None
        """
        channel_id = channel['id']
        channel_type = channel['channel_type']
        channel_name = channel['name']
        webhook_url = channel['webhook_url']
        topic = channel.get('topic')

        try:
            if channel_type == ChannelType.DISCORD.value:
                adapter = DiscordAdapter(webhook_url, channel_name)
            elif channel_type == ChannelType.SLACK.value:
                adapter = SlackAdapter(webhook_url, channel_name)
            elif channel_type == ChannelType.NTFY.value:
                if not topic:
                    logger.warning("ntfy channel missing topic",
                                  channel_id=channel_id)
                    return None
                adapter = NtfyAdapter(webhook_url, topic, channel_name)
            else:
                logger.warning("Unknown channel type",
                              channel_type=channel_type, channel_id=channel_id)
                return None

            self._adapters[channel_id] = adapter
            return adapter

        except Exception as e:
            logger.error("Failed to create adapter",
                        channel_id=channel_id, error=str(e))
            return None

    def _get_adapter(self, channel_id: str) -> Optional[BaseNotificationAdapter]:
        """Get adapter for a channel ID."""
        return self._adapters.get(channel_id)

    # =========================================================================
    # Event Handlers
    # =========================================================================

    async def _on_job_started(self, data: Dict[str, Any]) -> None:
        """Handle job started event."""
        await self._dispatch_notification(
            NotificationEventType.JOB_STARTED,
            data
        )

    async def _on_job_completed(self, data: Dict[str, Any]) -> None:
        """Handle job completed event."""
        await self._dispatch_notification(
            NotificationEventType.JOB_COMPLETED,
            data
        )

    async def _on_job_status_changed(self, data: Dict[str, Any]) -> None:
        """Handle job status changed event."""
        status = data.get('status', '').lower()

        if status == 'failed':
            await self._dispatch_notification(
                NotificationEventType.JOB_FAILED,
                data
            )
        elif status == 'paused':
            await self._dispatch_notification(
                NotificationEventType.JOB_PAUSED,
                data
            )

    async def _on_printer_connected(self, data: Dict[str, Any]) -> None:
        """Handle printer connected event."""
        await self._dispatch_notification(
            NotificationEventType.PRINTER_ONLINE,
            data
        )

    async def _on_printer_disconnected(self, data: Dict[str, Any]) -> None:
        """Handle printer disconnected event."""
        await self._dispatch_notification(
            NotificationEventType.PRINTER_OFFLINE,
            data
        )

    async def _on_material_low_stock(self, data: Dict[str, Any]) -> None:
        """Handle material low stock event."""
        await self._dispatch_notification(
            NotificationEventType.MATERIAL_LOW_STOCK,
            data
        )

    async def _on_file_downloaded(self, data: Dict[str, Any]) -> None:
        """Handle file downloaded event."""
        await self._dispatch_notification(
            NotificationEventType.FILE_DOWNLOADED,
            data
        )

    async def _dispatch_notification(
        self,
        event_type: NotificationEventType,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Dispatch notification to all subscribed channels.

        Args:
            event_type: Type of notification event
            event_data: Event payload data
        """
        if not self.repository:
            return

        try:
            # Get all channels subscribed to this event
            channels = await self.repository.get_channels_for_event(event_type.value)

            if not channels:
                return

            # Dispatch to each channel (non-blocking)
            for channel in channels:
                asyncio.create_task(
                    self._send_notification(channel, event_type, event_data)
                )

        except Exception as e:
            logger.error("Failed to dispatch notification",
                        event_type=event_type.value, error=str(e))

    async def _send_notification(
        self,
        channel: Dict[str, Any],
        event_type: NotificationEventType,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Send notification to a specific channel.

        Args:
            channel: Channel configuration
            event_type: Type of notification event
            event_data: Event payload data
        """
        channel_id = channel['id']
        adapter = self._get_adapter(channel_id)

        if not adapter:
            # Try to create adapter
            adapter = self._create_adapter(channel)
            if not adapter:
                return

        try:
            success = await adapter.send(event_type.value, event_data)

            # Record history
            if self.repository:
                await self.repository.record_notification(
                    channel_id=channel_id,
                    event_type=event_type.value,
                    event_data=event_data,
                    status=NotificationStatus.SENT.value if success else NotificationStatus.FAILED.value
                )

        except Exception as e:
            logger.error("Failed to send notification",
                        channel_id=channel_id,
                        event_type=event_type.value,
                        error=str(e))

            if self.repository:
                await self.repository.record_notification(
                    channel_id=channel_id,
                    event_type=event_type.value,
                    event_data=event_data,
                    status=NotificationStatus.FAILED.value,
                    error_message=str(e)
                )

    # =========================================================================
    # Channel Management
    # =========================================================================

    async def create_channel(self, request: ChannelCreate) -> Optional[ChannelResponse]:
        """
        Create a new notification channel.

        Args:
            request: Channel creation request

        Returns:
            Created channel response or None
        """
        if not self.repository:
            return None

        channel = NotificationChannel(
            name=request.name,
            channel_type=request.channel_type,
            webhook_url=request.webhook_url,
            topic=request.topic,
            is_enabled=request.is_enabled
        )

        try:
            # Create channel in database
            success = await self.repository.create_channel(channel.model_dump())

            if not success:
                return None

            # Set subscriptions if provided
            if request.subscribed_events:
                await self.repository.set_subscriptions(
                    channel.id,
                    [e.value for e in request.subscribed_events]
                )

            # Create adapter if enabled
            if channel.is_enabled:
                self._create_adapter(channel.model_dump())

            # Return response
            return ChannelResponse(
                id=channel.id,
                name=channel.name,
                channel_type=channel.channel_type,
                webhook_url=channel.webhook_url,
                topic=channel.topic,
                is_enabled=channel.is_enabled,
                subscribed_events=request.subscribed_events,
                created_at=channel.created_at,
                updated_at=channel.updated_at
            )

        except Exception as e:
            logger.error("Failed to create channel", error=str(e))
            return None

    async def update_channel(
        self,
        channel_id: str,
        request: ChannelUpdate
    ) -> bool:
        """
        Update a notification channel.

        Args:
            channel_id: Channel ID to update
            request: Update request

        Returns:
            True if successful
        """
        if not self.repository:
            return False

        try:
            updates = request.model_dump(exclude_unset=True)

            if not updates:
                return False

            success = await self.repository.update_channel(channel_id, updates)

            if success:
                # Reload adapter
                channel = await self.repository.get_channel(channel_id)
                if channel:
                    if channel['is_enabled']:
                        self._create_adapter(channel)
                    else:
                        # Remove adapter if disabled
                        self._adapters.pop(channel_id, None)

            return success

        except Exception as e:
            logger.error("Failed to update channel",
                        channel_id=channel_id, error=str(e))
            return False

    async def delete_channel(self, channel_id: str) -> bool:
        """
        Delete a notification channel.

        Args:
            channel_id: Channel ID to delete

        Returns:
            True if successful
        """
        if not self.repository:
            return False

        try:
            success = await self.repository.delete_channel(channel_id)

            if success:
                self._adapters.pop(channel_id, None)

            return success

        except Exception as e:
            logger.error("Failed to delete channel",
                        channel_id=channel_id, error=str(e))
            return False

    async def get_channel(self, channel_id: str) -> Optional[ChannelResponse]:
        """
        Get a notification channel by ID.

        Args:
            channel_id: Channel ID

        Returns:
            Channel response or None
        """
        if not self.repository:
            return None

        try:
            channel = await self.repository.get_channel(channel_id)

            if not channel:
                return None

            # Get subscriptions
            event_types = await self.repository.get_subscribed_event_types(channel_id)

            return ChannelResponse(
                id=channel['id'],
                name=channel['name'],
                channel_type=ChannelType(channel['channel_type']),
                webhook_url=channel['webhook_url'],
                topic=channel.get('topic'),
                is_enabled=channel['is_enabled'],
                subscribed_events=[NotificationEventType(e) for e in event_types],
                created_at=datetime.fromisoformat(channel['created_at']),
                updated_at=datetime.fromisoformat(channel['updated_at'])
            )

        except Exception as e:
            logger.error("Failed to get channel",
                        channel_id=channel_id, error=str(e))
            return None

    async def list_channels(self) -> List[ChannelResponse]:
        """
        List all notification channels.

        Returns:
            List of channel responses
        """
        if not self.repository:
            return []

        try:
            channels = await self.repository.get_all_channels()
            result = []

            for channel in channels:
                event_types = await self.repository.get_subscribed_event_types(
                    channel['id']
                )

                result.append(ChannelResponse(
                    id=channel['id'],
                    name=channel['name'],
                    channel_type=ChannelType(channel['channel_type']),
                    webhook_url=channel['webhook_url'],
                    topic=channel.get('topic'),
                    is_enabled=channel['is_enabled'],
                    subscribed_events=[NotificationEventType(e) for e in event_types],
                    created_at=datetime.fromisoformat(channel['created_at']),
                    updated_at=datetime.fromisoformat(channel['updated_at'])
                ))

            return result

        except Exception as e:
            logger.error("Failed to list channels", error=str(e))
            return []

    async def update_subscriptions(
        self,
        channel_id: str,
        event_types: List[NotificationEventType]
    ) -> bool:
        """
        Update event subscriptions for a channel.

        Args:
            channel_id: Channel ID
            event_types: List of events to subscribe to

        Returns:
            True if successful
        """
        if not self.repository:
            return False

        try:
            return await self.repository.set_subscriptions(
                channel_id,
                [e.value for e in event_types]
            )

        except Exception as e:
            logger.error("Failed to update subscriptions",
                        channel_id=channel_id, error=str(e))
            return False

    async def test_channel(self, channel_id: str) -> Dict[str, Any]:
        """
        Send a test notification to a channel.

        Args:
            channel_id: Channel ID to test

        Returns:
            Test result dictionary
        """
        if not self.repository:
            return {
                'success': False,
                'message': 'Service not initialized',
                'channel_id': channel_id,
                'channel_name': 'Unknown'
            }

        try:
            channel = await self.repository.get_channel(channel_id)

            if not channel:
                return {
                    'success': False,
                    'message': 'Channel not found',
                    'channel_id': channel_id,
                    'channel_name': 'Unknown'
                }

            adapter = self._get_adapter(channel_id)

            if not adapter:
                adapter = self._create_adapter(channel)

            if not adapter:
                return {
                    'success': False,
                    'message': 'Failed to create adapter',
                    'channel_id': channel_id,
                    'channel_name': channel['name']
                }

            result = await adapter.test_connection()

            return {
                'success': result['success'],
                'message': result['message'],
                'channel_id': channel_id,
                'channel_name': channel['name']
            }

        except Exception as e:
            logger.error("Failed to test channel",
                        channel_id=channel_id, error=str(e))
            return {
                'success': False,
                'message': str(e),
                'channel_id': channel_id,
                'channel_name': 'Unknown'
            }

    async def get_history(
        self,
        channel_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get notification delivery history.

        Args:
            channel_id: Optional filter by channel
            limit: Maximum records to return
            offset: Pagination offset

        Returns:
            Dictionary with history records and total count
        """
        if not self.repository:
            return {'history': [], 'total': 0}

        try:
            history = await self.repository.get_notification_history(
                channel_id=channel_id,
                limit=limit,
                offset=offset
            )
            total = await self.repository.get_history_count(channel_id)

            return {
                'history': history,
                'total': total
            }

        except Exception as e:
            logger.error("Failed to get history", error=str(e))
            return {'history': [], 'total': 0}

    async def cleanup_history(self, days: int = 30) -> int:
        """
        Clean up old notification history.

        Args:
            days: Number of days to keep

        Returns:
            Number of records deleted
        """
        if not self.repository:
            return 0

        try:
            return await self.repository.cleanup_old_history(days)
        except Exception as e:
            logger.error("Failed to cleanup history", error=str(e))
            return 0
