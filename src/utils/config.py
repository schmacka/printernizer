"""
Configuration utilities and settings for Printernizer.
Handles environment variables, settings validation, and Home Assistant integration.
"""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class PrinternizerSettings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database Configuration
    database_path: str = Field(default="/app/data/printernizer.db", env="DATABASE_PATH")
    
    # Server Configuration  
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    environment: str = Field(default="production", env="ENVIRONMENT")
    
    # Logging
    log_level: str = Field(default="info", env="LOG_LEVEL")
    
    # CORS
    cors_origins: str = Field(default="", env="CORS_ORIGINS")
    
    # Printer Settings
    printer_polling_interval: int = Field(default=30, env="PRINTER_POLLING_INTERVAL")
    max_concurrent_downloads: int = Field(default=5, env="MAX_CONCURRENT_DOWNLOADS")
    
    # WebSocket Configuration
    enable_websockets: bool = Field(default=True, env="ENABLE_WEBSOCKETS")
    
    # German Business Features
    enable_german_compliance: bool = Field(default=True, env="ENABLE_GERMAN_COMPLIANCE")
    vat_rate: float = Field(default=19.0, env="VAT_RATE")
    currency: str = Field(default="EUR", env="CURRENCY")
    timezone: str = Field(default="Europe/Berlin", env="TZ")
    
    # Home Assistant MQTT Integration
    mqtt_host: Optional[str] = Field(default=None, env="MQTT_HOST")
    mqtt_port: int = Field(default=1883, env="MQTT_PORT")
    mqtt_username: Optional[str] = Field(default=None, env="MQTT_USERNAME")
    mqtt_password: Optional[str] = Field(default=None, env="MQTT_PASSWORD")
    mqtt_discovery_prefix: str = Field(default="homeassistant", env="MQTT_DISCOVERY_PREFIX")
    
    # Redis Configuration (optional)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # Security
    secret_key: str = Field(default="your-super-secret-key-change-in-production", env="SECRET_KEY")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def is_homeassistant_addon(self) -> bool:
        """Check if running as Home Assistant addon."""
        return self.environment == "homeassistant" or os.path.exists("/run/s6/services")
    
    @property  
    def mqtt_available(self) -> bool:
        """Check if MQTT configuration is available."""
        return self.mqtt_host is not None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
_settings: Optional[PrinternizerSettings] = None


def get_settings() -> PrinternizerSettings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = PrinternizerSettings()
    return _settings


def reload_settings() -> PrinternizerSettings:
    """Reload settings from environment."""
    global _settings
    _settings = PrinternizerSettings()
    return _settings