"""Timelapse management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
import structlog

from src.models.timelapse import (
    Timelapse,
    TimelapseStatus,
    TimelapseStats,
    TimelapseLinkJob,
    TimelapseBulkDelete,
    TimelapseBulkDeleteResult
)
from src.services.timelapse_service import TimelapseService
from src.utils.dependencies import get_timelapse_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=List[dict])
async def list_timelapses(
    status: Optional[TimelapseStatus] = Query(None, description="Filter by status"),
    linked_only: bool = Query(False, description="Show only timelapses linked to jobs"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    List all timelapses with optional filtering.

    - **status**: Filter by timelapse status
    - **linked_only**: Only show timelapses linked to jobs
    - **limit**: Maximum number of results (1-1000)
    - **offset**: Pagination offset
    """
    try:
        timelapses = await timelapse_service.get_timelapses(
            status=status,
            linked_only=linked_only,
            limit=limit,
            offset=offset
        )
        return timelapses
    except Exception as e:
        logger.error("Failed to list timelapses", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve timelapses"
        )


@router.get("/stats", response_model=TimelapseStats)
async def get_timelapse_stats(
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Get timelapse statistics including storage usage and queue status.

    Returns counts for each status and total storage used.
    """
    try:
        stats = await timelapse_service.get_stats()
        return TimelapseStats(**stats)
    except Exception as e:
        logger.error("Failed to get timelapse stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.get("/{timelapse_id}", response_model=dict)
async def get_timelapse(
    timelapse_id: str,
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Get specific timelapse details by ID.

    - **timelapse_id**: Unique timelapse identifier
    """
    try:
        timelapse = await timelapse_service.get_timelapse(timelapse_id)

        if not timelapse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Timelapse {timelapse_id} not found"
            )

        return timelapse
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get timelapse", timelapse_id=timelapse_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve timelapse"
        )


@router.post("/{timelapse_id}/process", response_model=dict)
async def trigger_processing(
    timelapse_id: str,
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Manually trigger processing for a timelapse.

    Immediately sets status to pending, bypassing the auto-detection timeout.

    - **timelapse_id**: Unique timelapse identifier
    """
    try:
        timelapse = await timelapse_service.trigger_processing(timelapse_id)

        if not timelapse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Timelapse {timelapse_id} not found"
            )

        return timelapse
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to trigger processing", timelapse_id=timelapse_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger processing"
        )


@router.delete("/{timelapse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timelapse(
    timelapse_id: str,
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Delete timelapse video and database record.

    - **timelapse_id**: Unique timelapse identifier

    Note: This is a placeholder for Phase 1. Full implementation in Phase 2.
    """
    # Phase 2 will implement actual deletion
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deletion will be implemented in Phase 2"
    )


@router.patch("/{timelapse_id}/link", response_model=dict)
async def link_to_job(
    timelapse_id: str,
    link_data: TimelapseLinkJob,
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Manually link timelapse to a job.

    - **timelapse_id**: Unique timelapse identifier
    - **job_id**: Job ID to link to

    Note: This is a placeholder for Phase 1. Full implementation in Phase 2.
    """
    # Phase 2 will implement job linking
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Job linking will be implemented in Phase 2"
    )


@router.patch("/{timelapse_id}/pin", response_model=dict)
async def toggle_pin(
    timelapse_id: str,
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Toggle pinned status for timelapse.

    Pinned timelapses are exempt from cleanup recommendations.

    - **timelapse_id**: Unique timelapse identifier

    Note: This is a placeholder for Phase 1. Full implementation in Phase 2.
    """
    # Phase 2 will implement pinning
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Pinning will be implemented in Phase 2"
    )


@router.get("/cleanup/candidates", response_model=List[dict])
async def get_cleanup_candidates(
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Get timelapses recommended for deletion.

    Returns videos older than the configured threshold and not pinned.

    Note: This is a placeholder for Phase 1. Full implementation in Phase 2.
    """
    # Phase 2 will implement cleanup candidates
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Cleanup recommendations will be implemented in Phase 2"
    )


@router.post("/bulk-delete", response_model=TimelapseBulkDeleteResult)
async def bulk_delete_timelapses(
    delete_request: TimelapseBulkDelete,
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Delete multiple timelapses in one operation.

    - **timelapse_ids**: List of timelapse IDs to delete

    Returns count of successful and failed deletions.

    Note: This is a placeholder for Phase 1. Full implementation in Phase 2.
    """
    # Phase 2 will implement bulk deletion
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Bulk deletion will be implemented in Phase 2"
    )
