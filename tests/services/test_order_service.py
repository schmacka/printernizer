"""Tests for OrderService and OrderRepository."""
import pytest
import aiosqlite
from unittest.mock import AsyncMock, MagicMock, patch


# ── Integration fixtures (Task 1 only) ──────────────────────────────────────

ORDER_SOURCES_DDL = """
CREATE TABLE IF NOT EXISTS order_sources (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
"""


@pytest.fixture
async def real_db_connection():
    """In-memory SQLite connection with order_sources table created."""
    async with aiosqlite.connect(':memory:') as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute(ORDER_SOURCES_DDL)
        await conn.commit()
        yield conn


# ── Shared mock fixtures (used by Tasks 2–10) ────────────────────────────────

@pytest.fixture
def mock_order_repo():
    repo = MagicMock()
    repo.create_source = AsyncMock(return_value=True)
    repo.get_source = AsyncMock(return_value=None)
    repo.list_sources = AsyncMock(return_value=[])
    repo.update_source = AsyncMock(return_value=True)
    repo.delete_source = AsyncMock(return_value=True)
    repo.is_source_in_use = AsyncMock(return_value=False)
    repo.create_order = AsyncMock(return_value=True)
    repo.get_order = AsyncMock(return_value=None)
    repo.update_order = AsyncMock(return_value=True)
    repo.list_orders = AsyncMock(return_value=[])
    repo.count_orders = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def mock_customer_repo():
    repo = MagicMock()
    repo.list = AsyncMock(return_value=[])
    repo.get = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=True)
    repo.update = AsyncMock(return_value=True)
    repo.delete = AsyncMock(return_value=True)
    repo.get_order_count = AsyncMock(return_value=0)
    repo.get_orders_for_customer = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_database():
    db = MagicMock()
    db._connection = MagicMock()
    return db


@pytest.fixture
def order_service(mock_database, mock_order_repo, mock_customer_repo):
    from src.services.order_service import OrderService
    with patch('src.services.order_service.OrderRepository', return_value=mock_order_repo), \
         patch('src.services.order_service.CustomerRepository', return_value=mock_customer_repo):
        service = OrderService(mock_database)
        service.order_repo = mock_order_repo
        service.customer_repo = mock_customer_repo
        return service


# ── Task 1: Integration tests for repository SQL ─────────────────────────────

class TestCreateSourceSQL:
    @pytest.mark.asyncio
    async def test_create_source_succeeds_without_description(self, real_db_connection):
        """create_source() must not reference the non-existent description column."""
        from src.database.repositories.order_repository import OrderRepository
        repo = OrderRepository(real_db_connection)
        data = {
            'id': 'src-test-1',
            'name': 'Instagram',
            'is_active': True,
        }
        result = await repo.create_source(data)
        assert result is True, "create_source() failed — likely references a non-existent column"

    @pytest.mark.asyncio
    async def test_update_source_with_name_only_succeeds(self, real_db_connection):
        """update_source() allowed_fields must not reference description."""
        from src.database.repositories.order_repository import OrderRepository
        repo = OrderRepository(real_db_connection)
        # Insert a row first
        await repo.create_source({'id': 'src-upd-1', 'name': 'Old Name', 'is_active': True})
        # Update — if description is in allowed_fields and the column doesn't exist, this crashes
        result = await repo.update_source('src-upd-1', {'name': 'New Name'})
        assert result is True
