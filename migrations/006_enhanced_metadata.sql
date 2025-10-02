-- Migration: 006_enhanced_metadata.sql
-- Add enhanced metadata columns to files table for comprehensive 3D model information
-- Feature: METADATA-001 - Enhanced 3D Model Metadata Display
-- Version: v1.2.0

-- Physical Properties
ALTER TABLE files ADD COLUMN model_width DECIMAL(8,3);
ALTER TABLE files ADD COLUMN model_depth DECIMAL(8,3); 
ALTER TABLE files ADD COLUMN model_height DECIMAL(8,3);
ALTER TABLE files ADD COLUMN model_volume DECIMAL(10,3);
ALTER TABLE files ADD COLUMN surface_area DECIMAL(10,3);
ALTER TABLE files ADD COLUMN object_count INTEGER DEFAULT 1;

-- Print Settings
ALTER TABLE files ADD COLUMN nozzle_diameter DECIMAL(3,2);
ALTER TABLE files ADD COLUMN wall_count INTEGER;
ALTER TABLE files ADD COLUMN wall_thickness DECIMAL(4,2);
ALTER TABLE files ADD COLUMN infill_pattern VARCHAR(50);
ALTER TABLE files ADD COLUMN first_layer_height DECIMAL(4,3);

-- Material Information
ALTER TABLE files ADD COLUMN total_filament_weight DECIMAL(8,3);
ALTER TABLE files ADD COLUMN filament_length DECIMAL(10,2);
ALTER TABLE files ADD COLUMN filament_colors TEXT; -- JSON array
ALTER TABLE files ADD COLUMN waste_weight DECIMAL(8,3);

-- Cost Analysis
ALTER TABLE files ADD COLUMN material_cost DECIMAL(8,2);
ALTER TABLE files ADD COLUMN energy_cost DECIMAL(6,2);
ALTER TABLE files ADD COLUMN total_cost DECIMAL(8,2);

-- Quality Metrics
ALTER TABLE files ADD COLUMN complexity_score INTEGER;
ALTER TABLE files ADD COLUMN success_probability DECIMAL(3,2);
ALTER TABLE files ADD COLUMN difficulty_level VARCHAR(20);
ALTER TABLE files ADD COLUMN overhang_percentage DECIMAL(5,2);

-- Compatibility
ALTER TABLE files ADD COLUMN compatible_printers TEXT; -- JSON array
ALTER TABLE files ADD COLUMN slicer_name VARCHAR(100);
ALTER TABLE files ADD COLUMN slicer_version VARCHAR(50);
ALTER TABLE files ADD COLUMN profile_name VARCHAR(100);

-- Metadata timestamp
ALTER TABLE files ADD COLUMN last_analyzed TIMESTAMP;

-- Create flexible metadata storage table for additional properties
CREATE TABLE IF NOT EXISTS file_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    data_type VARCHAR(20) DEFAULT 'string',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE(file_id, category, key)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_file_metadata_file_id ON file_metadata(file_id);
CREATE INDEX IF NOT EXISTS idx_file_metadata_category ON file_metadata(category);
CREATE INDEX IF NOT EXISTS idx_files_complexity ON files(complexity_score);
CREATE INDEX IF NOT EXISTS idx_files_dimensions ON files(model_width, model_depth, model_height);
CREATE INDEX IF NOT EXISTS idx_files_cost ON files(total_cost);
CREATE INDEX IF NOT EXISTS idx_files_analyzed ON files(last_analyzed);
