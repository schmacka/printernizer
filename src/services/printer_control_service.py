"""
Printer control service for managing print operations.

This service is responsible for controlling print jobs on printers including
pause, resume, stop/cancel operations, and monitoring control.

Part of PrinterService refactoring - Phase 2 technical debt reduction.
"""
from datetime import datetime
import structlog

from src.services.event_service import EventService
from src.printers import BasePrinter
from src.utils.errors import PrinterConnectionError, NotFoundError

logger = structlog.get_logger()


class PrinterControlService:
    """
    Service for controlling printer operations.

    This service handles:
    - Pausing print jobs
    - Resuming print jobs
    - Stopping/canceling print jobs
    - Per-printer monitoring control (start/stop)

    Events Emitted:
    - print_paused: When print is paused
    - print_resumed: When print is resumed
    - print_stopped: When print is stopped/cancelled

    Example:
        >>> control_svc = PrinterControlService(event_service, connection_service)
        >>> success = await control_svc.pause_printer("bambu_001")
    """

    def __init__(
        self,
        event_service: EventService,
        connection_service=None
    ):
        """
        Initialize printer control service.

        Args:
            event_service: Event service for emitting control events
            connection_service: Optional connection service to get printer instances
        """
        self.event_service = event_service
        self.connection_service = connection_service

        logger.info("PrinterControlService initialized")

    async def pause_printer(self, printer_id: str) -> bool:
        """
        Pause printing on a specific printer.

        Args:
            printer_id: Printer identifier

        Returns:
            True if pause was successful, False otherwise

        Raises:
            NotFoundError: If printer not found
            PrinterConnectionError: If pause command fails

        Example:
            >>> success = await control_svc.pause_printer("bambu_001")
            >>> if success:
            ...     print("Print paused successfully")
        """
        instance = self._get_printer_instance(printer_id)

        try:
            if not instance.is_connected:
                await instance.connect()

            result = await instance.pause_print()

            if result:
                # Emit pause event
                await self.event_service.emit_event("print_paused", {
                    "printer_id": printer_id,
                    "timestamp": datetime.now().isoformat()
                })

                logger.info("Print paused successfully", printer_id=printer_id)

            return result
        except Exception as e:
            logger.error("Failed to pause printer",
                        printer_id=printer_id,
                        error=str(e))
            raise PrinterConnectionError(printer_id, str(e))

    async def resume_printer(self, printer_id: str) -> bool:
        """
        Resume printing on a specific printer.

        Args:
            printer_id: Printer identifier

        Returns:
            True if resume was successful, False otherwise

        Raises:
            NotFoundError: If printer not found
            PrinterConnectionError: If resume command fails

        Example:
            >>> success = await control_svc.resume_printer("bambu_001")
            >>> if success:
            ...     print("Print resumed successfully")
        """
        instance = self._get_printer_instance(printer_id)

        try:
            if not instance.is_connected:
                await instance.connect()

            result = await instance.resume_print()

            if result:
                # Emit resume event
                await self.event_service.emit_event("print_resumed", {
                    "printer_id": printer_id,
                    "timestamp": datetime.now().isoformat()
                })

                logger.info("Print resumed successfully", printer_id=printer_id)

            return result
        except Exception as e:
            logger.error("Failed to resume printer",
                        printer_id=printer_id,
                        error=str(e))
            raise PrinterConnectionError(printer_id, str(e))

    async def stop_printer(self, printer_id: str) -> bool:
        """
        Stop/cancel printing on a specific printer.

        Args:
            printer_id: Printer identifier

        Returns:
            True if stop was successful, False otherwise

        Raises:
            NotFoundError: If printer not found
            PrinterConnectionError: If stop command fails

        Example:
            >>> success = await control_svc.stop_printer("bambu_001")
            >>> if success:
            ...     print("Print stopped successfully")
        """
        instance = self._get_printer_instance(printer_id)

        try:
            if not instance.is_connected:
                await instance.connect()

            result = await instance.stop_print()

            if result:
                # Emit stop event
                await self.event_service.emit_event("print_stopped", {
                    "printer_id": printer_id,
                    "timestamp": datetime.now().isoformat()
                })

                logger.info("Print stopped successfully", printer_id=printer_id)

            return result
        except Exception as e:
            logger.error("Failed to stop printer",
                        printer_id=printer_id,
                        error=str(e))
            raise PrinterConnectionError(printer_id, str(e))

    async def start_printer_monitoring(self, printer_id: str) -> bool:
        """
        Start monitoring for a specific printer.

        Note: This is a simplified wrapper. Actual monitoring is handled by
        PrinterMonitoringService. This method ensures the printer is connected
        and ready for monitoring.

        Args:
            printer_id: Printer identifier

        Returns:
            True if monitoring control succeeds

        Raises:
            NotFoundError: If printer not found

        Example:
            >>> success = await control_svc.start_printer_monitoring("bambu_001")
        """
        instance = self._get_printer_instance(printer_id)

        try:
            if not instance.is_connected:
                await instance.connect()

            # For now, we'll treat this as ensuring the printer is connected and active
            # The monitoring is handled globally by the monitoring service
            logger.info("Started monitoring control for printer", printer_id=printer_id)
            return True
        except Exception as e:
            logger.error("Failed to start monitoring control",
                        printer_id=printer_id,
                        error=str(e))
            return False

    async def stop_printer_monitoring(self, printer_id: str) -> bool:
        """
        Stop monitoring for a specific printer.

        Note: This is a simplified wrapper. Actual monitoring is handled by
        PrinterMonitoringService. This method is provided for API compatibility.

        Args:
            printer_id: Printer identifier

        Returns:
            True if monitoring control succeeds

        Raises:
            NotFoundError: If printer not found

        Example:
            >>> success = await control_svc.stop_printer_monitoring("bambu_001")
        """
        instance = self._get_printer_instance(printer_id)

        try:
            # For now, this is a no-op since monitoring is global
            # In the future, this could be used for per-printer monitoring control
            logger.info("Stopped monitoring control for printer", printer_id=printer_id)
            return True
        except Exception as e:
            logger.error("Failed to stop monitoring control",
                        printer_id=printer_id,
                        error=str(e))
            return False

    def _get_printer_instance(self, printer_id: str) -> BasePrinter:
        """
        Get printer instance from connection service.

        Args:
            printer_id: Printer identifier

        Returns:
            BasePrinter instance

        Raises:
            NotFoundError: If printer not found or connection service not set

        Example:
            >>> instance = control_svc._get_printer_instance("bambu_001")
        """
        if not self.connection_service:
            raise NotFoundError("Printer", printer_id)

        instance = self.connection_service.get_printer_instance(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)

        return instance

    def set_connection_service(self, connection_service) -> None:
        """
        Set connection service dependency.

        This allows for late binding to resolve circular dependencies.

        Args:
            connection_service: PrinterConnectionService instance
        """
        self.connection_service = connection_service
        logger.debug("Connection service set in PrinterControlService")
