"""
Database models for aggregation service.

Stores aggregated statistics submissions in a structured format.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Submission(Base):
    """
    Stores aggregated statistics from Printernizer installations.

    Each row represents one submission from one installation for one time period.
    """

    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Installation identification (anonymous UUID)
    installation_id = Column(String(36), nullable=False, index=True)

    # Submission metadata
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    schema_version = Column(String(10), nullable=False)

    # Time period covered by this submission
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Installation information (anonymous)
    app_version = Column(String(50), nullable=True)
    platform = Column(String(50), nullable=True)
    deployment_mode = Column(String(50), nullable=True)
    country_code = Column(String(2), nullable=True)

    # Printer fleet stats (aggregated, no PII)
    printer_count = Column(Integer, nullable=False, default=0)
    printer_types = Column(JSON, nullable=True)  # List of types
    printer_type_counts = Column(JSON, nullable=True)  # Dict: {type: count}

    # Usage statistics (aggregated)
    total_jobs_created = Column(Integer, nullable=False, default=0)
    total_jobs_completed = Column(Integer, nullable=False, default=0)
    total_jobs_failed = Column(Integer, nullable=False, default=0)
    total_files_downloaded = Column(Integer, nullable=False, default=0)
    total_files_uploaded = Column(Integer, nullable=False, default=0)
    uptime_hours = Column(Integer, nullable=False, default=0)

    # Feature usage flags
    feature_usage = Column(JSON, nullable=True)  # Dict: {feature: enabled}

    # Event counts by type
    event_counts = Column(JSON, nullable=True)  # Dict: {event_type: count}

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_installation_period", "installation_id", "period_start"),
        Index("idx_submitted_at", "submitted_at"),
    )

    def __repr__(self):
        return (
            f"<Submission(id={self.id}, "
            f"installation_id={self.installation_id}, "
            f"submitted_at={self.submitted_at})>"
        )


class RateLimit(Base):
    """
    Tracks submission rate limits per installation.

    Used to prevent abuse by limiting submissions per hour.
    """

    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    installation_id = Column(String(36), nullable=False, unique=True, index=True)
    last_submission_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    submission_count = Column(Integer, nullable=False, default=1)
    window_start = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<RateLimit(installation_id={self.installation_id}, "
            f"count={self.submission_count}, "
            f"window_start={self.window_start})>"
        )
