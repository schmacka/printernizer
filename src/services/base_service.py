"""
Base service class for common service patterns.

Provides standardized initialization and lifecycle management.
"""

from abc import ABC
from typing import Optional
import structlog

from src.database.database import Database


logger = structlog.get_logger()


class BaseService(ABC):
    """
    Base class for all Printernizer services.

    Provides common patterns:
    - Initialization tracking
    - Database access
    - Lifecycle management

    Usage:
        class MyService(BaseService):
            def __init__(self, database: Database, **kwargs):
                super().__init__(database)
                # Additional initialization

            async def initialize(self):
                '''Initialize service resources.'''
                await super().initialize()  # Marks as initialized
                # Service-specific initialization
                await self._create_tables()

            async def shutdown(self):
                '''Cleanup service resources.'''
                # Service-specific cleanup
                await super().shutdown()  # Marks as not initialized
    """

    def __init__(self, database: Database):
        """
        Initialize base service.

        Args:
            database: Database instance for storage
        """
        self.db = database
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize service.

        Override in subclasses to add service-specific initialization.
        Always call super().initialize() to mark service as initialized.
        """
        if self._initialized:
            logger.debug(f"{self.__class__.__name__} already initialized")
            return

        self._initialized = True
        logger.debug(f"{self.__class__.__name__} initialized")

    async def shutdown(self) -> None:
        """
        Shutdown service and cleanup resources.

        Override in subclasses to add service-specific cleanup.
        Always call super().shutdown() to mark service as not initialized.
        """
        if not self._initialized:
            logger.debug(f"{self.__class__.__name__} already shutdown")
            return

        self._initialized = False
        logger.debug(f"{self.__class__.__name__} shutdown")

    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized
