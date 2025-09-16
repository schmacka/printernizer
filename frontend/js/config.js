/**
 * Printernizer Configuration
 * Central configuration for the frontend application
 */

// Dynamic API URL detection for network access
const getApiBaseUrl = () => {
    const host = window.location.hostname;
    const protocol = window.location.protocol;
    // Use same host as frontend, but port 8000 for API
    return `${protocol}//${host}:8000/api/v1`;
};

const getWebSocketUrl = () => {
    const host = window.location.hostname;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use same host as frontend, but port 8000 for WebSocket
    return `${protocol}//${host}:8000/ws`;
};

const CONFIG = {
    // API Configuration - Dynamic URLs for network access
    API_BASE_URL: getApiBaseUrl(),
    WEBSOCKET_URL: getWebSocketUrl(),
    
    // Application Settings
    APP_NAME: 'Printernizer',
    APP_VERSION: '1.0.0',
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
        }
    },
    
    // Printer Types
    PRINTER_TYPES: {
        'bambu_lab': {
            label: 'Bambu Lab A1',
            icon: '🖨️',
            color: '#2563eb'
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
        HEALTH: '/health',
        SYSTEM_INFO: '/system/info',
        
        // Printers
    PRINTERS: '/printers/',
    PRINTER_DETAIL: (id) => `/printers/${id}`,
        
        // Jobs
        JOBS: '/jobs',
        JOB_DETAIL: (id) => `/jobs/${id}`,
        JOB_CANCEL: (id) => `/jobs/${id}/cancel`,
        
        // Files
        FILES: '/files/',
        FILE_DETAIL: (id) => `/files/${id}`,
        FILE_DOWNLOAD: (id) => `/files/${id}/download`,
        FILE_DOWNLOAD_STATUS: (id) => `/files/${id}/download/status`,
        FILES_CLEANUP: '/files/cleanup',
        FILES_CLEANUP_CANDIDATES: '/files/cleanup/candidates',
        
        // Statistics
        STATISTICS_OVERVIEW: '/analytics/overview',
        STATISTICS_PRINTER: (id) => `/analytics/printers/${id}`,

        // ========================================
        // MILESTONE 1.2: ENHANCED ENDPOINTS
        // ========================================
        
        // Real-time Printer Status
        PRINTER_STATUS: (id) => `/printers/${id}/status`,
        PRINTER_STATUS_HISTORY: (id) => `/printers/${id}/status/history`,
        PRINTER_CONNECTION_STATUS: (id) => `/printers/${id}/connection`,
        
        // Real-time Monitoring
        PRINTER_MONITORING_START: (id) => `/printers/${id}/monitoring/start`,
        PRINTER_MONITORING_STOP: (id) => `/printers/${id}/monitoring/stop`,
        
        // Enhanced File Management (Drucker-Dateien)
        PRINTER_FILES: (id) => `/printers/${id}/files`,
        PRINTER_FILE_DOWNLOAD: (id, filename) => `/printers/${id}/files/${filename}/download`,
        PRINTER_FILE_DOWNLOAD_STATUS: (id, filename) => `/printers/${id}/files/${filename}/status`,
        
        // Enhanced Job Management
        PRINTER_CURRENT_JOB: (id) => `/printers/${id}/jobs/current`,
        PRINTER_SYNC_JOBS: (id) => `/printers/${id}/jobs/sync`
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
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}

// Freeze configuration to prevent modification
Object.freeze(CONFIG);