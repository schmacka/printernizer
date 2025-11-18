/**
 * Printernizer Auto-Download & Processing Manager
 * Comprehensive system for automatic file downloads and thumbnail processing
 */

class AutoDownloadManager {
    constructor() {
        this.downloadQueue = new DownloadQueue();
        this.thumbnailQueue = new ThumbnailQueue();
        this.logger = new DownloadLogger();
        this.monitoredPrinters = new Map();
        this.isActive = false;
        this.statsUpdateInterval = null;

        // Configuration
        this.config = {
            maxConcurrentDownloads: 2,
            maxConcurrentThumbnails: 1,
            retryAttempts: 3,
            retryDelay: 5000, // 5 seconds
            autoDetectionEnabled: true,
            logRetentionDays: 30
        };
    }

    /**
     * Initialize the auto-download system
     */
    async init() {
        Logger.debug('🚀 Initializing Auto-Download Manager');

        try {
            // Initialize components
            await this.downloadQueue.init();
            await this.thumbnailQueue.init();
            await this.logger.init();

            // Setup WebSocket monitoring
            this.setupWebSocketMonitoring();

            // Setup automatic job detection
            this.setupJobDetection();

            // Start stats update interval
            this.startStatsUpdates();

            this.isActive = true;
            this.logger.log('system', 'Auto-Download Manager initialized successfully');

            // Show system status in UI
            this.updateSystemStatus();

        } catch (error) {
            Logger.error('Failed to initialize Auto-Download Manager:', error);
            this.logger.error('system', 'Failed to initialize Auto-Download Manager', error);
        }
    }

    /**
     * Setup WebSocket monitoring for printer status changes
     */
    setupWebSocketMonitoring() {
        // Listen for printer status updates
        document.addEventListener('printerStatusUpdate', (event) => {
            this.handlePrinterStatusChange(event.detail);
        });

        // Listen for job updates
        document.addEventListener('jobUpdate', (event) => {
            this.handleJobUpdate(event.detail);
        });
    }

    /**
     * Handle printer status changes for auto-detection
     */
    async handlePrinterStatusChange(printerData) {
        if (!this.config.autoDetectionEnabled) return;

        const printerId = printerData.printer_id || printerData.id;
        const previousStatus = this.monitoredPrinters.get(printerId)?.status;
        const currentStatus = printerData.status;

        // Update monitored printer data
        this.monitoredPrinters.set(printerId, {
            ...printerData,
            lastUpdate: new Date()
        });

        // Detect job start (idle/offline -> printing)
        if (currentStatus === 'printing' && previousStatus !== 'printing') {
            await this.handleJobStart(printerId, printerData);
        }

        // Detect job completion (printing -> idle/completed)
        if (previousStatus === 'printing' && currentStatus !== 'printing') {
            await this.handleJobComplete(printerId, printerData);
        }
    }

    /**
     * Handle job start - automatically download current file
     */
    async handleJobStart(printerId, printerData) {
        this.logger.log('job_start', `Job started on printer ${printerId}`, {
            printerId,
            jobName: printerData.current_job,
            status: printerData.status
        });

        // Add to download queue with high priority
        const downloadTask = {
            id: `current_job_${printerId}_${Date.now()}`,
            type: 'current_job',
            printerId: printerId,
            printerName: printerData.name || `Printer ${printerId}`,
            jobName: printerData.current_job || 'Unknown Job',
            priority: 'high',
            attempts: 0,
            createdAt: new Date(),
            autoTriggered: true
        };

        await this.downloadQueue.add(downloadTask);

        // Show notification
        showToast('info', 'Auto-Download', `Downloading current job file from ${printerData.name || printerId}`);
    }

    /**
     * Handle job completion
     */
    async handleJobComplete(printerId, printerData) {
        this.logger.log('job_complete', `Job completed on printer ${printerId}`, {
            printerId,
            previousJob: this.monitoredPrinters.get(printerId)?.current_job,
            status: printerData.status
        });
    }

    /**
     * Handle job updates
     */
    async handleJobUpdate(jobData) {
        // Could be used for progress tracking in the future
        this.logger.debug('job_update', 'Job progress updated', jobData);
    }

    /**
     * Setup automatic job detection via polling (fallback)
     */
    setupJobDetection() {
        // Poll every 30 seconds for job changes (backup to WebSocket)
        setInterval(async () => {
            if (!this.config.autoDetectionEnabled) return;

            try {
                const printers = await api.getPrinters({ active: true });
                const printerList = Array.isArray(printers) ? printers : (printers.data || []);

                for (const printer of printerList) {
                    this.handlePrinterStatusChange(printer);
                }
            } catch (error) {
                this.logger.error('polling', 'Failed to poll printer status', error);
            }
        }, 30000);
    }

    /**
     * Manually trigger download for specific printer
     */
    async triggerManualDownload(printerId, printerName = null) {
        const downloadTask = {
            id: `manual_${printerId}_${Date.now()}`,
            type: 'manual',
            printerId: printerId,
            printerName: printerName || `Printer ${printerId}`,
            priority: 'normal',
            attempts: 0,
            createdAt: new Date(),
            autoTriggered: false
        };

        await this.downloadQueue.add(downloadTask);
        this.logger.log('manual_download', `Manual download triggered for printer ${printerId}`);

        showToast('info', 'Download Queued', `Manual download queued for ${printerName || printerId}`);
    }

    /**
     * Get system statistics
     */
    getStats() {
        return {
            system: {
                active: this.isActive,
                autoDetectionEnabled: this.config.autoDetectionEnabled,
                monitoredPrinters: this.monitoredPrinters.size
            },
            downloads: this.downloadQueue.getStats(),
            thumbnails: this.thumbnailQueue.getStats(),
            logs: this.logger.getStats()
        };
    }

    /**
     * Update system status in UI
     */
    updateSystemStatus() {
        const stats = this.getStats();

        // Update dashboard if visible
        const statusEl = document.getElementById('auto-download-status');
        if (statusEl) {
            statusEl.innerHTML = `
                <div class="auto-download-status ${this.isActive ? 'active' : 'inactive'}">
                    <div class="status-indicator ${this.isActive ? 'online' : 'offline'}"></div>
                    <div class="status-info">
                        <div class="status-title">Auto-Download ${this.isActive ? 'Active' : 'Inactive'}</div>
                        <div class="status-details">
                            ${stats.downloads.queued} in queue, ${stats.downloads.processing} processing
                        </div>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Start periodic stats updates
     */
    startStatsUpdates() {
        this.statsUpdateInterval = setInterval(() => {
            this.updateSystemStatus();
        }, 5000); // Update every 5 seconds
    }

    /**
     * Stop the auto-download system
     */
    async shutdown() {
        Logger.debug('🛑 Shutting down Auto-Download Manager');

        this.isActive = false;

        if (this.statsUpdateInterval) {
            clearInterval(this.statsUpdateInterval);
        }

        await this.downloadQueue.shutdown();
        await this.thumbnailQueue.shutdown();

        this.logger.log('system', 'Auto-Download Manager shut down');
    }

    /**
     * Enable/disable auto-detection
     */
    setAutoDetection(enabled) {
        this.config.autoDetectionEnabled = enabled;
        this.logger.log('config', `Auto-detection ${enabled ? 'enabled' : 'disabled'}`);
        this.updateSystemStatus();
    }

    /**
     * Get download history
     */
    getDownloadHistory(days = 7) {
        return this.logger.getDownloadHistory(days);
    }

    /**
     * Get error log
     */
    getErrorLog(days = 7) {
        return this.logger.getErrorLog(days);
    }
}

// Export for use in other modules
window.AutoDownloadManager = AutoDownloadManager;