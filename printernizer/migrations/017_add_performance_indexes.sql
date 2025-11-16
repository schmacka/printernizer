-- Migration: 017_add_performance_indexes.sql
-- Add performance indexes for library_files
-- Priority: MINOR
-- Date: 2025-11-13

-- Library files performance indexes
CREATE INDEX IF NOT EXISTS idx_library_search ON library_files(search_index);
CREATE INDEX IF NOT EXISTS idx_library_complexity ON library_files(complexity_score);
CREATE INDEX IF NOT EXISTS idx_library_dimensions ON library_files(model_width, model_depth, model_height);
CREATE INDEX IF NOT EXISTS idx_library_cost ON library_files(total_cost);
CREATE INDEX IF NOT EXISTS idx_library_analyzed ON library_files(last_analyzed);
CREATE INDEX IF NOT EXISTS idx_library_has_thumbnail ON library_files(has_thumbnail);
