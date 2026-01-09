"""
File download service for managing file downloads from printers.

This service is responsible for downloading files from printers, tracking download
progress, managing download state, and integrating with the library system.

Part of FileService refactoring - Phase 2 technical debt reduction.
"""
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import structlog

from src.database.database import Database
from src.database.repositories import FileRepository
from src.services.event_service import EventService

logger = structlog.get_logger()


class FileDownloadService:
    """
    Service for downloading files from printers.

    This service handles:
    - Downloading files from printers with progress tracking
    - Managing download state (starting, downloading, completed, failed)
    - Path validation and security
    - Database updates for downloaded files
    - Library integration for downloaded files
    - Triggering thumbnail processing after download

    Events Emitted:
    - file_download_started: When download begins
    - file_download_progress: During download (if supported)
    - file_download_complete: When download succeeds
    - file_download_failed: When download fails

    Example:
        >>> downloader = FileDownloadService(database, event_service, ...)
        >>> result = await downloader.download_file("printer_123", "model.3mf")
        >>> if result['status'] == 'success':
        ...     print(f"Downloaded to: {result['local_path']}")
    """

    def __init__(
        self,
        database: Database,
        event_service: EventService,
        printer_service=None,
        config_service=None,
        library_service=None,
        usage_stats_service=None
    ):
        """
        Initialize file download service.

        Args:
            database: Database instance for storing file records
            event_service: Event service for emitting download events
            printer_service: Optional printer service for performing downloads
            config_service: Optional config service for download paths
            library_service: Optional library service for adding downloaded files
            usage_stats_service: Optional usage statistics service for telemetry
        """
        self.database = database
        self.file_repo = FileRepository(database._connection)
        self.event_service = event_service
        self.printer_service = printer_service
        self.config_service = config_service
        self.library_service = library_service
        self.usage_stats_service = usage_stats_service

        # Download state tracking
        self.download_progress: Dict[str, int] = {}
        self.download_status: Dict[str, str] = {}
        self.download_bytes: Dict[str, int] = {}
        self.download_total_bytes: Dict[str, int] = {}

    async def download_file(
        self,
        printer_id: str,
        filename: str,
        destination_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download file from printer.

        ⭐ PRIMARY FILE DOWNLOAD METHOD - Always use this for file downloads.

        This is the canonical implementation that provides:
        - Progress tracking
        - Automatic destination path creation
        - Database updates
        - File verification
        - Error handling
        - Event emission
        - Library integration
        - Thumbnail processing trigger

        Args:
            printer_id: ID of the printer containing the file
            filename: Name of the file to download
            destination_path: Optional custom destination (auto-created if not provided)

        Returns:
            Dict with keys:
                - status: 'success' or 'error'
                - message: Status message
                - local_path: Path to downloaded file (None on error)
                - file_id: File identifier
                - file_size: Size of downloaded file in bytes

        Raises:
            ValueError: If printer service not available or invalid parameters

        Example:
            >>> result = await downloader.download_file("bambu_001", "model.3mf")
            >>> print(result)
            {
                'status': 'success',
                'message': 'File downloaded successfully',
                'local_path': '/downloads/bambu_001/model.3mf',
                'file_id': 'bambu_001_model.3mf',
                'file_size': 1024000
            }

        Note:
            Do NOT call printer.download_file() directly. Always use this method.
            See docs/development/FILE_OPERATIONS_GUIDE.md for architecture details.
        """
        try:
            if not self.printer_service:
                raise ValueError("Printer service not available")

            file_id = f"{printer_id}_{filename}"

            # Set up progress tracking
            self.download_progress[file_id] = 0
            self.download_status[file_id] = "starting"

            # Create destination path if not provided
            if not destination_path:
                destination_path = await self._create_destination_path(
                    printer_id,
                    filename
                )

            logger.info("Starting file download",
                       printer_id=printer_id,
                       filename=filename,
                       destination=destination_path)

            # Emit download started event
            await self.event_service.emit_event("file_download_started", {
                "printer_id": printer_id,
                "filename": filename,
                "file_id": file_id,
                "destination": destination_path
            })

            # Update status to downloading
            self.download_status[file_id] = "downloading"

            # Perform actual download via printer service
            success = await self.printer_service.download_printer_file(
                printer_id, filename, destination_path
            )

            if success:
                return await self._handle_successful_download(
                    printer_id,
                    filename,
                    file_id,
                    destination_path
                )
            else:
                return await self._handle_failed_download(
                    printer_id,
                    filename,
                    file_id,
                    "Download failed"
                )

        except Exception as e:
            logger.error("File download failed",
                        printer_id=printer_id,
                        filename=filename,
                        error=str(e))
            if 'file_id' in locals():
                self.download_status[file_id] = "failed"
            return {
                "status": "error",
                "message": str(e),
                "local_path": None
            }

    async def _handle_successful_download(
        self,
        printer_id: str,
        filename: str,
        file_id: str,
        destination_path: str
    ) -> Dict[str, Any]:
        """
        Handle successful download completion.

        Performs:
        - Database updates
        - File verification
        - Thumbnail processing trigger
        - Library integration
        - Event emission

        Args:
            printer_id: Printer ID
            filename: Filename
            file_id: File identifier
            destination_path: Path to downloaded file

        Returns:
            Success result dictionary
        """
        try:
            # Update database with download info
            await self.file_repo.update(file_id, {
                'status': 'downloaded',
                'file_path': destination_path,
                'downloaded_at': datetime.now().isoformat(),
                'download_progress': 100
            })

            self.download_progress[file_id] = 100
            self.download_status[file_id] = "completed"

            # Verify the file was actually downloaded
            if not Path(destination_path).exists():
                logger.error("Download reported success but file doesn't exist",
                           file_id=file_id,
                           destination=destination_path)
                self.download_status[file_id] = "failed"
                return {
                    "status": "error",
                    "message": "Download completed but file not found",
                    "local_path": None
                }

            file_size = Path(destination_path).stat().st_size
            logger.info("File download verified",
                       printer_id=printer_id,
                       filename=filename,
                       destination=destination_path,
                       size=file_size)

            # Emit event to trigger thumbnail processing
            # Thumbnail service will subscribe to this event
            await self.event_service.emit_event("file_needs_thumbnail_processing", {
                "file_id": file_id,
                "file_path": destination_path
            })

            # Add to library if library service is available and enabled
            if self.library_service and self.library_service.enabled:
                await self._add_to_library(
                    printer_id,
                    filename,
                    destination_path
                )

            # Emit download complete event
            await self.event_service.emit_event("file_download_complete", {
                "printer_id": printer_id,
                "filename": filename,
                "file_id": file_id,
                "local_path": destination_path,
                "file_size": file_size
            })

            logger.info("File download completed successfully",
                       printer_id=printer_id,
                       filename=filename,
                       size=file_size)

            # Record usage statistics (privacy-safe: no filenames or personal data)
            if self.usage_stats_service:
                await self.usage_stats_service.record_event("file_downloaded", {
                    "file_size_mb": round(file_size / (1024 * 1024), 2)
                })

            return {
                "status": "success",
                "message": "File downloaded successfully",
                "local_path": destination_path,
                "file_id": file_id,
                "file_size": file_size
            }

        except Exception as e:
            logger.error("Error in download completion processing",
                        printer_id=printer_id,
                        filename=filename,
                        error=str(e))
            self.download_status[file_id] = "failed"
            return {
                "status": "error",
                "message": f"Download post-processing failed: {str(e)}",
                "local_path": destination_path
            }

    async def _handle_failed_download(
        self,
        printer_id: str,
        filename: str,
        file_id: str,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Handle failed download.

        Updates state and emits failure event.

        Args:
            printer_id: Printer ID
            filename: Filename
            file_id: File identifier
            error_message: Error message

        Returns:
            Error result dictionary
        """
        self.download_status[file_id] = "failed"

        # Emit download failed event
        await self.event_service.emit_event("file_download_failed", {
            "printer_id": printer_id,
            "filename": filename,
            "file_id": file_id,
            "error": error_message
        })

        return {
            "status": "error",
            "message": error_message,
            "local_path": None
        }

    async def _create_destination_path(
        self,
        printer_id: str,
        filename: str
    ) -> str:
        """
        Create and validate destination path for download.

        Args:
            printer_id: Printer ID
            filename: Filename to download

        Returns:
            Validated destination path string

        Raises:
            ValueError: If path creation fails or path traversal detected
        """
        # Get download path from configuration
        base_download_path = "/data/printernizer/printer-files"  # fallback default for HA addon
        if self.config_service:
            try:
                base_download_path = self.config_service.settings.downloads_path
            except Exception as e:
                logger.warning(
                    "Failed to get downloads path from config, using default",
                    error=str(e)
                )

        downloads_dir = Path(base_download_path) / printer_id
        try:
            downloads_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Created downloads directory",
                        path=str(downloads_dir),
                        base_path=base_download_path)
        except Exception as e:
            logger.error("Failed to create downloads directory",
                        path=str(downloads_dir),
                        error=str(e))
            raise ValueError(f"Cannot create downloads directory: {e}")

        # Validate filename to prevent path traversal attacks
        validated_path = self._validate_safe_path(downloads_dir, filename)
        return str(validated_path)

    async def _add_to_library(
        self,
        printer_id: str,
        filename: str,
        file_path: str
    ):
        """
        Add downloaded file to library.

        Args:
            printer_id: Printer ID
            filename: Filename
            file_path: Path to downloaded file
        """
        try:
            # Get printer info
            printer = await self.printer_service.get_printer(printer_id)
            printer_name = printer.name if printer else 'unknown'

            # Extract manufacturer and model (convert Printer object to dict for extraction)
            printer_dict = printer.dict() if printer else {}
            printer_info = self._extract_printer_info(printer_dict) if printer else {
                'manufacturer': 'unknown',
                'printer_model': 'unknown'
            }

            source_info = {
                'type': 'printer',
                'printer_id': printer_id,
                'printer_name': printer_name,
                'manufacturer': printer_info['manufacturer'],
                'printer_model': printer_info['printer_model'],
                'original_filename': filename,
                'original_path': f'/cache/{filename}',  # Typical printer path
                'discovered_at': datetime.now().isoformat()
            }

            # Add file to library (will copy to library folder)
            await self.library_service.add_file_to_library(
                source_path=Path(file_path),
                source_info=source_info,
                copy_file=True  # Copy, preserve downloads folder
            )

            logger.info("Added downloaded file to library",
                       filename=filename,
                       printer_id=printer_id,
                       printer_name=printer_name,
                       manufacturer=printer_info['manufacturer'],
                       printer_model=printer_info['printer_model'])

        except Exception as e:
            logger.error("Failed to add downloaded file to library",
                        filename=filename,
                        printer_id=printer_id,
                        error=str(e))
            # Continue anyway - download still successful

    def _extract_printer_info(self, printer: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract manufacturer and printer model from printer configuration.

        Args:
            printer: Printer configuration dict with 'type' and 'name' fields

        Returns:
            Dict with 'manufacturer' and 'printer_model' keys

        Example:
            >>> info = downloader._extract_printer_info({
            ...     'type': 'bambu_lab',
            ...     'name': 'Bambu A1'
            ... })
            >>> print(info)
            {'manufacturer': 'bambu_lab', 'printer_model': 'A1'}
        """
        from src.models.printer import PrinterType

        manufacturer = 'unknown'
        printer_model = 'unknown'

        # Extract manufacturer from printer type
        printer_type = printer.get('type', 'unknown')
        if printer_type == PrinterType.BAMBU_LAB.value or printer_type == 'bambu_lab':
            manufacturer = 'bambu_lab'
        elif printer_type == PrinterType.PRUSA_CORE.value or printer_type == 'prusa_core':
            manufacturer = 'prusa_research'

        # Extract model from printer name or configuration
        printer_name = printer.get('name', '')

        # Common Bambu Lab models
        bambu_models = ['A1', 'A1 Mini', 'P1P', 'P1S', 'X1C', 'X1E']
        for model in bambu_models:
            if model.lower() in printer_name.lower():
                printer_model = model
                break

        # Common Prusa models
        prusa_models = ['Core One', 'MK4', 'MK3S', 'MK3', 'MINI', 'XL']
        for model in prusa_models:
            if model.lower() in printer_name.lower():
                printer_model = model
                break

        # If no model matched, use the printer name as fallback
        if printer_model == 'unknown' and printer_name:
            printer_model = printer_name

        return {
            'manufacturer': manufacturer,
            'printer_model': printer_model
        }

    def _validate_safe_path(self, base_dir: Path, filename: str) -> Path:
        """
        Ensure path is within base_dir to prevent path traversal attacks.

        Args:
            base_dir: The base directory that the file should be within
            filename: The filename (potentially containing path components)

        Returns:
            The validated full path

        Raises:
            ValueError: If the path attempts to escape the base directory

        Example:
            >>> path = downloader._validate_safe_path(Path("/downloads"), "model.3mf")
            >>> # Returns: Path("/downloads/model.3mf")
            >>>
            >>> path = downloader._validate_safe_path(Path("/downloads"), "../etc/passwd")
            >>> # Raises: ValueError("Path traversal detected: ../etc/passwd")
        """
        full_path = (base_dir / filename).resolve()
        base_resolved = base_dir.resolve()

        if not str(full_path).startswith(str(base_resolved)):
            raise ValueError(f"Path traversal detected: {filename}")

        return full_path

    async def get_download_status(self, file_id: str) -> Dict[str, Any]:
        """
        Get download status of a file.

        Checks both in-memory state and database for download status.

        Args:
            file_id: File identifier

        Returns:
            Dict with keys:
                - file_id: File identifier
                - status: Current status (starting, downloading, completed, failed, unknown, not_found)
                - progress: Download progress (0-100)
                - downloaded_at: Timestamp of download completion (if available)
                - local_path: Path to downloaded file (if available)
                - error: Error message (if status is error)

        Example:
            >>> status = await downloader.get_download_status("bambu_001_model.3mf")
            >>> print(f"Status: {status['status']}, Progress: {status['progress']}%")
        """
        try:
            # Check in-memory status first
            if file_id in self.download_status:
                return {
                    "file_id": file_id,
                    "status": self.download_status[file_id],
                    "progress": self.download_progress.get(file_id, 0),
                    "bytes_downloaded": self.download_bytes.get(file_id, 0),
                    "total_bytes": self.download_total_bytes.get(file_id, 0)
                }

            # Check database for historical status
            file_data = await self.file_repo.list()
            for file_info in file_data:
                if file_info['id'] == file_id:
                    return {
                        "file_id": file_id,
                        "status": file_info.get('status', 'unknown'),
                        "progress": file_info.get('download_progress', 0),
                        "downloaded_at": file_info.get('downloaded_at'),
                        "local_path": file_info.get('file_path')
                    }

            # File not found
            return {
                "file_id": file_id,
                "status": "not_found",
                "progress": 0
            }

        except Exception as e:
            logger.error("Failed to get download status",
                        file_id=file_id,
                        error=str(e))
            return {
                "file_id": file_id,
                "status": "error",
                "progress": 0,
                "error": str(e)
            }

    async def _broadcast_progress(self, file_id: str) -> None:
        """
        Broadcast download progress via WebSocket.

        Emits a system_event with type 'download_progress' containing
        current download state for real-time UI updates.

        Args:
            file_id: File identifier to broadcast progress for
        """
        try:
            # Lazy import to avoid circular dependency
            from src.api.routers.websocket import broadcast_system_event

            await broadcast_system_event("download_progress", {
                "download_id": file_id,
                "progress": self.download_progress.get(file_id, 0),
                "status": self.download_status.get(file_id, "unknown"),
                "bytes_downloaded": self.download_bytes.get(file_id, 0),
                "total_bytes": self.download_total_bytes.get(file_id, 0)
            })
        except Exception as e:
            # Don't fail the download if broadcast fails
            logger.warning("Failed to broadcast download progress",
                          file_id=file_id,
                          error=str(e))

    async def cleanup_download_status(self, max_age_hours: int = 24) -> None:
        """
        Clean up old download status entries.

        Removes completed/failed downloads from in-memory tracking after
        the specified age to prevent memory growth.

        Args:
            max_age_hours: Maximum age in hours for keeping status (default: 24)

        Example:
            >>> await downloader.cleanup_download_status(max_age_hours=12)
        """
        try:
            # Clean up in-memory status for completed/failed downloads
            to_remove = []
            for file_id, status in self.download_status.items():
                if status in ['completed', 'failed']:
                    to_remove.append(file_id)

            for file_id in to_remove:
                if file_id in self.download_status:
                    del self.download_status[file_id]
                if file_id in self.download_progress:
                    del self.download_progress[file_id]
                if file_id in self.download_bytes:
                    del self.download_bytes[file_id]
                if file_id in self.download_total_bytes:
                    del self.download_total_bytes[file_id]

            logger.info("Cleaned up download status", removed_entries=len(to_remove))

        except Exception as e:
            logger.error("Failed to cleanup download status", error=str(e))

    def set_printer_service(self, printer_service) -> None:
        """
        Set printer service dependency.

        Allows for late binding of printer service to resolve circular dependencies.

        Args:
            printer_service: PrinterService instance
        """
        self.printer_service = printer_service
        logger.debug("Printer service set in FileDownloadService")

    def set_config_service(self, config_service) -> None:
        """
        Set config service dependency.

        Args:
            config_service: ConfigService instance
        """
        self.config_service = config_service
        logger.debug("Config service set in FileDownloadService")

    def set_library_service(self, library_service):
        """
        Set library service dependency.

        Args:
            library_service: LibraryService instance
        """
        self.library_service = library_service
        logger.debug("Library service set in FileDownloadService")
