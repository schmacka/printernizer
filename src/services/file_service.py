"""
File service for managing 3D files and downloads.
Handles both printer files (via APIs) and local files (via folder watching).

REFACTORED VERSION - Phase 2 Technical Debt Reduction
This version delegates responsibilities to specialized services:
- FileDiscoveryService: File discovery from printers
- FileDownloadService: Download management with progress tracking
- FileThumbnailService: Thumbnail extraction and processing
- FileMetadataService: Enhanced metadata extraction

The FileService now acts as a coordinator, maintaining backward compatibility
while using the specialized services internally.
"""
from typing import List, Dict, Any, Optional
import structlog
import asyncio
from pathlib import Path
from datetime import datetime

from src.database.database import Database
from src.database.repositories.file_repository import FileRepository
from src.services.event_service import EventService
from src.services.file_watcher_service import FileWatcherService
from src.services.file_discovery_service import FileDiscoveryService
from src.services.file_download_service import FileDownloadService
from src.services.file_thumbnail_service import FileThumbnailService
from src.services.file_metadata_service import FileMetadataService
from src.services.file_upload_service import FileUploadService
from src.utils.errors import NotFoundError
from src.utils.config import get_settings

logger = structlog.get_logger()


class FileService:
    """
    Coordinating service for managing 3D files and downloads.

    This service acts as a facade/coordinator for file-related operations,
    delegating to specialized services:
    - Discovery: FileDiscoveryService
    - Downloads: FileDownloadService
    - Uploads: FileUploadService
    - Thumbnails: FileThumbnailService
    - Metadata: FileMetadataService

    Responsibilities:
    - File listing and filtering (get_files)
    - File lookups (get_file_by_id)
    - Statistics aggregation
    - Local file management (via FileWatcherService)
    - Coordination between specialized services
    - Backward compatibility with existing API

    Example:
        >>> file_service = FileService(database, event_service, ...)
        >>> files = await file_service.get_files(printer_id="bambu_001")
        >>> result = await file_service.download_file("bambu_001", "model.3mf")
        >>> result = await file_service.upload_files([file1, file2])
    """

    def __init__(
        self,
        database: Database,
        event_service: EventService,
        file_watcher: Optional[FileWatcherService] = None,
        printer_service=None,
        config_service=None,
        library_service=None,
        usage_stats_service=None
    ):
        """
        Initialize file service and its specialized sub-services.

        Args:
            database: Database instance
            event_service: Event service for event-driven communication
            file_watcher: Optional file watcher service for local files
            printer_service: Optional printer service (can be set later)
            config_service: Optional config service (can be set later)
            library_service: Optional library service (can be set later)
            usage_stats_service: Optional usage statistics service for telemetry
        """
        self.database = database
        self.event_service = event_service
        self.file_watcher = file_watcher
        self.printer_service = printer_service
        self.config_service = config_service
        self.library_service = library_service
        self.usage_stats_service = usage_stats_service

        # Initialize specialized services
        self.discovery = FileDiscoveryService(
            database=database,
            event_service=event_service,
            printer_service=printer_service
        )

        self.downloader = FileDownloadService(
            database=database,
            event_service=event_service,
            printer_service=printer_service,
            config_service=config_service,
            library_service=library_service,
            usage_stats_service=usage_stats_service
        )

        self.thumbnail = FileThumbnailService(
            database=database,
            event_service=event_service,
            printer_service=printer_service
        )

        self.metadata = FileMetadataService(
            database=database,
            event_service=event_service
        )

        self.uploader = FileUploadService(
            database=database,
            event_service=event_service,
            thumbnail_service=self.thumbnail,
            metadata_service=self.metadata,
            library_service=library_service,
            usage_stats_service=usage_stats_service
        )

        # Settings access
        self.settings = get_settings()

        # Background task tracking for graceful shutdown
        self._background_tasks: set = set()

        logger.info("FileService initialized with specialized sub-services",
                   discovery=True,
                   downloader=True,
                   uploader=True,
                   thumbnail=True,
                   metadata=True)

    async def initialize(self) -> None:
        """
        Initialize the file service and subscribe to events.

        This should be called after all dependencies are injected.
        """
        # Subscribe thumbnail service to download events
        await self.thumbnail.subscribe_to_download_events()
        logger.info("FileService initialization complete")

    # ========================================================================
    # FILE LISTING AND FILTERING
    # These methods stay in FileService as they coordinate data from multiple sources
    # ========================================================================

    async def get_files(
        self,
        printer_id: Optional[str] = None,
        include_local: bool = True,
        status: Optional[str] = None,
        source: Optional[str] = None,
        has_thumbnail: Optional[bool] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = "created_at",
        order_dir: Optional[str] = "desc",
        page: Optional[int] = 1
    ) -> List[Dict[str, Any]]:
        """
        Get list of available files from printers and local folders.

        This method aggregates files from multiple sources (printers, local watch folders),
        enriches them with printer information, applies filters, and returns paginated results.

        Args:
            printer_id: Filter by specific printer ID
            include_local: Include local watch folder files
            status: Filter by file status
            source: Filter by file source
            has_thumbnail: Filter by thumbnail availability
            search: Search term for filename filtering
            limit: Maximum number of results per page
            order_by: Field to sort by
            order_dir: Sort direction ('asc' or 'desc')
            page: Page number (1-indexed)

        Returns:
            List of file dictionaries with enriched information

        Example:
            >>> files = await file_service.get_files(
            ...     printer_id="bambu_001",
            ...     status="downloaded",
            ...     limit=20,
            ...     page=1
            ... )
        """
        files = []

        # Get printer files from database
        try:
            printer_files = await self.database.list_files(
                printer_id=printer_id if printer_id != 'local' else None,
                source='printer'
            )

            # Get printer information for enriching file data
            printer_info_map = {}
            if self.printer_service:
                try:
                    printers = await self.printer_service.list_printers()
                    printer_info_map = {p.id: p for p in printers}
                except Exception as e:
                    logger.warning(
                        "Could not fetch printer information for file enrichment",
                        error=str(e)
                    )

            # Convert database rows to file format and enrich with printer info
            for file_data in printer_files:
                file_dict = dict(file_data)
                file_dict['source'] = 'printer'

                # Add printer name and type information
                printer_id_val = file_dict.get('printer_id')
                if printer_id_val and printer_id_val in printer_info_map:
                    printer_info = printer_info_map[printer_id_val]
                    printer_name = printer_info.name
                    printer_type = printer_info.type.value if hasattr(printer_info.type, 'value') else str(printer_info.type)

                    file_dict['printer_name'] = printer_name
                    file_dict['printer_type'] = printer_type
                    file_dict['source_display'] = f"{printer_name} ({printer_type})"
                else:
                    file_dict['printer_name'] = 'Unknown'
                    file_dict['printer_type'] = 'unknown'
                    file_dict['source_display'] = 'Unknown Printer'

                files.append(file_dict)

            logger.debug("Retrieved printer files from database", count=len(printer_files))

        except Exception as e:
            logger.error("Error retrieving printer files from database", error=str(e))

        # Get local files from file watcher if enabled and available
        if include_local and self.file_watcher:
            try:
                local_files = self.file_watcher.get_local_files()

                # Enrich local files with source display information
                for local_file in local_files:
                    if local_file.get('source') == 'local_watch':
                        local_file['source_display'] = 'Local Watch Folder'
                        local_file['printer_name'] = None
                        local_file['printer_type'] = None

                files.extend(local_files)
                logger.debug("Retrieved local files", count=len(local_files))
            except Exception as e:
                logger.error("Error retrieving local files", error=str(e))

        # Apply filters
        if printer_id and printer_id != 'local':
            files = [f for f in files if f.get('printer_id') == printer_id or f.get('source') == 'local_watch']

        if status:
            files = [f for f in files if f.get('status') == status]

        if source:
            files = [f for f in files if f.get('source') == source]

        if has_thumbnail is not None:
            files = [f for f in files if bool(f.get('has_thumbnail', False)) == has_thumbnail]

        # Apply search filter (case-insensitive partial match on filename)
        if search:
            search_lower = search.lower()
            files = [f for f in files if search_lower in f.get('filename', '').lower()]

        # Sort files
        reverse_order = order_dir.lower() == 'desc'
        if order_by == 'downloaded_at':
            files = sorted(files, key=lambda x: x.get('downloaded_at') or x.get('created_at') or '', reverse=reverse_order)
        elif order_by == 'created_at':
            files = sorted(files, key=lambda x: x.get('created_at', ''), reverse=reverse_order)
        elif order_by == 'filename':
            files = sorted(files, key=lambda x: x.get('filename', ''), reverse=reverse_order)
        elif order_by == 'file_size':
            files = sorted(files, key=lambda x: x.get('file_size', 0), reverse=reverse_order)

        # Apply pagination
        if limit:
            start_idx = (page - 1) * limit if page > 1 else 0
            files = files[start_idx:start_idx + limit]

        return files

    async def get_files_with_count(
        self,
        printer_id: Optional[str] = None,
        include_local: bool = True,
        status: Optional[str] = None,
        source: Optional[str] = None,
        has_thumbnail: Optional[bool] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = "created_at",
        order_dir: Optional[str] = "desc",
        page: Optional[int] = 1
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get files with total count (optimized pagination).

        This method efficiently returns both the paginated file list and the total count,
        avoiding the need to fetch all records twice.

        Args:
            printer_id: Filter by specific printer ID
            include_local: Include local watch folder files
            status: Filter by file status
            source: Filter by file source
            has_thumbnail: Filter by thumbnail availability
            search: Search term for filename filtering
            limit: Maximum number of results per page
            order_by: Field to sort by
            order_dir: Sort direction ('asc' or 'desc')
            page: Page number (1-indexed)

        Returns:
            Tuple of (files list, total count)

        Example:
            >>> files, total = await file_service.get_files_with_count(limit=20, page=1)
            >>> print(f"Showing {len(files)} of {total} files")

        Notes:
            - This method applies filters in memory after fetching from repository
            - Count reflects the filtered results, not raw database count
        """
        # Get all files without pagination first (for accurate count after filtering)
        all_files = await self.get_files(
            printer_id=printer_id,
            include_local=include_local,
            status=status,
            source=source,
            has_thumbnail=has_thumbnail,
            search=search,
            limit=None,  # No limit to get all for counting
            order_by=order_by,
            order_dir=order_dir,
            page=1
        )

        total_count = len(all_files)

        # Now apply pagination to get the subset
        if limit and page:
            start_idx = (page - 1) * limit if page > 1 else 0
            paginated_files = all_files[start_idx:start_idx + limit]
        else:
            paginated_files = all_files

        logger.info("Got files with count",
                   count=len(paginated_files),
                   total=total_count,
                   printer_id=printer_id,
                   status=status,
                   source=source)

        return paginated_files, total_count

    async def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file information by ID.

        Searches both printer files in database and local files from file watcher.

        Args:
            file_id: File identifier

        Returns:
            File dictionary if found, None otherwise

        Example:
            >>> file = await file_service.get_file_by_id("bambu_001_model.3mf")
        """
        try:
            # Check printer files in database first
            files = await self.database.list_files()
            for file_data in files:
                if file_data['id'] == file_id:
                    return dict(file_data)

            # Check local files from file watcher if available
            if self.file_watcher:
                local_files = self.file_watcher.get_local_files()
                for file_data in local_files:
                    if file_data.get('id') == file_id:
                        return dict(file_data)

            return None
        except Exception as e:
            logger.error("Failed to get file by ID", file_id=file_id, error=str(e))
            return None

    async def get_file_statistics(self) -> Dict[str, Any]:
        """
        Get file management statistics.

        Aggregates statistics from all file sources.

        Returns:
            Dictionary with statistics including counts, sizes, and success rates

        Example:
            >>> stats = await file_service.get_file_statistics()
            >>> print(f"Total files: {stats['total_files']}")
        """
        try:
            # Get all files without pagination
            files = await self.get_files(limit=None)

            # Calculate statistics
            total_files = len(files)

            # Separate by source
            local_files = [f for f in files if f.get('source') == 'local_watch']
            printer_files = [f for f in files if f.get('source') == 'printer']

            # Calculate total size
            total_size = sum(f.get('file_size', 0) or 0 for f in files)

            # Count by status for PRINTER files
            available_count = len([f for f in printer_files if f.get('status') == 'available'])
            downloaded_count = len([f for f in printer_files if f.get('status') == 'downloaded'])
            failed_count = len([f for f in printer_files if f.get('status') == 'failed'])
            local_count = len(local_files)

            # Calculate download success rate
            total_download_attempts = downloaded_count + failed_count
            download_success_rate = downloaded_count / total_download_attempts if total_download_attempts > 0 else 1.0

            logger.info("File statistics calculated",
                       total=total_files,
                       available=available_count,
                       downloaded=downloaded_count,
                       local_count=local_count,
                       failed=failed_count,
                       total_size_bytes=total_size)

            return {
                "total_files": total_files,
                "local_files": len(local_files),
                "printer_files": len(printer_files),
                "available_count": available_count,
                "downloaded_count": downloaded_count,
                "failed_count": failed_count,
                "local_count": local_count,
                "total_size": total_size,
                "download_success_rate": download_success_rate
            }

        except Exception as e:
            logger.error("Error calculating file statistics", error=str(e), exc_info=True)
            return {
                "total_files": 0,
                "local_files": 0,
                "printer_files": 0,
                "available_count": 0,
                "downloaded_count": 0,
                "failed_count": 0,
                "local_count": 0,
                "total_size": 0,
                "download_success_rate": 0.0
            }

    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file record (for local files and downloaded files, also delete physical file).

        Args:
            file_id: File identifier

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            NotFoundError: If file not found

        Example:
            >>> success = await file_service.delete_file("bambu_001_model.3mf")
        """
        try:
            file_data = await self.get_file_by_id(file_id)
            if not file_data:
                raise NotFoundError("File", file_id)

            # Delete physical file if it exists locally
            should_delete_physical = (
                file_data.get('source') == 'local_watch' or
                (file_data.get('source') == 'printer' and file_data.get('status') == 'downloaded')
            )

            if should_delete_physical and file_data.get('file_path'):
                try:
                    file_path = Path(file_data['file_path'])
                    if file_path.exists():
                        file_path.unlink()
                        logger.info("Deleted physical file", path=str(file_path))
                except Exception as e:
                    logger.warning("Could not delete physical file",
                                 path=file_data['file_path'],
                                 error=str(e))

            # Delete from database
            if file_data.get('source') == 'local_watch':
                success = await self.database.delete_local_file(file_id)
            else:
                # For printer files, reset to available status so they can be downloaded again
                success = await self.database.update_file(file_id, {
                    'status': 'available',
                    'file_path': None,
                    'downloaded_at': None,
                    'download_progress': 0
                })

            if success:
                logger.info("File deleted successfully", file_id=file_id)

                # Emit file deleted event
                await self.event_service.emit_event("file_deleted", {
                    "file_id": file_id,
                    "filename": file_data.get('filename'),
                    "source": file_data.get('source')
                })

            return success

        except Exception as e:
            logger.error("Failed to delete file", file_id=file_id, error=str(e))
            return False

    # ========================================================================
    # DELEGATION TO FileDiscoveryService
    # ========================================================================

    async def get_printer_files(self, printer_id: str) -> List[Dict[str, Any]]:
        """Get files available on specific printer. Delegates to FileDiscoveryService."""
        return await self.discovery.get_printer_files(printer_id)

    async def sync_printer_files(self, printer_id: str) -> Dict[str, Any]:
        """Synchronize files from a specific printer. Delegates to FileDiscoveryService."""
        return await self.discovery.sync_printer_files(printer_id)

    async def discover_printer_files(self, printer_id: str) -> List[Dict[str, Any]]:
        """
        Discover files on a specific printer for background discovery task.
        Delegates to FileDiscoveryService.
        """
        return await self.discovery.discover_printer_files(printer_id)

    async def find_file_by_name(
        self,
        filename: str,
        printer_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find file by filename, optionally filtering by printer_id.
        Delegates to FileDiscoveryService for printer files, checks local files too.
        """
        # Check printer files via discovery service
        file_data = await self.discovery.find_file_by_name(filename, printer_id)
        if file_data:
            return file_data

        # Check local files from file watcher if available
        if self.file_watcher:
            try:
                local_files = self.file_watcher.get_local_files()
                for local_file in local_files:
                    if local_file.get('filename') == filename:
                        # Only return local files if no printer_id filter or if it matches
                        if printer_id is None or local_file.get('printer_id') == printer_id:
                            return dict(local_file)
            except Exception as e:
                logger.error("Error checking local files", error=str(e))

        return None

    # ========================================================================
    # DELEGATION TO FileDownloadService
    # ========================================================================

    async def download_file(
        self,
        printer_id: str,
        filename: str,
        destination_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download file from printer. Delegates to FileDownloadService.

        ⭐ PRIMARY FILE DOWNLOAD METHOD - Always use this for file downloads.
        """
        return await self.downloader.download_file(printer_id, filename, destination_path)

    async def get_download_status(self, file_id: str) -> Dict[str, Any]:
        """Get download status of a file. Delegates to FileDownloadService."""
        return await self.downloader.get_download_status(file_id)

    async def cleanup_download_status(self, max_age_hours: int = 24) -> None:
        """Clean up old download status entries. Delegates to FileDownloadService."""
        await self.downloader.cleanup_download_status(max_age_hours)

    # Backward compatibility: expose download progress/status from downloader
    @property
    def download_progress(self) -> Dict[str, int]:
        """Access download progress from downloader (backward compatibility)."""
        return self.downloader.download_progress

    @property
    def download_status(self) -> Dict[str, str]:
        """Access download status from downloader (backward compatibility)."""
        return self.downloader.download_status

    @property
    def download_bytes(self) -> Dict[str, int]:
        """Access download bytes from downloader (backward compatibility)."""
        return self.downloader.download_bytes

    @property
    def download_total_bytes(self) -> Dict[str, int]:
        """Access download total bytes from downloader (backward compatibility)."""
        return self.downloader.download_total_bytes

    # ========================================================================
    # DELEGATION TO FileUploadService
    # ========================================================================

    async def upload_files(
        self,
        files: List,
        is_business: bool = False,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload files to the library. Delegates to FileUploadService.

        ⭐ PRIMARY FILE UPLOAD METHOD - Always use this for file uploads.

        Args:
            files: List of UploadFile objects
            is_business: Whether these are business order files
            notes: Optional notes to attach to files

        Returns:
            Dict with upload results:
                - uploaded_files: List of successfully uploaded file info
                - failed_files: List of failed uploads with errors
                - total_count: Total files processed
                - success_count: Number of successful uploads
                - failure_count: Number of failed uploads
        """
        return await self.uploader.upload_files(files, is_business, notes)

    # ========================================================================
    # DELEGATION TO FileThumbnailService
    # ========================================================================

    async def process_file_thumbnails(self, file_path: str, file_id: str) -> bool:
        """
        Process a file to extract thumbnails and metadata.
        Delegates to FileThumbnailService.
        """
        return await self.thumbnail.process_file_thumbnails(file_path, file_id)

    def get_thumbnail_processing_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent thumbnail processing log entries. Delegates to FileThumbnailService."""
        return self.thumbnail.get_thumbnail_processing_log(limit)

    # Backward compatibility: expose thumbnail processing log
    @property
    def thumbnail_processing_log(self) -> List[Dict[str, Any]]:
        """Access thumbnail processing log (backward compatibility)."""
        return self.thumbnail.thumbnail_processing_log

    # ========================================================================
    # DELEGATION TO FileMetadataService
    # ========================================================================

    async def extract_enhanced_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract enhanced metadata from a file.
        Delegates to FileMetadataService.
        """
        return await self.metadata.extract_enhanced_metadata(file_id)

    # ========================================================================
    # LOCAL FILE MANAGEMENT (via FileWatcherService)
    # ========================================================================

    async def get_local_files(self) -> List[Dict[str, Any]]:
        """Get list of local files only."""
        if not self.file_watcher:
            return []

        try:
            return self.file_watcher.get_local_files()
        except Exception as e:
            logger.error("Error retrieving local files", error=str(e))
            return []

    async def scan_local_files(self) -> List[Dict[str, Any]]:
        """Scan local watch folders for new files (called by file discovery task)."""
        if not self.file_watcher:
            return []

        try:
            # Get current local files from file watcher
            current_files = self.file_watcher.get_local_files()
            logger.debug("Scanned local files", count=len(current_files))
            return current_files
        except Exception as e:
            logger.error("Error scanning local files", error=str(e))
            return []

    async def get_watch_status(self) -> Dict[str, Any]:
        """Get file watcher status."""
        if not self.file_watcher:
            return {"enabled": False, "message": "File watcher not available"}

        try:
            return self.file_watcher.get_watch_status()
        except Exception as e:
            logger.error("Error getting watch status", error=str(e))
            return {"enabled": False, "error": str(e)}

    async def reload_watch_folders(self) -> Dict[str, Any]:
        """Reload watch folders configuration."""
        if not self.file_watcher:
            return {"success": False, "message": "File watcher not available"}

        try:
            await self.file_watcher.reload_watch_folders()
            return {"success": True, "message": "Watch folders reloaded successfully"}
        except Exception as e:
            logger.error("Error reloading watch folders", error=str(e))
            return {"success": False, "error": str(e)}

    # ========================================================================
    # DEPENDENCY INJECTION (for resolving circular dependencies)
    # ========================================================================

    def set_printer_service(self, printer_service) -> None:
        """
        Set printer service dependency on FileService and all sub-services.

        This allows for late binding to resolve circular dependencies.

        Args:
            printer_service: PrinterService instance
        """
        self.printer_service = printer_service
        self.discovery.set_printer_service(printer_service)
        self.downloader.set_printer_service(printer_service)
        self.thumbnail.set_printer_service(printer_service)
        logger.info("Printer service set in FileService and all sub-services")

    def set_config_service(self, config_service) -> None:
        """Set config service dependency."""
        self.config_service = config_service
        self.downloader.set_config_service(config_service)
        logger.debug("Config service set in FileService")

    def set_library_service(self, library_service):
        """Set library service dependency."""
        self.library_service = library_service
        self.downloader.set_library_service(library_service)
        logger.debug("Library service set in FileService")

    # ========================================================================
    # BACKGROUND TASK MANAGEMENT
    # ========================================================================

    def _create_background_task(self, coro):
        """
        Create and track a background task for proper cleanup.

        This ensures tasks are tracked and can be properly cancelled/awaited
        during service shutdown, preventing resource leaks.

        Args:
            coro: The coroutine to run as a background task

        Returns:
            The created asyncio.Task
        """
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

    async def cleanup_files(
        self,
        dry_run: bool = True,
        deleted_days: int = 30,
        failed_days: int = 7
    ) -> Dict[str, Any]:
        """
        Clean up old file records from the database.

        Removes file records that are:
        - Marked as 'deleted' and older than deleted_days (default: 30 days)
        - Marked as 'failed' and older than failed_days (default: 7 days)

        This is a conservative cleanup that only removes database records,
        not physical files. Physical file deletion should be handled separately.

        Args:
            dry_run: If True, only report what would be deleted without actually deleting.
                    Default is True for safety.
            deleted_days: Number of days after which deleted files are cleaned up (default: 30)
            failed_days: Number of days after which failed files are cleaned up (default: 7)

        Returns:
            Dictionary with cleanup statistics:
                - old_deleted_removed: Count of deleted file records removed
                - failed_downloads_removed: Count of failed file records removed
                - dry_run: Whether this was a dry run

        Example:
            >>> # Preview what would be deleted
            >>> stats = await file_service.cleanup_files(dry_run=True)
            >>> print(f"Would remove {stats['old_deleted_removed']} deleted files")

            >>> # Actually perform cleanup
            >>> stats = await file_service.cleanup_files(dry_run=False)
            >>> print(f"Removed {stats['old_deleted_removed'] + stats['failed_downloads_removed']} file records")
        """
        try:
            # Get repository access via database connection
            file_repo = FileRepository(self.database.get_connection())

            # Find old deleted files
            old_deleted = await file_repo.get_old_deleted_files(days=deleted_days)
            old_deleted_ids = [f['id'] for f in old_deleted]

            # Find old failed files
            old_failed = await file_repo.get_old_failed_files(days=failed_days)
            old_failed_ids = [f['id'] for f in old_failed]

            logger.info(
                "File cleanup analysis complete",
                old_deleted_count=len(old_deleted_ids),
                old_failed_count=len(old_failed_ids),
                dry_run=dry_run
            )

            old_deleted_removed = 0
            failed_downloads_removed = 0

            if not dry_run:
                # Delete old deleted files
                if old_deleted_ids:
                    old_deleted_removed = await file_repo.delete_by_ids(old_deleted_ids)
                    logger.info(
                        "Cleaned up old deleted file records",
                        count=old_deleted_removed
                    )

                # Delete old failed files
                if old_failed_ids:
                    failed_downloads_removed = await file_repo.delete_by_ids(old_failed_ids)
                    logger.info(
                        "Cleaned up old failed file records",
                        count=failed_downloads_removed
                    )

                # Emit cleanup event
                await self.event_service.emit_event("files_cleaned_up", {
                    "old_deleted_removed": old_deleted_removed,
                    "failed_downloads_removed": failed_downloads_removed,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # In dry run mode, report what would be deleted
                old_deleted_removed = len(old_deleted_ids)
                failed_downloads_removed = len(old_failed_ids)

            return {
                "old_deleted_removed": old_deleted_removed,
                "failed_downloads_removed": failed_downloads_removed,
                "dry_run": dry_run
            }

        except Exception as e:
            logger.error("Failed to cleanup files", error=str(e), exc_info=True)
            return {
                "old_deleted_removed": 0,
                "failed_downloads_removed": 0,
                "dry_run": dry_run,
                "error": str(e)
            }

    async def shutdown(self):
        """
        Gracefully shutdown the file service.

        Waits for all background tasks to complete or cancels them if they
        take too long. Call this during application shutdown.
        """
        if self._background_tasks:
            logger.info("Shutting down FileService, waiting for background tasks",
                       task_count=len(self._background_tasks))

            # Give tasks 5 seconds to complete gracefully
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._background_tasks, return_exceptions=True),
                    timeout=5.0
                )
                logger.info("All FileService background tasks completed")
            except asyncio.TimeoutError:
                logger.warning("FileService background tasks timed out, cancelling",
                             remaining_tasks=len(self._background_tasks))
                # Cancel remaining tasks
                for task in self._background_tasks:
                    task.cancel()
                # Wait for cancellation to complete
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

        logger.info("FileService shutdown complete")


async def scan_printer_files(printer_service=None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Module-level function to scan files from all connected printers.
    Returns a dictionary mapping printer IDs to lists of discovered files.
    
    This is a stub implementation used by E2E tests to mock file discovery.
    Real implementation would be called via FileService.discover_printer_files.
    
    Args:
        printer_service: Optional printer service instance
    
    Returns:
        Dictionary mapping printer IDs to lists of file metadata dictionaries
    """
    try:
        logger.info("scan_printer_files_called")
        
        # Stub implementation - returns empty dict
        # Real implementation would query all active printers
        return {}
        
    except Exception as e:
        logger.error("scan_printer_files_error", error=str(e))
        return {}
