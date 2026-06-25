-- Migration: 034_slicer_backends.sql
-- Description: Add pluggable backend fields to slicer_configs (remote slicer service)
-- Purpose: Allow a slicer config to point at a remote slicer microservice instead
--          of a locally-installed slicer binary.
-- Date: 2026-06-24

ALTER TABLE slicer_configs ADD COLUMN backend_type TEXT NOT NULL DEFAULT 'local';
ALTER TABLE slicer_configs ADD COLUMN endpoint_url TEXT;

CREATE INDEX IF NOT EXISTS idx_slicer_configs_backend ON slicer_configs(backend_type);
