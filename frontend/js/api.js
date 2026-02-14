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
     * Normalize an endpoint to start with a single "/" and collapse duplicate slashes
     */
    _normalizeEndpoint(endpoint) {
        // Reject null/undefined endpoints to prevent "/null" URLs
        if (endpoint === null || endpoint === undefined || endpoint === 'null' || endpoint === 'undefined') {
            console.error('API Error: Attempting to call endpoint with null/undefined value:', endpoint);
            console.trace();
            throw new Error('Invalid API endpoint: cannot be null or undefined');
        }
        const raw = String(endpoint);
        const [path, query] = raw.split('?');
        const normalizedPath = '/' + path.replace(/(^\/+|\/+$)/g, '').replace(/\/{2,}/g, '/');
        return query ? `${normalizedPath}?${query}` : normalizedPath;
    }

    /**
     * Join path segments safely (collapses duplicate slashes)
     */
    _joinPath(...parts) {
        const joined = parts
            .filter(Boolean)
            .map(p => String(p).replace(/(^\/+|\/+$)/g, ''))
            .join('/');
        return '/' + joined.replace(/\/{2,}/g, '/');
    }

    /**
     * Make HTTP request with error handling
     */
    async request(endpoint, options = {}) {
        const normalizedEndpoint = this._normalizeEndpoint(endpoint);
        const base = this.baseURL.replace(/\/+$/, '');
        const url = `${base}${normalizedEndpoint}`;
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
                    errorData.message || errorData.detail || errorData.error?.message || CONFIG.ERROR_MESSAGES.SERVER_ERROR,
                    errorData.error_code || errorData.error?.code,
                    errorData.details || errorData.error?.details
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
        const normalizedEndpoint = this._normalizeEndpoint(endpoint);
        const search = new URLSearchParams();
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
                search.append(key, params[key]);
            }
        });
        const finalEndpoint = search.toString()
            ? `${normalizedEndpoint}?${search.toString()}`
            : normalizedEndpoint;
        return this.request(finalEndpoint);
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

    async shutdownServer() {
        return this.post(CONFIG.ENDPOINTS.SYSTEM_SHUTDOWN);
    }

    // Settings Endpoints
    async getApplicationSettings() {
        return this.get(CONFIG.ENDPOINTS.APPLICATION_SETTINGS);
    }

    async updateApplicationSettings(settingsData) {
        return this.put(CONFIG.ENDPOINTS.APPLICATION_SETTINGS, settingsData);
    }

    async getWatchFolderSettings() {
        return this.get(CONFIG.ENDPOINTS.WATCH_FOLDER_SETTINGS);
    }

    // Setup Wizard Endpoints
    async getSetupStatus() {
        return this.get('/setup/status');
    }

    async getSetupDefaults() {
        return this.get('/setup/defaults');
    }

    async completeSetup(skipWizard = false) {
        return this.post('/setup/complete', { skip_wizard: skipWizard });
    }

    async resetSetup() {
        return this.post('/setup/reset');
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

    async deletePrinter(printerId, { force = false } = {}) {
        const endpoint = force
            ? `${CONFIG.ENDPOINTS.PRINTER_DETAIL(printerId)}?force=true`
            : CONFIG.ENDPOINTS.PRINTER_DETAIL(printerId);
        return this.delete(endpoint);
    }

    async testPrinterConnection(printerConfig) {
        return this.post('/printers/test-connection', printerConfig);
    }

    /**
     * Printer Discovery Functions
     */
    async discoverPrinters(params = {}) {
        return this.get(CONFIG.ENDPOINTS.PRINTER_DISCOVER, params);
    }

    async getNetworkInterfaces() {
        return this.get(CONFIG.ENDPOINTS.PRINTER_DISCOVER_INTERFACES);
    }

    async getStartupDiscoveredPrinters() {
        return this.get(CONFIG.ENDPOINTS.PRINTER_DISCOVER_STARTUP);
    }

    async clearStartupDiscoveredPrinters() {
        return this.delete(CONFIG.ENDPOINTS.PRINTER_DISCOVER_STARTUP);
    }

    /**
     * Printer Control Functions
     */
    async pausePrinter(printerId) {
        return this.post(this._joinPath(CONFIG.ENDPOINTS.PRINTER_DETAIL(printerId), 'pause'));
    }
    
    async resumePrinter(printerId) {
        return this.post(this._joinPath(CONFIG.ENDPOINTS.PRINTER_DETAIL(printerId), 'resume'));
    }
    
    async stopPrinter(printerId) {
        return this.post(this._joinPath(CONFIG.ENDPOINTS.PRINTER_DETAIL(printerId), 'stop'));
    }

    // Manually trigger download & processing of current job file (thumbnail extraction)
    async downloadCurrentJobFile(printerId) {
        return this.post(CONFIG.ENDPOINTS.PRINTER_DOWNLOAD_CURRENT_JOB(printerId));
    }

    async downloadPrinterFile(printerId, filename) {
        return this.post(CONFIG.ENDPOINTS.PRINTER_DOWNLOAD_FILE(printerId), { filename });
    }

    async getPrinterFiles(printerId) {
        return this.get(CONFIG.ENDPOINTS.PRINTER_FILES(printerId));
    }

    // Thumbnail Processing Endpoints
    async extractFileThumbnail(fileId) {
        return this.post(CONFIG.ENDPOINTS.FILE_EXTRACT_THUMBNAIL(fileId));
    }

    async generateFileThumbnail(fileId) {
        return this.post(CONFIG.ENDPOINTS.FILE_GENERATE_THUMBNAIL(fileId));
    }

    async analyzeGcodeThumbnail(fileId) {
        return this.post(CONFIG.ENDPOINTS.FILE_ANALYZE_GCODE(fileId));
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

    async createJob(jobData) {
        return this.post(CONFIG.ENDPOINTS.JOBS, jobData);
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

    async getFileMetadata(fileId) {
        return this.get(`files/${fileId}/metadata`);
    }

    async getFileStatistics() {
        return this.get('files/statistics');
    }

    async deleteFile(fileId) {
        return this.delete(`files/${fileId}`);
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
        return this.get('files/watch-folders/settings');
    }

    async getWatchFolderStatus() {
        return this.get('files/watch-folders/status');
    }

    async validateWatchFolder(folderPath) {
        return this.post('files/watch-folders/validate?folder_path=' + encodeURIComponent(folderPath));
    }

    async validateDownloadsPath(folderPath) {
        return this.post('settings/downloads-path/validate?folder_path=' + encodeURIComponent(folderPath));
    }

    async validateLibraryPath(folderPath) {
        return this.post('settings/library-path/validate?folder_path=' + encodeURIComponent(folderPath));
    }

    async addWatchFolder(folderPath) {
        return this.post('files/watch-folders/add?folder_path=' + encodeURIComponent(folderPath));
    }

    async removeWatchFolder(folderPath) {
        return this.delete('files/watch-folders/remove?folder_path=' + encodeURIComponent(folderPath));
    }

    async reloadWatchFolders() {
        return this.post('files/watch-folders/reload');
    }

    async updateWatchFolder(folderPath, isActive) {
        return this.patch('files/watch-folders/update?folder_path=' + encodeURIComponent(folderPath) + '&is_active=' + isActive);
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

    // Search Endpoints
    /**
     * Unified search across local files and ideas
     * @param {string} query - Search query string
     * @param {Object} filters - Search filters (sources, file_types, dimensions, etc.)
     * @param {number} page - Page number (default: 1)
     * @param {number} limit - Results per page (default: 50)
     * @returns {Promise<Object>} Search results grouped by source
     */
    async unifiedSearch(query, filters = {}, page = 1, limit = 50) {
        const params = {
            q: query,
            page,
            limit,
            ...filters
        };
        return this.get('/search', params);
    }

    /**
     * Get search history
     * @param {number} limit - Number of history entries (default: 20)
     * @returns {Promise<Array>} Search history entries
     */
    async getSearchHistory(limit = 20) {
        return this.get('/search/history', { limit });
    }

    /**
     * Delete search history entry
     * @param {string} searchId - Search history entry ID
     * @returns {Promise<Object>} Deletion confirmation
     */
    async deleteSearchHistory(searchId) {
        return this.delete(`/search/history/${searchId}`);
    }

    /**
     * Get search suggestions
     * @param {string} query - Partial query for autocomplete
     * @param {number} limit - Number of suggestions (default: 10)
     * @returns {Promise<Array>} Search suggestions
     */
    async getSearchSuggestions(query, limit = 10) {
        return this.get('/search/suggestions', { q: query, limit });
    }

    /**
     * Download file with progress tracking
     */
    async downloadWithProgress(endpoint, onProgress) {
        const normalizedEndpoint = this._normalizeEndpoint(endpoint);
        const base = this.baseURL.replace(/\/+$/, '');
        const url = `${base}${normalizedEndpoint}`;
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

    // ==================== Timelapses API ====================

    /**
     * Get timelapses with optional filtering
     */
    async getTimelapses(filters = {}) {
        const params = new URLSearchParams();
        if (filters.status) params.append('status', filters.status);
        if (filters.linked_only) params.append('linked_only', 'true');
        if (filters.limit) params.append('limit', filters.limit);
        if (filters.offset) params.append('offset', filters.offset);

        const queryString = params.toString();
        const endpoint = queryString ? `/api/v1/timelapses?${queryString}` : '/api/v1/timelapses';

        return this.request(endpoint);
    }

    /**
     * Get timelapse statistics
     */
    async getTimelapseStats() {
        return this.request('/api/v1/timelapses/stats');
    }

    /**
     * Get specific timelapse by ID
     */
    async getTimelapse(timelapseId) {
        return this.request(`/api/v1/timelapses/${timelapseId}`);
    }

    /**
     * Trigger manual processing for a timelapse
     */
    async triggerTimelapseProcessing(timelapseId) {
        return this.request(`/api/v1/timelapses/${timelapseId}/process`, {
            method: 'POST'
        });
    }

    /**
     * Delete timelapse
     */
    async deleteTimelapse(timelapseId) {
        return this.request(`/api/v1/timelapses/${timelapseId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Link timelapse to job
     */
    async linkTimelapseToJob(timelapseId, jobId) {
        return this.request(`/api/v1/timelapses/${timelapseId}/link`, {
            method: 'PATCH',
            body: JSON.stringify({ job_id: jobId })
        });
    }

    /**
     * Toggle pin status for timelapse
     */
    async toggleTimelapsePin(timelapseId) {
        return this.request(`/api/v1/timelapses/${timelapseId}/pin`, {
            method: 'PATCH'
        });
    }

    /**
     * Get cleanup candidates
     */
    async getCleanupCandidates() {
        return this.request('/api/v1/timelapses/cleanup/candidates');
    }

    /**
     * Bulk delete timelapses
     */
    async bulkDeleteTimelapses(timelapseIds) {
        return this.request('/api/v1/timelapses/bulk-delete', {
            method: 'POST',
            body: JSON.stringify({ timelapse_ids: timelapseIds })
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
            if (this.details?.endpoint && String(this.details.endpoint).includes('/printers/')) {
                return CONFIG.ERROR_MESSAGES.PRINTER_NOT_FOUND || 'Drucker wurde nicht gefunden.';
            }
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