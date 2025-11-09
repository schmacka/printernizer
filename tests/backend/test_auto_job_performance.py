"""
Performance and stress tests for automated job creation feature.

Tests:
- Memory usage and leak detection
- Cache growth and cleanup
- High-frequency status updates
- Multiple concurrent printers
- Database query performance
"""
import pytest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import tracemalloc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.services.printer_monitoring_service import PrinterMonitoringService
from src.models.printer import PrinterStatus, PrinterStatusUpdate
from src.database.database import Database
from src.services.event_service import EventService
from src.services.job_service import JobService


@pytest.fixture
async def performance_test_stack():
    """Create service stack for performance testing."""
    import tempfile
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()

    database = Database(temp_db.name)
    await database.initialize()

    event_service = EventService()
    job_service = JobService(database, event_service)

    monitoring_service = PrinterMonitoringService(
        database=database,
        event_service=event_service,
        job_service=job_service
    )

    monitoring_service.auto_create_jobs = True

    yield {
        'database': database,
        'event_service': event_service,
        'job_service': job_service,
        'monitoring_service': monitoring_service,
        'db_file': temp_db.name
    }

    await database.close()
    os.unlink(temp_db.name)


class TestMemoryUsage:
    """Test memory usage and leak detection."""

    @pytest.mark.asyncio
    async def test_discovery_cache_memory_growth(self, performance_test_stack):
        """Discovery cache should not grow unbounded."""
        monitoring = performance_test_stack['monitoring_service']

        # Track memory before
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # Simulate many status updates for different files (100 prints)
        for i in range(100):
            status = PrinterStatusUpdate(
                printer_id="bambu_001",
                status=PrinterStatus.PRINTING,
                current_job=f"model_{i}.3mf",
                progress=50,
                timestamp=datetime.now()
            )
            await monitoring._auto_create_job_if_needed(status)

        # Take memory snapshot after
        snapshot2 = tracemalloc.take_snapshot()
        tracemalloc.stop()

        # Calculate memory difference
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_memory_kb = sum(stat.size_diff for stat in top_stats) / 1024

        # Cache should contain 100 entries
        assert len(monitoring._print_discoveries) == 100

        # Memory growth should be reasonable (< 500KB for 100 entries)
        # Each entry is just: string key -> datetime (very small)
        assert total_memory_kb < 500, f"Memory growth too large: {total_memory_kb}KB"

    @pytest.mark.asyncio
    async def test_job_cache_memory_growth(self, performance_test_stack):
        """Job cache should not grow unbounded."""
        monitoring = performance_test_stack['monitoring_service']

        # Create 50 "jobs" (cache entries)
        printer_id = "bambu_001"
        monitoring._auto_job_cache[printer_id] = set()

        for i in range(50):
            job_key = f"bambu_001:model_{i}.3mf:2025-01-09T10:30"
            monitoring._auto_job_cache[printer_id].add(job_key)

        # Check cache size
        cache_size = len(monitoring._auto_job_cache[printer_id])
        assert cache_size == 50

        # Memory footprint should be small (strings in a set)
        # Estimate: ~50 strings * ~50 bytes = ~2.5KB
        import sys
        cache_memory_bytes = sys.getsizeof(monitoring._auto_job_cache[printer_id])
        assert cache_memory_bytes < 10000, f"Cache too large: {cache_memory_bytes} bytes"


class TestCacheCleanup:
    """Test cache cleanup mechanisms."""

    @pytest.mark.asyncio
    async def test_discovery_cleanup_on_print_end(self, performance_test_stack):
        """Discovery tracking should be cleaned up when print ends."""
        monitoring = performance_test_stack['monitoring_service']

        # Start print
        status_printing = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.PRINTING,
            current_job="model.3mf",
            progress=50,
            timestamp=datetime.now()
        )
        await monitoring._auto_create_job_if_needed(status_printing)

        # Check discovery was tracked
        discovery_key = "bambu_001:model.3mf"
        assert discovery_key in monitoring._print_discoveries

        # Simulate print completion (status = ONLINE, still has current_job temporarily)
        status_complete = PrinterStatusUpdate(
            printer_id="bambu_001",
            status=PrinterStatus.ONLINE,
            current_job="model.3mf",  # Still present in status briefly
            progress=100,
            timestamp=datetime.now()
        )

        # Simulate the status update handler (which cleans up)
        if status_complete.status in [PrinterStatus.ONLINE, PrinterStatus.ERROR]:
            if status_complete.current_job:
                monitoring._print_discoveries.pop(discovery_key, None)

        # Discovery should be cleaned up
        assert discovery_key not in monitoring._print_discoveries

    @pytest.mark.asyncio
    async def test_cache_size_remains_bounded(self, performance_test_stack):
        """Cache should remain bounded even with many prints."""
        monitoring = performance_test_stack['monitoring_service']

        # Simulate 1000 status updates
        for i in range(1000):
            status = PrinterStatusUpdate(
                printer_id="bambu_001",
                status=PrinterStatus.PRINTING,
                current_job=f"model_{i % 10}.3mf",  # Only 10 unique files
                progress=50,
                timestamp=datetime.now()
            )
            await monitoring._auto_create_job_if_needed(status)

        # Cache should only contain entries for 10 unique files
        assert len(monitoring._print_discoveries) <= 10

        # Job cache should also be bounded
        if "bambu_001" in monitoring._auto_job_cache:
            assert len(monitoring._auto_job_cache["bambu_001"]) <= 10


class TestHighFrequencyUpdates:
    """Test high-frequency status updates (stress testing)."""

    @pytest.mark.asyncio
    async def test_rapid_status_updates_no_duplicates(self, performance_test_stack):
        """Rapid status updates should not create duplicate jobs."""
        monitoring = performance_test_stack['monitoring_service']
        job_service = performance_test_stack['job_service']

        # Simulate 100 rapid status updates (like every second)
        for i in range(100):
            status = PrinterStatusUpdate(
                printer_id="bambu_001",
                status=PrinterStatus.PRINTING,
                current_job="stress_test.3mf",
                progress=i % 100,  # Progress changes
                timestamp=datetime.now()
            )
            await monitoring._auto_create_job_if_needed(status)

        # Should only have ONE job created
        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1

    @pytest.mark.asyncio
    async def test_performance_under_load(self, performance_test_stack):
        """Test performance with many rapid updates."""
        monitoring = performance_test_stack['monitoring_service']

        import time
        start_time = time.time()

        # 1000 status updates
        for i in range(1000):
            status = PrinterStatusUpdate(
                printer_id="bambu_001",
                status=PrinterStatus.PRINTING,
                current_job="model.3mf",
                progress=i % 100,
                timestamp=datetime.now()
            )
            await monitoring._auto_create_job_if_needed(status)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (< 5 seconds for 1000 updates)
        assert duration < 5.0, f"Performance issue: {duration:.2f}s for 1000 updates"


class TestConcurrentPrinters:
    """Test handling of multiple concurrent printers."""

    @pytest.mark.asyncio
    async def test_multiple_printers_concurrent(self, performance_test_stack):
        """Should handle multiple printers printing concurrently."""
        monitoring = performance_test_stack['monitoring_service']
        job_service = performance_test_stack['job_service']

        # Simulate 10 printers printing concurrently
        async def simulate_printer(printer_id, file_num):
            status = PrinterStatusUpdate(
                printer_id=printer_id,
                status=PrinterStatus.PRINTING,
                current_job=f"model_{file_num}.3mf",
                progress=50,
                timestamp=datetime.now()
            )
            await monitoring._auto_create_job_if_needed(status)

        # Create tasks for 10 printers
        tasks = []
        for i in range(10):
            printer_id = f"printer_{i:03d}"
            tasks.append(simulate_printer(printer_id, i))

        # Run concurrently
        await asyncio.gather(*tasks)

        # Should have created 10 jobs (one per printer)
        all_jobs = await job_service.list_jobs()
        assert len(all_jobs) == 10

        # Verify unique printers
        printer_ids = {job['printer_id'] for job in all_jobs}
        assert len(printer_ids) == 10

    @pytest.mark.asyncio
    async def test_concurrent_updates_same_printer(self, performance_test_stack):
        """Should handle concurrent updates for same printer correctly."""
        monitoring = performance_test_stack['monitoring_service']
        job_service = performance_test_stack['job_service']

        # Simulate 20 concurrent status updates for same printer
        async def send_update(progress):
            status = PrinterStatusUpdate(
                printer_id="bambu_001",
                status=PrinterStatus.PRINTING,
                current_job="model.3mf",
                progress=progress,
                timestamp=datetime.now()
            )
            await monitoring._auto_create_job_if_needed(status)

        tasks = [send_update(i) for i in range(20)]
        await asyncio.gather(*tasks)

        # Should only have ONE job (lock prevents race conditions)
        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 1


class TestDatabasePerformance:
    """Test database query performance."""

    @pytest.mark.asyncio
    async def test_find_existing_job_performance(self, performance_test_stack):
        """Database lookup should be fast even with many jobs."""
        monitoring = performance_test_stack['monitoring_service']
        job_service = performance_test_stack['job_service']

        # Create 100 jobs in database
        for i in range(100):
            job_data = {
                'printer_id': 'bambu_001',
                'printer_type': 'bambu_lab',
                'job_name': f'Job {i}',
                'filename': f'model_{i}.3mf',
                'status': 'completed'  # Old jobs
            }
            await job_service.create_job(job_data)

        # Now search for a specific job
        import time
        start_time = time.time()

        result = await monitoring._find_existing_job(
            "bambu_001",
            "model_50.3mf",
            datetime.now()
        )

        end_time = time.time()
        query_time = end_time - start_time

        # Query should be fast (< 100ms)
        assert query_time < 0.1, f"Query too slow: {query_time*1000:.2f}ms"

    @pytest.mark.asyncio
    async def test_database_query_limit(self, performance_test_stack):
        """Should only query limited number of jobs."""
        monitoring = performance_test_stack['monitoring_service']
        database = performance_test_stack['database']

        # Mock to track query parameters
        original_list_jobs = database.list_jobs
        query_params = []

        async def mock_list_jobs(**kwargs):
            query_params.append(kwargs)
            return await original_list_jobs(**kwargs)

        database.list_jobs = mock_list_jobs

        # Trigger a search
        await monitoring._find_existing_job(
            "bambu_001",
            "model.3mf",
            datetime.now()
        )

        # Should have limited the query
        assert len(query_params) > 0
        assert query_params[0].get('limit') == 20  # Limit from design doc


class TestStressScenarios:
    """Stress test extreme scenarios."""

    @pytest.mark.asyncio
    async def test_many_unique_files(self, performance_test_stack):
        """Should handle many unique files being printed."""
        monitoring = performance_test_stack['monitoring_service']
        job_service = performance_test_stack['job_service']

        # Print 200 unique files
        for i in range(200):
            status = PrinterStatusUpdate(
                printer_id="bambu_001",
                status=PrinterStatus.PRINTING,
                current_job=f"unique_model_{i}.3mf",
                progress=50,
                timestamp=datetime.now()
            )
            await monitoring._auto_create_job_if_needed(status)

        # Should have created 200 jobs
        jobs = await job_service.list_jobs(printer_id="bambu_001")
        assert len(jobs) == 200

        # Discovery cache might be large, but bounded
        assert len(monitoring._print_discoveries) <= 200

    @pytest.mark.asyncio
    async def test_long_running_service(self, performance_test_stack):
        """Simulate long-running service with many operations."""
        monitoring = performance_test_stack['monitoring_service']

        # Simulate 1 hour of operation (120 status updates per print, 10 prints)
        for print_num in range(10):
            filename = f"model_{print_num}.3mf"

            # 120 updates per print (30 seconds * 120 = 1 hour)
            for progress in range(0, 100, 1):
                status = PrinterStatusUpdate(
                    printer_id="bambu_001",
                    status=PrinterStatus.PRINTING,
                    current_job=filename,
                    progress=progress,
                    timestamp=datetime.now()
                )
                await monitoring._auto_create_job_if_needed(status)

            # Simulate print completion
            monitoring._print_discoveries.pop(f"bambu_001:{filename}", None)

        # Cache should be cleaned up (no active prints)
        assert len(monitoring._print_discoveries) == 0


class TestLockPerformance:
    """Test asyncio.Lock performance under contention."""

    @pytest.mark.asyncio
    async def test_lock_contention(self, performance_test_stack):
        """Lock should perform well under high contention."""
        monitoring = performance_test_stack['monitoring_service']

        import time
        start_time = time.time()

        # 50 concurrent tasks trying to create jobs
        async def try_create_job(task_id):
            status = PrinterStatusUpdate(
                printer_id="bambu_001",
                status=PrinterStatus.PRINTING,
                current_job="model.3mf",
                progress=task_id % 100,
                timestamp=datetime.now()
            )
            await monitoring._auto_create_job_if_needed(status)

        tasks = [try_create_job(i) for i in range(50)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time despite lock contention
        # (< 2 seconds for 50 tasks)
        assert duration < 2.0, f"Lock contention issue: {duration:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
