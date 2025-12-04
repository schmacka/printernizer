/**
 * Auto-Download System Debug Utilities
 * Tools for debugging download and thumbnail processing issues
 */

class DownloadDebugger {
    constructor() {
        this.enabled = true;
        this.logLevel = 'debug'; // debug, info, warn, error
    }

    /**
     * Test the download API endpoint directly
     */
    async testDownloadEndpoint(printerId) {
        console.group(`🔍 Testing Download Endpoint for Printer: ${printerId}`);

        try {
            console.log('📡 Making API call to:', CONFIG.ENDPOINTS.PRINTER_DOWNLOAD_CURRENT_JOB(printerId));

            const startTime = Date.now();
            const response = await api.downloadCurrentJobFile(printerId);
            const endTime = Date.now();

            console.log(`⏱️ API Response Time: ${endTime - startTime}ms`);
            console.log('📋 Full Response Object:', response);
            console.log('📋 Response Type:', typeof response);
            console.log('📋 Response Keys:', response ? Object.keys(response) : 'No keys (null/undefined)');

            if (response) {
                console.log('📋 Status Field:', response.status, typeof response.status);
                console.log('📋 Message Field:', response.message);
                console.log('📋 Error Field:', response.error);
                console.log('📋 File ID:', response.file_id);
                console.log('📋 Filename:', response.filename);
                console.log('📋 Has Thumbnail:', response.has_thumbnail);
            }

            // Test what the download queue would do with this response
            console.log('🧪 Testing Download Queue Response Handling...');
            this.simulateDownloadQueueProcessing(response);

        } catch (error) {
            console.error('❌ API Call Failed:', error);
            console.log('📋 Error Type:', typeof error);
            console.log('📋 Error Message:', error.message);
            console.log('📋 Error Stack:', error.stack);
        }

        console.groupEnd();
    }

    /**
     * Simulate how the download queue would process the response
     */
    simulateDownloadQueueProcessing(response) {
        try {
            if (!response) {
                throw new Error('No response from download API');
            }

            if (!response.status) {
                console.error('Response missing status field:', response);
                throw new Error('Invalid response from download API: missing status field');
            }

            console.log(`🧪 Processing status: "${response.status}"`);

            // Simulate the switch statement from download-queue.js
            switch (response.status) {
                case 'success':
                case 'processed':
                case 'exists_with_thumbnail':
                    console.log('✅ Would be processed as: SUCCESS');
                    return {
                        success: true,
                        status: response.status,
                        fileId: response.file_id,
                        filename: response.filename,
                        hasThumbnail: response.has_thumbnail || false,
                        message: response.message || 'Download successful'
                    };

                case 'exists_no_thumbnail':
                    console.log('✅ Would be processed as: SUCCESS (no thumbnail)');
                    return {
                        success: true,
                        status: response.status,
                        fileId: response.file_id,
                        filename: response.filename,
                        hasThumbnail: false,
                        message: 'File exists but no thumbnail available'
                    };

                case 'not_printing':
                    console.log('❌ Would throw error: Printer is not currently printing');
                    throw new Error('Printer is not currently printing');

                case 'no_file':
                    console.log('❌ Would throw error: No file available for current job');
                    throw new Error('No file available for current job');

                case 'error':
                    console.log('❌ Would throw error: Download failed with error status');
                    console.log('📋 Error message would be:', response.message || response.error || 'Download failed with error status');
                    throw new Error(response.message || response.error || 'Download failed with error status');

                case 'failed':
                    console.log('❌ Would throw error: Download failed');
                    throw new Error(response.message || response.error || 'Download failed');

                case 'timeout':
                    console.log('❌ Would throw error: Download request timed out');
                    throw new Error('Download request timed out');

                case 'connection_error':
                    console.log('❌ Would throw error: Connection error');
                    throw new Error('Connection error: ' + (response.message || 'Unable to connect to printer'));

                case 'file_not_found':
                    console.log('❌ Would throw error: File not found on printer');
                    throw new Error('File not found on printer');

                case 'access_denied':
                    console.log('❌ Would throw error: Access denied');
                    throw new Error('Access denied: ' + (response.message || 'Insufficient permissions'));

                default:
                    console.log('❌ Would throw error: Unknown download status');
                    console.error('Unknown download response:', response);
                    throw new Error(`Unknown download status: ${response.status}. Message: ${response.message || 'No additional details'}`);
            }

        } catch (error) {
            console.log('❌ Simulation threw error:', error.message);
            return { error: error.message };
        }
    }

    /**
     * Check system status and health
     */
    checkSystemHealth() {
        console.group('🏥 Auto-Download System Health Check');

        // Check if system is initialized
        const systemStatus = window.autoDownloadSystemInitializer?.getSystemStatus();
        console.log('🤖 System Status:', systemStatus);

        // Check individual components
        console.log('📋 Download Queue Available:', !!window.downloadQueue);
        console.log('🖼️ Thumbnail Queue Available:', !!window.thumbnailQueue);
        console.log('📝 Logger Available:', !!window.downloadLogger);
        console.log('🖥️ UI Available:', !!window.autoDownloadUI);
        console.log('🤖 Manager Available:', !!window.autoDownloadManager);

        // Check queue contents
        if (window.downloadQueue) {
            const queueContents = window.downloadQueue.getQueueContents();
            console.log('📋 Download Queue Contents:', queueContents);
            console.log('📋 Download Queue Stats:', window.downloadQueue.getStats());
        }

        if (window.thumbnailQueue) {
            const thumbnailContents = window.thumbnailQueue.getQueueContents();
            console.log('🖼️ Thumbnail Queue Contents:', thumbnailContents);
            console.log('🖼️ Thumbnail Queue Stats:', window.thumbnailQueue.getStats());
        }

        // Check logs
        if (window.downloadLogger) {
            const logStats = window.downloadLogger.getStats();
            console.log('📝 Logger Stats:', logStats);

            const recentErrors = window.downloadLogger.getErrorLog(1);
            if (recentErrors.length > 0) {
                console.log('❌ Recent Errors:', recentErrors);
            }
        }

        console.groupEnd();
    }

    /**
     * Clear all failed tasks for fresh testing
     */
    clearFailedTasks() {
        console.log('🧹 Clearing failed tasks...');

        if (window.downloadQueue) {
            // Access the private failed map (this is for debugging only)
            window.downloadQueue.failed.clear();
            console.log('✅ Cleared download failed tasks');
        }

        if (window.thumbnailQueue) {
            window.thumbnailQueue.failed.clear();
            console.log('✅ Cleared thumbnail failed tasks');
        }

        // Refresh UI
        if (window.autoDownloadUI && window.autoDownloadUI.isVisible) {
            window.autoDownloadUI.updateQueueDisplay();
        }

        console.log('🧹 Failed tasks cleared');
    }

    /**
     * Manually trigger a download with full debugging
     */
    async debugDownload(printerId, printerName = 'Debug Printer') {
        console.group(`🐛 Debug Download for Printer: ${printerId}`);

        // Test the API endpoint first
        await this.testDownloadEndpoint(printerId);

        // Now trigger through the normal system
        if (window.autoDownloadManager) {
            console.log('🚀 Triggering manual download through system...');
            await window.autoDownloadManager.triggerManualDownload(printerId, printerName);
        } else {
            console.error('❌ AutoDownloadManager not available');
        }

        console.groupEnd();
    }

    /**
     * Monitor download queue in real-time
     */
    startQueueMonitoring(intervalSeconds = 5) {
        console.log(`👁️ Starting queue monitoring (every ${intervalSeconds}s)`);

        const monitor = setInterval(() => {
            if (window.downloadQueue) {
                const stats = window.downloadQueue.getStats();
                const contents = window.downloadQueue.getQueueContents();

                console.log(`📊 Queue Monitor: ${stats.queued} queued, ${stats.processing} processing, ${stats.completed} completed, ${stats.failed} failed`);

                if (contents.processing.length > 0) {
                    console.log('🔄 Currently processing:', contents.processing.map(t => `${t.id} (${t.printerName})`));
                }

                if (contents.recentFailed.length > 0) {
                    console.log('❌ Recent failures:', contents.recentFailed.map(t => `${t.id}: ${t.lastError}`));
                }
            }
        }, intervalSeconds * 1000);

        // Store reference to stop monitoring later
        this.queueMonitor = monitor;

        return monitor;
    }

    /**
     * Stop queue monitoring
     */
    stopQueueMonitoring() {
        if (this.queueMonitor) {
            clearInterval(this.queueMonitor);
            this.queueMonitor = null;
            console.log('🛑 Queue monitoring stopped');
        }
    }

    /**
     * Export detailed debug report
     */
    exportDebugReport() {
        const report = {
            timestamp: new Date().toISOString(),
            systemStatus: window.autoDownloadSystemInitializer?.getSystemStatus(),
            downloadQueueStats: window.downloadQueue?.getStats(),
            downloadQueueContents: window.downloadQueue?.getQueueContents(),
            thumbnailQueueStats: window.thumbnailQueue?.getStats(),
            thumbnailQueueContents: window.thumbnailQueue?.getQueueContents(),
            loggerStats: window.downloadLogger?.getStats(),
            recentLogs: window.downloadLogger?.exportLogs(1),
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `printernizer_debug_report_${new Date().toISOString().split('T')[0]}.json`;
        a.click();

        URL.revokeObjectURL(url);

        console.log('📊 Debug report exported:', report);
        return report;
    }
}

// Create global debug instance
window.downloadDebugger = new DownloadDebugger();

// Add convenient console methods
window.debugDownload = (printerId, printerName) => window.downloadDebugger.debugDownload(printerId, printerName);
window.testDownloadAPI = (printerId) => window.downloadDebugger.testDownloadEndpoint(printerId);
window.checkDownloadHealth = () => window.downloadDebugger.checkSystemHealth();
window.clearFailedDownloads = () => window.downloadDebugger.clearFailedTasks();
window.monitorDownloads = (interval) => window.downloadDebugger.startQueueMonitoring(interval);
window.stopMonitoringDownloads = () => window.downloadDebugger.stopQueueMonitoring();
window.exportDownloadDebug = () => window.downloadDebugger.exportDebugReport();

console.log('🐛 Download Debug Tools Loaded! Available commands:');
console.log('- debugDownload(printerId, printerName) - Full debug test');
console.log('- testDownloadAPI(printerId) - Test API endpoint only');
console.log('- checkDownloadHealth() - System health check');
console.log('- clearFailedDownloads() - Clear failed tasks');
console.log('- monitorDownloads(5) - Start monitoring (5s interval)');
console.log('- stopMonitoringDownloads() - Stop monitoring');
console.log('- exportDownloadDebug() - Export debug report');