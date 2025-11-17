"""
Base repository class providing common database operations.
"""
from typing import Optional, List, Dict, Any
import aiosqlite
import structlog

logger = structlog.get_logger()


class BaseRepository:
    """Base class for all repositories providing common database operations."""

    def __init__(self, connection: aiosqlite.Connection):
        """
        Initialize the repository with a database connection.

        Args:
            connection: Active aiosqlite database connection
        """
        self.connection = connection

    async def _execute_write(self, sql: str, params: Optional[tuple] = None,
                             retry_count: int = 3) -> Optional[int]:
        """
        Execute a write operation (INSERT, UPDATE, DELETE) with retry logic.

        Args:
            sql: SQL query to execute
            params: Query parameters
            retry_count: Number of retries for locked database

        Returns:
            Last row ID for INSERT operations, None otherwise
        """
        for attempt in range(retry_count):
            try:
                cursor = await self.connection.execute(sql, params or ())
                await self.connection.commit()
                return cursor.lastrowid
            except aiosqlite.OperationalError as e:
                if "locked" in str(e).lower() and attempt < retry_count - 1:
                    logger.warning(f"Database locked, retrying... (attempt {attempt + 1}/{retry_count})")
                    continue
                else:
                    logger.error("Database write operation failed",
                               sql=sql[:100], error=str(e), exc_info=True)
                    raise
            except Exception as e:
                logger.error("Unexpected error in database write",
                           sql=sql[:100], error=str(e), exc_info=True)
                raise

        return None

    async def _fetch_one(self, sql: str, params: Optional[List[Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from the database.

        Args:
            sql: SQL query to execute
            params: Query parameters

        Returns:
            Dictionary representation of the row, or None if not found
        """
        try:
            cursor = await self.connection.execute(sql, params or [])
            row = await cursor.fetchone()

            if row is None:
                return None

            # Convert row to dictionary using column names
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))

        except Exception as e:
            logger.error("Error fetching single row",
                        sql=sql[:100], error=str(e), exc_info=True)
            raise

    async def _fetch_all(self, sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch all rows from the database.

        Args:
            sql: SQL query to execute
            params: Query parameters

        Returns:
            List of dictionaries, each representing a row
        """
        try:
            cursor = await self.connection.execute(sql, params or [])
            rows = await cursor.fetchall()

            if not rows:
                return []

            # Convert rows to dictionaries using column names
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logger.error("Error fetching multiple rows",
                        sql=sql[:100], error=str(e), exc_info=True)
            raise
