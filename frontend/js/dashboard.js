/**
 * Printernizer Dashboard Page
 * Handles dashboard functionality including overview cards, printer grid, and recent jobs
 */

class Dashboard {
    constructor() {
        this.refreshInterval = null;
        this.printers = new Map();
        this.statisticsCache = null;
        this.lastRefresh = null;
        this.carouselInterval = null;
        this.currentCarouselIndex = 0;
        this.carouselFiles = [];
    }

    /**
     * Initialize dashboard page
     */
    init() {
        Logger.debug('Initializing dashboard');

        // Load initial data (pass true to indicate initial load)
        this.loadDashboard(true);

        // Set up refresh interval
        this.startAutoRefresh();

        // Listen for WebSocket updates
        this.setupWebSocketListeners();
    }

    /**
     * Cleanup dashboard resources
     */
    cleanup() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        if (this.carouselInterval) {
            clearInterval(this.carouselInterval);
            this.carouselInterval = null;
        }
    }

    /**
     * Load all dashboard data
     */
    async loadDashboard(isInitialLoad = false) {
        try {
            // Check for startup discovered printers only on initial load, not on refreshes
            if (isInitialLoad) {
                await this.checkStartupDiscoveredPrinters();
            }

            // Load overview statistics
            await this.loadOverviewStatistics();

            // Load printers
            await this.loadPrinters();

            // Load recent jobs
            await this.loadRecentJobs();

            // Load recent printed files
            await this.loadRecentPrintedFiles();

            this.lastRefresh = new Date();
        } catch (error) {
            Logger.error('Failed to load dashboard:', error);
            this.showDashboardError(error);
        }
    }

    /**
     * Check for printers discovered during startup
     */
    async checkStartupDiscoveredPrinters() {
        try {
            const result = await api.getStartupDiscoveredPrinters();

            if (result && result.new_count > 0) {
                // Create a unique key for this discovery session
                const discoveredIds = result.discovered
                    .filter(p => !p.already_added)
                    .map(p => p.ip)
                    .sort()
                    .join(',');

                const sessionKey = `discovered_printers_notified_${discoveredIds}`;

                // Check if we've already notified about these specific printers in this session
                const alreadyNotified = sessionStorage.getItem(sessionKey);

                if (!alreadyNotified) {
                    // Mark as notified before showing notification
                    sessionStorage.setItem(sessionKey, 'true');

                    // Show notification with discovered printers
                    const message = result.new_count === 1
                        ? `1 neuer Drucker gefunden! Klicken Sie hier, um ihn anzuzeigen.`
                        : `${result.new_count} neue Drucker gefunden! Klicken Sie hier, um sie anzuzeigen.`;

                    // Show persistent notification with action
                    showNotification(message, 'success', 10000, () => {
                        // Navigate to printers page and trigger discovery display
                        if (typeof app !== 'undefined' && app.showPage) {
                            app.showPage('printers');
                            // Scroll to discovered section
                            setTimeout(() => {
                                const section = document.getElementById('discoveredPrintersSection');
                                if (section) {
                                    section.style.display = 'block';
                                    section.scrollIntoView({ behavior: 'smooth' });

                                    // Populate discovered printers list (only show new printers, not already added)
                                    const list = document.getElementById('discoveredPrintersList');
                                    if (list && typeof createDiscoveredPrinterCard === 'function') {
                                        list.innerHTML = '';
                                        result.discovered
                                            .filter(printer => !printer.already_added)
                                            .forEach(printer => {
                                                const card = createDiscoveredPrinterCard(printer);
                                                list.appendChild(card);
                                            });
                                    }
                                }
                            }, 100);
                        }
                    });

                    // Also show banner on dashboard
                    this.showDiscoveredPrintersBanner(result.new_count);
                }
            }
        } catch (error) {
            Logger.error('Failed to check startup discovered printers:', error);
            // Silently fail - don't disrupt dashboard loading
        }
    }

    /**
     * Show banner for discovered printers on dashboard
     */
    showDiscoveredPrintersBanner(count) {
        const dashboardContainer = document.getElementById('dashboard');
        if (!dashboardContainer) return;

        // Create banner element
        const banner = document.createElement('div');
        banner.className = 'discovered-printers-banner';
        banner.innerHTML = `
            <div class="banner-content">
                <div class="banner-icon">🔍</div>
                <div class="banner-text">
                    <h4>${count === 1 ? '1 neuer Drucker gefunden' : `${count} neue Drucker gefunden`}</h4>
                    <p>Neue Drucker wurden beim Start automatisch erkannt.</p>
                </div>
                <button class="btn btn-primary" onclick="app.showPage('printers')">
                    Zur Drucker-Seite
                </button>
                <button class="btn-icon-only" onclick="dashboard.dismissDiscoveredPrintersBanner()" title="Schließen">
                    ✕
                </button>
            </div>
        `;

        // Insert banner at the top of dashboard
        const firstChild = dashboardContainer.firstElementChild;
        if (firstChild) {
            dashboardContainer.insertBefore(banner, firstChild);
        } else {
            dashboardContainer.appendChild(banner);
        }
    }

    /**
     * Dismiss discovered printers banner and clear backend state
     */
    async dismissDiscoveredPrintersBanner() {
        // Remove banner from DOM
        const banner = document.querySelector('.discovered-printers-banner');
        if (banner) {
            banner.remove();
        }

        // Clear discovered printers from backend
        try {
            await api.clearStartupDiscoveredPrinters();
        } catch (error) {
            Logger.error('Failed to clear discovered printers:', error);
        }
    }

    /**
     * Load overview statistics cards
     */
    async loadOverviewStatistics() {
        try {
            // Show loading state
            this.setOverviewCardsLoading(true);
            
            // Load statistics from API
            const [stats, printers] = await Promise.all([
                api.getStatisticsOverview('day'),
                api.getPrinters({ active: true })
            ]);

            // Update overview cards
            this.updateOverviewCards(stats, printers);
            
            this.statisticsCache = stats;
        } catch (error) {
            Logger.error('Failed to load overview statistics:', error);
            this.showOverviewCardsError();
        }
    }

    /**
     * Update overview cards with statistics
     */
    updateOverviewCards(stats, printers) {
        // Printer count card
        const printerCountEl = document.getElementById('printerCount');
        const printerDetailEl = document.getElementById('printerDetail');
        
        if (printerCountEl && printerDetailEl) {
            // Handle printers - API returns {printers: [], total_count: N} or array directly
            const printersData = printers?.printers || printers;
            const printersArray = Array.isArray(printersData) ? printersData : [];
            const onlineCount = printersArray.filter(p => p.status === 'online').length || 0;
            const totalCount = printersArray.length || 0;
            
            printerCountEl.textContent = `${onlineCount}/${totalCount}`;
            printerDetailEl.textContent = `${totalCount} Drucker konfiguriert`;
        }

        // Active jobs card
        const activeJobsEl = document.getElementById('activeJobsCount');
        const jobsDetailEl = document.getElementById('jobsDetail');
        
        if (activeJobsEl && jobsDetailEl) {
            const activeJobs = stats.jobs?.total_jobs || 0;
            // Use extracted printersArray from above
            const printersData = printers?.printers || printers;
            const printersArr = Array.isArray(printersData) ? printersData : [];
            const printingJobs = printersArr.filter(p => p.current_job?.status === 'printing').length;

            activeJobsEl.textContent = printingJobs;
            jobsDetailEl.textContent = `${activeJobs} Aufträge heute`;
        }

        // Files card
        const filesCountEl = document.getElementById('filesCount');
        const filesDetailEl = document.getElementById('filesDetail');
        
        if (filesCountEl && filesDetailEl) {
            const filesCount = stats.files?.total_files || 0;
            const downloadedCount = stats.files?.downloaded_files || 0;
            
            filesCountEl.textContent = filesCount;
            filesDetailEl.textContent = `${downloadedCount} heruntergeladen`;
        }

        // Today's jobs card
        const todayJobsEl = document.getElementById('todayJobsCount');
        const todayDetailEl = document.getElementById('todayDetail');
        
        if (todayJobsEl && todayDetailEl) {
            const completedToday = stats.jobs?.completed_jobs || 0;
            const successRate = stats.jobs?.success_rate || 0;

            todayJobsEl.textContent = completedToday;
            // API returns success_rate as 0-100, no need to multiply
            todayDetailEl.textContent = `${formatPercentage(successRate)} Erfolgsrate`;
        }
    }

    /**
     * Set loading state for overview cards
     */
    setOverviewCardsLoading(loading) {
        const loadingText = loading ? 'Lade...' : '-';
        
        const elements = [
            'printerCount', 'activeJobsCount', 'filesCount', 'todayJobsCount'
        ];
        
        elements.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = loadingText;
            }
        });

        const detailElements = [
            'printerDetail', 'jobsDetail', 'filesDetail', 'todayDetail'
        ];
        
        detailElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = loading ? 'Lade...' : '-';
            }
        });
    }

    /**
     * Show error state for overview cards
     */
    showOverviewCardsError() {
        const elements = [
            'printerCount', 'activeJobsCount', 'filesCount', 'todayJobsCount'
        ];
        
        elements.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = '⚠️';
            }
        });

        const detailElements = [
            'printerDetail', 'jobsDetail', 'filesDetail', 'todayDetail'
        ];
        
        detailElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = 'Ladefehler';
            }
        });
    }

    /**
     * Load and display printers
     */
    async loadPrinters() {
        try {
            const printerGrid = document.getElementById('printerGrid');
            if (!printerGrid) return;
            
            // Show loading state
            setLoadingState(printerGrid, true);
            
            // Load printers from API
            const response = await api.getPrinters({ active: true });
            
            // Clear existing printers
            this.printers.clear();
            
            // API returns {printers: [], total_count: N, pagination: {...}}
            const printers = response?.printers || response;
            const printersArray = Array.isArray(printers) ? printers : (Array.isArray(response) ? response : []);
            
            if (printersArray.length > 0) {
                // Create printer cards
                printerGrid.innerHTML = '';
                
                printersArray.forEach(printer => {
                    const printerCard = new PrinterCard(printer);
                    const cardElement = printerCard.render();
                    printerGrid.appendChild(cardElement);
                    
                    // Store printer card for updates
                    this.printers.set(printer.id, printerCard);
                });
            } else {
                // Show empty state
                printerGrid.innerHTML = this.renderEmptyPrintersState();
            }
        } catch (error) {
            Logger.error('Failed to load printers:', error);
            const printerGrid = document.getElementById('printerGrid');
            if (printerGrid) {
                printerGrid.innerHTML = this.renderPrintersError(error);
            }
        }
    }

    /**
     * Render empty printers state
     */
    renderEmptyPrintersState() {
        return `
            <div class="empty-state">
                <div class="empty-state-icon">🖨️</div>
                <h3>Keine Drucker konfiguriert</h3>
                <p>Fügen Sie Ihren ersten Drucker hinzu, um mit dem Drucken zu beginnen.</p>
                <button class="btn btn-primary" onclick="showAddPrinter()">
                    <span class="btn-icon">➕</span>
                    Drucker hinzufügen
                </button>
            </div>
        `;
    }

    /**
     * Render printers error state
     */
    renderPrintersError(error) {
        const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Laden der Drucker';
        
        return `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Ladefehler</h3>
                <p>${escapeHtml(message)}</p>
                <button class="btn btn-primary" onclick="dashboard.loadPrinters()">
                    <span class="btn-icon">🔄</span>
                    Erneut versuchen
                </button>
            </div>
        `;
    }

    /**
     * Load and display recent jobs
     */
    async loadRecentJobs() {
        try {
            const recentJobsContainer = document.getElementById('recentJobs');
            if (!recentJobsContainer) return;
            
            // Show loading state
            setLoadingState(recentJobsContainer, true);
            
            // Load recent jobs from API
            const response = await api.getJobs({
                limit: 5,
                order_by: 'created_at',
                order_dir: 'desc'
            });
            
            if (response.jobs && response.jobs.length > 0) {
                // Create job preview cards
                recentJobsContainer.innerHTML = '';
                
                response.jobs.forEach(job => {
                    const jobPreview = this.createJobPreviewCard(job);
                    recentJobsContainer.appendChild(jobPreview);
                });
            } else {
                // Show empty state
                recentJobsContainer.innerHTML = this.renderEmptyJobsState();
            }
        } catch (error) {
            Logger.error('Failed to load recent jobs:', error);
            const recentJobsContainer = document.getElementById('recentJobs');
            if (recentJobsContainer) {
                recentJobsContainer.innerHTML = this.renderJobsError(error);
            }
        }
    }

    /**
     * Create job preview card element
     */
    createJobPreviewCard(job) {
        const card = document.createElement('div');
        card.className = 'job-preview-card';
        card.setAttribute('data-job-id', sanitizeAttribute(job.id));

        const status = getStatusConfig('job', job.status);

        card.innerHTML = `
            ${this.renderJobPreviewThumbnail(job)}
            <div class="job-preview-info">
                <div class="job-preview-name">
                    <div class="job-name">${escapeHtml(job.job_name)}</div>
                    <div class="job-preview-printer">${escapeHtml(job.printer_name)}</div>
                </div>

                <div class="job-preview-status">
                    <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
                </div>

                <div class="job-preview-time">
                    ${job.start_time ? formatDateTime(job.start_time) : 'Nicht gestartet'}
                </div>

                <div class="job-preview-progress">
                    ${this.renderJobPreviewProgress(job)}
                </div>
            </div>
        `;

        // Add click handler to show job details
        card.addEventListener('click', () => {
            showJobDetails(job.id);
        });

        return card;
    }

    /**
     * Render job preview thumbnail
     */
    renderJobPreviewThumbnail(job) {
        // If job has a file_id or files array with thumbnails, show thumbnail
        if (job.file_id || (job.files && job.files.length > 0)) {
            const fileId = job.file_id || (job.files[0] && job.files[0].id);
            const hasThumb = job.has_thumbnail || (job.files && job.files[0] && job.files[0].has_thumbnail);

            if (fileId && hasThumb) {
                return `
                    <div class="job-preview-thumbnail">
                        <img src="${CONFIG.API_BASE_URL}/files/${sanitizeAttribute(fileId)}/thumbnail"
                             alt="Print Preview"
                             class="job-thumbnail-image"
                             onerror="this.src='assets/placeholder-thumbnail.svg'; this.onerror=null;"
                             loading="lazy">
                    </div>
                `;
            }
        }

        // Show placeholder for jobs without thumbnails
        return `
            <div class="job-preview-thumbnail fallback">
                <img src="assets/placeholder-thumbnail.svg"
                     alt="Keine Vorschau verfügbar"
                     class="job-thumbnail-image placeholder-image">
            </div>
        `;
    }

    /**
     * Get file type icon for job
     */
    getJobFileTypeIcon(job) {
        const fileName = job.job_name || job.filename || '';
        const extension = fileName.split('.').pop().toLowerCase();

        const iconMap = {
            'gcode': '🔧',
            '3mf': '📦',
            'stl': '🏗️',
            'obj': '📐',
            'ply': '🧊'
        };

        return iconMap[extension] || '📄';
    }

    /**
     * Render job preview progress
     */
    renderJobPreviewProgress(job) {
        if (job.status === 'printing' && job.progress !== undefined) {
            return `
                <div class="progress">
                    <div class="progress-bar" style="width: ${job.progress}%"></div>
                </div>
                <div class="progress-text">${formatPercentage(job.progress)}</div>
            `;
        }
        
        if (job.status === 'completed' && job.actual_duration) {
            return `
                <div class="completion-time">
                    <div class="time-label">Dauer:</div>
                    <div class="time-value">${formatDuration(job.actual_duration)}</div>
                </div>
            `;
        }
        
        if (job.estimated_duration) {
            return `
                <div class="estimated-time">
                    <div class="time-label">Geschätzt:</div>
                    <div class="time-value">${formatDuration(job.estimated_duration)}</div>
                </div>
            `;
        }
        
        return '';
    }

    /**
     * Render empty jobs state
     */
    renderEmptyJobsState() {
        return `
            <div class="empty-state">
                <div class="empty-state-icon">⚙️</div>
                <h3>Keine aktuellen Aufträge</h3>
                <p>Hier werden Ihre neuesten Druckaufträge angezeigt.</p>
            </div>
        `;
    }

    /**
     * Load and display recent printed files
     */
    async loadRecentPrintedFiles() {
        try {
            const printedFilesContainer = document.getElementById('recentPrintedFiles');
            if (!printedFilesContainer) return;

            // Show loading state
            setLoadingState(printedFilesContainer, true);

            // Load recent files from API - changed to 8 for carousel
            const response = await api.getFiles({
                status: 'downloaded',
                has_thumbnail: true,
                limit: 8,
                order_by: 'downloaded_at',
                order_dir: 'desc'
            });

            if (response.files && response.files.length > 0) {
                // Store files for carousel
                this.carouselFiles = response.files;
                this.currentCarouselIndex = 0;

                // Create carousel container
                printedFilesContainer.innerHTML = '';
                const carouselContainer = document.createElement('div');
                carouselContainer.className = 'printed-files-carousel';
                carouselContainer.innerHTML = `
                    <button class="carousel-nav carousel-prev" aria-label="Previous">
                        <span>‹</span>
                    </button>
                    <div class="carousel-track-container">
                        <div class="carousel-track" id="printedFilesCarouselTrack"></div>
                    </div>
                    <button class="carousel-nav carousel-next" aria-label="Next">
                        <span>›</span>
                    </button>
                    <div class="carousel-indicators" id="carouselIndicators"></div>
                `;

                printedFilesContainer.appendChild(carouselContainer);

                // Populate carousel track
                const carouselTrack = document.getElementById('printedFilesCarouselTrack');
                this.carouselFiles.forEach(file => {
                    const filePreview = this.createPrintedFilePreviewCard(file);
                    carouselTrack.appendChild(filePreview);
                });

                // Create indicators
                const indicators = document.getElementById('carouselIndicators');
                this.carouselFiles.forEach((_, index) => {
                    const indicator = document.createElement('button');
                    indicator.className = `carousel-indicator ${index === 0 ? 'active' : ''}`;
                    indicator.setAttribute('data-index', index);
                    indicator.setAttribute('aria-label', `Go to slide ${index + 1}`);
                    indicator.addEventListener('click', () => this.goToSlide(index));
                    indicators.appendChild(indicator);
                });

                // Add navigation event listeners
                const prevBtn = printedFilesContainer.querySelector('.carousel-prev');
                const nextBtn = printedFilesContainer.querySelector('.carousel-next');
                prevBtn.addEventListener('click', () => this.previousSlide());
                nextBtn.addEventListener('click', () => this.nextSlide());

                // Start auto-rotation
                this.startCarouselRotation();

                // Update carousel display
                this.updateCarouselDisplay();
            } else {
                // Show empty state
                printedFilesContainer.innerHTML = this.renderEmptyPrintedFilesState();
            }
        } catch (error) {
            Logger.error('Failed to load recent printed files:', error);
            const printedFilesContainer = document.getElementById('recentPrintedFiles');
            if (printedFilesContainer) {
                printedFilesContainer.innerHTML = this.renderPrintedFilesError(error);
            }
        }
    }

    /**
     * Create printed file preview card element
     */
    createPrintedFilePreviewCard(file) {
        const card = document.createElement('div');
        card.className = 'printed-file-preview-card';
        card.setAttribute('data-file-id', sanitizeAttribute(file.id));

        const fileTypeIcon = this.getFileTypeIcon(file.filename);

        card.innerHTML = `
            <div class="printed-file-thumbnail">
                ${file.has_thumbnail ?
                    `<img src="${CONFIG.API_BASE_URL}/files/${sanitizeAttribute(file.id)}/thumbnail"
                         alt="File Preview"
                         class="printed-file-thumbnail-image"
                         onerror="this.src='assets/placeholder-thumbnail.svg'; this.onerror=null;"
                         loading="lazy">` :
                    `<img src="assets/placeholder-thumbnail.svg"
                         alt="Keine Vorschau verfügbar"
                         class="printed-file-thumbnail-image placeholder-image">`
                }
            </div>
            <div class="printed-file-info">
                <div class="printed-file-name" title="${escapeHtml(file.filename)}">${escapeHtml(this.truncateFileName(file.filename, 20))}</div>
                <div class="printed-file-metadata">
                    ${file.file_size ? `<span class="file-size">${formatBytes(file.file_size)}</span>` : ''}
                    ${file.downloaded_at ? `<span class="download-date">${formatDate(file.downloaded_at)}</span>` : ''}
                </div>
                ${this.renderPrintedFileMetadata(file)}
            </div>
        `;

        // Add click handler to open file preview or show details
        card.addEventListener('click', () => {
            this.showPrintedFileDetails(file);
        });

        return card;
    }

    /**
     * Render printed file metadata
     */
    renderPrintedFileMetadata(file) {
        if (!file.metadata) return '';

        const metadata = file.metadata;
        const metadataItems = [];

        // Show key print information
        if (metadata.estimated_time || metadata.estimated_print_time) {
            const timeSeconds = metadata.estimated_time || metadata.estimated_print_time;
            const timeText = typeof timeSeconds === 'number' ? formatDuration(timeSeconds) : timeSeconds;
            metadataItems.push(`⏱️ ${timeText}`);
        }

        if (metadata.total_filament_used) {
            metadataItems.push(`🧵 ${metadata.total_filament_used.toFixed(1)}g`);
        }

        if (metadataItems.length === 0) return '';

        return `
            <div class="printed-file-metadata-items">
                ${metadataItems.slice(0, 2).map(item => `<span class="metadata-item">${item}</span>`).join('')}
            </div>
        `;
    }

    /**
     * Show printed file details
     */
    showPrintedFileDetails(file) {
        // For now, redirect to files page - later we can implement a modal
        showPage('files');
        // Could add file highlight or auto-filter here
    }

    /**
     * Start carousel auto-rotation
     */
    startCarouselRotation() {
        // Clear any existing interval
        if (this.carouselInterval) {
            clearInterval(this.carouselInterval);
        }

        // Auto-rotate every 5 seconds
        this.carouselInterval = setInterval(() => {
            this.nextSlide();
        }, 5000);
    }

    /**
     * Stop carousel auto-rotation
     */
    stopCarouselRotation() {
        if (this.carouselInterval) {
            clearInterval(this.carouselInterval);
            this.carouselInterval = null;
        }
    }

    /**
     * Go to next slide
     */
    nextSlide() {
        if (this.carouselFiles.length === 0) return;
        this.currentCarouselIndex = (this.currentCarouselIndex + 1) % this.carouselFiles.length;
        this.updateCarouselDisplay();
    }

    /**
     * Go to previous slide
     */
    previousSlide() {
        if (this.carouselFiles.length === 0) return;
        this.currentCarouselIndex = (this.currentCarouselIndex - 1 + this.carouselFiles.length) % this.carouselFiles.length;
        this.updateCarouselDisplay();
    }

    /**
     * Go to specific slide
     */
    goToSlide(index) {
        if (index < 0 || index >= this.carouselFiles.length) return;
        this.currentCarouselIndex = index;
        this.updateCarouselDisplay();
        // Reset auto-rotation timer
        this.startCarouselRotation();
    }

    /**
     * Update carousel display to show current slide
     */
    updateCarouselDisplay() {
        const track = document.getElementById('printedFilesCarouselTrack');
        if (!track) return;

        // Move track to show current slide
        const slideWidth = 100; // percentage
        track.style.transform = `translateX(-${this.currentCarouselIndex * slideWidth}%)`;

        // Update indicators - scope to the carousel container
        const carouselContainer = track.closest('.printed-files-carousel');
        if (!carouselContainer) return;
        
        const indicators = carouselContainer.querySelectorAll('.carousel-indicator');
        indicators.forEach((indicator, index) => {
            if (index === this.currentCarouselIndex) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
    }

    /**
     * Get file type icon
     */
    getFileTypeIcon(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        const iconMap = {
            'gcode': '🔧',
            '3mf': '📦',
            'stl': '🏗️',
            'obj': '📐',
            'ply': '🧊'
        };
        return iconMap[extension] || '📄';
    }

    /**
     * Truncate filename for display
     */
    truncateFileName(filename, maxLength) {
        if (filename.length <= maxLength) return filename;

        const extension = filename.split('.').pop();
        const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.'));
        const maxNameLength = maxLength - extension.length - 4; // -4 for "..." and "."

        if (nameWithoutExt.length > maxNameLength) {
            return nameWithoutExt.substring(0, maxNameLength) + '...' + '.' + extension;
        }

        return filename;
    }

    /**
     * Render empty printed files state
     */
    renderEmptyPrintedFilesState() {
        return `
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <h3>Keine gedruckten Dateien</h3>
                <p>Hier werden Ihre kürzlich gedruckten Dateien mit Vorschaubildern angezeigt.</p>
            </div>
        `;
    }

    /**
     * Render printed files error state
     */
    renderPrintedFilesError(error) {
        const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Laden der Dateien';

        return `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Ladefehler</h3>
                <p>${escapeHtml(message)}</p>
                <button class="btn btn-primary" onclick="dashboard.loadRecentPrintedFiles()">
                    <span class="btn-icon">🔄</span>
                    Erneut versuchen
                </button>
            </div>
        `;
    }

    /**
     * Render jobs error state
     */
    renderJobsError(error) {
        const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Laden der Aufträge';
        
        return `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Ladefehler</h3>
                <p>${escapeHtml(message)}</p>
                <button class="btn btn-primary" onclick="dashboard.loadRecentJobs()">
                    <span class="btn-icon">🔄</span>
                    Erneut versuchen
                </button>
            </div>
        `;
    }

    /**
     * Show dashboard error
     */
    showDashboardError(error) {
        const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Laden des Dashboards';
        showToast('error', 'Dashboard-Fehler', message);
    }

    /**
     * Start auto-refresh interval
     */
    startAutoRefresh() {
        // Clear existing interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Set up new interval
        this.refreshInterval = setInterval(() => {
            if (window.currentPage === 'dashboard') {
                this.refreshDashboard();
            }
        }, CONFIG.DASHBOARD_REFRESH_INTERVAL);
    }

    /**
     * Refresh dashboard data
     */
    async refreshDashboard() {
        try {
            Logger.debug('Refreshing dashboard data');
            
            // Only refresh if not currently loading
            if (document.querySelector('.loading-placeholder')) {
                return;
            }
            
            // Load fresh statistics and printer data
            await Promise.all([
                this.loadOverviewStatistics(),
                this.updatePrintersStatus(),
                this.loadRecentJobs(),
                this.loadRecentPrintedFiles()
            ]);
            
            this.lastRefresh = new Date();
        } catch (error) {
            Logger.error('Failed to refresh dashboard:', error);
        }
    }

    /**
     * Update printer status without full reload
     */
    async updatePrintersStatus() {
        try {
            const response = await api.getPrinters({ active: true });
            
            if (response.printers) {
                response.printers.forEach(printer => {
                    const printerCard = this.printers.get(printer.id);
                    if (printerCard) {
                        printerCard.update(printer);
                    } else {
                        // New printer - reload all printers
                        this.loadPrinters();
                    }
                });
            }
        } catch (error) {
            Logger.error('Failed to update printer status:', error);
        }
    }

    /**
     * Setup WebSocket listeners for real-time updates
     */
    setupWebSocketListeners() {
        // Listen for printer status updates
        document.addEventListener('printerStatusUpdate', (event) => {
            const data = event.detail;
            const printerCard = this.printers.get(data.printer_id);
            
            if (printerCard) {
                printerCard.update(data);
            }
            
            // Update overview statistics if needed
            this.updatePrinterCountFromStatus();
        });

        // Listen for job updates
        document.addEventListener('jobUpdate', (event) => {
            const data = event.detail;
            
            // Update job preview card if visible
            const jobPreview = document.querySelector(`[data-job-id="${data.id}"]`);
            if (jobPreview) {
                this.updateJobPreview(jobPreview, data);
            }
            
            // Update active jobs count
            this.updateActiveJobsCount();
        });
    }

    /**
     * Update printer count from status updates
     */
    updatePrinterCountFromStatus() {
        const onlineCount = Array.from(this.printers.values())
            .filter(card => card.printer.status === 'online').length;
        const totalCount = this.printers.size;
        
        const printerCountEl = document.getElementById('printerCount');
        if (printerCountEl) {
            printerCountEl.textContent = `${onlineCount}/${totalCount}`;
        }
    }

    /**
     * Update active jobs count from job updates
     */
    updateActiveJobsCount() {
        const printingCount = Array.from(this.printers.values())
            .filter(card => card.printer.current_job?.status === 'printing').length;
        
        const activeJobsEl = document.getElementById('activeJobsCount');
        if (activeJobsEl) {
            activeJobsEl.textContent = printingCount;
        }
    }

    /**
     * Update job preview with new data
     */
    updateJobPreview(previewElement, jobData) {
        const status = getStatusConfig('job', jobData.status);
        
        // Update status badge
        const statusBadge = previewElement.querySelector('.status-badge');
        if (statusBadge) {
            statusBadge.className = `status-badge ${status.class}`;
            statusBadge.innerHTML = `${status.icon} ${status.label}`;
        }

        // Update progress
        if (jobData.progress !== undefined) {
            const progressBar = previewElement.querySelector('.progress-bar');
            const progressText = previewElement.querySelector('.progress-text');
            
            if (progressBar) {
                progressBar.style.width = `${jobData.progress}%`;
            }
            
            if (progressText) {
                progressText.textContent = formatPercentage(jobData.progress);
            }
        }
    }
}

// Global dashboard instance
const dashboard = new Dashboard();

/**
 * Global functions for dashboard
 */

/**
 * Refresh dashboard manually
 */
function refreshDashboard() {
    dashboard.loadDashboard();
}

/**
 * Show add printer modal
 */
function showAddPrinter() {
    showModal('addPrinterModal');
    
    // Reset form
    const form = document.getElementById('addPrinterForm');
    if (form) {
        form.reset();
        
        // Hide all printer-specific fields
        const specificFields = document.querySelectorAll('.printer-specific-fields');
        specificFields.forEach(field => {
            field.style.display = 'none';
        });
    }
}

/**
 * Show printer details
 */
async function showPrinterDetails(printerId) {
    try {
        // For now, redirect to printers page
        // In future, could show detailed modal
        showPage('printers');
        
        // Highlight specific printer
        setTimeout(() => {
            const printerCard = document.querySelector(`[data-printer-id="${printerId}"]`);
            if (printerCard) {
                printerCard.scrollIntoView({ behavior: 'smooth' });
                printerCard.style.outline = '2px solid var(--primary-color)';
                setTimeout(() => {
                    printerCard.style.outline = '';
                }, 3000);
            }
        }, 500);
    } catch (error) {
        Logger.error('Failed to show printer details:', error);
        showToast('error', 'Fehler', 'Drucker-Details konnten nicht geladen werden');
    }
}

/**
 * Edit printer configuration
 */
function editPrinter(printerId) {
    // Implementation would open edit modal
    showToast('info', 'Funktion nicht verfügbar', 'Drucker-Bearbeitung wird in Phase 2 implementiert');
}

/**
 * Show job details
 */
function showJobDetails(jobId) {
    // Implementation would load and show job details modal
    // For now, redirect to jobs page
    showPage('jobs');
    
    // Highlight specific job
    setTimeout(() => {
        const jobCard = document.querySelector(`[data-job-id="${jobId}"]`);
        if (jobCard) {
            jobCard.scrollIntoView({ behavior: 'smooth' });
            jobCard.style.outline = '2px solid var(--primary-color)';
            setTimeout(() => {
                jobCard.style.outline = '';
            }, 3000);
        }
    }, 500);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Dashboard, dashboard };
}

/**
 * Manually trigger current job file download & thumbnail processing from dashboard card
 */
async function triggerCurrentJobDownload(printerId) {
    try {
        showToast('info', 'Thumbnail', 'Lade aktuelle Druckdatei...');
        const result = await api.downloadCurrentJobFile(printerId);
        const status = result.status || 'unbekannt';
        if (['exists_with_thumbnail','processed','success'].includes(status)) {
            showToast('success', 'Thumbnail', 'Thumbnail verfügbar.');
        } else if (status === 'not_printing') {
            showToast('warning', 'Kein Druck', 'Kein aktiver Druckauftrag.');
        } else if (status === 'exists_no_thumbnail') {
            showToast('info', 'Keine Vorschau', 'Datei ohne eingebettetes Thumbnail.');
        } else {
            showToast('info', 'Status', `Status: ${status}`);
        }
        // Reload dashboard section to display thumbnail if new
        refreshDashboard();
    } catch (error) {
        Logger.error('Failed to trigger current job download:', error);
        const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Abrufen der Druckdatei';
        showToast('error', 'Fehler', message);
    }
}