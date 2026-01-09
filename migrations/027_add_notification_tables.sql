-- Migration: 027_add_notification_tables
-- Description: Add tables for multi-channel notification system (Discord, Slack, ntfy.sh)
-- Date: 2026-01-09

-- Notification channels configuration (Discord, Slack, ntfy)
CREATE TABLE IF NOT EXISTS notification_channels (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    channel_type TEXT NOT NULL CHECK (channel_type IN ('discord', 'slack', 'ntfy')),
    webhook_url TEXT NOT NULL,
    topic TEXT,  -- Used for ntfy.sh topic
    is_enabled INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notification_channels_type ON notification_channels(channel_type);
CREATE INDEX IF NOT EXISTS idx_notification_channels_enabled ON notification_channels(is_enabled);

-- Per-event subscriptions for each channel
CREATE TABLE IF NOT EXISTS notification_subscriptions (
    id TEXT PRIMARY KEY NOT NULL,
    channel_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'job_started',
        'job_completed',
        'job_failed',
        'job_paused',
        'printer_online',
        'printer_offline',
        'printer_error',
        'material_low_stock',
        'file_downloaded'
    )),
    is_enabled INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (channel_id) REFERENCES notification_channels(id) ON DELETE CASCADE,
    UNIQUE(channel_id, event_type)
);

CREATE INDEX IF NOT EXISTS idx_notification_subscriptions_channel ON notification_subscriptions(channel_id);
CREATE INDEX IF NOT EXISTS idx_notification_subscriptions_event ON notification_subscriptions(event_type);
CREATE INDEX IF NOT EXISTS idx_notification_subscriptions_enabled ON notification_subscriptions(is_enabled);

-- Notification delivery history
CREATE TABLE IF NOT EXISTS notification_history (
    id TEXT PRIMARY KEY NOT NULL,
    channel_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT,  -- JSON serialized event data
    status TEXT NOT NULL CHECK (status IN ('sent', 'failed', 'pending')),
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (channel_id) REFERENCES notification_channels(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notification_history_channel ON notification_history(channel_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_status ON notification_history(status);
CREATE INDEX IF NOT EXISTS idx_notification_history_sent ON notification_history(sent_at);
