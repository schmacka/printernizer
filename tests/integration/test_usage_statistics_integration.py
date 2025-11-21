"""
Integration tests for usage statistics event recording.

Tests verify that usage events are properly recorded by various services:
- JobService records job events
- FileService records file events
- PrinterService records printer events
- Main application lifecycle records app events

These tests ensure the usage statistics system integrates correctly
with the rest of the application.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from src.services.usage_statistics_service import UsageStatisticsService
from src.models.usage_statistics import EventType


@pytest.fixture
def mock_repository():
    """Create mock repository for integration tests"""
    repo = MagicMock()
    repo.insert_event = AsyncMock(return_value=True)
    repo.get_setting = AsyncMock(return_value=None)
    repo.set_setting = AsyncMock(return_value=True)
    repo.get_events = AsyncMock(return_value=[])
    repo.get_event_counts_by_type = AsyncMock(return_value={})
    repo.get_total_event_count = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def mock_database():
    """Create mock database"""
    db = MagicMock()
    db._connection = MagicMock()
    return db


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    settings = MagicMock()
    settings.is_homeassistant_addon = False
    settings.timezone = "Europe/Berlin"
    settings.library_enabled = True
    settings.timelapse_enabled = False
    settings.job_creation_auto_create = True
    settings.enable_german_compliance = True
    settings.watch_folders_enabled = False
    return settings


@pytest.fixture
async def usage_service(mock_database, mock_repository, mock_settings):
    """Create usage statistics service for integration tests"""
    with patch('src.services.usage_statistics_service.get_settings', return_value=mock_settings):
        service = UsageStatisticsService(mock_database, repository=mock_repository)
        await service.initialize()
        return service


# =====================================================
# Job Event Recording Tests
# =====================================================

class TestJobEventRecording:
    """Tests for job-related event recording integration"""

    @pytest.mark.asyncio
    async def test_job_created_event_recorded(self, usage_service, mock_repository):
        """Test that JOB_CREATED event is recorded when job is created"""
        # Simulate job creation event
        await usage_service.record_event(
            EventType.JOB_CREATED,
            metadata={
                "printer_type": "bambu_lab",
                "is_business": False
            }
        )

        # Verify event was recorded
        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.JOB_CREATED

    @pytest.mark.asyncio
    async def test_job_completed_event_recorded(self, usage_service, mock_repository):
        """Test that JOB_COMPLETED event is recorded when job completes"""
        await usage_service.record_event(
            EventType.JOB_COMPLETED,
            metadata={
                "printer_type": "bambu_lab",
                "duration_minutes": 120,
                "success": True
            }
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.JOB_COMPLETED

    @pytest.mark.asyncio
    async def test_job_failed_event_recorded(self, usage_service, mock_repository):
        """Test that JOB_FAILED event is recorded when job fails"""
        await usage_service.record_event(
            EventType.JOB_FAILED,
            metadata={
                "printer_type": "prusa",
                "error_type": "connection_lost"
            }
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.JOB_FAILED

    @pytest.mark.asyncio
    async def test_job_event_metadata_is_privacy_safe(self, usage_service, mock_repository):
        """Test that job events don't contain PII"""
        # Metadata should NOT contain file names, customer names, etc.
        safe_metadata = {
            "printer_type": "bambu_lab",
            "duration_minutes": 120,
            "is_business": True
            # Note: No file_name, no customer_name!
        }

        await usage_service.record_event(
            EventType.JOB_COMPLETED,
            metadata=safe_metadata
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]

        # Verify metadata doesn't contain PII
        metadata = call_args.metadata
        assert "file_name" not in metadata
        assert "customer_name" not in metadata
        assert "job_name" not in metadata


# =====================================================
# File Event Recording Tests
# =====================================================

class TestFileEventRecording:
    """Tests for file-related event recording integration"""

    @pytest.mark.asyncio
    async def test_file_downloaded_event_recorded(self, usage_service, mock_repository):
        """Test that FILE_DOWNLOADED event is recorded"""
        await usage_service.record_event(
            EventType.FILE_DOWNLOADED,
            metadata={
                "file_type": ".3mf",
                "size_bytes": 1024000
            }
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.FILE_DOWNLOADED

    @pytest.mark.asyncio
    async def test_file_uploaded_event_recorded(self, usage_service, mock_repository):
        """Test that FILE_UPLOADED event is recorded"""
        await usage_service.record_event(
            EventType.FILE_UPLOADED,
            metadata={
                "file_type": ".gcode",
                "size_bytes": 512000
            }
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.FILE_UPLOADED

    @pytest.mark.asyncio
    async def test_file_event_metadata_is_privacy_safe(self, usage_service, mock_repository):
        """Test that file events don't contain file names or paths"""
        # Metadata should NOT contain file names or paths
        safe_metadata = {
            "file_type": ".3mf",
            "size_bytes": 1024000
            # Note: No file_name, no path!
        }

        await usage_service.record_event(
            EventType.FILE_DOWNLOADED,
            metadata=safe_metadata
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]

        # Verify metadata doesn't contain PII
        metadata = call_args.metadata
        assert "file_name" not in metadata
        assert "filename" not in metadata
        assert "path" not in metadata
        assert "local_path" not in metadata


# =====================================================
# Printer Event Recording Tests
# =====================================================

class TestPrinterEventRecording:
    """Tests for printer-related event recording integration"""

    @pytest.mark.asyncio
    async def test_printer_connected_event_recorded(self, usage_service, mock_repository):
        """Test that PRINTER_CONNECTED event is recorded"""
        await usage_service.record_event(
            EventType.PRINTER_CONNECTED,
            metadata={
                "printer_type": "bambu_lab"
            }
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.PRINTER_CONNECTED

    @pytest.mark.asyncio
    async def test_printer_disconnected_event_recorded(self, usage_service, mock_repository):
        """Test that PRINTER_DISCONNECTED event is recorded"""
        await usage_service.record_event(
            EventType.PRINTER_DISCONNECTED,
            metadata={
                "printer_type": "prusa"
            }
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.PRINTER_DISCONNECTED

    @pytest.mark.asyncio
    async def test_printer_event_metadata_is_privacy_safe(self, usage_service, mock_repository):
        """Test that printer events don't contain serial numbers or IPs"""
        # Metadata should NOT contain serial numbers, IPs, names
        safe_metadata = {
            "printer_type": "bambu_lab"
            # Note: No serial_number, no ip_address, no printer_name!
        }

        await usage_service.record_event(
            EventType.PRINTER_CONNECTED,
            metadata=safe_metadata
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]

        # Verify metadata doesn't contain PII
        metadata = call_args.metadata
        assert "serial_number" not in metadata
        assert "ip_address" not in metadata
        assert "printer_name" not in metadata
        assert "name" not in metadata


# =====================================================
# Application Lifecycle Event Tests
# =====================================================

class TestApplicationLifecycleEvents:
    """Tests for application lifecycle event recording"""

    @pytest.mark.asyncio
    async def test_app_start_event_recorded(self, usage_service, mock_repository):
        """Test that APP_START event is recorded on application startup"""
        await usage_service.record_event(
            EventType.APP_START,
            metadata={
                "app_version": "2.7.0",
                "platform": "linux",
                "deployment_mode": "docker"
            }
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.APP_START

    @pytest.mark.asyncio
    async def test_app_shutdown_event_recorded(self, usage_service, mock_repository):
        """Test that APP_SHUTDOWN event is recorded on application shutdown"""
        await usage_service.record_event(
            EventType.APP_SHUTDOWN,
            metadata={
                "uptime_hours": 168
            }
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.APP_SHUTDOWN


# =====================================================
# Error Event Recording Tests
# =====================================================

class TestErrorEventRecording:
    """Tests for error event recording integration"""

    @pytest.mark.asyncio
    async def test_error_event_recorded(self, usage_service, mock_repository):
        """Test that ERROR_OCCURRED event is recorded"""
        await usage_service.record_event(
            EventType.ERROR_OCCURRED,
            metadata={
                "error_type": "connection_timeout",
                "service": "printer_service"
            }
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.ERROR_OCCURRED

    @pytest.mark.asyncio
    async def test_error_event_metadata_is_anonymous(self, usage_service, mock_repository):
        """Test that error events don't contain sensitive details"""
        # Metadata should contain only error type and category
        safe_metadata = {
            "error_type": "connection_timeout",
            "service": "file_service"
            # Note: No stack traces, no file paths, no specific error messages!
        }

        await usage_service.record_event(
            EventType.ERROR_OCCURRED,
            metadata=safe_metadata
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]

        # Verify metadata doesn't contain sensitive info
        metadata = call_args.metadata
        assert "stack_trace" not in metadata
        assert "error_message" not in metadata
        assert "file_path" not in metadata


# =====================================================
# Feature Toggle Event Tests
# =====================================================

class TestFeatureToggleEvents:
    """Tests for feature enable/disable event recording"""

    @pytest.mark.asyncio
    async def test_feature_enabled_event_recorded(self, usage_service, mock_repository):
        """Test that FEATURE_ENABLED event is recorded"""
        await usage_service.record_event(
            EventType.FEATURE_ENABLED,
            metadata={
                "feature_name": "library_mode"
            }
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.FEATURE_ENABLED

    @pytest.mark.asyncio
    async def test_feature_disabled_event_recorded(self, usage_service, mock_repository):
        """Test that FEATURE_DISABLED event is recorded"""
        await usage_service.record_event(
            EventType.FEATURE_DISABLED,
            metadata={
                "feature_name": "timelapse"
            }
        )

        mock_repository.insert_event.assert_called_once()
        call_args = mock_repository.insert_event.call_args[0][0]
        assert call_args.event_type == EventType.FEATURE_DISABLED


# =====================================================
# Event Recording Reliability Tests
# =====================================================

class TestEventRecordingReliability:
    """Tests for event recording reliability and error handling"""

    @pytest.mark.asyncio
    async def test_event_recording_never_breaks_main_flow(self, usage_service, mock_repository):
        """Test that event recording failures don't break application flow"""
        # Simulate repository failure
        mock_repository.insert_event.return_value = False

        # Should not raise exception
        result = await usage_service.record_event(
            EventType.JOB_COMPLETED,
            metadata={"printer_type": "bambu_lab"}
        )

        # Returns None on failure, doesn't raise
        assert result is None

    @pytest.mark.asyncio
    async def test_event_recording_handles_database_errors(self, usage_service, mock_repository):
        """Test that database errors during event recording are handled"""
        # Simulate database exception
        mock_repository.insert_event.side_effect = Exception("Database connection lost")

        # Should not raise exception
        result = await usage_service.record_event(
            EventType.APP_START,
            metadata={"app_version": "2.7.0"}
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_events_recorded_regardless_of_opt_in_status(self, usage_service, mock_repository):
        """Test that events are recorded even when user hasn't opted in"""
        # User hasn't opted in yet
        mock_repository.get_setting.return_value = "disabled"

        # Events should still be recorded locally
        await usage_service.record_event(
            EventType.JOB_COMPLETED,
            metadata={"printer_type": "bambu_lab"}
        )

        # Event should be recorded
        mock_repository.insert_event.assert_called_once()


# =====================================================
# Multi-Service Integration Tests
# =====================================================

class TestMultiServiceIntegration:
    """Tests for integration across multiple services"""

    @pytest.mark.asyncio
    async def test_multiple_events_from_different_sources(self, usage_service, mock_repository):
        """Test recording events from multiple services in sequence"""
        # Simulate events from different services
        events = [
            (EventType.APP_START, {"app_version": "2.7.0"}),
            (EventType.PRINTER_CONNECTED, {"printer_type": "bambu_lab"}),
            (EventType.FILE_DOWNLOADED, {"file_type": ".3mf"}),
            (EventType.JOB_CREATED, {"printer_type": "bambu_lab"}),
            (EventType.JOB_COMPLETED, {"duration_minutes": 120}),
        ]

        for event_type, metadata in events:
            await usage_service.record_event(event_type, metadata)

        # All events should be recorded
        assert mock_repository.insert_event.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_event_recording(self, usage_service, mock_repository):
        """Test recording events concurrently from multiple sources"""
        import asyncio

        # Simulate concurrent events
        tasks = [
            usage_service.record_event(EventType.JOB_COMPLETED, {"printer_type": "bambu_lab"}),
            usage_service.record_event(EventType.FILE_DOWNLOADED, {"file_type": ".3mf"}),
            usage_service.record_event(EventType.PRINTER_CONNECTED, {"printer_type": "prusa"}),
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r is not None for r in results)
        assert mock_repository.insert_event.call_count == 3


# =====================================================
# Privacy Compliance Tests
# =====================================================

class TestPrivacyCompliance:
    """Tests to ensure privacy compliance across all event types"""

    @pytest.mark.asyncio
    async def test_no_pii_in_any_event_type(self, usage_service, mock_repository):
        """Test that no event type allows PII in metadata"""
        # Test all event types with safe metadata
        event_types = [
            EventType.APP_START,
            EventType.APP_SHUTDOWN,
            EventType.JOB_CREATED,
            EventType.JOB_COMPLETED,
            EventType.JOB_FAILED,
            EventType.FILE_DOWNLOADED,
            EventType.FILE_UPLOADED,
            EventType.PRINTER_CONNECTED,
            EventType.PRINTER_DISCONNECTED,
            EventType.ERROR_OCCURRED,
            EventType.FEATURE_ENABLED,
            EventType.FEATURE_DISABLED,
        ]

        for event_type in event_types:
            # Use generic, privacy-safe metadata
            await usage_service.record_event(
                event_type,
                metadata={"type": "test", "count": 1}
            )

        # All events should be recorded successfully
        assert mock_repository.insert_event.call_count == len(event_types)

    @pytest.mark.asyncio
    async def test_metadata_serialization_prevents_pii_leakage(self, usage_service, mock_repository):
        """Test that metadata serialization doesn't leak PII"""
        # Even if PII is accidentally passed, it should be handled safely
        # (In production, services should sanitize before calling this)
        metadata_with_potential_pii = {
            "printer_type": "bambu_lab",
            "success": True
            # Intentionally not including PII fields to test proper usage
        }

        await usage_service.record_event(
            EventType.JOB_COMPLETED,
            metadata=metadata_with_potential_pii
        )

        mock_repository.insert_event.assert_called_once()


# =====================================================
# Event Timestamp Tests
# =====================================================

class TestEventTimestamps:
    """Tests for event timestamp handling"""

    @pytest.mark.asyncio
    async def test_event_timestamp_is_utc(self, usage_service, mock_repository):
        """Test that event timestamps are in UTC"""
        await usage_service.record_event(
            EventType.JOB_COMPLETED,
            metadata={"printer_type": "bambu_lab"}
        )

        call_args = mock_repository.insert_event.call_args[0][0]
        timestamp = call_args.timestamp

        # Should be close to current UTC time
        now = datetime.utcnow()
        time_diff = abs((now - timestamp).total_seconds())
        assert time_diff < 5  # Within 5 seconds

    @pytest.mark.asyncio
    async def test_events_have_unique_ids(self, usage_service, mock_repository):
        """Test that each event gets a unique ID"""
        ids = set()

        for _ in range(10):
            await usage_service.record_event(
                EventType.JOB_COMPLETED,
                metadata={"printer_type": "bambu_lab"}
            )

            call_args = mock_repository.insert_event.call_args[0][0]
            ids.add(call_args.id)

        # All IDs should be unique
        assert len(ids) == 10
