"""
Slack webhook notification adapter.

Sends notifications to Slack channels via webhook with Block Kit formatting.
"""
from typing import Dict, Any, List
from datetime import datetime
import aiohttp
import structlog

from .base_adapter import BaseNotificationAdapter

logger = structlog.get_logger()


class SlackAdapter(BaseNotificationAdapter):
    """
    Slack webhook notification adapter.

    Sends formatted Block Kit messages to Slack channels using the webhook API.
    Supports rich formatting with sections, context, and dividers.
    """

    def __init__(self, webhook_url: str, channel_name: str = "Slack"):
        """
        Initialize the Slack adapter.

        Args:
            webhook_url: Slack webhook URL
            channel_name: Display name for the channel
        """
        super().__init__(channel_name)
        self.webhook_url = webhook_url

    async def send(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Send a notification to Slack.

        Args:
            event_type: Type of event
            event_data: Event payload with details

        Returns:
            True if notification was sent successfully
        """
        try:
            payload = self.format_message(event_type, event_data)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_text = await response.text()

                    if response.status == 200 and response_text == 'ok':
                        logger.info("Slack notification sent",
                                   channel=self.channel_name,
                                   event_type=event_type)
                        return True
                    else:
                        logger.error("Slack notification failed",
                                    status=response.status,
                                    response=response_text,
                                    event_type=event_type)
                        return False

        except aiohttp.ClientError as e:
            logger.error("Slack notification network error",
                        error=str(e), event_type=event_type)
            return False
        except Exception as e:
            logger.error("Slack notification unexpected error",
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
        Format event data as a Slack Block Kit message.

        Args:
            event_type: Type of event
            event_data: Event payload with details

        Returns:
            Slack message payload with blocks
        """
        title = self._get_event_title(event_type)
        emoji = self._get_event_emoji(event_type)
        job_info = self._extract_job_info(event_data)

        blocks: List[Dict[str, Any]] = []

        # Header section
        header_text = f"{emoji} *{title}*"
        if 'job' in job_info:
            header_text += f"\n`{job_info['job']}`"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": header_text
            }
        })

        # Details section with fields
        fields: List[Dict[str, str]] = []

        if 'printer' in job_info:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Printer:*\n{job_info['printer']}"
            })

        if 'duration' in job_info:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Duration:*\n{job_info['duration']}"
            })

        if 'material' in job_info:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Material:*\n{job_info['material']}"
            })

        if 'progress' in job_info:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Progress:*\n{job_info['progress']}"
            })

        if 'status' in job_info:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Status:*\n{job_info['status']}"
            })

        # Handle material low stock
        if event_type == 'material_low_stock':
            if material_name := event_data.get('material_name'):
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*Material:*\n{material_name}"
                })
            if current_stock := event_data.get('current_stock'):
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*Current Stock:*\n{current_stock}g"
                })
            if threshold := event_data.get('threshold'):
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*Threshold:*\n{threshold}g"
                })

        # Handle file downloaded
        if event_type == 'file_downloaded':
            if file_size := event_data.get('file_size'):
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*Size:*\n{self._format_file_size(file_size)}"
                })

        # Add fields section if we have any
        if fields:
            # Slack limits to 10 fields per section, and 2 fields per row works best
            for i in range(0, len(fields), 2):
                section_fields = fields[i:i+2]
                blocks.append({
                    "type": "section",
                    "fields": section_fields
                })

        # Error section (if present)
        if 'error' in job_info:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":warning: *Error:*\n```{job_info['error'][:2000]}```"
                }
            })

        # Context footer with timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":printer: Printernizer | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        })

        return {"blocks": blocks}

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
