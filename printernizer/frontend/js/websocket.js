/**
 * Printernizer WebSocket Client
 * Handles real-time communication with the backend for live updates
 */

class WebSocketClient {
    constructor() {
        this.socket = null;
        this.url = CONFIG.WEBSOCKET_URL;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this.heartbeatTimeout = null;
        this.messageQueue = [];
        this.listeners = new Map();
    }

    /**
     * Connect to WebSocket server
     */
    async connect() {
        try {
            this.updateConnectionStatus('connecting');
            
            this.socket = new WebSocket(this.url);
            this.setupEventHandlers();
            
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Connection timeout'));
                }, 10000);

                this.socket.onopen = () => {
                    clearTimeout(timeout);
                    this.handleConnection();
                    resolve();
                };

                this.socket.onerror = (error) => {
                    clearTimeout(timeout);
                    reject(error);
                };
            });
        } catch (error) {
            window.ErrorHandler?.handleWebSocketError(error, { operation: 'connection' });
            this.handleDisconnection();
            throw error;
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }

        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }

        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }

        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.updateConnectionStatus('disconnected');
    }

    /**
     * Setup WebSocket event handlers
     */
    setupEventHandlers() {
        this.socket.onopen = this.handleConnection.bind(this);
        this.socket.onclose = this.handleDisconnection.bind(this);
        this.socket.onerror = this.handleError.bind(this);
        this.socket.onmessage = this.handleMessage.bind(this);
    }

    /**
     * Handle successful connection
     */
    handleConnection() {
        Logger.debug('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.updateConnectionStatus('connected');
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Send queued messages
        this.sendQueuedMessages();
        
        // Emit connection event
        this.emit('connected');
    }

    /**
     * Handle disconnection
     */
    handleDisconnection(event) {
        Logger.debug('WebSocket disconnected:', event?.code, event?.reason);
        this.isConnected = false;
        this.updateConnectionStatus('disconnected');
        
        // Stop heartbeat
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        // Emit disconnection event
        this.emit('disconnected', event);
        
        // Auto-reconnect if not intentionally closed
        if (event?.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
        }
    }

    /**
     * Handle WebSocket errors
     */
    handleError(error) {
        window.ErrorHandler?.handleWebSocketError(error, { event: 'websocket_error' });
        this.emit('error', error);
    }

    /**
     * Handle incoming messages
     */
    handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            Logger.debug('WebSocket message received:', message.type, message);
            
            // Handle heartbeat pong
            if (message.type === 'pong') {
                this.handlePong();
                return;
            }
            
            // Emit message to appropriate listeners
            this.emit(message.type, message.data, message);
            this.emit('message', message);
            
        } catch (error) {
            window.ErrorHandler?.handleWebSocketError(error, { operation: 'message_parsing', data: event.data });
        }
    }

    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
            30000 // Max 30 seconds
        );
        
        Logger.debug(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.reconnectAttempts++;
            this.connect().catch(error => {
                window.ErrorHandler?.handleWebSocketError(error, { operation: 'reconnection', attempt: this.reconnectAttempts });
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect();
                } else {
                    window.ErrorHandler?.handleWebSocketError(new Error('Max reconnection attempts reached'), { operation: 'max_reconnect_attempts', attempts: this.maxReconnectAttempts });
                    this.updateConnectionStatus('failed');
                }
            });
        }, delay);
    }

    /**
     * Start heartbeat mechanism
     */
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'ping', timestamp: new Date().toISOString() });
                
                // Set timeout for pong response
                this.heartbeatTimeout = setTimeout(() => {
                    Logger.warn('Heartbeat timeout - connection may be lost');
                    this.socket?.close();
                }, 5000);
            }
        }, 30000); // Every 30 seconds
    }

    /**
     * Handle heartbeat pong response
     */
    handlePong() {
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }

    /**
     * Send message to server
     */
    send(message) {
        if (this.isConnected && this.socket?.readyState === WebSocket.OPEN) {
            try {
                this.socket.send(JSON.stringify(message));
            } catch (error) {
                window.ErrorHandler?.handleWebSocketError(error, { operation: 'send_message', message });
                this.messageQueue.push(message);
            }
        } else {
            // Queue message for later
            this.messageQueue.push(message);
        }
    }

    /**
     * Send queued messages
     */
    sendQueuedMessages() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.send(message);
        }
    }

    /**
     * Add event listener
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
     * Remove event listener
     */
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * Emit event to listeners
     */
    emit(event, ...args) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(...args);
                } catch (error) {
                    window.ErrorHandler?.handleWebSocketError(error, { operation: 'event_listener', event });
                }
            });
        }
    }

    /**
     * Update connection status in UI
     */
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        if (!statusElement) return;

        const statusDot = statusElement.querySelector('.status-dot');
        const statusText = statusElement.querySelector('.status-text');

        if (statusDot) {
            statusDot.className = `status-dot ${status}`;
        }

        if (statusText) {
            const statusTexts = {
                'connecting': 'Verbinde...',
                'connected': 'Verbunden',
                'disconnected': 'Getrennt',
                'failed': 'Verbindung fehlgeschlagen'
            };
            statusText.textContent = statusTexts[status] || 'Unbekannt';
        }
    }

    /**
     * Get connection status
     */
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            queuedMessages: this.messageQueue.length
        };
    }
}

/**
 * WebSocket Event Handlers for Printernizer
 */
class PrinternizerWebSocketHandler {
    constructor(wsClient) {
        this.ws = wsClient;
        this.setupEventHandlers();
    }

    /**
     * Setup all WebSocket event handlers
     */
    setupEventHandlers() {
        // Printer status updates
        this.ws.on(CONFIG.WS_MESSAGE_TYPES.PRINTER_STATUS, (data) => {
            this.handlePrinterStatusUpdate(data);
        });

        // Job updates
        this.ws.on(CONFIG.WS_MESSAGE_TYPES.JOB_UPDATE, (data) => {
            this.handleJobUpdate(data);
        });

        // Auto-created job notifications
        this.ws.on('job_auto_created', (data) => {
            this.handleAutoJobCreated(data);
        });

        // File updates
        this.ws.on(CONFIG.WS_MESSAGE_TYPES.FILE_UPDATE, (data) => {
            this.handleFileUpdate(data);
        });

        // System alerts
        this.ws.on(CONFIG.WS_MESSAGE_TYPES.SYSTEM_ALERT, (data) => {
            this.handleSystemAlert(data);
        });

        // Connection events with deduplication
        this.ws.on('connected', () => {
            showToast('success', 'Verbindung hergestellt', 'WebSocket-Verbindung ist aktiv', CONFIG.TOAST_DURATION, {
                uniqueKey: CONFIG.NOTIFICATION_KEYS.WS_CONNECTED,
                deduplicateMode: 'update',
                cooldown: 5000 // 5 seconds cooldown
            });
        });

        this.ws.on('disconnected', () => {
            showToast('warning', 'Verbindung getrennt', 'Live-Updates sind nicht verfügbar', CONFIG.TOAST_DURATION, {
                uniqueKey: CONFIG.NOTIFICATION_KEYS.WS_DISCONNECTED,
                deduplicateMode: 'update',
                cooldown: 5000 // 5 seconds cooldown
            });
        });
    }

    /**
     * Handle printer status updates
     */
    handlePrinterStatusUpdate(data) {
        Logger.debug('Printer status update:', data);
        
        // Update printer cards on dashboard
        const printerCard = document.querySelector(`[data-printer-id="${data.printer_id}"]`);
        if (printerCard) {
            this.updatePrinterCard(printerCard, data);
        }

        // Update printer details if currently viewing
        if (window.currentPage === 'printers') {
            refreshPrinters();
        }

        // Emit custom event for other components
        document.dispatchEvent(new CustomEvent('printerStatusUpdate', {
            detail: data
        }));
    }

    /**
     * Handle job updates
     */
    handleJobUpdate(data) {
        Logger.debug('Job update:', data);
        
        // Update job lists
        if (window.currentPage === 'jobs' || window.currentPage === 'dashboard') {
            this.updateJobInList(data);
        }

        // Update progress bars
        const progressElements = document.querySelectorAll(`[data-job-id="${data.id}"]`);
        progressElements.forEach(element => {
            this.updateJobProgress(element, data);
        });

        // Show notifications for important job events
        if (data.status === 'completed') {
            showToast('success', 'Druck abgeschlossen', `${data.job_name} wurde erfolgreich gedruckt`);
        } else if (data.status === 'failed') {
            showToast('error', 'Druck fehlgeschlagen', `${data.job_name} ist fehlgeschlagen`);
        }

        // Emit custom event
        document.dispatchEvent(new CustomEvent('jobUpdate', {
            detail: data
        }));
    }

    /**
     * Handle auto-created job notification
     */
    handleAutoJobCreated(data) {
        Logger.debug('Auto-created job:', data);

        // Extract job details
        const jobName = data.job_name || data.filename || 'Unbenannter Auftrag';
        const printerName = data.printer_id || 'Unbekannter Drucker';
        const isStartup = data.customer_info?.discovered_on_startup;

        // Build notification message
        let message = `${jobName} auf ${printerName}`;
        if (isStartup) {
            message += ' (beim Start entdeckt)';
        }

        // Show toast notification
        showToast('info', '⚡ Auftrag automatisch erstellt', message, 5000, {
            uniqueKey: `auto_job_${data.id}`,
            deduplicateMode: 'ignore', // Don't show duplicate for same job
            cooldown: 60000 // 1 minute cooldown per job
        });

        // Show one-time tip for first auto-created job
        this.showFirstAutoJobTip();

        // Update job lists if on jobs or dashboard page
        if (window.currentPage === 'jobs' || window.currentPage === 'dashboard') {
            // Refresh job list to show new auto-created job
            if (window.jobManager) {
                window.jobManager.loadJobs();
            }
        }

        // Emit custom event
        document.dispatchEvent(new CustomEvent('jobAutoCreated', {
            detail: data
        }));
    }

    /**
     * Show one-time tip about auto-created jobs (first time only)
     */
    showFirstAutoJobTip() {
        const tipKey = 'printernizer_auto_job_tip_shown';

        // Check if tip has been shown before
        if (localStorage.getItem(tipKey) === 'true') {
            return;
        }

        // Mark tip as shown
        localStorage.setItem(tipKey, 'true');

        // Show informative banner with longer duration
        const tipMessage = `
            Aufträge werden jetzt automatisch erstellt!
            Sie finden sie mit dem ⚡ Auto Badge in der Auftragsliste.
            Diese Funktion kann in den Einstellungen deaktiviert werden.
        `;

        showToast('info', 'ℹ️ Automatische Auftrags-Erstellung', tipMessage, 10000, {
            uniqueKey: 'auto_job_first_tip',
            deduplicateMode: 'ignore'
        });

        Logger.debug('First auto-job tip shown');
    }

    /**
     * Handle file updates
     */
    handleFileUpdate(data) {
        Logger.debug('File update:', data);
        
        // Update file lists
        if (window.currentPage === 'files') {
            this.updateFileInList(data);
        }

        // Update download progress
        if (data.status === 'downloading') {
            this.updateDownloadProgress(data);
        } else if (data.status === 'downloaded') {
            showToast('success', 'Download abgeschlossen', `${data.filename} wurde heruntergeladen`);
        }

        // Emit custom event
        document.dispatchEvent(new CustomEvent('fileUpdate', {
            detail: data
        }));
    }

    /**
     * Handle system alerts
     */
    handleSystemAlert(data) {
        Logger.debug('System alert:', data);
        
        const alertType = data.level || 'info';
        showToast(alertType, data.title || 'System-Benachrichtigung', data.message);

        // Emit custom event
        document.dispatchEvent(new CustomEvent('systemAlert', {
            detail: data
        }));
    }

    /**
     * Update printer card with new status
     */
    updatePrinterCard(card, data) {
        // Update status badge
        const statusBadge = card.querySelector('.status-badge');
        if (statusBadge && CONFIG.PRINTER_STATUS[data.status]) {
            const status = CONFIG.PRINTER_STATUS[data.status];
            statusBadge.className = `status-badge ${status.class}`;
            statusBadge.textContent = status.label;
        }

        // Update temperatures
        if (data.temperatures) {
            this.updateTemperatureDisplays(card, data.temperatures);
        }

        // Update current job if present
        if (data.current_job) {
            this.updateCurrentJobDisplay(card, data.current_job);
        }

        // Handle thumbnail updates (new real-time fields)
        if (data.current_job_file_id) {
            const currentJobContainer = card.querySelector('.current-job');
            if (currentJobContainer) {
                let thumbEl = currentJobContainer.querySelector('.job-thumbnail img.thumbnail-image');
                if (data.current_job_has_thumbnail && data.current_job_thumbnail_url) {
                    // Create container if missing
                    if (!thumbEl) {
                        const wrapper = document.createElement('div');
                        wrapper.className = 'job-thumbnail';
                        wrapper.innerHTML = `
                            <img class="thumbnail-image" loading="lazy" alt="Job Thumbnail">
                            <div class="thumbnail-overlay"><i class="fas fa-expand"></i></div>
                        `;
                        currentJobContainer.prepend(wrapper);
                        thumbEl = wrapper.querySelector('img.thumbnail-image');
                    }
                    const newSrc = data.current_job_thumbnail_url;
                    // Avoid flicker if unchanged
                    if (thumbEl.getAttribute('src') !== newSrc) {
                        thumbEl.src = newSrc + `?t=${Date.now()}`; // Bust cache on change
                        thumbEl.dataset.fileId = data.current_job_file_id;
                    }
                } else if (thumbEl) {
                    // Remove thumbnail if no longer available
                    const parent = thumbEl.closest('.job-thumbnail');
                    if (parent) parent.remove();
                }
            }
        }

        // Update last seen time
        const lastSeenElement = card.querySelector('.printer-last-seen');
        if (lastSeenElement && data.last_seen) {
            lastSeenElement.textContent = `Zuletzt gesehen: ${formatDateTime(data.last_seen)}`;
        }
    }

    /**
     * Update job in list
     */
    updateJobInList(data) {
        const jobElement = document.querySelector(`[data-job-id="${data.id}"]`);
        if (jobElement) {
            // Update status
            const statusBadge = jobElement.querySelector('.status-badge');
            if (statusBadge && CONFIG.JOB_STATUS[data.status]) {
                const status = CONFIG.JOB_STATUS[data.status];
                statusBadge.className = `status-badge ${status.class}`;
                statusBadge.textContent = status.label;
            }

            // Update progress
            this.updateJobProgress(jobElement, data);
        }
    }

    /**
     * Update job progress display
     */
    updateJobProgress(element, data) {
        const progressBar = element.querySelector('.progress-bar');
        const progressText = element.querySelector('.progress-text');

        if (progressBar && data.progress !== undefined) {
            progressBar.style.width = `${data.progress}%`;
        }

        if (progressText && data.progress !== undefined) {
            progressText.textContent = `${data.progress.toFixed(1)}%`;
        }

        // Update estimated time
        const timeElement = element.querySelector('.estimated-time');
        if (timeElement && data.estimated_remaining) {
            timeElement.textContent = formatDuration(data.estimated_remaining);
        }
    }

    /**
     * Update file in list
     */
    updateFileInList(data) {
        const fileElement = document.querySelector(`[data-file-id="${data.id}"]`);
        if (fileElement) {
            // Update status
            const statusElement = fileElement.querySelector('.file-status');
            if (statusElement && CONFIG.FILE_STATUS[data.status]) {
                const status = CONFIG.FILE_STATUS[data.status];
                statusElement.textContent = `${status.icon} ${status.label}`;
            }

            // Update download progress if applicable
            if (data.status === 'downloading') {
                this.updateDownloadProgress(data, fileElement);
            }
        }
    }

    /**
     * Update download progress
     */
    updateDownloadProgress(data, element = null) {
        const fileElement = element || document.querySelector(`[data-file-id="${data.file_id}"]`);
        if (!fileElement) return;

        const progressContainer = fileElement.querySelector('.download-progress');
        if (progressContainer) {
            const progressBar = progressContainer.querySelector('.progress-bar');
            const statusText = progressContainer.querySelector('.download-status');

            if (progressBar && data.progress !== undefined) {
                progressBar.style.width = `${data.progress}%`;
            }

            if (statusText) {
                statusText.textContent = `${data.progress?.toFixed(1) || 0}% - ${formatBytes(data.speed_mbps * 1024 * 1024)}/s`;
            }
        }
    }

    /**
     * Update temperature displays
     */
    updateTemperatureDisplays(container, temperatures) {
        Object.entries(temperatures).forEach(([type, temp]) => {
            const tempElement = container.querySelector(`[data-temp-type="${type}"]`);
            if (tempElement && typeof temp === 'object') {
                const valueElement = tempElement.querySelector('.temp-value');
                const targetElement = tempElement.querySelector('.temp-target');
                
                if (valueElement) {
                    valueElement.textContent = `${parseFloat(temp.current).toFixed(1)}°C`;
                    
                    // Add heating indicator
                    if (Math.abs(temp.current - temp.target) > 2) {
                        valueElement.classList.add('temp-heating');
                    } else {
                        valueElement.classList.remove('temp-heating');
                    }
                }
                
                if (targetElement && temp.target) {
                    targetElement.textContent = `Ziel: ${parseFloat(temp.target).toFixed(1)}°C`;
                }
            }
        });
    }

    /**
     * Update current job display
     */
    updateCurrentJobDisplay(container, jobData) {
        const currentJobElement = container.querySelector('.current-job');
        if (currentJobElement) {
            const jobName = currentJobElement.querySelector('.job-name');
            const progressBar = currentJobElement.querySelector('.progress-bar');
            const progressText = currentJobElement.querySelector('.progress-percentage');
            const layerInfo = currentJobElement.querySelector('.layer-info');

            if (jobName) {
                jobName.textContent = jobData.name || jobData.job_name;
            }

            if (progressBar && jobData.progress !== undefined) {
                progressBar.style.width = `${jobData.progress}%`;
            }

            if (progressText && jobData.progress !== undefined) {
                progressText.textContent = `${jobData.progress.toFixed(1)}%`;
            }

            if (layerInfo && jobData.layer_current && jobData.layer_total) {
                layerInfo.innerHTML = `
                    <span>Schicht: ${escapeHtml(String(jobData.layer_current))}/${escapeHtml(String(jobData.layer_total))}</span>
                    <span>Verbleibend: ${formatDuration(jobData.estimated_remaining || 0)}</span>
                `;
            }
        }
    }
}

// Initialize WebSocket client
const wsClient = new WebSocketClient();
const wsHandler = new PrinternizerWebSocketHandler(wsClient);

// Auto-connect when page loads
document.addEventListener('DOMContentLoaded', () => {
    wsClient.connect().catch(error => {
        window.ErrorHandler?.handleWebSocketError(error, { operation: 'initial_connection' });
    });
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    wsClient.disconnect();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { WebSocketClient, PrinternizerWebSocketHandler };
}