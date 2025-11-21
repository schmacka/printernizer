"""
Usage Statistics Aggregation Service

FastAPI service for receiving and storing aggregated usage statistics
from Printernizer installations.

Privacy & Security:
    - Only accepts aggregated data (no individual events)
    - No PII (personally identifiable information)
    - Rate limiting per installation
    - API key authentication
    - GDPR-compliant data deletion
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .config import settings
from .database import init_db, get_db_dependency
from .models import Submission, RateLimit

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Printernizer Usage Statistics Aggregation Service",
    description="Receives and stores aggregated usage statistics from Printernizer installations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify API key for authentication."""
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key


# Request/Response models (matching Printernizer models)
class TimePeriodModel(BaseModel):
    """Time period for aggregated statistics."""
    start: datetime
    end: datetime


class InstallationInfoModel(BaseModel):
    """Anonymous installation information."""
    installation_id: str
    app_version: str
    platform: str
    deployment_mode: str
    country_code: str


class PrinterFleetStatsModel(BaseModel):
    """Aggregated printer fleet statistics (no PII)."""
    printer_count: int
    printer_types: list[str]
    printer_type_counts: Dict[str, int]


class UsageStatsModel(BaseModel):
    """Aggregated usage statistics."""
    total_jobs_created: int
    total_jobs_completed: int
    total_jobs_failed: int
    total_files_downloaded: int
    total_files_uploaded: int
    uptime_hours: int
    feature_usage: Dict[str, bool]
    event_counts: Dict[str, int]


class AggregatedStatsModel(BaseModel):
    """Complete aggregated statistics payload."""
    schema_version: str = Field(default="1.0.0")
    period: TimePeriodModel
    installation: InstallationInfoModel
    printer_fleet: PrinterFleetStatsModel
    usage: UsageStatsModel


class SubmissionResponse(BaseModel):
    """Response after successful submission."""
    status: str
    submission_id: int
    message: str


class DeleteResponse(BaseModel):
    """Response after data deletion."""
    status: str
    deleted_count: int
    message: str


# Rate limiting
def check_rate_limit(installation_id: str, db: Session) -> None:
    """
    Check and enforce rate limiting per installation.

    Raises:
        HTTPException: If rate limit exceeded
    """
    rate_limit = db.query(RateLimit).filter(
        RateLimit.installation_id == installation_id
    ).first()

    now = datetime.utcnow()

    if rate_limit:
        # Check if we're in a new time window (1 hour)
        if now - rate_limit.window_start > timedelta(hours=1):
            # Reset counter for new window
            rate_limit.window_start = now
            rate_limit.submission_count = 1
            rate_limit.last_submission_at = now
        else:
            # Same window - check limit
            if rate_limit.submission_count >= settings.rate_limit_per_hour:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {settings.rate_limit_per_hour} submissions per hour."
                )
            rate_limit.submission_count += 1
            rate_limit.last_submission_at = now
    else:
        # First submission from this installation
        rate_limit = RateLimit(
            installation_id=installation_id,
            window_start=now,
            submission_count=1,
            last_submission_at=now
        )
        db.add(rate_limit)

    db.commit()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting aggregation service...")
    init_db()
    logger.info("Database initialized")
    logger.info(f"Service running on {settings.host}:{settings.port}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Printernizer Usage Statistics Aggregation",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }


@app.post("/submit", response_model=SubmissionResponse)
async def submit_statistics(
    stats: AggregatedStatsModel,
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Submit aggregated usage statistics.

    This endpoint receives and stores aggregated statistics from Printernizer
    installations. It enforces rate limiting and validates the schema.

    Privacy Note:
        - Only aggregated data is accepted (no individual events)
        - No PII is stored (no names, emails, IP addresses, etc.)
        - Installation ID is a random UUID (not traceable)

    Args:
        stats: Aggregated statistics payload
        db: Database session
        api_key: API key for authentication

    Returns:
        SubmissionResponse with submission ID

    Raises:
        HTTPException: If rate limit exceeded or validation fails
    """
    try:
        # Check rate limit
        check_rate_limit(stats.installation.installation_id, db)

        # Create submission record
        submission = Submission(
            installation_id=stats.installation.installation_id,
            submitted_at=datetime.utcnow(),
            schema_version=stats.schema_version,
            period_start=stats.period.start,
            period_end=stats.period.end,
            app_version=stats.installation.app_version,
            platform=stats.installation.platform,
            deployment_mode=stats.installation.deployment_mode,
            country_code=stats.installation.country_code,
            printer_count=stats.printer_fleet.printer_count,
            printer_types=stats.printer_fleet.printer_types,
            printer_type_counts=stats.printer_fleet.printer_type_counts,
            total_jobs_created=stats.usage.total_jobs_created,
            total_jobs_completed=stats.usage.total_jobs_completed,
            total_jobs_failed=stats.usage.total_jobs_failed,
            total_files_downloaded=stats.usage.total_files_downloaded,
            total_files_uploaded=stats.usage.total_files_uploaded,
            uptime_hours=stats.usage.uptime_hours,
            feature_usage=stats.usage.feature_usage,
            event_counts=stats.usage.event_counts
        )

        db.add(submission)
        db.commit()
        db.refresh(submission)

        logger.info(
            f"Submission received",
            extra={
                "submission_id": submission.id,
                "installation_id": stats.installation.installation_id,
                "app_version": stats.installation.app_version,
                "printer_count": stats.printer_fleet.printer_count
            }
        )

        return SubmissionResponse(
            status="success",
            submission_id=submission.id,
            message="Statistics submitted successfully"
        )

    except HTTPException:
        # Re-raise HTTP exceptions (rate limit, auth, etc.)
        raise
    except Exception as e:
        logger.error(f"Failed to process submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process submission"
        )


@app.delete("/installation/{installation_id}", response_model=DeleteResponse)
async def delete_installation_data(
    installation_id: str,
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Delete all data for an installation (GDPR compliance).

    This endpoint allows users to request deletion of all their submitted
    statistics data. This is required for GDPR compliance.

    Args:
        installation_id: Installation UUID to delete
        db: Database session
        api_key: API key for authentication

    Returns:
        DeleteResponse with deletion count

    Raises:
        HTTPException: If deletion fails
    """
    try:
        # Delete all submissions for this installation
        deleted_count = db.query(Submission).filter(
            Submission.installation_id == installation_id
        ).delete()

        # Delete rate limit record
        db.query(RateLimit).filter(
            RateLimit.installation_id == installation_id
        ).delete()

        db.commit()

        logger.info(
            f"Data deletion requested",
            extra={
                "installation_id": installation_id,
                "deleted_count": deleted_count
            }
        )

        return DeleteResponse(
            status="success",
            deleted_count=deleted_count,
            message=f"Deleted {deleted_count} submissions for installation {installation_id}"
        )

    except Exception as e:
        logger.error(f"Failed to delete data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete data"
        )


@app.get("/stats/summary")
async def get_stats_summary(
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Get aggregated statistics summary (for monitoring).

    Returns high-level statistics about submissions.

    Args:
        db: Database session
        api_key: API key for authentication

    Returns:
        Summary statistics
    """
    try:
        total_submissions = db.query(Submission).count()
        unique_installations = db.query(Submission.installation_id).distinct().count()
        latest_submission = db.query(Submission).order_by(
            Submission.submitted_at.desc()
        ).first()

        return {
            "total_submissions": total_submissions,
            "unique_installations": unique_installations,
            "latest_submission_at": latest_submission.submitted_at if latest_submission else None,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get stats summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get stats summary"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
