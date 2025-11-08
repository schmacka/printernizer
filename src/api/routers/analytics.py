"""Analytics and reporting endpoints."""

from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
import structlog

from src.services.analytics_service import AnalyticsService
from src.utils.dependencies import get_analytics_service
from src.utils.errors import success_response


logger = structlog.get_logger()
router = APIRouter(prefix="/analytics")


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


class OverviewResponse(BaseModel):
    """Overview statistics response for dashboard."""
    jobs: dict  # Contains job statistics 
    files: dict  # Contains file statistics
    printers: dict  # Contains printer statistics


@router.get("/summary", response_model=AnalyticsResponse)
async def get_analytics_summary(
    start_date: Optional[date] = Query(None, description="Start date for analytics period"),
    end_date: Optional[date] = Query(None, description="End date for analytics period"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get overall analytics summary."""
    analytics = await analytics_service.get_summary(start_date, end_date)
    return analytics


@router.get("/business", response_model=BusinessAnalyticsResponse)
async def get_business_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics period"),
    end_date: Optional[date] = Query(None, description="End date for analytics period"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get business analytics for print operations."""
    analytics = await analytics_service.get_business_analytics(start_date, end_date)
    return analytics


@router.get("/overview", response_model=OverviewResponse)
async def get_analytics_overview(
    period: Optional[str] = Query('day', description="Period for analytics (day, week, month)"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get dashboard overview statistics."""
    overview = await analytics_service.get_dashboard_overview(period)
    return overview