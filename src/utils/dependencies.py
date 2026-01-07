"""FastAPI dependency providers."""

from fastapi import Depends, Request

from src.database.database import Database
from src.database.repositories import (
    SnapshotRepository,
    TrendingRepository,
    IdeaRepository,
    PrinterRepository,
    JobRepository,
    FileRepository
)
from src.services.config_service import ConfigService
from src.services.printer_service import PrinterService
from src.services.job_service import JobService
from src.services.file_service import FileService
from src.services.analytics_service import AnalyticsService
from src.services.event_service import EventService
from src.services.file_watcher_service import FileWatcherService
from src.services.idea_service import IdeaService
# from src.services.trending_service import TrendingService  # DISABLED
from src.services.thumbnail_service import ThumbnailService
from src.services.url_parser_service import UrlParserService
from src.services.material_service import MaterialService
from src.services.timelapse_service import TimelapseService
from src.services.search_service import SearchService
from src.services.camera_snapshot_service import CameraSnapshotService
from src.services.slicer_service import SlicerService
from src.services.slicing_queue import SlicingQueue


async def get_database(request: Request) -> Database:
    """Get database instance from app state."""
    return request.app.state.database


async def get_snapshot_repository(
    database: Database = Depends(get_database)
) -> SnapshotRepository:
    """Get snapshot repository instance."""
    return SnapshotRepository(database._connection)


async def get_trending_repository(
    database: Database = Depends(get_database)
) -> TrendingRepository:
    """Get trending repository instance."""
    return TrendingRepository(database._connection)


async def get_idea_repository(
    database: Database = Depends(get_database)
) -> IdeaRepository:
    """Get idea repository instance."""
    return IdeaRepository(database._connection)


async def get_printer_repository(
    database: Database = Depends(get_database)
) -> PrinterRepository:
    """Get printer repository instance."""
    return PrinterRepository(database._connection)


async def get_job_repository(
    database: Database = Depends(get_database)
) -> JobRepository:
    """Get job repository instance."""
    return JobRepository(database._connection)


async def get_file_repository(
    database: Database = Depends(get_database)
) -> FileRepository:
    """Get file repository instance."""
    return FileRepository(database._connection)


async def get_config_service(request: Request) -> ConfigService:
    """Get config service instance from app state."""
    return request.app.state.config_service


async def get_event_service(request: Request) -> EventService:
    """Get event service instance from app state.""" 
    return request.app.state.event_service


async def get_printer_service(request: Request) -> PrinterService:
    """Get printer service instance from app state."""
    return request.app.state.printer_service


async def get_job_service(request: Request) -> JobService:
    """Get job service instance from app state."""
    return request.app.state.job_service


async def get_file_service(request: Request) -> FileService:
    """Get file service instance from app state."""
    return request.app.state.file_service


async def get_analytics_service(
    database: Database = Depends(get_database)
) -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService(database)


async def get_idea_service(
    database: Database = Depends(get_database)
) -> IdeaService:
    """Get idea service instance."""
    return IdeaService(database)


# DISABLED - Trending service disabled
# async def get_trending_service(request: Request) -> TrendingService:
#     """Get trending service instance from app state."""
#     return request.app.state.trending_service


async def get_thumbnail_service(request: Request) -> ThumbnailService:
    """Get thumbnail service instance from app state."""
    return request.app.state.thumbnail_service


async def get_url_parser_service(request: Request) -> UrlParserService:
    """Get URL parser service instance from app state."""
    return request.app.state.url_parser_service


async def get_material_service(request: Request) -> MaterialService:
    """Get material service instance from app state."""
    return request.app.state.material_service
async def get_timelapse_service(request: Request) -> TimelapseService:
    """Get timelapse service instance from app state."""
    return request.app.state.timelapse_service


async def get_search_service(
    database: Database = Depends(get_database),
    request: Request = None
) -> SearchService:
    """Get search service instance."""
    file_service = request.app.state.file_service if request else None
    idea_service = IdeaService(database)
    return SearchService(database, file_service, idea_service)


async def get_camera_snapshot_service(request: Request) -> CameraSnapshotService:
    """Get camera snapshot service instance from app state."""
    return request.app.state.camera_snapshot_service


async def get_slicer_service(request: Request) -> SlicerService:
    """Get slicer service instance from app state."""
    return request.app.state.slicer_service


async def get_slicing_queue(request: Request) -> SlicingQueue:
    """Get slicing queue instance from app state."""
    return request.app.state.slicing_queue
