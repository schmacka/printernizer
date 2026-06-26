-- Migration: 035_slicer_profile_metadata.sql
-- Description: Add source/printer_model/is_builtin to slicer_profiles for
--              curated (built-in) and uploaded profiles.
-- Date: 2026-06-26

ALTER TABLE slicer_profiles ADD COLUMN source TEXT NOT NULL DEFAULT 'import';
ALTER TABLE slicer_profiles ADD COLUMN printer_model TEXT;
ALTER TABLE slicer_profiles ADD COLUMN is_builtin INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_slicer_profiles_source ON slicer_profiles(source);
