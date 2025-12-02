"""
Library repository for managing centralized 3D print file library operations.

This module provides data access methods for the centralized library that aggregates
files from all sources (printers, watch folders, URLs). It implements intelligent
deduplication using file checksums and tracks all source locations for each unique file.

Key Capabilities:
    - Centralized file library with checksum-based deduplication
    - Multi-source tracking (one file, multiple source locations)
    - Search indexing for fast file discovery
    - Duplicate detection and management
    - Comprehensive filtering and sorting
    - Library statistics and analytics
    - File source management (add/remove sources per file)

Database Schema:
    The library_files table stores deduplicated files:
    - id (TEXT PRIMARY KEY): Unique file identifier
    - checksum (TEXT UNIQUE): SHA256 checksum for deduplication
    - filename (TEXT): Original filename
    - display_name (TEXT): Human-readable name
    - library_path (TEXT): Path in library storage
    - file_size (INTEGER): File size in bytes
    - file_type (TEXT): File extension (.gcode, .3mf, .bgcode)
    - sources (TEXT): JSON array of source information
    - status (TEXT): File status (available, deleted)
    - added_to_library (DATETIME): When first added to library
    - last_modified (DATETIME): Last modification timestamp
    - search_index (TEXT): Searchable text (filename, tags, metadata)
    - is_duplicate (BOOLEAN): Whether file is a duplicate
    - duplicate_of_checksum (TEXT): Checksum of original if duplicate
    - duplicate_count (INTEGER): Number of duplicates found

    The library_file_sources table tracks file source locations:
    - id (INTEGER PRIMARY KEY AUTOINCREMENT): Unique source ID
    - file_checksum (TEXT): Foreign key to library_files.checksum
    - source_type (TEXT): Source type ('printer', 'watch_folder', 'url')
    - source_id (TEXT): Source identifier (printer ID, folder path, etc.)
    - source_path (TEXT): Original path at source
    - discovered_at (DATETIME): When source was discovered
    - last_seen (DATETIME): Last verification timestamp

    Indexes:
    - idx_library_files_checksum: Fast deduplication lookups (UNIQUE)
    - idx_library_files_file_type: Fast filtering by file type
    - idx_library_files_status: Fast filtering by status
    - idx_library_file_sources_checksum: Fast source lookups per file
    - idx_library_file_sources_type: Fast filtering by source type

Usage Examples:
    ```python
    from src.database.repositories import LibraryRepository
    import hashlib

    # Initialize
    library_repo = LibraryRepository(db.connection)

    # Add a file to library
    checksum = hashlib.sha256(file_content).hexdigest()
    file_data = {
        'id': 'lib_file_123',
        'checksum': checksum,
        'filename': 'model.3mf',
        'display_name': 'Calibration Cube',
        'library_path': '/library/models/model_abc123.3mf',
        'file_size': 1024000,
        'file_type': '.3mf',
        'sources': json.dumps([{
            'source_type': 'printer',
            'source_id': 'bambu_a1_001',
            'source_path': '/models/model.3mf'
        }]),
        'added_to_library': datetime.now().isoformat()
    }
    await library_repo.create_file(file_data)

    # Check for duplicate before adding
    existing = await library_repo.get_file_by_checksum(checksum)
    if existing:
        print(f"File already in library: {existing['display_name']}")
        # Add new source to existing file
        await library_repo.create_file_source({
            'file_checksum': checksum,
            'source_type': 'watch_folder',
            'source_id': '/watch_folders/prints',
            'source_path': '/watch_folders/prints/model.3mf',
            'discovered_at': datetime.now().isoformat()
        })
    else:
        # Add as new file
        await library_repo.create_file(file_data)

    # Search library
    search_results = await library_repo.list_files(
        filters={
            'file_type': '.3mf',
            'search_query': 'calibration'
        },
        limit=50
    )

    # Get files from specific source
    printer_files = await library_repo.list_files(
        filters={'source_type': 'printer'},
        sort_by='added_to_library',
        sort_direction='DESC'
    )

    # Get library statistics
    stats = await library_repo.get_stats()
    print(f"Total files: {stats['total_files']}")
    print(f"Total size: {stats['total_size_gb']:.2f} GB")
    print(f"Duplicates found: {stats['duplicate_count']}")
    ```

Deduplication Strategy:
    - Files are deduplicated using SHA256 checksums
    - First occurrence becomes the canonical file
    - Subsequent identical files are tracked as additional sources
    - Duplicate detection prevents storage waste
    - All source locations are preserved and queryable

Multi-Source Tracking:
    - Each unique file (by checksum) can have multiple sources
    - Sources tracked separately in library_file_sources table
    - Enables finding all locations where a file exists
    - Supports source removal without deleting file
    - Last seen timestamps for source verification

Search Indexing:
    - search_index field contains searchable text
    - Includes filename, display_name, tags, metadata
    - Enables fast full-text search across library
    - Updated when file metadata changes

Error Handling:
    - Duplicate checksums handled gracefully
    - JSON sources serialized/deserialized automatically
    - All database errors logged with context
    - Retry logic inherited from BaseRepository

See Also:
    - src/services/library_service.py - Library management service
    - src/services/file_service.py - File operations
    - src/api/routers/library.py - Library API endpoints
    - docs/technical-debt/COMPLETION-REPORT.md - Repository pattern
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import structlog

from .base_repository import BaseRepository


logger = structlog.get_logger(__name__)


class LibraryRepository(BaseRepository):
    """
    Repository for library-related database operations.

    Handles CRUD operations for the centralized library of 3D print files with
    intelligent checksum-based deduplication and multi-source tracking. A single
    file can exist in multiple locations (printers, watch folders) while being
    stored only once in the library.

    Key Features:
        - Checksum-based deduplication (SHA256)
        - Multi-source tracking per file
        - Search indexing for fast discovery
        - Comprehensive filtering and sorting
        - Library statistics and analytics
        - Source management (add/remove per file)

    Thread Safety:
        Operations are atomic but the repository is not thread-safe.
        Use connection pooling for concurrent access.
    """

    async def create_file(self, file_data: Dict[str, Any]) -> bool:
        """Create a new library file record.

        Args:
            file_data: Dictionary containing library file information with keys:
                - id: Unique file identifier (required)
                - checksum: File checksum for duplicate detection (required)
                - filename: Original filename (required)
                - display_name: Human-readable name
                - library_path: Path in library storage (required)
                - file_size: File size in bytes (required)
                - file_type: File extension (.gcode, .3mf, etc.) (required)
                - sources: JSON array of source information (required)
                - status: File status (default: 'available')
                - added_to_library: Timestamp when added (required)
                - last_modified: Last modification timestamp
                - search_index: Searchable text index (default: '')
                - is_duplicate: Duplicate flag (default: 0)
                - duplicate_of_checksum: Checksum of original if duplicate
                - duplicate_count: Number of duplicates found (default: 0)

        Returns:
            True if file was created successfully, False otherwise
        """
        try:
            await self._execute_write(
                """INSERT INTO library_files
                (id, checksum, filename, display_name, library_path, file_size, file_type,
                 sources, status, added_to_library, last_modified, search_index,
                 is_duplicate, duplicate_of_checksum, duplicate_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    file_data['id'],
                    file_data['checksum'],
                    file_data['filename'],
                    file_data.get('display_name'),
                    file_data['library_path'],
                    file_data['file_size'],
                    file_data['file_type'],
                    file_data['sources'],
                    file_data.get('status', 'available'),
                    file_data['added_to_library'],
                    file_data.get('last_modified'),
                    file_data.get('search_index', ''),
                    file_data.get('is_duplicate', 0),
                    file_data.get('duplicate_of_checksum'),
                    file_data.get('duplicate_count', 0)
                )
            )
            return True
        except sqlite3.IntegrityError as e:
            error_msg = str(e).lower()
            if 'unique' in error_msg:
                logger.info("Duplicate library file detected (UNIQUE constraint)",
                           checksum=file_data.get('checksum'))
                return False
            raise
        except Exception as e:
            logger.error("Failed to create library file", file_id=file_data.get('id'),
                        error=str(e), exc_info=True)
            return False

    async def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get library file by ID.

        Args:
            file_id: Unique file identifier

        Returns:
            Library file dictionary with all fields, or None if not found
        """
        try:
            file_data = await self._fetch_one("SELECT * FROM library_files WHERE id = ?", (file_id,))
            # CRITICAL FIX: Remove leading dot from file_type for frontend compatibility
            if file_data and file_data.get('file_type') and file_data['file_type'].startswith('.'):
                file_data['file_type'] = file_data['file_type'].lstrip('.')
            return file_data
        except Exception as e:
            logger.error("Failed to get library file", file_id=file_id, error=str(e), exc_info=True)
            return None

    async def get_file_by_checksum(self, checksum: str) -> Optional[Dict[str, Any]]:
        """Get library file by checksum.

        Args:
            checksum: File checksum (MD5, SHA256, etc.)

        Returns:
            Library file dictionary with all fields, or None if not found

        Notes:
            - Useful for duplicate detection and file matching
        """
        try:
            file_data = await self._fetch_one("SELECT * FROM library_files WHERE checksum = ?", (checksum,))
            # CRITICAL FIX: Remove leading dot from file_type for frontend compatibility
            if file_data and file_data.get('file_type') and file_data['file_type'].startswith('.'):
                file_data['file_type'] = file_data['file_type'].lstrip('.')
            return file_data
        except Exception as e:
            logger.error("Failed to get library file by checksum", checksum=checksum,
                        error=str(e), exc_info=True)
            return None

    async def update_file(self, checksum: str, updates: Dict[str, Any]) -> bool:
        """Update library file by checksum.

        Args:
            checksum: File checksum
            updates: Dictionary of fields to update

        Returns:
            True if update succeeded, False otherwise

        Notes:
            - Updates by checksum instead of ID for duplicate management
            - No immutable field protection (caller responsible)
        """
        try:
            if not updates:
                return False

            # Build update query
            set_clauses = [f"{key} = ?" for key in updates.keys()]
            set_clause = ", ".join(set_clauses)

            query = f"UPDATE library_files SET {set_clause} WHERE checksum = ?"
            params = list(updates.values()) + [checksum]

            await self._execute_write(query, tuple(params))
            return True
        except Exception as e:
            logger.error("Failed to update library file", checksum=checksum, error=str(e), exc_info=True)
            return False

    async def delete_file(self, checksum: str) -> bool:
        """Delete library file by checksum.

        Args:
            checksum: File checksum

        Returns:
            True if deletion succeeded, False otherwise

        Notes:
            - Deletes by checksum to handle all duplicates
            - Does NOT cascade delete to library_file_sources (use delete_file_sources separately)
        """
        try:
            await self._execute_write("DELETE FROM library_files WHERE checksum = ?", (checksum,))
            return True
        except Exception as e:
            logger.error("Failed to delete library file", checksum=checksum, error=str(e), exc_info=True)
            return False

    async def list_files(self, filters: Optional[Dict[str, Any]] = None,
                        page: int = 1, limit: int = 50) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """List library files with filters and pagination.

        Args:
            filters: Optional filtering criteria:
                - source_type: Filter by source type ('printer', 'local_watch', 'url', etc.)
                - file_type: Filter by file extension
                - status: Filter by status ('available', 'error', etc.)
                - search: Text search in search_index field
                - has_thumbnail: Boolean filter for thumbnail presence
                - has_metadata: Boolean filter for metadata presence
                - manufacturer: Filter by printer manufacturer (requires JOIN)
                - printer_model: Filter by printer model (requires JOIN)
                - show_duplicates: If False, hide duplicate files (default: True)
                - only_duplicates: If True, show only duplicates
                - sort_by: Field to sort by ('created_at', 'filename', 'file_size', 'last_modified')
                - sort_order: Sort direction ('asc' or 'desc', default: 'desc')
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (files_list, pagination_info)
            - files_list: List of library file dictionaries
            - pagination_info: Dictionary with pagination metadata

        Notes:
            - Automatically JOINs library_file_sources when filtering by manufacturer/printer_model
            - Uses DISTINCT when JOIN is required to avoid duplicates
            - Returns empty list and default pagination on error
        """
        try:
            filters = filters or {}

            # Check if manufacturer/model filters require JOIN
            needs_join = filters.get('manufacturer') or filters.get('printer_model')

            # Build WHERE clause
            where_clauses = []
            params = []

            if filters.get('source_type'):
                where_clauses.append("lf.sources LIKE ?")
                params.append(f'%"type": "{filters["source_type"]}"%')

            if filters.get('file_type'):
                where_clauses.append("lf.file_type = ?")
                params.append(filters['file_type'])

            if filters.get('status'):
                where_clauses.append("lf.status = ?")
                params.append(filters['status'])

            if filters.get('search'):
                where_clauses.append("lf.search_index LIKE ?")
                params.append(f"%{filters['search'].lower()}%")

            if filters.get('has_thumbnail') is not None:
                where_clauses.append("lf.has_thumbnail = ?")
                params.append(1 if filters['has_thumbnail'] else 0)

            if filters.get('has_metadata') is not None:
                where_clauses.append("lf.last_analyzed IS NOT NULL" if filters['has_metadata'] else "lf.last_analyzed IS NULL")

            # Manufacturer and printer_model filters (require JOIN)
            if filters.get('manufacturer'):
                where_clauses.append("lfs.manufacturer = ?")
                params.append(filters['manufacturer'])

            if filters.get('printer_model'):
                where_clauses.append("lfs.printer_model = ?")
                params.append(filters['printer_model'])

            # Duplicate filters
            if filters.get('show_duplicates') is False:
                where_clauses.append("lf.is_duplicate = 0")

            if filters.get('only_duplicates') is True:
                where_clauses.append("lf.is_duplicate = 1")

            # Build query based on whether JOIN is needed
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            if needs_join:
                # Query with JOIN to library_file_sources
                count_query = f"""
                    SELECT COUNT(DISTINCT lf.checksum) as total
                    FROM library_files lf
                    INNER JOIN library_file_sources lfs ON lf.checksum = lfs.file_checksum
                    WHERE {where_clause}
                """
                count_params = params.copy()
            else:
                # Simple query without JOIN
                count_query = f"SELECT COUNT(*) as total FROM library_files lf WHERE {where_clause}"
                count_params = params.copy()

            count_row = await self._fetch_one(count_query, tuple(count_params))
            total_items = count_row['total'] if count_row else 0

            # Calculate pagination
            offset = (page - 1) * limit
            total_pages = (total_items + limit - 1) // limit if limit > 0 else 1

            # Build ORDER BY clause
            sort_by = filters.get('sort_by', 'created_at')
            sort_order = filters.get('sort_order', 'desc').upper()

            # Map frontend field names to database columns
            sort_field_map = {
                'created_at': 'lf.added_to_library',
                'filename': 'lf.filename',
                'file_size': 'lf.file_size',
                'last_modified': 'lf.last_modified'
            }

            # Get the database column name (default to added_to_library if invalid)
            db_field = sort_field_map.get(sort_by, 'lf.added_to_library')

            # Validate sort order
            if sort_order not in ['ASC', 'DESC']:
                sort_order = 'DESC'

            order_by = f"{db_field} {sort_order}"

            if needs_join:
                # Query with JOIN (distinct to avoid duplicates)
                query = f"""
                    SELECT DISTINCT lf.* FROM library_files lf
                    INNER JOIN library_file_sources lfs ON lf.checksum = lfs.file_checksum
                    WHERE {where_clause}
                    ORDER BY {order_by}
                    LIMIT ? OFFSET ?
                """
            else:
                # Simple query without JOIN
                query = f"""
                    SELECT lf.* FROM library_files lf
                    WHERE {where_clause}
                    ORDER BY {order_by}
                    LIMIT ? OFFSET ?
                """

            params.extend([limit, offset])

            rows = await self._fetch_all(query, tuple(params))

            # CRITICAL FIX: Remove leading dot from file_type for frontend compatibility
            for row in rows:
                if row.get('file_type') and row['file_type'].startswith('.'):
                    row['file_type'] = row['file_type'].lstrip('.')

            pagination = {
                'page': page,
                'limit': limit,
                'total_items': total_items,
                'total_pages': total_pages,
                'page_size': limit,
                'current_page': page,
                'has_previous': page > 1,
                'has_next': page < total_pages
            }

            return rows, pagination

        except Exception as e:
            logger.error("Failed to list library files", error=str(e), exc_info=True)
            return [], {'page': page, 'limit': limit, 'total_items': 0, 'total_pages': 0,
                       'page_size': limit, 'current_page': page, 'has_previous': False, 'has_next': False}

    async def create_file_source(self, source_data: Dict[str, Any]) -> bool:
        """Create library file source record.

        Args:
            source_data: Dictionary containing source information with keys:
                - file_checksum: Checksum of the library file (required)
                - source_type: Type of source ('printer', 'local_watch', 'url', etc.) (required)
                - source_id: Identifier within source system
                - source_name: Human-readable source name
                - original_path: Original file path at source
                - original_filename: Original filename at source
                - discovered_at: Timestamp when file was discovered (required)
                - metadata: JSON serializable source-specific metadata
                - manufacturer: Printer manufacturer (for printer sources)
                - printer_model: Printer model (for printer sources)

        Returns:
            True if source was created successfully, False otherwise

        Notes:
            - Uses INSERT OR IGNORE to handle duplicate sources gracefully
            - Allows tracking multiple sources for the same file (e.g., same file on different printers)
        """
        try:
            await self._execute_write(
                """INSERT OR IGNORE INTO library_file_sources
                (file_checksum, source_type, source_id, source_name, original_path,
                 original_filename, discovered_at, metadata, manufacturer, printer_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    source_data['file_checksum'],
                    source_data['source_type'],
                    source_data.get('source_id'),
                    source_data.get('source_name'),
                    source_data.get('original_path'),
                    source_data.get('original_filename'),
                    source_data['discovered_at'],
                    source_data.get('metadata'),
                    source_data.get('manufacturer'),
                    source_data.get('printer_model')
                )
            )
            return True
        except Exception as e:
            logger.error("Failed to create library file source", checksum=source_data.get('file_checksum'),
                        error=str(e), exc_info=True)
            return False

    async def delete_file_sources(self, checksum: str) -> bool:
        """Delete all sources for a library file.

        Args:
            checksum: File checksum

        Returns:
            True if deletion succeeded, False otherwise

        Notes:
            - Deletes ALL source records for the given checksum
            - Use when removing a file from the library
        """
        try:
            await self._execute_write(
                "DELETE FROM library_file_sources WHERE file_checksum = ?",
                (checksum,)
            )
            return True
        except Exception as e:
            logger.error("Failed to delete library file sources", checksum=checksum,
                        error=str(e), exc_info=True)
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get library statistics.

        Returns:
            Dictionary with library statistics from library_stats view

        Notes:
            - Returns empty dict on error
            - Stats are calculated from library_stats materialized view or query
        """
        try:
            row = await self._fetch_one("SELECT * FROM library_stats", ())
            return row if row else {}
        except Exception as e:
            logger.error("Failed to get library stats", error=str(e), exc_info=True)
            return {}

    async def exists(self, checksum: str) -> bool:
        """Check if a library file exists by checksum.

        Args:
            checksum: File checksum

        Returns:
            True if file exists, False otherwise
        """
        try:
            result = await self._fetch_one("SELECT 1 FROM library_files WHERE checksum = ?", (checksum,))
            return result is not None
        except Exception as e:
            logger.error("Failed to check library file existence", checksum=checksum,
                        error=str(e), exc_info=True)
            return False
