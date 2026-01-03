-- Migration: 022_slicer_integration.sql
-- Description: Add tables for command-line slicer integration (PrusaSlicer, BambuStudio)
-- Purpose: Enable direct slicing of 3D models from library with profile management
-- Date: 2026-01-03

-- =====================================================
-- SLICER CONFIGURATIONS TABLE
-- Stores detected slicer installations
-- =====================================================
CREATE TABLE IF NOT EXISTS slicer_configs (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    slicer_type TEXT NOT NULL CHECK (
        slicer_type IN ('prusaslicer', 'bambustudio', 'orcaslicer', 'superslicer')
    ),
    executable_path TEXT NOT NULL,
    version TEXT,
    config_dir TEXT,
    is_available BOOLEAN DEFAULT 1 NOT NULL,
    last_verified TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_slicer_configs_type ON slicer_configs(slicer_type);
CREATE INDEX IF NOT EXISTS idx_slicer_configs_available ON slicer_configs(is_available);

-- =====================================================
-- SLICER PROFILES TABLE
-- Stores imported slicer profiles (print/filament/printer presets)
-- =====================================================
CREATE TABLE IF NOT EXISTS slicer_profiles (
    id TEXT PRIMARY KEY NOT NULL,
    slicer_id TEXT NOT NULL REFERENCES slicer_configs(id) ON DELETE CASCADE,
    profile_name TEXT NOT NULL,
    profile_type TEXT NOT NULL CHECK (
        profile_type IN ('print', 'filament', 'printer', 'bundle')
    ),
    profile_path TEXT,
    settings_json TEXT,
    compatible_printers TEXT,
    is_default BOOLEAN DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(slicer_id, profile_name, profile_type)
);

CREATE INDEX IF NOT EXISTS idx_slicer_profiles_slicer_id ON slicer_profiles(slicer_id);
CREATE INDEX IF NOT EXISTS idx_slicer_profiles_type ON slicer_profiles(profile_type);
CREATE INDEX IF NOT EXISTS idx_slicer_profiles_default ON slicer_profiles(is_default);

-- =====================================================
-- SLICING JOBS TABLE
-- Tracks slicing operations and their progress
-- =====================================================
CREATE TABLE IF NOT EXISTS slicing_jobs (
    id TEXT PRIMARY KEY NOT NULL,
    file_checksum TEXT NOT NULL REFERENCES library_files(checksum) ON DELETE CASCADE,
    slicer_id TEXT NOT NULL REFERENCES slicer_configs(id) ON DELETE CASCADE,
    profile_id TEXT NOT NULL REFERENCES slicer_profiles(id) ON DELETE CASCADE,
    target_printer_id TEXT REFERENCES printers(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'queued' CHECK (
        status IN ('queued', 'running', 'completed', 'failed', 'cancelled')
    ),
    priority INTEGER DEFAULT 5 NOT NULL,
    progress INTEGER DEFAULT 0 NOT NULL CHECK (progress >= 0 AND progress <= 100),
    output_file_path TEXT,
    output_gcode_checksum TEXT,
    estimated_print_time INTEGER,
    filament_used REAL,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0 NOT NULL,
    auto_upload BOOLEAN DEFAULT 0 NOT NULL,
    auto_start BOOLEAN DEFAULT 0 NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_slicing_jobs_status ON slicing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_slicing_jobs_file ON slicing_jobs(file_checksum);
CREATE INDEX IF NOT EXISTS idx_slicing_jobs_printer ON slicing_jobs(target_printer_id);
CREATE INDEX IF NOT EXISTS idx_slicing_jobs_created ON slicing_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_slicing_jobs_priority_status ON slicing_jobs(priority DESC, status);

-- =====================================================
-- INSERT DEFAULT CONFIGURATION VALUES
-- =====================================================
INSERT OR IGNORE INTO configuration (key, value, value_type, category, description) VALUES
('slicing.enabled', 'true', 'boolean', 'slicing', 'Enable slicer integration feature'),
('slicing.max_concurrent', '2', 'integer', 'slicing', 'Maximum concurrent slicing jobs'),
('slicing.output_dir', '/data/printernizer/sliced', 'string', 'slicing', 'Directory for sliced G-code output'),
('slicing.cleanup_days', '7', 'integer', 'slicing', 'Days to keep sliced files before cleanup'),
('slicing.auto_retry', 'true', 'boolean', 'slicing', 'Automatically retry failed slicing jobs'),
('slicing.max_retries', '3', 'integer', 'slicing', 'Maximum retry attempts for failed jobs'),
('slicing.timeout_seconds', '3600', 'integer', 'slicing', 'Slicing job timeout in seconds'),
('slicing.auto_detect', 'true', 'boolean', 'slicing', 'Auto-detect slicers on startup');
