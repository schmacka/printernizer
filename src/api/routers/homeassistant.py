"""
Home Assistant specific API endpoints for the Printernizer addon.
Provides integration-specific functionality and configuration management.
"""

import os
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import structlog

from services.printer_service import PrinterService
from services.config_service import ConfigService
from integrations.homeassistant import get_homeassistant_mqtt
from utils.dependencies import get_printer_service, get_config_service

logger = structlog.get_logger()

router = APIRouter(prefix="/homeassistant", tags=["Home Assistant Integration"])


class AddonInfo(BaseModel):
    """Home Assistant addon information"""
    name: str = "Printernizer"
    version: str = "1.0.0"  
    description: str = "Professional 3D print management system"
    startup: str = "services"
    boot: str = "auto"
    homeassistant_integration: bool = True
    mqtt_available: bool = False


class AddonConfig(BaseModel):
    """Home Assistant addon configuration"""
    timezone: str = "Europe/Berlin"
    log_level: str = "info"
    cors_origins: List[str] = []
    printer_polling_interval: int = 30
    max_concurrent_downloads: int = 5
    enable_websockets: bool = True
    business_features: Dict[str, Any] = {
        "enable_german_compliance": True,
        "vat_rate": 19.0,
        "currency": "EUR"
    }


class MQTTStatus(BaseModel):
    """MQTT connection status"""
    connected: bool = False
    host: Optional[str] = None
    port: Optional[int] = None
    discovery_prefix: str = "homeassistant"
    devices_registered: int = 0
    entities_created: int = 0


class HomeAssistantStatus(BaseModel):
    """Overall Home Assistant integration status"""
    addon_running: bool = True
    supervisor_available: bool = False
    mqtt_integration: MQTTStatus
    devices_count: int = 0
    entities_count: int = 0


@router.get("/info", response_model=AddonInfo)
async def get_addon_info() -> AddonInfo:
    """Get Home Assistant addon information."""
    
    # Check if MQTT is available
    ha_mqtt = await get_homeassistant_mqtt()
    mqtt_available = ha_mqtt is not None and ha_mqtt.connected
    
    return AddonInfo(
        mqtt_available=mqtt_available
    )


@router.get("/status", response_model=HomeAssistantStatus)
async def get_integration_status(
    printer_service: PrinterService = Depends(get_printer_service)
) -> HomeAssistantStatus:
    """Get comprehensive Home Assistant integration status."""
    
    try:
        # Check MQTT status
        ha_mqtt = await get_homeassistant_mqtt()
        mqtt_status = MQTTStatus()
        
        if ha_mqtt:
            mqtt_status.connected = ha_mqtt.connected
            mqtt_status.host = ha_mqtt.mqtt_host
            mqtt_status.port = ha_mqtt.mqtt_port
            mqtt_status.devices_registered = len(ha_mqtt.devices)
            mqtt_status.entities_created = len(ha_mqtt.entities)
        
        # Check supervisor API availability
        supervisor_available = os.path.exists('/run/s6/services')
        
        # Count printers and entities
        printers = await printer_service.get_all_printers()
        devices_count = len([p for p in printers if p.is_active])
        entities_count = devices_count * 8  # ~8 entities per printer
        
        return HomeAssistantStatus(
            supervisor_available=supervisor_available,
            mqtt_integration=mqtt_status,
            devices_count=devices_count,
            entities_count=entities_count
        )
        
    except Exception as e:
        logger.error("Failed to get integration status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration status: {str(e)}"
        )


@router.get("/config", response_model=AddonConfig)
async def get_addon_config() -> AddonConfig:
    """Get current addon configuration from environment."""
    
    return AddonConfig(
        timezone=os.getenv("TZ", "Europe/Berlin"),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        cors_origins=os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [],
        printer_polling_interval=int(os.getenv("PRINTER_POLLING_INTERVAL", "30")),
        max_concurrent_downloads=int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "5")),
        enable_websockets=os.getenv("ENABLE_WEBSOCKETS", "true").lower() == "true",
        business_features={
            "enable_german_compliance": os.getenv("ENABLE_GERMAN_COMPLIANCE", "true").lower() == "true",
            "vat_rate": float(os.getenv("VAT_RATE", "19.0")),
            "currency": os.getenv("CURRENCY", "EUR")
        }
    )


@router.post("/mqtt/rediscover")
async def rediscover_mqtt_devices(
    printer_service: PrinterService = Depends(get_printer_service)
) -> Dict[str, Any]:
    """Rediscover and recreate MQTT devices in Home Assistant."""
    
    try:
        ha_mqtt = await get_homeassistant_mqtt()
        if not ha_mqtt:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MQTT integration not available"
            )
            
        if not ha_mqtt.connected:
            # Attempt to reconnect
            await ha_mqtt.connect()
            
        if not ha_mqtt.connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to MQTT broker"
            )
        
        # Get all active printers
        printers = await printer_service.get_all_printers()
        active_printers = [p for p in printers if p.is_active]
        
        devices_created = 0
        entities_created = 0
        
        # Re-register all devices
        for printer in active_printers:
            # Register device
            ha_mqtt.register_printer_device(
                printer_id=printer.id,
                printer_name=printer.name,
                printer_type=printer.type.value.lower(),
                ip_address=printer.ip_address,
                serial_number=printer.serial_number
            )
            devices_created += 1
            
            # Create entities  
            await ha_mqtt.create_printer_entities(
                printer_id=printer.id,
                printer_name=printer.name,
                printer_type=printer.type.value.lower()
            )
            entities_created += 8  # ~8 entities per printer
            
        logger.info("MQTT devices rediscovered", 
                   devices=devices_created, entities=entities_created)
                   
        return {
            "success": True,
            "devices_created": devices_created,
            "entities_created": entities_created,
            "message": f"Successfully rediscovered {devices_created} devices with {entities_created} entities"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to rediscover MQTT devices", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rediscover devices: {str(e)}"
        )


@router.delete("/mqtt/devices")
async def remove_all_mqtt_devices(
    printer_service: PrinterService = Depends(get_printer_service)
) -> Dict[str, Any]:
    """Remove all MQTT devices from Home Assistant."""
    
    try:
        ha_mqtt = await get_homeassistant_mqtt()
        if not ha_mqtt or not ha_mqtt.connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MQTT integration not available"
            )
        
        # Get all printers
        printers = await printer_service.get_all_printers()
        
        devices_removed = 0
        for printer in printers:
            await ha_mqtt.remove_printer(printer.id)
            devices_removed += 1
            
        logger.info("MQTT devices removed", count=devices_removed)
        
        return {
            "success": True,
            "devices_removed": devices_removed,
            "message": f"Successfully removed {devices_removed} devices from Home Assistant"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove MQTT devices", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove devices: {str(e)}"
        )


@router.get("/entities/{printer_id}")
async def get_printer_entities(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
) -> Dict[str, Any]:
    """Get Home Assistant entities for a specific printer."""
    
    try:
        # Verify printer exists
        printer = await printer_service.get_printer(printer_id)
        if not printer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Printer {printer_id} not found"
            )
            
        ha_mqtt = await get_homeassistant_mqtt()
        if not ha_mqtt:
            return {
                "printer_id": printer_id,
                "printer_name": printer.name,
                "mqtt_available": False,
                "entities": []
            }
        
        # Get entities for this printer
        printer_entities = [
            entity for entity_id, entity in ha_mqtt.entities.items()
            if entity_id.startswith(f"printernizer_{printer_id}_")
        ]
        
        entities_info = []
        for entity in printer_entities:
            entities_info.append({
                "unique_id": entity.unique_id,
                "name": entity.name,
                "state_topic": entity.state_topic,
                "device_class": entity.device_class,
                "unit_of_measurement": entity.unit_of_measurement,
                "icon": entity.icon
            })
            
        return {
            "printer_id": printer_id,
            "printer_name": printer.name,
            "mqtt_available": True,
            "entities": entities_info,
            "entity_count": len(entities_info)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get printer entities", 
                    printer_id=printer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get entities: {str(e)}"
        )


@router.get("/supervisor/info")
async def get_supervisor_info() -> Dict[str, Any]:
    """Get Home Assistant Supervisor information (if available)."""
    
    supervisor_available = os.path.exists('/run/s6/services')
    
    info = {
        "supervisor_available": supervisor_available,
        "addon_slug": "printernizer",
        "environment": os.getenv("ENVIRONMENT", "standalone")
    }
    
    if supervisor_available:
        # Additional supervisor info could be added here
        info.update({
            "s6_services": os.path.exists('/run/s6/services'),
            "supervisor_token": bool(os.getenv("SUPERVISOR_TOKEN")),
            "addon_data_path": "/data",
            "addon_config_path": "/data/options.json" if os.path.exists("/data/options.json") else None
        })
    
    return info


@router.get("/health")
async def addon_health_check() -> Dict[str, Any]:
    """Health check endpoint for Home Assistant addon monitoring."""
    
    try:
        # Check basic service health
        health_status = {
            "status": "healthy",
            "timestamp": "2025-09-05T12:00:00Z",
            "checks": {}
        }
        
        # Check MQTT connection
        ha_mqtt = await get_homeassistant_mqtt()
        health_status["checks"]["mqtt"] = {
            "available": ha_mqtt is not None,
            "connected": ha_mqtt.connected if ha_mqtt else False
        }
        
        # Check file system
        health_status["checks"]["filesystem"] = {
            "data_dir": os.path.exists("/data"),
            "writable": os.access("/data", os.W_OK) if os.path.exists("/data") else False
        }
        
        # Check environment
        health_status["checks"]["environment"] = {
            "timezone": os.getenv("TZ"),
            "log_level": os.getenv("LOG_LEVEL"),
            "supervisor": os.path.exists('/run/s6/services')
        }
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-09-05T12:00:00Z"
        }