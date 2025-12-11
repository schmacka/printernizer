-- Migration: 007_library_system.sql
-- Create library system tables for unified file management
-- Feature: Library System - Comprehensive file management with checksum-based deduplication
-- Version: v1.2.0

-- Main library files table
CREATE TABLE IF NOT EXISTS library_files (
    -- Identity
    id TEXT PRIMARY KEY,                        -- UUID for database record
    checksum TEXT UNIQUE NOT NULL,              -- SHA-256 content hash (unique identifier)
    filename TEXT NOT NULL,                     -- Original filename
    display_name TEXT,                          -- User-editable display name

    -- Physical location
    library_path TEXT NOT NULL,                 -- Path within library/ structure
    file_size INTEGER NOT NULL,                 -- File size in bytes
    file_type TEXT NOT NULL,                    -- File extension (.3mf, .stl, .gcode, etc.)

    -- Source tracking (JSON array of source objects)
    sources TEXT NOT NULL,                      -- JSON: [{type, printer_id, folder_path, discovered_at}]

    -- Status & lifecycle
    status TEXT DEFAULT 'available',            -- available, processing, ready, error
    download_status TEXT,                       -- For printer files: pending, downloading, completed
    download_progress INTEGER DEFAULT 0,        -- Download progress (0-100)
    error_message TEXT,                         -- Error details if status=error

    -- Timestamps
    added_to_library TIMESTAMP NOT NULL,        -- When added to library
    last_modified TIMESTAMP,                    -- File modification time
    last_accessed TIMESTAMP,                    -- Last time file was accessed/viewed

    -- Enhanced metadata (from METADATA-001)
    has_thumbnail BOOLEAN DEFAULT 0,
    thumbnail_data TEXT,                        -- Base64 or path to thumbnail
    thumbnail_width INTEGER,
    thumbnail_height INTEGER,
    thumbnail_format TEXT,

    -- Physical properties
    model_width DECIMAL(8,3),
    model_depth DECIMAL(8,3),
    model_height DECIMAL(8,3),
    model_volume DECIMAL(10,3),
    surface_area DECIMAL(10,3),
    object_count INTEGER DEFAULT 1,

    -- Print settings
    layer_height DECIMAL(4,3),
    first_layer_height DECIMAL(4,3),
    nozzle_diameter DECIMAL(3,2),
    wall_count INTEGER,
    wall_thickness DECIMAL(4,2),
    infill_density DECIMAL(5,2),
    infill_pattern VARCHAR(50),
    support_used BOOLEAN,
    nozzle_temperature INTEGER,
    bed_temperature INTEGER,
    print_speed DECIMAL(6,2),
    total_layer_count INTEGER,

    -- Material requirements
    total_filament_weight DECIMAL(8,3),         -- Total weight in grams
    filament_length DECIMAL(10,2),              -- Total length in meters
    filament_colors TEXT,                       -- JSON array of color codes
    material_types TEXT,                        -- JSON array of material types
    waste_weight DECIMAL(8,3),
    multi_material BOOLEAN DEFAULT 0,

    -- Cost analysis
    material_cost DECIMAL(8,2),
    energy_cost DECIMAL(6,2),
    total_cost DECIMAL(8,2),

    -- Quality metrics
    complexity_score INTEGER,                   -- 1-10
    difficulty_level VARCHAR(20),               -- Beginner, Intermediate, Advanced, Expert
    success_probability DECIMAL(5,2),           -- 0-100
    overhang_percentage DECIMAL(5,2),

    -- Compatibility
    compatible_printers TEXT,                   -- JSON array
    slicer_name VARCHAR(100),
    slicer_version VARCHAR(50),
    profile_name VARCHAR(100),
    bed_type VARCHAR(50),

    -- Organization
    tags TEXT,                                  -- JSON array: ["benchy", "calibration"]
    collection_id TEXT,                         -- FK to collections table (future)
    notes TEXT,                                 -- User notes

    -- Metadata timestamp
    last_analyzed TIMESTAMP,                    -- When metadata was last extracted

    -- Search optimization
    search_index TEXT                           -- Full-text search helper (filename + tags + notes)
);

-- File sources junction table (detailed source tracking)
CREATE TABLE IF NOT EXISTS library_file_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_checksum TEXT NOT NULL,                -- FK to library_files.checksum
    source_type TEXT NOT NULL,                  -- printer, watch_folder, upload
    source_id TEXT,                             -- printer_id or folder path
    source_name TEXT,                           -- Human-readable name
    original_path TEXT,                         -- Original file path/location
    original_filename TEXT,                     -- Original filename at source
    discovered_at TIMESTAMP NOT NULL,           -- When discovered at this source
    metadata TEXT,                              -- JSON for source-specific data

    FOREIGN KEY (file_checksum) REFERENCES library_files(checksum) ON DELETE CASCADE,
    UNIQUE(file_checksum, source_type, source_id, original_path)
);

-- Collections table (for organizing files into groups)
CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    thumbnail_checksum TEXT,                    -- FK to library_files.checksum
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (thumbnail_checksum) REFERENCES library_files(checksum) ON DELETE SET NULL
);

-- Collection members (many-to-many relationship)
CREATE TABLE IF NOT EXISTS collection_members (
    collection_id TEXT NOT NULL,
    file_checksum TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sort_order INTEGER DEFAULT 0,

    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
    FOREIGN KEY (file_checksum) REFERENCES library_files(checksum) ON DELETE CASCADE,
    PRIMARY KEY (collection_id, file_checksum)
);

-- Performance indexes for library_files
CREATE INDEX IF NOT EXISTS idx_library_checksum ON library_files(checksum);
CREATE INDEX IF NOT EXISTS idx_library_status ON library_files(status);
CREATE INDEX IF NOT EXISTS idx_library_file_type ON library_files(file_type);
CREATE INDEX IF NOT EXISTS idx_library_added ON library_files(added_to_library DESC);
CREATE INDEX IF NOT EXISTS idx_library_search ON library_files(search_index);
CREATE INDEX IF NOT EXISTS idx_library_complexity ON library_files(complexity_score);
CREATE INDEX IF NOT EXISTS idx_library_dimensions ON library_files(model_width, model_depth, model_height);
CREATE INDEX IF NOT EXISTS idx_library_cost ON library_files(total_cost);
CREATE INDEX IF NOT EXISTS idx_library_analyzed ON library_files(last_analyzed);
CREATE INDEX IF NOT EXISTS idx_library_has_thumbnail ON library_files(has_thumbnail);
CREATE INDEX IF NOT EXISTS idx_library_tags ON library_files(tags);

-- Indexes for library_file_sources
CREATE INDEX IF NOT EXISTS idx_library_sources_checksum ON library_file_sources(file_checksum);
CREATE INDEX IF NOT EXISTS idx_library_sources_type ON library_file_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_library_sources_id ON library_file_sources(source_id);

-- Indexes for collections
CREATE INDEX IF NOT EXISTS idx_collection_members_collection ON collection_members(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_members_file ON collection_members(file_checksum);

-- View for quick library statistics
-- Drop old TABLE if it exists (from database.py _create_tables)
DROP TABLE IF EXISTS library_stats;

-- Create as VIEW for auto-updating statistics
CREATE VIEW IF NOT EXISTS library_stats AS
SELECT
    COUNT(*) as total_files,
    SUM(file_size) as total_size,
    COUNT(CASE WHEN has_thumbnail = 1 THEN 1 END) as files_with_thumbnails,
    COUNT(CASE WHEN last_analyzed IS NOT NULL THEN 1 END) as files_analyzed,
    COUNT(CASE WHEN status = 'available' THEN 1 END) as available_files,
    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_files,
    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_files,
    COUNT(DISTINCT file_type) as unique_file_types,
    AVG(file_size) as avg_file_size,
    SUM(CASE WHEN material_cost IS NOT NULL THEN material_cost ELSE 0 END) as total_material_cost
FROM library_files;

-- View for file sources (denormalized for easy querying)
CREATE VIEW IF NOT EXISTS library_files_with_sources AS
SELECT
    lf.*,
    GROUP_CONCAT(lfs.source_type || ':' || lfs.source_name, ', ') as source_list,
    COUNT(lfs.id) as source_count
FROM library_files lf
LEFT JOIN library_file_sources lfs ON lf.checksum = lfs.file_checksum
GROUP BY lf.checksum;

-- Migration notes:
-- 1. This migration creates new tables for the library system
-- 2. Old 'files' table is preserved for backwards compatibility
-- 3. A separate migration script will handle data migration from files -> library_files
-- 4. The library system can run in parallel with the old system during transition
