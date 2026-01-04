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

    // Use toFixed(2) to ensure exactly 2 decimal places for file sizes
    const value = (bytes / Math.pow(k, i)).toFixed(2);
    return `${value} ${sizes[i]}`;
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
 * Active toasts tracking for deduplication
 */
const activeToasts = new Map();

/**
 * Show toast notification with deduplication support
 * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
 * @param {string} title - Toast title
 * @param {string} message - Toast message
 * @param {number} duration - Auto-dismiss duration in ms (0 = no auto-dismiss)
 * @param {object} options - Additional options
 * @param {string} options.uniqueKey - Unique key for deduplication (defaults to type+title)
 * @param {string} options.deduplicateMode - 'allow', 'prevent', 'update' (default: 'update')
 * @param {number} options.cooldown - Minimum time between same notification (ms)
 */
function showToast(type, title, message, duration = CONFIG.TOAST_DURATION, options = {}) {
    const {
        uniqueKey = `${type}:${title}`,
        deduplicateMode = 'update',
        cooldown = 0
    } = options;

    // Check if toast with same key already exists
    const existingToast = activeToasts.get(uniqueKey);

    if (existingToast) {
        const timeSinceCreated = Date.now() - existingToast.timestamp;

        // Apply cooldown check
        if (cooldown > 0 && timeSinceCreated < cooldown) {
            return existingToast.element;
        }

        // Handle deduplication modes
        if (deduplicateMode === 'prevent') {
            // Don't create new toast, return existing
            return existingToast.element;
        } else if (deduplicateMode === 'update') {
            // Update existing toast content
            updateToast(existingToast.element, type, title, message);

            // Reset auto-dismiss timer
            if (existingToast.timeoutId) {
                clearTimeout(existingToast.timeoutId);
            }

            if (duration > 0) {
                const timeoutId = setTimeout(() => {
                    removeToast(existingToast.element, uniqueKey);
                }, duration);
                existingToast.timeoutId = timeoutId;
            }

            // Update timestamp
            existingToast.timestamp = Date.now();

            return existingToast.element;
        }
        // deduplicateMode === 'allow' - create new toast (fall through)
    }

    const toastContainer = getOrCreateToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.dataset.uniqueKey = uniqueKey;
    toast.innerHTML = `
        <div class="toast-header">
            <h4 class="toast-title">${escapeHtml(title)}</h4>
            <button class="toast-close">&times;</button>
        </div>
        <div class="toast-body">${escapeHtml(message)}</div>
    `;

    // Add close button handler
    const closeButton = toast.querySelector('.toast-close');
    closeButton.addEventListener('click', () => {
        removeToast(toast, uniqueKey);
    });

    toastContainer.appendChild(toast);

    // Track active toast
    const toastData = {
        element: toast,
        timestamp: Date.now(),
        timeoutId: null
    };

    // Auto-remove after duration
    if (duration > 0) {
        const timeoutId = setTimeout(() => {
            removeToast(toast, uniqueKey);
        }, duration);
        toastData.timeoutId = timeoutId;
    }

    activeToasts.set(uniqueKey, toastData);

    return toast;
}

/**
 * Update existing toast content
 */
function updateToast(toast, type, title, message) {
    // Update toast type class
    toast.className = `toast toast-${type}`;

    // Update title
    const titleElement = toast.querySelector('.toast-title');
    if (titleElement) {
        titleElement.textContent = title;
    }

    // Update message
    const bodyElement = toast.querySelector('.toast-body');
    if (bodyElement) {
        bodyElement.textContent = message;
    }

    // Add flash animation to indicate update
    toast.classList.add('toast-updated');
    setTimeout(() => {
        toast.classList.remove('toast-updated');
    }, 300);
}

/**
 * Remove toast and clean up tracking
 */
function removeToast(toast, uniqueKey) {
    if (toast.parentElement) {
        toast.remove();
    }

    // Clean up tracking
    const toastData = activeToasts.get(uniqueKey);
    if (toastData?.timeoutId) {
        clearTimeout(toastData.timeoutId);
    }
    activeToasts.delete(uniqueKey);
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
 * Navigate to settings page and open specific tab with modal overlay option
 * @param {string} settingsTab - Tab ID to open (e.g., 'timelapse', 'library')
 * @param {string} sourcePage - Optional page name to show in breadcrumb
 * @param {boolean} useModal - If true, show settings in modal overlay instead of navigating
 */
function openPageSettings(settingsTab, sourcePage = null, useModal = true) {
    if (useModal) {
        // Show settings in modal overlay
        showSettingsModal(settingsTab, sourcePage);
    } else {
        // Navigate to settings page
        if (sourcePage) {
            // Store source page and current hash for breadcrumb
            sessionStorage.setItem('settingsSourcePage', sourcePage);
            sessionStorage.setItem('settingsSourceHash', window.location.hash);
        }

        window.location.hash = '#settings';

        // Wait for settings page to load, then switch to specific tab and update breadcrumb
        setTimeout(() => {
            if (window.settingsManager && settingsManager.switchTab) {
                settingsManager.switchTab(settingsTab);
            }
            updateSettingsBreadcrumb();
        }, 150);
    }
}

/**
 * Show settings in a modal overlay
 * @param {string} settingsTab - Tab ID to open
 * @param {string} sourcePage - Source page name for context
 */
function showSettingsModal(settingsTab, sourcePage) {
    const modal = document.getElementById('settingsModal');
    if (!modal) {
        Logger.error('Settings modal not found');
        return;
    }

    // Store current tab and source page
    modal.dataset.currentTab = settingsTab;
    modal.dataset.sourcePage = sourcePage || '';

    // Update modal title with breadcrumb if source page provided
    const modalTitle = modal.querySelector('.settings-modal-title');
    if (modalTitle && sourcePage) {
        modalTitle.innerHTML = `
            <button class="breadcrumb-back" onclick="closeSettingsModal()">
                ← Zurück zu ${escapeHtml(sourcePage)}
            </button>
            <span class="breadcrumb-separator">/</span>
            <span>Einstellungen</span>
        `;
    }

    // Load settings content into modal
    loadSettingsIntoModal(settingsTab);

    // Show modal
    showModal('settingsModal');
}

/**
 * Load settings tab content into modal
 * @param {string} settingsTab - Tab ID to load
 */
function loadSettingsIntoModal(settingsTab) {
    const modalBody = document.querySelector('#settingsModal .settings-modal-body');
    if (!modalBody) return;

    // Clone the settings tab content
    const tabPane = document.getElementById(`${settingsTab}-tab`);
    if (!tabPane) {
        Logger.error(`Settings tab not found: ${settingsTab}`);
        return;
    }

    // Clear and populate modal body
    modalBody.innerHTML = '';
    const clonedContent = tabPane.cloneNode(true);
    clonedContent.id = `modal-${settingsTab}-tab`;
    clonedContent.classList.add('active');
    modalBody.appendChild(clonedContent);

    // Update tab selector in modal
    updateModalTabSelector(settingsTab);
}

/**
 * Update the tab selector in modal header
 * @param {string} activeTab - Currently active tab
 */
function updateModalTabSelector(activeTab) {
    const tabSelector = document.querySelector('#settingsModal .modal-tab-selector');
    if (!tabSelector) return;

    const tabs = [
        { id: 'general', icon: '⚙️', label: 'Allgemein' },
        { id: 'jobs', icon: '🖨️', label: 'Aufträge & G-Code' },
        { id: 'library', icon: '🗄️', label: 'Bibliothek' },
        { id: 'files', icon: '📁', label: 'Uploads & Downloads' },
        { id: 'timelapse', icon: '🎬', label: 'Timelapse' },
        { id: 'watch', icon: '👁️', label: 'Überwachung' },
        { id: 'system', icon: '💻', label: 'System' }
    ];

    const options = tabs.map(tab => {
        const selected = tab.id === activeTab ? 'selected' : '';
        return `<option value="${tab.id}" ${selected}>${tab.icon} ${tab.label}</option>`;
    }).join('');

    tabSelector.innerHTML = options;
}

/**
 * Switch tab in settings modal
 * @param {string} tabId - Tab to switch to
 */
function switchModalSettingsTab(tabId) {
    const modal = document.getElementById('settingsModal');
    if (!modal) return;

    modal.dataset.currentTab = tabId;
    loadSettingsIntoModal(tabId);
}

/**
 * Close settings modal
 */
function closeSettingsModal() {
    closeModal('settingsModal');
}

/**
 * Navigate back from settings page to source page
 */
function navigateBackFromSettings() {
    const sourcePage = sessionStorage.getItem('settingsSourcePage');
    const sourceHash = sessionStorage.getItem('settingsSourceHash');

    // Clear stored values
    sessionStorage.removeItem('settingsSourcePage');
    sessionStorage.removeItem('settingsSourceHash');

    if (sourceHash) {
        window.location.hash = sourceHash;
    } else if (sourcePage) {
        // Fallback to page name if hash not stored
        window.location.hash = `#${sourcePage.toLowerCase()}`;
    } else {
        // Default to dashboard
        window.location.hash = '#dashboard';
    }

    // Hide breadcrumb
    const breadcrumb = document.getElementById('settingsBreadcrumb');
    if (breadcrumb) {
        breadcrumb.style.display = 'none';
    }
}

/**
 * Show breadcrumb in settings page if navigating from another page
 * Should be called when settings page loads
 */
function updateSettingsBreadcrumb() {
    const sourcePage = sessionStorage.getItem('settingsSourcePage');
    const breadcrumb = document.getElementById('settingsBreadcrumb');

    if (!breadcrumb) return;

    if (sourcePage) {
        const backButton = breadcrumb.querySelector('.breadcrumb-back');
        if (backButton) {
            backButton.innerHTML = `← Zurück zu ${escapeHtml(sourcePage)}`;
        }
        breadcrumb.style.display = 'block';
    } else {
        breadcrumb.style.display = 'none';
    }
}

/**
 * Save settings from modal
 */
async function saveModalSettings() {
    const modal = document.getElementById('settingsModal');
    const currentTab = modal?.dataset.currentTab;

    if (!currentTab) {
        showToast('error', 'Fehler', 'Keine Einstellungen zum Speichern gefunden');
        return;
    }

    try {
        // Get form data from modal
        const modalBody = document.querySelector('#settingsModal .settings-modal-body');
        const forms = modalBody.querySelectorAll('form');

        const settingsData = {};
        forms.forEach(form => {
            const formData = new FormData(form);
            for (const [key, value] of formData.entries()) {
                settingsData[key] = value;
            }
        });

        // Save settings via API
        const response = await fetch(`${CONFIG.API_BASE_URL}/settings`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settingsData)
        });

        if (response.ok) {
            showToast('success', 'Gespeichert', 'Einstellungen wurden erfolgreich gespeichert');

            // Reload settings in main page if needed
            if (window.settingsManager) {
                await settingsManager.loadSettings();
            }

            // Close modal after brief delay
            setTimeout(() => closeSettingsModal(), 500);
        } else {
            throw new Error('Failed to save settings');
        }
    } catch (error) {
        Logger.error('Error saving settings:', error);
        showToast('error', 'Fehler', 'Einstellungen konnten nicht gespeichert werden');
    }
}

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
        label: escapeHtml(status),  // Escape unknown status values for safety
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
 * Security Utilities for XSS Prevention
 */

/**
 * Escape HTML to prevent XSS attacks
 * Use this before inserting user-generated content into HTML
 * @param {string} unsafe - Unsafe string that may contain HTML
 * @returns {string} - HTML-escaped string
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
 * Sanitize HTML attributes to prevent XSS in attributes
 * Use this for href, src, and other attribute values
 * @param {string} unsafe - Unsafe attribute value
 * @returns {string} - Sanitized attribute value
 */
function sanitizeAttribute(unsafe) {
    if (typeof unsafe !== 'string') return '';

    // Remove javascript:, data:, and vbscript: protocols
    const dangerous = /^(javascript|data|vbscript):/i;
    if (dangerous.test(unsafe.trim())) {
        return '';
    }

    return escapeHtml(unsafe);
}

/**
 * Sanitize URL to prevent XSS via URL schemes
 * @param {string} url - URL to sanitize
 * @returns {string} - Sanitized URL or empty string if dangerous
 */
function sanitizeUrl(url) {
    if (typeof url !== 'string') return '';

    const trimmed = url.trim().toLowerCase();

    // Allow only safe protocols
    const safeProtocols = /^(https?|ftp|mailto):/i;
    const dangerous = /^(javascript|data|vbscript):/i;

    if (dangerous.test(trimmed)) {
        return '';
    }

    // If it has a protocol, it must be safe
    if (trimmed.includes(':') && !safeProtocols.test(trimmed)) {
        return '';
    }

    return url;
}

/**
 * Create a safe DOM element with escaped content
 * Preferred over innerHTML for dynamic content
 * @param {string} tag - HTML tag name
 * @param {object} attributes - Element attributes (will be sanitized)
 * @param {string|Node|Array} content - Element content (strings will be escaped)
 * @returns {HTMLElement} - Safe DOM element
 */
function createSafeElement(tag, attributes = {}, content = null) {
    const element = document.createElement(tag);

    // Set attributes safely
    for (const [key, value] of Object.entries(attributes)) {
        if (key === 'href' || key === 'src') {
            const safeUrl = sanitizeUrl(value);
            if (safeUrl) {
                element.setAttribute(key, safeUrl);
            }
        } else if (key === 'class' || key === 'className') {
            element.className = value;
        } else if (key === 'style') {
            if (typeof value === 'object') {
                Object.assign(element.style, value);
            } else {
                element.setAttribute('style', value);
            }
        } else {
            element.setAttribute(key, sanitizeAttribute(value));
        }
    }

    // Set content safely
    if (content !== null) {
        if (Array.isArray(content)) {
            content.forEach(item => {
                if (typeof item === 'string') {
                    element.appendChild(document.createTextNode(item));
                } else if (item instanceof Node) {
                    element.appendChild(item);
                }
            });
        } else if (typeof content === 'string') {
            element.textContent = content; // Automatically escaped
        } else if (content instanceof Node) {
            element.appendChild(content);
        }
    }

    return element;
}

/**
 * Safely set innerHTML with HTML escaping
 * Use only when you need to insert already-escaped HTML
 * @param {HTMLElement} element - Target element
 * @param {string} html - HTML string (should be pre-escaped or trusted)
 * @param {boolean} escape - Whether to escape the HTML (default: true)
 */
function safeSetInnerHTML(element, html, escape = true) {
    if (!element) return;

    if (escape) {
        element.textContent = html; // textContent auto-escapes
    } else {
        // Only use this with trusted, pre-escaped content
        element.innerHTML = html;
    }
}

/**
 * Truncate text to specified length with ellipsis
 */
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + '...';
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

/**
 * Fetch and display application version in footer
 */
async function loadAppVersion() {
    Logger.debug('[Version] Loading app version...');

    const versionElement = document.getElementById('appVersion');
    if (!versionElement) {
        Logger.error('[Version] ERROR: appVersion element not found in DOM');
        Logger.debug('[Version] Available elements with "version":',
            Array.from(document.querySelectorAll('[id*="version"]')).map(el => el.id));
        return;
    }

    Logger.debug('[Version] Found appVersion element:', versionElement);

    try {
        Logger.debug('[Version] Fetching health endpoint...');
        const response = await fetch(`${CONFIG.API_BASE_URL}/health`, {
            cache: 'no-cache' // Force fresh data
        });

        Logger.debug('[Version] Response status:', response.status, response.statusText);

        if (response.ok) {
            const data = await response.json();
            Logger.debug('[Version] Health data received:', data);

            const version = data.version || 'unknown';
            Logger.debug('[Version] Setting version to:', version);
            versionElement.textContent = version;
            Logger.debug('[Version] Version element content now:', versionElement.textContent);

            // Store version globally
            window.printernizer = window.printernizer || {};
            window.printernizer.version = version;

            // Check for updates
            checkForUpdates(version);
        } else {
            Logger.error('[Version] Health endpoint returned non-OK status:', response.status);
            versionElement.textContent = 'error';
        }
    } catch (error) {
        Logger.error('[Version] Failed to load version:', error);
        versionElement.textContent = 'error';
    }
}

/**
 * Check for available updates from GitHub
 */
async function checkForUpdates(currentVersion) {
    Logger.debug('[Update Check] Checking for updates...');

    const updateStatusElement = document.getElementById('updateStatus');
    if (!updateStatusElement) {
        Logger.error('[Update Check] updateStatus element not found');
        return;
    }

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/update-check`, {
            cache: 'no-cache'
        });

        if (response.ok) {
            const data = await response.json();
            Logger.debug('[Update Check] Update check data:', data);

            if (data.check_failed) {
                Logger.warn('[Update Check] Update check failed:', data.error_message);
                // Don't show anything if check failed
                updateStatusElement.textContent = '';
                return;
            }

            if (data.update_available) {
                Logger.debug('[Update Check] Update available:', data.latest_version);
                const releaseUrl = sanitizeUrl(data.release_url || 'https://github.com/schmacka/printernizer/releases/latest');
                const version = escapeHtml(data.latest_version);
                updateStatusElement.innerHTML = `<a href="${releaseUrl}" target="_blank" title="Update available: v${version}">Update available</a>`;
                updateStatusElement.className = 'update-status outdated';

                // Show a notification
                showToast(
                    `New version available: v${data.latest_version}`,
                    'info',
                    {
                        duration: 10000,
                        action: {
                            label: 'View Release',
                            callback: () => {
                                window.open(data.release_url || 'https://github.com/schmacka/printernizer/releases/latest', '_blank');
                            }
                        }
                    }
                );
            } else {
                Logger.debug('[Update Check] Version is current');
                updateStatusElement.textContent = 'Up to date';
                updateStatusElement.className = 'update-status current';
            }
        } else {
            Logger.error('[Update Check] Update check endpoint returned non-OK status:', response.status);
        }
    } catch (error) {
        Logger.error('[Update Check] Failed to check for updates:', error);
        // Silently fail - don't show error to user for update check
    }
}

// Make loadAppVersion available globally
window.loadAppVersion = loadAppVersion;

/**
 * Simplified notification wrapper for backward compatibility
 * Maps simple notification calls to the full showToast system with deduplication
 *
 * @param {string} message - The notification message
 * @param {string} type - Notification type: 'success', 'error', 'warning', 'info'
 */
function showNotification(message, type = 'info') {
    // Map type to title
    const titles = {
        success: 'Erfolg',
        error: 'Fehler',
        warning: 'Warnung',
        info: 'Information'
    };

    const title = titles[type] || titles.info;

    // Generate a hash of the message for deduplication
    const messageHash = hashString(message);

    // Use existing showToast with deduplication based on type+message
    return showToast(type, title, message, CONFIG.TOAST_DURATION, {
        uniqueKey: `notification:${type}:${messageHash}`,
        deduplicateMode: 'update',
        cooldown: 3000  // Prevent same notification within 3 seconds
    });
}

/**
 * Simple string hash for notification deduplication
 * @param {string} str - String to hash
 * @returns {number} - Hash value
 */
function hashString(str) {
    let hash = 0;
    if (!str || str.length === 0) return hash;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash);
}

// Make showNotification available globally
window.showNotification = showNotification;

// Initialize system time, version info, and modal helpers when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    initSystemTime();
    loadAppVersion();
    initializeJobModalControls();
});

/**
 * Job Modal Functions
 */
let jobModalControlsInitialized = false;

function initializeJobModalControls() {
    if (jobModalControlsInitialized) {
        return;
    }

    if (!document.getElementById('jobModal')) {
        return;
    }

    const businessCheckbox = document.getElementById('isBusiness');
    const materialCostInput = document.getElementById('materialCost');

    if (businessCheckbox) {
        businessCheckbox.addEventListener('change', syncBusinessJobFields);
    }

    if (materialCostInput) {
        materialCostInput.addEventListener('input', calculateVAT);
    }

    jobModalControlsInitialized = true;
    syncBusinessJobFields();
}

function syncBusinessJobFields() {
    const businessCheckbox = document.getElementById('isBusiness');
    const customerNameGroup = document.getElementById('customerNameGroup');
    const costCalculationGroup = document.getElementById('costCalculationGroup');
    const isChecked = Boolean(businessCheckbox?.checked);

    if (customerNameGroup) {
        customerNameGroup.style.display = isChecked ? 'block' : 'none';
    }

    if (costCalculationGroup) {
        costCalculationGroup.style.display = isChecked ? 'block' : 'none';
    }

    if (isChecked) {
        calculateVAT();
    } else {
        resetVatCalculationDisplay();
    }
}

function resetVatCalculationDisplay() {
    const netPriceElement = document.getElementById('netPrice');
    const vatAmountElement = document.getElementById('vatAmount');
    const grossTotalElement = document.getElementById('grossTotal');

    if (netPriceElement) netPriceElement.textContent = '€0.00';
    if (vatAmountElement) vatAmountElement.textContent = '€0.00';
    if (grossTotalElement) grossTotalElement.textContent = '€0.00';
}

function showCreateJobModal() {
    initializeJobModalControls();
    syncBusinessJobFields();
    showModal('jobModal');
}

/**
 * Calculate and display VAT for business jobs
 */
function calculateVAT() {
    const materialCostInput = document.getElementById('materialCost');
    const netPriceElement = document.getElementById('netPrice');
    const vatAmountElement = document.getElementById('vatAmount');
    const grossTotalElement = document.getElementById('grossTotal');
    
    if (!materialCostInput || !netPriceElement || !vatAmountElement || !grossTotalElement) {
        return;
    }
    
    const VAT_RATE = 0.19; // 19% for Germany
    const netPrice = parseFloat(materialCostInput.value) || 0;
    const vatAmount = netPrice * VAT_RATE;
    const grossTotal = netPrice + vatAmount;
    
    // Format as EUR currency
    netPriceElement.textContent = '€' + netPrice.toFixed(2);
    vatAmountElement.textContent = '€' + vatAmount.toFixed(2);
    grossTotalElement.textContent = '€' + grossTotal.toFixed(2);
}

function closeJobModal() {
    const modal = document.getElementById('jobModal');
    if (!modal) {
        return;
    }

    closeModal('jobModal');

    const form = document.getElementById('createJobForm');
    if (form) {
        form.reset();
    }

    syncBusinessJobFields();
}

// Make modal functions available globally
window.showCreateJobModal = showCreateJobModal;
window.closeJobModal = closeJobModal;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatDate, formatTime, formatDateTime, getRelativeTime, formatDuration,
        formatNumber, formatCurrency, formatPercentage, formatBytes, formatWeight,
        isValidIP, isValidEmail, validateForm,
        setLoadingState, showToast, showNotification, showModal, closeModal,
        debounce, throttle, copyToClipboard, downloadFile,
        getStatusConfig, createStatusBadge, escapeHtml, truncateText, generateId,
        Storage, URLParams,
        showCreateJobModal, closeJobModal
    };
}