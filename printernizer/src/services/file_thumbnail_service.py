"""
File thumbnail service for extracting and processing file thumbnails.

This service is responsible for extracting thumbnails from 3D files (embedded),
downloading thumbnails from printer APIs, generating preview thumbnails,
and storing them in the database.

Part of FileService refactoring - Phase 2 technical debt reduction.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import os
import structlog

from src.database.database import Database
from src.database.repositories import FileRepository
from src.services.event_service import EventService
from src.services.bambu_parser import BambuParser
from src.services.preview_render_service import PreviewRenderService

logger = structlog.get_logger()


class FileThumbnailService:
    """
    Service for processing file thumbnails.

    This service handles:
    - Extracting embedded thumbnails from 3MF/G-code files
    - Downloading thumbnails from printer APIs (Prusa)
    - Generating preview thumbnails for files without embedded thumbnails
    - Storing thumbnail data in database
    - Tracking thumbnail processing status

    Thumbnail sources (in priority order):
    1. Embedded thumbnails in 3MF/G-code files
    2. Printer API thumbnails (Prusa)
    3. Generated preview thumbnails (STL, OBJ)

    Events Emitted:
    - file_thumbnails_processed: When thumbnails are successfully extracted
    - thumbnail_processing_failed: When processing fails

    Example:
        >>> thumbnail_svc = FileThumbnailService(database, event_service)
        >>> success = await thumbnail_svc.process_file_thumbnails(
        ...     "/downloads/model.3mf",
        ...     "bambu_001_model.3mf"
        ... )
    """

    def __init__(
        self,
        database: Database,
        event_service: EventService,
        printer_service=None
    ):
        """
        Initialize file thumbnail service.

        Args:
            database: Database instance for storing thumbnail data
            event_service: Event service for emitting processing events
            printer_service: Optional printer service for API thumbnail downloads
        """
        self.database = database
        self.file_repo = FileRepository(database._connection)
        self.event_service = event_service
        self.printer_service = printer_service
        self.bambu_parser = BambuParser()
        self.preview_render_service = PreviewRenderService()

        # Thumbnail processing status tracking
        self.thumbnail_processing_log: List[Dict[str, Any]] = []
        self.max_log_entries = 50  # Keep last 50 attempts

    async def process_file_thumbnails(
        self,
        file_path: str,
        file_id: str
    ) -> bool:
        """
        Process a file to extract thumbnails and metadata using Bambu parser.

        This method attempts to extract thumbnails in the following order:
        1. Embedded thumbnails from 3MF/G-code files (via BambuParser)
        2. Printer API thumbnails (for Prusa files without embedded thumbnails)
        3. Generated preview thumbnails (for STL, OBJ, etc.)

        Args:
            file_path: Local path to the file
            file_id: File ID in database

        Returns:
            True if processing was successful, False otherwise

        Example:
            >>> success = await thumbnail_svc.process_file_thumbnails(
            ...     "/downloads/bambu_001/model.3mf",
            ...     "bambu_001_model.3mf"
            ... )
            >>> if success:
            ...     print("Thumbnail extracted and stored")
        """
        start_time = datetime.utcnow()

        try:
            # Log the attempt
            self._log_thumbnail_processing(file_path, file_id, "started", None)

            if not os.path.exists(file_path):
                error_msg = "File not found for thumbnail processing"
                logger.warning(error_msg, file_path=file_path)
                self._log_thumbnail_processing(file_path, file_id, "failed", error_msg)
                return False

            # Parse file with Bambu parser
            parse_result = await self.bambu_parser.parse_file(file_path)

            if not parse_result['success']:
                error_msg = parse_result.get('error', 'Unknown parsing error')
                logger.info("File parsing failed or not applicable",
                           file_path=file_path,
                           error=error_msg)
                self._log_thumbnail_processing(file_path, file_id, "failed", error_msg)
                return False

            thumbnails = parse_result['thumbnails']
            metadata = parse_result['metadata']

            # Get best thumbnail for storage
            thumbnail_data = None
            thumbnail_width = None
            thumbnail_height = None
            thumbnail_format = None
            thumbnail_source = 'embedded'

            if thumbnails:
                # Prefer thumbnail closest to 200x200 for UI display
                best_thumbnail = self.bambu_parser.get_thumbnail_by_size(
                    thumbnails, (200, 200)
                )

                if best_thumbnail:
                    thumbnail_data = best_thumbnail['data']
                    thumbnail_width = best_thumbnail['width']
                    thumbnail_height = best_thumbnail['height']
                    thumbnail_format = best_thumbnail.get('format', 'png')
                    thumbnail_source = 'embedded'

            elif parse_result.get('needs_generation', False):
                # No embedded thumbnails - try Prusa printer API first, then generate preview
                thumbnail_result = await self._get_fallback_thumbnail(
                    file_id,
                    file_path
                )
                if thumbnail_result:
                    thumbnail_data = thumbnail_result['data']
                    thumbnail_width = thumbnail_result['width']
                    thumbnail_height = thumbnail_result['height']
                    thumbnail_format = thumbnail_result['format']
                    thumbnail_source = thumbnail_result['source']

            # Update file record with thumbnail and metadata
            update_data = {
                'has_thumbnail': thumbnail_data is not None,
                'thumbnail_data': thumbnail_data,
                'thumbnail_width': thumbnail_width,
                'thumbnail_height': thumbnail_height,
                'thumbnail_format': thumbnail_format,
                'thumbnail_source': thumbnail_source,
            }

            # Merge parsed metadata with existing metadata
            existing_file = await self.file_repo.get(file_id)
            if existing_file:
                existing_metadata = existing_file.get('metadata', {}) or {}
                merged_metadata = {**existing_metadata, **metadata}
                update_data['metadata'] = merged_metadata
            else:
                update_data['metadata'] = metadata

            success = await self.file_repo.update(file_id, update_data)

            if success:
                success_msg = f"Successfully processed {len(thumbnails)} thumbnails"
                logger.info("Successfully processed file thumbnails",
                           file_path=file_path,
                           file_id=file_id,
                           thumbnail_count=len(thumbnails),
                           has_thumbnail=len(thumbnails) > 0,
                           metadata_keys=list(metadata.keys()))

                self._log_thumbnail_processing(
                    file_path,
                    file_id,
                    "success",
                    f"{len(thumbnails)} thumbnails extracted"
                )

                # Emit file updated event
                await self.event_service.emit_event("file_thumbnails_processed", {
                    "file_id": file_id,
                    "file_path": file_path,
                    "thumbnail_count": len(thumbnails),
                    "has_thumbnail": len(thumbnails) > 0,
                    "metadata": metadata
                })

                return True
            else:
                error_msg = "Failed to update file with thumbnail data"
                logger.error(error_msg, file_id=file_id)
                self._log_thumbnail_processing(file_path, file_id, "failed", error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception during processing: {str(e)}"
            logger.error("Failed to process file thumbnails",
                        file_path=file_path,
                        file_id=file_id,
                        error=str(e))
            self._log_thumbnail_processing(file_path, file_id, "failed", error_msg)
            return False

    async def _get_fallback_thumbnail(
        self,
        file_id: str,
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get thumbnail using fallback methods.

        Tries in order:
        1. Download from Prusa printer API
        2. Generate preview thumbnail

        Args:
            file_id: File identifier (format: printer_id_filename)
            file_path: Path to the file

        Returns:
            Dict with thumbnail data, dimensions, format, and source, or None
        """
        # Try to download thumbnail from Prusa printer API first
        prusa_thumbnail = await self._download_prusa_thumbnail(file_id)
        if prusa_thumbnail:
            return prusa_thumbnail

        # If still no thumbnail, generate preview
        return await self._generate_preview_thumbnail(file_path)

    async def _download_prusa_thumbnail(
        self,
        file_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Download thumbnail from Prusa printer API.

        Args:
            file_id: File identifier (format: printer_id_filename)

        Returns:
            Dict with thumbnail data or None if download fails
        """
        if not self.printer_service:
            return None

        # Extract printer_id from file_id (format: printer_id_filename)
        if '_' not in file_id:
            return None

        try:
            import base64
            import struct

            printer_id = file_id.split('_', 1)[0]
            filename = file_id.split('_', 1)[1]

            logger.info("Attempting to download thumbnail from Prusa API",
                       file_id=file_id,
                       printer_id=printer_id,
                       filename=filename)

            # Get the Prusa printer instance
            printer_instance = self.printer_service.printers.get(printer_id)
            if not printer_instance or not hasattr(printer_instance, 'download_thumbnail'):
                return None

            prusa_thumb_bytes = await printer_instance.download_thumbnail(
                filename,
                size='l'
            )

            if not prusa_thumb_bytes:
                return None

            thumbnail_data = base64.b64encode(prusa_thumb_bytes).decode('utf-8')

            # Try to extract dimensions from PNG header
            width, height = 200, 200  # defaults
            if len(prusa_thumb_bytes) > 24 and prusa_thumb_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                try:
                    width, height = struct.unpack('>II', prusa_thumb_bytes[16:24])
                except (struct.error, ValueError) as e:
                    logger.debug("Could not parse PNG dimensions, using defaults",
                                error=str(e))

            logger.info("Successfully downloaded thumbnail from Prusa API",
                       size_bytes=len(prusa_thumb_bytes))

            return {
                'data': thumbnail_data,
                'width': width,
                'height': height,
                'format': 'png',
                'source': 'printer'
            }

        except Exception as e:
            logger.warning(
                "Failed to download thumbnail from Prusa API, will try generation",
                file_id=file_id,
                error=str(e)
            )
            return None

    async def _generate_preview_thumbnail(
        self,
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate preview thumbnail for file.

        Args:
            file_path: Path to the file

        Returns:
            Dict with thumbnail data or None if generation fails
        """
        try:
            import base64
            file_type = self._get_file_type(os.path.basename(file_path))

            logger.info("Generating preview thumbnail for file",
                       file_path=file_path,
                       file_type=file_type)

            preview_bytes = await self.preview_render_service.get_or_generate_preview(
                file_path,
                file_type,
                size=(200, 200)
            )

            if not preview_bytes:
                logger.warning("Preview generation returned no data",
                             file_path=file_path)
                return None

            thumbnail_data = base64.b64encode(preview_bytes).decode('utf-8')

            logger.info("Successfully generated preview thumbnail",
                       file_path=file_path)

            # Also generate animated preview in the background (non-blocking)
            # This will be cached and served via separate endpoint
            if file_type.lower() in ['stl', '3mf']:
                try:
                    # Generate animated preview asynchronously without blocking
                    asyncio.create_task(
                        self.preview_render_service.get_or_generate_animated_preview(
                            file_path,
                            file_type,
                            size=(200, 200)
                        )
                    )
                    logger.debug("Started animated preview generation in background",
                               file_path=file_path)
                except Exception as e:
                    logger.warning("Failed to start animated preview generation",
                                 file_path=file_path,
                                 error=str(e))

            return {
                'data': thumbnail_data,
                'width': 200,
                'height': 200,
                'format': 'png',
                'source': 'generated'
            }

        except Exception as e:
            logger.error("Failed to generate preview thumbnail",
                        file_path=file_path,
                        error=str(e))
            return None

    def _get_file_type(self, filename: str) -> str:
        """
        Get file type from filename extension.

        Args:
            filename: Name of the file

        Returns:
            File type string (e.g., '3mf', 'gcode', 'stl')
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

    def _log_thumbnail_processing(
        self,
        file_path: str,
        file_id: str,
        status: str,
        details: Optional[str] = None
    ) -> None:
        """
        Log a thumbnail processing attempt for debugging.

        Args:
            file_path: Path to the file
            file_id: File identifier
            status: Status ('started', 'success', 'failed')
            details: Optional details message
        """
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'file_path': file_path,
            'file_id': file_id,
            'status': status,  # 'started', 'success', 'failed'
            'details': details,
            'file_extension': Path(file_path).suffix.lower()
        }

        # Add to the beginning of the list (most recent first)
        self.thumbnail_processing_log.insert(0, entry)

        # Keep only the last N entries
        if len(self.thumbnail_processing_log) > self.max_log_entries:
            self.thumbnail_processing_log = self.thumbnail_processing_log[:self.max_log_entries]

    def get_thumbnail_processing_log(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent thumbnail processing log entries.

        Args:
            limit: Optional limit on number of entries to return

        Returns:
            List of log entry dictionaries (most recent first)

        Example:
            >>> log = thumbnail_svc.get_thumbnail_processing_log(limit=10)
            >>> for entry in log:
            ...     print(f"{entry['timestamp']}: {entry['status']} - {entry['file_path']}")
        """
        if limit:
            return self.thumbnail_processing_log[:limit]
        return self.thumbnail_processing_log

    def set_printer_service(self, printer_service) -> None:
        """
        Set printer service dependency.

        Allows for late binding of printer service to resolve circular dependencies.

        Args:
            printer_service: PrinterService instance
        """
        self.printer_service = printer_service
        logger.debug("Printer service set in FileThumbnailService")

    async def subscribe_to_download_events(self):
        """
        Subscribe to file download events to automatically process thumbnails.

        This should be called during service initialization to set up
        event-driven thumbnail processing after downloads complete.
        """
        async def _on_file_needs_thumbnail(data: Dict[str, Any]):
            """Handle file_needs_thumbnail_processing event."""
            file_id = data.get('file_id')
            file_path = data.get('file_path')

            if not file_id or not file_path:
                logger.warning(
                    "Invalid thumbnail processing event data",
                    data=data
                )
                return

            logger.info("Processing thumbnails from event",
                       file_id=file_id,
                       file_path=file_path)

            await self.process_file_thumbnails(file_path, file_id)

        self.event_service.subscribe(
            "file_needs_thumbnail_processing",
            _on_file_needs_thumbnail
        )

        logger.info("FileThumbnailService subscribed to download events")
