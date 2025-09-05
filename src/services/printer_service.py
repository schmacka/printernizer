"""
Printer service for managing printer connections and status.
Handles Bambu Lab and Prusa printer integrations with real-time monitoring.
"""
import asyncio
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID
import structlog

from database.database import Database
from services.event_service import EventService
from services.config_service import ConfigService
from models.printer import PrinterType, PrinterStatus, PrinterStatusUpdate, Printer
from printers import BambuLabPrinter, PrusaPrinter, BasePrinter
from utils.exceptions import PrinterConnectionError, NotFoundError
from integrations.homeassistant import get_homeassistant_mqtt

logger = structlog.get_logger()


class PrinterService:
    """Service for managing printer connections and monitoring."""
    
    def __init__(self, database: Database, event_service: EventService, config_service: ConfigService):
        """Initialize printer service."""
        self.database = database
        self.event_service = event_service
        self.config_service = config_service
        self.printer_instances: Dict[str, BasePrinter] = {}
        self.monitoring_active = False
        
    async def initialize(self):
        """Initialize printer service and load configured printers."""
        logger.info("Initializing printer service")
        await self._load_printers()
        await self._sync_database_printers()
        
        # Initialize Home Assistant integration if available
        await self._setup_homeassistant_integration()
        
    async def _load_printers(self):
        """Load printer configurations and create instances."""
        printer_configs = self.config_service.get_active_printers()
        
        for printer_id, config in printer_configs.items():
            try:
                # Create printer instance based on type
                printer_instance = await self._create_printer_instance(printer_id, config)
                
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
        
    async def _create_printer_instance(self, printer_id: str, config) -> Optional[BasePrinter]:
        """Create printer instance based on configuration."""
        if config.type == "bambu_lab":
            return BambuLabPrinter(
                printer_id=printer_id,
                name=config.name,
                ip_address=config.ip_address,
                access_code=config.access_code,
                serial_number=config.serial_number
            )
        elif config.type == "prusa_core":
            return PrusaPrinter(
                printer_id=printer_id,
                name=config.name,
                ip_address=config.ip_address,
                api_key=config.api_key
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
            "timestamp": status.timestamp.isoformat()
        })
        
        # Update Home Assistant if available
        await self._update_homeassistant_status(status)
        
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
            printer = Printer(
                id=printer_id,
                name=instance.name,
                type=PrinterType.BAMBU_LAB if 'bambu' in type(instance).__name__.lower() else PrinterType.PRUSA_CORE,
                ip_address=instance.ip_address,
                api_key=getattr(instance, 'api_key', None),
                access_code=getattr(instance, 'access_code', None),
                serial_number=getattr(instance, 'serial_number', None),
                is_active=True,
                status=instance.last_status.status if instance.last_status else PrinterStatus.UNKNOWN,
                last_seen=instance.last_status.timestamp if instance.last_status else None
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
        
    async def get_printer(self, printer_id: str) -> Optional[Dict[str, Any]]:
        """Get specific printer by ID."""
        instance = self.printer_instances.get(printer_id)
        if not instance:
            return None
            
        return {
            "id": printer_id,
            "name": instance.name,
            "type": type(instance).__name__.lower().replace('printer', ''),
            "ip_address": instance.ip_address,
            "is_connected": instance.is_connected,
            "last_status": instance.last_status.dict() if instance.last_status else None,
            "monitoring_active": instance._monitoring_task is not None
        }
        
    async def get_printer_status(self, printer_id: str) -> Dict[str, Any]:
        """Get current status of a printer."""
        instance = self.printer_instances.get(printer_id)
        if not instance:
            raise NotFoundError("Printer", printer_id)
            
        try:
            status = await instance.get_status()
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
            return await instance.connect()
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
                    await instance.connect()
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
                        await instance.connect()
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
                             if instance.last_status else None
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
        
    async def _setup_homeassistant_integration(self):
        """Set up Home Assistant MQTT discovery integration."""
        try:
            ha_mqtt = await get_homeassistant_mqtt()
            if ha_mqtt:
                logger.info("Setting up Home Assistant integration")
                
                # Register all active printers as Home Assistant devices
                for printer_id, instance in self.printer_instances.items():
                    config = self.config_service.get_printer(printer_id)
                    if config and config.is_active:
                        # Register device
                        ha_mqtt.register_printer_device(
                            printer_id=printer_id,
                            printer_name=config.name,
                            printer_type=config.type,
                            ip_address=config.ip_address,
                            serial_number=config.serial_number
                        )
                        
                        # Create entities
                        await ha_mqtt.create_printer_entities(
                            printer_id=printer_id,
                            printer_name=config.name,
                            printer_type=config.type
                        )
                        
                logger.info("Home Assistant integration initialized")
            else:
                logger.debug("Home Assistant integration not available")
                
        except Exception as e:
            logger.error("Failed to setup Home Assistant integration", error=str(e))
            
    async def _update_homeassistant_status(self, status: PrinterStatusUpdate):
        """Update printer status in Home Assistant."""
        try:
            ha_mqtt = await get_homeassistant_mqtt()
            if ha_mqtt:
                # Prepare status data for Home Assistant
                status_data = {
                    "status": status.status.value,
                    "connected": status.status != PrinterStatus.ERROR,
                    "progress": status.progress or 0,
                    "job_name": status.current_job,
                    "bed_temperature": status.temperature_bed,
                    "nozzle_temperature": status.temperature_nozzle,
                    "time_remaining": status.time_remaining,
                    "material_used": getattr(status, 'material_used', None),
                    "cost_eur": getattr(status, 'cost_eur', None),
                    "last_job_completion": status.timestamp.isoformat() if status.status == PrinterStatus.COMPLETED else None
                }
                
                await ha_mqtt.update_printer_state(status.printer_id, status_data)
                
        except Exception as e:
            logger.error("Failed to update Home Assistant status", 
                        printer_id=status.printer_id, error=str(e))