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
from src.utils.errors import NotFoundError
from src.services.slicing_queue import parse_gcode_metadata, _parse_human_time, GCodeMetadata


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


class TestHumanTimeParsing:
    """Test human-readable time parsing."""

    def test_parse_hours_minutes_seconds(self):
        """Test parsing time with hours, minutes, and seconds."""
        result = _parse_human_time("1h 30m 15s")
        assert result == 5415  # 1*3600 + 30*60 + 15

    def test_parse_minutes_seconds(self):
        """Test parsing time with minutes and seconds."""
        result = _parse_human_time("30m 15s")
        assert result == 1815  # 30*60 + 15

    def test_parse_seconds_only(self):
        """Test parsing time with seconds only."""
        result = _parse_human_time("45s")
        assert result == 45

    def test_parse_hours_only(self):
        """Test parsing time with hours only."""
        result = _parse_human_time("2h")
        assert result == 7200  # 2*3600

    def test_parse_days_hours_minutes(self):
        """Test parsing time with days, hours, and minutes."""
        result = _parse_human_time("1d 2h 30m")
        assert result == 95400  # 1*86400 + 2*3600 + 30*60

    def test_parse_no_spaces(self):
        """Test parsing time without spaces."""
        result = _parse_human_time("1h30m")
        assert result == 5400  # 1*3600 + 30*60

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = _parse_human_time("")
        assert result is None

    def test_parse_none(self):
        """Test parsing None returns None."""
        result = _parse_human_time(None)
        assert result is None

    def test_parse_invalid_format(self):
        """Test parsing invalid format returns None."""
        result = _parse_human_time("not a time")
        assert result is None


class TestGCodeMetadataParsing:
    """Test G-code metadata parsing from sample files."""

    @pytest.fixture
    def tmp_gcode_file(self, tmp_path):
        """Create a temporary G-code file with sample content."""
        def _create_file(content):
            gcode_file = tmp_path / "test.gcode"
            gcode_file.write_text(content)
            return str(gcode_file)
        return _create_file

    def test_parse_prusaslicer_format(self, tmp_gcode_file):
        """Test parsing PrusaSlicer G-code format."""
        content = """; generated by PrusaSlicer
; config: some_profile
; estimated printing time (normal mode) = 1h 30m 15s
; filament used [g] = 15.23
; filament used [mm] = 5123.45

G28 ; home all axes
G1 X0 Y0 Z10 F3000
"""
        gcode_path = tmp_gcode_file(content)
        metadata = parse_gcode_metadata(gcode_path)

        assert metadata.estimated_print_time == 5415  # 1h 30m 15s
        assert metadata.filament_used == pytest.approx(15.23, rel=0.01)

    def test_parse_orcaslicer_format(self, tmp_gcode_file):
        """Test parsing OrcaSlicer G-code format."""
        content = """; OrcaSlicer
; estimated printing time (normal mode) = 2h 15m
; filament used [g] = 23.5

G28
M104 S200
"""
        gcode_path = tmp_gcode_file(content)
        metadata = parse_gcode_metadata(gcode_path)

        assert metadata.estimated_print_time == 8100  # 2h 15m
        assert metadata.filament_used == pytest.approx(23.5, rel=0.01)

    def test_parse_bambustudio_format(self, tmp_gcode_file):
        """Test parsing BambuStudio G-code format."""
        content = """; BambuStudio
; model: test_model.stl
; estimated printing time (normal mode) = 45m 30s
; total filament used [g] = 8.75

G28
"""
        gcode_path = tmp_gcode_file(content)
        metadata = parse_gcode_metadata(gcode_path)

        assert metadata.estimated_print_time == 2730  # 45m 30s
        assert metadata.filament_used == pytest.approx(8.75, rel=0.01)

    def test_parse_cura_time_format(self, tmp_gcode_file):
        """Test parsing Cura G-code format with TIME: directive."""
        content = """;FLAVOR:Marlin
;TIME:5415
;Filament used: 5.12m

G28
"""
        gcode_path = tmp_gcode_file(content)
        metadata = parse_gcode_metadata(gcode_path)

        assert metadata.estimated_print_time == 5415
        # Cura reports in meters, convert: 5.12m * 2.98g/m
        assert metadata.filament_used == pytest.approx(15.26, rel=0.1)

    def test_parse_filament_in_mm(self, tmp_gcode_file):
        """Test parsing filament usage reported in mm."""
        content = """; estimated printing time (normal mode) = 1h
; filament used [mm] = 5000.0

G28
"""
        gcode_path = tmp_gcode_file(content)
        metadata = parse_gcode_metadata(gcode_path)

        assert metadata.estimated_print_time == 3600  # 1h
        # 5000mm = 5m, 5m * 2.98g/m = 14.9g
        assert metadata.filament_used == pytest.approx(14.9, rel=0.1)

    def test_parse_no_metadata(self, tmp_gcode_file):
        """Test parsing G-code with no metadata."""
        content = """G28
G1 X0 Y0 Z10
G1 X100 Y100
"""
        gcode_path = tmp_gcode_file(content)
        metadata = parse_gcode_metadata(gcode_path)

        assert metadata.estimated_print_time is None
        assert metadata.filament_used is None

    def test_parse_footer_metadata(self, tmp_gcode_file):
        """Test parsing metadata from footer of G-code file."""
        # Create a file with metadata at the end
        content = """G28
G1 X0 Y0 Z10
G1 X100 Y100
M104 S0
M140 S0
; some commands

; estimated printing time (normal mode) = 30m
; filament used [g] = 5.5
"""
        gcode_path = tmp_gcode_file(content)
        metadata = parse_gcode_metadata(gcode_path)

        assert metadata.estimated_print_time == 1800  # 30m
        assert metadata.filament_used == pytest.approx(5.5, rel=0.01)

    def test_parse_case_insensitive(self, tmp_gcode_file):
        """Test that parsing is case-insensitive."""
        content = """; ESTIMATED PRINTING TIME (NORMAL MODE) = 1H 30M
; FILAMENT USED [G] = 10.0

G28
"""
        gcode_path = tmp_gcode_file(content)
        metadata = parse_gcode_metadata(gcode_path)

        assert metadata.estimated_print_time == 5400  # 1h 30m
        assert metadata.filament_used == pytest.approx(10.0, rel=0.01)

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file returns empty metadata."""
        metadata = parse_gcode_metadata("/nonexistent/path/file.gcode")

        assert metadata.estimated_print_time is None
        assert metadata.filament_used is None

    def test_parse_alternative_time_format(self, tmp_gcode_file):
        """Test parsing alternative time format (total estimated time)."""
        content = """; total estimated time (s) = 3600
; filament_used = 12.5

G28
"""
        gcode_path = tmp_gcode_file(content)
        metadata = parse_gcode_metadata(gcode_path)

        assert metadata.estimated_print_time == 3600
        assert metadata.filament_used == pytest.approx(12.5, rel=0.01)
