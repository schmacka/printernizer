-- Migration: 040_api_keys.sql
-- Description: API keys for authenticating Printernizer Connect (the PrusaSlicer
--              companion) against the /api/v1/connect endpoints. Only the SHA-256
--              hash of a key is stored; the plaintext is shown to the user once.
-- Date: 2026-09-06

CREATE TABLE IF NOT EXISTS api_keys (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    key_hash     TEXT NOT NULL UNIQUE,
    created_at   TEXT NOT NULL,
    last_used_at TEXT
);

-- No separate index on key_hash: the UNIQUE constraint already creates one.
