"""API routers for Printernizer."""

from .health import router as health_router
from .printers import router as printers_router
from .jobs import router as jobs_router
from .files import router as files_router
from .analytics import router as analytics_router
from .system import router as system_router
from .websocket import router as websocket_router
from .settings import router as settings_router
from .errors import router as errors_router
from .camera import router as camera_router

__all__ = [
    "health_router",
    "printers_router", 
    "jobs_router",
    "files_router",
    "analytics_router",
    "system_router",
    "websocket_router",
    "settings_router",
    "errors_router",
    "camera_router"
]