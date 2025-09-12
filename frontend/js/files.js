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
        
        // Load watch folders
        this.loadWatchFolders();
        
        // Load discovered files
        loadDiscoveredFiles();
        
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
     * Preview file (now with thumbnail support)
     */
    previewFile(fileId) {
        const fileItem = this.files.get(fileId);
        if (!fileItem) return;
        
        // Show preview modal
        const modal = document.getElementById('filePreviewModal');
        const content = document.getElementById('filePreviewContent');
        
        if (modal && content) {
            showModal('filePreviewModal');
            
            // Enhanced preview with thumbnail and metadata
            const thumbnailSection = fileItem.file.has_thumbnail ? `
                <div class="file-preview-thumbnail">
                    <img src="/api/files/${fileId}/thumbnail" 
                         alt="Thumbnail für ${escapeHtml(fileItem.file.filename)}"
                         class="preview-thumbnail-image"
                         onerror="this.style.display='none'; this.nextSibling.style.display='block';">
                    <div class="preview-thumbnail-fallback" style="display: none;">
                        <div class="preview-icon-large">${fileItem.getFileIcon()}</div>
                        <p>Thumbnail nicht verfügbar</p>
                    </div>
                </div>
            ` : `
                <div class="file-preview-placeholder">
                    <div class="preview-icon">${fileItem.getFileIcon()}</div>
                </div>
            `;
            
            const metadataSection = this._renderPreviewMetadata(fileItem.file);
            
            content.innerHTML = `
                ${thumbnailSection}
                <div class="file-preview-info">
                    <h3>${escapeHtml(fileItem.file.filename)}</h3>
                    <div class="file-basic-info">
                        <p><strong>Größe:</strong> ${formatBytes(fileItem.file.file_size)}</p>
                        <p><strong>Typ:</strong> ${fileItem.file.file_type}</p>
                        ${fileItem.file.printer_name ? `<p><strong>Drucker:</strong> ${fileItem.file.printer_name}</p>` : ''}
                    </div>
                    ${metadataSection}
                </div>
            `;
        }
    }

    /**
     * Render metadata section for preview modal
     */
    _renderPreviewMetadata(file) {
        const metadataItems = [];
        
        if (file.estimated_print_time) {
            const hours = Math.floor(file.estimated_print_time / 3600);
            const minutes = Math.floor((file.estimated_print_time % 3600) / 60);
            const timeStr = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
            metadataItems.push(`<p><strong>⏱️ Geschätzte Druckzeit:</strong> ${timeStr}</p>`);
        }
        
        if (file.estimated_material_usage) {
            metadataItems.push(`<p><strong>🧵 Materialverbrauch:</strong> ${file.estimated_material_usage.toFixed(1)}g</p>`);
        }
        
        if (file.layer_height) {
            metadataItems.push(`<p><strong>📏 Schichthöhe:</strong> ${file.layer_height}mm</p>`);
        }
        
        if (file.infill) {
            metadataItems.push(`<p><strong>🔲 Füllung:</strong> ${file.infill}%</p>`);
        }
        
        if (file.material_type) {
            metadataItems.push(`<p><strong>🧪 Material:</strong> ${file.material_type}</p>`);
        }
        
        if (metadataItems.length > 0) {
            return `
                <div class="file-preview-metadata">
                    <h4>Druckeinstellungen</h4>
                    ${metadataItems.join('')}
                </div>
            `;
        }
        
        return '';
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
            console.error('Failed to load watch folders:', error);
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
                    <h3>Keine überwachten Verzeichnisse</h3>
                    <p>Fügen Sie Verzeichnisse hinzu, um automatisch neue 3D-Dateien zu erkennen.</p>
                    <button class="btn btn-primary" onclick="showAddWatchFolderDialog()">
                        <span class="btn-icon">📂</span>
                        Erstes Verzeichnis hinzufügen
                    </button>
                </div>
            `;
        }

        const statusBadge = isRunning 
            ? '<span class="badge badge-success">Aktiv</span>'
            : '<span class="badge badge-danger">Inaktiv</span>';

        const settingsInfo = `
            <div class="watch-folders-info">
                <div class="info-item">
                    <strong>Status:</strong> ${statusBadge}
                </div>
                <div class="info-item">
                    <strong>Überwachung:</strong> ${isEnabled ? 'Aktiviert' : 'Deaktiviert'}
                </div>
                <div class="info-item">
                    <strong>Rekursiv:</strong> ${isRecursive ? 'Ja' : 'Nein'}
                </div>
                <div class="info-item">
                    <strong>Lokale Dateien:</strong> ${status.local_files_count || 0}
                </div>
            </div>
        `;

        const foldersGrid = `
            <div class="watch-folders-grid">
                ${watchFolders.map(folder => {
                    const folderPath = typeof folder === 'string' ? folder : folder.folder_path;
                    const isActive = typeof folder === 'object' ? folder.is_active : true;
                    const statusBadge = isActive 
                        ? '<span class="status-badge active">Aktiv</span>'
                        : '<span class="status-badge inactive">Inaktiv</span>';
                    
                    const toggleButton = isActive
                        ? `<button class="btn btn-warning btn-sm" onclick="deactivateWatchFolder('${escapeHtml(folderPath)}')" 
                               title="Verzeichnis deaktivieren">
                               <span class="btn-icon">⏸️</span>
                           </button>`
                        : `<button class="btn btn-success btn-sm" onclick="activateWatchFolder('${escapeHtml(folderPath)}')" 
                               title="Verzeichnis aktivieren">
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
                                        title="Verzeichnis entfernen">
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
        const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Laden der überwachten Verzeichnisse';
        
        return `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Ladefehler</h3>
                <p>${escapeHtml(message)}</p>
                <button class="btn btn-primary" onclick="fileManager.loadWatchFolders()">
                    <span class="btn-icon">🔄</span>
                    Erneut versuchen
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
     * Add a new watch folder
     */
    async addWatchFolder() {
        const folderPathInput = document.getElementById('watchFolderPath');
        const submitButton = document.getElementById('addWatchFolderSubmit');
        
        if (!folderPathInput || !submitButton) return;

        const folderPath = folderPathInput.value.trim();
        if (!folderPath) {
            showToast('error', 'Fehler', 'Bitte geben Sie einen Verzeichnispfad an');
            return;
        }

        try {
            // Disable submit button
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-small"></span> Hinzufügen...';

            // Add the watch folder
            const response = await api.addWatchFolder(folderPath);

            if (response.status === 'added') {
                showToast('success', 'Erfolg', `Verzeichnis "${folderPath}" wurde hinzugefügt`);
                
                // Close modal and refresh
                closeModal('addWatchFolderModal');
                this.loadWatchFolders();
                
                // Reset form
                folderPathInput.value = '';
                const validationResult = document.getElementById('folderValidationResult');
                if (validationResult) {
                    validationResult.style.display = 'none';
                }
            }

        } catch (error) {
            console.error('Failed to add watch folder:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Hinzufügen des Verzeichnisses';
            showToast('error', 'Fehler', message);
        } finally {
            // Re-enable submit button
            submitButton.disabled = false;
            submitButton.innerHTML = '<span class="btn-icon">📂</span> Hinzufügen';
        }
    }

    /**
     * Remove a watch folder
     */
    async removeWatchFolder(folderPath) {
        const confirmed = confirm(`Möchten Sie das Verzeichnis "${folderPath}" wirklich aus der Überwachung entfernen?`);
        if (!confirmed) return;

        try {
            const response = await api.removeWatchFolder(folderPath);

            if (response.status === 'removed') {
                showToast('success', 'Erfolg', `Verzeichnis "${folderPath}" wurde entfernt`);
                this.loadWatchFolders();
            }

        } catch (error) {
            console.error('Failed to remove watch folder:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Entfernen des Verzeichnisses';
            showToast('error', 'Fehler', message);
        }
    }
}

// Global file manager instance
const fileManager = new FileManager();

/**
 * Show file thumbnail in modal
 */
function showFileThumbnail(fileId) {
    const fileItem = fileManager.files.get(fileId);
    if (!fileItem || !fileItem.file.has_thumbnail) return;
    
    // Create thumbnail modal if it doesn't exist
    let thumbnailModal = document.getElementById('thumbnailModal');
    if (!thumbnailModal) {
        thumbnailModal = document.createElement('div');
        thumbnailModal.id = 'thumbnailModal';
        thumbnailModal.className = 'modal';
        thumbnailModal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h3>Thumbnail Vorschau</h3>
                    <button class="modal-close" onclick="closeModal('thumbnailModal')">&times;</button>
                </div>
                <div class="modal-body" id="thumbnailModalContent">
                    <!-- Content will be inserted here -->
                </div>
            </div>
        `;
        document.body.appendChild(thumbnailModal);
    }
    
    const content = document.getElementById('thumbnailModalContent');
    if (!content) return;
    
    content.innerHTML = `
        <div class="thumbnail-preview">
            <div class="thumbnail-image-container">
                <img src="/api/files/${fileId}/thumbnail" 
                     alt="Thumbnail für ${escapeHtml(fileItem.file.filename)}"
                     class="thumbnail-image-large"
                     onerror="this.style.display='none'; this.nextSibling.style.display='block';">
                <div class="thumbnail-error" style="display: none;">
                    <div class="error-icon">🖼️</div>
                    <p>Thumbnail konnte nicht geladen werden</p>
                </div>
            </div>
            <div class="thumbnail-info">
                <h4>${escapeHtml(fileItem.file.filename)}</h4>
                <p class="thumbnail-description">G-Code Vorschaubild</p>
            </div>
        </div>
    `;
    
    showModal('thumbnailModal');
}

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
            showToast('success', 'Erfolg', `Verzeichnis "${folderPath}" wurde aktiviert`);
            fileManager.loadWatchFolders();
        }
    } catch (error) {
        console.error('Failed to activate watch folder:', error);
        const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Aktivieren des Verzeichnisses';
        showToast('error', 'Fehler', message);
    }
}

/**
 * Deactivate watch folder (called from template)
 */
async function deactivateWatchFolder(folderPath) {
    const confirmed = confirm(`Möchten Sie das Verzeichnis "${folderPath}" wirklich deaktivieren? Es wird nicht mehr überwacht.`);
    if (!confirmed) return;
    
    try {
        const response = await api.updateWatchFolder(folderPath, false);
        
        if (response.success) {
            showToast('success', 'Erfolg', `Verzeichnis "${folderPath}" wurde deaktiviert`);
            fileManager.loadWatchFolders();
        }
    } catch (error) {
        console.error('Failed to deactivate watch folder:', error);
        const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Deaktivieren des Verzeichnisses';
        showToast('error', 'Fehler', message);
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
        validationResult.innerHTML = '<span class="spinner-small"></span> Validiere...';

        // Validate path
        const response = await api.validateWatchFolder(folderPath);
        
        if (response.valid) {
            validationResult.className = 'validation-result success';
            validationResult.innerHTML = '<span class="icon">✓</span> ' + (response.message || 'Verzeichnis ist gültig');
        } else {
            validationResult.className = 'validation-result error';
            validationResult.innerHTML = '<span class="icon">✗</span> ' + (response.error || 'Verzeichnis ist ungültig');
        }

    } catch (error) {
        console.error('Failed to validate watch folder:', error);
        validationResult.className = 'validation-result error';
        validationResult.innerHTML = '<span class="icon">✗</span> Validierung fehlgeschlagen';
    }
}

// ========================================
// DISCOVERED FILES MANAGEMENT
// ========================================

/**
 * Load and display discovered files from watch folders
 */
async function loadDiscoveredFiles() {
    const container = document.getElementById('discoveredFilesContainer');
    if (!container) return;

    try {
        // Show loading state
        container.innerHTML = `
            <div class="loading-placeholder">
                <div class="spinner"></div>
                <p>Lade entdeckte Dateien...</p>
            </div>
        `;

        // Fetch discovered files
        const response = await api.get('/files/local');
        const files = response.files || [];

        if (files.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📂</div>
                    <h3>Keine Dateien entdeckt</h3>
                    <p>Keine Dateien in den überwachten Verzeichnissen gefunden.</p>
                </div>
            `;
            return;
        }

        // Render discovered files table
        container.innerHTML = renderDiscoveredFilesTable(files);

    } catch (error) {
        console.error('Failed to load discovered files:', error);
        container.innerHTML = `
            <div class="error-state">
                <div class="error-icon">⚠️</div>
                <h3>Fehler beim Laden</h3>
                <p>Entdeckte Dateien konnten nicht geladen werden.</p>
                <button class="btn btn-secondary" onclick="loadDiscoveredFiles()">
                    <span class="btn-icon">🔄</span>
                    Erneut versuchen
                </button>
            </div>
        `;
    }
}

/**
 * Render discovered files table
 */
function renderDiscoveredFilesTable(files) {
    const totalFiles = files.length;
    const totalSize = files.reduce((sum, file) => sum + (file.size || 0), 0);
    
    return `
        <div class="discovered-files-summary">
            <div class="summary-stats">
                <div class="stat-item">
                    <span class="stat-value">${totalFiles}</span>
                    <span class="stat-label">Dateien</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${formatFileSize(totalSize)}</span>
                    <span class="stat-label">Gesamtgröße</span>
                </div>
            </div>
        </div>
        
        <div class="table-container">
            <table class="files-table">
                <thead>
                    <tr>
                        <th>📄 Dateiname</th>
                        <th>📐 Größe</th>
                        <th>📁 Verzeichnis</th>
                        <th>📅 Geändert</th>
                        <th>🔧 Aktionen</th>
                    </tr>
                </thead>
                <tbody>
                    ${files.map(file => renderDiscoveredFileRow(file)).join('')}
                </tbody>
            </table>
        </div>
    `;
}

/**
 * Render individual discovered file row
 */
function renderDiscoveredFileRow(file) {
    const fileName = file.name || 'Unbekannt';
    const fileSize = formatFileSize(file.size || 0);
    const watchFolderPath = file.watch_folder_path || 'Unbekannt';
    const modifiedTime = file.modified_time ? 
        new Date(file.modified_time).toLocaleString('de-DE') : 'Unbekannt';
    
    const fileIcon = getFileIcon(fileName);
    const truncatedPath = truncateText(watchFolderPath, 40);
    
    return `
        <tr class="file-row discovered-file" data-file-path="${file.path}">
            <td class="file-name">
                <div class="file-info">
                    <span class="file-icon">${fileIcon}</span>
                    <div class="file-details">
                        <span class="name" title="${fileName}">${truncateText(fileName, 30)}</span>
                        <span class="path" title="${file.path}">${truncateText(file.relative_path || '', 50)}</span>
                    </div>
                </div>
            </td>
            <td class="file-size">${fileSize}</td>
            <td class="watch-folder" title="${watchFolderPath}">
                <span class="folder-icon">📁</span>
                ${truncatedPath}
            </td>
            <td class="modified-time">${modifiedTime}</td>
            <td class="file-actions">
                <div class="action-buttons">
                    <button class="btn btn-small btn-secondary" 
                            onclick="openFileLocation('${file.path}')" 
                            title="Im Explorer öffnen">
                        <span class="btn-icon">📂</span>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

/**
 * Open file location in explorer
 */
function openFileLocation(filePath) {
    if (!filePath) return;
    
    // Note: This would typically require a desktop app or system integration
    // For now, we'll just show the path
    showToast('info', 'Dateipfad', filePath);
}

/**
 * Get file icon based on extension
 */
function getFileIcon(filename) {
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

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FileManager, fileManager };
}