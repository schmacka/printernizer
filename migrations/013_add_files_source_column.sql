-- Migration: Add missing columns to files table
-- Date: 2025-11-10
-- Description: Adds source, watch_folder_path, relative_path, and modified_time columns to files table
--              These columns were added to the schema but missing migrations for existing databases
--
-- Note: SQLite does not support IF NOT EXISTS for ALTER TABLE ADD COLUMN until version 3.35.0
-- This migration may fail if columns already exist - this is expected for new databases
-- The migration service should handle this gracefully

-- Temporary table approach for safe column additions
-- 1. Create new table with desired schema
-- 2. Copy data from old table
-- 3. Drop old table
-- 4. Rename new table

-- Save existing data
CREATE TABLE IF NOT EXISTS files_backup AS SELECT * FROM files;

-- Drop existing files table
DROP TABLE IF EXISTS files;

-- Create files table with complete schema
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    printer_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    display_name TEXT,
    file_path TEXT,
    file_size INTEGER,
    file_type TEXT,
    status TEXT DEFAULT 'available',
    source TEXT DEFAULT 'printer',
    download_progress INTEGER DEFAULT 0,
    downloaded_at TIMESTAMP,
    metadata TEXT,
    watch_folder_path TEXT,
    relative_path TEXT,
    modified_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Thumbnail columns (from migration 002)
    has_thumbnail BOOLEAN DEFAULT 0,
    thumbnail_data TEXT,
    thumbnail_width INTEGER,
    thumbnail_height INTEGER,
    thumbnail_format TEXT,
    -- Preview columns (from migration 003)
    thumbnail_source TEXT DEFAULT 'embedded',
    -- Enhanced metadata columns (from migration 006)
    model_width DECIMAL(8,3),
    model_depth DECIMAL(8,3),
    model_height DECIMAL(8,3),
    model_volume DECIMAL(10,3),
    surface_area DECIMAL(10,3),
    object_count INTEGER DEFAULT 1,
    nozzle_diameter DECIMAL(3,2),
    wall_count INTEGER,
    wall_thickness DECIMAL(4,2),
    infill_pattern VARCHAR(50),
    first_layer_height DECIMAL(4,3),
    total_filament_weight DECIMAL(8,3),
    filament_length DECIMAL(10,2),
    filament_colors TEXT,
    waste_weight DECIMAL(8,3),
    material_cost DECIMAL(8,2),
    energy_cost DECIMAL(6,2),
    total_cost DECIMAL(8,2),
    complexity_score INTEGER,
    success_probability DECIMAL(3,2),
    difficulty_level VARCHAR(20),
    overhang_percentage DECIMAL(5,2),
    compatible_printers TEXT,
    slicer_name VARCHAR(100),
    slicer_version VARCHAR(50),
    profile_name VARCHAR(100),
    last_analyzed TIMESTAMP,
    UNIQUE(printer_id, filename)
);

-- Restore data with proper column mapping
INSERT INTO files SELECT
    id,
    printer_id,
    filename,
    display_name,
    file_path,
    file_size,
    file_type,
    status,
    COALESCE(source, 'printer') as source,
    download_progress,
    downloaded_at,
    metadata,
    watch_folder_path,
    relative_path,
    modified_time,
    created_at,
    COALESCE(has_thumbnail, 0),
    thumbnail_data,
    thumbnail_width,
    thumbnail_height,
    thumbnail_format,
    thumbnail_source,
    model_width,
    model_depth,
    model_height,
    model_volume,
    surface_area,
    object_count,
    nozzle_diameter,
    wall_count,
    wall_thickness,
    infill_pattern,
    first_layer_height,
    total_filament_weight,
    filament_length,
    filament_colors,
    waste_weight,
    material_cost,
    energy_cost,
    total_cost,
    complexity_score,
    success_probability,
    difficulty_level,
    overhang_percentage,
    compatible_printers,
    slicer_name,
    slicer_version,
    profile_name,
    last_analyzed
FROM files_backup;

-- Drop backup table
DROP TABLE files_backup;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
CREATE INDEX IF NOT EXISTS idx_files_source ON files(source);
CREATE INDEX IF NOT EXISTS idx_files_watch_folder ON files(watch_folder_path);
CREATE INDEX IF NOT EXISTS idx_files_has_thumbnail ON files(has_thumbnail);
CREATE INDEX IF NOT EXISTS idx_files_complexity ON files(complexity_score);
CREATE INDEX IF NOT EXISTS idx_files_dimensions ON files(model_width, model_depth, model_height);
CREATE INDEX IF NOT EXISTS idx_files_cost ON files(total_cost);
CREATE INDEX IF NOT EXISTS idx_files_analyzed ON files(last_analyzed);

-- Migration complete - files table rebuilt with complete schema
