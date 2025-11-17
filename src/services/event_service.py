"""
Event service for Printernizer.
Manages background tasks, printer monitoring, and real-time events.
"""
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import structlog

from src.config.constants import PollingIntervals

logger = structlog.get_logger()


class EventService:
    """Service for managing background events and printer monitoring."""
    
    def __init__(self, printer_service=None, job_service=None, file_service=None, database=None):
        """Initialize event service with dependencies."""
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Service dependencies - will be injected after initialization
        self.printer_service = printer_service
        self.job_service = job_service
        self.file_service = file_service
        self.database = database
        
        # Monitoring state
        self.last_printer_status = {}
        self.last_job_status = {}
        self.last_file_discovery = datetime.now()
        
        # Event counters for debugging
        self.event_counts = {
            'printer_status': 0,
            'job_update': 0,
            'files_discovered': 0,
            'printer_connected': 0,
            'printer_disconnected': 0,
            'job_started': 0,
            'job_completed': 0,
            'new_files_found': 0
        }
        
    async def start(self) -> None:
        """Start the event service and background tasks."""
        if self._running:
            logger.warning("Event service already running")
            return

        self._running = True
        logger.info("Starting event service")

        # Start background monitoring tasks
        self._tasks.extend([
            asyncio.create_task(self._printer_monitoring_task()),
            asyncio.create_task(self._job_status_task()),
            asyncio.create_task(self._file_discovery_task())
        ])

        logger.info("Event service started", tasks=len(self._tasks))

    async def stop(self) -> None:
        """Stop the event service and cancel all tasks."""
        if not self._running:
            return

        logger.info("Stopping event service")
        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to finish
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()
        logger.info("Event service stopped")

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to event notifications."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from event notifications."""
        if event_type in self._event_handlers:
            if handler in self._event_handlers[event_type]:
                self._event_handlers[event_type].remove(handler)
                
    async def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to all subscribers."""
        if event_type not in self._event_handlers:
            return
            
        handlers = self._event_handlers[event_type].copy()
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error("Error in event handler", 
                           event_type=event_type, error=str(e))
                
    async def _printer_monitoring_task(self):
        """Background task for monitoring printer status."""
        logger.info("Starting printer monitoring task")
        
        while self._running:
            try:
                if not self.printer_service:
                    await asyncio.sleep(PollingIntervals.PRINTER_STATUS_CHECK)
                    continue
                
                # Get current printer status from all printers
                printer_statuses = []
                status_changes = []
                
                try:
                    # Get list of active printers
                    printers = await self.printer_service.list_printers()
                    
                    for printer in printers:
                        printer_id = printer['id']
                        
                        try:
                            # Get current status from printer
                            current_status = await self.printer_service.get_printer_status(printer_id)
                            
                            if current_status:
                                printer_statuses.append({
                                    'printer_id': printer_id,
                                    'name': printer['name'],
                                    'type': printer['type'],
                                    'status': current_status.get('status', 'unknown'),
                                    'temperature': current_status.get('temperature', {}),
                                    'progress': current_status.get('progress', 0),
                                    'current_job': current_status.get('current_job'),
                                    'last_seen': datetime.now().isoformat()
                                })
                                
                                # Check for status changes
                                last_status = self.last_printer_status.get(printer_id, {})
                                if last_status.get('status') != current_status.get('status'):
                                    status_changes.append({
                                        'printer_id': printer_id,
                                        'old_status': last_status.get('status', 'unknown'),
                                        'new_status': current_status.get('status', 'unknown'),
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    
                                    # Emit specific connection/disconnection events
                                    if current_status.get('status') == 'online' and last_status.get('status') != 'online':
                                        await self.emit_event('printer_connected', {
                                            'printer_id': printer_id,
                                            'name': printer['name'],
                                            'timestamp': datetime.now().isoformat()
                                        })
                                        self.event_counts['printer_connected'] += 1
                                    elif current_status.get('status') != 'online' and last_status.get('status') == 'online':
                                        await self.emit_event('printer_disconnected', {
                                            'printer_id': printer_id,
                                            'name': printer['name'],
                                            'timestamp': datetime.now().isoformat()
                                        })
                                        self.event_counts['printer_disconnected'] += 1
                                
                                # Update last known status
                                self.last_printer_status[printer_id] = current_status
                                
                                # Update database status if needed
                                if self.database:
                                    await self.database.update_printer_status(
                                        printer_id, 
                                        current_status.get('status', 'unknown'),
                                        datetime.now()
                                    )
                            
                        except Exception as e:
                            logger.warning("Failed to get printer status", printer_id=printer_id, error=str(e))
                            # Mark printer as offline if we can't connect
                            printer_statuses.append({
                                'printer_id': printer_id,
                                'name': printer['name'],
                                'type': printer['type'],
                                'status': 'offline',
                                'error': str(e),
                                'last_seen': datetime.now().isoformat()
                            })
                    
                    # Emit general printer status event
                    await self.emit_event("printer_status", {
                        "timestamp": datetime.now().isoformat(),
                        "printers": printer_statuses,
                        "status_changes": status_changes
                    })
                    self.event_counts['printer_status'] += 1
                    
                    logger.debug("Printer monitoring complete", 
                               printer_count=len(printer_statuses),
                               status_changes=len(status_changes))
                    
                except Exception as e:
                    logger.error("Error getting printer list", error=str(e))

                await asyncio.sleep(PollingIntervals.PRINTER_STATUS_CHECK)  # 30-second polling interval
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in printer monitoring", error=str(e))
                await asyncio.sleep(PollingIntervals.PRINTER_STATUS_ERROR_BACKOFF)  # Wait longer on error
                
        logger.info("Printer monitoring task stopped")
        
    async def _job_status_task(self):
        """Background task for monitoring job status changes."""
        logger.info("Starting job status monitoring task")
        
        while self._running:
            try:
                if not self.job_service:
                    await asyncio.sleep(PollingIntervals.JOB_STATUS_CHECK)
                    continue
                
                # Get active jobs to monitor
                try:
                    active_jobs = await self.job_service.get_active_jobs()
                    job_updates = []
                    
                    for job in active_jobs:
                        job_id = job['id']
                        current_status = job['status']
                        current_progress = job.get('progress', 0)
                        
                        # Check for status changes
                        last_job = self.last_job_status.get(job_id, {})
                        last_status = last_job.get('status')
                        last_progress = last_job.get('progress', 0)
                        
                        job_changed = False
                        
                        # Check for status changes
                        if last_status and last_status != current_status:
                            job_updates.append({
                                'job_id': job_id,
                                'printer_id': job['printer_id'],
                                'job_name': job['job_name'],
                                'old_status': last_status,
                                'new_status': current_status,
                                'progress': current_progress,
                                'timestamp': datetime.now().isoformat()
                            })
                            job_changed = True
                            
                            # Emit specific job lifecycle events
                            if current_status == 'running' and last_status != 'running':
                                await self.emit_event('job_started', {
                                    'job_id': job_id,
                                    'printer_id': job['printer_id'],
                                    'job_name': job['job_name'],
                                    'timestamp': datetime.now().isoformat()
                                })
                                self.event_counts['job_started'] += 1
                            elif current_status in ['completed', 'failed', 'cancelled'] and last_status not in ['completed', 'failed', 'cancelled']:
                                await self.emit_event('job_completed', {
                                    'job_id': job_id,
                                    'printer_id': job['printer_id'],
                                    'job_name': job['job_name'],
                                    'status': current_status,
                                    'timestamp': datetime.now().isoformat()
                                })
                                self.event_counts['job_completed'] += 1
                        
                        # Check for significant progress changes (every 10%)
                        if abs(current_progress - last_progress) >= 10:
                            job_updates.append({
                                'job_id': job_id,
                                'printer_id': job['printer_id'],
                                'job_name': job['job_name'],
                                'status': current_status,
                                'old_progress': last_progress,
                                'new_progress': current_progress,
                                'timestamp': datetime.now().isoformat()
                            })
                            job_changed = True
                        
                        # Update last known status
                        if job_changed or job_id not in self.last_job_status:
                            self.last_job_status[job_id] = {
                                'status': current_status,
                                'progress': current_progress,
                                'last_update': datetime.now().isoformat()
                            }
                    
                    # Clean up completed jobs from tracking
                    completed_jobs = [jid for jid, jdata in self.last_job_status.items() 
                                    if jid not in [j['id'] for j in active_jobs]]
                    for job_id in completed_jobs:
                        del self.last_job_status[job_id]
                    
                    # Emit job update event if there are changes
                    if job_updates or active_jobs:
                        await self.emit_event("job_update", {
                            "timestamp": datetime.now().isoformat(),
                            "active_jobs": len(active_jobs),
                            "job_updates": job_updates
                        })
                        self.event_counts['job_update'] += 1
                        
                        if job_updates:
                            logger.debug("Job status changes detected", updates=len(job_updates))
                    
                except Exception as e:
                    logger.error("Error getting active jobs", error=str(e))

                await asyncio.sleep(PollingIntervals.JOB_STATUS_CHECK)  # 10-second job polling
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in job monitoring", error=str(e))
                await asyncio.sleep(PollingIntervals.JOB_STATUS_ERROR_BACKOFF)
                
        logger.info("Job status monitoring task stopped")
        
    async def _file_discovery_task(self):
        """Background task for discovering new files on printers."""
        logger.info("Starting file discovery task")
        
        while self._running:
            try:
                if not self.file_service:
                    await asyncio.sleep(PollingIntervals.FILE_DISCOVERY_CHECK)
                    continue
                
                new_files_found = []
                discovery_results = {}
                
                try:
                    # Discover files on all active printers
                    if self.printer_service:
                        printers = await self.printer_service.list_printers()
                        
                        for printer in printers:
                            printer_id = printer['id']
                            
                            try:
                                # Discover files on this printer
                                discovered_files = await self.file_service.discover_printer_files(printer_id)
                                
                                if discovered_files:
                                    new_files_found.extend([
                                        {
                                            'printer_id': printer_id,
                                            'printer_name': printer['name'],
                                            'filename': file_info['filename'],
                                            'file_size': file_info.get('file_size'),
                                            'file_type': file_info.get('file_type'),
                                            'discovered_at': datetime.now().isoformat()
                                        }
                                        for file_info in discovered_files
                                    ])
                                
                                discovery_results[printer_id] = {
                                    'printer_name': printer['name'],
                                    'files_found': len(discovered_files),
                                    'success': True
                                }
                                
                                logger.debug("File discovery complete for printer", 
                                           printer_id=printer_id, 
                                           files_found=len(discovered_files))
                                
                            except Exception as e:
                                logger.warning("File discovery failed for printer", 
                                             printer_id=printer_id, error=str(e))
                                discovery_results[printer_id] = {
                                    'printer_name': printer['name'],
                                    'files_found': 0,
                                    'success': False,
                                    'error': str(e)
                                }
                    
                    # Also check for new local files if file watcher is available
                    if hasattr(self.file_service, 'file_watcher') and self.file_service.file_watcher:
                        try:
                            # Trigger a scan of watch folders
                            local_files = await self.file_service.scan_local_files()
                            if local_files:
                                new_files_found.extend([
                                    {
                                        'printer_id': 'local',
                                        'printer_name': 'Local Files',
                                        'filename': file_info['filename'],
                                        'file_path': file_info.get('file_path'),
                                        'file_size': file_info.get('file_size'),
                                        'file_type': file_info.get('file_type'),
                                        'discovered_at': datetime.now().isoformat()
                                    }
                                    for file_info in local_files
                                ])
                                
                                discovery_results['local'] = {
                                    'printer_name': 'Local Files',
                                    'files_found': len(local_files),
                                    'success': True
                                }
                        except Exception as e:
                            logger.warning("Local file discovery failed", error=str(e))
                    
                    # Emit file discovery event
                    await self.emit_event("files_discovered", {
                        "timestamp": datetime.now().isoformat(),
                        "new_files": new_files_found,
                        "discovery_results": discovery_results,
                        "total_new_files": len(new_files_found)
                    })
                    self.event_counts['files_discovered'] += 1
                    
                    # Emit specific event for new files if any were found
                    if new_files_found:
                        await self.emit_event("new_files_found", {
                            "timestamp": datetime.now().isoformat(),
                            "files": new_files_found,
                            "count": len(new_files_found)
                        })
                        self.event_counts['new_files_found'] += 1
                        logger.info("New files discovered", count=len(new_files_found))
                    
                    self.last_file_discovery = datetime.now()
                    
                except Exception as e:
                    logger.error("Error during file discovery", error=str(e))

                await asyncio.sleep(PollingIntervals.FILE_DISCOVERY_CHECK)  # 5-minute file discovery interval
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in file discovery task", error=str(e))
                await asyncio.sleep(PollingIntervals.FILE_DISCOVERY_ERROR_BACKOFF)  # Wait longer on error
                
        logger.info("File discovery task stopped")
        
    def get_status(self) -> Dict[str, Any]:
        """Get current event service status."""
        return {
            "running": self._running,
            "active_tasks": len([t for t in self._tasks if not t.done()]),
            "total_tasks": len(self._tasks),
            "event_handlers": {
                event_type: len(handlers) 
                for event_type, handlers in self._event_handlers.items()
            },
            "monitoring_status": {
                "printers_tracked": len(self.last_printer_status),
                "jobs_tracked": len(self.last_job_status),
                "last_file_discovery": self.last_file_discovery.isoformat() if self.last_file_discovery else None
            },
            "event_counts": self.event_counts.copy(),
            "service_dependencies": {
                "printer_service": self.printer_service is not None,
                "job_service": self.job_service is not None,
                "file_service": self.file_service is not None,
                "database": self.database is not None
            }
        }
    
    def set_services(self, printer_service=None, job_service=None, file_service=None, database=None) -> None:
        """Set service dependencies after initialization."""
        if printer_service:
            self.printer_service = printer_service
        if job_service:
            self.job_service = job_service
        if file_service:
            self.file_service = file_service
        if database:
            self.database = database
            
        logger.info("Event service dependencies updated",
                   printer_service=self.printer_service is not None,
                   job_service=self.job_service is not None,
                   file_service=self.file_service is not None,
                   database=self.database is not None)
    
    async def force_discovery(self) -> Dict[str, Any]:
        """Force an immediate file discovery run."""
        logger.info("Forcing immediate file discovery")
        
        if not self.file_service:
            return {"error": "File service not available"}
        
        try:
            # Run discovery immediately
            new_files_found = []
            discovery_results = {}
            
            if self.printer_service:
                printers = await self.printer_service.list_printers()
                
                for printer in printers:
                    printer_id = printer['id']
                    try:
                        discovered_files = await self.file_service.discover_printer_files(printer_id)
                        if discovered_files:
                            new_files_found.extend(discovered_files)
                        discovery_results[printer_id] = {
                            'files_found': len(discovered_files),
                            'success': True
                        }
                    except Exception as e:
                        discovery_results[printer_id] = {
                            'files_found': 0,
                            'success': False,
                            'error': str(e)
                        }
            
            # Emit events
            await self.emit_event("files_discovered", {
                "timestamp": datetime.now().isoformat(),
                "new_files": new_files_found,
                "discovery_results": discovery_results,
                "forced": True
            })
            
            return {
                "success": True,
                "files_found": len(new_files_found),
                "printers_scanned": len(discovery_results)
            }
            
        except Exception as e:
            logger.error("Force discovery failed", error=str(e))
            return {"error": str(e)}
    
    async def reset_monitoring_state(self) -> None:
        """Reset all monitoring state - useful for testing or after configuration changes."""
        logger.info("Resetting event service monitoring state")
        self.last_printer_status.clear()
        self.last_job_status.clear()
        self.last_file_discovery = datetime.now()
        
        # Reset event counters
        for event_type in self.event_counts:
            self.event_counts[event_type] = 0