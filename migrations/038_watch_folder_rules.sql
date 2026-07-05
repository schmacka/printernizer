-- Migration: 038_watch_folder_rules.sql
-- Description: Per-folder processing rules for watch folders (Phase 7b).
--              auto_tag: derive a tag from the first-level subfolder on ingest.
--              classification: tag ingested files as business or private.
--              default_printer_id / default_profile_id: defaults consumed by
--              the auto-slice workflows (Phase 7c).
-- Date: 2026-07-05

ALTER TABLE watch_folders ADD COLUMN auto_tag BOOLEAN NOT NULL DEFAULT 0;
ALTER TABLE watch_folders ADD COLUMN classification TEXT;
ALTER TABLE watch_folders ADD COLUMN default_printer_id TEXT;
ALTER TABLE watch_folders ADD COLUMN default_profile_id TEXT;
