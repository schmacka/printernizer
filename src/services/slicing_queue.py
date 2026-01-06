"""
Slicing queue service for managing slicing job execution.

Handles job queuing, execution, progress tracking, and WebSocket updates.
"""
import os
import uuid
import asyncio
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import structlog

from src.database.database import Database
from src.services.base_service import BaseService
from src.services.event_service import EventService
from src.services.slicer_service import SlicerService
from src.models.slicer import (
    SlicingJob,
    SlicingJobStatus,
    SlicingJobRequest,
)
from src.utils.exceptions import NotFoundError
from src.utils.config import get_settings

logger = structlog.get_logger()


class SlicingQueue(BaseService):
    """
    Service for managing slicing job queue and execution.

    Responsibilities:
    - Queue management (FIFO with priority)
    - Concurrent job execution (max configurable)
    - Progress monitoring
    - Automatic retry on failure
    - WebSocket progress updates
    - Auto-upload to printer after completion
    """

    def __init__(
        self,
        database: Database,
        event_service: EventService,
        slicer_service: SlicerService,
        file_service=None,
        printer_service=None,
        library_service=None,
    ):
        """
        Initialize slicing queue.

        Args:
            database: Database instance
            event_service: Event service for notifications
            slicer_service: Slicer service instance
            file_service: Optional file service for uploads
            printer_service: Optional printer service for auto-start
            library_service: Optional library service for file access
        """
        super().__init__(database)
        self.event_service = event_service
        self.slicer_service = slicer_service
        self.file_service = file_service
        self.printer_service = printer_service
        self.library_service = library_service
        
        self.settings = get_settings()
        self._running_jobs: Dict[str, asyncio.Task] = {}
        self._max_concurrent = 2
        # Read from env var first, then settings, then default
        default_slicing_dir = os.environ.get(
            "SLICING_OUTPUT_DIR",
            getattr(self.settings, 'slicing_output_dir', '/data/printernizer/sliced')
        )
        self._output_dir = Path(default_slicing_dir)
        self._enabled = True

    async def initialize(self) -> None:
        """Initialize service and load settings."""
        await super().initialize()

        logger.info("Initializing slicing queue")

        # Load settings (database settings override config/env vars)
        self._enabled = await self._get_setting("slicing.enabled", True)
        self._max_concurrent = await self._get_setting("slicing.max_concurrent", 2)

        # For slicing output dir, ALWAYS prefer env var if set
        env_slicing_dir = os.environ.get("SLICING_OUTPUT_DIR")
        if env_slicing_dir:
            output_dir = env_slicing_dir
            logger.info("Using SLICING_OUTPUT_DIR from environment", output_dir=output_dir)
        else:
            # Fall back to database setting or config default
            settings_default = getattr(self.settings, 'slicing_output_dir', '/data/printernizer/sliced')
            output_dir = await self._get_setting("slicing.output_dir", settings_default)
            logger.info("Using slicing output dir from settings/default", output_dir=output_dir)

        self._output_dir = Path(output_dir)
        
        # Create output directory
        self._output_dir.mkdir(parents=True, exist_ok=True)
        
        # Resume queued jobs from previous session
        await self._resume_queued_jobs()
        
        logger.info(
            "Slicing queue initialized",
            enabled=self._enabled,
            max_concurrent=self._max_concurrent,
            output_dir=str(self._output_dir)
        )

    async def shutdown(self) -> None:
        """Shutdown service and cancel running jobs."""
        logger.info("Shutting down slicing queue")
        
        # Cancel all running jobs
        for job_id, task in self._running_jobs.items():
            if not task.done():
                task.cancel()
                await self._update_job_status(job_id, SlicingJobStatus.CANCELLED)
        
        await super().shutdown()

    async def create_job(self, job_request: SlicingJobRequest) -> SlicingJob:
        """
        Create and queue a slicing job.

        Args:
            job_request: Slicing job request

        Returns:
            Created slicing job
        """
        job_id = str(uuid.uuid4())
        now = datetime.now()

        async with self.db.connection() as conn:
            await conn.execute(
                """
                INSERT INTO slicing_jobs (
                    id, file_checksum, slicer_id, profile_id, target_printer_id,
                    status, priority, progress, auto_upload, auto_start,
                    retry_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    job_request.file_checksum,
                    job_request.slicer_id,
                    job_request.profile_id,
                    job_request.target_printer_id,
                    SlicingJobStatus.QUEUED.value,
                    job_request.priority,
                    0,
                    job_request.auto_upload,
                    job_request.auto_start,
                    0,
                    now,
                    now,
                ),
            )
            await conn.commit()

        logger.info(
            "Created slicing job",
            job_id=job_id,
            file_checksum=job_request.file_checksum,
            priority=job_request.priority
        )

        job = await self.get_job(job_id)
        await self.event_service.emit("slicing_job.created", {"job_id": job_id})
        
        # Start processing if slots available
        await self._process_queue()
        
        return job

    async def get_job(self, job_id: str) -> SlicingJob:
        """
        Get slicing job by ID.

        Args:
            job_id: Job ID

        Returns:
            Slicing job

        Raises:
            NotFoundError: If job not found
        """
        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM slicing_jobs WHERE id = ?",
                (job_id,)
            )
            row = await cursor.fetchone()

        if not row:
            raise NotFoundError("Slicing job", job_id)

        return self._row_to_job(row)

    async def list_jobs(
        self,
        status: Optional[SlicingJobStatus] = None,
        limit: int = 50
    ) -> List[SlicingJob]:
        """
        List slicing jobs.

        Args:
            status: Filter by status
            limit: Maximum number of jobs to return

        Returns:
            List of slicing jobs
        """
        query = "SELECT * FROM slicing_jobs WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY priority DESC, created_at ASC LIMIT ?"
        params.append(limit)

        async with self.db.connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

        return [self._row_to_job(row) for row in rows]

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a slicing job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled
        """
        job = await self.get_job(job_id)
        
        if job.status == SlicingJobStatus.COMPLETED:
            logger.warning("Cannot cancel completed job", job_id=job_id)
            return False

        # Cancel running task if exists
        if job_id in self._running_jobs:
            task = self._running_jobs[job_id]
            if not task.done():
                task.cancel()

        await self._update_job_status(job_id, SlicingJobStatus.CANCELLED)
        
        logger.info("Cancelled slicing job", job_id=job_id)
        await self.event_service.emit("slicing_job.cancelled", {"job_id": job_id})
        
        return True

    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a slicing job.

        Args:
            job_id: Job ID

        Returns:
            True if deleted
        """
        job = await self.get_job(job_id)
        
        # Delete output file if exists
        if job.output_file_path:
            try:
                Path(job.output_file_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning("Failed to delete output file", path=job.output_file_path, error=str(e))

        async with self.db.connection() as conn:
            await conn.execute(
                "DELETE FROM slicing_jobs WHERE id = ?",
                (job_id,)
            )
            await conn.commit()

        logger.info("Deleted slicing job", job_id=job_id)
        return True

    async def _resume_queued_jobs(self) -> None:
        """Resume queued jobs from previous session."""
        # Mark running jobs as queued
        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE slicing_jobs SET status = ?, updated_at = ? WHERE status = ?",
                (SlicingJobStatus.QUEUED.value, datetime.now(), SlicingJobStatus.RUNNING.value)
            )
            await conn.commit()

        # Start processing queue
        await self._process_queue()

    async def _process_queue(self) -> None:
        """Process queued jobs if slots available."""
        if not self._enabled:
            return

        # Check available slots
        active_count = len([t for t in self._running_jobs.values() if not t.done()])
        if active_count >= self._max_concurrent:
            return

        # Get next queued job
        jobs = await self.list_jobs(status=SlicingJobStatus.QUEUED, limit=1)
        if not jobs:
            return

        job = jobs[0]
        
        # Start job processing
        task = asyncio.create_task(self._execute_job(job.id))
        self._running_jobs[job.id] = task
        
        # Continue processing if more slots available
        if active_count + 1 < self._max_concurrent:
            await self._process_queue()

    async def _execute_job(self, job_id: str) -> None:
        """
        Execute a slicing job.

        Args:
            job_id: Job ID
        """
        try:
            job = await self.get_job(job_id)
            
            # Update status to running
            await self._update_job_status(job_id, SlicingJobStatus.RUNNING)
            await self._update_job_progress(job_id, 0)
            
            # Get slicer and profile
            slicer = await self.slicer_service.get_slicer(job.slicer_id)
            profile = await self.slicer_service.get_profile(job.profile_id)
            
            # Verify slicer is available
            is_available = await self.slicer_service.verify_slicer_availability(job.slicer_id)
            if not is_available:
                raise Exception("Slicer is not available")
            
            # Get input file from library
            if not self.library_service:
                raise Exception("Library service not available")
            
            library_file = await self.library_service.get_file_by_checksum(job.file_checksum)
            if not library_file or not library_file.get("file_path"):
                raise Exception("Library file not found")
            
            input_file = Path(library_file["file_path"])
            if not input_file.exists():
                raise Exception(f"Input file not found: {input_file}")
            
            # Prepare output file
            output_filename = f"{input_file.stem}_{job_id[:8]}.gcode"
            output_file = self._output_dir / output_filename
            
            await self._update_job_progress(job_id, 10)
            
            # Build slicing command
            cmd = [
                str(slicer.executable_path),
                "--export-gcode",
                "--output", str(output_file),
            ]
            
            # Add profile if path exists
            if profile.profile_path and Path(profile.profile_path).exists():
                cmd.extend(["--load", str(profile.profile_path)])
            
            cmd.append(str(input_file))
            
            logger.info(
                "Starting slicing",
                job_id=job_id,
                slicer=slicer.name,
                profile=profile.profile_name,
                input_file=str(input_file)
            )
            
            await self._update_job_progress(job_id, 20)
            
            # Execute slicing command
            timeout = await self._get_setting("slicing.timeout_seconds", 3600)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress with timeout tracking
            start_time = asyncio.get_event_loop().time()
            progress_steps = [30, 40, 50, 60, 70, 80, 90]
            step_interval = 5  # Fixed 5-second interval between progress updates
            
            for progress in progress_steps:
                # Check if we've exceeded timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    process.kill()
                    raise Exception("Slicing timed out")
                
                await asyncio.sleep(step_interval)
                if process.returncode is not None:
                    break
                await self._update_job_progress(job_id, progress)
            
            # Wait for completion with remaining timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            remaining_timeout = max(1, timeout - elapsed)
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=remaining_timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise Exception("Slicing timed out")
            
            if process.returncode != 0:
                # stderr is already bytes from communicate()
                error_msg = stderr.decode('utf-8', errors='ignore') if isinstance(stderr, bytes) else str(stderr)
                raise Exception(f"Slicing failed: {error_msg}")
            
            if not output_file.exists():
                raise Exception("Output file was not created")
            
            # Parse G-code metadata (simplified)
            # TODO: Extract estimated time and filament usage from G-code
            
            # Update job with results
            async with self.db.connection() as conn:
                await conn.execute(
                    """
                    UPDATE slicing_jobs
                    SET output_file_path = ?,
                        status = ?,
                        progress = ?,
                        completed_at = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        str(output_file),
                        SlicingJobStatus.COMPLETED.value,
                        100,
                        datetime.now(),
                        datetime.now(),
                        job_id,
                    )
                )
                await conn.commit()
            
            logger.info(
                "Slicing completed",
                job_id=job_id,
                output_file=str(output_file)
            )
            
            await self.event_service.emit("slicing_job.completed", {"job_id": job_id})
            
            # Handle auto-upload if enabled
            if job.auto_upload and job.target_printer_id:
                await self._handle_auto_upload(job_id)
            
        except asyncio.CancelledError:
            logger.info("Slicing job cancelled", job_id=job_id)
            await self._update_job_status(job_id, SlicingJobStatus.CANCELLED)
            
        except Exception as e:
            logger.error("Slicing job failed", job_id=job_id, error=str(e))
            
            # Check if should retry
            job = await self.get_job(job_id)
            auto_retry = await self._get_setting("slicing.auto_retry", True)
            max_retries = await self._get_setting("slicing.max_retries", 3)
            
            if auto_retry and job.retry_count < max_retries:
                # Increment retry count and re-queue
                async with self.db.connection() as conn:
                    await conn.execute(
                        """
                        UPDATE slicing_jobs
                        SET retry_count = retry_count + 1,
                            status = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (SlicingJobStatus.QUEUED.value, datetime.now(), job_id)
                    )
                    await conn.commit()
                
                logger.info("Re-queuing failed job", job_id=job_id, retry_count=job.retry_count + 1)
            else:
                # Mark as failed
                async with self.db.connection() as conn:
                    await conn.execute(
                        """
                        UPDATE slicing_jobs
                        SET status = ?,
                            error_message = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (SlicingJobStatus.FAILED.value, str(e), datetime.now(), job_id)
                    )
                    await conn.commit()
                
                await self.event_service.emit("slicing_job.failed", {"job_id": job_id, "error": str(e)})
        
        finally:
            # Remove from running jobs
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]
            
            # Process next job in queue
            await self._process_queue()

    async def _handle_auto_upload(self, job_id: str) -> None:
        """
        Handle auto-upload of sliced file to printer.

        Args:
            job_id: Job ID
        """
        try:
            job = await self.get_job(job_id)
            
            if not job.output_file_path or not job.target_printer_id:
                return
            
            if not self.file_service:
                logger.warning("File service not available for auto-upload")
                return
            
            logger.info(
                "Auto-uploading sliced file",
                job_id=job_id,
                printer_id=job.target_printer_id
            )
            
            # TODO: Implement file upload to printer
            # await self.file_service.upload_to_printer(
            #     job.target_printer_id,
            #     job.output_file_path
            # )
            
            # Handle auto-start if enabled
            if job.auto_start and self.printer_service:
                # TODO: Implement auto-start
                pass
            
        except Exception as e:
            logger.error("Auto-upload failed", job_id=job_id, error=str(e))

    async def _update_job_status(self, job_id: str, status: SlicingJobStatus) -> None:
        """Update job status."""
        async with self.db.connection() as conn:
            updates = {"status": status.value, "updated_at": datetime.now()}
            
            if status == SlicingJobStatus.RUNNING:
                updates["started_at"] = datetime.now()
            elif status in (SlicingJobStatus.COMPLETED, SlicingJobStatus.FAILED, SlicingJobStatus.CANCELLED):
                updates["completed_at"] = datetime.now()
            
            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values())
            values.append(job_id)
            
            await conn.execute(
                f"UPDATE slicing_jobs SET {set_clause} WHERE id = ?",
                values
            )
            await conn.commit()
        
        await self.event_service.emit("slicing_job.status_changed", {
            "job_id": job_id,
            "status": status.value
        })

    async def _update_job_progress(self, job_id: str, progress: int) -> None:
        """Update job progress."""
        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE slicing_jobs SET progress = ?, updated_at = ? WHERE id = ?",
                (progress, datetime.now(), job_id)
            )
            await conn.commit()
        
        await self.event_service.emit("slicing_job.progress", {
            "job_id": job_id,
            "progress": progress
        })

    async def _get_setting(self, key: str, default: Any) -> Any:
        """Get setting from database or return default."""
        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "SELECT value, value_type FROM configuration WHERE key = ?",
                (key,)
            )
            row = await cursor.fetchone()

        if not row:
            return default

        value, value_type = row
        
        if value_type == "boolean":
            return value.lower() in ("true", "1", "yes")
        elif value_type == "integer":
            return int(value)
        elif value_type == "float":
            return float(value)
        else:
            return value

    def _row_to_job(self, row) -> SlicingJob:
        """Convert database row to SlicingJob."""
        return SlicingJob(
            id=row[0],
            file_checksum=row[1],
            slicer_id=row[2],
            profile_id=row[3],
            target_printer_id=row[4],
            status=row[5],
            priority=row[6],
            progress=row[7],
            output_file_path=row[8],
            output_gcode_checksum=row[9],
            estimated_print_time=row[10],
            filament_used=row[11],
            error_message=row[12],
            retry_count=row[13],
            auto_upload=bool(row[14]),
            auto_start=bool(row[15]),
            started_at=datetime.fromisoformat(row[16]) if row[16] else None,
            completed_at=datetime.fromisoformat(row[17]) if row[17] else None,
            created_at=datetime.fromisoformat(row[18]),
            updated_at=datetime.fromisoformat(row[19]),
        )
