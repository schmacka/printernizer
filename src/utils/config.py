"""
Configuration utilities and settings for Printernizer.
Handles environment variables, settings validation, and Home Assistant integration.
"""

import os
import secrets
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import structlog

logger = structlog.get_logger()


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

    # File Management
    downloads_path: str = Field(default="downloads", env="DOWNLOADS_PATH")
    max_file_size: int = Field(default=100, env="MAX_FILE_SIZE")
    monitoring_interval: int = Field(default=30, env="MONITORING_INTERVAL")
    connection_timeout: int = Field(default=30, env="CONNECTION_TIMEOUT")
    
    # Watch Folders Settings
    watch_folders: str = Field(default="", env="WATCH_FOLDERS")
    watch_folders_enabled: bool = Field(default=True, env="WATCH_FOLDERS_ENABLED")
    watch_recursive: bool = Field(default=True, env="WATCH_RECURSIVE")
    
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
    secret_key: str = Field(default="", env="SECRET_KEY")
    
    # G-code Preview Optimization
    gcode_optimize_print_only: bool = Field(default=True, env="GCODE_OPTIMIZE_PRINT_ONLY")
    gcode_optimization_max_lines: int = Field(default=1000, env="GCODE_OPTIMIZATION_MAX_LINES")
    gcode_render_max_lines: int = Field(default=10000, env="GCODE_RENDER_MAX_LINES")
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Validate and generate secure secret key if needed."""
        # If no secret key provided (empty or default), generate one
        if not v or v == "your-super-secret-key-change-in-production":
            generated_key = secrets.token_urlsafe(32)
            logger.warning("No SECRET_KEY environment variable set. Generated secure key for this session.")
            logger.info("For production, set SECRET_KEY environment variable to persist sessions across restarts.")
            return generated_key
        
        # Validate provided key
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long for security. Set a longer SECRET_KEY environment variable.")
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def watch_folders_list(self) -> List[str]:
        """Get watch folders as list."""
        if not self.watch_folders:
            return []
        return [folder.strip() for folder in self.watch_folders.split(",") if folder.strip()]
    
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