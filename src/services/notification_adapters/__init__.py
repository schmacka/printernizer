"""
Notification channel adapters for multi-channel notification system.

Each adapter handles formatting and sending notifications to a specific
service (Discord, Slack, ntfy.sh).
"""
from .base_adapter import BaseNotificationAdapter
from .discord_adapter import DiscordAdapter
from .slack_adapter import SlackAdapter
from .ntfy_adapter import NtfyAdapter

__all__ = [
    'BaseNotificationAdapter',
    'DiscordAdapter',
    'SlackAdapter',
    'NtfyAdapter',
]
