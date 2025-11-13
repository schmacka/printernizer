-- Migration: 013_add_source_column_to_files.sql
-- Add source column to files table for backward compatibility
-- Date: 2025-11-10
-- Description: Adds the 'source' column to existing files table to prevent startup errors

-- Check if column exists before adding (SQLite doesn't have IF NOT EXISTS for ALTER TABLE)
-- We'll use a pragma check to see what columns exist

-- Add source column if it doesn't exist
-- SQLite doesn't support IF NOT EXISTS for columns, so we need to handle errors gracefully
-- The migration system should catch errors and continue if column already exists

-- Add source column with default value
ALTER TABLE files ADD COLUMN source TEXT DEFAULT 'printer';

-- Record migration
INSERT INTO schema_migrations (migration_name)
VALUES ('013_add_source_column_to_files')
ON CONFLICT(migration_name) DO NOTHING;
