-- Migration: Create configuration table for application settings
-- Date: 2024-12-01
-- Description: Creates the configuration key/value table used by services and later migrations

-- Create configuration table
CREATE TABLE IF NOT EXISTS configuration (
    key TEXT PRIMARY KEY NOT NULL,
    value TEXT,
    value_type TEXT NOT NULL DEFAULT 'string', -- 'string' | 'integer' | 'boolean' | 'json'
    category TEXT,                             -- logical grouping, e.g. 'files', 'printer', 'system'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Helpful index for category queries
CREATE INDEX IF NOT EXISTS idx_configuration_category ON configuration(category);

-- Trigger to keep updated_at in sync
CREATE TRIGGER IF NOT EXISTS trg_configuration_updated_at 
AFTER UPDATE ON configuration
BEGIN
    UPDATE configuration SET updated_at = CURRENT_TIMESTAMP WHERE key = NEW.key;
END;
