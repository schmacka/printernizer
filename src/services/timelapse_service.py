"""
Timelapse service for managing timelapse video creation.
Handles folder monitoring, auto-detection, and video processing.
"""
from typing import List, Dict, Any, Optional
import uuid
import asyncio
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path
import structlog

from src.config.constants import PollingIntervals
from src.database.database import Database
from src.services.event_service import EventService
from src.models.timelapse import (
    Timelapse,
    TimelapseStatus,
    TimelapseCreate,
    TimelapseUpdate,
    TimelapseStats,
    TimelapseBulkDeleteResult
)
from src.utils.config import get_settings

logger = structlog.get_logger()


class TimelapseService:
    """Service for managing timelapse videos."""

    def __init__(self, database: Database, event_service: EventService):
        """Initialize timelapse service."""
        self.database = database
        self.event_service = event_service
        self.settings = get_settings()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._queue_task: Optional[asyncio.Task] = None
        self._shutdown = False

    async def start(self) -> None:
        """Start timelapse service background tasks."""
        if not self.settings.timelapse_enabled:
            logger.info("Timelapse feature disabled in settings")
            return

        # Check if FlickerFree script exists
        flickerfree_path = Path(self.settings.timelapse_flickerfree_path)
        if not flickerfree_path.exists():
            logger.warning(
                "FlickerFree script not found, timelapse feature will be unavailable",
                path=str(flickerfree_path)
            )
            return

        logger.info("Starting timelapse service")

        # Start background tasks
        self._shutdown = False
        self._monitoring_task = asyncio.create_task(self._folder_monitor_loop())
        self._queue_task = asyncio.create_task(self._process_queue_loop())

        logger.info("Timelapse service started")

    async def shutdown(self) -> None:
        """Shutdown timelapse service and cancel background tasks."""
        logger.info("Shutting down timelapse service")
        self._shutdown = True

        # Cancel monitoring task
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        # Cancel queue processing task
        if self._queue_task and not self._queue_task.done():
            self._queue_task.cancel()
            try:
                await self._queue_task
            except asyncio.CancelledError:
                pass

        logger.info("Timelapse service shutdown complete")

    async def _folder_monitor_loop(self):
        """Background task to monitor source folder for new timelapse folders."""
        logger.info("Starting folder monitoring loop")

        while not self._shutdown:
            try:
                await self._scan_source_folders()
            except Exception as e:
                logger.error("Folder monitoring error", error=str(e), error_type=type(e).__name__)

            # Wait 30 seconds before next scan
            await asyncio.sleep(PollingIntervals.TIMELAPSE_CHECK_INTERVAL)

    async def _scan_source_folders(self):
        """Scan source folder for timelapse image subfolders."""
        source_folder = Path(self.settings.timelapse_source_folder)

        # Check if source folder exists
        if not source_folder.exists():
            logger.warning("Timelapse source folder does not exist", path=str(source_folder))
            return

        logger.debug("Scanning source folder for timelapses", path=str(source_folder))

        # List subfolders
        try:
            subfolders = [f for f in source_folder.iterdir() if f.is_dir() and not f.name.startswith('.')]
        except Exception as e:
            logger.error("Failed to list source folder contents", path=str(source_folder), error=str(e))
            return

        for subfolder in subfolders:
            try:
                await self._process_subfolder(subfolder)
            except Exception as e:
                logger.error("Failed to process subfolder", folder=subfolder.name, error=str(e))

        logger.debug("Folder scan complete", folders_found=len(subfolders))

    async def _process_subfolder(self, subfolder: Path):
        """Process a single subfolder - count images and track status."""
        folder_name = subfolder.name
        source_folder_path = str(subfolder)

        # Count image files
        image_extensions = {'.jpg', '.jpeg', '.png'}
        try:
            image_files = [
                f for f in subfolder.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]
            image_count = len(image_files)
        except Exception as e:
            logger.error("Failed to count images in folder", folder=folder_name, error=str(e))
            return

        # Skip folders with no images
        if image_count == 0:
            return

        # Check if timelapse already tracked
        existing = await self.get_timelapse_by_source_folder(source_folder_path)

        if not existing:
            # Create new timelapse record
            await self._create_timelapse(source_folder_path, folder_name, image_count)
        else:
            # Update existing timelapse
            await self._update_existing_timelapse(existing, image_count)

    async def _create_timelapse(self, source_folder: str, folder_name: str, image_count: int):
        """Create a new timelapse record."""
        timelapse_id = str(uuid.uuid4())
        now = datetime.now()

        data = {
            'id': timelapse_id,
            'source_folder': source_folder,
            'folder_name': folder_name,
            'status': TimelapseStatus.DISCOVERED.value,
            'image_count': image_count,
            'last_image_detected_at': now.isoformat(),
            'auto_process_eligible_at': (now + timedelta(seconds=self.settings.timelapse_auto_process_timeout)).isoformat(),
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }

        await self.database.execute(
            """
            INSERT INTO timelapses (
                id, source_folder, folder_name, status, image_count,
                last_image_detected_at, auto_process_eligible_at, retry_count, pinned,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
            """,
            (
                data['id'], data['source_folder'], data['folder_name'], data['status'],
                data['image_count'], data['last_image_detected_at'], data['auto_process_eligible_at'],
                data['created_at'], data['updated_at']
            )
        )

        logger.info("Created new timelapse", timelapse_id=timelapse_id, folder=folder_name, images=image_count)

        # Emit WebSocket event
        await self.event_service.emit('timelapse.discovered', {
            'id': timelapse_id,
            'folder_name': folder_name,
            'image_count': image_count,
            'status': TimelapseStatus.DISCOVERED.value
        })

    async def _update_existing_timelapse(self, existing: Dict[str, Any], new_image_count: int):
        """Update existing timelapse if image count changed."""
        old_image_count = existing.get('image_count', 0)

        if new_image_count > old_image_count:
            # New images detected
            now = datetime.now()
            new_eligible_at = now + timedelta(seconds=self.settings.timelapse_auto_process_timeout)

            await self.database.execute(
                """
                UPDATE timelapses
                SET image_count = ?,
                    last_image_detected_at = ?,
                    auto_process_eligible_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (new_image_count, now.isoformat(), new_eligible_at.isoformat(), now.isoformat(), existing['id'])
            )

            logger.info(
                "Updated timelapse with new images",
                timelapse_id=existing['id'],
                old_count=old_image_count,
                new_count=new_image_count
            )

        # Check if auto-processing should be triggered
        if existing['status'] == TimelapseStatus.DISCOVERED.value:
            eligible_at = datetime.fromisoformat(existing['auto_process_eligible_at'])
            if datetime.now() >= eligible_at:
                # Mark as pending
                await self.database.execute(
                    "UPDATE timelapses SET status = ?, updated_at = ? WHERE id = ?",
                    (TimelapseStatus.PENDING.value, datetime.now().isoformat(), existing['id'])
                )

                logger.info("Timelapse moved to pending (timeout reached)", timelapse_id=existing['id'])

                await self.event_service.emit('timelapse.pending', {
                    'id': existing['id'],
                    'folder_name': existing['folder_name'],
                    'status': TimelapseStatus.PENDING.value
                })

    async def _process_queue_loop(self):
        """Background task to process pending timelapses."""
        logger.info("Starting queue processing loop")

        while not self._shutdown:
            try:
                await self._process_queue()
            except Exception as e:
                logger.error("Queue processing error", error=str(e), error_type=type(e).__name__)

            # Wait 10 seconds before next check
            await asyncio.sleep(PollingIntervals.TIMELAPSE_FRAME_INTERVAL)

    async def _process_queue(self):
        """Check for pending timelapses and process next one if none currently processing."""
        # Check if any timelapse is currently processing
        result = await self.database._fetch_one(
            "SELECT COUNT(*) as count FROM timelapses WHERE status = ?",
            (TimelapseStatus.PROCESSING.value,)
        )

        if result and result['count'] > 0:
            # Already processing one, wait
            return

        # Get next pending timelapse (FIFO)
        result = await self.database._fetch_one(
            """
            SELECT * FROM timelapses
            WHERE status = ?
            ORDER BY auto_process_eligible_at ASC
            LIMIT 1
            """,
            (TimelapseStatus.PENDING.value,)
        )

        if result:
            logger.info("Found pending timelapse, starting processing", timelapse_id=result['id'])
            # Process in background to avoid blocking queue loop
            asyncio.create_task(self._process_timelapse(result['id']))


    async def _process_timelapse(self, timelapse_id: str):
        """Process a timelapse by calling FlickerFree script."""
        try:
            # Load timelapse record
            timelapse = await self.get_timelapse(timelapse_id)
            if not timelapse:
                logger.error("Timelapse not found for processing", timelapse_id=timelapse_id)
                return

            # Update status to processing
            now = datetime.now()
            await self.database.execute(
                "UPDATE timelapses SET status = ?, processing_started_at = ?, updated_at = ? WHERE id = ?",
                (TimelapseStatus.PROCESSING.value, now.isoformat(), now.isoformat(), timelapse_id)
            )

            logger.info("Started processing timelapse", timelapse_id=timelapse_id, folder=timelapse['folder_name'])

            # Emit WebSocket event
            await self.event_service.emit('timelapse.processing', {
                'id': timelapse_id,
                'folder_name': timelapse['folder_name'],
                'status': TimelapseStatus.PROCESSING.value
            })

            # Determine output path
            output_path = self._determine_output_path(timelapse)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build FlickerFree command
            flickerfree_script = Path(self.settings.timelapse_flickerfree_path)
            source_folder = Path(timelapse['source_folder'])

            cmd = [
                str(flickerfree_script),
                str(source_folder),
                str(output_path)
            ]

            logger.info(
                "Executing FlickerFree command",
                timelapse_id=timelapse_id,
                command=" ".join(cmd)
            )

            # Execute subprocess with timeout (30 minutes)
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=1800  # 30 minutes
                )

                stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
                stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""

                if process.returncode == 0:
                    # Success!
                    await self._handle_processing_success(timelapse_id, output_path, stdout_str)
                else:
                    # Failed
                    error_msg = self._parse_error_message(stderr_str, stdout_str, process.returncode)
                    await self._handle_processing_failure(timelapse_id, error_msg)

            except asyncio.TimeoutError:
                logger.error("Timelapse processing timeout", timelapse_id=timelapse_id)
                await self._handle_processing_failure(
                    timelapse_id,
                    "Processing exceeded 30-minute timeout. Try with fewer images or increase timeout."
                )

            except FileNotFoundError:
                logger.error("FlickerFree script not found", path=str(flickerfree_script))
                await self._handle_processing_failure(
                    timelapse_id,
                    f"FlickerFree script not found at {flickerfree_script}. Please configure correct path."
                )

        except Exception as e:
            logger.error("Unexpected error during processing", timelapse_id=timelapse_id, error=str(e), error_type=type(e).__name__)
            await self._handle_processing_failure(timelapse_id, f"Unexpected error: {str(e)}")

    def _determine_output_path(self, timelapse: Dict[str, Any]) -> Path:
        """Determine output video path based on configuration strategy."""
        folder_name = timelapse['folder_name']
        video_filename = f"{folder_name}.mp4"

        strategy = self.settings.timelapse_output_strategy

        if strategy == "same":
            # Output in same folder as images
            return Path(timelapse['source_folder']) / video_filename
        elif strategy == "both":
            # Output in both locations (primary is separate folder)
            return Path(self.settings.timelapse_output_folder) / video_filename
        else:  # "separate" (default)
            return Path(self.settings.timelapse_output_folder) / video_filename

    def _parse_error_message(self, stderr: str, stdout: str, returncode: int) -> str:
        """Parse error message from FlickerFree output."""
        combined_output = f"{stderr}\n{stdout}".lower()

        # Check for common errors
        if "ffmpeg: not found" in combined_output or "ffmpeg" in combined_output and "not found" in combined_output:
            return "FlickerFree requires ffmpeg to be installed. Please install ffmpeg and try again."

        if "no space left" in combined_output or "disk full" in combined_output:
            return "Not enough disk space to create video. Free up space and retry."

        if "decode error" in combined_output or "corrupt" in combined_output:
            return "Unable to read one or more image files. Check source folder for corrupted images."

        if "permission denied" in combined_output:
            return "Permission denied accessing files. Check file permissions."

        if returncode == 126:
            return "Permission denied executing FlickerFree script. Check file permissions (chmod +x)."

        # Generic error with stderr if available
        if stderr.strip():
            return f"FlickerFree error (code {returncode}): {stderr.strip()[:200]}"

        return f"FlickerFree exited with code {returncode}. Check logs for details."

    async def _handle_processing_success(self, timelapse_id: str, output_path: Path, stdout: str):
        """Handle successful video processing."""
        try:
            # Get video file info
            if not output_path.exists():
                raise FileNotFoundError(f"Output video not found at {output_path}")

            file_size = output_path.stat().st_size

            # Try to extract duration from ffmpeg output in stdout
            video_duration = self._extract_video_duration(stdout)

            # Update database
            now = datetime.now()
            await self.database.execute(
                """
                UPDATE timelapses
                SET status = ?,
                    output_video_path = ?,
                    file_size_bytes = ?,
                    video_duration = ?,
                    processing_completed_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    TimelapseStatus.COMPLETED.value,
                    str(output_path),
                    file_size,
                    video_duration,
                    now.isoformat(),
                    now.isoformat(),
                    timelapse_id
                )
            )

            # Reload timelapse
            timelapse = await self.get_timelapse(timelapse_id)

            logger.info(
                "Timelapse processing completed successfully",
                timelapse_id=timelapse_id,
                output_path=str(output_path),
                file_size_mb=round(file_size / (1024 * 1024), 2)
            )

            # Handle "both" strategy - copy to source folder
            if self.settings.timelapse_output_strategy == "both":
                source_copy = Path(timelapse['source_folder']) / output_path.name
                try:
                    import shutil
                    shutil.copy2(output_path, source_copy)
                    logger.info("Copied video to source folder", dest=str(source_copy))
                except Exception as e:
                    logger.warning("Failed to copy video to source folder", error=str(e))

            # Try to match to job
            await self._match_to_job(timelapse_id)

            # Emit WebSocket event
            await self.event_service.emit('timelapse.completed', {
                'id': timelapse_id,
                'folder_name': timelapse['folder_name'],
                'status': TimelapseStatus.COMPLETED.value,
                'output_video_path': str(output_path),
                'file_size_bytes': file_size,
                'video_duration': video_duration,
                'job_id': timelapse.get('job_id')
            })

        except Exception as e:
            logger.error("Error handling processing success", timelapse_id=timelapse_id, error=str(e))
            await self._handle_processing_failure(timelapse_id, f"Post-processing error: {str(e)}")

    def _extract_video_duration(self, output: str) -> Optional[float]:
        """Extract video duration from ffmpeg output."""
        try:
            # Look for Duration: HH:MM:SS.mm pattern
            duration_match = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', output)
            if duration_match:
                hours, minutes, seconds, centiseconds = map(int, duration_match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
                return round(total_seconds, 2)
        except Exception as e:
            logger.debug("Could not extract video duration", error=str(e))

        return None

    async def _handle_processing_failure(self, timelapse_id: str, error_message: str):
        """Handle processing failure with retry logic."""
        try:
            # Get current retry count
            result = await self.database._fetch_one(
                "SELECT retry_count FROM timelapses WHERE id = ?",
                (timelapse_id,)
            )

            current_retry_count = result['retry_count'] if result else 0
            new_retry_count = current_retry_count + 1

            # Check if should retry (max 1 retry)
            if new_retry_count <= 1:
                # Reset to pending for retry
                await self.database.execute(
                    """
                    UPDATE timelapses
                    SET status = ?,
                        retry_count = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (TimelapseStatus.PENDING.value, new_retry_count, datetime.now().isoformat(), timelapse_id)
                )

                logger.info(
                    "Timelapse processing failed, will retry",
                    timelapse_id=timelapse_id,
                    retry_count=new_retry_count,
                    error=error_message
                )
            else:
                # Mark as failed (no more retries)
                await self.database.execute(
                    """
                    UPDATE timelapses
                    SET status = ?,
                        error_message = ?,
                        retry_count = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        TimelapseStatus.FAILED.value,
                        error_message,
                        new_retry_count,
                        datetime.now().isoformat(),
                        timelapse_id
                    )
                )

                logger.error(
                    "Timelapse processing failed permanently",
                    timelapse_id=timelapse_id,
                    retry_count=new_retry_count,
                    error=error_message
                )

                # Emit WebSocket event
                timelapse = await self.get_timelapse(timelapse_id)
                await self.event_service.emit('timelapse.failed', {
                    'id': timelapse_id,
                    'folder_name': timelapse.get('folder_name'),
                    'status': TimelapseStatus.FAILED.value,
                    'error_message': error_message,
                    'retry_count': new_retry_count
                })

        except Exception as e:
            logger.error("Error handling processing failure", timelapse_id=timelapse_id, error=str(e))

    async def _match_to_job(self, timelapse_id: str):
        """Try to automatically match timelapse to a print job."""
        try:
            timelapse = await self.get_timelapse(timelapse_id)
            if not timelapse:
                return

            folder_name = timelapse['folder_name']

            # Extract patterns from folder name
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{8})',
                r'(\d{4}_\d{2}_\d{2})'
            ]

            found_date = None
            for pattern in date_patterns:
                match = re.search(pattern, folder_name)
                if match:
                    found_date = match.group(1)
                    break

            # Extract potential filename
            filename_pattern = r'([a-zA-Z0-9_-]+)\.(3mf|stl|gcode|obj)'
            filename_match = re.search(filename_pattern, folder_name, re.IGNORECASE)
            potential_filename = filename_match.group(0) if filename_match else None

            matches = []

            if potential_filename:
                result = await self.database._fetch_all(
                    """
                    SELECT id, job_name, filename, printer_id, created_at
                    FROM jobs
                    WHERE filename LIKE ? OR job_name LIKE ?
                    LIMIT 5
                    """,
                    (f"%{potential_filename}%", f"%{potential_filename}%")
                )
                matches.extend(result)

            if found_date and not matches:
                try:
                    if len(found_date) == 8:
                        date_str = f"{found_date[:4]}-{found_date[4:6]}-{found_date[6:8]}"
                    else:
                        date_str = found_date.replace('_', '-')

                    search_date = datetime.fromisoformat(date_str)
                    date_start = (search_date - timedelta(days=1)).isoformat()
                    date_end = (search_date + timedelta(days=1)).isoformat()

                    result = await self.database._fetch_all(
                        """
                        SELECT id, job_name, filename, printer_id, created_at
                        FROM jobs
                        WHERE created_at BETWEEN ? AND ?
                        LIMIT 5
                        """,
                        (date_start, date_end)
                    )
                    matches.extend(result)

                except Exception as e:
                    logger.debug("Could not parse date for job matching", error=str(e))

            # If exactly one match, auto-link
            if len(matches) == 1:
                job_id = matches[0]['id']
                await self.database.execute(
                    "UPDATE timelapses SET job_id = ?, updated_at = ? WHERE id = ?",
                    (job_id, datetime.now().isoformat(), timelapse_id)
                )

                logger.info(
                    "Auto-linked timelapse to job",
                    timelapse_id=timelapse_id,
                    job_id=job_id,
                    job_name=matches[0]['job_name']
                )

            elif len(matches) > 1:
                logger.info(
                    "Multiple potential job matches found, skipping auto-link",
                    timelapse_id=timelapse_id,
                    match_count=len(matches)
                )
            else:
                logger.debug("No job matches found for timelapse", timelapse_id=timelapse_id, folder_name=folder_name)

        except Exception as e:
            logger.error("Error during job matching", timelapse_id=timelapse_id, error=str(e))

    # Public API methods

    async def get_timelapses(
        self,
        status: Optional[TimelapseStatus] = None,
        linked_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get list of timelapses with optional filtering."""
        try:
            query = "SELECT * FROM timelapses WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status.value)

            if linked_only:
                query += " AND job_id IS NOT NULL"

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            results = await self.database._fetch_all(query, tuple(params))

            timelapses = []
            for row in results:
                timelapse_dict = dict(row)
                # Convert datetime strings
                for field in ['created_at', 'updated_at', 'last_image_detected_at', 'auto_process_eligible_at', 'processing_started_at', 'processing_completed_at']:
                    if timelapse_dict.get(field):
                        timelapse_dict[field] = datetime.fromisoformat(timelapse_dict[field])

                # Convert boolean
                timelapse_dict['pinned'] = bool(timelapse_dict.get('pinned', 0))

                timelapses.append(timelapse_dict)

            logger.info("Retrieved timelapses", count=len(timelapses))
            return timelapses

        except Exception as e:
            logger.error("Failed to get timelapses", error=str(e))
            return []

    async def get_timelapse(self, timelapse_id: str) -> Optional[Dict[str, Any]]:
        """Get specific timelapse by ID."""
        try:
            result = await self.database._fetch_one(
                "SELECT * FROM timelapses WHERE id = ?",
                (timelapse_id,)
            )

            if not result:
                return None

            timelapse_dict = dict(result)
            # Convert datetime strings
            for field in ['created_at', 'updated_at', 'last_image_detected_at', 'auto_process_eligible_at', 'processing_started_at', 'processing_completed_at']:
                if timelapse_dict.get(field):
                    timelapse_dict[field] = datetime.fromisoformat(timelapse_dict[field])

            # Convert boolean
            timelapse_dict['pinned'] = bool(timelapse_dict.get('pinned', 0))

            return timelapse_dict

        except Exception as e:
            logger.error("Failed to get timelapse", timelapse_id=timelapse_id, error=str(e))
            return None

    async def get_timelapse_by_source_folder(self, source_folder: str) -> Optional[Dict[str, Any]]:
        """Get timelapse by source folder path."""
        try:
            result = await self.database._fetch_one(
                "SELECT * FROM timelapses WHERE source_folder = ?",
                (source_folder,)
            )

            if not result:
                return None

            return dict(result)

        except Exception as e:
            logger.error("Failed to get timelapse by source folder", source_folder=source_folder, error=str(e))
            return None

    async def trigger_processing(self, timelapse_id: str) -> Optional[Dict[str, Any]]:
        """Manually trigger processing for a timelapse (set status to pending)."""
        try:
            timelapse = await self.get_timelapse(timelapse_id)
            if not timelapse:
                logger.error("Timelapse not found", timelapse_id=timelapse_id)
                return None

            # Only allow triggering from discovered or failed status
            if timelapse['status'] not in [TimelapseStatus.DISCOVERED.value, TimelapseStatus.FAILED.value]:
                logger.warning(
                    "Cannot trigger processing from current status",
                    timelapse_id=timelapse_id,
                    status=timelapse['status']
                )
                return timelapse

            # Update status to pending
            await self.database.execute(
                "UPDATE timelapses SET status = ?, updated_at = ? WHERE id = ?",
                (TimelapseStatus.PENDING.value, datetime.now().isoformat(), timelapse_id)
            )

            logger.info("Manually triggered processing", timelapse_id=timelapse_id)

            await self.event_service.emit('timelapse.pending', {
                'id': timelapse_id,
                'folder_name': timelapse['folder_name'],
                'status': TimelapseStatus.PENDING.value
            })

            return await self.get_timelapse(timelapse_id)

        except Exception as e:
            logger.error("Failed to trigger processing", timelapse_id=timelapse_id, error=str(e))
            return None

    async def get_stats(self) -> Dict[str, Any]:
        """Get timelapse statistics."""
        try:
            # Get counts by status
            status_counts = {}
            for status in TimelapseStatus:
                result = await self.database._fetch_one(
                    "SELECT COUNT(*) as count FROM timelapses WHERE status = ?",
                    (status.value,)
                )
                status_counts[f"{status.value}_count"] = result['count'] if result else 0

            # Get total size
            result = await self.database._fetch_one(
                "SELECT SUM(file_size_bytes) as total_size FROM timelapses WHERE file_size_bytes IS NOT NULL"
            )
            total_size = result['total_size'] if result and result['total_size'] else 0

            # Get total count
            result = await self.database._fetch_one("SELECT COUNT(*) as count FROM timelapses")
            total_count = result['count'] if result else 0

            # Get cleanup candidates count
            cleanup_age = datetime.now() - timedelta(days=self.settings.timelapse_cleanup_age_days)
            result = await self.database._fetch_one(
                """
                SELECT COUNT(*) as count FROM timelapses
                WHERE created_at < ? AND pinned = 0 AND status = ?
                """,
                (cleanup_age.isoformat(), TimelapseStatus.COMPLETED.value)
            )
            cleanup_count = result['count'] if result else 0

            stats = {
                'total_videos': total_count,
                'total_size_bytes': total_size,
                'discovered_count': status_counts.get('discovered_count', 0),
                'pending_count': status_counts.get('pending_count', 0),
                'processing_count': status_counts.get('processing_count', 0),
                'completed_count': status_counts.get('completed_count', 0),
                'failed_count': status_counts.get('failed_count', 0),
                'cleanup_candidates_count': cleanup_count
            }

            return stats

        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            return {
                'total_videos': 0,
                'total_size_bytes': 0,
                'discovered_count': 0,
                'pending_count': 0,
                'processing_count': 0,
                'completed_count': 0,
                'failed_count': 0,
                'cleanup_candidates_count': 0
            }

    async def delete_timelapse(self, timelapse_id: str) -> bool:
        """Delete timelapse video and database record."""
        try:
            timelapse = await self.get_timelapse(timelapse_id)
            if not timelapse:
                logger.error("Timelapse not found for deletion", timelapse_id=timelapse_id)
                return False

            # Delete video file if it exists
            if timelapse.get('output_video_path'):
                video_path = Path(timelapse['output_video_path'])
                if video_path.exists():
                    try:
                        video_path.unlink()
                        logger.info("Deleted video file", path=str(video_path))
                    except Exception as e:
                        logger.warning("Failed to delete video file", path=str(video_path), error=str(e))

            # Delete database record
            await self.database.execute(
                "DELETE FROM timelapses WHERE id = ?",
                (timelapse_id,)
            )

            logger.info("Deleted timelapse", timelapse_id=timelapse_id, folder=timelapse.get('folder_name'))

            # Emit WebSocket event
            await self.event_service.emit('timelapse.deleted', {
                'id': timelapse_id
            })

            return True

        except Exception as e:
            logger.error("Failed to delete timelapse", timelapse_id=timelapse_id, error=str(e))
            return False

    async def bulk_delete_timelapses(self, timelapse_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple timelapses."""
        deleted = 0
        failed = 0
        errors = []

        for timelapse_id in timelapse_ids:
            try:
                success = await self.delete_timelapse(timelapse_id)
                if success:
                    deleted += 1
                else:
                    failed += 1
                    errors.append(f"Failed to delete {timelapse_id}")
            except Exception as e:
                failed += 1
                errors.append(f"Error deleting {timelapse_id}: {str(e)}")

        logger.info("Bulk delete completed", deleted=deleted, failed=failed)

        return {
            'deleted': deleted,
            'failed': failed,
            'errors': errors
        }

    async def toggle_pin(self, timelapse_id: str) -> Optional[Dict[str, Any]]:
        """Toggle pinned status for a timelapse."""
        try:
            timelapse = await self.get_timelapse(timelapse_id)
            if not timelapse:
                logger.error("Timelapse not found for pinning", timelapse_id=timelapse_id)
                return None

            new_pinned_status = not timelapse.get('pinned', False)

            await self.database.execute(
                "UPDATE timelapses SET pinned = ?, updated_at = ? WHERE id = ?",
                (1 if new_pinned_status else 0, datetime.now().isoformat(), timelapse_id)
            )

            logger.info(
                "Toggled pin status",
                timelapse_id=timelapse_id,
                pinned=new_pinned_status
            )

            return await self.get_timelapse(timelapse_id)

        except Exception as e:
            logger.error("Failed to toggle pin", timelapse_id=timelapse_id, error=str(e))
            return None

    async def link_to_job(self, timelapse_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Manually link timelapse to a job."""
        try:
            # Verify timelapse exists
            timelapse = await self.get_timelapse(timelapse_id)
            if not timelapse:
                logger.error("Timelapse not found for linking", timelapse_id=timelapse_id)
                return None

            # Verify job exists
            job_result = await self.database._fetch_one(
                "SELECT id, job_name FROM jobs WHERE id = ?",
                (job_id,)
            )
            if not job_result:
                logger.error("Job not found for linking", job_id=job_id)
                return None

            # Update link
            await self.database.execute(
                "UPDATE timelapses SET job_id = ?, updated_at = ? WHERE id = ?",
                (job_id, datetime.now().isoformat(), timelapse_id)
            )

            logger.info(
                "Linked timelapse to job",
                timelapse_id=timelapse_id,
                job_id=job_id,
                job_name=job_result['job_name']
            )

            return await self.get_timelapse(timelapse_id)

        except Exception as e:
            logger.error("Failed to link timelapse to job", timelapse_id=timelapse_id, job_id=job_id, error=str(e))
            return None

    async def get_cleanup_candidates(self) -> List[Dict[str, Any]]:
        """Get timelapses recommended for deletion."""
        try:
            cleanup_age = datetime.now() - timedelta(days=self.settings.timelapse_cleanup_age_days)

            results = await self.database._fetch_all(
                """
                SELECT * FROM timelapses
                WHERE created_at < ? AND pinned = 0 AND status = ?
                ORDER BY created_at ASC
                """,
                (cleanup_age.isoformat(), TimelapseStatus.COMPLETED.value)
            )

            timelapses = []
            for row in results:
                timelapse_dict = dict(row)
                # Convert datetime strings
                for field in ['created_at', 'updated_at', 'last_image_detected_at', 'auto_process_eligible_at', 'processing_started_at', 'processing_completed_at']:
                    if timelapse_dict.get(field):
                        timelapse_dict[field] = datetime.fromisoformat(timelapse_dict[field])

                # Convert boolean
                timelapse_dict['pinned'] = bool(timelapse_dict.get('pinned', 0))

                timelapses.append(timelapse_dict)

            logger.info("Retrieved cleanup candidates", count=len(timelapses))
            return timelapses

        except Exception as e:
            logger.error("Failed to get cleanup candidates", error=str(e))
            return []
