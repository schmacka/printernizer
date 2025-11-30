"""
Pytest fixtures for aggregation service tests.

Provides shared fixtures for database setup, test clients,
authentication, and mock data generation.
"""
import os
import pytest
from datetime import datetime, timedelta
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Set test environment before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["API_KEY"] = "test-api-key-123"
os.environ["RATE_LIMIT_PER_HOUR"] = "10"
os.environ["LOG_LEVEL"] = "ERROR"

from services.aggregation.main import app
from services.aggregation.database import Base, get_db_dependency
from services.aggregation.models import Submission, RateLimit


# Database fixtures
@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine using in-memory SQLite."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with dependency overrides."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_dependency] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# Authentication fixtures
@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Valid authentication headers."""
    return {"X-API-Key": "test-api-key-123"}


@pytest.fixture
def invalid_auth_headers() -> Dict[str, str]:
    """Invalid authentication headers."""
    return {"X-API-Key": "wrong-key"}


# Mock data fixtures
@pytest.fixture
def sample_installation_id() -> str:
    """Sample installation ID."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_stats_payload(sample_installation_id) -> Dict[str, Any]:
    """Sample aggregated statistics payload."""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    return {
        "schema_version": "1.0.0",
        "period": {
            "start": week_ago.isoformat(),
            "end": now.isoformat()
        },
        "installation": {
            "installation_id": sample_installation_id,
            "app_version": "2.7.0",
            "platform": "linux",
            "deployment_mode": "docker",
            "country_code": "DE"
        },
        "printer_fleet": {
            "printer_count": 3,
            "printer_types": ["bambu_lab", "prusa_core"],
            "printer_type_counts": {
                "bambu_lab": 2,
                "prusa_core": 1
            }
        },
        "usage": {
            "total_jobs_created": 45,
            "total_jobs_completed": 42,
            "total_jobs_failed": 3,
            "total_files_downloaded": 38,
            "total_files_uploaded": 12,
            "uptime_hours": 156,
            "feature_usage": {
                "library": True,
                "timelapse": True,
                "analytics": False
            },
            "event_counts": {
                "app_start": 2,
                "job_created": 45,
                "job_completed": 42,
                "file_downloaded": 38
            }
        }
    }


@pytest.fixture
def multiple_stats_payloads(sample_stats_payload) -> list[Dict[str, Any]]:
    """Generate multiple stats payloads with different installation IDs."""
    payloads = []

    for i in range(5):
        payload = sample_stats_payload.copy()
        payload["installation"] = payload["installation"].copy()
        payload["installation"]["installation_id"] = f"installation-{i:04d}"
        payloads.append(payload)

    return payloads


@pytest.fixture
def create_submission(db_session):
    """Factory fixture for creating test submissions."""
    def _create_submission(
        installation_id: str = "test-installation-id",
        app_version: str = "2.7.0",
        printer_count: int = 2,
        **kwargs
    ) -> Submission:
        """Create a submission in the test database."""
        now = datetime.utcnow()

        submission = Submission(
            installation_id=installation_id,
            submitted_at=kwargs.get("submitted_at", now),
            schema_version=kwargs.get("schema_version", "1.0.0"),
            period_start=kwargs.get("period_start", now - timedelta(days=7)),
            period_end=kwargs.get("period_end", now),
            app_version=app_version,
            platform=kwargs.get("platform", "linux"),
            deployment_mode=kwargs.get("deployment_mode", "docker"),
            country_code=kwargs.get("country_code", "DE"),
            printer_count=printer_count,
            printer_types=kwargs.get("printer_types", ["bambu_lab"]),
            printer_type_counts=kwargs.get("printer_type_counts", {"bambu_lab": 2}),
            total_jobs_created=kwargs.get("total_jobs_created", 10),
            total_jobs_completed=kwargs.get("total_jobs_completed", 8),
            total_jobs_failed=kwargs.get("total_jobs_failed", 2),
            total_files_downloaded=kwargs.get("total_files_downloaded", 5),
            total_files_uploaded=kwargs.get("total_files_uploaded", 3),
            uptime_hours=kwargs.get("uptime_hours", 100),
            feature_usage=kwargs.get("feature_usage", {"library": True}),
            event_counts=kwargs.get("event_counts", {"app_start": 1})
        )

        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        return submission

    return _create_submission


@pytest.fixture
def create_rate_limit(db_session):
    """Factory fixture for creating test rate limit records."""
    def _create_rate_limit(
        installation_id: str = "test-installation-id",
        submission_count: int = 1,
        **kwargs
    ) -> RateLimit:
        """Create a rate limit record in the test database."""
        now = datetime.utcnow()

        rate_limit = RateLimit(
            installation_id=installation_id,
            last_submission_at=kwargs.get("last_submission_at", now),
            submission_count=submission_count,
            window_start=kwargs.get("window_start", now)
        )

        db_session.add(rate_limit)
        db_session.commit()
        db_session.refresh(rate_limit)

        return rate_limit

    return _create_rate_limit


# Utility fixtures
@pytest.fixture
def clear_database(db_session):
    """Clear all data from the database."""
    db_session.query(Submission).delete()
    db_session.query(RateLimit).delete()
    db_session.commit()
