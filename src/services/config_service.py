"""
Configuration service for Printernizer.
Manages printer configurations, API keys, and system settings.
"""
from typing import Dict, Any, Optional, List
from pydantic_settings import BaseSettings
from pathlib import Path
import json
import os
from dataclasses import dataclass
from datetime import datetime
import structlog
from utils.config import get_settings

logger = structlog.get_logger()


@dataclass
class PrinterConfig:
    """Configuration for a single printer with validation."""
    printer_id: str
    name: str
    type: str
    ip_address: Optional[str] = None
    api_key: Optional[str] = None
    access_code: Optional[str] = None
    serial_number: Optional[str] = None
    is_active: bool = True
    
    def __post_init__(self):
        """Validate printer configuration after initialization."""
        self._validate_config()
        
    def _validate_config(self):
        """Validate printer configuration based on type."""
        if self.type == "bambu_lab":
            if not self.ip_address or not self.access_code:
                raise ValueError(f"Bambu Lab printer {self.printer_id} requires ip_address and access_code")
        elif self.type == "prusa_core":
            if not self.ip_address or not self.api_key:
                raise ValueError(f"Prusa Core printer {self.printer_id} requires ip_address and api_key")
        elif self.type not in ["bambu_lab", "prusa_core"]:
            logger.warning("Unknown printer type", printer_id=self.printer_id, type=self.type)
    
    @classmethod
    def from_dict(cls, printer_id: str, config: Dict[str, Any]) -> 'PrinterConfig':
        """Create PrinterConfig from dictionary."""
        return cls(
            printer_id=printer_id,
            name=config.get('name', printer_id),
            type=config.get('type', 'unknown'),
            ip_address=config.get('ip_address'),
            api_key=config.get('api_key'),
            access_code=config.get('access_code'),
            serial_number=config.get('serial_number'),
            is_active=config.get('is_active', True)
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert PrinterConfig to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "ip_address": self.ip_address,
            "api_key": self.api_key,
            "access_code": self.access_code,
            "serial_number": self.serial_number,
            "is_active": self.is_active
        }


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    database_path: str = "./data/printernizer.db"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    environment: str = "production"
    
    # CORS - Enhanced for Porcus3D (will be parsed from comma-separated string)
    cors_origins: str = "https://porcus3d.de,https://www.porcus3d.de,http://localhost:3000"
    
    # Logging
    log_level: str = "INFO"
    
    # German Business Settings
    timezone: str = "Europe/Berlin"
    currency: str = "EUR"
    vat_rate: float = 0.19  # German VAT rate
    
    # File Management
    downloads_path: str = "./data/downloads"
    max_file_size: int = 500 * 1024 * 1024  # 500MB limit
    
    # Monitoring
    monitoring_interval: int = 30  # seconds
    connection_timeout: int = 10  # seconds
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # Allow extra fields from .env to be ignored
    }


class ConfigService:
    """Configuration service for managing printer and system settings."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration service."""
        self.settings = Settings()
        
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "printers.json"
        
        self.config_path = Path(config_path)
        self._printers: Dict[str, PrinterConfig] = {}
        self._load_printer_configs()
        
    def _load_printer_configs(self):
        """Load printer configurations from file and environment variables."""
        # First, try to load from environment variables
        self._load_from_environment()
        
        # Then, try to load from config file (will override environment)
        if not self.config_path.exists():
            logger.warning("Printer config file not found, creating default", path=str(self.config_path))
            self._create_default_config()
            return
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Validate and load printer configurations
            for printer_id, config in config_data.get('printers', {}).items():
                try:
                    self._printers[printer_id] = PrinterConfig.from_dict(printer_id, config)
                except ValueError as e:
                    logger.error("Invalid printer configuration", printer_id=printer_id, error=str(e))
                    continue
                
            logger.info("Loaded printer configurations", count=len(self._printers))
            
        except Exception as e:
            logger.error("Failed to load printer config", error=str(e), path=str(self.config_path))
            self._create_default_config()
            
    def _load_from_environment(self):
        """Load printer configurations from environment variables."""
        # Environment variable format: PRINTERNIZER_PRINTER_{ID}_{FIELD}
        # Example: PRINTERNIZER_PRINTER_BAMBU_A1_01_IP_ADDRESS=192.168.1.100
        
        printer_configs = {}
        
        for key, value in os.environ.items():
            if key.startswith('PRINTERNIZER_PRINTER_'):
                parts = key.split('_')
                if len(parts) >= 4:
                    # Extract printer ID and field name
                    printer_id = '_'.join(parts[2:-1])  # Handle multi-part IDs
                    field_name = parts[-1].lower()
                    
                    if printer_id not in printer_configs:
                        printer_configs[printer_id] = {}
                    
                    # Convert field names to match expected format
                    if field_name == 'ip' and len(parts) > 4 and parts[-2] == 'ADDRESS':
                        field_name = 'ip_address'
                    elif field_name == 'api' and len(parts) > 4 and parts[-2] == 'KEY':
                        field_name = 'api_key'
                    elif field_name == 'access' and len(parts) > 4 and parts[-2] == 'CODE':
                        field_name = 'access_code'
                    elif field_name == 'serial' and len(parts) > 4 and parts[-2] == 'NUMBER':
                        field_name = 'serial_number'
                    elif field_name == 'active':
                        field_name = 'is_active'
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    
                    printer_configs[printer_id][field_name] = value
        
        # Create PrinterConfig objects from environment data
        for printer_id, config in printer_configs.items():
            try:
                self._printers[printer_id] = PrinterConfig.from_dict(printer_id, config)
                logger.info("Loaded printer from environment", printer_id=printer_id)
            except ValueError as e:
                logger.error("Invalid printer configuration from environment", 
                           printer_id=printer_id, error=str(e))
            
    def _create_default_config(self):
        """Create default configuration file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "printers": {
                "bambu_a1_01": {
                    "name": "Bambu Lab A1 #01",
                    "type": "bambu_lab",
                    "ip_address": "192.168.1.100",
                    "access_code": "12345678",
                    "serial_number": "01S00A3B0300123",
                    "is_active": True
                },
                "prusa_core_01": {
                    "name": "Prusa Core One #01", 
                    "type": "prusa_core",
                    "ip_address": "192.168.1.101",
                    "api_key": "your_prusa_api_key_here",
                    "is_active": True
                }
            }
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info("Created default printer configuration", path=str(self.config_path))
        except Exception as e:
            logger.error("Failed to create default config", error=str(e))
            
    def get_printers(self) -> Dict[str, PrinterConfig]:
        """Get all printer configurations."""
        return self._printers.copy()
        
    def get_printer(self, printer_id: str) -> Optional[PrinterConfig]:
        """Get specific printer configuration."""
        return self._printers.get(printer_id)
        
    def get_active_printers(self) -> Dict[str, PrinterConfig]:
        """Get only active printer configurations."""
        return {
            pid: config for pid, config in self._printers.items() 
            if config.is_active
        }
        
    def add_printer(self, printer_id: str, config: Dict[str, Any]) -> bool:
        """Add or update printer configuration with validation."""
        try:
            # Validate configuration before adding
            printer_config = PrinterConfig.from_dict(printer_id, config)
            self._printers[printer_id] = printer_config
            self._save_config()
            logger.info("Added/updated printer configuration", printer_id=printer_id)
            return True
        except ValueError as e:
            logger.error("Invalid printer configuration", printer_id=printer_id, error=str(e))
            return False
        except Exception as e:
            logger.error("Failed to add printer", printer_id=printer_id, error=str(e))
            return False
            
    def remove_printer(self, printer_id: str) -> bool:
        """Remove printer configuration."""
        if printer_id in self._printers:
            del self._printers[printer_id]
            self._save_config()
            logger.info("Removed printer configuration", printer_id=printer_id)
            return True
        return False
        
    def _save_config(self):
        """Save current configuration to file with proper encoding."""
        config_data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "printers": {
                pid: config.to_dict()
                for pid, config in self._printers.items()
            }
        }
        
        try:
            # Create backup of existing config
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix('.backup')
                import shutil
                shutil.copy2(self.config_path, backup_path)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            logger.info("Saved printer configuration", path=str(self.config_path))
        except Exception as e:
            logger.error("Failed to save printer config", error=str(e))
            
    def validate_printer_connection(self, printer_id: str) -> Dict[str, Any]:
        """Validate printer connection configuration."""
        config = self.get_printer(printer_id)
        if not config:
            return {"valid": False, "error": "Printer configuration not found"}
            
        try:
            config._validate_config()  # This will raise ValueError if invalid
            return {"valid": True, "message": "Configuration is valid"}
        except ValueError as e:
            return {"valid": False, "error": str(e)}
            
    def get_business_settings(self) -> Dict[str, Any]:
        """Get German business-specific settings."""
        return {
            "timezone": self.settings.timezone,
            "currency": self.settings.currency,
            "vat_rate": self.settings.vat_rate,
            "downloads_path": self.settings.downloads_path
        }
        
    def reload_config(self) -> bool:
        """Reload configuration from file and environment."""
        try:
            old_count = len(self._printers)
            self._printers.clear()
            self._load_printer_configs()
            
            logger.info("Reloaded printer configuration", 
                       old_count=old_count, new_count=len(self._printers))
            return True
        except Exception as e:
            logger.error("Failed to reload configuration", error=str(e))
            return False
    
    def get_watch_folders(self) -> List[str]:
        """Get list of configured watch folders."""
        settings = get_settings()
        return settings.watch_folders_list
    
    def is_watch_folders_enabled(self) -> bool:
        """Check if watch folders monitoring is enabled."""
        settings = get_settings()
        return settings.watch_folders_enabled
    
    def is_recursive_watching_enabled(self) -> bool:
        """Check if recursive folder watching is enabled."""
        settings = get_settings()
        return settings.watch_recursive
    
    def validate_watch_folder(self, folder_path: str) -> Dict[str, Any]:
        """Validate a watch folder path."""
        try:
            path = Path(folder_path)
            
            if not path.exists():
                return {"valid": False, "error": "Path does not exist"}
            
            if not path.is_dir():
                return {"valid": False, "error": "Path is not a directory"}
            
            if not os.access(path, os.R_OK):
                return {"valid": False, "error": "Directory is not readable"}
            
            return {"valid": True, "message": "Watch folder is valid"}
            
        except Exception as e:
            return {"valid": False, "error": f"Invalid path: {str(e)}"}
    
    def get_watch_folder_settings(self) -> Dict[str, Any]:
        """Get all watch folder related settings."""
        settings = get_settings()
        return {
            "watch_folders": settings.watch_folders_list,
            "enabled": settings.watch_folders_enabled,
            "recursive": settings.watch_recursive,
            "supported_extensions": ['.stl', '.3mf', '.gcode', '.obj', '.ply']
        }