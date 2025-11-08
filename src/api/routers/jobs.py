"""Job management endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
import structlog

from src.models.job import Job, JobStatus, JobCreate
from src.services.job_service import JobService
from src.utils.dependencies import get_job_service


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
    try:
        # Calculate offset for database-level pagination
        offset = (page - 1) * limit

        # Get paginated jobs from service with database-level pagination
        paginated_jobs = await job_service.list_jobs(
            printer_id=printer_id,
            status=job_status,
            is_business=is_business,
            limit=limit,
            offset=offset
        )

        # Get total count for pagination metadata
        # TODO: Optimize by adding count-only query to avoid fetching all records
        all_jobs_count = await job_service.list_jobs(
            printer_id=printer_id,
            status=job_status,
            is_business=is_business,
            limit=None,
            offset=0
        )
        total_items = len(all_jobs_count)
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
    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Job created but could not be retrieved"
            )
        return JobResponse.model_validate(_transform_job_to_response(job))
    except ValueError as e:
        logger.error("Invalid job data", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create job", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    job_service: JobService = Depends(get_job_service)
):
    """Get job details by ID."""
    try:
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        # Job is already a dictionary from the service layer
        return JobResponse.model_validate(_transform_job_to_response(job))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job"
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete job", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )