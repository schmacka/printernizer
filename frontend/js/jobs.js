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
        Logger.debug('Initializing jobs management');
        
        // Load jobs
        this.loadJobs();
        
        // Setup filter handlers
        this.setupFilterHandlers();
        
        // Setup form handler
        this.setupFormHandler();
        
        // Set up refresh interval
        this.startAutoRefresh();
        
        // Setup WebSocket listeners
        this.setupWebSocketListeners();
        
        // Load printer options for filter
        this.loadPrinterOptions();
        
        // Populate form dropdowns
        this.populateFormDropdowns();
    }

    /**
     * Setup form submission handler
     */
    setupFormHandler() {
        const form = document.getElementById('createJobForm');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleCreateJob(e.target);
            });
        }
    }

    /**
     * Handle job creation form submission
     */
    async handleCreateJob(form) {
        try {
            // Get form data
            const formData = new FormData(form);
            const jobData = {
                name: formData.get('job_name'),
                file_id: formData.get('file') ? parseInt(formData.get('file')) : null,
                printer_id: formData.get('printer'),
                is_business: formData.get('is_business') === 'on',
                customer_name: formData.get('customer_name') || null
            };

            // Validate required fields
            if (!jobData.name) {
                showToast('error', 'Fehler', 'Bitte geben Sie einen Job-Namen ein');
                return;
            }
            if (!jobData.printer_id) {
                showToast('error', 'Fehler', 'Bitte wählen Sie einen Drucker aus');
                return;
            }

            // Create job via API
            const response = await api.createJob(jobData);
            
            if (response) {
                showToast('success', 'Erfolg', 'Job wurde erstellt');
                closeJobModal();
                form.reset();
                this.loadJobs();
            }
        } catch (error) {
            Logger.error('Failed to create job:', error);
            showToast('error', 'Fehler', `Job konnte nicht erstellt werden: ${error.message}`);
        }
    }

    /**
     * Populate form dropdowns with files and printers
     */
    async populateFormDropdowns() {
        try {
            // Populate files dropdown
            const fileSelect = document.getElementById('fileSelect');
            if (fileSelect) {
                const files = await api.getFiles();
                fileSelect.innerHTML = '<option value="">Datei auswählen...</option>';
                if (files && files.files && files.files.length > 0) {
                    files.files.forEach(file => {
                        const option = document.createElement('option');
                        option.value = file.id;
                        option.textContent = file.filename || file.name;
                        fileSelect.appendChild(option);
                    });
                }
            }

            // Populate printers dropdown
            const printerSelect = document.getElementById('printerSelect');
            if (printerSelect) {
                const printers = await api.getPrinters();
                printerSelect.innerHTML = '<option value="">Drucker auswählen...</option>';
                if (printers && printers.printers && printers.printers.length > 0) {
                    printers.printers.forEach(printer => {
                        const option = document.createElement('option');
                        option.value = printer.id;
                        option.textContent = printer.name;
                        printerSelect.appendChild(option);
                    });
                }
            }
        } catch (error) {
            Logger.error('Failed to populate form dropdowns:', error);
        }
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
            const jobsTable = document.getElementById('jobsTableBody');
            if (!jobsTable) {
                Logger.error('Jobs table body not found');
                return;
            }
            
            // Show loading state on initial load
            if (page === 1) {
                jobsTable.innerHTML = '<tr><td colspan="6" class="loading-placeholder"><div class="spinner"></div><p>Lade Aufträge...</p></td></tr>';
            }
            
            // Prepare filters
            const filters = {
                ...this.currentFilters,
                page: page,
                limit: CONFIG.DEFAULT_PAGE_SIZE || 50
            };
            
            // Load jobs from API
            const response = await api.getJobs(filters);
            
            if (page === 1) {
                // Clear existing jobs on new search
                this.jobs.clear();
                jobsTable.innerHTML = '';
            }
            
            if (response && response.length > 0) {
                // Render job rows
                response.forEach(job => {
                    const row = this.renderJobRow(job);
                    jobsTable.appendChild(row);
                    this.jobs.set(job.id, job);
                });
            } else if (page === 1) {
                // Show empty state
                jobsTable.innerHTML = '<tr><td colspan="6" class="empty-state"><p>Keine Aufträge gefunden</p></td></tr>';
            }
            
            this.currentPage = page;
            
        } catch (error) {
            Logger.error('Failed to load jobs:', error);
            const jobsTable = document.getElementById('jobsTableBody');
            if (jobsTable && this.currentPage === 1) {
                jobsTable.innerHTML = `<tr><td colspan="6" class="error-state"><p>Fehler beim Laden: ${escapeHtml(error.message)}</p></td></tr>`;
            }
        }
    }

    /**
     * Render a single job row for the table
     */
    renderJobRow(job) {
        const row = document.createElement('tr');
        row.setAttribute('data-job-id', job.id);
        row.className = `job-row status-${job.status}`;
        
        // Job name
        const nameCell = document.createElement('td');
        nameCell.innerHTML = `
            <div class="job-name">
                ${job.is_business ? '<span class="business-badge" title="Geschäftlich">🏢</span>' : ''}
                <strong>${escapeHtml(job.name || 'Unbenannt')}</strong>
                ${job.customer_name ? `<small>${escapeHtml(job.customer_name)}</small>` : ''}
            </div>
        `;
        row.appendChild(nameCell);
        
        // Printer
        const printerCell = document.createElement('td');
        printerCell.textContent = job.printer_name || job.printer_id || '-';
        row.appendChild(printerCell);
        
        // Status
        const statusCell = document.createElement('td');
        const statusBadge = this.getStatusBadge(job.status);
        statusCell.innerHTML = statusBadge;
        row.appendChild(statusCell);
        
        // File
        const fileCell = document.createElement('td');
        fileCell.textContent = job.file_name || '-';
        row.appendChild(fileCell);
        
        // Progress
        const progressCell = document.createElement('td');
        if (job.progress !== undefined && job.status === 'printing') {
            progressCell.innerHTML = `
                <div class="progress-container">
                    <div class="progress">
                        <div class="progress-bar" style="width: ${job.progress}%"></div>
                    </div>
                    <span class="progress-text">${Math.round(job.progress)}%</span>
                </div>
            `;
        } else {
            progressCell.textContent = '-';
        }
        row.appendChild(progressCell);
        
        // Actions
        const actionsCell = document.createElement('td');
        actionsCell.innerHTML = `
            <div class="action-buttons">
                ${job.status === 'printing' ? '<button class="btn-icon" title="Pause" onclick="jobManager.pauseJob(\'' + sanitizeAttribute(job.id) + '\')">⏸️</button>' : ''}
                ${job.status === 'paused' ? '<button class="btn-icon" title="Fortsetzen" onclick="jobManager.resumeJob(\'' + sanitizeAttribute(job.id) + '\')">▶️</button>' : ''}
                ${['printing', 'paused', 'queued'].includes(job.status) ? '<button class="btn-icon" title="Abbrechen" onclick="jobManager.cancelJob(\'' + sanitizeAttribute(job.id) + '\')">⏹️</button>' : ''}
                <button class="btn-icon" title="Details" onclick="jobManager.showJobDetails(\'' + sanitizeAttribute(job.id) + '\')">ℹ️</button>
            </div>
        `;
        row.appendChild(actionsCell);
        
        return row;
    }

    /**
     * Get status badge HTML
     */
    getStatusBadge(status) {
        const statusMap = {
            'printing': { label: 'Druckt', icon: '🖨️', class: 'status-printing' },
            'queued': { label: 'Warteschlange', icon: '⏳', class: 'status-queued' },
            'completed': { label: 'Abgeschlossen', icon: '✅', class: 'status-completed' },
            'failed': { label: 'Fehlgeschlagen', icon: '❌', class: 'status-failed' },
            'cancelled': { label: 'Abgebrochen', icon: '⏹️', class: 'status-cancelled' },
            'paused': { label: 'Pausiert', icon: '⏸️', class: 'status-paused' }
        };
        
        const statusInfo = statusMap[status] || { label: status, icon: '❓', class: 'status-unknown' };
        return `<span class="status-badge ${statusInfo.class}">${statusInfo.icon} ${statusInfo.label}</span>`;
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
            Logger.error('Failed to load printer options:', error);
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
            Logger.error('Failed to refresh jobs:', error);
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
            Logger.error('Failed to load job details:', error);
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
                    <h3>${escapeHtml(job.filename || job.job_name || 'Unbekannter Auftrag')}</h3>
                    <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
                </div>

                <div class="job-details-grid">
                    <div class="detail-section">
                        <h4>Allgemeine Informationen</h4>
                        <div class="detail-item">
                            <label>Dateiname:</label>
                            <span>${escapeHtml(job.filename || 'Unbekannt')}</span>
                        </div>
                        <div class="detail-item">
                            <label>Drucker ID:</label>
                            <span>${escapeHtml(job.printer_id || job.printer_name || 'Unbekannt')}</span>
                        </div>
                        <div class="detail-item">
                            <label>Erstellt:</label>
                            <span>${formatDateTime(job.created_at)}</span>
                        </div>
                        <div class="detail-item">
                            <label>Gestartet:</label>
                            <span>${job.started_at ? formatDateTime(job.started_at) : 'Nicht gestartet'}</span>
                        </div>
                        ${job.completed_at ? `
                            <div class="detail-item">
                                <label>Beendet:</label>
                                <span>${formatDateTime(job.completed_at)}</span>
                            </div>
                        ` : ''}
                        <div class="detail-item">
                            <label>Geschäftlich:</label>
                            <span>${job.is_business ? 'Ja' : 'Nein'}</span>
                        </div>
                        ${job.customer_name ? `
                            <div class="detail-item">
                                <label>Kunde:</label>
                                <span>${escapeHtml(job.customer_name)}</span>
                            </div>
                        ` : ''}
                    </div>

                    ${this.renderJobProgressFromBackend(job)}
                    ${this.renderJobCostsFromBackend(job)}
                    ${this.renderJobTimingFromBackend(job)}
                </div>

                <div class="job-actions">
                    ${this.renderJobDetailActions(job)}
                </div>
            </div>
        `;
    }

    /**
     * Render job progress section for backend data format
     */
    renderJobProgressFromBackend(job) {
        if (job.progress_percent !== undefined && job.progress_percent > 0) {
            return `
                <div class="detail-section">
                    <h4>Fortschritt</h4>
                    <div class="detail-item">
                        <label>Fortschritt:</label>
                        <div class="progress-display">
                            <div class="progress">
                                <div class="progress-bar" style="width: ${job.progress_percent}%"></div>
                            </div>
                            <span class="progress-text">${formatPercentage(job.progress_percent)}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        return '';
    }

    /**
     * Render job costs section for backend data format
     */
    renderJobCostsFromBackend(job) {
        if (job.cost_eur !== undefined || job.material_used_grams !== undefined) {
            return `
                <div class="detail-section">
                    <h4>Ressourcen & Kosten</h4>
                    ${job.material_used_grams ? `
                        <div class="detail-item">
                            <label>Material verbraucht:</label>
                            <span>${formatWeight(job.material_used_grams)}</span>
                        </div>
                    ` : ''}
                    ${job.cost_eur ? `
                        <div class="detail-item">
                            <label><strong>Gesamtkosten:</strong></label>
                            <span><strong>${formatCurrency(job.cost_eur)}</strong></span>
                        </div>
                    ` : ''}
                </div>
            `;
        }
        return '';
    }

    /**
     * Render job timing section for backend data format
     */
    renderJobTimingFromBackend(job) {
        if (job.estimated_time_minutes || job.elapsed_time_minutes || job.remaining_time_minutes) {
            return `
                <div class="detail-section">
                    <h4>Zeitschätzung</h4>
                    ${job.estimated_time_minutes ? `
                        <div class="detail-item">
                            <label>Geschätzte Zeit:</label>
                            <span>${formatDuration(job.estimated_time_minutes * 60)}</span>
                        </div>
                    ` : ''}
                    ${job.elapsed_time_minutes ? `
                        <div class="detail-item">
                            <label>Vergangene Zeit:</label>
                            <span>${formatDuration(job.elapsed_time_minutes * 60)}</span>
                        </div>
                    ` : ''}
                    ${job.remaining_time_minutes ? `
                        <div class="detail-item">
                            <label>Verbleibende Zeit:</label>
                            <span>${formatDuration(job.remaining_time_minutes * 60)}</span>
                        </div>
                    ` : ''}
                </div>
            `;
        }
        return '';
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
                <button class="btn btn-warning" onclick="jobManager.cancelJob('${job.id}')">
                    <span class="btn-icon">⏹️</span>
                    Auftrag abbrechen
                </button>
            `);
        }

        // Edit job info
        actions.push(`
            <button class="btn btn-secondary" onclick="jobManager.editJob('${job.id}')">
                <span class="btn-icon">✏️</span>
                Bearbeiten
            </button>
        `);

        // Export job data
        actions.push(`
            <button class="btn btn-secondary" onclick="jobManager.exportJob('${job.id}')">
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
            Logger.error('Failed to cancel job:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Abbrechen des Auftrags';
            showToast('error', 'Fehler', message);
        }
    }

    /**
     * Edit job information
     */
    async editJob(jobId) {
        try {
            // First, get current job data
            const job = await api.getJob(jobId);

            // Show edit modal with job data
            this.showEditJobModal(job);

        } catch (error) {
            Logger.error('Failed to load job for editing:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Laden der Auftrag-Daten';
            showToast('error', 'Fehler', message);
        }
    }

    /**
     * Show edit job modal
     */
    showEditJobModal(job) {
        const modal = document.getElementById('editJobModal');
        if (!modal) {
            // Create edit modal dynamically if it doesn't exist
            this.createEditJobModal();
        }

        // Populate form with job data
        document.getElementById('editJobId').value = job.id;
        document.getElementById('editJobFilename').value = job.filename || '';
        document.getElementById('editJobBusiness').checked = job.is_business || false;
        document.getElementById('editJobCustomer').value = job.customer_name || '';

        showModal('editJobModal');
    }

    /**
     * Create edit job modal HTML
     */
    createEditJobModal() {
        const modalHTML = `
            <div id="editJobModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Auftrag bearbeiten</h3>
                        <button class="modal-close" onclick="closeModal('editJobModal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="editJobForm" onsubmit="jobManager.updateJob(event)">
                            <input type="hidden" id="editJobId">

                            <div class="form-group">
                                <label for="editJobFilename">Dateiname:</label>
                                <input type="text" id="editJobFilename" readonly class="form-control">
                                <small class="form-text text-muted">Dateiname kann nicht geändert werden</small>
                            </div>

                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="editJobBusiness">
                                    Geschäftlicher Auftrag
                                </label>
                            </div>

                            <div class="form-group">
                                <label for="editJobCustomer">Kundenname:</label>
                                <input type="text" id="editJobCustomer" class="form-control"
                                       placeholder="Optional - nur für geschäftliche Aufträge">
                            </div>

                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">
                                    <span class="btn-icon">💾</span>
                                    Speichern
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="closeModal('editJobModal')">
                                    Abbrechen
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;

        // Append modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    /**
     * Update job with form data
     */
    async updateJob(event) {
        event.preventDefault();

        const jobId = document.getElementById('editJobId').value;
        const isBusiness = document.getElementById('editJobBusiness').checked;
        const customerName = document.getElementById('editJobCustomer').value.trim();

        try {
            // Prepare update data
            const updateData = {
                is_business: isBusiness
            };

            // Only include customer_name if provided
            if (customerName) {
                updateData.customer_name = customerName;
            } else if (isBusiness) {
                // Validate: customer name required for business jobs
                showToast('error', 'Fehler', 'Kundenname ist für geschäftliche Aufträge erforderlich');
                return;
            } else {
                // Clear customer name for non-business jobs
                updateData.customer_name = null;
            }

            // Make API call to update job
            const response = await fetch(`/api/v1/jobs/${jobId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update job');
            }

            const updatedJob = await response.json();

            showToast('success', 'Erfolg', 'Auftrag wurde erfolgreich aktualisiert');
            closeModal('editJobModal');

            // Refresh job list to show changes
            this.loadJobs(this.currentPage);

            Logger.info('Job updated successfully', { jobId, updatedJob });

        } catch (error) {
            Logger.error('Failed to update job:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : (error.message || 'Fehler beim Aktualisieren des Auftrags');
            showToast('error', 'Fehler', message);
        }
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