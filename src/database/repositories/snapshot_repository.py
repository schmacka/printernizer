"""
Snapshot repository for managing camera snapshot database operations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import structlog

from .base_repository import BaseRepository

logger = structlog.get_logger()


class SnapshotRepository(BaseRepository):
    """Repository for camera snapshot-related database operations."""

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
