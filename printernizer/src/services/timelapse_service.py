"""
Timelapse service for managing timelapse video creation.
Handles folder monitoring, auto-detection, and video processing.
"""
from typing import List, Dict, Any, Optional
import uuid
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import structlog

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

    async def start(self):
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

    async def shutdown(self):
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
            await asyncio.sleep(30)

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
            await asyncio.sleep(10)

    async def _process_queue(self):
        """Check for pending timelapses and process next one if none currently processing."""
        # Check if any timelapse is currently processing
        result = await self.database.fetch_one(
            "SELECT COUNT(*) as count FROM timelapses WHERE status = ?",
            (TimelapseStatus.PROCESSING.value,)
        )

        if result and result['count'] > 0:
            # Already processing one, wait
            return

        # Get next pending timelapse (FIFO)
        result = await self.database.fetch_one(
            """
            SELECT * FROM timelapses
            WHERE status = ?
            ORDER BY auto_process_eligible_at ASC
            LIMIT 1
            """,
            (TimelapseStatus.PENDING.value,)
        )

        if result:
            logger.info("Found pending timelapse, will process in Phase 2", timelapse_id=result['id'])
            # Phase 2 will implement: await self._process_timelapse(result['id'])

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

            results = await self.database.fetch_all(query, tuple(params))

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
            result = await self.database.fetch_one(
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
            result = await self.database.fetch_one(
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
                result = await self.database.fetch_one(
                    "SELECT COUNT(*) as count FROM timelapses WHERE status = ?",
                    (status.value,)
                )
                status_counts[f"{status.value}_count"] = result['count'] if result else 0

            # Get total size
            result = await self.database.fetch_one(
                "SELECT SUM(file_size_bytes) as total_size FROM timelapses WHERE file_size_bytes IS NOT NULL"
            )
            total_size = result['total_size'] if result and result['total_size'] else 0

            # Get total count
            result = await self.database.fetch_one("SELECT COUNT(*) as count FROM timelapses")
            total_count = result['count'] if result else 0

            # Get cleanup candidates count
            cleanup_age = datetime.now() - timedelta(days=self.settings.timelapse_cleanup_age_days)
            result = await self.database.fetch_one(
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
