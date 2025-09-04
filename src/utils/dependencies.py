"""FastAPI dependency providers."""

from fastapi import Depends, Request

from database.database import Database
from services.config_service import ConfigService
from services.printer_service import PrinterService
from services.job_service import JobService
from services.file_service import FileService
from services.analytics_service import AnalyticsService
from services.event_service import EventService


async def get_database(request: Request) -> Database:
    """Get database instance from app state."""
    return request.app.state.database


async def get_config_service(request: Request) -> ConfigService:
    """Get config service instance from app state."""
    return request.app.state.config_service


async def get_event_service(request: Request) -> EventService:
    """Get event service instance from app state.""" 
    return request.app.state.event_service


async def get_printer_service(request: Request) -> PrinterService:
    """Get printer service instance from app state."""
    return request.app.state.printer_service


async def get_job_service(
    database: Database = Depends(get_database),
    event_service: EventService = Depends(get_event_service)
) -> JobService:
    """Get job service instance."""
    return JobService(database, event_service)


async def get_file_service(
    database: Database = Depends(get_database),
    event_service: EventService = Depends(get_event_service)
) -> FileService:
    """Get file service instance."""
    return FileService(database, event_service)


async def get_analytics_service(
    database: Database = Depends(get_database)
) -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService(database)