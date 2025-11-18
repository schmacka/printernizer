"""
Configuration service for Printernizer.
Manages printer configurations, API keys, and system settings.
"""
from typing import Dict, Any, Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path
import json
import os
from dataclasses import dataclass
from datetime import datetime
import structlog
from src.utils.config import get_settings
from src.services.watch_folder_db_service import WatchFolderDbService
from src.models.watch_folder import WatchFolder, WatchFolderSource

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
        
    def _validate_config(self) -> None:
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
        """
        Convert PrinterConfig to dictionary.

        WARNING: This includes sensitive fields (api_key, access_code).
        For logging/debugging, use to_dict_safe() instead.
        """
        return {
            "name": self.name,
            "type": self.type,
            "ip_address": self.ip_address,
            "api_key": self.api_key,
            "access_code": self.access_code,
            "serial_number": self.serial_number,
            "is_active": self.is_active
        }

    def to_dict_safe(self) -> Dict[str, Any]:
        """
        Convert PrinterConfig to dictionary with sensitive fields masked.
        Use this method for logging and debugging.
        """
        from src.utils.logging_config import mask_sensitive_data
        return mask_sensitive_data(self.to_dict())


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    database_path: str = "./data/printernizer.db"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    environment: str = "production"
    
    # CORS - Configure allowed origins (will be parsed from comma-separated string)
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://192.168.176.159:3000"
    
    # Logging
    log_level: str = "INFO"
    
    # German Business Settings
    timezone: str = "Europe/Berlin"
    currency: str = "EUR"
    vat_rate: float = 0.19  # German VAT rate
    
    # File Management
    downloads_path: str = "./data/downloads"
    max_file_size: int = 500 * 1024 * 1024  # 500MB limit

    # Library System Configuration
    library_enabled: bool = True
    library_path: str = "/app/data/library"
    library_auto_organize: bool = True
    library_auto_extract_metadata: bool = True
    library_auto_deduplicate: bool = True
    library_preserve_originals: bool = True
    library_checksum_algorithm: str = "sha256"

    # Monitoring
    monitoring_interval: int = 30  # seconds
    connection_timeout: int = 10  # seconds

    # Job Creation
    job_creation_auto_create: bool = True  # Auto-create jobs when prints start

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # -------------------------------------------------
    # Validators / Normalizers
    # -------------------------------------------------
    @field_validator("downloads_path")
    @classmethod
    def normalize_downloads_path(cls, v: str) -> str:
        """Normalize the downloads path to avoid hidden control characters and ensure portability.

        Handles accidental escape sequences coming from .env parsing (e.g. C:\\temp becomes C:<TAB>emp
        when written as "C:\temp"), converts backslashes to forward slashes (Windows-compatible and
        safer for URL/display), removes control chars, collapses duplicate slashes and resolves to an
        absolute path when possible.
        """
        if not v:
            return v
        original = v
        # Remove control characters (tabs, newlines, carriage returns)
        control_chars = ['\t', '\n', '\r']
        if any(c in v for c in ['\t', '\n', '\r']):
            v = v.replace('\t', '').replace('\n', '').replace('\r', '')
        # Uniform slashes
        v = v.replace('\\', '/')
        # Collapse duplicate slashes (preserve drive designator like C:/)
        while '//' in v.replace('://', '§§'):  # temporary substitution to avoid touching URL schemes
            v = v.replace('://', '§§').replace('//', '/').replace('§§', '://')
        # Resolve to absolute path if local filesystem path
        try:
            # Only resolve if it looks like a local path, not a URL
            if not (v.startswith('http://') or v.startswith('https://')):
                v = str(Path(v).expanduser().resolve())
        except (OSError, ValueError, RuntimeError) as e:
            # Best-effort; keep the normalized (non-resolved) path if resolution fails
            logger.debug("Could not resolve downloads_path, using as-is",
                        path=v, error=str(e))
        if v != original:
            # Log at info level so user can see the normalization (structlog fields are structured)
            logger.info("Normalized downloads_path", original=original, normalized=v)
        return v

    @field_validator("library_path")
    @classmethod
    def normalize_library_path(cls, v: str) -> str:
        """Normalize the library path to avoid hidden control characters and ensure portability."""
        if not v:
            return v
        original = v
        # Remove control characters
        if any(c in v for c in ['\t', '\n', '\r']):
            v = v.replace('\t', '').replace('\n', '').replace('\r', '')
        # Uniform slashes
        v = v.replace('\\', '/')
        # Collapse duplicate slashes
        while '//' in v.replace('://', '§§'):
            v = v.replace('://', '§§').replace('//', '/').replace('§§', '://')
        # Resolve to absolute path
        try:
            if not (v.startswith('http://') or v.startswith('https://')):
                v = str(Path(v).expanduser().resolve())
        except (OSError, ValueError, RuntimeError) as e:
            # Best-effort; keep the normalized (non-resolved) path if resolution fails
            logger.debug("Could not resolve library_path, using as-is",
                        path=v, error=str(e))
        if v != original:
            logger.info("Normalized library_path", original=original, normalized=v)
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # Allow extra fields from .env to be ignored
    }


class ConfigService:
    """Configuration service for managing printer and system settings."""

    def __init__(self, config_path: Optional[str] = None, database = None):
        """Initialize configuration service."""
        self.settings = Settings()
        self.watch_folder_db = WatchFolderDbService(database)
        self._migrated_env_folders = False

        if config_path is None:
            # Check for environment variable for config path (used in HA addon for persistence)
            env_config_path = os.environ.get('PRINTER_CONFIG_PATH')
            if env_config_path:
                config_path = Path(env_config_path)
            else:
                # Default to data directory for persistence, fallback to config if not exists
                data_config_path = Path("/data/printernizer/printers.json")
                legacy_config_path = Path(__file__).parent.parent.parent / "config" / "printers.json"

                # Use data path if in HA environment, otherwise use legacy path
                if os.path.exists("/data"):
                    config_path = data_config_path
                else:
                    config_path = legacy_config_path

        self.config_path = Path(config_path)
        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._printers: Dict[str, PrinterConfig] = {}
        self._load_printer_configs()
        
    def _load_printer_configs(self) -> None:
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
            
    def _load_from_environment(self) -> None:
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
                try:
                    # Use copy() instead of copy2() to avoid permission errors on mounted volumes
                    # copy2() tries to preserve metadata which fails on Windows-mounted volumes
                    shutil.copy(self.config_path, backup_path)
                except (PermissionError, OSError) as backup_error:
                    logger.warning("Could not create config backup, continuing with save", error=str(backup_error))
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            logger.info("Saved printer configuration", path=str(self.config_path))
        except Exception as e:
            logger.error("Failed to save printer config", error=str(e))
            raise  # Re-raise so caller knows save failed
            
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
    
    async def get_watch_folders(self) -> List[str]:
        """Get list of configured watch folders from database."""
        await self._ensure_env_migration()
        return await self.watch_folder_db.get_active_folder_paths()
    
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

    def validate_downloads_path(self, folder_path: str) -> Dict[str, Any]:
        """Validate the downloads path - check if it's available, writable, and deletable."""
        import tempfile

        try:
            path = Path(folder_path)

            # Check if path exists, if not try to create it
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info("Created downloads directory", path=str(path))
                except Exception as e:
                    return {"valid": False, "error": f"Cannot create directory: {str(e)}"}

            # Check if it's a directory
            if not path.is_dir():
                return {"valid": False, "error": "Path is not a directory"}

            # Check if it's readable
            if not os.access(path, os.R_OK):
                return {"valid": False, "error": "Directory is not readable"}

            # Check if it's writable
            if not os.access(path, os.W_OK):
                return {"valid": False, "error": "Directory is not writable"}

            # Test actual write and delete operations
            try:
                # Create a temporary test file
                test_file = path / f".printernizer_test_{os.getpid()}.tmp"
                test_file.write_text("test")

                # Try to delete it
                test_file.unlink()

                logger.info("Downloads path validation successful", path=str(path))
                return {"valid": True, "message": "Download path is valid and writable"}

            except Exception as e:
                return {"valid": False, "error": f"Cannot write or delete files: {str(e)}"}

        except Exception as e:
            logger.error("Error validating downloads path", path=folder_path, error=str(e))
            return {"valid": False, "error": f"Invalid path: {str(e)}"}

    def validate_library_path(self, folder_path: str) -> Dict[str, Any]:
        """Validate the library path - check if it's available, writable, and deletable."""
        import tempfile

        try:
            path = Path(folder_path)

            # Check if path exists, if not try to create it
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info("Created library directory", path=str(path))
                except Exception as e:
                    return {"valid": False, "error": f"Cannot create directory: {str(e)}"}

            # Check if it's a directory
            if not path.is_dir():
                return {"valid": False, "error": "Path is not a directory"}

            # Check if it's readable
            if not os.access(path, os.R_OK):
                return {"valid": False, "error": "Directory is not readable"}

            # Check if it's writable
            if not os.access(path, os.W_OK):
                return {"valid": False, "error": "Directory is not writable"}

            # Test actual write and delete operations
            try:
                # Create a temporary test file
                test_file = path / f".printernizer_test_{os.getpid()}.tmp"
                test_file.write_text("test")

                # Try to delete it
                test_file.unlink()

                logger.info("Library path validation successful", path=str(path))
                return {"valid": True, "message": "Library path is valid and writable"}

            except Exception as e:
                return {"valid": False, "error": f"Cannot write or delete files: {str(e)}"}

        except Exception as e:
            logger.error("Error validating library path", path=folder_path, error=str(e))
            return {"valid": False, "error": f"Invalid path: {str(e)}"}

    async def get_watch_folder_settings(self) -> Dict[str, Any]:
        """Get all watch folder related settings."""
        await self._ensure_env_migration()
        settings = get_settings()
        watch_folders = await self.watch_folder_db.get_all_watch_folders(active_only=True)
        
        return {
            "watch_folders": [wf.folder_path for wf in watch_folders],
            "enabled": settings.watch_folders_enabled,
            "recursive": settings.watch_recursive,
            "supported_extensions": ['.stl', '.3mf', '.gcode', '.obj', '.ply']
        }

    def get_application_settings(self) -> Dict[str, Any]:
        """Get all application settings."""
        settings = get_settings()
        return {
            "database_path": str(settings.database_path),
            "host": settings.api_host,
            "port": settings.api_port,
            "debug": getattr(settings, 'debug', False),
            "environment": settings.environment,
            "log_level": settings.log_level,
            "timezone": settings.timezone,
            "currency": settings.currency,
            "vat_rate": settings.vat_rate,
            "downloads_path": str(settings.downloads_path),
            "max_file_size": settings.max_file_size,
            "monitoring_interval": settings.printer_polling_interval,
            "connection_timeout": settings.connection_timeout,
            "cors_origins": self._get_cors_origins_list(settings.cors_origins),
            # Job creation settings
            "job_creation_auto_create": settings.job_creation_auto_create,
            # G-code optimization settings
            "gcode_optimize_print_only": settings.gcode_optimize_print_only,
            "gcode_optimization_max_lines": settings.gcode_optimization_max_lines,
            "gcode_render_max_lines": settings.gcode_render_max_lines,
            # Upload settings
            "enable_upload": settings.enable_upload,
            "max_upload_size_mb": settings.max_upload_size_mb,
            "allowed_upload_extensions": settings.allowed_upload_extensions,
            # Library System settings
            "library_enabled": settings.library_enabled,
            "library_path": str(settings.library_path),
            "library_auto_organize": settings.library_auto_organize,
            "library_auto_extract_metadata": settings.library_auto_extract_metadata,
            "library_auto_deduplicate": getattr(settings, 'library_auto_deduplicate', True),
            "library_preserve_originals": settings.library_preserve_originals,
            "library_checksum_algorithm": settings.library_checksum_algorithm,
            "library_processing_workers": settings.library_processing_workers,
            "library_search_enabled": settings.library_search_enabled,
            "library_search_min_length": settings.library_search_min_length,
            # Timelapse settings
            "timelapse_enabled": settings.timelapse_enabled,
            "timelapse_source_folder": str(settings.timelapse_source_folder),
            "timelapse_output_folder": str(settings.timelapse_output_folder),
            "timelapse_output_strategy": settings.timelapse_output_strategy,
            "timelapse_auto_process_timeout": settings.timelapse_auto_process_timeout,
            "timelapse_cleanup_age_days": settings.timelapse_cleanup_age_days
        }

    def _get_cors_origins_list(self, cors_origins_str: str) -> List[str]:
        """Convert CORS origins string to list."""
        if not cors_origins_str:
            return []
        return [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]

    def update_application_settings(self, settings_dict: Dict[str, Any]) -> bool:
        """Update runtime-modifiable application settings."""
        logger.info("update_application_settings called", settings_dict=settings_dict)
        updated_fields = []
        settings = get_settings()
        logger.info("Got settings object", settings_type=type(settings).__name__)

        # List of settings that can be updated at runtime
        updatable_settings = {
            "log_level", "monitoring_interval", "connection_timeout",
            "max_file_size", "vat_rate", "downloads_path",
            # Job creation settings
            "job_creation_auto_create",
            # G-code optimization settings
            "gcode_optimize_print_only", "gcode_optimization_max_lines", "gcode_render_max_lines",
            # Upload settings
            "enable_upload", "max_upload_size_mb", "allowed_upload_extensions",
            # Library settings
            "library_enabled", "library_path", "library_auto_organize",
            "library_auto_extract_metadata", "library_auto_deduplicate",
            "library_preserve_originals", "library_checksum_algorithm",
            "library_processing_workers", "library_search_enabled", "library_search_min_length",
            # Timelapse settings
            "timelapse_enabled", "timelapse_source_folder", "timelapse_output_folder",
            "timelapse_output_strategy", "timelapse_auto_process_timeout", "timelapse_cleanup_age_days"
        }

        logger.info("Processing settings update", settings_dict=settings_dict, updatable_settings=updatable_settings)

        for key, value in settings_dict.items():
            logger.info("Processing setting", key=key, value=value)
            if key in updatable_settings:
                logger.info("Setting is updatable", key=key)
                if hasattr(settings, key):
                    old_value = getattr(settings, key)
                    logger.info("Updating setting", key=key, old_value=old_value, new_value=value)
                    # Update in memory
                    setattr(settings, key, value)
                    updated_fields.append(key)
                    logger.info("Updated application setting", key=key, old_value=old_value, new_value=value)
                else:
                    logger.warning("Settings object does not have attribute", key=key)
            else:
                logger.warning("Setting is not updatable", key=key)

        # Persist changes to .env file if any updates were made
        if updated_fields:
            logger.info("Persisting settings to .env file", updated_fields=updated_fields)
            try:
                self._persist_settings_to_env(settings_dict)
                logger.info("Successfully persisted settings to .env file")
            except Exception as e:
                logger.error("Failed to persist settings to .env file", error=str(e))
                # Still return True since in-memory update succeeded

        return len(updated_fields) > 0

    def _persist_settings_to_env(self, settings_dict: Dict[str, Any]) -> None:
        """Persist settings to .env file."""
        import os
        from pathlib import Path

        # Path to .env file
        env_file_path = Path(__file__).parent.parent.parent / ".env"

        # Read existing .env file content
        existing_env = {}
        if env_file_path.exists():
            with open(env_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_env[key.strip()] = value.strip()

        # Map settings keys to environment variable names
        env_key_mapping = {
            "log_level": "LOG_LEVEL",
            "monitoring_interval": "MONITORING_INTERVAL",
            "connection_timeout": "CONNECTION_TIMEOUT",
            "max_file_size": "MAX_FILE_SIZE",
            "vat_rate": "VAT_RATE",
            "downloads_path": "DOWNLOADS_PATH",
            "library_enabled": "LIBRARY_ENABLED",
            "library_path": "LIBRARY_PATH",
            "library_auto_organize": "LIBRARY_AUTO_ORGANIZE",
            "library_auto_extract_metadata": "LIBRARY_AUTO_EXTRACT_METADATA",
            "library_auto_deduplicate": "LIBRARY_AUTO_DEDUPLICATE"
        }

        # Update environment variables
        for key, value in settings_dict.items():
            if key in env_key_mapping:
                env_key = env_key_mapping[key]
                # Format value appropriately
                if isinstance(value, bool):
                    existing_env[env_key] = str(value).lower()
                elif isinstance(value, str):
                    existing_env[env_key] = f'"{value}"'
                else:
                    existing_env[env_key] = str(value)
                logger.info("Updated env variable", env_key=env_key, value=value)

        # Write back to .env file
        with open(env_file_path, 'w', encoding='utf-8') as f:
            for key, value in existing_env.items():
                f.write(f"{key}={value}\n")

        logger.info("Persisted settings to .env file", env_file=str(env_file_path))

    async def add_watch_folder(self, folder_path: str) -> bool:
        """Add a watch folder to the database configuration."""
        try:
            await self._ensure_env_migration()
            
            # Check if folder already exists
            existing = await self.watch_folder_db.get_watch_folder_by_path(folder_path)
            if existing:
                logger.warning("Watch folder already exists", folder_path=folder_path)
                return False
            
            # Validate the folder
            validation = self.validate_watch_folder(folder_path)
            if not validation["valid"]:
                logger.error("Cannot add invalid watch folder", 
                           folder_path=folder_path, error=validation["error"])
                return False
            
            # Create watch folder record
            watch_folder = WatchFolder(
                folder_path=folder_path,
                folder_name=Path(folder_path).name,
                source=WatchFolderSource.MANUAL
            )
            
            # Save to database
            folder_id = await self.watch_folder_db.create_watch_folder(watch_folder)
            logger.info("Added watch folder to database", folder_path=folder_path, folder_id=folder_id)
            return True
            
        except Exception as e:
            logger.error("Failed to add watch folder", folder_path=folder_path, error=str(e))
            return False
    
    async def remove_watch_folder(self, folder_path: str) -> bool:
        """Remove a watch folder from the database configuration."""
        try:
            await self._ensure_env_migration()
            
            # Check if folder exists in database
            existing = await self.watch_folder_db.get_watch_folder_by_path(folder_path)
            if not existing:
                logger.warning("Watch folder not found for removal", folder_path=folder_path)
                return False
            
            # Remove from database
            deleted = await self.watch_folder_db.delete_watch_folder_by_path(folder_path)
            if deleted:
                logger.info("Removed watch folder from database", folder_path=folder_path)
            
            return deleted
            
        except Exception as e:
            logger.error("Failed to remove watch folder", folder_path=folder_path, error=str(e))
            return False
    
    async def _ensure_env_migration(self):
        """Ensure environment variables are migrated to database on first use."""
        if self._migrated_env_folders:
            return
        
        try:
            settings = get_settings()
            env_folders = settings.watch_folders_list
            
            if env_folders:
                migrated = await self.watch_folder_db.migrate_env_folders(env_folders)
                logger.info("Migrated environment watch folders", 
                          env_folders=len(env_folders), migrated=migrated)
            
            self._migrated_env_folders = True
            
        except Exception as e:
            logger.error("Failed to migrate environment watch folders", error=str(e))