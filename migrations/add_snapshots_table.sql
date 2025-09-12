-- =====================================================
-- Add Snapshots Table for Camera Integration
-- Migration to support printer camera snapshots
-- =====================================================

-- Snapshots table to store camera images linked to jobs
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    printer_id TEXT NOT NULL REFERENCES printers(id) ON DELETE CASCADE,
    
    -- Snapshot metadata
    filename TEXT NOT NULL,                  -- Generated filename for snapshot
    original_filename TEXT,                  -- Original filename if provided
    file_size INTEGER NOT NULL,             -- Image file size in bytes
    content_type TEXT DEFAULT 'image/jpeg', -- MIME type of image
    
    -- Storage details  
    storage_path TEXT NOT NULL,             -- Local filesystem path where image is stored
    
    -- Capture details
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    capture_trigger TEXT NOT NULL DEFAULT 'manual' CHECK (
        capture_trigger IN ('manual', 'auto', 'job_start', 'job_complete', 'job_failed')
    ),
    
    -- Image metadata
    width INTEGER,                          -- Image width in pixels
    height INTEGER,                         -- Image height in pixels
    
    -- Status and validation
    is_valid BOOLEAN DEFAULT 1,            -- Whether file exists and is valid
    validation_error TEXT,                 -- Error message if validation fails
    last_validated_at TIMESTAMP,           -- Last validation check
    
    -- Additional metadata
    metadata JSON,                         -- Additional structured data (camera settings, etc.)
    notes TEXT,                            -- User notes about snapshot
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for snapshots table
CREATE INDEX IF NOT EXISTS idx_snapshots_job_id ON snapshots(job_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_printer_id ON snapshots(printer_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_captured_at ON snapshots(captured_at);
CREATE INDEX IF NOT EXISTS idx_snapshots_trigger ON snapshots(capture_trigger);
CREATE INDEX IF NOT EXISTS idx_snapshots_printer_captured ON snapshots(printer_id, captured_at);

-- Trigger for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS trg_snapshots_updated_at 
    AFTER UPDATE ON snapshots
BEGIN
    UPDATE snapshots SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- View for snapshots with job and printer information
CREATE VIEW IF NOT EXISTS v_snapshots_with_context AS
SELECT 
    s.*,
    j.job_name,
    j.status as job_status,
    j.start_time as job_start_time,
    j.end_time as job_end_time,
    p.name as printer_name,
    p.type as printer_type
FROM snapshots s
LEFT JOIN jobs j ON s.job_id = j.id
JOIN printers p ON s.printer_id = p.id
ORDER BY s.captured_at DESC;

-- =====================================================
-- End of Migration
-- =====================================================