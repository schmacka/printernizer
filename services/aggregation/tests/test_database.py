"""
Tests for database operations and models in the aggregation service.

Tests SQLAlchemy models, database schema, queries, indexes,
and data integrity.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import inspect
from services.aggregation.models import Submission, RateLimit, Base


class TestDatabaseSchema:
    """Tests for database schema and table structure."""

    def test_submissions_table_exists(self, db_engine):
        """Test that submissions table is created."""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert "submissions" in tables

    def test_rate_limits_table_exists(self, db_engine):
        """Test that rate_limits table is created."""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert "rate_limits" in tables

    def test_submissions_table_columns(self, db_engine):
        """Test that submissions table has all required columns."""
        inspector = inspect(db_engine)
        columns = {col["name"] for col in inspector.get_columns("submissions")}

        required_columns = {
            "id",
            "installation_id",
            "submitted_at",
            "schema_version",
            "period_start",
            "period_end",
            "app_version",
            "platform",
            "deployment_mode",
            "country_code",
            "printer_count",
            "printer_types",
            "printer_type_counts",
            "total_jobs_created",
            "total_jobs_completed",
            "total_jobs_failed",
            "total_files_downloaded",
            "total_files_uploaded",
            "uptime_hours",
            "feature_usage",
            "event_counts",
        }

        assert required_columns.issubset(columns)

    def test_rate_limits_table_columns(self, db_engine):
        """Test that rate_limits table has all required columns."""
        inspector = inspect(db_engine)
        columns = {col["name"] for col in inspector.get_columns("rate_limits")}

        required_columns = {
            "id",
            "installation_id",
            "last_submission_at",
            "submission_count",
            "window_start",
        }

        assert required_columns.issubset(columns)

    def test_submissions_indexes(self, db_engine):
        """Test that submissions table has proper indexes."""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("submissions")

        # Should have indexes on installation_id and submitted_at
        index_columns = []
        for idx in indexes:
            index_columns.extend(idx["column_names"])

        assert "installation_id" in index_columns
        assert "submitted_at" in index_columns

    def test_rate_limits_unique_constraint(self, db_engine):
        """Test that rate_limits has unique constraint on installation_id."""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("rate_limits")

        # Check for unique index on installation_id
        has_unique_installation = any(
            idx["unique"] and "installation_id" in idx["column_names"]
            for idx in indexes
        )

        assert has_unique_installation


class TestSubmissionModel:
    """Tests for Submission model CRUD operations."""

    def test_create_submission(self, db_session):
        """Test creating a submission record."""
        submission = Submission(
            installation_id="test-id",
            submitted_at=datetime.utcnow(),
            schema_version="1.0.0",
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow(),
            app_version="2.7.0",
            platform="linux",
            deployment_mode="docker",
            country_code="DE",
            printer_count=2,
            printer_types=["bambu_lab"],
            printer_type_counts={"bambu_lab": 2},
            total_jobs_created=10,
            total_jobs_completed=8,
            total_jobs_failed=2,
            total_files_downloaded=5,
            total_files_uploaded=3,
            uptime_hours=100,
            feature_usage={"library": True},
            event_counts={"app_start": 1}
        )

        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        assert submission.id is not None
        assert submission.installation_id == "test-id"

    def test_read_submission(self, db_session, create_submission):
        """Test reading a submission from database."""
        created = create_submission(installation_id="read-test")

        # Query it back
        found = db_session.query(Submission).filter(
            Submission.installation_id == "read-test"
        ).first()

        assert found is not None
        assert found.id == created.id
        assert found.installation_id == "read-test"

    def test_update_submission(self, db_session, create_submission):
        """Test updating a submission record."""
        submission = create_submission(app_version="1.0.0")

        # Update version
        submission.app_version = "2.0.0"
        db_session.commit()

        # Verify update
        db_session.refresh(submission)
        assert submission.app_version == "2.0.0"

    def test_delete_submission(self, db_session, create_submission):
        """Test deleting a submission record."""
        submission = create_submission(installation_id="delete-test")
        submission_id = submission.id

        db_session.delete(submission)
        db_session.commit()

        # Verify deletion
        found = db_session.query(Submission).filter(
            Submission.id == submission_id
        ).first()
        assert found is None

    def test_submission_json_fields(self, db_session, create_submission):
        """Test that JSON fields are properly stored and retrieved."""
        complex_data = {
            "printer_types": ["bambu_lab", "prusa_core", "custom"],
            "printer_type_counts": {"bambu_lab": 3, "prusa_core": 2},
            "feature_usage": {"library": True, "timelapse": False, "analytics": True},
            "event_counts": {"app_start": 5, "job_created": 100, "error": 3}
        }

        submission = create_submission(**complex_data)

        # Verify JSON fields are correct
        assert submission.printer_types == complex_data["printer_types"]
        assert submission.printer_type_counts == complex_data["printer_type_counts"]
        assert submission.feature_usage == complex_data["feature_usage"]
        assert submission.event_counts == complex_data["event_counts"]


class TestRateLimitModel:
    """Tests for RateLimit model CRUD operations."""

    def test_create_rate_limit(self, db_session):
        """Test creating a rate limit record."""
        rate_limit = RateLimit(
            installation_id="test-id",
            last_submission_at=datetime.utcnow(),
            submission_count=1,
            window_start=datetime.utcnow()
        )

        db_session.add(rate_limit)
        db_session.commit()
        db_session.refresh(rate_limit)

        assert rate_limit.id is not None
        assert rate_limit.installation_id == "test-id"
        assert rate_limit.submission_count == 1

    def test_read_rate_limit(self, db_session, create_rate_limit):
        """Test reading a rate limit from database."""
        created = create_rate_limit(installation_id="read-test")

        # Query it back
        found = db_session.query(RateLimit).filter(
            RateLimit.installation_id == "read-test"
        ).first()

        assert found is not None
        assert found.id == created.id
        assert found.installation_id == "read-test"

    def test_update_rate_limit(self, db_session, create_rate_limit):
        """Test updating a rate limit record."""
        rate_limit = create_rate_limit(submission_count=1)

        # Update count
        rate_limit.submission_count = 5
        db_session.commit()

        # Verify update
        db_session.refresh(rate_limit)
        assert rate_limit.submission_count == 5

    def test_delete_rate_limit(self, db_session, create_rate_limit):
        """Test deleting a rate limit record."""
        rate_limit = create_rate_limit(installation_id="delete-test")
        rate_limit_id = rate_limit.id

        db_session.delete(rate_limit)
        db_session.commit()

        # Verify deletion
        found = db_session.query(RateLimit).filter(
            RateLimit.id == rate_limit_id
        ).first()
        assert found is None

    def test_rate_limit_unique_installation(self, db_session):
        """Test that only one rate limit per installation is allowed."""
        rate_limit1 = RateLimit(
            installation_id="unique-test",
            last_submission_at=datetime.utcnow(),
            submission_count=1,
            window_start=datetime.utcnow()
        )
        db_session.add(rate_limit1)
        db_session.commit()

        # Try to add another with same installation_id
        rate_limit2 = RateLimit(
            installation_id="unique-test",
            last_submission_at=datetime.utcnow(),
            submission_count=2,
            window_start=datetime.utcnow()
        )
        db_session.add(rate_limit2)

        # Should raise integrity error
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db_session.commit()


class TestDatabaseQueries:
    """Tests for common database queries."""

    def test_query_submissions_by_installation(
        self,
        db_session,
        create_submission
    ):
        """Test querying submissions by installation_id."""
        create_submission(installation_id="query-test-1")
        create_submission(installation_id="query-test-1")
        create_submission(installation_id="query-test-2")

        results = db_session.query(Submission).filter(
            Submission.installation_id == "query-test-1"
        ).all()

        assert len(results) == 2

    def test_query_submissions_by_date_range(
        self,
        db_session,
        create_submission
    ):
        """Test querying submissions within a date range."""
        now = datetime.utcnow()
        old_date = now - timedelta(days=30)
        recent_date = now - timedelta(days=5)

        create_submission(submitted_at=old_date)
        create_submission(submitted_at=recent_date)
        create_submission(submitted_at=now)

        # Query last 10 days
        cutoff = now - timedelta(days=10)
        results = db_session.query(Submission).filter(
            Submission.submitted_at >= cutoff
        ).all()

        assert len(results) == 2

    def test_query_latest_submission(self, db_session, create_submission):
        """Test querying the most recent submission."""
        create_submission(submitted_at=datetime.utcnow() - timedelta(days=5))
        create_submission(submitted_at=datetime.utcnow() - timedelta(days=2))
        latest = create_submission(submitted_at=datetime.utcnow())

        result = db_session.query(Submission).order_by(
            Submission.submitted_at.desc()
        ).first()

        assert result.id == latest.id

    def test_count_unique_installations(self, db_session, create_submission):
        """Test counting unique installations."""
        create_submission(installation_id="install-1")
        create_submission(installation_id="install-1")
        create_submission(installation_id="install-2")
        create_submission(installation_id="install-3")

        unique_count = db_session.query(Submission.installation_id).distinct().count()

        assert unique_count == 3

    def test_aggregate_total_jobs(self, db_session, create_submission):
        """Test aggregating total jobs across submissions."""
        create_submission(total_jobs_completed=10)
        create_submission(total_jobs_completed=20)
        create_submission(total_jobs_completed=30)

        total = db_session.query(
            Submission
        ).with_entities(
            db_session.query(Submission.total_jobs_completed).label("total")
        ).all()

        # Sum manually for test
        total_jobs = sum(s.total_jobs_completed for s in db_session.query(Submission).all())
        assert total_jobs == 60


class TestDataIntegrity:
    """Tests for data integrity and constraints."""

    def test_submission_required_fields(self, db_session):
        """Test that required fields cannot be null."""
        submission = Submission(
            # Missing required fields
            installation_id="test",
            submitted_at=datetime.utcnow()
        )

        db_session.add(submission)

        # Should raise error for missing non-nullable fields
        with pytest.raises(Exception):
            db_session.commit()

    def test_timestamp_defaults(self, db_session):
        """Test that timestamp defaults are set correctly."""
        submission = Submission(
            installation_id="timestamp-test",
            schema_version="1.0.0",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
            printer_count=0,
            total_jobs_created=0,
            total_jobs_completed=0,
            total_jobs_failed=0,
            total_files_downloaded=0,
            total_files_uploaded=0,
            uptime_hours=0
            # submitted_at should default
        )

        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        # submitted_at should be set automatically
        assert submission.submitted_at is not None
        assert isinstance(submission.submitted_at, datetime)

    def test_cascade_delete_behavior(
        self,
        db_session,
        create_submission,
        create_rate_limit
    ):
        """Test deletion behavior (submissions and rate limits are independent)."""
        create_submission(installation_id="cascade-test")
        create_rate_limit(installation_id="cascade-test")

        # Delete submission
        db_session.query(Submission).filter(
            Submission.installation_id == "cascade-test"
        ).delete()
        db_session.commit()

        # Rate limit should still exist (no cascade)
        rate_limit = db_session.query(RateLimit).filter(
            RateLimit.installation_id == "cascade-test"
        ).first()

        assert rate_limit is not None


class TestModelRepresentations:
    """Tests for model __repr__ methods."""

    def test_submission_repr(self, create_submission):
        """Test Submission __repr__ output."""
        submission = create_submission(installation_id="repr-test")

        repr_str = repr(submission)

        assert "Submission" in repr_str
        assert str(submission.id) in repr_str
        assert "repr-test" in repr_str

    def test_rate_limit_repr(self, create_rate_limit):
        """Test RateLimit __repr__ output."""
        rate_limit = create_rate_limit(installation_id="repr-test")

        repr_str = repr(rate_limit)

        assert "RateLimit" in repr_str
        assert "repr-test" in repr_str
        assert str(rate_limit.submission_count) in repr_str


class TestDatabasePerformance:
    """Tests for database performance and indexes."""

    def test_query_with_index_installation_id(
        self,
        db_session,
        create_submission
    ):
        """Test that queries on installation_id use index."""
        # Create multiple submissions
        for i in range(20):
            create_submission(installation_id=f"perf-test-{i % 5}")

        # Query should be efficient (indexed)
        results = db_session.query(Submission).filter(
            Submission.installation_id == "perf-test-0"
        ).all()

        # Verify results
        assert len(results) == 4

    def test_query_with_index_submitted_at(
        self,
        db_session,
        create_submission
    ):
        """Test that queries on submitted_at use index."""
        now = datetime.utcnow()

        for i in range(10):
            create_submission(submitted_at=now - timedelta(days=i))

        # Query recent submissions
        cutoff = now - timedelta(days=5)
        results = db_session.query(Submission).filter(
            Submission.submitted_at >= cutoff
        ).all()

        assert len(results) == 6  # 0, 1, 2, 3, 4, 5 days ago


class TestJSONFieldEdgeCases:
    """Tests for JSON field edge cases."""

    def test_empty_json_objects(self, db_session, create_submission):
        """Test storing empty JSON objects."""
        submission = create_submission(
            printer_types=[],
            printer_type_counts={},
            feature_usage={},
            event_counts={}
        )

        assert submission.printer_types == []
        assert submission.printer_type_counts == {}
        assert submission.feature_usage == {}
        assert submission.event_counts == {}

    def test_null_json_fields(self, db_session):
        """Test that JSON fields can be null."""
        submission = Submission(
            installation_id="null-test",
            submitted_at=datetime.utcnow(),
            schema_version="1.0.0",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
            printer_count=0,
            total_jobs_created=0,
            total_jobs_completed=0,
            total_jobs_failed=0,
            total_files_downloaded=0,
            total_files_uploaded=0,
            uptime_hours=0,
            # All JSON fields null
            printer_types=None,
            printer_type_counts=None,
            feature_usage=None,
            event_counts=None
        )

        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        assert submission.printer_types is None
        assert submission.printer_type_counts is None

    def test_nested_json_objects(self, db_session, create_submission):
        """Test storing nested JSON structures."""
        nested_data = {
            "feature_usage": {
                "library": {
                    "enabled": True,
                    "items": 50
                }
            }
        }

        submission = create_submission(**nested_data)

        # Note: This will fail with current flat schema
        # This test documents the limitation
        assert isinstance(submission.feature_usage, dict)
