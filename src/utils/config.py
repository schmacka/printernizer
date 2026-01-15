"""
Configuration utilities and settings for Printernizer.
Handles environment variables, settings validation, and Home Assistant integration.
"""

import os
import secrets
from typing import Optional, List
from pathlib import Path
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import structlog

logger = structlog.get_logger()


class PrinternizerSettings(BaseSettings):
    """
    Application settings with comprehensive validation.

    All settings are loaded from environment variables or .env file.
    This class provides validation to ensure configuration is correct on startup.

    Settings are categorized into:
    - Required: Must be set or have secure defaults (e.g., SECRET_KEY)
    - Optional: Can be omitted, will use sensible defaults
    - Validated: All values are checked for correctness (ranges, formats, paths)
    """

    # Database Configuration
    database_path: str = Field(
        default="/data/printernizer/printernizer.db",
        env="DATABASE_PATH",
        description="Path to SQLite database file. Parent directory must exist and be writable."
    )

    # Server Configuration
    api_host: str = Field(
        default="0.0.0.0",
        env="API_HOST",
        description="API server bind address. Use 0.0.0.0 for all interfaces or 127.0.0.1 for localhost only."
    )
    api_port: int = Field(
        default=8000,
        env="API_PORT",
        description="API server port. Must be between 1 and 65535.",
        ge=1,
        le=65535
    )
    environment: str = Field(
        default="production",
        env="ENVIRONMENT",
        description="Application environment: development, production, or homeassistant"
    )
    
    # Logging
    log_level: str = Field(
        default="info",
        env="LOG_LEVEL",
        description="Logging level: debug, info, warning, error, critical"
    )

    # CORS
    cors_origins: str = Field(
        default="",
        env="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins. Empty means no CORS restrictions."
    )

    # Printer Settings
    printer_polling_interval: int = Field(
        default=30,
        env="PRINTER_POLLING_INTERVAL",
        description="Interval in seconds between printer status polls. Must be at least 5 seconds.",
        ge=5,
        le=3600
    )
    max_concurrent_downloads: int = Field(
        default=5,
        env="MAX_CONCURRENT_DOWNLOADS",
        description="Maximum number of concurrent file downloads. Must be between 1 and 20.",
        ge=1,
        le=20
    )

    # Job Management
    job_creation_auto_create: bool = Field(
        default=True,
        env="JOB_CREATION_AUTO_CREATE",
        description="Automatically create jobs when print starts are detected."
    )

    # File Management
    downloads_path: str = Field(
        default="/data/printernizer/printer-files",
        env="DOWNLOADS_PATH",
        description="Directory path for downloaded files. Will be created if it doesn't exist."
    )
    max_file_size: int = Field(
        default=100,
        env="MAX_FILE_SIZE",
        description="Maximum file size in MB for downloads. Must be between 1 and 10000 MB.",
        ge=1,
        le=10000
    )
    monitoring_interval: int = Field(
        default=30,
        env="MONITORING_INTERVAL",
        description="Interval in seconds for file monitoring. Must be between 5 and 3600 seconds.",
        ge=5,
        le=3600
    )
    connection_timeout: int = Field(
        default=30,
        env="CONNECTION_TIMEOUT",
        description="Connection timeout in seconds for printer communication. Must be between 5 and 300 seconds.",
        ge=5,
        le=300
    )

    # File Upload Settings
    enable_upload: bool = Field(
        default=True,
        env="ENABLE_UPLOAD",
        description="Enable drag-and-drop file upload feature in the library."
    )
    max_upload_size_mb: int = Field(
        default=500,
        env="MAX_UPLOAD_SIZE_MB",
        description="Maximum file size in MB for uploads. Must be between 1 and 5000 MB.",
        ge=1,
        le=5000
    )
    allowed_upload_extensions: str = Field(
        default=".3mf,.stl,.gcode,.obj,.ply",
        env="ALLOWED_UPLOAD_EXTENSIONS",
        description="Comma-separated list of allowed file extensions for upload (with leading dot)."
    )

    # Watch Folders Settings
    watch_folders: str = Field(
        default="",
        env="WATCH_FOLDERS",
        description="Comma-separated list of folder paths to watch for new files. Leave empty to disable."
    )
    watch_folders_enabled: bool = Field(
        default=True,
        env="WATCH_FOLDERS_ENABLED",
        description="Enable or disable watch folder monitoring globally."
    )
    watch_recursive: bool = Field(
        default=True,
        env="WATCH_RECURSIVE",
        description="Enable recursive monitoring of subdirectories in watch folders."
    )

    # WebSocket Configuration
    enable_websockets: bool = Field(
        default=True,
        env="ENABLE_WEBSOCKETS",
        description="Enable WebSocket connections for real-time updates."
    )

    # German Business Features
    enable_german_compliance: bool = Field(
        default=True,
        env="ENABLE_GERMAN_COMPLIANCE",
        description="Enable German business compliance features (VAT, invoicing, etc.)."
    )
    vat_rate: float = Field(
        default=19.0,
        env="VAT_RATE",
        description="VAT rate as percentage (0-100). German standard VAT is 19%.",
        ge=0.0,
        le=100.0
    )
    currency: str = Field(
        default="EUR",
        env="CURRENCY",
        description="Currency code for business features. Must be 3-letter ISO 4217 code."
    )
    timezone: str = Field(
        default="Europe/Berlin",
        env="TZ",
        description="Timezone for timestamps and scheduling. Use IANA timezone database names."
    )

    # Home Assistant MQTT Integration (Optional)
    mqtt_host: Optional[str] = Field(
        default=None,
        env="MQTT_HOST",
        description="MQTT broker hostname or IP address. Leave empty to disable MQTT integration."
    )
    mqtt_port: int = Field(
        default=1883,
        env="MQTT_PORT",
        description="MQTT broker port. Standard ports are 1883 (unencrypted) or 8883 (TLS).",
        ge=1,
        le=65535
    )
    mqtt_username: Optional[str] = Field(
        default=None,
        env="MQTT_USERNAME",
        description="MQTT broker username for authentication. Optional."
    )
    mqtt_password: Optional[str] = Field(
        default=None,
        env="MQTT_PASSWORD",
        description="MQTT broker password for authentication. Optional."
    )
    mqtt_discovery_prefix: str = Field(
        default="homeassistant",
        env="MQTT_DISCOVERY_PREFIX",
        description="MQTT topic prefix for Home Assistant discovery."
    )

    # Redis Configuration (Optional)
    redis_url: Optional[str] = Field(
        default=None,
        env="REDIS_URL",
        description="Redis connection URL for caching. Format: redis://host:port/db. Optional."
    )

    # Security (Critical)
    secret_key: str = Field(
        default="",
        env="SECRET_KEY",
        description="Secret key for session encryption and signing. MUST be at least 32 characters. Auto-generated if not provided."
    )

    # G-code Preview Optimization
    gcode_optimize_print_only: bool = Field(
        default=True,
        env="GCODE_OPTIMIZE_PRINT_ONLY",
        description="Optimize G-code preview by showing only print moves (no travel)."
    )
    gcode_optimization_max_lines: int = Field(
        default=1000,
        env="GCODE_OPTIMIZATION_MAX_LINES",
        description="Maximum lines to process for G-code optimization. Must be between 100 and 100000.",
        ge=100,
        le=100000
    )
    gcode_render_max_lines: int = Field(
        default=10000,
        env="GCODE_RENDER_MAX_LINES",
        description="Maximum lines to render in G-code preview. Must be between 100 and 1000000.",
        ge=100,
        le=1000000
    )
    preview_render_timeout: int = Field(
        default=60,
        env="PREVIEW_RENDER_TIMEOUT",
        description="Timeout in seconds for rendering 3D file previews. Increase for large/complex models.",
        ge=10,
        le=300
    )

    # Library System Configuration
    library_enabled: bool = Field(
        default=True,
        env="LIBRARY_ENABLED",
        description="Enable library system for file organization and management."
    )
    library_path: str = Field(
        default="/data/printernizer/library",
        env="LIBRARY_PATH",
        description="Directory path for library files. Must be absolute path. Will be created if doesn't exist."
    )
    library_auto_organize: bool = Field(
        default=True,
        env="LIBRARY_AUTO_ORGANIZE",
        description="Automatically organize library files into subfolders."
    )
    library_auto_extract_metadata: bool = Field(
        default=True,
        env="LIBRARY_AUTO_EXTRACT_METADATA",
        description="Automatically extract metadata from uploaded files."
    )
    library_auto_deduplicate: bool = Field(
        default=True,
        env="LIBRARY_AUTO_DEDUPLICATE",
        description="Automatically detect and handle duplicate files in library."
    )
    library_preserve_originals: bool = Field(
        default=True,
        env="LIBRARY_PRESERVE_ORIGINALS",
        description="Preserve original files when processing library items."
    )
    library_checksum_algorithm: str = Field(
        default="sha256",
        env="LIBRARY_CHECKSUM_ALGORITHM",
        description="Checksum algorithm for file hashing: md5, sha1, or sha256."
    )
    library_processing_workers: int = Field(
        default=2,
        env="LIBRARY_PROCESSING_WORKERS",
        description="Number of worker threads for library processing. Must be between 1 and 10.",
        ge=1,
        le=10
    )

    # Library Search Configuration
    library_search_enabled: bool = Field(
        default=True,
        env="LIBRARY_SEARCH_ENABLED",
        description="Enable full-text search in library."
    )
    library_search_min_length: int = Field(
        default=3,
        env="LIBRARY_SEARCH_MIN_LENGTH",
        description="Minimum search query length. Must be between 1 and 10 characters.",
        ge=1,
        le=10
    )

    # Timelapse Configuration
    timelapse_enabled: bool = Field(
        default=True,
        env="TIMELAPSE_ENABLED",
        description="Enable timelapse video creation feature"
    )
    timelapse_source_folder: str = Field(
        default="/data/timelapse-images",
        env="TIMELAPSE_SOURCE_FOLDER",
        description="Folder to watch for timelapse image subfolders. Will be created if doesn't exist."
    )
    timelapse_output_folder: str = Field(
        default="/data/timelapses",
        env="TIMELAPSE_OUTPUT_FOLDER",
        description="Folder for completed timelapse videos. Will be created if doesn't exist."
    )
    timelapse_output_strategy: str = Field(
        default="separate",
        env="TIMELAPSE_OUTPUT_STRATEGY",
        description="Video output location: same, separate, or both"
    )
    timelapse_auto_process_timeout: int = Field(
        default=300,
        env="TIMELAPSE_AUTO_PROCESS_TIMEOUT",
        description="Seconds to wait after last image before auto-processing. Must be between 60 and 3600 seconds.",
        ge=60,
        le=3600
    )
    timelapse_cleanup_age_days: int = Field(
        default=30,
        env="TIMELAPSE_CLEANUP_AGE_DAYS",
        description="Age threshold in days for cleanup recommendations. Must be between 1 and 365 days.",
        ge=1,
        le=365
    )
    timelapse_flickerfree_path: str = Field(
        default="/usr/local/bin/do_timelapse.sh",
        env="TIMELAPSE_FLICKERFREE_PATH",
        description="Path to FlickerFree do_timelapse.sh script for video processing."
    )

    # Slicing Configuration
    slicing_output_dir: str = Field(
        default="/data/printernizer/sliced",
        description="Directory for sliced G-code output files. Will be created if doesn't exist."
    )
    # Note: Env var SLICING_OUTPUT_DIR is automatically mapped from field name

    # =====================================================================
    # USAGE STATISTICS - Privacy-first telemetry (opt-in only)
    # =====================================================================

    usage_stats_endpoint: str = Field(
        default="http://80.240.28.236:8080/submit",
        env="USAGE_STATS_ENDPOINT",
        description="Endpoint URL for submitting aggregated usage statistics."
    )
    usage_stats_api_key: str = Field(
        default="",
        env="USAGE_STATS_API_KEY",
        description="API key for authenticating with usage statistics aggregation service. Contact the server admin for the key."
    )
    usage_stats_timeout: int = Field(
        default=10,
        env="USAGE_STATS_TIMEOUT",
        description="HTTP request timeout in seconds for statistics submission. Must be between 5 and 60 seconds.",
        ge=5,
        le=60
    )
    usage_stats_retry_count: int = Field(
        default=3,
        env="USAGE_STATS_RETRY_COUNT",
        description="Number of retry attempts for failed statistics submissions. Must be between 0 and 10.",
        ge=0,
        le=10
    )
    usage_stats_submission_interval_days: int = Field(
        default=7,
        env="USAGE_STATS_SUBMISSION_INTERVAL_DAYS",
        description="Interval in days between automatic statistics submissions. Must be between 1 and 30 days.",
        ge=1,
        le=30
    )

    # =====================================================================
    # VALIDATORS - Comprehensive validation for all settings
    # =====================================================================

    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_environments = ['development', 'production', 'homeassistant', 'testing']
        if v.lower() not in valid_environments:
            raise ValueError(
                f"Invalid environment '{v}'. Must be one of: {', '.join(valid_environments)}"
            )
        return v.lower()

    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level setting."""
        valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
        if v.lower() not in valid_levels:
            raise ValueError(
                f"Invalid log_level '{v}'. Must be one of: {', '.join(valid_levels)}"
            )
        return v.lower()

    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Validate and generate secure secret key if needed."""
        # If no secret key provided (empty or default), generate one
        if not v or v == "your-super-secret-key-change-in-production" or v == "REPLACE_WITH_SECURE_GENERATED_KEY":
            generated_key = secrets.token_urlsafe(32)
            logger.warning(
                "No SECRET_KEY environment variable set. Generated secure key for this session.",
                generated_key_length=len(generated_key)
            )
            logger.info(
                "For production, set SECRET_KEY environment variable to persist sessions across restarts. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
            return generated_key

        # Validate provided key
        if len(v) < 32:
            raise ValueError(
                f"Secret key must be at least 32 characters long for security (got {len(v)}). "
                "Set a longer SECRET_KEY environment variable."
            )
        return v

    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code format."""
        if not v or len(v) != 3:
            raise ValueError(
                f"Invalid currency code '{v}'. Must be 3-letter ISO 4217 code (e.g., EUR, USD, GBP)."
            )
        return v.upper()

    @validator('library_checksum_algorithm')
    def validate_checksum_algorithm(cls, v):
        """Validate checksum algorithm."""
        valid_algorithms = ['md5', 'sha1', 'sha256']
        if v.lower() not in valid_algorithms:
            raise ValueError(
                f"Invalid checksum algorithm '{v}'. Must be one of: {', '.join(valid_algorithms)}"
            )
        return v.lower()

    @validator('timelapse_output_strategy')
    def validate_timelapse_strategy(cls, v):
        """Validate timelapse output strategy."""
        valid_strategies = ['same', 'separate', 'both']
        if v.lower() not in valid_strategies:
            raise ValueError(
                f"Invalid timelapse output strategy '{v}'. Must be one of: {', '.join(valid_strategies)}"
            )
        return v.lower()

    @validator('database_path')
    def validate_database_path(cls, v):
        """Validate database path."""
        path = Path(v)

        # Ensure absolute path
        if not path.is_absolute():
            logger.warning(
                "DATABASE_PATH is not absolute - converting",
                original=v,
                converted=str(path.absolute())
            )
            return str(path.absolute())

        return v

    @validator('downloads_path')
    def validate_downloads_path(cls, v):
        """Validate downloads path."""
        path = Path(v)

        # Ensure absolute path for production paths
        if not path.is_absolute() and not v.startswith('./'):
            logger.warning(
                "DOWNLOADS_PATH is not absolute - converting",
                original=v,
                converted=str(path.absolute())
            )
            return str(path.absolute())

        return v

    @validator('library_path')
    def validate_library_path(cls, v):
        """Validate library path is absolute."""
        if not v:
            return "/data/printernizer/library"  # Default for HA addon

        path = Path(v)

        # Ensure absolute path
        if not path.is_absolute():
            logger.warning(
                "LIBRARY_PATH is not absolute - converting",
                original=v,
                converted=str(path.absolute())
            )
            return str(path.absolute())

        return v

    @validator('timelapse_source_folder', 'timelapse_output_folder')
    def validate_timelapse_paths(cls, v):
        """Validate timelapse folder paths."""
        path = Path(v)

        # Ensure absolute path
        if not path.is_absolute():
            logger.warning(
                "Timelapse path is not absolute - converting",
                original=v,
                converted=str(path.absolute())
            )
            return str(path.absolute())

        return v

    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate timezone name."""
        try:
            import zoneinfo
            # This will raise if timezone is invalid
            zoneinfo.ZoneInfo(v)
            return v
        except Exception:
            # Fall back to pytz for older Python versions
            try:
                import pytz
                pytz.timezone(v)
                return v
            except Exception:
                logger.warning(
                    "Invalid timezone - using default",
                    timezone=v,
                    default="Europe/Berlin"
                )
                return "Europe/Berlin"
    
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
    def allowed_upload_extensions_list(self) -> List[str]:
        """Get allowed upload extensions as list."""
        if not self.allowed_upload_extensions:
            return []
        return [ext.strip().lower() for ext in self.allowed_upload_extensions.split(",") if ext.strip()]

    @property
    def is_homeassistant_addon(self) -> bool:
        """Check if running as Home Assistant addon."""
        return self.environment == "homeassistant" or os.path.exists("/run/s6/services")
    
    @property  
    def mqtt_available(self) -> bool:
        """Check if MQTT configuration is available."""
        return self.mqtt_host is not None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Enable case-insensitive env var matching
        case_sensitive=False,
    )


# Global settings instance
_settings: Optional[PrinternizerSettings] = None


def get_settings() -> PrinternizerSettings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = PrinternizerSettings()
    return _settings


def reload_settings() -> PrinternizerSettings:
    """Reload settings from environment variables.

    Forces a reload of all settings by recreating the global settings instance.
    Useful after environment variable changes.

    Returns:
        Newly loaded PrinternizerSettings instance.
    """
    global _settings
    _settings = PrinternizerSettings()
    return _settings


def validate_settings_on_startup(settings: Optional[PrinternizerSettings] = None) -> dict:
    """
    Comprehensive startup validation of all settings.

    Performs thorough validation including:
    - Required directories existence and permissions
    - Numeric value ranges
    - String format validation
    - Security settings verification

    Args:
        settings: Settings instance to validate. If None, uses global settings.

    Returns:
        dict: Validation results with structure:
            {
                "valid": bool,
                "errors": List[str],     # Critical errors that prevent startup
                "warnings": List[str],   # Non-critical issues to log
                "info": List[str]        # Informational messages
            }
    """
    if settings is None:
        settings = get_settings()

    errors = []
    warnings = []
    info = []

    # ========================================================================
    # Validate Critical Paths
    # ========================================================================

    # Database path - parent directory must exist and be writable
    try:
        db_path = Path(settings.database_path)
        db_parent = db_path.parent

        if not db_parent.exists():
            try:
                db_parent.mkdir(parents=True, exist_ok=True)
                info.append(f"Created database directory: {db_parent}")
            except Exception as e:
                errors.append(f"Cannot create database directory {db_parent}: {e}")
        elif not os.access(db_parent, os.W_OK):
            errors.append(f"Database directory not writable: {db_parent}")
    except Exception as e:
        errors.append(f"Invalid database path: {e}")

    # Downloads path - must be creatable and writable
    try:
        downloads_path = Path(settings.downloads_path)
        if not downloads_path.exists():
            try:
                downloads_path.mkdir(parents=True, exist_ok=True)
                info.append(f"Created downloads directory: {downloads_path}")
            except Exception as e:
                errors.append(f"Cannot create downloads directory {downloads_path}: {e}")
        elif not os.access(downloads_path, os.W_OK):
            errors.append(f"Downloads directory not writable: {downloads_path}")
    except Exception as e:
        errors.append(f"Invalid downloads path: {e}")

    # Library path - must be creatable and writable
    if settings.library_enabled:
        try:
            library_path = Path(settings.library_path)
            if not library_path.exists():
                try:
                    library_path.mkdir(parents=True, exist_ok=True)
                    info.append(f"Created library directory: {library_path}")
                except Exception as e:
                    errors.append(f"Cannot create library directory {library_path}: {e}")
            elif not os.access(library_path, os.W_OK):
                errors.append(f"Library directory not writable: {library_path}")
        except Exception as e:
            errors.append(f"Invalid library path: {e}")

    # Timelapse paths - must be creatable if timelapse is enabled
    if settings.timelapse_enabled:
        for path_name, path_value in [
            ("timelapse source", settings.timelapse_source_folder),
            ("timelapse output", settings.timelapse_output_folder)
        ]:
            try:
                path = Path(path_value)
                if not path.exists():
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        info.append(f"Created {path_name} directory: {path}")
                    except Exception as e:
                        warnings.append(f"Cannot create {path_name} directory {path}: {e}")
            except Exception as e:
                warnings.append(f"Invalid {path_name} path: {e}")

    # ========================================================================
    # Validate Security Settings
    # ========================================================================

    # Secret key validation (already done in validator, but double-check)
    if len(settings.secret_key) < 32:
        errors.append(f"Secret key too short: {len(settings.secret_key)} chars (minimum 32)")

    # ========================================================================
    # Validate Numeric Ranges (already validated by Pydantic, but log info)
    # ========================================================================

    if settings.api_port < 1024 and settings.api_port != 80 and settings.api_port != 443:
        warnings.append(
            f"Using privileged port {settings.api_port} (< 1024) may require root privileges"
        )

    # ========================================================================
    # Validate MQTT Settings
    # ========================================================================

    if settings.mqtt_host:
        if not settings.mqtt_username and not settings.mqtt_password:
            warnings.append("MQTT host configured but no authentication set - connection may fail")
        info.append(f"MQTT integration enabled: {settings.mqtt_host}:{settings.mqtt_port}")
    else:
        info.append("MQTT integration disabled (no host configured)")

    # ========================================================================
    # Validate Feature Flags and Dependencies
    # ========================================================================

    if settings.library_enabled:
        info.append("Library system enabled")
    else:
        info.append("Library system disabled")

    if settings.timelapse_enabled:
        # Check if flickerfree script exists
        flickerfree_path = Path(settings.timelapse_flickerfree_path)
        if not flickerfree_path.exists():
            warnings.append(
                f"Timelapse enabled but FlickerFree script not found: {flickerfree_path}"
            )
        info.append("Timelapse feature enabled")
    else:
        info.append("Timelapse feature disabled")

    # ========================================================================
    # Summary
    # ========================================================================

    is_valid = len(errors) == 0

    # Log results
    if errors:
        logger.error("Settings validation FAILED", errors=errors, warnings=warnings)
    elif warnings:
        logger.warning("Settings validation succeeded with warnings", warnings=warnings)
    else:
        logger.info("Settings validation succeeded", info_count=len(info))

    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "info": info
    }