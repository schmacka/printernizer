"""
Slicing API router.

REST endpoints for slicer management and slicing operations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
import structlog

from src.models.slicer import (
    SlicerConfig,
    SlicerProfile,
    SlicingJob,
    SlicingJobRequest,
    SlicingJobResponse,
    SlicingJobStatus,
    SliceAndPrintRequest,
    ProfileType,
)
from src.services.slicer_service import SlicerService
from src.services.slicing_queue import SlicingQueue
from src.utils.errors import (
    NotFoundError as PrinternizerNotFoundError,
    success_response,
)
from src.utils.dependencies import get_slicer_service, get_slicing_queue

logger = structlog.get_logger()
router = APIRouter()


# Response models
class SlicerListResponse(BaseModel):
    """Response model for slicer list."""
    slicers: List[SlicerConfig]
    count: int


class ProfileListResponse(BaseModel):
    """Response model for profile list."""
    profiles: List[SlicerProfile]
    count: int


class JobListResponse(BaseModel):
    """Response model for job list."""
    jobs: List[SlicingJobResponse]
    count: int


class DetectSlicersResponse(BaseModel):
    """Response model for slicer detection."""
    detected: List[SlicerConfig]
    count: int


class ImportProfilesResponse(BaseModel):
    """Response model for profile import."""
    profiles: List[SlicerProfile]
    count: int


# =====================================================
# SLICER MANAGEMENT ENDPOINTS
# =====================================================

@router.get("", response_model=SlicerListResponse)
async def list_slicers(
    available_only: bool = Query(False, description="Only return available slicers"),
    slicer_service: SlicerService = Depends(get_slicer_service),
):
    """
    List all registered slicers.

    Args:
        available_only: Only return slicers that are currently available
        slicer_service: Slicer service dependency

    Returns:
        List of slicer configurations
    """
    try:
        slicers = await slicer_service.list_slicers(available_only=available_only)
        return SlicerListResponse(slicers=slicers, count=len(slicers))
    except Exception as e:
        logger.error("Failed to list slicers", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list slicers: {str(e)}"
        )


@router.post("/detect", response_model=DetectSlicersResponse)
async def detect_slicers(
    slicer_service: SlicerService = Depends(get_slicer_service),
):
    """
    Detect and register available slicers on the system.

    Args:
        slicer_service: Slicer service dependency

    Returns:
        List of detected and registered slicers
    """
    try:
        detected = await slicer_service.detect_and_register_slicers()
        return DetectSlicersResponse(detected=detected, count=len(detected))
    except Exception as e:
        logger.error("Failed to detect slicers", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect slicers: {str(e)}"
        )


@router.get("/{slicer_id}", response_model=SlicerConfig)
async def get_slicer(
    slicer_id: str,
    slicer_service: SlicerService = Depends(get_slicer_service),
):
    """
    Get slicer configuration by ID.

    Args:
        slicer_id: Slicer configuration ID
        slicer_service: Slicer service dependency

    Returns:
        Slicer configuration
    """
    try:
        slicer = await slicer_service.get_slicer(slicer_id)
        return slicer
    except PrinternizerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to get slicer", slicer_id=slicer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get slicer: {str(e)}"
        )


@router.delete("/{slicer_id}")
async def delete_slicer(
    slicer_id: str,
    slicer_service: SlicerService = Depends(get_slicer_service),
):
    """
    Delete slicer configuration.

    Args:
        slicer_id: Slicer configuration ID
        slicer_service: Slicer service dependency

    Returns:
        Success response
    """
    try:
        await slicer_service.delete_slicer(slicer_id)
        return success_response(message="Slicer deleted successfully")
    except Exception as e:
        logger.error("Failed to delete slicer", slicer_id=slicer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete slicer: {str(e)}"
        )


# =====================================================
# PROFILE MANAGEMENT ENDPOINTS
# =====================================================

@router.get("/{slicer_id}/profiles", response_model=ProfileListResponse)
async def list_profiles(
    slicer_id: str,
    profile_type: Optional[ProfileType] = Query(None, description="Filter by profile type"),
    slicer_service: SlicerService = Depends(get_slicer_service),
):
    """
    List profiles for a slicer.

    Args:
        slicer_id: Slicer configuration ID
        profile_type: Optional profile type filter
        slicer_service: Slicer service dependency

    Returns:
        List of profiles
    """
    try:
        profiles = await slicer_service.list_profiles(
            slicer_id=slicer_id,
            profile_type=profile_type
        )
        return ProfileListResponse(profiles=profiles, count=len(profiles))
    except Exception as e:
        logger.error("Failed to list profiles", slicer_id=slicer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list profiles: {str(e)}"
        )


@router.post("/{slicer_id}/profiles/import", response_model=ImportProfilesResponse)
async def import_profiles(
    slicer_id: str,
    slicer_service: SlicerService = Depends(get_slicer_service),
):
    """
    Import profiles from slicer config directory.

    Args:
        slicer_id: Slicer configuration ID
        slicer_service: Slicer service dependency

    Returns:
        List of imported profiles
    """
    try:
        profiles = await slicer_service.import_profiles(slicer_id)
        return ImportProfilesResponse(profiles=profiles, count=len(profiles))
    except PrinternizerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to import profiles", slicer_id=slicer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import profiles: {str(e)}"
        )


@router.get("/profiles/{profile_id}", response_model=SlicerProfile)
async def get_profile(
    profile_id: str,
    slicer_service: SlicerService = Depends(get_slicer_service),
):
    """
    Get profile by ID.

    Args:
        profile_id: Profile ID
        slicer_service: Slicer service dependency

    Returns:
        Profile configuration
    """
    try:
        profile = await slicer_service.get_profile(profile_id)
        return profile
    except PrinternizerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to get profile", profile_id=profile_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )


@router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: str,
    slicer_service: SlicerService = Depends(get_slicer_service),
):
    """
    Delete profile.

    Args:
        profile_id: Profile ID
        slicer_service: Slicer service dependency

    Returns:
        Success response
    """
    try:
        await slicer_service.delete_profile(profile_id)
        return success_response(message="Profile deleted successfully")
    except Exception as e:
        logger.error("Failed to delete profile", profile_id=profile_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )


# =====================================================
# SLICING JOB ENDPOINTS
# =====================================================

@router.post("/jobs", response_model=SlicingJobResponse)
async def create_slicing_job(
    job_request: SlicingJobRequest,
    slicing_queue: SlicingQueue = Depends(get_slicing_queue),
):
    """
    Create a slicing job.

    Args:
        job_request: Slicing job request
        slicing_queue: Slicing queue dependency

    Returns:
        Created slicing job
    """
    try:
        job = await slicing_queue.create_job(job_request)
        return await _job_to_response(job, slicing_queue)
    except Exception as e:
        logger.error("Failed to create slicing job", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create slicing job: {str(e)}"
        )


@router.get("/jobs", response_model=JobListResponse)
async def list_slicing_jobs(
    status_filter: Optional[SlicingJobStatus] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    slicing_queue: SlicingQueue = Depends(get_slicing_queue),
):
    """
    List slicing jobs.

    Args:
        status_filter: Optional status filter
        limit: Maximum number of jobs to return
        slicing_queue: Slicing queue dependency

    Returns:
        List of slicing jobs
    """
    try:
        jobs = await slicing_queue.list_jobs(status=status_filter, limit=limit)
        job_responses = [await _job_to_response(job, slicing_queue) for job in jobs]
        return JobListResponse(jobs=job_responses, count=len(job_responses))
    except Exception as e:
        logger.error("Failed to list slicing jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list slicing jobs: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=SlicingJobResponse)
async def get_slicing_job(
    job_id: str,
    slicing_queue: SlicingQueue = Depends(get_slicing_queue),
):
    """
    Get slicing job by ID.

    Args:
        job_id: Job ID
        slicing_queue: Slicing queue dependency

    Returns:
        Slicing job
    """
    try:
        job = await slicing_queue.get_job(job_id)
        return await _job_to_response(job, slicing_queue)
    except PrinternizerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to get slicing job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get slicing job: {str(e)}"
        )


@router.post("/jobs/{job_id}/cancel")
async def cancel_slicing_job(
    job_id: str,
    slicing_queue: SlicingQueue = Depends(get_slicing_queue),
):
    """
    Cancel a slicing job.

    Args:
        job_id: Job ID
        slicing_queue: Slicing queue dependency

    Returns:
        Success response
    """
    try:
        await slicing_queue.cancel_job(job_id)
        return success_response(message="Slicing job cancelled successfully")
    except PrinternizerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to cancel slicing job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel slicing job: {str(e)}"
        )


@router.delete("/jobs/{job_id}")
async def delete_slicing_job(
    job_id: str,
    slicing_queue: SlicingQueue = Depends(get_slicing_queue),
):
    """
    Delete a slicing job.

    Args:
        job_id: Job ID
        slicing_queue: Slicing queue dependency

    Returns:
        Success response
    """
    try:
        await slicing_queue.delete_job(job_id)
        return success_response(message="Slicing job deleted successfully")
    except PrinternizerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to delete slicing job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete slicing job: {str(e)}"
        )


# =====================================================
# QUICK ACTION ENDPOINTS
# =====================================================

@router.post("/library/{checksum}/slice", response_model=SlicingJobResponse)
async def slice_library_file(
    checksum: str,
    job_request: SlicingJobRequest,
    slicing_queue: SlicingQueue = Depends(get_slicing_queue),
):
    """
    Slice a library file.

    Args:
        checksum: File checksum
        job_request: Slicing job request
        slicing_queue: Slicing queue dependency

    Returns:
        Created slicing job
    """
    # Override checksum from URL
    job_request.file_checksum = checksum
    return await create_slicing_job(job_request, slicing_queue)


@router.post("/slice-and-print", response_model=SlicingJobResponse)
async def slice_and_print(
    request: SliceAndPrintRequest,
    slicing_queue: SlicingQueue = Depends(get_slicing_queue),
):
    """
    Slice a file and automatically upload to printer (optionally start print).

    Args:
        request: Slice and print request
        slicing_queue: Slicing queue dependency

    Returns:
        Created slicing job
    """
    job_request = SlicingJobRequest(
        file_checksum=request.file_checksum,
        slicer_id=request.slicer_id,
        profile_id=request.profile_id,
        target_printer_id=request.printer_id,
        priority=request.priority,
        auto_upload=True,
        auto_start=request.auto_start,
    )
    
    return await create_slicing_job(job_request, slicing_queue)


# =====================================================
# HELPER FUNCTIONS
# =====================================================

async def _job_to_response(job: SlicingJob, slicing_queue: SlicingQueue) -> SlicingJobResponse:
    """
    Convert SlicingJob to SlicingJobResponse with additional metadata.

    Args:
        job: Slicing job
        slicing_queue: Slicing queue service

    Returns:
        Slicing job response
    """
    # Get slicer and profile names
    slicer_name = None
    profile_name = None
    filename = None
    
    try:
        slicer = await slicing_queue.slicer_service.get_slicer(job.slicer_id)
        slicer_name = slicer.name
    except Exception:
        pass
    
    try:
        profile = await slicing_queue.slicer_service.get_profile(job.profile_id)
        profile_name = profile.profile_name
    except Exception:
        pass
    
    # Get filename from library
    if slicing_queue.library_service:
        try:
            library_file = await slicing_queue.library_service.get_file_by_checksum(job.file_checksum)
            if library_file:
                filename = library_file.get("filename")
        except Exception:
            pass
    
    return SlicingJobResponse(
        id=job.id,
        file_checksum=job.file_checksum,
        filename=filename,
        slicer_id=job.slicer_id,
        slicer_name=slicer_name,
        profile_id=job.profile_id,
        profile_name=profile_name,
        target_printer_id=job.target_printer_id,
        status=job.status,
        priority=job.priority,
        progress=job.progress,
        output_file_path=job.output_file_path,
        estimated_print_time=job.estimated_print_time,
        filament_used=job.filament_used,
        error_message=job.error_message,
        retry_count=job.retry_count,
        auto_upload=job.auto_upload,
        auto_start=job.auto_start,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
