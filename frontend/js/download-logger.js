/**
 * Download Logger System
 * Comprehensive logging for downloads, thumbnails, and system events
 */

class DownloadLogger {
    constructor() {
        this.logs = [];
        this.maxLogs = 10000; // Keep last 10k log entries
        this.storageKey = 'printernizer_download_logs';
        this.sessionId = this.generateSessionId();
        this.logLevels = {
            'debug': 0,
            'info': 1,
            'warn': 2,
            'error': 3,
            'critical': 4
        };
        this.currentLogLevel = 1; // Info and above
    }

    /**
     * Initialize the logger
     */
    async init() {
        Logger.debug('📝 Initializing Download Logger');

        // Load existing logs from localStorage
        await this.loadLogs();

        // Log session start
        this.log('system', 'Download Logger initialized', {
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent
        });

        // Auto-save logs every 30 seconds
        setInterval(() => {
            this.saveLogs();
        }, 30000);

        // Cleanup old logs daily
        setInterval(() => {
            this.cleanupOldLogs();
        }, 24 * 60 * 60 * 1000); // 24 hours
    }

    /**
     * Generate unique session ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Main logging method
     */
    log(category, message, data = {}, level = 'info') {
        if (this.logLevels[level] < this.currentLogLevel) {
            return; // Skip if below current log level
        }

        const logEntry = {
            id: this.generateLogId(),
            sessionId: this.sessionId,
            timestamp: new Date(),
            category,
            level,
            message,
            data: { ...data },
            url: window.location.href,
            userAgent: navigator.userAgent.substring(0, 100) // Truncate for storage
        };

        this.logs.push(logEntry);

        // Trim logs if too many
        if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(-this.maxLogs);
        }

        // Console output for debugging
        this.outputToConsole(logEntry);

        // Auto-save critical errors immediately
        if (level === 'critical' || level === 'error') {
            this.saveLogs();
        }
    }

    /**
     * Generate unique log ID
     */
    generateLogId() {
        return 'log_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
    }

    /**
     * Output log entry to console with appropriate formatting
     */
    outputToConsole(entry) {
        const prefix = `[${entry.level.toUpperCase()}] ${entry.category}:`;
        const message = `${prefix} ${entry.message}`;

        switch (entry.level) {
            case 'debug':
                Logger.debug(message, entry.data);
                break;
            case 'info':
                Logger.info(message, entry.data);
                break;
            case 'warn':
                Logger.warn(message, entry.data);
                break;
            case 'error':
            case 'critical':
                Logger.error(message, entry.data);
                break;
            default:
                Logger.info(message, entry.data);
        }
    }

    /**
     * Convenience methods for different log levels
     */
    debug(category, message, data = {}) {
        this.log(category, message, data, 'debug');
    }

    info(category, message, data = {}) {
        this.log(category, message, data, 'info');
    }

    warn(category, message, data = {}) {
        this.log(category, message, data, 'warn');
    }

    error(category, message, data = {}) {
        this.log(category, message, data, 'error');
    }

    critical(category, message, data = {}) {
        this.log(category, message, data, 'critical');
    }

    /**
     * Specialized logging methods for common events
     */

    // Download events
    logDownloadStart(taskId, printerId, type) {
        this.log('download', `Download started: ${taskId}`, {
            taskId,
            printerId,
            type,
            event: 'download_start'
        });
    }

    logDownloadSuccess(taskId, printerId, result) {
        this.log('download', `Download completed: ${taskId}`, {
            taskId,
            printerId,
            result,
            event: 'download_success'
        });
    }

    logDownloadError(taskId, printerId, error, attempt) {
        this.log('download', `Download failed: ${taskId}`, {
            taskId,
            printerId,
            error: error.message || error,
            attempt,
            event: 'download_error'
        }, 'error');
    }

    // Thumbnail events
    logThumbnailStart(taskId, fileId, method) {
        this.log('thumbnail', `Thumbnail processing started: ${taskId}`, {
            taskId,
            fileId,
            method,
            event: 'thumbnail_start'
        });
    }

    logThumbnailSuccess(taskId, fileId, result) {
        this.log('thumbnail', `Thumbnail processing completed: ${taskId}`, {
            taskId,
            fileId,
            result,
            event: 'thumbnail_success'
        });
    }

    logThumbnailError(taskId, fileId, error, attempt) {
        this.log('thumbnail', `Thumbnail processing failed: ${taskId}`, {
            taskId,
            fileId,
            error: error.message || error,
            attempt,
            event: 'thumbnail_error'
        }, 'error');
    }

    // Printer events
    logPrinterStatusChange(printerId, oldStatus, newStatus, jobName) {
        this.log('printer', `Printer status changed: ${printerId}`, {
            printerId,
            oldStatus,
            newStatus,
            jobName,
            event: 'status_change'
        });
    }

    logJobStart(printerId, jobName) {
        this.log('printer', `Job started: ${printerId}`, {
            printerId,
            jobName,
            event: 'job_start'
        });
    }

    logJobComplete(printerId, jobName) {
        this.log('printer', `Job completed: ${printerId}`, {
            printerId,
            jobName,
            event: 'job_complete'
        });
    }

    // API events
    logApiRequest(endpoint, method, params) {
        this.debug('api', `API request: ${method} ${endpoint}`, {
            endpoint,
            method,
            params,
            event: 'api_request'
        });
    }

    logApiResponse(endpoint, method, status, responseTime) {
        this.debug('api', `API response: ${method} ${endpoint}`, {
            endpoint,
            method,
            status,
            responseTime,
            event: 'api_response'
        });
    }

    logApiError(endpoint, method, error) {
        this.error('api', `API error: ${method} ${endpoint}`, {
            endpoint,
            method,
            error: error.message || error,
            event: 'api_error'
        });
    }

    /**
     * Query methods for retrieving specific logs
     */

    // Get logs by category
    getLogsByCategory(category, limit = 100) {
        return this.logs
            .filter(log => log.category === category)
            .slice(-limit);
    }

    // Get logs by level
    getLogsByLevel(level, limit = 100) {
        return this.logs
            .filter(log => log.level === level)
            .slice(-limit);
    }

    // Get logs by date range
    getLogsByDateRange(startDate, endDate, limit = 1000) {
        return this.logs
            .filter(log => log.timestamp >= startDate && log.timestamp <= endDate)
            .slice(-limit);
    }

    // Get download history
    getDownloadHistory(days = 7) {
        const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
        return this.logs
            .filter(log =>
                log.category === 'download' &&
                log.timestamp >= startDate &&
                log.data.event === 'download_success'
            )
            .map(log => ({
                taskId: log.data.taskId,
                printerId: log.data.printerId,
                timestamp: log.timestamp,
                result: log.data.result
            }));
    }

    // Get error log
    getErrorLog(days = 7) {
        const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
        return this.logs
            .filter(log =>
                (log.level === 'error' || log.level === 'critical') &&
                log.timestamp >= startDate
            );
    }

    // Get performance metrics
    getPerformanceMetrics(days = 1) {
        const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
        const downloadLogs = this.logs.filter(log =>
            log.category === 'download' &&
            log.timestamp >= startDate
        );

        const thumbnailLogs = this.logs.filter(log =>
            log.category === 'thumbnail' &&
            log.timestamp >= startDate
        );

        return {
            downloads: {
                total: downloadLogs.filter(l => l.data.event === 'download_start').length,
                successful: downloadLogs.filter(l => l.data.event === 'download_success').length,
                failed: downloadLogs.filter(l => l.data.event === 'download_error').length
            },
            thumbnails: {
                total: thumbnailLogs.filter(l => l.data.event === 'thumbnail_start').length,
                successful: thumbnailLogs.filter(l => l.data.event === 'thumbnail_success').length,
                failed: thumbnailLogs.filter(l => l.data.event === 'thumbnail_error').length
            }
        };
    }

    /**
     * Get general statistics
     */
    getStats() {
        const last24h = new Date(Date.now() - 24 * 60 * 60 * 1000);
        const recentLogs = this.logs.filter(log => log.timestamp >= last24h);

        return {
            total: this.logs.length,
            recent: recentLogs.length,
            errors: recentLogs.filter(log => log.level === 'error' || log.level === 'critical').length,
            warnings: recentLogs.filter(log => log.level === 'warn').length,
            sessionId: this.sessionId,
            oldestLog: this.logs.length > 0 ? this.logs[0].timestamp : null,
            newestLog: this.logs.length > 0 ? this.logs[this.logs.length - 1].timestamp : null
        };
    }

    /**
     * Load logs from localStorage
     */
    async loadLogs() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                const parsedLogs = JSON.parse(stored);
                this.logs = parsedLogs.map(log => ({
                    ...log,
                    timestamp: new Date(log.timestamp) // Convert string back to Date
                }));
                Logger.debug(`📝 Loaded ${this.logs.length} existing log entries`);
            }
        } catch (error) {
            Logger.warn('Failed to load logs from localStorage', error);
            this.logs = [];
        }
    }

    /**
     * Save logs to localStorage
     */
    saveLogs() {
        try {
            const serializedLogs = this.logs.map(log => ({
                ...log,
                timestamp: log.timestamp.toISOString() // Convert Date to string
            }));
            localStorage.setItem(this.storageKey, JSON.stringify(serializedLogs));
        } catch (error) {
            Logger.warn('Failed to save logs to localStorage', error);
        }
    }

    /**
     * Clean up old logs (older than retention period)
     */
    cleanupOldLogs() {
        const retentionPeriod = 30 * 24 * 60 * 60 * 1000; // 30 days
        const cutoffDate = new Date(Date.now() - retentionPeriod);

        const beforeCount = this.logs.length;
        this.logs = this.logs.filter(log => log.timestamp >= cutoffDate);
        const afterCount = this.logs.length;

        if (beforeCount !== afterCount) {
            Logger.debug(`📝 Cleaned up ${beforeCount - afterCount} old log entries`);
            this.saveLogs();
        }
    }

    /**
     * Export logs as JSON
     */
    exportLogs(days = 7) {
        const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
        const exportLogs = this.logs.filter(log => log.timestamp >= startDate);

        return {
            exported: new Date().toISOString(),
            sessionId: this.sessionId,
            period: `${days} days`,
            count: exportLogs.length,
            logs: exportLogs
        };
    }

    /**
     * Clear all logs
     */
    clearLogs() {
        this.logs = [];
        localStorage.removeItem(this.storageKey);
        this.log('system', 'All logs cleared');
    }

    /**
     * Set log level
     */
    setLogLevel(level) {
        if (this.logLevels.hasOwnProperty(level)) {
            this.currentLogLevel = this.logLevels[level];
            this.log('system', `Log level set to: ${level}`);
        }
    }
}

// Export for use in other modules
window.DownloadLogger = DownloadLogger;