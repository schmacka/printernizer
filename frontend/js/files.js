/**
 * Printernizer File Management (Drucker-Dateien) Page
 * Handles unified file listing, downloads, and file operations
 */

class FileManager {
    constructor() {
        this.files = new Map();
        this.refreshInterval = null;
        this.currentFilters = {};
        this.currentPage = 1;
        this.totalPages = 1;
        this.pagination = null;
        this.downloadProgress = new Map(); // Track download progress
        this.searchDebounceTimer = null; // Debounce timer for search input
    }

    /**
     * Initialize file management page
     */
    async init() {
        Logger.debug('Initializing file management');

        // Load files
        this.loadFiles();

        // Load file statistics
        this.loadFileStatistics();

        // Load watch folders
        this.loadWatchFolders();

        // Load discovered files
        this.loadDiscoveredFiles();

        // Setup filter handlers
        this.setupFilterHandlers();
        
        // Set up refresh interval
        this.startAutoRefresh();
        
        // Setup WebSocket listeners
        this.setupWebSocketListeners();
        
        // Load printer options for filter
        this.loadPrinterOptions();
        
        // Setup watch folder form handler
        this.setupWatchFolderForm();
    }

    /**
     * Cleanup file manager resources
     */
    cleanup() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Load and display file statistics
     */
    async loadFileStatistics() {
        try {
            const statsContainer = document.getElementById('filesStats');
            if (!statsContainer) return;
            
            // Show loading state
            setLoadingState(statsContainer, true);
            
            // Load file statistics from API
            const response = await api.getFileStatistics();

            if (response && response.statistics) {
                statsContainer.innerHTML = this.renderFileStatistics(response.statistics);
            } else {
                statsContainer.innerHTML = this.renderFileStatisticsError();
            }
            
        } catch (error) {
            Logger.error('Failed to load file statistics:', error);
            const statsContainer = document.getElementById('filesStats');
            if (statsContainer) {
                statsContainer.innerHTML = this.renderFileStatisticsError();
            }
        }
    }

    /**
     * Render file statistics display
     */
    renderFileStatistics(summary) {
        return `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${summary.available_count || 0}</div>
                    <div class="stat-label">📁 ${t('status.file.available')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${summary.downloaded_count || 0}</div>
                    <div class="stat-label">✓ ${t('status.file.downloaded')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${summary.local_count || 0}</div>
                    <div class="stat-label">💾 ${t('status.file.local')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${formatBytes(summary.total_size || 0)}</div>
                    <div class="stat-label">${t('files.totalSize')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${formatPercentage((summary.download_success_rate || 0) * 100)}</div>
                    <div class="stat-label">${t('files.successRate')}</div>
                </div>
            </div>
        `;
    }

    /**
     * Render file statistics error
     */
    renderFileStatisticsError() {
        return `
            <div class="alert alert-warning">
                <strong>${t('files.statsUnavailable')}</strong><br>
                ${t('files.statsLoadError')}
            </div>
        `;
    }

    /**
     * Load and display files
     */
    async loadFiles(page = 1) {
        try {
            const filesList = document.getElementById('filesList');
            if (!filesList) return;
            
            // Show loading state on initial load
            if (page === 1) {
                setLoadingState(filesList, true);
            }
            
            // Prepare filters
            const filters = {
                ...this.currentFilters,
                page: page,
                limit: CONFIG.DEFAULT_PAGE_SIZE
            };
            
            // Load files from API
            const response = await api.getFiles(filters);
            
            if (page === 1) {
                // Clear existing files on new search
                this.files.clear();
                filesList.innerHTML = '';
            }
            
            if (response.files && response.files.length > 0) {
                // Create file items
                response.files.forEach(file => {
                    const fileItem = new FileListItem(file);
                    const itemElement = fileItem.render();
                    filesList.appendChild(itemElement);
                    
                    // Store file item for updates
                    this.files.set(file.id, fileItem);
                });
                
                // Update pagination
                this.updatePagination(response.pagination);
                
            } else if (page === 1) {
                // Show empty state
                filesList.innerHTML = this.renderEmptyFilesState();
            }
            
            this.currentPage = page;
            
        } catch (error) {
            Logger.error('Failed to load files:', error);
            const filesList = document.getElementById('filesList');
            if (filesList && this.currentPage === 1) {
                filesList.innerHTML = this.renderFilesError(error);
            }
        }
    }

    /**
     * Update pagination component
     */
    updatePagination(paginationData) {
        if (!paginationData) return;
        
        this.totalPages = paginationData.total_pages;
        
        // Find or create pagination container
        let paginationContainer = document.querySelector('.files-pagination');
        if (!paginationContainer) {
            paginationContainer = document.createElement('div');
            paginationContainer.className = 'files-pagination';
            
            const filesContainer = document.querySelector('.files-container');
            if (filesContainer) {
                filesContainer.appendChild(paginationContainer);
            }
        }
        
        // Create or update pagination component
        if (this.pagination) {
            this.pagination.update(paginationData.page, paginationData.total_pages);
        } else {
            this.pagination = new Pagination(
                paginationData.page,
                paginationData.total_pages,
                (page) => this.loadFiles(page)
            );
            const paginationElement = this.pagination.render();
            paginationContainer.innerHTML = '';
            paginationContainer.appendChild(paginationElement);
        }
        
        // Update pagination info
        this.updatePaginationInfo(paginationData);
    }

    /**
     * Update pagination information display
     */
    updatePaginationInfo(paginationData) {
        let infoContainer = document.querySelector('.files-pagination-info');
        if (!infoContainer) {
            infoContainer = document.createElement('div');
            infoContainer.className = 'files-pagination-info text-center text-muted';
            
            const paginationContainer = document.querySelector('.files-pagination');
            if (paginationContainer) {
                paginationContainer.insertBefore(infoContainer, paginationContainer.firstChild);
            }
        }
        
        const start = (paginationData.page - 1) * paginationData.limit + 1;
        const end = Math.min(start + paginationData.limit - 1, paginationData.total_items);
        
        infoContainer.innerHTML = `
            ${t('files.paginationInfo', { start: start, end: end, total: paginationData.total_items })}
        `;
    }

    /**
     * Setup filter change handlers
     */
    setupFilterHandlers() {
        // Search input
        const searchInput = document.getElementById('fileSearchInput');
        const searchClearBtn = document.getElementById('fileSearchClear');

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const searchValue = e.target.value.trim();

                // Show/hide clear button
                if (searchClearBtn) {
                    searchClearBtn.style.display = searchValue ? 'flex' : 'none';
                }

                // Debounce search to reduce API calls
                if (this.searchDebounceTimer) {
                    clearTimeout(this.searchDebounceTimer);
                }

                this.searchDebounceTimer = setTimeout(() => {
                    this.currentFilters.search = searchValue || undefined;
                    this.loadFiles(1);
                    this.loadFileStatistics(); // Refresh stats with filter
                }, 300); // 300ms debounce delay
            });

            // Handle Enter key
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (this.searchDebounceTimer) {
                        clearTimeout(this.searchDebounceTimer);
                    }
                    const searchValue = searchInput.value.trim();
                    this.currentFilters.search = searchValue || undefined;
                    this.loadFiles(1);
                    this.loadFileStatistics();
                }
            });
        }

        // Status filter
        const statusFilter = document.getElementById('fileStatusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.currentFilters.status = e.target.value || undefined;
                this.loadFiles(1);
                this.loadFileStatistics(); // Refresh stats with filter
            });
        }

        // Printer filter
        const printerFilter = document.getElementById('filePrinterFilter');
        if (printerFilter) {
            printerFilter.addEventListener('change', (e) => {
                this.currentFilters.printer_id = e.target.value || undefined;
                this.loadFiles(1);
                this.loadFileStatistics(); // Refresh stats with filter
            });
        }
    }

    /**
     * Load printer options for filter dropdown
     */
    async loadPrinterOptions() {
        try {
            const printerFilter = document.getElementById('filePrinterFilter');
            if (!printerFilter) {
                Logger.warn('Printer filter dropdown not found');
                return;
            }

            Logger.debug('Loading printer options for filter dropdown...');
            const response = await api.getPrinters();
            Logger.debug('Printers API response:', response);

            // Clear existing options (except "All Printers")
            const firstOption = printerFilter.firstElementChild;
            printerFilter.innerHTML = '';
            if (firstOption) {
                printerFilter.appendChild(firstOption);
            }

            // Add printer options
            if (response && Array.isArray(response)) {
                Logger.debug(`Adding ${response.length} printers to filter dropdown`);
                response.forEach(printer => {
                    const option = document.createElement('option');
                    option.value = printer.id;
                    option.textContent = printer.name;
                    printerFilter.appendChild(option);
                    Logger.debug(`Added printer: ${printer.name} (${printer.id})`);
                });

                if (response.length === 0) {
                    Logger.warn('No printers found in response');
                }
            } else {
                Logger.error('Invalid printers response format:', response);
            }
        } catch (error) {
            Logger.error('Failed to load printer options:', error);
            Logger.error('Error details:', {
                message: error.message,
                stack: error.stack
            });
        }
    }

    /**
     * Render empty files state
     */
    renderEmptyFilesState() {
        const hasFilters = Object.keys(this.currentFilters).length > 0;
        
        if (hasFilters) {
            return `
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <h3>${t('files.noFilesFound')}</h3>
                    <p>${t('files.noFilesMatchFilters')}</p>
                    <button class="btn btn-secondary" onclick="fileManager.clearFilters()">
                        <span class="btn-icon">🗑️</span>
                        ${t('files.clearFilters')}
                    </button>
                </div>
            `;
        }
        
        return `
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <h3>${t('files.noFilesAvailable')}</h3>
                <p>${t('files.emptyHint')}</p>
            </div>
        `;
    }

    /**
     * Render files error state
     */
    renderFilesError(error) {
        const message = error instanceof ApiError ? error.getUserMessage() : t('files.loadError');

        return `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>${t('files.loadErrorTitle')}</h3>
                <p>${escapeHtml(message)}</p>
                <button class="btn btn-primary" onclick="fileManager.loadFiles()">
                    <span class="btn-icon">🔄</span>
                    ${t('common.retry')}
                </button>
            </div>
        `;
    }

    /**
     * Clear all filters
     */
    clearFilters() {
        this.currentFilters = {};

        // Reset filter controls
        const statusFilter = document.getElementById('fileStatusFilter');
        const printerFilter = document.getElementById('filePrinterFilter');
        const searchInput = document.getElementById('fileSearchInput');
        const searchClearBtn = document.getElementById('fileSearchClear');

        if (statusFilter) statusFilter.value = '';
        if (printerFilter) printerFilter.value = '';
        if (searchInput) searchInput.value = '';
        if (searchClearBtn) searchClearBtn.style.display = 'none';

        // Reload files
        this.loadFiles(1);
        this.loadFileStatistics();
    }

    /**
     * Start auto-refresh interval
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            if (window.currentPage === 'files') {
                this.refreshFiles();
            }
        }, CONFIG.DASHBOARD_REFRESH_INTERVAL); // Use dashboard interval for files
    }

    /**
     * Refresh files without full reload
     */
    async refreshFiles() {
        try {
            // Only refresh first page to get latest files
            const filters = {
                ...this.currentFilters,
                page: 1,
                limit: CONFIG.DEFAULT_PAGE_SIZE
            };
            
            const response = await api.getFiles(filters);
            
            if (response.files) {
                // Update existing files
                response.files.forEach(fileData => {
                    const existingFile = this.files.get(fileData.id);
                    if (existingFile) {
                        existingFile.update(fileData);
                    }
                });
            }
            
            // Update statistics
            if (response.summary) {
                const statsContainer = document.getElementById('filesStats');
                if (statsContainer && !statsContainer.querySelector('.loading-placeholder')) {
                    statsContainer.innerHTML = this.renderFileStatistics(response.summary);
                }
            }
        } catch (error) {
            Logger.error('Failed to refresh files:', error);
        }
    }

    /**
     * Setup WebSocket listeners
     */
    setupWebSocketListeners() {
        // Listen for file updates
        document.addEventListener('fileUpdate', (event) => {
            const fileData = event.detail;
            const fileItem = this.files.get(fileData.file_id || fileData.id);
            
            if (fileItem) {
                fileItem.update(fileData);
                
                // Update download progress if downloading
                if (fileData.status === 'downloading' && fileData.progress !== undefined) {
                    this.updateDownloadProgress(fileData.file_id || fileData.id, fileData);
                }
            }
            
            // Refresh statistics if file status changed significantly
            if (['downloaded', 'available', 'error'].includes(fileData.status)) {
                this.loadFileStatistics();
            }
        });
    }

    /**
     * Download file from printer
     */
    async downloadFileFromPrinter(fileId) {
        try {
            const fileItem = this.files.get(fileId);
            if (!fileItem) return;
            
            // Start download
            const response = await api.downloadFile(fileId);
            
            if (response.status === 'downloading') {
                showToast('info', t('files.downloadStartedTitle'), t('files.downloadStartedMessage', { name: fileItem.file.filename }));
                
                // Update file status immediately
                fileItem.file.status = 'downloading';
                fileItem.update(fileItem.file);
                
                // Start monitoring download progress
                this.monitorDownloadProgress(fileId, response.download_id);
            }
            
        } catch (error) {
            Logger.error('Failed to start download:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : CONFIG.ERROR_MESSAGES.DOWNLOAD_FAILED;
            showToast('error', t('files.downloadErrorTitle'), message);
        }
    }

    /**
     * Monitor download progress
     */
    async monitorDownloadProgress(fileId, downloadId) {
        const maxAttempts = 300; // 5 minutes with 1-second intervals
        let attempts = 0;
        
        const checkProgress = async () => {
            try {
                const response = await api.getDownloadStatus(downloadId || fileId);
                const progress = response?.data || response;

                if (progress.status === 'downloading' || progress.status === 'starting') {
                    // Update progress display
                    this.updateDownloadProgress(fileId, progress);

                    // Continue monitoring
                    if (attempts < maxAttempts) {
                        attempts++;
                        setTimeout(checkProgress, 1000);
                    }
                } else if (progress.status === 'completed') {
                    // Download completed
                    showToast('success', t('files.downloadCompleted'), CONFIG.SUCCESS_MESSAGES.FILE_DOWNLOADED);
                    
                    // Update file item
                    const fileItem = this.files.get(fileId);
                    if (fileItem) {
                        fileItem.file.status = 'downloaded';
                        fileItem.update(fileItem.file);
                    }
                    
                    // Refresh statistics
                    this.loadFileStatistics();
                    
                } else if (progress.status === 'failed') {
                    // Download failed
                    showToast('error', t('files.downloadFailed'), progress.error || CONFIG.ERROR_MESSAGES.DOWNLOAD_FAILED);
                    
                    // Reset file status
                    const fileItem = this.files.get(fileId);
                    if (fileItem) {
                        fileItem.file.status = 'available';
                        fileItem.update(fileItem.file);
                    }
                }
                
            } catch (error) {
                Logger.error('Failed to check download progress:', error);
                
                // Stop monitoring on persistent errors
                if (attempts > 5) {
                    showToast('error', t('files.downloadErrorTitle'), t('files.downloadProgressMonitorError'));
                    return;
                }
                
                // Retry after delay
                setTimeout(checkProgress, 1000);
                attempts++;
            }
        };
        
        // Start monitoring
        setTimeout(checkProgress, 1000);
    }

    /**
     * Update download progress display
     */
    updateDownloadProgress(fileId, progressData) {
        const fileItem = this.files.get(fileId);
        if (fileItem && fileItem.element) {
            const progressContainer = fileItem.element.querySelector('.download-progress');
            
            if (progressContainer) {
                const progressBar = progressContainer.querySelector('.progress-bar');
                const statusText = progressContainer.querySelector('.download-status');
                
                if (progressBar && progressData.progress !== undefined) {
                    progressBar.style.width = `${progressData.progress}%`;
                }
                
                if (statusText) {
                    const speedText = progressData.speed_mbps 
                        ? ` - ${formatBytes(progressData.speed_mbps * 1024 * 1024)}/s`
                        : '';
                    statusText.textContent = `${formatPercentage(progressData.progress || 0)}${speedText}`;
                }
            }
        }
    }

    /**
     * Preview file with STL/3MF support and enhanced metadata
     */
    async previewFile(fileId) {
        const fileItem = this.files.get(fileId);
        if (!fileItem) return;
        
        const modal = document.getElementById('filePreviewModal');
        const content = document.getElementById('filePreviewContent');
        
        if (!modal || !content) return;
        
        // Show modal immediately with loading state
        showModal('filePreviewModal');
        content.innerHTML = `
            <div class="loading-placeholder">
                <div class="spinner"></div>
                <p>${t('files.loadingPreview')}</p>
            </div>
        `;
        
        try {
            // Load metadata, enhanced metadata, and thumbnail
            const [metadata, thumbnailUrl] = await Promise.all([
                this.loadFileMetadata(fileId),
                this.loadFileThumbnail(fileId)
            ]);
            
            // Load enhanced metadata separately (non-blocking)
            const enhancedMetadata = new EnhancedFileMetadata(fileId);
            
            // Render preview based on file type
            const fileType = fileItem.file.file_type?.toLowerCase();
            const is3DFile = fileType && ['stl', '3mf', 'gcode', 'obj', 'ply'].includes(fileType);
            
            if (is3DFile) {
                content.innerHTML = this.render3DFilePreview(fileItem, metadata, thumbnailUrl, enhancedMetadata);
            } else {
                content.innerHTML = this.renderGenericFilePreview(fileItem, metadata);
            }
            
            // Load and render enhanced metadata asynchronously
            if (is3DFile) {
                await this.loadAndRenderEnhancedMetadata(fileId, enhancedMetadata);
            }
            
        } catch (error) {
            Logger.error('Failed to load file preview:', error);
            content.innerHTML = this.renderPreviewError(fileItem, error);
        }
    }
    
    /**
     * Load and render enhanced metadata asynchronously
     */
    async loadAndRenderEnhancedMetadata(fileId, enhancedMetadata) {
        const metadataContainer = document.getElementById(`enhanced-metadata-${fileId}`);
        if (!metadataContainer) return;
        
        // Show loading state
        metadataContainer.innerHTML = enhancedMetadata.renderLoading();
        
        try {
            // Load metadata from API
            await enhancedMetadata.loadMetadata();
            
            // Render the enhanced metadata
            metadataContainer.innerHTML = enhancedMetadata.render();
        } catch (error) {
            Logger.error('Failed to load enhanced metadata:', error);
            metadataContainer.innerHTML = enhancedMetadata.renderError();
        }
    }
    
    /**
     * Load file metadata from API
     */
    async loadFileMetadata(fileId) {
        try {
            const response = await api.getFileMetadata(fileId);
            return response;
        } catch (error) {
            Logger.warn('Failed to load metadata for file:', fileId, error);
            return null;
        }
    }
    
    /**
     * Load file thumbnail from API
     */
    async loadFileThumbnail(fileId) {
        try {
            // Check if file has thumbnail
            const fileItem = this.files.get(fileId);
            if (!fileItem?.file.has_thumbnail) {
                return null;
            }
            
            // Return thumbnail URL
            return `${CONFIG.API_BASE_URL}/files/${fileId}/thumbnail`;
        } catch (error) {
            Logger.warn('Failed to load thumbnail for file:', fileId, error);
            return null;
        }
    }
    
    /**
     * Render 3D file preview with thumbnail and enhanced metadata
     */
    render3DFilePreview(fileItem, metadata, thumbnailUrl, enhancedMetadata) {
        const file = fileItem.file;
        const fileMetadata = metadata?.metadata || {};
        
        const thumbnailSection = thumbnailUrl ? `
            <div class="preview-thumbnail">
                <img src="${thumbnailUrl}" alt="3D Preview" class="thumbnail-image"
                     onerror="this.src='assets/placeholder-thumbnail.svg'; this.onerror=null; this.classList.add('placeholder-image');" />
                <div class="thumbnail-overlay">
                    <span class="thumbnail-format">${t('files.preview3d')}</span>
                </div>
            </div>
        ` : `
            <div class="preview-placeholder">
                <img src="assets/placeholder-thumbnail.svg" alt="${t('files.noPreviewAvailable')}" class="placeholder-image" style="max-width: 200px; max-height: 200px;" />
                <p>${t('files.noPreviewAvailable')}</p>
            </div>
        `;
        
        const basicInfo = this.renderBasicFileInfo(file);
        
        return `
            <div class="file-preview-3d">
                <div class="preview-header">
                    <h3>${escapeHtml(file.filename)}</h3>
                    <div class="file-type-badge badge-3d">${file.file_type?.toUpperCase()}</div>
                </div>
                
                <div class="preview-content">
                    <div class="preview-main">
                        ${thumbnailSection}
                        ${basicInfo}
                    </div>
                </div>
                
                <!-- Enhanced Metadata Section -->
                <div id="enhanced-metadata-${file.id}" class="enhanced-metadata-container">
                    ${enhancedMetadata ? enhancedMetadata.renderLoading() : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * Render generic file preview (non-3D files)
     */
    renderGenericFilePreview(fileItem, metadata) {
        const file = fileItem.file;
        const basicInfo = this.renderBasicFileInfo(file);
        
        return `
            <div class="file-preview-generic">
                <div class="preview-header">
                    <div class="preview-icon">${fileItem.getFileIcon()}</div>
                    <div>
                        <h3>${escapeHtml(file.filename)}</h3>
                        <div class="file-type-badge">${file.file_type?.toUpperCase() || t('common.unknown').toUpperCase()}</div>
                    </div>
                </div>
                
                <div class="preview-content">
                    ${basicInfo}
                </div>
            </div>
        `;
    }
    
    /**
     * Render basic file information
     */
    renderBasicFileInfo(file) {
        return `
            <div class="file-info-section">
                <h4>${t('files.fileInformation')}</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">${t('files.size')}:</span>
                        <span class="info-value">${formatBytes(file.file_size)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">${t('files.type')}:</span>
                        <span class="info-value">${file.file_type || t('common.unknown')}</span>
                    </div>
                    ${file.printer_name ? `
                        <div class="info-item">
                            <span class="info-label">${t('files.printer')}:</span>
                            <span class="info-value">${escapeHtml(file.printer_name)}</span>
                        </div>
                    ` : ''}
                    ${file.created_at ? `
                        <div class="info-item">
                            <span class="info-label">${t('files.created')}:</span>
                            <span class="info-value">${formatDateTime(file.created_at)}</span>
                        </div>
                    ` : ''}
                    ${file.modified_time ? `
                        <div class="info-item">
                            <span class="info-label">${t('files.modified')}:</span>
                            <span class="info-value">${formatDateTime(file.modified_time)}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * Render 3D metadata information
     */
    render3DMetadata(metadata) {
        if (!metadata || Object.keys(metadata).length === 0) {
            return `
                <div class="metadata-section">
                    <h4>${t('files.modelInformation')}</h4>
                    <p class="no-metadata">${t('files.noMetadata')}</p>
                    <small>${t('files.metadataExtractHint')}</small>
                </div>
            `;
        }
        
        const metadataItems = [];
        
        // Print settings
        if (metadata.layer_height) {
            metadataItems.push({
                label: t('files.layerHeight'),
                value: `${metadata.layer_height} mm`
            });
        }
        
        if (metadata.infill_density) {
            metadataItems.push({
                label: t('files.infill'),
                value: `${metadata.infill_density}%`
            });
        }
        
        if (metadata.print_speed) {
            metadataItems.push({
                label: t('files.printSpeed'),
                value: `${metadata.print_speed} mm/s`
            });
        }
        
        if (metadata.nozzle_temperature) {
            metadataItems.push({
                label: t('files.nozzleTemp'),
                value: `${metadata.nozzle_temperature}°C`
            });
        }
        
        if (metadata.bed_temperature) {
            metadataItems.push({
                label: t('files.bedTemp'),
                value: `${metadata.bed_temperature}°C`
            });
        }
        
        // Time and material estimates
        if (metadata.estimated_print_time) {
            metadataItems.push({
                label: t('files.estimatedPrintTime'),
                value: formatDuration(metadata.estimated_print_time)
            });
        }
        
        if (metadata.filament_used) {
            metadataItems.push({
                label: t('files.filamentUsed'),
                value: `${metadata.filament_used} g`
            });
        }
        
        // Model dimensions
        if (metadata.model_width && metadata.model_depth && metadata.model_height) {
            metadataItems.push({
                label: t('files.modelSize'),
                value: `${metadata.model_width} × ${metadata.model_depth} × ${metadata.model_height} mm`
            });
        }
        
        // Slicer info
        if (metadata.slicer_name && metadata.slicer_version) {
            metadataItems.push({
                label: 'Slicer',
                value: `${metadata.slicer_name} ${metadata.slicer_version}`
            });
        }
        
        return `
            <div class="metadata-section">
                <h4>${t('files.modelInformation')}</h4>
                ${metadataItems.length > 0 ? `
                    <div class="info-grid">
                        ${metadataItems.map(item => `
                            <div class="info-item">
                                <span class="info-label">${item.label}:</span>
                                <span class="info-value">${item.value}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : `
                    <p class="no-metadata">${t('files.noMetadata')}</p>
                `}
            </div>
        `;
    }
    
    /**
     * Render error state for preview
     */
    renderPreviewError(fileItem, error) {
        return `
            <div class="preview-error">
                <div class="error-icon">⚠️</div>
                <h3>${t('files.previewLoadError')}</h3>
                <p>${t('files.previewLoadErrorMessage', { name: escapeHtml(fileItem.file.filename) })}</p>
                <details>
                    <summary>${t('files.errorDetails')}</summary>
                    <pre>${escapeHtml(error.toString())}</pre>
                </details>
                <div class="preview-actions">
                    <button class="btn btn-secondary" onclick="closeModal('filePreviewModal')">
                        ${t('common.close')}
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Open local file (delegates to the global browser-download helper)
     */
    openLocalFile(fileId) {
        window.openLocalFile(fileId);
    }

    /**
     * Upload file to printer (delegates to the global helper)
     */
    uploadToPrinter(fileId) {
        window.uploadFileToPrinter(fileId);
    }

    /**
     * Delete local file
     */
    async deleteLocalFile(fileId) {
        const fileItem = this.files.get(fileId);
        if (!fileItem) return;
        
        const confirmed = confirm(t('files.deleteLocalConfirm', { name: fileItem.file.filename }));
        if (!confirmed) return;

        try {
            await api.deleteFile(fileId);
            showToast('success', t('common.success'), t('files.localFileDeleted'));
            
            // Update file item
            fileItem.file.status = 'available';
            fileItem.file.local_path = null;
            fileItem.update(fileItem.file);
            
            // Refresh statistics
            this.loadFileStatistics();
            
        } catch (error) {
            Logger.error('Failed to delete local file:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('files.deleteLocalError');
            showToast('error', t('common.error'), message);
        }
    }

    /**
     * Show cleanup candidates
     */
    async showCleanupCandidates() {
        try {
            const response = await api.getCleanupCandidates({
                deleted_days: 30,
                failed_days: 7
            });
            const result = response?.data || response;

            if (result.total_candidates > 0) {
                const message = t('files.cleanupCandidates', {
                    count: result.total_candidates,
                    deleted: result.candidates.old_deleted,
                    failed: result.candidates.failed_downloads
                });
                showToast('info', t('files.cleanupPossible'), message);
            } else {
                showToast('info', t('files.cleanup'), t('files.noCleanupCandidates'));
            }

        } catch (error) {
            Logger.error('Failed to load cleanup candidates:', error);
            showToast('error', t('common.error'), t('files.cleanupLoadError'));
        }
    }

    /**
     * Load and display watch folders
     */
    async loadWatchFolders() {
        try {
            const container = document.getElementById('watchFoldersContainer');
            if (!container) return;
            
            // Show loading state
            setLoadingState(container, true);
            
            // Load watch folder settings and status
            const [settings, status] = await Promise.all([
                api.getWatchFolderSettings(),
                api.getWatchFolderStatus()
            ]);
            
            // Render watch folders display
            container.innerHTML = this.renderWatchFolders(settings, status);
            
        } catch (error) {
            Logger.error('Failed to load watch folders:', error);
            const container = document.getElementById('watchFoldersContainer');
            if (container) {
                container.innerHTML = this.renderWatchFoldersError(error);
            }
        }
    }

    /**
     * Render watch folders display
     */
    renderWatchFolders(settings, status) {
        const watchFolders = settings.watch_folders || [];
        const isEnabled = settings.enabled;
        const isRecursive = settings.recursive;
        const isRunning = status.is_running;

        if (watchFolders.length === 0) {
            return `
                <div class="empty-state">
                    <div class="empty-state-icon">📂</div>
                    <h3>${t('files.noWatchFolders')}</h3>
                    <p>${t('files.watchFoldersHint')}</p>
                    <button class="btn btn-primary" onclick="showAddWatchFolderDialog()">
                        <span class="btn-icon">📂</span>
                        ${t('files.addFirstFolder')}
                    </button>
                </div>
            `;
        }

        const statusBadge = isRunning
            ? `<span class="badge badge-success">${t('files.active')}</span>`
            : `<span class="badge badge-danger">${t('files.inactive')}</span>`;

        const settingsInfo = `
            <div class="watch-folders-info">
                <div class="info-item">
                    <strong>Status:</strong> ${statusBadge}
                </div>
                <div class="info-item">
                    <strong>${t('files.monitoring')}:</strong> ${isEnabled ? t('files.enabled') : t('files.disabled')}
                </div>
                <div class="info-item">
                    <strong>${t('files.recursive')}:</strong> ${isRecursive ? t('common.yes') : t('common.no')}
                </div>
                <div class="info-item">
                    <strong>${t('files.localFiles')}:</strong> ${status.local_files_count || 0}
                </div>
            </div>
        `;

        const foldersGrid = `
            <div class="watch-folders-grid">
                ${watchFolders.map(folder => {
                    const folderPath = typeof folder === 'string' ? folder : folder.folder_path;
                    const isActive = typeof folder === 'object' ? folder.is_active : true;
                    const statusBadge = isActive
                        ? `<span class="status-badge active">${t('files.active')}</span>`
                        : `<span class="status-badge inactive">${t('files.inactive')}</span>`;

                    const toggleButton = isActive
                        ? `<button class="btn btn-warning btn-sm" onclick="deactivateWatchFolder('${escapeHtml(folderPath)}')"
                               title="${t('files.deactivateFolder')}">
                               <span class="btn-icon">⏸️</span>
                           </button>`
                        : `<button class="btn btn-success btn-sm" onclick="activateWatchFolder('${escapeHtml(folderPath)}')"
                               title="${t('files.activateFolder')}">
                               <span class="btn-icon">▶️</span>
                           </button>`;
                    
                    return `
                        <div class="watch-folder-item ${isActive ? 'active' : 'inactive'}">
                            <div class="folder-icon">📂</div>
                            <div class="folder-info">
                                <div class="folder-path" title="${escapeHtml(folderPath)}">${escapeHtml(folderPath)}</div>
                                <div class="folder-status">${statusBadge}</div>
                            </div>
                            <div class="folder-actions">
                                ${toggleButton}
                                <button class="btn btn-danger btn-sm" onclick="removeWatchFolder('${escapeHtml(folderPath)}')"
                                        title="${t('files.removeFolder')}">
                                    <span class="btn-icon">🗑️</span>
                                </button>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        return settingsInfo + foldersGrid;
    }

    /**
     * Render watch folders error state
     */
    renderWatchFoldersError(error) {
        const message = error instanceof ApiError ? error.getUserMessage() : t('files.watchFoldersLoadError');

        return `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>${t('files.loadErrorTitle')}</h3>
                <p>${escapeHtml(message)}</p>
                <button class="btn btn-primary" onclick="fileManager.loadWatchFolders()">
                    <span class="btn-icon">🔄</span>
                    ${t('common.retry')}
                </button>
            </div>
        `;
    }

    /**
     * Setup watch folder form handler
     */
    setupWatchFolderForm() {
        const form = document.getElementById('addWatchFolderForm');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.addWatchFolder();
        });
    }

    /**
     * Load and display discovered files from watch folders
     */
    async loadDiscoveredFiles(page = 1) {
        const container = document.getElementById('discoveredFilesContainer');
        if (!container) return;

        try {
            // Show loading state on initial load
            if (page === 1) {
                container.innerHTML = `
                    <div class="loading-placeholder">
                        <div class="spinner"></div>
                        <p>${t('files.loadingDiscovered')}</p>
                    </div>
                `;
            }

            // Fetch discovered files with pagination
            const response = await api.getFiles({
                source: 'local_watch',
                page: page,
                limit: 50
            });
            const files = response.files || [];
            const pagination = response.pagination || { page: 1, total_pages: 1, total_items: files.length };

            if (files.length === 0 && page === 1) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📂</div>
                        <h3>${t('files.noFilesDiscovered')}</h3>
                        <p>${t('files.noFilesInWatchFolders')}</p>
                    </div>
                `;
                return;
            }

            // Render discovered files table with pagination
            container.innerHTML = this.renderDiscoveredFilesTable(files, pagination);

        } catch (error) {
            Logger.error('Failed to load discovered files:', error);
            container.innerHTML = `
                <div class="error-state">
                    <div class="error-icon">⚠️</div>
                    <h3>${t('files.loadingFailed')}</h3>
                    <p>${t('files.discoveredLoadError')}</p>
                    <button class="btn btn-secondary" onclick="fileManager.loadDiscoveredFiles()">
                        <span class="btn-icon">🔄</span>
                        ${t('common.retry')}
                    </button>
                </div>
            `;
        }
    }

    /**
     * Render discovered files table
     */
    renderDiscoveredFilesTable(files, pagination) {
        const currentPageSize = files.length;
        const totalSize = files.reduce((sum, file) => sum + (file.file_size || 0), 0);
        const totalItems = pagination ? pagination.total_items : files.length;

        const paginationHtml = pagination && pagination.total_pages > 1 ? `
            <div class="discovered-files-pagination">
                <div class="pagination-info">
                    ${t('files.pageInfo', { page: pagination.page, total: pagination.total_pages, count: totalItems })}
                </div>
                <div class="pagination-controls">
                    ${pagination.page > 1 ? `
                        <button class="btn btn-small btn-secondary" onclick="fileManager.loadDiscoveredFiles(${pagination.page - 1})">
                            <span class="btn-icon">◀</span>
                            ${t('common.back')}
                        </button>
                    ` : ''}
                    ${pagination.page < pagination.total_pages ? `
                        <button class="btn btn-small btn-secondary" onclick="fileManager.loadDiscoveredFiles(${pagination.page + 1})">
                            ${t('common.next')}
                            <span class="btn-icon">▶</span>
                        </button>
                    ` : ''}
                </div>
            </div>
        ` : '';

        return `
            <div class="discovered-files-summary">
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-value">${totalItems}</span>
                        <span class="stat-label">${t('files.totalFiles')}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${currentPageSize}</span>
                        <span class="stat-label">${t('files.onThisPage')}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${formatBytes(totalSize)}</span>
                        <span class="stat-label">${t('files.sizePage')}</span>
                    </div>
                </div>
            </div>

            ${paginationHtml}

            <div class="table-container">
                <table class="files-table">
                    <thead>
                        <tr>
                            <th>📄 ${t('files.filename')}</th>
                            <th>📐 ${t('files.size')}</th>
                            <th>📁 ${t('files.source')}</th>
                            <th>📁 ${t('files.folder')}</th>
                            <th>📅 ${t('files.modified')}</th>
                            <th>🔧 ${t('files.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${files.map(file => this.renderDiscoveredFileRow(file)).join('')}
                    </tbody>
                </table>
            </div>

            ${paginationHtml}
        `;
    }

    /**
     * Render individual discovered file row
     */
    renderDiscoveredFileRow(file) {
        const fileName = file.filename || file.name || t('common.unknown');
        const fileSize = formatBytes(file.file_size || 0);
        const watchFolderPath = file.watch_folder_path || t('common.unknown');
        const modifiedTime = file.modified_time ?
            new Date(file.modified_time).toLocaleString('de-DE') : t('common.unknown');

        // Determine source display (printer or watch folder)
        let sourceDisplay = t('status.file.local');
        if (file.source === 'printer' && file.printer_name) {
            sourceDisplay = file.printer_name;
        } else if (file.source === 'local_watch') {
            sourceDisplay = 'Watch Folder';
        } else if (file.source_display) {
            sourceDisplay = file.source_display;
        }

        const fileIcon = this.getFileIcon(fileName);
        const truncatedPath = truncateText(watchFolderPath, 40);
        const filePath = file.file_path || file.path || '';

        return `
            <tr class="file-row discovered-file" data-file-path="${escapeHtml(filePath)}">
                <td class="file-name">
                    <div class="file-info">
                        <span class="file-icon">${fileIcon}</span>
                        <div class="file-details">
                            <span class="name" title="${escapeHtml(fileName)}">${truncateText(fileName, 30)}</span>
                            <span class="path" title="${escapeHtml(filePath)}">${truncateText(file.relative_path || '', 50)}</span>
                        </div>
                    </div>
                </td>
                <td class="file-size">${fileSize}</td>
                <td class="file-source" title="${escapeHtml(sourceDisplay)}">
                    <span class="source-icon">📍</span>
                    ${truncateText(sourceDisplay, 20)}
                </td>
                <td class="watch-folder" title="${escapeHtml(watchFolderPath)}">
                    <span class="folder-icon">📁</span>
                    ${truncatedPath}
                </td>
                <td class="modified-time">${modifiedTime}</td>
                <td class="file-actions">
                    <div class="action-buttons">
                        <button class="btn btn-small btn-secondary"
                                onclick="openFileLocation('${escapeHtml(filePath)}')"
                                title="${t('files.openInExplorer')}">
                            <span class="btn-icon">📂</span>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * Get file icon based on extension
     */
    getFileIcon(filename) {
        if (!filename) return '📄';

        const ext = filename.toLowerCase().split('.').pop();

        const iconMap = {
            // 3D Files
            'stl': '🏗️',
            '3mf': '📐',
            'obj': '🎯',
            'ply': '⚪',

            // G-Code
            'gcode': '⚙️',
            'g': '⚙️',

            // Images
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
            'bmp': '🖼️', 'tiff': '🖼️', 'webp': '🖼️',

            // Documents
            'pdf': '📕', 'doc': '📄', 'docx': '📄', 'txt': '📝',

            // Archives
            'zip': '📦', 'rar': '📦', '7z': '📦', 'tar': '📦',

            // Default
            'default': '📄'
        };

        return iconMap[ext] || iconMap['default'];
    }

    /**
     * Add a new watch folder
     */
    async addWatchFolder() {
        const folderPathInput = document.getElementById('watchFolderPath');
        const submitButton = document.getElementById('addWatchFolderSubmit');
        
        if (!folderPathInput || !submitButton) return;

        const folderPath = folderPathInput.value.trim();
        if (!folderPath) {
            showToast('error', t('common.error'), t('files.enterFolderPath'));
            return;
        }

        try {
            // Disable submit button
            submitButton.disabled = true;
            submitButton.innerHTML = `<span class="spinner-small"></span> ${t('files.adding')}`;

            // Add the watch folder
            const response = await api.addWatchFolder(folderPath);

            if (response.status === 'added') {
                showToast('success', t('common.success'), t('files.folderAdded', { path: folderPath }));

                // Reset form
                folderPathInput.value = '';
                const validationResult = document.getElementById('folderValidationResult');
                if (validationResult) {
                    validationResult.style.display = 'none';
                }

                // Close modal first to give immediate feedback
                closeModal('addWatchFolderModal');

                // Reload watch folders and discovered files (in background, don't block on errors)
                try {
                    await this.loadWatchFolders();
                    await this.loadDiscoveredFiles();
                } catch (reloadError) {
                    Logger.warn('Error reloading after folder addition:', reloadError);
                    // Don't show error to user - folder was added successfully
                }
            }

        } catch (error) {
            Logger.error('Failed to add watch folder:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('files.addFolderError');
            showToast('error', t('common.error'), message);
            // Don't close modal on error so user can see the error and try again
        } finally {
            // Re-enable submit button
            submitButton.disabled = false;
            submitButton.innerHTML = `<span class="btn-icon">📂</span> ${t('common.add')}`;
        }
    }

    /**
     * Remove a watch folder
     */
    async removeWatchFolder(folderPath) {
        Logger.debug('[removeWatchFolder] Called with folderPath:', folderPath);

        const confirmed = confirm(t('files.removeFolderConfirm', { path: folderPath }));
        if (!confirmed) {
            Logger.debug('[removeWatchFolder] User cancelled');
            return;
        }

        try {
            Logger.debug('[removeWatchFolder] Calling API to remove folder');
            showToast('info', t('settings.removingFolderTitle'), t('files.removingFromWatch'));

            const response = await api.removeWatchFolder(folderPath);
            Logger.debug('[removeWatchFolder] API response:', response);

            if (response.status === 'removed') {
                showToast('success', t('files.folderRemovedTitle'), t('files.folderRemoved', { path: folderPath }));

                // Reload watch folders and discovered files
                try {
                    Logger.debug('[removeWatchFolder] Reloading UI components');
                    await this.loadWatchFolders();
                    await this.loadDiscoveredFiles();
                    // Also reload the main file list to remove files from removed folder
                    await this.loadFiles(1);
                    Logger.debug('[removeWatchFolder] UI reload completed');
                } catch (reloadError) {
                    Logger.warn('Error reloading after folder removal:', reloadError);
                    showToast('warning', t('common.info'), t('files.folderRemovedReloadHint'));
                }
            } else {
                Logger.warn('[removeWatchFolder] Unexpected response status:', response.status);
            }

        } catch (error) {
            Logger.error('[removeWatchFolder] Failed to remove watch folder:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('files.removeFolderError');
            showToast('error', t('files.removeFolderErrorTitle'), message);
        }
    }
}

// Global file manager instance
const fileManager = new FileManager();

/**
 * Global functions for file management
 */

/**
 * Refresh files list
 */
function refreshFiles() {
    fileManager.loadFiles();
    fileManager.loadFileStatistics();
}

/**
 * Clear file search
 */
function clearFileSearch() {
    const searchInput = document.getElementById('fileSearchInput');
    const searchClearBtn = document.getElementById('fileSearchClear');

    if (searchInput) {
        searchInput.value = '';
    }
    if (searchClearBtn) {
        searchClearBtn.style.display = 'none';
    }

    // Clear search filter and reload
    fileManager.currentFilters.search = undefined;
    fileManager.loadFiles(1);
    fileManager.loadFileStatistics();
}

/**
 * Download file from printer (called from components)
 */
function downloadFileFromPrinter(fileId) {
    fileManager.downloadFileFromPrinter(fileId);
}

/**
 * Preview file (called from components)
 */
function previewFile(fileId) {
    fileManager.previewFile(fileId);
}

/**
 * Open local file (called from components)
 */
function openLocalFile(fileId) {
    fileManager.openLocalFile(fileId);
}

/**
 * Upload file to printer (called from components)
 */
function uploadToPrinter(fileId) {
    fileManager.uploadToPrinter(fileId);
}

/**
 * Delete local file (called from components)
 */
function deleteLocalFile(fileId) {
    fileManager.deleteLocalFile(fileId);
}

/**
 * Refresh watch folders
 */
function refreshWatchFolders() {
    fileManager.loadWatchFolders();
}

/**
 * Show add watch folder dialog
 */
function showAddWatchFolderDialog() {
    showModal('addWatchFolderModal');
}

/**
 * Remove watch folder (called from template)
 */
function removeWatchFolder(folderPath) {
    fileManager.removeWatchFolder(folderPath);
}

/**
 * Activate watch folder (called from template)
 */
async function activateWatchFolder(folderPath) {
    try {
        const response = await api.updateWatchFolder(folderPath, true);
        
        if (response.success) {
            showToast('success', t('common.success'), t('files.folderActivated', { path: folderPath }));
            fileManager.loadWatchFolders();
        }
    } catch (error) {
        Logger.error('Failed to activate watch folder:', error);
        const message = error instanceof ApiError ? error.getUserMessage() : t('files.activateFolderError');
        showToast('error', t('common.error'), message);
    }
}

/**
 * Deactivate watch folder (called from template)
 */
async function deactivateWatchFolder(folderPath) {
    const confirmed = confirm(t('files.deactivateFolderConfirm', { path: folderPath }));
    if (!confirmed) return;
    
    try {
        const response = await api.updateWatchFolder(folderPath, false);
        
        if (response.success) {
            showToast('success', t('common.success'), t('files.folderDeactivated', { path: folderPath }));
            fileManager.loadWatchFolders();
        }
    } catch (error) {
        Logger.error('Failed to deactivate watch folder:', error);
        const message = error instanceof ApiError ? error.getUserMessage() : t('files.deactivateFolderError');
        showToast('error', t('common.error'), message);
    }
}

/**
 * Validate watch folder path
 */
async function validateWatchFolderPath() {
    const folderPathInput = document.getElementById('watchFolderPath');
    const validationResult = document.getElementById('folderValidationResult');
    
    if (!folderPathInput || !validationResult) return;

    const folderPath = folderPathInput.value.trim();
    if (!folderPath) {
        validationResult.style.display = 'none';
        return;
    }

    try {
        // Show loading state
        validationResult.style.display = 'block';
        validationResult.className = 'validation-result loading';
        validationResult.innerHTML = `<span class="spinner-small"></span> ${t('settings.validating')}`;

        // Validate path
        const response = await api.validateWatchFolder(folderPath);
        
        if (response.valid) {
            validationResult.className = 'validation-result success';
            validationResult.innerHTML = '<span class="icon">✓</span> ' + (response.message || t('files.folderValid'));
        } else {
            validationResult.className = 'validation-result error';
            validationResult.innerHTML = '<span class="icon">✗</span> ' + (response.error || t('files.folderInvalid'));
        }

    } catch (error) {
        Logger.error('Failed to validate watch folder:', error);
        validationResult.className = 'validation-result error';
        validationResult.innerHTML = `<span class="icon">✗</span> ${t('settings.validationFailed')}`;
    }
}

/**
 * Open file location in explorer
 */
function openFileLocation(filePath) {
    if (!filePath) return;

    // Note: This would typically require a desktop app or system integration
    // For now, we'll just show the path
    showToast('info', t('files.filePath'), filePath);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FileManager, fileManager };
}