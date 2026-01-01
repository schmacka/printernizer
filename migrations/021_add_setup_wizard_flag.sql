-- Migration: Add setup wizard completion flag
-- Date: 2025-12-16
-- Description: Adds setup_wizard_completed flag to settings table for tracking first-run wizard status

-- Insert setup wizard completion flag (default to false = wizard should show)
INSERT OR IGNORE INTO settings (key, value, category, description) VALUES 
    ('setup_wizard_completed', 'false', 'system', 'Whether the initial setup wizard has been completed');
