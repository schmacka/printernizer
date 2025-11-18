/**
 * Auto-Download System UI Components
 * Provides user interface for monitoring and managing the auto-download system
 */

class AutoDownloadUI {
    constructor() {
        this.container = null;
        this.autoDownloadManager = null;
        this.updateInterval = null;
        this.isVisible = false;
    }

    /**
     * Initialize the Auto-Download UI
     */
    async init(autoDownloadManager) {
        this.autoDownloadManager = autoDownloadManager;

        // Add system status to dashboard
        this.addSystemStatusToDashboard();

        // Setup event listeners for queue updates
        this.setupEventListeners();

        // Start periodic UI updates
        this.startPeriodicUpdates();

        Logger.debug('🖥️ Auto-Download UI initialized');
    }

    /**
     * Add system status indicator to dashboard
     */
    addSystemStatusToDashboard() {
        // Find a good location in the dashboard to add the status
        const dashboardContainer = document.querySelector('.overview-cards') || document.querySelector('.dashboard-content');

        if (dashboardContainer) {
            const statusCard = document.createElement('div');
            statusCard.className = 'card overview-card';
            statusCard.innerHTML = `
                <div class="card-header">
                    <h3>Auto-Download</h3>
                    <span class="card-icon">🤖</span>
                </div>
                <div class="card-body">
                    <div class="stat-number" id="auto-download-count">-</div>
                    <div class="stat-label" id="auto-download-label">Initializing</div>
                    <div class="stat-detail" id="auto-download-detail">System starting...</div>
                    <button class="btn btn-sm btn-secondary" onclick="autoDownloadUI.showManagementPanel()" style="margin-top: 1rem;">
                        <span class="btn-icon">⚙️</span> Verwalten
                    </button>
                </div>
            `;
            dashboardContainer.appendChild(statusCard);
        }
    }

    /**
     * Setup event listeners for queue updates
     */
    setupEventListeners() {
        // Listen for download queue updates
        document.addEventListener('downloadTaskUpdate', (event) => {
            this.handleDownloadUpdate(event.detail);
        });

        // Listen for thumbnail queue updates
        document.addEventListener('thumbnailTaskUpdate', (event) => {
            this.handleThumbnailUpdate(event.detail);
        });

        // Listen for thumbnail processing completion
        document.addEventListener('thumbnailProcessingComplete', (event) => {
            this.handleThumbnailComplete(event.detail);
        });
    }

    /**
     * Handle download queue updates
     */
    handleDownloadUpdate(detail) {
        const { task, queueStats } = detail;

        // Show toast notifications for important events
        if (task.status === 'completed') {
            showToast('success', 'Download Complete',
                `${task.jobName || 'File'} downloaded from ${task.printerName}`);
        } else if (task.status === 'failed') {
            showToast('error', 'Download Failed',
                `Failed to download from ${task.printerName}: ${task.lastError}`);
        }

        // Update dashboard card
        this.updateDashboardCard();

        // Update UI if management panel is open
        if (this.isVisible) {
            this.updateQueueDisplay();
        }
    }

    /**
     * Handle thumbnail queue updates
     */
    handleThumbnailUpdate(detail) {
        const { task, queueStats } = detail;

        if (task.status === 'completed') {
            showToast('info', 'Thumbnail Ready',
                `Thumbnail processed for ${task.filename || 'file'}`);
        } else if (task.status === 'failed') {
            showToast('warn', 'Thumbnail Failed',
                `Could not process thumbnail for ${task.filename || 'file'}`);
        }

        // Update dashboard card
        this.updateDashboardCard();

        // Update UI if management panel is open
        if (this.isVisible) {
            this.updateQueueDisplay();
        }
    }

    /**
     * Handle thumbnail processing completion
     */
    handleThumbnailComplete(detail) {
        // Refresh any printer cards or file displays that might need the new thumbnail
        const event = new CustomEvent('thumbnailUpdated', {
            detail: {
                fileId: detail.fileId,
                thumbnailUrl: detail.result.thumbnailUrl
            }
        });
        document.dispatchEvent(event);
    }

    /**
     * Update the dashboard card with current stats
     */
    updateDashboardCard() {
        if (!this.autoDownloadManager) return;

        const stats = this.autoDownloadManager.getStats();
        const countElement = document.getElementById('auto-download-count');
        const labelElement = document.getElementById('auto-download-label');
        const detailElement = document.getElementById('auto-download-detail');

        if (!countElement || !labelElement || !detailElement) return;

        // Calculate active tasks (queued + processing)
        const activeDownloads = stats.downloads.queued + stats.downloads.processing;
        const activeThumbnails = stats.thumbnails.queued + stats.thumbnails.processing;
        const totalActive = activeDownloads + activeThumbnails;

        // Update count
        countElement.textContent = totalActive;

        // Update label based on activity
        if (totalActive > 0) {
            labelElement.textContent = 'Active Tasks';
        } else if (stats.system.active) {
            labelElement.textContent = 'System Active';
        } else {
            labelElement.textContent = 'System Inactive';
        }

        // Update detail text
        const detailParts = [];
        if (activeDownloads > 0) {
            detailParts.push(`${activeDownloads} download${activeDownloads !== 1 ? 's' : ''}`);
        }
        if (activeThumbnails > 0) {
            detailParts.push(`${activeThumbnails} thumbnail${activeThumbnails !== 1 ? 's' : ''}`);
        }
        if (detailParts.length === 0) {
            if (stats.downloads.completed > 0 || stats.thumbnails.completed > 0) {
                detailElement.textContent = `${stats.downloads.completed} downloads today`;
            } else {
                detailElement.textContent = stats.system.active ? 'Monitoring...' : 'Idle';
            }
        } else {
            detailElement.textContent = detailParts.join(', ');
        }
    }

    /**
     * Show the management panel modal
     */
    showManagementPanel() {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h3>🤖 Auto-Download System Management</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">×</button>
                </div>
                <div class="modal-body" style="padding: 0; max-height: 80vh; overflow-y: auto;">
                    <div class="auto-download-management">
                        ${this.renderManagementInterface()}
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.container = modal.querySelector('.auto-download-management');
        this.isVisible = true;

        // Setup modal close handler
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
                this.isVisible = false;
            }
        });

        // Initial queue display update
        this.updateQueueDisplay();
    }

    /**
     * Render the management interface
     */
    renderManagementInterface() {
        const stats = this.autoDownloadManager.getStats();

        return `
            <div class="management-header">
                <div class="system-overview">
                    <div class="overview-grid">
                        <div class="overview-item">
                            <div class="item-icon ${stats.system.active ? 'status-active' : 'status-inactive'}">
                                ${stats.system.active ? '✅' : '❌'}
                            </div>
                            <div class="item-content">
                                <div class="item-title">System Status</div>
                                <div class="item-value">${stats.system.active ? 'Active' : 'Inactive'}</div>
                            </div>
                        </div>
                        <div class="overview-item">
                            <div class="item-icon">🔍</div>
                            <div class="item-content">
                                <div class="item-title">Auto-Detection</div>
                                <div class="item-value">${stats.system.autoDetectionEnabled ? 'Enabled' : 'Disabled'}</div>
                            </div>
                        </div>
                        <div class="overview-item">
                            <div class="item-icon">🖨️</div>
                            <div class="item-content">
                                <div class="item-title">Monitored Printers</div>
                                <div class="item-value">${stats.system.monitoredPrinters}</div>
                            </div>
                        </div>
                        <div class="overview-item">
                            <div class="item-icon">📥</div>
                            <div class="item-content">
                                <div class="item-title">Downloads Today</div>
                                <div class="item-value">${stats.downloads.completed}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="system-controls">
                    <button class="btn ${stats.system.autoDetectionEnabled ? 'btn-warning' : 'btn-success'}"
                            onclick="autoDownloadUI.toggleAutoDetection()">
                        ${stats.system.autoDetectionEnabled ? '⏸️ Disable Auto-Detection' : '▶️ Enable Auto-Detection'}
                    </button>
                    <button class="btn btn-secondary" onclick="autoDownloadUI.showLogs()">
                        📋 View Logs
                    </button>
                    <button class="btn btn-secondary" onclick="autoDownloadUI.exportLogs()">
                        💾 Export Logs
                    </button>
                </div>
            </div>

            <div class="queue-tabs">
                <button class="tab-btn active" onclick="autoDownloadUI.showTab('downloads')">
                    📥 Downloads (${stats.downloads.queued + stats.downloads.processing})
                </button>
                <button class="tab-btn" onclick="autoDownloadUI.showTab('thumbnails')">
                    🖼️ Thumbnails (${stats.thumbnails.queued + stats.thumbnails.processing})
                </button>
                <button class="tab-btn" onclick="autoDownloadUI.showTab('history')">
                    📊 History
                </button>
            </div>

            <div class="queue-content">
                <div id="downloads-tab" class="tab-content active">
                    <div id="download-queue-display">Loading...</div>
                </div>
                <div id="thumbnails-tab" class="tab-content">
                    <div id="thumbnail-queue-display">Loading...</div>
                </div>
                <div id="history-tab" class="tab-content">
                    <div id="history-display">Loading...</div>
                </div>
            </div>
        `;
    }

    /**
     * Update queue displays
     */
    updateQueueDisplay() {
        if (!this.container) return;

        // Update download queue
        const downloadQueue = this.autoDownloadManager.downloadQueue.getQueueContents();
        const downloadDisplay = this.container.querySelector('#download-queue-display');
        if (downloadDisplay) {
            downloadDisplay.innerHTML = this.renderDownloadQueue(downloadQueue);
        }

        // Update thumbnail queue
        const thumbnailQueue = this.autoDownloadManager.thumbnailQueue.getQueueContents();
        const thumbnailDisplay = this.container.querySelector('#thumbnail-queue-display');
        if (thumbnailDisplay) {
            thumbnailDisplay.innerHTML = this.renderThumbnailQueue(thumbnailQueue);
        }

        // Update history
        const historyDisplay = this.container.querySelector('#history-display');
        if (historyDisplay) {
            historyDisplay.innerHTML = this.renderHistory();
        }
    }

    /**
     * Render download queue
     */
    renderDownloadQueue(queue) {
        let html = '<div class="queue-section">';

        // Processing
        if (queue.processing.length > 0) {
            html += '<h4>🔄 Currently Processing</h4>';
            queue.processing.forEach(task => {
                html += this.renderDownloadTask(task, 'processing');
            });
        }

        // Queued
        if (queue.queued.length > 0) {
            html += '<h4>⏳ Queued</h4>';
            queue.queued.forEach(task => {
                html += this.renderDownloadTask(task, 'queued');
            });
        }

        // Recent completed
        if (queue.recentCompleted.length > 0) {
            html += '<h4>✅ Recently Completed</h4>';
            queue.recentCompleted.forEach(task => {
                html += this.renderDownloadTask(task, 'completed');
            });
        }

        // Recent failed
        if (queue.recentFailed.length > 0) {
            html += '<h4>❌ Recent Failures</h4>';
            queue.recentFailed.forEach(task => {
                html += this.renderDownloadTask(task, 'failed');
            });
        }

        if (queue.processing.length === 0 && queue.queued.length === 0 &&
            queue.recentCompleted.length === 0 && queue.recentFailed.length === 0) {
            html += '<div class="empty-state">No download activity</div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * Render individual download task
     */
    renderDownloadTask(task, section) {
        const elapsed = task.startedAt ?
            ((new Date() - new Date(task.startedAt)) / 1000).toFixed(1) : 0;

        // Format error message properly
        let errorMessage = '';
        if (task.lastError) {
            if (typeof task.lastError === 'object') {
                errorMessage = task.lastError.message || JSON.stringify(task.lastError);
            } else {
                errorMessage = task.lastError;
            }
        }

        return `
            <div class="task-item ${section}">
                <div class="task-info">
                    <div class="task-title">${escapeHtml(task.jobName || 'Unknown Job')}</div>
                    <div class="task-subtitle">${escapeHtml(task.printerName)} • ${task.type} • Priority: ${task.priority}</div>
                    <div class="task-timing">
                        Created: ${new Date(task.createdAt).toLocaleString('de-DE')}
                        ${task.startedAt ? ` • Started: ${new Date(task.startedAt).toLocaleString('de-DE')}` : ''}
                        ${section === 'processing' ? ` • Elapsed: ${elapsed}s` : ''}
                        ${task.attempts > 0 ? ` • Attempts: ${task.attempts}/${task.maxAttempts}` : ''}
                    </div>
                    ${errorMessage ? `<div class="task-error">Error: ${escapeHtml(errorMessage)}</div>` : ''}
                    ${task.result && section === 'completed' ? `<div class="task-success">✅ ${escapeHtml(task.result.message || 'Completed successfully')}</div>` : ''}
                </div>
                <div class="task-actions">
                    ${section === 'queued' ? `<button class="btn btn-sm btn-warning" onclick="autoDownloadUI.cancelTask('download', '${sanitizeAttribute(task.id)}')">Cancel</button>` : ''}
                    ${section === 'failed' && task.attempts < task.maxAttempts ? `<button class="btn btn-sm btn-primary" onclick="autoDownloadUI.retryTask('download', '${sanitizeAttribute(task.id)}')">Retry</button>` : ''}
                    ${section === 'failed' ? `<button class="btn btn-sm btn-secondary" onclick="autoDownloadUI.showTaskDetails('${sanitizeAttribute(task.id)}')">Details</button>` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Render thumbnail queue
     */
    renderThumbnailQueue(queue) {
        let html = '<div class="queue-section">';

        // Processing
        if (queue.processing.length > 0) {
            html += '<h4>🔄 Currently Processing</h4>';
            queue.processing.forEach(task => {
                html += this.renderThumbnailTask(task, 'processing');
            });
        }

        // Queued
        if (queue.queued.length > 0) {
            html += '<h4>⏳ Queued</h4>';
            queue.queued.forEach(task => {
                html += this.renderThumbnailTask(task, 'queued');
            });
        }

        // Recent completed
        if (queue.recentCompleted.length > 0) {
            html += '<h4>✅ Recently Completed</h4>';
            queue.recentCompleted.forEach(task => {
                html += this.renderThumbnailTask(task, 'completed');
            });
        }

        // Recent failed
        if (queue.recentFailed.length > 0) {
            html += '<h4>❌ Recent Failures</h4>';
            queue.recentFailed.forEach(task => {
                html += this.renderThumbnailTask(task, 'failed');
            });
        }

        if (queue.processing.length === 0 && queue.queued.length === 0 &&
            queue.recentCompleted.length === 0 && queue.recentFailed.length === 0) {
            html += '<div class="empty-state">No thumbnail processing activity</div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * Render individual thumbnail task
     */
    renderThumbnailTask(task, section) {
        const elapsed = task.startedAt ?
            ((new Date() - new Date(task.startedAt)) / 1000).toFixed(1) : 0;

        return `
            <div class="task-item ${section}">
                <div class="task-info">
                    <div class="task-title">${escapeHtml(task.filename || 'Unknown File')}</div>
                    <div class="task-subtitle">${task.fileType?.toUpperCase()} • Method: ${escapeHtml(task.method)} • Priority: ${task.priority}</div>
                    <div class="task-timing">
                        Created: ${new Date(task.createdAt).toLocaleString('de-DE')}
                        ${task.startedAt ? ` • Started: ${new Date(task.startedAt).toLocaleString('de-DE')}` : ''}
                        ${section === 'processing' ? ` • Elapsed: ${elapsed}s` : ''}
                    </div>
                    ${task.lastError ? `<div class="task-error">Error: ${escapeHtml(task.lastError)}</div>` : ''}
                </div>
                <div class="task-actions">
                    ${section === 'queued' ? `<button class="btn btn-sm btn-warning" onclick="autoDownloadUI.cancelTask('thumbnail', '${sanitizeAttribute(task.id)}')">Cancel</button>` : ''}
                    ${section === 'failed' && task.attempts < task.maxAttempts ? `<button class="btn btn-sm btn-primary" onclick="autoDownloadUI.retryTask('thumbnail', '${sanitizeAttribute(task.id)}')">Retry</button>` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Render history view
     */
    renderHistory() {
        const history = this.autoDownloadManager.getDownloadHistory(7);
        const errors = this.autoDownloadManager.getErrorLog(7);

        let html = '<div class="history-section">';

        html += '<h4>📥 Recent Downloads (Last 7 Days)</h4>';
        if (history.length > 0) {
            html += '<div class="history-list">';
            history.forEach(item => {
                html += `
                    <div class="history-item">
                        <div class="history-info">
                            <strong>${escapeHtml(item.result.filename || 'Unknown File')}</strong>
                            <span class="history-printer">from ${escapeHtml(item.printerId)}</span>
                        </div>
                        <div class="history-time">${new Date(item.timestamp).toLocaleString('de-DE')}</div>
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<div class="empty-state">No recent downloads</div>';
        }

        html += '<h4>❌ Recent Errors (Last 7 Days)</h4>';
        if (errors.length > 0) {
            html += '<div class="error-list">';
            errors.slice(-10).forEach(error => {
                html += `
                    <div class="error-item">
                        <div class="error-info">
                            <strong>${escapeHtml(error.category)}</strong>: ${escapeHtml(error.message)}
                            ${error.data.taskId ? `<span class="error-task">Task: ${escapeHtml(error.data.taskId)}</span>` : ''}
                        </div>
                        <div class="error-time">${new Date(error.timestamp).toLocaleString('de-DE')}</div>
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<div class="empty-state">No recent errors</div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * Tab management
     */
    showTab(tabName) {
        if (!this.container) return;

        // Update tab buttons
        this.container.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        this.container.querySelector(`[onclick="autoDownloadUI.showTab('${tabName}')"]`).classList.add('active');

        // Update tab content
        this.container.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        this.container.querySelector(`#${tabName}-tab`).classList.add('active');

        // Update display
        this.updateQueueDisplay();
    }

    /**
     * Toggle auto-detection
     */
    toggleAutoDetection() {
        const currentState = this.autoDownloadManager.config.autoDetectionEnabled;
        this.autoDownloadManager.setAutoDetection(!currentState);

        // Refresh the management panel
        if (this.container) {
            this.container.innerHTML = this.renderManagementInterface();
            this.updateQueueDisplay();
        }
    }

    /**
     * Show logs modal
     */
    showLogs() {
        // Implementation for detailed log viewing
        showToast('info', 'Feature Coming Soon', 'Detailed log viewer will be available in the next update');
    }

    /**
     * Export logs
     */
    exportLogs() {
        const logs = this.autoDownloadManager.logger.exportLogs(7);
        const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `printernizer_logs_${new Date().toISOString().split('T')[0]}.json`;
        a.click();

        URL.revokeObjectURL(url);
        showToast('success', 'Logs Exported', 'Download logs have been exported successfully');
    }

    /**
     * Cancel a task
     */
    cancelTask(queueType, taskId) {
        if (queueType === 'download') {
            this.autoDownloadManager.downloadQueue.cancel(taskId);
        } else if (queueType === 'thumbnail') {
            this.autoDownloadManager.thumbnailQueue.cancel(taskId);
        }

        showToast('info', 'Task Cancelled', 'Task has been removed from the queue');
        this.updateQueueDisplay();
    }

    /**
     * Retry a failed task
     */
    retryTask(queueType, taskId) {
        // Implementation would depend on queue structure
        showToast('info', 'Feature Coming Soon', 'Manual retry will be available in the next update');
    }

    /**
     * Show detailed task information
     */
    showTaskDetails(taskId) {
        // Find the task in either queue
        let task = null;
        const downloadQueue = this.autoDownloadManager.downloadQueue.getQueueContents();
        const thumbnailQueue = this.autoDownloadManager.thumbnailQueue.getQueueContents();

        // Search in all task arrays
        const allTasks = [
            ...downloadQueue.queued,
            ...downloadQueue.processing,
            ...downloadQueue.recentCompleted,
            ...downloadQueue.recentFailed,
            ...thumbnailQueue.queued,
            ...thumbnailQueue.processing,
            ...thumbnailQueue.recentCompleted,
            ...thumbnailQueue.recentFailed
        ];

        task = allTasks.find(t => t.id === taskId);

        if (!task) {
            showToast('error', 'Task Not Found', 'Could not find task details');
            return;
        }

        // Create details modal
        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>📋 Task Details</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="task-details">
                        <h4>Task Information</h4>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <strong>ID:</strong> ${escapeHtml(task.id)}
                            </div>
                            <div class="detail-item">
                                <strong>Type:</strong> ${task.type}
                            </div>
                            <div class="detail-item">
                                <strong>Status:</strong> ${task.status}
                            </div>
                            <div class="detail-item">
                                <strong>Priority:</strong> ${task.priority}
                            </div>
                            <div class="detail-item">
                                <strong>Printer:</strong> ${escapeHtml(task.printerName || 'Unknown')} (${escapeHtml(task.printerId)})
                            </div>
                            <div class="detail-item">
                                <strong>Job/File:</strong> ${escapeHtml(task.jobName || task.filename || 'Unknown')}
                            </div>
                            <div class="detail-item">
                                <strong>Created:</strong> ${new Date(task.createdAt).toLocaleString('de-DE')}
                            </div>
                            ${task.startedAt ? `<div class="detail-item"><strong>Started:</strong> ${new Date(task.startedAt).toLocaleString('de-DE')}</div>` : ''}
                            ${task.completedAt ? `<div class="detail-item"><strong>Completed:</strong> ${new Date(task.completedAt).toLocaleString('de-DE')}</div>` : ''}
                            ${task.failedAt ? `<div class="detail-item"><strong>Failed:</strong> ${new Date(task.failedAt).toLocaleString('de-DE')}</div>` : ''}
                            <div class="detail-item">
                                <strong>Attempts:</strong> ${task.attempts}/${task.maxAttempts}
                            </div>
                            <div class="detail-item">
                                <strong>Auto-triggered:</strong> ${task.autoTriggered ? 'Yes' : 'No'}
                            </div>
                        </div>

                        ${task.lastError ? `
                            <h4>Error Information</h4>
                            <div class="error-details">
                                <pre>${escapeHtml(typeof task.lastError === 'object' ? JSON.stringify(task.lastError, null, 2) : task.lastError)}</pre>
                                ${task.lastAttemptAt ? `<p><strong>Last Attempt:</strong> ${new Date(task.lastAttemptAt).toLocaleString('de-DE')}</p>` : ''}
                            </div>
                        ` : ''}

                        ${task.result ? `
                            <h4>Result Information</h4>
                            <div class="result-details">
                                <pre>${escapeHtml(JSON.stringify(task.result, null, 2))}</pre>
                            </div>
                        ` : ''}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
                    ${task.status === 'failed' && task.attempts < task.maxAttempts ?
                        `<button class="btn btn-primary" onclick="autoDownloadUI.retryTask('download', '${sanitizeAttribute(task.id)}'); this.closest('.modal').remove();">Retry Task</button>` : ''}
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * Start periodic UI updates
     */
    startPeriodicUpdates() {
        // Initial update
        this.updateDashboardCard();

        this.updateInterval = setInterval(() => {
            // Always update dashboard card
            this.updateDashboardCard();

            // Update management panel if visible
            if (this.isVisible) {
                this.updateQueueDisplay();
            }
        }, 5000); // Update every 5 seconds
    }

    /**
     * Cleanup
     */
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Create global instance
window.autoDownloadUI = new AutoDownloadUI();