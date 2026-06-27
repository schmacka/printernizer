-- Migration: 037_library_analysis_error.sql
-- Description: Add analysis_error to library_files so metadata-extraction failures
--              are visible via the API (they otherwise only reach stdout).
-- Date: 2026-06-27

ALTER TABLE library_files ADD COLUMN analysis_error TEXT;
