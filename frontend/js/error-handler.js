/**
 * Comprehensive Error Handling System for Printernizer Frontend
 * Replaces console.error calls with proper error tracking and user feedback
 */

class ErrorHandler {
    constructor() {
        this.errors = [];
        this.maxErrors = 100; // Keep last 100 errors
        this.errorReporting = {
            enabled: true,
            endpoint: '/api/v1/errors/report',
            batchSize: 10,
            batchTimeout: 5000
        };
        this.pendingReports = [];
        this.init();
    }

    init() {
        // Setup global error handlers
        this.setupGlobalErrorHandlers();
        
        // Initialize error display elements
        this.createErrorDisplay();
        
        // Setup periodic error reporting if enabled
        if (this.errorReporting.enabled) {
            this.setupBatchReporting();
        }
    }

    setupGlobalErrorHandlers() {
        // Global JavaScript error handler
        window.addEventListener('error', (event) => {
            this.handleError('javascript', event.error || new Error(event.message), {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError('promise', event.reason, {
                type: 'unhandled_promise_rejection'
            });
        });
    }

    createErrorDisplay() {
        // Create error notification container if it doesn't exist
        if (!document.getElementById('error-notifications')) {
            const container = document.createElement('div');
            container.id = 'error-notifications';
            container.className = 'error-notifications';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
    }

    handleError(category, error, context = {}, userMessage = null) {
        const errorInfo = {
            id: this.generateErrorId(),
            timestamp: new Date().toISOString(),
            category,
            message: error?.message || error?.toString() || 'Unknown error',
            stack: error?.stack,
            context,
            userAgent: navigator.userAgent,
            url: window.location.href,
            severity: this.determineSeverity(category, error),
            userMessage: userMessage || this.generateUserMessage(category, error)
        };

        // Store error
        this.storeError(errorInfo);

        // Log to console for development
        if (this.isDevelopment()) {
            if (typeof Logger !== 'undefined') {
                Logger.group(`🚨 ${errorInfo.category.toUpperCase()} ERROR`);
                Logger.error('Message:', errorInfo.message);
                Logger.error('Context:', errorInfo.context);
                if (errorInfo.stack) {
                    Logger.error('Stack:', errorInfo.stack);
                }
                Logger.groupEnd();
            } else {
                // Fallback if Logger not available yet
                console.group(`🚨 ${errorInfo.category.toUpperCase()} ERROR`);
                console.error('Message:', errorInfo.message);
                console.error('Context:', errorInfo.context);
                if (errorInfo.stack) {
                    console.error('Stack:', errorInfo.stack);
                }
                console.groupEnd();
            }
        }

        // Show user notification for critical errors
        if (errorInfo.severity === 'critical' || errorInfo.severity === 'high') {
            this.showUserNotification(errorInfo);
        }

        // Add to reporting queue
        if (this.errorReporting.enabled) {
            this.queueForReporting(errorInfo);
        }

        return errorInfo;
    }

    // Specific error handlers for different categories
    handleWebSocketError(error, context = {}) {
        const userMessage = "Connection to server lost. Trying to reconnect...";
        return this.handleError('websocket', error, context, userMessage);
    }

    handleApiError(error, context = {}) {
        const userMessage = this.getApiErrorMessage(error, context);
        return this.handleError('api', error, context, userMessage);
    }

    handleLocalStorageError(error, context = {}) {
        const userMessage = "Local storage error. Some settings might not be saved.";
        return this.handleError('localStorage', error, context, userMessage);
    }

    handleSettingsError(error, context = {}) {
        const userMessage = "Settings operation failed. Please try again.";
        return this.handleError('settings', error, context, userMessage);
    }

    handleFileOperationError(error, context = {}) {
        const userMessage = `File operation failed: ${context.operation || 'unknown operation'}`;
        return this.handleError('fileOperation', error, context, userMessage);
    }

    handlePrinterError(error, context = {}) {
        const userMessage = `Printer operation failed: ${context.operation || 'unknown operation'}`;
        return this.handleError('printer', error, context, userMessage);
    }

    getApiErrorMessage(error, context) {
        const status = context.status || error.status;
        const endpoint = context.endpoint || 'API';
        
        switch (status) {
            case 400:
                return `Invalid request to ${endpoint}. Please check your input.`;
            case 401:
                return "Authentication required. Please refresh the page.";
            case 403:
                return "Access denied. You don't have permission for this operation.";
            case 404:
                return `${endpoint} not found. This feature might not be available.`;
            case 429:
                return "Too many requests. Please wait a moment and try again.";
            case 500:
                return `Server error in ${endpoint}. Please try again later.`;
            case 503:
                return "Service temporarily unavailable. Please try again later.";
            default:
                return `Request to ${endpoint} failed. Please try again.`;
        }
    }

    determineSeverity(category, error) {
        // Define severity based on category and error type
        const criticalCategories = ['websocket', 'api'];
        const highSeverityErrors = ['NetworkError', 'TypeError', 'ReferenceError'];
        
        if (criticalCategories.includes(category)) {
            return 'critical';
        }
        
        if (error?.name && highSeverityErrors.includes(error.name)) {
            return 'high';
        }
        
        if (category === 'localStorage' || category === 'settings') {
            return 'medium';
        }
        
        return 'low';
    }

    generateUserMessage(category, error) {
        const messages = {
            javascript: "An unexpected error occurred. Please refresh the page.",
            promise: "An operation didn't complete successfully. Please try again.",
            websocket: "Connection problem. Attempting to reconnect...",
            api: "Server request failed. Please try again.",
            localStorage: "Local storage issue. Some data might not be saved.",
            settings: "Settings operation failed. Please try again.",
            fileOperation: "File operation failed. Please try again.",
            printer: "Printer operation failed. Please check printer status."
        };
        
        return messages[category] || "An error occurred. Please try again.";
    }

    generateErrorId() {
        return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    storeError(errorInfo) {
        this.errors.unshift(errorInfo);
        
        // Keep only the most recent errors
        if (this.errors.length > this.maxErrors) {
            this.errors = this.errors.slice(0, this.maxErrors);
        }
    }

    showUserNotification(errorInfo) {
        const container = document.getElementById('error-notifications');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `error-notification severity-${errorInfo.severity}`;
        notification.style.cssText = `
            background: ${this.getSeverityColor(errorInfo.severity)};
            color: white;
            padding: 12px 16px;
            margin-bottom: 8px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            animation: slideIn 0.3s ease-out;
            cursor: pointer;
            position: relative;
        `;

        notification.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 4px;">
                ${this.getSeverityIcon(errorInfo.severity)} ${errorInfo.category.toUpperCase()} ERROR
            </div>
            <div style="font-size: 14px;">${escapeHtml(errorInfo.userMessage)}</div>
            <div style="position: absolute; top: 8px; right: 8px; cursor: pointer; font-size: 18px;" onclick="this.parentElement.remove()">×</div>
        `;

        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);

        // Add animation styles if not already present
        this.addAnimationStyles();
    }

    getSeverityColor(severity) {
        const colors = {
            low: '#6c757d',
            medium: '#ffc107',
            high: '#fd7e14',
            critical: '#dc3545'
        };
        return colors[severity] || colors.medium;
    }

    getSeverityIcon(severity) {
        const icons = {
            low: 'ℹ️',
            medium: '⚠️',
            high: '🚨',
            critical: '🔥'
        };
        return icons[severity] || icons.medium;
    }

    addAnimationStyles() {
        if (document.getElementById('error-handler-styles')) return;

        const style = document.createElement('style');
        style.id = 'error-handler-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }

    queueForReporting(errorInfo) {
        this.pendingReports.push(errorInfo);
        
        if (this.pendingReports.length >= this.errorReporting.batchSize) {
            this.sendErrorReports();
        }
    }

    setupBatchReporting() {
        setInterval(() => {
            if (this.pendingReports.length > 0) {
                this.sendErrorReports();
            }
        }, this.errorReporting.batchTimeout);
    }

    async sendErrorReports() {
        if (this.pendingReports.length === 0) return;

        const reports = [...this.pendingReports];
        this.pendingReports = [];

        try {
            await fetch(this.errorReporting.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    errors: reports,
                    session: this.getSessionInfo()
                })
            });
        } catch (error) {
            // If reporting fails, put errors back in queue
            this.pendingReports.unshift(...reports);
            
            // Don't create infinite loop by calling handleError here
            if (this.isDevelopment()) {
                if (typeof Logger !== 'undefined') {
                    Logger.warn('Error reporting failed:', error);
                } else {
                    console.warn('Error reporting failed:', error);
                }
            }
        }
    }

    getSessionInfo() {
        return {
            sessionId: this.getSessionId(),
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            }
        };
    }

    getSessionId() {
        let sessionId = localStorage.getItem('printernizer_session_id');
        if (!sessionId) {
            sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            try {
                localStorage.setItem('printernizer_session_id', sessionId);
            } catch (e) {
                // If localStorage fails, use a temporary session ID
                sessionId = `temp_${Date.now()}`;
            }
        }
        return sessionId;
    }

    isDevelopment() {
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               window.location.hostname.includes('dev');
    }

    // Public API methods
    getErrors(category = null, limit = 20) {
        let filteredErrors = this.errors;
        
        if (category) {
            filteredErrors = this.errors.filter(error => error.category === category);
        }
        
        return filteredErrors.slice(0, limit);
    }

    clearErrors() {
        this.errors = [];
    }

    enableReporting(endpoint = null) {
        this.errorReporting.enabled = true;
        if (endpoint) {
            this.errorReporting.endpoint = endpoint;
        }
    }

    disableReporting() {
        this.errorReporting.enabled = false;
    }

    // Utility method to wrap async functions with error handling
    wrapAsync(asyncFn, context = {}) {
        return async (...args) => {
            try {
                return await asyncFn(...args);
            } catch (error) {
                this.handleError('async', error, { ...context, function: asyncFn.name });
                throw error; // Re-throw to maintain normal error flow
            }
        };
    }
}

// Create global error handler instance
window.ErrorHandler = new ErrorHandler();

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}