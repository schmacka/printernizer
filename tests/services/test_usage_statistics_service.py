"""
Comprehensive tests for UsageStatisticsService.

Tests cover opt-in/opt-out, event recording, aggregation, privacy,
local statistics viewing, and data export/deletion.
"""
import pytest
import uuid
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.services.usage_statistics_service import UsageStatisticsService
from src.models.usage_statistics import (
    UsageEvent,
    EventType,
    OptInResponse,
    LocalStatsResponse,
    AggregatedStats
)


@pytest.fixture
def mock_repository():
    """Create mock UsageStatisticsRepository for testing"""
    repo = MagicMock()

    # Mock repository methods
    repo.get_setting = AsyncMock(return_value=None)
    repo.set_setting = AsyncMock(return_value=True)
    repo.insert_event = AsyncMock(return_value=True)
    repo.get_events = AsyncMock(return_value=[])
    repo.get_event_counts_by_type = AsyncMock(return_value={})
    repo.get_total_event_count = AsyncMock(return_value=0)
    repo.get_first_event_timestamp = AsyncMock(return_value=None)
    repo.mark_events_submitted = AsyncMock(return_value=True)
    repo.delete_all_events = AsyncMock(return_value=True)
    repo.get_all_settings = AsyncMock(return_value={})

    return repo


@pytest.fixture
def mock_database():
    """Create mock Database for testing"""
    db = MagicMock()
    db._connection = MagicMock()
    return db


@pytest.fixture
def mock_settings():
    """Create mock settings for testing"""
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
    """Create UsageStatisticsService instance with mocks"""
    with patch('src.services.usage_statistics_service.get_settings', return_value=mock_settings):
        service = UsageStatisticsService(mock_database, repository=mock_repository)
        await service.initialize()
        return service


# =====================================================
# Opt-In/Opt-Out Tests
# =====================================================

class TestOptInOptOut:
    """Tests for opt-in and opt-out functionality"""

    @pytest.mark.asyncio
    async def test_is_opted_in_when_disabled(self, usage_service, mock_repository):
        """Test is_opted_in returns False when disabled"""
        mock_repository.get_setting.return_value = "disabled"

        result = await usage_service.is_opted_in()

        assert result is False

    @pytest.mark.asyncio
    async def test_is_opted_in_when_enabled(self, usage_service, mock_repository):
        """Test is_opted_in returns True when enabled"""
        mock_repository.get_setting.return_value = "enabled"

        result = await usage_service.is_opted_in()

        assert result is True

    @pytest.mark.asyncio
    async def test_is_opted_in_when_not_set(self, usage_service, mock_repository):
        """Test is_opted_in returns False when setting doesn't exist"""
        mock_repository.get_setting.return_value = None

        result = await usage_service.is_opted_in()

        assert result is False

    @pytest.mark.asyncio
    async def test_opt_in_success(self, usage_service, mock_repository):
        """Test successful opt-in"""
        mock_repository.get_setting.return_value = None  # No installation ID yet

        response = await usage_service.opt_in()

        assert response.success is True
        assert response.installation_id is not None
        assert "enabled" in response.message.lower() or "thank" in response.message.lower()

        # Verify settings were updated
        mock_repository.set_setting.assert_any_call("opt_in_status", "enabled")

    @pytest.mark.asyncio
    async def test_opt_in_generates_installation_id(self, usage_service, mock_repository):
        """Test that opt-in generates installation ID if not exists"""
        mock_repository.get_setting.return_value = None

        response = await usage_service.opt_in()

        assert response.installation_id is not None
        # Verify it's a valid UUID format
        assert len(response.installation_id) == 36
        assert response.installation_id.count('-') == 4

    @pytest.mark.asyncio
    async def test_opt_in_preserves_existing_installation_id(self, usage_service, mock_repository):
        """Test that opt-in preserves existing installation ID"""
        existing_id = str(uuid.uuid4())
        mock_repository.get_setting.return_value = existing_id

        response = await usage_service.opt_in()

        assert response.installation_id == existing_id

    @pytest.mark.asyncio
    async def test_opt_in_sets_first_run_date(self, usage_service, mock_repository):
        """Test that opt-in sets first_run_date"""
        mock_repository.get_setting.return_value = None

        await usage_service.opt_in()

        # Check that first_run_date was set
        calls = mock_repository.set_setting.call_args_list
        first_run_calls = [call for call in calls if call[0][0] == "first_run_date"]
        assert len(first_run_calls) > 0

    @pytest.mark.asyncio
    async def test_opt_out_success(self, usage_service, mock_repository):
        """Test successful opt-out"""
        response = await usage_service.opt_out()

        assert response.success is True
        assert "disabled" in response.message.lower() or "local" in response.message.lower()

        # Verify setting was updated
        mock_repository.set_setting.assert_called_with("opt_in_status", "disabled")

    @pytest.mark.asyncio
    async def test_opt_out_preserves_data(self, usage_service, mock_repository):
        """Test that opt-out doesn't delete local data"""
        await usage_service.opt_out()

        # Verify delete was NOT called
        mock_repository.delete_all_events.assert_not_called()


# =====================================================
# Event Recording Tests
# =====================================================

class TestEventRecording:
    """Tests for recording usage events"""

    @pytest.mark.asyncio
    async def test_record_event_with_string_type(self, usage_service, mock_repository):
        """Test recording event with string event type"""
        result = await usage_service.record_event(
            "job_completed",
            metadata={"printer_type": "bambu_lab"}
        )

        assert result is not None
        assert isinstance(result, UsageEvent)
        mock_repository.insert_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_event_with_enum_type(self, usage_service, mock_repository):
        """Test recording event with EventType enum"""
        result = await usage_service.record_event(
            EventType.JOB_COMPLETED,
            metadata={"printer_type": "bambu_lab"}
        )

        assert result is not None
        mock_repository.insert_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_event_without_metadata(self, usage_service, mock_repository):
        """Test recording event without metadata"""
        result = await usage_service.record_event(EventType.APP_START)

        assert result is not None

    @pytest.mark.asyncio
    async def test_record_event_with_complex_metadata(self, usage_service, mock_repository):
        """Test recording event with complex metadata"""
        metadata = {
            "printer_type": "bambu_lab",
            "duration_seconds": 3600,
            "material_usage": {
                "type": "PLA",
                "grams": 25.5
            },
            "success": True
        }

        result = await usage_service.record_event(
            EventType.JOB_COMPLETED,
            metadata=metadata
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_record_event_with_invalid_type(self, usage_service, mock_repository):
        """Test recording event with invalid event type returns None"""
        result = await usage_service.record_event("invalid_event_type")

        assert result is None

    @pytest.mark.asyncio
    async def test_record_event_handles_repository_failure(self, usage_service, mock_repository):
        """Test that event recording handles repository failures gracefully"""
        mock_repository.insert_event.return_value = False

        result = await usage_service.record_event(EventType.APP_START)

        assert result is None

    @pytest.mark.asyncio
    async def test_record_event_never_raises_exception(self, usage_service, mock_repository):
        """Test that event recording never raises exceptions"""
        mock_repository.insert_event.side_effect = Exception("Database error")

        # Should not raise
        result = await usage_service.record_event(EventType.APP_START)

        assert result is None


# =====================================================
# Statistics Aggregation Tests
# =====================================================

class TestStatisticsAggregation:
    """Tests for aggregating usage statistics"""

    @pytest.mark.asyncio
    async def test_aggregate_stats_basic(self, usage_service, mock_repository):
        """Test basic statistics aggregation"""
        # Mock repository responses
        mock_repository.get_setting.side_effect = lambda key: {
            "installation_id": str(uuid.uuid4()),
            "first_run_date": datetime.utcnow().isoformat()
        }.get(key)

        mock_repository.get_event_counts_by_type.return_value = {
            "job_completed": 10,
            "file_downloaded": 5,
            "error_occurred": 2
        }

        stats = await usage_service.aggregate_stats()

        assert stats is not None
        assert isinstance(stats, AggregatedStats)
        assert stats.usage_stats.job_count >= 10
        assert stats.usage_stats.file_count >= 5

    @pytest.mark.asyncio
    async def test_aggregate_stats_with_custom_date_range(self, usage_service, mock_repository):
        """Test aggregation with custom date range"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        mock_repository.get_setting.side_effect = lambda key: {
            "installation_id": str(uuid.uuid4()),
            "first_run_date": start_date.isoformat()
        }.get(key)

        mock_repository.get_event_counts_by_type.return_value = {}

        stats = await usage_service.aggregate_stats(start_date=start_date, end_date=end_date)

        assert stats is not None
        assert stats.period.duration_days == 30

    @pytest.mark.asyncio
    async def test_aggregate_stats_defaults_to_last_week(self, usage_service, mock_repository):
        """Test that aggregation defaults to last 7 days"""
        mock_repository.get_setting.side_effect = lambda key: {
            "installation_id": str(uuid.uuid4()),
            "first_run_date": datetime.utcnow().isoformat()
        }.get(key)

        mock_repository.get_event_counts_by_type.return_value = {}

        stats = await usage_service.aggregate_stats()

        assert stats is not None
        assert stats.period.duration_days == 7

    @pytest.mark.asyncio
    async def test_aggregate_stats_generates_installation_id_if_missing(self, usage_service, mock_repository):
        """Test that aggregation generates installation ID if missing"""
        mock_repository.get_setting.return_value = None
        mock_repository.get_event_counts_by_type.return_value = {}

        stats = await usage_service.aggregate_stats()

        assert stats is not None
        assert stats.installation.installation_id is not None

    @pytest.mark.asyncio
    async def test_aggregate_stats_includes_installation_info(self, usage_service, mock_repository):
        """Test that aggregated stats include installation information"""
        mock_repository.get_setting.side_effect = lambda key: {
            "installation_id": str(uuid.uuid4()),
            "first_run_date": datetime.utcnow().isoformat()
        }.get(key)

        mock_repository.get_event_counts_by_type.return_value = {}

        stats = await usage_service.aggregate_stats()

        assert stats.installation.app_version is not None
        assert stats.installation.python_version is not None
        assert stats.installation.platform in ["linux", "windows", "darwin"]
        assert stats.installation.deployment_mode in ["homeassistant", "docker", "standalone", "pi"]

    @pytest.mark.asyncio
    async def test_aggregate_stats_includes_feature_usage(self, usage_service, mock_repository, mock_settings):
        """Test that aggregated stats include feature usage flags"""
        mock_repository.get_setting.side_effect = lambda key: {
            "installation_id": str(uuid.uuid4()),
            "first_run_date": datetime.utcnow().isoformat()
        }.get(key)

        mock_repository.get_event_counts_by_type.return_value = {}

        stats = await usage_service.aggregate_stats()

        assert "library_enabled" in stats.usage_stats.feature_usage
        assert "timelapse_enabled" in stats.usage_stats.feature_usage
        assert stats.usage_stats.feature_usage["library_enabled"] is True
        assert stats.usage_stats.feature_usage["timelapse_enabled"] is False

    @pytest.mark.asyncio
    async def test_aggregate_stats_handles_errors_gracefully(self, usage_service, mock_repository):
        """Test that aggregation handles errors gracefully"""
        mock_repository.get_setting.side_effect = Exception("Database error")

        stats = await usage_service.aggregate_stats()

        assert stats is None


# =====================================================
# Statistics Submission Tests
# =====================================================

class TestStatisticsSubmission:
    """Tests for submitting statistics (Phase 2 placeholder)"""

    @pytest.mark.asyncio
    async def test_submit_stats_skips_when_opted_out(self, usage_service, mock_repository):
        """Test that submission is skipped when user is opted out"""
        mock_repository.get_setting.return_value = "disabled"

        result = await usage_service.submit_stats()

        assert result is True  # Returns True (no error) but doesn't submit

    @pytest.mark.asyncio
    async def test_submit_stats_aggregates_data_when_opted_in(self, usage_service, mock_repository):
        """Test that submission aggregates data when user is opted in"""
        mock_repository.get_setting.side_effect = lambda key: {
            "opt_in_status": "enabled",
            "installation_id": str(uuid.uuid4()),
            "first_run_date": datetime.utcnow().isoformat()
        }.get(key, "enabled" if key == "opt_in_status" else None)

        mock_repository.get_event_counts_by_type.return_value = {}

        result = await usage_service.submit_stats()

        # Phase 1: Just logs, doesn't actually submit
        assert result is True

    @pytest.mark.asyncio
    async def test_submit_stats_handles_aggregation_failure(self, usage_service, mock_repository):
        """Test that submission handles aggregation failures"""
        # User is opted in, but aggregation fails
        mock_repository.get_setting.side_effect = lambda key: {
            "opt_in_status": "enabled"
        }.get(key, None)

        # Make sure aggregation fails
        mock_repository.get_event_counts_by_type.side_effect = Exception("Database error")

        result = await usage_service.submit_stats()

        # Should handle error gracefully
        assert result is False


# =====================================================
# Local Statistics Tests
# =====================================================

class TestLocalStatistics:
    """Tests for viewing local statistics"""

    @pytest.mark.asyncio
    async def test_get_local_stats_basic(self, usage_service, mock_repository):
        """Test getting basic local statistics"""
        installation_id = str(uuid.uuid4())

        # Properly mock get_setting to return correct values for each key
        def mock_get_setting(key):
            if key == "installation_id":
                return installation_id
            elif key == "opt_in_status":
                return "enabled"
            elif key == "last_submission_date":
                return None
            return None

        mock_repository.get_setting = AsyncMock(side_effect=mock_get_setting)
        mock_repository.get_total_event_count = AsyncMock(return_value=100)
        mock_repository.get_first_event_timestamp = AsyncMock(return_value=datetime.utcnow() - timedelta(days=30))
        mock_repository.get_event_counts_by_type = AsyncMock(return_value={
            "job_completed": 20,
            "file_downloaded": 15
        })

        stats = await usage_service.get_local_stats()

        assert isinstance(stats, LocalStatsResponse)
        assert stats.installation_id == installation_id
        assert stats.opt_in_status == "enabled"
        assert stats.total_events == 100

    @pytest.mark.asyncio
    async def test_get_local_stats_this_week_summary(self, usage_service, mock_repository):
        """Test that local stats include this week's summary"""
        # Properly mock get_setting
        def mock_get_setting(key):
            if key == "installation_id":
                return str(uuid.uuid4())
            elif key == "opt_in_status":
                return "enabled"
            elif key == "last_submission_date":
                return None
            return None

        mock_repository.get_setting = AsyncMock(side_effect=mock_get_setting)
        mock_repository.get_total_event_count = AsyncMock(return_value=50)
        mock_repository.get_first_event_timestamp = AsyncMock(return_value=None)
        mock_repository.get_event_counts_by_type = AsyncMock(return_value={
            "job_completed": 10,
            "job_failed": 2,
            "file_downloaded": 8,
            "error_occurred": 1
        })

        stats = await usage_service.get_local_stats()

        assert "job_count" in stats.this_week
        assert "file_count" in stats.this_week
        assert "error_count" in stats.this_week
        assert stats.this_week["job_count"] == 12  # completed + failed
        assert stats.this_week["file_count"] == 8
        assert stats.this_week["error_count"] == 1

    @pytest.mark.asyncio
    async def test_get_local_stats_handles_no_installation_id(self, usage_service, mock_repository):
        """Test getting local stats when no installation ID exists"""
        mock_repository.get_setting.return_value = None
        mock_repository.get_total_event_count.return_value = 0
        mock_repository.get_event_counts_by_type.return_value = {}

        stats = await usage_service.get_local_stats()

        assert stats.installation_id == "not_generated"

    @pytest.mark.asyncio
    async def test_get_local_stats_handles_errors(self, usage_service, mock_repository):
        """Test that get_local_stats handles errors gracefully"""
        mock_repository.get_setting.side_effect = Exception("Database error")

        stats = await usage_service.get_local_stats()

        # Should return empty response instead of raising
        assert isinstance(stats, LocalStatsResponse)
        assert stats.installation_id == "error"
        assert stats.total_events == 0


# =====================================================
# Data Export Tests
# =====================================================

class TestDataExport:
    """Tests for exporting statistics data"""

    @pytest.mark.asyncio
    async def test_export_stats_returns_json(self, usage_service, mock_repository):
        """Test that export returns valid JSON"""
        mock_repository.get_events.return_value = [
            {
                "id": str(uuid.uuid4()),
                "event_type": "job_completed",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"printer_type": "bambu_lab"}
            }
        ]
        mock_repository.get_all_settings.return_value = {
            "opt_in_status": "enabled",
            "installation_id": str(uuid.uuid4())
        }

        export_data = await usage_service.export_stats()

        # Should be valid JSON
        parsed = json.loads(export_data)
        assert "events" in parsed
        assert "settings" in parsed
        assert "exported_at" in parsed
        assert "export_version" in parsed

    @pytest.mark.asyncio
    async def test_export_stats_includes_all_events(self, usage_service, mock_repository):
        """Test that export includes all events"""
        events = [
            {"id": str(uuid.uuid4()), "event_type": "job_completed"},
            {"id": str(uuid.uuid4()), "event_type": "file_downloaded"}
        ]
        mock_repository.get_events.return_value = events
        mock_repository.get_all_settings.return_value = {}

        export_data = await usage_service.export_stats()
        parsed = json.loads(export_data)

        assert len(parsed["events"]) == 2

    @pytest.mark.asyncio
    async def test_export_stats_includes_all_settings(self, usage_service, mock_repository):
        """Test that export includes all settings"""
        settings = {
            "opt_in_status": "enabled",
            "installation_id": str(uuid.uuid4()),
            "first_run_date": datetime.utcnow().isoformat()
        }
        mock_repository.get_events.return_value = []
        mock_repository.get_all_settings.return_value = settings

        export_data = await usage_service.export_stats()
        parsed = json.loads(export_data)

        assert parsed["settings"] == settings

    @pytest.mark.asyncio
    async def test_export_stats_handles_errors(self, usage_service, mock_repository):
        """Test that export handles errors gracefully"""
        mock_repository.get_events.side_effect = Exception("Database error")

        export_data = await usage_service.export_stats()
        parsed = json.loads(export_data)

        # Should contain error instead of raising
        assert "error" in parsed


# =====================================================
# Data Deletion Tests
# =====================================================

class TestDataDeletion:
    """Tests for deleting statistics data"""

    @pytest.mark.asyncio
    async def test_delete_all_stats_success(self, usage_service, mock_repository):
        """Test successful deletion of all statistics"""
        mock_repository.delete_all_events.return_value = True

        result = await usage_service.delete_all_stats()

        assert result is True
        mock_repository.delete_all_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_all_stats_preserves_settings(self, usage_service, mock_repository):
        """Test that delete_all_stats only deletes events, not settings"""
        await usage_service.delete_all_stats()

        # Should call delete_all_events, not any setting-related methods
        mock_repository.delete_all_events.assert_called_once()
        mock_repository.set_setting.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_all_stats_handles_failure(self, usage_service, mock_repository):
        """Test handling deletion failure"""
        mock_repository.delete_all_events.return_value = False

        result = await usage_service.delete_all_stats()

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_all_stats_handles_errors(self, usage_service, mock_repository):
        """Test that deletion handles errors gracefully"""
        mock_repository.delete_all_events.side_effect = Exception("Database error")

        result = await usage_service.delete_all_stats()

        assert result is False


# =====================================================
# Privacy Tests
# =====================================================

class TestPrivacy:
    """Tests for privacy-related functionality"""

    @pytest.mark.asyncio
    async def test_aggregated_stats_contains_no_pii(self, usage_service, mock_repository):
        """Test that aggregated stats contain no personally identifiable information"""
        mock_repository.get_setting.side_effect = lambda key: {
            "installation_id": str(uuid.uuid4()),
            "first_run_date": datetime.utcnow().isoformat()
        }.get(key)

        mock_repository.get_event_counts_by_type.return_value = {}

        stats = await usage_service.aggregate_stats()

        # Convert to dict and check for PII
        stats_dict = stats.model_dump()
        stats_json = json.dumps(stats_dict, default=str)

        # Should not contain any file names, paths, usernames, IPs, serial numbers
        # (Installation ID is anonymous and not PII)
        assert "192.168" not in stats_json  # No IP addresses
        assert "serial" not in stats_json.lower()  # No serial numbers
        assert ".3mf" not in stats_json  # No file names
        assert ".gcode" not in stats_json

    @pytest.mark.asyncio
    async def test_country_code_derived_from_timezone(self, usage_service, mock_settings):
        """Test that country code is derived from timezone, not IP"""
        mock_settings.timezone = "Europe/Berlin"

        country_code = usage_service._get_country_code_from_timezone()

        assert country_code == "DE"

    @pytest.mark.asyncio
    async def test_deployment_mode_detection(self, usage_service):
        """Test deployment mode detection"""
        deployment_mode = usage_service._get_deployment_mode()

        assert deployment_mode in ["homeassistant", "docker", "standalone", "pi"]

    @pytest.mark.asyncio
    async def test_feature_usage_contains_no_pii(self, usage_service):
        """Test that feature usage tracking contains no PII"""
        feature_usage = usage_service._get_feature_usage()

        # Should only contain boolean flags
        for key, value in feature_usage.items():
            assert isinstance(value, bool)
            assert "_enabled" in key


# =====================================================
# Initialization Tests
# =====================================================

class TestInitialization:
    """Tests for service initialization"""

    @pytest.mark.asyncio
    async def test_service_initializes_successfully(self, mock_database, mock_repository, mock_settings):
        """Test that service initializes without errors"""
        with patch('src.services.usage_statistics_service.get_settings', return_value=mock_settings):
            service = UsageStatisticsService(mock_database, repository=mock_repository)
            await service.initialize()

            assert service._init_timestamp is not None

    @pytest.mark.asyncio
    async def test_initialization_sets_timestamp(self, usage_service):
        """Test that initialization sets init timestamp for uptime tracking"""
        assert usage_service._init_timestamp is not None
        assert usage_service._init_timestamp <= datetime.utcnow()
