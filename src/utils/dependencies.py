"""FastAPI dependency providers."""

from fastapi import Depends, Request

from src.database.database import Database
from src.services.config_service import ConfigService
from src.services.printer_service import PrinterService
from src.services.job_service import JobService
from src.services.file_service import FileService
from src.services.analytics_service import AnalyticsService
from src.services.event_service import EventService
from src.services.file_watcher_service import FileWatcherService


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


async def get_file_service(request: Request) -> FileService:
    """Get file service instance from app state."""
    return request.app.state.file_service


async def get_analytics_service(
    database: Database = Depends(get_database)
) -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService(database)