"""
Integration tests for automated job creation feature.

Tests end-to-end scenarios including:
- Auto-creation on print start
- Auto-creation on system startup
- Same file printed twice
- Pause/resume without duplicates
- Network reconnection handling
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.services.printer_monitoring_service import PrinterMonitoringService
from src.services.printer_connection_service import PrinterConnectionService
from src.models.printer import PrinterStatus, PrinterStatusUpdate, PrinterType
from src.database.database import Database
from src.services.event_service import EventService
from src.services.job_service import JobService
from src.services.config_service import ConfigService


@pytest.fixture
async def test_services():
    """Create full service stack for integration testing."""
    # Create real database
    import tempfile
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()

    database = Database(temp_db.name)
    await database.initialize()

    event_service = EventService()
    job_service = JobService(database, event_service)

    # Create mock config service
    mock_config_service = Mock(spec=ConfigService)
    mock_config_service.settings = Mock()
    mock_config_service.settings.job_creation_auto_create = True

    # Create monitoring service
    monitoring_service = PrinterMonitoringService(
        database=database,
        event_service=event_service,
        job_service=job_service,
        config_service=mock_config_service
    )

    # Set auto-creation enabled
    monitoring_service.auto_create_jobs = True

    yield {
        'database': database,
        'event_service': event_service,
        'job_service': job_service,
        'monitoring_service': monitoring_service,
        'db_file': temp_db.name
    }

    # Cleanup
    await database.close()
    os.unlink(temp_db.name)


class TestPrintStartAutoCreation:
    """Test auto-creation when print starts (ONLINE → PRINTING transition)."""

    @pytest.mark.asyncio
    async def test_auto_create_on_print_start(self, test_services):
        """Should auto-create job when printer starts printing."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        # Simulate printer starting to print
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="test_cube.3mf",
            progress=5,
            print_start_time=datetime.now(),
            timestamp=datetime.now()
        )

        # Trigger auto-creation
        await monitoring._auto_create_job_if_needed(status)

        # Verify job was created
        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1
        assert jobs[0]['filename'] == "test_cube.3mf"
        assert jobs[0]['status'] == 'running'
        assert jobs[0]['job_name'] == "test_cube"  # Extension removed

    @pytest.mark.asyncio
    async def test_auto_create_includes_start_time(self, test_services):
        """Should include printer-reported start time when available."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        start_time = datetime.now() - timedelta(minutes=5)
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=10,
            print_start_time=start_time,
            elapsed_time_minutes=5,
            timestamp=datetime.now()
        )

        await monitoring._auto_create_job_if_needed(status)

        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1

        # Start time should be set
        job = jobs[0]
        assert job['start_time'] is not None

        # Check metadata
        customer_info = json.loads(job['customer_info'])
        assert customer_info['auto_created'] is True
        assert customer_info['printer_start_time'] is not None

    @pytest.mark.asyncio
    async def test_auto_create_without_start_time(self, test_services):
        """Should create job even without printer-reported start time."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=10,
            print_start_time=None,  # No start time available
            timestamp=datetime.now()
        )

        await monitoring._auto_create_job_if_needed(status)

        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1
        assert jobs[0]['filename'] == "model.3mf"
        # start_time can be None - discovery time is used for deduplication


class TestStartupDetection:
    """Test auto-creation when system starts with print in progress."""

    @pytest.mark.asyncio
    async def test_auto_create_on_startup(self, test_services):
        """Should auto-create job when Printernizer starts and printer is already printing."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        # Simulate startup detection
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="ongoing_print.3mf",
            progress=45,  # Mid-print
            print_start_time=datetime.now() - timedelta(minutes=30),
            elapsed_time_minutes=30,
            timestamp=datetime.now()
        )

        # Call with is_startup=True
        await monitoring._auto_create_job_if_needed(status, is_startup=True)

        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1
        assert jobs[0]['filename'] == "ongoing_print.3mf"

        # Check startup flag
        customer_info = json.loads(jobs[0]['customer_info'])
        assert customer_info['auto_created'] is True
        assert customer_info['discovered_on_startup'] is True


class TestDeduplicationScenarios:
    """Test deduplication in various scenarios."""

    @pytest.mark.asyncio
    async def test_same_file_twice_creates_two_jobs(self, test_services):
        """Printing same file twice should create two separate jobs."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        # First print
        status1 = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="repeated_model.3mf",
            progress=50,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status1)

        # Simulate print completion
        await asyncio.sleep(0.1)
        monitoring._print_discoveries.clear()  # Clear discovery tracking

        # Second print (5 minutes later)
        await asyncio.sleep(0.1)
        status2 = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="repeated_model.3mf",
            progress=10,
            timestamp=datetime.now() + timedelta(minutes=5)
        )
        await monitoring._auto_create_job_if_needed(status2)

        # Should have two separate jobs
        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 2
        assert all(j['filename'] == "repeated_model.3mf" for j in jobs)

    @pytest.mark.asyncio
    async def test_multiple_status_updates_no_duplicate(self, test_services):
        """Multiple status updates during same print should not create duplicates."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        # Simulate multiple status updates (polling every 30 seconds)
        for progress in [10, 20, 30, 40, 50]:
            status = PrinterStatusUpdate(
                printer_id="bambu_001",
                status=PrinterStatus.PRINTING,
                current_job="model.3mf",
                progress=progress,
                timestamp=datetime.now()
            )
            await monitoring._auto_create_job_if_needed(status)
            await asyncio.sleep(0.05)  # Simulate time between updates

        # Should only have ONE job
        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1

    @pytest.mark.asyncio
    async def test_pause_resume_no_duplicate(self, test_services):
        """Pausing and resuming should not create duplicate job."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        # Start printing
        status_printing = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=30,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status_printing)

        # Pause (status update still has current_job but status=PAUSED)
        status_paused = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PAUSED,
            current_job="model.3mf",
            progress=30,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status_paused)

        # Resume
        status_resumed = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=35,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status_resumed)

        # Should still only have ONE job
        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1

    @pytest.mark.asyncio
    async def test_system_restart_no_duplicate(self, test_services):
        """System restart during print should not create duplicate."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        # Initial print status
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=40,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status)

        # Get the created job
        jobs_before = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs_before) == 1

        # Simulate restart: clear in-memory caches
        monitoring._print_discoveries.clear()
        monitoring._auto_job_cache.clear()

        # Status update after restart (database lookup should find existing job)
        status_after_restart = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=45,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status_after_restart)

        # Should still only have ONE job (database deduplication)
        jobs_after = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs_after) == 1
        assert jobs_after[0]['id'] == jobs_before[0]['id']  # Same job

    @pytest.mark.asyncio
    async def test_manual_job_exists_no_duplicate(self, test_services):
        """Should not create auto job if manual job already exists."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        # Create manual job first
        manual_job_data = {
            'printer_id': 'bambu_001',
            'printer_type': 'bambu_lab',
            'job_name': 'Manual Job',
            'filename': 'model.3mf',
            'status': 'running',
            'is_business': True
        }
        manual_job_id = await job_service.create_job(manual_job_data)

        # Now simulate print status update
        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=30,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status)

        # Should still only have one job (the manual one)
        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1
        assert jobs[0]['id'] == manual_job_id


class TestMultiplePrinters:
    """Test scenarios with multiple printers."""

    @pytest.mark.asyncio
    async def test_multiple_printers_same_file(self, test_services):
        """Multiple printers printing same file should create separate jobs."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        # Bambu printer printing
        status_bambu = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="popular_model.3mf",
            progress=25,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status_bambu)

        # Prusa printer printing same file
        status_prusa = PrinterStatusUpdate(
            printer_id="prusa_001",
            status=PrinterStatus.PRINTING,
            current_job="popular_model.3mf",
            progress=30,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status_prusa)

        # Should have TWO jobs (different printers)
        bambu_jobs = await job_service.list_jobs(printer_id="bambu_001")
        prusa_jobs = await job_service.list_jobs(printer_id="prusa_001")

        assert len(bambu_jobs) == 1
        assert len(prusa_jobs) == 1
        assert bambu_jobs[0]['printer_id'] == "bambu_001"
        assert prusa_jobs[0]['printer_id'] == "prusa_001"


class TestFilenameVariations:
    """Test handling of filename variations."""

    @pytest.mark.asyncio
    async def test_cache_prefix_normalization(self, test_services):
        """Should normalize cache/ prefix in filenames."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        # First status with cache/ prefix
        status1 = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="cache/model.3mf",
            progress=20,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status1)

        # Second status without cache/ prefix (but same file)
        status2 = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",  # No cache/ prefix
            progress=25,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status2)

        # Should only have ONE job (cache/ prefix normalized)
        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1

    @pytest.mark.asyncio
    async def test_cleaned_job_name(self, test_services):
        """Should create clean job names without extensions."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="cache/my_model_v2.3mf",
            progress=10,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status)

        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1
        # Job name should have cache/ and .3mf removed
        assert jobs[0]['job_name'] == "my_model_v2"
        # But filename should be preserved
        assert jobs[0]['filename'] == "cache/my_model_v2.3mf"


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_disabled_auto_creation(self, test_services):
        """Should not create jobs when auto-creation is disabled."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        # Disable auto-creation
        monitoring.auto_create_jobs = False

        status = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=50,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status)

        # Should NOT have created a job
        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 0

    @pytest.mark.asyncio
    async def test_concurrent_status_updates(self, test_services):
        """Should handle concurrent status updates without creating duplicates."""
        monitoring = test_services['monitoring_service']
        job_service = test_services['job_service']

        # Simulate multiple concurrent status updates
        async def send_status_update(progress):
            status = PrinterStatusUpdate(
                printer_id="bambu_001",
                status=PrinterStatus.PRINTING,
                current_job="model.3mf",
                progress=progress,
                timestamp=datetime.now()
            )
            await monitoring._auto_create_job_if_needed(status)

        # Fire off multiple concurrent updates
        await asyncio.gather(
            send_status_update(10),
            send_status_update(11),
            send_status_update(12),
            send_status_update(13),
            send_status_update(14)
        )

        # Should only have ONE job (lock prevents race conditions)
        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
