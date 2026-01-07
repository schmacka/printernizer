"""
Printer service for managing printer connections and status.
Handles Bambu Lab and Prusa printer integrations with real-time monitoring.

REFACTORED VERSION - Phase 2 Technical Debt Reduction
This version delegates responsibilities to specialized services:
- PrinterConnectionService: Printer lifecycle and connection management
- PrinterMonitoringService: Status monitoring and auto-download logic
- PrinterControlService: Print control operations (pause/resume/stop)

The PrinterService now acts as a coordinator, maintaining backward compatibility
while using the specialized services internally.
"""
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import structlog

from src.database.database import Database
from src.services.event_service import EventService
from src.services.config_service import ConfigService
from src.services.printer_connection_service import PrinterConnectionService
from src.services.printer_monitoring_service import PrinterMonitoringService
from src.services.printer_control_service import PrinterControlService
from src.models.printer import PrinterType, PrinterStatus, Printer
from src.printers import BasePrinter
from src.utils.exceptions import PrinterConnectionError, NotFoundError

logger = structlog.get_logger()


class PrinterService:
    """
    Coordinating service for managing printers.

    This service acts as a facade/coordinator for printer-related operations,
    delegating to specialized services:
    - Connection: PrinterConnectionService
    - Monitoring: PrinterMonitoringService
    - Control: PrinterControlService

    Responsibilities:
    - Printer listing and querying
    - Printer CRUD operations
    - Status queries
    - File operations delegation
    - Coordination between specialized services
    - Backward compatibility with existing API

    Example:
        >>> printer_service = PrinterService(database, event_service, config_service)
        >>> await printer_service.initialize()
        >>> printers = await printer_service.list_printers()
    """

    def __init__(
        self,
        database: Database,
        event_service: EventService,
        config_service: ConfigService,
        file_service=None,
        usage_stats_service=None
    ):
        """
        Initialize printer service and its specialized sub-services.

        Args:
            database: Database instance
            event_service: Event service for event-driven communication
            config_service: Config service for printer configurations
            file_service: Optional file service (can be set later)
            usage_stats_service: Optional usage statistics service for telemetry
        """
        self.database = database
        self.event_service = event_service
        self.config_service = config_service
        self.file_service = file_service
        self.usage_stats_service = usage_stats_service

        # Initialize specialized services
        # Create monitoring service first (no connection service yet to avoid circular ref)
        self.monitoring = PrinterMonitoringService(
            database=database,
            event_service=event_service,
            file_service=file_service,
            connection_service=None  # Will be set after connection service is created
        )

        # Create connection service with monitoring service reference
        self.connection = PrinterConnectionService(
            database=database,
            event_service=event_service,
            config_service=config_service,
            file_service=file_service,
            monitoring_service=self.monitoring,
            usage_stats_service=usage_stats_service
        )

        # Set connection service reference in monitoring service
        self.monitoring.connection_service = self.connection

        self.control = PrinterControlService(
            event_service=event_service,
            connection_service=self.connection
        )

        logger.info("PrinterService initialized with specialized sub-services",
                   connection=True,
                   monitoring=True,
                   control=True)

    async def initialize(self) -> None:
        """
        Initialize printer service and load configured printers.

        This sets up printer instances, configures monitoring callbacks,
        and prepares the service for operation.

        Example:
            >>> await printer_service.initialize()
        """
        logger.info("Initializing printer service")

        # Initialize connection service (loads printers)
        await self.connection.initialize()

        # Setup monitoring callbacks for all printer instances
        for printer_id, instance in self.connection.printer_instances.items():
            self.monitoring.setup_status_callback(instance)

        logger.info("Printer service initialization complete",
                   printer_count=len(self.connection.printer_instances))

    # ========================================================================
    # PRINTER LISTING AND QUERYING
    # These methods stay in PrinterService as they coordinate data
    # ========================================================================

    async def list_printers(self) -> List[Printer]:
        """
        Get list of all configured printers as Printer objects.

        Returns:
            List of Printer domain model objects with current status

        Example:
            >>> printers = await printer_service.list_printers()
            >>> for printer in printers:
            ...     print(f"{printer.name}: {printer.status.value}")
        """
        printers = []

        for printer_id, instance in self.connection.printer_instances.items():
            # Determine current status
            current_status = PrinterStatus.OFFLINE
            last_seen = None

            if instance.is_connected:
                if instance.last_status:
                    current_status = instance.last_status.status
                    last_seen = instance.last_status.timestamp
                else:
                    current_status = PrinterStatus.ONLINE
                    last_seen = datetime.now()

            printer = Printer(
                id=printer_id,
                name=instance.name,
                type=PrinterType.BAMBU_LAB if 'bambu' in type(instance).__name__.lower() else PrinterType.PRUSA_CORE,
                ip_address=instance.ip_address,
                api_key=getattr(instance, 'api_key', None),
                access_code=getattr(instance, 'access_code', None),
                serial_number=getattr(instance, 'serial_number', None),
                is_active=True,
                status=current_status,
                last_seen=last_seen
            )
            printers.append(printer)

        return printers


    async def get_printer(self, printer_id: str) -> Optional[Printer]:
        """
        Get specific printer by ID as domain model.

        Args:
            printer_id: Printer identifier

        Returns:
            Printer object or None if not found

        Example:
            >>> printer = await printer_service.get_printer("bambu_001")
            >>> if printer:
            ...     print(f"Status: {printer.status.value}")
        """
        instance = self.connection.printer_instances.get(printer_id)
        if not instance:
            return None

        current_status = PrinterStatus.OFFLINE
        last_seen = None
        if instance.is_connected:
            if instance.last_status:
                current_status = instance.last_status.status
                last_seen = instance.last_status.timestamp
            else:
                current_status = PrinterStatus.ONLINE

        return Printer(
            id=printer_id,
            name=instance.name,
            type=PrinterType.BAMBU_LAB if 'bambu' in type(instance).__name__.lower() else PrinterType.PRUSA_CORE,
            ip_address=instance.ip_address,
            api_key=getattr(instance, 'api_key', None),
            access_code=getattr(instance, 'access_code', None),
            serial_number=getattr(instance, 'serial_number', None),
            is_active=True,
            status=current_status,
            last_seen=last_seen
        )

    async def get_printer_driver(self, printer_id: str) -> Optional[BasePrinter]:
        """
        Get printer driver instance for direct access.

        Args:
            printer_id: Printer identifier

        Returns:
            BasePrinter instance or None

        Example:
            >>> driver = await printer_service.get_printer_driver("bambu_001")
            >>> if driver and driver.is_connected:
            ...     status = await driver.get_status()
        """
        return self.connection.get_printer_instance(printer_id)

    async def get_printer_status(self, printer_id: str) -> Dict[str, Any]:
        """
        Get current status of a printer.

        Args:
            printer_id: Printer identifier

        Returns:
            Dict with status information

        Raises:
            NotFoundError: If printer not found

        Example:
            >>> status = await printer_service.get_printer_status("bambu_001")
            >>> print(f"Status: {status['status']}, Progress: {status['progress']}%")
        """
        instance = self.connection.get_printer_instance(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)

        try:
            status = await instance.get_status()
            # Update last_seen when we successfully get status
            await self.database.update_printer_status(
                printer_id,
                status.status.value.lower(),
                datetime.now()
            )
            return {
                "printer_id": status.printer_id,
                "status": status.status.value,
                "message": status.message,
                "temperature_bed": status.temperature_bed,
                "temperature_nozzle": status.temperature_nozzle,
                "progress": status.progress,
                "current_job": status.current_job,
                "timestamp": status.timestamp.isoformat()
            }
        except Exception as e:
            logger.error("Failed to get printer status",
                        printer_id=printer_id,
                        error=str(e))
            return {
                "printer_id": printer_id,
                "status": "error",
                "message": f"Status check failed: {str(e)}"
            }

    # ========================================================================
    # DELEGATION TO PrinterConnectionService
    # ========================================================================

    async def connect_printer(self, printer_id: str) -> bool:
        """Connect to a specific printer. Delegates to PrinterConnectionService."""
        return await self.connection.connect_printer(printer_id)

    async def disconnect_printer(self, printer_id: str) -> bool:
        """Disconnect from a specific printer. Delegates to PrinterConnectionService."""
        return await self.connection.disconnect_printer(printer_id)

    async def test_connection(
        self,
        printer_type: str,
        connection_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test printer connection without creating a persistent configuration.

        This is useful for validating connection parameters in setup wizards
        before actually creating a printer.

        Args:
            printer_type: Type of printer ('bambu_lab' or 'prusa_core')
            connection_config: Connection configuration dict containing
                - For Bambu Lab: ip_address, access_code, serial_number (optional)
                - For Prusa: ip_address, api_key

        Returns:
            Dict with 'success' bool, 'message' string, and optional 'details'
        """
        from src.printers.bambu_lab import BambuLabPrinter
        from src.printers.prusa import PrusaPrinter

        temp_printer = None
        try:
            # Normalize printer type
            ptype = printer_type.value if hasattr(printer_type, 'value') else str(printer_type)
            ptype = ptype.lower()

            # Create temporary printer instance
            if ptype == "bambu_lab":
                temp_printer = BambuLabPrinter(
                    printer_id="test_connection_temp",
                    name="Test Connection",
                    ip_address=connection_config.get("ip_address"),
                    access_code=connection_config.get("access_code"),
                    serial_number=connection_config.get("serial_number"),
                    file_service=None
                )
            elif ptype in ("prusa_core", "prusa"):
                temp_printer = PrusaPrinter(
                    printer_id="test_connection_temp",
                    name="Test Connection",
                    ip_address=connection_config.get("ip_address"),
                    api_key=connection_config.get("api_key"),
                    file_service=None
                )
            else:
                return {
                    "success": False,
                    "message": f"Unknown printer type: {printer_type}"
                }

            # Test connection
            success = await temp_printer.connect()

            if success:
                # Get some basic info if available
                details = {}
                if hasattr(temp_printer, 'get_status'):
                    try:
                        status = await temp_printer.get_status()
                        if status:
                            details["printer_model"] = status.get("model", "Unknown")
                    except Exception:
                        pass

                return {
                    "success": True,
                    "message": "Connection successful",
                    "details": details
                }
            else:
                return {
                    "success": False,
                    "message": "Connection failed - could not establish connection"
                }

        except Exception as e:
            logger.error("Test connection error", error=str(e), printer_type=printer_type)
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
        finally:
            # Clean up temporary connection
            if temp_printer:
                try:
                    await temp_printer.disconnect()
                except Exception:
                    pass

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all printer connections. Delegates to PrinterConnectionService."""
        health = await self.connection.health_check()
        # Add monitoring status
        health["monitoring_active"] = self.monitoring.monitoring_active
        return health

    # Backward compatibility: expose printer_instances
    @property
    def printer_instances(self) -> Dict[str, BasePrinter]:
        """Access printer instances from connection service (backward compatibility)."""
        return self.connection.printer_instances

    # ========================================================================
    # DELEGATION TO PrinterMonitoringService
    # ========================================================================

    async def start_monitoring(self, printer_id: Optional[str] = None) -> bool:
        """
        Start printer monitoring for all or specific printer.

        Args:
            printer_id: Optional printer ID to monitor, or None for all

        Returns:
            True if monitoring started successfully

        Example:
            >>> # Monitor all printers
            >>> await printer_service.start_monitoring()
            >>> # Monitor specific printer
            >>> await printer_service.start_monitoring("bambu_001")
        """
        if printer_id:
            # Start monitoring for specific printer
            instance = self.connection.get_printer_instance(printer_id)
            if not instance:
                raise NotFoundError("Printer", printer_id)

            try:
                if not instance.is_connected:
                    connected = await instance.connect()
                    if connected:
                        await self.database.update_printer_status(
                            printer_id,
                            "online",
                            datetime.now()
                        )
                return await self.monitoring.start_monitoring(printer_id, instance)
            except Exception as e:
                logger.error("Failed to start monitoring",
                            printer_id=printer_id,
                            error=str(e))
                return False
        else:
            # Start monitoring for all printers in parallel (non-blocking)
            import asyncio
            tasks = []

            for printer_id, instance in self.connection.printer_instances.items():
                # Create background task for each printer connection
                task = asyncio.create_task(
                    self.connection.connect_and_monitor_printer(
                        printer_id,
                        instance,
                        lambda pid, inst: self.monitoring.start_monitoring(pid, inst)
                    )
                )
                tasks.append(task)

            # Don't wait for connections to complete - they run in background
            logger.info("Started printer monitoring in background",
                       printer_count=len(self.connection.printer_instances))

            # Mark as active if we have any printers configured
            self.monitoring.monitoring_active = len(self.connection.printer_instances) > 0
            return True

    async def stop_monitoring(self, printer_id: Optional[str] = None) -> bool:
        """
        Stop printer monitoring for all or specific printer.

        Args:
            printer_id: Optional printer ID to stop monitoring, or None for all

        Returns:
            True if monitoring stopped successfully

        Example:
            >>> await printer_service.stop_monitoring()
        """
        if printer_id:
            # Stop monitoring for specific printer
            instance = self.connection.get_printer_instance(printer_id)
            if not instance:
                raise NotFoundError("Printer", printer_id)

            return await self.monitoring.stop_monitoring(printer_id, instance)
        else:
            # Stop monitoring for all printers
            for printer_id, instance in self.connection.printer_instances.items():
                try:
                    await self.monitoring.stop_monitoring(printer_id, instance)
                except Exception as e:
                    logger.error("Failed to stop monitoring",
                                printer_id=printer_id,
                                error=str(e))

            self.monitoring.monitoring_active = False
            logger.info("Stopped all printer monitoring")
            return True

    async def download_current_job_file(self, printer_id: str) -> Dict[str, Any]:
        """
        Download currently printing job file. Delegates to PrinterMonitoringService.
        """
        instance = self.connection.get_printer_instance(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)

        return await self.monitoring.download_current_job_file(printer_id, instance)

    # Backward compatibility: expose monitoring_active
    @property
    def monitoring_active(self) -> bool:
        """Access monitoring active state (backward compatibility)."""
        return self.monitoring.monitoring_active

    # ========================================================================
    # DELEGATION TO PrinterControlService
    # ========================================================================

    async def pause_printer(self, printer_id: str) -> bool:
        """Pause printing on a specific printer. Delegates to PrinterControlService."""
        return await self.control.pause_printer(printer_id)

    async def resume_printer(self, printer_id: str) -> bool:
        """Resume printing on a specific printer. Delegates to PrinterControlService."""
        return await self.control.resume_printer(printer_id)

    async def stop_printer(self, printer_id: str) -> bool:
        """Stop/cancel printing on a specific printer. Delegates to PrinterControlService."""
        return await self.control.stop_printer(printer_id)

    async def start_printer_monitoring(self, printer_id: str) -> bool:
        """Start monitoring for a specific printer. Delegates to PrinterControlService."""
        return await self.control.start_printer_monitoring(printer_id)

    async def stop_printer_monitoring(self, printer_id: str) -> bool:
        """Stop monitoring for a specific printer. Delegates to PrinterControlService."""
        return await self.control.stop_printer_monitoring(printer_id)

    # ========================================================================
    # FILE OPERATIONS (delegated to printer instances)
    # ========================================================================

    async def get_printer_files(self, printer_id: str) -> List[Dict[str, Any]]:
        """
        Get list of files available on printer.

        Args:
            printer_id: Printer identifier

        Returns:
            List of file dictionaries

        Raises:
            NotFoundError: If printer not found
            PrinterConnectionError: If file listing fails

        Example:
            >>> files = await printer_service.get_printer_files("bambu_001")
            >>> for file in files:
            ...     print(f"{file['filename']}: {file['size']} bytes")
        """
        instance = self.connection.get_printer_instance(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)

        if not instance.is_connected:
            await instance.connect()

        try:
            files = await instance.list_files()
            return [
                {
                    "filename": f.filename,
                    "size": f.size,
                    "modified": f.modified.isoformat() if f.modified else None,
                    "path": f.path
                }
                for f in files
            ]
        except Exception as e:
            logger.error("Failed to get printer files",
                        printer_id=printer_id,
                        error=str(e))
            raise PrinterConnectionError(printer_id, f"File listing failed: {str(e)}")

    async def download_printer_file(
        self,
        printer_id: str,
        filename: str,
        local_path: str = None
    ) -> bool:
        """
        Download a file from printer.

        Args:
            printer_id: Printer identifier
            filename: Name of file to download
            local_path: Optional local destination path

        Returns:
            True if download successful

        Raises:
            NotFoundError: If printer not found

        Example:
            >>> success = await printer_service.download_printer_file(
            ...     "bambu_001",
            ...     "model.3mf"
            ... )
        """
        instance = self.connection.get_printer_instance(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)

        if not instance.is_connected:
            await instance.connect()

        # If no local path provided, use file service to manage the download
        if local_path is None and self.file_service:
            try:
                result = await self.file_service.download_file(printer_id, filename)
                return result.get('status') == 'success'
            except Exception as e:
                logger.error("Failed to download file via file service",
                            printer_id=printer_id,
                            filename=filename,
                            error=str(e))
                return False

        try:
            return await instance.download_file(filename, local_path)
        except Exception as e:
            logger.error("Failed to download file",
                        printer_id=printer_id,
                        filename=filename,
                        error=str(e))
            return False

    # ========================================================================
    # PRINTER CRUD OPERATIONS
    # ========================================================================

    async def create_printer(
        self,
        name: str,
        printer_type: PrinterType,
        connection_config: Dict[str, Any],
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> Printer:
        """
        Create a new printer configuration.

        Args:
            name: Printer name
            printer_type: Type of printer (BAMBU_LAB or PRUSA_CORE)
            connection_config: Connection configuration dict
            location: Optional location description
            description: Optional description

        Returns:
            Created Printer object

        Raises:
            ValueError: If printer creation fails

        Example:
            >>> printer = await printer_service.create_printer(
            ...     name="My Bambu A1",
            ...     printer_type=PrinterType.BAMBU_LAB,
            ...     connection_config={
            ...         "ip_address": "192.168.1.100",
            ...         "access_code": "12345678",
            ...         "serial_number": "ABC123"
            ...     }
            ... )
        """
        printer_id = str(uuid4())

        # Map printer type to string
        type_str = "bambu_lab" if printer_type == PrinterType.BAMBU_LAB else "prusa_core"

        # Create configuration dict
        config_dict = {
            "name": name,
            "type": type_str,
            "location": location,
            "description": description,
            **connection_config
        }

        # Add to configuration service
        if not self.config_service.add_printer(printer_id, config_dict):
            raise ValueError("Failed to add printer configuration")

        # Create and add instance
        config = self.config_service.get_printer(printer_id)
        if config:
            instance = self.connection._create_printer_instance(printer_id, config)
            if instance:
                self.connection.printer_instances[printer_id] = instance

                # Setup monitoring callback
                self.monitoring.setup_status_callback(instance)

                # Add to database
                await self.database.create_printer({
                    "id": printer_id,
                    "name": name,
                    "type": type_str,
                    "ip_address": connection_config.get("ip_address"),
                    "api_key": connection_config.get("api_key"),
                    "access_code": connection_config.get("access_code"),
                    "serial_number": connection_config.get("serial_number"),
                    "webcam_url": connection_config.get("webcam_url"),
                    "location": location,
                    "description": description,
                    "is_active": True
                })

        return Printer(
            id=printer_id,
            name=name,
            type=printer_type,
            ip_address=connection_config.get("ip_address"),
            api_key=connection_config.get("api_key"),
            access_code=connection_config.get("access_code"),
            serial_number=connection_config.get("serial_number"),
            webcam_url=connection_config.get("webcam_url"),
            location=location,
            description=description,
            is_active=True,
            status=PrinterStatus.UNKNOWN
        )

    async def update_printer(self, printer_id: str, **updates) -> Optional[Printer]:
        """
        Update printer configuration.

        Args:
            printer_id: Printer identifier
            **updates: Fields to update

        Returns:
            Updated Printer object or None

        Example:
            >>> printer = await printer_service.update_printer(
            ...     "bambu_001",
            ...     name="Updated Name",
            ...     connection_config={"ip_address": "192.168.1.101"}
            ... )
        """
        printer_id_str = printer_id

        # Get current configuration
        config = self.config_service.get_printer(printer_id_str)
        if not config:
            return None

        # Update configuration
        config_dict = config.to_dict()

        # Map API fields to config fields
        if "name" in updates:
            config_dict["name"] = updates["name"]
        if "location" in updates:
            config_dict["location"] = updates["location"]
        if "description" in updates:
            config_dict["description"] = updates["description"]
        if "connection_config" in updates:
            config_dict.update(updates["connection_config"])
        if "is_enabled" in updates:
            config_dict["is_active"] = updates["is_enabled"]

        # Save updated configuration
        if not self.config_service.add_printer(printer_id_str, config_dict):
            return None

        # Update database with the changed fields
        db_updates = {}
        if "name" in updates:
            db_updates["name"] = updates["name"]
        if "location" in updates:
            db_updates["location"] = updates["location"]
        if "description" in updates:
            db_updates["description"] = updates["description"]
        if "connection_config" in updates:
            conn_config = updates["connection_config"]
            if "ip_address" in conn_config:
                db_updates["ip_address"] = conn_config["ip_address"]
            if "api_key" in conn_config:
                db_updates["api_key"] = conn_config["api_key"]
            if "access_code" in conn_config:
                db_updates["access_code"] = conn_config["access_code"]
            if "serial_number" in conn_config:
                db_updates["serial_number"] = conn_config["serial_number"]
            if "webcam_url" in conn_config:
                db_updates["webcam_url"] = conn_config["webcam_url"]
        if "is_enabled" in updates:
            db_updates["is_active"] = updates["is_enabled"]

        if db_updates:
            await self.database.update_printer(printer_id_str, db_updates)

        # Recreate printer instance if it exists
        if printer_id_str in self.connection.printer_instances:
            old_instance = self.connection.printer_instances[printer_id_str]
            if old_instance.is_connected:
                await old_instance.disconnect()

            new_config = self.config_service.get_printer(printer_id_str)
            if new_config:
                new_instance = self.connection._create_printer_instance(printer_id_str, new_config)
                if new_instance:
                    self.connection.printer_instances[printer_id_str] = new_instance
                    self.monitoring.setup_status_callback(new_instance)

        # Return updated printer
        updated_config = self.config_service.get_printer(printer_id_str)
        if updated_config:
            return Printer(
                id=printer_id_str,
                name=updated_config.name,
                type=PrinterType.BAMBU_LAB if updated_config.type == "bambu_lab" else PrinterType.PRUSA_CORE,
                ip_address=updated_config.ip_address,
                api_key=updated_config.api_key,
                access_code=updated_config.access_code,
                serial_number=updated_config.serial_number,
                webcam_url=updated_config.webcam_url,
                location=updated_config.location,
                description=updated_config.description,
                is_active=updated_config.is_active,
                status=PrinterStatus.UNKNOWN
            )
        return None

    async def delete_printer(self, printer_id: str, force: bool = False) -> bool:
        """
        Delete a printer configuration.

        Args:
            printer_id: Printer identifier
            force: If True, skip active job validation

        Returns:
            True if deletion successful

        Raises:
            ValueError: If printer has active jobs and force=False

        Example:
            >>> success = await printer_service.delete_printer("bambu_001")
        """
        printer_id_str = printer_id

        # Check for active jobs (unless force=True)
        if not force:
            # Check database for active jobs on this printer
            active_statuses = ['running', 'pending', 'paused']
            async with self.database.connection() as conn:
                cursor = await conn.execute(
                    "SELECT COUNT(*) FROM jobs WHERE printer_id = ? AND status IN (?, ?, ?)",
                    (printer_id_str, *active_statuses)
                )
                row = await cursor.fetchone()
                active_job_count = row[0] if row else 0

                if active_job_count > 0:
                    raise ValueError(
                        f"Cannot delete printer with {active_job_count} active job(s). "
                        "Complete or cancel active jobs first, or use force=true to override."
                    )

        # Disconnect if connected
        if printer_id_str in self.connection.printer_instances:
            instance = self.connection.printer_instances[printer_id_str]
            if instance.is_connected:
                await instance.disconnect()
            del self.connection.printer_instances[printer_id_str]

        # Remove from configuration
        return self.config_service.remove_printer(printer_id_str)

    # ========================================================================
    # GRACEFUL SHUTDOWN
    # ========================================================================

    async def shutdown(self) -> None:
        """
        Gracefully shutdown printer service.

        Stops monitoring, disconnects all printers, and cleans up resources.

        Example:
            >>> await printer_service.shutdown()
        """
        logger.info("Shutting down printer service")

        # Stop monitoring
        await self.stop_monitoring()

        # Shutdown monitoring service (cleans up background tasks)
        await self.monitoring.shutdown()

        # Shutdown connection service (disconnects all printers)
        await self.connection.shutdown()

        logger.info("Printer service shutdown complete")
