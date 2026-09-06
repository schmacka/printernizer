"""Tests for ApiKeyService — key generation, hashing and verification."""
import hashlib
from unittest.mock import AsyncMock

import pytest

from src.services.api_key_service import ApiKeyService, KEY_PREFIX


@pytest.fixture
def repo():
    """Repository double."""
    r = AsyncMock()
    r.create = AsyncMock(return_value=True)
    r.get_by_hash = AsyncMock(return_value=None)
    r.touch = AsyncMock(return_value=True)
    r.delete = AsyncMock(return_value=True)
    r.list_keys = AsyncMock(return_value=[])
    return r


@pytest.fixture
def service(repo):
    return ApiKeyService(repo)


class TestCreateKey:
    async def test_returns_plaintext_key_with_prefix(self, service):
        plaintext, record = await service.create_key("My laptop")
        assert plaintext.startswith(KEY_PREFIX)
        assert len(plaintext) > len(KEY_PREFIX) + 20
        assert record["name"] == "My laptop"

    async def test_stores_only_the_hash_never_the_plaintext(self, service, repo):
        plaintext, _ = await service.create_key("My laptop")

        repo.create.assert_awaited_once()
        _key_id, _name, stored_hash = repo.create.await_args.args
        assert stored_hash == hashlib.sha256(plaintext.encode()).hexdigest()
        assert plaintext not in stored_hash

    async def test_two_keys_differ(self, service):
        first, _ = await service.create_key("a")
        second, _ = await service.create_key("b")
        assert first != second

    async def test_returned_record_does_not_leak_the_hash(self, service):
        _plaintext, record = await service.create_key("My laptop")
        assert "key_hash" not in record


class TestVerify:
    async def test_returns_none_for_unknown_key(self, service):
        assert await service.verify("pk_nope") is None

    async def test_returns_none_for_empty_key(self, service, repo):
        assert await service.verify("") is None
        repo.get_by_hash.assert_not_awaited()

    async def test_returns_record_and_touches_on_success(self, service, repo):
        repo.get_by_hash.return_value = {
            "id": "key1", "name": "Laptop", "key_hash": "h",
            "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None,
        }

        record = await service.verify("pk_whatever")

        assert record["id"] == "key1"
        repo.touch.assert_awaited_once_with("key1")

    async def test_looks_up_by_hash_not_plaintext(self, service, repo):
        await service.verify("pk_secret")
        repo.get_by_hash.assert_awaited_once_with(
            hashlib.sha256(b"pk_secret").hexdigest()
        )


class TestListKeys:
    async def test_strips_hashes_from_listed_keys(self, service, repo):
        repo.list_keys.return_value = [
            {"id": "key1", "name": "Laptop", "key_hash": "secret-hash",
             "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None},
        ]

        keys = await service.list_keys()

        assert keys == [{
            "id": "key1", "name": "Laptop",
            "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None,
        }]
