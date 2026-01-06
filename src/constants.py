"""
Application-wide constants for Printernizer.

This module centralizes all magic numbers and hardcoded values used throughout
the application, making them easier to maintain, document, and modify.

Constants are organized into logical groups using classes as namespaces.
"""


class NetworkConstants:
    """
    Network-related configuration constants.

    Includes connection timeouts, retry configurations, and network protocols.
    """

    # Connection Timeouts
    CONNECTION_TIMEOUT_SECONDS: int = 30
    """General connection timeout for printer connections"""

    PRUSA_CONNECT_TIMEOUT_SECONDS: int = 5
    """Prusa printer connection-specific timeout"""

    THUMBNAIL_DOWNLOAD_TIMEOUT_SECONDS: int = 15
    """HTTP timeout for thumbnail downloads"""

    SNAPSHOT_TIMEOUT_SECONDS: int = 10
    """Camera snapshot request timeout"""

    HTTP_DOWNLOAD_TIMEOUT_SECONDS: int = 120
    """Timeout for large file downloads via HTTP"""

    MQTT_CONNECT_TIMEOUT_SECONDS: int = 60
    """MQTT broker connection timeout"""

    MQTT_CONNECTION_WAIT_SECONDS: int = 3
    """Wait time for MQTT connection establishment"""

    # Network Configuration
    PRUSA_KEEPALIVE_TIMEOUT_SECONDS: int = 30
    """TCP keepalive timeout for Prusa connections"""

    PRUSA_DNS_CACHE_TTL_SECONDS: int = 300
    """DNS cache time-to-live for Prusa connections"""

    PRUSA_CONNECTION_LIMIT: int = 10
    """Maximum concurrent connections to Prusa printer"""

    # Retry Configuration
    FTP_RETRY_COUNT: int = 3
    """Number of FTP connection retry attempts"""

    FTP_RETRY_DELAY_SECONDS: float = 1.0
    """Initial delay between FTP retry attempts (base for exponential backoff)"""

    FTP_RETRY_BACKOFF_MULTIPLIER: float = 2.0
    """Exponential backoff multiplier for FTP retries"""

    FTP_RETRY_MAX_DELAY_SECONDS: float = 30.0
    """Maximum delay between FTP retry attempts"""

    FTP_RETRY_JITTER_FACTOR: float = 0.1
    """Random jitter factor (±10%) to prevent thundering herd"""

    MQTT_RETRY_COUNT: int = 3
    """Number of MQTT connection retry attempts"""

    MQTT_RETRY_DELAY_SECONDS: float = 2.0
    """Initial delay between MQTT retry attempts"""

    MQTT_RETRY_BACKOFF_MULTIPLIER: float = 2.0
    """Exponential backoff multiplier for MQTT retries"""

    MQTT_RETRY_MAX_DELAY_SECONDS: float = 60.0
    """Maximum delay between MQTT retry attempts"""

    MQTT_AUTO_RECONNECT_DELAY_SECONDS: float = 5.0
    """Delay before automatic MQTT reconnection on disconnect"""

    PRUSA_MAX_RETRIES: int = 2
    """Maximum connection retry attempts for Prusa"""

    PRUSA_RETRY_BACKOFF_MULTIPLIER: int = 2
    """Exponential backoff multiplier for Prusa retries"""


class PortConstants:
    """
    Network port number constants.

    Defines standard ports used by printers, services, and the application.
    """

    BAMBU_MQTT_PORT: int = 8883
    """Bambu Lab MQTT broker port (implicit TLS)"""

    BAMBU_FTP_PORT: int = 990
    """Bambu Lab FTP port (implicit TLS)"""

    BAMBU_CAMERA_PORT: int = 6000
    """Bambu Lab A1/P1 camera TCP port (proprietary protocol)"""

    BAMBU_CAMERA_PORT_RTSP: int = 322
    """Bambu Lab X1 series RTSP port (future support)"""

    MQTT_DEFAULT_PORT: int = 1883
    """Home Assistant MQTT default port"""

    DEFAULT_API_PORT: int = 8000
    """Default HTTP server port for Printernizer API"""

    BAMBU_SSDP_DISCOVERY_PORT_1: int = 1990
    """Bambu Lab SSDP discovery port (primary)"""

    BAMBU_SSDP_DISCOVERY_PORT_2: int = 2021
    """Bambu Lab SSDP discovery port (alternate)"""


class TimeoutConstants:
    """
    Application lifecycle and shutdown timeout constants.

    Controls graceful shutdown timing for services and background tasks.
    """

    SHUTDOWN_TIMEOUT_SECONDS: int = 30
    """Maximum time allowed for graceful shutdown"""

    SERVICE_SHUTDOWN_TIMEOUT_SECONDS: int = 5
    """Individual service shutdown timeout"""

    PRINTER_SERVICE_SHUTDOWN_TIMEOUT_SECONDS: int = 15
    """Extended timeout for printer service shutdown"""

    BACKGROUND_TASK_TIMEOUT_SECONDS: int = 5
    """Timeout for background task completion during shutdown"""

    DISCOVERY_STARTUP_DELAY_SECONDS: int = 60
    """Delay before automatic printer discovery on startup"""

    DISCOVERY_TIMEOUT_SECONDS: int = 10
    """Timeout for printer discovery scan"""


class FileConstants:
    """
    File processing and download configuration constants.

    Includes file size limits, chunk sizes, and download concurrency settings.
    """

    MAX_FILE_SIZE_MB: int = 100
    """Maximum allowed file size for downloads in megabytes"""

    MAX_CONCURRENT_DOWNLOADS: int = 5
    """Maximum number of concurrent file downloads"""

    DOWNLOAD_CHUNK_SIZE_BYTES: int = 8192
    """Chunk size for streaming file downloads"""

    DOWNLOAD_PROGRESS_LOG_INTERVAL_BYTES: int = 1_048_576
    """Log progress every 1MB during download (1024 * 1024)"""

    LIBRARY_PROCESSING_WORKERS: int = 2
    """Number of worker threads for library file processing"""

    BAMBU_FILE_CACHE_VALIDITY_SECONDS: int = 30
    """Cached file list validity duration"""


class MonitoringConstants:
    """
    Printer monitoring and polling configuration constants.

    Controls monitoring intervals, backoff strategies, and jitter.
    """

    PRINTER_MONITOR_INTERVAL_SECONDS: int = 30
    """Base interval for printer status polling"""

    MONITOR_BACKOFF_FACTOR: float = 2.0
    """Exponential backoff multiplier for failed monitoring attempts"""

    MONITOR_MAX_INTERVAL_SECONDS: int = 300
    """Maximum monitoring interval after backoff"""

    MONITOR_JITTER_MIN: float = -0.1
    """Minimum jitter for monitoring interval randomization"""

    MONITOR_JITTER_MAX: float = 0.1
    """Maximum jitter for monitoring interval randomization"""

    FILENAME_PREFIX_MATCH_LENGTH: int = 20
    """Prefix length for truncated filename matching"""


class TemperatureConstants:
    """
    Temperature threshold constants for printer state detection.

    Used to infer printer status from nozzle and bed temperatures.
    """

    # Nozzle Temperatures (Celsius)
    NOZZLE_TEMP_PRINTING_THRESHOLD_C: int = 200
    """Minimum nozzle temp to infer printing status"""

    NOZZLE_TEMP_ACTIVE_THRESHOLD_C: int = 100
    """Nozzle temp indicating active heating/printing"""

    NOZZLE_TEMP_COOLING_THRESHOLD_C: int = 50
    """Nozzle temp indicating cooling down"""

    # Bed Temperatures (Celsius)
    BED_TEMP_PRINTING_THRESHOLD_C: int = 50
    """Minimum bed temp to infer printing status"""

    BED_TEMP_COOLING_THRESHOLD_C: int = 30
    """Bed temp indicating cooling down"""


class PaginationConstants:
    """
    API pagination configuration constants.

    Defines default page sizes, limits, and pagination behavior.
    """

    DEFAULT_PAGE_LIMIT: int = 50
    """Default number of items per page"""

    MAX_PAGE_LIMIT: int = 1000
    """Maximum allowed items per page"""

    DEFAULT_PAGE_NUMBER: int = 1
    """Default starting page number"""


class SearchConstants:
    """
    Search and query configuration constants.
    """

    LIBRARY_SEARCH_MIN_LENGTH: int = 3
    """Minimum search query length"""


class SecurityConstants:
    """
    Security and validation configuration constants.

    Includes secret key requirements and security settings.
    """

    SECRET_KEY_MIN_LENGTH: int = 32
    """Minimum required secret key length for security"""

    SECRET_KEY_GENERATION_BYTES: int = 32
    """Length for auto-generated secure secret keys"""

    DEFAULT_VAT_RATE_PERCENT: float = 19.0
    """Default German VAT rate"""


class ServerConstants:
    """
    Server and application configuration constants.

    Includes uvicorn worker settings and development configuration.
    """

    UVICORN_WORKERS: int = 1
    """Force single worker to avoid database initialization conflicts"""

    DEV_PORT_ALTERNATIVES: tuple = (3000, 8000)
    """Additional CORS origins for development"""


class TimelapseConstants:
    """
    Timelapse recording and processing configuration constants.

    Controls timelapse timing, processing, and cleanup behavior.
    """

    TIMELAPSE_AUTO_PROCESS_TIMEOUT_SECONDS: int = 300
    """Wait time after last image before auto-processing"""

    TIMELAPSE_FOLDER_SCAN_INTERVAL_SECONDS: int = 30
    """Interval for scanning source folders for new timelapses"""

    TIMELAPSE_CLEANUP_AGE_DAYS: int = 30
    """Age threshold for cleanup recommendations"""


class ThumbnailConstants:
    """
    Thumbnail image processing configuration constants.

    Includes size limits, quality settings, and caching behavior.
    """

    MAX_WIDTH: int = 512
    """Maximum thumbnail width in pixels"""

    MAX_HEIGHT: int = 512
    """Maximum thumbnail height in pixels"""

    JPEG_QUALITY: int = 85
    """JPEG compression quality for thumbnails"""

    CACHE_DURATION_DAYS: int = 30
    """How long to cache downloaded thumbnails"""

    BACKGROUND_COLOR_RGB: tuple = (255, 255, 255)
    """White background for transparent images"""


class GCodeConstants:
    """
    G-code processing and rendering configuration constants.
    """

    GCODE_OPTIMIZATION_MAX_LINES: int = 1000
    """Maximum lines to process during G-code optimization"""

    GCODE_RENDER_MAX_LINES: int = 10000
    """Maximum lines to render in G-code preview"""


class MQTTTopicConstants:
    """
    MQTT topic templates and paths.

    String format templates for MQTT communications.
    """

    BAMBU_DEVICE_REPORT_TOPIC: str = "device/{serial_number}/report"
    """Topic pattern for Bambu Lab device status reports"""

    BAMBU_DEVICE_REQUEST_TOPIC: str = "device/{serial_number}/request"
    """Topic pattern for Bambu Lab device command requests"""


class FTPPathConstants:
    """
    FTP directory paths for Bambu Lab printers.
    """

    BAMBU_FTP_CACHE_DIR: str = "/cache"
    """FTP path for cache directory"""

    BAMBU_FTP_MODEL_DIR: str = "/model"
    """FTP path for model files"""

    BAMBU_FTP_TIMELAPSE_DIR: str = "/timelapse"
    """FTP path for timelapse files"""


class CameraConstants:
    """
    Camera streaming and snapshot configuration constants.

    Controls Bambu Lab camera protocol parameters, connection management,
    frame processing, and resource limits for camera services.
    """

    # Bambu Lab Camera Protocol
    CAMERA_USERNAME: str = "bblp"
    """Bambu Lab camera authentication username (fixed)"""

    # Frame Management
    FRAME_CACHE_TTL_SECONDS: int = 5
    """Snapshot cache validity duration"""

    JPEG_CHUNK_SIZE: int = 4096
    """TCP read chunk size for JPEG data"""

    MJPEG_TARGET_FPS: int = 30
    """Target frame rate for MJPEG streams"""

    MJPEG_FRAME_DELAY_SECONDS: float = 0.033
    """Delay between frames (~30 FPS)"""

    # Connection Management
    CAMERA_CONNECTION_TIMEOUT_SECONDS: int = 10
    """Camera TCP connection timeout"""

    CAMERA_RECONNECT_DELAY_SECONDS: int = 5
    """Delay between reconnection attempts"""

    CAMERA_MAX_RECONNECT_ATTEMPTS: int = 3
    """Maximum reconnection attempts before giving up"""

    CAMERA_IDLE_TIMEOUT_SECONDS: int = 60
    """Close camera connection after this many seconds of inactivity"""

    # Resource Limits
    MAX_VIEWERS_PER_PRINTER: int = 5
    """Maximum concurrent stream viewers per printer"""

    # Authentication Packet Structure
    AUTH_PACKET_SIZE: int = 80
    """Size of authentication packet in bytes"""

    AUTH_PAYLOAD_SIZE: int = 0x40
    """Authentication payload size (64 bytes)"""

    AUTH_PACKET_TYPE: int = 0x3000
    """Authentication packet type identifier"""

    AUTH_USERNAME_FIELD_SIZE: int = 32
    """Username field size in auth packet (bytes 16-47)"""

    AUTH_PASSWORD_FIELD_SIZE: int = 32
    """Password field size in auth packet (bytes 48-79)"""

    # Frame Header Structure
    FRAME_HEADER_SIZE: int = 16
    """Size of frame header in bytes"""

    # JPEG Validation
    JPEG_MIN_SIZE_BYTES: int = 1024
    """Minimum reasonable JPEG size (1KB)"""

    JPEG_MAX_SIZE_BYTES: int = 10_000_000
    """Maximum reasonable JPEG size (10MB)"""

    JPEG_START_MARKER: bytes = b'\xff\xd8'
    """JPEG start-of-image marker"""

    JPEG_END_MARKER: bytes = b'\xff\xd9'
    """JPEG end-of-image marker"""

    # MJPEG Streaming
    MJPEG_BOUNDARY: str = "frame"
    """Multipart boundary for MJPEG streaming"""


class FileExtensionConstants:
    """
    Common file extension constants.
    """

    EXT_3MF: str = ".3mf"
    """3D Manufacturing Format file extension"""

    EXT_STL: str = ".stl"
    """STereoLithography file extension"""

    EXT_GCODE: str = ".gcode"
    """G-code file extension"""

    EXT_BGCODE: str = ".bgcode"
    """Binary G-code file extension (Prusa)"""

    EXT_JPG: str = ".jpg"
    """JPEG image file extension"""

    EXT_PNG: str = ".png"
    """PNG image file extension"""

    SUPPORTED_3D_FORMATS: tuple = (".3mf", ".stl", ".gcode", ".bgcode")
    """Tuple of all supported 3D print file formats"""

    SUPPORTED_IMAGE_FORMATS: tuple = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
    """Tuple of all supported image formats"""


# Convenience aggregation of all constants for introspection
ALL_CONSTANT_CLASSES = [
    NetworkConstants,
    PortConstants,
    TimeoutConstants,
    FileConstants,
    MonitoringConstants,
    TemperatureConstants,
    PaginationConstants,
    SearchConstants,
    SecurityConstants,
    ServerConstants,
    TimelapseConstants,
    ThumbnailConstants,
    GCodeConstants,
    MQTTTopicConstants,
    FTPPathConstants,
    CameraConstants,
    FileExtensionConstants,
]
