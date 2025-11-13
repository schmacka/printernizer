-- Migration: 008_fix_library_stats_nulls.sql
-- Fix library_stats view to return 0 instead of NULL for empty library
-- Version: v1.2.1

-- Drop old view
DROP VIEW IF EXISTS library_stats;

-- Recreate view with COALESCE for NULL handling
CREATE VIEW library_stats AS
SELECT
    COUNT(*) as total_files,
    COALESCE(SUM(file_size), 0) as total_size,
    COUNT(CASE WHEN has_thumbnail = 1 THEN 1 END) as files_with_thumbnails,
    COUNT(CASE WHEN last_analyzed IS NOT NULL THEN 1 END) as files_analyzed,
    COUNT(CASE WHEN status = 'available' THEN 1 END) as available_files,
    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_files,
    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_files,
    COUNT(DISTINCT file_type) as unique_file_types,
    COALESCE(AVG(file_size), 0) as avg_file_size,
    COALESCE(SUM(CASE WHEN material_cost IS NOT NULL THEN material_cost ELSE 0 END), 0) as total_material_cost
FROM library_files;
