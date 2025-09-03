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
    }

    /**
     * Initialize dashboard page
     */
    init() {
        console.log('Initializing dashboard');
        
        // Load initial data
        this.loadDashboard();
        
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
    }

    /**
     * Load all dashboard data
     */
    async loadDashboard() {
        try {
            // Load overview statistics
            await this.loadOverviewStatistics();
            
            // Load printers
            await this.loadPrinters();
            
            // Load recent jobs
            await this.loadRecentJobs();
            
            this.lastRefresh = new Date();
        } catch (error) {
            console.error('Failed to load dashboard:', error);
            this.showDashboardError(error);
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
            console.error('Failed to load overview statistics:', error);
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
            const onlineCount = printers.printers?.filter(p => p.status === 'online').length || 0;
            const totalCount = printers.total_count || 0;
            
            printerCountEl.textContent = `${onlineCount}/${totalCount}`;
            printerDetailEl.textContent = `${totalCount} Drucker konfiguriert`;
        }

        // Active jobs card
        const activeJobsEl = document.getElementById('activeJobsCount');
        const jobsDetailEl = document.getElementById('jobsDetail');
        
        if (activeJobsEl && jobsDetailEl) {
            const activeJobs = stats.jobs?.total_jobs || 0;
            const printingJobs = printers.printers?.filter(p => p.current_job?.status === 'printing').length || 0;
            
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
            todayDetailEl.textContent = `${formatPercentage(successRate * 100)} Erfolgsrate`;
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
            
            if (response.printers && response.printers.length > 0) {
                // Create printer cards
                printerGrid.innerHTML = '';
                
                response.printers.forEach(printer => {
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
            console.error('Failed to load printers:', error);
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
            console.error('Failed to load recent jobs:', error);
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
        card.setAttribute('data-job-id', job.id);
        
        const status = getStatusConfig('job', job.status);
        
        card.innerHTML = `
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
            console.log('Refreshing dashboard data');
            
            // Only refresh if not currently loading
            if (document.querySelector('.loading-placeholder')) {
                return;
            }
            
            // Load fresh statistics and printer data
            await Promise.all([
                this.loadOverviewStatistics(),
                this.updatePrintersStatus()
            ]);
            
            this.lastRefresh = new Date();
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
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
            console.error('Failed to update printer status:', error);
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
        console.error('Failed to show printer details:', error);
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