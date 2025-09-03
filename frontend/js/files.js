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
    }

    /**
     * Initialize file management page
     */
    init() {
        console.log('Initializing file management');
        
        // Load files
        this.loadFiles();
        
        // Load file statistics
        this.loadFileStatistics();
        
        // Setup filter handlers
        this.setupFilterHandlers();
        
        // Set up refresh interval
        this.startAutoRefresh();
        
        // Setup WebSocket listeners
        this.setupWebSocketListeners();
        
        // Load printer options for filter
        this.loadPrinterOptions();
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
            const response = await api.getFiles({ page: 1, limit: 1 });
            
            if (response.summary) {
                statsContainer.innerHTML = this.renderFileStatistics(response.summary);
            } else {
                statsContainer.innerHTML = this.renderFileStatisticsError();
            }
            
        } catch (error) {
            console.error('Failed to load file statistics:', error);
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
                    <div class="stat-label">📁 Verfügbar</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${summary.downloaded_count || 0}</div>
                    <div class="stat-label">✓ Heruntergeladen</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${summary.local_count || 0}</div>
                    <div class="stat-label">💾 Lokal</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${formatBytes(summary.total_size || 0)}</div>
                    <div class="stat-label">Gesamtgröße</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${formatPercentage((summary.download_success_rate || 0) * 100)}</div>
                    <div class="stat-label">Erfolgsrate</div>
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
                <strong>Statistiken nicht verfügbar</strong><br>
                Fehler beim Laden der Datei-Statistiken.
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
            console.error('Failed to load files:', error);
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
            Dateien ${start}-${end} von ${paginationData.total_items}
        `;
    }

    /**
     * Setup filter change handlers
     */
    setupFilterHandlers() {
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
            if (!printerFilter) return;
            
            const response = await api.getPrinters();
            
            // Clear existing options (except "All Printers")
            const firstOption = printerFilter.firstElementChild;
            printerFilter.innerHTML = '';
            if (firstOption) {
                printerFilter.appendChild(firstOption);
            }
            
            // Add printer options
            if (response.printers) {
                response.printers.forEach(printer => {
                    const option = document.createElement('option');
                    option.value = printer.id;
                    option.textContent = printer.name;
                    printerFilter.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Failed to load printer options:', error);
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
                    <h3>Keine Dateien gefunden</h3>
                    <p>Keine Dateien entsprechen den aktuellen Filterkriterien.</p>
                    <button class="btn btn-secondary" onclick="fileManager.clearFilters()">
                        <span class="btn-icon">🗑️</span>
                        Filter löschen
                    </button>
                </div>
            `;
        }
        
        return `
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <h3>Keine Dateien verfügbar</h3>
                <p>Hier werden alle verfügbaren Dateien von Ihren Druckern angezeigt.</p>
            </div>
        `;
    }

    /**
     * Render files error state
     */
    renderFilesError(error) {
        const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Laden der Dateien';
        
        return `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Ladefehler</h3>
                <p>${escapeHtml(message)}</p>
                <button class="btn btn-primary" onclick="fileManager.loadFiles()">
                    <span class="btn-icon">🔄</span>
                    Erneut versuchen
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
        
        if (statusFilter) statusFilter.value = '';
        if (printerFilter) printerFilter.value = '';
        
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
            console.error('Failed to refresh files:', error);
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
                showToast('info', 'Download gestartet', `Download von "${fileItem.file.filename}" wurde gestartet`);
                
                // Update file status immediately
                fileItem.file.status = 'downloading';
                fileItem.update(fileItem.file);
                
                // Start monitoring download progress
                this.monitorDownloadProgress(fileId, response.download_id);
            }
            
        } catch (error) {
            console.error('Failed to start download:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : CONFIG.ERROR_MESSAGES.DOWNLOAD_FAILED;
            showToast('error', 'Download-Fehler', message);
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
                const progress = await api.getDownloadStatus(fileId);
                
                if (progress.status === 'downloading') {
                    // Update progress display
                    this.updateDownloadProgress(fileId, progress);
                    
                    // Continue monitoring
                    if (attempts < maxAttempts) {
                        attempts++;
                        setTimeout(checkProgress, 1000);
                    }
                } else if (progress.status === 'completed') {
                    // Download completed
                    showToast('success', 'Download abgeschlossen', CONFIG.SUCCESS_MESSAGES.FILE_DOWNLOADED);
                    
                    // Update file item
                    const fileItem = this.files.get(fileId);
                    if (fileItem) {
                        fileItem.file.status = 'downloaded';
                        fileItem.update(fileItem.file);
                    }
                    
                    // Refresh statistics
                    this.loadFileStatistics();
                    
                } else if (progress.error) {
                    // Download failed
                    showToast('error', 'Download fehlgeschlagen', progress.error);
                    
                    // Reset file status
                    const fileItem = this.files.get(fileId);
                    if (fileItem) {
                        fileItem.file.status = 'available';
                        fileItem.update(fileItem.file);
                    }
                }
                
            } catch (error) {
                console.error('Failed to check download progress:', error);
                
                // Stop monitoring on persistent errors
                if (attempts > 5) {
                    showToast('error', 'Download-Fehler', 'Download-Fortschritt kann nicht überwacht werden');
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
     * Preview file (placeholder implementation)
     */
    previewFile(fileId) {
        const fileItem = this.files.get(fileId);
        if (!fileItem) return;
        
        // Show preview modal (placeholder)
        const modal = document.getElementById('filePreviewModal');
        const content = document.getElementById('filePreviewContent');
        
        if (modal && content) {
            showModal('filePreviewModal');
            content.innerHTML = `
                <div class="file-preview-placeholder">
                    <div class="preview-icon">${fileItem.getFileIcon()}</div>
                    <h3>${escapeHtml(fileItem.file.filename)}</h3>
                    <p>3D-Vorschau wird in Phase 2 implementiert</p>
                    <div class="file-info">
                        <p><strong>Größe:</strong> ${formatBytes(fileItem.file.file_size)}</p>
                        <p><strong>Typ:</strong> ${fileItem.file.file_type}</p>
                        ${fileItem.file.printer_name ? `<p><strong>Drucker:</strong> ${fileItem.file.printer_name}</p>` : ''}
                    </div>
                </div>
            `;
        }
    }

    /**
     * Open local file
     */
    openLocalFile(fileId) {
        showToast('info', 'Funktion nicht verfügbar', 'Lokale Datei-Anzeige wird in Phase 2 implementiert');
    }

    /**
     * Upload file to printer
     */
    uploadToPrinter(fileId) {
        showToast('info', 'Funktion nicht verfügbar', 'Upload zu Drucker wird in Phase 2 implementiert');
    }

    /**
     * Delete local file
     */
    async deleteLocalFile(fileId) {
        const fileItem = this.files.get(fileId);
        if (!fileItem) return;
        
        const confirmed = confirm(`Möchten Sie die lokale Datei "${fileItem.file.filename}" wirklich löschen?`);
        if (!confirmed) return;
        
        try {
            await api.deleteFile(fileId);
            showToast('success', 'Erfolg', 'Lokale Datei wurde gelöscht');
            
            // Update file item
            fileItem.file.status = 'available';
            fileItem.file.local_path = null;
            fileItem.update(fileItem.file);
            
            // Refresh statistics
            this.loadFileStatistics();
            
        } catch (error) {
            console.error('Failed to delete local file:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Löschen der lokalen Datei';
            showToast('error', 'Fehler', message);
        }
    }

    /**
     * Show cleanup candidates
     */
    async showCleanupCandidates() {
        try {
            const candidates = await api.getCleanupCandidates({
                older_than_days: 30,
                min_size_mb: 1,
                unused_only: true
            });
            
            if (candidates.cleanup_candidates && candidates.cleanup_candidates.length > 0) {
                const message = `
                    ${candidates.total_candidates} Dateien können bereinigt werden
                    Speicherplatz-Ersparnis: ${candidates.total_space_savings_mb} MB
                `;
                showToast('info', 'Bereinigung möglich', message);
            } else {
                showToast('info', 'Bereinigung', 'Keine Dateien zur Bereinigung gefunden');
            }
            
        } catch (error) {
            console.error('Failed to load cleanup candidates:', error);
            showToast('error', 'Fehler', 'Bereinigungs-Kandidaten konnten nicht geladen werden');
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

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FileManager, fileManager };
}