"""Analytics and reporting endpoints."""

from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
import structlog

from services.analytics_service import AnalyticsService
from utils.dependencies import get_analytics_service


logger = structlog.get_logger()
router = APIRouter()


class AnalyticsResponse(BaseModel):
    """Analytics data response."""
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_print_time_hours: float
    total_material_used_kg: float
    total_cost_eur: float
    average_job_duration_hours: float
    success_rate_percent: float


class BusinessAnalyticsResponse(BaseModel):
    """Business-specific analytics."""
    business_jobs: int
    private_jobs: int
    business_revenue_eur: float
    business_material_cost_eur: float
    business_profit_eur: float
    top_customers: list


@router.get("/summary", response_model=AnalyticsResponse)
async def get_analytics_summary(
    start_date: Optional[date] = Query(None, description="Start date for analytics period"),
    end_date: Optional[date] = Query(None, description="End date for analytics period"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get overall analytics summary."""
    try:
        analytics = await analytics_service.get_summary(start_date, end_date)
        return analytics
    except Exception as e:
        logger.error("Failed to get analytics summary", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.get("/business", response_model=BusinessAnalyticsResponse)  
async def get_business_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics period"),
    end_date: Optional[date] = Query(None, description="End date for analytics period"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get business-specific analytics for Porcus3D operations."""
    try:
        analytics = await analytics_service.get_business_analytics(start_date, end_date)
        return analytics
    except Exception as e:
        logger.error("Failed to get business analytics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve business analytics"
        )