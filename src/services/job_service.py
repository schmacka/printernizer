"""
Job service for managing print jobs and tracking.
This will be expanded in Phase 1.3 with actual job monitoring.
"""
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime
import structlog
from src.database.database import Database
from src.database.repositories import JobRepository
from src.services.event_service import EventService
from src.models.job import Job, JobStatus, JobCreate, JobUpdate, JobUpdateRequest, JobStatusUpdateRequest

logger = structlog.get_logger()


class JobService:
    """Service for managing print jobs and monitoring."""

    def __init__(self, database: Database, event_service: EventService, usage_stats_service=None):
        """Initialize job service."""
        # Use JobRepository for database operations
        self.job_repo = JobRepository(database._connection)
        self.database = database
        self.event_service = event_service
        self.usage_stats_service = usage_stats_service

    def _deserialize_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize job data from database format to application format.

        Handles:
        - Parsing customer_info JSON string to dict
        - Converting datetime strings to datetime objects

        Args:
            job_data: Raw job data from database

        Returns:
            Deserialized job data ready for Job model validation

        Note:
            This method mutates the input dictionary for performance.
        """
        # Parse customer_info JSON if present
        if job_data.get('customer_info'):
            job_data['customer_info'] = json.loads(job_data['customer_info'])

        # Convert datetime strings to datetime objects
        for field in ['start_time', 'end_time', 'created_at', 'updated_at']:
            if job_data.get(field):
                job_data[field] = datetime.fromisoformat(job_data[field])

        return job_data

    async def get_jobs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get list of print jobs."""
        try:
            jobs_data = await self.job_repo.list()

            # Apply pagination
            start = offset
            end = offset + limit
            paginated_jobs = jobs_data[start:end]

            # Convert to Job models for validation and formatting
            jobs = []
            skipped_count = 0
            for job_data in paginated_jobs:
                try:
                    # Validate job has ID - critical field
                    if not job_data.get('id'):
                        logger.error("Job missing ID field, skipping",
                                   printer_id=job_data.get('printer_id'),
                                   job_name=job_data.get('job_name'),
                                   job_data=job_data)
                        skipped_count += 1
                        continue

                    # Deserialize job data from database format
                    job_data = self._deserialize_job_data(job_data)

                    job = Job(**job_data)
                    jobs.append(job.dict())
                except Exception as e:
                    logger.error("Failed to parse job data, skipping",
                               job_id=job_data.get('id'),
                               error=str(e),
                               error_type=type(e).__name__)
                    skipped_count += 1
                    continue

            if skipped_count > 0:
                logger.warning("Skipped jobs during retrieval",
                             skipped_count=skipped_count,
                             valid_count=len(jobs))

            logger.info("Retrieved jobs", count=len(jobs), total_available=len(jobs_data))
            return jobs

        except Exception as e:
            logger.error("Failed to get jobs", error=str(e))
            return []
    
    async def list_jobs(self, printer_id=None, status=None, is_business=None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List jobs with optional filtering."""
        try:
            # Use enhanced database method with direct filtering and pagination
            jobs_data = await self.job_repo.list(
                printer_id=printer_id,
                status=status,
                is_business=is_business,
                limit=limit,
                offset=offset
            )

            # Convert to Job models
            jobs = []
            skipped_count = 0
            for job_data in jobs_data:
                try:
                    # Validate job has ID - critical field
                    if not job_data.get('id'):
                        logger.error("Job missing ID field, skipping",
                                   printer_id=job_data.get('printer_id'),
                                   job_name=job_data.get('job_name'))
                        skipped_count += 1
                        continue

                    # Deserialize job data from database format
                    job_data = self._deserialize_job_data(job_data)

                    job = Job(**job_data)
                    jobs.append(job.dict())
                except Exception as e:
                    logger.error("Failed to parse job data, skipping",
                               job_id=job_data.get('id'),
                               error=str(e),
                               error_type=type(e).__name__)
                    skipped_count += 1
                    continue

            if skipped_count > 0:
                logger.warning("Skipped jobs during list operation",
                             skipped_count=skipped_count,
                             valid_count=len(jobs))

            logger.info("Listed jobs",
                       printer_id=printer_id,
                       status=status,
                       is_business=is_business,
                       count=len(jobs),
                       limit=limit,
                       offset=offset)
            return jobs

        except Exception as e:
            logger.error("Failed to list jobs", error=str(e))
            return []

    async def list_jobs_with_count(self, printer_id=None, status=None, is_business=None,
                                   limit: int = 100, offset: int = 0) -> tuple[List[Dict[str, Any]], int]:
        """List jobs with total count (optimized pagination).

        This method efficiently returns both the paginated job list and the total count
        using separate optimized queries, avoiding the need to fetch all records twice.

        Args:
            printer_id: Filter by printer ID
            status: Filter by job status
            is_business: Filter by business flag
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            Tuple of (jobs list, total count)

        Example:
            >>> jobs, total = await job_service.list_jobs_with_count(limit=20, offset=0)
            >>> print(f"Showing {len(jobs)} of {total} jobs")
        """
        try:
            # Get paginated jobs
            jobs = await self.list_jobs(
                printer_id=printer_id,
                status=status,
                is_business=is_business,
                limit=limit,
                offset=offset
            )

            # Get total count with efficient COUNT query
            total_count = await self.job_repo.count(
                printer_id=printer_id,
                status=status,
                is_business=is_business
            )

            logger.info("Listed jobs with count",
                       count=len(jobs),
                       total=total_count,
                       printer_id=printer_id,
                       status=status,
                       is_business=is_business)

            return jobs, total_count

        except Exception as e:
            logger.error("Failed to list jobs with count", error=str(e))
            return [], 0

    async def get_job(self, job_id) -> Optional[Dict[str, Any]]:
        """Get specific job by ID."""
        try:
            job_data = await self.job_repo.get(str(job_id))
            if not job_data:
                return None

            # Deserialize job data from database format
            job_data = self._deserialize_job_data(job_data)
            
            # Validate with Job model
            job = Job(**job_data)
            logger.info("Retrieved job", job_id=job_id)
            return job.dict()
            
        except Exception as e:
            logger.error("Failed to get job", job_id=job_id, error=str(e))
            return None
        
    async def delete_job(self, job_id) -> bool:
        """Delete a job record."""
        try:
            # Check if job exists first
            existing_job = await self.job_repo.get(str(job_id))
            if not existing_job:
                logger.warning("Job not found for deletion", job_id=job_id)
                return False
            
            # Delete the job record from database
            success = await self.job_repo.delete(str(job_id))
            
            if success:
                logger.info("Job deleted successfully", job_id=job_id)
                # Emit event for job deletion
                await self.event_service.emit_event('job_deleted', {
                    'job_id': str(job_id),
                    'timestamp': datetime.now().isoformat()
                })
            
            return success
            
        except Exception as e:
            logger.error("Failed to delete job", job_id=job_id, error=str(e))
            return False
        
    async def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get currently active/running jobs."""
        try:
            # Get jobs that are in active states
            active_statuses = [JobStatus.RUNNING, JobStatus.PENDING, JobStatus.PAUSED]
            active_jobs = []
            
            for status in active_statuses:
                jobs_data = await self.job_repo.list(status=status)
                active_jobs.extend(jobs_data)
            
            # Convert to Job models
            jobs = []
            for job_data in active_jobs:
                try:
                    # Deserialize job data from database format
                    job_data = self._deserialize_job_data(job_data)

                    job = Job(**job_data)
                    jobs.append(job.dict())
                except Exception as e:
                    logger.warning("Failed to parse active job data", job_id=job_data.get('id'), error=str(e))
                    continue
            
            logger.info("Retrieved active jobs", count=len(jobs))
            return jobs
            
        except Exception as e:
            logger.error("Failed to get active jobs", error=str(e))
            return []
        
    async def create_job(self, job_data: Dict[str, Any]) -> str:
        """Create a new print job."""
        try:
            # Check if this is an auto-created job (has all fields already)
            # or a user-created job (needs validation with JobCreate model)
            is_auto_created = 'printer_type' in job_data and 'created_at' in job_data

            if not is_auto_created:
                # Validate input data with JobCreate model for user-created jobs
                if isinstance(job_data, dict):
                    job_create = JobCreate(**job_data)
                else:
                    job_create = job_data

                # Generate unique job ID - ensure it's never NULL
                job_id = str(uuid.uuid4())
                if not job_id or job_id == '':
                    raise ValueError("Generated job ID is empty")

                # Prepare job data for database
                db_job_data = {
                    'id': job_id,
                    'printer_id': job_create.printer_id,
                    'printer_type': 'unknown',  # This should be determined from printer service
                    'job_name': job_create.job_name,
                    'filename': job_create.filename,
                    'status': JobStatus.PENDING,
                    'estimated_duration': job_create.estimated_duration,
                    'is_business': job_create.is_business,
                    'customer_info': json.dumps(job_create.customer_info) if job_create.customer_info else None
                }
            else:
                # Auto-created job - already has all fields
                job_id = str(uuid.uuid4())
                if not job_id or job_id == '':
                    raise ValueError("Generated job ID is empty")

                # Pass through all fields from auto-creation
                db_job_data = {
                    'id': job_id,
                    'printer_id': job_data['printer_id'],
                    'printer_type': job_data.get('printer_type', 'unknown'),
                    'job_name': job_data['job_name'],
                    'filename': job_data.get('filename'),
                    'status': job_data.get('status', JobStatus.PENDING),
                    'start_time': job_data.get('start_time'),  # From printer
                    'end_time': job_data.get('end_time'),
                    'estimated_duration': job_data.get('estimated_duration'),
                    'actual_duration': job_data.get('actual_duration'),
                    'progress': job_data.get('progress', 0),
                    'material_used': job_data.get('material_used'),
                    'material_cost': job_data.get('material_cost'),
                    'power_cost': job_data.get('power_cost'),
                    'is_business': job_data.get('is_business', False),
                    'customer_info': json.dumps(job_data.get('customer_info')) if job_data.get('customer_info') else None,
                    'created_at': job_data.get('created_at'),  # Discovery time
                    'updated_at': job_data.get('updated_at')
                }

            # Validate all required fields are present before database insert
            required_fields = ['id', 'printer_id', 'printer_type', 'job_name']
            for field in required_fields:
                if not db_job_data.get(field):
                    raise ValueError(f"Required field '{field}' is missing or empty")

            # Create job in database
            success = await self.job_repo.create(db_job_data)

            if success:
                logger.info("Job created successfully",
                           job_id=job_id,
                           job_name=db_job_data['job_name'],
                           start_time=db_job_data.get('start_time'),
                           is_auto_created=is_auto_created)

                # Emit event for job creation
                await self.event_service.emit_event('job_created', {
                    'job_id': job_id,
                    'printer_id': db_job_data['printer_id'],
                    'job_name': db_job_data['job_name'],
                    'is_business': db_job_data.get('is_business', False),
                    'timestamp': datetime.now().isoformat()
                })

                # Record usage statistics (privacy-safe: no job names, only printer type)
                if self.usage_stats_service:
                    await self.usage_stats_service.record_event('job_created', {
                        'printer_type': db_job_data.get('printer_type', 'unknown'),
                        'is_auto_created': is_auto_created
                    })

                return job_id
            else:
                # Job creation failed - likely duplicate (UNIQUE constraint violation)
                if is_auto_created and db_job_data.get('start_time'):
                    logger.info("Duplicate job detected (likely from restart)",
                               printer_id=db_job_data['printer_id'],
                               filename=db_job_data.get('filename'),
                               start_time=db_job_data.get('start_time'))
                    # Don't raise exception for duplicate auto-created jobs
                    # Return a special marker or re-query for the existing job
                    # For now, we'll raise to maintain the existing behavior
                    raise Exception("Duplicate job detected by database constraint")
                else:
                    logger.error("Failed to create job in database", data=job_data)
                    raise Exception("Database operation failed")

        except Exception as e:
            logger.error("Failed to create job", error=str(e), error_type=type(e).__name__, data=job_data)
            raise
        
    async def update_job(self, job_id: str, updates: JobUpdateRequest) -> Optional[Dict[str, Any]]:
        """
        Update job fields with validation.

        Args:
            job_id: Job UUID
            updates: JobUpdateRequest schema with validated data

        Returns:
            Updated Job object

        Raises:
            ValueError: If validation fails
            HTTPException: If job not found or printer doesn't exist
        """
        from fastapi import HTTPException

        # Get existing job
        existing_job = await self.job_repo.get(job_id)
        if not existing_job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Convert JobUpdateRequest to dict, excluding unset fields
        update_dict = updates.model_dump(exclude_unset=True)

        if not update_dict:
            # No fields to update
            return await self.get_job(job_id)

        # Business validation: if is_business=true, customer_name required
        is_business = update_dict.get('is_business', existing_job.get('is_business'))
        customer_name = update_dict.get('customer_name', existing_job.get('customer_name'))

        if is_business and not customer_name:
            raise ValueError("customer_name is required for business jobs")

        # Validate printer exists if provided
        if 'printer_id' in update_dict and update_dict['printer_id']:
            # We need access to printer service - for now, we'll skip this validation
            # In production, you'd inject PrinterService as a dependency
            # printer = await self.printer_service.get_printer(update_dict['printer_id'])
            # if not printer:
            #     raise HTTPException(status_code=400, detail=f"Printer {update_dict['printer_id']} not found")
            pass

        # Map file_name to filename for database compatibility
        if 'file_name' in update_dict:
            update_dict['filename'] = update_dict.pop('file_name')

        # Update job
        success = await self.job_repo.update(job_id, update_dict)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update job")

        # Get updated job
        updated_job = await self.get_job(job_id)

        # Emit WebSocket event
        await self.event_service.emit_event('job_updated', {
            'job_id': job_id,
            'job': updated_job,
            'updated_fields': list(update_dict.keys())
        })

        logger.info("Job updated", job_id=job_id, updated_fields=list(update_dict.keys()))

        return updated_job

    def _validate_status_transition(self, old_status: str, new_status: str) -> None:
        """
        Validate status transition is allowed.

        Raises:
            ValueError: If transition is not allowed
        """
        # Define valid transitions based on the plan
        valid_transitions = {
            'pending': {'running', 'printing', 'completed', 'failed', 'cancelled'},
            'queued': {'running', 'printing', 'preparing', 'completed', 'failed', 'cancelled'},
            'preparing': {'printing', 'running', 'completed', 'failed', 'cancelled'},
            'running': {'completed', 'failed', 'cancelled', 'paused'},
            'printing': {'completed', 'failed', 'cancelled', 'paused'},
            'paused': {'running', 'printing', 'completed', 'failed', 'cancelled'},
            'completed': {'failed'},  # Rare: correct completion to failure
            'failed': {'completed'},  # Rare: retry succeeded
            'cancelled': set(),  # Cannot transition from cancelled
        }

        allowed = valid_transitions.get(old_status, set())

        if new_status not in allowed and old_status != new_status:
            raise ValueError(
                f"Invalid status transition: {old_status} → {new_status}. "
                f"Allowed transitions from {old_status}: {', '.join(sorted(allowed)) if allowed else 'none'}"
            )

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        data: Dict[str, Any] = None,
        completion_notes: Optional[str] = None,
        force: bool = False,
        validate_transitions: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Update job status with optional transition validation.

        Args:
            job_id: Job UUID
            status: Target status
            data: Additional data to update (legacy parameter)
            completion_notes: Optional notes explaining manual status change
            force: Skip validation (admin override)
            validate_transitions: Enable status transition validation

        Returns:
            Updated Job object or None

        Raises:
            ValueError: If status transition is not allowed
        """
        from fastapi import HTTPException

        try:
            # Validate status
            if status not in [s.value for s in JobStatus]:
                raise ValueError(f"Invalid job status: {status}")

            # Get existing job if validation is needed
            old_status = None
            if validate_transitions or completion_notes:
                job = await self.job_repo.get(job_id)
                if not job:
                    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
                old_status = job.get('status')

                # Check if status actually changed
                if old_status == status:
                    logger.info(f"Job {job_id} already in status {status} (no-op)")
                    return await self.get_job(job_id)

                # Validate transition (unless forced)
                if validate_transitions and not force:
                    self._validate_status_transition(old_status, status)

            # Prepare update data
            updates = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }

            # Add additional data if provided (legacy support)
            if data:
                # Handle specific fields that might be updated
                if 'progress' in data:
                    updates['progress'] = data['progress']
                if 'material_used' in data:
                    updates['material_used'] = data['material_used']
                if 'actual_duration' in data:
                    updates['actual_duration'] = data['actual_duration']
                if 'material_cost' in data:
                    updates['material_cost'] = data['material_cost']
                if 'power_cost' in data:
                    updates['power_cost'] = data['power_cost']

            # Set timestamps based on status
            now = datetime.now()
            if status in [JobStatus.RUNNING.value, JobStatus.PRINTING.value] and 'start_time' not in updates:
                updates['start_time'] = now.isoformat()
            elif status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value] and 'end_time' not in updates:
                updates['end_time'] = now.isoformat()

            # Add completion notes if provided
            if completion_notes and old_status:
                # Get existing notes
                existing_job = await self.job_repo.get(job_id) if not validate_transitions else job
                existing_notes = existing_job.get('notes', '') if existing_job else ''

                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                status_note = f"[{timestamp}] Status changed: {old_status} → {status}: {completion_notes}"

                if existing_notes:
                    updates['notes'] = f"{existing_notes}\n{status_note}"
                else:
                    updates['notes'] = status_note

            # Update job in database
            success = await self.job_repo.update(str(job_id), updates)

            if success:
                logger.info("Job status updated",
                           job_id=job_id,
                           status=status,
                           old_status=old_status,
                           forced=force if validate_transitions else None)

                # Get updated job
                updated_job = await self.get_job(job_id)

                # Emit event for status change
                await self.event_service.emit_event('job_status_changed', {
                    'job_id': str(job_id),
                    'status': status,
                    'old_status': old_status,
                    'data': data or {},
                    'timestamp': now.isoformat()
                })

                # Record usage statistics for completed/failed jobs
                if self.usage_stats_service:
                    if status == JobStatus.COMPLETED.value:
                        await self.usage_stats_service.record_event('job_completed', {
                            'duration_minutes': updates.get('actual_duration', 0) // 60 if updates.get('actual_duration') else None
                        })
                    elif status == JobStatus.FAILED.value:
                        await self.usage_stats_service.record_event('job_failed', {})

                return updated_job
            else:
                logger.error("Failed to update job status in database", job_id=job_id, status=status)
                return None

        except ValueError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to update job status", job_id=job_id, status=status, error=str(e))
            return None
        
    async def get_job_statistics(self) -> Dict[str, Any]:
        """Get job statistics for dashboard."""
        try:
            # Use optimized database statistics method
            stats = await self.job_repo.get_statistics()
            
            # Calculate active jobs from individual status counts
            stats["active_jobs"] = (
                stats.get("pending_jobs", 0) + 
                stats.get("running_jobs", 0) + 
                stats.get("paused_jobs", 0)
            )
            
            # Ensure all expected fields are present with defaults
            default_stats = {
                "total_jobs": 0,
                "active_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "cancelled_jobs": 0,
                "pending_jobs": 0,
                "running_jobs": 0,
                "paused_jobs": 0,
                "business_jobs": 0,
                "private_jobs": 0,
                "total_material_used": 0.0,
                "avg_material_used": 0.0,
                "total_material_cost": 0.0,
                "avg_material_cost": 0.0,
                "total_power_cost": 0.0,
                "avg_power_cost": 0.0,
                "total_print_time": 0,
                "avg_print_time": 0
            }
            
            # Merge database stats with defaults
            for key, default_value in default_stats.items():
                if key not in stats:
                    stats[key] = default_value
            
            logger.info("Retrieved job statistics", stats=stats)
            return stats
            
        except Exception as e:
            logger.error("Failed to get job statistics", error=str(e))
            return {
                "total_jobs": 0,
                "active_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0
            }
    
    async def get_jobs_by_date_range(self, start_date: str, end_date: str, is_business: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get jobs within a date range for reporting purposes."""
        try:
            jobs_data = await self.job_repo.get_by_date_range(start_date, end_date, is_business)
            
            # Convert to Job models
            jobs = []
            for job_data in jobs_data:
                try:
                    # Deserialize job data from database format
                    job_data = self._deserialize_job_data(job_data)

                    job = Job(**job_data)
                    jobs.append(job.dict())
                except Exception as e:
                    logger.warning("Failed to parse job data in date range", job_id=job_data.get('id'), error=str(e))
                    continue
            
            logger.info("Retrieved jobs by date range", 
                       start_date=start_date, 
                       end_date=end_date, 
                       is_business=is_business, 
                       count=len(jobs))
            return jobs
            
        except Exception as e:
            logger.error("Failed to get jobs by date range", error=str(e))
            return []
    
    async def get_business_jobs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get business jobs specifically."""
        return await self.list_jobs(is_business=True, limit=limit, offset=offset)
    
    async def get_private_jobs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get private jobs specifically."""
        return await self.list_jobs(is_business=False, limit=limit, offset=offset)
    
    async def calculate_material_costs(self, job_id: str, material_cost_per_gram: float, power_cost_per_hour: float) -> Dict[str, float]:
        """Calculate material and power costs for a job."""
        try:
            job_data = await self.get_job(job_id)
            if not job_data:
                return {"error": "Job not found"}
            
            costs = {"material_cost": 0.0, "power_cost": 0.0, "total_cost": 0.0}
            
            # Calculate material cost
            if job_data.get('material_used'):
                costs['material_cost'] = job_data['material_used'] * material_cost_per_gram
            
            # Calculate power cost
            if job_data.get('actual_duration'):
                hours = job_data['actual_duration'] / 3600  # Convert seconds to hours
                costs['power_cost'] = hours * power_cost_per_hour
            
            costs['total_cost'] = costs['material_cost'] + costs['power_cost']
            
            # Update the job with calculated costs
            await self.job_repo.update(job_id, {
                'material_cost': costs['material_cost'],
                'power_cost': costs['power_cost']
            })
            
            logger.info("Calculated costs for job", job_id=job_id, costs=costs)
            return costs
            
        except Exception as e:
            logger.error("Failed to calculate material costs", job_id=job_id, error=str(e))
            return {"error": str(e)}
    
    async def get_printer_jobs(self, printer_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all jobs for a specific printer."""
        return await self.list_jobs(printer_id=printer_id, limit=limit, offset=offset)
    
    async def update_job_progress(self, job_id: str, progress: int, material_used: Optional[float] = None) -> bool:
        """Update job progress and optionally material usage."""
        try:
            updates = {
                'progress': max(0, min(100, progress)),  # Ensure progress is between 0-100
                'updated_at': datetime.now().isoformat()
            }
            
            if material_used is not None:
                updates['material_used'] = material_used
            
            success = await self.job_repo.update(str(job_id), updates)
            
            if success:
                logger.info("Job progress updated", job_id=job_id, progress=progress, material_used=material_used)
                
                # Emit event for progress update
                await self.event_service.emit_event('job_progress_updated', {
                    'job_id': str(job_id),
                    'progress': progress,
                    'material_used': material_used,
                    'timestamp': datetime.now().isoformat()
                })
            
            return success
            
        except Exception as e:
            logger.error("Failed to update job progress", job_id=job_id, error=str(e))
            return False