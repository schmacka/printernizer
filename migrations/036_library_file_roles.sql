-- Migration: 036_library_file_roles.sql
-- Description: Add role (model|printfile) and parent_checksum to library_files
--              to express the model -> printfile relation.
-- Date: 2026-06-26

ALTER TABLE library_files ADD COLUMN role TEXT;
ALTER TABLE library_files ADD COLUMN parent_checksum TEXT;

CREATE INDEX IF NOT EXISTS idx_library_files_role ON library_files(role);
CREATE INDEX IF NOT EXISTS idx_library_files_parent ON library_files(parent_checksum);
