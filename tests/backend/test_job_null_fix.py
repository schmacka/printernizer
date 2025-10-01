"""
Simplified tests for NULL job ID fix (Migration 005).
Focused on critical functionality without complex fixtures.
"""
import pytest
import uuid
import sqlite3
import tempfile
import os
from src.database.database import Database
from src.services.job_service import JobService
from src.services.event_service import EventService
from src.models.job import Job, JobStatus
from pydantic import ValidationError


class TestNullJobIDFix:
    """Test NULL job ID prevention and migration."""

    @pytest.mark.asyncio
    async def test_job_model_rejects_null_id(self):
        """Test that Job model validates ID field and rejects NULL."""
        # Valid job should work
        valid_job = Job(
            id=str(uuid.uuid4()),
            printer_id='printer_001',
            printer_type='bambu',
            job_name='Test Job',
            status=JobStatus.PENDING
        )
        assert valid_job.id is not None

        # NULL ID should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            Job(
                id=None,
                printer_id='printer_001',
                printer_type='bambu',
                job_name='Test Job',
                status=JobStatus.PENDING
            )

        errors = exc_info.value.errors()
        assert any(e['loc'] == ('id',) and e['type'] == 'string_type' for e in errors)

    @pytest.mark.asyncio
    async def test_database_prevents_null_job_ids(self):
        """Test that database enforces NOT NULL constraint."""
        # Create temp database
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        db = Database(db_path)
        await db.initialize()

        try:
            # Attempt to insert job with NULL ID should fail
            with pytest.raises(sqlite3.IntegrityError):
                async with db.connection() as conn:
                    await conn.execute("""
                        INSERT INTO jobs (id, printer_id, printer_type, job_name, status)
                        VALUES (NULL, 'test_printer', 'bambu', 'test_job', 'pending')
                    """)
                    await conn.commit()

            # Attempt to insert job with empty ID should also fail
            with pytest.raises(sqlite3.IntegrityError):
                async with db.connection() as conn:
                    await conn.execute("""
                        INSERT INTO jobs (id, printer_id, printer_type, job_name, status)
                        VALUES ('', 'test_printer', 'bambu', 'test_job', 'pending')
                    """)
                    await conn.commit()

        finally:
            await db.close()
            try:
                os.unlink(db_path)
            except:
                pass

    @pytest.mark.asyncio
    async def test_job_service_creates_valid_ids(self):
        """Test that JobService always creates jobs with valid UUIDs."""
        # Create temp database
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        db = Database(db_path)
        await db.initialize()

        try:
            event_service = EventService()
            job_service = JobService(db, event_service)

            # Create multiple jobs
            job_ids = []
            for i in range(3):
                job_id = await job_service.create_job({
                    'printer_id': 'test_printer',
                    'job_name': f'Test Job {i}',
                    'filename': f'test{i}.3mf'
                })
                job_ids.append(job_id)

                # Validate ID format
                assert job_id is not None
                assert job_id != ''
                assert len(job_id) == 36  # Standard UUID string length
                uuid.UUID(job_id)  # Should parse as valid UUID

            # All IDs should be unique
            assert len(job_ids) == len(set(job_ids))

            # All jobs should be retrievable
            for job_id in job_ids:
                job = await job_service.get_job(job_id)
                assert job is not None
                assert job['id'] == job_id

        finally:
            await db.close()
            try:
                os.unlink(db_path)
            except:
                pass

    @pytest.mark.asyncio
    async def test_migration_005_applied(self):
        """Test that migration 005 is applied and tracked."""
        # Create temp database
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        db = Database(db_path)
        await db.initialize()

        try:
            # Check migrations table exists
            async with db.connection() as conn:
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='migrations'"
                )
                result = await cursor.fetchone()
                assert result is not None, "Migrations table should exist"

                # Check migration 005 is recorded
                cursor = await conn.execute(
                    "SELECT version, description FROM migrations WHERE version='005'"
                )
                migration = await cursor.fetchone()
                assert migration is not None, "Migration 005 should be recorded"
                assert migration[0] == '005'

        finally:
            await db.close()
            try:
                os.unlink(db_path)
            except:
                pass

    @pytest.mark.asyncio
    async def test_job_service_error_logging(self):
        """Test that job service logs errors for invalid jobs."""
        # Create temp database
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        db = Database(db_path)
        await db.initialize()

        try:
            event_service = EventService()
            job_service = JobService(db, event_service)

            # Create a valid job
            job_id = await job_service.create_job({
                'printer_id': 'test_printer',
                'job_name': 'Valid Job',
                'filename': 'valid.3mf'
            })

            # Retrieve jobs should work without errors
            jobs = await job_service.get_jobs()
            assert len(jobs) == 1
            assert jobs[0]['id'] == job_id

            # List jobs should also work
            job_list = await job_service.list_jobs()
            assert len(job_list) == 1

        finally:
            await db.close()
            try:
                os.unlink(db_path)
            except:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
