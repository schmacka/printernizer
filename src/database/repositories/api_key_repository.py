"""
Repository for API key records.

Stores only the SHA-256 hash of each key. Generation, hashing and verification
live in `src.services.api_key_service` — this class is pure storage.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from .base_repository import BaseRepository

logger = structlog.get_logger()


class ApiKeyRepository(BaseRepository):
    """Storage for API keys used by Printernizer Connect."""

    async def create(self, key_id: str, name: str, key_hash: str) -> bool:
        """Insert a new API key record. Returns True on success."""
        await self._execute_write(
            """
            INSERT INTO api_keys (id, name, key_hash, created_at, last_used_at)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (key_id, name, key_hash, datetime.now(timezone.utc).isoformat()),
        )
        logger.info("API key created", key_id=key_id, name=name)
        return True

    async def list_keys(self) -> List[Dict[str, Any]]:
        """Return all API key records, newest first."""
        return await self._fetch_all(
            "SELECT id, name, key_hash, created_at, last_used_at "
            "FROM api_keys ORDER BY created_at DESC"
        )

    async def get_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Look up a key record by its hash, or None."""
        return await self._fetch_one(
            "SELECT id, name, key_hash, created_at, last_used_at "
            "FROM api_keys WHERE key_hash = ?",
            [key_hash],
        )

    async def touch(self, key_id: str) -> bool:
        """Record that a key was just used. Returns True if the key exists."""
        existing = await self._fetch_one(
            "SELECT id FROM api_keys WHERE id = ?", [key_id]
        )
        if existing is None:
            return False
        await self._execute_write(
            "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), key_id),
        )
        return True

    async def delete(self, key_id: str) -> bool:
        """Delete a key. Returns True if it existed."""
        existing = await self._fetch_one(
            "SELECT id FROM api_keys WHERE id = ?", [key_id]
        )
        if existing is None:
            return False
        await self._execute_write("DELETE FROM api_keys WHERE id = ?", (key_id,))
        logger.info("API key deleted", key_id=key_id)
        return True
