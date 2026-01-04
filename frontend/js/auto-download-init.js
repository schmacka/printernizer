/**
 * Auto-Download System Initialization
 * Coordinates startup and integration of all auto-download components
 */

class AutoDownloadSystemInitializer {
    constructor() {
        this.initialized = false;
        this.autoDownloadManager = null;
        this.components = {
            downloadQueue: null,
            thumbnailQueue: null,
            logger: null,
            ui: null
        };
    }

    /**
     * Initialize the complete auto-download system
     */
    async initialize() {
        if (this.initialized) {
            Logger.warn('Auto-Download System already initialized');
            return;
        }

        Logger.debug('🚀 Starting Auto-Download System initialization...');

        try {
            // Step 1: Initialize core components
            await this.initializeCoreComponents();

            // Step 2: Initialize the main manager
            await this.initializeManager();

            // Step 3: Initialize UI components
            await this.initializeUI();

            // Step 4: Setup WebSocket integration
            this.setupWebSocketIntegration();

            // Step 5: Update existing functionality
            this.updateExistingFunctionality();

            // Mark as initialized
            this.initialized = true;

            Logger.debug('✅ Auto-Download System initialization complete');

            // Show success notification only if backend is actually reachable
            setTimeout(async () => {
                const backendStatus = await this.checkBackendConnectivity();

                if (backendStatus.healthy) {
                    showToast('success', 'System Ready', 'Auto-Download System is now active and monitoring printers', CONFIG.TOAST_DURATION, {
                        uniqueKey: CONFIG.NOTIFICATION_KEYS.AUTO_DOWNLOAD_READY,
                        deduplicateMode: 'update'
                    });
                } else {
                    showToast('warning', 'Backend Offline', backendStatus.message || 'Auto-Download System wartet auf Backend-Verbindung', CONFIG.TOAST_DURATION, {
                        uniqueKey: CONFIG.NOTIFICATION_KEYS.AUTO_DOWNLOAD_OFFLINE,
                        deduplicateMode: 'update'
                    });
                }
            }, 1500); // Slightly delayed to allow backend health check to complete

        } catch (error) {
            Logger.error('❌ Failed to initialize Auto-Download System:', error);
            showToast('error', 'Initialization Failed', 'Auto-Download System could not be started', CONFIG.TOAST_DURATION, {
                uniqueKey: CONFIG.NOTIFICATION_KEYS.AUTO_DOWNLOAD_ERROR,
                deduplicateMode: 'update'
            });
            throw error;
        }
    }

    /**
     * Initialize core components
     */
    async initializeCoreComponents() {
        Logger.debug('📋 Initializing core components...');

        // Initialize download queue
        this.components.downloadQueue = new DownloadQueue();
        await this.components.downloadQueue.init();

        // Initialize thumbnail queue
        this.components.thumbnailQueue = new ThumbnailQueue();
        await this.components.thumbnailQueue.init();

        // Initialize logger
        this.components.logger = new DownloadLogger();
        await this.components.logger.init();

        // Make queues globally available
        window.downloadQueue = this.components.downloadQueue;
        window.thumbnailQueue = this.components.thumbnailQueue;
        window.downloadLogger = this.components.logger;

        Logger.debug('✅ Core components initialized');
    }

    /**
     * Initialize the main auto-download manager
     */
    async initializeManager() {
        Logger.debug('🤖 Initializing Auto-Download Manager...');

        this.autoDownloadManager = new AutoDownloadManager();

        // Inject dependencies
        this.autoDownloadManager.downloadQueue = this.components.downloadQueue;
        this.autoDownloadManager.thumbnailQueue = this.components.thumbnailQueue;
        this.autoDownloadManager.logger = this.components.logger;

        await this.autoDownloadManager.init();

        // Make globally available
        window.autoDownloadManager = this.autoDownloadManager;

        Logger.debug('✅ Auto-Download Manager initialized');
    }

    /**
     * Initialize UI components
     */
    async initializeUI() {
        Logger.debug('🖥️ Initializing UI components...');

        this.components.ui = window.autoDownloadUI;
        await this.components.ui.init(this.autoDownloadManager);

        Logger.debug('✅ UI components initialized');
    }

    /**
     * Setup WebSocket integration
     */
    setupWebSocketIntegration() {
        Logger.debug('🔌 Setting up WebSocket integration...');

        // Enhance existing WebSocket handlers
        if (window.websocketManager) {
            this.enhanceWebSocketHandlers();
        } else {
            // Wait for WebSocket manager to be available
            const checkWebSocket = setInterval(() => {
                if (window.websocketManager) {
                    this.enhanceWebSocketHandlers();
                    clearInterval(checkWebSocket);
                }
            }, 1000);

            // Stop checking after 30 seconds
            setTimeout(() => {
                clearInterval(checkWebSocket);
                Logger.warn('WebSocket manager not found, auto-detection may be limited');
            }, 30000);
        }
    }

    /**
     * Enhance WebSocket handlers for auto-detection
     */
    enhanceWebSocketHandlers() {
        const originalWebSocketManager = window.websocketManager;

        // If websocketManager has a messageHandler, enhance it
        if (originalWebSocketManager && originalWebSocketManager.messageHandler) {
            const originalHandler = originalWebSocketManager.messageHandler.bind(originalWebSocketManager);

            originalWebSocketManager.messageHandler = (data) => {
                // Call original handler first
                originalHandler(data);

                // Then handle auto-download logic
                this.handleWebSocketMessage(data);
            };

            Logger.debug('✅ WebSocket handlers enhanced for auto-detection');
        }

        // Also listen for custom events
        document.addEventListener('printerStatusUpdate', (event) => {
            this.handlePrinterStatusUpdate(event.detail);
        });
    }

    /**
     * Handle WebSocket messages for auto-detection
     */
    handleWebSocketMessage(data) {
        if (!this.autoDownloadManager) return;

        // Forward to auto-download manager
        if (data.type === 'printer_status') {
            this.autoDownloadManager.handlePrinterStatusChange(data);
        } else if (data.type === 'job_update') {
            this.autoDownloadManager.handleJobUpdate(data);
        }
    }

    /**
     * Handle printer status updates
     */
    handlePrinterStatusUpdate(printerData) {
        if (!this.autoDownloadManager) return;

        this.autoDownloadManager.handlePrinterStatusChange(printerData);
    }

    /**
     * Update existing functionality to integrate with auto-download system
     */
    updateExistingFunctionality() {
        Logger.debug('🔧 Updating existing functionality...');

        // Enhance triggerCurrentJobDownload function
        this.enhanceTriggerCurrentJobDownload();

        // Enhance printer file downloads
        this.enhancePrinterFileDownloads();

        // Enhance thumbnail handling
        this.enhanceThumbnailHandling();

        Logger.debug('✅ Existing functionality updated');
    }

    /**
     * Enhance the triggerCurrentJobDownload function
     */
    enhanceTriggerCurrentJobDownload() {
        // Replace global function with queue-based version
        window.triggerCurrentJobDownload = async (printerId) => {
            if (!this.autoDownloadManager) {
                Logger.error('Auto-Download Manager not available');
                showToast('error', 'System Error', 'Auto-Download System not available');
                return;
            }

            try {
                // Get printer info
                const printers = await api.getPrinters();
                const printerList = Array.isArray(printers) ? printers : (printers.data || []);
                const printer = printerList.find(p => p.id === printerId);
                const printerName = printer ? printer.name : `Printer ${printerId}`;

                // Add to download queue
                await this.autoDownloadManager.triggerManualDownload(printerId, printerName);

            } catch (error) {
                Logger.error('Failed to trigger manual download:', error);
                showToast('error', 'Download Failed', 'Could not start download');
            }
        };
    }

    /**
     * Enhance printer file downloads
     */
    enhancePrinterFileDownloads() {
        // Enhance DruckerDateienManager if available
        if (window.DruckerDateienManager) {
            const originalDownloadFile = window.DruckerDateienManager.prototype.downloadFile;

            if (originalDownloadFile) {
                window.DruckerDateienManager.prototype.downloadFile = function(filename, printerId) {
                    // Add to download queue instead of direct download
                    const downloadTask = {
                        id: `file_${printerId}_${filename}_${Date.now()}`,
                        type: 'printer_file',
                        printerId: printerId,
                        filename: filename,
                        priority: 'normal',
                        attempts: 0,
                        createdAt: new Date(),
                        autoTriggered: false
                    };

                    if (window.downloadQueue) {
                        window.downloadQueue.add(downloadTask);
                        showToast('info', 'Download Queued', `${filename} added to download queue`);
                    } else {
                        // Fallback to original method
                        return originalDownloadFile.call(this, filename, printerId);
                    }
                };
            }
        }
    }

    /**
     * Enhance thumbnail handling
     */
    enhanceThumbnailHandling() {
        // Listen for thumbnail completion events
        document.addEventListener('thumbnailProcessingComplete', (event) => {
            const { fileId, result } = event.detail;

            // Update any displayed thumbnails
            this.updateDisplayedThumbnails(fileId, result.thumbnailUrl);

            // Refresh printer cards if they show this file
            this.refreshPrinterCards();
        });
    }

    /**
     * Update displayed thumbnails after processing
     */
    updateDisplayedThumbnails(fileId, thumbnailUrl) {
        // Update file thumbnails
        const fileImages = document.querySelectorAll(`img[data-file-id="${fileId}"]`);
        fileImages.forEach(img => {
            if (img.src.includes('placeholder-thumbnail.svg')) {
                img.src = thumbnailUrl;
                img.classList.remove('placeholder-image');
            }
        });

        // Update printer card thumbnails if they match this file
        const printerThumbnails = document.querySelectorAll('.job-thumbnail img, .thumbnail-image-small, .job-thumbnail-image');
        printerThumbnails.forEach(img => {
            if (img.src.includes('placeholder-thumbnail.svg') && img.dataset.fileId === fileId) {
                img.src = thumbnailUrl;
                img.classList.remove('placeholder-image');
            }
        });
    }

    /**
     * Refresh printer cards to show updated thumbnails
     */
    refreshPrinterCards() {
        // Trigger refresh of printer data
        const event = new CustomEvent('refreshPrinterData');
        document.dispatchEvent(event);
    }

    /**
     * Get system status
     */
    getSystemStatus() {
        if (!this.initialized) {
            return {
                status: 'not_initialized',
                message: 'System not initialized'
            };
        }

        const stats = this.autoDownloadManager.getStats();
        return {
            status: 'active',
            stats: stats,
            components: {
                downloadQueue: this.components.downloadQueue ? 'initialized' : 'not_initialized',
                thumbnailQueue: this.components.thumbnailQueue ? 'initialized' : 'not_initialized',
                logger: this.components.logger ? 'initialized' : 'not_initialized',
                ui: this.components.ui ? 'initialized' : 'not_initialized'
            }
        };
    }

    /**
     * Check backend connectivity by calling the health endpoint
     * @returns {Promise<{healthy: boolean, message: string}>}
     */
    async checkBackendConnectivity() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

            const response = await fetch(`${CONFIG.API_BASE_URL}/health`, {
                method: 'GET',
                signal: controller.signal,
                cache: 'no-cache'
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                const data = await response.json();
                // Update global health flag
                window.printernizer = window.printernizer || {};
                window.printernizer.backendHealthy = true;

                return {
                    healthy: true,
                    message: `Backend v${data.version || 'unknown'} connected`
                };
            } else {
                window.printernizer = window.printernizer || {};
                window.printernizer.backendHealthy = false;

                return {
                    healthy: false,
                    message: `Backend returned status ${response.status}`
                };
            }
        } catch (error) {
            window.printernizer = window.printernizer || {};
            window.printernizer.backendHealthy = false;

            if (error.name === 'AbortError') {
                return {
                    healthy: false,
                    message: 'Backend connection timeout'
                };
            }

            return {
                healthy: false,
                message: 'Backend not reachable'
            };
        }
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        Logger.debug('🛑 Shutting down Auto-Download System...');

        if (this.autoDownloadManager) {
            await this.autoDownloadManager.shutdown();
        }

        if (this.components.ui) {
            this.components.ui.destroy();
        }

        this.initialized = false;
        Logger.debug('✅ Auto-Download System shut down');
    }
}

// Initialize the system when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    // Wait a bit for other systems to initialize
    setTimeout(async () => {
        try {
            window.autoDownloadSystemInitializer = new AutoDownloadSystemInitializer();
            await window.autoDownloadSystemInitializer.initialize();
        } catch (error) {
            Logger.error('Failed to initialize Auto-Download System:', error);
        }
    }, 2000); // 2 second delay
});

// Export for manual initialization if needed
window.AutoDownloadSystemInitializer = AutoDownloadSystemInitializer;