"""
Unit tests for automated job creation feature.

Tests the core auto-job creation logic in PrinterMonitoringService including:
- Job key generation and deduplication
- Filename cleaning
- Discovery time tracking
- Database lookups for existing jobs
- Auto-creation triggering logic
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import json

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.services.printer_monitoring_service import PrinterMonitoringService
from src.models.printer import PrinterStatus, PrinterStatusUpdate
from src.database.database import Database
from src.services.event_service import EventService


class TestJobKeyGeneration:
    """Test job key generation for deduplication."""

    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service instance for testing."""
        mock_db = AsyncMock(spec=Database)
        mock_event_service = Mock(spec=EventService)
        return PrinterMonitoringService(
            database=mock_db,
            event_service=mock_event_service
        )

    def test_make_job_key_stable(self, monitoring_service):
        """Job key should be stable for same inputs."""
        printer_id = "bambu_001"
        filename = "test_model.3mf"
        discovery_time = datetime(2025, 1, 9, 10, 30, 45)

        key1 = monitoring_service._make_job_key(printer_id, filename, discovery_time)
        key2 = monitoring_service._make_job_key(printer_id, filename, discovery_time)

        assert key1 == key2
        assert "bambu_001" in key1
        assert "test_model.3mf" in key1

    def test_make_job_key_rounds_to_minute(self, monitoring_service):
        """Job key should be same within same minute (handles polling jitter)."""
        printer_id = "bambu_001"
        filename = "model.3mf"

        # Different seconds, same minute
        time1 = datetime(2025, 1, 9, 10, 30, 15)
        time2 = datetime(2025, 1, 9, 10, 30, 45)

        key1 = monitoring_service._make_job_key(printer_id, filename, time1)
        key2 = monitoring_service._make_job_key(printer_id, filename, time2)

        assert key1 == key2  # Same minute = same key

    def test_make_job_key_different_for_different_minutes(self, monitoring_service):
        """Job key should differ for different minutes."""
        printer_id = "bambu_001"
        filename = "model.3mf"

        time1 = datetime(2025, 1, 9, 10, 30, 0)
        time2 = datetime(2025, 1, 9, 10, 31, 0)

        key1 = monitoring_service._make_job_key(printer_id, filename, time1)
        key2 = monitoring_service._make_job_key(printer_id, filename, time2)

        assert key1 != key2  # Different minute = different key

    def test_make_job_key_removes_cache_prefix(self, monitoring_service):
        """Job key should remove cache/ prefix from Bambu Lab filenames."""
        printer_id = "bambu_001"
        discovery_time = datetime(2025, 1, 9, 10, 30, 0)

        filename_with_cache = "cache/model.3mf"
        filename_without_cache = "model.3mf"

        key1 = monitoring_service._make_job_key(printer_id, filename_with_cache, discovery_time)
        key2 = monitoring_service._make_job_key(printer_id, filename_without_cache, discovery_time)

        assert key1 == key2  # Cache prefix should be normalized

    def test_make_job_key_different_printers(self, monitoring_service):
        """Job key should differ for different printers printing same file."""
        filename = "model.3mf"
        discovery_time = datetime(2025, 1, 9, 10, 30, 0)

        key1 = monitoring_service._make_job_key("bambu_001", filename, discovery_time)
        key2 = monitoring_service._make_job_key("prusa_001", filename, discovery_time)

        assert key1 != key2  # Different printer = different key

    def test_make_job_key_format(self, monitoring_service):
        """Job key should have expected format."""
        printer_id = "bambu_001"
        filename = "test_model.3mf"
        discovery_time = datetime(2025, 1, 9, 10, 30, 45)

        key = monitoring_service._make_job_key(printer_id, filename, discovery_time)

        # Format: "printer_id:filename:YYYY-MM-DDTHH:MM:SS" (ISO 8601 timestamp has 2 colons)
        assert key.count(":") == 4  # Should have 4 colons (1 + 1 + 2 from timestamp)
        assert key.startswith("bambu_001:")
        assert "test_model.3mf" in key
        assert "2025-01-09T10:30" in key


class TestFilenameClean:
    """Test filename cleaning logic."""

    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service instance for testing."""
        mock_db = AsyncMock(spec=Database)
        mock_event_service = Mock(spec=EventService)
        return PrinterMonitoringService(
            database=mock_db,
            event_service=mock_event_service
        )

    def test_clean_filename_removes_extensions(self, monitoring_service):
        """Should remove common 3D printing file extensions."""
        assert monitoring_service._clean_filename("model.3mf") == "model"
        assert monitoring_service._clean_filename("print.gcode") == "print"
        assert monitoring_service._clean_filename("file.bgcode") == "file"
        assert monitoring_service._clean_filename("shape.stl") == "shape"

    def test_clean_filename_removes_cache_prefix(self, monitoring_service):
        """Should remove cache/ prefix from Bambu Lab filenames."""
        assert monitoring_service._clean_filename("cache/model.3mf") == "model"
        assert monitoring_service._clean_filename("cache/test.gcode") == "test"

    def test_clean_filename_removes_cache_and_extension(self, monitoring_service):
        """Should remove both cache prefix and extension."""
        assert monitoring_service._clean_filename("cache/model.3mf") == "model"

    def test_clean_filename_handles_whitespace(self, monitoring_service):
        """Should trim whitespace from filenames."""
        assert monitoring_service._clean_filename("  model.3mf  ") == "model"
        assert monitoring_service._clean_filename("cache/  test.gcode  ") == "test"

    def test_clean_filename_preserves_spaces_in_name(self, monitoring_service):
        """Should preserve spaces within the filename."""
        assert monitoring_service._clean_filename("my model.3mf") == "my model"
        assert monitoring_service._clean_filename("test print v2.gcode") == "test print v2"

    def test_clean_filename_case_insensitive_extensions(self, monitoring_service):
        """Should handle extensions case-insensitively."""
        assert monitoring_service._clean_filename("model.3MF") == "model"
        assert monitoring_service._clean_filename("print.GCODE") == "print"

    def test_clean_filename_no_extension(self, monitoring_service):
        """Should handle filenames without extensions."""
        assert monitoring_service._clean_filename("model") == "model"
        assert monitoring_service._clean_filename("cache/test") == "test"


class TestFindExistingJob:
    """Test database lookup for existing jobs."""

    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service with mocked database."""
        mock_db = AsyncMock(spec=Database)
        mock_event_service = Mock(spec=EventService)
        service = PrinterMonitoringService(
            database=mock_db,
            event_service=mock_event_service
        )
        return service

    @pytest.mark.asyncio
    async def test_find_existing_job_exact_match(self, monitoring_service):
        """Should find job with exact filename and time match."""
        printer_id = "bambu_001"
        filename = "model.3mf"
        discovery_time = datetime(2025, 1, 9, 10, 30, 0)

        # Mock database to return a matching job
        existing_job = {
            'id': 'job_123',
            'printer_id': printer_id,
            'filename': filename,
            'created_at': discovery_time.isoformat(),
            'status': 'running'
        }
        monitoring_service.database.list_jobs = AsyncMock(return_value=[existing_job])

        result = await monitoring_service._find_existing_job(printer_id, filename, discovery_time)

        assert result is not None
        assert result['id'] == 'job_123'

    @pytest.mark.asyncio
    async def test_find_existing_job_within_time_window(self, monitoring_service):
        """Should find job within ±5 minute window."""
        printer_id = "bambu_001"
        filename = "model.3mf"
        discovery_time = datetime(2025, 1, 9, 10, 30, 0)

        # Job created 3 minutes earlier (within window)
        existing_job = {
            'id': 'job_123',
            'printer_id': printer_id,
            'filename': filename,
            'created_at': (discovery_time - timedelta(minutes=3)).isoformat(),
            'status': 'running'
        }
        monitoring_service.database.list_jobs = AsyncMock(return_value=[existing_job])

        result = await monitoring_service._find_existing_job(printer_id, filename, discovery_time)

        assert result is not None
        assert result['id'] == 'job_123'

    @pytest.mark.asyncio
    async def test_find_existing_job_outside_time_window(self, monitoring_service):
        """Should NOT find job outside ±5 minute window."""
        printer_id = "bambu_001"
        filename = "model.3mf"
        discovery_time = datetime(2025, 1, 9, 10, 30, 0)

        # Job created 6 minutes earlier (outside ±5 minute window)
        existing_job = {
            'id': 'job_123',
            'printer_id': printer_id,
            'filename': filename,
            'created_at': (discovery_time - timedelta(minutes=6)).isoformat(),
            'status': 'running'
        }
        monitoring_service.database.list_jobs = AsyncMock(return_value=[existing_job])

        result = await monitoring_service._find_existing_job(printer_id, filename, discovery_time)

        assert result is None

    @pytest.mark.asyncio
    async def test_find_existing_job_handles_cache_prefix(self, monitoring_service):
        """Should match filenames with and without cache/ prefix."""
        printer_id = "bambu_001"
        filename = "cache/model.3mf"
        discovery_time = datetime(2025, 1, 9, 10, 30, 0)

        # Job in database without cache/ prefix
        existing_job = {
            'id': 'job_123',
            'printer_id': printer_id,
            'filename': 'model.3mf',  # No cache/ prefix
            'created_at': discovery_time.isoformat(),
            'status': 'running'
        }
        monitoring_service.database.list_jobs = AsyncMock(return_value=[existing_job])

        result = await monitoring_service._find_existing_job(printer_id, filename, discovery_time)

        assert result is not None
        assert result['id'] == 'job_123'

    @pytest.mark.asyncio
    async def test_find_existing_job_different_filename(self, monitoring_service):
        """Should NOT find job with different filename."""
        printer_id = "bambu_001"
        filename = "model1.3mf"
        discovery_time = datetime(2025, 1, 9, 10, 30, 0)

        # Job with different filename
        existing_job = {
            'id': 'job_123',
            'printer_id': printer_id,
            'filename': 'model2.3mf',  # Different file
            'created_at': discovery_time.isoformat(),
            'status': 'running'
        }
        monitoring_service.database.list_jobs = AsyncMock(return_value=[existing_job])

        result = await monitoring_service._find_existing_job(printer_id, filename, discovery_time)

        assert result is None

    @pytest.mark.asyncio
    async def test_find_existing_job_no_jobs(self, monitoring_service):
        """Should return None when no jobs exist."""
        printer_id = "bambu_001"
        filename = "model.3mf"
        discovery_time = datetime(2025, 1, 9, 10, 30, 0)

        monitoring_service.database.list_jobs = AsyncMock(return_value=[])

        result = await monitoring_service._find_existing_job(printer_id, filename, discovery_time)

        assert result is None


class TestAutoCreateJobLogic:
    """Test auto-job creation triggering logic."""

    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service with mocked dependencies."""
        mock_db = AsyncMock(spec=Database)
        mock_event_service = AsyncMock(spec=EventService)
        mock_job_service = AsyncMock()
        mock_connection_service = Mock()

        service = PrinterMonitoringService(
            database=mock_db,
            event_service=mock_event_service,
            job_service=mock_job_service,
            connection_service=mock_connection_service
        )

        # Enable auto-creation
        service.auto_create_jobs = True

        return service

    @pytest.mark.asyncio
    async def test_auto_create_job_only_when_printing(self, monitoring_service):
        """Should only create jobs when status is PRINTING."""
        # Non-printing status
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.ONLINE,
            current_job="model.3mf",
            timestamp=datetime.now()
        )

        await monitoring_service._auto_create_job_if_needed(status)

        # Should not create job
        assert monitoring_service.job_service.create_job.call_count == 0

    @pytest.mark.asyncio
    async def test_auto_create_job_requires_filename(self, monitoring_service):
        """Should only create jobs when filename is known."""
        # Printing but no filename
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job=None,
            timestamp=datetime.now()
        )

        await monitoring_service._auto_create_job_if_needed(status)

        # Should not create job
        assert monitoring_service.job_service.create_job.call_count == 0

    @pytest.mark.asyncio
    async def test_auto_create_job_tracks_discovery_time(self, monitoring_service):
        """Should track discovery time for first occurrence."""
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            timestamp=datetime.now()
        )

        # Mock no existing job
        monitoring_service.database.list_jobs = AsyncMock(return_value=[])
        monitoring_service.job_service.create_job = AsyncMock(return_value={'id': 'job_123'})

        await monitoring_service._auto_create_job_if_needed(status)

        # Check discovery time was tracked
        discovery_key = "bambu_001:model.3mf"
        assert discovery_key in monitoring_service._print_discoveries
        assert isinstance(monitoring_service._print_discoveries[discovery_key], datetime)

    @pytest.mark.asyncio
    async def test_auto_create_job_deduplication_cache(self, monitoring_service):
        """Should not create duplicate jobs using in-memory cache."""
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=50,
            timestamp=datetime.now()
        )

        # Mock no existing job in database
        monitoring_service.database.list_jobs = AsyncMock(return_value=[])
        monitoring_service.job_service.create_job = AsyncMock(return_value={'id': 'job_123'})

        # First call - should create job
        await monitoring_service._auto_create_job_if_needed(status)
        assert monitoring_service.job_service.create_job.call_count == 1

        # Second call - should use cache, not create duplicate
        await monitoring_service._auto_create_job_if_needed(status)
        assert monitoring_service.job_service.create_job.call_count == 1  # Still 1, no duplicate

    @pytest.mark.asyncio
    async def test_auto_create_job_with_start_time(self, monitoring_service):
        """Should include printer-reported start time when available."""
        start_time = datetime.now() - timedelta(minutes=10)
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=50,
            print_start_time=start_time,
            elapsed_time_minutes=10,
            timestamp=datetime.now()
        )

        # Mock dependencies
        monitoring_service.database.list_jobs = AsyncMock(return_value=[])
        monitoring_service.job_service.create_job = AsyncMock(return_value={'id': 'job_123'})

        # Mock connection service for printer type
        mock_printer = Mock()
        mock_printer.__class__.__name__ = "BambuLabPrinter"
        monitoring_service.connection_service.printer_instances = {"bambu_001": mock_printer}

        await monitoring_service._auto_create_job_if_needed(status)

        # Verify job was created with start_time
        call_args = monitoring_service.job_service.create_job.call_args
        job_data = call_args[0][0]

        assert job_data['start_time'] == start_time.isoformat()
        assert job_data['status'] == 'running'

    @pytest.mark.asyncio
    async def test_auto_create_job_startup_flag(self, monitoring_service):
        """Should set startup flag when is_startup=True."""
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=50,
            timestamp=datetime.now()
        )

        # Mock dependencies
        monitoring_service.database.list_jobs = AsyncMock(return_value=[])
        monitoring_service.job_service.create_job = AsyncMock(return_value={'id': 'job_123'})

        mock_printer = Mock()
        mock_printer.__class__.__name__ = "BambuLabPrinter"
        monitoring_service.connection_service.printer_instances = {"bambu_001": mock_printer}

        await monitoring_service._auto_create_job_if_needed(status, is_startup=True)

        # Verify startup flag in customer_info
        call_args = monitoring_service.job_service.create_job.call_args
        job_data = call_args[0][0]

        customer_info = job_data['customer_info']
        # Handle both dict and JSON string formats
        if isinstance(customer_info, str):
            customer_info = json.loads(customer_info)
        assert customer_info['discovered_on_startup'] is True
        assert customer_info['auto_created'] is True

    @pytest.mark.asyncio
    async def test_auto_create_job_handles_database_existing(self, monitoring_service):
        """Should not create job if one exists in database."""
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            timestamp=datetime.now()
        )

        # Mock existing job in database
        existing_job = {
            'id': 'job_existing',
            'printer_id': 'bambu_001',
            'filename': 'model.3mf',
            'created_at': datetime.now().isoformat(),
            'status': 'running'
        }
        monitoring_service.database.list_jobs = AsyncMock(return_value=[existing_job])
        monitoring_service.job_service.create_job = AsyncMock()

        await monitoring_service._auto_create_job_if_needed(status)

        # Should not create new job
        assert monitoring_service.job_service.create_job.call_count == 0


class TestDiscoveryTracking:
    """Test print discovery tracking and cleanup."""

    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service instance."""
        mock_db = AsyncMock(spec=Database)
        mock_event_service = AsyncMock(spec=EventService)
        return PrinterMonitoringService(
            database=mock_db,
            event_service=mock_event_service
        )

    @pytest.mark.asyncio
    async def test_discovery_tracking_first_occurrence(self, monitoring_service):
        """Should track first occurrence of a print."""
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            timestamp=datetime.now()
        )

        monitoring_service.database.list_jobs = AsyncMock(return_value=[])
        monitoring_service.job_service = AsyncMock()
        monitoring_service.job_service.create_job = AsyncMock(return_value={'id': 'job_123'})
        monitoring_service.auto_create_jobs = True

        await monitoring_service._auto_create_job_if_needed(status)

        # Should have tracked discovery
        discovery_key = "bambu_001:model.3mf"
        assert discovery_key in monitoring_service._print_discoveries

    @pytest.mark.asyncio
    async def test_discovery_tracking_reuses_time(self, monitoring_service):
        """Should reuse discovery time for subsequent status updates."""
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            timestamp=datetime.now()
        )

        monitoring_service.database.list_jobs = AsyncMock(return_value=[])
        monitoring_service.job_service = AsyncMock()
        monitoring_service.job_service.create_job = AsyncMock(return_value={'id': 'job_123'})
        monitoring_service.auto_create_jobs = True

        # First call
        await monitoring_service._auto_create_job_if_needed(status)
        discovery_key = "bambu_001:model.3mf"
        first_discovery_time = monitoring_service._print_discoveries[discovery_key]

        # Second call (simulating next status update)
        await monitoring_service._auto_create_job_if_needed(status)
        second_discovery_time = monitoring_service._print_discoveries[discovery_key]

        # Should be same discovery time
        assert first_discovery_time == second_discovery_time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
