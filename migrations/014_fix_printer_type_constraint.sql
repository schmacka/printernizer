-- Migration: Fix printer type CHECK constraint issue
-- Date: 2025-11-10
-- Description: Removes CHECK constraint on printers.type and normalizes existing printer types
--              to match expected values ('bambu_lab', 'prusa')

-- SQLite doesn't support DROP CONSTRAINT, so we need to recreate the table
-- Save existing printers data
CREATE TABLE IF NOT EXISTS printers_backup AS SELECT * FROM printers;

-- Drop existing printers table
DROP TABLE IF EXISTS printers;

-- Recreate printers table without CHECK constraint
CREATE TABLE printers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    ip_address TEXT,
    api_key TEXT,
    access_code TEXT,
    serial_number TEXT,
    status TEXT DEFAULT 'unknown',
    last_seen TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Restore data with normalized printer types
-- Convert any variant types to standard values
INSERT INTO printers SELECT
    id,
    name,
    CASE
        -- Normalize all Prusa variants to 'prusa'
        WHEN LOWER(type) LIKE '%prusa%' THEN 'prusa'
        -- Normalize all Bambu Lab variants to 'bambu_lab'
        WHEN LOWER(type) LIKE '%bambu%' THEN 'bambu_lab'
        -- Keep original value if it's already correct
        WHEN type IN ('prusa', 'bambu_lab') THEN type
        -- Default to the original value (should not happen)
        ELSE type
    END as type,
    ip_address,
    api_key,
    access_code,
    serial_number,
    status,
    last_seen,
    is_active,
    created_at
FROM printers_backup;

-- Drop backup table
DROP TABLE printers_backup;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_printers_is_active ON printers(is_active);
CREATE INDEX IF NOT EXISTS idx_printers_type ON printers(type);

-- Migration complete - printer types normalized and CHECK constraint removed
