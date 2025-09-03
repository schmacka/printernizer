/**
 * Printernizer Jobs Management Page
 * Handles job monitoring, filtering, and real-time updates
 */

class JobManager {
    constructor() {
        this.jobs = new Map();
        this.refreshInterval = null;
        this.currentFilters = {};
        this.currentPage = 1;
        this.totalPages = 1;
        this.pagination = null;
    }

    /**
     * Initialize jobs management page
     */
    init() {
        console.log('Initializing jobs management');
        
        // Load jobs
        this.loadJobs();
        
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
     * Cleanup jobs manager resources
     */
    cleanup() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Load and display jobs
     */
    async loadJobs(page = 1) {
        try {
            const jobsList = document.getElementById('jobsList');
            if (!jobsList) return;
            
            // Show loading state on initial load
            if (page === 1) {
                setLoadingState(jobsList, true);
            }
            
            // Prepare filters
            const filters = {
                ...this.currentFilters,
                page: page,
                limit: CONFIG.DEFAULT_PAGE_SIZE
            };
            
            // Load jobs from API
            const response = await api.getJobs(filters);
            
            if (page === 1) {
                // Clear existing jobs on new search
                this.jobs.clear();
                jobsList.innerHTML = '';
            }
            
            if (response.jobs && response.jobs.length > 0) {
                // Create job items
                response.jobs.forEach(job => {
                    const jobItem = new JobListItem(job);
                    const itemElement = jobItem.render();
                    jobsList.appendChild(itemElement);
                    
                    // Store job item for updates
                    this.jobs.set(job.id, jobItem);
                });
                
                // Update pagination
                this.updatePagination(response.pagination);
                
            } else if (page === 1) {
                // Show empty state
                jobsList.innerHTML = this.renderEmptyJobsState();
            }
            
            this.currentPage = page;
            
        } catch (error) {
            console.error('Failed to load jobs:', error);
            const jobsList = document.getElementById('jobsList');
            if (jobsList && this.currentPage === 1) {
                jobsList.innerHTML = this.renderJobsError(error);
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
        let paginationContainer = document.querySelector('.jobs-pagination');
        if (!paginationContainer) {
            paginationContainer = document.createElement('div');
            paginationContainer.className = 'jobs-pagination';
            
            const jobsContainer = document.querySelector('.jobs-container');
            if (jobsContainer) {
                jobsContainer.appendChild(paginationContainer);
            }
        }
        
        // Create or update pagination component
        if (this.pagination) {
            this.pagination.update(paginationData.page, paginationData.total_pages);
        } else {
            this.pagination = new Pagination(
                paginationData.page,
                paginationData.total_pages,
                (page) => this.loadJobs(page)
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
        let infoContainer = document.querySelector('.jobs-pagination-info');
        if (!infoContainer) {
            infoContainer = document.createElement('div');
            infoContainer.className = 'jobs-pagination-info text-center text-muted';
            
            const paginationContainer = document.querySelector('.jobs-pagination');
            if (paginationContainer) {
                paginationContainer.insertBefore(infoContainer, paginationContainer.firstChild);
            }
        }
        
        const start = (paginationData.page - 1) * paginationData.limit + 1;
        const end = Math.min(start + paginationData.limit - 1, paginationData.total_items);
        
        infoContainer.innerHTML = `
            Aufträge ${start}-${end} von ${paginationData.total_items}
        `;
    }

    /**
     * Setup filter change handlers
     */
    setupFilterHandlers() {
        // Status filter
        const statusFilter = document.getElementById('jobStatusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.currentFilters.status = e.target.value || undefined;
                this.loadJobs(1);
            });
        }
        
        // Printer filter
        const printerFilter = document.getElementById('jobPrinterFilter');
        if (printerFilter) {
            printerFilter.addEventListener('change', (e) => {
                this.currentFilters.printer_id = e.target.value || undefined;
                this.loadJobs(1);
            });
        }
        
        // Date filters (could be added later)
        // Business filter (could be added later)
    }

    /**
     * Load printer options for filter dropdown
     */
    async loadPrinterOptions() {
        try {
            const printerFilter = document.getElementById('jobPrinterFilter');
            if (!printerFilter) return;
            
            const response = await api.getPrinters({ active: true });
            
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
     * Render empty jobs state
     */
    renderEmptyJobsState() {
        const hasFilters = Object.keys(this.currentFilters).length > 0;
        
        if (hasFilters) {
            return `
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <h3>Keine Aufträge gefunden</h3>
                    <p>Keine Aufträge entsprechen den aktuellen Filterkriterien.</p>
                    <button class="btn btn-secondary" onclick="jobManager.clearFilters()">
                        <span class="btn-icon">🗑️</span>
                        Filter löschen
                    </button>
                </div>
            `;
        }
        
        return `
            <div class="empty-state">
                <div class="empty-state-icon">⚙️</div>
                <h3>Keine Aufträge vorhanden</h3>
                <p>Hier werden alle Druckaufträge angezeigt, sobald sie erstellt werden.</p>
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
                <button class="btn btn-primary" onclick="jobManager.loadJobs()">
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
        const statusFilter = document.getElementById('jobStatusFilter');
        const printerFilter = document.getElementById('jobPrinterFilter');
        
        if (statusFilter) statusFilter.value = '';
        if (printerFilter) printerFilter.value = '';
        
        // Reload jobs
        this.loadJobs(1);
    }

    /**
     * Start auto-refresh interval
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            if (window.currentPage === 'jobs') {
                this.refreshJobs();
            }
        }, CONFIG.JOB_REFRESH_INTERVAL);
    }

    /**
     * Refresh jobs without full reload
     */
    async refreshJobs() {
        try {
            // Only refresh first page to get latest jobs
            const filters = {
                ...this.currentFilters,
                page: 1,
                limit: CONFIG.DEFAULT_PAGE_SIZE
            };
            
            const response = await api.getJobs(filters);
            
            if (response.jobs) {
                // Update existing jobs or add new ones
                response.jobs.forEach(jobData => {
                    const existingJob = this.jobs.get(jobData.id);
                    if (existingJob) {
                        existingJob.update(jobData);
                    }
                    // Note: New jobs would require a full reload to maintain proper order
                });
            }
        } catch (error) {
            console.error('Failed to refresh jobs:', error);
        }
    }

    /**
     * Setup WebSocket listeners
     */
    setupWebSocketListeners() {
        // Listen for job updates
        document.addEventListener('jobUpdate', (event) => {
            const jobData = event.detail;
            const jobItem = this.jobs.get(jobData.id);
            
            if (jobItem) {
                jobItem.update(jobData);
            }
            // If job doesn't exist in current view, could trigger refresh
        });
    }

    /**
     * Show job details modal
     */
    async showJobDetails(jobId) {
        try {
            const modal = document.getElementById('jobDetailsModal');
            const content = document.getElementById('jobDetailsContent');
            
            if (!modal || !content) return;
            
            // Show modal with loading state
            showModal('jobDetailsModal');
            setLoadingState(content, true);
            
            // Load job details
            const job = await api.getJob(jobId);
            
            // Render job details
            content.innerHTML = this.renderJobDetailsContent(job);
            
        } catch (error) {
            console.error('Failed to load job details:', error);
            const content = document.getElementById('jobDetailsContent');
            if (content) {
                content.innerHTML = this.renderJobDetailsError(error);
            }
        }
    }

    /**
     * Render job details modal content
     */
    renderJobDetailsContent(job) {
        const status = getStatusConfig('job', job.status);
        
        return `
            <div class="job-details">
                <div class="job-header">
                    <h3>${escapeHtml(job.job_name)}</h3>
                    <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
                </div>
                
                <div class="job-details-grid">
                    <div class="detail-section">
                        <h4>Allgemeine Informationen</h4>
                        <div class="detail-item">
                            <label>Drucker:</label>
                            <span>${escapeHtml(job.printer_name)}</span>
                        </div>
                        <div class="detail-item">
                            <label>Erstellt:</label>
                            <span>${formatDateTime(job.created_at)}</span>
                        </div>
                        <div class="detail-item">
                            <label>Gestartet:</label>
                            <span>${job.start_time ? formatDateTime(job.start_time) : 'Nicht gestartet'}</span>
                        </div>
                        ${job.end_time ? `
                            <div class="detail-item">
                                <label>Beendet:</label>
                                <span>${formatDateTime(job.end_time)}</span>
                            </div>
                        ` : ''}
                        <div class="detail-item">
                            <label>Geschäftlich:</label>
                            <span>${job.is_business ? 'Ja' : 'Nein'}</span>
                        </div>
                    </div>
                    
                    ${this.renderJobProgress(job)}
                    ${this.renderJobFile(job.file_info)}
                    ${this.renderJobMaterial(job.material_info)}
                    ${this.renderJobSettings(job.print_settings)}
                    ${this.renderJobCosts(job.costs)}
                    ${job.customer_info ? this.renderJobCustomer(job.customer_info) : ''}
                </div>
                
                <div class="job-actions">
                    ${this.renderJobDetailActions(job)}
                </div>
            </div>
        `;
    }

    /**
     * Render job progress section
     */
    renderJobProgress(job) {
        if (!['printing', 'paused'].includes(job.status)) {
            return '';
        }
        
        return `
            <div class="detail-section">
                <h4>Fortschritt</h4>
                ${job.progress !== undefined ? `
                    <div class="detail-item">
                        <label>Fortschritt:</label>
                        <div class="progress-display">
                            <div class="progress">
                                <div class="progress-bar" style="width: ${job.progress}%"></div>
                            </div>
                            <span class="progress-text">${formatPercentage(job.progress)}</span>
                        </div>
                    </div>
                ` : ''}
                ${job.layer_current && job.layer_total ? `
                    <div class="detail-item">
                        <label>Schicht:</label>
                        <span>${job.layer_current} / ${job.layer_total}</span>
                    </div>
                ` : ''}
                ${job.estimated_completion ? `
                    <div class="detail-item">
                        <label>Voraussichtlich fertig:</label>
                        <span>${formatDateTime(job.estimated_completion)}</span>
                    </div>
                ` : ''}
                ${job.estimated_remaining ? `
                    <div class="detail-item">
                        <label>Verbleibende Zeit:</label>
                        <span>${formatDuration(job.estimated_remaining)}</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Render job file information
     */
    renderJobFile(fileInfo) {
        if (!fileInfo) return '';
        
        return `
            <div class="detail-section">
                <h4>Datei</h4>
                <div class="detail-item">
                    <label>Dateiname:</label>
                    <span>${escapeHtml(fileInfo.filename)}</span>
                </div>
                <div class="detail-item">
                    <label>Größe:</label>
                    <span>${formatBytes(fileInfo.size)}</span>
                </div>
                ${fileInfo.uploaded_at ? `
                    <div class="detail-item">
                        <label>Hochgeladen:</label>
                        <span>${formatDateTime(fileInfo.uploaded_at)}</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Render job material information
     */
    renderJobMaterial(materialInfo) {
        if (!materialInfo) return '';
        
        return `
            <div class="detail-section">
                <h4>Material</h4>
                <div class="detail-item">
                    <label>Typ:</label>
                    <span>${materialInfo.type}${materialInfo.brand ? ` (${materialInfo.brand})` : ''}</span>
                </div>
                ${materialInfo.color ? `
                    <div class="detail-item">
                        <label>Farbe:</label>
                        <span>${materialInfo.color}</span>
                    </div>
                ` : ''}
                ${materialInfo.estimated_usage ? `
                    <div class="detail-item">
                        <label>Geschätzter Verbrauch:</label>
                        <span>${formatWeight(materialInfo.estimated_usage * 1000)}</span>
                    </div>
                ` : ''}
                ${materialInfo.actual_usage ? `
                    <div class="detail-item">
                        <label>Tatsächlicher Verbrauch:</label>
                        <span>${formatWeight(materialInfo.actual_usage * 1000)}</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Render job print settings
     */
    renderJobSettings(printSettings) {
        if (!printSettings) return '';
        
        return `
            <div class="detail-section">
                <h4>Druckeinstellungen</h4>
                ${printSettings.layer_height ? `
                    <div class="detail-item">
                        <label>Schichthöhe:</label>
                        <span>${printSettings.layer_height} mm</span>
                    </div>
                ` : ''}
                ${printSettings.infill_percentage ? `
                    <div class="detail-item">
                        <label>Füllung:</label>
                        <span>${printSettings.infill_percentage}%</span>
                    </div>
                ` : ''}
                ${printSettings.print_speed ? `
                    <div class="detail-item">
                        <label>Geschwindigkeit:</label>
                        <span>${printSettings.print_speed} mm/min</span>
                    </div>
                ` : ''}
                ${printSettings.nozzle_temperature ? `
                    <div class="detail-item">
                        <label>Düsentemperatur:</label>
                        <span>${printSettings.nozzle_temperature}°C</span>
                    </div>
                ` : ''}
                ${printSettings.bed_temperature ? `
                    <div class="detail-item">
                        <label>Betttemperatur:</label>
                        <span>${printSettings.bed_temperature}°C</span>
                    </div>
                ` : ''}
                ${printSettings.supports_used !== undefined ? `
                    <div class="detail-item">
                        <label>Stützmaterial:</label>
                        <span>${printSettings.supports_used ? 'Ja' : 'Nein'}</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Render job cost information
     */
    renderJobCosts(costs) {
        if (!costs) return '';
        
        return `
            <div class="detail-section">
                <h4>Kosten</h4>
                ${costs.material_cost ? `
                    <div class="detail-item">
                        <label>Material:</label>
                        <span>${formatCurrency(costs.material_cost)}</span>
                    </div>
                ` : ''}
                ${costs.power_cost ? `
                    <div class="detail-item">
                        <label>Strom:</label>
                        <span>${formatCurrency(costs.power_cost)}</span>
                    </div>
                ` : ''}
                ${costs.labor_cost ? `
                    <div class="detail-item">
                        <label>Arbeit:</label>
                        <span>${formatCurrency(costs.labor_cost)}</span>
                    </div>
                ` : ''}
                <div class="detail-item">
                    <label><strong>Gesamt:</strong></label>
                    <span><strong>${formatCurrency(costs.total_cost)}</strong></span>
                </div>
            </div>
        `;
    }

    /**
     * Render job customer information
     */
    renderJobCustomer(customerInfo) {
        return `
            <div class="detail-section">
                <h4>Kunde</h4>
                ${customerInfo.customer_name ? `
                    <div class="detail-item">
                        <label>Name:</label>
                        <span>${escapeHtml(customerInfo.customer_name)}</span>
                    </div>
                ` : ''}
                ${customerInfo.order_id ? `
                    <div class="detail-item">
                        <label>Auftragsnummer:</label>
                        <span>${escapeHtml(customerInfo.order_id)}</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Render job detail action buttons
     */
    renderJobDetailActions(job) {
        const actions = [];
        
        // Cancel job if active
        if (['printing', 'queued', 'preparing', 'paused'].includes(job.status)) {
            actions.push(`
                <button class="btn btn-warning" onclick="jobManager.cancelJob(${job.id})">
                    <span class="btn-icon">⏹️</span>
                    Auftrag abbrechen
                </button>
            `);
        }
        
        // Edit job info
        actions.push(`
            <button class="btn btn-secondary" onclick="jobManager.editJob(${job.id})">
                <span class="btn-icon">✏️</span>
                Bearbeiten
            </button>
        `);
        
        // Export job data
        actions.push(`
            <button class="btn btn-secondary" onclick="jobManager.exportJob(${job.id})">
                <span class="btn-icon">📊</span>
                Export
            </button>
        `);
        
        return actions.join('');
    }

    /**
     * Render job details error
     */
    renderJobDetailsError(error) {
        const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Laden der Auftrag-Details';
        
        return `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Ladefehler</h3>
                <p>${escapeHtml(message)}</p>
            </div>
        `;
    }

    /**
     * Cancel job
     */
    async cancelJob(jobId) {
        const confirmed = confirm('Möchten Sie diesen Auftrag wirklich abbrechen?');
        if (!confirmed) return;
        
        try {
            await api.cancelJob(jobId);
            showToast('success', 'Erfolg', CONFIG.SUCCESS_MESSAGES.JOB_CANCELLED);
            
            // Close modal if open
            closeModal('jobDetailsModal');
            
            // Refresh jobs
            this.loadJobs(this.currentPage);
            
        } catch (error) {
            console.error('Failed to cancel job:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Abbrechen des Auftrags';
            showToast('error', 'Fehler', message);
        }
    }

    /**
     * Edit job information
     */
    editJob(jobId) {
        showToast('info', 'Funktion nicht verfügbar', 'Auftrag-Bearbeitung wird in einer späteren Version implementiert');
    }

    /**
     * Export job data
     */
    exportJob(jobId) {
        showToast('info', 'Funktion nicht verfügbar', 'Auftrag-Export wird in Phase 2 implementiert');
    }
}

// Global job manager instance
const jobManager = new JobManager();

/**
 * Global functions for job management
 */

/**
 * Refresh jobs list
 */
function refreshJobs() {
    jobManager.loadJobs();
}

/**
 * Show job details (called from components)
 */
function showJobDetails(jobId) {
    jobManager.showJobDetails(jobId);
}

/**
 * Cancel job (called from components)
 */
function cancelJob(jobId) {
    jobManager.cancelJob(jobId);
}

/**
 * Edit job (called from components)
 */
function editJob(jobId) {
    jobManager.editJob(jobId);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { JobManager, jobManager };
}