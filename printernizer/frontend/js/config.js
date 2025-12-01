/**
 * Printernizer Configuration
 * Central configuration for the frontend application
 */

// Debug logging helper
const debugLog = (message, data = {}) => {
    if (typeof Logger !== 'undefined' && Logger.isDebug()) {
        Logger.debug(`[Printernizer Config] ${message}`, data);
    } else if (window.location.search.includes('debug=true') || localStorage.getItem('printernizer_debug') === 'true') {
        // Fallback to console.log if Logger not available yet
        console.log(`[Printernizer Config] ${message}`, data);
    }
};

// Dynamic API URL detection for network access
// Supports both Home Assistant Ingress (absolute-path-relative URLs) and direct access (port 8000)
const getApiBaseUrl = () => {
    const host = window.location.hostname;
    const port = window.location.port;
    const protocol = window.location.protocol;
    const pathname = window.location.pathname;
    const href = window.location.href;

    debugLog('Detecting API Base URL', { host, port, protocol, pathname, href });

    // If accessed through HA Ingress (no port in URL) or on port 8123, use absolute-path-relative URLs
    // Home Assistant Ingress proxies requests through /api/hassio_ingress/<token>/
    // We extract the base path and construct absolute-path-relative URLs (starting with /)
    if (!port || port === '8123') {
        // Extract the ingress base path from pathname
        // Pathname will be like: /api/hassio_ingress/<token>/ or /api/hassio_ingress/<token>/index.html
        // We need to preserve the base path including the trailing slash
        let basePath = pathname;

        // Remove any file name (index.html, etc.) but keep the directory path
        if (basePath.includes('.')) {
            basePath = basePath.substring(0, basePath.lastIndexOf('/') + 1);
        }

        // Collapse any double slashes that might occur from HA Ingress
        basePath = basePath.replace(/\/+/g, '/');

        // Ensure trailing slash
        if (!basePath.endsWith('/')) {
            basePath += '/';
        }

        const apiUrl = `${basePath}api/v1`;

        debugLog('HA Ingress mode detected - using absolute-path-relative URL', {
            apiUrl,
            pathname,
            basePath,
            reason: !port ? 'no port' : 'port 8123',
            note: 'Absolute-path-relative URL includes ingress proxy path'
        });

        return apiUrl;
    }

    // Direct access mode: use explicit port 8000
    const apiUrl = `${protocol}//${host}:8000/api/v1`;
    debugLog('Direct access mode detected', { apiUrl, port });
    return apiUrl;
};

const getBasePath = () => {
    const port = window.location.port;
    const pathname = window.location.pathname;

    debugLog('Detecting Base Path', { port, pathname });

    // Direct access mode (with port) - no base path needed
    if (port && port !== '8123' && port !== '80' && port !== '443') {
        debugLog('Direct access mode - no base path');
        return '';
    }

    // HA Ingress or Nabu Casa - extract the ingress base path
    // Home Assistant Ingress uses paths like /api/hassio_ingress/<token>/
    // Nabu Casa cloud serves at root: /
    let basePath = pathname;

    // Remove any file name (index.html, debug.html, etc.) but keep the directory path
    if (basePath.includes('.')) {
        basePath = basePath.substring(0, basePath.lastIndexOf('/') + 1);
    }

    // Collapse any double slashes that might occur from HA Ingress
    basePath = basePath.replace(/\/+/g, '/');

    // Remove trailing slash
    basePath = basePath.replace(/\/+$/, '');

    // If basePath is exactly "/" (root), return empty string to prevent double slash
    if (basePath === '' || basePath === '/') {
        debugLog('Root path detected - returning empty base path');
        return '';
    }

    debugLog('HA Ingress base path detected', { basePath, pathname });
    return basePath;
};

const getWebSocketUrl = () => {
    const host = window.location.hostname;
    const port = window.location.port;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const basePath = getBasePath();

    debugLog('Detecting WebSocket URL', { host, port, protocol, basePath });

    // If accessed through HA Ingress (no port in URL) or on port 8123, use absolute-path-relative WebSocket path
    // Home Assistant Ingress proxies WebSocket connections through /api/hassio_ingress/<token>/
    if (!port || port === '8123') {
        // Build WebSocket URL with absolute-path-relative path
        const wsUrl = `${protocol}//${host}${port ? ':' + port : ''}${basePath}/ws`;

        debugLog('HA Ingress WebSocket mode - using absolute-path-relative URL', {
            wsUrl,
            basePath,
            note: 'WebSocket URL with absolute path includes ingress proxy path'
        });

        return wsUrl;
    }

    // Direct access mode: use explicit port 8000
    const wsUrl = `${protocol}//${host}:8000/ws`;
    debugLog('Direct WebSocket mode', { wsUrl });
    return wsUrl;
};

/**
 * Safely join path segments, preventing double slashes
 * @param {...string} parts - Path segments to join
 * @returns {string} - Joined path
 */
const joinPath = (...parts) => {
    return parts
        .filter(Boolean)
        .map(part => String(part).replace(/^\/+|\/+$/g, '')) // Remove leading/trailing slashes
        .join('/')
        .replace(/\/+/g, '/') // Collapse multiple slashes
        .replace(/^(?!\/)/, '/'); // Ensure leading slash
};

const CONFIG = {
    // API Configuration - Dynamic URLs for network access
    API_BASE_URL: getApiBaseUrl(),
    WEBSOCKET_URL: getWebSocketUrl(),
    BASE_PATH: getBasePath(), // Base ingress path for non-API URLs (e.g., /api/hassio_ingress/<token> or empty)

    // Path helper function
    joinPath: joinPath, // Helper to safely join paths (prevents double slashes)

    // Application Settings
    APP_NAME: 'Printernizer',
    APP_VERSION: '1.5.7',
    LANGUAGE: 'de',
    TIMEZONE: 'Europe/Berlin',
    CURRENCY: 'EUR',

    // Update Intervals (milliseconds)
    DASHBOARD_REFRESH_INTERVAL: 30000,  // 30 seconds
    JOB_REFRESH_INTERVAL: 5000,         // 5 seconds
    PRINTER_STATUS_INTERVAL: 10000,     // 10 seconds

    // Pagination
    DEFAULT_PAGE_SIZE: 50,
    MAX_PAGE_SIZE: 100,

    // File Upload
    MAX_FILE_SIZE: 50 * 1024 * 1024,    // 50MB
    ALLOWED_FILE_TYPES: ['.3mf', '.stl', '.obj', '.gcode'],

    // UI Settings
    TOAST_DURATION: 5000,               // 5 seconds
    MODAL_ANIMATION_DURATION: 300,      // 300ms

    // Business Settings
    BUSINESS_HOURS: {
        start: '08:00',
        end: '18:00'
    },

    // German Date/Time Formats
    DATE_FORMAT: 'DD.MM.YYYY',
    TIME_FORMAT: 'HH:mm',
    DATETIME_FORMAT: 'DD.MM.YYYY HH:mm',

    // Currency Formatting (German)
    CURRENCY_FORMAT: {
        style: 'currency',
        currency: 'EUR',
        locale: 'de-DE',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    },

    // Number Formatting (German)
    NUMBER_FORMAT: {
        locale: 'de-DE',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    },

    // Status Mappings
    PRINTER_STATUS: {
        'online': {
            label: 'Online',
            icon: '🟢',
            class: 'status-online'
        },
        'offline': {
            label: 'Offline',
            icon: '🔴',
            class: 'status-offline'
        },
        'printing': {
            label: 'Druckt',
            icon: '🖨️',
            class: 'status-printing'
        },
        'idle': {
            label: 'Bereit',
            icon: '⏸️',
            class: 'status-idle'
        },
        'error': {
            label: 'Fehler',
            icon: '⚠️',
            class: 'status-error'
        },
        'unknown': {
            label: 'Unbekannt',
            icon: '❓',
            class: 'status-unknown'
        }
    },

    JOB_STATUS: {
        'queued': {
            label: 'Warteschlange',
            icon: '⏳',
            class: 'status-queued'
        },
        'preparing': {
            label: 'Vorbereitung',
            icon: '⚙️',
            class: 'status-preparing'
        },
        'printing': {
            label: 'Druckt',
            icon: '🖨️',
            class: 'status-printing'
        },
        'paused': {
            label: 'Pausiert',
            icon: '⏸️',
            class: 'status-paused'
        },
        'completed': {
            label: 'Abgeschlossen',
            icon: '✅',
            class: 'status-completed'
        },
        'failed': {
            label: 'Fehlgeschlagen',
            icon: '❌',
            class: 'status-failed'
        },
        'cancelled': {
            label: 'Abgebrochen',
            icon: '🚫',
            class: 'status-cancelled'
        }
    },

    FILE_STATUS: {
        'available': {
            label: 'Verfügbar',
            icon: '📁',
            class: 'status-available'
        },
        'downloaded': {
            label: 'Heruntergeladen',
            icon: '✓',
            class: 'status-downloaded'
        },
        'local': {
            label: 'Lokal',
            icon: '💾',
            class: 'status-local'
        },
        'downloading': {
            label: 'Lädt herunter...',
            icon: '⬇️',
            class: 'status-downloading'
        },
        'error': {
            label: 'Fehler',
            icon: '❌',
            class: 'status-error'
        },
        'deleted': {
            label: 'Gelöscht',
            icon: '🗑️',
            class: 'status-deleted'
        },
        'unavailable': {
            label: 'Nicht verfügbar',
            icon: '⚠️',
            class: 'status-unavailable'
        }
    },

    // Printer Types
    PRINTER_TYPES: {
        'bambu_lab': {
            label: 'Bambu Lab A1',
            icon: '🖨️',
            color: '#2563eb'
        },
        'prusa_core': {
            label: 'Prusa Core One',
            icon: '🖨️',
            color: '#ea580c'
        },
        'prusa': {
            label: 'Prusa Core One',
            icon: '🖨️',
            color: '#ea580c'
        }
    },

    // Material Types
    MATERIAL_TYPES: {
        'PLA': { label: 'PLA', color: '#22c55e' },
        'PETG': { label: 'PETG', color: '#3b82f6' },
        'ABS': { label: 'ABS', color: '#ef4444' },
        'TPU': { label: 'TPU', color: '#a855f7' },
        'ASA': { label: 'ASA', color: '#f59e0b' },
        'PC': { label: 'PC', color: '#6b7280' }
    },

    // API Endpoints
    ENDPOINTS: {
        // System
        HEALTH: 'health',
        SYSTEM_INFO: 'system/info',
        SYSTEM_SHUTDOWN: 'system/shutdown',

        // Settings
        APPLICATION_SETTINGS: 'settings/application',
        WATCH_FOLDER_SETTINGS: 'settings/watch-folders',

        // Printers
        PRINTERS: 'printers',
        PRINTER_DETAIL: (id) => `printers/${id}`,
        PRINTER_DISCOVER: 'printers/discover',
        PRINTER_DISCOVER_INTERFACES: 'printers/discover/interfaces',
        PRINTER_DISCOVER_STARTUP: 'printers/discover/startup',

        // Jobs
        JOBS: 'jobs',
        JOB_DETAIL: (id) => `jobs/${id}`,
        JOB_CANCEL: (id) => `jobs/${id}/cancel`,

        // Files
        FILES: 'files',
        FILE_DETAIL: (id) => `files/${id}`,
        FILE_DOWNLOAD: (id) => `files/${id}/download`,
        FILE_DOWNLOAD_STATUS: (id) => `files/${id}/download/status`,
        FILES_CLEANUP: 'files/cleanup',
        FILES_CLEANUP_CANDIDATES: 'files/cleanup/candidates',

        // Statistics
        STATISTICS_OVERVIEW: 'analytics/overview',
        STATISTICS_PRINTER: (id) => `analytics/printers/${id}`,

        // ========================================
        // MILESTONE 1.2: ENHANCED ENDPOINTS
        // ========================================

        // Real-time Printer Status
        PRINTER_STATUS: (id) => `printers/${id}/status`,

        // Real-time Monitoring
        PRINTER_MONITORING_START: (id) => `printers/${id}/monitoring/start`,
        PRINTER_MONITORING_STOP: (id) => `printers/${id}/monitoring/stop`,

        // Enhanced File Management (Drucker-Dateien)
        PRINTER_FILES: (id) => `printers/${id}/files`,
        PRINTER_FILE_DOWNLOAD: (id, filename) => `printers/${id}/files/${filename}/download`,
        PRINTER_FILE_DOWNLOAD_STATUS: (id, filename) => `printers/${id}/files/${filename}/status`,
        PRINTER_DOWNLOAD_FILE: (id) => `printers/${id}/download-file`,
	// Manual trigger to download & process currently printing job file for thumbnail extraction
	PRINTER_DOWNLOAD_CURRENT_JOB: (id) => `printers/${id}/download-current-job`,

        // Thumbnail Processing Endpoints
        FILE_EXTRACT_THUMBNAIL: (fileId) => `files/${fileId}/thumbnail/extract`,
        FILE_GENERATE_THUMBNAIL: (fileId) => `files/${fileId}/thumbnail/generate`,
        FILE_ANALYZE_GCODE: (fileId) => `files/${fileId}/analyze/gcode`
    },

    // WebSocket Message Types
    WS_MESSAGE_TYPES: {
        PRINTER_STATUS: 'printer_status',
        JOB_UPDATE: 'job_update',
        FILE_UPDATE: 'file_update',
        SYSTEM_ALERT: 'system_alert'
    },

    // Error Messages (German)
    ERROR_MESSAGES: {
        NETWORK_ERROR: 'Netzwerkfehler. Bitte überprüfen Sie Ihre Internetverbindung.',
        SERVER_ERROR: 'Serverfehler. Bitte versuchen Sie es später erneut.',
        PRINTER_OFFLINE: 'Drucker ist offline oder nicht erreichbar.',
        FILE_NOT_FOUND: 'Datei wurde nicht gefunden.',
	PRINTER_NOT_FOUND: 'Drucker wurde nicht gefunden.',
        DOWNLOAD_FAILED: 'Download fehlgeschlagen.',
        INVALID_INPUT: 'Ungültige Eingabe. Bitte überprüfen Sie Ihre Daten.',
        PERMISSION_DENIED: 'Zugriff verweigert.',
        TIMEOUT: 'Zeitüberschreitung. Vorgang abgebrochen.',
        UNKNOWN_ERROR: 'Ein unbekannter Fehler ist aufgetreten.'
    },

    // Success Messages (German)
    SUCCESS_MESSAGES: {
        PRINTER_ADDED: 'Drucker erfolgreich hinzugefügt.',
        PRINTER_UPDATED: 'Drucker-Einstellungen aktualisiert.',
        PRINTER_REMOVED: 'Drucker entfernt.',
        FILE_DOWNLOADED: 'Datei erfolgreich heruntergeladen.',
        JOB_CANCELLED: 'Auftrag wurde abgebrochen.',
        SETTINGS_SAVED: 'Einstellungen gespeichert.'
    },

    // Loading Messages (German)
    LOADING_MESSAGES: {
        LOADING_PRINTERS: 'Lade Drucker...',
        LOADING_JOBS: 'Lade Aufträge...',
        LOADING_FILES: 'Lade Dateien...',
        LOADING_STATISTICS: 'Lade Statistiken...',
        CONNECTING: 'Verbinde...',
        DOWNLOADING: 'Lade herunter...',
        UPDATING: 'Aktualisiere...'
    },

    // Notification Unique Keys for Deduplication
    NOTIFICATION_KEYS: {
        // Connection Status
        WS_CONNECTED: 'connection:websocket:connected',
        WS_DISCONNECTED: 'connection:websocket:disconnected',
        WS_RECONNECTING: 'connection:websocket:reconnecting',
        BACKEND_CONNECTED: 'connection:backend:connected',
        BACKEND_OFFLINE: 'connection:backend:offline',
        BACKEND_ERROR: 'connection:backend:error',

        // Auto-Download System
        AUTO_DOWNLOAD_READY: 'system:autodownload:ready',
        AUTO_DOWNLOAD_ERROR: 'system:autodownload:error',
        AUTO_DOWNLOAD_OFFLINE: 'system:autodownload:offline',

        // System Status
        SYSTEM_HEALTHY: 'system:health:ok',
        SYSTEM_WARNING: 'system:health:warning',
        SYSTEM_ERROR: 'system:health:error',

        // Welcome/Initialization
        APP_WELCOME: 'app:welcome',
        APP_INITIALIZED: 'app:initialized'
    }
};

// Log final configuration
debugLog('Final Configuration', {
    API_BASE_URL: CONFIG.API_BASE_URL,
    WEBSOCKET_URL: CONFIG.WEBSOCKET_URL,
    BASE_PATH: CONFIG.BASE_PATH,
    location: {
        href: window.location.href,
        pathname: window.location.pathname,
        hostname: window.location.hostname,
        port: window.location.port
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}

// Freeze configuration to prevent modification
Object.freeze(CONFIG);

// Make debug logging globally available
window.PrinternizerDebug = {
    enable: () => localStorage.setItem('printernizer_debug', 'true'),
    disable: () => localStorage.removeItem('printernizer_debug'),
    getConfig: () => ({
        API_BASE_URL: CONFIG.API_BASE_URL,
        WEBSOCKET_URL: CONFIG.WEBSOCKET_URL,
        BASE_PATH: CONFIG.BASE_PATH,
        location: {
            href: window.location.href,
            pathname: window.location.pathname,
            hostname: window.location.hostname,
            port: window.location.port
        }
    })
};
