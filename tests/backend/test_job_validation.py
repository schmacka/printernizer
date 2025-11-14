"""
Test job validation and NULL ID prevention.
Tests for migration 005 and job service validation enhancements.
"""
import pytest
import uuid
import sqlite3
import tempfile
import os
from pathlib import Path
from src.database.database import Database
from src.services.job_service import JobService
from src.services.event_service import EventService
from src.models.job import Job, JobCreate, JobStatus


# Helper function to create test database
async def create_test_db():
    """Create a test database instance."""
    # Create temp db file
    fd, test_db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db = Database(test_db_path)
    await db.initialize()
    return db, test_db_path


class TestJobIDValidation:
    """Test suite for job ID validation and NULL prevention."""

    @pytest.mark.asyncio
    async def test_database_schema_prevents_null_ids(self):
        """Test that database schema enforces NOT NULL on job.id."""
        db, db_path = await create_test_db()
        try:
            # Try to insert a job with NULL id using raw SQL
            with pytest.raises(sqlite3.IntegrityError):
                async with db.connection() as conn:
                    await conn.execute("""
                        INSERT INTO jobs (id, printer_id, printer_type, job_name, status)
                        VALUES (NULL, 'test_printer', 'bambu', 'test_job', 'pending')
                    """)
                    await conn.commit()
        finally:
            await db.close()
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_database_schema_prevents_empty_ids(self):
        """Test that database schema enforces non-empty ID strings."""
        db, db_path = await create_test_db()
        try:
            # Try to insert a job with empty string id
            with pytest.raises(sqlite3.IntegrityError):
                async with db.connection() as conn:
                    await conn.execute("""
                        INSERT INTO jobs (id, printer_id, printer_type, job_name, status)
                        VALUES ('', 'test_printer', 'bambu', 'test_job', 'pending')
                    """)
                    await conn.commit()
        finally:
            await db.close()
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_job_service_creates_valid_id(self):
        """Test that job service always creates jobs with valid IDs."""
        db, db_path = await create_test_db()
        try:
            event_service = EventService()
            job_service = JobService(db, event_service)

            # Create test printer first (required for foreign key constraint)
            async with db.connection() as conn:
                await conn.execute("""
                    INSERT INTO printers (id, name, type, ip_address, is_active)
                    VALUES ('test_printer_001', 'Test Printer', 'bambu', '192.168.1.1', 1)
                """)
                await conn.commit()

            job_data = {
                'printer_id': 'test_printer_001',
                'job_name': 'Test Print Job',
                'filename': 'test.3mf',
                'estimated_duration': 3600,
                'is_business': False
            }

            job_id = await job_service.create_job(job_data)

            # Verify ID is valid UUID
            assert job_id is not None
            assert job_id != ''
            assert len(job_id) == 36  # UUID format

            # Verify job can be retrieved
            job = await job_service.get_job(job_id)
            assert job is not None
            assert job['id'] == job_id
        finally:
            await db.close()
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_job_model_validates_id_field(self):
        """Test that Job pydantic model validates ID field."""
        # Valid job
        valid_job = Job(
            id=str(uuid.uuid4()),
            printer_id='printer_001',
            printer_type='bambu',
            job_name='Test Job',
            status=JobStatus.PENDING
        )
        assert valid_job.id is not None

        # Invalid job with None ID should raise validation error
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Job(
                id=None,
                printer_id='printer_001',
                printer_type='bambu',
                job_name='Test Job',
                status=JobStatus.PENDING
            )

        errors = exc_info.value.errors()
        assert any(e['loc'] == ('id',) for e in errors)

    @pytest.mark.asyncio
    async def test_get_jobs_skips_invalid_jobs(self):
        """Test that get_jobs handles and logs invalid jobs gracefully."""
        db, db_path = await create_test_db()
        try:
            from src.services.event_service import EventService
            from src.services.job_service import JobService
            event_service = EventService()
            job_service = JobService(db, event_service)

            # Create test printer first (required for foreign key constraint)
            async with db.connection() as conn:
                await conn.execute("""
                    INSERT INTO printers (id, name, type, ip_address, is_active)
                    VALUES ('test_printer', 'Test Printer', 'bambu', '192.168.1.1', 1)
                """)
                await conn.commit()

            # Create a valid job first
            valid_job_id = await job_service.create_job({
                'printer_id': 'test_printer',
                'job_name': 'Valid Job',
                'filename': 'valid.3mf'
            })

            # Get jobs should return the valid job
            jobs = await job_service.get_jobs()
            assert len(jobs) == 1
            assert jobs[0]['id'] == valid_job_id
        finally:
            await db.close()
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_list_jobs_skips_invalid_jobs(self):
        """Test that list_jobs handles invalid jobs gracefully."""
        db, db_path = await create_test_db()
        try:
            from src.services.event_service import EventService
            from src.services.job_service import JobService
            event_service = EventService()
            job_service = JobService(db, event_service)

            # Create test printers first (required for foreign key constraint)
            async with db.connection() as conn:
                await conn.execute("""
                    INSERT INTO printers (id, name, type, ip_address, is_active)
                    VALUES ('printer_001', 'Printer 1', 'bambu', '192.168.1.1', 1)
                """)
                await conn.execute("""
                    INSERT INTO printers (id, name, type, ip_address, is_active)
                    VALUES ('printer_002', 'Printer 2', 'prusa', '192.168.1.2', 1)
                """)
                await conn.commit()

            # Create valid jobs
            job1_id = await job_service.create_job({
                'printer_id': 'printer_001',
                'job_name': 'Job 1',
                'filename': 'job1.3mf'
            })

            job2_id = await job_service.create_job({
                'printer_id': 'printer_002',
                'job_name': 'Job 2',
                'filename': 'job2.3mf'
            })

            # List all jobs
            all_jobs = await job_service.list_jobs()
            assert len(all_jobs) == 2

            # List filtered by printer
            printer1_jobs = await job_service.list_jobs(printer_id='printer_001')
            assert len(printer1_jobs) == 1
            assert printer1_jobs[0]['id'] == job1_id
        finally:
            await db.close()
            os.unlink(db_path)


class TestMigration005:
    """Test suite for migration 005."""

    @pytest.mark.asyncio
    async def test_migration_tracking_table_created(self):
        """Test that migrations table is created."""
        db, db_path = await create_test_db()
        try:
            async with db.connection() as conn:
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='migrations'"
                )
                result = await cursor.fetchone()
                assert result is not None
        finally:
            await db.close()
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_migration_005_recorded(self):
        """Test that migration 005 is recorded in migrations table."""
        db, db_path = await create_test_db()
        try:
            async with db.connection() as conn:
                cursor = await conn.execute(
                    "SELECT version, description FROM migrations WHERE version='005'"
                )
                result = await cursor.fetchone()
                assert result is not None
                assert result[0] == '005'
                assert 'NULL' in result[1] or 'job' in result[1].lower()
        finally:
            await db.close()
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_jobs_table_has_not_null_constraint(self):
        """Test that jobs table has NOT NULL constraint on id column."""
        db, db_path = await create_test_db()
        try:
            async with db.connection() as conn:
                cursor = await conn.execute("PRAGMA table_info(jobs)")
                columns = await cursor.fetchall()

                # Find the id column
                id_column = next(col for col in columns if col[1] == 'id')

                # Check NOT NULL constraint (column index 3)
                assert id_column[3] == 1, "ID column should have NOT NULL constraint"
        finally:
            await db.close()
            os.unlink(db_path)


class TestJobCreationValidation:
    """Test job creation validation."""

    @pytest.mark.asyncio
    async def test_create_job_validates_required_fields(self):
        """Test that create_job validates all required fields."""
        db, db_path = await create_test_db()
        try:
            from src.services.event_service import EventService
            from src.services.job_service import JobService
            event_service = EventService()
            job_service = JobService(db, event_service)

            # Missing printer_id
            with pytest.raises(Exception):
                await job_service.create_job({
                    'job_name': 'Test Job'
                })

            # Missing job_name
            with pytest.raises(Exception):
                await job_service.create_job({
                    'printer_id': 'printer_001'
                })
        finally:
            await db.close()
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_create_job_generates_unique_ids(self):
        """Test that create_job generates unique IDs for each job."""
        db, db_path = await create_test_db()
        try:
            from src.services.event_service import EventService
            from src.services.job_service import JobService
            event_service = EventService()
            job_service = JobService(db, event_service)

            # Create test printer first (required for foreign key constraint)
            async with db.connection() as conn:
                await conn.execute("""
                    INSERT INTO printers (id, name, type, ip_address, is_active)
                    VALUES ('test_printer', 'Test Printer', 'bambu', '192.168.1.1', 1)
                """)
                await conn.commit()

            job_ids = []

            for i in range(5):
                job_id = await job_service.create_job({
                    'printer_id': 'test_printer',
                    'job_name': f'Job {i}',
                    'filename': f'job{i}.3mf'
                })
                job_ids.append(job_id)

            # All IDs should be unique
            assert len(job_ids) == len(set(job_ids))

            # All IDs should be valid UUIDs
            for job_id in job_ids:
                uuid.UUID(job_id)  # Will raise if invalid
        finally:
            await db.close()
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_create_job_with_business_info(self):
        """Test creating business jobs with customer info."""
        db, db_path = await create_test_db()
        try:
            from src.services.event_service import EventService
            from src.services.job_service import JobService
            event_service = EventService()
            job_service = JobService(db, event_service)

            # Create test printer first (required for foreign key constraint)
            async with db.connection() as conn:
                await conn.execute("""
                    INSERT INTO printers (id, name, type, ip_address, is_active)
                    VALUES ('printer_001', 'Printer 1', 'bambu', '192.168.1.1', 1)
                """)
                await conn.commit()

            job_id = await job_service.create_job({
                'printer_id': 'printer_001',
                'job_name': 'Business Print',
                'filename': 'business.3mf',
                'is_business': True,
                'customer_info': {
                    'name': 'Test Customer',
                    'order_id': 'ORD-12345'
                }
            })

            # Retrieve and verify
            job = await job_service.get_job(job_id)
            assert job['is_business'] is True
            assert job['customer_info']['name'] == 'Test Customer'
        finally:
            await db.close()
            os.unlink(db_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
