-- Migration: Add thumbnail support to files table
-- Date: 2024-01-01
-- Description: Add thumbnail fields for Bambu G-code and 3MF file thumbnails

-- Add thumbnail columns to files table
ALTER TABLE files ADD COLUMN has_thumbnail BOOLEAN DEFAULT 0 NOT NULL;
ALTER TABLE files ADD COLUMN thumbnail_data TEXT; -- Base64 encoded thumbnail
ALTER TABLE files ADD COLUMN thumbnail_width INTEGER;
ALTER TABLE files ADD COLUMN thumbnail_height INTEGER;
ALTER TABLE files ADD COLUMN thumbnail_format TEXT; -- 'png', 'jpg', etc.

-- Add index for thumbnail queries
CREATE INDEX idx_files_has_thumbnail ON files(has_thumbnail);

-- Update updated_at trigger to include new columns
-- (The existing trigger will handle this automatically)

-- Add example configuration for thumbnail processing
INSERT OR IGNORE INTO configuration (key, value, value_type, category, description) VALUES
('thumbnails.enabled', 'true', 'boolean', 'files', 'Enable thumbnail extraction from 3D files'),
('thumbnails.max_size_kb', '500', 'integer', 'files', 'Maximum thumbnail size in KB'),
('thumbnails.preferred_width', '200', 'integer', 'files', 'Preferred thumbnail width in pixels'),
('thumbnails.preferred_height', '200', 'integer', 'files', 'Preferred thumbnail height in pixels'),
('thumbnails.cache_lifetime_hours', '24', 'integer', 'files', 'Thumbnail cache lifetime in hours');