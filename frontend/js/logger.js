/**
 * Frontend Logging Utility
 *
 * Provides centralized logging with debug mode support.
 * Production builds can disable debug/info logs for security and performance.
 *
 * Usage:
 *   Logger.debug('Component initialized', { data });
 *   Logger.info('User action completed');
 *   Logger.warn('Deprecated feature used');
 *   Logger.error('Operation failed', error);
 *
 * Enable debug mode:
 *   - Add ?debug=true to URL
 *   - Set localStorage: localStorage.setItem('debug', 'true')
 *   - Set window.DEBUG_MODE = true
 */

const Logger = (() => {
    // Check if debug mode is enabled
    const isDebugEnabled = () => {
        // Check URL parameter
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('debug') === 'true') {
            return true;
        }

        // Check localStorage
        try {
            if (localStorage.getItem('debug') === 'true') {
                return true;
            }
        } catch (e) {
            // localStorage might not be available
        }

        // Check window global
        if (window.DEBUG_MODE === true) {
            return true;
        }

        return false;
    };

    // Store debug state
    let debugMode = isDebugEnabled();

    // Format timestamp
    const timestamp = () => {
        const now = new Date();
        return now.toISOString().substring(11, 23); // HH:mm:ss.SSS
    };

    // Format log message with prefix
    const formatMessage = (level, msg) => {
        return `[${timestamp()}] [${level}] ${msg}`;
    };

    return {
        /**
         * Check if debug mode is currently enabled
         * @returns {boolean}
         */
        isDebug() {
            return debugMode;
        },

        /**
         * Enable debug mode
         */
        enableDebug() {
            debugMode = true;
            try {
                localStorage.setItem('debug', 'true');
            } catch (e) {
                // Ignore localStorage errors
            }
            console.info('[Logger] Debug mode enabled');
        },

        /**
         * Disable debug mode
         */
        disableDebug() {
            debugMode = false;
            try {
                localStorage.removeItem('debug');
            } catch (e) {
                // Ignore localStorage errors
            }
            console.info('[Logger] Debug mode disabled');
        },

        /**
         * Debug level logging (only in debug mode)
         * Use for detailed debugging information
         * @param {string} msg - Message to log
         * @param {...any} args - Additional arguments
         */
        debug(msg, ...args) {
            if (debugMode) {
                console.log(formatMessage('DEBUG', msg), ...args);
            }
        },

        /**
         * Info level logging (only in debug mode)
         * Use for general informational messages
         * @param {string} msg - Message to log
         * @param {...any} args - Additional arguments
         */
        info(msg, ...args) {
            if (debugMode) {
                console.info(formatMessage('INFO', msg), ...args);
            }
        },

        /**
         * Warning level logging (always shown)
         * Use for recoverable issues that should be investigated
         * @param {string} msg - Message to log
         * @param {...any} args - Additional arguments
         */
        warn(msg, ...args) {
            console.warn(formatMessage('WARN', msg), ...args);
        },

        /**
         * Error level logging (always shown)
         * Use for errors and exceptions
         * @param {string} msg - Message to log
         * @param {...any} args - Additional arguments
         */
        error(msg, ...args) {
            console.error(formatMessage('ERROR', msg), ...args);

            // Could send to error tracking service here
            // Example: sendToErrorTracking(msg, args);
        },

        /**
         * Group logging (only in debug mode)
         * Use for grouping related log messages
         * @param {string} label - Group label
         */
        group(label) {
            if (debugMode) {
                console.group(formatMessage('GROUP', label));
            }
        },

        /**
         * End group logging
         */
        groupEnd() {
            if (debugMode) {
                console.groupEnd();
            }
        },

        /**
         * Table logging (only in debug mode)
         * Use for displaying tabular data
         * @param {any} data - Data to display as table
         */
        table(data) {
            if (debugMode) {
                console.table(data);
            }
        },

        /**
         * Time logging (only in debug mode)
         * Use for performance measurement
         * @param {string} label - Timer label
         */
        time(label) {
            if (debugMode) {
                console.time(label);
            }
        },

        /**
         * End time logging
         * @param {string} label - Timer label
         */
        timeEnd(label) {
            if (debugMode) {
                console.timeEnd(label);
            }
        }
    };
})();

// Make Logger globally available
window.Logger = Logger;

// Log initialization (only in debug mode)
if (Logger.isDebug()) {
    Logger.info('Logger initialized - Debug mode enabled');
    Logger.info('Disable with: Logger.disableDebug() or localStorage.removeItem("debug")');
}
