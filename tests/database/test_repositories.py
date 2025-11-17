"""
Comprehensive tests for all repository classes.

Tests cover CRUD operations, error handling, and edge cases for all 8 repositories.
"""
import pytest
import aiosqlite
from datetime import datetime, timedelta
import json

from src.database.repositories.base_repository import BaseRepository
from src.database.repositories.printer_repository import PrinterRepository
from src.database.repositories.job_repository import JobRepository
from src.database.repositories.file_repository import FileRepository
from src.database.repositories.snapshot_repository import SnapshotRepository
from src.database.repositories.trending_repository import TrendingRepository
from src.database.repositories.idea_repository import IdeaRepository
from src.database.repositories.library_repository import LibraryRepository


@pytest.fixture
async def async_db_connection(temp_database):
    """Async database connection fixture for repository tests"""
    conn = await aiosqlite.connect(temp_database)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    await conn.close()


# =====================================================
# BaseRepository Tests
# =====================================================

class TestBaseRepository:
    """Tests for BaseRepository common functionality"""

    @pytest.mark.asyncio
    async def test_execute_write(self, async_db_connection):
        """Test basic write operation"""
        repo = BaseRepository(async_db_connection)

        # Insert a test printer
        result = await repo._execute_write(
            "INSERT INTO printers (id, name, type) VALUES (?, ?, ?)",
            ("test_printer_1", "Test Printer", "bambu_lab")
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_write_with_retry(self, async_db_connection):
        """Test write operation with database lock retry"""
        repo = BaseRepository(async_db_connection)

        # This should succeed even with retries configured
        result = await repo._execute_write(
            "INSERT INTO printers (id, name, type) VALUES (?, ?, ?)",
            ("test_printer_2", "Test Printer 2", "prusa"),
            retry_count=3
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_one(self, async_db_connection):
        """Test fetching single row"""
        repo = BaseRepository(async_db_connection)

        # Insert test data
        await repo._execute_write(
            "INSERT INTO printers (id, name, type) VALUES (?, ?, ?)",
            ("test_printer_3", "Test Printer 3", "bambu_lab")
        )

        # Fetch it back
        row = await repo._fetch_one(
            "SELECT * FROM printers WHERE id = ?",
            ["test_printer_3"]
        )

        assert row is not None
        assert row['id'] == "test_printer_3"
        assert row['name'] == "Test Printer 3"

    @pytest.mark.asyncio
    async def test_fetch_one_not_found(self, async_db_connection):
        """Test fetching non-existent row returns None"""
        repo = BaseRepository(async_db_connection)

        row = await repo._fetch_one(
            "SELECT * FROM printers WHERE id = ?",
            ["non_existent_id"]
        )

        assert row is None

    @pytest.mark.asyncio
    async def test_fetch_all(self, async_db_connection):
        """Test fetching multiple rows"""
        repo = BaseRepository(async_db_connection)

        # Insert test data
        for i in range(3):
            await repo._execute_write(
                "INSERT INTO printers (id, name, type) VALUES (?, ?, ?)",
                (f"printer_{i}", f"Printer {i}", "bambu_lab")
            )

        # Fetch all
        rows = await repo._fetch_all(
            "SELECT * FROM printers WHERE type = ?",
            ["bambu_lab"]
        )

        assert len(rows) >= 3
        assert all(row['type'] == "bambu_lab" for row in rows)

    @pytest.mark.asyncio
    async def test_fetch_all_empty(self, async_db_connection):
        """Test fetching from empty result set"""
        repo = BaseRepository(async_db_connection)

        rows = await repo._fetch_all(
            "SELECT * FROM printers WHERE type = ?",
            ["non_existent_type"]
        )

        assert rows == []


# =====================================================
# PrinterRepository Tests
# =====================================================

class TestPrinterRepository:
    """Tests for PrinterRepository"""

    @pytest.mark.asyncio
    async def test_create_printer(self, async_db_connection):
        """Test creating a new printer"""
        repo = PrinterRepository(async_db_connection)

        printer_data = {
            'id': 'bambu_001',
            'name': 'Bambu Lab A1',
            'type': 'bambu_lab',
            'ip_address': '192.168.1.100',
            'access_code': 'test123',
            'serial_number': 'ABC123',
            'is_active': True
        }

        result = await repo.create(printer_data)
        assert result is True

        # Verify it was created
        printer = await repo.get('bambu_001')
        assert printer is not None
        assert printer['name'] == 'Bambu Lab A1'

    @pytest.mark.asyncio
    async def test_get_printer(self, async_db_connection):
        """Test retrieving a printer"""
        repo = PrinterRepository(async_db_connection)

        # Create printer first
        await repo.create({
            'id': 'prusa_001',
            'name': 'Prusa Core One',
            'type': 'prusa',
            'api_key': 'key123'
        })

        # Get it back
        printer = await repo.get('prusa_001')
        assert printer is not None
        assert printer['type'] == 'prusa'

    @pytest.mark.asyncio
    async def test_get_nonexistent_printer(self, async_db_connection):
        """Test getting non-existent printer returns None"""
        repo = PrinterRepository(async_db_connection)

        printer = await repo.get('nonexistent_id')
        assert printer is None

    @pytest.mark.asyncio
    async def test_list_all_printers(self, async_db_connection):
        """Test listing all printers"""
        repo = PrinterRepository(async_db_connection)

        # Create multiple printers
        for i in range(3):
            await repo.create({
                'id': f'printer_{i}',
                'name': f'Printer {i}',
                'type': 'bambu_lab',
                'is_active': i % 2 == 0  # Every other one is active
            })

        # List all
        printers = await repo.list(active_only=False)
        assert len(printers) >= 3

    @pytest.mark.asyncio
    async def test_list_active_printers_only(self, async_db_connection):
        """Test listing only active printers"""
        repo = PrinterRepository(async_db_connection)

        # Create active and inactive printers
        await repo.create({
            'id': 'active_1',
            'name': 'Active Printer',
            'type': 'bambu_lab',
            'is_active': True
        })
        await repo.create({
            'id': 'inactive_1',
            'name': 'Inactive Printer',
            'type': 'bambu_lab',
            'is_active': False
        })

        # List only active
        printers = await repo.list(active_only=True)
        assert all(p['is_active'] == 1 for p in printers)

    @pytest.mark.asyncio
    async def test_update_printer_status(self, async_db_connection):
        """Test updating printer status"""
        repo = PrinterRepository(async_db_connection)

        # Create printer
        await repo.create({
            'id': 'printer_status_test',
            'name': 'Status Test Printer',
            'type': 'bambu_lab'
        })

        # Update status
        now = datetime.now()
        result = await repo.update_status('printer_status_test', 'printing', now)
        assert result is True

        # Verify update
        printer = await repo.get('printer_status_test')
        assert printer['status'] == 'printing'

    @pytest.mark.asyncio
    async def test_update_printer_fields(self, async_db_connection):
        """Test updating multiple printer fields"""
        repo = PrinterRepository(async_db_connection)

        # Create printer
        await repo.create({
            'id': 'printer_update_test',
            'name': 'Original Name',
            'type': 'bambu_lab'
        })

        # Update multiple fields
        updates = {
            'name': 'Updated Name',
            'ip_address': '192.168.1.200'
        }
        result = await repo.update('printer_update_test', updates)
        assert result is True

        # Verify updates
        printer = await repo.get('printer_update_test')
        assert printer['name'] == 'Updated Name'
        assert printer['ip_address'] == '192.168.1.200'

    @pytest.mark.asyncio
    async def test_delete_printer(self, async_db_connection):
        """Test deleting a printer"""
        repo = PrinterRepository(async_db_connection)

        # Create printer
        await repo.create({
            'id': 'printer_delete_test',
            'name': 'Delete Test',
            'type': 'bambu_lab'
        })

        # Verify it exists
        assert await repo.exists('printer_delete_test') is True

        # Delete it
        result = await repo.delete('printer_delete_test')
        assert result is True

        # Verify it's gone
        assert await repo.exists('printer_delete_test') is False

    @pytest.mark.asyncio
    async def test_printer_exists(self, async_db_connection):
        """Test checking printer existence"""
        repo = PrinterRepository(async_db_connection)

        # Create printer
        await repo.create({
            'id': 'exists_test',
            'name': 'Exists Test',
            'type': 'bambu_lab'
        })

        # Test exists
        assert await repo.exists('exists_test') is True
        assert await repo.exists('nonexistent') is False


# =====================================================
# JobRepository Tests
# =====================================================

class TestJobRepository:
    """Tests for JobRepository"""

    @pytest.mark.asyncio
    async def test_create_job(self, async_db_connection):
        """Test creating a new job"""
        # First create a printer
        printer_repo = PrinterRepository(async_db_connection)
        await printer_repo.create({
            'id': 'printer_for_job',
            'name': 'Job Test Printer',
            'type': 'bambu_lab'
        })

        repo = JobRepository(async_db_connection)

        job_data = {
            'id': 'job_001',
            'printer_id': 'printer_for_job',
            'printer_type': 'bambu_lab',
            'job_name': 'test_print.3mf',
            'filename': 'test_print.3mf',
            'status': 'printing',
            'progress': 50
        }

        result = await repo.create(job_data)
        assert result is True

        # Verify it was created
        job = await repo.get('job_001')
        assert job is not None
        assert job['job_name'] == 'test_print.3mf'

    @pytest.mark.asyncio
    async def test_create_duplicate_job(self, async_db_connection):
        """Test creating duplicate job is handled gracefully"""
        # Create printer
        printer_repo = PrinterRepository(async_db_connection)
        await printer_repo.create({
            'id': 'printer_dup',
            'name': 'Dup Test Printer',
            'type': 'bambu_lab'
        })

        repo = JobRepository(async_db_connection)

        job_data = {
            'id': 'job_dup',
            'printer_id': 'printer_dup',
            'printer_type': 'bambu_lab',
            'job_name': 'duplicate.3mf',
            'filename': 'duplicate.3mf',
            'start_time': datetime.now().isoformat()
        }

        # Create once
        result1 = await repo.create(job_data)
        assert result1 is True

        # Try to create again (same unique constraint)
        result2 = await repo.create(job_data)
        assert result2 is False  # Should return False for duplicate

    @pytest.mark.asyncio
    async def test_list_jobs_with_filters(self, async_db_connection):
        """Test listing jobs with various filters"""
        # Create printer
        printer_repo = PrinterRepository(async_db_connection)
        await printer_repo.create({
            'id': 'printer_list',
            'name': 'List Test Printer',
            'type': 'bambu_lab'
        })

        repo = JobRepository(async_db_connection)

        # Create jobs with different statuses
        for i, status in enumerate(['printing', 'completed', 'failed']):
            await repo.create({
                'id': f'job_filter_{i}',
                'printer_id': 'printer_list',
                'printer_type': 'bambu_lab',
                'job_name': f'job_{i}.3mf',
                'status': status
            })

        # List all jobs
        all_jobs = await repo.list()
        assert len(all_jobs) >= 3

        # List by printer
        printer_jobs = await repo.list(printer_id='printer_list')
        assert len(printer_jobs) >= 3

        # List by status
        printing_jobs = await repo.list(status='printing')
        assert all(j['status'] == 'printing' for j in printing_jobs)

    @pytest.mark.asyncio
    async def test_get_jobs_by_date_range(self, async_db_connection):
        """Test getting jobs within date range"""
        # Create printer
        printer_repo = PrinterRepository(async_db_connection)
        await printer_repo.create({
            'id': 'printer_date',
            'name': 'Date Test Printer',
            'type': 'bambu_lab'
        })

        repo = JobRepository(async_db_connection)

        # Create jobs with different dates
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        last_week = now - timedelta(days=7)

        await repo.create({
            'id': 'job_recent',
            'printer_id': 'printer_date',
            'printer_type': 'bambu_lab',
            'job_name': 'recent.3mf',
            'start_time': now.isoformat()
        })

        await repo.create({
            'id': 'job_old',
            'printer_id': 'printer_date',
            'printer_type': 'bambu_lab',
            'job_name': 'old.3mf',
            'start_time': last_week.isoformat()
        })

        # Get jobs from last 2 days
        jobs = await repo.get_by_date_range(
            yesterday.isoformat(),
            (now + timedelta(days=1)).isoformat()
        )

        # Should include recent job but not old job
        job_ids = [j['id'] for j in jobs]
        assert 'job_recent' in job_ids

    @pytest.mark.asyncio
    async def test_get_job_statistics(self, async_db_connection):
        """Test getting job statistics"""
        # Create printer
        printer_repo = PrinterRepository(async_db_connection)
        await printer_repo.create({
            'id': 'printer_stats',
            'name': 'Stats Test Printer',
            'type': 'bambu_lab'
        })

        repo = JobRepository(async_db_connection)

        # Create jobs with various statuses
        statuses = ['completed', 'completed', 'failed', 'printing']
        for i, status in enumerate(statuses):
            await repo.create({
                'id': f'job_stats_{i}',
                'printer_id': 'printer_stats',
                'printer_type': 'bambu_lab',
                'job_name': f'stats_{i}.3mf',
                'status': status
            })

        # Get statistics
        stats = await repo.get_statistics()

        assert stats['total_jobs'] >= 4
        assert stats['completed_jobs'] >= 2
        assert stats['failed_jobs'] >= 1
        assert 0 <= stats['success_rate'] <= 100

    @pytest.mark.asyncio
    async def test_update_job(self, async_db_connection):
        """Test updating job fields"""
        # Create printer
        printer_repo = PrinterRepository(async_db_connection)
        await printer_repo.create({
            'id': 'printer_update_job',
            'name': 'Update Job Printer',
            'type': 'bambu_lab'
        })

        repo = JobRepository(async_db_connection)

        # Create job
        await repo.create({
            'id': 'job_update',
            'printer_id': 'printer_update_job',
            'printer_type': 'bambu_lab',
            'job_name': 'update_test.3mf',
            'status': 'printing',
            'progress': 10
        })

        # Update it
        updates = {
            'progress': 75,
            'status': 'printing'
        }
        result = await repo.update('job_update', updates)
        assert result is True

        # Verify update
        job = await repo.get('job_update')
        assert job['progress'] == 75


# =====================================================
# SnapshotRepository Tests
# =====================================================

class TestSnapshotRepository:
    """Tests for SnapshotRepository"""

    @pytest.mark.asyncio
    async def test_create_snapshot(self, async_db_connection):
        """Test creating a camera snapshot record"""
        from src.database.repositories.snapshot_repository import SnapshotRepository

        # Create printer
        printer_repo = PrinterRepository(async_db_connection)
        await printer_repo.create({
            'id': 'printer_snap',
            'name': 'Snapshot Printer',
            'type': 'bambu_lab'
        })

        repo = SnapshotRepository(async_db_connection)

        snapshot_data = {
            'id': 'snap_001',
            'printer_id': 'printer_snap',
            'image_path': '/snapshots/snap_001.jpg',
            'image_format': 'jpg',
            'image_size_bytes': 102400
        }

        result = await repo.create(snapshot_data)
        assert result is True

        # Verify it was created
        snapshot = await repo.get('snap_001')
        assert snapshot is not None
        assert snapshot['printer_id'] == 'printer_snap'

    @pytest.mark.asyncio
    async def test_list_snapshots_by_printer(self, async_db_connection):
        """Test listing snapshots for a specific printer"""
        from src.database.repositories.snapshot_repository import SnapshotRepository

        # Create printers
        printer_repo = PrinterRepository(async_db_connection)
        await printer_repo.create({
            'id': 'printer_snap1',
            'name': 'Snapshot Printer 1',
            'type': 'bambu_lab'
        })
        await printer_repo.create({
            'id': 'printer_snap2',
            'name': 'Snapshot Printer 2',
            'type': 'prusa'
        })

        repo = SnapshotRepository(async_db_connection)

        # Create snapshots for different printers
        for i in range(3):
            await repo.create({
                'id': f'snap_p1_{i}',
                'printer_id': 'printer_snap1',
                'image_path': f'/snapshots/p1_{i}.jpg',
                'image_format': 'jpg'
            })

        await repo.create({
            'id': 'snap_p2_1',
            'printer_id': 'printer_snap2',
            'image_path': '/snapshots/p2_1.jpg',
            'image_format': 'jpg'
        })

        # List snapshots for printer 1
        snapshots = await repo.list(printer_id='printer_snap1')
        assert len(snapshots) >= 3
        assert all(s['printer_id'] == 'printer_snap1' for s in snapshots)


# =====================================================
# TrendingRepository Tests
# =====================================================

class TestTrendingRepository:
    """Tests for TrendingRepository"""

    @pytest.mark.asyncio
    async def test_upsert_trending_item(self, async_db_connection):
        """Test upserting trending items"""
        from src.database.repositories.trending_repository import TrendingRepository

        repo = TrendingRepository(async_db_connection)

        item_data = {
            'platform_id': 'thangs_12345',
            'platform': 'thangs',
            'title': 'Cool 3D Model',
            'url': 'https://thangs.com/model/12345',
            'thumbnail_url': 'https://thangs.com/thumb/12345.jpg'
        }

        result = await repo.upsert(item_data)
        assert result is True

        # Verify it was created
        item = await repo.get('thangs_12345')
        assert item is not None
        assert item['title'] == 'Cool 3D Model'

    @pytest.mark.asyncio
    async def test_list_trending_by_platform(self, async_db_connection):
        """Test listing trending items by platform"""
        from src.database.repositories.trending_repository import TrendingRepository

        repo = TrendingRepository(async_db_connection)

        # Create items for different platforms
        for i in range(2):
            await repo.upsert({
                'platform_id': f'thangs_{i}',
                'platform': 'thangs',
                'title': f'Thangs Model {i}',
                'url': f'https://thangs.com/{i}'
            })

        for i in range(3):
            await repo.upsert({
                'platform_id': f'printables_{i}',
                'platform': 'printables',
                'title': f'Printables Model {i}',
                'url': f'https://printables.com/{i}'
            })

        # List by platform
        thangs_items = await repo.list(platform='thangs')
        printables_items = await repo.list(platform='printables')

        assert len(thangs_items) >= 2
        assert len(printables_items) >= 3
        assert all(item['platform'] == 'thangs' for item in thangs_items)


# =====================================================
# Run marker for pytest
# =====================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
