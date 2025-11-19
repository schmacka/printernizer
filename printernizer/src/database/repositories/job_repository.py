"""
Job repository for managing job-related database operations.

This module provides data access methods for 3D print jobs, including job creation,
tracking, status updates, and analytics queries.

The JobRepository is part of the repository pattern implementation that replaced
the monolithic Database class. It handles all job-related database operations,
making it easy to:

- Create and track print jobs
- Update job status and progress
- Query jobs with flexible filtering
- Generate job statistics and analytics
- Handle duplicate job detection

Database Schema:
    The jobs table tracks all print jobs with the following key fields:
    - id (TEXT PRIMARY KEY): Unique job identifier
    - printer_id (TEXT): Associated printer
    - job_name (TEXT): Name of the print job
    - filename (TEXT): Original file name
    - status (TEXT): Current status (pending, printing, completed, failed, cancelled)
    - start_time (DATETIME): When the job started
    - end_time (DATETIME): When the job finished
    - progress (INTEGER): Print progress (0-100)
    - material_used (REAL): Amount of material used (grams)
    - is_business (BOOLEAN): Whether this is a business order
    - customer_info (TEXT): Customer information (JSON)

    Indexes:
    - idx_jobs_printer_id: Fast lookup by printer
    - idx_jobs_status: Fast filtering by status
    - idx_jobs_unique_print: Prevent duplicate jobs (printer_id + filename + start_time)

Usage Examples:
    ```python
    from src.database.repositories import JobRepository

    # Initialize
    job_repo = JobRepository(db.connection)

    # Create a new job
    job = {
        'id': 'bambu_printer1_20250117_103045',
        'printer_id': 'bambu_a1_001',
        'printer_type': 'bambu_lab',
        'job_name': 'calibration_cube.gcode',
        'filename': 'calibration_cube.3mf',
        'status': 'pending',
        'is_business': False
    }
    success = await job_repo.create(job)

    # Update job status and progress
    await job_repo.update('bambu_printer1_20250117_103045', {
        'status': 'printing',
        'progress': 50,
        'start_time': datetime.now().isoformat()
    })

    # Query jobs
    active_jobs = await job_repo.list(
        printer_id='bambu_a1_001',
        status='printing'
    )

    # Get business jobs only
    business_jobs = await job_repo.list(is_business=True)

    # Get job statistics
    stats = await job_repo.get_statistics()
    print(f"Success rate: {stats['success_rate']}%")
    ```

Error Handling:
    - Duplicate jobs are handled gracefully (returns False from create())
    - All database errors are logged with context
    - Retry logic is inherited from BaseRepository

See Also:
    - src/services/job_service.py - Business logic using this repository
    - src/api/routers/jobs.py - API endpoints
    - docs/technical-debt/COMPLETION-REPORT.md - Phase 1 repository extraction
"""
from typing import Optional, List, Dict, Any
import sqlite3
import structlog

from .base_repository import BaseRepository

logger = structlog.get_logger()


class JobRepository(BaseRepository):
    """
    Repository for job-related database operations.

    Provides CRUD operations and specialized queries for 3D print jobs.
    Handles duplicate detection, status tracking, and job analytics.

    Key Features:
        - Duplicate job detection via UNIQUE constraint
        - Flexible filtering (by printer, status, business flag)
        - Efficient count queries for pagination
        - Date range queries for analytics
        - Job statistics and success rate calculation

    Thread Safety:
        Operations are atomic but the repository is not thread-safe.
        Use connection pooling for concurrent access.
    """

    async def create(self, job_data: Dict[str, Any]) -> bool:
        """
        Create a new job record.

        Args:
            job_data: Dictionary containing job information
                Required: id, printer_id, printer_type, job_name
                Optional: filename, status, start_time, end_time, etc.

        Returns:
            True if job was created successfully, False otherwise
        """
        try:
            # Build dynamic INSERT query based on which fields are provided
            # This allows database DEFAULT values to be used for created_at/updated_at
            columns = ['id', 'printer_id', 'printer_type', 'job_name', 'filename', 'status',
                      'start_time', 'end_time', 'estimated_duration', 'actual_duration', 'progress',
                      'material_used', 'material_cost', 'power_cost', 'is_business', 'customer_info']
            values = [
                job_data['id'],
                job_data['printer_id'],
                job_data['printer_type'],
                job_data['job_name'],
                job_data.get('filename'),
                job_data.get('status', 'pending'),
                job_data.get('start_time'),
                job_data.get('end_time'),
                job_data.get('estimated_duration'),
                job_data.get('actual_duration'),
                job_data.get('progress', 0),
                job_data.get('material_used'),
                job_data.get('material_cost'),
                job_data.get('power_cost'),
                job_data.get('is_business', False),
                job_data.get('customer_info')
            ]

            # Only include created_at/updated_at if explicitly provided (not None)
            if job_data.get('created_at') is not None:
                columns.append('created_at')
                values.append(job_data['created_at'])
            if job_data.get('updated_at') is not None:
                columns.append('updated_at')
                values.append(job_data['updated_at'])

            placeholders = ', '.join(['?' for _ in columns])
            column_str = ', '.join(columns)

            await self._execute_write(
                f"INSERT INTO jobs ({column_str}) VALUES ({placeholders})",
                tuple(values)
            )

            logger.info("Job created",
                       job_id=job_data['id'],
                       printer_id=job_data['printer_id'],
                       job_name=job_data['job_name'])
            return True

        except sqlite3.IntegrityError as e:
            # Handle unique constraint violations gracefully
            error_msg = str(e).lower()
            if 'unique' in error_msg or 'idx_jobs_unique_print' in error_msg:
                logger.info("Duplicate job detected (UNIQUE constraint)",
                           printer_id=job_data.get('printer_id'),
                           filename=job_data.get('filename'),
                           start_time=job_data.get('start_time'))
                # Return False to indicate the job already exists
                return False
            else:
                # Other integrity errors (e.g., foreign key violations)
                logger.error("Database integrity error creating job",
                            error=str(e),
                            job_data=job_data,
                            exc_info=True)
                return False

        except Exception as e:
            logger.error("Failed to create job",
                        job_id=job_data.get('id'),
                        error=str(e),
                        exc_info=True)
            return False

    async def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a job by ID.

        Args:
            job_id: Unique job identifier

        Returns:
            Job data dictionary or None if not found
        """
        try:
            row = await self._fetch_one("SELECT * FROM jobs WHERE id = ?", [job_id])
            return row

        except Exception as e:
            logger.error("Failed to get job",
                        job_id=job_id,
                        error=str(e),
                        exc_info=True)
            return None

    async def list(self, printer_id: Optional[str] = None,
                  status: Optional[str] = None,
                  is_business: Optional[bool] = None,
                  limit: Optional[int] = None,
                  offset: int = 0) -> List[Dict[str, Any]]:
        """
        List jobs with optional filtering.

        Args:
            printer_id: Filter by printer ID
            status: Filter by job status
            is_business: Filter by business flag (True/False/None for all)
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of job dictionaries
        """
        try:
            query = "SELECT * FROM jobs WHERE 1=1"
            params: List[Any] = []

            if printer_id:
                query += " AND printer_id = ?"
                params.append(printer_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            if is_business is not None:
                query += " AND is_business = ?"
                params.append(1 if is_business else 0)

            query += " ORDER BY created_at DESC"

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            rows = await self._fetch_all(query, params)
            return rows

        except Exception as e:
            logger.error("Failed to list jobs",
                        printer_id=printer_id,
                        status=status,
                        is_business=is_business,
                        error=str(e),
                        exc_info=True)
            return []

    async def count(self, printer_id: Optional[str] = None,
                   status: Optional[str] = None,
                   is_business: Optional[bool] = None) -> int:
        """
        Count jobs with optional filtering (efficient COUNT query).

        Args:
            printer_id: Filter by printer ID
            status: Filter by job status
            is_business: Filter by business flag (True/False/None for all)

        Returns:
            Total count of jobs matching filters
        """
        try:
            query = "SELECT COUNT(*) as count FROM jobs WHERE 1=1"
            params: List[Any] = []

            if printer_id:
                query += " AND printer_id = ?"
                params.append(printer_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            if is_business is not None:
                query += " AND is_business = ?"
                params.append(1 if is_business else 0)

            row = await self._fetch_one(query, params)
            return row['count'] if row else 0

        except Exception as e:
            logger.error("Failed to count jobs",
                        printer_id=printer_id,
                        status=status,
                        is_business=is_business,
                        error=str(e),
                        exc_info=True)
            return 0

    async def get_by_date_range(self, start_date: str, end_date: str,
                                printer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get jobs within a date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            printer_id: Optional printer ID filter

        Returns:
            List of job dictionaries
        """
        try:
            query = """
                SELECT * FROM jobs
                WHERE (created_at >= ? AND created_at <= ?)
                   OR (start_time >= ? AND start_time <= ?)
            """
            params: List[Any] = [start_date, end_date, start_date, end_date]

            if printer_id:
                query += " AND printer_id = ?"
                params.append(printer_id)

            query += " ORDER BY created_at DESC"

            rows = await self._fetch_all(query, params)
            return rows

        except Exception as e:
            logger.error("Failed to get jobs by date range",
                        start_date=start_date,
                        end_date=end_date,
                        printer_id=printer_id,
                        error=str(e),
                        exc_info=True)
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get job statistics.

        Returns:
            Dictionary with job statistics
        """
        try:
            # Get total jobs
            total_row = await self._fetch_one("SELECT COUNT(*) as count FROM jobs")
            total_jobs = total_row['count'] if total_row else 0

            # Get jobs by status
            status_rows = await self._fetch_all("""
                SELECT status, COUNT(*) as count
                FROM jobs
                GROUP BY status
            """)

            status_counts = {row['status']: row['count'] for row in status_rows}

            # Calculate success rate
            completed = status_counts.get('completed', 0)
            failed = status_counts.get('failed', 0) + status_counts.get('cancelled', 0)
            total_finished = completed + failed
            success_rate = (completed / total_finished * 100) if total_finished > 0 else 0.0

            return {
                'total_jobs': total_jobs,
                'status_counts': status_counts,
                'completed_jobs': completed,
                'failed_jobs': failed,
                'success_rate': round(success_rate, 2)
            }

        except Exception as e:
            logger.error("Failed to get job statistics",
                        error=str(e),
                        exc_info=True)
            return {
                'total_jobs': 0,
                'status_counts': {},
                'completed_jobs': 0,
                'failed_jobs': 0,
                'success_rate': 0.0
            }

    async def update(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update job fields.

        Args:
            job_id: Unique job identifier
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

            values.append(job_id)

            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = ?"

            await self._execute_write(query, tuple(values))

            logger.debug("Job updated",
                        job_id=job_id,
                        fields=list(updates.keys()))
            return True

        except Exception as e:
            logger.error("Failed to update job",
                        job_id=job_id,
                        error=str(e),
                        exc_info=True)
            return False

    async def delete(self, job_id: str) -> bool:
        """
        Delete a job.

        Args:
            job_id: Unique job identifier

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            await self._execute_write(
                "DELETE FROM jobs WHERE id = ?",
                (job_id,)
            )

            logger.info("Job deleted", job_id=job_id)
            return True

        except Exception as e:
            logger.error("Failed to delete job",
                        job_id=job_id,
                        error=str(e),
                        exc_info=True)
            return False

    async def exists(self, job_id: str) -> bool:
        """
        Check if a job exists.

        Args:
            job_id: Unique job identifier

        Returns:
            True if job exists, False otherwise
        """
        try:
            row = await self._fetch_one(
                "SELECT 1 FROM jobs WHERE id = ?",
                [job_id]
            )
            return row is not None

        except Exception as e:
            logger.error("Failed to check job existence",
                        job_id=job_id,
                        error=str(e),
                        exc_info=True)
            return False
