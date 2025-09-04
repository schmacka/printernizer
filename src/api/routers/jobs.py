"""Job management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
import structlog

from models.job import Job, JobStatus
from services.job_service import JobService
from utils.dependencies import get_job_service


logger = structlog.get_logger()
router = APIRouter()


class JobResponse(BaseModel):
    """Response model for job data."""
    id: UUID
    printer_id: UUID
    filename: str
    status: JobStatus
    progress_percent: float
    estimated_time_minutes: Optional[int]
    elapsed_time_minutes: Optional[int]
    remaining_time_minutes: Optional[int]
    material_used_grams: Optional[float]
    cost_eur: Optional[float]
    is_business: bool
    customer_name: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: str
    updated_at: str


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    printer_id: Optional[UUID] = Query(None, description="Filter by printer ID"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    is_business: Optional[bool] = Query(None, description="Filter business/private jobs"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    job_service: JobService = Depends(get_job_service)
):
    """List jobs with optional filtering."""
    try:
        jobs = await job_service.list_jobs(
            printer_id=printer_id,
            status=status,
            is_business=is_business,
            limit=limit,
            offset=offset
        )
        return [JobResponse.model_validate(job.__dict__) for job in jobs]
    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
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
        return JobResponse.model_validate(job.__dict__)
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