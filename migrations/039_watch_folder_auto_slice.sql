-- Migration: 039_watch_folder_auto_slice.sql
-- Description: Auto-slice workflow flag for watch folders (Phase 7c).
--              When enabled (and a default profile is configured), newly
--              ingested model files are queued for slicing automatically.
--              Prints are never started automatically.
-- Date: 2026-07-05

ALTER TABLE watch_folders ADD COLUMN auto_slice BOOLEAN NOT NULL DEFAULT 0;
