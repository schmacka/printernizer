"""File repository for database operations.

This repository handles all file-related database operations including
printer files, local watch folder files, and file statistics.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog

from .base_repository import BaseRepository


logger = structlog.get_logger(__name__)


class FileRepository(BaseRepository):
    """Repository for file-related database operations.

    Handles CRUD operations for 3D print files from printers and local watch folders,
    including metadata management, thumbnails, and enhanced metadata from file analysis.
    """

    async def create(self, file_data: Dict[str, Any]) -> bool:
        """Create a new file record or update if exists (preserving thumbnails).

        Args:
            file_data: Dictionary containing file information with keys:
                - id: Unique file identifier (required)
                - printer_id: Printer that owns the file (default: 'local')
                - filename: Original filename (required)
                - display_name: Human-readable name
                - file_path: Local filesystem path
                - file_size: File size in bytes
                - file_type: File extension (.gcode, .3mf, etc.)
                - status: File status (default: 'available')
                - source: File source ('printer', 'local_watch')
                - metadata: JSON serializable metadata dict
                - watch_folder_path: Path to watch folder if source='local_watch'
                - relative_path: Relative path within watch folder
                - modified_time: Last modified timestamp

        Returns:
            True if file was created/updated successfully, False otherwise

        Notes:
            - If file exists, preserves thumbnail data and only updates non-thumbnail fields
            - Uses upsert logic to handle duplicate file IDs gracefully
        """
        try:
            file_id = file_data['id']

            # Check if file already exists
            existing = await self._fetch_one(
                "SELECT id, has_thumbnail, thumbnail_data, thumbnail_width, thumbnail_height, thumbnail_format, thumbnail_source FROM files WHERE id = ?",
                (file_id,)
            )

            if existing:
                # File exists - update only non-thumbnail fields to preserve thumbnail data
                updates = {
                    'display_name': file_data.get('display_name'),
                    'file_size': file_data.get('file_size'),
                    'file_type': file_data.get('file_type'),
                    'modified_time': file_data.get('modified_time')
                }

                # Only update file_path and status if provided (e.g., after download)
                if file_data.get('file_path'):
                    updates['file_path'] = file_data['file_path']
                if file_data.get('status'):
                    updates['status'] = file_data['status']

                # Update metadata if provided
                if file_data.get('metadata'):
                    updates['metadata'] = file_data['metadata']

                return await self.update(file_id, updates)
            else:
                # New file - insert with all fields
                await self._execute_write(
                    """INSERT INTO files (id, printer_id, filename, display_name, file_path, file_size,
                                                file_type, status, source, metadata, watch_folder_path,
                                                relative_path, modified_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        file_id,
                        file_data.get('printer_id', 'local'),
                        file_data['filename'],
                        file_data.get('display_name'),
                        file_data.get('file_path'),
                        file_data.get('file_size'),
                        file_data.get('file_type'),
                        file_data.get('status', 'available'),
                        file_data.get('source', 'printer'),
                        file_data.get('metadata'),
                        file_data.get('watch_folder_path'),
                        file_data.get('relative_path'),
                        file_data.get('modified_time')
                    )
                )
                return True
        except sqlite3.IntegrityError as e:
            error_msg = str(e).lower()
            if 'unique' in error_msg:
                logger.info("Duplicate file detected (UNIQUE constraint)", file_id=file_id)
                return False
            raise
        except Exception as e:
            logger.error("Failed to create file", file_id=file_data.get('id'), error=str(e), exc_info=True)
            return False

    async def get(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get a single file by ID.

        Args:
            file_id: Unique file identifier

        Returns:
            File dictionary with all fields, or None if not found

        Notes:
            - Deserializes JSON metadata field into dict
            - Returns None if file doesn't exist
        """
        try:
            file_data = await self._fetch_one("SELECT * FROM files WHERE id = ?", (file_id,))

            if file_data:
                # Deserialize JSON metadata back to dict
                if file_data.get('metadata') and isinstance(file_data['metadata'], str):
                    try:
                        file_data['metadata'] = json.loads(file_data['metadata'])
                    except (json.JSONDecodeError, TypeError):
                        # If deserialization fails, set to empty dict
                        file_data['metadata'] = {}

            return file_data
        except Exception as e:
            logger.error("Failed to get file", file_id=file_id, error=str(e), exc_info=True)
            return None

    async def list(self, printer_id: Optional[str] = None, status: Optional[str] = None,
                   source: Optional[str] = None) -> List[Dict[str, Any]]:
        """List files with optional filtering.

        Args:
            printer_id: Filter by printer ID
            status: Filter by file status ('available', 'downloading', 'error', etc.)
            source: Filter by file source ('printer', 'local_watch')

        Returns:
            List of file dictionaries ordered by created_at DESC

        Notes:
            - Automatically deserializes JSON metadata fields
            - Returns empty list on error
        """
        try:
            query = "SELECT * FROM files"
            params = []
            conditions = []

            if printer_id:
                conditions.append("printer_id = ?")
                params.append(printer_id)
            if status:
                conditions.append("status = ?")
                params.append(status)
            if source:
                conditions.append("source = ?")
                params.append(source)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC"

            rows = await self._fetch_all(query, tuple(params))
            files = []
            for file_data in rows:
                # Deserialize JSON metadata back to dict
                if file_data.get('metadata') and isinstance(file_data['metadata'], str):
                    try:
                        file_data['metadata'] = json.loads(file_data['metadata'])
                    except (json.JSONDecodeError, TypeError):
                        # If deserialization fails, set to empty dict
                        file_data['metadata'] = {}
                files.append(file_data)
            return files
        except Exception as e:
            logger.error("Failed to list files", error=str(e), exc_info=True)
            return []

    async def update(self, file_id: str, updates: Dict[str, Any]) -> bool:
        """Update file with provided fields.

        Args:
            file_id: Unique file identifier
            updates: Dictionary of fields to update

        Returns:
            True if update succeeded, False otherwise

        Notes:
            - Protects immutable fields (id, printer_id, filename, created_at)
            - Automatically serializes dict metadata to JSON
            - Returns True if no fields need updating
        """
        try:
            # Build dynamic update query
            set_clauses = []
            params = []

            for field, value in updates.items():
                if field not in ['id', 'printer_id', 'filename', 'created_at']:  # Protect immutable fields
                    # Handle special types that need JSON serialization
                    if field == 'metadata' and isinstance(value, dict):
                        value = json.dumps(value)

                    set_clauses.append(f"{field} = ?")
                    params.append(value)

            if not set_clauses:
                return True  # Nothing to update

            params.append(file_id)
            query = f"UPDATE files SET {', '.join(set_clauses)} WHERE id = ?"

            await self._execute_write(query, tuple(params))
            return True
        except Exception as e:
            logger.error("Failed to update file", file_id=file_id, error=str(e), exc_info=True)
            return False

    async def update_enhanced_metadata(self, file_id: str, enhanced_metadata: Dict[str, Any],
                                      last_analyzed: datetime) -> bool:
        """Update file with enhanced metadata from 3D file analysis.

        This method stores comprehensive metadata extracted from 3D files including
        physical properties, print settings, material requirements, cost analysis,
        quality metrics, and compatibility information.

        Args:
            file_id: Unique file identifier
            enhanced_metadata: Dictionary with nested metadata structure:
                - physical_properties: width, depth, height, volume, surface_area, object_count
                - print_settings: nozzle_diameter, wall_count, infill_pattern, etc.
                - material_requirements: total_weight, filament_length, filament_colors
                - cost_breakdown: material_cost, energy_cost, total_cost
                - quality_metrics: complexity_score, success_probability, difficulty_level
                - compatibility_info: compatible_printers, slicer_name, profile_name
            last_analyzed: Timestamp when analysis was performed

        Returns:
            True if update succeeded, False otherwise

        Notes:
            - Issue #43 - METADATA-001 implementation
            - Filters out None values to avoid overwriting existing data
            - JSON-serializes array fields (filament_colors, compatible_printers)
        """
        try:
            # Extract individual fields from enhanced metadata structure
            physical_props = enhanced_metadata.get('physical_properties') or {}
            print_settings = enhanced_metadata.get('print_settings') or {}
            material_req = enhanced_metadata.get('material_requirements') or {}
            cost_breakdown = enhanced_metadata.get('cost_breakdown') or {}
            quality_metrics = enhanced_metadata.get('quality_metrics') or {}
            compatibility = enhanced_metadata.get('compatibility_info') or {}

            # Build update query with all enhanced metadata fields
            updates = {
                # Physical properties
                'model_width': physical_props.get('width'),
                'model_depth': physical_props.get('depth'),
                'model_height': physical_props.get('height'),
                'model_volume': physical_props.get('volume'),
                'surface_area': physical_props.get('surface_area'),
                'object_count': physical_props.get('object_count', 1),

                # Print settings
                'nozzle_diameter': print_settings.get('nozzle_diameter'),
                'wall_count': print_settings.get('wall_count'),
                'wall_thickness': print_settings.get('wall_thickness'),
                'infill_pattern': print_settings.get('infill_pattern'),
                'first_layer_height': print_settings.get('first_layer_height'),

                # Material information
                'total_filament_weight': material_req.get('total_weight'),
                'filament_length': material_req.get('filament_length'),
                'filament_colors': json.dumps(material_req.get('filament_colors', [])) if material_req.get('filament_colors') else None,

                # Cost analysis
                'material_cost': cost_breakdown.get('material_cost'),
                'energy_cost': cost_breakdown.get('energy_cost'),
                'total_cost': cost_breakdown.get('total_cost'),

                # Quality metrics
                'complexity_score': quality_metrics.get('complexity_score'),
                'success_probability': quality_metrics.get('success_probability'),
                'difficulty_level': quality_metrics.get('difficulty_level'),

                # Compatibility
                'compatible_printers': json.dumps(compatibility.get('compatible_printers', [])) if compatibility.get('compatible_printers') else None,
                'slicer_name': compatibility.get('slicer_name'),
                'slicer_version': compatibility.get('slicer_version'),
                'profile_name': compatibility.get('profile_name'),

                # Metadata timestamp
                'last_analyzed': last_analyzed.isoformat() if isinstance(last_analyzed, datetime) else last_analyzed
            }

            # Filter out None values
            updates = {k: v for k, v in updates.items() if v is not None}

            # Use existing update method
            return await self.update(file_id, updates)

        except Exception as e:
            logger.error("Failed to update file enhanced metadata", file_id=file_id, error=str(e), exc_info=True)
            return False

    async def list_local_files(self, watch_folder_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """List local files from watch folders.

        Args:
            watch_folder_path: Optional filter by specific watch folder path

        Returns:
            List of local watch folder files ordered by modified_time DESC

        Notes:
            - Only returns files with source='local_watch'
            - Returns empty list on error
        """
        try:
            query = "SELECT * FROM files WHERE source = 'local_watch'"
            params = []

            if watch_folder_path:
                query += " AND watch_folder_path = ?"
                params.append(watch_folder_path)

            query += " ORDER BY modified_time DESC"

            return await self._fetch_all(query, tuple(params) if params else ())
        except Exception as e:
            logger.error("Failed to list local files", error=str(e), exc_info=True)
            return []

    async def delete(self, file_id: str) -> bool:
        """Delete a file record.

        Args:
            file_id: Unique file identifier

        Returns:
            True if deletion succeeded, False otherwise
        """
        try:
            await self._execute_write("DELETE FROM files WHERE id = ?", (file_id,))
            return True
        except Exception as e:
            logger.error("Failed to delete file", file_id=file_id, error=str(e), exc_info=True)
            return False

    async def delete_local_file(self, file_id: str) -> bool:
        """Delete a local watch folder file record.

        Args:
            file_id: Unique file identifier

        Returns:
            True if deletion succeeded, False otherwise

        Notes:
            - Only deletes files with source='local_watch' for safety
        """
        try:
            await self._execute_write("DELETE FROM files WHERE id = ? AND source = 'local_watch'", (file_id,))
            return True
        except Exception as e:
            logger.error("Failed to delete local file", file_id=file_id, error=str(e), exc_info=True)
            return False

    async def exists(self, file_id: str) -> bool:
        """Check if a file exists.

        Args:
            file_id: Unique file identifier

        Returns:
            True if file exists, False otherwise
        """
        try:
            result = await self._fetch_one("SELECT 1 FROM files WHERE id = ?", (file_id,))
            return result is not None
        except Exception as e:
            logger.error("Failed to check file existence", file_id=file_id, error=str(e), exc_info=True)
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """Get file statistics by source and status.

        Returns:
            Dictionary with statistics including:
                - {source}_count: Count of files by source
                - {source}_size: Total size in bytes by source
                - {status}_count: Count of files by status

        Notes:
            - Returns empty dict on error
        """
        try:
            stats = {}

            # Total counts by source
            rows = await self._fetch_all("SELECT COUNT(*), source FROM files GROUP BY source", ())
            for row in rows:
                source = row['source'] or 'unknown'
                stats[f"{source}_count"] = row['COUNT(*)']

            # Total size by source
            rows = await self._fetch_all("SELECT SUM(file_size), source FROM files GROUP BY source", ())
            for row in rows:
                source = row['source'] or 'unknown'
                stats[f"{source}_size"] = row['SUM(file_size)'] or 0

            # Status counts
            rows = await self._fetch_all("SELECT COUNT(*), status FROM files GROUP BY status", ())
            for row in rows:
                status = row['status'] or 'unknown'
                stats[f"{status}_count"] = row['COUNT(*)']

            return stats
        except Exception as e:
            logger.error("Failed to get file statistics", error=str(e), exc_info=True)
            return {}
