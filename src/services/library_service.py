"""
Library Service for unified file management.
Handles checksum-based file identification, deduplication, and organization.
"""

import hashlib
import asyncio
import shutil
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from uuid import uuid4
import json

import structlog

logger = structlog.get_logger()


class LibraryService:
    """Service for managing the unified file library."""

    def __init__(self, database, config_service, event_service):
        """
        Initialize library service.

        Args:
            database: Database instance for storage
            config_service: Configuration service
            event_service: Event service for notifications
        """
        self.database = database
        self.config_service = config_service
        self.event_service = event_service

        # Get library configuration
        self.library_path = Path(getattr(config_service.settings, 'library_path', '/app/data/library'))
        self.enabled = getattr(config_service.settings, 'library_enabled', False)
        self.auto_organize = getattr(config_service.settings, 'library_auto_organize', True)
        self.auto_extract_metadata = getattr(config_service.settings, 'library_auto_extract_metadata', True)
        self.checksum_algorithm = getattr(config_service.settings, 'library_checksum_algorithm', 'sha256')
        self.preserve_originals = getattr(config_service.settings, 'library_preserve_originals', True)

        # Processing state
        self._processing_files = set()  # Track files currently being processed

        logger.info("Library service initialized",
                   library_path=str(self.library_path),
                   enabled=self.enabled)

    async def initialize(self):
        """Initialize library folders and verify configuration."""
        if not self.enabled:
            logger.info("Library system disabled")
            return

        try:
            # Create library folder structure
            folders = [
                self.library_path,
                self.library_path / 'models',
                self.library_path / 'printers',
                self.library_path / 'uploads',
                self.library_path / '.metadata' / 'thumbnails',
                self.library_path / '.metadata' / 'previews',
            ]

            for folder in folders:
                folder.mkdir(parents=True, exist_ok=True)
                logger.debug("Created library folder", path=str(folder))

            # Verify write permissions
            test_file = self.library_path / '.write_test'
            try:
                test_file.write_text('test')
                test_file.unlink()
                logger.info("Library write permissions verified")
            except Exception as e:
                logger.error("Library write permission test failed", error=str(e))
                raise

            logger.info("Library initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize library", error=str(e))
            raise

    async def calculate_checksum(self, file_path: Path, algorithm: str = None) -> str:
        """
        Calculate file checksum.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm (sha256, md5)

        Returns:
            Hexadecimal checksum string
        """
        if algorithm is None:
            algorithm = self.checksum_algorithm

        # Run checksum calculation in thread pool to avoid blocking
        return await asyncio.to_thread(self._calculate_checksum_sync, file_path, algorithm)

    def _calculate_checksum_sync(self, file_path: Path, algorithm: str) -> str:
        """Synchronous checksum calculation."""
        if algorithm == 'sha256':
            hasher = hashlib.sha256()
        elif algorithm == 'md5':
            hasher = hashlib.md5()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        file_size = file_path.stat().st_size
        chunk_size = 8192

        with open(file_path, 'rb') as f:
            bytes_read = 0
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
                bytes_read += len(chunk)

                # Log progress for large files
                if file_size > 10 * 1024 * 1024:  # >10MB
                    if bytes_read % (1024 * 1024) == 0:  # Every 1MB
                        progress = (bytes_read / file_size) * 100
                        logger.debug("Checksum progress",
                                   file=str(file_path),
                                   progress=f"{progress:.1f}%")

        return hasher.hexdigest()

    def get_library_path_for_file(self, checksum: str, source_type: str,
                                   original_filename: str = None, printer_name: str = None) -> Path:
        """
        Get library storage path for a file based on source type.

        Args:
            checksum: File checksum
            source_type: Source type (printer, watch_folder, upload)
            original_filename: Original filename (optional)
            printer_name: Printer name (required for printer source type)

        Returns:
            Path object for library storage location
        """
        # Use first 2 characters of checksum for sharding (scalability)
        shard = checksum[:2]

        if source_type == 'watch_folder':
            # Store in models/{shard}/ with checksum + extension
            if original_filename:
                ext = Path(original_filename).suffix
            else:
                ext = ''
            return self.library_path / 'models' / shard / f"{checksum}{ext}"

        elif source_type == 'printer':
            # Store in printers/{printer_name}/{shard}/ with checksum + original filename
            if not printer_name:
                printer_name = 'unknown'
            if original_filename:
                return self.library_path / 'printers' / printer_name / shard / f"{checksum}_{original_filename}"
            else:
                return self.library_path / 'printers' / printer_name / shard / f"{checksum}"

        elif source_type == 'upload':
            # Store in uploads/{shard}/ with checksum + extension
            if original_filename:
                ext = Path(original_filename).suffix
            else:
                ext = ''
            return self.library_path / 'uploads' / shard / f"{checksum}{ext}"

        else:
            raise ValueError(f"Unknown source type: {source_type}")

    async def add_file_to_library(self, source_path: Path, source_info: Dict[str, Any],
                                  copy_file: bool = True, calculate_hash: bool = True) -> Dict[str, Any]:
        """
        Add a file to the library.

        Args:
            source_path: Path to source file
            source_info: Dictionary with source information:
                - type: 'printer', 'watch_folder', 'upload'
                - printer_id: ID of printer (for printer source)
                - printer_name: Name of printer (for printer source)
                - folder_path: Path to watch folder (for watch_folder source)
                - relative_path: Relative path within folder
            copy_file: Whether to copy file to library (False to move)
            calculate_hash: Whether to calculate checksum (False if already known)

        Returns:
            Dictionary with file information
        """
        try:
            if not source_path.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            # Validate source info
            source_type = source_info.get('type')
            if source_type not in ['printer', 'watch_folder', 'upload']:
                raise ValueError(f"Invalid source type: {source_type}")

            # Calculate checksum
            if calculate_hash:
                logger.info("Calculating checksum", file=str(source_path))
                checksum = await self.calculate_checksum(source_path)
                logger.info("Checksum calculated", file=str(source_path), checksum=checksum[:16])
            else:
                checksum = source_info.get('checksum')
                if not checksum:
                    raise ValueError("Checksum required when calculate_hash=False")

            # Check if file already exists in library
            existing_file = await self.get_file_by_checksum(checksum)

            if existing_file:
                logger.info("File already in library", checksum=checksum[:16])

                # Add new source to existing file
                await self.add_file_source(checksum, source_info)

                # Update file access time
                await self.database.update_library_file(checksum, {
                    'last_accessed': datetime.now().isoformat()
                })

                return existing_file

            # File is new - add to library
            logger.info("Adding new file to library", checksum=checksum[:16])

            # Check disk space before copying
            file_size = source_path.stat().st_size
            required_space = file_size * 1.5  # 50% buffer for safety
            disk_usage = shutil.disk_usage(self.library_path)
            if disk_usage.free < required_space:
                free_gb = disk_usage.free / (1024**3)
                required_gb = required_space / (1024**3)
                raise IOError(
                    f"Insufficient disk space: {free_gb:.2f} GB free, "
                    f"need {required_gb:.2f} GB for this file"
                )

            # Determine library path
            printer_name = source_info.get('printer_name', 'unknown')
            library_path = self.get_library_path_for_file(
                checksum,
                source_type,
                source_path.name,
                printer_name=printer_name
            )

            # Create parent directory
            library_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy or move file to library
            if copy_file:
                logger.debug("Copying file to library",
                           source=str(source_path),
                           dest=str(library_path))
                await asyncio.to_thread(shutil.copy2, source_path, library_path)
            else:
                logger.debug("Moving file to library",
                           source=str(source_path),
                           dest=str(library_path))
                await asyncio.to_thread(shutil.move, source_path, library_path)

            # Verify checksum after copy/move
            verify_checksum = await self.calculate_checksum(library_path)
            if verify_checksum != checksum:
                # Checksum mismatch - delete and raise error
                library_path.unlink()
                raise ValueError(f"Checksum mismatch after copy/move: {verify_checksum} != {checksum}")

            # Get file info
            file_stat = library_path.stat()
            file_size = file_stat.st_size
            file_type = library_path.suffix.lower()

            # Create library file record
            file_id = str(uuid4())

            # Prepare sources array
            sources = [source_info]

            # Create search index (filename + tags)
            search_index = source_path.name.lower()

            file_record = {
                'id': file_id,
                'checksum': checksum,
                'filename': source_path.name,
                'display_name': source_path.name,
                'library_path': str(library_path.relative_to(self.library_path)),
                'file_size': file_size,
                'file_type': file_type,
                'sources': json.dumps(sources),
                'status': 'available',
                'added_to_library': datetime.now().isoformat(),
                'last_modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'search_index': search_index,
            }

            # Save to database (handle race condition with UNIQUE constraint)
            try:
                success = await self.database.create_library_file(file_record)

                if not success:
                    # Database insert failed - likely race condition
                    # Check if file now exists (another process added it)
                    existing_file = await self.get_file_by_checksum(checksum)
                    if existing_file:
                        logger.info("File was added by another process, adding source",
                                   checksum=checksum[:16])
                        # Delete our copy and add source to existing record
                        library_path.unlink()
                        await self.add_file_source(checksum, source_info)
                        return existing_file
                    else:
                        # Insert failed for other reason
                        library_path.unlink()
                        raise RuntimeError("Failed to create library file record")

            except Exception as e:
                # Clean up on any database error
                if library_path.exists():
                    library_path.unlink()
                logger.error("Database error while adding file", checksum=checksum[:16], error=str(e))
                raise

            # Add source to junction table
            await self.add_file_source(checksum, source_info)

            logger.info("File added to library successfully",
                       checksum=checksum[:16],
                       library_path=str(library_path))

            # Emit event
            await self.event_service.emit_event('library_file_added', {
                'checksum': checksum,
                'filename': source_path.name,
                'file_size': file_size,
                'source_type': source_type
            })

            # Schedule metadata extraction if enabled
            if self.auto_extract_metadata:
                asyncio.create_task(self._extract_metadata_async(file_id, checksum))

            return file_record

        except Exception as e:
            logger.error("Failed to add file to library",
                        file=str(source_path),
                        error=str(e))
            raise

    async def get_file_by_checksum(self, checksum: str) -> Optional[Dict[str, Any]]:
        """
        Get file from library by checksum.

        Args:
            checksum: File checksum

        Returns:
            File record or None if not found
        """
        return await self.database.get_library_file_by_checksum(checksum)

    async def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file from library by ID.

        Args:
            file_id: File database ID

        Returns:
            File record or None if not found
        """
        return await self.database.get_library_file(file_id)

    async def list_files(self, filters: Dict[str, Any] = None,
                        page: int = 1, limit: int = 50) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        List files in library with filters and pagination.

        Args:
            filters: Filter dictionary:
                - source_type: Filter by source type
                - file_type: Filter by file extension
                - status: Filter by status
                - search: Search query (filename)
                - has_thumbnail: Filter by thumbnail presence
                - has_metadata: Filter by metadata presence
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (files list, pagination info)
        """
        return await self.database.list_library_files(filters, page, limit)

    async def add_file_source(self, checksum: str, source_info: Dict[str, Any]):
        """
        Add a source to an existing file.

        Args:
            checksum: File checksum
            source_info: Source information dictionary
        """
        # Update sources JSON array in main record
        file_record = await self.get_file_by_checksum(checksum)
        if not file_record:
            raise ValueError(f"File not found: {checksum}")

        # Parse existing sources
        sources = json.loads(file_record.get('sources', '[]'))

        # Check if source already exists
        source_key = f"{source_info.get('type')}:{source_info.get('printer_id') or source_info.get('folder_path')}"
        existing_keys = [f"{s.get('type')}:{s.get('printer_id') or s.get('folder_path')}" for s in sources]

        if source_key not in existing_keys:
            # Add discovered_at if not present
            if 'discovered_at' not in source_info:
                source_info['discovered_at'] = datetime.now().isoformat()

            sources.append(source_info)

            # Update database
            await self.database.update_library_file(checksum, {
                'sources': json.dumps(sources)
            })

            logger.info("Added source to file", checksum=checksum[:16], source_type=source_info.get('type'))

        # Add to junction table
        await self.database.create_library_file_source({
            'file_checksum': checksum,
            'source_type': source_info.get('type'),
            'source_id': source_info.get('printer_id') or source_info.get('folder_path'),
            'source_name': source_info.get('printer_name') or source_info.get('folder_path'),
            'original_path': source_info.get('original_path', ''),
            'original_filename': source_info.get('original_filename', ''),
            'discovered_at': source_info.get('discovered_at', datetime.now().isoformat()),
            'metadata': json.dumps(source_info)
        })

    async def delete_file(self, checksum: str, delete_physical: bool = True) -> bool:
        """
        Delete file from library.

        Args:
            checksum: File checksum
            delete_physical: Whether to delete physical file

        Returns:
            True if successful
        """
        try:
            file_record = await self.get_file_by_checksum(checksum)
            if not file_record:
                logger.warning("File not found for deletion", checksum=checksum[:16])
                return False

            # Delete physical file if requested
            if delete_physical:
                library_path = self.library_path / file_record['library_path']
                if library_path.exists():
                    library_path.unlink()
                    logger.info("Deleted physical file", path=str(library_path))

            # Delete from database
            await self.database.delete_library_file(checksum)
            await self.database.delete_library_file_sources(checksum)

            logger.info("File deleted from library", checksum=checksum[:16])

            # Emit event
            await self.event_service.emit_event('library_file_deleted', {
                'checksum': checksum,
                'filename': file_record.get('filename')
            })

            return True

        except Exception as e:
            logger.error("Failed to delete file from library", checksum=checksum[:16], error=str(e))
            return False

    async def get_library_statistics(self) -> Dict[str, Any]:
        """
        Get library statistics.

        Returns:
            Statistics dictionary
        """
        return await self.database.get_library_stats()

    async def _extract_metadata_async(self, file_id: str, checksum: str):
        """
        Asynchronously extract metadata from file.
        Internal method called after file is added to library.

        Args:
            file_id: File database ID
            checksum: File checksum
        """
        try:
            # Prevent duplicate processing
            if checksum in self._processing_files:
                logger.debug("File already being processed", checksum=checksum[:16])
                return

            self._processing_files.add(checksum)

            # Update status to processing
            await self.database.update_library_file(checksum, {
                'status': 'processing'
            })

            # Get file record
            file_record = await self.get_file_by_checksum(checksum)
            if not file_record:
                return

            library_path = self.library_path / file_record['library_path']

            # Use existing metadata extraction service
            # This will be integrated with BambuParser and ThreeMFAnalyzer
            # For now, just mark as ready

            logger.info("Metadata extraction started", checksum=checksum[:16])

            # TODO: Call metadata extraction service here
            # await self.metadata_service.extract_metadata(library_path, file_id)

            # Update status to ready
            await self.database.update_library_file(checksum, {
                'status': 'ready',
                'last_analyzed': datetime.now().isoformat()
            })

            logger.info("Metadata extraction completed", checksum=checksum[:16])

        except Exception as e:
            logger.error("Metadata extraction failed", checksum=checksum[:16], error=str(e))
            await self.database.update_library_file(checksum, {
                'status': 'error',
                'error_message': str(e)
            })

        finally:
            self._processing_files.discard(checksum)

    async def reprocess_file(self, checksum: str) -> bool:
        """
        Reprocess file metadata.

        Args:
            checksum: File checksum

        Returns:
            True if reprocessing started successfully
        """
        try:
            file_record = await self.get_file_by_checksum(checksum)
            if not file_record:
                logger.warning("File not found for reprocessing", checksum=checksum[:16])
                return False

            # Schedule metadata extraction
            asyncio.create_task(self._extract_metadata_async(file_record['id'], checksum))

            logger.info("File reprocessing scheduled", checksum=checksum[:16])
            return True

        except Exception as e:
            logger.error("Failed to schedule reprocessing", checksum=checksum[:16], error=str(e))
            return False
