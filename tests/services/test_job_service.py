"""
Unit tests for Job Service.
Implements test cases from TEST_COVERAGE_ANALYSIS.md Phase 1.
"""
import pytest
import uuid
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from src.services.job_service import JobService
from src.services.event_service import EventService
from src.models.job import Job, JobStatus


@pytest.fixture
def mock_database():
    """Create mock database for testing."""
    db = MagicMock()
    db.list_jobs = AsyncMock(return_value=[])
    db.get_job = AsyncMock()
    db.create_job = AsyncMock()
    db.update_job = AsyncMock(return_value=True)
    db.delete_job = AsyncMock(return_value=True)
    db.get_job_statistics = AsyncMock(return_value={})
    db.get_jobs_by_date_range = AsyncMock(return_value=[])
    return db


@pytest.fixture
def mock_event_service():
    """Create mock event service for testing."""
    event_service = MagicMock(spec=EventService)
    event_service.emit = AsyncMock()
    event_service.emit_event = AsyncMock()
    return event_service


@pytest.fixture
def job_service(mock_database, mock_event_service):
    """Create JobService instance with mock dependencies."""
    return JobService(mock_database, mock_event_service)


def create_sample_job_data(
    job_id=None,
    printer_id='test_printer',
    printer_type='bambu_lab',
    job_name='Test Job',
    filename='test.3mf',
    status='pending',
    **kwargs
):
    """Helper to create sample job data."""
    job_id = job_id or str(uuid.uuid4())
    data = {
        'id': job_id,
        'printer_id': printer_id,
        'printer_type': printer_type,
        'job_name': job_name,
        'filename': filename,
        'status': status,
        'start_time': None,
        'end_time': None,
        'estimated_duration': None,
        'actual_duration': None,
        'progress': 0,
        'material_used': None,
        'material_cost': None,
        'power_cost': None,
        'is_business': False,
        'customer_info': None,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
    }
    data.update(kwargs)
    return data


class TestJobCreation:
    """Test job creation functionality."""

    @pytest.mark.asyncio
    async def test_create_job_with_valid_data(self, job_service, mock_database):
        """Test creating a job with valid data."""
        job_data = {
            'printer_id': 'printer_001',
            'printer_type': 'bambu_lab',
            'job_name': 'Test Print',
            'filename': 'test.3mf'
        }
        
        result = await job_service.create_job(job_data)
        
        # Job service generates its own UUID
        assert result is not None
        assert isinstance(result, str)
        # Verify UUID format
        assert len(result) == 36
        mock_database.create_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_job_auto_generates_id(self, job_service, mock_database):
        """Test that job creation auto-generates UUID if not provided."""
        job_data = {
            'printer_id': 'printer_001',
            'printer_type': 'bambu_lab',
            'job_name': 'Test Print'
        }
        
        job_id = str(uuid.uuid4())
        mock_database.create_job.return_value = job_id
        
        result = await job_service.create_job(job_data)
        
        # Verify a valid UUID was generated
        assert result is not None
        # UUID should be valid format
        assert len(result) == 36

    @pytest.mark.asyncio
    async def test_create_job_sets_default_status(self, job_service, mock_database):
        """Test that new jobs default to pending status."""
        job_data = {
            'printer_id': 'printer_001',
            'printer_type': 'bambu_lab',
            'job_name': 'Test Print'
        }
        
        job_id = str(uuid.uuid4())
        mock_database.create_job.return_value = job_id
        
        await job_service.create_job(job_data)
        
        # Check the call arguments
        call_args = mock_database.create_job.call_args[0][0]
        assert call_args.get('status') in [None, 'pending', JobStatus.PENDING]

    @pytest.mark.asyncio
    async def test_create_job_with_missing_required_fields(self, job_service, mock_database):
        """Test creating job with missing required fields raises exception."""
        job_data = {
            'job_name': 'Test Print'
            # Missing printer_id - should fail
        }
        
        with pytest.raises(Exception):
            await job_service.create_job(job_data)

    @pytest.mark.asyncio
    async def test_create_job_with_business_flag(self, job_service, mock_database):
        """Test creating a business job."""
        job_data = {
            'printer_id': 'printer_001',
            'printer_type': 'bambu_lab',
            'job_name': 'Customer Order',
            'filename': 'order.3mf',
            'is_business': True,
            'customer_info': {'name': 'Test Customer', 'order_id': 'ORD-123'}
        }
        
        result = await job_service.create_job(job_data)
        
        assert result is not None
        assert isinstance(result, str)
        call_args = mock_database.create_job.call_args[0][0]
        assert call_args.get('is_business') == True


class TestJobRetrieval:
    """Test job retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_jobs_all(self, job_service, mock_database):
        """Test retrieving all jobs."""
        sample_jobs = [
            create_sample_job_data(job_id=str(uuid.uuid4())),
            create_sample_job_data(job_id=str(uuid.uuid4())),
        ]
        mock_database.list_jobs.return_value = sample_jobs
        
        jobs = await job_service.get_jobs()
        
        assert len(jobs) == 2
        mock_database.list_jobs.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_jobs_with_pagination(self, job_service, mock_database):
        """Test job retrieval with pagination."""
        sample_jobs = [create_sample_job_data(job_id=str(uuid.uuid4())) for _ in range(10)]
        mock_database.list_jobs.return_value = sample_jobs
        
        jobs = await job_service.get_jobs(limit=5, offset=0)
        
        # Should return first 5 jobs
        assert len(jobs) == 5

    @pytest.mark.asyncio
    async def test_get_job_by_id(self, job_service, mock_database):
        """Test retrieving a specific job by ID."""
        job_id = str(uuid.uuid4())
        job_data = create_sample_job_data(job_id=job_id)
        mock_database.get_job.return_value = job_data
        
        job = await job_service.get_job(job_id)
        
        assert job is not None
        assert job['id'] == job_id
        mock_database.get_job.assert_called_once_with(job_id)

    @pytest.mark.asyncio
    async def test_get_job_by_id_not_found(self, job_service, mock_database):
        """Test retrieving non-existent job returns None."""
        mock_database.get_job.return_value = None
        
        job = await job_service.get_job('nonexistent_id')
        
        assert job is None

    @pytest.mark.asyncio
    async def test_list_jobs_by_printer(self, job_service, mock_database):
        """Test filtering jobs by printer ID."""
        printer_id = 'printer_001'
        sample_jobs = [
            create_sample_job_data(printer_id=printer_id),
            create_sample_job_data(printer_id=printer_id),
        ]
        mock_database.list_jobs.return_value = sample_jobs
        
        jobs = await job_service.list_jobs(printer_id=printer_id)
        
        assert len(jobs) == 2
        for job in jobs:
            assert job['printer_id'] == printer_id

    @pytest.mark.asyncio
    async def test_list_jobs_by_status(self, job_service, mock_database):
        """Test filtering jobs by status."""
        sample_jobs = [
            create_sample_job_data(status='printing'),
            create_sample_job_data(status='printing'),
        ]
        mock_database.list_jobs.return_value = sample_jobs
        
        jobs = await job_service.list_jobs(status='printing')
        
        assert len(jobs) == 2
        for job in jobs:
            assert job['status'] == 'printing'

    @pytest.mark.asyncio
    async def test_get_business_jobs(self, job_service, mock_database):
        """Test retrieving only business jobs."""
        sample_jobs = [
            create_sample_job_data(is_business=True),
            create_sample_job_data(is_business=True),
        ]
        mock_database.list_jobs.return_value = sample_jobs
        
        jobs = await job_service.get_business_jobs()
        
        assert len(jobs) == 2
        for job in jobs:
            assert job['is_business'] == True

    @pytest.mark.asyncio
    async def test_get_private_jobs(self, job_service, mock_database):
        """Test retrieving only private (non-business) jobs."""
        sample_jobs = [
            create_sample_job_data(is_business=False),
            create_sample_job_data(is_business=False),
        ]
        mock_database.list_jobs.return_value = sample_jobs
        
        jobs = await job_service.get_private_jobs()
        
        assert len(jobs) == 2
        for job in jobs:
            assert job['is_business'] == False

    @pytest.mark.asyncio
    async def test_get_jobs_by_date_range(self, job_service, mock_database):
        """Test retrieving jobs within a date range."""
        start_date = '2024-01-01'
        end_date = '2024-01-31'
        sample_jobs = [create_sample_job_data()]
        mock_database.get_jobs_by_date_range.return_value = sample_jobs
        
        jobs = await job_service.get_jobs_by_date_range(start_date, end_date)
        
        assert len(jobs) == 1
        mock_database.get_jobs_by_date_range.assert_called_once_with(start_date, end_date, None)

    @pytest.mark.asyncio
    async def test_get_printer_jobs(self, job_service, mock_database):
        """Test retrieving jobs for a specific printer."""
        printer_id = 'printer_001'
        sample_jobs = [create_sample_job_data(printer_id=printer_id)]
        mock_database.list_jobs.return_value = sample_jobs
        
        jobs = await job_service.get_printer_jobs(printer_id)
        
        assert len(jobs) == 1
        assert jobs[0]['printer_id'] == printer_id


class TestJobUpdates:
    """Test job update functionality."""

    @pytest.mark.asyncio
    async def test_update_job_status(self, job_service, mock_database, mock_event_service):
        """Test updating job status."""
        job_id = str(uuid.uuid4())
        
        await job_service.update_job_status(job_id, 'printing')
        
        mock_database.update_job.assert_called_once()
        # Verify event was emitted
        mock_event_service.emit_event.assert_called()

    @pytest.mark.asyncio
    async def test_update_job_progress(self, job_service, mock_database):
        """Test updating job progress percentage."""
        job_id = str(uuid.uuid4())
        progress = 50
        
        await job_service.update_job_progress(job_id, progress)
        
        mock_database.update_job.assert_called_once()
        # Check the call was made with progress in the updates dict
        call_args = mock_database.update_job.call_args[0]
        assert call_args[1]['progress'] == progress

    @pytest.mark.asyncio
    async def test_update_job_progress_with_material(self, job_service, mock_database):
        """Test updating job progress with material usage."""
        job_id = str(uuid.uuid4())
        progress = 75
        material_used = 150.5
        
        await job_service.update_job_progress(job_id, progress, material_used)
        
        mock_database.update_job.assert_called_once()
        call_args = mock_database.update_job.call_args[0]
        assert call_args[1]['progress'] == progress
        assert call_args[1]['material_used'] == material_used


class TestJobDeletion:
    """Test job deletion functionality."""

    @pytest.mark.asyncio
    async def test_delete_job_success(self, job_service, mock_database):
        """Test successful job deletion."""
        job_id = str(uuid.uuid4())
        mock_database.delete_job.return_value = True
        
        result = await job_service.delete_job(job_id)
        
        assert result == True
        mock_database.delete_job.assert_called_once_with(job_id)

    @pytest.mark.asyncio
    async def test_delete_job_not_found(self, job_service, mock_database):
        """Test deleting non-existent job returns False."""
        mock_database.delete_job.return_value = False
        
        result = await job_service.delete_job('nonexistent_id')
        
        assert result == False


class TestJobStatistics:
    """Test job statistics functionality."""

    @pytest.mark.asyncio
    async def test_get_job_statistics(self, job_service, mock_database):
        """Test retrieving job statistics."""
        expected_stats = {
            'total_jobs': 100,
            'completed_jobs': 80,
            'failed_jobs': 5,
            'pending_jobs': 15
        }
        mock_database.get_job_statistics.return_value = expected_stats
        
        stats = await job_service.get_job_statistics()
        
        assert stats == expected_stats
        mock_database.get_job_statistics.assert_called_once()


class TestJobDataDeserialization:
    """Test job data deserialization."""

    def test_deserialize_job_data_with_customer_info(self, job_service):
        """Test deserialization of job with customer_info JSON."""
        job_data = {
            'id': str(uuid.uuid4()),
            'printer_id': 'printer_001',
            'customer_info': '{"name": "Test Customer", "email": "test@example.com"}'
        }
        
        result = job_service._deserialize_job_data(job_data)
        
        assert isinstance(result['customer_info'], dict)
        assert result['customer_info']['name'] == 'Test Customer'

    def test_deserialize_job_data_with_datetime_strings(self, job_service):
        """Test deserialization of datetime strings."""
        now = datetime.now()
        job_data = {
            'id': str(uuid.uuid4()),
            'printer_id': 'printer_001',
            'start_time': now.isoformat(),
            'end_time': now.isoformat(),
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }
        
        result = job_service._deserialize_job_data(job_data)
        
        assert isinstance(result['start_time'], datetime)
        assert isinstance(result['end_time'], datetime)
        assert isinstance(result['created_at'], datetime)
        assert isinstance(result['updated_at'], datetime)

    def test_deserialize_job_data_with_null_values(self, job_service):
        """Test deserialization handles null values correctly."""
        job_data = {
            'id': str(uuid.uuid4()),
            'printer_id': 'printer_001',
            'customer_info': None,
            'start_time': None,
            'end_time': None
        }
        
        result = job_service._deserialize_job_data(job_data)
        
        assert result['customer_info'] is None
        assert result['start_time'] is None
        assert result['end_time'] is None


class TestJobValidation:
    """Test job validation and error handling."""

    @pytest.mark.asyncio
    async def test_get_jobs_skips_jobs_without_id(self, job_service, mock_database):
        """Test that jobs without ID are skipped with proper logging."""
        sample_jobs = [
            create_sample_job_data(job_id=str(uuid.uuid4())),
            {'printer_id': 'printer_001', 'job_name': 'No ID Job'},  # Missing ID
            create_sample_job_data(job_id=str(uuid.uuid4())),
        ]
        mock_database.list_jobs.return_value = sample_jobs
        
        jobs = await job_service.get_jobs()
        
        # Should return 2 valid jobs, skipping the one without ID
        assert len(jobs) == 2

    @pytest.mark.asyncio
    async def test_get_jobs_handles_malformed_data(self, job_service, mock_database):
        """Test that malformed job data is handled gracefully."""
        sample_jobs = [
            create_sample_job_data(job_id=str(uuid.uuid4())),
            {'id': str(uuid.uuid4()), 'invalid_field': 'bad data'},  # Malformed
        ]
        mock_database.list_jobs.return_value = sample_jobs
        
        # Should not raise exception
        jobs = await job_service.get_jobs()
        
        # Should return at least 1 valid job
        assert len(jobs) >= 1

    @pytest.mark.asyncio
    async def test_get_jobs_empty_list(self, job_service, mock_database):
        """Test handling of empty job list."""
        mock_database.list_jobs.return_value = []
        
        jobs = await job_service.get_jobs()
        
        assert jobs == []

    @pytest.mark.asyncio
    async def test_get_jobs_database_error(self, job_service, mock_database):
        """Test handling of database errors during job retrieval."""
        mock_database.list_jobs.side_effect = Exception("Database error")
        
        # Should not raise exception, return empty list
        jobs = await job_service.get_jobs()
        
        assert jobs == []


class TestJobCostCalculations:
    """Test job cost calculation functionality."""

    @pytest.mark.asyncio
    async def test_calculate_material_costs(self, job_service, mock_database):
        """Test material cost calculation."""
        job_id = str(uuid.uuid4())
        material_cost_per_gram = 0.05
        power_cost_per_hour = 0.15
        
        job_data = create_sample_job_data(
            job_id=job_id,
            material_used=100.0,
            actual_duration=7200  # 2 hours in seconds
        )
        mock_database.get_job.return_value = job_data
        
        costs = await job_service.calculate_material_costs(
            job_id,
            material_cost_per_gram,
            power_cost_per_hour
        )
        
        assert 'material_cost' in costs
        assert 'power_cost' in costs
        assert 'total_cost' in costs


class TestActiveJobs:
    """Test active job tracking."""

    @pytest.mark.asyncio
    async def test_get_active_jobs(self, job_service, mock_database):
        """Test retrieving currently active (printing) jobs."""
        active_jobs = [
            create_sample_job_data(status='printing'),
            create_sample_job_data(status='printing'),
        ]
        mock_database.list_jobs.return_value = active_jobs
        
        jobs = await job_service.get_active_jobs()
        
        assert len(jobs) == 2
        for job in jobs:
            assert job['status'] == 'printing'


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_pagination_beyond_available_jobs(self, job_service, mock_database):
        """Test pagination with offset beyond available jobs."""
        sample_jobs = [create_sample_job_data() for _ in range(5)]
        mock_database.list_jobs.return_value = sample_jobs
        
        jobs = await job_service.get_jobs(limit=10, offset=10)
        
        # Should return empty list, not error
        assert jobs == []

    @pytest.mark.asyncio
    async def test_negative_pagination_values(self, job_service, mock_database):
        """Test handling of negative pagination values."""
        sample_jobs = [create_sample_job_data()]
        mock_database.list_jobs.return_value = sample_jobs
        
        # Should handle gracefully (implementation dependent)
        jobs = await job_service.get_jobs(limit=-1, offset=-1)
        
        # Should not crash
        assert isinstance(jobs, list)

    @pytest.mark.asyncio
    async def test_very_large_pagination_limit(self, job_service, mock_database):
        """Test handling of very large pagination limits."""
        sample_jobs = [create_sample_job_data() for _ in range(10)]
        mock_database.list_jobs.return_value = sample_jobs
        
        jobs = await job_service.get_jobs(limit=1000000)
        
        assert len(jobs) == 10  # Should return available jobs

    @pytest.mark.asyncio
    async def test_concurrent_job_updates(self, job_service, mock_database):
        """Test handling concurrent updates to the same job."""
        job_id = str(uuid.uuid4())
        
        # Simulate concurrent updates
        await job_service.update_job_status(job_id, 'printing')
        await job_service.update_job_progress(job_id, 50)
        
        # Both should succeed without conflict - both use update_job
        assert mock_database.update_job.call_count == 2
