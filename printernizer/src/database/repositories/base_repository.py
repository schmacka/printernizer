"""
Base repository class providing common database operations.

This module implements the Repository Pattern, which provides a clean abstraction
over database operations and separates data access logic from business logic.

Design Principles:
    - Single Responsibility: Each repository handles one domain entity
    - DRY (Don't Repeat Yourself): Common CRUD operations in base class
    - Error Handling: Consistent retry logic and error logging
    - Type Safety: Full type hints for better IDE support

Architecture:
    The repository pattern was introduced in Phase 1 of technical debt remediation
    to break up the monolithic Database class (2,344 LOC) into focused,
    maintainable components.

    BaseRepository → Provides common operations
        ├── JobRepository → Job-related operations
        ├── FileRepository → File management
        ├── PrinterRepository → Printer configuration
        ├── IdeaRepository → Idea/model management
        ├── LibraryRepository → Library sources
        ├── SnapshotRepository → Camera snapshots
        ├── TrendingRepository → Trending models cache
        └── MaterialRepository → Material spool tracking

Usage Example:
    ```python
    from src.database.repositories import JobRepository

    # Initialize repository with database connection
    db = Database(db_path)
    await db.connect()
    job_repo = JobRepository(db.connection)

    # Create a job
    job_data = {
        'id': 'job_123',
        'printer_id': 'printer_1',
        'job_name': 'test_print.gcode',
        'status': 'pending'
    }
    success = await job_repo.create(job_data)

    # Query jobs
    jobs = await job_repo.list(printer_id='printer_1', status='completed')

    # Update a job
    await job_repo.update('job_123', {'status': 'printing', 'progress': 50})
    ```

See Also:
    - docs/technical-debt/COMPLETION-REPORT.md - Phase 1 repository extraction
    - src/services/ - Services that use these repositories
"""
from typing import Optional, List, Dict, Any
import aiosqlite
import structlog

logger = structlog.get_logger()


class BaseRepository:
    """
    Base class for all repositories providing common database operations.

    This abstract base class provides common CRUD (Create, Read, Update, Delete)
    operations that are inherited by all specialized repositories. It handles:

    - Database connection management
    - Retry logic for locked database errors
    - Consistent error handling and logging
    - Row-to-dictionary conversion

    All repositories should inherit from this class to ensure consistent behavior
    across the application.

    Attributes:
        connection (aiosqlite.Connection): Active database connection shared
            across all repository operations.

    Error Handling:
        Write operations automatically retry up to 3 times if the database is locked
        (common with SQLite under concurrent access). All errors are logged with
        context for debugging.

    Thread Safety:
        While individual operations are atomic, the repository itself is not
        thread-safe. Use connection pooling (Database.pooled_connection()) for
        concurrent access.
    """

    def __init__(self, connection: aiosqlite.Connection):
        """
        Initialize the repository with a database connection.

        Args:
            connection: Active aiosqlite database connection. This should be
                obtained from Database.connection or Database.pooled_connection().

        Example:
            ```python
            db = Database(db_path)
            await db.connect()
            repo = JobRepository(db.connection)
            ```
        """
        self.connection = connection

    async def _execute_write(self, sql: str, params: Optional[tuple] = None,
                             retry_count: int = 3) -> Optional[int]:
        """
        Execute a write operation (INSERT, UPDATE, DELETE) with retry logic.

        This method automatically handles database locked errors by retrying the
        operation. This is essential for SQLite which can have lock contention
        under concurrent access (even with WAL mode enabled).

        Args:
            sql: SQL query to execute (INSERT, UPDATE, DELETE, etc.)
            params: Query parameters as a tuple (prevents SQL injection)
            retry_count: Number of retries for locked database (default: 3)

        Returns:
            Last row ID for INSERT operations, None for UPDATE/DELETE

        Raises:
            aiosqlite.OperationalError: If database is locked after all retries
            Exception: For any other database errors

        Example:
            ```python
            # Insert with auto-retry on lock
            last_id = await self._execute_write(
                "INSERT INTO jobs (id, name) VALUES (?, ?)",
                ("job_123", "Test Job")
            )

            # Update with retry logic
            await self._execute_write(
                "UPDATE jobs SET status = ? WHERE id = ?",
                ("completed", "job_123")
            )
            ```

        Note:
            The retry logic helps with SQLite's locking behavior but doesn't
            replace proper connection pooling for high concurrency scenarios.
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

        Executes a SELECT query and returns the first row as a dictionary with
        column names as keys. Returns None if no rows match the query.

        Args:
            sql: SQL SELECT query to execute
            params: Query parameters as a list (prevents SQL injection)

        Returns:
            Dictionary representation of the row with column names as keys,
            or None if no row found

        Raises:
            Exception: For any database errors (logged automatically)

        Example:
            ```python
            # Fetch a specific job
            job = await self._fetch_one(
                "SELECT * FROM jobs WHERE id = ?",
                ["job_123"]
            )
            if job:
                print(f"Job name: {job['job_name']}")
                print(f"Status: {job['status']}")

            # With multiple conditions
            active_job = await self._fetch_one(
                "SELECT * FROM jobs WHERE printer_id = ? AND status = ?",
                ["printer_1", "printing"]
            )
            ```

        Note:
            Automatically converts sqlite3.Row objects to dictionaries for
            easier access and JSON serialization.
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

        Executes a SELECT query and returns all matching rows as a list of
        dictionaries with column names as keys. Returns an empty list if no
        rows match the query.

        Args:
            sql: SQL SELECT query to execute
            params: Query parameters as a list (prevents SQL injection)

        Returns:
            List of dictionaries, each representing a row with column names as keys.
            Returns empty list if no rows found.

        Raises:
            Exception: For any database errors (logged automatically)

        Example:
            ```python
            # Fetch all jobs for a printer
            jobs = await self._fetch_all(
                "SELECT * FROM jobs WHERE printer_id = ?",
                ["printer_1"]
            )
            for job in jobs:
                print(f"{job['job_name']}: {job['status']}")

            # With sorting and limiting
            recent_jobs = await self._fetch_all(
                \"\"\"SELECT * FROM jobs
                   WHERE status = ?
                   ORDER BY created_at DESC
                   LIMIT ?\"\"\",
                ["completed", 10]
            )

            # Complex query with aggregation
            stats = await self._fetch_all(
                \"\"\"SELECT printer_id, COUNT(*) as job_count
                   FROM jobs
                   WHERE status = ?
                   GROUP BY printer_id\"\"\",
                ["completed"]
            )
            ```

        Performance Note:
            For large result sets, consider using pagination with LIMIT and OFFSET
            to avoid loading all rows into memory at once.
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
