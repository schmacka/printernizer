"""
Printer repository for managing printer-related database operations.

This module provides data access methods for printer configuration and status
tracking, including printer registration, status updates, and printer queries.

Database Schema:
    The printers table stores printer configuration and status:
    - id (TEXT PRIMARY KEY): Unique printer identifier
    - name (TEXT): Human-readable printer name
    - type (TEXT): Printer type (bambu_lab, prusa, etc.)
    - ip_address (TEXT): Network IP address
    - api_key (TEXT): API authentication key (encrypted)
    - access_code (TEXT): Printer access code
    - serial_number (TEXT): Hardware serial number
    - webcam_url (TEXT): External webcam URL (HTTP snapshot or RTSP stream)
    - is_active (BOOLEAN): Whether printer is enabled
    - status (TEXT): Current status (online, offline, printing, etc.)
    - last_seen (DATETIME): Last communication timestamp

    Indexes:
    - idx_printers_type: Fast filtering by printer type
    - idx_printers_active: Quick lookups of active printers

Usage Examples:
    ```python
    from src.database.repositories import PrinterRepository

    # Initialize
    printer_repo = PrinterRepository(db.connection)

    # Register a new printer
    printer_data = {
        'id': 'bambu_a1_001',
        'name': 'Bambu Lab A1 #1',
        'type': 'bambu_lab',
        'ip_address': '192.168.1.100',
        'serial_number': 'BL-A1-2024-001',
        'is_active': True
    }
    await printer_repo.create(printer_data)

    # Update printer status
    await printer_repo.update_status('bambu_a1_001', 'printing')

    # Get all active printers
    active_printers = await printer_repo.list(active_only=True)

    # Update configuration
    await printer_repo.update('bambu_a1_001', {
        'name': 'Bambu Lab A1 Main',
        'ip_address': '192.168.1.101'
    })
    ```

See Also:
    - src/services/printer_service.py - Business logic
    - src/printers/bambu_lab.py - Bambu Lab printer driver
    - src/printers/prusa.py - Prusa printer driver
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog

from .base_repository import BaseRepository

logger = structlog.get_logger()


class PrinterRepository(BaseRepository):
    """
    Repository for printer-related database operations.

    Provides CRUD operations for printer configuration and status management.
    Handles printer registration, status updates, and active printer tracking.

    Key Features:
        - Printer registration and configuration
        - Status tracking with timestamps
        - Active/inactive printer filtering
        - Type-based printer queries
    """

    async def create(self, printer_data: Dict[str, Any]) -> bool:
        """
        Create a new printer record.

        Args:
            printer_data: Dictionary containing printer information
                Required: id, name, type
                Optional: ip_address, api_key, access_code, serial_number, webcam_url, is_active

        Returns:
            True if printer was created successfully, False otherwise
        """
        try:
            await self._execute_write(
                """INSERT INTO printers (id, name, type, ip_address, api_key, access_code, serial_number, webcam_url, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    printer_data['id'],
                    printer_data['name'],
                    printer_data['type'],
                    printer_data.get('ip_address'),
                    printer_data.get('api_key'),
                    printer_data.get('access_code'),
                    printer_data.get('serial_number'),
                    printer_data.get('webcam_url'),
                    printer_data.get('is_active', True)
                )
            )
            logger.info("Printer created", printer_id=printer_data['id'], name=printer_data['name'])
            return True

        except Exception as e:
            logger.error("Failed to create printer",
                        printer_id=printer_data.get('id'),
                        error=str(e),
                        exc_info=True)
            return False

    async def get(self, printer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a printer by ID.

        Args:
            printer_id: Unique printer identifier

        Returns:
            Printer data dictionary or None if not found
        """
        try:
            row = await self._fetch_one("SELECT * FROM printers WHERE id = ?", [printer_id])
            return row

        except Exception as e:
            logger.error("Failed to get printer",
                        printer_id=printer_id,
                        error=str(e),
                        exc_info=True)
            return None

    async def list(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all printers.

        Args:
            active_only: If True, only return active printers

        Returns:
            List of printer dictionaries
        """
        try:
            query = "SELECT * FROM printers"
            params: List[Any] = []

            if active_only:
                query += " WHERE is_active = 1"

            rows = await self._fetch_all(query, params)
            return rows

        except Exception as e:
            logger.error("Failed to list printers",
                        active_only=active_only,
                        error=str(e),
                        exc_info=True)
            return []

    async def update_status(self, printer_id: str, status: str,
                           last_seen: Optional[datetime] = None) -> bool:
        """
        Update printer status and last seen time.

        Args:
            printer_id: Unique printer identifier
            status: New printer status
            last_seen: Last seen timestamp (defaults to now)

        Returns:
            True if update was successful, False otherwise
        """
        try:
            if last_seen is None:
                last_seen = datetime.now()

            await self._execute_write(
                "UPDATE printers SET status = ?, last_seen = ? WHERE id = ?",
                (status, last_seen.isoformat(), printer_id)
            )

            logger.debug("Printer status updated",
                        printer_id=printer_id,
                        status=status)
            return True

        except Exception as e:
            logger.error("Failed to update printer status",
                        printer_id=printer_id,
                        status=status,
                        error=str(e),
                        exc_info=True)
            return False

    async def update(self, printer_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update printer fields.

        Args:
            printer_id: Unique printer identifier
            updates: Dictionary of fields to update

        Returns:
            True if update was successful, False otherwise
        """
        try:
            if not updates:
                return True

            # Build SET clause dynamically
            set_clauses = []
            values = []

            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)

            values.append(printer_id)

            query = f"UPDATE printers SET {', '.join(set_clauses)} WHERE id = ?"

            await self._execute_write(query, tuple(values))

            logger.info("Printer updated",
                       printer_id=printer_id,
                       fields=list(updates.keys()))
            return True

        except Exception as e:
            logger.error("Failed to update printer",
                        printer_id=printer_id,
                        error=str(e),
                        exc_info=True)
            return False

    async def delete(self, printer_id: str) -> bool:
        """
        Delete a printer.

        Args:
            printer_id: Unique printer identifier

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            await self._execute_write(
                "DELETE FROM printers WHERE id = ?",
                (printer_id,)
            )

            logger.info("Printer deleted", printer_id=printer_id)
            return True

        except Exception as e:
            logger.error("Failed to delete printer",
                        printer_id=printer_id,
                        error=str(e),
                        exc_info=True)
            return False

    async def exists(self, printer_id: str) -> bool:
        """
        Check if a printer exists.

        Args:
            printer_id: Unique printer identifier

        Returns:
            True if printer exists, False otherwise
        """
        try:
            row = await self._fetch_one(
                "SELECT 1 FROM printers WHERE id = ?",
                [printer_id]
            )
            return row is not None

        except Exception as e:
            logger.error("Failed to check printer existence",
                        printer_id=printer_id,
                        error=str(e),
                        exc_info=True)
            return False
