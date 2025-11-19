-- Migration 005: Fix NULL Job IDs and Add NOT NULL Constraint
-- Version: 1.1.2
-- Date: 2025-10-01
-- Description: Fixes existing jobs with NULL IDs and enforces NOT NULL constraint on jobs.id column

-- Step 1: Drop views that depend on jobs table
DROP VIEW IF EXISTS v_snapshots_with_context;

-- Step 2: Generate UUIDs for existing jobs with NULL IDs
-- We need to create a new table since SQLite doesn't allow adding NOT NULL to existing columns

-- Create new jobs table with proper constraints
CREATE TABLE IF NOT EXISTS jobs_new (
    id TEXT PRIMARY KEY NOT NULL CHECK(length(id) > 0),
    printer_id TEXT NOT NULL REFERENCES printers(id) ON DELETE CASCADE,
    printer_type TEXT NOT NULL,
    job_name TEXT NOT NULL,
    filename TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    estimated_duration INTEGER,
    actual_duration INTEGER,
    progress INTEGER DEFAULT 0,
    material_used REAL,
    material_cost REAL,
    power_cost REAL,
    is_business BOOLEAN DEFAULT 0,
    customer_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Copy data from old table to new table, generating UUIDs for NULL IDs
INSERT INTO jobs_new (
    id, printer_id, printer_type, job_name, filename, status,
    start_time, end_time, estimated_duration, actual_duration, progress,
    material_used, material_cost, power_cost, is_business, customer_info,
    created_at, updated_at
)
SELECT
    CASE
        WHEN id IS NULL OR id = '' THEN lower(hex(randomblob(16)))
        ELSE id
    END as id,
    printer_id,
    printer_type,
    job_name,
    filename,
    status,
    start_time,
    end_time,
    estimated_duration,
    actual_duration,
    progress,
    material_used,
    material_cost,
    power_cost,
    is_business,
    customer_info,
    created_at,
    updated_at
FROM jobs;

-- Drop old table
DROP TABLE jobs;

-- Rename new table to original name
ALTER TABLE jobs_new RENAME TO jobs;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_jobs_printer_id ON jobs(printer_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

-- Step 3: Recreate the view that depends on jobs table
CREATE VIEW IF NOT EXISTS v_snapshots_with_context AS
SELECT
    s.*,
    j.job_name,
    j.status as job_status,
    j.start_time as job_start_time,
    j.end_time as job_end_time,
    p.name as printer_name,
    p.type as printer_type
FROM snapshots s
LEFT JOIN jobs j ON s.job_id = j.id
JOIN printers p ON s.printer_id = p.id
ORDER BY s.captured_at DESC;
