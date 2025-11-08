"""
Printer monitoring service for tracking printer status and managing auto-downloads.

This service is responsible for monitoring printer status updates, handling
auto-download logic for current print jobs, and managing background tasks.

Part of PrinterService refactoring - Phase 2 technical debt reduction.
"""
import asyncio
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import structlog

from src.database.database import Database
from src.services.event_service import EventService
from src.models.printer import PrinterStatus, PrinterStatusUpdate
from src.printers import BasePrinter
from src.utils.exceptions import NotFoundError

logger = structlog.get_logger()


class PrinterMonitoringService:
    """
    Service for monitoring printer status and managing auto-downloads.

    This service handles:
    - Status update processing from printers
    - Auto-download of current print jobs
    - Background task management and cleanup
    - Monitoring lifecycle (start/stop)
    - Status persistence to database

    Events Emitted:
    - printer_status_update: When printer status changes
    - printer_monitoring_started: When monitoring begins
    - printer_monitoring_stopped: When monitoring ends

    Example:
        >>> monitoring_svc = PrinterMonitoringService(database, event_service)
        >>> await monitoring_svc.start_monitoring("bambu_001", instance)
    """

    def __init__(
        self,
        database: Database,
        event_service: EventService,
        file_service=None,
        connection_service=None
    ):
        """
        Initialize printer monitoring service.

        Args:
            database: Database instance for storing status updates
            event_service: Event service for emitting status events
            file_service: Optional file service for auto-downloads
            connection_service: Optional connection service to get printer instances
        """
        self.database = database
        self.event_service = event_service
        self.file_service = file_service
        self.connection_service = connection_service

        # Monitoring state
        self.monitoring_active = False

        # Track job filenames we've already attempted to auto-download to avoid loops
        self._auto_download_attempts: Dict[str, Set[str]] = {}

        # Background task tracking for graceful shutdown
        self._background_tasks: set = set()

        logger.info("PrinterMonitoringService initialized")

    def setup_status_callback(self, printer_instance: BasePrinter):
        """
        Set up status callback for a printer instance.

        This should be called after printer instance is created to ensure
        status updates are routed to this monitoring service.

        Args:
            printer_instance: Printer instance to attach callback to

        Example:
            >>> monitoring_svc.setup_status_callback(printer_instance)
        """
        printer_instance.add_status_callback(
            lambda status: asyncio.create_task(
                self._handle_status_update(status)
            )
        )
        logger.debug("Status callback setup for printer",
                    printer_id=getattr(printer_instance, 'printer_id', 'unknown'))

    async def _handle_status_update(self, status: PrinterStatusUpdate):
        """
        Handle status updates from printers.

        Processes incoming status updates by:
        1. Storing in database
        2. Emitting events for real-time updates
        3. Triggering auto-download if applicable

        Args:
            status: PrinterStatusUpdate object with current status

        Example:
            >>> # Called automatically via status callback
            >>> await monitoring_svc._handle_status_update(status)
        """
        # Store status in database
        await self._store_status_update(status)

        # Emit event for real-time updates
        await self.event_service.emit_event("printer_status_update", {
            "printer_id": status.printer_id,
            "status": status.status.value,
            "message": status.message,
            "temperature_bed": status.temperature_bed,
            "temperature_nozzle": status.temperature_nozzle,
            "progress": status.progress,
            "current_job": status.current_job,
            "current_job_file_id": status.current_job_file_id,
            "current_job_has_thumbnail": status.current_job_has_thumbnail,
            "current_job_thumbnail_url": status.current_job_thumbnail_url,
            "timestamp": status.timestamp.isoformat()
        })

        # Auto-download & process current job file if needed
        await self._check_auto_download(status)

    async def _check_auto_download(self, status: PrinterStatusUpdate):
        """
        Check if auto-download should be triggered for current job.

        Auto-downloads when:
        - Printer is printing
        - Has a current job
        - No file_id or no thumbnail yet
        - File not already attempted

        Args:
            status: Current printer status
        """
        try:
            if (self.file_service and
                status.status == PrinterStatus.PRINTING and
                status.current_job and
                # Only if we don't already have a file id or we have no thumbnail
                (not status.current_job_file_id or status.current_job_has_thumbnail is False)):

                filename = status.current_job
                printer_id = status.printer_id

                # Initialize attempts tracking for this printer
                if printer_id not in self._auto_download_attempts:
                    self._auto_download_attempts[printer_id] = set()

                # Normalize filename (strip any leading cache/ from Bambu)
                if filename.startswith('cache/'):
                    filename_to_download = filename.split('/', 1)[1]
                else:
                    filename_to_download = filename

                # Only proceed if looks like a printable file and not attempted already
                if (self._is_print_file(filename_to_download) and
                    filename_to_download not in self._auto_download_attempts[printer_id]):
                    self._auto_download_attempts[printer_id].add(filename_to_download)
                    # Track the task for proper cleanup on shutdown
                    self._create_background_task(
                        self._attempt_download_current_job(printer_id, filename_to_download)
                    )
        except Exception as e:
            logger.debug("Auto-download check failed", error=str(e))

    def _is_print_file(self, filename: str) -> bool:
        """
        Heuristic: check if filename has a known printable extension.

        Args:
            filename: Name of the file

        Returns:
            True if file has printable extension

        Example:
            >>> monitoring_svc._is_print_file("model.3mf")
            True
            >>> monitoring_svc._is_print_file("readme.txt")
            False
        """
        printable_exts = {'.gcode', '.bgcode', '.3mf'}
        lower = filename.lower()
        import os as _os
        return _os.path.splitext(lower)[1] in printable_exts

    async def _attempt_download_current_job(self, printer_id: str, filename: str):
        """
        Attempt to download the currently printing file for thumbnail processing.

        Tries multiple filename variants to handle:
        - Case differences
        - Special character handling
        - Name truncation by printer
        - Space/underscore variations

        Args:
            printer_id: Printer identifier
            filename: Filename to download

        Example:
            >>> await monitoring_svc._attempt_download_current_job("bambu_001", "model.3mf")
        """
        try:
            logger.info("Auto-downloading active print file for thumbnail processing",
                        printer_id=printer_id, filename=filename)

            async def _attempt(name: str) -> Optional[Dict[str, Any]]:
                try:
                    return await self.file_service.download_file(printer_id, name)
                except Exception as e:
                    logger.debug("Variant download attempt raised exception",
                                printer_id=printer_id,
                                variant=name,
                                error=str(e))
                    return {"status": "error", "message": str(e)}

            # First attempt: exact reported filename
            attempts: List[tuple[str, Dict[str, Any]]] = []
            primary = await _attempt(filename)
            attempts.append((filename, primary))

            if primary and primary.get("status") == "success":
                logger.info("Auto-download completed", printer_id=printer_id, filename=filename)
                return

            # Collect printer file list to find a near match (case-insensitive, stripped)
            printer_files = []
            if self.connection_service:
                try:
                    instance = self.connection_service.get_printer_instance(printer_id)
                    if instance and instance.is_connected:
                        file_list = await instance.list_files()
                        printer_files = [{"filename": f.filename} for f in file_list]
                except Exception as e:
                    logger.debug("Could not list printer files for variant matching",
                                printer_id=printer_id,
                                error=str(e))

            reported_lower = filename.lower().strip()
            # Generate candidate variants
            variants = set()

            # 1. Exact names from printer that case-insensitively match
            for f in printer_files:
                fname = f.get("filename") or ""
                if fname.lower() == reported_lower and fname != filename:
                    variants.add(fname)

            # 2. Replace problematic characters (commas, parentheses) with underscores / remove
            simple = filename.replace('(', '').replace(')', '').replace(',', '').replace('  ', ' ').strip()
            if simple != filename:
                variants.add(simple)
            underscore_variant = simple.replace(' ', '_')
            if underscore_variant != simple:
                variants.add(underscore_variant)

            # 3. Collapse multiple spaces
            import re as _re
            collapsed = _re.sub(r'\s+', ' ', filename).strip()
            if collapsed != filename:
                variants.add(collapsed)

            # 4. Some slicers truncate long names on printer storage - try prefix matches
            for f in printer_files:
                fname = f.get("filename") or ""
                if fname.lower().startswith(reported_lower[:20]) and abs(len(fname) - len(filename)) > 5:
                    variants.add(fname)

            # Try each variant until success
            for variant in variants:
                if variant in self._auto_download_attempts.get(printer_id, set()):
                    continue  # already tried
                self._auto_download_attempts[printer_id].add(variant)
                res = await _attempt(variant)
                attempts.append((variant, res))
                if res and res.get("status") == "success":
                    logger.info("Auto-download completed via variant",
                               printer_id=printer_id,
                               original=filename,
                               variant=variant)
                    return

            # If we reach here all attempts failed
            last_msg = attempts[-1][1].get("message") if attempts else "unknown"
            logger.warning("Auto-download failed",
                          printer_id=printer_id,
                          filename=filename,
                          attempts=[{
                              "variant": v,
                              "status": r.get("status"),
                              "message": r.get("message")
                          } for v, r in attempts],
                          message=last_msg)
        except Exception as e:
            logger.warning("Auto-download exception",
                          printer_id=printer_id,
                          filename=filename,
                          error=str(e))

    async def _store_status_update(self, status: PrinterStatusUpdate):
        """
        Store status update in database for history.

        Args:
            status: Status update to store

        Example:
            >>> await monitoring_svc._store_status_update(status)
        """
        # Log the status update
        logger.info("Printer status update",
                   printer_id=status.printer_id,
                   status=status.status.value,
                   progress=status.progress)

        # Update database with current status (could be expanded to track history)
        try:
            await self.database.update_printer_status(
                status.printer_id,
                status.status.value.lower(),
                status.timestamp
            )
        except Exception as e:
            logger.error("Failed to store status update",
                        printer_id=status.printer_id,
                        error=str(e))

    async def start_monitoring(
        self,
        printer_id: str,
        printer_instance: BasePrinter
    ) -> bool:
        """
        Start monitoring for a specific printer.

        Args:
            printer_id: Printer identifier
            printer_instance: Printer instance to monitor

        Returns:
            True if monitoring started successfully

        Raises:
            Exception: If monitoring fails to start

        Example:
            >>> instance = conn_svc.get_printer_instance("bambu_001")
            >>> success = await monitoring_svc.start_monitoring("bambu_001", instance)
        """
        try:
            await printer_instance.start_monitoring()
            logger.info("Started monitoring for printer", printer_id=printer_id)

            # Emit monitoring started event
            await self.event_service.emit_event("printer_monitoring_started", {
                "printer_id": printer_id,
                "timestamp": datetime.now().isoformat()
            })

            return True
        except Exception as e:
            logger.error("Failed to start monitoring",
                        printer_id=printer_id,
                        error=str(e))
            return False

    async def stop_monitoring(
        self,
        printer_id: str,
        printer_instance: BasePrinter
    ) -> bool:
        """
        Stop monitoring for a specific printer.

        Args:
            printer_id: Printer identifier
            printer_instance: Printer instance to stop monitoring

        Returns:
            True if monitoring stopped successfully

        Example:
            >>> instance = conn_svc.get_printer_instance("bambu_001")
            >>> success = await monitoring_svc.stop_monitoring("bambu_001", instance)
        """
        try:
            await printer_instance.stop_monitoring()
            logger.info("Stopped monitoring for printer", printer_id=printer_id)

            # Emit monitoring stopped event
            await self.event_service.emit_event("printer_monitoring_stopped", {
                "printer_id": printer_id,
                "timestamp": datetime.now().isoformat()
            })

            return True
        except Exception as e:
            logger.error("Failed to stop monitoring",
                        printer_id=printer_id,
                        error=str(e))
            return False

    async def download_current_job_file(self, printer_id: str, printer_instance: BasePrinter) -> Dict[str, Any]:
        """
        Download (and process) the currently printing job file to generate a thumbnail.

        Logic:
          1. Get current status
          2. If no active job -> return informative response
          3. If file already known & has thumbnail -> return existing
          4. If file known but no thumbnail & local path present -> process thumbnails directly
          5. Else attempt download from printer (FileService handles async thumbnail processing)

        Args:
            printer_id: Printer identifier
            printer_instance: Printer instance

        Returns:
            Dict with status, file_id, and message

        Example:
            >>> result = await monitoring_svc.download_current_job_file("bambu_001", instance)
            >>> print(result['status'])
        """
        if not self.file_service:
            return {"status": "error", "message": "File service unavailable"}

        # Ensure connection
        if not printer_instance.is_connected:
            try:
                await printer_instance.connect()
            except Exception as e:
                return {"status": "error", "message": f"Connect failed: {e}"}

        try:
            status = await printer_instance.get_status()
        except Exception as e:
            return {"status": "error", "message": f"Status failed: {e}"}

        if not status.current_job:
            return {"status": "no_active_job", "message": "No active print job"}

        filename = status.current_job
        if filename.startswith('cache/'):
            filename = filename.split('/', 1)[1]

        # Check existing record
        existing = None
        try:
            existing = await self.file_service.find_file_by_name(filename, printer_id)
        except Exception as e:
            logger.debug("Could not find existing file record",
                        filename=filename,
                        printer_id=printer_id,
                        error=str(e))

        if existing and existing.get('has_thumbnail'):
            return {
                "status": "exists_with_thumbnail",
                "file_id": existing.get('id'),
                "message": "File already processed with thumbnail"
            }

        # If existing without thumbnail but local_path available -> process immediately
        if existing and not existing.get('has_thumbnail') and existing.get('file_path'):
            processed = await self.file_service.process_file_thumbnails(
                existing.get('file_path'),
                existing.get('id')
            )
            return {
                "status": "processed" if processed else "process_failed",
                "file_id": existing.get('id'),
                "message": "Processed existing local file" if processed else "Processing failed"
            }

        # Attempt download
        try:
            dl_result = await self.file_service.download_file(printer_id, filename)
            return {
                "status": dl_result.get('status'),
                "file_id": dl_result.get('file_id'),
                "message": dl_result.get('message'),
                "note": "Thumbnail processing runs asynchronously after download"
            }
        except Exception as e:
            return {"status": "error", "message": f"Download failed: {e}"}

    def _create_background_task(self, coro):
        """
        Create and track a background task for proper cleanup.

        This ensures tasks are tracked and can be properly cancelled/awaited
        during service shutdown, preventing resource leaks.

        Args:
            coro: The coroutine to run as a background task

        Returns:
            The created asyncio.Task

        Example:
            >>> task = monitoring_svc._create_background_task(some_coroutine())
        """
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

    async def shutdown(self):
        """
        Gracefully shutdown the monitoring service.

        Waits for all background tasks to complete or cancels them if they
        take too long. Call this during application shutdown.

        Example:
            >>> await monitoring_svc.shutdown()
        """
        if self._background_tasks:
            logger.info("Shutting down PrinterMonitoringService, waiting for background tasks",
                       task_count=len(self._background_tasks))

            # Give tasks 5 seconds to complete gracefully
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._background_tasks, return_exceptions=True),
                    timeout=5.0
                )
                logger.info("All PrinterMonitoringService background tasks completed")
            except asyncio.TimeoutError:
                logger.warning("PrinterMonitoringService background tasks timed out, cancelling",
                             remaining_tasks=len(self._background_tasks))
                # Cancel remaining tasks
                for task in self._background_tasks:
                    task.cancel()
                # Wait for cancellation to complete
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

        logger.info("PrinterMonitoringService shutdown complete")

    def set_file_service(self, file_service):
        """
        Set file service dependency.

        This allows for late binding to resolve circular dependencies.

        Args:
            file_service: FileService instance
        """
        self.file_service = file_service
        logger.debug("File service set in PrinterMonitoringService")

    def set_connection_service(self, connection_service):
        """
        Set connection service dependency.

        This allows for late binding to resolve circular dependencies.

        Args:
            connection_service: PrinterConnectionService instance
        """
        self.connection_service = connection_service
        logger.debug("Connection service set in PrinterMonitoringService")
