"""
API key generation and verification for Printernizer Connect.

Keys are 32 random url-safe bytes behind a `pk_` prefix. Only the SHA-256 hash
is persisted; the plaintext is returned exactly once, at creation.

A fast hash is deliberate: keys are high-entropy values we generate, not
user-chosen passwords, so there is nothing for a slow KDF to defend against and
verification runs on every companion request.
"""
import hashlib
import secrets
import uuid
from typing import Any, Dict, List, Optional, Tuple

import structlog

from src.database.repositories.api_key_repository import ApiKeyRepository

logger = structlog.get_logger()

KEY_PREFIX = "pk_"
_KEY_BYTES = 32


def hash_key(key: str) -> str:
    """Return the storage hash for a plaintext key."""
    return hashlib.sha256(key.encode()).hexdigest()


class ApiKeyService:
    """Creates, verifies and revokes API keys."""

    def __init__(self, repository: ApiKeyRepository):
        self.repository = repository

    async def create_key(self, name: str) -> Tuple[str, Dict[str, Any]]:
        """
        Create a new API key.

        Returns:
            (plaintext_key, record) — the plaintext is not recoverable later.
        """
        plaintext = KEY_PREFIX + secrets.token_urlsafe(_KEY_BYTES)
        key_id = str(uuid.uuid4())

        await self.repository.create(key_id, name, hash_key(plaintext))

        record = await self.repository.get_by_hash(hash_key(plaintext))
        if record is None:
            # The row was just written; a miss means the write silently failed.
            record = {"id": key_id, "name": name,
                      "created_at": None, "last_used_at": None}
        return plaintext, _without_hash(record)

    async def verify(self, key: Optional[str]) -> Optional[Dict[str, Any]]:
        """Return the key record if `key` is valid, else None. Touches on success."""
        if not key:
            return None

        record = await self.repository.get_by_hash(hash_key(key))
        if record is None:
            return None

        await self.repository.touch(record["id"])
        return _without_hash(record)

    async def list_keys(self) -> List[Dict[str, Any]]:
        """Return all keys, without their hashes."""
        return [_without_hash(r) for r in await self.repository.list_keys()]

    async def delete_key(self, key_id: str) -> bool:
        """Revoke a key. Returns True if it existed."""
        return await self.repository.delete(key_id)


def _without_hash(record: Dict[str, Any]) -> Dict[str, Any]:
    """Copy a record with the hash removed — hashes never leave this module."""
    return {k: v for k, v in record.items() if k != "key_hash"}
