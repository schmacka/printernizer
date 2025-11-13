-- Migration: 018_add_triggers.sql
-- Add automatic timestamp update triggers and event logging
-- Priority: MINOR
-- Date: 2025-11-13

-- Timestamp update triggers
CREATE TRIGGER IF NOT EXISTS trg_printers_updated_at 
    AFTER UPDATE ON printers
BEGIN
    UPDATE printers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_jobs_updated_at 
    AFTER UPDATE ON jobs
BEGIN
    UPDATE jobs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_watch_folders_updated_at 
    AFTER UPDATE ON watch_folders
BEGIN
    UPDATE watch_folders SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_configuration_updated_at 
    AFTER UPDATE ON configuration
BEGIN
    UPDATE configuration SET updated_at = CURRENT_TIMESTAMP WHERE key = NEW.key;
END;

CREATE TRIGGER IF NOT EXISTS trg_collections_updated_at 
    AFTER UPDATE ON collections
BEGIN
    UPDATE collections SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_materials_updated_at 
    AFTER UPDATE ON materials
BEGIN
    UPDATE materials SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_ideas_updated_at 
    AFTER UPDATE ON ideas
BEGIN
    UPDATE ideas SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Job status change logging trigger (requires system_events table)
CREATE TRIGGER IF NOT EXISTS trg_job_status_change 
    AFTER UPDATE OF status ON jobs
WHEN NEW.status != OLD.status
BEGIN
    INSERT INTO system_events (event_type, severity, title, description, printer_id, job_id)
    VALUES (
        CASE NEW.status
            WHEN 'completed' THEN 'job_complete'
            WHEN 'failed' THEN 'job_fail'
            WHEN 'printing' THEN 'job_start'
            ELSE 'info'
        END,
        CASE NEW.status
            WHEN 'failed' THEN 'error'
            ELSE 'info'
        END,
        'Job Status Changed: ' || NEW.job_name,
        'Status changed from ' || OLD.status || ' to ' || NEW.status,
        NEW.printer_id,
        NEW.id
    );
END;
