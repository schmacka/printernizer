"""Timelapse management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
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
from src.utils.errors import NotFoundError

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
    timelapses = await timelapse_service.get_timelapses(
        status=status,
        linked_only=linked_only,
        limit=limit,
        offset=offset
    )
    return timelapses


@router.get("/stats", response_model=TimelapseStats)
async def get_timelapse_stats(
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Get timelapse statistics including storage usage and queue status.

    Returns counts for each status and total storage used.
    """
    stats = await timelapse_service.get_stats()
    return TimelapseStats(**stats)


@router.get("/{timelapse_id}", response_model=dict)
async def get_timelapse(
    timelapse_id: str,
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Get specific timelapse details by ID.

    - **timelapse_id**: Unique timelapse identifier
    """
    timelapse = await timelapse_service.get_timelapse(timelapse_id)

    if not timelapse:
        raise NotFoundError(resource_type="timelapse", resource_id=timelapse_id)

    return timelapse


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
    timelapse = await timelapse_service.trigger_processing(timelapse_id)

    if not timelapse:
        raise NotFoundError(resource_type="timelapse", resource_id=timelapse_id)

    return timelapse


@router.delete("/{timelapse_id}", status_code=204)
async def delete_timelapse(
    timelapse_id: str,
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Delete timelapse video and database record.

    - **timelapse_id**: Unique timelapse identifier
    """
    success = await timelapse_service.delete_timelapse(timelapse_id)

    if not success:
        raise NotFoundError(resource_type="timelapse", resource_id=timelapse_id)

    return Response(status_code=204)


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
    """
    timelapse = await timelapse_service.link_to_job(timelapse_id, link_data.job_id)

    if not timelapse:
        raise NotFoundError(resource_type="timelapse", resource_id=timelapse_id)

    return timelapse


@router.patch("/{timelapse_id}/pin", response_model=dict)
async def toggle_pin(
    timelapse_id: str,
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Toggle pinned status for timelapse.

    Pinned timelapses are exempt from cleanup recommendations.

    - **timelapse_id**: Unique timelapse identifier
    """
    timelapse = await timelapse_service.toggle_pin(timelapse_id)

    if not timelapse:
        raise NotFoundError(resource_type="timelapse", resource_id=timelapse_id)

    return timelapse


@router.get("/cleanup/candidates", response_model=List[dict])
async def get_cleanup_candidates(
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Get timelapses recommended for deletion.

    Returns videos older than the configured threshold and not pinned.
    """
    candidates = await timelapse_service.get_cleanup_candidates()
    return candidates


@router.post("/bulk-delete", response_model=TimelapseBulkDeleteResult)
async def bulk_delete_timelapses(
    delete_request: TimelapseBulkDelete,
    timelapse_service: TimelapseService = Depends(get_timelapse_service)
):
    """
    Delete multiple timelapses in one operation.

    - **timelapse_ids**: List of timelapse IDs to delete

    Returns count of successful and failed deletions.
    """
    result = await timelapse_service.bulk_delete_timelapses(delete_request.timelapse_ids)
    return TimelapseBulkDeleteResult(**result)
