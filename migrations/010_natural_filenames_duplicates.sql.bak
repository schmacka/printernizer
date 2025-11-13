-- Migration: 010_natural_filenames_duplicates.sql
-- Add duplicate detection and tracking to library system
-- Feature: Natural Filenames with Duplicate Detection
-- Version: v1.3.0

-- Add duplicate tracking columns to library_files table
ALTER TABLE library_files ADD COLUMN is_duplicate BOOLEAN DEFAULT 0;
ALTER TABLE library_files ADD COLUMN duplicate_of_checksum TEXT;
ALTER TABLE library_files ADD COLUMN duplicate_count INTEGER DEFAULT 0;

-- Add foreign key constraint for duplicate_of_checksum
-- (References the checksum of the first/original file with the same content)

-- Create indexes for efficient duplicate queries
CREATE INDEX IF NOT EXISTS idx_library_is_duplicate
    ON library_files(is_duplicate);

CREATE INDEX IF NOT EXISTS idx_library_duplicate_of
    ON library_files(duplicate_of_checksum);

CREATE INDEX IF NOT EXISTS idx_library_checksum_added
    ON library_files(checksum, added_to_library);

-- Create view for duplicate groups (files with same checksum)
CREATE VIEW IF NOT EXISTS library_duplicate_groups AS
SELECT
    lf1.checksum,
    lf1.filename as original_filename,
    lf1.id as original_id,
    lf1.added_to_library as original_added,
    COUNT(lf2.id) as total_copies,
    SUM(lf2.file_size) as total_duplicate_size,
    GROUP_CONCAT(lf2.filename, ', ') as duplicate_filenames
FROM library_files lf1
LEFT JOIN library_files lf2 ON lf1.checksum = lf2.checksum AND lf2.is_duplicate = 1
WHERE lf1.is_duplicate = 0
GROUP BY lf1.checksum
HAVING COUNT(lf2.id) > 0;

-- Create view for library stats including duplicate information
CREATE VIEW IF NOT EXISTS library_stats_with_duplicates AS
SELECT
    COUNT(*) as total_files,
    SUM(file_size) as total_size,
    COUNT(CASE WHEN is_duplicate = 0 THEN 1 END) as unique_files,
    COUNT(CASE WHEN is_duplicate = 1 THEN 1 END) as duplicate_files,
    SUM(CASE WHEN is_duplicate = 1 THEN file_size ELSE 0 END) as wasted_space_bytes,
    COUNT(CASE WHEN has_thumbnail = 1 THEN 1 END) as files_with_thumbnails,
    COUNT(CASE WHEN last_analyzed IS NOT NULL THEN 1 END) as files_analyzed,
    COUNT(DISTINCT file_type) as unique_file_types,
    AVG(file_size) as avg_file_size
FROM library_files;

-- Migration notes:
-- 1. This migration adds duplicate detection without changing storage structure
-- 2. is_duplicate=0 means this is the original/first file with this checksum
-- 3. is_duplicate=1 means this is a duplicate (copied from another source)
-- 4. duplicate_of_checksum points to the original file's checksum
-- 5. duplicate_count on original file tracks how many duplicates exist
-- 6. Files are now stored with natural filenames (no checksum-based sharding)
-- 7. Filename conflicts are resolved by appending _1, _2, etc.
