-- Migration: Make cost_per_kg optional in materials table
-- Date: 2025-11-04
-- Description: Allow cost_per_kg to be NULL or 0 for users who don't track material costs

-- SQLite doesn't support ALTER COLUMN directly, so we need to:
-- 1. Create a new table with the updated schema
-- 2. Copy data from old table
-- 3. Drop old table
-- 4. Rename new table

BEGIN TRANSACTION;

-- Create new materials table with cost_per_kg allowing NULL/0
CREATE TABLE IF NOT EXISTS materials_new (
    id TEXT PRIMARY KEY,
    material_type TEXT NOT NULL,
    brand TEXT NOT NULL,
    color TEXT NOT NULL,
    diameter REAL NOT NULL,
    weight REAL NOT NULL,
    remaining_weight REAL NOT NULL,
    cost_per_kg DECIMAL(10,2) DEFAULT 0,
    purchase_date TIMESTAMP NOT NULL,
    vendor TEXT NOT NULL,
    batch_number TEXT,
    notes TEXT,
    printer_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE SET NULL
);

-- Copy existing data
INSERT INTO materials_new 
SELECT * FROM materials;

-- Drop old table
DROP TABLE materials;

-- Rename new table to materials
ALTER TABLE materials_new RENAME TO materials;

COMMIT;
