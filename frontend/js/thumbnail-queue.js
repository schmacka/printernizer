/**
 * Thumbnail Processing Queue System
 * Handles thumbnail generation and extraction for 3D files
 */

class ThumbnailQueue {
    constructor() {
        this.queue = [];
        this.processing = new Map();
        this.completed = new Map();
        this.failed = new Map();
        this.isProcessing = false;
        this.maxConcurrent = 1; // Process one thumbnail at a time
        this.processInterval = null;

        // Supported file types for thumbnail processing
        this.supportedTypes = {
            '3mf': { priority: 1, method: 'extract' },
            'stl': { priority: 2, method: 'generate' },
            'obj': { priority: 2, method: 'generate' },
            'gcode': { priority: 3, method: 'analyze' },
            'bgcode': { priority: 1, method: 'extract' }
        };
    }

    /**
     * Initialize the thumbnail queue
     */
    async init() {
        Logger.debug('🖼️ Initializing Thumbnail Queue');

        // Start processing queue
        this.startProcessing();

        // Cleanup old records every hour
        setInterval(() => {
            this.cleanupOldRecords();
        }, 3600000); // 1 hour
    }

    /**
     * Add a thumbnail processing task to the queue
     */
    async add(task) {
        // Validate task
        if (!task.id || !task.fileId) {
            throw new Error('Invalid thumbnail task: missing required fields');
        }

        // Check if already in queue or processing
        if (this.isTaskInQueue(task.id) || this.processing.has(task.id)) {
            Logger.warn(`Thumbnail task ${task.id} already exists`);
            return false;
        }

        // Determine file type and processing method
        const fileExt = this.getFileExtension(task.filename || '');
        const typeInfo = this.supportedTypes[fileExt.toLowerCase()];

        if (!typeInfo) {
            Logger.warn(`Unsupported file type for thumbnail: ${fileExt}`);
            return false;
        }

        // Set task properties
        task.fileType = fileExt.toLowerCase();
        task.method = typeInfo.method;
        task.priority = task.priority || 'normal';
        task.attempts = task.attempts || 0;
        task.maxAttempts = task.maxAttempts || 2;
        task.createdAt = task.createdAt || new Date();
        task.status = 'queued';

        // Insert in priority order
        this.insertByPriority(task);

        Logger.debug(`🖼️ Added thumbnail task: ${task.id} (${task.fileType}, method: ${task.method})`);

        // Trigger immediate processing if not busy
        if (!this.isProcessing) {
            this.processNext();
        }

        return true;
    }

    /**
     * Get file extension from filename
     */
    getFileExtension(filename) {
        const parts = filename.toLowerCase().split('.');
        return parts.length > 1 ? parts[parts.length - 1] : '';
    }

    /**
     * Insert task in queue based on file type priority and task priority
     */
    insertByPriority(task) {
        const typePriority = this.supportedTypes[task.fileType]?.priority || 5;
        const taskPriorityValue = this.getPriorityValue(task.priority);

        // Combined priority (lower is better)
        const combinedPriority = (typePriority * 10) + taskPriorityValue;

        let insertIndex = this.queue.length;
        for (let i = 0; i < this.queue.length; i++) {
            const queueTypePriority = this.supportedTypes[this.queue[i].fileType]?.priority || 5;
            const queueTaskPriority = this.getPriorityValue(this.queue[i].priority);
            const queueCombinedPriority = (queueTypePriority * 10) + queueTaskPriority;

            if (combinedPriority < queueCombinedPriority) {
                insertIndex = i;
                break;
            }
        }

        this.queue.splice(insertIndex, 0, task);
    }

    /**
     * Get numeric priority value
     */
    getPriorityValue(priority) {
        const priorities = {
            'urgent': 1,
            'high': 2,
            'normal': 3,
            'low': 4
        };
        return priorities[priority] || priorities.normal;
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
        }, 2000); // Check every 2 seconds
    }

    /**
     * Process next item in queue
     */
    async processNext() {
        if (this.processing.size >= this.maxConcurrent || this.queue.length === 0) {
            return;
        }

        const task = this.queue.shift();
        this.processing.set(task.id, task);

        Logger.debug(`🖼️ Processing thumbnail: ${task.id} (${task.method})`);

        try {
            task.status = 'processing';
            task.startedAt = new Date();

            // Update UI
            this.notifyTaskUpdate(task);

            // Execute thumbnail processing based on method
            const result = await this.processThumbnail(task);

            // Mark as completed
            task.status = 'completed';
            task.completedAt = new Date();
            task.result = result;

            this.processing.delete(task.id);
            this.completed.set(task.id, task);

            Logger.debug(`✅ Thumbnail completed: ${task.id}`);

            // Notify download queue of completion
            this.notifyThumbnailComplete(task, result);

        } catch (error) {
            Logger.error(`❌ Thumbnail processing failed: ${task.id}`, error);

            task.attempts += 1;
            task.lastError = error.message;
            task.lastAttemptAt = new Date();

            if (task.attempts < task.maxAttempts) {
                // Retry with delay
                setTimeout(() => {
                    task.status = 'retrying';
                    this.insertByPriority(task);
                    Logger.debug(`🔄 Retrying thumbnail: ${task.id} (attempt ${task.attempts + 1})`);
                }, 10000); // 10 second delay

            } else {
                // Mark as failed
                task.status = 'failed';
                task.failedAt = new Date();

                this.processing.delete(task.id);
                this.failed.set(task.id, task);

                Logger.error(`💥 Thumbnail permanently failed: ${task.id}`);
            }
        }

        // Update UI
        this.notifyTaskUpdate(task);
    }

    /**
     * Process thumbnail based on method
     */
    async processThumbnail(task) {
        switch (task.method) {
            case 'extract':
                return await this.extractThumbnail(task);
            case 'generate':
                return await this.generateThumbnail(task);
            case 'analyze':
                return await this.analyzeThumbnail(task);
            default:
                throw new Error(`Unknown thumbnail method: ${task.method}`);
        }
    }

    /**
     * Extract embedded thumbnail from file
     */
    async extractThumbnail(task) {
        try {
            Logger.debug(`🔍 Extracting thumbnail from ${task.fileType} file: ${task.fileId}`);

            const response = await api.extractFileThumbnail(task.fileId);

            if (!response || !response.success) {
                throw new Error(response?.message || 'Failed to extract thumbnail');
            }

            return {
                success: true,
                method: 'extracted',
                thumbnailUrl: response.thumbnail_url,
                message: 'Thumbnail extracted successfully'
            };

        } catch (error) {
            Logger.error('Thumbnail extraction failed:', error);
            throw error;
        }
    }

    /**
     * Generate thumbnail from 3D model
     */
    async generateThumbnail(task) {
        try {
            Logger.debug(`🎨 Generating thumbnail for ${task.fileType} file: ${task.fileId}`);

            const response = await api.generateFileThumbnail(task.fileId);

            if (!response || !response.success) {
                throw new Error(response?.message || 'Failed to generate thumbnail');
            }

            return {
                success: true,
                method: 'generated',
                thumbnailUrl: response.thumbnail_url,
                message: 'Thumbnail generated successfully'
            };

        } catch (error) {
            Logger.error('Thumbnail generation failed:', error);
            throw error;
        }
    }

    /**
     * Analyze G-code for thumbnail data
     */
    async analyzeThumbnail(task) {
        try {
            Logger.debug(`📊 Analyzing G-code for thumbnail: ${task.fileId}`);

            const response = await api.analyzeGcodeThumbnail(task.fileId);

            if (!response || !response.success) {
                throw new Error(response?.message || 'Failed to analyze G-code');
            }

            return {
                success: true,
                method: 'analyzed',
                thumbnailUrl: response.thumbnail_url,
                metadata: response.metadata,
                message: 'G-code analyzed successfully'
            };

        } catch (error) {
            Logger.error('G-code analysis failed:', error);
            throw error;
        }
    }

    /**
     * Notify UI of task updates
     */
    notifyTaskUpdate(task) {
        const event = new CustomEvent('thumbnailTaskUpdate', {
            detail: {
                task: { ...task },
                queueStats: this.getStats()
            }
        });
        document.dispatchEvent(event);
    }

    /**
     * Notify that thumbnail processing is complete
     */
    notifyThumbnailComplete(task, result) {
        const event = new CustomEvent('thumbnailProcessingComplete', {
            detail: {
                fileId: task.fileId,
                downloadTaskId: task.downloadTaskId,
                result: result,
                task: task
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
     * Get processing statistics by file type
     */
    getProcessingStatsByType() {
        const stats = {};

        // Count by file type
        for (const [type] of Object.entries(this.supportedTypes)) {
            stats[type] = {
                queued: this.queue.filter(t => t.fileType === type).length,
                processing: Array.from(this.processing.values()).filter(t => t.fileType === type).length,
                completed: Array.from(this.completed.values()).filter(t => t.fileType === type).length,
                failed: Array.from(this.failed.values()).filter(t => t.fileType === type).length
            };
        }

        return stats;
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

        // Cancel if processing
        if (this.processing.has(taskId)) {
            const task = this.processing.get(taskId);
            task.status = 'cancelled';
            this.processing.delete(taskId);

            Logger.debug(`❌ Cancelled thumbnail processing: ${taskId}`);
            return true;
        }

        return false;
    }

    /**
     * Shutdown queue processing
     */
    async shutdown() {
        Logger.debug('🛑 Shutting down Thumbnail Queue');

        if (this.processInterval) {
            clearInterval(this.processInterval);
        }

        // Wait for current processing to complete (with timeout)
        const timeout = 60000; // 60 seconds
        const start = Date.now();

        while (this.processing.size > 0 && (Date.now() - start) < timeout) {
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        Logger.debug('🖼️ Thumbnail Queue shut down');
    }
}

// Export for use in other modules
window.ThumbnailQueue = ThumbnailQueue;