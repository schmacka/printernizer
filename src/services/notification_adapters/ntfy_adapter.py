"""
ntfy.sh notification adapter.

Sends push notifications via ntfy.sh with priority and tags support.
"""
from typing import Dict, Any
from datetime import datetime
import aiohttp
import structlog

from .base_adapter import BaseNotificationAdapter

logger = structlog.get_logger()


class NtfyAdapter(BaseNotificationAdapter):
    """
    ntfy.sh notification adapter.

    Sends push notifications to ntfy.sh topics. Supports priorities,
    tags, and plain text formatting optimized for mobile display.
    """

    # Default ntfy.sh public server
    DEFAULT_SERVER = "https://ntfy.sh"

    def __init__(
        self,
        server_url: str,
        topic: str,
        channel_name: str = "ntfy"
    ):
        """
        Initialize the ntfy adapter.

        Args:
            server_url: ntfy server URL (e.g., https://ntfy.sh)
            topic: Topic name to publish to
            channel_name: Display name for the channel
        """
        super().__init__(channel_name)
        self.server_url = server_url.rstrip('/')
        self.topic = topic

    async def send(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Send a notification to ntfy.

        Args:
            event_type: Type of event
            event_data: Event payload with details

        Returns:
            True if notification was sent successfully
        """
        try:
            url = f"{self.server_url}/{self.topic}"
            message, headers = self.format_message(event_type, event_data)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=message.encode('utf-8'),
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("ntfy notification sent",
                                   channel=self.channel_name,
                                   topic=self.topic,
                                   event_type=event_type)
                        return True
                    else:
                        error_text = await response.text()
                        logger.error("ntfy notification failed",
                                    status=response.status,
                                    error=error_text,
                                    event_type=event_type)
                        return False

        except aiohttp.ClientError as e:
            logger.error("ntfy notification network error",
                        error=str(e), event_type=event_type)
            return False
        except Exception as e:
            logger.error("ntfy notification unexpected error",
                        error=str(e), event_type=event_type)
            return False

    async def test_connection(self) -> Dict[str, Any]:
        """
        Send a test notification to verify the topic works.

        Returns:
            Dictionary with success status and message
        """
        test_data = {
            'job_name': 'Test Print',
            'printer_name': 'Test Printer',
            'timestamp': datetime.utcnow().isoformat()
        }

        success = await self.send('test', test_data)

        if success:
            return {
                'success': True,
                'message': f'Test notification sent to {self.channel_name} ({self.topic})'
            }
        else:
            return {
                'success': False,
                'message': f'Failed to send test notification to {self.channel_name}'
            }

    def format_message(self, event_type: str, event_data: Dict[str, Any]) -> tuple:
        """
        Format event data for ntfy.

        Args:
            event_type: Type of event
            event_data: Event payload with details

        Returns:
            Tuple of (message body, headers dict)
        """
        title = self._get_event_title(event_type)
        job_info = self._extract_job_info(event_data)

        # Build message body
        lines = []

        if 'job' in job_info:
            lines.append(job_info['job'])

        details = []
        if 'printer' in job_info:
            details.append(f"Printer: {job_info['printer']}")
        if 'duration' in job_info:
            details.append(f"Duration: {job_info['duration']}")
        if 'material' in job_info:
            details.append(f"Material: {job_info['material']}")
        if 'progress' in job_info:
            details.append(f"Progress: {job_info['progress']}")

        if details:
            lines.append(" | ".join(details))

        # Handle material low stock
        if event_type == 'material_low_stock':
            material_details = []
            if material_name := event_data.get('material_name'):
                material_details.append(f"Material: {material_name}")
            if current_stock := event_data.get('current_stock'):
                material_details.append(f"Stock: {current_stock}g")
            if threshold := event_data.get('threshold'):
                material_details.append(f"Threshold: {threshold}g")
            if material_details:
                lines.append(" | ".join(material_details))

        # Handle file downloaded
        if event_type == 'file_downloaded':
            if filename := event_data.get('filename'):
                lines.append(filename)
            if file_size := event_data.get('file_size'):
                lines.append(f"Size: {self._format_file_size(file_size)}")

        # Error message
        if 'error' in job_info:
            lines.append(f"Error: {job_info['error'][:200]}")

        message = "\n".join(lines) if lines else title

        # Build headers
        headers = {
            "Title": title,
            "Priority": self._get_priority(event_type),
            "Tags": self._get_tags(event_type),
        }

        return message, headers

    def _get_priority(self, event_type: str) -> str:
        """
        Get ntfy priority for an event type.

        ntfy priorities: min, low, default, high, urgent

        Args:
            event_type: Event type string

        Returns:
            Priority string
        """
        priorities = {
            'job_started': 'low',
            'job_completed': 'default',
            'job_failed': 'high',
            'job_paused': 'default',
            'printer_online': 'low',
            'printer_offline': 'high',
            'printer_error': 'urgent',
            'material_low_stock': 'high',
            'file_downloaded': 'low',
            'test': 'default',
        }
        return priorities.get(event_type, 'default')

    def _get_tags(self, event_type: str) -> str:
        """
        Get ntfy tags (emojis) for an event type.

        Args:
            event_type: Event type string

        Returns:
            Comma-separated tag string
        """
        tags = {
            'job_started': 'arrow_forward,printer',
            'job_completed': 'white_check_mark,printer',
            'job_failed': 'x,printer',
            'job_paused': 'pause_button,printer',
            'printer_online': 'green_circle,printer',
            'printer_offline': 'red_circle,printer',
            'printer_error': 'warning,printer',
            'material_low_stock': 'thread,warning',
            'file_downloaded': 'inbox_tray,printer',
            'test': 'bell,wrench',
        }
        return tags.get(event_type, 'printer')

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
