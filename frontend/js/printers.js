/**
 * Printernizer Printer Management Page
 * Handles printer configuration, management, and monitoring
 */

class PrinterManager {
    constructor() {
        this.printers = new Map();
        this.refreshInterval = null;
        this.currentFilters = {};
    }

    /**
     * Initialize printer management page
     */
    init() {
        Logger.debug('Initializing printer management');

        // Scroll to top of page
        window.scrollTo(0, 0);

        // Load printers
        this.loadPrinters();

        // Check for startup discovered printers and display them
        this.checkAndDisplayStartupDiscoveredPrinters();

        // Set up refresh interval
        this.startAutoRefresh();

        // Setup form handlers
        this.setupFormHandlers();

        // Setup WebSocket listeners
        this.setupWebSocketListeners();
    }

    /**
     * Cleanup printer manager resources
     */
    cleanup() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Check for startup discovered printers and display them automatically
     */
    async checkAndDisplayStartupDiscoveredPrinters() {
        try {
            const result = await api.getStartupDiscoveredPrinters();

            if (result && result.new_count > 0) {
                const discoveredSection = document.getElementById('discoveredPrintersSection');
                const discoveredList = document.getElementById('discoveredPrintersList');

                if (discoveredSection && discoveredList) {
                    // Show the discovered section
                    discoveredSection.style.display = 'block';

                    // Populate discovered printers list (only show new printers, not already added)
                    discoveredList.innerHTML = '';
                    const newPrinters = result.discovered.filter(printer => !printer.already_added);

                    if (newPrinters.length > 0) {
                        newPrinters.forEach(printer => {
                            const card = createDiscoveredPrinterCard(printer);
                            discoveredList.appendChild(card);
                        });

                        // Scroll to discovered section
                        setTimeout(() => {
                            discoveredSection.scrollIntoView({ behavior: 'smooth' });
                        }, 100);
                    }
                }
            }
        } catch (error) {
            Logger.error('Failed to check startup discovered printers:', error);
            // Silently fail - don't disrupt printer page loading
        }
    }

    /**
     * Load and display all printers
     */
    async loadPrinters() {
        try {
            const printersList = document.getElementById('printersList');
            if (!printersList) return;
            
            // Show loading state
            setLoadingState(printersList, true);
            
            // Load printers from API
            const response = await api.getPrinters(this.currentFilters);
            
            // Clear existing printers
            this.printers.clear();
            printersList.innerHTML = '';
            
            // API returns {printers: [], total_count: N, pagination: {...}}
            const printers = response?.printers || response;
            const printersArray = Array.isArray(printers) ? printers : (Array.isArray(response) ? response : []);
            
            if (printersArray.length > 0) {
                // Create printer cards
                printersArray.forEach(printer => {
                    const printerCard = this.createPrinterManagementCard(printer);
                    printersList.appendChild(printerCard);
                    
                    // Store printer card for updates
                    this.printers.set(printer.id, {
                        data: printer,
                        element: printerCard
                    });
                });
            } else {
                // Show empty state
                printersList.innerHTML = this.renderEmptyPrintersState();
            }
        } catch (error) {
            Logger.error('Failed to load printers:', error);
            const printersList = document.getElementById('printersList');
            if (printersList) {
                printersList.innerHTML = this.renderPrintersError(error);
            }
        }
    }

    /**
     * Create detailed printer management card
     */
    createPrinterManagementCard(printer) {
        const card = document.createElement('div');
        const isConnecting = printer.status === 'connecting' || printer.connection_state === 'connecting';
        const statusClass = isConnecting ? 'status-connecting' : `status-${printer.status}`;
        card.className = `card printer-tile-card ${statusClass}`;
        card.setAttribute('data-printer-id', printer.id);

        const status = getStatusConfig('printer', isConnecting ? 'connecting' : printer.status);
        const printerType = CONFIG.PRINTER_TYPES[printer.printer_type] || { label: printer.printer_type, color: '#6b7280' };

        // Connection type indicator
        const connectionType = printer.connection_type || (printer.printer_type === 'bambu_lab' ? 'MQTT' : 'HTTP');
        const connectionIndicator = isConnecting
            ? `<span class="connection-indicator connecting" title="${t('printers.connectionEstablishing')}">⟳ ${connectionType}</span>`
            : `<span class="connection-indicator ${printer.status === 'online' || printer.status === 'printing' ? 'connected' : 'disconnected'}" title="${t('printers.connectionType', { type: connectionType })}">${connectionType}</span>`;

        card.innerHTML = `
            <div class="printer-tile-header">
                <div class="printer-tile-status">
                    <span class="status-badge ${status.class}">${status.icon}</span>
                    ${connectionIndicator}
                </div>
                <div class="printer-tile-type" style="background-color: ${sanitizeAttribute(printerType.color)};">
                    ${printerType.label}
                </div>
            </div>

            <div class="printer-tile-body">
                <div class="printer-tile-title">
                    <h3>${escapeHtml(printer.name)}</h3>
                    <p class="printer-tile-ip">${escapeHtml(printer.ip_address)}</p>
                </div>

                ${this.renderTileCurrentJob(printer)}
                ${this.renderTileTemperatures(printer.temperatures)}
                ${this.renderTileFilaments(printer.filaments)}

                <div class="printer-tile-stats">
                    ${this.renderTileStatistics(printer.statistics)}
                </div>
            </div>

            <div class="printer-tile-footer">
                <div class="printer-tile-actions">
                    <button class="btn-icon" onclick="printerManager.showPrinterDetails('${sanitizeAttribute(printer.id)}')" title="${t('printers.showDetails')}">
                        👁️
                    </button>
                    <button class="btn-icon" onclick="printerManager.editPrinter('${sanitizeAttribute(printer.id)}')" title="${t('common.edit')}">
                        ✏️
                    </button>
                    ${this.renderTilePrinterControls(printer)}
                    <button class="btn-icon btn-error-icon" onclick="printerManager.deletePrinter('${sanitizeAttribute(printer.id)}')" title="${t('common.delete')}">
                        🗑️
                    </button>
                </div>
            </div>
        `;

        return card;
    }

    /**
     * Render current job info for tile layout
     */
    renderTileCurrentJob(printer) {
        if (!printer.current_job) {
            return `<div class="printer-tile-idle"><span class="text-muted">${t('status.printer.idle')}</span></div>`;
        }

        const jobName = typeof printer.current_job === 'string' ? printer.current_job : printer.current_job.name;

        return `
            <div class="printer-tile-job">
                <div class="tile-job-name" title="${escapeHtml(jobName)}">${escapeHtml(this.truncateJobName(jobName, 30))}</div>
                ${printer.progress !== undefined ? `
                    <div class="tile-progress-container">
                        <div class="progress">
                            <div class="progress-bar" style="width: ${printer.progress}%"></div>
                        </div>
                        <span class="tile-progress-text">${formatPercentage(printer.progress)}</span>
                    </div>
                ` : ''}
                ${printer.remaining_time_minutes ? `
                    <div class="tile-time-remaining">
                        ⏱️ ${t('printers.timeRemaining', { time: formatDuration(printer.remaining_time_minutes * 60) })}
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Render temperatures for tile layout
     */
    renderTileTemperatures(temperatures) {
        // Always show temperatures for consistent card height
        if (!temperatures) {
            return `
                <div class="printer-tile-temps printer-tile-temps-placeholder">
                    <span class="tile-temp text-muted" title="${t('printers.nozzle')}">🔥 --°C</span>
                    <span class="tile-temp text-muted" title="${t('printers.printBed')}">🛏️ --°C</span>
                </div>
            `;
        }

        const tempItems = [];

        if (temperatures.nozzle !== undefined) {
            const nozzle = typeof temperatures.nozzle === 'object' ? temperatures.nozzle : { current: temperatures.nozzle };
            tempItems.push(`<span class="tile-temp" title="${t('printers.nozzle')}">🔥 ${parseFloat(nozzle.current).toFixed(0)}°C</span>`);
        }

        if (temperatures.bed !== undefined) {
            const bed = typeof temperatures.bed === 'object' ? temperatures.bed : { current: temperatures.bed };
            tempItems.push(`<span class="tile-temp" title="${t('printers.printBed')}">🛏️ ${parseFloat(bed.current).toFixed(0)}°C</span>`);
        }

        if (tempItems.length === 0) {
            return `
                <div class="printer-tile-temps printer-tile-temps-placeholder">
                    <span class="tile-temp text-muted" title="${t('printers.nozzle')}">🔥 --°C</span>
                    <span class="tile-temp text-muted" title="${t('printers.printBed')}">🛏️ --°C</span>
                </div>
            `;
        }

        return `
            <div class="printer-tile-temps">
                ${tempItems.join('')}
            </div>
        `;
    }

    /**
     * Render filaments for tile layout
     */
    renderTileFilaments(filaments) {
        if (!filaments || filaments.length === 0) {
            return '';
        }

        const filamentItems = filaments.map(filament => {
            const slotLabel = filament.slot === 254 ? 'Ext' : `${filament.slot + 1}`;
            const filamentType = filament.type || '?';
            const filamentColor = filament.color || '#CCCCCC';
            const isActive = filament.is_active;

            return `
                <div class="filament-item ${isActive ? 'filament-active' : ''}" data-slot="${filament.slot}" title="${t('printers.slotTitle', { slot: slotLabel, type: filamentType })}">
                    <div class="filament-color" style="background-color: ${escapeHtml(filamentColor)}"></div>
                    <div class="filament-info">
                        <span class="filament-slot">${slotLabel}</span>
                        <span class="filament-type">${escapeHtml(filamentType)}</span>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="filaments">
                <div class="filaments-header">
                    <span class="filaments-label">${t('printers.filaments')}</span>
                </div>
                <div class="filaments-list">
                    ${filamentItems}
                </div>
            </div>
        `;
    }

    /**
     * Render statistics for tile layout
     */
    renderTileStatistics(statistics) {
        if (!statistics) return `<span class="text-muted">${t('printers.noStatistics')}</span>`;

        const stats = [];

        if (statistics.total_jobs !== undefined) {
            stats.push(`<span class="tile-stat" title="${t('printers.totalJobs')}">📊 ${statistics.total_jobs}</span>`);
        }

        if (statistics.success_rate !== undefined) {
            const rate = (statistics.success_rate * 100).toFixed(0);
            stats.push(`<span class="tile-stat" title="${t('printers.successRate')}">✓ ${rate}%</span>`);
        }

        if (stats.length === 0) return '<span class="text-muted">-</span>';

        return stats.join('');
    }

    /**
     * Render printer controls for tile layout
     */
    renderTilePrinterControls(printer) {
        if (printer.status === 'printing') {
            return `
                <button class="btn-icon" onclick="printerManager.pausePrinter('${printer.id}')" title="${t('printers.pause')}">
                    ⏸️
                </button>
                <button class="btn-icon btn-error-icon" onclick="printerManager.stopPrinter('${printer.id}')" title="${t('printers.stop')}">
                    ⏹️
                </button>
            `;
        } else if (printer.status === 'paused') {
            return `
                <button class="btn-icon" onclick="printerManager.resumePrinter('${printer.id}')" title="${t('printers.resume')}">
                    ▶️
                </button>
                <button class="btn-icon btn-error-icon" onclick="printerManager.stopPrinter('${printer.id}')" title="${t('printers.stop')}">
                    ⏹️
                </button>
            `;
        }
        return '';
    }

    /**
     * Truncate job name for display
     */
    truncateJobName(jobName, maxLength) {
        if (jobName.length <= maxLength) return jobName;
        return jobName.substring(0, maxLength - 3) + '...';
    }

    /**
     * Render current job information
     */
    renderCurrentJobInfo(printer) {
        if (!printer.current_job) {
            return `<div class="info-item"><span class="text-muted">${t('printers.noActiveJob')}</span></div>`;
        }

        // Handle both old job object structure and new string job name structure
        const jobName = typeof printer.current_job === 'string' ? printer.current_job : printer.current_job.name;
        const jobStatus = printer.status === 'printing' ? 'printing' : 'idle';
        const status = getStatusConfig('job', jobStatus);

        return `
            <div class="current-job-info">
                <div class="info-item">
                    <label>${t('printers.currentJob')}:</label>
                    <span>${escapeHtml(jobName)}</span>
                </div>
                ${this.renderJobThumbnail(printer)}
                <div class="info-item">
                    <label>Status:</label>
                    <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
                </div>
                ${printer.progress !== undefined ? `
                    <div class="info-item">
                        <label>${t('printers.progress')}:</label>
                        <div class="inline-progress">
                            <div class="progress">
                                <div class="progress-bar" style="width: ${printer.progress}%"></div>
                            </div>
                            <span class="progress-text">${formatPercentage(printer.progress)}</span>
                        </div>
                    </div>
                ` : ''}
                ${printer.remaining_time_minutes ? `
                    <div class="info-item">
                        <label>${t('printers.remaining')}:</label>
                        <span>${formatDuration(printer.remaining_time_minutes * 60)}</span>
                    </div>
                ` : ''}
                ${printer.estimated_end_time ? `
                    <div class="info-item">
                        <label>${t('printers.end')}:</label>
                        <span>${formatTime(printer.estimated_end_time)}</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Render job thumbnail section for printers page
     */
    renderJobThumbnail(printer) {
        // Check if we have current job file data
        if (!printer.current_job_file_id) {
            // Show camera unavailable placeholder
            return `
                <div class="info-item">
                    <label>${t('printers.preview')}:</label>
                    <div class="job-thumbnail-info thumbnail-unavailable">
                        <div class="camera-placeholder">
                            <span class="camera-icon">📷</span>
                            <span class="camera-text">${t('printers.noPreview')}</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // Determine thumbnail source
        const thumbnailSrc = printer.current_job_has_thumbnail
            ? `${CONFIG.API_BASE_URL}/files/${printer.current_job_file_id}/thumbnail`
            : 'assets/placeholder-thumbnail.svg';

        return `
            <div class="info-item">
                <label>${t('printers.preview')}:</label>
                <div class="job-thumbnail-info">
                    <img src="${thumbnailSrc}"
                         alt="${printer.current_job_has_thumbnail ? 'Job Thumbnail' : t('printers.noPreviewAvailable')}"
                         class="thumbnail-image-small ${!printer.current_job_has_thumbnail ? 'placeholder-image' : ''}"
                         data-file-id="${printer.current_job_file_id}"
                         loading="lazy"
                         onclick="showFullThumbnail('${printer.current_job_file_id}', '${escapeHtml(printer.current_job || 'Current Job')}')"
                         ${printer.current_job_has_thumbnail ? `onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\\'camera-placeholder\\'><span class=\\'camera-icon\\'>📷</span><span class=\\'camera-text\\'>${t('printers.imageUnavailable')}</span></div>';"` : ''}>
                </div>
            </div>
        `;
    }

    /**
     * Render temperature information
     */
    renderTemperatureInfo(temperatures) {
        if (!temperatures) {
            return '';
        }
        
        const tempItems = [];
        
        if (temperatures.nozzle !== undefined) {
            const nozzle = typeof temperatures.nozzle === 'object' ? temperatures.nozzle : { current: temperatures.nozzle };
            tempItems.push(`
                <div class="info-item">
                    <label>${t('printers.nozzle')}:</label>
                    <span class="temperature ${Math.abs(nozzle.current - (nozzle.target || 0)) > 2 ? 'temp-heating' : ''}">
                        ${parseFloat(nozzle.current).toFixed(1)}°C${nozzle.target ? ` / ${parseFloat(nozzle.target).toFixed(1)}°C` : ''}
                    </span>
                </div>
            `);
        }
        
        if (temperatures.bed !== undefined) {
            const bed = typeof temperatures.bed === 'object' ? temperatures.bed : { current: temperatures.bed };
            tempItems.push(`
                <div class="info-item">
                    <label>${t('printers.bed')}:</label>
                    <span class="temperature ${Math.abs(bed.current - (bed.target || 0)) > 2 ? 'temp-heating' : ''}">
                        ${parseFloat(bed.current).toFixed(1)}°C${bed.target ? ` / ${parseFloat(bed.target).toFixed(1)}°C` : ''}
                    </span>
                </div>
            `);
        }
        
        if (temperatures.chamber !== undefined) {
            const chamber = typeof temperatures.chamber === 'object' ? temperatures.chamber : { current: temperatures.chamber };
            tempItems.push(`
                <div class="info-item">
                    <label>${t('printers.chamber')}:</label>
                    <span class="temperature">${parseFloat(chamber.current).toFixed(1)}°C</span>
                </div>
            `);
        }
        
        return tempItems.join('');
    }

    /**
     * Render printer statistics
     */
    renderPrinterStatistics(statistics) {
        if (!statistics) {
            return `<div class="info-item"><span class="text-muted">${t('printers.noStatisticsAvailable')}</span></div>`;
        }

        return `
            <div class="info-item">
                <label>${t('printers.jobs')}:</label>
                <span>${t('printers.jobsSuccess', { count: statistics.total_jobs, rate: formatPercentage(statistics.success_rate * 100) })}</span>
            </div>
            <div class="info-item">
                <label>${t('printers.printTime')}:</label>
                <span>${formatDuration(statistics.total_print_time)}</span>
            </div>
            <div class="info-item">
                <label>Material:</label>
                <span>${formatWeight(statistics.material_used_total * 1000)}</span>
            </div>
        `;
    }

    /**
     * Render printer action buttons
     */
    renderPrinterActionButtons(printer) {
        const buttons = [];
        
        // Test connection
        buttons.push(`
            <button class="btn btn-sm btn-secondary" onclick="printerManager.testConnection('${printer.id}')" title="${t('printers.testConnection')}">
                <span class="btn-icon">🔌</span>
                ${t('printers.testConnection')}
            </button>
        `);
        
        // Printer controls based on status
        if (printer.status === 'printing') {
            // Show pause and stop buttons when printing
            buttons.push(`
                <button class="btn btn-sm btn-warning" onclick="printerManager.pausePrint('${printer.id}')" title="${t('printers.pausePrint')}">
                    <span class="btn-icon">⏸️</span>
                    ${t('printers.pause')}
                </button>
                <button class="btn btn-sm btn-error" onclick="printerManager.stopPrint('${printer.id}')" title="${t('printers.stopPrint')}">
                    <span class="btn-icon">⏹️</span>
                    ${t('printers.stop')}
                </button>
                <button class="btn btn-sm btn-secondary" onclick="printerManager.downloadCurrentJob('${printer.id}')" title="${t('printers.downloadCurrentJobTitle')}">
                    <span class="btn-icon">🖼️</span>
                    ${t('printers.fetchThumbnail')}
                </button>
            `);
        } else if (printer.status === 'paused') {
            // Show resume and stop buttons when paused
            buttons.push(`
                <button class="btn btn-sm btn-success" onclick="printerManager.resumePrint('${printer.id}')" title="${t('printers.resumePrint')}">
                    <span class="btn-icon">▶️</span>
                    ${t('printers.resume')}
                </button>
                <button class="btn btn-sm btn-error" onclick="printerManager.stopPrint('${printer.id}')" title="${t('printers.stopPrint')}">
                    <span class="btn-icon">⏹️</span>
                    ${t('printers.stop')}
                </button>
            `);
        } else if (printer.status === 'online') {
            // Show generic control button when online but not printing
            buttons.push(`
                <button class="btn btn-sm btn-secondary" onclick="printerManager.showPrinterControl('${printer.id}')" title="${t('printers.controlPrinter')}">
                    <span class="btn-icon">🎮</span>
                    ${t('printers.control')}
                </button>
            `);
        }
        
        // View statistics
        buttons.push(`
            <button class="btn btn-sm btn-secondary" onclick="printerManager.showStatistics('${printer.id}')" title="${t('printers.showStatistics')}">
                <span class="btn-icon">📊</span>
                ${t('printers.statistics')}
            </button>
        `);
        
        return buttons.join('');
    }

    /**
     * Render empty printers state
     */
    renderEmptyPrintersState() {
        return `
            <div class="empty-state">
                <div class="empty-state-icon">🖨️</div>
                <h3>${t('printers.noneConfigured')}</h3>
                <p>${t('printers.addFirstPrinter')}</p>
                <button class="btn btn-primary" onclick="showAddPrinter()">
                    <span class="btn-icon">➕</span>
                    ${t('printers.addPrinter')}
                </button>
            </div>
        `;
    }

    /**
     * Render printers error state
     */
    renderPrintersError(error) {
        const message = error instanceof ApiError ? error.getUserMessage() : t('printers.loadFailed');

        return `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>${t('printers.loadError')}</h3>
                <p>${escapeHtml(message)}</p>
                <button class="btn btn-primary" onclick="printerManager.loadPrinters()">
                    <span class="btn-icon">🔄</span>
                    ${t('common.retry')}
                </button>
            </div>
        `;
    }

    /**
     * Setup form handlers
     */
    setupFormHandlers() {
        // Form handlers are managed by PrinterFormHandler in printer-form.js
        // No duplicate handlers needed here
    }

    /**
     * Show printer details modal
     */
    async showPrinterDetails(printerId) {
        try {
            // Fetch comprehensive printer details
            const data = await api.getPrinterDetails(printerId);

            // Create modal HTML
            const modalHtml = this.renderPrinterDetailsModal(data);

            // Remove existing modal if any
            const existingModal = document.getElementById('printerDetailsModal');
            if (existingModal) existingModal.remove();

            // Add modal to page
            document.body.insertAdjacentHTML('beforeend', modalHtml);

            // Show modal
            const modal = document.getElementById('printerDetailsModal');
            modal.style.display = 'flex';

            // Setup close handlers
            modal.querySelector('.btn-close').onclick = () => this.closePrinterDetailsModal();
            modal.onclick = (e) => {
                if (e.target === modal) this.closePrinterDetailsModal();
            };

            // Setup tab handlers
            modal.querySelectorAll('.tab-btn').forEach(btn => {
                btn.onclick = () => this.switchTab(btn.dataset.tab);
            });

        } catch (error) {
            Logger.error('Failed to load printer details:', error);
            showToast('error', t('common.error'), t('printers.detailsLoadFailed'));
        }
    }

    /**
     * Close printer details modal
     */
    closePrinterDetailsModal() {
        const modal = document.getElementById('printerDetailsModal');
        if (modal) modal.remove();
    }

    /**
     * Render printer details modal HTML
     */
    renderPrinterDetailsModal(data) {
        const { printer, connection, statistics, recent_jobs, current_status } = data;

        const statusIcon = this.getStatusIcon(printer.status);
        const connectionStatus = connection.is_connected ? `🟢 ${t('printers.connected')}` : `🔴 ${t('printers.disconnected')}`;
        const isPrinting = printer.status === 'printing';
        const isPaused = printer.status === 'paused';
        const canControl = connection.is_connected && (isPrinting || isPaused);

        return `
            <div id="printerDetailsModal" class="modal-overlay printer-details-modal">
                <div class="modal-content printer-details-content printer-details-enhanced">
                    <div class="modal-header">
                        <div class="modal-header-info">
                            <h2>${statusIcon} ${escapeHtml(printer.name)}</h2>
                            <span class="printer-type-badge">${this.formatPrinterType(printer.type)}</span>
                        </div>
                        <button class="btn-close">×</button>
                    </div>

                    <!-- Tab Navigation -->
                    <div class="modal-tabs">
                        <button class="tab-btn active" data-tab="overview">📊 ${t('printers.tabOverview')}</button>
                        <button class="tab-btn" data-tab="status">⚡ Status</button>
                        <button class="tab-btn" data-tab="history">📜 ${t('printers.tabHistory')}</button>
                        <button class="tab-btn" data-tab="diagnostics">🔧 ${t('printers.tabDiagnostics')}</button>
                    </div>

                    <div class="modal-body">
                        <!-- Overview Tab -->
                        <div class="tab-content active" data-tab="overview">
                            <!-- Statistics Cards -->
                            <div class="stats-grid stats-grid-4">
                                <div class="stat-card-small">
                                    <div class="stat-value">${statistics.total_jobs}</div>
                                    <div class="stat-label">${t('printers.jobsTotal')}</div>
                                </div>
                                <div class="stat-card-small stat-success">
                                    <div class="stat-value">${statistics.success_rate}%</div>
                                    <div class="stat-label">${t('printers.successRate')}</div>
                                </div>
                                <div class="stat-card-small">
                                    <div class="stat-value">${statistics.total_print_time_hours}h</div>
                                    <div class="stat-label">${t('printers.printTime')}</div>
                                </div>
                                <div class="stat-card-small">
                                    <div class="stat-value">${statistics.total_material_kg}kg</div>
                                    <div class="stat-label">${t('printers.materialUsed')}</div>
                                </div>
                            </div>

                            <!-- Printer Info Grid -->
                            <div class="details-section">
                                <h3>📋 ${t('printers.printerInformation')}</h3>
                                <div class="details-grid details-grid-2">
                                    <div class="detail-item">
                                        <span class="detail-label">Status</span>
                                        <span class="detail-value status-badge status-${printer.status}">${this.formatStatus(printer.status)}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">${t('printers.location')}</span>
                                        <span class="detail-value">${escapeHtml(printer.location) || '-'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">${t('printers.description')}</span>
                                        <span class="detail-value">${escapeHtml(printer.description) || '-'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">${t('printers.enabled')}</span>
                                        <span class="detail-value">${printer.is_enabled ? `✅ ${t('common.yes')}` : `❌ ${t('common.no')}`}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">${t('printers.created')}</span>
                                        <span class="detail-value">${printer.created_at ? new Date(printer.created_at).toLocaleDateString(getIntlLocale()) : '-'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">${t('printers.lastActivity')}</span>
                                        <span class="detail-value">${printer.last_seen ? new Date(printer.last_seen).toLocaleString(getIntlLocale()) : '-'}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Recent Jobs Preview -->
                            <div class="details-section">
                                <h3>📜 ${t('printers.recentJobs')}</h3>
                                ${recent_jobs.length > 0 ? `
                                <div class="recent-jobs-list">
                                    ${recent_jobs.slice(0, 3).map(job => `
                                        <div class="recent-job-item">
                                            <div class="job-info">
                                                <span class="job-name">${escapeHtml(job.file_name || t('common.unknown'))}</span>
                                                <span class="job-meta">${job.print_time_minutes ? this.formatMinutes(job.print_time_minutes) : ''} ${job.material_used ? `· ${job.material_used}g` : ''}</span>
                                            </div>
                                            <span class="job-status status-badge status-${job.status}">${this.formatJobStatus(job.status)}</span>
                                            <span class="job-date">${job.started_at ? new Date(job.started_at).toLocaleDateString(getIntlLocale()) : '-'}</span>
                                        </div>
                                    `).join('')}
                                </div>
                                <button class="btn btn-link" onclick="printerManager.switchTab('history')">${t('printers.showAllJobs')} →</button>
                                ` : `<p class="no-data">${t('printers.noJobs')}</p>`}
                            </div>
                        </div>

                        <!-- Status Tab -->
                        <div class="tab-content" data-tab="status">
                            ${current_status ? `
                            <!-- Current Job Section -->
                            <div class="details-section current-job-section">
                                <h3>🖨️ ${t('printers.currentPrintJob')}</h3>
                                ${current_status.current_job ? `
                                <div class="current-job-card">
                                    <div class="job-header">
                                        <span class="job-name-large">${escapeHtml(current_status.current_job)}</span>
                                        <span class="job-progress-value">${current_status.progress || 0}%</span>
                                    </div>
                                    <div class="progress-bar-container">
                                        <div class="progress-bar" style="width: ${current_status.progress || 0}%"></div>
                                    </div>
                                    ${current_status.remaining_time ? `
                                    <div class="job-time-info">
                                        <span>⏱️ ${t('printers.remaining')}: ${this.formatMinutes(current_status.remaining_time)}</span>
                                    </div>
                                    ` : ''}

                                    <!-- Printer Controls -->
                                    ${canControl ? `
                                    <div class="printer-controls">
                                        ${isPrinting ? `
                                            <button class="btn btn-warning" onclick="printerManager.pausePrinter('${printer.id}')">
                                                ⏸️ ${t('printers.pause')}
                                            </button>
                                        ` : ''}
                                        ${isPaused ? `
                                            <button class="btn btn-success" onclick="printerManager.resumePrinter('${printer.id}')">
                                                ▶️ ${t('printers.resume')}
                                            </button>
                                        ` : ''}
                                        <button class="btn btn-danger" onclick="printerManager.stopPrinter('${printer.id}')">
                                            ⏹️ ${t('common.cancel')}
                                        </button>
                                    </div>
                                    ` : ''}
                                </div>
                                ` : `<p class="no-active-job">${t('printers.noActivePrintJob')}</p>`}
                            </div>

                            <!-- Temperature Section -->
                            ${current_status.temperatures ? `
                            <div class="details-section">
                                <h3>🌡️ ${t('printers.temperatures')}</h3>
                                <div class="temperature-grid">
                                    <div class="temp-card">
                                        <div class="temp-icon">🛏️</div>
                                        <div class="temp-info">
                                            <span class="temp-label">${t('printers.printBed')}</span>
                                            <span class="temp-value ${this.getTempClass(current_status.temperatures.bed)}">
                                                ${current_status.temperatures.bed.current || 0}°C
                                            </span>
                                            <span class="temp-target">${t('printers.target')}: ${current_status.temperatures.bed.target || 0}°C</span>
                                        </div>
                                    </div>
                                    <div class="temp-card">
                                        <div class="temp-icon">🔥</div>
                                        <div class="temp-info">
                                            <span class="temp-label">${t('printers.nozzle')}</span>
                                            <span class="temp-value ${this.getTempClass(current_status.temperatures.nozzle)}">
                                                ${current_status.temperatures.nozzle.current || 0}°C
                                            </span>
                                            <span class="temp-target">${t('printers.target')}: ${current_status.temperatures.nozzle.target || 0}°C</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            ` : ''}

                            <!-- Filament Section -->
                            ${current_status.filaments && current_status.filaments.length > 0 ? `
                            <div class="details-section">
                                <h3>🧵 Filament</h3>
                                <div class="filament-slots">
                                    ${current_status.filaments.map(f => `
                                        <div class="filament-slot ${f.is_active ? 'active' : ''}">
                                            <div class="filament-color" style="background-color: ${f.color || '#ccc'}"></div>
                                            <div class="filament-info">
                                                <span class="filament-slot-num">Slot ${f.slot === 254 ? 'Ext' : f.slot + 1}</span>
                                                <span class="filament-type">${f.type || t('common.unknown')}</span>
                                            </div>
                                            ${f.is_active ? `<span class="filament-active-badge">${t('printers.active')}</span>` : ''}
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            ` : ''}
                            ` : `<p class="no-data">${t('printers.statusUnavailable')}</p>`}
                        </div>

                        <!-- History Tab -->
                        <div class="tab-content" data-tab="history">
                            <div class="details-section">
                                <h3>📜 ${t('printers.printHistory')}</h3>
                                ${recent_jobs.length > 0 ? `
                                <div class="job-history-table">
                                    <div class="job-history-header">
                                        <span>${t('printers.file')}</span>
                                        <span>Status</span>
                                        <span>${t('printers.duration')}</span>
                                        <span>Material</span>
                                        <span>${t('printers.date')}</span>
                                    </div>
                                    ${recent_jobs.map(job => `
                                        <div class="job-history-row">
                                            <span class="job-filename" title="${escapeHtml(job.file_name || t('common.unknown'))}">${escapeHtml(job.file_name || t('common.unknown'))}</span>
                                            <span class="job-status status-badge status-${job.status}">${this.formatJobStatus(job.status)}</span>
                                            <span>${job.print_time_minutes ? this.formatMinutes(job.print_time_minutes) : '-'}</span>
                                            <span>${job.material_used ? `${job.material_used}g` : '-'}</span>
                                            <span>${job.started_at ? new Date(job.started_at).toLocaleString(getIntlLocale()) : '-'}</span>
                                        </div>
                                    `).join('')}
                                </div>
                                ` : `<p class="no-data">${t('printers.noJobs')}</p>`}
                            </div>
                        </div>

                        <!-- Diagnostics Tab -->
                        <div class="tab-content" data-tab="diagnostics">
                            <div class="details-section">
                                <h3>🔌 ${t('printers.connectionDetails')}</h3>
                                <div class="details-grid details-grid-2">
                                    <div class="detail-item">
                                        <span class="detail-label">${t('printers.connectionStatus')}</span>
                                        <span class="detail-value">${connectionStatus}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">${t('printers.protocol')}</span>
                                        <span class="detail-value">${connection.connection_type.toUpperCase()}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">${t('printers.ipAddress')}</span>
                                        <span class="detail-value">${connection.ip_address}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">${t('printers.lastSeen')}</span>
                                        <span class="detail-value">${connection.last_seen ? new Date(connection.last_seen).toLocaleString(getIntlLocale()) : '-'}</span>
                                    </div>
                                    ${connection.firmware_version ? `
                                    <div class="detail-item">
                                        <span class="detail-label">${t('printers.firmwareVersion')}</span>
                                        <span class="detail-value">${connection.firmware_version}</span>
                                    </div>
                                    ` : ''}
                                    ${connection.uptime ? `
                                    <div class="detail-item">
                                        <span class="detail-label">${t('printers.uptime')}</span>
                                        <span class="detail-value">${this.formatUptime(connection.uptime)}</span>
                                    </div>
                                    ` : ''}
                                </div>
                            </div>

                            <div class="details-section">
                                <h3>🔧 ${t('printers.diagnosticsActions')}</h3>
                                <div class="diagnostics-actions">
                                    <button class="btn btn-secondary" onclick="printerManager.testConnection('${printer.id}')">
                                        🔍 ${t('printers.testConnection')}
                                    </button>
                                    <button class="btn btn-secondary" onclick="printerManager.reconnectPrinter('${printer.id}')">
                                        🔄 ${t('printers.reconnect')}
                                    </button>
                                    <button class="btn btn-secondary" onclick="printerManager.refreshPrinterFiles('${printer.id}')">
                                        📁 ${t('printers.refreshFiles')}
                                    </button>
                                </div>
                            </div>

                            <div class="details-section">
                                <h3>ℹ️ ${t('printers.systemInformation')}</h3>
                                <div class="system-info">
                                    <p><strong>${t('printers.printerId')}:</strong> <code>${printer.id}</code></p>
                                    <p><strong>${t('printers.serialNumber')}:</strong> <code>${printer.serial_number || 'N/A'}</code></p>
                                    <p><strong>${t('printers.printerType')}:</strong> ${this.formatPrinterType(printer.type)}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="printerManager.closePrinterDetailsModal()">${t('common.close')}</button>
                        <button class="btn btn-primary" onclick="printerManager.closePrinterDetailsModal(); printerManager.editPrinter('${printer.id}')">✏️ ${t('common.edit')}</button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Switch tab in printer details modal
     */
    switchTab(tabName) {
        const modal = document.getElementById('printerDetailsModal');
        if (!modal) return;

        // Update tab buttons
        modal.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab content
        modal.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.dataset.tab === tabName);
        });
    }

    /**
     * Get temperature CSS class based on current vs target
     */
    getTempClass(temp) {
        if (!temp || !temp.target || temp.target === 0) return '';
        const diff = Math.abs((temp.current || 0) - temp.target);
        if (diff <= 2) return 'temp-at-target';
        if (temp.current < temp.target) return 'temp-heating';
        return 'temp-cooling';
    }

    /**
     * Format uptime in human readable format
     */
    formatUptime(seconds) {
        if (!seconds) return '-';
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        if (days > 0) return `${days}d ${hours}h`;
        if (hours > 0) return `${hours}h ${mins}m`;
        return `${mins}m`;
    }

    /**
     * Format status for display
     */
    formatStatus(status) {
        const labels = {
            'online': t('status.printer.online'),
            'offline': t('status.printer.offline'),
            'printing': t('status.printer.printing'),
            'paused': t('status.job.paused'),
            'idle': t('status.printer.idle'),
            'error': t('status.printer.error')
        };
        return labels[status] || status;
    }

    /**
     * Format job status for display
     */
    formatJobStatus(status) {
        const labels = {
            'pending': t('status.job.pending'),
            'running': t('status.job.running'),
            'printing': t('status.job.printing'),
            'completed': t('status.job.completed'),
            'failed': t('status.job.failed'),
            'cancelled': t('status.job.cancelled'),
            'paused': t('status.job.paused')
        };
        return labels[status] || status;
    }

    /**
     * Pause a printing job
     */
    async pausePrinter(printerId) {
        try {
            await api.pausePrinter(printerId);
            showToast('success', t('common.success'), t('printers.printPaused'));
            this.showPrinterDetails(printerId); // Refresh modal
        } catch (error) {
            Logger.error('Failed to pause printer:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('printers.printPauseFailed');
            showToast('error', t('common.error'), message);
        }
    }

    /**
     * Resume a paused job
     */
    async resumePrinter(printerId) {
        try {
            await api.resumePrinter(printerId);
            showToast('success', t('common.success'), t('printers.printResuming'));
            this.showPrinterDetails(printerId); // Refresh modal
        } catch (error) {
            Logger.error('Failed to resume printer:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('printers.printResumeFailed');
            showToast('error', t('common.error'), message);
        }
    }

    /**
     * Stop/cancel a job
     */
    async stopPrinter(printerId) {
        if (!confirm(t('printers.cancelJobConfirm'))) return;

        try {
            await api.stopPrinter(printerId);
            showToast('success', t('common.success'), t('printers.jobCancelled'));
            this.showPrinterDetails(printerId); // Refresh modal
        } catch (error) {
            Logger.error('Failed to stop printer:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('printers.jobCancelFailed');
            showToast('error', t('common.error'), message);
        }
    }

    /**
     * Test connection to printer
     */
    async testConnection(printerId) {
        showToast('info', t('printers.connectionTest'), t('printers.testingConnection'));
        try {
            await api.getPrinterStatus(printerId);
            showToast('success', t('common.success'), t('printers.connectionSuccessful'));
        } catch (error) {
            showToast('warning', t('common.warning'), t('printers.printerNotResponding'));
        }
    }

    /**
     * Reconnect to printer
     */
    async reconnectPrinter(printerId) {
        showToast('info', t('printers.connection'), t('printers.reconnecting'));
        try {
            await api.disconnectPrinter(printerId);
            await new Promise(resolve => setTimeout(resolve, 1000));
            await api.connectPrinter(printerId);
            showToast('success', t('common.success'), t('printers.reconnected'));
            this.showPrinterDetails(printerId); // Refresh modal
        } catch (error) {
            const message = error instanceof ApiError ? error.getUserMessage() : t('printers.connectionFailed');
            showToast('error', t('common.error'), message);
        }
    }

    /**
     * Refresh printer files
     */
    async refreshPrinterFiles(printerId) {
        showToast('info', t('printers.files'), t('printers.refreshingFiles'));
        try {
            const data = await api.getPrinterFiles(printerId);
            showToast('success', t('common.success'), t('printers.filesFound', { count: data.files?.length || 0 }));
        } catch (error) {
            const message = error instanceof ApiError ? error.getUserMessage() : t('printers.fileRefreshFailed');
            showToast('error', t('common.error'), message);
        }
    }

    /**
     * Get status icon for printer
     */
    getStatusIcon(status) {
        const icons = {
            'online': '🟢',
            'offline': '🔴',
            'printing': '🖨️',
            'idle': '💤',
            'error': '⚠️',
            'paused': '⏸️'
        };
        return icons[status] || '❓';
    }

    /**
     * Format printer type for display
     */
    formatPrinterType(type) {
        const types = {
            'bambu_lab': 'Bambu Lab',
            'prusa': 'Prusa'
        };
        return types[type] || type;
    }

    /**
     * Format minutes to readable string
     */
    formatMinutes(minutes) {
        if (!minutes) return '-';
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        if (hours > 0) {
            return `${hours}h ${mins}min`;
        }
        return `${mins}min`;
    }

    /**
     * Edit printer configuration
     */
    async editPrinter(printerId) {
        try {
            // Get printer data from API
            const printer = await api.getPrinter(printerId);
            
            // Populate edit form with printer data
            if (typeof printerFormHandler !== 'undefined' && printerFormHandler.populateEditForm) {
                printerFormHandler.populateEditForm(printer);
            }
            
            // Show edit modal
            showModal('editPrinterModal');
            
        } catch (error) {
            Logger.error('Failed to load printer for editing:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('printers.printerDataLoadFailed');
            showToast('error', t('common.error'), message);
        }
    }

    /**
     * Delete printer
     */
    async deletePrinter(printerId) {
        const printer = this.printers.get(printerId);
        if (!printer) return;

        const confirmed = confirm(t('printers.deleteConfirm', { name: printer.data.name }));
        if (!confirmed) return;

        try {
            await api.deletePrinter(printerId);
            showToast('success', t('common.success'), CONFIG.SUCCESS_MESSAGES.PRINTER_REMOVED);
            this.loadPrinters();
        } catch (error) {
            // If blocked by active/stale jobs, offer force deletion
            if (error instanceof ApiError && error.status === 409) {
                const forceConfirmed = confirm(
                    `${error.message}\n\n${t('printers.forceDeleteConfirm')}`
                );
                if (forceConfirmed) {
                    try {
                        await api.deletePrinter(printerId, { force: true });
                        showToast('success', t('common.success'), CONFIG.SUCCESS_MESSAGES.PRINTER_REMOVED);
                        this.loadPrinters();
                        return;
                    } catch (forceError) {
                        Logger.error('Failed to force-delete printer:', forceError);
                        const message = forceError instanceof ApiError ? forceError.getUserMessage() : t('printers.deleteFailed');
                        showToast('error', t('common.error'), message);
                        return;
                    }
                }
                return;
            }
            Logger.error('Failed to delete printer:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('printers.deleteFailed');
            showToast('error', t('common.error'), message);
        }
    }

    /**
     * Test printer connection
     */
    async testConnection(printerId) {
        try {
            showToast('info', t('printers.connectionTest'), t('printers.testingPrinterConnection'));
            
            // Get fresh printer status
            const printer = await api.getPrinter(printerId);
            
            if (printer.status === 'online') {
                showToast('success', t('printers.connectionOk'), t('printers.printerReachable', { name: printer.name }));
            } else {
                showToast('warning', t('printers.connectionFailed'), t('printers.printerNotReachable', { name: printer.name }));
            }
            
        } catch (error) {
            Logger.error('Connection test failed:', error);
            showToast('error', t('printers.connectionError'), t('printers.connectionTestFailed'));
        }
    }

    /**
     * Show printer control interface
     */
    showPrinterControl(printerId) {
        showToast('info', t('printers.printerControl'), t('printers.controlHint'));
    }
    
    /**
     * Pause print job
     */
    async pausePrint(printerId) {
        const printer = this.printers.get(printerId);
        if (!printer) return;
        
        const confirmed = confirm(t('printers.pauseConfirm', { name: printer.data.name }));
        if (!confirmed) return;
        
        try {
            showToast('info', t('printers.pause'), t('printers.pausingJob'));
            
            await api.pausePrinter(printerId);
            showToast('success', t('common.success'), t('printers.jobPaused'));
            
            // Refresh printer status
            this.refreshPrinters();
            
        } catch (error) {
            Logger.error('Failed to pause print:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('printers.jobPauseFailed');
            showToast('error', t('common.error'), message);
        }
    }
    
    /**
     * Resume print job
     */
    async resumePrint(printerId) {
        const printer = this.printers.get(printerId);
        if (!printer) return;
        
        const confirmed = confirm(t('printers.resumeConfirm', { name: printer.data.name }));
        if (!confirmed) return;
        
        try {
            showToast('info', t('printers.resume'), t('printers.resumingJob'));
            
            await api.resumePrinter(printerId);
            showToast('success', t('common.success'), t('printers.jobResumed'));
            
            // Refresh printer status
            this.refreshPrinters();
            
        } catch (error) {
            Logger.error('Failed to resume print:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('printers.jobResumeFailed');
            showToast('error', t('common.error'), message);
        }
    }
    
    /**
     * Stop print job
     */
    async stopPrint(printerId) {
        const printer = this.printers.get(printerId);
        if (!printer) return;
        
        const confirmed = confirm(t('printers.stopConfirm', { name: printer.data.name }));
        if (!confirmed) return;
        
        try {
            showToast('info', t('printers.stop'), t('printers.stoppingJob'));
            
            await api.stopPrinter(printerId);
            showToast('success', t('common.success'), t('printers.jobStopped'));
            
            // Refresh printer status
            this.refreshPrinters();
            
        } catch (error) {
            Logger.error('Failed to stop print:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('printers.jobStopFailed');
            showToast('error', t('common.error'), message);
        }
    }

    /**
     * Manually trigger download & processing of the currently printing job file
     */
    async downloadCurrentJob(printerId) {
        const printer = this.printers.get(printerId);
        if (!printer) return;
        try {
            showToast('info', t('printers.thumbnail'), t('printers.downloadingCurrentFile'));
            const result = await api.downloadCurrentJobFile(printerId);
            const status = result.status || t('common.unknown');
            if (status === 'exists_with_thumbnail' || status === 'processed' || status === 'success') {
                showToast('success', t('printers.thumbnail'), t('printers.thumbnailReady'));
            } else if (status === 'not_printing') {
                showToast('warning', t('printers.noPrint'), t('printers.noActiveJobMessage'));
            } else if (status === 'exists_no_thumbnail') {
                showToast('info', t('printers.noPreview'), t('printers.noEmbeddedThumbnail'));
            } else {
                showToast('info', 'Status', `Status: ${status}`);
            }
            // Refresh printers to get updated thumbnail/file id flags
            this.refreshPrinters();
        } catch (error) {
            Logger.error('Failed to download current job file:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : t('printers.currentFileDownloadFailed');
            showToast('error', t('common.error'), message);
        }
    }

    /**
     * Show printer statistics
     */
    async showStatistics(printerId) {
        try {
            const stats = await api.getPrinterStatistics(printerId);
            
            // Create simple statistics display (placeholder)
            const message = t('printers.statisticsMessage', {
                jobs: stats.jobs.total_jobs,
                successRate: formatPercentage(stats.jobs.success_rate * 100),
                uptime: formatDuration(stats.uptime.active_hours * 3600),
                material: formatWeight(stats.materials.total_used_kg * 1000)
            });
            
            showToast('info', t('printers.printerStatistics'), message);
            
        } catch (error) {
            Logger.error('Failed to load printer statistics:', error);
            showToast('error', t('common.error'), t('printers.statisticsLoadFailed'));
        }
    }

    /**
     * Start auto-refresh interval
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            if (window.currentPage === 'printers') {
                this.refreshPrinters();
            }
        }, CONFIG.PRINTER_STATUS_INTERVAL);
    }

    /**
     * Refresh printer status
     */
    async refreshPrinters() {
        try {
            const response = await api.getPrinters(this.currentFilters);
            
            if (response.printers) {
                response.printers.forEach(printer => {
                    const printerInfo = this.printers.get(printer.id);
                    if (printerInfo) {
                        // Update printer data
                        printerInfo.data = printer;
                        
                        // Update card element
                        const newCard = this.createPrinterManagementCard(printer);
                        printerInfo.element.parentNode.replaceChild(newCard, printerInfo.element);
                        printerInfo.element = newCard;
                    }
                });
            }
        } catch (error) {
            Logger.error('Failed to refresh printers:', error);
        }
    }

    /**
     * Setup WebSocket listeners
     */
    setupWebSocketListeners() {
        // Listen for printer status updates
        document.addEventListener('printerStatusUpdate', (event) => {
            const data = event.detail;
            const printerInfo = this.printers.get(data.printer_id);
            
            if (printerInfo) {
                // Update printer data
                printerInfo.data = { ...printerInfo.data, ...data };
                
                // Update card element
                const newCard = this.createPrinterManagementCard(printerInfo.data);
                printerInfo.element.parentNode.replaceChild(newCard, printerInfo.element);
                printerInfo.element = newCard;
            }
        });
    }
}

// Global printer manager instance
const printerManager = new PrinterManager();

/**
 * Global functions for printer management
 */

/**
 * Refresh printers list
 */
function refreshPrinters() {
    printerManager.loadPrinters();
}

/**
 * Discover printers on the network
 */
async function discoverPrinters() {
    const discoveredSection = document.getElementById('discoveredPrintersSection');
    const discoveredList = document.getElementById('discoveredPrintersList');
    const discoverButton = document.getElementById('discoverButton');
    const interfaceSelect = document.getElementById('networkInterfaceSelect');

    if (!discoveredSection || !discoveredList) return;

    try {
        // Show the discovered section
        discoveredSection.style.display = 'block';

        // Show loading state
        discoveredList.innerHTML = `
            <div class="loading-placeholder">
                <div class="spinner"></div>
                <p>${t('printers.searchingNetwork')}</p>
            </div>
        `;

        // Disable discover button
        if (discoverButton) {
            discoverButton.disabled = true;
            discoverButton.innerHTML = `<span class="btn-icon">⏳</span> ${t('printers.searchRunning')}`;
        }

        // Get selected interface (if any)
        const selectedInterface = interfaceSelect ? interfaceSelect.value : null;

        // Call discovery API
        const params = {};
        if (selectedInterface) {
            params.interface = selectedInterface;
        }

        const response = await api.discoverPrinters(params);

        // Display results
        if (response.discovered && response.discovered.length > 0) {
            discoveredList.innerHTML = '';

            // Show all discovered printers (including already added ones with their status)
            response.discovered.forEach(printer => {
                const printerCard = createDiscoveredPrinterCard(printer);
                discoveredList.appendChild(printerCard);
            });

            // Count new printers (not already added)
            const newCount = response.discovered.filter(p => !p.already_added).length;
            const totalCount = response.discovered.length;

            // Show success message with proper counts
            if (newCount > 0) {
                showNotification(t('printers.discoveredNew', { count: newCount, total: totalCount, duration: response.scan_duration_ms }), 'success');
            } else {
                showNotification(t('printers.discoveredAllAdded', { total: totalCount, duration: response.scan_duration_ms }), 'info');
            }
        } else {
            discoveredList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <h3>${t('printers.noPrintersFound')}</h3>
                    <p>${t('printers.noPrintersFoundMessage')}</p>
                    <p class="text-sm text-muted">${t('printers.makeSure')}</p>
                    <ul class="text-sm text-muted" style="text-align: left; max-width: 400px; margin: 10px auto;">
                        <li>${t('printers.checkPowered')}</li>
                        <li>${t('printers.checkSameNetwork')}</li>
                        <li>${t('printers.checkHostNetwork')}</li>
                    </ul>
                </div>
            `;
        }

        // Show errors if any
        if (response.errors && response.errors.length > 0) {
            Logger.warn('Discovery errors:', response.errors);
            response.errors.forEach(error => {
                showNotification(error, 'warning');
            });
        }

    } catch (error) {
        Logger.error('Failed to discover printers:', error);
        discoveredList.innerHTML = `
            <div class="error-state">
                <div class="error-icon">⚠️</div>
                <h3>${t('printers.searchFailedTitle')}</h3>
                <p>${escapeHtml(error.message || t('printers.unknownError'))}</p>
            </div>
        `;
        showNotification(t('printers.searchFailed'), 'error');
    } finally {
        // Re-enable discover button
        if (discoverButton) {
            discoverButton.disabled = false;
            discoverButton.innerHTML = `<span class="btn-icon">🔍</span> ${t('printers.searchPrinters')}`;
        }
    }
}

/**
 * Create a card for a discovered printer
 */
function createDiscoveredPrinterCard(printer) {
    const card = document.createElement('div');
    card.className = `card discovered-printer-card ${printer.already_added ? 'already-added' : ''}`;

    // Manufacturer icon and badge
    const manufacturerIcon = printer.type === 'bambu' ?
        '<img src="/assets/bambu-icon.svg" class="manufacturer-icon" alt="Bambu Lab" title="Bambu Lab">' :
        '<img src="/assets/prusa-icon.svg" class="manufacturer-icon" alt="Prusa" title="Prusa">';

    const typeBadge = printer.type === 'bambu' ?
        '<span class="badge badge-bambu"><img src="/assets/bambu-icon.svg" class="badge-icon" alt="">Bambu Lab</span>' :
        '<span class="badge badge-prusa"><img src="/assets/prusa-icon.svg" class="badge-icon" alt="">Prusa</span>';

    const statusBadge = printer.already_added ?
        `<span class="badge badge-secondary">${t('printers.alreadyAdded')}</span>` :
        `<span class="badge badge-success">${t('printers.newlyFound')}</span>`;

    card.innerHTML = `
        <div class="card-header">
            <div class="printer-title">
                <div class="printer-title-with-icon">
                    ${manufacturerIcon}
                    <h3>${escapeHtml(printer.name || printer.hostname || printer.ip)}</h3>
                </div>
                <div class="printer-badges">
                    ${typeBadge}
                    ${statusBadge}
                </div>
            </div>
        </div>
        <div class="card-body">
            <div class="printer-info">
                <div class="info-row">
                    <span class="label">${t('printers.ipAddress')}:</span>
                    <span class="value">${escapeHtml(printer.ip)}</span>
                </div>
                <div class="info-row">
                    <span class="label">Hostname:</span>
                    <span class="value">${escapeHtml(printer.hostname)}</span>
                </div>
                ${printer.model ? `
                <div class="info-row">
                    <span class="label">${t('printers.model')}:</span>
                    <span class="value">${escapeHtml(printer.model)}</span>
                </div>
                ` : ''}
            </div>
        </div>
        <div class="card-footer">
            ${!printer.already_added ? `
                <button class="btn btn-primary" onclick="addDiscoveredPrinter('${sanitizeAttribute(printer.ip)}', '${sanitizeAttribute(printer.type)}', '${sanitizeAttribute(printer.name || printer.hostname)}')">
                    <span class="btn-icon">➕</span>
                    ${t('common.add')}
                </button>
            ` : `
                <button class="btn btn-secondary" disabled>
                    <span class="btn-icon">✓</span>
                    ${t('printers.alreadyConfigured')}
                </button>
            `}
        </div>
    `;

    return card;
}

/**
 * Add a discovered printer
 */
function addDiscoveredPrinter(ipAddress, type, name) {
    // Show the add printer modal
    showModal('addPrinterModal');

    // Wait for modal to be shown, then fill the form
    setTimeout(() => {
        const nameInput = document.getElementById('printerName');
        const typeSelect = document.getElementById('printerType');
        const ipInput = document.getElementById('printerIP');

        // Fill in the discovered printer information
        if (nameInput) {
            nameInput.value = name || '';
        }

        if (ipInput) {
            ipInput.value = ipAddress || '';
        }

        if (typeSelect) {
            // Map discovery type to form type
            const formType = type === 'bambu' ? 'bambu_lab' : 'prusa_core';
            typeSelect.value = formType;

            // Trigger change event to show printer-specific fields
            typeSelect.dispatchEvent(new Event('change', { bubbles: true }));

            Logger.debug('Pre-filled discovered printer:', {
                name: name,
                ip: ipAddress,
                type: formType
            });
        }
    }, 150); // Slightly longer delay to ensure modal is fully rendered
}

/**
 * Load network interfaces for discovery
 */
async function loadNetworkInterfaces() {
    try {
        const interfaceSelect = document.getElementById('networkInterfaceSelect');
        if (!interfaceSelect) return;

        const response = await api.getNetworkInterfaces();

        if (response.interfaces && response.interfaces.length > 0) {
            // Clear existing options except auto-detect
            interfaceSelect.innerHTML = `<option value="">${t('printers.autoDetect')}</option>`;

            // Add interfaces
            response.interfaces.forEach(iface => {
                const option = document.createElement('option');
                option.value = iface.name;
                option.textContent = `${iface.name} (${iface.ip})${iface.is_default ? ` - ${t('printers.defaultInterface')}` : ''}`;
                if (iface.is_default) {
                    option.selected = false; // Keep auto-detect selected by default
                }
                interfaceSelect.appendChild(option);
            });
        }
    } catch (error) {
        Logger.error('Failed to load network interfaces:', error);
    }
}

// Load network interfaces when printer page is shown
document.addEventListener('DOMContentLoaded', () => {
    if (window.currentPage === 'printers') {
        loadNetworkInterfaces();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PrinterManager, printerManager };
}