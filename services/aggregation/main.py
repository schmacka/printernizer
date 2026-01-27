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

from config import settings
from database import init_db, get_db_dependency
from models import Submission, RateLimit

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


# Request/Response models (matching Printernizer client models)
from typing import Optional, List

class TimePeriodModel(BaseModel):
    """Time period for aggregated statistics."""
    start: datetime
    end: datetime
    duration_days: int = Field(default=0, ge=0)


class InstallationInfoModel(BaseModel):
    """Anonymous installation information."""
    installation_id: str
    first_seen: Optional[datetime] = None
    app_version: str
    python_version: Optional[str] = None
    platform: str
    deployment_mode: str
    country_code: str


class PrinterFleetStatsModel(BaseModel):
    """Aggregated printer fleet statistics (no PII)."""
    printer_count: int = Field(default=0, ge=0)
    printer_types: List[str] = Field(default_factory=list)
    printer_type_counts: Dict[str, int] = Field(default_factory=dict)


class UsageStatsModel(BaseModel):
    """Aggregated usage statistics."""
    job_count: int = Field(default=0, ge=0)
    file_count: int = Field(default=0, ge=0)
    upload_count: int = Field(default=0, ge=0)
    uptime_hours: int = Field(default=0, ge=0)
    feature_usage: Dict[str, bool] = Field(default_factory=dict)


class AggregatedStatsModel(BaseModel):
    """Complete aggregated statistics payload."""
    schema_version: str = Field(default="1.0")
    submission_timestamp: Optional[datetime] = None
    period: TimePeriodModel
    installation: InstallationInfoModel
    printer_fleet: PrinterFleetStatsModel
    usage_stats: UsageStatsModel
    error_summary: Dict[str, int] = Field(default_factory=dict)


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
            # Map from client field names to database columns
            total_jobs_created=stats.usage_stats.job_count,
            total_jobs_completed=stats.usage_stats.job_count,  # Client only tracks total
            total_jobs_failed=0,  # Not tracked separately by client
            total_files_downloaded=stats.usage_stats.file_count,
            total_files_uploaded=stats.usage_stats.upload_count,
            uptime_hours=stats.usage_stats.uptime_hours,
            feature_usage=stats.usage_stats.feature_usage,
            event_counts=stats.error_summary  # Map error_summary to event_counts
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


# ============================================================================
# Dashboard Analytics Endpoints (Phase 3)
# ============================================================================

from analytics import AnalyticsService


@app.get("/stats/overview")
async def get_dashboard_overview(
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Get combined dashboard overview with all metrics.

    Returns comprehensive statistics for the admin dashboard including
    installations, deployment modes, versions, geography, and printer stats.

    Args:
        db: Database session
        api_key: API key for authentication

    Returns:
        Combined overview with all dashboard metrics
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.get_overview()
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard overview"
        )


@app.get("/stats/installations")
async def get_installation_stats(
    days: int = 30,
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Get installation metrics including active users and growth.

    Args:
        days: Number of days for trend data (default 30)
        db: Database session
        api_key: API key for authentication

    Returns:
        Installation statistics with total, active counts, growth, and trend
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.get_installation_stats(days_trend=days)
    except Exception as e:
        logger.error(f"Failed to get installation stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get installation stats"
        )


@app.get("/stats/deployment-modes")
async def get_deployment_distribution(
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Get deployment mode distribution across installations.

    Shows how many installations use each deployment type
    (Home Assistant, Docker, Standalone, Raspberry Pi).

    Args:
        db: Database session
        api_key: API key for authentication

    Returns:
        Deployment mode breakdown with counts and percentages
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.get_deployment_distribution()
    except Exception as e:
        logger.error(f"Failed to get deployment distribution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get deployment distribution"
        )


@app.get("/stats/versions")
async def get_version_distribution(
    limit: int = 10,
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Get version adoption rates across installations.

    Shows which versions are in use and their adoption percentages.

    Args:
        limit: Maximum number of versions to return (default 10)
        db: Database session
        api_key: API key for authentication

    Returns:
        Version distribution with counts and percentages
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.get_version_distribution(limit=limit)
    except Exception as e:
        logger.error(f"Failed to get version distribution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get version distribution"
        )


@app.get("/stats/geography")
async def get_geography_distribution(
    limit: int = 20,
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Get geographic distribution of installations by country.

    Based on the country_code derived from timezone settings.

    Args:
        limit: Maximum number of countries to return (default 20)
        db: Database session
        api_key: API key for authentication

    Returns:
        Country distribution with counts and percentages
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.get_geography_distribution(limit=limit)
    except Exception as e:
        logger.error(f"Failed to get geography distribution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get geography distribution"
        )


@app.get("/stats/printers")
async def get_printer_stats(
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Get aggregated printer statistics across all installations.

    Shows total printers, average per installation, and type breakdown.

    Args:
        db: Database session
        api_key: API key for authentication

    Returns:
        Printer statistics with totals and type distribution
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.get_printer_stats()
    except Exception as e:
        logger.error(f"Failed to get printer stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get printer stats"
        )


@app.get("/stats/features")
async def get_feature_usage(
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Get feature usage statistics across all installations.

    Shows which features are enabled/disabled and their adoption rates.

    Args:
        db: Database session
        api_key: API key for authentication

    Returns:
        Feature usage statistics with enabled/disabled counts
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.get_feature_usage()
    except Exception as e:
        logger.error(f"Failed to get feature usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get feature usage"
        )


@app.get("/stats/version-migration")
async def get_version_migration(
    days: int = 30,
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Get version adoption over time (migration patterns).

    Shows how users migrate between versions over the specified period.

    Args:
        days: Number of days to analyze (default 30)
        db: Database session
        api_key: API key for authentication

    Returns:
        Daily version distribution data
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.get_version_migration(days=days)
    except Exception as e:
        logger.error(f"Failed to get version migration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get version migration"
        )


@app.get("/stats/anomalies")
async def get_anomalies(
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Detect anomalies in usage patterns.

    Checks for sudden drops in active users, error spikes,
    and unusual submission patterns.

    Args:
        db: Database session
        api_key: API key for authentication

    Returns:
        List of detected anomalies with severity levels
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.get_anomalies()
    except Exception as e:
        logger.error(f"Failed to get anomalies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get anomalies"
        )


@app.get("/stats/export")
async def export_data(
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Export all dashboard data for external use.

    Returns comprehensive data dump for backup or external analysis.

    Args:
        db: Database session
        api_key: API key for authentication

    Returns:
        Complete export of all dashboard metrics
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.export_data()
    except Exception as e:
        logger.error(f"Failed to export data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export data"
        )


@app.get("/stats/feature-trends")
async def get_feature_trends(
    days: int = 30,
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Get feature adoption trends over time.

    Shows how feature usage changes day by day over the specified period.

    Args:
        days: Number of days to analyze (default 30)
        db: Database session
        api_key: API key for authentication

    Returns:
        Daily feature adoption data
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.get_feature_trends(days=days)
    except Exception as e:
        logger.error(f"Failed to get feature trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get feature trends"
        )


@app.get("/stats/errors")
async def get_error_stats(
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Get error statistics from submissions.

    Analyzes error patterns and week-over-week changes.

    Args:
        db: Database session
        api_key: API key for authentication

    Returns:
        Error statistics with trends
    """
    try:
        analytics = AnalyticsService(db)
        return analytics.get_error_stats()
    except Exception as e:
        logger.error(f"Failed to get error stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get error stats"
        )


# ============================================================================
# Email Report Endpoints (Phase 3)
# ============================================================================

from email_service import email_service, report_generator


class EmailRequest(BaseModel):
    """Request model for sending emails."""
    recipients: Optional[List[str]] = Field(
        default=None,
        description="Override default recipients"
    )


@app.get("/reports/email-status")
async def get_email_status(
    api_key: str = Depends(verify_api_key)
):
    """
    Get SMTP email configuration status.

    Returns whether email is configured and ready to send reports.

    Args:
        api_key: API key for authentication

    Returns:
        Email configuration status
    """
    return {
        "enabled": settings.smtp_enabled,
        "configured": email_service.is_configured(),
        "host": settings.smtp_host if settings.smtp_enabled else None,
        "from_email": settings.smtp_from_email if settings.smtp_enabled else None,
        "recipients_count": len(settings.report_recipients),
        "use_tls": settings.smtp_use_tls,
        "use_ssl": settings.smtp_use_ssl
    }


@app.post("/reports/test-email")
async def send_test_email(
    request: EmailRequest = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Send a test email to verify SMTP configuration.

    Args:
        request: Optional recipient override
        api_key: API key for authentication

    Returns:
        Result of the email send attempt
    """
    recipients = request.recipients if request and request.recipients else None

    result = email_service.send_email(
        subject="Printernizer Stats - Test Email",
        html_content="""
        <html>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1 style="color: #3b82f6;">Test Email</h1>
            <p>This is a test email from Printernizer Usage Statistics.</p>
            <p>If you received this, your SMTP configuration is working correctly!</p>
        </body>
        </html>
        """,
        text_content="This is a test email from Printernizer Usage Statistics. If you received this, your SMTP configuration is working correctly!",
        recipients=recipients
    )

    if result["success"]:
        return {
            "status": "success",
            "message": "Test email sent successfully",
            "recipients": result.get("recipients", [])
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to send test email")
        )


@app.post("/reports/weekly")
async def send_weekly_report(
    request: EmailRequest = None,
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Send weekly summary report via email.

    Generates and sends a weekly summary email with key metrics,
    anomalies, and version information.

    Args:
        request: Optional recipient override
        db: Database session
        api_key: API key for authentication

    Returns:
        Result of the email send attempt
    """
    try:
        # Gather data for the report
        analytics = AnalyticsService(db)
        data = {
            "overview": analytics.get_overview(),
            "anomalies": analytics.get_anomalies().get("anomalies", []),
            "trends": analytics.get_installation_stats(days_trend=7)
        }

        # Generate report
        report = report_generator.generate_weekly_summary(data)

        # Send email
        recipients = request.recipients if request and request.recipients else None
        result = email_service.send_email(
            subject=report["subject"],
            html_content=report["html"],
            text_content=report["text"],
            recipients=recipients
        )

        if result["success"]:
            logger.info(f"Weekly report sent to {len(result.get('recipients', []))} recipients")
            return {
                "status": "success",
                "message": "Weekly report sent successfully",
                "recipients": result.get("recipients", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to send weekly report")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send weekly report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate or send weekly report"
        )


@app.post("/reports/monthly")
async def send_monthly_report(
    request: EmailRequest = None,
    db: Session = Depends(get_db_dependency),
    api_key: str = Depends(verify_api_key)
):
    """
    Send monthly comprehensive report via email.

    Generates and sends a detailed monthly report with all metrics,
    deployment distribution, geography, and feature adoption.

    Args:
        request: Optional recipient override
        db: Database session
        api_key: API key for authentication

    Returns:
        Result of the email send attempt
    """
    try:
        # Gather comprehensive data for the report
        analytics = AnalyticsService(db)
        data = {
            "overview": analytics.get_overview(),
            "anomalies": analytics.get_anomalies().get("anomalies", []),
            "deployment_modes": analytics.get_deployment_distribution().get("deployment_modes", []),
            "geography": analytics.get_geography_distribution(limit=20).get("countries", []),
            "features": analytics.get_feature_usage().get("features", [])
        }

        # Generate report
        report = report_generator.generate_monthly_report(data)

        # Send email
        recipients = request.recipients if request and request.recipients else None
        result = email_service.send_email(
            subject=report["subject"],
            html_content=report["html"],
            text_content=report["text"],
            recipients=recipients
        )

        if result["success"]:
            logger.info(f"Monthly report sent to {len(result.get('recipients', []))} recipients")
            return {
                "status": "success",
                "message": "Monthly report sent successfully",
                "recipients": result.get("recipients", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to send monthly report")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send monthly report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate or send monthly report"
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
