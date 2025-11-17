"""
Printer repository for managing printer-related database operations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog

from .base_repository import BaseRepository

logger = structlog.get_logger()


class PrinterRepository(BaseRepository):
    """Repository for printer-related database operations."""

    async def create(self, printer_data: Dict[str, Any]) -> bool:
        """
        Create a new printer record.

        Args:
            printer_data: Dictionary containing printer information
                Required: id, name, type
                Optional: ip_address, api_key, access_code, serial_number, is_active

        Returns:
            True if printer was created successfully, False otherwise
        """
        try:
            await self._execute_write(
                """INSERT INTO printers (id, name, type, ip_address, api_key, access_code, serial_number, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    printer_data['id'],
                    printer_data['name'],
                    printer_data['type'],
                    printer_data.get('ip_address'),
                    printer_data.get('api_key'),
                    printer_data.get('access_code'),
                    printer_data.get('serial_number'),
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
