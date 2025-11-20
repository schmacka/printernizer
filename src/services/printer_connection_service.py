"""
Printer connection service for managing printer lifecycle and connections.

This service is responsible for initializing printers, creating printer instances,
managing connections and disconnections, and performing health checks.

Part of PrinterService refactoring - Phase 2 technical debt reduction.
"""
import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from src.database.database import Database
from src.database.repositories import PrinterRepository
from src.services.event_service import EventService
from src.services.config_service import ConfigService
from src.printers import BambuLabPrinter, PrusaPrinter, BasePrinter
from src.utils.exceptions import PrinterConnectionError, NotFoundError

logger = structlog.get_logger()


class PrinterConnectionService:
    """
    Service for managing printer connections and lifecycle.

    This service handles:
    - Loading printer configurations
    - Creating printer instances (BambuLab, Prusa)
    - Connection/disconnection management
    - Database synchronization
    - Health checking
    - Background connection tasks

    Events Emitted:
    - printer_connection_progress: Connection status updates
    - printer_connected: Successful connection
    - printer_disconnected: Disconnection complete

    Example:
        >>> conn_svc = PrinterConnectionService(database, event_service, config_service)
        >>> await conn_svc.initialize()
        >>> success = await conn_svc.connect_printer("bambu_001")
    """

    def __init__(
        self,
        database: Database,
        event_service: EventService,
        config_service: ConfigService,
        file_service=None,
        monitoring_service=None,
        usage_stats_service=None
    ):
        """
        Initialize printer connection service.

        Args:
            database: Database instance for storing printer data
            event_service: Event service for emitting connection events
            config_service: Config service for loading printer configurations
            file_service: Optional file service (injected to printer instances)
            monitoring_service: Optional monitoring service for auto-job creation on startup
            usage_stats_service: Optional usage statistics service for telemetry
        """
        self.database = database
        self.printer_repo = PrinterRepository(database._connection)
        self.event_service = event_service
        self.config_service = config_service
        self.file_service = file_service
        self.monitoring_service = monitoring_service
        self.usage_stats_service = usage_stats_service

        # Printer instance management
        self.printer_instances: Dict[str, BasePrinter] = {}

        logger.info("PrinterConnectionService initialized")

    async def initialize(self) -> None:
        """
        Initialize printer connection service.

        Loads printer configurations from config service, creates printer instances,
        and synchronizes with database.

        Example:
            >>> await conn_svc.initialize()
            >>> print(f"Loaded {len(conn_svc.printer_instances)} printers")
        """
        logger.info("Initializing printer connection service")
        await self._load_printers()
        await self._sync_database_printers()
        logger.info("Printer connection service initialization complete",
                   printer_count=len(self.printer_instances))

    async def _load_printers(self) -> None:
        """
        Load printer configurations and create instances.

        Reads printer configurations from config service and creates
        appropriate printer instances (BambuLabPrinter or PrusaPrinter).

        Raises:
            Exception: If printer instance creation fails (logged, not raised)
        """
        printer_configs = self.config_service.get_active_printers()

        for printer_id, config in printer_configs.items():
            try:
                # Create printer instance based on type
                printer_instance = self._create_printer_instance(printer_id, config)

                if printer_instance:
                    self.printer_instances[printer_id] = printer_instance
                    logger.info("Loaded printer instance",
                               printer_id=printer_id,
                               type=config.type)

            except Exception as e:
                logger.error("Failed to create printer instance",
                           printer_id=printer_id,
                           error=str(e))

        logger.info("Printer instances loaded", count=len(self.printer_instances))

    def _create_printer_instance(
        self,
        printer_id: str,
        config
    ) -> Optional[BasePrinter]:
        """
        Create printer instance based on configuration.

        Args:
            printer_id: Unique printer identifier
            config: Printer configuration object

        Returns:
            BasePrinter instance (BambuLabPrinter or PrusaPrinter), or None if type unknown

        Example:
            >>> config = config_service.get_printer("bambu_001")
            >>> instance = conn_svc._create_printer_instance("bambu_001", config)
        """
        if config.type == "bambu_lab":
            return BambuLabPrinter(
                printer_id=printer_id,
                name=config.name,
                ip_address=config.ip_address,
                access_code=config.access_code,
                serial_number=config.serial_number,
                file_service=self.file_service
            )
        elif config.type == "prusa_core":
            return PrusaPrinter(
                printer_id=printer_id,
                name=config.name,
                ip_address=config.ip_address,
                api_key=config.api_key,
                file_service=self.file_service
            )
        else:
            logger.warning("Unknown printer type",
                          printer_id=printer_id,
                          type=config.type)
            return None

    async def _sync_database_printers(self) -> None:
        """
        Sync printer configurations with database.

        Updates database with current printer instances, ensuring database
        matches loaded configuration.

        Example:
            >>> await conn_svc._sync_database_printers()
        """
        async with self.database._connection.cursor() as cursor:
            for printer_id, instance in self.printer_instances.items():
                # Insert or update printer in database
                await cursor.execute("""
                    INSERT OR REPLACE INTO printers
                    (id, name, type, ip_address, api_key, access_code, serial_number, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    printer_id,
                    instance.name,
                    getattr(instance, '__class__').__name__.lower().replace('printer', ''),
                    instance.ip_address,
                    getattr(instance, 'api_key', None),
                    getattr(instance, 'access_code', None),
                    getattr(instance, 'serial_number', None),
                    True
                ))

            await self.database._connection.commit()
        logger.info("Synchronized printers with database")

    async def connect_printer(self, printer_id: str) -> bool:
        """
        Connect to a specific printer.

        Establishes connection to the printer and updates database with connection status.

        Args:
            printer_id: Printer identifier

        Returns:
            True if connection successful, False otherwise

        Raises:
            NotFoundError: If printer not found
            PrinterConnectionError: If connection fails

        Example:
            >>> success = await conn_svc.connect_printer("bambu_001")
            >>> if success:
            ...     print("Connected!")
        """
        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)

        try:
            result = await instance.connect()
            if result:
                # Update last_seen timestamp in database when connection succeeds
                await self.printer_repo.update_status(
                    printer_id,
                    "online",  # Set status to online when connected
                    datetime.now()
                )

                # Emit connection event
                await self.event_service.emit_event("printer_connected", {
                    "printer_id": printer_id,
                    "name": instance.name,
                    "timestamp": datetime.now().isoformat()
                })

                logger.info("Printer connected successfully", printer_id=printer_id)

                # Record usage statistics (privacy-safe: only printer type, no names or IDs)
                if self.usage_stats_service:
                    await self.usage_stats_service.record_event("printer_connected", {
                        "printer_type": instance.printer_type.value if hasattr(instance, "printer_type") else "unknown"
                    })

            return result
        except Exception as e:
            logger.error("Failed to connect printer",
                        printer_id=printer_id,
                        error=str(e))
            raise PrinterConnectionError(printer_id, str(e))

    async def disconnect_printer(self, printer_id: str) -> bool:
        """
        Disconnect from a specific printer.

        Closes connection to the printer.

        Args:
            printer_id: Printer identifier

        Returns:
            True if disconnection successful, False otherwise

        Raises:
            NotFoundError: If printer not found

        Example:
            >>> success = await conn_svc.disconnect_printer("bambu_001")
        """
        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)

        try:
            await instance.disconnect()

            # Emit disconnection event
            await self.event_service.emit_event("printer_disconnected", {
                "printer_id": printer_id,
                "name": instance.name,
                "timestamp": datetime.now().isoformat()
            })

            logger.info("Printer disconnected successfully", printer_id=printer_id)

            # Record usage statistics (privacy-safe: only printer type, no names or IDs)
            if self.usage_stats_service:
                await self.usage_stats_service.record_event("printer_disconnected", {
                    "printer_type": instance.printer_type.value if hasattr(instance, "printer_type") else "unknown"
                })

            return True
        except Exception as e:
            logger.error("Failed to disconnect printer",
                        printer_id=printer_id,
                        error=str(e))
            return False

    async def connect_and_monitor_printer(
        self,
        printer_id: str,
        instance: BasePrinter,
        start_monitoring_callback=None
    ):
        """
        Connect to printer and start monitoring (background task helper).

        This method is designed to be called as a background task during
        service initialization. It connects to the printer and optionally
        starts monitoring via a callback.

        Args:
            printer_id: Printer identifier
            instance: Printer instance to connect
            start_monitoring_callback: Optional async callback to start monitoring

        Example:
            >>> task = asyncio.create_task(
            ...     conn_svc.connect_and_monitor_printer(
            ...         "bambu_001",
            ...         instance,
            ...         lambda pid: monitoring_svc.start_monitoring(pid)
            ...     )
            ... )
        """
        start_time = time.time()
        try:
            # Emit connection starting event
            await self.event_service.emit_event("printer_connection_progress", {
                "printer_id": printer_id,
                "status": "connecting",
                "message": "Initiating connection..."
            })

            if not instance.is_connected:
                logger.info("Connecting to printer", printer_id=printer_id)
                connect_start = time.time()
                connected = await instance.connect()
                connect_duration = time.time() - connect_start

                if connected:
                    # Update last_seen timestamp when connection succeeds
                    await self.printer_repo.update_status(
                        printer_id,
                        "online",
                        datetime.now()
                    )
                    logger.info("[TIMING] Printer connection successful",
                               printer_id=printer_id,
                               duration_seconds=round(connect_duration, 2))

                    # Emit connection success event
                    await self.event_service.emit_event("printer_connection_progress", {
                        "printer_id": printer_id,
                        "status": "connected",
                        "message": f"Connected in {round(connect_duration, 1)}s",
                        "duration_seconds": round(connect_duration, 2)
                    })

                    # Check if printer is already printing (startup detection)
                    if self.monitoring_service:
                        try:
                            status = await instance.get_status()
                            if status.status.value == 'printing' and status.current_job:
                                logger.info("Detected print in progress on startup",
                                           printer_id=printer_id,
                                           filename=status.current_job,
                                           progress=status.progress)

                                # Auto-create job with is_startup=True flag
                                if hasattr(self.monitoring_service, '_auto_create_job_if_needed'):
                                    await self.monitoring_service._auto_create_job_if_needed(status, is_startup=True)
                        except Exception as e:
                            logger.warning("Failed to check for active print on startup",
                                         printer_id=printer_id,
                                         error=str(e))
                else:
                    logger.warning("[TIMING] Printer connection failed",
                                  printer_id=printer_id,
                                  duration_seconds=round(connect_duration, 2))

                    # Emit connection failure event
                    await self.event_service.emit_event("printer_connection_progress", {
                        "printer_id": printer_id,
                        "status": "failed",
                        "message": "Connection failed"
                    })
                    return

            # Start monitoring if callback provided
            if start_monitoring_callback:
                await start_monitoring_callback(printer_id, instance)

            total_duration = time.time() - start_time
            logger.info("[TIMING] Printer connection and monitoring setup complete",
                       printer_id=printer_id,
                       total_duration_seconds=round(total_duration, 2))

            # Emit monitoring started event
            await self.event_service.emit_event("printer_connection_progress", {
                "printer_id": printer_id,
                "status": "monitoring",
                "message": "Monitoring active"
            })

        except Exception as e:
            duration = time.time() - start_time
            logger.error("[TIMING] Failed to connect and monitor printer",
                        printer_id=printer_id,
                        duration_seconds=round(duration, 2),
                        error=str(e),
                        exc_info=True)

            # Emit error event
            await self.event_service.emit_event("printer_connection_progress", {
                "printer_id": printer_id,
                "status": "error",
                "message": f"Error: {str(e)}"
            })

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all printer connections.

        Returns health status including connection states, monitoring status,
        and per-printer health information.

        Returns:
            Dict with keys:
                - total_printers: Total number of configured printers
                - connected_printers: Number of connected printers
                - healthy_printers: Number of healthy printers
                - printers: Per-printer health details

        Example:
            >>> health = await conn_svc.health_check()
            >>> print(f"{health['connected_printers']}/{health['total_printers']} connected")
        """
        health_status = {
            "service_active": True,
            "total_printers": len(self.printer_instances),
            "connected_printers": 0,
            "healthy_printers": 0,
            "printers": {}
        }

        for printer_id, instance in self.printer_instances.items():
            is_connected = instance.is_connected
            is_healthy = await instance.health_check() if is_connected else False

            if is_connected:
                health_status["connected_printers"] += 1
            if is_healthy:
                health_status["healthy_printers"] += 1

            health_status["printers"][printer_id] = {
                "connected": is_connected,
                "healthy": is_healthy,
                "last_seen": instance.last_status.timestamp.isoformat()
                             if instance.last_status else None,
                "name": instance.name,
                "ip_address": instance.ip_address
            }

        return health_status

    async def shutdown(self):
        """
        Gracefully shutdown all printer connections.

        Disconnects all printers and clears instance cache.

        Example:
            >>> await conn_svc.shutdown()
        """
        logger.info("Shutting down printer connection service")

        # Disconnect all printers
        for printer_id, instance in self.printer_instances.items():
            try:
                await instance.disconnect()
                logger.debug("Disconnected printer", printer_id=printer_id)
            except Exception as e:
                logger.error("Error disconnecting printer",
                            printer_id=printer_id,
                            error=str(e))

        self.printer_instances.clear()
        logger.info("Printer connection service shutdown complete")

    def get_printer_instance(self, printer_id: str) -> Optional[BasePrinter]:
        """
        Get printer driver instance by ID.

        Args:
            printer_id: Printer identifier

        Returns:
            BasePrinter instance or None if not found

        Example:
            >>> instance = conn_svc.get_printer_instance("bambu_001")
            >>> if instance and instance.is_connected:
            ...     print("Printer is connected")
        """
        return self.printer_instances.get(printer_id)

    def set_file_service(self, file_service) -> None:
        """
        Set file service dependency.

        Updates file service reference for all existing printer instances.
        This allows for late binding to resolve circular dependencies.

        Args:
            file_service: FileService instance
        """
        self.file_service = file_service

        # Update all existing printer instances
        for instance in self.printer_instances.values():
            instance.file_service = file_service

        logger.debug("File service set in PrinterConnectionService and all instances")
