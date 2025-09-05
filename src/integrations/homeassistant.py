"""
Home Assistant Integration for Printernizer
Provides MQTT discovery, entity management, and state updates for Home Assistant
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import paho.mqtt.client as mqtt_client
from paho.mqtt.client import Client as MQTTClient

from models.printer import PrinterStatus
from models.job import JobStatus
from utils.config import get_settings


logger = logging.getLogger(__name__)


class DeviceClass(Enum):
    """Home Assistant device classes for sensors"""
    TEMPERATURE = "temperature"
    DURATION = "duration"
    TIMESTAMP = "timestamp"
    POWER = "power"
    ENERGY = "energy"
    PERCENTAGE = "percentage"


@dataclass
class HADevice:
    """Home Assistant device information"""
    identifiers: List[str]
    manufacturer: str
    model: str
    name: str
    sw_version: Optional[str] = None
    configuration_url: Optional[str] = None


@dataclass
class HAEntityConfig:
    """Home Assistant entity configuration for MQTT discovery"""
    name: str
    unique_id: str
    state_topic: str
    device: HADevice
    availability_topic: Optional[str] = None
    device_class: Optional[str] = None
    unit_of_measurement: Optional[str] = None
    icon: Optional[str] = None
    entity_category: Optional[str] = None
    value_template: Optional[str] = None
    json_attributes_topic: Optional[str] = None


class HomeAssistantMQTT:
    """Home Assistant MQTT integration for Printernizer"""
    
    def __init__(self, 
                 mqtt_host: str = "localhost", 
                 mqtt_port: int = 1883,
                 mqtt_username: Optional[str] = None,
                 mqtt_password: Optional[str] = None,
                 discovery_prefix: str = "homeassistant"):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port  
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        self.discovery_prefix = discovery_prefix
        self.client: Optional[MQTTClient] = None
        self.connected = False
        
        # Topic structure: printernizer/{printer_id}/{entity}
        self.state_prefix = "printernizer"
        
        # Registered devices and entities
        self.devices: Dict[str, HADevice] = {}
        self.entities: Dict[str, HAEntityConfig] = {}
        
    async def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            self.client = mqtt_client.Client()
            
            if self.mqtt_username and self.mqtt_password:
                self.client.username_pw_set(self.mqtt_username, self.mqtt_password)
                
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            await asyncio.get_event_loop().run_in_executor(
                None, 
                self.client.connect, 
                self.mqtt_host, 
                self.mqtt_port, 
                60
            )
            
            # Start MQTT loop in background
            self.client.loop_start()
            
            logger.info(f"Connected to Home Assistant MQTT at {self.mqtt_host}:{self.mqtt_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
            
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to Home Assistant MQTT broker")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
            
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        logger.warning("Disconnected from Home Assistant MQTT broker")
        
    def _on_message(self, client, userdata, msg):
        """MQTT message callback"""
        logger.debug(f"Received MQTT message: {msg.topic} -> {msg.payload.decode()}")
        
    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            
    def register_printer_device(self, printer_id: str, printer_name: str, printer_type: str, 
                              ip_address: str, serial_number: Optional[str] = None) -> HADevice:
        """Register a 3D printer as a Home Assistant device"""
        
        device = HADevice(
            identifiers=[f"printernizer_{printer_id}"],
            manufacturer="Bambu Lab" if printer_type == "bambu_lab" else "Prusa Research",
            model="A1" if printer_type == "bambu_lab" else "Core One",
            name=f"Printernizer {printer_name}",
            sw_version="1.0.0",
            configuration_url=f"http://{get_settings().api_host}:8000"
        )
        
        self.devices[printer_id] = device
        logger.info(f"Registered printer device: {printer_name} ({printer_type})")
        
        return device
        
    async def create_printer_entities(self, printer_id: str, printer_name: str, printer_type: str):
        """Create all MQTT discovery entities for a printer"""
        
        if not self.connected or printer_id not in self.devices:
            logger.warning(f"Cannot create entities for {printer_id}: not connected or device not registered")
            return
            
        device = self.devices[printer_id]
        
        # Printer status sensor
        await self._create_sensor_entity(
            printer_id, "status", "Status",
            device=device,
            icon="mdi:printer-3d",
            entity_category="diagnostic"
        )
        
        # Job progress sensor
        await self._create_sensor_entity(
            printer_id, "progress", "Progress", 
            device=device,
            device_class=DeviceClass.PERCENTAGE.value,
            unit_of_measurement="%",
            icon="mdi:progress-check"
        )
        
        # Current job name
        await self._create_sensor_entity(
            printer_id, "current_job", "Current Job",
            device=device,
            icon="mdi:file-document"
        )
        
        # Bed temperature (if supported)
        if printer_type in ["bambu_lab", "prusa"]:
            await self._create_sensor_entity(
                printer_id, "bed_temp", "Bed Temperature",
                device=device,
                device_class=DeviceClass.TEMPERATURE.value,
                unit_of_measurement="°C",
                icon="mdi:thermometer"
            )
            
        # Nozzle temperature (if supported) 
        if printer_type in ["bambu_lab", "prusa"]:
            await self._create_sensor_entity(
                printer_id, "nozzle_temp", "Nozzle Temperature",
                device=device,
                device_class=DeviceClass.TEMPERATURE.value,
                unit_of_measurement="°C", 
                icon="mdi:thermometer-high"
            )
            
        # Print time remaining
        await self._create_sensor_entity(
            printer_id, "time_remaining", "Time Remaining",
            device=device,
            device_class=DeviceClass.DURATION.value,
            unit_of_measurement="min",
            icon="mdi:clock-outline"
        )
        
        # Material used
        await self._create_sensor_entity(
            printer_id, "material_used", "Material Used",
            device=device,
            unit_of_measurement="g",
            icon="mdi:scale"
        )
        
        # Print cost (German business feature)
        await self._create_sensor_entity(
            printer_id, "print_cost", "Print Cost",
            device=device,
            unit_of_measurement="EUR",
            icon="mdi:currency-eur",
            entity_category="diagnostic"
        )
        
        # Last job completion
        await self._create_sensor_entity(
            printer_id, "last_job", "Last Job Completion",
            device=device,
            device_class=DeviceClass.TIMESTAMP.value,
            icon="mdi:clock-check"
        )
        
        logger.info(f"Created Home Assistant entities for printer: {printer_name}")
        
    async def _create_sensor_entity(self, printer_id: str, entity_id: str, entity_name: str,
                                   device: HADevice, **kwargs):
        """Create a sensor entity with MQTT discovery"""
        
        unique_id = f"printernizer_{printer_id}_{entity_id}"
        state_topic = f"{self.state_prefix}/{printer_id}/{entity_id}"
        availability_topic = f"{self.state_prefix}/{printer_id}/availability"
        
        config = HAEntityConfig(
            name=entity_name,
            unique_id=unique_id,
            state_topic=state_topic,
            device=device,
            availability_topic=availability_topic,
            **kwargs
        )
        
        # Create discovery topic
        discovery_topic = f"{self.discovery_prefix}/sensor/{unique_id}/config"
        
        # Convert config to dict for JSON serialization
        config_dict = asdict(config)
        config_dict["device"] = asdict(device)
        
        # Remove None values
        config_dict = {k: v for k, v in config_dict.items() if v is not None}
        config_dict["device"] = {k: v for k, v in config_dict["device"].items() if v is not None}
        
        # Publish discovery configuration
        await self._publish(discovery_topic, json.dumps(config_dict), retain=True)
        
        # Store entity config
        self.entities[unique_id] = config
        
        logger.debug(f"Created sensor entity: {entity_name} ({unique_id})")
        
    async def update_printer_state(self, printer_id: str, status_data: Dict[str, Any]):
        """Update printer state in Home Assistant"""
        
        if not self.connected:
            return
            
        # Update individual entity states
        entities_map = {
            "status": status_data.get("status", "unknown"),
            "progress": status_data.get("progress", 0),
            "current_job": status_data.get("job_name", "None"),
            "bed_temp": status_data.get("bed_temperature"),
            "nozzle_temp": status_data.get("nozzle_temperature"),
            "time_remaining": status_data.get("time_remaining"),
            "material_used": status_data.get("material_used"),
            "print_cost": status_data.get("cost_eur"),
            "last_job": status_data.get("last_job_completion")
        }
        
        # Publish states
        for entity_id, value in entities_map.items():
            if value is not None:
                topic = f"{self.state_prefix}/{printer_id}/{entity_id}"
                await self._publish(topic, str(value))
                
        # Update availability
        availability_topic = f"{self.state_prefix}/{printer_id}/availability"
        availability = "online" if status_data.get("connected", False) else "offline"
        await self._publish(availability_topic, availability, retain=True)
        
    async def update_job_state(self, printer_id: str, job_data: Dict[str, Any]):
        """Update job-specific state in Home Assistant"""
        
        if not self.connected:
            return
            
        # Update job-related entities
        job_entities = {
            "current_job": job_data.get("name", "None"),
            "progress": job_data.get("progress", 0),
            "time_remaining": job_data.get("time_remaining"),
            "material_used": job_data.get("material_used", 0),
            "print_cost": job_data.get("cost_calculation", {}).get("total_eur", 0)
        }
        
        for entity_id, value in job_entities.items():
            if value is not None:
                topic = f"{self.state_prefix}/{printer_id}/{entity_id}"
                await self._publish(topic, str(value))
                
    async def remove_printer(self, printer_id: str):
        """Remove a printer and all its entities from Home Assistant"""
        
        if not self.connected:
            return
            
        # Remove all entities for this printer
        entities_to_remove = [
            entity_id for entity_id in self.entities.keys() 
            if entity_id.startswith(f"printernizer_{printer_id}_")
        ]
        
        for entity_id in entities_to_remove:
            discovery_topic = f"{self.discovery_prefix}/sensor/{entity_id}/config"
            await self._publish(discovery_topic, "", retain=True)  # Empty payload removes entity
            del self.entities[entity_id]
            
        # Remove device
        if printer_id in self.devices:
            del self.devices[printer_id]
            
        logger.info(f"Removed printer {printer_id} from Home Assistant")
        
    async def _publish(self, topic: str, payload: str, retain: bool = False):
        """Publish MQTT message"""
        
        if not self.client or not self.connected:
            logger.warning(f"Cannot publish to {topic}: not connected")
            return
            
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.publish,
                topic,
                payload,
                1,  # QoS
                retain
            )
            logger.debug(f"Published to {topic}: {payload}")
            
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            

# Global Home Assistant MQTT instance
_ha_mqtt: Optional[HomeAssistantMQTT] = None


async def get_homeassistant_mqtt() -> Optional[HomeAssistantMQTT]:
    """Get the global Home Assistant MQTT instance"""
    global _ha_mqtt
    
    # Check if running in Home Assistant addon environment
    settings = get_settings()
    if not hasattr(settings, 'mqtt_host') or not settings.mqtt_host:
        return None
        
    if _ha_mqtt is None:
        _ha_mqtt = HomeAssistantMQTT(
            mqtt_host=settings.mqtt_host,
            mqtt_port=getattr(settings, 'mqtt_port', 1883),
            mqtt_username=getattr(settings, 'mqtt_username', None),
            mqtt_password=getattr(settings, 'mqtt_password', None)
        )
        
        # Connect on first access
        await _ha_mqtt.connect()
        
    return _ha_mqtt


async def initialize_homeassistant_integration():
    """Initialize Home Assistant integration if available"""
    
    ha_mqtt = await get_homeassistant_mqtt()
    if ha_mqtt:
        logger.info("Home Assistant MQTT integration initialized")
        return ha_mqtt
    else:
        logger.info("Home Assistant MQTT integration not available")
        return None