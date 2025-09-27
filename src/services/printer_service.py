"""
Printer service for managing printer connections and status.
Handles Bambu Lab and Prusa printer integrations with real-time monitoring.
"""
import asyncio
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID
from datetime import datetime
import structlog

from src.database.database import Database
from src.services.event_service import EventService
from src.services.config_service import ConfigService
from src.models.printer import PrinterType, PrinterStatus, PrinterStatusUpdate, Printer
from src.printers import BambuLabPrinter, PrusaPrinter, BasePrinter
from src.utils.exceptions import PrinterConnectionError, NotFoundError

logger = structlog.get_logger()


class PrinterService:
    """Service for managing printer connections and monitoring."""
    
    def __init__(self, database: Database, event_service: EventService, config_service: ConfigService, file_service=None):
        """Initialize printer service."""
        self.database = database
        self.event_service = event_service
        self.config_service = config_service
        self.file_service = file_service
        self.printer_instances: Dict[str, BasePrinter] = {}
        self.monitoring_active = False
        # Track job filenames we've already attempted to auto-download to avoid loops
        self._auto_download_attempts: Dict[str, set] = {}
        
    async def initialize(self):
        """Initialize printer service and load configured printers."""
        logger.info("Initializing printer service")
        await self._load_printers()
        await self._sync_database_printers()
        
        
    async def _load_printers(self):
        """Load printer configurations and create instances."""
        printer_configs = self.config_service.get_active_printers()
        
        for printer_id, config in printer_configs.items():
            try:
                # Create printer instance based on type
                printer_instance = self._create_printer_instance(printer_id, config)
                
                if printer_instance:
                    self.printer_instances[printer_id] = printer_instance
                    
                    # Add status callback for real-time updates
                    printer_instance.add_status_callback(
                        lambda status: asyncio.create_task(
                            self._handle_status_update(status)
                        )
                    )
                    
                    logger.info("Loaded printer instance", 
                               printer_id=printer_id, type=config.type)
                    
            except Exception as e:
                logger.error("Failed to create printer instance", 
                           printer_id=printer_id, error=str(e))
                           
        logger.info("Printer instances loaded", count=len(self.printer_instances))
        
    def _create_printer_instance(self, printer_id: str, config) -> Optional[BasePrinter]:
        """Create printer instance based on configuration."""
        if config.type == "bambu_lab":
            return BambuLabPrinter(
                printer_id=printer_id,
                name=config.name,
                ip_address=config.ip_address,
                access_code=config.access_code,
                serial_number=config.serial_number,
                file_service=self.file_service
            )
        elif config.type == "prusa_core":
            return PrusaPrinter(
                printer_id=printer_id,
                name=config.name,
                ip_address=config.ip_address,
                api_key=config.api_key,
                file_service=self.file_service
            )
        else:
            logger.warning("Unknown printer type", printer_id=printer_id, type=config.type)
            return None
            
    async def _sync_database_printers(self):
        """Sync printer configurations with database."""
        async with self.database._connection.cursor() as cursor:
            for printer_id, instance in self.printer_instances.items():
                # Insert or update printer in database
                await cursor.execute("""
                    INSERT OR REPLACE INTO printers 
                    (id, name, type, ip_address, api_key, access_code, serial_number, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    printer_id,
                    instance.name,
                    getattr(instance, '__class__').__name__.lower().replace('printer', ''),
                    instance.ip_address,
                    getattr(instance, 'api_key', None),
                    getattr(instance, 'access_code', None),
                    getattr(instance, 'serial_number', None),
                    True
                ))
                
            await self.database._connection.commit()
        logger.info("Synchronized printers with database")
        
    async def _handle_status_update(self, status: PrinterStatusUpdate):
        """Handle status updates from printers."""
        # Store status in database
        await self._store_status_update(status)
        
        # Emit event for real-time updates
        await self.event_service.emit_event("printer_status_update", {
            "printer_id": status.printer_id,
            "status": status.status.value,
            "message": status.message,
            "temperature_bed": status.temperature_bed,
            "temperature_nozzle": status.temperature_nozzle,
            "progress": status.progress,
            "current_job": status.current_job,
            "current_job_file_id": status.current_job_file_id,
            "current_job_has_thumbnail": status.current_job_has_thumbnail,
            "current_job_thumbnail_url": status.current_job_thumbnail_url,
            "timestamp": status.timestamp.isoformat()
        })

        # Auto-download & process current job file if we have a printing job without a thumbnail yet
        try:
            if (self.file_service and
                status.status == PrinterStatus.PRINTING and
                status.current_job and
                # Only if we don't already have a file id or we have no thumbnail
                (not status.current_job_file_id or status.current_job_has_thumbnail is False)):

                filename = status.current_job
                printer_id = status.printer_id

                # Initialize attempts tracking for this printer
                if printer_id not in self._auto_download_attempts:
                    self._auto_download_attempts[printer_id] = set()

                # Normalize filename (strip any leading cache/ from Bambu, handled earlier usually)
                if filename.startswith('cache/'):
                    filename_to_download = filename.split('/', 1)[1]
                else:
                    filename_to_download = filename

                # Only proceed if looks like a printable file and not attempted already
                if (self._is_print_file(filename_to_download) and
                    filename_to_download not in self._auto_download_attempts[printer_id]):
                    self._auto_download_attempts[printer_id].add(filename_to_download)
                    asyncio.create_task(self._attempt_download_current_job(printer_id, filename_to_download))
        except Exception as e:
            logger.debug("Auto-download check failed", error=str(e))

    def _is_print_file(self, filename: str) -> bool:
        """Heuristic: check if filename has a known printable extension."""
        printable_exts = {'.gcode', '.bgcode', '.3mf'}
        lower = filename.lower()
        import os as _os
        return _os.path.splitext(lower)[1] in printable_exts

    async def _attempt_download_current_job(self, printer_id: str, filename: str):
        """Attempt to download the currently printing file so thumbnail extraction can occur."""
        try:
            logger.info("Auto-downloading active print file for thumbnail processing",
                        printer_id=printer_id, filename=filename)

            async def _attempt(name: str) -> Optional[Dict[str, Any]]:
                try:
                    return await self.file_service.download_file(printer_id, name)
                except Exception as e:
                    logger.debug("Variant download attempt raised exception", printer_id=printer_id, variant=name, error=str(e))
                    return {"status": "error", "message": str(e)}

            # First attempt: exact reported filename
            attempts: List[tuple[str, Dict[str, Any]]] = []
            primary = await _attempt(filename)
            attempts.append((filename, primary))

            if primary and primary.get("status") == "success":
                logger.info("Auto-download completed", printer_id=printer_id, filename=filename)
                return

            # Collect printer file list to find a near match (case-insensitive, stripped)
            try:
                printer_files = await self.get_printer_files(printer_id)
            except Exception as e:
                printer_files = []
                logger.debug("Could not list printer files for variant matching", printer_id=printer_id, error=str(e))

            reported_lower = filename.lower().strip()
            # Generate candidate variants
            variants = set()
            # 1. Exact names from printer that case-insensitively match
            for f in printer_files:
                fname = f.get("filename") or ""
                if fname.lower() == reported_lower and fname != filename:
                    variants.add(fname)
            # 2. Replace problematic characters (commas, parentheses) with underscores / remove
            simple = filename.replace('(', '').replace(')', '').replace(',', '').replace('  ', ' ').strip()
            if simple != filename:
                variants.add(simple)
            underscore_variant = simple.replace(' ', '_')
            if underscore_variant != simple:
                variants.add(underscore_variant)
            # 3. Collapse multiple spaces
            import re as _re
            collapsed = _re.sub(r'\s+', ' ', filename).strip()
            if collapsed != filename:
                variants.add(collapsed)
            # 4. Some slicers truncate long names on printer storage - try prefix matches
            for f in printer_files:
                fname = f.get("filename") or ""
                if fname.lower().startswith(reported_lower[:20]) and abs(len(fname) - len(filename)) > 5:
                    variants.add(fname)

            # Try each variant until success
            for variant in variants:
                if variant in self._auto_download_attempts.get(printer_id, set()):
                    continue  # already tried
                self._auto_download_attempts[printer_id].add(variant)
                res = await _attempt(variant)
                attempts.append((variant, res))
                if res and res.get("status") == "success":
                    logger.info("Auto-download completed via variant", printer_id=printer_id, original=filename, variant=variant)
                    return

            # If we reach here all attempts failed
            last_msg = attempts[-1][1].get("message") if attempts else "unknown"
            logger.warning("Auto-download failed", printer_id=printer_id, filename=filename, attempts=[{"variant": v, "status": r.get("status"), "message": r.get("message")} for v, r in attempts], message=last_msg)
        except Exception as e:
            logger.warning("Auto-download exception", printer_id=printer_id, filename=filename, error=str(e))
        
        
    async def _store_status_update(self, status: PrinterStatusUpdate):
        """Store status update in database for history."""
        # This would typically update a printer_status_history table
        # For now, we'll just log it
        logger.info("Printer status update", 
                   printer_id=status.printer_id,
                   status=status.status.value,
                   progress=status.progress)
                   
    async def list_printers(self) -> List[Printer]:
        """Get list of all configured printers as Printer objects."""
        printers = []
        
        for printer_id, instance in self.printer_instances.items():
            # Determine current status
            current_status = PrinterStatus.OFFLINE
            last_seen = None
            
            if instance.is_connected:
                if instance.last_status:
                    current_status = instance.last_status.status
                    last_seen = instance.last_status.timestamp
                else:
                    current_status = PrinterStatus.ONLINE
                    # If connected but no status yet, use current time as last_seen
                    last_seen = datetime.now()
            
            printer = Printer(
                id=printer_id,
                name=instance.name,
                type=PrinterType.BAMBU_LAB if 'bambu' in type(instance).__name__.lower() else PrinterType.PRUSA_CORE,
                ip_address=instance.ip_address,
                api_key=getattr(instance, 'api_key', None),
                access_code=getattr(instance, 'access_code', None),
                serial_number=getattr(instance, 'serial_number', None),
                is_active=True,
                status=current_status,
                last_seen=last_seen
            )
            printers.append(printer)
            
        return printers
        
    async def get_printers(self) -> List[Dict[str, Any]]:
        """Get list of all configured printers as dictionaries (legacy method)."""
        printers = []
        
        for printer_id, instance in self.printer_instances.items():
            printer_data = {
                "id": printer_id,
                "name": instance.name,
                "type": type(instance).__name__.lower().replace('printer', ''),
                "ip_address": instance.ip_address,
                "is_connected": instance.is_connected,
                "last_status": instance.last_status.dict() if instance.last_status else None
            }
            printers.append(printer_data)
            
        return printers
        
    async def get_printer(self, printer_id: str) -> Optional[Printer]:
        """Get specific printer by ID as domain model."""
        instance = self.printer_instances.get(printer_id)
        if not instance:
            return None

        current_status = PrinterStatus.OFFLINE
        last_seen = None
        if instance.is_connected:
            if instance.last_status:
                current_status = instance.last_status.status
                last_seen = instance.last_status.timestamp
            else:
                current_status = PrinterStatus.ONLINE

        return Printer(
            id=printer_id,
            name=instance.name,
            type=PrinterType.BAMBU_LAB if 'bambu' in type(instance).__name__.lower() else PrinterType.PRUSA_CORE,
            ip_address=instance.ip_address,
            api_key=getattr(instance, 'api_key', None),
            access_code=getattr(instance, 'access_code', None),
            serial_number=getattr(instance, 'serial_number', None),
            is_active=True,
            status=current_status,
            last_seen=last_seen
        )

    async def get_printer_driver(self, printer_id: str) -> Optional[BasePrinter]:
        """Get printer driver instance for direct access."""
        return self.printer_instances.get(printer_id)
        
    async def get_printer_status(self, printer_id: str) -> Dict[str, Any]:
        """Get current status of a printer."""
        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)
            
        try:
            status = await instance.get_status()
            # Update last_seen when we successfully get status
            from datetime import datetime
            await self.database.update_printer_status(
                printer_id,
                status.status.value.lower(),  # Convert enum to string
                datetime.now()
            )
            return {
                "printer_id": status.printer_id,
                "status": status.status.value,
                "message": status.message,
                "temperature_bed": status.temperature_bed,
                "temperature_nozzle": status.temperature_nozzle,
                "progress": status.progress,
                "current_job": status.current_job,
                "timestamp": status.timestamp.isoformat()
            }
        except Exception as e:
            logger.error("Failed to get printer status", printer_id=printer_id, error=str(e))
            return {
                "printer_id": printer_id,
                "status": "error",
                "message": f"Status check failed: {str(e)}"
            }
            
    async def connect_printer(self, printer_id: str) -> bool:
        """Connect to a specific printer."""
        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)

        try:
            result = await instance.connect()
            if result:
                # Update last_seen timestamp in database when connection succeeds
                from datetime import datetime
                await self.database.update_printer_status(
                    printer_id,
                    "online",  # Set status to online when connected
                    datetime.now()
                )
            return result
        except Exception as e:
            logger.error("Failed to connect printer", printer_id=printer_id, error=str(e))
            raise PrinterConnectionError(printer_id, str(e))
            
    async def disconnect_printer(self, printer_id: str) -> bool:
        """Disconnect from a specific printer."""
        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)
            
        try:
            await instance.disconnect()
            return True
        except Exception as e:
            logger.error("Failed to disconnect printer", printer_id=printer_id, error=str(e))
            return False
            
    async def start_monitoring(self, printer_id: Optional[str] = None) -> bool:
        """Start printer monitoring for all or specific printer."""
        if printer_id:
            # Start monitoring for specific printer
            instance = self.printer_instances.get(printer_id)
            if not instance:
                raise NotFoundError("Printer", printer_id)

            try:
                if not instance.is_connected:
                    connected = await instance.connect()
                    if connected:
                        # Update last_seen timestamp when connection succeeds
                        from datetime import datetime
                        await self.database.update_printer_status(
                            printer_id,
                            "online",
                            datetime.now()
                        )
                await instance.start_monitoring()
                logger.info("Started monitoring for printer", printer_id=printer_id)
                return True
            except Exception as e:
                logger.error("Failed to start monitoring", printer_id=printer_id, error=str(e))
                return False
        else:
            # Start monitoring for all printers
            success_count = 0
            
            for printer_id, instance in self.printer_instances.items():
                try:
                    if not instance.is_connected:
                        connected = await instance.connect()
                        if connected:
                            # Update last_seen timestamp when connection succeeds
                            from datetime import datetime
                            await self.database.update_printer_status(
                                printer_id,
                                "online",
                                datetime.now()
                            )
                    await instance.start_monitoring()
                    success_count += 1
                except Exception as e:
                    logger.error("Failed to start monitoring", printer_id=printer_id, error=str(e))
                    
            self.monitoring_active = success_count > 0
            logger.info("Started printer monitoring", active_printers=success_count)
            return success_count > 0
        
    async def stop_monitoring(self, printer_id: Optional[str] = None) -> bool:
        """Stop printer monitoring for all or specific printer."""
        if printer_id:
            # Stop monitoring for specific printer
            instance = self.printer_instances.get(printer_id)
            if not instance:
                raise NotFoundError("Printer", printer_id)
                
            try:
                await instance.stop_monitoring()
                logger.info("Stopped monitoring for printer", printer_id=printer_id)
                return True
            except Exception as e:
                logger.error("Failed to stop monitoring", printer_id=printer_id, error=str(e))
                return False
        else:
            # Stop monitoring for all printers
            for printer_id, instance in self.printer_instances.items():
                try:
                    await instance.stop_monitoring()
                except Exception as e:
                    logger.error("Failed to stop monitoring", printer_id=printer_id, error=str(e))
                    
            self.monitoring_active = False
            logger.info("Stopped all printer monitoring")
            return True
            
    async def get_printer_files(self, printer_id: str) -> List[Dict[str, Any]]:
        """Get list of files available on printer."""
        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)
            
        if not instance.is_connected:
            await instance.connect()
            
        try:
            files = await instance.list_files()
            return [
                {
                    "filename": f.filename,
                    "size": f.size,
                    "modified": f.modified.isoformat() if f.modified else None,
                    "path": f.path
                }
                for f in files
            ]
        except Exception as e:
            logger.error("Failed to get printer files", printer_id=printer_id, error=str(e))
            raise PrinterConnectionError(printer_id, f"File listing failed: {str(e)}")
            
    async def download_printer_file(self, printer_id: str, filename: str, local_path: str) -> bool:
        """Download a file from printer."""
        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)
            
        if not instance.is_connected:
            await instance.connect()
            
        try:
            return await instance.download_file(filename, local_path)
        except Exception as e:
            logger.error("Failed to download file", 
                        printer_id=printer_id, filename=filename, error=str(e))
            return False

    async def download_current_job_file(self, printer_id: str) -> Dict[str, Any]:
        """Download (and process) the currently printing job file to generate a thumbnail.

        Logic:
          1. Get current status
          2. If no active job -> return informative response
          3. If file already known & has thumbnail -> return existing
          4. If file known but no thumbnail & local path present -> process thumbnails directly
          5. Else attempt download from printer (FileService handles async thumbnail processing)
        """
        if not self.file_service:
            return {"status": "error", "message": "File service unavailable"}

        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)

        # Ensure connection
        if not instance.is_connected:
            try:
                await instance.connect()
            except Exception as e:
                return {"status": "error", "message": f"Connect failed: {e}"}

        try:
            status = await instance.get_status()
        except Exception as e:
            return {"status": "error", "message": f"Status failed: {e}"}

        if not status.current_job:
            return {"status": "no_active_job", "message": "No active print job"}

        filename = status.current_job
        if filename.startswith('cache/'):
            filename = filename.split('/', 1)[1]

        # Check existing record
        existing = None
        try:
            existing = await self.file_service.find_file_by_name(filename, printer_id)
        except Exception:
            pass

        if existing and existing.get('has_thumbnail'):
            return {
                "status": "exists_with_thumbnail",
                "file_id": existing.get('id'),
                "message": "File already processed with thumbnail"
            }

        # If existing without thumbnail but local_path available -> process immediately
        if existing and not existing.get('has_thumbnail') and existing.get('file_path'):
            processed = await self.file_service.process_file_thumbnails(existing.get('file_path'), existing.get('id'))
            return {
                "status": "processed" if processed else "process_failed",
                "file_id": existing.get('id'),
                "message": "Processed existing local file" if processed else "Processing failed"
            }

        # Attempt download
        try:
            dl_result = await self.file_service.download_file(printer_id, filename)
            return {
                "status": dl_result.get('status'),
                "file_id": dl_result.get('file_id'),
                "message": dl_result.get('message'),
                "note": "Thumbnail processing runs asynchronously after download"
            }
        except Exception as e:
            return {"status": "error", "message": f"Download failed: {e}"}
            
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all printer connections."""
        health_status = {
            "service_active": True,
            "monitoring_active": self.monitoring_active,
            "total_printers": len(self.printer_instances),
            "connected_printers": 0,
            "healthy_printers": 0,
            "printers": {}
        }
        
        for printer_id, instance in self.printer_instances.items():
            is_connected = instance.is_connected
            is_healthy = await instance.health_check() if is_connected else False
            
            if is_connected:
                health_status["connected_printers"] += 1
            if is_healthy:
                health_status["healthy_printers"] += 1
                
            health_status["printers"][printer_id] = {
                "connected": is_connected,
                "healthy": is_healthy,
                "last_seen": instance.last_status.timestamp.isoformat() 
                             if instance.last_status else None,
                "monitoring": getattr(instance, "get_monitoring_metrics", lambda: {})()
            }
            
        return health_status
        
    async def shutdown(self):
        """Gracefully shutdown printer service."""
        logger.info("Shutting down printer service")
        
        # Stop all monitoring
        await self.stop_monitoring()
        
        # Disconnect all printers
        for printer_id, instance in self.printer_instances.items():
            try:
                await instance.disconnect()
            except Exception as e:
                logger.error("Error disconnecting printer", printer_id=printer_id, error=str(e))
                
        self.printer_instances.clear()
        logger.info("Printer service shutdown complete")
            
    # API-compatible methods for the router
    async def create_printer(self, name: str, printer_type: PrinterType, 
                           connection_config: Dict[str, Any], 
                           location: Optional[str] = None, 
                           description: Optional[str] = None) -> Printer:
        """Create a new printer configuration."""
        printer_id = str(uuid4())
        
        # Map printer type to string
        type_str = "bambu_lab" if printer_type == PrinterType.BAMBU_LAB else "prusa_core"
        
        # Create configuration dict
        config_dict = {
            "name": name,
            "type": type_str,
            **connection_config
        }
        
        # Add to configuration service
        if not self.config_service.add_printer(printer_id, config_dict):
            raise ValueError("Failed to add printer configuration")
            
        # Create and add instance
        config = self.config_service.get_printer(printer_id)
        if config:
            instance = self._create_printer_instance(printer_id, config)
            if instance:
                self.printer_instances[printer_id] = instance
                
                # Add to database
                await self.database.create_printer({
                    "id": printer_id,
                    "name": name,
                    "type": type_str,
                    "ip_address": connection_config.get("ip_address"),
                    "api_key": connection_config.get("api_key"),
                    "access_code": connection_config.get("access_code"),
                    "serial_number": connection_config.get("serial_number"),
                    "is_active": True
                })
                
        return Printer(
            id=printer_id,
            name=name,
            type=printer_type,
            ip_address=connection_config.get("ip_address"),
            api_key=connection_config.get("api_key"),
            access_code=connection_config.get("access_code"),
            serial_number=connection_config.get("serial_number"),
            is_active=True,
            status=PrinterStatus.UNKNOWN
        )
        
    async def update_printer(self, printer_id: UUID, **updates) -> Optional[Printer]:
        """Update printer configuration."""
        printer_id_str = str(printer_id)
        
        # Get current configuration
        config = self.config_service.get_printer(printer_id_str)
        if not config:
            return None
            
        # Update configuration
        config_dict = config.to_dict()
        
        # Map API fields to config fields
        if "name" in updates:
            config_dict["name"] = updates["name"]
        if "connection_config" in updates:
            config_dict.update(updates["connection_config"])
        if "is_enabled" in updates:
            config_dict["is_active"] = updates["is_enabled"]
            
        # Save updated configuration
        if not self.config_service.add_printer(printer_id_str, config_dict):
            return None
            
        # Recreate printer instance if it exists
        if printer_id_str in self.printer_instances:
            old_instance = self.printer_instances[printer_id_str]
            if old_instance.is_connected:
                await old_instance.disconnect()
                
            new_config = self.config_service.get_printer(printer_id_str)
            if new_config:
                new_instance = self._create_printer_instance(printer_id_str, new_config)
                if new_instance:
                    self.printer_instances[printer_id_str] = new_instance
                    
        # Return updated printer
        updated_config = self.config_service.get_printer(printer_id_str)
        if updated_config:
            return Printer(
                id=printer_id_str,
                name=updated_config.name,
                type=PrinterType.BAMBU_LAB if updated_config.type == "bambu_lab" else PrinterType.PRUSA_CORE,
                ip_address=updated_config.ip_address,
                api_key=updated_config.api_key,
                access_code=updated_config.access_code,
                serial_number=updated_config.serial_number,
                is_active=updated_config.is_active,
                status=PrinterStatus.UNKNOWN
            )
        return None
        
    async def delete_printer(self, printer_id: UUID) -> bool:
        """Delete a printer configuration."""
        printer_id_str = str(printer_id)
        
        # Disconnect if connected
        if printer_id_str in self.printer_instances:
            instance = self.printer_instances[printer_id_str]
            if instance.is_connected:
                await instance.disconnect()
            del self.printer_instances[printer_id_str]
            
        # Remove from configuration
        return self.config_service.remove_printer(printer_id_str)
        
    async def pause_printer(self, printer_id: str) -> bool:
        """Pause printing on a specific printer."""
        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)
            
        try:
            if not instance.is_connected:
                await instance.connect()
            return await instance.pause_print()
        except Exception as e:
            logger.error("Failed to pause printer", printer_id=printer_id, error=str(e))
            raise PrinterConnectionError(printer_id, str(e))
            
    async def resume_printer(self, printer_id: str) -> bool:
        """Resume printing on a specific printer."""
        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)
            
        try:
            if not instance.is_connected:
                await instance.connect()
            return await instance.resume_print()
        except Exception as e:
            logger.error("Failed to resume printer", printer_id=printer_id, error=str(e))
            raise PrinterConnectionError(printer_id, str(e))
            
    async def stop_printer(self, printer_id: str) -> bool:
        """Stop/cancel printing on a specific printer."""
        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)
            
        try:
            if not instance.is_connected:
                await instance.connect()
            return await instance.stop_print()
        except Exception as e:
            logger.error("Failed to stop printer", printer_id=printer_id, error=str(e))
            raise PrinterConnectionError(printer_id, str(e))
        
