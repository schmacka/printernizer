"""
Base notification adapter class.

Defines the interface that all notification channel adapters must implement.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import structlog

logger = structlog.get_logger()


class BaseNotificationAdapter(ABC):
    """
    Abstract base class for notification channel adapters.

    All channel-specific adapters (Discord, Slack, ntfy) must inherit from
    this class and implement the required methods.
    """

    def __init__(self, channel_name: str):
        """
        Initialize the adapter.

        Args:
            channel_name: Display name of the notification channel
        """
        self.channel_name = channel_name

    @abstractmethod
    async def send(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Send a notification for the given event.

        Args:
            event_type: Type of event (e.g., 'job_completed', 'printer_offline')
            event_data: Event payload with details

        Returns:
            True if notification was sent successfully, False otherwise
        """
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the channel connection by sending a test notification.

        Returns:
            Dictionary with:
                - success: bool - Whether the test was successful
                - message: str - Human-readable result message
        """
        pass

    @abstractmethod
    def format_message(self, event_type: str, event_data: Dict[str, Any]) -> Any:
        """
        Format event data for the specific channel.

        Args:
            event_type: Type of event
            event_data: Event payload with details

        Returns:
            Formatted message payload (format depends on channel type)
        """
        pass

    def _get_event_title(self, event_type: str) -> str:
        """
        Get a human-readable title for an event type.

        Args:
            event_type: Event type string

        Returns:
            Human-readable title
        """
        titles = {
            'job_started': 'Print Job Started',
            'job_completed': 'Print Job Completed',
            'job_failed': 'Print Job Failed',
            'job_paused': 'Print Job Paused',
            'printer_online': 'Printer Online',
            'printer_offline': 'Printer Offline',
            'printer_error': 'Printer Error',
            'material_low_stock': 'Material Low Stock',
            'file_downloaded': 'File Downloaded',
            'test': 'Test Notification',
        }
        return titles.get(event_type, event_type.replace('_', ' ').title())

    def _get_event_emoji(self, event_type: str) -> str:
        """
        Get an emoji for an event type.

        Args:
            event_type: Event type string

        Returns:
            Emoji character
        """
        emojis = {
            'job_started': '\u25b6\ufe0f',      # Play button
            'job_completed': '\u2705',          # Check mark
            'job_failed': '\u274c',             # Cross mark
            'job_paused': '\u23f8\ufe0f',       # Pause button
            'printer_online': '\ud83d\udfe2',   # Green circle
            'printer_offline': '\ud83d\udd34',  # Red circle
            'printer_error': '\u26a0\ufe0f',    # Warning sign
            'material_low_stock': '\ud83e\uddf5',  # Thread/spool
            'file_downloaded': '\ud83d\udce5',  # Inbox tray
            'test': '\ud83d\udd14',             # Bell
        }
        return emojis.get(event_type, '\ud83d\udce2')  # Default: megaphone

    def _get_event_color(self, event_type: str) -> int:
        """
        Get a color (as integer) for an event type (for Discord embeds).

        Args:
            event_type: Event type string

        Returns:
            Color as integer (RGB)
        """
        colors = {
            'job_started': 0x3498db,     # Blue
            'job_completed': 0x2ecc71,   # Green
            'job_failed': 0xe74c3c,      # Red
            'job_paused': 0xf39c12,      # Orange
            'printer_online': 0x2ecc71,  # Green
            'printer_offline': 0xe74c3c, # Red
            'printer_error': 0xe74c3c,   # Red
            'material_low_stock': 0xf39c12,  # Orange
            'file_downloaded': 0x3498db, # Blue
            'test': 0x9b59b6,            # Purple
        }
        return colors.get(event_type, 0x95a5a6)  # Default: gray

    def _format_duration(self, seconds: int) -> str:
        """
        Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string (e.g., "2h 15m")
        """
        if not seconds or seconds < 0:
            return "Unknown"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{seconds}s"

    def _extract_job_info(self, event_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract job information from event data for display.

        Args:
            event_data: Event payload

        Returns:
            Dictionary with formatted job info fields
        """
        info = {}

        # Job name
        if job_name := event_data.get('job_name'):
            info['job'] = job_name
        elif filename := event_data.get('filename'):
            info['job'] = filename

        # Printer info
        if printer_name := event_data.get('printer_name'):
            info['printer'] = printer_name
        elif printer_id := event_data.get('printer_id'):
            info['printer'] = printer_id

        # Duration
        if duration := event_data.get('actual_duration'):
            info['duration'] = self._format_duration(duration)
        elif duration := event_data.get('duration'):
            info['duration'] = self._format_duration(duration)

        # Material
        if material := event_data.get('material_used'):
            info['material'] = f"{material:.1f}g"

        # Progress
        if progress := event_data.get('progress'):
            info['progress'] = f"{progress}%"

        # Status (for errors)
        if status := event_data.get('status'):
            info['status'] = status

        # Error message
        if error := event_data.get('error_message'):
            info['error'] = error

        return info
