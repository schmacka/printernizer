/**
 * Printernizer API Client
 * Handles all HTTP requests to the backend API with proper error handling
 */

class ApiClient {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    /**
     * Make HTTP request with error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            // Handle HTTP errors
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new ApiError(
                    response.status,
                    errorData.error?.message || CONFIG.ERROR_MESSAGES.SERVER_ERROR,
                    errorData.error?.code,
                    errorData.error?.details
                );
            }

            // Return JSON response or null for empty responses
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return null;
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            
            // Network errors
            if (error.name === 'TypeError' || error.message.includes('fetch')) {
                throw new ApiError(0, CONFIG.ERROR_MESSAGES.NETWORK_ERROR, 'NETWORK_ERROR');
            }
            
            // Unknown errors
            throw new ApiError(500, CONFIG.ERROR_MESSAGES.UNKNOWN_ERROR, 'UNKNOWN_ERROR');
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const url = new URL(`${this.baseURL}${endpoint}`);
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
                url.searchParams.append(key, params[key]);
            }
        });
        
        return this.request(endpoint + url.search);
    }

    /**
     * POST request
     */
    async post(endpoint, data = null) {
        return this.request(endpoint, {
            method: 'POST',
            body: data ? JSON.stringify(data) : null
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data = null) {
        return this.request(endpoint, {
            method: 'PUT',
            body: data ? JSON.stringify(data) : null
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    /**
     * PATCH request
     */
    async patch(endpoint, data = null) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: data ? JSON.stringify(data) : null
        });
    }

    // System Endpoints
    async getHealth() {
        return this.get(CONFIG.ENDPOINTS.HEALTH);
    }

    async getSystemInfo() {
        return this.get(CONFIG.ENDPOINTS.SYSTEM_INFO);
    }

    // Printer Endpoints
    async getPrinters(filters = {}) {
        return this.get(CONFIG.ENDPOINTS.PRINTERS, filters);
    }

    async getPrinter(printerId) {
        return this.get(CONFIG.ENDPOINTS.PRINTER_DETAIL(printerId));
    }

    async addPrinter(printerData) {
        return this.post(CONFIG.ENDPOINTS.PRINTERS, printerData);
    }

    async updatePrinter(printerId, printerData) {
        return this.put(CONFIG.ENDPOINTS.PRINTER_DETAIL(printerId), printerData);
    }

    async deletePrinter(printerId) {
        return this.delete(CONFIG.ENDPOINTS.PRINTER_DETAIL(printerId));
    }
    
    /**
     * Printer Control Functions
     */
    async pausePrinter(printerId) {
        return this.post(`${CONFIG.ENDPOINTS.PRINTER_DETAIL(printerId)}/pause`);
    }
    
    async resumePrinter(printerId) {
        return this.post(`${CONFIG.ENDPOINTS.PRINTER_DETAIL(printerId)}/resume`);
    }
    
    async stopPrinter(printerId) {
        return this.post(`${CONFIG.ENDPOINTS.PRINTER_DETAIL(printerId)}/stop`);
    }

    // Job Endpoints
    async getJobs(filters = {}) {
        return this.get(CONFIG.ENDPOINTS.JOBS, {
            page: filters.page || 1,
            limit: filters.limit || CONFIG.DEFAULT_PAGE_SIZE,
            ...filters
        });
    }

    async getJob(jobId) {
        return this.get(CONFIG.ENDPOINTS.JOB_DETAIL(jobId));
    }

    async cancelJob(jobId) {
        return this.post(CONFIG.ENDPOINTS.JOB_CANCEL(jobId));
    }

    async updateJob(jobId, jobData) {
        return this.put(CONFIG.ENDPOINTS.JOB_DETAIL(jobId), jobData);
    }

    // File Endpoints
    async getFiles(filters = {}) {
        return this.get(CONFIG.ENDPOINTS.FILES, {
            page: filters.page || 1,
            limit: filters.limit || CONFIG.DEFAULT_PAGE_SIZE,
            ...filters
        });
    }

    async getFile(fileId) {
        return this.get(CONFIG.ENDPOINTS.FILE_DETAIL(fileId));
    }

    async downloadFile(fileId) {
        return this.post(CONFIG.ENDPOINTS.FILE_DOWNLOAD(fileId));
    }

    async getDownloadStatus(fileId) {
        return this.get(CONFIG.ENDPOINTS.FILE_DOWNLOAD_STATUS(fileId));
    }

    async deleteFile(fileId) {
        return this.delete(CONFIG.ENDPOINTS.FILE_DETAIL(fileId));
    }

    async getCleanupCandidates(filters = {}) {
        return this.get(CONFIG.ENDPOINTS.FILES_CLEANUP_CANDIDATES, filters);
    }

    async performCleanup(fileIds) {
        return this.post(CONFIG.ENDPOINTS.FILES_CLEANUP, {
            file_ids: fileIds,
            confirm: true
        });
    }

    // Watch Folder Management Endpoints
    async getWatchFolderSettings() {
        return this.get(CONFIG.ENDPOINTS.FILES + '/watch-folders/settings');
    }

    async getWatchFolderStatus() {
        return this.get(CONFIG.ENDPOINTS.FILES + '/watch-folders/status');
    }

    async validateWatchFolder(folderPath) {
        return this.post(CONFIG.ENDPOINTS.FILES + '/watch-folders/validate?folder_path=' + encodeURIComponent(folderPath));
    }

    async addWatchFolder(folderPath) {
        return this.post(CONFIG.ENDPOINTS.FILES + '/watch-folders/add?folder_path=' + encodeURIComponent(folderPath));
    }

    async removeWatchFolder(folderPath) {
        return this.delete(CONFIG.ENDPOINTS.FILES + '/watch-folders/remove?folder_path=' + encodeURIComponent(folderPath));
    }

    async reloadWatchFolders() {
        return this.post(CONFIG.ENDPOINTS.FILES + '/watch-folders/reload');
    }

    async updateWatchFolder(folderPath, isActive) {
        return this.patch(CONFIG.ENDPOINTS.FILES + '/watch-folders/update?folder_path=' + encodeURIComponent(folderPath) + '&is_active=' + isActive);
    }

    // Statistics Endpoints
    async getStatisticsOverview(period = 'month') {
        return this.get(CONFIG.ENDPOINTS.STATISTICS_OVERVIEW, { period });
    }

    async getPrinterStatistics(printerId, period = 'month') {
        return this.get(CONFIG.ENDPOINTS.STATISTICS_PRINTER(printerId), { period });
    }

    // ========================================
    // MILESTONE 1.2: ENHANCED API ENDPOINTS
    // ========================================

    // Real-time Printer Status Endpoints
    async getPrinterStatus(printerId) {
        return this.get(CONFIG.ENDPOINTS.PRINTER_STATUS(printerId));
    }

    async getPrinterStatusHistory(printerId, hours = 24) {
        return this.get(CONFIG.ENDPOINTS.PRINTER_STATUS_HISTORY(printerId), { hours });
    }

    // Real-time Monitoring Endpoints
    async startPrinterMonitoring(printerId) {
        return this.post(CONFIG.ENDPOINTS.PRINTER_MONITORING_START(printerId));
    }

    async stopPrinterMonitoring(printerId) {
        return this.post(CONFIG.ENDPOINTS.PRINTER_MONITORING_STOP(printerId));
    }

    // Enhanced File Management Endpoints
    async getPrinterFiles(printerId, includeStatus = true) {
        return this.get(CONFIG.ENDPOINTS.PRINTER_FILES(printerId), { include_status: includeStatus });
    }

    async downloadPrinterFile(printerId, filename, onProgress = null) {
        const endpoint = CONFIG.ENDPOINTS.PRINTER_FILE_DOWNLOAD(printerId, filename);
        
        // For progress tracking, we need to handle this differently
        if (onProgress) {
            return this.downloadWithProgress(endpoint, onProgress);
        }
        
        return this.post(endpoint);
    }

    async getPrinterFileDownloadStatus(printerId, filename) {
        return this.get(CONFIG.ENDPOINTS.PRINTER_FILE_DOWNLOAD_STATUS(printerId, filename));
    }

    // Enhanced Job Endpoints
    async getCurrentJob(printerId) {
        return this.get(CONFIG.ENDPOINTS.PRINTER_CURRENT_JOB(printerId));
    }

    async syncJobHistory(printerId) {
        return this.post(CONFIG.ENDPOINTS.PRINTER_SYNC_JOBS(printerId));
    }

    // Connection Status Endpoint
    async getPrinterConnectionStatus(printerId) {
        return this.get(CONFIG.ENDPOINTS.PRINTER_CONNECTION_STATUS(printerId));
    }

    /**
     * Download file with progress tracking
     */
    async downloadWithProgress(endpoint, onProgress) {
        const url = `${this.baseURL}${endpoint}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: this.defaultHeaders
        });

        if (!response.ok) {
            throw new ApiError(response.status, 'Download failed', 'DOWNLOAD_ERROR');
        }

        const reader = response.body.getReader();
        const contentLength = parseInt(response.headers.get('content-length'), 10);
        let receivedLength = 0;
        const chunks = [];

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            chunks.push(value);
            receivedLength += value.length;
            
            if (onProgress && contentLength) {
                onProgress({
                    progress: (receivedLength / contentLength) * 100,
                    loaded: receivedLength,
                    total: contentLength
                });
            }
        }

        return new Uint8Array(receivedLength).map((_, i) => {
            let offset = 0;
            for (const chunk of chunks) {
                if (i >= offset && i < offset + chunk.length) {
                    return chunk[i - offset];
                }
                offset += chunk.length;
            }
        });
    }
}

/**
 * Custom API Error class
 */
class ApiError extends Error {
    constructor(status, message, code = null, details = null) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.code = code;
        this.details = details;
    }

    /**
     * Check if error is a specific type
     */
    isNetworkError() {
        return this.status === 0 || this.code === 'NETWORK_ERROR';
    }

    isServerError() {
        return this.status >= 500;
    }

    isClientError() {
        return this.status >= 400 && this.status < 500;
    }

    isPrinterOffline() {
        return this.code === 'PRINTER_OFFLINE';
    }

    isNotFound() {
        return this.status === 404;
    }

    /**
     * Get user-friendly error message
     */
    getUserMessage() {
        if (this.isNetworkError()) {
            return CONFIG.ERROR_MESSAGES.NETWORK_ERROR;
        }
        
        if (this.isPrinterOffline()) {
            return CONFIG.ERROR_MESSAGES.PRINTER_OFFLINE;
        }
        
        if (this.isNotFound()) {
            return CONFIG.ERROR_MESSAGES.FILE_NOT_FOUND;
        }
        
        if (this.status === 422) {
            return CONFIG.ERROR_MESSAGES.INVALID_INPUT;
        }
        
        if (this.status === 403) {
            return CONFIG.ERROR_MESSAGES.PERMISSION_DENIED;
        }
        
        return this.message || CONFIG.ERROR_MESSAGES.UNKNOWN_ERROR;
    }
}

/**
 * Request retry utility
 */
class RetryableRequest {
    constructor(apiClient, maxRetries = 3, retryDelay = 1000) {
        this.api = apiClient;
        this.maxRetries = maxRetries;
        this.retryDelay = retryDelay;
    }

    /**
     * Execute request with retry logic
     */
    async execute(requestFn, ...args) {
        let lastError;
        
        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                return await requestFn.call(this.api, ...args);
            } catch (error) {
                lastError = error;
                
                // Don't retry client errors (4xx)
                if (error instanceof ApiError && error.isClientError()) {
                    throw error;
                }
                
                // Don't retry on last attempt
                if (attempt === this.maxRetries) {
                    break;
                }
                
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * (attempt + 1)));
            }
        }
        
        throw lastError;
    }
}

/**
 * API Response Cache
 */
class ApiCache {
    constructor(ttl = 60000) { // 1 minute default TTL
        this.cache = new Map();
        this.ttl = ttl;
    }

    /**
     * Generate cache key from URL and params
     */
    generateKey(endpoint, params = {}) {
        const sortedParams = Object.keys(params)
            .sort()
            .map(key => `${key}=${params[key]}`)
            .join('&');
        
        return `${endpoint}?${sortedParams}`;
    }

    /**
     * Get cached response
     */
    get(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;
        
        if (Date.now() - cached.timestamp > this.ttl) {
            this.cache.delete(key);
            return null;
        }
        
        return cached.data;
    }

    /**
     * Set cached response
     */
    set(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Clear cache
     */
    clear() {
        this.cache.clear();
    }

    /**
     * Remove expired entries
     */
    cleanup() {
        const now = Date.now();
        for (const [key, entry] of this.cache.entries()) {
            if (now - entry.timestamp > this.ttl) {
                this.cache.delete(key);
            }
        }
    }
}

// Initialize global API client
const api = new ApiClient();
const retryableApi = new RetryableRequest(api);
const apiCache = new ApiCache(30000); // 30 seconds TTL

// Cleanup cache periodically
setInterval(() => {
    apiCache.cleanup();
}, 60000); // Every minute

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, ApiError, RetryableRequest, ApiCache };
}