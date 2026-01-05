-- Migration: 023_add_file_tags.sql
-- Description: Add tagging system for library files
-- Purpose: Enable users to organize files with custom tags for filtering and categorization
-- Date: 2026-01-05

-- =====================================================
-- FILE TAGS TABLE
-- Stores tag definitions with metadata
-- =====================================================
CREATE TABLE IF NOT EXISTS file_tags (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    color TEXT DEFAULT '#6b7280',           -- Hex color for visual display
    description TEXT,
    usage_count INTEGER DEFAULT 0 NOT NULL, -- Denormalized count for performance
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_file_tags_name ON file_tags(name);
CREATE INDEX IF NOT EXISTS idx_file_tags_usage ON file_tags(usage_count DESC);

-- =====================================================
-- FILE TAG ASSIGNMENTS TABLE
-- Junction table linking files to tags (many-to-many)
-- =====================================================
CREATE TABLE IF NOT EXISTS file_tag_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_checksum TEXT NOT NULL REFERENCES library_files(checksum) ON DELETE CASCADE,
    tag_id TEXT NOT NULL REFERENCES file_tags(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(file_checksum, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_file_tag_assignments_file ON file_tag_assignments(file_checksum);
CREATE INDEX IF NOT EXISTS idx_file_tag_assignments_tag ON file_tag_assignments(tag_id);

-- =====================================================
-- INSERT DEFAULT TAGS
-- Provide commonly useful starter tags
-- =====================================================
INSERT OR IGNORE INTO file_tags (id, name, color, description) VALUES
('tag_functional', 'Functional', '#22c55e', 'Functional prints and tools'),
('tag_decorative', 'Decorative', '#a855f7', 'Decorative items and art'),
('tag_gift', 'Gift', '#f97316', 'Items to gift to others'),
('tag_prototype', 'Prototype', '#3b82f6', 'Test prints and prototypes'),
('tag_business', 'Business', '#eab308', 'Business/commercial orders'),
('tag_personal', 'Personal', '#06b6d4', 'Personal projects'),
('tag_favorite', 'Favorite', '#ef4444', 'Favorite models');

-- =====================================================
-- TRIGGER: Update usage_count on assignment
-- =====================================================
CREATE TRIGGER IF NOT EXISTS update_tag_usage_on_insert
AFTER INSERT ON file_tag_assignments
BEGIN
    UPDATE file_tags
    SET usage_count = usage_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.tag_id;
END;

CREATE TRIGGER IF NOT EXISTS update_tag_usage_on_delete
AFTER DELETE ON file_tag_assignments
BEGIN
    UPDATE file_tags
    SET usage_count = CASE WHEN usage_count > 0 THEN usage_count - 1 ELSE 0 END,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.tag_id;
END;
