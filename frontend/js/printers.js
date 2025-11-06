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
        console.log('Initializing printer management');
        
        // Load printers
        this.loadPrinters();
        
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
            
            if (response && Array.isArray(response) && response.length > 0) {
                // Create printer cards
                response.forEach(printer => {
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
            console.error('Failed to load printers:', error);
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
        card.className = `card printer-management-card status-${printer.status}`;
        card.setAttribute('data-printer-id', printer.id);
        
        const status = getStatusConfig('printer', printer.status);
        const printerType = CONFIG.PRINTER_TYPES[printer.printer_type] || { label: printer.printer_type, color: '#6b7280' };
        
        card.innerHTML = `
            <div class="card-header">
                <div class="printer-title">
                    <h3>${escapeHtml(printer.name)}</h3>
                    <div class="printer-meta">
                        <span class="printer-type" style="background-color: ${printerType.color};">
                            ${printerType.label}
                        </span>
                        <span class="status-badge ${status.class}">
                            ${status.icon} ${status.label}
                        </span>
                    </div>
                </div>
                <div class="printer-actions">
                    <button class="btn btn-sm btn-secondary" onclick="printerManager.showPrinterDetails('${printer.id}')" title="Details anzeigen">
                        <span class="btn-icon">👁️</span>
                        Details
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="printerManager.editPrinter('${printer.id}')" title="Bearbeiten">
                        <span class="btn-icon">✏️</span>
                        Bearbeiten
                    </button>
                    <button class="btn btn-sm btn-error" onclick="printerManager.deletePrinter('${printer.id}')" title="Löschen">
                        <span class="btn-icon">🗑️</span>
                    </button>
                </div>
            </div>
            
            <div class="card-body">
                <div class="printer-info-grid">
                    <div class="info-section">
                        <h4>Verbindung</h4>
                        <div class="info-item">
                            <label>IP-Adresse:</label>
                            <span>${escapeHtml(printer.ip_address)}</span>
                        </div>
                        <div class="info-item">
                            <label>Letzte Verbindung:</label>
                            <span>${printer.last_seen ? formatDateTime(printer.last_seen) : 'Nie'}</span>
                        </div>
                        <div class="info-item">
                            <label>Firmware:</label>
                            <span>${printer.firmware_version || 'Unbekannt'}</span>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <h4>Status</h4>
                        ${this.renderCurrentJobInfo(printer)}
                        ${this.renderTemperatureInfo(printer.temperatures)}
                    </div>
                    
                    ${cameraManager ? cameraManager.renderCameraSection(printer) : ''}
                    
                    <div class="info-section">
                        <h4>Statistiken</h4>
                        ${this.renderPrinterStatistics(printer.statistics)}
                    </div>
                    
                    <div class="info-section">
                        <h4>Aktionen</h4>
                        <div class="action-buttons">
                            ${this.renderPrinterActionButtons(printer)}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return card;
    }

    /**
     * Render current job information
     */
    renderCurrentJobInfo(printer) {
        if (!printer.current_job) {
            return '<div class="info-item"><span class="text-muted">Kein aktiver Auftrag</span></div>';
        }

        // Handle both old job object structure and new string job name structure
        const jobName = typeof printer.current_job === 'string' ? printer.current_job : printer.current_job.name;
        const jobStatus = printer.status === 'printing' ? 'printing' : 'idle';
        const status = getStatusConfig('job', jobStatus);

        return `
            <div class="current-job-info">
                <div class="info-item">
                    <label>Aktueller Auftrag:</label>
                    <span>${escapeHtml(jobName)}</span>
                </div>
                ${this.renderJobThumbnail(printer)}
                <div class="info-item">
                    <label>Status:</label>
                    <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
                </div>
                ${printer.progress !== undefined ? `
                    <div class="info-item">
                        <label>Fortschritt:</label>
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
                        <label>Verbleibend:</label>
                        <span>${formatDuration(printer.remaining_time_minutes * 60)}</span>
                    </div>
                ` : ''}
                ${printer.estimated_end_time ? `
                    <div class="info-item">
                        <label>Ende:</label>
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
            return '';
        }

        // Determine thumbnail source
        const thumbnailSrc = printer.current_job_has_thumbnail
            ? `/api/v1/files/${printer.current_job_file_id}/thumbnail`
            : 'assets/placeholder-thumbnail.svg';

        return `
            <div class="info-item">
                <label>Vorschau:</label>
                <div class="job-thumbnail-info">
                    <img src="${thumbnailSrc}"
                         alt="${printer.current_job_has_thumbnail ? 'Job Thumbnail' : 'Keine Vorschau verfügbar'}"
                         class="thumbnail-image-small ${!printer.current_job_has_thumbnail ? 'placeholder-image' : ''}"
                         data-file-id="${printer.current_job_file_id}"
                         loading="lazy"
                         onclick="showFullThumbnail('${printer.current_job_file_id}', '${escapeHtml(printer.current_job || 'Current Job')}')"
                         ${printer.current_job_has_thumbnail ? "onerror=\"this.src='assets/placeholder-thumbnail.svg'; this.onerror=null; this.classList.add('placeholder-image');\"" : ''}>
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
                    <label>Düse:</label>
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
                    <label>Bett:</label>
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
                    <label>Kammer:</label>
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
            return '<div class="info-item"><span class="text-muted">Keine Statistiken verfügbar</span></div>';
        }
        
        return `
            <div class="info-item">
                <label>Aufträge:</label>
                <span>${statistics.total_jobs} (${formatPercentage(statistics.success_rate * 100)} Erfolg)</span>
            </div>
            <div class="info-item">
                <label>Druckzeit:</label>
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
            <button class="btn btn-sm btn-secondary" onclick="printerManager.testConnection('${printer.id}')" title="Verbindung testen">
                <span class="btn-icon">🔌</span>
                Verbindung testen
            </button>
        `);
        
        // Printer controls based on status
        if (printer.status === 'printing') {
            // Show pause and stop buttons when printing
            buttons.push(`
                <button class="btn btn-sm btn-warning" onclick="printerManager.pausePrint('${printer.id}')" title="Druck pausieren">
                    <span class="btn-icon">⏸️</span>
                    Pausieren
                </button>
                <button class="btn btn-sm btn-error" onclick="printerManager.stopPrint('${printer.id}')" title="Druck stoppen">
                    <span class="btn-icon">⏹️</span>
                    Stoppen
                </button>
                <button class="btn btn-sm btn-secondary" onclick="printerManager.downloadCurrentJob('${printer.id}')" title="Aktuelle Druckdatei herunterladen & Thumbnail verarbeiten">
                    <span class="btn-icon">🖼️</span>
                    Thumbnail holen
                </button>
            `);
        } else if (printer.status === 'paused') {
            // Show resume and stop buttons when paused
            buttons.push(`
                <button class="btn btn-sm btn-success" onclick="printerManager.resumePrint('${printer.id}')" title="Druck fortsetzen">
                    <span class="btn-icon">▶️</span>
                    Fortsetzen
                </button>
                <button class="btn btn-sm btn-error" onclick="printerManager.stopPrint('${printer.id}')" title="Druck stoppen">
                    <span class="btn-icon">⏹️</span>
                    Stoppen
                </button>
            `);
        } else if (printer.status === 'online') {
            // Show generic control button when online but not printing
            buttons.push(`
                <button class="btn btn-sm btn-secondary" onclick="printerManager.showPrinterControl('${printer.id}')" title="Drucker steuern">
                    <span class="btn-icon">🎮</span>
                    Steuern
                </button>
            `);
        }
        
        // View statistics
        buttons.push(`
            <button class="btn btn-sm btn-secondary" onclick="printerManager.showStatistics('${printer.id}')" title="Statistiken anzeigen">
                <span class="btn-icon">📊</span>
                Statistiken
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
                <h3>Keine Drucker konfiguriert</h3>
                <p>Fügen Sie Ihren ersten Drucker hinzu, um mit der Verwaltung zu beginnen.</p>
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
                <button class="btn btn-primary" onclick="printerManager.loadPrinters()">
                    <span class="btn-icon">🔄</span>
                    Erneut versuchen
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
     * Show printer details
     */
    async showPrinterDetails(printerId) {
        try {
            const printer = await api.getPrinter(printerId);
            
            // Create and show details modal (placeholder implementation)
            showToast('info', 'Details', `Drucker: ${printer.name}\nStatus: ${printer.status}\nIP: ${printer.ip_address}`);
            
        } catch (error) {
            console.error('Failed to load printer details:', error);
            showToast('error', 'Fehler', 'Drucker-Details konnten nicht geladen werden');
        }
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
            console.error('Failed to load printer for editing:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Laden der Drucker-Daten';
            showToast('error', 'Fehler', message);
        }
    }

    /**
     * Delete printer
     */
    async deletePrinter(printerId) {
        const printer = this.printers.get(printerId);
        if (!printer) return;
        
        const confirmed = confirm(`Möchten Sie den Drucker "${printer.data.name}" wirklich löschen?`);
        if (!confirmed) return;
        
        try {
            await api.deletePrinter(printerId);
            showToast('success', 'Erfolg', CONFIG.SUCCESS_MESSAGES.PRINTER_REMOVED);
            this.loadPrinters();
        } catch (error) {
            console.error('Failed to delete printer:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Löschen des Druckers';
            showToast('error', 'Fehler', message);
        }
    }

    /**
     * Test printer connection
     */
    async testConnection(printerId) {
        try {
            showToast('info', 'Verbindungstest', 'Teste Verbindung zum Drucker...');
            
            // Get fresh printer status
            const printer = await api.getPrinter(printerId);
            
            if (printer.status === 'online') {
                showToast('success', 'Verbindung OK', `Drucker ${printer.name} ist erreichbar`);
            } else {
                showToast('warning', 'Verbindung fehlgeschlagen', `Drucker ${printer.name} ist nicht erreichbar`);
            }
            
        } catch (error) {
            console.error('Connection test failed:', error);
            showToast('error', 'Verbindungsfehler', 'Verbindungstest fehlgeschlagen');
        }
    }

    /**
     * Show printer control interface
     */
    showPrinterControl(printerId) {
        showToast('info', 'Drucker-Steuerung', 'Verwenden Sie die Druck-Steuerungstasten zum Pausieren/Stoppen von Druckaufträgen');
    }
    
    /**
     * Pause print job
     */
    async pausePrint(printerId) {
        const printer = this.printers.get(printerId);
        if (!printer) return;
        
        const confirmed = confirm(`Möchten Sie den Druckauftrag auf "${printer.data.name}" pausieren?`);
        if (!confirmed) return;
        
        try {
            showToast('info', 'Pausieren', 'Pausiere Druckauftrag...');
            
            await api.pausePrinter(printerId);
            showToast('success', 'Erfolg', 'Druckauftrag wurde pausiert');
            
            // Refresh printer status
            this.refreshPrinters();
            
        } catch (error) {
            console.error('Failed to pause print:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Pausieren des Druckauftrags';
            showToast('error', 'Fehler', message);
        }
    }
    
    /**
     * Resume print job
     */
    async resumePrint(printerId) {
        const printer = this.printers.get(printerId);
        if (!printer) return;
        
        const confirmed = confirm(`Möchten Sie den Druckauftrag auf "${printer.data.name}" fortsetzen?`);
        if (!confirmed) return;
        
        try {
            showToast('info', 'Fortsetzen', 'Setze Druckauftrag fort...');
            
            await api.resumePrinter(printerId);
            showToast('success', 'Erfolg', 'Druckauftrag wurde fortgesetzt');
            
            // Refresh printer status
            this.refreshPrinters();
            
        } catch (error) {
            console.error('Failed to resume print:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Fortsetzen des Druckauftrags';
            showToast('error', 'Fehler', message);
        }
    }
    
    /**
     * Stop print job
     */
    async stopPrint(printerId) {
        const printer = this.printers.get(printerId);
        if (!printer) return;
        
        const confirmed = confirm(`Möchten Sie den Druckauftrag auf "${printer.data.name}" wirklich stoppen? Dies kann nicht rückgängig gemacht werden.`);
        if (!confirmed) return;
        
        try {
            showToast('info', 'Stoppen', 'Stoppe Druckauftrag...');
            
            await api.stopPrinter(printerId);
            showToast('success', 'Erfolg', 'Druckauftrag wurde gestoppt');
            
            // Refresh printer status
            this.refreshPrinters();
            
        } catch (error) {
            console.error('Failed to stop print:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Stoppen des Druckauftrags';
            showToast('error', 'Fehler', message);
        }
    }

    /**
     * Manually trigger download & processing of the currently printing job file
     */
    async downloadCurrentJob(printerId) {
        const printer = this.printers.get(printerId);
        if (!printer) return;
        try {
            showToast('info', 'Thumbnail', 'Lade aktuelle Druckdatei herunter...');
            const result = await api.downloadCurrentJobFile(printerId);
            const status = result.status || 'unbekannt';
            if (status === 'exists_with_thumbnail' || status === 'processed' || status === 'success') {
                showToast('success', 'Thumbnail', 'Thumbnail wurde bereitgestellt.');
            } else if (status === 'not_printing') {
                showToast('warning', 'Kein Druck', 'Kein aktiver Druckauftrag vorhanden.');
            } else if (status === 'exists_no_thumbnail') {
                showToast('info', 'Keine Vorschau', 'Datei ohne eingebettetes Thumbnail oder Parsing fehlgeschlagen.');
            } else {
                showToast('info', 'Status', `Status: ${status}`);
            }
            // Refresh printers to get updated thumbnail/file id flags
            this.refreshPrinters();
        } catch (error) {
            console.error('Failed to download current job file:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Herunterladen der aktuellen Datei';
            showToast('error', 'Fehler', message);
        }
    }

    /**
     * Show printer statistics
     */
    async showStatistics(printerId) {
        try {
            const stats = await api.getPrinterStatistics(printerId);
            
            // Create simple statistics display (placeholder)
            const message = `
                Aufträge: ${stats.jobs.total_jobs}
                Erfolgsrate: ${formatPercentage(stats.jobs.success_rate * 100)}
                Betriebszeit: ${formatDuration(stats.uptime.active_hours * 3600)}
                Material: ${formatWeight(stats.materials.total_used_kg * 1000)}
            `;
            
            showToast('info', 'Drucker-Statistiken', message);
            
        } catch (error) {
            console.error('Failed to load printer statistics:', error);
            showToast('error', 'Fehler', 'Statistiken konnten nicht geladen werden');
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
            console.error('Failed to refresh printers:', error);
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
                <p>Suche nach Druckern im Netzwerk...</p>
            </div>
        `;

        // Disable discover button
        if (discoverButton) {
            discoverButton.disabled = true;
            discoverButton.innerHTML = '<span class="btn-icon">⏳</span> Suche läuft...';
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
            response.discovered.forEach(printer => {
                const printerCard = createDiscoveredPrinterCard(printer);
                discoveredList.appendChild(printerCard);
            });

            // Show success message
            showNotification(`${response.discovered.length} Drucker gefunden (${response.scan_duration_ms}ms)`, 'success');
        } else {
            discoveredList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <h3>Keine Drucker gefunden</h3>
                    <p>Es wurden keine Drucker im Netzwerk gefunden.</p>
                    <p class="text-sm text-muted">Stellen Sie sicher, dass:</p>
                    <ul class="text-sm text-muted" style="text-align: left; max-width: 400px; margin: 10px auto;">
                        <li>Ihre Drucker eingeschaltet und mit dem Netzwerk verbunden sind</li>
                        <li>Sie sich im gleichen Netzwerk befinden</li>
                        <li>Bei Docker/Home Assistant: Host-Netzwerkmodus aktiviert ist</li>
                    </ul>
                </div>
            `;
        }

        // Show errors if any
        if (response.errors && response.errors.length > 0) {
            console.warn('Discovery errors:', response.errors);
            response.errors.forEach(error => {
                showNotification(error, 'warning');
            });
        }

    } catch (error) {
        console.error('Failed to discover printers:', error);
        discoveredList.innerHTML = `
            <div class="error-state">
                <div class="error-icon">⚠️</div>
                <h3>Fehler bei der Drucker-Suche</h3>
                <p>${escapeHtml(error.message || 'Unbekannter Fehler')}</p>
            </div>
        `;
        showNotification('Drucker-Suche fehlgeschlagen', 'error');
    } finally {
        // Re-enable discover button
        if (discoverButton) {
            discoverButton.disabled = false;
            discoverButton.innerHTML = '<span class="btn-icon">🔍</span> Drucker suchen';
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
        '<span class="badge badge-secondary">Bereits hinzugefügt</span>' :
        '<span class="badge badge-success">Neu gefunden</span>';

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
                    <span class="label">IP-Adresse:</span>
                    <span class="value">${escapeHtml(printer.ip)}</span>
                </div>
                <div class="info-row">
                    <span class="label">Hostname:</span>
                    <span class="value">${escapeHtml(printer.hostname)}</span>
                </div>
                ${printer.model ? `
                <div class="info-row">
                    <span class="label">Modell:</span>
                    <span class="value">${escapeHtml(printer.model)}</span>
                </div>
                ` : ''}
            </div>
        </div>
        <div class="card-footer">
            ${!printer.already_added ? `
                <button class="btn btn-primary" onclick="addDiscoveredPrinter('${escapeHtml(printer.ip)}', '${printer.type}', '${escapeHtml(printer.name || printer.hostname)}')">
                    <span class="btn-icon">➕</span>
                    Hinzufügen
                </button>
            ` : `
                <button class="btn btn-secondary" disabled>
                    <span class="btn-icon">✓</span>
                    Bereits konfiguriert
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
    // Pre-fill the add printer form with discovered info
    showAddPrinter();

    // Wait for form to be shown, then fill it
    setTimeout(() => {
        const nameInput = document.querySelector('input[name="name"]');
        const typeSelect = document.querySelector('select[name="printer_type"]');
        const ipInput = document.querySelector('input[name="ip_address"]');

        if (nameInput) nameInput.value = name;
        if (ipInput) ipInput.value = ipAddress;
        if (typeSelect) {
            // Map discovery type to form type
            const formType = type === 'bambu' ? 'bambu_lab' : 'prusa_core';
            typeSelect.value = formType;
            // Trigger change event to update form fields
            typeSelect.dispatchEvent(new Event('change'));
        }
    }, 100);
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
            interfaceSelect.innerHTML = '<option value="">Auto-Erkennung</option>';

            // Add interfaces
            response.interfaces.forEach(iface => {
                const option = document.createElement('option');
                option.value = iface.name;
                option.textContent = `${iface.name} (${iface.ip})${iface.is_default ? ' - Standard' : ''}`;
                if (iface.is_default) {
                    option.selected = false; // Keep auto-detect selected by default
                }
                interfaceSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load network interfaces:', error);
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