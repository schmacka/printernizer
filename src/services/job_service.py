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
from src.services.event_service import EventService
from src.models.job import Job, JobStatus, JobCreate, JobUpdate

logger = structlog.get_logger()


class JobService:
    """Service for managing print jobs and monitoring."""
    
    def __init__(self, database: Database, event_service: EventService):
        """Initialize job service."""
        self.database = database
        self.event_service = event_service
        
    async def get_jobs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get list of print jobs."""
        try:
            jobs_data = await self.database.list_jobs()
            
            # Apply pagination
            start = offset
            end = offset + limit
            paginated_jobs = jobs_data[start:end]
            
            # Convert to Job models for validation and formatting
            jobs = []
            for job_data in paginated_jobs:
                try:
                    # Parse customer_info JSON if present
                    if job_data.get('customer_info'):
                        job_data['customer_info'] = json.loads(job_data['customer_info'])
                    
                    # Convert datetime strings to datetime objects
                    for field in ['start_time', 'end_time', 'created_at', 'updated_at']:
                        if job_data.get(field):
                            job_data[field] = datetime.fromisoformat(job_data[field])
                    
                    job = Job(**job_data)
                    jobs.append(job.dict())
                except Exception as e:
                    logger.warning("Failed to parse job data", job_id=job_data.get('id'), error=str(e))
                    continue
            
            logger.info("Retrieved jobs", count=len(jobs), total_available=len(jobs_data))
            return jobs
            
        except Exception as e:
            logger.error("Failed to get jobs", error=str(e))
            return []
    
    async def list_jobs(self, printer_id=None, status=None, is_business=None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List jobs with optional filtering."""
        try:
            # Use enhanced database method with direct filtering and pagination
            jobs_data = await self.database.list_jobs(
                printer_id=printer_id, 
                status=status, 
                is_business=is_business,
                limit=limit,
                offset=offset
            )
            
            # Convert to Job models
            jobs = []
            for job_data in jobs_data:
                try:
                    # Parse customer_info JSON if present
                    if job_data.get('customer_info'):
                        job_data['customer_info'] = json.loads(job_data['customer_info'])
                    
                    # Convert datetime strings to datetime objects
                    for field in ['start_time', 'end_time', 'created_at', 'updated_at']:
                        if job_data.get(field):
                            job_data[field] = datetime.fromisoformat(job_data[field])
                    
                    job = Job(**job_data)
                    jobs.append(job.dict())
                except Exception as e:
                    logger.warning("Failed to parse job data", job_id=job_data.get('id'), error=str(e))
                    continue
            
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
        
    async def get_job(self, job_id) -> Optional[Dict[str, Any]]:
        """Get specific job by ID."""
        try:
            job_data = await self.database.get_job(str(job_id))
            if not job_data:
                return None
            
            # Parse customer_info JSON if present
            if job_data.get('customer_info'):
                job_data['customer_info'] = json.loads(job_data['customer_info'])
            
            # Convert datetime strings to datetime objects
            for field in ['start_time', 'end_time', 'created_at', 'updated_at']:
                if job_data.get(field):
                    job_data[field] = datetime.fromisoformat(job_data[field])
            
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
            existing_job = await self.database.get_job(str(job_id))
            if not existing_job:
                logger.warning("Job not found for deletion", job_id=job_id)
                return False
            
            # Delete the job record from database
            success = await self.database.delete_job(str(job_id))
            
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
                jobs_data = await self.database.list_jobs(status=status)
                active_jobs.extend(jobs_data)
            
            # Convert to Job models
            jobs = []
            for job_data in active_jobs:
                try:
                    # Parse customer_info JSON if present
                    if job_data.get('customer_info'):
                        job_data['customer_info'] = json.loads(job_data['customer_info'])
                    
                    # Convert datetime strings to datetime objects
                    for field in ['start_time', 'end_time', 'created_at', 'updated_at']:
                        if job_data.get(field):
                            job_data[field] = datetime.fromisoformat(job_data[field])
                    
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
            # Validate input data with JobCreate model
            if isinstance(job_data, dict):
                job_create = JobCreate(**job_data)
            else:
                job_create = job_data
            
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            
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
            
            # Create job in database
            success = await self.database.create_job(db_job_data)
            
            if success:
                logger.info("Job created successfully", job_id=job_id, job_name=job_create.job_name)
                
                # Emit event for job creation
                await self.event_service.emit_event('job_created', {
                    'job_id': job_id,
                    'printer_id': job_create.printer_id,
                    'job_name': job_create.job_name,
                    'is_business': job_create.is_business,
                    'timestamp': datetime.now().isoformat()
                })
                
                return job_id
            else:
                logger.error("Failed to create job in database", data=job_data)
                raise Exception("Database operation failed")
                
        except Exception as e:
            logger.error("Failed to create job", error=str(e), data=job_data)
            raise
        
    async def update_job_status(self, job_id: str, status: str, data: Dict[str, Any] = None):
        """Update job status."""
        try:
            # Validate status
            if status not in [s.value for s in JobStatus]:
                raise ValueError(f"Invalid job status: {status}")
            
            # Prepare update data
            updates = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            # Add additional data if provided
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
            if status == JobStatus.RUNNING and 'start_time' not in updates:
                updates['start_time'] = datetime.now().isoformat()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and 'end_time' not in updates:
                updates['end_time'] = datetime.now().isoformat()
            
            # Update job in database
            success = await self.database.update_job(str(job_id), updates)
            
            if success:
                logger.info("Job status updated", job_id=job_id, status=status)
                
                # Emit event for status change
                await self.event_service.emit_event('job_status_changed', {
                    'job_id': str(job_id),
                    'status': status,
                    'data': data or {},
                    'timestamp': datetime.now().isoformat()
                })
            else:
                logger.error("Failed to update job status in database", job_id=job_id, status=status)
                
        except Exception as e:
            logger.error("Failed to update job status", job_id=job_id, status=status, error=str(e))
        
    async def get_job_statistics(self) -> Dict[str, Any]:
        """Get job statistics for dashboard."""
        try:
            # Use optimized database statistics method
            stats = await self.database.get_job_statistics()
            
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
            jobs_data = await self.database.get_jobs_by_date_range(start_date, end_date, is_business)
            
            # Convert to Job models
            jobs = []
            for job_data in jobs_data:
                try:
                    # Parse customer_info JSON if present
                    if job_data.get('customer_info'):
                        job_data['customer_info'] = json.loads(job_data['customer_info'])
                    
                    # Convert datetime strings to datetime objects
                    for field in ['start_time', 'end_time', 'created_at', 'updated_at']:
                        if job_data.get(field):
                            job_data[field] = datetime.fromisoformat(job_data[field])
                    
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
            await self.database.update_job(job_id, {
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
    
    async def update_job_progress(self, job_id: str, progress: int, material_used: Optional[float] = None):
        """Update job progress and optionally material usage."""
        try:
            updates = {
                'progress': max(0, min(100, progress)),  # Ensure progress is between 0-100
                'updated_at': datetime.now().isoformat()
            }
            
            if material_used is not None:
                updates['material_used'] = material_used
            
            success = await self.database.update_job(str(job_id), updates)
            
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