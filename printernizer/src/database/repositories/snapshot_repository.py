"""
Snapshot repository for managing camera snapshot database operations.

This module provides data access methods for printer camera snapshots, including
snapshot storage, validation tracking, and job association. Snapshots can be
captured manually, on schedule, or triggered by print events.

Key Capabilities:
    - Camera snapshot creation and tracking
    - Job association for print timelapse creation
    - Snapshot validation (image integrity checks)
    - Metadata storage (dimensions, capture trigger, notes)
    - Context-aware queries (joins with jobs and printers)
    - Capture trigger tracking (manual, scheduled, event-based)

Database Schema:
    The snapshots table stores camera snapshots:
    - id (INTEGER PRIMARY KEY AUTOINCREMENT): Unique snapshot ID
    - job_id (INTEGER): Associated job ID (nullable, foreign key to jobs)
    - printer_id (TEXT): Source printer ID (required, foreign key to printers)
    - filename (TEXT): Stored filename (required)
    - original_filename (TEXT): Original filename from camera
    - file_size (INTEGER): File size in bytes (required)
    - content_type (TEXT): MIME type (default: 'image/jpeg')
    - storage_path (TEXT): Path to stored image file (required)
    - captured_at (DATETIME): When snapshot was captured
    - capture_trigger (TEXT): What triggered capture ('manual', 'scheduled', 'event')
    - width (INTEGER): Image width in pixels
    - height (INTEGER): Image height in pixels
    - is_valid (BOOLEAN): Whether snapshot passed validation (default: True)
    - validation_error (TEXT): Error message if validation failed
    - last_validated_at (DATETIME): Last validation timestamp
    - notes (TEXT): User notes about snapshot
    - metadata (TEXT): JSON metadata for extensibility
    - created_at (DATETIME): When record was created

    The v_snapshots_with_context view provides enriched snapshot data:
    - All snapshot fields
    - job_name: Name of associated job
    - printer_name: Name of source printer
    - printer_type: Type of printer (bambu_lab, prusa)

    Indexes:
    - idx_snapshots_printer_id: Fast lookup by printer
    - idx_snapshots_job_id: Fast lookup by job
    - idx_snapshots_captured_at: Fast sorting by capture time

Usage Examples:
    ```python
    from src.database.repositories import SnapshotRepository

    # Initialize
    snapshot_repo = SnapshotRepository(db.connection)

    # Create a snapshot
    snapshot_data = {
        'printer_id': 'bambu_a1_001',
        'job_id': 12345,
        'filename': 'snapshot_20250117_103045.jpg',
        'file_size': 524288,
        'storage_path': '/snapshots/bambu_a1_001/20250117_103045.jpg',
        'capture_trigger': 'scheduled',
        'width': 1920,
        'height': 1080,
        'captured_at': datetime.now().isoformat()
    }
    snapshot_id = await snapshot_repo.create(snapshot_data)

    # Get snapshot with context (includes job and printer info)
    snapshot = await snapshot_repo.get(snapshot_id)
    if snapshot:
        print(f"Snapshot for job: {snapshot['job_name']}")
        print(f"Printer: {snapshot['printer_name']}")

    # List snapshots for a printer
    printer_snapshots = await snapshot_repo.list(
        printer_id='bambu_a1_001',
        limit=50
    )

    # List snapshots for a job (for timelapse creation)
    job_snapshots = await snapshot_repo.list(
        job_id=12345
    )

    # Update validation status after image check
    await snapshot_repo.update_validation(
        snapshot_id=snapshot_id,
        is_valid=False,
        validation_error='Corrupt image data'
    )

    # Clean up - delete snapshot
    await snapshot_repo.delete(snapshot_id)
    ```

Capture Triggers:
    - 'manual': User-initiated snapshot
    - 'scheduled': Periodic snapshot (e.g., every 30 seconds)
    - 'event': Event-based (e.g., layer change, print start/end)
    - Used for organizing snapshots and timelapse creation

Snapshot Validation:
    - Snapshots can be validated for integrity (valid image data)
    - validation_error stores reason for invalid snapshots
    - last_validated_at tracks validation freshness
    - Invalid snapshots can be filtered out or revalidated

Job Association:
    - Snapshots can be linked to print jobs
    - Enables timelapse video creation per job
    - Snapshots remain accessible even after job completion
    - Allows chronological reconstruction of print process

Error Handling:
    - All database errors logged with context
    - JSON metadata serialized/deserialized automatically
    - Retry logic inherited from BaseRepository
    - Failed validations don't delete snapshots

See Also:
    - src/services/camera_snapshot_service.py - Snapshot capture service
    - src/services/timelapse_service.py - Timelapse video creation
    - src/api/routers/snapshots.py - Snapshot API endpoints
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import structlog

from .base_repository import BaseRepository

logger = structlog.get_logger()


class SnapshotRepository(BaseRepository):
    """
    Repository for camera snapshot-related database operations.

    Handles CRUD operations for printer camera snapshots with job association,
    validation tracking, and context-aware queries. Snapshots are used for
    monitoring prints and creating timelapse videos.

    Key Features:
        - Job association for timelapse creation
        - Validation tracking (image integrity)
        - Context-aware queries (with job/printer info)
        - Capture trigger tracking
        - Metadata storage

    Thread Safety:
        Operations are atomic but the repository is not thread-safe.
        Use connection pooling for concurrent access.
    """

    async def create(self, snapshot_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new snapshot record.

        Args:
            snapshot_data: Dictionary containing snapshot information
                Required: printer_id, filename, file_size, storage_path
                Optional: job_id, original_filename, content_type, captured_at,
                         capture_trigger, width, height, is_valid, notes, metadata

        Returns:
            Snapshot ID if successful, None otherwise
        """
        try:
            metadata_json = json.dumps(snapshot_data.get('metadata')) if snapshot_data.get('metadata') else None

            lastrowid = await self._execute_write(
                """INSERT INTO snapshots (
                    job_id, printer_id, filename, original_filename,
                    file_size, content_type, storage_path,
                    captured_at, capture_trigger, width, height,
                    is_valid, notes, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot_data.get('job_id'),
                    snapshot_data['printer_id'],
                    snapshot_data['filename'],
                    snapshot_data.get('original_filename'),
                    snapshot_data['file_size'],
                    snapshot_data.get('content_type', 'image/jpeg'),
                    snapshot_data['storage_path'],
                    snapshot_data.get('captured_at', datetime.now().isoformat()),
                    snapshot_data.get('capture_trigger', 'manual'),
                    snapshot_data.get('width'),
                    snapshot_data.get('height'),
                    snapshot_data.get('is_valid', True),
                    snapshot_data.get('notes'),
                    metadata_json
                )
            )

            logger.info("Snapshot created",
                       snapshot_id=lastrowid,
                       filename=snapshot_data['filename'],
                       printer_id=snapshot_data['printer_id'])
            return lastrowid

        except Exception as e:
            logger.error("Failed to create snapshot",
                        error=str(e),
                        snapshot_data=snapshot_data,
                        exc_info=True)
            return None

    async def get(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """
        Get snapshot by ID with context information.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Snapshot dictionary with context data, or None if not found
        """
        try:
            sql = """
                SELECT * FROM v_snapshots_with_context
                WHERE id = ?
            """
            row = await self._fetch_one(sql, [snapshot_id])

            if row:
                snapshot = dict(row)
                # Parse JSON metadata
                if snapshot.get('metadata'):
                    try:
                        snapshot['metadata'] = json.loads(snapshot['metadata'])
                    except (json.JSONDecodeError, TypeError):
                        snapshot['metadata'] = None
                return snapshot

            return None

        except Exception as e:
            logger.error("Failed to get snapshot",
                        error=str(e),
                        snapshot_id=snapshot_id,
                        exc_info=True)
            return None

    async def list(
        self,
        printer_id: Optional[str] = None,
        job_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List snapshots with optional filters.

        Args:
            printer_id: Filter by printer ID (optional)
            job_id: Filter by job ID (optional)
            limit: Maximum number of results (default: 50)
            offset: Offset for pagination (default: 0)

        Returns:
            List of snapshot dictionaries with context data
        """
        try:
            conditions = []
            params = []

            if printer_id:
                conditions.append("printer_id = ?")
                params.append(printer_id)

            if job_id:
                conditions.append("job_id = ?")
                params.append(job_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            sql = f"""
                SELECT * FROM v_snapshots_with_context
                {where_clause}
                ORDER BY captured_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            rows = await self._fetch_all(sql, params)

            snapshots = []
            for row in rows:
                snapshot = dict(row)
                # Parse JSON metadata
                if snapshot.get('metadata'):
                    try:
                        snapshot['metadata'] = json.loads(snapshot['metadata'])
                    except (json.JSONDecodeError, TypeError):
                        snapshot['metadata'] = None
                snapshots.append(snapshot)

            return snapshots

        except Exception as e:
            logger.error("Failed to list snapshots",
                        error=str(e),
                        printer_id=printer_id,
                        job_id=job_id,
                        exc_info=True)
            return []

    async def delete(self, snapshot_id: int) -> bool:
        """
        Delete a snapshot record.

        Args:
            snapshot_id: Snapshot ID to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            await self._execute_write(
                "DELETE FROM snapshots WHERE id = ?",
                (snapshot_id,)
            )
            logger.info("Snapshot deleted", snapshot_id=snapshot_id)
            return True

        except Exception as e:
            logger.error("Failed to delete snapshot",
                        error=str(e),
                        snapshot_id=snapshot_id,
                        exc_info=True)
            return False

    async def update_validation(
        self,
        snapshot_id: int,
        is_valid: bool,
        validation_error: Optional[str] = None
    ) -> bool:
        """
        Update snapshot validation status.

        Args:
            snapshot_id: Snapshot ID
            is_valid: Whether snapshot is valid
            validation_error: Error message if invalid (optional)

        Returns:
            True if updated, False otherwise
        """
        try:
            await self._execute_write(
                """UPDATE snapshots
                   SET is_valid = ?, validation_error = ?, last_validated_at = ?
                   WHERE id = ?""",
                (is_valid, validation_error, datetime.now().isoformat(), snapshot_id)
            )
            logger.debug("Snapshot validation updated",
                        snapshot_id=snapshot_id,
                        is_valid=is_valid)
            return True

        except Exception as e:
            logger.error("Failed to update snapshot validation",
                        error=str(e),
                        snapshot_id=snapshot_id,
                        exc_info=True)
            return False

    async def exists(self, snapshot_id: int) -> bool:
        """
        Check if a snapshot exists.

        Args:
            snapshot_id: Snapshot ID to check

        Returns:
            True if snapshot exists, False otherwise
        """
        try:
            result = await self._fetch_one(
                "SELECT 1 FROM snapshots WHERE id = ?",
                [snapshot_id]
            )
            return result is not None

        except Exception as e:
            logger.error("Failed to check snapshot existence",
                        error=str(e),
                        snapshot_id=snapshot_id,
                        exc_info=True)
            return False
