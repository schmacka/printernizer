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
        const printerType = CONFIG.PRINTER_TYPES[printer.type] || { label: printer.type, color: '#6b7280' };
        
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
                        ${this.renderCurrentJobInfo(printer.current_job)}
                        ${this.renderTemperatureInfo(printer.temperatures)}
                    </div>
                    
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
    renderCurrentJobInfo(currentJob) {
        if (!currentJob) {
            return '<div class="info-item"><span class="text-muted">Kein aktiver Auftrag</span></div>';
        }
        
        const status = getStatusConfig('job', currentJob.status);
        
        return `
            <div class="current-job-info">
                <div class="info-item">
                    <label>Aktueller Auftrag:</label>
                    <span>${escapeHtml(currentJob.name)}</span>
                </div>
                <div class="info-item">
                    <label>Status:</label>
                    <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
                </div>
                ${currentJob.progress !== undefined ? `
                    <div class="info-item">
                        <label>Fortschritt:</label>
                        <div class="inline-progress">
                            <div class="progress">
                                <div class="progress-bar" style="width: ${currentJob.progress}%"></div>
                            </div>
                            <span class="progress-text">${formatPercentage(currentJob.progress)}</span>
                        </div>
                    </div>
                ` : ''}
                ${currentJob.estimated_remaining ? `
                    <div class="info-item">
                        <label>Verbleibend:</label>
                        <span>${formatDuration(currentJob.estimated_remaining)}</span>
                    </div>
                ` : ''}
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
                        ${nozzle.current}°C${nozzle.target ? ` / ${nozzle.target}°C` : ''}
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
                        ${bed.current}°C${bed.target ? ` / ${bed.target}°C` : ''}
                    </span>
                </div>
            `);
        }
        
        if (temperatures.chamber !== undefined) {
            const chamber = typeof temperatures.chamber === 'object' ? temperatures.chamber : { current: temperatures.chamber };
            tempItems.push(`
                <div class="info-item">
                    <label>Kammer:</label>
                    <span class="temperature">${chamber.current}°C</span>
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
        
        // Printer controls (if online)
        if (printer.status === 'online') {
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
        // Printer type selection handler
        const printerTypeSelect = document.getElementById('printerType');
        if (printerTypeSelect) {
            printerTypeSelect.addEventListener('change', (e) => {
                this.handlePrinterTypeChange(e.target.value);
            });
        }
        
        // Add printer form submission
        const addPrinterForm = document.getElementById('addPrinterForm');
        if (addPrinterForm) {
            addPrinterForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleAddPrinter();
            });
        }
    }

    /**
     * Handle printer type selection change
     */
    handlePrinterTypeChange(printerType) {
        const bambuFields = document.getElementById('bambuFields');
        const prusaFields = document.getElementById('prusaFields');
        
        // Hide all fields first
        if (bambuFields) bambuFields.style.display = 'none';
        if (prusaFields) prusaFields.style.display = 'none';
        
        // Show relevant fields
        if (printerType === 'bambu_lab' && bambuFields) {
            bambuFields.style.display = 'block';
        } else if (printerType === 'prusa_core' && prusaFields) {
            prusaFields.style.display = 'block';
        }
    }

    /**
     * Handle add printer form submission
     */
    async handleAddPrinter() {
        const form = document.getElementById('addPrinterForm');
        if (!form) return;
        
        // Validate form
        const errors = validateForm(form);
        if (errors.length > 0) {
            const errorMessage = errors.map(e => e.message).join('\n');
            showToast('error', 'Validierungsfehler', errorMessage);
            return;
        }
        
        try {
            // Prepare printer data
            const formData = new FormData(form);
            const printerType = formData.get('printerType');
            const name = formData.get('printerName');
            const ipAddress = formData.get('printerIP');
            const isActive = formData.get('printerActive') === 'on';
            
            // Build connection config based on printer type
            const connectionConfig = {
                ip_address: ipAddress
            };

            // Add printer-specific fields to connection config
            if (printerType === 'bambu_lab') {
                connectionConfig.access_code = formData.get('accessCode');
                connectionConfig.serial_number = formData.get('serialNumber');
            } else if (printerType === 'prusa_core') {
                connectionConfig.api_key = formData.get('apiKey');
            }

            // Format data according to backend API expectations
            const printerData = {
                name: name,
                printer_type: printerType,
                connection_config: connectionConfig
            };

            // Add optional fields if needed
            if (!isActive) {
                printerData.is_enabled = false;
            }
            
            // Add printer via API
            const response = await api.addPrinter(printerData);
            
            // Close modal and refresh list
            closeModal('addPrinterModal');
            showToast('success', 'Erfolg', CONFIG.SUCCESS_MESSAGES.PRINTER_ADDED);
            this.loadPrinters();
            
        } catch (error) {
            console.error('Failed to add printer:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : 'Fehler beim Hinzufügen des Druckers';
            showToast('error', 'Fehler', message);
        }
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
    editPrinter(printerId) {
        showToast('info', 'Funktion nicht verfügbar', 'Drucker-Bearbeitung wird in einer späteren Version implementiert');
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
        showToast('info', 'Funktion nicht verfügbar', 'Drucker-Steuerung wird in Phase 2 implementiert');
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

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PrinterManager, printerManager };
}