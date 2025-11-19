-- Migration: Create settings table for business configuration
-- Date: 2025-11-14
-- Description: Creates the settings table for German business requirements (VAT, currency, timezone, etc.)

-- Create settings table (similar to configuration but with specific business focus)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY NOT NULL,
    value TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',  -- 'business', 'printer', 'system', etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Helpful index for category queries
CREATE INDEX IF NOT EXISTS idx_settings_category ON settings(category);

-- Trigger to keep updated_at in sync
CREATE TRIGGER IF NOT EXISTS trg_settings_updated_at 
AFTER UPDATE ON settings
BEGIN
    UPDATE settings SET updated_at = CURRENT_TIMESTAMP WHERE key = NEW.key;
END;

-- Insert default German business settings
INSERT OR IGNORE INTO settings (key, value, category, description) VALUES 
    ('vat_rate', '0.19', 'business', 'German standard VAT rate (19%)'),
    ('currency', 'EUR', 'business', 'Default currency (Euro)'),
    ('timezone', 'Europe/Berlin', 'business', 'Default timezone (Europe/Berlin)'),
    ('business_hours_start', '9', 'business', 'Business hours start (24-hour format)'),
    ('business_hours_end', '17', 'business', 'Business hours end (24-hour format)'),
    ('locale', 'de_DE', 'business', 'German locale for formatting');
