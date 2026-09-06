"""Tests for ApiKeyRepository — storage and lookup of API key records."""
import pytest

from src.database.repositories.api_key_repository import ApiKeyRepository


@pytest.fixture
async def repo(async_database):
    """ApiKeyRepository bound to a real temporary database."""
    return ApiKeyRepository(async_database.get_connection())


class TestApiKeyRepository:
    async def test_create_then_get_by_hash(self, repo):
        created = await repo.create("key1", "My laptop", "hash-aaa")
        assert created is True

        row = await repo.get_by_hash("hash-aaa")
        assert row is not None
        assert row["id"] == "key1"
        assert row["name"] == "My laptop"
        assert row["last_used_at"] is None

    async def test_get_by_hash_returns_none_when_unknown(self, repo):
        assert await repo.get_by_hash("nope") is None

    async def test_list_keys_returns_all_without_hashes_stripped(self, repo):
        await repo.create("key1", "Laptop", "hash-aaa")
        await repo.create("key2", "Workshop PC", "hash-bbb")

        keys = await repo.list_keys()
        assert {k["id"] for k in keys} == {"key1", "key2"}

    async def test_touch_sets_last_used_at(self, repo):
        await repo.create("key1", "Laptop", "hash-aaa")
        assert await repo.touch("key1") is True

        row = await repo.get_by_hash("hash-aaa")
        assert row["last_used_at"] is not None

    async def test_delete_removes_the_key(self, repo):
        await repo.create("key1", "Laptop", "hash-aaa")
        assert await repo.delete("key1") is True
        assert await repo.get_by_hash("hash-aaa") is None

    async def test_delete_returns_false_for_unknown_key(self, repo):
        assert await repo.delete("ghost") is False
