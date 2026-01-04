"""
Unit tests for Printer Monitoring Service.
Tests status monitoring, auto-download, and auto-job creation.

Sprint 2 Phase 1 - Core Service Test Coverage.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from src.services.printer_monitoring_service import PrinterMonitoringService
from src.services.event_service import EventService
from src.models.printer import PrinterStatus, PrinterStatusUpdate


class TestPrinterMonitoringServiceInitialization:
    """Test PrinterMonitoringService initialization."""

    @pytest.fixture
    def mock_database(self):
        """Create mock database."""
        db = MagicMock()
        db._connection = MagicMock()
        db.list_jobs = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def mock_event_service(self):
        """Create mock event service."""
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()
        return event_service

    def test_initialization(self, mock_database, mock_event_service):
        """Test service initializes correctly."""
        service = PrinterMonitoringService(mock_database, mock_event_service)

        assert service.database is mock_database
        assert service.event_service is mock_event_service
        assert service.monitoring_active == False
        assert service.auto_create_jobs == True

    def test_initialization_with_optional_services(self, mock_database, mock_event_service):
        """Test initialization with optional service dependencies."""
        mock_file_service = MagicMock()
        mock_connection_service = MagicMock()

        service = PrinterMonitoringService(
            mock_database,
            mock_event_service,
            file_service=mock_file_service,
            connection_service=mock_connection_service
        )

        assert service.file_service is mock_file_service
        assert service.connection_service is mock_connection_service


class TestIsPrintFile:
    """Test print file detection."""

    @pytest.fixture
    def service(self):
        """Create monitoring service for testing."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()
        return PrinterMonitoringService(db, event_service)

    def test_is_print_file_gcode(self, service):
        """Test .gcode files are detected as printable."""
        assert service._is_print_file("model.gcode") == True

    def test_is_print_file_bgcode(self, service):
        """Test .bgcode files are detected as printable."""
        assert service._is_print_file("model.bgcode") == True

    def test_is_print_file_3mf(self, service):
        """Test .3mf files are detected as printable."""
        assert service._is_print_file("model.3mf") == True

    def test_is_print_file_case_insensitive(self, service):
        """Test file detection is case insensitive."""
        assert service._is_print_file("MODEL.GCODE") == True
        assert service._is_print_file("Model.3MF") == True

    def test_is_print_file_not_printable(self, service):
        """Test non-printable files are rejected."""
        assert service._is_print_file("readme.txt") == False
        assert service._is_print_file("image.png") == False
        assert service._is_print_file("config.json") == False


class TestCleanFilename:
    """Test filename cleaning for job names."""

    @pytest.fixture
    def service(self):
        """Create monitoring service for testing."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()
        return PrinterMonitoringService(db, event_service)

    def test_clean_filename_removes_cache_prefix(self, service):
        """Test cache/ prefix is removed."""
        result = service._clean_filename("cache/model.3mf")
        assert result == "model"

    def test_clean_filename_removes_gcode_extension(self, service):
        """Test .gcode extension is removed."""
        result = service._clean_filename("model.gcode")
        assert result == "model"

    def test_clean_filename_removes_bgcode_extension(self, service):
        """Test .bgcode extension is removed."""
        result = service._clean_filename("model.bgcode")
        assert result == "model"

    def test_clean_filename_removes_3mf_extension(self, service):
        """Test .3mf extension is removed."""
        result = service._clean_filename("model.3mf")
        assert result == "model"

    def test_clean_filename_removes_stl_extension(self, service):
        """Test .stl extension is removed."""
        result = service._clean_filename("model.stl")
        assert result == "model"

    def test_clean_filename_strips_whitespace(self, service):
        """Test whitespace is stripped."""
        result = service._clean_filename("  model.3mf  ")
        assert result == "model"

    def test_clean_filename_preserves_complex_names(self, service):
        """Test complex filenames are preserved correctly."""
        result = service._clean_filename("cache/My Model V2 (Test).3mf")
        assert result == "My Model V2 (Test)"


class TestMakeJobKey:
    """Test job key generation for deduplication."""

    @pytest.fixture
    def service(self):
        """Create monitoring service for testing."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()
        return PrinterMonitoringService(db, event_service)

    def test_make_job_key_format(self, service):
        """Test job key format is correct."""
        ref_time = datetime(2025, 6, 15, 10, 30, 45)

        key = service._make_job_key("printer_001", "model.3mf", ref_time)

        # Seconds should be truncated
        assert key == "printer_001:model.3mf:2025-06-15T10:30:00"

    def test_make_job_key_removes_cache_prefix(self, service):
        """Test cache/ prefix is removed from filename in key."""
        ref_time = datetime(2025, 6, 15, 10, 30, 0)

        key = service._make_job_key("printer_001", "cache/model.3mf", ref_time)

        assert key == "printer_001:model.3mf:2025-06-15T10:30:00"

    def test_make_job_key_rounds_to_minute(self, service):
        """Test reference time is rounded to minute."""
        ref_time1 = datetime(2025, 6, 15, 10, 30, 0)
        ref_time2 = datetime(2025, 6, 15, 10, 30, 59)

        key1 = service._make_job_key("printer_001", "model.3mf", ref_time1)
        key2 = service._make_job_key("printer_001", "model.3mf", ref_time2)

        # Both should have same key (rounded to same minute)
        assert key1 == key2


class TestLateBindingSetters:
    """Test late binding dependency setters."""

    @pytest.fixture
    def service(self):
        """Create monitoring service for testing."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()
        return PrinterMonitoringService(db, event_service)

    def test_set_file_service(self, service):
        """Test setting file service dependency."""
        mock_file_service = MagicMock()

        service.set_file_service(mock_file_service)

        assert service.file_service is mock_file_service

    def test_set_connection_service(self, service):
        """Test setting connection service dependency."""
        mock_connection_service = MagicMock()

        service.set_connection_service(mock_connection_service)

        assert service.connection_service is mock_connection_service

    def test_set_job_service(self, service):
        """Test setting job service dependency."""
        mock_job_service = MagicMock()

        service.set_job_service(mock_job_service)

        assert service.job_service is mock_job_service

    def test_set_config_service_loads_auto_create(self, service):
        """Test setting config service loads auto-create setting."""
        mock_config_service = MagicMock()
        mock_config_service.settings = MagicMock()
        mock_config_service.settings.job_creation_auto_create = False

        service.set_config_service(mock_config_service)

        assert service.config_service is mock_config_service
        assert service.auto_create_jobs == False


class TestStatusCallback:
    """Test status callback setup."""

    @pytest.fixture
    def service(self):
        """Create monitoring service for testing."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()
        return PrinterMonitoringService(db, event_service)

    def test_setup_status_callback_registers_handler(self, service):
        """Test status callback is registered on printer instance."""
        mock_printer = MagicMock()
        mock_printer.add_status_callback = MagicMock()

        service.setup_status_callback(mock_printer)

        mock_printer.add_status_callback.assert_called_once()


class TestStartStopMonitoring:
    """Test monitoring start/stop functionality."""

    @pytest.fixture
    def service(self):
        """Create monitoring service for testing."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()
        return PrinterMonitoringService(db, event_service)

    @pytest.mark.asyncio
    async def test_start_monitoring(self, service):
        """Test starting monitoring for a printer."""
        mock_printer = MagicMock()
        mock_printer.start_monitoring = AsyncMock()

        result = await service.start_monitoring("printer_001", mock_printer)

        assert result == True
        mock_printer.start_monitoring.assert_called_once()

        # Verify event was emitted with correct structure
        service.event_service.emit_event.assert_called_once()
        call_args = service.event_service.emit_event.call_args
        assert call_args[0][0] == "printer_monitoring_started"
        assert call_args[0][1]["printer_id"] == "printer_001"
        assert "timestamp" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_start_monitoring_failure(self, service):
        """Test start monitoring handles failure."""
        mock_printer = MagicMock()
        mock_printer.start_monitoring = AsyncMock(side_effect=Exception("Connection failed"))

        result = await service.start_monitoring("printer_001", mock_printer)

        assert result == False

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, service):
        """Test stopping monitoring for a printer."""
        mock_printer = MagicMock()
        mock_printer.stop_monitoring = AsyncMock()

        result = await service.stop_monitoring("printer_001", mock_printer)

        assert result == True
        mock_printer.stop_monitoring.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_monitoring_failure(self, service):
        """Test stop monitoring handles failure."""
        mock_printer = MagicMock()
        mock_printer.stop_monitoring = AsyncMock(side_effect=Exception("Disconnect failed"))

        result = await service.stop_monitoring("printer_001", mock_printer)

        assert result == False


class TestHandleStatusUpdate:
    """Test status update handling."""

    @pytest.fixture
    def service(self):
        """Create monitoring service with mocked dependencies."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()

        service = PrinterMonitoringService(db, event_service)

        # Mock printer repo
        service.printer_repo = MagicMock()
        service.printer_repo.update_status = AsyncMock()

        return service

    @pytest.mark.asyncio
    async def test_handle_status_update_stores_status(self, service):
        """Test status update is stored in database."""
        status = PrinterStatusUpdate(
            printer_id="printer_001",
            status=PrinterStatus.ONLINE,
            message="Printer online",
            timestamp=datetime.now()
        )

        await service._handle_status_update(status)

        service.printer_repo.update_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_status_update_emits_event(self, service):
        """Test status update emits event."""
        status = PrinterStatusUpdate(
            printer_id="printer_001",
            status=PrinterStatus.ONLINE,
            message="Printer online",
            timestamp=datetime.now()
        )

        await service._handle_status_update(status)

        service.event_service.emit_event.assert_called_with(
            "printer_status_update",
            pytest.approx({
                "printer_id": "printer_001",
                "status": "online",
                "message": "Printer online",
                "temperature_bed": None,
                "temperature_nozzle": None,
                "progress": None,
                "current_job": None,
                "current_job_file_id": None,
                "current_job_has_thumbnail": None,
                "current_job_thumbnail_url": None,
                "timestamp": pytest.approx(status.timestamp.isoformat(), abs=5)
            }, rel=1e-2)
        )


class TestCheckAutoDownload:
    """Test auto-download checking logic."""

    @pytest.fixture
    def service(self):
        """Create monitoring service with file service."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()

        service = PrinterMonitoringService(db, event_service)
        service.file_service = MagicMock()
        service.file_service.download_file = AsyncMock(return_value={"status": "success"})

        # Mock printer repo
        service.printer_repo = MagicMock()
        service.printer_repo.update_status = AsyncMock()

        return service

    @pytest.mark.asyncio
    async def test_check_auto_download_triggers_for_printing(self, service):
        """Test auto-download triggers when printing with no file_id."""
        status = PrinterStatusUpdate(
            printer_id="printer_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            current_job_file_id=None,
            timestamp=datetime.now()
        )

        # The auto-download runs in a background task
        await service._check_auto_download(status)

        # Wait a bit for background task
        await asyncio.sleep(0.1)

        # File should be in attempts
        assert "model.3mf" in service._auto_download_attempts.get("printer_001", set())

    @pytest.mark.asyncio
    async def test_check_auto_download_skips_non_printing(self, service):
        """Test auto-download doesn't trigger when not printing."""
        status = PrinterStatusUpdate(
            printer_id="printer_001",
            status=PrinterStatus.ONLINE,
            current_job="model.3mf",
            timestamp=datetime.now()
        )

        await service._check_auto_download(status)

        assert len(service._auto_download_attempts.get("printer_001", set())) == 0

    @pytest.mark.asyncio
    async def test_check_auto_download_skips_if_already_attempted(self, service):
        """Test auto-download doesn't retry already attempted files."""
        service._auto_download_attempts["printer_001"] = {"model.3mf"}

        status = PrinterStatusUpdate(
            printer_id="printer_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            current_job_file_id=None,
            timestamp=datetime.now()
        )

        await service._check_auto_download(status)

        # Should still just have the one attempt
        assert len(service._auto_download_attempts["printer_001"]) == 1


class TestDownloadCurrentJobFile:
    """Test current job file download functionality."""

    @pytest.fixture
    def service(self):
        """Create monitoring service with dependencies."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()

        service = PrinterMonitoringService(db, event_service)
        service.file_service = MagicMock()
        service.file_service.download_file = AsyncMock(return_value={"status": "success", "file_id": "file_001"})
        service.file_service.find_file_by_name = AsyncMock(return_value=None)

        return service

    @pytest.mark.asyncio
    async def test_download_without_file_service(self):
        """Test download returns error without file service."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()

        service = PrinterMonitoringService(db, event_service)
        service.file_service = None

        mock_printer = MagicMock()

        result = await service.download_current_job_file("printer_001", mock_printer)

        assert result["status"] == "error"
        assert "unavailable" in result["message"]

    @pytest.mark.asyncio
    async def test_download_connects_if_needed(self, service):
        """Test download connects to printer if not connected."""
        mock_printer = MagicMock()
        mock_printer.is_connected = False
        mock_printer.connect = AsyncMock()
        mock_printer.get_status = AsyncMock(return_value=MagicMock(current_job="model.3mf"))

        await service.download_current_job_file("printer_001", mock_printer)

        mock_printer.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_no_active_job(self, service):
        """Test download returns no_active_job when not printing."""
        mock_printer = MagicMock()
        mock_printer.is_connected = True
        mock_printer.get_status = AsyncMock(return_value=MagicMock(current_job=None))

        result = await service.download_current_job_file("printer_001", mock_printer)

        assert result["status"] == "no_active_job"


class TestAutoCreateJobIfNeeded:
    """Test auto job creation logic."""

    @pytest.fixture
    def service(self):
        """Create monitoring service with job service."""
        db = MagicMock()
        db._connection = MagicMock()
        db.list_jobs = AsyncMock(return_value=[])

        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()

        service = PrinterMonitoringService(db, event_service)
        service.job_service = MagicMock()
        service.job_service.create_job = AsyncMock(return_value="job_001")
        service.auto_create_jobs = True

        return service

    @pytest.mark.asyncio
    async def test_auto_create_disabled(self, service):
        """Test auto-create is skipped when disabled."""
        service.auto_create_jobs = False

        status = PrinterStatusUpdate(
            printer_id="printer_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            timestamp=datetime.now()
        )

        await service._auto_create_job_if_needed(status)

        service.job_service.create_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_auto_create_skips_non_printing(self, service):
        """Test auto-create is skipped when not printing."""
        status = PrinterStatusUpdate(
            printer_id="printer_001",
            status=PrinterStatus.ONLINE,
            current_job="model.3mf",
            timestamp=datetime.now()
        )

        await service._auto_create_job_if_needed(status)

        service.job_service.create_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_auto_create_skips_no_job_name(self, service):
        """Test auto-create is skipped when no current job."""
        status = PrinterStatusUpdate(
            printer_id="printer_001",
            status=PrinterStatus.PRINTING,
            current_job=None,
            timestamp=datetime.now()
        )

        await service._auto_create_job_if_needed(status)

        service.job_service.create_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_auto_create_creates_job(self, service):
        """Test auto-create creates job for new print."""
        status = PrinterStatusUpdate(
            printer_id="printer_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            timestamp=datetime.now()
        )

        await service._auto_create_job_if_needed(status)

        service.job_service.create_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_create_tracks_discovery(self, service):
        """Test auto-create tracks print discovery time."""
        status = PrinterStatusUpdate(
            printer_id="printer_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            timestamp=datetime.now()
        )

        await service._auto_create_job_if_needed(status)

        assert "printer_001:model.3mf" in service._print_discoveries


class TestFindActiveJob:
    """Test active job finding logic."""

    @pytest.fixture
    def service(self):
        """Create monitoring service for testing."""
        db = MagicMock()
        db._connection = MagicMock()
        db.list_jobs = AsyncMock(return_value=[])

        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()

        return PrinterMonitoringService(db, event_service)

    @pytest.mark.asyncio
    async def test_find_active_job_not_found(self, service):
        """Test finding no active job returns None."""
        result = await service._find_active_job("printer_001", "model.3mf")

        assert result is None

    @pytest.mark.asyncio
    async def test_find_active_job_found(self, service):
        """Test finding active job by filename."""
        service.database.list_jobs = AsyncMock(return_value=[
            {"id": "job_001", "filename": "model.3mf", "status": "running"}
        ])

        result = await service._find_active_job("printer_001", "model.3mf")

        assert result is not None
        assert result["id"] == "job_001"

    @pytest.mark.asyncio
    async def test_find_active_job_strips_cache_prefix(self, service):
        """Test finding active job handles cache/ prefix."""
        service.database.list_jobs = AsyncMock(return_value=[
            {"id": "job_001", "filename": "model.3mf", "status": "running"}
        ])

        result = await service._find_active_job("printer_001", "cache/model.3mf")

        assert result is not None


class TestFindExistingJob:
    """Test existing job finding with time window."""

    @pytest.fixture
    def service(self):
        """Create monitoring service for testing."""
        db = MagicMock()
        db._connection = MagicMock()
        db.list_jobs = AsyncMock(return_value=[])

        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()

        return PrinterMonitoringService(db, event_service)

    @pytest.mark.asyncio
    async def test_find_existing_job_not_found(self, service):
        """Test finding no existing job returns None."""
        ref_time = datetime.now()

        result = await service._find_existing_job("printer_001", "model.3mf", ref_time)

        assert result is None

    @pytest.mark.asyncio
    async def test_find_existing_job_by_start_time(self, service):
        """Test finding existing job by matching start_time."""
        ref_time = datetime.now()
        service.database.list_jobs = AsyncMock(return_value=[
            {
                "id": "job_001",
                "filename": "model.3mf",
                "start_time": ref_time.isoformat()
            }
        ])

        result = await service._find_existing_job("printer_001", "model.3mf", ref_time)

        assert result is not None
        assert result["id"] == "job_001"

    @pytest.mark.asyncio
    async def test_find_existing_job_within_window(self, service):
        """Test finding existing job within ±5 minute window."""
        ref_time = datetime.now()
        job_time = ref_time - timedelta(minutes=3)

        service.database.list_jobs = AsyncMock(return_value=[
            {
                "id": "job_001",
                "filename": "model.3mf",
                "start_time": job_time.isoformat()
            }
        ])

        result = await service._find_existing_job("printer_001", "model.3mf", ref_time)

        assert result is not None

    @pytest.mark.asyncio
    async def test_find_existing_job_outside_window(self, service):
        """Test not finding job outside time window."""
        ref_time = datetime.now()
        job_time = ref_time - timedelta(minutes=10)  # Outside ±5 min window

        service.database.list_jobs = AsyncMock(return_value=[
            {
                "id": "job_001",
                "filename": "model.3mf",
                "start_time": job_time.isoformat()
            }
        ])

        result = await service._find_existing_job("printer_001", "model.3mf", ref_time)

        assert result is None


class TestShutdown:
    """Test graceful shutdown functionality."""

    @pytest.fixture
    def service(self):
        """Create monitoring service for testing."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()
        return PrinterMonitoringService(db, event_service)

    @pytest.mark.asyncio
    async def test_shutdown_no_tasks(self, service):
        """Test shutdown with no background tasks."""
        # Should not raise
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_waits_for_tasks(self, service):
        """Test shutdown waits for background tasks."""
        # Create a mock task
        async def slow_task():
            await asyncio.sleep(0.1)

        task = service._create_background_task(slow_task())

        # Shutdown should wait for task
        await service.shutdown()

        # Task set should be empty after shutdown
        assert len(service._background_tasks) == 0


class TestBackgroundTaskTracking:
    """Test background task creation and tracking."""

    @pytest.fixture
    def service(self):
        """Create monitoring service for testing."""
        db = MagicMock()
        db._connection = MagicMock()
        event_service = MagicMock(spec=EventService)
        event_service.emit_event = AsyncMock()
        return PrinterMonitoringService(db, event_service)

    @pytest.mark.asyncio
    async def test_create_background_task_tracks_task(self, service):
        """Test created task is tracked."""
        async def simple_task():
            await asyncio.sleep(0.01)

        task = service._create_background_task(simple_task())

        assert task in service._background_tasks

        await task

    @pytest.mark.asyncio
    async def test_create_background_task_removes_on_done(self, service):
        """Test completed task is removed from tracking."""
        async def simple_task():
            await asyncio.sleep(0.01)

        task = service._create_background_task(simple_task())
        await task

        # Give callback time to run
        await asyncio.sleep(0.01)

        assert task not in service._background_tasks
