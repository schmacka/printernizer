/**
 * Library Management UI
 * Handles file library display, search, filtering, and management
 */

class LibraryManager {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 50;
        this.filters = {
            source_type: null,
            file_type: null,
            status: null,
            has_thumbnail: null,
            search: null,
            manufacturer: null,
            printer_model: null,
            show_duplicates: true,
            only_duplicates: false,
            sort_by: 'created_at',
            sort_order: 'desc'
        };
        this.selectedFile = null;
        this.isLoading = false;
        this.allowedExtensions = ['.3mf', '.stl', '.gcode', '.obj', '.ply'];
    }

    /**
     * Initialize library manager
     */
    async initialize() {
        Logger.debug('Initializing Library Manager');
        this.setupEventListeners();
        await this.loadStatistics();
        await this.loadFiles();

        // Setup WebSocket for real-time updates
        if (window.wsManager) {
            window.wsManager.on('library_file_added', () => this.handleFileAdded());
            window.wsManager.on('library_file_updated', () => this.handleFileUpdated());
            window.wsManager.on('library_file_deleted', () => this.handleFileDeleted());
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Search input with debounce
        const searchInput = document.getElementById('librarySearchInput');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.filters.search = e.target.value || null;
                    this.currentPage = 1;
                    this.loadFiles();
                }, 300);
            });
        }

        // Filter dropdowns
        const filterElements = [
            'filterSourceType',
            'filterManufacturer',
            'filterPrinterModel',
            'filterFileType',
            'filterStatus',
            'filterMetadata',
            'sortBy'
        ];

        filterElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.applyFilters());
            }
        });

        // Pagination
        document.getElementById('pageSizeSelect')?.addEventListener('change', (e) => {
            this.pageSize = parseInt(e.target.value);
            this.currentPage = 1;
            this.loadFiles();
        });

        // Modal close
        document.getElementById('closeFileDetailModal')?.addEventListener('click', () => {
            this.closeFileDetailModal();
        });

        // Close modal on outside click
        document.getElementById('fileDetailModal')?.addEventListener('click', (e) => {
            if (e.target.id === 'fileDetailModal') {
                this.closeFileDetailModal();
            }
        });

        // Setup drag-and-drop upload
        this.setupDragAndDrop();
    }

    /**
     * Apply filters from UI
     */
    applyFilters() {
        const sourceType = document.getElementById('filterSourceType')?.value;
        const manufacturer = document.getElementById('filterManufacturer')?.value;
        const printerModel = document.getElementById('filterPrinterModel')?.value;
        const fileType = document.getElementById('filterFileType')?.value;
        const status = document.getElementById('filterStatus')?.value;
        const metadata = document.getElementById('filterMetadata')?.value;
        const sortBy = document.getElementById('sortBy')?.value;

        this.filters.source_type = sourceType !== 'all' ? sourceType : null;
        this.filters.manufacturer = manufacturer !== 'all' ? manufacturer : null;
        this.filters.printer_model = printerModel !== 'all' ? printerModel : null;
        this.filters.file_type = fileType !== 'all' ? fileType : null;
        this.filters.status = status !== 'all' ? status : null;

        if (metadata === 'with_thumbnail') {
            this.filters.has_thumbnail = true;
        } else if (metadata === 'analyzed') {
            this.filters.has_metadata = true;
        } else {
            this.filters.has_thumbnail = null;
            this.filters.has_metadata = null;
        }

        // Parse sort_by (format: "field:order")
        if (sortBy) {
            const [field, order] = sortBy.split(':');
            this.filters.sort_by = field;
            this.filters.sort_order = order;
        }

        this.currentPage = 1;
        this.loadFiles();
    }

    /**
     * Load library statistics
     */
    async loadStatistics() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/library/statistics`);
            if (!response.ok) throw new Error('Failed to load statistics');

            const stats = await response.json();

            // Update stat cards
            document.getElementById('statTotalFiles').textContent = stats.total_files || 0;
            document.getElementById('statTotalSize').textContent = this.formatFileSize(stats.total_size || 0);
            document.getElementById('statWithThumbnails').textContent = stats.files_with_thumbnails || 0;
            document.getElementById('statAnalyzed').textContent = stats.files_analyzed || 0;

        } catch (error) {
            Logger.error('Failed to load statistics:', error);
            this.showError('Fehler beim Laden der Statistiken');
        }
    }

    /**
     * Load library files with current filters
     */
    async loadFiles() {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showLoading();

        try {
            // Build query parameters
            const params = new URLSearchParams({
                page: this.currentPage,
                limit: this.pageSize
            });

            // Add filters
            Object.entries(this.filters).forEach(([key, value]) => {
                if (value !== null && value !== undefined) {
                    params.append(key, value);
                }
            });

            const response = await fetch(`${CONFIG.API_BASE_URL}/library/files?${params}`);
            if (!response.ok) throw new Error('Failed to load files');

            const data = await response.json();

            this.renderFiles(data.files);
            this.renderPagination(data.pagination);

        } catch (error) {
            Logger.error('Failed to load files:', error);
            this.showError('Fehler beim Laden der Dateien');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Render files grid
     */
    renderFiles(files) {
        const grid = document.getElementById('libraryFilesGrid');
        if (!grid) return;

        if (!files || files.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📁</div>
                    <div class="empty-message">Keine Dateien gefunden</div>
                    <div class="empty-hint">Passen Sie die Filter an oder fügen Sie Dateien hinzu</div>
                </div>
            `;
            return;
        }

        grid.innerHTML = files.map(file => this.createFileCard(file)).join('');

        // Add click handlers
        grid.querySelectorAll('.library-file-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Don't open modal if clicking thumbnail on touch device
                if (e.target.closest('.file-card-thumbnail') && 'ontouchstart' in window) {
                    Logger.debug('Touch device - ignoring thumbnail click to allow animation toggle');
                    return;
                }

                const checksum = card.dataset.checksum;
                const file = files.find(f => f.checksum === checksum);
                if (file) this.showFileDetail(file);
            });
        });

        // Setup animated thumbnails for STL/3MF files
        this.setupAnimatedThumbnails();
    }

    /**
     * Create file card HTML
     */
    createFileCard(file) {
        const sourceIcon = this.getSourceIcon(file.sources);
        const statusBadge = this.getStatusBadge(file.status);
        const duplicateBadge = this.getDuplicateBadge(file);
        const thumbnailUrl = file.has_thumbnail ? `${CONFIG.API_BASE_URL}/library/files/${file.checksum}/thumbnail` : null;

        // Check if file supports animated preview (STL or 3MF) and has a thumbnail
        const supportsAnimation = file.has_thumbnail && file.file_type && ['stl', '3mf'].includes(file.file_type.toLowerCase());

        Logger.debug('Creating file card', {
            filename: file.filename,
            fileType: file.file_type,
            supportsAnimation: supportsAnimation,
            hasThumbnail: file.has_thumbnail
        });

        return `
            <div class="library-file-card ${file.is_duplicate ? 'is-duplicate' : ''}" data-checksum="${sanitizeAttribute(file.checksum)}">
                <div class="file-card-thumbnail ${supportsAnimation ? 'supports-animation' : ''}"
                     ${supportsAnimation ? `data-static-url="${CONFIG.API_BASE_URL}/library/files/${file.checksum}/thumbnail" data-animated-url="${CONFIG.API_BASE_URL}/library/files/${file.checksum}/thumbnail/animated"` : ''}>
                    ${thumbnailUrl
                        ? `<img src="${sanitizeUrl(thumbnailUrl)}" alt="${sanitizeAttribute(file.filename)}" loading="lazy" class="thumbnail-image">`
                        : `<div class="thumbnail-placeholder">${this.getFileTypeIcon(file.file_type)}</div>`
                    }
                    ${statusBadge}
                    ${duplicateBadge}
                </div>
                <div class="file-card-info">
                    <div class="file-card-name" title="${sanitizeAttribute(file.filename)}">${escapeHtml(file.filename)}</div>
                    <div class="file-card-meta">
                        ${sourceIcon}
                        <span class="file-size">${this.formatFileSize(file.file_size)}</span>
                        ${file.print_time ? `<span class="print-time">⏱️ ${this.formatDuration(file.print_time)}</span>` : ''}
                    </div>
                    ${this.renderQuickMetadata(file)}
                </div>
            </div>
        `;
    }

    /**
     * Render quick metadata preview
     */
    renderQuickMetadata(file) {
        const metadata = [];

        if (file.layer_height) {
            metadata.push(`📏 ${file.layer_height}mm`);
        }
        if (file.nozzle_temperature) {
            metadata.push(`🌡️ ${file.nozzle_temperature}°C`);
        }
        if (file.filament_used) {
            metadata.push(`🧵 ${Math.round(file.filament_used)}g`);
        }

        if (metadata.length === 0) return '';

        return `<div class="file-card-metadata">${metadata.join(' · ')}</div>`;
    }

    /**
     * Setup animated thumbnails for all STL/3MF files
     */
    setupAnimatedThumbnails() {
        const animatedThumbnails = document.querySelectorAll('.file-card-thumbnail.supports-animation');
        Logger.info(`Setting up ${animatedThumbnails.length} animated thumbnails`);

        animatedThumbnails.forEach(thumbnail => {
            this.setupAnimatedThumbnail(thumbnail);
        });
    }

    /**
     * Setup animated thumbnail on hover for a single thumbnail
     */
    setupAnimatedThumbnail(thumbnailElement) {
        const img = thumbnailElement.querySelector('.thumbnail-image');
        const staticUrl = thumbnailElement.dataset.staticUrl;
        const animatedUrl = thumbnailElement.dataset.animatedUrl;

        Logger.debug('Setting up animated thumbnail', {
            hasImg: !!img,
            hasStaticUrl: !!staticUrl,
            hasAnimatedUrl: !!animatedUrl,
            staticUrl: staticUrl,
            animatedUrl: animatedUrl
        });

        if (!img || !animatedUrl) {
            Logger.warn('Animated thumbnail setup failed - missing requirements', {
                hasImg: !!img,
                hasAnimatedUrl: !!animatedUrl
            });
            return;
        }

        let isAnimatedLoaded = false;
        let isHovering = false;
        let isAnimating = false; // Track animation state for touch devices
        let loadTimeout = null;

        const preloadAnimatedGif = () => {
            if (isAnimatedLoaded) {
                Logger.debug('Animated GIF already loaded');
                return;
            }

            Logger.debug('Preloading animated GIF', { url: animatedUrl });
            const preloadImg = new Image();

            preloadImg.onload = () => {
                isAnimatedLoaded = true;
                Logger.info('Animated GIF loaded successfully', { url: animatedUrl });

                if ((isHovering || isAnimating) && img.src !== animatedUrl) {
                    Logger.debug('Swapping to animated image');
                    img.src = animatedUrl;
                }
            };

            preloadImg.onerror = (error) => {
                Logger.error('Failed to load animated preview', {
                    url: animatedUrl,
                    error: error
                });
                // Clean up state on error
                isAnimating = false;
                thumbnailElement.classList.remove('animating');
            };

            preloadImg.src = animatedUrl;
        };

        // MOUSE EVENTS (Desktop)
        thumbnailElement.addEventListener('mouseenter', () => {
            isHovering = true;
            Logger.debug('Mouse entered thumbnail - preparing animation');

            loadTimeout = setTimeout(() => {
                if (isHovering) {
                    preloadAnimatedGif();

                    if (isAnimatedLoaded && img.src !== animatedUrl) {
                        img.src = animatedUrl;
                    }
                }
            }, 200);
        });

        thumbnailElement.addEventListener('mouseleave', () => {
            isHovering = false;
            Logger.debug('Mouse left thumbnail - restoring static');

            if (loadTimeout) {
                clearTimeout(loadTimeout);
                loadTimeout = null;
            }

            if (img.src !== staticUrl && !isAnimating) {
                Logger.debug('Restoring static image');
                img.src = staticUrl;
            }
        });

        // TOUCH EVENTS (Mobile)
        thumbnailElement.addEventListener('touchstart', (e) => {
            // Prevent this from triggering mouseenter and card click
            e.stopPropagation();

            // Toggle animation state
            isAnimating = !isAnimating;
            Logger.debug('Touch toggle animation', { isAnimating: isAnimating });

            if (isAnimating) {
                // Show animation
                preloadAnimatedGif();
                if (isAnimatedLoaded && img.src !== animatedUrl) {
                    img.src = animatedUrl;
                }
                // Add visual indicator
                thumbnailElement.classList.add('animating');
            } else {
                // Return to static
                if (img.src !== staticUrl) {
                    img.src = staticUrl;
                }
                thumbnailElement.classList.remove('animating');
            }
        }, { passive: true });

        Logger.info('Animated thumbnail setup complete');
    }

    /**
     * Parse sources field (handles both JSON string and array)
     */
    parseSources(sources) {
        if (!sources) return [];
        if (Array.isArray(sources)) return sources;

        try {
            // Parse JSON string
            return JSON.parse(sources);
        } catch (e) {
            Logger.warn('Failed to parse sources:', e);
            return [];
        }
    }

    /**
     * Get source icon with manufacturer info
     */
    getSourceIcon(sources) {
        const sourceArray = this.parseSources(sources);
        if (sourceArray.length === 0) return '❓';

        const sourceTypes = sourceArray.map(s => s.type);

        if (sourceTypes.includes('printer')) {
            // Find printer source to get manufacturer info
            const printerSource = sourceArray.find(s => s.type === 'printer');
            if (printerSource) {
                const manufacturer = printerSource.manufacturer;
                const model = printerSource.printer_model || printerSource.printer_name;

                // Format: "🖨️ Manufacturer Model"
                if (manufacturer === 'bambu_lab') {
                    return `🖨️ Bambu ${model}`;
                } else if (manufacturer === 'prusa_research') {
                    return `🖨️ Prusa ${model}`;
                } else {
                    return `🖨️ ${model || 'Drucker'}`;
                }
            }
            return '🖨️';
        }

        if (sourceTypes.includes('watch_folder')) return '📁';
        if (sourceTypes.includes('upload')) return '⬆️';

        return '📄';
    }

    /**
     * Get duplicate badge
     */
    getDuplicateBadge(file) {
        if (!file.is_duplicate) {
            // Show count on original files if they have duplicates
            if (file.duplicate_count && file.duplicate_count > 0) {
                return `<span class="duplicate-badge has-duplicates" title="${file.duplicate_count} duplicate(s)">🔗 ${file.duplicate_count}</span>`;
            }
            return '';
        }

        return '<span class="duplicate-badge is-duplicate" title="Duplicate file">⚠️ Duplicate</span>';
    }

    /**
     * Get status badge
     */
    getStatusBadge(status) {
        const badges = {
            'available': '<span class="status-badge status-available">Verfügbar</span>',
            'downloaded': '<span class="status-badge status-downloaded">✓</span>',
            'local': '<span class="status-badge status-local">💾</span>',
            'error': '<span class="status-badge status-error">⚠️</span>'
        };

        return badges[status] || '';
    }

    /**
     * Get file type icon
     */
    getFileTypeIcon(fileType) {
        const icons = {
            '3mf': '📦',
            'gcode': '📝',
            'stl': '🔺',
            'obj': '🔷'
        };

        return icons[fileType?.toLowerCase()] || '📄';
    }

    /**
     * Render pagination controls
     */
    renderPagination(pagination) {
        if (!pagination) return;

        // Update info text
        const infoText = document.getElementById('paginationInfo');
        if (infoText) {
            const start = (pagination.current_page - 1) * pagination.page_size + 1;
            const end = Math.min(pagination.current_page * pagination.page_size, pagination.total_items);
            infoText.textContent = `${start}-${end} von ${pagination.total_items}`;
        }

        // Update buttons
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        const pageInfo = document.getElementById('currentPageInfo');

        if (prevBtn) {
            prevBtn.disabled = !pagination.has_previous;
            prevBtn.onclick = () => this.goToPage(pagination.current_page - 1);
        }

        if (nextBtn) {
            nextBtn.disabled = !pagination.has_next;
            nextBtn.onclick = () => this.goToPage(pagination.current_page + 1);
        }

        if (pageInfo) {
            // Generate page number buttons
            const currentPage = pagination.current_page;
            const totalPages = pagination.total_pages;

            // Calculate which pages to show
            const maxPageButtons = 7; // Show max 7 page buttons
            let startPage = Math.max(1, currentPage - Math.floor(maxPageButtons / 2));
            let endPage = Math.min(totalPages, startPage + maxPageButtons - 1);

            // Adjust if we're near the end
            if (endPage - startPage < maxPageButtons - 1) {
                startPage = Math.max(1, endPage - maxPageButtons + 1);
            }

            let pageHTML = '';

            // First page (if not in range)
            if (startPage > 1) {
                pageHTML += `<button class="page-number-btn" onclick="libraryManager.goToPage(1)">1</button>`;
                if (startPage > 2) {
                    pageHTML += `<span class="page-ellipsis">...</span>`;
                }
            }

            // Page number buttons
            for (let i = startPage; i <= endPage; i++) {
                const isActive = i === currentPage;
                pageHTML += `<button class="page-number-btn ${isActive ? 'active' : ''}"
                             onclick="libraryManager.goToPage(${i})">${i}</button>`;
            }

            // Last page (if not in range)
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) {
                    pageHTML += `<span class="page-ellipsis">...</span>`;
                }
                pageHTML += `<button class="page-number-btn" onclick="libraryManager.goToPage(${totalPages})">${totalPages}</button>`;
            }

            pageInfo.innerHTML = pageHTML;
        }
    }

    /**
     * Go to specific page
     */
    goToPage(page) {
        this.currentPage = page;
        this.loadFiles();
    }

    /**
     * Show file detail modal
     */
    async showFileDetail(file) {
        this.selectedFile = file;

        const modal = document.getElementById('fileDetailModal');
        const content = document.getElementById('fileDetailContent');

        if (!modal || !content) return;

        // Show modal with loading state
        content.innerHTML = '<div class="loading">Lade Details...</div>';
        modal.style.display = 'flex';

        try {
            // Fetch full file details
            const response = await fetch(`${CONFIG.API_BASE_URL}/library/files/${file.checksum}`);
            if (!response.ok) throw new Error('Failed to load file details');

            const fullFile = await response.json();

            content.innerHTML = this.renderFileDetail(fullFile);

            // Setup action buttons
            this.setupFileDetailActions(fullFile);

        } catch (error) {
            Logger.error('Failed to load file details:', error);
            content.innerHTML = '<div class="error">Fehler beim Laden der Details</div>';
        }
    }

    /**
     * Render file detail view
     */
    renderFileDetail(file) {
        const thumbnailUrl = file.has_thumbnail ? `${CONFIG.API_BASE_URL}/library/files/${file.checksum}/thumbnail` : null;

        return `
            <div class="file-detail-container">
                <!-- Header -->
                <div class="file-detail-header">
                    <h2>${file.filename}</h2>
                    <div class="file-detail-meta">
                        ${this.getSourceIcon(file.sources)} ${this.getStatusBadge(file.status)}
                        <span class="file-size">${this.formatFileSize(file.file_size)}</span>
                    </div>
                </div>

                <!-- Thumbnail -->
                ${thumbnailUrl ? `
                    <div class="file-detail-thumbnail">
                        <img src="${thumbnailUrl}" alt="${file.filename}">
                    </div>
                ` : ''}

                <!-- Tabs -->
                <div class="file-detail-tabs">
                    <button class="tab-button active" data-tab="overview">Übersicht</button>
                    <button class="tab-button" data-tab="metadata">Metadaten</button>
                    <button class="tab-button" data-tab="sources">Quellen</button>
                </div>

                <!-- Tab Content -->
                <div class="file-detail-tabs-content">
                    <!-- Overview Tab -->
                    <div class="tab-content active" data-tab="overview">
                        ${this.renderOverviewTab(file)}
                    </div>

                    <!-- Metadata Tab -->
                    <div class="tab-content" data-tab="metadata">
                        ${this.renderMetadataTab(file)}
                    </div>

                    <!-- Sources Tab -->
                    <div class="tab-content" data-tab="sources">
                        ${this.renderSourcesTab(file)}
                    </div>
                </div>

                <!-- Actions -->
                <div class="file-detail-actions">
                    <button class="btn btn-primary" id="reprocessFileBtn">
                        🔄 Neu analysieren
                    </button>
                    <button class="btn btn-secondary" id="downloadFileBtn">
                        ⬇️ Herunterladen
                    </button>
                    <button class="btn btn-danger" id="deleteFileBtn">
                        🗑️ Löschen
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render overview tab
     */
    renderOverviewTab(file) {
        const sections = [];

        // Print settings
        if (file.layer_height || file.nozzle_temperature || file.print_time) {
            sections.push(`
                <div class="metadata-section">
                    <h3>Druckeinstellungen</h3>
                    <div class="metadata-grid">
                        ${file.layer_height ? `<div class="metadata-item"><strong>Schichthöhe:</strong> ${file.layer_height}mm</div>` : ''}
                        ${file.nozzle_temperature ? `<div class="metadata-item"><strong>Düsentemperatur:</strong> ${file.nozzle_temperature}°C</div>` : ''}
                        ${file.bed_temperature ? `<div class="metadata-item"><strong>Betttemperatur:</strong> ${file.bed_temperature}°C</div>` : ''}
                        ${file.print_speed ? `<div class="metadata-item"><strong>Druckgeschwindigkeit:</strong> ${file.print_speed}mm/s</div>` : ''}
                        ${file.print_time ? `<div class="metadata-item"><strong>Druckzeit:</strong> ${this.formatDuration(file.print_time)}</div>` : ''}
                        ${file.total_layers ? `<div class="metadata-item"><strong>Schichten:</strong> ${file.total_layers}</div>` : ''}
                    </div>
                </div>
            `);
        }

        // Material requirements
        if (file.filament_used || file.filament_type) {
            sections.push(`
                <div class="metadata-section">
                    <h3>Materialbedarf</h3>
                    <div class="metadata-grid">
                        ${file.filament_used ? `<div class="metadata-item"><strong>Filamentmenge:</strong> ${Math.round(file.filament_used)}g</div>` : ''}
                        ${file.filament_type ? `<div class="metadata-item"><strong>Materialtyp:</strong> ${file.filament_type}</div>` : ''}
                        ${file.estimated_cost ? `<div class="metadata-item"><strong>Geschätzte Kosten:</strong> €${file.estimated_cost.toFixed(2)}</div>` : ''}
                    </div>
                </div>
            `);
        }

        // Model properties
        if (file.model_width || file.model_height || file.model_depth) {
            sections.push(`
                <div class="metadata-section">
                    <h3>Modelleigenschaften</h3>
                    <div class="metadata-grid">
                        ${file.model_width ? `<div class="metadata-item"><strong>Breite:</strong> ${file.model_width.toFixed(1)}mm</div>` : ''}
                        ${file.model_depth ? `<div class="metadata-item"><strong>Tiefe:</strong> ${file.model_depth.toFixed(1)}mm</div>` : ''}
                        ${file.model_height ? `<div class="metadata-item"><strong>Höhe:</strong> ${file.model_height.toFixed(1)}mm</div>` : ''}
                        ${file.object_count ? `<div class="metadata-item"><strong>Objekte:</strong> ${file.object_count}</div>` : ''}
                    </div>
                </div>
            `);
        }

        if (sections.length === 0) {
            return '<div class="empty-state-small">Keine Metadaten verfügbar</div>';
        }

        return sections.join('');
    }

    /**
     * Render metadata tab
     */
    renderMetadataTab(file) {
        if (!file.last_analyzed) {
            return '<div class="empty-state-small">Datei wurde noch nicht analysiert</div>';
        }

        const allMetadata = [];

        // Collect all metadata fields
        const metadataFields = [
            'layer_height', 'first_layer_height', 'nozzle_diameter',
            'wall_count', 'wall_thickness', 'infill_density', 'infill_pattern',
            'support_used', 'nozzle_temperature', 'bed_temperature', 'print_speed',
            'total_layers', 'filament_used', 'filament_type', 'model_width',
            'model_height', 'model_depth', 'object_count', 'slicer_name',
            'slicer_version', 'profile_name', 'estimated_cost'
        ];

        metadataFields.forEach(field => {
            if (file[field] !== null && file[field] !== undefined) {
                allMetadata.push({
                    key: this.formatFieldName(field),
                    value: this.formatFieldValue(field, file[field])
                });
            }
        });

        if (allMetadata.length === 0) {
            return '<div class="empty-state-small">Keine erweiterten Metadaten verfügbar</div>';
        }

        return `
            <div class="metadata-full-list">
                ${allMetadata.map(item => `
                    <div class="metadata-row">
                        <span class="metadata-key">${item.key}:</span>
                        <span class="metadata-value">${item.value}</span>
                    </div>
                `).join('')}
            </div>
            <div class="metadata-info">
                Zuletzt analysiert: ${this.formatDateTime(file.last_analyzed)}
            </div>
        `;
    }

    /**
     * Render sources tab
     */
    renderSourcesTab(file) {
        const sourceArray = this.parseSources(file.sources);

        if (sourceArray.length === 0) {
            return '<div class="empty-state-small">Keine Quelleninformationen verfügbar</div>';
        }

        return `
            <div class="sources-list">
                ${sourceArray.map((source, index) => `
                    <div class="source-item">
                        <div class="source-header">
                            <span class="source-icon">${this.getSourceIcon([source])}</span>
                            <span class="source-type">${this.formatSourceType(source.type)}</span>
                        </div>
                        <div class="source-details">
                            ${source.printer_name ? `<div><strong>Drucker:</strong> ${source.printer_name}</div>` : ''}
                            ${source.folder_path ? `<div><strong>Ordner:</strong> ${source.folder_path}</div>` : ''}
                            ${source.relative_path ? `<div><strong>Pfad:</strong> ${source.relative_path}</div>` : ''}
                            ${source.discovered_at ? `<div><strong>Entdeckt:</strong> ${this.formatDateTime(source.discovered_at)}</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Setup file detail action buttons
     */
    setupFileDetailActions(file) {
        // Reprocess button
        document.getElementById('reprocessFileBtn')?.addEventListener('click', async () => {
            await this.reprocessFile(file.checksum);
        });

        // Download button
        document.getElementById('downloadFileBtn')?.addEventListener('click', () => {
            window.open(`${CONFIG.API_BASE_URL}/library/files/${file.checksum}/download`, '_blank');
        });

        // Delete button
        document.getElementById('deleteFileBtn')?.addEventListener('click', async () => {
            if (confirm('Möchten Sie diese Datei wirklich aus der Bibliothek löschen?')) {
                await this.deleteFile(file.checksum);
            }
        });

        // Tab switching
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;

                // Update buttons
                document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');

                // Update content
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.querySelector(`.tab-content[data-tab="${tab}"]`)?.classList.add('active');
            });
        });
    }

    /**
     * Reprocess file metadata
     */
    async reprocessFile(checksum) {
        try {
            Logger.debug('[reprocessFile] Starting re-analysis', checksum.substring(0, 16));

            // Show loading state on button
            const btn = document.getElementById('reprocessFileBtn');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-small"></span> Analysiere...';
            }

            // Call the reprocess API endpoint
            const response = await fetch(`${CONFIG.API_BASE_URL}/library/files/${checksum}/reprocess`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`Reprocessing failed with status ${response.status}`);
            }

            const result = await response.json();
            Logger.debug('[reprocessFile] Reprocess triggered', result);

            showToast('success', 'Analyse gestartet', 'Datei wird neu analysiert. Dies kann einige Sekunden dauern.');

            // Wait a bit for metadata extraction to complete
            await new Promise(resolve => setTimeout(resolve, 3000));

            // Reload file details to show updated metadata
            Logger.debug('[reprocessFile] Reloading file details');
            await this.showFileDetail({ checksum });

            // Reset button state
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '🔄 Neu analysieren';
            }

            showToast('success', 'Analyse abgeschlossen', 'Metadaten wurden aktualisiert');

        } catch (error) {
            Logger.error('[reprocessFile] Failed to reprocess file:', error);

            // Reset button state
            const btn = document.getElementById('reprocessFileBtn');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '🔄 Neu analysieren';
            }

            showToast('error', 'Fehler', 'Fehler beim Neu-Analysieren der Datei: ' + error.message);
        }
    }

    /**
     * Bulk re-analyze all library files
     */
    async bulkReanalyze() {
        try {
            Logger.debug('[bulkReanalyze] Starting bulk re-analysis');

            // Ask for confirmation
            const confirmed = confirm(
                'Alle 3MF und G-Code Dateien in der Library neu analysieren?\n\n' +
                'Dies kann einige Minuten dauern, je nach Anzahl der Dateien.\n' +
                'Die Analyse läuft im Hintergrund.'
            );

            if (!confirmed) {
                Logger.debug('[bulkReanalyze] User cancelled');
                return;
            }

            // Show loading state on button
            const btn = document.getElementById('bulkReanalyzeBtn');
            const originalHTML = btn ? btn.innerHTML : '';
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-small"></span> Analysiere...';
            }

            showToast('info', 'Analyse gestartet', 'Alle Dateien werden neu analysiert. Dies kann einige Minuten dauern.');

            // Call bulk re-analysis API
            const response = await fetch(`${CONFIG.API_BASE_URL}/library/reanalyze-all`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`Bulk re-analysis failed with status ${response.status}`);
            }

            const result = await response.json();
            Logger.debug('[bulkReanalyze] Result:', result);

            // Reset button
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalHTML;
            }

            // Show result
            showToast(
                'success',
                'Analyse gestartet',
                `${result.files_scheduled} Dateien werden im Hintergrund analysiert.\n` +
                `Dateitypen: ${result.file_types_included.join(', ')}`
            );

            // Show progress info
            showToast(
                'info',
                'Hinweis',
                'Die Analyse läuft im Hintergrund. Aktualisieren Sie die Seite nach einigen Minuten, ' +
                'um die neuen Metadaten zu sehen.'
            );

        } catch (error) {
            Logger.error('[bulkReanalyze] Failed:', error);

            // Reset button
            const btn = document.getElementById('bulkReanalyzeBtn');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<span class="btn-icon">🔬</span> Alle neu analysieren';
            }

            showToast('error', 'Fehler', 'Fehler beim Starten der Bulk-Analyse: ' + error.message);
        }
    }

    /**
     * Delete file from library
     */
    async deleteFile(checksum) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/library/files/${checksum}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Deletion failed');

            this.showSuccess('Datei wurde gelöscht');
            this.closeFileDetailModal();
            await this.loadFiles();
            await this.loadStatistics();

        } catch (error) {
            Logger.error('Failed to delete file:', error);
            this.showError('Fehler beim Löschen der Datei');
        }
    }

    /**
     * Close file detail modal
     */
    closeFileDetailModal() {
        const modal = document.getElementById('fileDetailModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.selectedFile = null;
    }

    /**
     * Handle real-time updates
     */
    handleFileAdded() {
        this.loadStatistics();
        if (this.currentPage === 1) {
            this.loadFiles();
        }
    }

    handleFileUpdated() {
        this.loadFiles();
    }

    handleFileDeleted() {
        this.loadStatistics();
        this.loadFiles();
    }

    /**
     * Show loading state
     */
    showLoading() {
        const grid = document.getElementById('libraryFilesGrid');
        if (grid) {
            grid.innerHTML = '<div class="loading-placeholder">Lädt Dateien...</div>';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        Logger.error(message);
        // Could integrate with notification system
        alert(message);
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        Logger.debug(message);
        // Could integrate with notification system
        alert(message);
    }

    /**
     * Format utilities
     */
    formatFileSize(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    formatDuration(seconds) {
        if (!seconds) return '0s';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);

        if (h > 0) return `${h}h ${m}m`;
        if (m > 0) return `${m}m ${s}s`;
        return `${s}s`;
    }

    formatDateTime(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleString('de-DE');
    }

    formatFieldName(field) {
        const names = {
            'layer_height': 'Schichthöhe',
            'first_layer_height': 'Erste Schichthöhe',
            'nozzle_diameter': 'Düsendurchmesser',
            'wall_count': 'Wandanzahl',
            'wall_thickness': 'Wanddicke',
            'infill_density': 'Fülldichte',
            'infill_pattern': 'Füllmuster',
            'support_used': 'Stützen verwendet',
            'nozzle_temperature': 'Düsentemperatur',
            'bed_temperature': 'Betttemperatur',
            'print_speed': 'Druckgeschwindigkeit',
            'total_layers': 'Gesamtschichten',
            'filament_used': 'Filament verwendet',
            'filament_type': 'Filamenttyp',
            'model_width': 'Modellbreite',
            'model_height': 'Modellhöhe',
            'model_depth': 'Modelltiefe',
            'object_count': 'Objektanzahl',
            'slicer_name': 'Slicer',
            'slicer_version': 'Slicer-Version',
            'profile_name': 'Profilname',
            'estimated_cost': 'Geschätzte Kosten'
        };
        return names[field] || field;
    }

    formatFieldValue(field, value) {
        if (value === null || value === undefined) return '-';

        if (field.includes('temperature')) return `${value}°C`;
        if (field.includes('speed')) return `${value}mm/s`;
        if (field.includes('height') || field.includes('width') || field.includes('depth') || field.includes('thickness') || field.includes('diameter')) {
            return `${value}mm`;
        }
        if (field.includes('density')) return `${value}%`;
        if (field === 'filament_used') return `${Math.round(value)}g`;
        if (field === 'estimated_cost') return `€${value.toFixed(2)}`;
        if (field === 'support_used') return value ? 'Ja' : 'Nein';

        return value;
    }

    formatSourceType(type) {
        const types = {
            'printer': 'Drucker',
            'watch_folder': 'Überwachter Ordner',
            'upload': 'Upload'
        };
        return types[type] || type;
    }

    /**
     * Setup drag-and-drop upload functionality
     */
    setupDragAndDrop() {
        const libraryGrid = document.getElementById('libraryFilesGrid');
        if (!libraryGrid) {
            Logger.warn('Library grid not found, drag-and-drop disabled');
            return;
        }

        // Allowed file extensions
        this.allowedExtensions = ['.3mf', '.stl', '.gcode', '.obj', '.ply'];

        // Counter to track nested drag events
        let dragCounter = 0;

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            libraryGrid.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        // Highlight drop zone when dragging over
        libraryGrid.addEventListener('dragenter', (e) => {
            dragCounter++;
            libraryGrid.classList.add('drag-over');
        });

        libraryGrid.addEventListener('dragleave', (e) => {
            dragCounter--;
            // Only remove highlight if we've left all nested elements
            if (dragCounter === 0) {
                libraryGrid.classList.remove('drag-over');
            }
        });

        // Handle file drop
        libraryGrid.addEventListener('drop', async (e) => {
            dragCounter = 0;
            libraryGrid.classList.remove('drag-over');

            const files = Array.from(e.dataTransfer.files);
            if (files.length > 0) {
                await this.handleFileDrop(files);
            }
        });

        Logger.debug('Drag-and-drop upload enabled for library grid');
    }

    /**
     * Handle dropped files
     */
    async handleFileDrop(files) {
        Logger.debug('Files dropped:', files.length);

        // Validate files
        const validFiles = [];
        const invalidFiles = [];

        files.forEach(file => {
            const ext = this.getFileExtension(file.name);
            if (this.allowedExtensions.includes(ext)) {
                validFiles.push(file);
            } else {
                invalidFiles.push({
                    name: file.name,
                    error: `Invalid file type: ${ext}`
                });
            }
        });

        // Show errors for invalid files
        if (invalidFiles.length > 0) {
            const errorMsg = `Invalid file types:\n${invalidFiles.map(f => `- ${f.name}`).join('\n')}\n\nSupported: ${this.allowedExtensions.join(', ')}`;
            this.showToast(errorMsg, 'error');
        }

        // Upload valid files
        if (validFiles.length > 0) {
            await this.uploadFiles(validFiles);
        } else if (invalidFiles.length === 0 && files.length === 0) {
            this.showToast('No files selected', 'info');
        }
    }

    /**
     * Get file extension (lowercase with dot)
     */
    getFileExtension(filename) {
        const lastDot = filename.lastIndexOf('.');
        if (lastDot === -1) return '';
        return filename.substring(lastDot).toLowerCase();
    }

    /**
     * Upload files to the server
     */
    async uploadFiles(files) {
        Logger.debug('Uploading files:', files.length);

        // Show upload overlay
        this.showUploadOverlay(files);

        // Create FormData
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        formData.append('is_business', 'false');

        try {
            // Upload files - use direct fetch since FormData requires custom handling
            // Note: Cannot use api.post() because it sets Content-Type to application/json
            // FormData needs browser to set multipart/form-data with boundary automatically
            const response = await fetch(`${api.baseURL}/files/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail?.message || 'Upload failed');
            }

            const result = await response.json();
            Logger.debug('Upload result:', result);

            // Show success message
            if (result.success_count > 0) {
                this.showToast(
                    `Successfully uploaded ${result.success_count} file(s)`,
                    'success'
                );
            }

            // Show errors for failed uploads
            if (result.failed_files && result.failed_files.length > 0) {
                result.failed_files.forEach(failed => {
                    this.showToast(`Failed: ${failed.filename} - ${failed.error}`, 'error');
                });
            }

            // Refresh library
            await this.loadFiles();
            await this.loadStatistics();

        } catch (error) {
            Logger.error('Upload error:', error);
            this.showToast(`Upload failed: ${error.message}`, 'error');
        } finally {
            this.hideUploadOverlay();
        }
    }

    /**
     * Show upload progress overlay
     */
    showUploadOverlay(files) {
        let overlay = document.getElementById('uploadOverlay');
        if (!overlay) {
            // Create overlay if it doesn't exist
            overlay = document.createElement('div');
            overlay.id = 'uploadOverlay';
            overlay.className = 'upload-overlay';
            overlay.innerHTML = `
                <div class="upload-content">
                    <div class="upload-header">
                        <h3>⬆️ Uploading Files</h3>
                    </div>
                    <div class="upload-files" id="uploadFilesList">
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
        }

        // Add file list
        const filesList = document.getElementById('uploadFilesList');
        filesList.innerHTML = files.map(file => `
            <div class="upload-file-item">
                <span class="upload-file-name">${file.name}</span>
                <span class="upload-file-size">${this.formatFileSize(file.size)}</span>
                <span class="upload-spinner">⏳</span>
            </div>
        `).join('');

        overlay.classList.add('visible');
    }

    /**
     * Hide upload progress overlay
     */
    hideUploadOverlay() {
        const overlay = document.getElementById('uploadOverlay');
        if (overlay) {
            overlay.classList.remove('visible');
            setTimeout(() => {
                overlay.remove();
            }, 300);
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Check if notification manager exists
        if (window.notificationManager) {
            window.notificationManager.showToast(message, type);
            return;
        }

        // Fallback to simple alert
        Logger.debug(`[${type.toUpperCase()}] ${message}`);

        // Create simple toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 10000;
            max-width: 400px;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
}

// Initialize library manager
const libraryManager = new LibraryManager();

// Export init function for page manager
libraryManager.init = function() {
    Logger.debug('Library page initialized');
    this.initialize();
};

// Global function to trigger file upload picker
// Explicitly attach to window object to ensure it's available globally
window.triggerFileUpload = function() {
    Logger.debug('triggerFileUpload called');
    const fileInput = document.getElementById('libraryFileInput');
    if (fileInput) {
        Logger.debug('File input found, triggering click');
        // iOS Safari requires the click to be triggered directly from user interaction
        // Use try-catch to handle any security restrictions
        try {
            fileInput.click();
        } catch (error) {
            Logger.error('Error triggering file input click:', error);
            alert('Unable to open file picker. Please try again.');
        }
    } else {
        Logger.error('File input not found');
        alert('File input not found. Please refresh the page.');
    }
};

// Global function to handle manual file upload
// Explicitly attach to window object to ensure it's available globally
window.handleManualFileUpload = async function(event) {
    Logger.debug('handleManualFileUpload called', event);
    const files = Array.from(event.target.files);
    Logger.debug('Files selected:', files.length, files.map(f => ({ name: f.name, type: f.type, size: f.size })));

    if (files.length > 0) {
        Logger.debug('Processing', files.length, 'file(s) for upload');
        await libraryManager.handleFileDrop(files);

        // Reset the file input so the same files can be selected again if needed
        event.target.value = '';
    } else {
        Logger.warn('No files selected from file input');
    }
};

// Global function to refresh the library
// Explicitly attach to window object to ensure it's available globally
window.refreshLibrary = async function() {
    Logger.debug('Refreshing library...');
    await libraryManager.loadFiles();
};

// Global function to clear library search
// Explicitly attach to window object to ensure it's available globally
window.clearLibrarySearch = function() {
    const searchInput = document.getElementById('librarySearchInput');
    const clearButton = document.querySelector('.search-clear-btn');

    if (searchInput) {
        searchInput.value = '';
    }

    if (clearButton) {
        clearButton.style.display = 'none';
    }

    // Clear the search filter and reload
    libraryManager.filters.search = null;
    libraryManager.currentPage = 1;
    libraryManager.loadFiles();
};
