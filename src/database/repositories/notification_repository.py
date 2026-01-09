"""
Notification repository for database operations.

This repository handles all database operations for the multi-channel
notification system, including channels, subscriptions, and delivery history.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
import structlog

from src.database.repositories.base_repository import BaseRepository

logger = structlog.get_logger()


class NotificationRepository(BaseRepository):
    """
    Repository for notification channel database operations.

    Handles CRUD operations for:
    - Notification channels (Discord, Slack, ntfy)
    - Event subscriptions per channel
    - Notification delivery history
    """

    # =========================================================================
    # Channel Operations
    # =========================================================================

    async def create_channel(self, channel_data: Dict[str, Any]) -> bool:
        """
        Create a new notification channel.

        Args:
            channel_data: Dictionary with channel configuration:
                - id: Unique channel ID (UUID)
                - name: Display name
                - channel_type: 'discord', 'slack', or 'ntfy'
                - webhook_url: Webhook URL or server URL
                - topic: ntfy topic (optional)
                - is_enabled: Whether channel is active

        Returns:
            True if successful, False otherwise
        """
        sql = """
            INSERT INTO notification_channels
            (id, name, channel_type, webhook_url, topic, is_enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.utcnow().isoformat()
        params = (
            channel_data.get('id', str(uuid.uuid4())),
            channel_data['name'],
            channel_data['channel_type'],
            channel_data['webhook_url'],
            channel_data.get('topic'),
            1 if channel_data.get('is_enabled', True) else 0,
            now,
            now
        )

        try:
            await self._execute_write(sql, params)
            logger.info("Created notification channel",
                       channel_id=channel_data.get('id'),
                       channel_type=channel_data['channel_type'],
                       name=channel_data['name'])
            return True
        except Exception as e:
            logger.error("Failed to create notification channel",
                        error=str(e), channel_data=channel_data)
            return False

    async def get_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a notification channel by ID.

        Args:
            channel_id: The channel's unique identifier

        Returns:
            Channel data as dictionary, or None if not found
        """
        sql = "SELECT * FROM notification_channels WHERE id = ?"
        result = await self._fetch_one(sql, [channel_id])

        if result:
            result['is_enabled'] = bool(result.get('is_enabled', 0))

        return result

    async def get_all_channels(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all notification channels.

        Args:
            enabled_only: If True, only return enabled channels

        Returns:
            List of channel data dictionaries
        """
        if enabled_only:
            sql = "SELECT * FROM notification_channels WHERE is_enabled = 1 ORDER BY created_at DESC"
        else:
            sql = "SELECT * FROM notification_channels ORDER BY created_at DESC"

        results = await self._fetch_all(sql)

        # Convert is_enabled to boolean
        for result in results:
            result['is_enabled'] = bool(result.get('is_enabled', 0))

        return results

    async def update_channel(self, channel_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a notification channel.

        Args:
            channel_id: The channel's unique identifier
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        if not updates:
            return False

        # Build dynamic update query
        set_clauses = []
        params = []

        for key, value in updates.items():
            if key in ('name', 'webhook_url', 'topic', 'is_enabled'):
                set_clauses.append(f"{key} = ?")
                if key == 'is_enabled':
                    params.append(1 if value else 0)
                else:
                    params.append(value)

        if not set_clauses:
            return False

        # Always update the updated_at timestamp
        set_clauses.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())

        params.append(channel_id)

        sql = f"UPDATE notification_channels SET {', '.join(set_clauses)} WHERE id = ?"

        try:
            await self._execute_write(sql, tuple(params))
            logger.info("Updated notification channel",
                       channel_id=channel_id, updates=list(updates.keys()))
            return True
        except Exception as e:
            logger.error("Failed to update notification channel",
                        error=str(e), channel_id=channel_id)
            return False

    async def delete_channel(self, channel_id: str) -> bool:
        """
        Delete a notification channel and its subscriptions.

        Args:
            channel_id: The channel's unique identifier

        Returns:
            True if successful, False otherwise
        """
        sql = "DELETE FROM notification_channels WHERE id = ?"

        try:
            await self._execute_write(sql, (channel_id,))
            logger.info("Deleted notification channel", channel_id=channel_id)
            return True
        except Exception as e:
            logger.error("Failed to delete notification channel",
                        error=str(e), channel_id=channel_id)
            return False

    # =========================================================================
    # Subscription Operations
    # =========================================================================

    async def set_subscriptions(self, channel_id: str, event_types: List[str]) -> bool:
        """
        Set event subscriptions for a channel (replaces existing subscriptions).

        Args:
            channel_id: The channel's unique identifier
            event_types: List of event types to subscribe to

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete existing subscriptions
            delete_sql = "DELETE FROM notification_subscriptions WHERE channel_id = ?"
            await self._execute_write(delete_sql, (channel_id,))

            # Insert new subscriptions
            if event_types:
                insert_sql = """
                    INSERT INTO notification_subscriptions
                    (id, channel_id, event_type, is_enabled, created_at)
                    VALUES (?, ?, ?, 1, ?)
                """
                now = datetime.utcnow().isoformat()

                for event_type in event_types:
                    await self._execute_write(insert_sql, (
                        str(uuid.uuid4()),
                        channel_id,
                        event_type,
                        now
                    ))

            logger.info("Set notification subscriptions",
                       channel_id=channel_id, event_count=len(event_types))
            return True

        except Exception as e:
            logger.error("Failed to set notification subscriptions",
                        error=str(e), channel_id=channel_id)
            return False

    async def get_subscriptions(self, channel_id: str) -> List[Dict[str, Any]]:
        """
        Get all subscriptions for a channel.

        Args:
            channel_id: The channel's unique identifier

        Returns:
            List of subscription data dictionaries
        """
        sql = """
            SELECT * FROM notification_subscriptions
            WHERE channel_id = ? AND is_enabled = 1
            ORDER BY event_type
        """
        return await self._fetch_all(sql, [channel_id])

    async def get_subscribed_event_types(self, channel_id: str) -> List[str]:
        """
        Get list of event types a channel is subscribed to.

        Args:
            channel_id: The channel's unique identifier

        Returns:
            List of event type strings
        """
        subscriptions = await self.get_subscriptions(channel_id)
        return [sub['event_type'] for sub in subscriptions]

    async def get_channels_for_event(self, event_type: str) -> List[Dict[str, Any]]:
        """
        Get all enabled channels subscribed to a specific event type.

        Args:
            event_type: The event type to find channels for

        Returns:
            List of channel data dictionaries
        """
        sql = """
            SELECT c.* FROM notification_channels c
            INNER JOIN notification_subscriptions s ON c.id = s.channel_id
            WHERE s.event_type = ?
              AND s.is_enabled = 1
              AND c.is_enabled = 1
            ORDER BY c.name
        """
        results = await self._fetch_all(sql, [event_type])

        # Convert is_enabled to boolean
        for result in results:
            result['is_enabled'] = bool(result.get('is_enabled', 0))

        return results

    # =========================================================================
    # History Operations
    # =========================================================================

    async def record_notification(
        self,
        channel_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]],
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Record a notification delivery attempt.

        Args:
            channel_id: The channel that received the notification
            event_type: Type of event that triggered the notification
            event_data: Event payload data (will be JSON serialized)
            status: Delivery status ('sent', 'failed', 'pending')
            error_message: Error message if delivery failed

        Returns:
            True if successful, False otherwise
        """
        sql = """
            INSERT INTO notification_history
            (id, channel_id, event_type, event_data, status, error_message, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            str(uuid.uuid4()),
            channel_id,
            event_type,
            json.dumps(event_data) if event_data else None,
            status,
            error_message,
            datetime.utcnow().isoformat()
        )

        try:
            await self._execute_write(sql, params)
            return True
        except Exception as e:
            logger.error("Failed to record notification history",
                        error=str(e), channel_id=channel_id, event_type=event_type)
            return False

    async def get_notification_history(
        self,
        channel_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get notification delivery history.

        Args:
            channel_id: Optional filter by channel ID
            limit: Maximum number of records to return
            offset: Number of records to skip (for pagination)

        Returns:
            List of history records
        """
        if channel_id:
            sql = """
                SELECT * FROM notification_history
                WHERE channel_id = ?
                ORDER BY sent_at DESC
                LIMIT ? OFFSET ?
            """
            params = [channel_id, limit, offset]
        else:
            sql = """
                SELECT * FROM notification_history
                ORDER BY sent_at DESC
                LIMIT ? OFFSET ?
            """
            params = [limit, offset]

        results = await self._fetch_all(sql, params)

        # Parse JSON event_data
        for result in results:
            if result.get('event_data'):
                try:
                    result['event_data'] = json.loads(result['event_data'])
                except json.JSONDecodeError:
                    pass

        return results

    async def get_history_count(self, channel_id: Optional[str] = None) -> int:
        """
        Get total count of notification history records.

        Args:
            channel_id: Optional filter by channel ID

        Returns:
            Total count of history records
        """
        if channel_id:
            sql = "SELECT COUNT(*) as count FROM notification_history WHERE channel_id = ?"
            result = await self._fetch_one(sql, [channel_id])
        else:
            sql = "SELECT COUNT(*) as count FROM notification_history"
            result = await self._fetch_one(sql)

        return result['count'] if result else 0

    async def cleanup_old_history(self, days: int = 30) -> int:
        """
        Delete notification history older than specified days.

        Args:
            days: Number of days to keep history

        Returns:
            Number of records deleted
        """
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Get count first
        count_sql = "SELECT COUNT(*) as count FROM notification_history WHERE sent_at < ?"
        count_result = await self._fetch_one(count_sql, [cutoff])
        count = count_result['count'] if count_result else 0

        if count > 0:
            delete_sql = "DELETE FROM notification_history WHERE sent_at < ?"
            await self._execute_write(delete_sql, (cutoff,))
            logger.info("Cleaned up old notification history",
                       deleted_count=count, days=days)

        return count
