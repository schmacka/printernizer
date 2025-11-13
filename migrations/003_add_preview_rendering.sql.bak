-- Migration: Add preview rendering support
-- Date: 2025-01-01
-- Description: Add thumbnail_source column and preview rendering configuration

-- Add thumbnail_source column to track origin of thumbnails
ALTER TABLE files ADD COLUMN thumbnail_source TEXT DEFAULT 'embedded';
-- Values: 'embedded' (extracted from file), 'generated' (rendered), 'placeholder' (fallback icon)

-- Add index for querying by thumbnail source
CREATE INDEX idx_files_thumbnail_source ON files(thumbnail_source);

-- Add preview rendering configuration
INSERT OR IGNORE INTO configuration (key, value, value_type, category, description) VALUES
('preview_rendering.enabled', 'true', 'boolean', 'files', 'Enable 3D preview rendering for files without embedded thumbnails'),
('preview_rendering.cache_dir', 'data/preview-cache', 'string', 'files', 'Directory for caching generated preview images'),
('preview_rendering.cache_duration_days', '30', 'integer', 'files', 'Number of days to cache generated previews'),
('preview_rendering.render_timeout', '10', 'integer', 'files', 'Maximum time in seconds for rendering a single preview'),
('preview_rendering.stl_camera_azimuth', '45', 'integer', 'files', 'Camera azimuth angle for STL rendering'),
('preview_rendering.stl_camera_elevation', '45', 'integer', 'files', 'Camera elevation angle for STL rendering'),
('preview_rendering.stl_background_color', '#ffffff', 'string', 'files', 'Background color for STL renders'),
('preview_rendering.stl_face_color', '#6c757d', 'string', 'files', 'Face color for STL renders'),
('preview_rendering.gcode_rendering_enabled', 'false', 'boolean', 'files', 'Enable G-code toolpath visualization rendering');

-- Update existing rows to have 'embedded' source by default
UPDATE files SET thumbnail_source = 'embedded' WHERE thumbnail_source IS NULL AND has_thumbnail = 1;
