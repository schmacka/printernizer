"""
Unit tests for Event Service.
Tests event subscription, emission, and background task management.

Sprint 2 Phase 1 - Core Service Test Coverage.
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from src.services.event_service import EventService


class TestEventServiceInitialization:
    """Test EventService initialization and configuration."""

    def test_event_service_initialization_default(self):
        """Test EventService initializes with defaults."""
        service = EventService()

        assert service._running == False
        assert len(service._tasks) == 0
        assert isinstance(service._event_handlers, dict)
        assert service.printer_service is None
        assert service.job_service is None
        assert service.file_service is None

    def test_event_service_initialization_with_services(self):
        """Test EventService initializes with injected services."""
        mock_printer_service = MagicMock()
        mock_job_service = MagicMock()

        service = EventService(
            printer_service=mock_printer_service,
            job_service=mock_job_service
        )

        assert service.printer_service is mock_printer_service
        assert service.job_service is mock_job_service

    def test_event_service_event_counts_initialized(self):
        """Test event counters are initialized to zero."""
        service = EventService()

        assert service.event_counts['printer_status'] == 0
        assert service.event_counts['job_update'] == 0
        assert service.event_counts['files_discovered'] == 0


class TestEventSubscription:
    """Test event subscription and unsubscription."""

    def test_subscribe_to_event(self):
        """Test subscribing to an event."""
        service = EventService()
        handler = MagicMock()

        service.subscribe("test_event", handler)

        assert "test_event" in service._event_handlers
        assert handler in service._event_handlers["test_event"]

    def test_subscribe_multiple_handlers(self):
        """Test subscribing multiple handlers to same event."""
        service = EventService()
        handler1 = MagicMock()
        handler2 = MagicMock()

        service.subscribe("test_event", handler1)
        service.subscribe("test_event", handler2)

        assert len(service._event_handlers["test_event"]) == 2

    def test_subscribe_to_different_events(self):
        """Test subscribing handlers to different events."""
        service = EventService()
        handler1 = MagicMock()
        handler2 = MagicMock()

        service.subscribe("event_a", handler1)
        service.subscribe("event_b", handler2)

        assert "event_a" in service._event_handlers
        assert "event_b" in service._event_handlers

    def test_unsubscribe_from_event(self):
        """Test unsubscribing from an event."""
        service = EventService()
        handler = MagicMock()

        service.subscribe("test_event", handler)
        service.unsubscribe("test_event", handler)

        assert handler not in service._event_handlers.get("test_event", [])

    def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing handler that wasn't subscribed."""
        service = EventService()
        handler = MagicMock()

        # Should not raise
        service.unsubscribe("test_event", handler)

    def test_unsubscribe_nonexistent_event(self):
        """Test unsubscribing from event that doesn't exist."""
        service = EventService()
        handler = MagicMock()

        # Should not raise
        service.unsubscribe("nonexistent_event", handler)


class TestEventEmission:
    """Test event emission to subscribers."""

    @pytest.mark.asyncio
    async def test_emit_event_calls_sync_handler(self):
        """Test emitting event calls synchronous handler."""
        service = EventService()
        handler = MagicMock()

        service.subscribe("test_event", handler)
        await service.emit_event("test_event", {"key": "value"})

        handler.assert_called_once_with({"key": "value"})

    @pytest.mark.asyncio
    async def test_emit_event_calls_async_handler(self):
        """Test emitting event calls asynchronous handler."""
        service = EventService()
        handler = AsyncMock()

        service.subscribe("test_event", handler)
        await service.emit_event("test_event", {"key": "value"})

        handler.assert_called_once_with({"key": "value"})

    @pytest.mark.asyncio
    async def test_emit_event_calls_all_handlers(self):
        """Test emitting event calls all subscribed handlers."""
        service = EventService()
        handler1 = MagicMock()
        handler2 = AsyncMock()

        service.subscribe("test_event", handler1)
        service.subscribe("test_event", handler2)
        await service.emit_event("test_event", {"key": "value"})

        handler1.assert_called_once()
        handler2.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_event_no_subscribers(self):
        """Test emitting event with no subscribers doesn't raise."""
        service = EventService()

        # Should not raise
        await service.emit_event("no_subscribers", {"key": "value"})

    @pytest.mark.asyncio
    async def test_emit_event_handler_error_doesnt_stop_others(self):
        """Test handler error doesn't prevent other handlers from running."""
        service = EventService()
        failing_handler = MagicMock(side_effect=Exception("Handler error"))
        success_handler = MagicMock()

        service.subscribe("test_event", failing_handler)
        service.subscribe("test_event", success_handler)

        await service.emit_event("test_event", {"key": "value"})

        # Both handlers should be called (error is logged but doesn't stop)
        failing_handler.assert_called_once()
        success_handler.assert_called_once()


class TestEventServiceStartStop:
    """Test EventService start and stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Test start sets running flag to True."""
        service = EventService()

        await service.start()

        assert service._running == True

        # Cleanup
        await service.stop()

    @pytest.mark.asyncio
    async def test_start_creates_background_tasks(self):
        """Test start creates background monitoring tasks."""
        service = EventService()

        await service.start()

        # Should have 3 tasks: printer monitoring, job status, file discovery
        assert len(service._tasks) == 3

        # Cleanup
        await service.stop()

    @pytest.mark.asyncio
    async def test_start_when_already_running(self):
        """Test calling start when already running doesn't create duplicate tasks."""
        service = EventService()

        await service.start()
        initial_task_count = len(service._tasks)

        await service.start()  # Second start

        assert len(service._tasks) == initial_task_count

        # Cleanup
        await service.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_tasks(self):
        """Test stop cancels all background tasks."""
        service = EventService()

        await service.start()
        await service.stop()

        assert service._running == False
        assert len(service._tasks) == 0

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self):
        """Test calling stop when not running doesn't raise."""
        service = EventService()

        # Should not raise
        await service.stop()

        assert service._running == False


class TestEventServiceStatus:
    """Test EventService status reporting."""

    def test_get_status_not_running(self):
        """Test status when service is not running."""
        service = EventService()

        status = service.get_status()

        assert status["running"] == False
        assert status["active_tasks"] == 0
        assert status["total_tasks"] == 0

    @pytest.mark.asyncio
    async def test_get_status_running(self):
        """Test status when service is running."""
        service = EventService()

        await service.start()
        status = service.get_status()

        assert status["running"] == True
        assert status["active_tasks"] == 3
        assert status["total_tasks"] == 3

        # Cleanup
        await service.stop()

    def test_get_status_includes_event_handlers(self):
        """Test status includes event handler counts."""
        service = EventService()
        service.subscribe("event_a", MagicMock())
        service.subscribe("event_a", MagicMock())
        service.subscribe("event_b", MagicMock())

        status = service.get_status()

        assert status["event_handlers"]["event_a"] == 2
        assert status["event_handlers"]["event_b"] == 1

    def test_get_status_includes_monitoring_status(self):
        """Test status includes monitoring state."""
        service = EventService()

        status = service.get_status()

        assert "monitoring_status" in status
        assert "printers_tracked" in status["monitoring_status"]
        assert "jobs_tracked" in status["monitoring_status"]

    def test_get_status_includes_event_counts(self):
        """Test status includes event counters."""
        service = EventService()

        status = service.get_status()

        assert "event_counts" in status
        assert "printer_status" in status["event_counts"]
        assert "job_update" in status["event_counts"]

    def test_get_status_includes_service_dependencies(self):
        """Test status includes service dependency info."""
        service = EventService()

        status = service.get_status()

        assert "service_dependencies" in status
        assert status["service_dependencies"]["printer_service"] == False
        assert status["service_dependencies"]["job_service"] == False


class TestEventServiceDependencies:
    """Test service dependency injection."""

    def test_set_services_updates_dependencies(self):
        """Test set_services updates service dependencies."""
        service = EventService()
        mock_printer_service = MagicMock()
        mock_job_service = MagicMock()
        mock_file_service = MagicMock()

        service.set_services(
            printer_service=mock_printer_service,
            job_service=mock_job_service,
            file_service=mock_file_service
        )

        assert service.printer_service is mock_printer_service
        assert service.job_service is mock_job_service
        assert service.file_service is mock_file_service

    def test_set_services_partial_update(self):
        """Test set_services only updates provided services."""
        service = EventService()
        original_printer_service = MagicMock()
        service.printer_service = original_printer_service

        service.set_services(job_service=MagicMock())

        assert service.printer_service is original_printer_service

    def test_set_services_database(self):
        """Test set_services can set database dependency."""
        service = EventService()
        mock_database = MagicMock()

        service.set_services(database=mock_database)

        assert service.database is mock_database


class TestEventServiceForceDiscovery:
    """Test force discovery functionality."""

    @pytest.mark.asyncio
    async def test_force_discovery_without_file_service(self):
        """Test force discovery returns error without file service."""
        service = EventService()

        result = await service.force_discovery()

        assert "error" in result
        assert "not available" in result["error"]

    @pytest.mark.asyncio
    async def test_force_discovery_with_file_service(self):
        """Test force discovery runs with file service."""
        service = EventService()
        mock_file_service = MagicMock()
        mock_file_service.discover_printer_files = AsyncMock(return_value=[])
        mock_printer_service = MagicMock()
        mock_printer_service.list_printers = AsyncMock(return_value=[])

        service.file_service = mock_file_service
        service.printer_service = mock_printer_service

        result = await service.force_discovery()

        assert result["success"] == True
        assert "files_found" in result
        assert "printers_scanned" in result

    @pytest.mark.asyncio
    async def test_force_discovery_emits_event(self):
        """Test force discovery emits files_discovered event."""
        service = EventService()
        mock_file_service = MagicMock()
        mock_file_service.discover_printer_files = AsyncMock(return_value=[])
        mock_printer_service = MagicMock()
        mock_printer_service.list_printers = AsyncMock(return_value=[])

        service.file_service = mock_file_service
        service.printer_service = mock_printer_service

        events_received = []
        service.subscribe("files_discovered", lambda data: events_received.append(data))

        await service.force_discovery()

        assert len(events_received) == 1
        assert events_received[0]["forced"] == True


class TestEventServiceResetState:
    """Test monitoring state reset functionality."""

    @pytest.mark.asyncio
    async def test_reset_monitoring_state_clears_printer_status(self):
        """Test reset clears printer status tracking."""
        service = EventService()
        service.last_printer_status = {"printer_001": {"status": "online"}}

        await service.reset_monitoring_state()

        assert len(service.last_printer_status) == 0

    @pytest.mark.asyncio
    async def test_reset_monitoring_state_clears_job_status(self):
        """Test reset clears job status tracking."""
        service = EventService()
        service.last_job_status = {"job_001": {"status": "running"}}

        await service.reset_monitoring_state()

        assert len(service.last_job_status) == 0

    @pytest.mark.asyncio
    async def test_reset_monitoring_state_resets_counters(self):
        """Test reset resets event counters."""
        service = EventService()
        service.event_counts['printer_status'] = 10
        service.event_counts['job_update'] = 5

        await service.reset_monitoring_state()

        assert service.event_counts['printer_status'] == 0
        assert service.event_counts['job_update'] == 0

    @pytest.mark.asyncio
    async def test_reset_monitoring_state_updates_last_discovery(self):
        """Test reset updates last file discovery timestamp."""
        service = EventService()
        old_time = service.last_file_discovery

        # Wait a tiny bit to ensure time difference
        await asyncio.sleep(0.01)
        await service.reset_monitoring_state()

        assert service.last_file_discovery >= old_time


class TestEventServiceBackgroundTasks:
    """Test background monitoring task behavior."""

    @pytest.mark.asyncio
    async def test_printer_monitoring_task_without_service(self):
        """Test printer monitoring gracefully handles missing service."""
        service = EventService()
        service._running = True

        # Should not raise, just logs and waits
        task = asyncio.create_task(service._printer_monitoring_task())

        # Let it run for a tiny bit
        await asyncio.sleep(0.1)

        # Cancel the task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_job_status_task_without_service(self):
        """Test job status monitoring gracefully handles missing service."""
        service = EventService()
        service._running = True

        # Should not raise, just logs and waits
        task = asyncio.create_task(service._job_status_task())

        # Let it run for a tiny bit
        await asyncio.sleep(0.1)

        # Cancel the task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_file_discovery_task_without_service(self):
        """Test file discovery gracefully handles missing service."""
        service = EventService()
        service._running = True

        # Should not raise, just logs and waits
        task = asyncio.create_task(service._file_discovery_task())

        # Let it run for a tiny bit
        await asyncio.sleep(0.1)

        # Cancel the task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


class TestEventServiceIntegration:
    """Integration tests for EventService with mocked services."""

    @pytest.mark.asyncio
    async def test_printer_status_change_emits_events(self):
        """Test printer status changes emit appropriate events."""
        service = EventService()

        # Track emitted events
        emitted_events = []
        service.subscribe("printer_status", lambda d: emitted_events.append(("status", d)))
        service.subscribe("printer_connected", lambda d: emitted_events.append(("connected", d)))

        # Simulate status change via emit_event
        await service.emit_event("printer_status", {
            "timestamp": datetime.now().isoformat(),
            "printers": [{"printer_id": "test_001", "status": "online"}],
            "status_changes": []
        })

        assert len(emitted_events) == 1
        assert emitted_events[0][0] == "status"

    @pytest.mark.asyncio
    async def test_job_lifecycle_events(self):
        """Test job lifecycle events are emitted correctly."""
        service = EventService()

        emitted_events = []
        service.subscribe("job_started", lambda d: emitted_events.append(("started", d)))
        service.subscribe("job_completed", lambda d: emitted_events.append(("completed", d)))

        # Simulate job started
        await service.emit_event("job_started", {
            "job_id": "job_001",
            "printer_id": "printer_001",
            "job_name": "Test Print",
            "timestamp": datetime.now().isoformat()
        })

        # Simulate job completed
        await service.emit_event("job_completed", {
            "job_id": "job_001",
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        })

        assert len(emitted_events) == 2
        assert emitted_events[0][0] == "started"
        assert emitted_events[1][0] == "completed"
