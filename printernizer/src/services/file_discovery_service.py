"""
File discovery service for managing file discovery from printers.

This service is responsible for discovering files available on printers via their APIs,
synchronizing file lists, and maintaining the database of available printer files.

Part of FileService refactoring - Phase 2 technical debt reduction.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import structlog

from src.database.database import Database
from src.database.repositories import FileRepository
from src.services.event_service import EventService

logger = structlog.get_logger()


class FileDiscoveryService:
    """
    Service for discovering files on printers.

    This service handles:
    - Discovering files available on specific printers
    - Synchronizing file lists between printers and database
    - Finding files by name or ID
    - Maintaining printer file metadata

    Events Emitted:
    - files_discovered: When new files are found on a printer
    - file_sync_complete: When sync operation completes
    - file_discovered: When a single file is discovered

    Example:
        >>> discovery = FileDiscoveryService(database, event_service, printer_service)
        >>> files = await discovery.get_printer_files("printer_123")
        >>> await discovery.sync_printer_files("printer_123")
    """

    def __init__(
        self,
        database: Database,
        event_service: EventService,
        printer_service=None
    ):
        """
        Initialize file discovery service.

        Args:
            database: Database instance for storing file records
            event_service: Event service for emitting discovery events
            printer_service: Optional printer service for accessing printer APIs
                           Can be None if using event-driven communication
        """
        self.database = database
        self.file_repo = FileRepository(database._connection)
        self.event_service = event_service
        self.printer_service = printer_service

    async def get_printer_files(self, printer_id: str) -> List[Dict[str, Any]]:
        """
        Get files available on specific printer.

        This method discovers files directly from the printer via the printer service,
        stores them in the database, and returns the file list.

        Args:
            printer_id: ID of the printer to query

        Returns:
            List of file dictionaries with keys:
                - id: Unique file identifier (printer_id_filename)
                - printer_id: ID of the printer
                - filename: Name of the file
                - display_name: Display name (same as filename)
                - file_size: Size in bytes
                - file_type: Type of file (.3mf, .gcode, etc.)
                - status: File status ('available', 'downloaded', etc.)
                - source: Always 'printer'
                - metadata: Additional metadata (None initially)
                - modified_time: Last modified time from printer

        Raises:
            Exception: If printer service is not available or discovery fails

        Example:
            >>> files = await discovery.get_printer_files("bambu_001")
            >>> print(f"Found {len(files)} files")
        """
        try:
            if not self.printer_service:
                logger.warning("Printer service not available for file discovery",
                             printer_id=printer_id)
                return []

            # Get files directly from printer via printer service
            printer_files = await self.printer_service.get_printer_files(printer_id)

            # Store/update files in database
            stored_files = []
            for file_info in printer_files:
                file_data = {
                    'id': f"{printer_id}_{file_info['filename']}",
                    'printer_id': printer_id,
                    'filename': file_info['filename'],
                    'display_name': file_info['filename'],
                    'file_size': file_info.get('size', 0),
                    'file_type': self._get_file_type(file_info['filename']),
                    'status': 'available',
                    'source': 'printer',
                    'metadata': None,
                    'modified_time': file_info.get('modified')
                }

                # Store in database
                await self.file_repo.create(file_data)
                stored_files.append(file_data)

            logger.info("Discovered printer files",
                       printer_id=printer_id,
                       count=len(stored_files))

            # Emit discovery event
            await self.event_service.emit_event("files_discovered", {
                "printer_id": printer_id,
                "files": stored_files,
                "count": len(stored_files),
                "timestamp": datetime.now().isoformat()
            })

            return stored_files

        except Exception as e:
            logger.error("Failed to discover printer files",
                        printer_id=printer_id,
                        error=str(e))
            # Fallback to database files
            db_files = await self.file_repo.list(
                printer_id=printer_id,
                source='printer'
            )
            return [dict(f) for f in db_files]

    async def sync_printer_files(self, printer_id: str) -> Dict[str, Any]:
        """
        Synchronize files from a specific printer.

        This method:
        1. Discovers current files on the printer
        2. Compares with database records
        3. Marks removed files as unavailable
        4. Adds new files to database

        Args:
            printer_id: ID of the printer to sync

        Returns:
            Dictionary with sync results:
                - success: True if sync completed without errors
                - total_files: Total number of files on printer
                - added_files: Number of new files discovered
                - removed_files: Number of files marked as unavailable
                - sync_time: ISO format timestamp of sync
                - error: Error message if success is False

        Example:
            >>> result = await discovery.sync_printer_files("prusa_001")
            >>> print(f"Synced {result['total_files']} files")
        """
        try:
            logger.info("Starting file sync for printer", printer_id=printer_id)

            # Discover current files on printer
            current_files = await self.get_printer_files(printer_id)

            # Get existing files in database for this printer
            existing_files = await self.file_repo.list(
                printer_id=printer_id,
                source='printer'
            )
            existing_filenames = {f['filename'] for f in existing_files}
            current_filenames = {f['filename'] for f in current_files}

            # Find files that no longer exist on printer
            removed_files = existing_filenames - current_filenames
            added_files = current_filenames - existing_filenames

            # Remove files that no longer exist
            removed_count = 0
            for file_data in existing_files:
                if file_data['filename'] in removed_files:
                    # Mark as unavailable rather than deleting
                    await self.file_repo.update(file_data['id'], {
                        'status': 'unavailable'
                    })
                    removed_count += 1

            logger.info("File sync completed",
                       printer_id=printer_id,
                       total_files=len(current_files),
                       added_files=len(added_files),
                       removed_files=removed_count)

            result = {
                "success": True,
                "total_files": len(current_files),
                "added_files": len(added_files),
                "removed_files": removed_count,
                "sync_time": datetime.now().isoformat()
            }

            # Emit sync complete event
            await self.event_service.emit_event("file_sync_complete", {
                "printer_id": printer_id,
                **result
            })

            return result

        except Exception as e:
            logger.error("File sync failed", printer_id=printer_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "sync_time": datetime.now().isoformat()
            }

    async def discover_printer_files(self, printer_id: str) -> List[Dict[str, Any]]:
        """
        Discover files on a specific printer for background discovery task.

        This method is called by the background file discovery task every 5 minutes.
        It discovers files on the printer and stores them in the database.

        Args:
            printer_id: The ID of the printer to discover files for

        Returns:
            List of file info dictionaries with:
                - filename: Name of the file
                - file_size: Size in bytes
                - file_type: Type of file
                - id: Unique file identifier
                - status: File status ('available', etc.)

        Example:
            >>> discovered = await discovery.discover_printer_files("bambu_001")
            >>> for file in discovered:
            ...     print(f"Found: {file['filename']}")
        """
        try:
            logger.info("Starting file discovery for printer", printer_id=printer_id)

            # Use existing get_printer_files method which discovers and stores files
            stored_files = await self.get_printer_files(printer_id)

            # Convert to format expected by background task
            discovered_files = []
            for file_data in stored_files:
                discovered_files.append({
                    'filename': file_data['filename'],
                    'file_size': file_data.get('file_size'),
                    'file_type': file_data.get('file_type'),
                    'id': file_data['id'],
                    'status': file_data.get('status', 'available')
                })

            logger.info("File discovery completed",
                       printer_id=printer_id,
                       files_found=len(discovered_files))

            return discovered_files

        except Exception as e:
            logger.error("File discovery failed",
                        printer_id=printer_id,
                        error=str(e))
            return []

    async def find_file_by_name(
        self,
        filename: str,
        printer_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find file by filename, optionally filtering by printer_id.

        Searches the database for a file matching the given filename.
        If printer_id is provided, only searches files from that printer.

        Args:
            filename: Name of the file to find
            printer_id: Optional printer ID to filter by

        Returns:
            File dictionary if found, None otherwise

        Example:
            >>> file = await discovery.find_file_by_name("model.3mf", "bambu_001")
            >>> if file:
            ...     print(f"Found file: {file['id']}")
        """
        try:
            # Check printer files in database first
            files = await self.file_repo.list(printer_id=printer_id)
            for file_data in files:
                if file_data.get('filename') == filename:
                    return dict(file_data)

            return None

        except Exception as e:
            logger.error("Failed to find file by name",
                        filename=filename,
                        printer_id=printer_id,
                        error=str(e))
            return None

    def _get_file_type(self, filename: str) -> str:
        """
        Get file type from filename extension.

        Args:
            filename: Name of the file

        Returns:
            File type string (e.g., '3mf', 'gcode', 'stl', 'unknown')

        Example:
            >>> discovery._get_file_type("model.3mf")
            '3mf'
            >>> discovery._get_file_type("print.gcode")
            'gcode'
        """
        ext = Path(filename).suffix.lower()
        type_map = {
            '.stl': 'stl',
            '.3mf': '3mf',
            '.obj': 'obj',
            '.gcode': 'gcode',
            '.bgcode': 'bgcode',
            '.ply': 'ply'
        }
        return type_map.get(ext, 'unknown')

    def set_printer_service(self, printer_service) -> None:
        """
        Set printer service dependency.

        This allows for late binding of the printer service to resolve
        circular dependency issues.

        Args:
            printer_service: PrinterService instance
        """
        self.printer_service = printer_service
        logger.debug("Printer service set in FileDiscoveryService")
