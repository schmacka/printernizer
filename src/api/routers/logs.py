"""
API router for unified log viewer system.

Provides endpoints for querying, filtering, and exporting logs from
multiple sources (backend errors, frontend logs, etc.).
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse
import structlog

from src.models.logs import (
    LogLevel,
    LogSource,
    LogQueryFilters,
    LogQueryResult,
    LogSourcesResponse,
    LogStatistics,
    LogExportFormat,
)
from src.services.log_service import get_log_service

logger = structlog.get_logger()

router = APIRouter()


@router.get(
    "",
    response_model=LogQueryResult,
    summary="Query unified logs",
    description="Query logs from all sources with filtering and pagination."
)
async def query_logs(
    source: Optional[LogSource] = Query(None, description="Filter by log source"),
    level: Optional[LogLevel] = Query(None, description="Filter by minimum log level"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Full-text search in message"),
    start_date: Optional[datetime] = Query(None, description="Start of date range (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End of date range (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order by timestamp"),
) -> LogQueryResult:
    """
    Query logs from all sources with filtering and pagination.

    Returns a paginated list of log entries with statistics.
    """
    log_service = get_log_service()

    filters = LogQueryFilters(
        source=source,
        level=level,
        category=category,
        search=search,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page,
        sort_order=sort_order,
    )

    result = await log_service.query_logs(filters)
    return result


@router.get(
    "/sources",
    response_model=LogSourcesResponse,
    summary="Get log sources",
    description="Get information about available log sources."
)
async def get_sources() -> LogSourcesResponse:
    """
    Get information about all available log sources.

    Returns a list of log sources with their counts and availability status.
    """
    log_service = get_log_service()
    return await log_service.get_sources()


@router.get(
    "/statistics",
    response_model=LogStatistics,
    summary="Get log statistics",
    description="Get aggregated statistics across all log sources."
)
async def get_statistics(
    hours: int = Query(24, ge=1, le=720, description="Time range in hours")
) -> LogStatistics:
    """
    Get aggregated statistics across all log sources.

    Returns counts by level, source, and category.
    """
    log_service = get_log_service()
    return await log_service.get_statistics(hours=hours)


@router.get(
    "/categories",
    response_model=list[str],
    summary="Get log categories",
    description="Get list of all unique log categories."
)
async def get_categories() -> list[str]:
    """
    Get a list of all unique log categories.

    Useful for populating filter dropdowns.
    """
    log_service = get_log_service()
    return await log_service.get_categories()


@router.get(
    "/export",
    summary="Export logs",
    description="Export filtered logs as CSV or JSON file."
)
async def export_logs(
    format: LogExportFormat = Query(LogExportFormat.JSON, description="Export format"),
    source: Optional[LogSource] = Query(None, description="Filter by log source"),
    level: Optional[LogLevel] = Query(None, description="Filter by minimum log level"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Full-text search in message"),
    start_date: Optional[datetime] = Query(None, description="Start of date range"),
    end_date: Optional[datetime] = Query(None, description="End of date range"),
) -> Response:
    """
    Export filtered logs as CSV or JSON.

    Returns a downloadable file with the filtered log entries.
    """
    log_service = get_log_service()

    # Query all matching logs without pagination limit for export
    # We directly call the internal methods to bypass per_page validation
    all_logs = log_service._get_all_logs()

    # Apply filters manually
    from src.models.logs import LogQueryFilters as FilterModel
    filters = FilterModel(
        source=source,
        level=level,
        category=category,
        search=search,
        start_date=start_date,
        end_date=end_date,
        page=1,
        per_page=200,  # Not used for export, just for validation
    )
    filtered_logs = log_service._apply_filters(all_logs, filters)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if format == LogExportFormat.CSV:
        content = log_service.export_to_csv(filtered_logs)
        filename = f"printernizer_logs_{timestamp}.csv"
        media_type = "text/csv"
    else:
        content = log_service.export_to_json(filtered_logs)
        filename = f"printernizer_logs_{timestamp}.json"
        media_type = "application/json"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.delete(
    "",
    summary="Clear logs",
    description="Clear logs from specified source or all sources."
)
async def clear_logs(
    source: Optional[LogSource] = Query(None, description="Source to clear (None = all)")
) -> dict:
    """
    Clear logs from specified source or all sources.

    Returns the number of logs cleared.
    """
    log_service = get_log_service()
    count = await log_service.clear_logs(source=source)

    return {
        "status": "success",
        "message": f"Cleared {count} log entries",
        "count": count
    }
