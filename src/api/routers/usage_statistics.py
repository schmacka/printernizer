"""
Usage statistics API endpoints.

Provides RESTful endpoints for managing usage statistics collection:
- Viewing local statistics
- Opt-in/opt-out management
- Data export and deletion

All endpoints respect user privacy and provide full transparency.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog

from src.models.usage_statistics import LocalStatsResponse, OptInResponse

logger = structlog.get_logger()
router = APIRouter()


# Response models
class DeleteResponse(BaseModel):
    """Response for delete operations."""
    success: bool
    deleted_events: int
    message: str


@router.get("/local", response_model=LocalStatsResponse)
async def get_local_statistics(request: Request):
    """
    Get local usage statistics summary.

    Returns a human-readable summary of all statistics collected
    locally. Includes this week's activity and opt-in status.

    **Privacy**: All data is from local storage only.

    Example response:
    ```json
    {
        "installation_id": "550e8400-e29b-41d4-a716-446655440000",
        "first_seen": "2024-11-01T00:00:00Z",
        "opt_in_status": "disabled",
        "total_events": 1234,
        "this_week": {
            "job_count": 23,
            "file_count": 18,
            "error_count": 2
        },
        "last_submission": null
    }
    ```
    """
    try:
        stats_service = request.app.state.usage_statistics_service

        if not stats_service:
            raise HTTPException(
                status_code=503,
                detail="Usage statistics service not available"
            )

        stats = await stats_service.get_local_stats()
        return stats

    except Exception as e:
        logger.error("Failed to get local statistics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.post("/opt-in", response_model=OptInResponse)
async def opt_in_statistics(request: Request):
    """
    Enable usage statistics collection and submission.

    Generates an anonymous installation ID if one doesn't exist.
    After opting in, statistics will be submitted weekly to help
    improve Printernizer.

    **What we collect**:
    - App version and deployment mode
    - Number and types of printers
    - Feature usage (on/off)
    - Anonymous error types

    **What we DON'T collect**:
    - Personal information
    - File names or content
    - IP addresses
    - Printer serial numbers

    See privacy policy for complete details.

    Example response:
    ```json
    {
        "success": true,
        "installation_id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "Usage statistics enabled. Thank you for helping improve Printernizer!"
    }
    ```
    """
    try:
        stats_service = request.app.state.usage_statistics_service

        if not stats_service:
            raise HTTPException(
                status_code=503,
                detail="Usage statistics service not available"
            )

        response = await stats_service.opt_in()

        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=response.message
            )

        logger.info("User opted in to usage statistics",
                   installation_id=response.installation_id)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to opt in", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enable statistics: {str(e)}"
        )


@router.post("/opt-out", response_model=OptInResponse)
async def opt_out_statistics(request: Request):
    """
    Disable usage statistics submission.

    Local data is preserved but will no longer be submitted.
    You can delete local data separately using DELETE /usage-stats.

    Example response:
    ```json
    {
        "success": true,
        "message": "Usage statistics disabled. Your data will remain local."
    }
    ```
    """
    try:
        stats_service = request.app.state.usage_statistics_service

        if not stats_service:
            raise HTTPException(
                status_code=503,
                detail="Usage statistics service not available"
            )

        response = await stats_service.opt_out()

        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=response.message
            )

        logger.info("User opted out of usage statistics")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to opt out", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disable statistics: {str(e)}"
        )


@router.get("/export")
async def export_statistics(request: Request):
    """
    Export all local usage statistics as JSON.

    Downloads a complete export of all collected data in JSON format.
    Provides full transparency by allowing users to see exactly
    what has been collected.

    **Download**: Returns a JSON file for download.

    Example response (as file download):
    ```json
    {
        "events": [
            {
                "id": "550e8400...",
                "event_type": "job_completed",
                "timestamp": "2024-11-20T12:00:00Z",
                "metadata": {"printer_type": "bambu_lab"},
                "submitted": false
            }
        ],
        "settings": {
            "opt_in_status": "disabled",
            "installation_id": "550e8400..."
        },
        "exported_at": "2024-11-20T14:30:00Z",
        "export_version": "1.0"
    }
    ```
    """
    try:
        stats_service = request.app.state.usage_statistics_service

        if not stats_service:
            raise HTTPException(
                status_code=503,
                detail="Usage statistics service not available"
            )

        json_data = await stats_service.export_stats()

        # Return as downloadable JSON file
        return Response(
            content=json_data,
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=usage-statistics-export.json"
            }
        )

    except Exception as e:
        logger.error("Failed to export statistics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export statistics: {str(e)}"
        )


@router.delete("", response_model=DeleteResponse)
async def delete_all_statistics(request: Request):
    """
    Delete all local usage statistics.

    Removes all locally stored events while preserving settings
    (opt-in status, installation ID). Use this to clear your
    local data while keeping your preferences.

    **Important**: This only deletes local data. If you previously
    opted in and data was submitted, contact us to delete remote data.

    Example response:
    ```json
    {
        "success": true,
        "deleted_events": 1234,
        "message": "All local statistics have been deleted."
    }
    ```
    """
    try:
        stats_service = request.app.state.usage_statistics_service

        if not stats_service:
            raise HTTPException(
                status_code=503,
                detail="Usage statistics service not available"
            )

        # Get count before deletion for response
        total_events = await stats_service.repository.get_total_event_count()

        # Delete all events
        success = await stats_service.delete_all_stats()

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete statistics"
            )

        logger.info("All usage statistics deleted", deleted_count=total_events)

        return DeleteResponse(
            success=True,
            deleted_events=total_events,
            message="All local statistics have been deleted."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete statistics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete statistics: {str(e)}"
        )


@router.get("/status")
async def get_statistics_status(request: Request) -> Dict[str, Any]:
    """
    Get usage statistics service status.

    Quick status check for the statistics collection service.
    Useful for health checks and UI status indicators.

    Example response:
    ```json
    {
        "service_available": true,
        "opted_in": false,
        "total_events": 1234,
        "collection_active": true
    }
    ```
    """
    try:
        stats_service = request.app.state.usage_statistics_service

        if not stats_service:
            return {
                "service_available": False,
                "opted_in": False,
                "total_events": 0,
                "collection_active": False
            }

        opted_in = await stats_service.is_opted_in()
        total_events = await stats_service.repository.get_total_event_count()

        return {
            "service_available": True,
            "opted_in": opted_in,
            "total_events": total_events,
            "collection_active": True
        }

    except Exception as e:
        logger.error("Failed to get statistics status", error=str(e))
        return {
            "service_available": False,
            "opted_in": False,
            "total_events": 0,
            "collection_active": False,
            "error": "Failed to retrieve statistics status"
        }
