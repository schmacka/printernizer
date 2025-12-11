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

from src.database.repositories import LibraryRepository
from src.services.bambu_parser import BambuParser
from src.services.stl_analyzer import STLAnalyzer
from src.services.preview_render_service import PreviewRenderService
from src.services.filament_colors import (
    extract_colors_from_filament_ids,
    extract_color_from_name,
    get_primary_color,
    format_color_list
)
import base64

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
        self.library_repo = LibraryRepository(database._connection)
        self.config_service = config_service
        self.event_service = event_service

        # Get library configuration
        self.library_path = Path(getattr(config_service.settings, 'library_path', '/app/data/library'))
        self.enabled = getattr(config_service.settings, 'library_enabled', True)
        self.auto_organize = getattr(config_service.settings, 'library_auto_organize', True)
        self.auto_extract_metadata = getattr(config_service.settings, 'library_auto_extract_metadata', True)
        self.checksum_algorithm = getattr(config_service.settings, 'library_checksum_algorithm', 'sha256')
        self.preserve_originals = getattr(config_service.settings, 'library_preserve_originals', True)

        # Processing state
        self._processing_files = set()  # Track files currently being processed

        # Initialize metadata extraction parsers
        self.bambu_parser = BambuParser()
        self.stl_analyzer = STLAnalyzer()

        # Initialize preview rendering service for thumbnail generation
        cache_dir = self.library_path / '.metadata' / 'preview-cache'
        self.preview_service = PreviewRenderService(cache_dir=str(cache_dir))

        logger.info("Library service initialized",
                   library_path=str(self.library_path),
                   enabled=self.enabled)

    async def initialize(self) -> None:
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
        Uses natural filenames without checksum-based sharding.

        Args:
            checksum: File checksum (not used in path anymore)
            source_type: Source type (printer, watch_folder, upload)
            original_filename: Original filename (required)
            printer_name: Printer name (required for printer source type)

        Returns:
            Path object for library storage location
        """
        if not original_filename:
            raise ValueError("original_filename is required for natural filename storage")

        if source_type == 'watch_folder':
            # Store in models/ with original filename
            return self.library_path / 'models' / original_filename

        elif source_type == 'printer':
            # Store in printers/{printer_name}/ with original filename
            if not printer_name:
                printer_name = 'unknown'
            return self.library_path / 'printers' / printer_name / original_filename

        elif source_type == 'upload':
            # Store in uploads/ with original filename
            return self.library_path / 'uploads' / original_filename

        else:
            raise ValueError(f"Unknown source type: {source_type}")

    def _resolve_filename_conflict(self, target_path: Path) -> Path:
        """
        Resolve filename conflict by appending _1, _2, etc.

        Args:
            target_path: Desired target path

        Returns:
            Resolved path that doesn't conflict with existing files
        """
        if not target_path.exists():
            return target_path

        # File exists, need to append counter
        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent

        counter = 1
        while True:
            new_filename = f"{stem}_{counter}{suffix}"
            new_path = parent / new_filename
            if not new_path.exists():
                logger.info("Resolved filename conflict",
                           original=target_path.name,
                           resolved=new_filename)
                return new_path
            counter += 1

            # Safety check to prevent infinite loop
            if counter > 1000:
                raise RuntimeError(f"Too many filename conflicts for {target_path.name}")

    async def _check_duplicate(self, checksum: str) -> Optional[Dict[str, Any]]:
        """
        Check if a file with this checksum already exists (duplicate detection).

        Args:
            checksum: File checksum to check

        Returns:
            Original file record if duplicate found, None otherwise
        """
        existing_file = await self.get_file_by_checksum(checksum)
        return existing_file

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

            # Check for duplicate (same checksum = same content)
            original_file = await self._check_duplicate(checksum)
            is_duplicate = original_file is not None
            duplicate_of_checksum = original_file['checksum'] if is_duplicate else None

            if is_duplicate:
                logger.info("Duplicate file detected",
                           checksum=checksum[:16],
                           original=original_file['filename'])
                # Continue to add the duplicate with a different filename
                # (will be handled by filename conflict resolution)

            # Determine if this is a new unique file or a duplicate
            if not is_duplicate:
                logger.info("Adding new unique file to library", checksum=checksum[:16])
            else:
                logger.info("Adding duplicate file to library",
                           checksum=checksum[:16],
                           duplicate_of=original_file['filename'])

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

            # Determine library path with natural filename
            printer_name = source_info.get('printer_name', 'unknown')
            desired_library_path = self.get_library_path_for_file(
                checksum,
                source_type,
                source_path.name,
                printer_name=printer_name
            )

            # Resolve filename conflicts (append _1, _2, etc. if needed)
            library_path = self._resolve_filename_conflict(desired_library_path)

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
            # For duplicates, we use a modified checksum to bypass UNIQUE constraint
            # The modified checksum is checksum + "-" + UUID to make it unique
            # The real checksum is stored in duplicate_of_checksum
            if is_duplicate:
                # Generate a unique "fake" checksum for database constraint
                unique_checksum = f"{checksum}-{str(uuid4())}"
            else:
                unique_checksum = checksum

            file_id = str(uuid4())

            # Prepare sources array
            sources = [source_info]

            # Create search index (filename + tags)
            search_index = source_path.name.lower()

            file_record = {
                'id': file_id,
                'checksum': unique_checksum,  # Unique for database, may be modified for duplicates
                'filename': library_path.name,  # Use actual filename (may have _1, _2 suffix)
                'display_name': library_path.name,
                'library_path': str(library_path.relative_to(self.library_path)),
                'file_size': file_size,
                'file_type': file_type,
                'sources': json.dumps(sources),
                'status': 'available',
                'added_to_library': datetime.now().isoformat(),
                'last_modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'search_index': search_index,
                'is_duplicate': is_duplicate,
                'duplicate_of_checksum': duplicate_of_checksum or checksum,  # Always store original checksum
                'duplicate_count': 0,  # Will be updated if other duplicates are added later
            }

            # Save to database (handle race condition with UNIQUE constraint)
            try:
                success = await self.library_repo.create_file(file_record)

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

            # Add source to junction table (use unique_checksum which is what's in the database)
            await self.add_file_source(unique_checksum, source_info)

            # If this is a duplicate, increment the duplicate_count on the original file
            if is_duplicate and original_file:
                current_count = original_file.get('duplicate_count', 0)
                await self.library_repo.update_file(original_file['checksum'], {
                    'duplicate_count': current_count + 1
                })
                logger.info("Incremented duplicate count on original file",
                           original_checksum=original_file['checksum'][:16],
                           new_count=current_count + 1)

            logger.info("File added to library successfully",
                       checksum=checksum[:16],
                       library_path=str(library_path),
                       is_duplicate=is_duplicate)

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
        return await self.library_repo.get_file_by_checksum(checksum)

    async def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file from library by ID.

        Args:
            file_id: File database ID

        Returns:
            File record or None if not found
        """
        return await self.library_repo.get_file(file_id)

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
        return await self.library_repo.list_files(filters, page, limit)

    async def add_file_source(self, checksum: str, source_info: Dict[str, Any]) -> None:
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
            await self.library_repo.update_file(checksum, {
                'sources': json.dumps(sources)
            })

            logger.info("Added source to file", checksum=checksum[:16], source_type=source_info.get('type'))

        # Add to junction table
        await self.library_repo.create_file_source({
            'file_checksum': checksum,
            'source_type': source_info.get('type'),
            'source_id': source_info.get('printer_id') or source_info.get('folder_path'),
            'source_name': source_info.get('printer_name') or source_info.get('folder_path'),
            'manufacturer': source_info.get('manufacturer'),  # NEW: manufacturer field
            'printer_model': source_info.get('printer_model'),  # NEW: printer model field
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
            await self.library_repo.delete_file(checksum)
            await self.library_repo.delete_file_sources(checksum)

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
        return await self.library_repo.get_stats()

    def _map_parser_metadata_to_db(self, parser_metadata: Dict[str, Any], parser_thumbnails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Map BambuParser output to database fields.

        This function handles the complex task of mapping 40+ metadata fields from various
        slicer formats (BambuStudio, PrusaSlicer, OrcaSlicer) to a normalized database schema.
        It includes multiple fallback strategies, type conversions, and data format handling.

        Complexity: F-54 (Cyclomatic Complexity)
        - 40+ metadata fields with conditional mapping
        - Multiple field name variants per data point
        - Type conversion and validation for each field
        - Comma-separated value parsing
        - JSON array construction

        Args:
            parser_metadata: Metadata extracted by BambuParser from 3MF/GCODE files
            parser_thumbnails: List of thumbnail dictionaries with data, width, height, format

        Returns:
            Dictionary with database field names and values (normalized schema)

        Design Rationale:
            Different slicers use different field names for the same data:
            - BambuStudio: 'fill_density', 'wall_loops', 'outer_wall_speed'
            - PrusaSlicer: 'infill_density', 'perimeters', 'print_speed'
            - This function normalizes these variations into consistent DB fields

        Performance Note:
            O(n) where n = number of metadata fields (~40-50)
            Runs once per file import, not performance-critical
        """
        db_fields = {}

        # ==================== PHYSICAL PROPERTIES ====================
        # Extract model dimensions in millimeters
        # Different slicers report dimensions differently:
        # - Some use model_width/depth/height directly from STL bounding box
        # - Others use max_z_height from actual print path
        # Priority: explicit dimensions > calculated from print path

        if 'model_width' in parser_metadata:
            db_fields['model_width'] = float(parser_metadata['model_width'])
        if 'model_depth' in parser_metadata:
            db_fields['model_depth'] = float(parser_metadata['model_depth'])
        if 'model_height' in parser_metadata:
            db_fields['model_height'] = float(parser_metadata['model_height'])

        # Fallback: Use max_z_height if model_height not available
        # max_z_height is more accurate as it reflects actual print height
        # (accounts for first layer height, raft, etc.)
        if 'max_z_height' in parser_metadata:
            db_fields['model_height'] = float(parser_metadata['max_z_height'])

        # ==================== PRINT SETTINGS ====================
        # Layer and nozzle settings affect print quality and time

        if 'layer_height' in parser_metadata:
            db_fields['layer_height'] = float(parser_metadata['layer_height'])
        if 'first_layer_height' in parser_metadata:
            # First layer often thicker for better bed adhesion
            db_fields['first_layer_height'] = float(parser_metadata['first_layer_height'])
        if 'nozzle_diameter' in parser_metadata:
            db_fields['nozzle_diameter'] = float(parser_metadata['nozzle_diameter'])

        # Wall count: Different field names across slicers
        # BambuStudio: 'wall_loops', PrusaSlicer: 'perimeters'
        if 'wall_loops' in parser_metadata:
            db_fields['wall_count'] = int(parser_metadata['wall_loops'])

        # Infill density: Critical for strength vs print time tradeoff
        # Field name varies: 'fill_density' (Bambu) vs 'infill_density' (Prusa)
        # Values can be percentage (0-100) or decimal (0-1) - parser normalizes to percentage
        if 'fill_density' in parser_metadata or 'infill_density' in parser_metadata:
            density = parser_metadata.get('fill_density') or parser_metadata.get('infill_density')
            db_fields['infill_density'] = float(density)

        if 'sparse_infill_pattern' in parser_metadata:
            # Pattern affects strength and print time: grid, gyroid, honeycomb, etc.
            db_fields['infill_pattern'] = parser_metadata['sparse_infill_pattern']

        # Support structures: Boolean in various formats
        # Input can be: "true"/"false", "1"/"0", "yes"/"no", or actual boolean
        # Normalize to integer (0/1) for database storage
        if 'support_used' in parser_metadata:
            support = parser_metadata['support_used']
            db_fields['support_used'] = 1 if str(support).lower() in ['true', '1', 'yes'] else 0

        # Temperature settings: Prefer initial layer temps (more accurate)
        # Initial layer temps often higher for bed adhesion
        # Fallback to general temps if initial layer not specified
        if 'nozzle_temperature_initial_layer' in parser_metadata or 'nozzle_temperature' in parser_metadata:
            temp = parser_metadata.get('nozzle_temperature_initial_layer') or parser_metadata.get('nozzle_temperature')
            db_fields['nozzle_temperature'] = int(temp)
        if 'bed_temperature_initial_layer' in parser_metadata or 'bed_temperature' in parser_metadata:
            temp = parser_metadata.get('bed_temperature_initial_layer') or parser_metadata.get('bed_temperature')
            db_fields['bed_temperature'] = int(temp)

        # Print speed: Affects quality vs time tradeoff
        # outer_wall_speed is more accurate (slowest speed = quality indicator)
        # Fallback to general print_speed if wall speed not specified
        if 'outer_wall_speed' in parser_metadata or 'print_speed' in parser_metadata:
            speed = parser_metadata.get('outer_wall_speed') or parser_metadata.get('print_speed')
            db_fields['print_speed'] = float(speed)

        if 'total_layer_count' in parser_metadata:
            # Total layers = height / layer_height (approximately)
            # Used for progress tracking during printing
            db_fields['total_layer_count'] = int(parser_metadata['total_layer_count'])

        # ==================== MATERIAL REQUIREMENTS ====================
        # Calculate material usage for cost estimation and inventory management

        # Filament weight: Critical for cost calculation
        # Field name varies: 'filament_used [g]' (Bambu) vs 'total_filament_weight' (Prusa)
        # IMPORTANT: Multi-material prints have comma-separated values (one per extruder)
        # Example: "15.5,8.3,0.0" = 15.5g extruder 1, 8.3g extruder 2, 0g extruder 3
        if 'filament_used [g]' in parser_metadata or 'total_filament_weight' in parser_metadata:
            weight = parser_metadata.get('filament_used [g]') or parser_metadata.get('total_filament_weight')

            # Handle multi-material prints: sum all extruder values
            # Skip empty values to handle trailing commas
            if isinstance(weight, str) and ',' in weight:
                weight = sum(float(x) for x in weight.split(',') if x)

            db_fields['total_filament_weight'] = float(weight)

        # Filament length: Used for spool tracking
        # Similar comma-separated handling for multi-material
        # Convert from mm to meters for database consistency
        if 'total_filament_length' in parser_metadata or 'total filament used [mm]' in parser_metadata:
            length = parser_metadata.get('total_filament_length') or parser_metadata.get('total filament used [mm]')

            # Multi-material: sum lengths from all extruders
            if isinstance(length, str) and ',' in length:
                length = sum(float(x) for x in length.split(',') if x)

            db_fields['filament_length'] = float(length) / 1000  # mm → meters

        # Material types: Store as JSON array for multi-material support
        # Format: semicolon-separated string → JSON array
        # Example: "PLA;PLA;PETG" → ["PLA", "PLA", "PETG"]
        if 'filament_type' in parser_metadata:
            types = parser_metadata['filament_type']
            if isinstance(types, str):
                # Split on semicolon, strip whitespace, filter empty strings
                types = [t.strip() for t in types.split(';') if t.strip()]
            db_fields['material_types'] = json.dumps(types)

        # Filament IDs and Colors: Extract color information from filament IDs
        # Uses mapping table for Bambu Lab filament IDs (GFL series)
        # Example: "GFL00;GFL02" → ["Black", "Red"]
        filament_colors = []

        if 'filament_ids' in parser_metadata:
            ids = parser_metadata['filament_ids']
            if isinstance(ids, str):
                ids = [i.strip() for i in ids.split(';') if i.strip()]
                # Extract colors from filament IDs using mapping table
                filament_colors = extract_colors_from_filament_ids(ids)

        # Fallback: Try to extract color from filename if no filament IDs
        # This helps with files from other slicers or manually named files
        if not filament_colors and 'filename' in parser_metadata:
            filename = parser_metadata['filename']
            detected_color = extract_color_from_name(filename)
            if detected_color:
                filament_colors = [detected_color]

        # Store extracted color information in database
        if filament_colors:
            # Store full color list as JSON array (supports multi-color prints)
            # Example: ["Black", "White", "Red"]
            db_fields['filament_colors'] = json.dumps(filament_colors)

            # Store primary (first/dominant) color for filtering and sorting
            # Simplifies queries like "show all red prints"
            primary_color = get_primary_color(filament_colors)
            if primary_color:
                db_fields['primary_color'] = primary_color

            # Store human-readable color string for UI display
            # Example: "Black & White" or "Red, Green & Blue"
            db_fields['color_display'] = format_color_list(filament_colors)

            logger.debug("Extracted filament colors",
                        colors=filament_colors,
                        primary=primary_color,
                        display=db_fields['color_display'])

        # ==================== COMPATIBILITY INFORMATION ====================
        # Track which printers/slicers created this file for troubleshooting

        # Compatible printers: List of printer models that can print this
        # Stored as JSON array for flexible querying
        if 'compatible_printers' in parser_metadata:
            db_fields['compatible_printers'] = json.dumps(parser_metadata['compatible_printers'].split(';'))

        # Slicer information: Extract name and version from generator string
        # Generator string format: "SlicerName Version.Number.Patch"
        # Examples:
        #   "BambuStudio 1.9.0"
        #   "PrusaSlicer 2.6.0"
        #   "OrcaSlicer 1.7.0-beta"
        # Useful for debugging slicer-specific issues
        if 'generator' in parser_metadata:
            generator = parser_metadata['generator']
            parts = generator.split()
            if len(parts) >= 1:
                db_fields['slicer_name'] = parts[0]
            if len(parts) >= 2:
                db_fields['slicer_version'] = parts[1]

        # Bed type: Different printer models support different bed surfaces
        # Examples: "Cool Plate", "Engineering Plate", "Textured PEI"
        # Affects first layer adhesion strategies
        if 'curr_bed_type' in parser_metadata:
            db_fields['bed_type'] = parser_metadata['curr_bed_type']

        # ==================== THUMBNAILS ====================
        # Embedded preview images for UI display
        # 3MF files can contain multiple thumbnail sizes

        if parser_thumbnails and len(parser_thumbnails) > 0:
            # Select largest thumbnail for best quality display
            # Thumbnails are sorted by pixel area (width × height)
            # Larger thumbnails provide better preview but increase file size
            largest_thumb = max(parser_thumbnails, key=lambda t: t['width'] * t['height'])

            db_fields['has_thumbnail'] = 1
            db_fields['thumbnail_data'] = largest_thumb['data']  # Base64 encoded PNG
            db_fields['thumbnail_width'] = largest_thumb['width']
            db_fields['thumbnail_height'] = largest_thumb['height']
            db_fields['thumbnail_format'] = largest_thumb['format']  # Usually "PNG"

        return db_fields

    def _map_stl_metadata_to_db(self, stl_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map STL analyzer output to database fields.

        Args:
            stl_metadata: Metadata extracted by STLAnalyzer

        Returns:
            Dictionary with database field names and values
        """
        db_fields = {}

        # Extract physical properties from STL analysis
        physical = stl_metadata.get('physical_properties', {})
        geometry = stl_metadata.get('geometry_info', {})
        quality = stl_metadata.get('quality_metrics', {})

        # Physical dimensions
        if 'model_width' in physical:
            db_fields['model_width'] = physical['model_width']
        if 'model_depth' in physical:
            db_fields['model_depth'] = physical['model_depth']
        if 'model_height' in physical:
            db_fields['model_height'] = physical['model_height']
        if 'model_volume' in physical:
            db_fields['model_volume'] = physical['model_volume']
        if 'surface_area' in physical:
            db_fields['surface_area'] = physical['surface_area']

        # Quality metrics
        if 'complexity_score' in quality:
            db_fields['complexity_score'] = quality['complexity_score']
        if 'difficulty_level' in quality:
            db_fields['difficulty_level'] = quality['difficulty_level']

        # Note: STL files don't have print settings or material info
        # Those would come from the slicer profile used later

        logger.debug("Mapped STL metadata to database fields",
                    fields_count=len(db_fields))

        return db_fields

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
            await self.library_repo.update_file(checksum, {
                'status': 'processing'
            })

            # Get file record
            file_record = await self.get_file_by_checksum(checksum)
            if not file_record:
                return

            library_path = self.library_path / file_record['library_path']
            file_type = file_record.get('file_type', '').lower()

            logger.info("Metadata extraction started",
                       checksum=checksum[:16],
                       file_type=file_type,
                       path=str(library_path))

            # Extract metadata using appropriate parser for file type
            metadata_fields = {}

            if file_type in ['3mf', 'gcode', 'bgcode', 'stl']:
                try:
                    # Parse file for metadata and thumbnails
                    parse_result = await self.bambu_parser.parse_file(str(library_path))

                    if parse_result['success']:
                        # Map parser output to database fields
                        metadata_fields = self._map_parser_metadata_to_db(
                            parse_result.get('metadata', {}),
                            parse_result.get('thumbnails', [])
                        )

                        logger.info("Metadata extracted from file parser",
                                   checksum=checksum[:16],
                                   fields_extracted=len(metadata_fields),
                                   has_thumbnail=metadata_fields.get('has_thumbnail', 0) == 1)

                        # Generate animated preview in background for 3D files with embedded thumbnails
                        if file_type in ['3mf'] and metadata_fields.get('has_thumbnail', 0) == 1:
                            try:
                                asyncio.create_task(
                                    self.preview_service.get_or_generate_animated_preview(
                                        str(library_path),
                                        file_type,
                                        size=(200, 200)
                                    )
                                )
                                logger.debug("Started animated preview generation for 3MF in background",
                                           checksum=checksum[:16])
                            except Exception as e:
                                logger.warning("Failed to start animated preview generation for 3MF",
                                             checksum=checksum[:16],
                                             error=str(e))
                    else:
                        logger.warning("File parser extraction failed",
                                     checksum=checksum[:16],
                                     error=parse_result.get('error'))

                    # For STL files, also extract geometric metadata using STL analyzer
                    if file_type == 'stl':
                        try:
                            stl_result = await self.stl_analyzer.analyze_file(library_path)

                            if stl_result['success']:
                                # Extract and merge STL-specific metadata
                                stl_fields = self._map_stl_metadata_to_db(stl_result)
                                metadata_fields.update(stl_fields)

                                logger.info("STL geometric metadata extracted",
                                           checksum=checksum[:16],
                                           stl_fields_added=len(stl_fields))
                            else:
                                logger.warning("STL analysis failed",
                                             checksum=checksum[:16],
                                             error=stl_result.get('error'))
                        except Exception as e:
                            logger.error("Error during STL analysis",
                                       checksum=checksum[:16],
                                       error=str(e))

                    # Generate thumbnail if file needs it (STL, gcode without embedded thumbnails)
                    if parse_result.get('needs_generation', False) and not metadata_fields.get('has_thumbnail'):
                        try:
                            logger.info("Generating preview thumbnail",
                                      checksum=checksum[:16],
                                      file_type=file_type)

                            # Remove leading dot from file_type for preview service
                            file_type_clean = file_type.lstrip('.')

                            # Generate thumbnail (512x512 for library preview)
                            thumbnail_bytes = await self.preview_service.get_or_generate_preview(
                                str(library_path),
                                file_type_clean,
                                size=(512, 512)
                            )

                            if thumbnail_bytes:
                                # Convert to base64 for database storage
                                thumbnail_b64 = base64.b64encode(thumbnail_bytes).decode('utf-8')
                                metadata_fields['has_thumbnail'] = 1
                                metadata_fields['thumbnail_data'] = thumbnail_b64
                                metadata_fields['thumbnail_width'] = 512
                                metadata_fields['thumbnail_height'] = 512
                                metadata_fields['thumbnail_format'] = 'png'

                                logger.info("Preview thumbnail generated successfully",
                                          checksum=checksum[:16],
                                          size_bytes=len(thumbnail_bytes))

                                # Also generate animated preview in the background for 3D files
                                if file_type_clean.lower() in ['stl', '3mf']:
                                    try:
                                        asyncio.create_task(
                                            self.preview_service.get_or_generate_animated_preview(
                                                str(library_path),
                                                file_type_clean,
                                                size=(200, 200)
                                            )
                                        )
                                        logger.debug("Started animated preview generation in background",
                                                   checksum=checksum[:16])
                                    except Exception as e:
                                        logger.warning("Failed to start animated preview generation",
                                                     checksum=checksum[:16],
                                                     error=str(e))
                            else:
                                logger.warning("Preview thumbnail generation returned no data",
                                             checksum=checksum[:16])

                        except Exception as e:
                            logger.error("Error generating preview thumbnail",
                                       checksum=checksum[:16],
                                       error=str(e))

                except Exception as e:
                    logger.error("Error during metadata extraction",
                               checksum=checksum[:16],
                               error=str(e))
            else:
                logger.info("File type does not support metadata extraction",
                           checksum=checksum[:16],
                           file_type=file_type)

            # Update database with extracted metadata and mark as ready
            update_fields = {
                **metadata_fields,
                'status': 'ready',
                'last_analyzed': datetime.now().isoformat()
            }

            await self.library_repo.update_file(checksum, update_fields)

            logger.info("Metadata extraction completed",
                       checksum=checksum[:16],
                       metadata_count=len(metadata_fields))

        except Exception as e:
            logger.error("Metadata extraction failed", checksum=checksum[:16], error=str(e))
            await self.library_repo.update_file(checksum, {
                'status': 'error',
                'error_message': str(e)
            })

        finally:
            self._processing_files.discard(checksum)

    async def add_file_from_upload(self, file_id: str, file_path: str) -> Dict[str, Any]:
        """
        Add uploaded file to library.

        This method bridges the file upload service with the library system.
        It reads the uploaded file information from the files table and adds it
        to the unified library with proper source tracking.

        Args:
            file_id: ID of uploaded file in files table
            file_path: Path to the uploaded file

        Returns:
            Library file record

        Raises:
            FileNotFoundError: If uploaded file doesn't exist
            ValueError: If file_id not found in database
        """
        try:
            # Get file info from files table
            conn = self.database.get_connection()
            async with conn.execute(
                "SELECT * FROM files WHERE id = ?",
                (file_id,)
            ) as cursor:
                file_row = await cursor.fetchone()

            if not file_row:
                raise ValueError(f"File not found in database: {file_id}")

            # Convert row to dictionary
            file_info = dict(file_row)

            # Convert file path string to Path object
            source_path = Path(file_path)

            # Create source info for library
            source_info = {
                'type': 'upload',
                'source_id': 'manual_upload',
                'source_name': 'Manual Upload',
                'original_path': file_path,
                'original_filename': file_info.get('filename', source_path.name),
                'discovered_at': datetime.now().isoformat(),
                'metadata': file_info.get('metadata', '{}')
            }

            logger.info("Adding uploaded file to library",
                       file_id=file_id,
                       filename=source_path.name)

            # Add to library using main library method
            # copy_file=True to preserve original in uploads folder
            library_record = await self.add_file_to_library(
                source_path=source_path,
                source_info=source_info,
                copy_file=True,
                calculate_hash=True
            )

            logger.info("Uploaded file added to library successfully",
                       file_id=file_id,
                       library_checksum=library_record['checksum'][:16])

            return library_record

        except Exception as e:
            logger.error("Failed to add uploaded file to library",
                        file_id=file_id,
                        error=str(e))
            raise

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
