"""
Tests for Pydantic model validation in the aggregation service.

Tests request/response models, data validation, schema validation,
and edge cases for all Pydantic models.
"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from services.aggregation.main import (
    TimePeriodModel,
    InstallationInfoModel,
    PrinterFleetStatsModel,
    UsageStatsModel,
    AggregatedStatsModel,
    SubmissionResponse,
    DeleteResponse,
)


class TestTimePeriodModel:
    """Tests for TimePeriodModel validation."""

    def test_valid_time_period(self):
        """Test creating valid time period."""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        period = TimePeriodModel(start=start, end=end)

        assert period.start == start
        assert period.end == end

    def test_time_period_accepts_iso_strings(self):
        """Test that time period accepts ISO datetime strings."""
        data = {
            "start": "2024-11-20T00:00:00",
            "end": "2024-11-27T00:00:00"
        }

        period = TimePeriodModel(**data)

        assert isinstance(period.start, datetime)
        assert isinstance(period.end, datetime)

    def test_time_period_missing_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError):
            TimePeriodModel(start=datetime.utcnow())  # Missing end

    def test_time_period_invalid_types(self):
        """Test that invalid types raise validation error."""
        with pytest.raises(ValidationError):
            TimePeriodModel(start="not-a-date", end="also-not-a-date")


class TestInstallationInfoModel:
    """Tests for InstallationInfoModel validation."""

    def test_valid_installation_info(self):
        """Test creating valid installation info."""
        info = InstallationInfoModel(
            installation_id="550e8400-e29b-41d4-a716-446655440000",
            app_version="2.7.0",
            platform="linux",
            deployment_mode="docker",
            country_code="DE"
        )

        assert info.installation_id == "550e8400-e29b-41d4-a716-446655440000"
        assert info.app_version == "2.7.0"
        assert info.country_code == "DE"

    def test_installation_info_all_fields_required(self):
        """Test that all fields are required."""
        with pytest.raises(ValidationError):
            InstallationInfoModel(
                installation_id="test-id",
                app_version="2.7.0"
                # Missing platform, deployment_mode, country_code
            )

    def test_installation_info_string_validation(self):
        """Test that fields must be strings."""
        with pytest.raises(ValidationError):
            InstallationInfoModel(
                installation_id=12345,  # Should be string
                app_version="2.7.0",
                platform="linux",
                deployment_mode="docker",
                country_code="DE"
            )

    def test_country_code_format(self):
        """Test country code accepts standard 2-letter codes."""
        valid_codes = ["DE", "US", "GB", "FR", "JP"]

        for code in valid_codes:
            info = InstallationInfoModel(
                installation_id="test-id",
                app_version="2.7.0",
                platform="linux",
                deployment_mode="docker",
                country_code=code
            )
            assert info.country_code == code


class TestPrinterFleetStatsModel:
    """Tests for PrinterFleetStatsModel validation."""

    def test_valid_printer_fleet_stats(self):
        """Test creating valid printer fleet stats."""
        stats = PrinterFleetStatsModel(
            printer_count=3,
            printer_types=["bambu_lab", "prusa_core"],
            printer_type_counts={"bambu_lab": 2, "prusa_core": 1}
        )

        assert stats.printer_count == 3
        assert len(stats.printer_types) == 2
        assert stats.printer_type_counts["bambu_lab"] == 2

    def test_printer_count_must_be_integer(self):
        """Test that printer_count must be an integer."""
        with pytest.raises(ValidationError):
            PrinterFleetStatsModel(
                printer_count="three",  # Should be int
                printer_types=["bambu_lab"],
                printer_type_counts={"bambu_lab": 3}
            )

    def test_printer_types_must_be_list(self):
        """Test that printer_types must be a list."""
        with pytest.raises(ValidationError):
            PrinterFleetStatsModel(
                printer_count=1,
                printer_types="bambu_lab",  # Should be list
                printer_type_counts={"bambu_lab": 1}
            )

    def test_printer_type_counts_must_be_dict(self):
        """Test that printer_type_counts must be a dict."""
        with pytest.raises(ValidationError):
            PrinterFleetStatsModel(
                printer_count=1,
                printer_types=["bambu_lab"],
                printer_type_counts=["bambu_lab", 1]  # Should be dict
            )

    def test_empty_printer_fleet(self):
        """Test handling of empty printer fleet."""
        stats = PrinterFleetStatsModel(
            printer_count=0,
            printer_types=[],
            printer_type_counts={}
        )

        assert stats.printer_count == 0
        assert stats.printer_types == []
        assert stats.printer_type_counts == {}


class TestUsageStatsModel:
    """Tests for UsageStatsModel validation."""

    def test_valid_usage_stats(self):
        """Test creating valid usage stats."""
        stats = UsageStatsModel(
            total_jobs_created=45,
            total_jobs_completed=42,
            total_jobs_failed=3,
            total_files_downloaded=38,
            total_files_uploaded=12,
            uptime_hours=156,
            feature_usage={"library": True, "timelapse": False},
            event_counts={"app_start": 2, "job_created": 45}
        )

        assert stats.total_jobs_created == 45
        assert stats.total_jobs_completed == 42
        assert stats.uptime_hours == 156

    def test_usage_stats_counters_must_be_integers(self):
        """Test that all counter fields must be integers."""
        with pytest.raises(ValidationError):
            UsageStatsModel(
                total_jobs_created="45",  # Should be int
                total_jobs_completed=42,
                total_jobs_failed=3,
                total_files_downloaded=38,
                total_files_uploaded=12,
                uptime_hours=156,
                feature_usage={},
                event_counts={}
            )

    def test_feature_usage_must_be_dict(self):
        """Test that feature_usage must be a dict."""
        with pytest.raises(ValidationError):
            UsageStatsModel(
                total_jobs_created=45,
                total_jobs_completed=42,
                total_jobs_failed=3,
                total_files_downloaded=38,
                total_files_uploaded=12,
                uptime_hours=156,
                feature_usage=["library", "timelapse"],  # Should be dict
                event_counts={}
            )

    def test_event_counts_must_be_dict(self):
        """Test that event_counts must be a dict."""
        with pytest.raises(ValidationError):
            UsageStatsModel(
                total_jobs_created=45,
                total_jobs_completed=42,
                total_jobs_failed=3,
                total_files_downloaded=38,
                total_files_uploaded=12,
                uptime_hours=156,
                feature_usage={},
                event_counts="invalid"  # Should be dict
            )

    def test_negative_values_accepted(self):
        """Test that negative values are accepted (for corrections)."""
        stats = UsageStatsModel(
            total_jobs_created=0,
            total_jobs_completed=0,
            total_jobs_failed=0,
            total_files_downloaded=0,
            total_files_uploaded=0,
            uptime_hours=0,
            feature_usage={},
            event_counts={}
        )

        assert stats.total_jobs_created == 0


class TestAggregatedStatsModel:
    """Tests for complete AggregatedStatsModel validation."""

    def test_valid_aggregated_stats(self):
        """Test creating valid aggregated stats payload."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        stats = AggregatedStatsModel(
            schema_version="1.0.0",
            period=TimePeriodModel(start=week_ago, end=now),
            installation=InstallationInfoModel(
                installation_id="test-id",
                app_version="2.7.0",
                platform="linux",
                deployment_mode="docker",
                country_code="DE"
            ),
            printer_fleet=PrinterFleetStatsModel(
                printer_count=2,
                printer_types=["bambu_lab"],
                printer_type_counts={"bambu_lab": 2}
            ),
            usage=UsageStatsModel(
                total_jobs_created=45,
                total_jobs_completed=42,
                total_jobs_failed=3,
                total_files_downloaded=38,
                total_files_uploaded=12,
                uptime_hours=156,
                feature_usage={"library": True},
                event_counts={"app_start": 2}
            )
        )

        assert stats.schema_version == "1.0.0"
        assert stats.installation.app_version == "2.7.0"

    def test_aggregated_stats_from_dict(self):
        """Test creating aggregated stats from dict (JSON payload)."""
        data = {
            "schema_version": "1.0.0",
            "period": {
                "start": "2024-11-20T00:00:00",
                "end": "2024-11-27T00:00:00"
            },
            "installation": {
                "installation_id": "test-id",
                "app_version": "2.7.0",
                "platform": "linux",
                "deployment_mode": "docker",
                "country_code": "DE"
            },
            "printer_fleet": {
                "printer_count": 2,
                "printer_types": ["bambu_lab"],
                "printer_type_counts": {"bambu_lab": 2}
            },
            "usage": {
                "total_jobs_created": 45,
                "total_jobs_completed": 42,
                "total_jobs_failed": 3,
                "total_files_downloaded": 38,
                "total_files_uploaded": 12,
                "uptime_hours": 156,
                "feature_usage": {"library": True},
                "event_counts": {"app_start": 2}
            }
        }

        stats = AggregatedStatsModel(**data)

        assert stats.schema_version == "1.0.0"
        assert isinstance(stats.period, TimePeriodModel)
        assert isinstance(stats.installation, InstallationInfoModel)

    def test_schema_version_default(self):
        """Test that schema_version has default value."""
        now = datetime.utcnow()

        # Create without schema_version
        stats = AggregatedStatsModel(
            period=TimePeriodModel(start=now, end=now),
            installation=InstallationInfoModel(
                installation_id="test-id",
                app_version="2.7.0",
                platform="linux",
                deployment_mode="docker",
                country_code="DE"
            ),
            printer_fleet=PrinterFleetStatsModel(
                printer_count=0,
                printer_types=[],
                printer_type_counts={}
            ),
            usage=UsageStatsModel(
                total_jobs_created=0,
                total_jobs_completed=0,
                total_jobs_failed=0,
                total_files_downloaded=0,
                total_files_uploaded=0,
                uptime_hours=0,
                feature_usage={},
                event_counts={}
            )
        )

        # Should have default value
        assert stats.schema_version == "1.0.0"

    def test_aggregated_stats_missing_nested_fields(self):
        """Test that missing nested model fields raise validation error."""
        with pytest.raises(ValidationError):
            AggregatedStatsModel(
                schema_version="1.0.0",
                period=TimePeriodModel(
                    start=datetime.utcnow(),
                    end=datetime.utcnow()
                )
                # Missing installation, printer_fleet, usage
            )


class TestSubmissionResponse:
    """Tests for SubmissionResponse model."""

    def test_valid_submission_response(self):
        """Test creating valid submission response."""
        response = SubmissionResponse(
            status="success",
            submission_id=123,
            message="Statistics submitted successfully"
        )

        assert response.status == "success"
        assert response.submission_id == 123
        assert "success" in response.message

    def test_submission_response_all_fields_required(self):
        """Test that all fields are required."""
        with pytest.raises(ValidationError):
            SubmissionResponse(
                status="success"
                # Missing submission_id and message
            )

    def test_submission_id_must_be_integer(self):
        """Test that submission_id must be an integer."""
        with pytest.raises(ValidationError):
            SubmissionResponse(
                status="success",
                submission_id="123",  # Should be int
                message="Test"
            )


class TestDeleteResponse:
    """Tests for DeleteResponse model."""

    def test_valid_delete_response(self):
        """Test creating valid delete response."""
        response = DeleteResponse(
            status="success",
            deleted_count=10,
            message="Deleted 10 submissions"
        )

        assert response.status == "success"
        assert response.deleted_count == 10

    def test_delete_response_zero_count(self):
        """Test delete response with zero deletions."""
        response = DeleteResponse(
            status="success",
            deleted_count=0,
            message="No data found"
        )

        assert response.deleted_count == 0

    def test_deleted_count_must_be_integer(self):
        """Test that deleted_count must be an integer."""
        with pytest.raises(ValidationError):
            DeleteResponse(
                status="success",
                deleted_count="10",  # Should be int
                message="Test"
            )


class TestModelSerialization:
    """Tests for model serialization to JSON."""

    def test_aggregated_stats_json_serialization(self):
        """Test that aggregated stats can be serialized to JSON."""
        now = datetime.utcnow()

        stats = AggregatedStatsModel(
            schema_version="1.0.0",
            period=TimePeriodModel(start=now, end=now),
            installation=InstallationInfoModel(
                installation_id="test-id",
                app_version="2.7.0",
                platform="linux",
                deployment_mode="docker",
                country_code="DE"
            ),
            printer_fleet=PrinterFleetStatsModel(
                printer_count=2,
                printer_types=["bambu_lab"],
                printer_type_counts={"bambu_lab": 2}
            ),
            usage=UsageStatsModel(
                total_jobs_created=45,
                total_jobs_completed=42,
                total_jobs_failed=3,
                total_files_downloaded=38,
                total_files_uploaded=12,
                uptime_hours=156,
                feature_usage={"library": True},
                event_counts={"app_start": 2}
            )
        )

        # Should be serializable to dict
        json_dict = stats.model_dump()

        assert isinstance(json_dict, dict)
        assert json_dict["schema_version"] == "1.0.0"
        assert "period" in json_dict
        assert "installation" in json_dict

    def test_model_json_round_trip(self):
        """Test that models can be serialized and deserialized."""
        original = InstallationInfoModel(
            installation_id="test-id",
            app_version="2.7.0",
            platform="linux",
            deployment_mode="docker",
            country_code="DE"
        )

        # Serialize to dict
        json_dict = original.model_dump()

        # Deserialize back
        restored = InstallationInfoModel(**json_dict)

        assert restored.installation_id == original.installation_id
        assert restored.app_version == original.app_version


class TestModelEdgeCases:
    """Tests for edge cases in model validation."""

    def test_very_large_numbers(self):
        """Test handling of very large counter values."""
        stats = UsageStatsModel(
            total_jobs_created=999999999,
            total_jobs_completed=999999999,
            total_jobs_failed=0,
            total_files_downloaded=999999999,
            total_files_uploaded=999999999,
            uptime_hours=999999999,
            feature_usage={},
            event_counts={}
        )

        assert stats.total_jobs_created == 999999999

    def test_empty_strings_in_installation_info(self):
        """Test that empty strings are accepted (but probably shouldn't be)."""
        # This documents current behavior
        info = InstallationInfoModel(
            installation_id="",
            app_version="",
            platform="",
            deployment_mode="",
            country_code=""
        )

        assert info.installation_id == ""

    def test_special_characters_in_strings(self):
        """Test handling of special characters in string fields."""
        info = InstallationInfoModel(
            installation_id="test-id-with-dashes",
            app_version="2.7.0-beta",
            platform="linux/amd64",
            deployment_mode="docker-compose",
            country_code="US"
        )

        assert "-" in info.installation_id
        assert "/" in info.platform

    def test_unicode_in_strings(self):
        """Test handling of unicode characters."""
        info = InstallationInfoModel(
            installation_id="test-装置",  # Chinese characters
            app_version="2.7.0",
            platform="linux",
            deployment_mode="docker",
            country_code="CN"
        )

        assert "装置" in info.installation_id

    def test_very_long_dict_values(self):
        """Test handling of large dictionaries."""
        large_event_counts = {f"event_{i}": i for i in range(100)}

        stats = UsageStatsModel(
            total_jobs_created=0,
            total_jobs_completed=0,
            total_jobs_failed=0,
            total_files_downloaded=0,
            total_files_uploaded=0,
            uptime_hours=0,
            feature_usage={},
            event_counts=large_event_counts
        )

        assert len(stats.event_counts) == 100
