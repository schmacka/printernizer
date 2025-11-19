"""
Tests for Database Connection Pooling (Phase 3 Technical Debt)

This test suite verifies that the connection pooling implementation from Phase 3
works correctly:
- Connection pool initialization
- Connection acquisition and release
- Pooled connection context manager
- Concurrent access handling
- Pool cleanup on shutdown
- WAL mode configuration

Related to Phase 3 Task 3.5: Implement Database Connection Pooling
"""
import pytest
import asyncio
import aiosqlite
from pathlib import Path

from src.database.database import Database


class TestConnectionPoolInitialization:
    """Test connection pool initialization and configuration"""

    @pytest.mark.asyncio
    async def test_pool_initialization(self, temp_database):
        """Verify that connection pool is initialized correctly"""
        db = Database(temp_database, pool_size=3)
        await db.initialize()

        # Verify pool exists and has correct size
        assert db._pool is not None
        assert db._pool.maxsize == 3
        assert db._pool_semaphore is not None
        assert db._pool_semaphore._value == 3

        await db.close()

    @pytest.mark.asyncio
    async def test_pool_default_size(self, temp_database):
        """Verify default pool size is 5"""
        db = Database(temp_database)
        await db.initialize()

        assert db._pool.maxsize == 5

        await db.close()

    @pytest.mark.asyncio
    async def test_wal_mode_enabled(self, temp_database):
        """Verify that WAL mode is enabled for concurrent reads"""
        db = Database(temp_database)
        await db.initialize()

        # Acquire a connection and check WAL mode
        conn = await db.acquire_connection()

        cursor = await conn.execute("PRAGMA journal_mode")
        row = await cursor.fetchone()
        journal_mode = row[0]

        assert journal_mode.upper() == 'WAL'

        await db.release_connection(conn)
        await db.close()

    @pytest.mark.asyncio
    async def test_synchronous_mode_normal(self, temp_database):
        """Verify that synchronous mode is set to NORMAL for performance"""
        db = Database(temp_database)
        await db.initialize()

        conn = await db.acquire_connection()

        cursor = await conn.execute("PRAGMA synchronous")
        row = await cursor.fetchone()
        synchronous = row[0]

        # NORMAL = 1
        assert synchronous == 1

        await db.release_connection(conn)
        await db.close()


class TestConnectionAcquisition:
    """Test connection acquisition and release"""

    @pytest.mark.asyncio
    async def test_acquire_connection(self, temp_database):
        """Test basic connection acquisition"""
        db = Database(temp_database)
        await db.initialize()

        # Acquire a connection
        conn = await db.acquire_connection()

        assert conn is not None
        assert isinstance(conn, aiosqlite.Connection)

        await db.release_connection(conn)
        await db.close()

    @pytest.mark.asyncio
    async def test_release_connection(self, temp_database):
        """Test connection release returns connection to pool"""
        db = Database(temp_database, pool_size=2)
        await db.initialize()

        # Pool should have 2 connections available
        assert db._pool.qsize() == 2

        # Acquire a connection
        conn = await db.acquire_connection()

        # Pool should have 1 connection available
        assert db._pool.qsize() == 1

        # Release it back
        await db.release_connection(conn)

        # Pool should have 2 connections available again
        assert db._pool.qsize() == 2

        await db.close()

    @pytest.mark.asyncio
    async def test_acquire_multiple_connections(self, temp_database):
        """Test acquiring multiple connections from pool"""
        db = Database(temp_database, pool_size=3)
        await db.initialize()

        connections = []

        # Acquire 3 connections (all from pool)
        for _ in range(3):
            conn = await db.acquire_connection()
            connections.append(conn)
            assert conn is not None

        # Pool should be empty now
        assert db._pool.qsize() == 0

        # Release all connections
        for conn in connections:
            await db.release_connection(conn)

        # Pool should have all 3 back
        assert db._pool.qsize() == 3

        await db.close()

    @pytest.mark.asyncio
    async def test_pool_exhaustion_blocks(self, temp_database):
        """Test that pool exhaustion causes waiting (not immediate failure)"""
        db = Database(temp_database, pool_size=2)
        await db.initialize()

        # Acquire all connections
        conn1 = await db.acquire_connection()
        conn2 = await db.acquire_connection()

        # Pool is now exhausted
        assert db._pool.qsize() == 0

        # Try to acquire another connection with timeout
        # This should block and timeout
        try:
            conn3 = await asyncio.wait_for(
                db.acquire_connection(),
                timeout=0.5
            )
            # If we got here, release it
            await db.release_connection(conn3)
            # This should not happen with our pool implementation
            pytest.fail("Should have timed out waiting for connection")
        except asyncio.TimeoutError:
            # Expected behavior - pool is exhausted
            pass

        # Release one connection
        await db.release_connection(conn1)

        # Now acquisition should work
        conn3 = await db.acquire_connection()
        assert conn3 is not None

        await db.release_connection(conn2)
        await db.release_connection(conn3)
        await db.close()


class TestPooledConnectionContextManager:
    """Test the pooled_connection() context manager"""

    @pytest.mark.asyncio
    async def test_pooled_connection_basic(self, temp_database):
        """Test basic pooled_connection() usage"""
        db = Database(temp_database)
        await db.initialize()

        # Use context manager
        async with db.pooled_connection() as conn:
            assert conn is not None
            assert isinstance(conn, aiosqlite.Connection)

            # Should be able to execute queries
            cursor = await conn.execute("SELECT 1")
            row = await cursor.fetchone()
            assert row[0] == 1

        # Connection should be released back to pool
        assert db._pool.qsize() == 5  # default pool size

        await db.close()

    @pytest.mark.asyncio
    async def test_pooled_connection_auto_release(self, temp_database):
        """Test that pooled_connection automatically releases on exit"""
        db = Database(temp_database, pool_size=1)
        await db.initialize()

        initial_size = db._pool.qsize()
        assert initial_size == 1

        async with db.pooled_connection() as conn:
            # Connection is acquired
            assert db._pool.qsize() == 0

        # Connection should be released automatically
        assert db._pool.qsize() == 1

        await db.close()

    @pytest.mark.asyncio
    async def test_pooled_connection_exception_handling(self, temp_database):
        """Test that pooled_connection releases connection even on exception"""
        db = Database(temp_database, pool_size=1)
        await db.initialize()

        try:
            async with db.pooled_connection() as conn:
                # Raise an exception
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # Connection should still be released
        assert db._pool.qsize() == 1

        await db.close()

    @pytest.mark.asyncio
    async def test_nested_pooled_connections(self, temp_database):
        """Test multiple nested pooled connections"""
        db = Database(temp_database, pool_size=3)
        await db.initialize()

        async with db.pooled_connection() as conn1:
            assert db._pool.qsize() == 2

            async with db.pooled_connection() as conn2:
                assert db._pool.qsize() == 1

                # Both connections should be different
                assert conn1 is not conn2

                # Both should work
                cursor1 = await conn1.execute("SELECT 1")
                cursor2 = await conn2.execute("SELECT 2")

                row1 = await cursor1.fetchone()
                row2 = await cursor2.fetchone()

                assert row1[0] == 1
                assert row2[0] == 2

            # conn2 released
            assert db._pool.qsize() == 2

        # conn1 released
        assert db._pool.qsize() == 3

        await db.close()


class TestConcurrentAccess:
    """Test concurrent database access with connection pool"""

    @pytest.mark.asyncio
    async def test_concurrent_reads(self, temp_database):
        """Test concurrent read operations using pool"""
        db = Database(temp_database, pool_size=5)
        await db.initialize()

        # Create some test data
        await db.create_printer({
            'id': 'printer_concurrent',
            'name': 'Concurrent Test Printer',
            'type': 'bambu_lab'
        })

        # Function to read data
        async def read_data():
            async with db.pooled_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM printers WHERE id = ?",
                    ('printer_concurrent',)
                )
                row = await cursor.fetchone()
                return row is not None

        # Run 10 concurrent reads
        tasks = [read_data() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results)
        assert len(results) == 10

        await db.close()

    @pytest.mark.asyncio
    async def test_concurrent_writes_with_pool(self, temp_database):
        """Test that concurrent writes work with connection pool"""
        db = Database(temp_database, pool_size=5)
        await db.initialize()

        # Function to write data
        async def write_data(index):
            async with db.pooled_connection() as conn:
                await conn.execute(
                    "INSERT INTO printers (id, name, type) VALUES (?, ?, ?)",
                    (f'printer_{index}', f'Printer {index}', 'bambu_lab')
                )
                await conn.commit()
                return index

        # Run 5 concurrent writes
        tasks = [write_data(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All should complete
        assert len(results) == 5

        # Verify all data was written
        async with db.pooled_connection() as conn:
            cursor = await conn.execute("SELECT COUNT(*) FROM printers")
            row = await cursor.fetchone()
            assert row[0] >= 5

        await db.close()

    @pytest.mark.asyncio
    async def test_pool_prevents_deadlock(self, temp_database):
        """Test that pool size prevents resource deadlock"""
        db = Database(temp_database, pool_size=3)
        await db.initialize()

        completed_tasks = 0

        async def slow_operation(index):
            nonlocal completed_tasks
            async with db.pooled_connection() as conn:
                await asyncio.sleep(0.1)  # Simulate slow operation
                cursor = await conn.execute("SELECT 1")
                await cursor.fetchone()
                completed_tasks += 1
                return index

        # Run 10 operations (more than pool size)
        tasks = [slow_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All should complete (no deadlock)
        assert len(results) == 10
        assert completed_tasks == 10

        await db.close()


class TestPoolCleanup:
    """Test connection pool cleanup on shutdown"""

    @pytest.mark.asyncio
    async def test_close_cleans_up_pool(self, temp_database):
        """Test that close() properly cleans up all pool connections"""
        db = Database(temp_database, pool_size=3)
        await db.initialize()

        # Pool should have 3 connections
        assert db._pool.qsize() == 3

        # Close database
        await db.close()

        # Pool should be empty
        assert db._pool.qsize() == 0

    @pytest.mark.asyncio
    async def test_close_with_active_connections(self, temp_database):
        """Test close() when some connections are in use"""
        db = Database(temp_database, pool_size=2)
        await db.initialize()

        # Acquire a connection
        conn = await db.acquire_connection()

        # Close database (should still work)
        await db.close()

        # Pool should be cleaned up
        assert db._pool.qsize() == 0

        # The active connection should still be open for cleanup
        # but we won't return it to the pool


class TestBackwardCompatibility:
    """Test that pooling doesn't break existing code"""

    @pytest.mark.asyncio
    async def test_existing_database_methods_work(self, temp_database):
        """Test that existing Database methods still work with pooling"""
        db = Database(temp_database)
        await db.initialize()

        # Test legacy methods still work
        printer_id = await db.create_printer({
            'id': 'printer_legacy',
            'name': 'Legacy Test',
            'type': 'bambu_lab'
        })

        assert printer_id is not None

        # Test retrieval
        printer = await db.get_printer('printer_legacy')
        assert printer is not None
        assert printer['name'] == 'Legacy Test'

        await db.close()


# =====================================================
# Run marker for pytest
# =====================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
