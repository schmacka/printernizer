-- Migration: Add timelapses table
-- Date: 2025-01-07
-- Description: Create timelapses table for timelapse management system

CREATE TABLE IF NOT EXISTS timelapses (
    -- Primary key
    id TEXT PRIMARY KEY,

    -- Paths
    source_folder TEXT NOT NULL,
    output_video_path TEXT,

    -- Status tracking
    status TEXT NOT NULL,

    -- Job linking
    job_id TEXT,

    -- Metadata
    folder_name TEXT NOT NULL,
    image_count INTEGER,
    video_duration REAL,
    file_size_bytes INTEGER,

    -- Processing tracking
    processing_started_at TEXT,
    processing_completed_at TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Auto-detection
    last_image_detected_at TEXT,
    auto_process_eligible_at TEXT,

    -- Management
    pinned INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_timelapses_status ON timelapses(status);
CREATE INDEX IF NOT EXISTS idx_timelapses_job_id ON timelapses(job_id);
CREATE INDEX IF NOT EXISTS idx_timelapses_created_at ON timelapses(created_at);
