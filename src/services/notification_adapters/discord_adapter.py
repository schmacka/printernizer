"""
Discord webhook notification adapter.

Sends notifications to Discord channels via webhook with rich embeds.
"""
from typing import Dict, Any, List
from datetime import datetime
import aiohttp
import structlog

from .base_adapter import BaseNotificationAdapter

logger = structlog.get_logger()


class DiscordAdapter(BaseNotificationAdapter):
    """
    Discord webhook notification adapter.

    Sends formatted embeds to Discord channels using the webhook API.
    Supports rich formatting with colors, fields, and timestamps.
    """

    def __init__(self, webhook_url: str, channel_name: str = "Discord"):
        """
        Initialize the Discord adapter.

        Args:
            webhook_url: Discord webhook URL
            channel_name: Display name for the channel
        """
        super().__init__(channel_name)
        self.webhook_url = webhook_url

    async def send(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Send a notification to Discord.

        Args:
            event_type: Type of event
            event_data: Event payload with details

        Returns:
            True if notification was sent successfully
        """
        try:
            embed = self.format_message(event_type, event_data)
            payload = {"embeds": [embed]}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 204:
                        logger.info("Discord notification sent",
                                   channel=self.channel_name,
                                   event_type=event_type)
                        return True
                    else:
                        error_text = await response.text()
                        logger.error("Discord notification failed",
                                    status=response.status,
                                    error=error_text,
                                    event_type=event_type)
                        return False

        except aiohttp.ClientError as e:
            logger.error("Discord notification network error",
                        error=str(e), event_type=event_type)
            return False
        except Exception as e:
            logger.error("Discord notification unexpected error",
                        error=str(e), event_type=event_type)
            return False

    async def test_connection(self) -> Dict[str, Any]:
        """
        Send a test notification to verify the webhook works.

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
                'message': f'Test notification sent to {self.channel_name}'
            }
        else:
            return {
                'success': False,
                'message': f'Failed to send test notification to {self.channel_name}'
            }

    def format_message(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format event data as a Discord embed.

        Args:
            event_type: Type of event
            event_data: Event payload with details

        Returns:
            Discord embed object as dictionary
        """
        title = self._get_event_title(event_type)
        color = self._get_event_color(event_type)
        job_info = self._extract_job_info(event_data)

        # Build embed
        embed = {
            "title": f"{self._get_event_emoji(event_type)} {title}",
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Printernizer"
            }
        }

        # Add description for job events
        if 'job' in job_info:
            embed["description"] = f"**{job_info['job']}**"

        # Build fields
        fields: List[Dict[str, Any]] = []

        if 'printer' in job_info:
            fields.append({
                "name": "Printer",
                "value": job_info['printer'],
                "inline": True
            })

        if 'duration' in job_info:
            fields.append({
                "name": "Duration",
                "value": job_info['duration'],
                "inline": True
            })

        if 'material' in job_info:
            fields.append({
                "name": "Material",
                "value": job_info['material'],
                "inline": True
            })

        if 'progress' in job_info:
            fields.append({
                "name": "Progress",
                "value": job_info['progress'],
                "inline": True
            })

        if 'status' in job_info:
            fields.append({
                "name": "Status",
                "value": job_info['status'],
                "inline": True
            })

        if 'error' in job_info:
            fields.append({
                "name": "Error",
                "value": job_info['error'][:1024],  # Discord limit
                "inline": False
            })

        # Handle material low stock specifically
        if event_type == 'material_low_stock':
            if material_name := event_data.get('material_name'):
                fields.append({
                    "name": "Material",
                    "value": material_name,
                    "inline": True
                })
            if current_stock := event_data.get('current_stock'):
                fields.append({
                    "name": "Current Stock",
                    "value": f"{current_stock}g",
                    "inline": True
                })
            if threshold := event_data.get('threshold'):
                fields.append({
                    "name": "Threshold",
                    "value": f"{threshold}g",
                    "inline": True
                })

        # Handle file downloaded
        if event_type == 'file_downloaded':
            if filename := event_data.get('filename'):
                embed["description"] = f"**{filename}**"
            if file_size := event_data.get('file_size'):
                fields.append({
                    "name": "Size",
                    "value": self._format_file_size(file_size),
                    "inline": True
                })

        if fields:
            embed["fields"] = fields

        return embed

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
