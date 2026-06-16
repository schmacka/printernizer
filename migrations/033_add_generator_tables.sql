-- Migration: 033_add_generator_tables
-- Description: Add tables for the build123d model generator (renders and presets)
-- Date: 2026-06-16
-- Note: numbered 033 (not 032) so databases that already applied the removed
--       032_add_openscad_tables migration still create the generator tables.

CREATE TABLE IF NOT EXISTS generator_renders (
    id TEXT PRIMARY KEY NOT NULL,
    template_id TEXT NOT NULL,          -- bundled template id
    parameters TEXT,                    -- JSON of parameter overrides
    format TEXT NOT NULL DEFAULT 'stl', -- 'stl' or 'png'
    status TEXT NOT NULL DEFAULT 'pending',
    work_dir TEXT,                      -- isolated working directory
    model_path TEXT,                    -- path to rendered STL
    preview_path TEXT,                  -- path to rendered PNG
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_generator_renders_template ON generator_renders(template_id);
CREATE INDEX IF NOT EXISTS idx_generator_renders_created ON generator_renders(created_at);

CREATE TABLE IF NOT EXISTS generator_presets (
    id TEXT PRIMARY KEY NOT NULL,
    template_id TEXT NOT NULL,
    name TEXT NOT NULL,
    parameters TEXT,                    -- JSON of parameter values
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_generator_presets_template ON generator_presets(template_id);
