/**
 * Printernizer Utility Functions
 * Common utilities for formatting, validation, and UI helpers
 */

/**
 * Date and Time Formatting (German locale)
 */

/**
 * Format date with German locale
 */
function formatDate(dateString, format = 'short') {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';
    
    const options = {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    };
    
    if (format === 'long') {
        options.weekday = 'long';
        options.month = 'long';
    }
    
    return date.toLocaleDateString('de-DE', options);
}

/**
 * Format time with German locale
 */
function formatTime(dateString, includeSeconds = false) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';
    
    const options = {
        hour: '2-digit',
        minute: '2-digit'
    };
    
    if (includeSeconds) {
        options.second = '2-digit';
    }
    
    return date.toLocaleTimeString('de-DE', options);
}

/**
 * Format date and time with German locale
 */
function formatDateTime(dateString, format = 'short') {
    if (!dateString) return '-';
    
    return `${formatDate(dateString, format)} ${formatTime(dateString)}`;
}

/**
 * Get relative time (German)
 */
function getRelativeTime(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 1) return 'gerade eben';
    if (diffMins < 60) return `vor ${diffMins} Min.`;
    if (diffHours < 24) return `vor ${diffHours} Std.`;
    if (diffDays < 7) return `vor ${diffDays} Tag(en)`;
    
    return formatDate(dateString);
}

/**
 * Format duration in seconds to human readable format (German)
 */
function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '-';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${remainingSeconds}s`;
    } else {
        return `${remainingSeconds}s`;
    }
}

/**
 * Number and Currency Formatting (German locale)
 */

/**
 * Format number with German locale
 */
function formatNumber(number, decimals = 2) {
    if (number === null || number === undefined || isNaN(number)) return '-';
    
    return new Intl.NumberFormat('de-DE', {
        minimumFractionDigits: 0,
        maximumFractionDigits: decimals
    }).format(number);
}

/**
 * Format currency (EUR) with German locale
 */
function formatCurrency(amount) {
    if (amount === null || amount === undefined || isNaN(amount)) return '-';
    
    return new Intl.NumberFormat('de-DE', CONFIG.CURRENCY_FORMAT).format(amount);
}

/**
 * Format percentage with German locale
 */
function formatPercentage(value, decimals = 1) {
    if (value === null || value === undefined || isNaN(value)) return '-';
    
    return `${formatNumber(value, decimals)}%`;
}

/**
 * Format file size in bytes to human readable format
 */
function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return `${formatNumber(bytes / Math.pow(k, i), 1)} ${sizes[i]}`;
}

/**
 * Format weight in grams
 */
function formatWeight(grams) {
    if (!grams || grams === 0) return '0 g';
    
    if (grams >= 1000) {
        return `${formatNumber(grams / 1000, 2)} kg`;
    }
    
    return `${formatNumber(grams, 1)} g`;
}

/**
 * Form and Input Validation
 */

/**
 * Validate IP address
 */
function isValidIP(ip) {
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipRegex.test(ip);
}

/**
 * Validate email address
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate Bambu Lab access code (8 digits)
 */
function isValidAccessCode(code) {
    return /^\d{8}$/.test(code);
}

/**
 * Validate Bambu Lab serial number
 */
function isValidSerialNumber(serial) {
    return /^[A-Z0-9]{8,20}$/.test(serial);
}

/**
 * Validate printer name (3-50 characters, alphanumeric and spaces)
 */
function isValidPrinterName(name) {
    return /^[a-zA-Z0-9\s\-_]{3,50}$/.test(name);
}

/**
 * Validate API key format
 */
function isValidApiKey(key) {
    return key && key.length >= 8 && key.length <= 128;
}

/**
 * Validate required fields in form
 */
function validateForm(form) {
    const errors = [];
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        const label = getFieldLabel(field);
        const value = field.value.trim();
        
        if (!value) {
            errors.push({
                field: field.name || field.id,
                message: `${label} ist erforderlich`
            });
            field.classList.add('error');
        } else {
            field.classList.remove('error');
        }
    });
    
    // Validate IP addresses
    const ipFields = form.querySelectorAll('[data-validate="ip"]');
    ipFields.forEach(field => {
        if (field.value && !isValidIP(field.value)) {
            errors.push({
                field: field.name || field.id,
                message: 'Ungültige IP-Adresse (Format: xxx.xxx.xxx.xxx)'
            });
            field.classList.add('error');
        }
    });
    
    // Validate printer names
    const nameFields = form.querySelectorAll('[data-validate="printer-name"]');
    nameFields.forEach(field => {
        if (field.value && !isValidPrinterName(field.value)) {
            errors.push({
                field: field.name || field.id,
                message: 'Druckername muss 3-50 Zeichen lang sein (Buchstaben, Zahlen, Leerzeichen)'
            });
            field.classList.add('error');
        }
    });
    
    // Validate access codes
    const accessCodeFields = form.querySelectorAll('[data-validate="access-code"]');
    accessCodeFields.forEach(field => {
        if (field.value && !isValidAccessCode(field.value)) {
            errors.push({
                field: field.name || field.id,
                message: 'Access Code muss genau 8 Ziffern enthalten'
            });
            field.classList.add('error');
        }
    });
    
    // Validate serial numbers
    const serialFields = form.querySelectorAll('[data-validate="serial-number"]');
    serialFields.forEach(field => {
        if (field.value && !isValidSerialNumber(field.value)) {
            errors.push({
                field: field.name || field.id,
                message: 'Seriennummer muss 8-20 Zeichen (Buchstaben und Zahlen) enthalten'
            });
            field.classList.add('error');
        }
    });
    
    // Validate API keys
    const apiKeyFields = form.querySelectorAll('[data-validate="api-key"]');
    apiKeyFields.forEach(field => {
        if (field.value && !isValidApiKey(field.value)) {
            errors.push({
                field: field.name || field.id,
                message: 'API Key muss zwischen 16 und 64 Zeichen lang sein'
            });
            field.classList.add('error');
        }
    });
    
    return errors;
}

/**
 * Get field label for error messages
 */
function getFieldLabel(field) {
    // Try to find associated label
    const label = document.querySelector(`label[for="${field.id}"]`);
    if (label) {
        return label.textContent.replace(':', '').trim();
    }
    
    // Use placeholder or field name/id as fallback
    return field.placeholder || field.name || field.id || 'Feld';
}

/**
 * Show field validation error
 */
function showFieldError(field, message) {
    field.classList.add('error');
    
    // Remove existing error message
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    field.parentNode.appendChild(errorElement);
}

/**
 * Clear field validation error
 */
function clearFieldError(field) {
    field.classList.remove('error');
    
    const errorElement = field.parentNode.querySelector('.field-error');
    if (errorElement) {
        errorElement.remove();
    }
}

/**
 * UI Helper Functions
 */

/**
 * Show/hide loading state
 */
function setLoadingState(element, loading = true) {
    if (!element) return;
    
    if (loading) {
        element.classList.add('loading');
        const existingSpinner = element.querySelector('.loading-placeholder');
        if (!existingSpinner) {
            element.innerHTML = `
                <div class="loading-placeholder">
                    <div class="spinner"></div>
                    <p>Laden...</p>
                </div>
            `;
        }
    } else {
        element.classList.remove('loading');
    }
}

/**
 * Show toast notification
 */
function showToast(type, title, message, duration = CONFIG.TOAST_DURATION) {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-header">
            <h4 class="toast-title">${title}</h4>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
        <div class="toast-body">${message}</div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, duration);
    }
    
    return toast;
}

/**
 * Get or create toast container
 */
function getOrCreateToastContainer() {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Show modal
 */
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.classList.add('modal-open');
        
        // Focus trap
        const focusableElements = modal.querySelectorAll('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        }
    }
}

/**
 * Close modal
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.body.classList.remove('modal-open');
    }
}

/**
 * Close modal when clicking outside
 */
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('show');
        document.body.classList.remove('modal-open');
    }
});

/**
 * Close modal with Escape key
 */
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            openModal.classList.remove('show');
            document.body.classList.remove('modal-open');
        }
    }
});

/**
 * Debounce function for search inputs
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function for scroll/resize events
 */
function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        if (navigator.clipboard) {
            await navigator.clipboard.writeText(text);
            showToast('success', 'Kopiert', 'Text wurde in die Zwischenablage kopiert');
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showToast('success', 'Kopiert', 'Text wurde in die Zwischenablage kopiert');
        }
        return true;
    } catch (error) {
        showToast('error', 'Fehler', 'Text konnte nicht kopiert werden');
        return false;
    }
}

/**
 * Download file from URL
 */
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Get status configuration for display
 */
function getStatusConfig(type, status) {
    const configs = {
        'printer': CONFIG.PRINTER_STATUS,
        'job': CONFIG.JOB_STATUS,
        'file': CONFIG.FILE_STATUS
    };
    
    return configs[type]?.[status] || {
        label: status,
        icon: '❓',
        class: 'status-unknown'
    };
}

/**
 * Create status badge HTML
 */
function createStatusBadge(type, status) {
    const config = getStatusConfig(type, status);
    return `<span class="status-badge ${config.class}">${config.icon} ${config.label}</span>`;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return unsafe;
    
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Generate unique ID
 */
function generateId(prefix = 'id') {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Local Storage helpers with error handling
 */
const Storage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            window.ErrorHandler?.handleLocalStorageError(error, { operation: 'save', key });
            return false;
        }
    },
    
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            window.ErrorHandler?.handleLocalStorageError(error, { operation: 'read', key });
            return defaultValue;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            window.ErrorHandler?.handleLocalStorageError(error, { operation: 'remove', key });
            return false;
        }
    },
    
    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            window.ErrorHandler?.handleLocalStorageError(error, { operation: 'clear' });
            return false;
        }
    }
};

/**
 * URL parameter helpers
 */
const URLParams = {
    get(name) {
        const params = new URLSearchParams(window.location.search);
        return params.get(name);
    },
    
    set(name, value) {
        const url = new URL(window.location);
        url.searchParams.set(name, value);
        window.history.replaceState({}, '', url);
    },
    
    remove(name) {
        const url = new URL(window.location);
        url.searchParams.delete(name);
        window.history.replaceState({}, '', url);
    },
    
    getAll() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    }
};

/**
 * Initialize system time display
 */
function initSystemTime() {
    const timeElement = document.getElementById('systemTime');
    if (!timeElement) return;
    
    function updateTime() {
        const now = new Date();
        timeElement.textContent = now.toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    updateTime();
    setInterval(updateTime, 1000);
}

// Initialize system time when DOM loads
document.addEventListener('DOMContentLoaded', initSystemTime);

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatDate, formatTime, formatDateTime, getRelativeTime, formatDuration,
        formatNumber, formatCurrency, formatPercentage, formatBytes, formatWeight,
        isValidIP, isValidEmail, validateForm,
        setLoadingState, showToast, showModal, closeModal,
        debounce, throttle, copyToClipboard, downloadFile,
        getStatusConfig, createStatusBadge, escapeHtml, generateId,
        Storage, URLParams
    };
}