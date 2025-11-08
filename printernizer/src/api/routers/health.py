"""Health check endpoints."""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
import structlog
import aiohttp

from src.services.config_service import ConfigService
from src.database.database import Database
from src.utils.dependencies import get_config_service, get_database


logger = structlog.get_logger()
router = APIRouter()


class ServiceHealth(BaseModel):
    """Service health status."""
    name: str
    status: str  # healthy, degraded, unhealthy
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    database: Dict[str, Any]
    services: Dict[str, Any]
    uptime_seconds: Optional[float] = None


class UpdateCheckResponse(BaseModel):
    """Update check response model."""
    current_version: str
    latest_version: Optional[str] = None
    update_available: bool
    release_url: Optional[str] = None
    check_failed: bool = False
    error_message: Optional[str] = None


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    config: ConfigService = Depends(get_config_service),
    db: Database = Depends(get_database)
):
    """
    Enhanced health check endpoint with detailed service status.
    Returns system status and comprehensive information about all services.
    """
    try:
        # Test database connection
        db_status = await db.health_check()

        # Get services from app state
        printer_service = getattr(request.app.state, "printer_service", None)
        file_service = getattr(request.app.state, "file_service", None)
        trending_service = getattr(request.app.state, "trending_service", None)
        event_service = getattr(request.app.state, "event_service", None)

        # Check critical services with detailed status
        services_status = {}

        # Database status
        services_status["database"] = {
            "status": "healthy" if db_status else "unhealthy",
            "type": "sqlite",
            "details": {"connected": db_status}
        }

        # Printer service status
        if printer_service:
            try:
                printer_count = len(printer_service._printers) if hasattr(printer_service, "_printers") else 0
                services_status["printer_service"] = {
                    "status": "healthy",
                    "details": {
                        "printer_count": printer_count,
                        "monitoring_active": hasattr(printer_service, "_monitoring_active") and printer_service._monitoring_active
                    }
                }
            except Exception as e:
                services_status["printer_service"] = {
                    "status": "degraded",
                    "details": {"error": str(e)}
                }
        else:
            services_status["printer_service"] = {"status": "unhealthy", "details": {"error": "not initialized"}}

        # File service status
        if file_service:
            services_status["file_service"] = {
                "status": "healthy",
                "details": {"initialized": True}
            }
        else:
            services_status["file_service"] = {"status": "unhealthy", "details": {"error": "not initialized"}}

        # Trending service status
        if trending_service:
            try:
                has_session = trending_service.session is not None and not trending_service.session.closed
                services_status["trending_service"] = {
                    "status": "healthy" if has_session else "degraded",
                    "details": {"http_session_active": has_session}
                }
            except Exception as e:
                services_status["trending_service"] = {
                    "status": "degraded",
                    "details": {"error": str(e)}
                }
        else:
            services_status["trending_service"] = {"status": "degraded", "details": {"error": "not initialized"}}

        # Event service status
        if event_service:
            services_status["event_service"] = {
                "status": "healthy",
                "details": {"initialized": True}
            }
        else:
            services_status["event_service"] = {"status": "unhealthy", "details": {"error": "not initialized"}}

        # Calculate overall status
        statuses = [s["status"] for s in services_status.values()]
        if all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        # Import APP_VERSION from main
        from src.main import APP_VERSION

        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version=APP_VERSION,
            environment=getattr(config.settings, "environment", "production"),
            database={
                "type": "sqlite",
                "healthy": db_status,
                "connection_count": 1 if db_status else 0
            },
            services=services_status,
            uptime_seconds=None  # Could be calculated from startup time
        )

    except Exception as e:
        logger.error("Health check failed", error=str(e), exc_info=True)
        # Import APP_VERSION from main
        from src.main import APP_VERSION

        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version=APP_VERSION,
            environment=getattr(config.settings, "environment", "production"),
            database={"type": "sqlite", "healthy": False},
            services={"error": str(e)}
        )


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    Returns 200 when application is ready to serve requests.
    """
    return {"status": "ready"}


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Returns 200 when application is alive.
    """
    return {"status": "alive"}


def _compare_versions(current: str, latest: str) -> bool:
    """
    Compare semantic versions to determine if update is available.

    Args:
        current: Current version string (e.g., "2.3.0" or "2.3.0-5-g1234567")
        latest: Latest version string (e.g., "v2.4.0" or "2.4.0")

    Returns:
        True if latest version is newer than current
    """
    def parse_version(v: str) -> tuple:
        """Parse version string into comparable tuple."""
        # Remove 'v' prefix if present
        v = v.lstrip('v')
        # Take only the major.minor.patch part (ignore git commit info)
        v = v.split('-')[0]
        # Split into parts and convert to integers
        try:
            parts = [int(x) for x in v.split('.')]
            # Ensure we have at least 3 parts (major, minor, patch)
            while len(parts) < 3:
                parts.append(0)
            return tuple(parts[:3])
        except (ValueError, AttributeError):
            return (0, 0, 0)

    current_parts = parse_version(current)
    latest_parts = parse_version(latest)

    return latest_parts > current_parts


@router.get("/update-check", response_model=UpdateCheckResponse)
async def check_for_updates():
    """
    Check if a newer version is available on GitHub.

    Fetches the latest release from GitHub and compares with current version.
    Returns update availability status and release information.
    """
    from src.main import APP_VERSION

    github_api_url = "https://api.github.com/repos/schmacka/printernizer/releases/latest"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                github_api_url,
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"Accept": "application/vnd.github+json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    latest_version = data.get("tag_name", "").lstrip('v')
                    release_url = data.get("html_url")

                    update_available = _compare_versions(APP_VERSION, latest_version)

                    logger.info(
                        "Version check completed",
                        current_version=APP_VERSION,
                        latest_version=latest_version,
                        update_available=update_available
                    )

                    return UpdateCheckResponse(
                        current_version=APP_VERSION,
                        latest_version=latest_version,
                        update_available=update_available,
                        release_url=release_url,
                        check_failed=False
                    )
                elif response.status == 404:
                    # No releases published yet - this is not an error
                    logger.info(
                        "No releases found on GitHub",
                        current_version=APP_VERSION
                    )
                    return UpdateCheckResponse(
                        current_version=APP_VERSION,
                        latest_version=None,
                        update_available=False,
                        check_failed=False,
                        error_message="No releases available yet"
                    )
                else:
                    logger.warning(
                        "GitHub API returned non-200 status",
                        status_code=response.status
                    )
                    return UpdateCheckResponse(
                        current_version=APP_VERSION,
                        update_available=False,
                        check_failed=True,
                        error_message=f"GitHub API error: status {response.status}"
                    )

    except asyncio.TimeoutError:
        logger.warning("Update check timed out")
        return UpdateCheckResponse(
            current_version=APP_VERSION,
            update_available=False,
            check_failed=True,
            error_message="Request timed out"
        )
    except Exception as e:
        logger.error("Update check failed", error=str(e), exc_info=True)
        return UpdateCheckResponse(
            current_version=APP_VERSION,
            update_available=False,
            check_failed=True,
            error_message=str(e)
        )