-- Migration: 032_add_openscad_tables
-- Description: Add tables for the OpenSCAD generator module (renders and presets)
-- Date: 2026-06-13

CREATE TABLE IF NOT EXISTS openscad_renders (
    id TEXT PRIMARY KEY NOT NULL,
    source_ref TEXT NOT NULL,           -- template id or uploaded source id
    parameters TEXT,                    -- JSON of parameter overrides
    format TEXT NOT NULL DEFAULT 'stl', -- 'stl' or 'png'
    status TEXT NOT NULL DEFAULT 'pending',
    work_dir TEXT,                      -- isolated working directory
    model_path TEXT,                    -- path to rendered STL
    preview_path TEXT,                  -- path to rendered PNG
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_openscad_renders_source ON openscad_renders(source_ref);
CREATE INDEX IF NOT EXISTS idx_openscad_renders_created ON openscad_renders(created_at);

CREATE TABLE IF NOT EXISTS openscad_presets (
    id TEXT PRIMARY KEY NOT NULL,
    template_id TEXT NOT NULL,
    name TEXT NOT NULL,
    parameters TEXT,                    -- JSON of parameter values
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_openscad_presets_template ON openscad_presets(template_id);
