-- Migration 014: Add Unique Constraint for Job Deduplication
-- Version: 2.5.4
-- Date: 2025-11-11
-- Description: Adds a partial unique index to prevent duplicate job discovery after app restarts
--
-- Problem: When the app restarts during an ongoing print, it discovers the same job
-- multiple times because the in-memory discovery tracking is lost and the deduplication
-- logic was using discovery_time (which changes on restart) instead of print_start_time
-- (which is stable and comes from the printer).
--
-- Solution: Add a partial unique index on (printer_id, filename, DATE(start_time))
-- This prevents duplicate jobs with the same printer, filename, and start time.
-- We use DATE() to allow slight time variations (seconds) in start_time calculation,
-- while still preventing duplicates within the same day.
--
-- The index is PARTIAL (only for rows where start_time IS NOT NULL) to:
-- - Allow multiple jobs with NULL start_time (backward compatibility/fallback)
-- - Only enforce uniqueness when we have reliable start_time data from the printer

-- Step 1: Create a partial unique index on (printer_id, filename, DATE(start_time))
-- This prevents duplicate job discovery after app restarts
-- Using DATE(start_time) instead of full timestamp to handle slight calculation variations
-- (since start_time = datetime.now() - elapsed_time, which can vary by a few seconds)
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_unique_print
ON jobs(printer_id, filename, DATE(start_time))
WHERE start_time IS NOT NULL;

-- Note: This is a partial unique index (WHERE clause) so:
-- 1. Jobs WITH start_time: Cannot have duplicates (same printer + filename + date)
-- 2. Jobs WITHOUT start_time (NULL): Multiple allowed (legacy/fallback behavior)
--
-- This approach balances:
-- - Strict deduplication for modern auto-created jobs (with print_start_time)
-- - Backward compatibility for manually created jobs or edge cases (without start_time)
