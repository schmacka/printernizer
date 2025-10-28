"""Job management endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
import structlog

from src.models.job import Job, JobStatus
from src.services.job_service import JobService
from src.utils.dependencies import get_job_service


logger = structlog.get_logger()
router = APIRouter()


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


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    printer_id: Optional[str] = Query(None, description="Filter by printer ID"),
    job_status: Optional[str] = Query(None, description="Filter by job status"),
    is_business: Optional[bool] = Query(None, description="Filter business/private jobs"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    job_service: JobService = Depends(get_job_service)
):
    """List jobs with optional filtering."""
    try:
        jobs = await job_service.list_jobs(
            printer_id=printer_id,
            status=job_status,
            is_business=is_business,
            limit=limit,
            offset=offset
        )
        return [JobResponse.model_validate(_transform_job_to_response(job.__dict__)) for job in jobs]
    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
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
        return JobResponse.model_validate(_transform_job_to_response(job.__dict__))
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