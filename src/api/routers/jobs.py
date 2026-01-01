"""Job management endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
import structlog

from src.models.job import Job, JobStatus, JobCreate, JobUpdateRequest, JobStatusUpdateRequest, JobStatusUpdateResponse
from src.services.job_service import JobService
from src.utils.dependencies import get_job_service
from src.utils.errors import (
    JobNotFoundError,
    ValidationError as PrinternizerValidationError,
    success_response
)


logger = structlog.get_logger()
router = APIRouter()


class PaginationResponse(BaseModel):
    """Pagination information."""
    page: int
    limit: int
    total_items: int
    total_pages: int


class JobResponse(BaseModel):
    """Response model for job data."""
    id: str = Field(..., description="Unique job identifier")
    printer_id: str = Field(..., description="Printer ID where job is running")
    printer_type: str = Field(..., description="Type of printer")
    job_name: str = Field(..., description="Human-readable job name")
    filename: Optional[str] = Field(None, description="Original filename")
    status: str = Field(..., description="Current job status")
    start_time: Optional[datetime] = Field(None, description="Job start time")
    end_time: Optional[datetime] = Field(None, description="Job completion time")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")
    actual_duration: Optional[int] = Field(None, description="Actual duration in seconds")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    material_used: Optional[float] = Field(None, description="Material used in grams")
    material_cost: Optional[float] = Field(None, description="Material cost in EUR")
    power_cost: Optional[float] = Field(None, description="Power cost in EUR")
    is_business: bool = Field(False, description="Whether this is a business job")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Additional frontend-compatible fields
    progress_percent: Optional[float] = Field(None, description="Progress percentage (alias)")
    cost_eur: Optional[float] = Field(None, description="Total cost in EUR")
    started_at: Optional[str] = Field(None, description="Start time as string")
    completed_at: Optional[str] = Field(None, description="Completion time as string")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class JobListResponse(BaseModel):
    """Response model for job list with pagination."""
    jobs: List[JobResponse]
    total_count: int
    pagination: PaginationResponse


def _transform_job_to_response(job_data: dict) -> dict:
    """Transform job data to response format."""
    # Create a copy to avoid modifying the original
    response_data = job_data.copy()

    # Add frontend-compatible aliases
    if 'progress' in response_data:
        response_data['progress_percent'] = response_data['progress']

    # Calculate total cost
    material_cost = response_data.get('material_cost', 0) or 0
    power_cost = response_data.get('power_cost', 0) or 0
    response_data['cost_eur'] = material_cost + power_cost

    # Convert datetime objects to strings for frontend compatibility
    if response_data.get('start_time'):
        response_data['started_at'] = response_data['start_time'].isoformat() if isinstance(response_data['start_time'], datetime) else str(response_data['start_time'])

    if response_data.get('end_time'):
        response_data['completed_at'] = response_data['end_time'].isoformat() if isinstance(response_data['end_time'], datetime) else str(response_data['end_time'])

    return response_data


@router.get("", response_model=JobListResponse)
async def list_jobs(
    printer_id: Optional[str] = Query(None, description="Filter by printer ID"),
    job_status: Optional[str] = Query(None, description="Filter by job status"),
    is_business: Optional[bool] = Query(None, description="Filter business/private jobs"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of jobs to return"),
    page: int = Query(1, ge=1, description="Page number"),
    job_service: JobService = Depends(get_job_service)
):
    """List jobs with optional filtering and pagination."""
    # Calculate offset for database-level pagination
    offset = (page - 1) * limit

    # Get paginated jobs with total count (optimized with separate COUNT query)
    paginated_jobs, total_items = await job_service.list_jobs_with_count(
        printer_id=printer_id,
        status=job_status,
        is_business=is_business,
        limit=limit,
        offset=offset
    )
    total_pages = max(1, (total_items + limit - 1) // limit)

    # Transform jobs to response format
    job_responses = [JobResponse.model_validate(_transform_job_to_response(job)) for job in paginated_jobs]

    return JobListResponse(
        jobs=job_responses,
        total_count=total_items,
        pagination=PaginationResponse(
            page=page,
            limit=limit,
            total_items=total_items,
            total_pages=total_pages
        )
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    job_service: JobService = Depends(get_job_service)
):
    """Create a new print job."""
    try:
        job_id = await job_service.create_job(job_data.model_dump())
        job = await job_service.get_job(job_id)
        if not job:
            # This shouldn't happen, but if it does, raise an error
            raise JobNotFoundError(
                job_id=job_id,
                details={"reason": "Job created but could not be retrieved"}
            )
        return JobResponse.model_validate(_transform_job_to_response(job))
    except ValueError as e:
        # Convert service ValueError to standardized ValidationError
        raise PrinternizerValidationError(
            field="job_data",
            error=str(e)
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    job_service: JobService = Depends(get_job_service)
):
    """Get job details by ID."""
    job = await job_service.get_job(job_id)
    if not job:
        raise JobNotFoundError(job_id)
    # Job is already a dictionary from the service layer
    return JobResponse.model_validate(_transform_job_to_response(job))


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    updates: JobUpdateRequest,
    job_service: JobService = Depends(get_job_service)
):
    """
    Update job fields.

    **Editable Fields**:
    - `job_name`: Display name (required, max 200 chars)
    - `status`: Job status (pending/running/completed/failed)
    - `is_business`: Business vs personal job
    - `customer_name`: Customer name (required if is_business=true)
    - `notes`: Additional notes (max 1000 chars)
    - `file_name`: Associated file name
    - `printer_id`: Associated printer UUID

    **Non-Editable Fields**:
    - Timestamps (created_at, start_time, end_time) are managed automatically
    - `id` is immutable

    **Business Logic**:
    - If `is_business=true`, `customer_name` is required
    - `printer_id` must reference an existing printer (validation optional)

    **Returns**: Updated job object

    **Raises**:
    - 404: Job not found
    - 400: Validation error or invalid printer_id
    - 422: Invalid request body
    """
    try:
        updated_job = await job_service.update_job(job_id, updates)
        return JobResponse.model_validate(_transform_job_to_response(updated_job))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{job_id}/status", response_model=JobStatusUpdateResponse)
async def update_job_status(
    job_id: str,
    request: JobStatusUpdateRequest,
    job_service: JobService = Depends(get_job_service)
):
    """
    Update job status with transition validation.

    This endpoint manages job workflow state transitions and automatically
    updates relevant timestamps (start_time, end_time).

    **Valid Status Transitions**:
    - `pending → running`: Job started
    - `pending → completed`: Manually mark as done (skip running)
    - `pending → failed`: Manually mark as failed
    - `running → completed`: Job finished successfully
    - `running → failed`: Job failed or cancelled
    - `completed → failed`: Correct status (rare)
    - `failed → completed`: Retry succeeded (rare)

    **Invalid Transitions**:
    - Cannot restart completed/failed jobs (→ running)
    - Cannot reset to pending from any state

    **Timestamp Behavior**:
    - Setting status to `running` sets `start_time` if not already set
    - Setting status to `completed` or `failed` sets `end_time`
    - Timestamps are immutable once set (unless using force=true)

    **Completion Notes**:
    - Optional notes explaining manual status change
    - Appended to job notes with timestamp
    - Useful for audit trail

    **Force Flag**:
    - Bypasses transition validation
    - Use with caution (admin only)
    - Allows any status change

    **Returns**: Updated job with new status and timestamps

    **Raises**:
    - 404: Job not found
    - 400: Invalid status transition
    - 422: Invalid request body
    """
    try:
        # Get job to capture previous status
        job = await job_service.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        previous_status = job.get('status', 'unknown')

        # Update status with validation
        updated_job = await job_service.update_job_status(
            job_id=job_id,
            status=request.status,
            completion_notes=request.completion_notes,
            force=request.force,
            validate_transitions=True  # Enable validation for this endpoint
        )

        if not updated_job:
            raise HTTPException(status_code=500, detail="Failed to update job status")

        # Build response
        return JobStatusUpdateResponse(
            id=updated_job['id'],
            status=updated_job['status'],
            previous_status=previous_status,
            started_at=updated_job.get('start_time'),
            completed_at=updated_job.get('end_time'),
            updated_at=updated_job.get('updated_at') or datetime.now()
        )

    except ValueError as e:
        # Invalid transition
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating job status", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    job_service: JobService = Depends(get_job_service)
):
    """
    Cancel a running or queued print job.

    This will:
    1. Update the job status to CANCELLED
    2. Attempt to stop the printer if job is currently printing

    Returns:
        Success message with updated job details
    """
    # Verify job exists
    job = await job_service.get_job(job_id)
    if not job:
        raise JobNotFoundError(job_id)

    # Get current job status
    current_status = job.get('status')

    # Check if job can be cancelled
    if current_status in ['completed', 'failed', 'cancelled']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status '{current_status}'"
        )

    # Update job status to cancelled
    await job_service.update_job_status(
        job_id=job_id,
        status=JobStatus.CANCELLED.value
    )

    # Get updated job data
    updated_job = await job_service.get_job(job_id)

    logger.info("Job cancelled successfully", job_id=job_id)

    return success_response(
        message="Job cancelled successfully",
        data=JobResponse.model_validate(_transform_job_to_response(updated_job))
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    job_service: JobService = Depends(get_job_service)
):
    """Delete a job record."""
    try:
        success = await job_service.delete_job(job_id)
        if not success:
            raise JobNotFoundError(str(job_id))
    except ValueError as e:
        # Handle active job deletion attempt
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )