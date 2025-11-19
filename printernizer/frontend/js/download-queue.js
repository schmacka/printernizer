/**
 * Download Queue Management System
 * Handles prioritized downloading of printer files with retry logic
 */

class DownloadQueue {
    constructor() {
        this.queue = [];
        this.processing = new Map(); // Currently processing downloads
        this.completed = new Map(); // Completed downloads (last 24h)
        this.failed = new Map(); // Failed downloads (last 24h)
        this.isProcessing = false;
        this.maxConcurrent = 2;
        this.processInterval = null;

        // Queue priorities
        this.priorities = {
            'urgent': 1,    // Critical system downloads
            'high': 2,      // Current job downloads
            'normal': 3,    // Manual downloads
            'low': 4        // Background/maintenance downloads
        };
    }

    /**
     * Initialize the download queue
     */
    async init() {
        Logger.debug('📋 Initializing Download Queue');

        // Start processing queue
        this.startProcessing();

        // Cleanup old completed/failed records every hour
        setInterval(() => {
            this.cleanupOldRecords();
        }, 3600000); // 1 hour
    }

    /**
     * Add a download task to the queue
     */
    async add(task) {
        // Validate task
        if (!task.id || !task.printerId || !task.type) {
            throw new Error('Invalid download task: missing required fields');
        }

        // Set default values
        task.priority = task.priority || 'normal';
        task.attempts = task.attempts || 0;
        task.maxAttempts = task.maxAttempts || 3;
        task.createdAt = task.createdAt || new Date();
        task.status = 'queued';

        // Check if already in queue or processing
        if (this.isTaskInQueue(task.id) || this.processing.has(task.id)) {
            Logger.warn(`Download task ${task.id} already exists`);
            return false;
        }

        // Insert in priority order
        this.insertByPriority(task);

        Logger.debug(`📋 Added download task: ${task.id} (${task.type}, priority: ${task.priority})`);

        // Trigger immediate processing if not busy
        if (!this.isProcessing) {
            this.processNext();
        }

        return true;
    }

    /**
     * Insert task in queue based on priority
     */
    insertByPriority(task) {
        const taskPriority = this.priorities[task.priority] || this.priorities.normal;

        let insertIndex = this.queue.length;
        for (let i = 0; i < this.queue.length; i++) {
            const queuePriority = this.priorities[this.queue[i].priority] || this.priorities.normal;
            if (taskPriority < queuePriority) {
                insertIndex = i;
                break;
            }
        }

        this.queue.splice(insertIndex, 0, task);
    }

    /**
     * Check if task is already in queue
     */
    isTaskInQueue(taskId) {
        return this.queue.some(task => task.id === taskId);
    }

    /**
     * Start queue processing
     */
    startProcessing() {
        this.processInterval = setInterval(() => {
            this.processNext();
        }, 1000); // Check every second
    }

    /**
     * Process next items in queue
     */
    async processNext() {
        if (this.processing.size >= this.maxConcurrent || this.queue.length === 0) {
            return;
        }

        const task = this.queue.shift();
        this.processing.set(task.id, task);

        Logger.debug(`🔄 Processing download: ${task.id}`);

        try {
            task.status = 'processing';
            task.startedAt = new Date();

            // Update UI
            this.notifyTaskUpdate(task);

            // Execute download based on type
            const result = await this.executeDownload(task);

            // Mark as completed
            task.status = 'completed';
            task.completedAt = new Date();
            task.result = result;

            this.processing.delete(task.id);
            this.completed.set(task.id, task);

            Logger.debug(`✅ Download completed: ${task.id}`);

            // Trigger thumbnail processing if file was downloaded
            if (result.success && result.fileId) {
                await this.triggerThumbnailProcessing(task, result);
            }

        } catch (error) {
            Logger.error(`❌ Download failed: ${task.id}`, error);

            task.attempts += 1;
            task.lastError = error.message;
            task.lastAttemptAt = new Date();

            if (task.attempts < task.maxAttempts) {
                // Retry with exponential backoff
                const delay = Math.min(5000 * Math.pow(2, task.attempts - 1), 60000);

                setTimeout(() => {
                    task.status = 'retrying';
                    this.insertByPriority(task);
                    Logger.debug(`🔄 Retrying download: ${task.id} (attempt ${task.attempts + 1})`);
                }, delay);

            } else {
                // Mark as failed
                task.status = 'failed';
                task.failedAt = new Date();

                this.processing.delete(task.id);
                this.failed.set(task.id, task);

                Logger.error(`💥 Download permanently failed: ${task.id}`);
            }
        }

        // Update UI
        this.notifyTaskUpdate(task);
    }

    /**
     * Execute download based on task type
     */
    async executeDownload(task) {
        switch (task.type) {
            case 'current_job':
                return await this.downloadCurrentJob(task);
            case 'printer_file':
                return await this.downloadPrinterFile(task);
            case 'manual':
                return await this.downloadCurrentJob(task); // Default to current job
            default:
                throw new Error(`Unknown download type: ${task.type}`);
        }
    }

    /**
     * Download current job file from printer
     */
    async downloadCurrentJob(task) {
        try {
            Logger.debug(`📥 Downloading current job from printer ${task.printerId}`);

            const response = await api.downloadCurrentJobFile(task.printerId);

            // Log the full response for debugging
            Logger.debug('Download API response:', response);

            if (!response) {
                throw new Error('No response from download API');
            }

            if (!response.status) {
                Logger.error('Response missing status field:', response);
                throw new Error('Invalid response from download API: missing status field');
            }

            // Handle different response statuses
            switch (response.status) {
                case 'success':
                case 'processed':
                case 'exists_with_thumbnail':
                    return {
                        success: true,
                        status: response.status,
                        fileId: response.file_id,
                        filename: response.filename,
                        hasThumbnail: response.has_thumbnail || false,
                        message: response.message || 'Download successful'
                    };

                case 'exists_no_thumbnail':
                    return {
                        success: true,
                        status: response.status,
                        fileId: response.file_id,
                        filename: response.filename,
                        hasThumbnail: false,
                        message: 'File exists but no thumbnail available'
                    };

                case 'not_printing':
                    throw new Error('Printer is not currently printing');

                case 'no_file':
                    throw new Error('No file available for current job');

                case 'no_active_job':
                    throw new Error('No active print job currently running');

                case 'error':
                    throw new Error(response.message || response.error || 'Download failed with error status');

                case 'failed':
                    throw new Error(response.message || response.error || 'Download failed');

                case 'timeout':
                    throw new Error('Download request timed out');

                case 'connection_error':
                    throw new Error('Connection error: ' + (response.message || 'Unable to connect to printer'));

                case 'file_not_found':
                    throw new Error('File not found on printer');

                case 'access_denied':
                    throw new Error('Access denied: ' + (response.message || 'Insufficient permissions'));

                default:
                    // Log the full response for debugging
                    Logger.error('Unknown download response:', response);
                    throw new Error(`Unknown download status: ${response.status}. Message: ${response.message || 'No additional details'}`);
            }

        } catch (error) {
            Logger.error('Download current job failed:', error);
            throw error;
        }
    }

    /**
     * Download specific printer file
     */
    async downloadPrinterFile(task) {
        try {
            Logger.debug(`📥 Downloading file ${task.filename} from printer ${task.printerId}`);

            const response = await api.downloadPrinterFile(task.printerId, task.filename);

            return {
                success: true,
                status: 'downloaded',
                fileId: response.file_id,
                filename: task.filename,
                hasThumbnail: response.has_thumbnail || false,
                message: 'File downloaded successfully'
            };

        } catch (error) {
            Logger.error('Download printer file failed:', error);
            throw error;
        }
    }

    /**
     * Trigger thumbnail processing for downloaded file
     */
    async triggerThumbnailProcessing(task, result) {
        if (!result.fileId) return;

        // Add to thumbnail queue if it doesn't have a thumbnail
        if (!result.hasThumbnail && window.thumbnailQueue) {
            const thumbnailTask = {
                id: `thumb_${result.fileId}_${Date.now()}`,
                fileId: result.fileId,
                filename: result.filename,
                downloadTaskId: task.id,
                priority: task.priority,
                createdAt: new Date()
            };

            await window.thumbnailQueue.add(thumbnailTask);
        }
    }

    /**
     * Notify UI of task updates
     */
    notifyTaskUpdate(task) {
        // Dispatch custom event for UI updates
        const event = new CustomEvent('downloadTaskUpdate', {
            detail: {
                task: { ...task },
                queueStats: this.getStats()
            }
        });
        document.dispatchEvent(event);
    }

    /**
     * Get queue statistics
     */
    getStats() {
        const now = new Date();
        const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);

        return {
            queued: this.queue.length,
            processing: this.processing.size,
            completed: Array.from(this.completed.values()).filter(t => t.completedAt > last24h).length,
            failed: Array.from(this.failed.values()).filter(t => t.failedAt > last24h).length,
            totalCompleted: this.completed.size,
            totalFailed: this.failed.size
        };
    }

    /**
     * Get current queue contents
     */
    getQueueContents() {
        return {
            queued: [...this.queue],
            processing: Array.from(this.processing.values()),
            recentCompleted: Array.from(this.completed.values()).slice(-10),
            recentFailed: Array.from(this.failed.values()).slice(-10)
        };
    }

    /**
     * Clear completed and failed records older than 24 hours
     */
    cleanupOldRecords() {
        const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000);

        // Clean completed
        for (const [id, task] of this.completed.entries()) {
            if (task.completedAt < cutoff) {
                this.completed.delete(id);
            }
        }

        // Clean failed
        for (const [id, task] of this.failed.entries()) {
            if (task.failedAt < cutoff) {
                this.failed.delete(id);
            }
        }
    }

    /**
     * Cancel a queued task
     */
    cancel(taskId) {
        // Remove from queue if queued
        this.queue = this.queue.filter(task => task.id !== taskId);

        // Cancel if processing (limited cancellation support)
        if (this.processing.has(taskId)) {
            const task = this.processing.get(taskId);
            task.status = 'cancelled';
            this.processing.delete(taskId);

            Logger.debug(`❌ Cancelled download: ${taskId}`);
            return true;
        }

        return false;
    }

    /**
     * Shutdown queue processing
     */
    async shutdown() {
        Logger.debug('🛑 Shutting down Download Queue');

        if (this.processInterval) {
            clearInterval(this.processInterval);
        }

        // Wait for current downloads to complete (with timeout)
        const timeout = 30000; // 30 seconds
        const start = Date.now();

        while (this.processing.size > 0 && (Date.now() - start) < timeout) {
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        Logger.debug('📋 Download Queue shut down');
    }
}

// Export for use in other modules
window.DownloadQueue = DownloadQueue;