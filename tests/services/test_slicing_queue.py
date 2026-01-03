"""
Unit tests for SlicingQueue service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from src.services.slicing_queue import SlicingQueue
from src.services.event_service import EventService
from src.services.slicer_service import SlicerService
from src.models.slicer import (
    SlicingJob,
    SlicingJobStatus,
    SlicingJobRequest,
    SlicerConfig,
    SlicerProfile,
    SlicerType,
    ProfileType
)
from src.utils.exceptions import NotFoundError


@pytest.fixture
def mock_database():
    """Create mock database for testing."""
    db = MagicMock()
    db.connection = MagicMock()
    
    # Setup async context manager
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone = AsyncMock()
    mock_cursor.fetchall = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_cursor)
    mock_conn.commit = AsyncMock()
    
    async_context = AsyncMock()
    async_context.__aenter__ = AsyncMock(return_value=mock_conn)
    async_context.__aexit__ = AsyncMock()
    
    db.connection.return_value = async_context
    
    return db


@pytest.fixture
def mock_event_service():
    """Create mock event service for testing."""
    event_service = MagicMock(spec=EventService)
    event_service.emit = AsyncMock()
    return event_service


@pytest.fixture
def mock_slicer_service():
    """Create mock slicer service for testing."""
    service = MagicMock(spec=SlicerService)
    service.get_slicer = AsyncMock()
    service.get_profile = AsyncMock()
    service.verify_slicer_availability = AsyncMock(return_value=True)
    return service


@pytest.fixture
def slicing_queue(mock_database, mock_event_service, mock_slicer_service):
    """Create SlicingQueue instance with mock dependencies."""
    queue = SlicingQueue(
        mock_database,
        mock_event_service,
        mock_slicer_service
    )
    queue._enabled = True
    return queue


class TestSlicingQueue:
    """Test slicing queue functionality."""

    @pytest.mark.asyncio
    async def test_initialization(self, slicing_queue):
        """Test queue initialization."""
        assert slicing_queue.db is not None
        assert slicing_queue.event_service is not None
        assert slicing_queue.slicer_service is not None
        assert slicing_queue._running_jobs == {}

    @pytest.mark.asyncio
    async def test_create_job(self, slicing_queue, mock_database, mock_event_service):
        """Test creating a slicing job."""
        job_request = SlicingJobRequest(
            file_checksum='abc123',
            slicer_id='slicer-id',
            profile_id='profile-id',
            priority=5,
            auto_upload=False,
            auto_start=False
        )
        
        # Mock get_job to return a SlicingJob
        with patch.object(slicing_queue, 'get_job') as mock_get:
            now = datetime.now()
            mock_get.return_value = SlicingJob(
                id='job-id',
                file_checksum=job_request.file_checksum,
                slicer_id=job_request.slicer_id,
                profile_id=job_request.profile_id,
                target_printer_id=None,
                status=SlicingJobStatus.QUEUED,
                priority=job_request.priority,
                progress=0,
                output_file_path=None,
                output_gcode_checksum=None,
                estimated_print_time=None,
                filament_used=None,
                error_message=None,
                retry_count=0,
                auto_upload=job_request.auto_upload,
                auto_start=job_request.auto_start,
                started_at=None,
                completed_at=None,
                created_at=now,
                updated_at=now
            )
            
            with patch.object(slicing_queue, '_process_queue') as mock_process:
                mock_process.return_value = None
                
                result = await slicing_queue.create_job(job_request)
                
                assert result is not None
                assert result.file_checksum == job_request.file_checksum
                assert result.status == SlicingJobStatus.QUEUED
                mock_event_service.emit.assert_called()

    @pytest.mark.asyncio
    async def test_get_job_found(self, slicing_queue, mock_database):
        """Test getting a job by ID."""
        job_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Setup mock database response
        async_context = mock_database.connection.return_value
        conn = await async_context.__aenter__()
        cursor = await conn.execute()
        cursor.fetchone.return_value = (
            job_id,
            'checksum123',
            'slicer-id',
            'profile-id',
            None,
            SlicingJobStatus.QUEUED.value,
            5,
            0,
            None,
            None,
            None,
            None,
            None,
            0,
            False,
            False,
            None,
            None,
            now.isoformat(),
            now.isoformat()
        )
        
        result = await slicing_queue.get_job(job_id)
        
        assert result is not None
        assert result.id == job_id
        assert result.status == SlicingJobStatus.QUEUED

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, slicing_queue, mock_database):
        """Test getting non-existent job."""
        job_id = str(uuid.uuid4())
        
        # Setup mock to return None
        async_context = mock_database.connection.return_value
        conn = await async_context.__aenter__()
        cursor = await conn.execute()
        cursor.fetchone.return_value = None
        
        with pytest.raises(NotFoundError):
            await slicing_queue.get_job(job_id)

    @pytest.mark.asyncio
    async def test_list_jobs(self, slicing_queue, mock_database):
        """Test listing jobs."""
        now = datetime.now()
        
        # Setup mock database response
        async_context = mock_database.connection.return_value
        conn = await async_context.__aenter__()
        cursor = await conn.execute()
        cursor.fetchall.return_value = [
            (
                'job1',
                'checksum1',
                'slicer-id',
                'profile-id',
                None,
                SlicingJobStatus.QUEUED.value,
                5,
                0,
                None,
                None,
                None,
                None,
                None,
                0,
                False,
                False,
                None,
                None,
                now.isoformat(),
                now.isoformat()
            ),
            (
                'job2',
                'checksum2',
                'slicer-id',
                'profile-id',
                None,
                SlicingJobStatus.RUNNING.value,
                5,
                50,
                None,
                None,
                None,
                None,
                None,
                0,
                False,
                False,
                now.isoformat(),
                None,
                now.isoformat(),
                now.isoformat()
            )
        ]
        
        results = await slicing_queue.list_jobs()
        
        assert len(results) == 2
        assert results[0].status == SlicingJobStatus.QUEUED
        assert results[1].status == SlicingJobStatus.RUNNING

    @pytest.mark.asyncio
    async def test_cancel_job(self, slicing_queue, mock_database, mock_event_service):
        """Test cancelling a job."""
        job_id = str(uuid.uuid4())
        now = datetime.now()
        
        with patch.object(slicing_queue, 'get_job') as mock_get:
            mock_get.return_value = SlicingJob(
                id=job_id,
                file_checksum='checksum',
                slicer_id='slicer-id',
                profile_id='profile-id',
                target_printer_id=None,
                status=SlicingJobStatus.QUEUED,
                priority=5,
                progress=0,
                output_file_path=None,
                output_gcode_checksum=None,
                estimated_print_time=None,
                filament_used=None,
                error_message=None,
                retry_count=0,
                auto_upload=False,
                auto_start=False,
                started_at=None,
                completed_at=None,
                created_at=now,
                updated_at=now
            )
            
            with patch.object(slicing_queue, '_update_job_status') as mock_update:
                mock_update.return_value = None
                
                result = await slicing_queue.cancel_job(job_id)
                
                assert result is True
                mock_event_service.emit.assert_called()

    @pytest.mark.asyncio
    async def test_cancel_completed_job(self, slicing_queue):
        """Test cancelling a completed job should fail."""
        job_id = str(uuid.uuid4())
        now = datetime.now()
        
        with patch.object(slicing_queue, 'get_job') as mock_get:
            mock_get.return_value = SlicingJob(
                id=job_id,
                file_checksum='checksum',
                slicer_id='slicer-id',
                profile_id='profile-id',
                target_printer_id=None,
                status=SlicingJobStatus.COMPLETED,
                priority=5,
                progress=100,
                output_file_path='/path/to/output.gcode',
                output_gcode_checksum=None,
                estimated_print_time=None,
                filament_used=None,
                error_message=None,
                retry_count=0,
                auto_upload=False,
                auto_start=False,
                started_at=now,
                completed_at=now,
                created_at=now,
                updated_at=now
            )
            
            result = await slicing_queue.cancel_job(job_id)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_job(self, slicing_queue, mock_database):
        """Test deleting a job."""
        job_id = str(uuid.uuid4())
        now = datetime.now()
        
        with patch.object(slicing_queue, 'get_job') as mock_get:
            mock_get.return_value = SlicingJob(
                id=job_id,
                file_checksum='checksum',
                slicer_id='slicer-id',
                profile_id='profile-id',
                target_printer_id=None,
                status=SlicingJobStatus.COMPLETED,
                priority=5,
                progress=100,
                output_file_path=None,
                output_gcode_checksum=None,
                estimated_print_time=None,
                filament_used=None,
                error_message=None,
                retry_count=0,
                auto_upload=False,
                auto_start=False,
                started_at=now,
                completed_at=now,
                created_at=now,
                updated_at=now
            )
            
            result = await slicing_queue.delete_job(job_id)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_update_job_status(self, slicing_queue, mock_database, mock_event_service):
        """Test updating job status."""
        job_id = str(uuid.uuid4())
        
        await slicing_queue._update_job_status(job_id, SlicingJobStatus.RUNNING)
        
        mock_event_service.emit.assert_called()

    @pytest.mark.asyncio
    async def test_update_job_progress(self, slicing_queue, mock_database, mock_event_service):
        """Test updating job progress."""
        job_id = str(uuid.uuid4())
        
        await slicing_queue._update_job_progress(job_id, 50)
        
        mock_event_service.emit.assert_called()
