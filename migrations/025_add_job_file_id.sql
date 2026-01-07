-- Migration 025: Add file_id column to jobs table
-- file_id references library_files.checksum (SHA256 hash)

ALTER TABLE jobs ADD COLUMN file_id TEXT;
