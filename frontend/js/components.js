/**
 * Printernizer UI Components
 * Reusable UI components for consistent interface elements
 */

/**
 * Enhanced Printer Card Component with Real-time Status
 */
class PrinterCard {
    constructor(printer) {
        this.printer = printer;
        this.element = null;
        this.statusUpdateInterval = null;
        this.isMonitoring = false;
        this.cameraStatus = null; // Will be fetched async
    }

    /**
     * Render printer card HTML with enhanced real-time features
     */
    render() {
        const status = getStatusConfig('printer', this.printer.status);
        const printerType = CONFIG.PRINTER_TYPES[this.printer.printer_type] || { label: this.printer.printer_type };
        
        this.element = document.createElement('div');
        this.element.className = `printer-card card status-${this.printer.status} ${this.isMonitoring ? 'monitoring-active' : ''}`;
        this.element.setAttribute('data-printer-id', this.printer.id);
        
        this.element.innerHTML = `
            <div class="printer-header">
                <div class="printer-title">
                    <h3>${escapeHtml(this.printer.name)}</h3>
                    <span class="printer-type">${printerType.label}</span>
                </div>
                <div class="printer-actions">
                    ${this.renderMonitoringToggle()}
                    <button class="btn btn-sm btn-secondary" onclick="showPrinterDetails('${sanitizeAttribute(this.printer.id)}')" title="Details anzeigen">
                        <span class="btn-icon">👁️</span>
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="showPrinterFiles('${sanitizeAttribute(this.printer.id)}')" title="Drucker-Dateien">
                        <span class="btn-icon">📁</span>
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="editPrinter('${sanitizeAttribute(this.printer.id)}')" title="Bearbeiten">
                        <span class="btn-icon">✏️</span>
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="triggerCurrentJobDownload('${sanitizeAttribute(this.printer.id)}')" title="Aktuelle Druckdatei herunterladen & Thumbnail verarbeiten">
                        <span class="btn-icon">🖼️</span>
                    </button>
                </div>
            </div>
            <div class="printer-body">
                <div class="printer-status-row">
                    <div class="printer-status-info">
                        <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
                        <span class="printer-ip text-muted">${escapeHtml(this.printer.ip_address)}</span>
                        ${this.renderLastCommunication()}
                    </div>
                    <div class="printer-quick-stats">
                        ${this.renderQuickStats()}
                    </div>
                </div>
                
                ${this.renderCurrentJob()}
                ${this.renderTemperatures()}
                ${this.renderFilaments()}
                ${this.renderRealtimeProgress()}
                ${this.renderCameraSection()}
            </div>
        `;
        
        // Auto-start monitoring if printer is printing
        if (this.printer.status === 'printing') {
            this.startRealtimeMonitoring();
        }
        
        // Fetch camera status async and update
        this.fetchCameraStatus();
        
        return this.element;
    }

    /**
     * Fetch camera status asynchronously
     */
    async fetchCameraStatus() {
        if (!this.printer || !this.printer.id) return;

        try {
            // Delegate to CameraManager for consistency
            if (window.cameraManager) {
                await cameraManager.getCameraStatus(this.printer.id);
                // Re-render camera section
                const cameraSection = this.element.querySelector('.camera-section');
                if (cameraSection) {
                    cameraSection.outerHTML = this.renderCameraSection();
                }
            }
        } catch (error) {
            // Safe error logging - check if Logger exists first
            if (typeof Logger !== 'undefined') {
                Logger.error('Failed to fetch camera status:', error);
            } else {
                console.error('Failed to fetch camera status:', error);
            }
        }
    }

    /**
     * Render camera section - delegated to CameraManager
     */
    renderCameraSection() {
        // Delegate to CameraManager for consistency
        // CameraManager has proper null checks and preview support
        if (window.cameraManager && this.printer) {
            return cameraManager.renderCameraSection(this.printer);
        }

        // Fallback if CameraManager not loaded yet
        return `
            <div class="info-section camera-section">
                <h4>📷 Kamera</h4>
                <div class="info-item">
                    <span class="text-muted">Wird geladen...</span>
                </div>
            </div>
        `;
    }


    /**
     * Render monitoring toggle button
     */
    renderMonitoringToggle() {
        const isActive = this.isMonitoring;
        const buttonClass = isActive ? 'btn-primary' : 'btn-secondary';
        const buttonIcon = isActive ? '⏹️' : '▶️';
        const buttonTitle = isActive ? 'Überwachung stoppen' : 'Überwachung starten';
        
        return `
            <button class="btn btn-sm ${buttonClass} monitoring-toggle" 
                    onclick="togglePrinterMonitoring('${this.printer.id}')" 
                    title="${buttonTitle}"
                    data-monitoring="${isActive}">
                <span class="btn-icon">${buttonIcon}</span>
            </button>
        `;
    }

    /**
     * Render last communication info
     */
    renderLastCommunication() {
        // Show "Druckt" when printer is actively printing
        if (this.printer.status === 'printing') {
            return '<span class="text-success printer-printing-status">🖨️ Druckt</span>';
        }

        if (!this.printer.last_seen) {
            return '<span class="text-muted">Nie verbunden</span>';
        }

        const timeSinceLastComm = Date.now() - new Date(this.printer.last_seen).getTime();
        const isRecent = timeSinceLastComm < 60000; // Less than 1 minute

        return `
            <span class="last-communication ${isRecent ? 'text-success' : 'text-warning'}" title="Letzte Kommunikation">
                ${isRecent ? '🟢' : '🟡'} ${getRelativeTime(this.printer.last_seen)}
            </span>
        `;
    }

    /**
     * Render quick stats (uptime, jobs today, etc.)
     */
    renderQuickStats() {
        const stats = [];
        
        if (this.printer.uptime) {
            stats.push(`<span class="quick-stat" title="Betriebszeit">⏱️ ${formatDuration(this.printer.uptime)}</span>`);
        }
        
        if (this.printer.jobs_today !== undefined) {
            stats.push(`<span class="quick-stat" title="Aufträge heute">📊 ${this.printer.jobs_today}</span>`);
        }
        
        return stats.join('');
    }

    /**
     * Render real-time progress section
     * Note: This is only shown when there's no job progress in renderCurrentJob()
     */
    renderRealtimeProgress() {
        // Don't show real-time progress if there's already job progress being displayed
        if (!this.printer.current_job || this.printer.status !== 'printing') {
            return '';
        }
        
        const job = this.printer.current_job;
        
        // Skip real-time progress if job progress will be shown in renderCurrentJob
        if (job.progress !== undefined) {
            return '';
        }
        
        return `
            <div class="realtime-progress">
                <div class="progress-header">
                    <span class="progress-label">Live-Fortschritt</span>
                    <span class="progress-percentage">${formatPercentage(job.progress || 0)}</span>
                </div>
                <div class="progress progress-animated">
                    <div class="progress-bar" style="width: ${job.progress || 0}%"></div>
                </div>
                <div class="progress-details">
                    ${job.layer_current && job.layer_total ? `
                        <span>Schicht ${job.layer_current}/${job.layer_total}</span>
                    ` : ''}
                    ${job.estimated_remaining ? `
                        <span>⏰ ${formatDuration(job.estimated_remaining)} verbleibend</span>
                    ` : ''}
                    ${job.print_speed ? `
                        <span>⚡ ${job.print_speed}%</span>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Render current job section
     */
    renderCurrentJob() {
        // Always render a job section container for consistent card height
        if (!this.printer.current_job) {
            return `
                <div class="current-job current-job-placeholder">
                    <div class="job-placeholder-content">
                        <span class="placeholder-icon">📭</span>
                        <p class="text-muted">Kein aktiver Auftrag</p>
                    </div>
                </div>
            `;
        }

        // Handle case where current_job is a string (job name) rather than an object
        const jobName = typeof this.printer.current_job === 'string' ? this.printer.current_job : this.printer.current_job.name;

        // Get progress from printer object (backend sends it at top level)
        const progress = this.printer.progress !== undefined && this.printer.progress !== null ? this.printer.progress : 0;

        return `
            <div class="current-job" data-job-name="${escapeHtml(jobName)}">
                ${this.renderJobThumbnail()}
                <div class="job-name">${escapeHtml(jobName)}</div>

                ${this.printer.status === 'printing' ? `
                    <div class="job-progress">
                        <div class="progress-info">
                            <span class="progress-percentage">${formatPercentage(progress)}</span>
                            <span class="progress-time estimated-time">
                                ${this.printer.remaining_time_minutes ? `Noch ${formatDuration(this.printer.remaining_time_minutes * 60)}` : ''}
                            </span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar" style="width: ${progress}%"></div>
                        </div>
                    </div>
                ` : ''}

                ${this.printer.remaining_time_minutes || this.printer.estimated_end_time ? `
                    <div class="time-info">
                        ${this.printer.remaining_time_minutes ? `
                            <span class="remaining-time">Verbleibend: ${formatDuration(this.printer.remaining_time_minutes * 60)}</span>
                        ` : ''}
                        ${this.printer.estimated_end_time ? `
                            <span class="end-time">Ende: ${formatTime(this.printer.estimated_end_time)}</span>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Render job thumbnail section
     */
    renderJobThumbnail() {
        // Check if we have current job file data
        if (!this.printer.current_job_file_id) {
            return '';
        }

        // Determine thumbnail source
        const thumbnailSrc = this.printer.current_job_has_thumbnail
            ? `/api/v1/files/${this.printer.current_job_file_id}/thumbnail`
            : 'assets/placeholder-thumbnail.svg';

        return `
            <div class="job-thumbnail">
                <img src="${thumbnailSrc}"
                     alt="${this.printer.current_job_has_thumbnail ? 'Job Thumbnail' : 'Keine Vorschau verfügbar'}"
                     class="thumbnail-image ${!this.printer.current_job_has_thumbnail ? 'placeholder-image' : ''}"
                     data-file-id="${this.printer.current_job_file_id}"
                     loading="lazy"
                     onclick="showFullThumbnail('${this.printer.current_job_file_id}', '${escapeHtml(this.printer.current_job || 'Current Job')}')"
                     ${this.printer.current_job_has_thumbnail ? "onerror=\"this.src='assets/placeholder-thumbnail.svg'; this.onerror=null; this.classList.add('placeholder-image');\"" : ''}>
                <div class="thumbnail-overlay">
                    <i class="fas fa-expand"></i>
                </div>
            </div>
        `;
    }

    /**
     * Render temperatures section
     */
    renderTemperatures() {
        // Always show temperature section for consistent height
        if (!this.printer.temperatures) {
            return `
                <div class="temperatures temperatures-placeholder">
                    <div class="temp-item">
                        <div class="temp-label">Düse</div>
                        <div class="temp-value text-muted">--°C</div>
                    </div>
                    <div class="temp-item">
                        <div class="temp-label">Bett</div>
                        <div class="temp-value text-muted">--°C</div>
                    </div>
                </div>
            `;
        }

        const temps = this.printer.temperatures;
        const tempItems = [];

        if (temps.nozzle !== undefined) {
            tempItems.push(this.renderTemperatureItem('nozzle', 'Düse', temps.nozzle));
        }

        if (temps.bed !== undefined) {
            tempItems.push(this.renderTemperatureItem('bed', 'Bett', temps.bed));
        }

        if (temps.chamber !== undefined) {
            tempItems.push(this.renderTemperatureItem('chamber', 'Kammer', temps.chamber));
        }

        if (tempItems.length === 0) {
            return `
                <div class="temperatures temperatures-placeholder">
                    <div class="temp-item">
                        <div class="temp-label">Düse</div>
                        <div class="temp-value text-muted">--°C</div>
                    </div>
                    <div class="temp-item">
                        <div class="temp-label">Bett</div>
                        <div class="temp-value text-muted">--°C</div>
                    </div>
                </div>
            `;
        }

        return `
            <div class="temperatures">
                ${tempItems.join('')}
            </div>
        `;
    }

    /**
     * Render individual temperature item
     */
    renderTemperatureItem(type, label, temperature) {
        let tempValue, tempTarget = '';

        if (typeof temperature === 'object') {
            tempValue = `${parseFloat(temperature.current).toFixed(1)}°C`;
            if (temperature.target) {
                tempTarget = `<div class="temp-target">Ziel: ${parseFloat(temperature.target).toFixed(1)}°C</div>`;
            }
        } else {
            tempValue = `${parseFloat(temperature).toFixed(1)}°C`;
        }

        const isHeating = typeof temperature === 'object' &&
                          temperature.target &&
                          Math.abs(temperature.current - temperature.target) > 2;

        return `
            <div class="temp-item" data-temp-type="${type}">
                <div class="temp-label">${label}</div>
                <div class="temp-value ${isHeating ? 'temp-heating' : ''}">${tempValue}</div>
                ${tempTarget}
            </div>
        `;
    }

    /**
     * Render filaments section
     */
    renderFilaments() {
        // Don't show filaments section if no filament data
        if (!this.printer.filaments || this.printer.filaments.length === 0) {
            return '';
        }

        const filamentItems = this.printer.filaments.map(filament =>
            this.renderFilamentItem(filament)
        ).join('');

        return `
            <div class="filaments">
                <div class="filaments-header">
                    <span class="filaments-label">Filamente</span>
                </div>
                <div class="filaments-list">
                    ${filamentItems}
                </div>
            </div>
        `;
    }

    /**
     * Render individual filament item
     */
    renderFilamentItem(filament) {
        const slotLabel = filament.slot === 254 ? 'Ext' : `${filament.slot + 1}`;
        const filamentType = filament.type || '?';
        const filamentColor = filament.color || '#CCCCCC';
        const isActive = filament.is_active;

        return `
            <div class="filament-item ${isActive ? 'filament-active' : ''}" data-slot="${filament.slot}" title="Slot ${slotLabel}: ${filamentType}">
                <div class="filament-color" style="background-color: ${escapeHtml(filamentColor)}"></div>
                <div class="filament-info">
                    <span class="filament-slot">${slotLabel}</span>
                    <span class="filament-type">${escapeHtml(filamentType)}</span>
                </div>
            </div>
        `;
    }

    /**
     * Start real-time monitoring for this printer
     */
    async startRealtimeMonitoring() {
        if (this.isMonitoring) return;
        
        try {
            await api.startPrinterMonitoring(this.printer.id);
            this.isMonitoring = true;
            
            // Update monitoring button
            this.updateMonitoringButton();
            
            // Start periodic status updates
            this.statusUpdateInterval = setInterval(async () => {
                try {
                    const status = await api.getPrinterStatus(this.printer.id);
                    this.updateRealtimeData(status);
                } catch (error) {
                    Logger.warn(`Failed to update printer ${this.printer.id} status:`, error);
                }
            }, CONFIG.PRINTER_STATUS_INTERVAL);
            
            // Add monitoring-active class
            this.element.classList.add('monitoring-active');
            
        } catch (error) {
            Logger.error('Failed to start monitoring:', error);
            showToast('Überwachung konnte nicht gestartet werden', 'error');
        }
    }

    /**
     * Stop real-time monitoring for this printer
     */
    async stopRealtimeMonitoring() {
        if (!this.isMonitoring) return;
        
        try {
            await api.stopPrinterMonitoring(this.printer.id);
            this.isMonitoring = false;
            
            // Clear update interval
            if (this.statusUpdateInterval) {
                clearInterval(this.statusUpdateInterval);
                this.statusUpdateInterval = null;
            }
            
            // Update monitoring button
            this.updateMonitoringButton();
            
            // Remove monitoring-active class
            this.element.classList.remove('monitoring-active');
            
        } catch (error) {
            Logger.error('Failed to stop monitoring:', error);
            showToast('Überwachung konnte nicht gestoppt werden', 'error');
        }
    }

    /**
     * Update monitoring button appearance
     */
    updateMonitoringButton() {
        const button = this.element.querySelector('.monitoring-toggle');
        if (!button) return;
        
        const isActive = this.isMonitoring;
        button.className = `btn btn-sm ${isActive ? 'btn-primary' : 'btn-secondary'} monitoring-toggle`;
        button.title = isActive ? 'Überwachung stoppen' : 'Überwachung starten';
        button.querySelector('.btn-icon').textContent = isActive ? '⏹️' : '▶️';
        button.setAttribute('data-monitoring', isActive);
    }

    /**
     * Update real-time data without full re-render
     */
    updateRealtimeData(statusData) {
        
        // Update temperatures
        if (statusData.temperatures) {
            this.updateTemperatureDisplay(statusData.temperatures);
        }
        
        // Update job progress
        if (statusData.current_job) {
            this.updateJobProgress(statusData.current_job);
        }
        
        // Update last communication
        if (statusData.last_communication) {
            this.printer.last_communication = statusData.last_communication;
            this.updateLastCommunication();
        }
        
        // Update status if changed
        if (statusData.status && statusData.status !== this.printer.status) {
            this.printer.status = statusData.status;
            this.updateStatusBadge();
        }
    }


    /**
     * Update temperature displays
     */
    updateTemperatureDisplay(temperatures) {
        Object.keys(temperatures).forEach(tempType => {
            const tempElement = this.element.querySelector(`[data-temp-type="${tempType}"] .temp-value`);
            if (tempElement) {
                const temp = temperatures[tempType];
                let tempValue = '';
                
                if (typeof temp === 'object') {
                    tempValue = `${temp.current}°C`;
                    const isHeating = temp.target && Math.abs(temp.current - temp.target) > 2;
                    tempElement.className = `temp-value ${isHeating ? 'temp-heating' : ''}`;
                } else {
                    tempValue = `${temp}°C`;
                }
                
                tempElement.textContent = tempValue;
            }
        });
    }

    /**
     * Update job progress
     */
    updateJobProgress(jobData) {
        // Update main progress bar
        const progressBar = this.element.querySelector('.progress-bar');
        if (progressBar && jobData.progress !== undefined) {
            progressBar.style.width = `${jobData.progress}%`;
        }
        
        // Update progress percentage
        const progressPercentage = this.element.querySelector('.progress-percentage');
        if (progressPercentage && jobData.progress !== undefined) {
            progressPercentage.textContent = formatPercentage(jobData.progress);
        }
        
        // Update layer info
        if (jobData.layer_current && jobData.layer_total) {
            const layerInfo = this.element.querySelector('.layer-info span');
            if (layerInfo) {
                layerInfo.textContent = `Schicht: ${jobData.layer_current}/${jobData.layer_total}`;
            }
        }
        
        // Update remaining time
        const remainingTimeElement = this.element.querySelector('.estimated-time');
        if (remainingTimeElement && jobData.estimated_remaining) {
            remainingTimeElement.textContent = `Noch ${formatDuration(jobData.estimated_remaining)}`;
        }
    }

    /**
     * Update last communication display
     */
    updateLastCommunication() {
        const commElement = this.element.querySelector('.last-communication, .printer-printing-status');
        if (!commElement) return;

        // Show "Druckt" when printer is actively printing
        if (this.printer.status === 'printing') {
            commElement.className = 'text-success printer-printing-status';
            commElement.innerHTML = '🖨️ Druckt';
            return;
        }

        if (!this.printer.last_communication) return;

        const timeSinceLastComm = Date.now() - new Date(this.printer.last_communication).getTime();
        const isRecent = timeSinceLastComm < 60000;

        commElement.className = `last-communication ${isRecent ? 'text-success' : 'text-warning'}`;
        commElement.innerHTML = `${isRecent ? '🟢' : '🟡'} ${getRelativeTime(this.printer.last_communication)}`;
    }

    /**
     * Update status badge
     */
    updateStatusBadge() {
        const statusBadge = this.element.querySelector('.status-badge');
        if (!statusBadge) return;
        
        const status = getStatusConfig('printer', this.printer.status);
        statusBadge.className = `status-badge ${status.class}`;
        statusBadge.innerHTML = `${status.icon} ${status.label}`;
        
        // Update card class
        this.element.className = `printer-card card status-${this.printer.status} ${this.isMonitoring ? 'monitoring-active' : ''}`;
    }

    /**
     * Update printer card with new data
     */
    update(printerData) {
        this.printer = { ...this.printer, ...printerData };
        
        // If we're monitoring, just update real-time data
        if (this.isMonitoring) {
            this.updateRealtimeData(printerData);
        } else {
            // Full re-render for major changes
            const oldElement = this.element;
            this.render();
            if (oldElement && oldElement.parentNode) {
                oldElement.parentNode.replaceChild(this.element, oldElement);
            }
        }
        
        return this.element;
    }

    /**
     * Cleanup when component is destroyed
     */
    destroy() {
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
        }
        if (this.isMonitoring) {
            this.stopRealtimeMonitoring();
        }
    }
}

/**
 * Job List Item Component
 */
class JobListItem {
    constructor(job) {
        this.job = job;
        this.element = null;
    }

    /**
     * Render job list item HTML
     */
    render() {
        const status = getStatusConfig('job', this.job.status);
        
        this.element = document.createElement('div');
        this.element.className = 'data-item job-item';
        this.element.setAttribute('data-job-id', this.job.id);
        
        this.element.innerHTML = `
            <div class="data-item-content">
                <div class="data-item-main">
                    <div class="data-item-title">${escapeHtml(this.job.filename || this.job.job_name || 'Unbenannter Job')}</div>
                    <div class="data-item-subtitle">
                        ${escapeHtml(this.job.printer_id || this.job.printer_name || 'Unbekannter Drucker')} •
                        ${this.job.started_at ? formatDateTime(this.job.started_at) : (this.job.start_time ? formatDateTime(this.job.start_time) : 'Nicht gestartet')}
                        ${this.job.is_business ? ' • Geschäftlich' : ''}
                    </div>
                </div>

                <div class="data-item-meta">
                    <div class="data-item-meta-label">Status</div>
                    <div class="status-badges">
                        <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
                        ${this.renderAutoJobBadge()}
                    </div>
                </div>

                ${this.renderProgress()}

                <div class="data-item-meta">
                    <div class="data-item-meta-label">Kosten</div>
                    <div class="data-item-meta-value">
                        ${this.job.cost_eur ? formatCurrency(this.job.cost_eur) : (this.job.costs ? formatCurrency(this.job.costs.total_cost) : '-')}
                    </div>
                </div>
            </div>

            <div class="data-item-actions">
                ${this.renderJobActions()}
            </div>
        `;
        
        return this.element;
    }

    /**
     * Render job progress section
     */
    renderProgress() {
        // Handle backend format with progress_percent
        const progressValue = this.job.progress_percent !== undefined ? this.job.progress_percent : this.job.progress;

        if (this.job.status === 'printing' && progressValue !== undefined) {
            return `
                <div class="data-item-meta">
                    <div class="data-item-meta-label">Fortschritt</div>
                    <div class="job-progress-container">
                        <div class="progress">
                            <div class="progress-bar" style="width: ${progressValue}%"></div>
                        </div>
                        <div class="progress-text">${formatPercentage(progressValue)}</div>
                        ${this.job.estimated_completion ? `
                            <div class="estimated-time text-muted">
                                Fertig: ${formatTime(this.job.estimated_completion)}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        // Handle backend format with elapsed_time_minutes
        if (this.job.elapsed_time_minutes) {
            return `
                <div class="data-item-meta">
                    <div class="data-item-meta-label">Dauer</div>
                    <div class="data-item-meta-value">
                        ${formatDuration(this.job.elapsed_time_minutes * 60)}
                    </div>
                </div>
            `;
        }

        if (this.job.actual_duration) {
            return `
                <div class="data-item-meta">
                    <div class="data-item-meta-label">Dauer</div>
                    <div class="data-item-meta-value">
                        ${formatDuration(this.job.actual_duration)}
                    </div>
                </div>
            `;
        }

        // Handle backend format with estimated_time_minutes
        if (this.job.estimated_time_minutes) {
            return `
                <div class="data-item-meta">
                    <div class="data-item-meta-label">Geschätzt</div>
                    <div class="data-item-meta-value">
                        ${formatDuration(this.job.estimated_time_minutes * 60)}
                    </div>
                </div>
            `;
        }

        if (this.job.estimated_duration) {
            return `
                <div class="data-item-meta">
                    <div class="data-item-meta-label">Geschätzt</div>
                    <div class="data-item-meta-value">
                        ${formatDuration(this.job.estimated_duration)}
                    </div>
                </div>
            `;
        }

        return `
            <div class="data-item-meta">
                <div class="data-item-meta-label">Erstellt</div>
                <div class="data-item-meta-value">
                    ${formatDateTime(this.job.created_at)}
                </div>
            </div>
        `;
    }

    /**
     * Render auto-job creation badge
     */
    renderAutoJobBadge() {
        // Check if job was auto-created
        if (this.job.customer_info && this.job.customer_info.auto_created) {
            const discoveryTime = this.job.customer_info.discovery_time;
            const printerStartTime = this.job.customer_info.printer_start_time;
            const wasStartup = this.job.customer_info.discovered_on_startup;

            // Build tooltip text
            let tooltipText = 'Automatisch erstellt';
            if (wasStartup) {
                tooltipText += ' (beim Start entdeckt)';
            }
            if (discoveryTime) {
                tooltipText += `\nEntdeckt: ${formatDateTime(discoveryTime)}`;
            }
            if (printerStartTime) {
                tooltipText += `\nDrucker-Start: ${formatDateTime(printerStartTime)}`;
            }

            return `
                <span class="status-badge badge-auto" title="${escapeHtml(tooltipText)}">
                    ⚡ Auto
                </span>
            `;
        }
        return '';
    }

    /**
     * Render job action buttons
     */
    renderJobActions() {
        const actions = [];

        // View details
        actions.push(`
            <button class="btn btn-sm btn-secondary" onclick="showJobDetails('${this.job.id}')" title="Details anzeigen">
                <span class="btn-icon">👁️</span>
            </button>
        `);

        // Cancel job if active
        if (['printing', 'queued', 'preparing'].includes(this.job.status)) {
            actions.push(`
                <button class="btn btn-sm btn-warning" onclick="cancelJob('${this.job.id}')" title="Auftrag abbrechen">
                    <span class="btn-icon">⏹️</span>
                </button>
            `);
        }

        // Edit job info
        actions.push(`
            <button class="btn btn-sm btn-secondary" onclick="editJob('${this.job.id}')" title="Bearbeiten">
                <span class="btn-icon">✏️</span>
            </button>
        `);

        return actions.join('');
    }

    /**
     * Update job item with new data
     */
    update(jobData) {
        this.job = { ...this.job, ...jobData };
        const oldElement = this.element;
        this.render();
        if (oldElement && oldElement.parentNode) {
            oldElement.parentNode.replaceChild(this.element, oldElement);
        }
        return this.element;
    }
}

/**
 * File List Item Component
 */
class FileListItem {
    constructor(file) {
        this.file = file;
        this.element = null;
    }

    /**
     * Render file list item HTML
     */
    render() {
        const status = getStatusConfig('file', this.file.status);
        
        this.element = document.createElement('div');
        this.element.className = 'file-item';
        this.element.setAttribute('data-file-id', this.file.id);
        
        this.element.innerHTML = `
            <div class="file-visual">
                ${this.renderThumbnailOrIcon()}
            </div>

            <div class="file-info">
                <div class="file-name">${escapeHtml(this.file.filename)}</div>
                <div class="file-details">
                    <span class="file-size">${formatBytes(this.file.file_size)}</span>
                    ${this.file.printer_name ? `<span class="file-printer">${escapeHtml(this.file.printer_name)}</span>` : ''}
                    <span class="file-date">
                        ${this.file.created_on_printer ? formatDateTime(this.file.created_on_printer) : formatDateTime(this.file.last_accessed)}
                    </span>
                </div>
                ${this.renderMetadata()}
            </div>

            <div class="file-status">
                <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
            </div>

            ${this.renderDownloadProgress()}

            <div class="file-actions">
                ${this.renderFileActions()}
            </div>
        `;

        // Attach thumbnail event listeners using extracted method
        this._attachThumbnailListeners();

        return this.element;
    }

    /**
     * Render thumbnail or file icon
     */
    renderThumbnailOrIcon() {
        if (this.file.has_thumbnail && this.file.id) {
            // Check if file supports animated preview (STL or 3MF)
            const supportsAnimation = this.file.file_type &&
                ['stl', '3mf'].includes(this.file.file_type.toLowerCase());

            // DEBUG: Log animation support detection
            Logger.debug('Rendering thumbnail', {
                fileId: this.file.id,
                filename: this.file.filename,
                fileType: this.file.file_type,
                supportsAnimation: supportsAnimation,
                hasThumbnail: this.file.has_thumbnail
            });

            return `
                <div class="file-thumbnail enhanced ${supportsAnimation ? 'supports-animation' : ''}"
                     title="Click to enlarge"
                     data-file-id="${this.file.id}"
                     data-static-url="${CONFIG.API_BASE_URL}/files/${this.file.id}/thumbnail"
                     ${supportsAnimation ? `data-animated-url="${CONFIG.API_BASE_URL}/files/${this.file.id}/thumbnail/animated"` : ''}>
                    <img src="${CONFIG.API_BASE_URL}/files/${this.file.id}/thumbnail"
                         alt="Thumbnail for ${escapeHtml(this.file.filename)}"
                         class="thumbnail-image"
                         onerror="this.src='assets/placeholder-thumbnail.svg'; this.onerror=null; this.classList.add('placeholder-image');"
                         loading="lazy">
                    <div class="file-icon fallback-icon" style="display: none">${this.getFileIcon()}</div>
                    <div class="thumbnail-overlay">
                        <span class="zoom-icon">🔍</span>
                    </div>
                </div>
            `;
        } else {
            return `
                <div class="file-icon">${this.getFileIcon()}</div>
            `;
        }
    }

    /**
     * Show full thumbnail in modal
     */
    showFullThumbnail(fileId, filename) {
        const modal = document.createElement('div');
        modal.className = 'thumbnail-modal';
        modal.innerHTML = `
            <div class="thumbnail-modal-content">
                <div class="thumbnail-modal-header">
                    <h3>${escapeHtml(filename)}</h3>
                    <button class="thumbnail-modal-close" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</button>
                </div>
                <div class="thumbnail-modal-body">
                    <img src="${CONFIG.API_BASE_URL}/files/${fileId}/thumbnail"
                         alt="Full size thumbnail"
                         class="full-thumbnail-image"
                         onerror="this.src='assets/placeholder-thumbnail.svg'; this.onerror=null; this.classList.add('placeholder-image');">
                    <div class="thumbnail-error" style="display: none">
                        <p>Unable to load thumbnail</p>
                    </div>
                </div>
            </div>
        `;

        // Add click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        document.body.appendChild(modal);
    }

    /**
     * Attach thumbnail event listeners
     * Called after render() and update() to ensure listeners persist
     */
    _attachThumbnailListeners() {
        if (this.file.has_thumbnail && this.file.id) {
            const thumbnail = this.element.querySelector('.file-thumbnail.enhanced');
            if (thumbnail) {
                // Click handler for full thumbnail
                thumbnail.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showFullThumbnail(this.file.id, this.file.filename);
                });

                // Hover animation support for STL/3MF files
                if (thumbnail.classList.contains('supports-animation')) {
                    this.setupAnimatedThumbnail(thumbnail);
                }
            }
        }
    }

    /**
     * Setup animated thumbnail on hover for 3D files
     */
    setupAnimatedThumbnail(thumbnailElement) {
        const img = thumbnailElement.querySelector('.thumbnail-image');
        const staticUrl = thumbnailElement.dataset.staticUrl;
        const animatedUrl = thumbnailElement.dataset.animatedUrl;

        // DEBUG: Log setup attempt
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
        let loadTimeout = null;

        // Preload the animated GIF on first hover
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

                // If still hovering, swap immediately
                if (isHovering && img.src !== animatedUrl) {
                    Logger.debug('Swapping to animated image');
                    img.src = animatedUrl;
                }
            };

            preloadImg.onerror = (error) => {
                Logger.error('Failed to load animated preview', {
                    url: animatedUrl,
                    error: error
                });
            };

            preloadImg.src = animatedUrl;
        };

        // Mouse enter: load and show animated GIF
        thumbnailElement.addEventListener('mouseenter', () => {
            isHovering = true;
            Logger.debug('Mouse entered thumbnail - preparing animation');

            // Start loading after a short delay to avoid loading on quick passes
            loadTimeout = setTimeout(() => {
                if (isHovering) {
                    preloadAnimatedGif();

                    // If already loaded, swap immediately
                    if (isAnimatedLoaded && img.src !== animatedUrl) {
                        img.src = animatedUrl;
                    }
                }
            }, 200); // 200ms delay before loading
        });

        // Mouse leave: restore static image
        thumbnailElement.addEventListener('mouseleave', () => {
            isHovering = false;
            Logger.debug('Mouse left thumbnail - restoring static');

            // Cancel loading if not started yet
            if (loadTimeout) {
                clearTimeout(loadTimeout);
                loadTimeout = null;
            }

            // Restore static image
            if (img.src !== staticUrl) {
                Logger.debug('Restoring static image');
                img.src = staticUrl;
            }
        });

        Logger.info('Animated thumbnail setup complete');
    }

    /**
     * Render parsed metadata information
     */
    renderMetadata() {
        if (!this.file.metadata) {
            return '';
        }

        const metadata = this.file.metadata;
        const metadataItems = [];

        // Show estimated print time
        if (metadata.estimated_time || metadata.estimated_print_time) {
            const timeSeconds = metadata.estimated_time || metadata.estimated_print_time;
            const timeText = typeof timeSeconds === 'number' ? this.formatDuration(timeSeconds) : timeSeconds;
            metadataItems.push(`⏱️ ${timeText}`);
        }

        // Show layer information
        if (metadata.total_layer_count || metadata.layer_count) {
            metadataItems.push(`📐 ${metadata.total_layer_count || metadata.layer_count} Schichten`);
        }

        // Show filament usage
        if (metadata.total_filament_used) {
            metadataItems.push(`🧵 ${metadata.total_filament_used.toFixed(1)}g`);
        }

        // Show layer height
        if (metadata.layer_height) {
            metadataItems.push(`📏 ${metadata.layer_height}mm`);
        }

        // Show infill
        if (metadata.infill_density) {
            metadataItems.push(`🏗️ ${metadata.infill_density}%`);
        }

        if (metadataItems.length === 0) {
            return '';
        }

        return `
            <div class="file-metadata">
                ${metadataItems.map(item => `<span class="metadata-item">${item}</span>`).join('')}
            </div>
        `;
    }

    /**
     * Format duration in seconds to human readable format
     */
    formatDuration(seconds) {
        if (typeof seconds !== 'number' || seconds <= 0) {
            return '';
        }

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m`;
        } else {
            return `${seconds}s`;
        }
    }

    /**
     * Get file icon based on file type
     */
    getFileIcon() {
        const extension = this.file.file_type || this.file.filename.split('.').pop().toLowerCase();
        
        const icons = {
            '3mf': '📦',
            'stl': '🔺',
            'obj': '🔷',
            'gcode': '⚙️',
            'amf': '📄',
            'ply': '🔶'
        };
        
        return icons[extension] || '📄';
    }

    /**
     * Render download progress section
     */
    renderDownloadProgress() {
        if (this.file.status !== 'downloading') {
            return '';
        }

        return `
            <div class="download-progress">
                <div class="progress">
                    <div class="progress-bar" style="width: 0%"></div>
                </div>
                <div class="download-status">Vorbereitung...</div>
            </div>
        `;
    }

    /**
     * Render file action buttons
     */
    renderFileActions() {
        const actions = [];
        
        // Preview button (if supported)
        if (this.file.preview_url) {
            actions.push(`
                <button class="btn btn-sm btn-secondary" onclick="previewFile('${this.file.id}')" title="Vorschau anzeigen">
                    <span class="btn-icon">👁️</span>
                </button>
            `);
        }
        
        // Download button
        if (this.file.status === 'available') {
            actions.push(`
                <button class="btn btn-sm btn-primary" onclick="downloadFileFromPrinter('${this.file.id}')" title="Herunterladen">
                    <span class="btn-icon">⬇️</span>
                </button>
            `);
        }
        
        // Open local file button
        if (this.file.status === 'downloaded' && this.file.local_path) {
            actions.push(`
                <button class="btn btn-sm btn-success" onclick="openLocalFile('${this.file.id}')" title="Lokale Datei öffnen">
                    <span class="btn-icon">📂</span>
                </button>
            `);
        }
        
        // Upload to printer (for local files)
        if (this.file.status === 'local') {
            actions.push(`
                <button class="btn btn-sm btn-secondary" onclick="uploadToPrinter('${this.file.id}')" title="Zu Drucker hochladen">
                    <span class="btn-icon">⬆️</span>
                </button>
            `);
        }
        
        // Delete button
        if (this.file.status === 'downloaded') {
            actions.push(`
                <button class="btn btn-sm btn-error" onclick="deleteLocalFile('${this.file.id}')" title="Lokale Datei löschen">
                    <span class="btn-icon">🗑️</span>
                </button>
            `);
        }
        
        return actions.join('');
    }

    /**
     * Update file item with new data
     */
    update(fileData) {
        this.file = { ...this.file, ...fileData };
        const oldElement = this.element;
        this.render();
        if (oldElement && oldElement.parentNode) {
            oldElement.parentNode.replaceChild(this.element, oldElement);
        }

        // CRITICAL FIX: Re-attach listeners after DOM replacement
        // render() already calls _attachThumbnailListeners(), but we call it again
        // to ensure listeners are properly attached after replaceChild
        this._attachThumbnailListeners();

        return this.element;
    }

    /**
     * Update download progress
     */
    updateDownloadProgress(progress, speed) {
        const progressBar = this.element.querySelector('.progress-bar');
        const statusText = this.element.querySelector('.download-status');
        
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        if (statusText) {
            statusText.textContent = `${formatPercentage(progress)} - ${formatBytes(speed * 1024 * 1024)}/s`;
        }
    }
}

/**
 * Statistics Card Component
 */
class StatCard {
    constructor(title, value, subtitle, icon, type = 'default') {
        this.title = title;
        this.value = value;
        this.subtitle = subtitle;
        this.icon = icon;
        this.type = type;
        this.element = null;
    }

    /**
     * Render statistics card HTML
     */
    render() {
        this.element = document.createElement('div');
        this.element.className = `stat-card card stat-${this.type}`;
        
        this.element.innerHTML = `
            <div class="card-header">
                <h3>${escapeHtml(this.title)}</h3>
                <span class="card-icon">${this.icon}</span>
            </div>
            <div class="card-body">
                <div class="stat-value">${escapeHtml(this.value)}</div>
                <div class="stat-label">${escapeHtml(this.subtitle)}</div>
            </div>
        `;
        
        return this.element;
    }

    /**
     * Update statistics card
     */
    update(value, subtitle) {
        this.value = value;
        if (subtitle) this.subtitle = subtitle;
        
        const valueElement = this.element.querySelector('.stat-value');
        const labelElement = this.element.querySelector('.stat-label');
        
        if (valueElement) valueElement.textContent = this.value;
        if (labelElement && subtitle) labelElement.textContent = this.subtitle;
        
        return this.element;
    }
}

/**
 * Pagination Component
 */
class Pagination {
    constructor(currentPage, totalPages, onPageChange) {
        this.currentPage = currentPage;
        this.totalPages = totalPages;
        this.onPageChange = onPageChange;
        this.element = null;
    }

    /**
     * Render pagination HTML
     */
    render() {
        if (this.totalPages <= 1) {
            return document.createElement('div');
        }

        this.element = document.createElement('div');
        this.element.className = 'pagination';
        
        const buttons = [];
        
        // Previous button
        buttons.push(this.createPageButton(
            '‹',
            this.currentPage - 1,
            this.currentPage <= 1,
            'Vorherige Seite'
        ));
        
        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(this.totalPages, this.currentPage + 2);
        
        if (startPage > 1) {
            buttons.push(this.createPageButton(1, 1, false));
            if (startPage > 2) {
                buttons.push('<span class="pagination-dots">...</span>');
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            buttons.push(this.createPageButton(
                i,
                i,
                false,
                `Seite ${i}`,
                i === this.currentPage
            ));
        }
        
        if (endPage < this.totalPages) {
            if (endPage < this.totalPages - 1) {
                buttons.push('<span class="pagination-dots">...</span>');
            }
            buttons.push(this.createPageButton(this.totalPages, this.totalPages, false));
        }
        
        // Next button
        buttons.push(this.createPageButton(
            '›',
            this.currentPage + 1,
            this.currentPage >= this.totalPages,
            'Nächste Seite'
        ));
        
        this.element.innerHTML = buttons.join('');
        
        // Add event listeners
        this.element.addEventListener('click', (e) => {
            if (e.target.classList.contains('pagination-btn') && !e.target.disabled) {
                const page = parseInt(e.target.getAttribute('data-page'));
                if (page && page !== this.currentPage) {
                    this.onPageChange(page);
                }
            }
        });
        
        return this.element;
    }

    /**
     * Create pagination button HTML
     */
    createPageButton(text, page, disabled = false, title = '', active = false) {
        const classes = ['pagination-btn'];
        if (disabled) classes.push('disabled');
        if (active) classes.push('active');
        
        return `
            <button 
                class="${classes.join(' ')}"
                data-page="${page}"
                ${disabled ? 'disabled' : ''}
                ${title ? `title="${title}"` : ''}
            >
                ${text}
            </button>
        `;
    }

    /**
     * Update pagination
     */
    update(currentPage, totalPages) {
        this.currentPage = currentPage;
        this.totalPages = totalPages;
        
        const oldElement = this.element;
        this.render();
        if (oldElement && oldElement.parentNode) {
            oldElement.parentNode.replaceChild(this.element, oldElement);
        }
        
        return this.element;
    }
}

/**
 * Enhanced Drucker-Dateien File Management Component
 */
class DruckerDateienManager {
    constructor(containerId, printerId = null) {
        this.containerId = containerId;
        this.printerId = printerId;
        this.container = null;
        this.files = [];
        this.downloadProgress = new Map(); // Track individual file download progress
        this.refreshInterval = null;
        this.filters = {
            status: 'all',
            printer: 'all',
            type: 'all',
            search: ''
        };
    }

    /**
     * Initialize the file manager
     */
    async init() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            throw new Error(`Container with ID ${this.containerId} not found`);
        }

        this.render();
        await this.loadFiles();
        
        // Auto-refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadFiles();
        }, 30000);
    }

    /**
     * Render the file manager interface
     */
    render() {
        this.container.innerHTML = `
            <div class="drucker-dateien-manager">
                <div class="file-manager-header">
                    <div class="header-title">
                        <h2>📁 Drucker-Dateien</h2>
                        <span class="subtitle">Einheitliche Verwaltung aller Drucker-Dateien</span>
                    </div>
                    <div class="header-actions">
                        <button class="btn btn-primary" onclick="refreshFiles()" title="Dateien aktualisieren">
                            <span class="btn-icon">🔄</span> Aktualisieren
                        </button>
                        <button class="btn btn-success" onclick="downloadAllAvailable()" title="Alle verfügbaren Dateien herunterladen">
                            <span class="btn-icon">⬇️</span> Alle laden
                        </button>
                    </div>
                </div>

                <div class="selection-controls">
                    <div class="selection-actions">
                        <button class="btn btn-sm btn-secondary" onclick="selectAllFiles()">
                            <span class="btn-icon">☑️</span> Alle auswählen
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="selectNone()">
                            <span class="btn-icon">☐</span> Auswahl aufheben
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="selectAvailable()">
                            <span class="btn-icon">📁</span> Verfügbare auswählen
                        </button>
                    </div>
                </div>

                <div class="file-filters">
                    <div class="filter-group">
                        <label for="status-filter">Status:</label>
                        <select id="status-filter" class="form-control">
                            <option value="all">Alle Status</option>
                            <option value="available">📁 Verfügbar</option>
                            <option value="downloaded">✓ Heruntergeladen</option>
                            <option value="local">💾 Lokal</option>
                            <option value="downloading">⬇️ Lädt herunter</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label for="printer-filter">Drucker:</label>
                        <select id="printer-filter" class="form-control">
                            <option value="all">Alle Drucker</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label for="type-filter">Dateityp:</label>
                        <select id="type-filter" class="form-control">
                            <option value="all">Alle Typen</option>
                            <option value="3mf">📦 3MF</option>
                            <option value="stl">🔺 STL</option>
                            <option value="gcode">⚙️ G-Code</option>
                        </select>
                    </div>
                    
                    <div class="filter-group search-group">
                        <label for="file-search">Suche:</label>
                        <input type="text" id="file-search" class="form-control" placeholder="Dateiname suchen...">
                    </div>
                </div>

                <div class="file-stats">
                    <div class="stat-item">
                        <span class="stat-label">Gesamt:</span>
                        <span class="stat-value" id="total-files">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Verfügbar:</span>
                        <span class="stat-value" id="available-files">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Heruntergeladen:</span>
                        <span class="stat-value" id="downloaded-files">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Gesamtgröße:</span>
                        <span class="stat-value" id="total-size">0 MB</span>
                    </div>
                </div>

                <div class="files-container">
                    <div id="files-list" class="files-list">
                        <div class="loading-state">
                            <div class="spinner"></div>
                            <p>Lade Dateien...</p>
                        </div>
                    </div>
                </div>

                <div class="bulk-actions" style="display: none;">
                    <div class="selected-info">
                        <span id="selected-count">0</span> Dateien ausgewählt
                    </div>
                    <div class="action-buttons">
                        <button class="btn btn-primary" onclick="downloadSelected()">
                            <span class="btn-icon">⬇️</span> Ausgewählte laden
                        </button>
                        <button class="btn btn-error" onclick="deleteSelected()">
                            <span class="btn-icon">🗑️</span> Ausgewählte löschen
                        </button>
                    </div>
                </div>
            </div>
        `;

        this.setupEventListeners();
    }

    /**
     * Setup event listeners for filters and interactions
     */
    setupEventListeners() {
        // Filter change handlers
        const statusFilter = this.container.querySelector('#status-filter');
        const printerFilter = this.container.querySelector('#printer-filter');
        const typeFilter = this.container.querySelector('#type-filter');
        const searchInput = this.container.querySelector('#file-search');

        statusFilter.addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.applyFilters();
        });

        printerFilter.addEventListener('change', (e) => {
            this.filters.printer = e.target.value;
            this.applyFilters();
        });

        typeFilter.addEventListener('change', (e) => {
            this.filters.type = e.target.value;
            this.applyFilters();
        });

        // Search with debouncing
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.filters.search = e.target.value.trim();
                this.applyFilters();
            }, 300);
        });

        // File checkbox change handling using event delegation
        this.container.addEventListener('change', (e) => {
            if (e.target.classList.contains('file-checkbox')) {
                console.log('Checkbox change detected:', e.target.value, 'checked:', e.target.checked);
                this.updateSelectedCount();
                this.updateBulkActions();
            }
        });

        // Also listen for clicks on checkboxes and labels (backup for change event)
        this.container.addEventListener('click', (e) => {
            // Check if click is on checkbox, label, or custom checkbox span
            const checkbox = e.target.classList.contains('file-checkbox') ? e.target :
                           e.target.classList.contains('checkbox-custom') ? e.target.previousElementSibling :
                           e.target.classList.contains('checkbox-label') ? e.target.querySelector('.file-checkbox') :
                           null;
            
            if (checkbox) {
                console.log('Checkbox click detected via delegation:', checkbox.value);
                // Small delay to ensure checkbox state is updated
                setTimeout(() => {
                    this.updateSelectedCount();
                    this.updateBulkActions();
                }, 10);
            }
        });
    }

    /**
     * Load files from all printers or specific printer
     */
    async loadFiles() {
        try {
            let files = [];
            
            if (this.printerId) {
                // Load files for specific printer
                const response = await api.getPrinterFiles(this.printerId);
                files = (response.data?.files || []).map(file => {
                    // Generate proper ID from printer and filename
                    const fileId = file.id && file.id !== 'undefined' ? file.id : `${this.printerId}_${file.filename}`;
                    const fileStatus = file.status && file.status !== 'undefined' ? file.status : 'available';

                    return {
                        ...file,
                        id: fileId,
                        printer_id: this.printerId,
                        status: fileStatus
                    };
                });
            } else {
                // Load files from all printers
                const printers = await api.getPrinters({ active: true });
                for (const printer of printers.data || []) {
                    try {
                        const response = await api.getPrinterFiles(printer.id);
                        const printerFiles = (response.data?.files || []).map(file => {
                            // Generate proper ID from printer and filename
                            const fileId = file.id && file.id !== 'undefined' ? file.id : `${printer.id}_${file.filename}`;
                            const fileStatus = file.status && file.status !== 'undefined' ? file.status : 'available';

                            return {
                                ...file,
                                id: fileId,
                                printer_id: printer.id,
                                printer_name: printer.name,
                                status: fileStatus
                            };
                        });
                        files = files.concat(printerFiles);
                    } catch (error) {
                        Logger.warn(`Failed to load files for printer ${printer.name}:`, error);
                    }
                }
            }

            this.files = files;
            this.updateStats();
            this.updatePrinterFilter();
            this.applyFilters();
            
        } catch (error) {
            Logger.error('Failed to load files:', error);
            this.showError('Fehler beim Laden der Dateien');
        }
    }

    /**
     * Update file statistics
     */
    updateStats() {
        const stats = {
            total: this.files.length,
            available: this.files.filter(f => f.status === 'available').length,
            downloaded: this.files.filter(f => f.status === 'downloaded').length,
            totalSize: this.files.reduce((sum, f) => sum + (f.file_size || 0), 0)
        };

        document.getElementById('total-files').textContent = stats.total;
        document.getElementById('available-files').textContent = stats.available;
        document.getElementById('downloaded-files').textContent = stats.downloaded;
        document.getElementById('total-size').textContent = formatBytes(stats.totalSize);
    }

    /**
     * Update printer filter options
     */
    updatePrinterFilter() {
        const printerFilter = this.container.querySelector('#printer-filter');
        const printers = [...new Set(this.files.map(f => f.printer_name))].sort();
        
        // Clear existing options except "Alle Drucker"
        while (printerFilter.children.length > 1) {
            printerFilter.removeChild(printerFilter.lastChild);
        }
        
        printers.forEach(printerName => {
            if (printerName) {
                const option = document.createElement('option');
                option.value = printerName;
                option.textContent = printerName;
                printerFilter.appendChild(option);
            }
        });
    }

    /**
     * Apply current filters to file list
     */
    applyFilters() {
        let filteredFiles = this.files;

        // Status filter
        if (this.filters.status !== 'all') {
            filteredFiles = filteredFiles.filter(f => f.status === this.filters.status);
        }

        // Printer filter
        if (this.filters.printer !== 'all') {
            filteredFiles = filteredFiles.filter(f => f.printer_name === this.filters.printer);
        }

        // Type filter
        if (this.filters.type !== 'all') {
            filteredFiles = filteredFiles.filter(f => {
                const ext = f.filename.split('.').pop().toLowerCase();
                return ext === this.filters.type;
            });
        }

        // Search filter
        if (this.filters.search) {
            const searchTerm = this.filters.search.toLowerCase();
            filteredFiles = filteredFiles.filter(f => 
                f.filename.toLowerCase().includes(searchTerm)
            );
        }

        this.renderFileList(filteredFiles);
    }

    /**
     * Render filtered file list
     */
    renderFileList(files) {
        const filesList = this.container.querySelector('#files-list');
        
        if (files.length === 0) {
            filesList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📭</div>
                    <h3>Keine Dateien gefunden</h3>
                    <p>Mit den aktuellen Filtern wurden keine Dateien gefunden.</p>
                </div>
            `;
            return;
        }

        const fileItems = files.map(file => this.renderFileItem(file)).join('');
        
        filesList.innerHTML = `
            <div class="files-grid">
                ${fileItems}
            </div>
        `;
    }

    /**
     * Render individual file item
     */
    renderFileItem(file) {
        const status = getStatusConfig('file', file.status);
        const fileIcon = this.getFileIcon(file.filename);
        const downloadProgress = this.downloadProgress.get(file.id);
        const isDownloaded = file.status === 'downloaded';
        const isAvailableForDownload = file.status !== 'downloaded' && file.status !== 'downloading';

        return `
            <div class="file-card ${file.status}" data-file-id="${file.id}">
                <div class="file-header">
                    <div class="file-checkbox-container">
                        <label class="checkbox-label">
                            <input type="checkbox" class="file-checkbox" value="${file.id}"
                                   ${!isAvailableForDownload ? 'disabled' : ''}>
                            <span class="checkbox-custom"></span>
                        </label>
                        ${isDownloaded ? '<span class="downloaded-indicator" title="Bereits heruntergeladen">✅</span>' : ''}
                    </div>
                    <div class="file-icon">${fileIcon}</div>
                    <div class="file-status">
                        <span class="status-badge ${status.class}">${status.icon}</span>
                    </div>
                </div>

                <div class="file-info">
                    <div class="file-name" title="${escapeHtml(file.filename)}">${escapeHtml(file.filename)}</div>
                    <div class="file-details">
                        <span class="file-size">${formatBytes(file.file_size)}</span>
                        ${file.printer_name ? `<span class="file-printer">📟 ${escapeHtml(file.printer_name)}</span>` : ''}
                        ${file.source ? `<span class="file-source">${this.getSourceDisplay(file.source, file.watch_folder_path)}</span>` : ''}
                    </div>
                    <div class="file-meta">
                        <span class="file-date">
                            ${file.created_on_printer ? formatDateTime(file.created_on_printer) : 'Unbekannt'}
                        </span>
                        ${isDownloaded ? '<span class="downloaded-badge">📁 Heruntergeladen</span>' : ''}
                    </div>
                </div>

                ${downloadProgress ? this.renderDownloadProgress(downloadProgress) : ''}

                <div class="file-actions">
                    ${this.renderFileActions(file)}
                </div>
            </div>
        `;
    }

    /**
     * Render file actions based on status
     */
    renderFileActions(file) {
        const actions = [];

        switch (file.status) {
            case 'available':
                actions.push(`
                    <button class="btn btn-sm btn-primary" onclick="downloadFile('${file.id}')" title="Datei herunterladen">
                        <span class="btn-icon">⬇️</span>
                    </button>
                `);
                break;

            case 'downloaded':
                actions.push(`
                    <button class="btn btn-sm btn-success" onclick="openLocalFile('${file.id}')" title="Lokale Datei öffnen">
                        <span class="btn-icon">📂</span>
                    </button>
                    <button class="btn btn-sm btn-error" onclick="deleteLocalFile('${file.id}')" title="Lokale Datei löschen">
                        <span class="btn-icon">🗑️</span>
                    </button>
                `);
                break;

            case 'downloading':
                actions.push(`
                    <button class="btn btn-sm btn-secondary" disabled title="Download läuft">
                        <span class="btn-icon">⏳</span>
                    </button>
                `);
                break;
        }

        // Preview button for supported formats
        if (this.isPreviewSupported(file.filename)) {
            actions.push(`
                <button class="btn btn-sm btn-secondary" onclick="previewFile('${file.id}')" title="Vorschau anzeigen">
                    <span class="btn-icon">👁️</span>
                </button>
            `);
        }

        return actions.join('');
    }

    /**
     * Render download progress for a file
     */
    renderDownloadProgress(progress) {
        return `
            <div class="download-progress-overlay">
                <div class="progress">
                    <div class="progress-bar" style="width: ${progress.percentage}%"></div>
                </div>
                <div class="progress-text">${Math.round(progress.percentage)}% - ${formatBytes(progress.speed * 1024)}/s</div>
            </div>
        `;
    }

    /**
     * Get appropriate icon for file type
     */
    getFileIcon(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        const icons = {
            '3mf': '📦',
            'stl': '🔺',
            'obj': '🔷',
            'gcode': '⚙️',
            'amf': '📄',
            'ply': '🔶'
        };
        return icons[extension] || '📄';
    }

    /**
     * Get display text for file source
     */
    getSourceDisplay(source, watchFolderPath) {
        const sourceIcons = {
            'printer': '🖨️ Drucker',
            'local_watch': '📁 Ordner',
            'local': '💾 Lokal'
        };

        let display = sourceIcons[source] || '❓ Unbekannt';

        // Add folder path for watch folders
        if (source === 'local_watch' && watchFolderPath) {
            const folderName = watchFolderPath.split(/[\\/]/).pop();
            display += `: ${folderName}`;
        }

        return display;
    }

    /**
     * Check if file format supports preview
     */
    isPreviewSupported(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        return ['3mf', 'stl', 'obj'].includes(extension);
    }

    /**
     * Start file download with progress tracking
     */
    async downloadFile(fileId) {
        const file = this.files.find(f => f.id === fileId);

        if (!file) {
            console.error('File not found:', fileId, 'Available:', this.files.map(f => f.id));
            throw new Error(`Datei mit ID ${fileId} nicht gefunden`);
        }

        if (!file.printer_id) {
            console.error('Missing printer_id:', file);
            throw new Error(`Datei "${file.filename}" hat keine Drucker-ID`);
        }

        if (!file.filename) {
            console.error('Missing filename:', file);
            throw new Error(`Datei hat keinen Dateinamen`);
        }

        console.log('Downloading:', { printer_id: file.printer_id, filename: file.filename });

        try {
            // Update file status to downloading
            file.status = 'downloading';
            this.applyFilters();

            // Start download with progress tracking
            await api.downloadPrinterFile(file.printer_id, file.filename, (progress) => {
                this.downloadProgress.set(fileId, {
                    percentage: progress.progress,
                    loaded: progress.loaded,
                    total: progress.total,
                    speed: progress.speed || 0
                });
                
                // Update progress display
                this.updateDownloadProgress(fileId);
            });

            // Download completed
            file.status = 'downloaded';
            this.downloadProgress.delete(fileId);
            this.applyFilters();
            
            showToast(`Datei "${file.filename}" erfolgreich heruntergeladen`, 'success');

        } catch (error) {
            Logger.error('Download failed:', error);
            file.status = 'available'; // Reset status
            this.downloadProgress.delete(fileId);
            this.applyFilters();
            showToast(`Download fehlgeschlagen: ${error.message}`, 'error');
        }
    }

    /**
     * Update download progress display for a specific file
     */
    updateDownloadProgress(fileId) {
        const fileCard = this.container.querySelector(`[data-file-id="${fileId}"]`);
        const progress = this.downloadProgress.get(fileId);

        if (!fileCard || !progress) return;

        let progressOverlay = fileCard.querySelector('.download-progress-overlay');
        if (!progressOverlay) {
            progressOverlay = document.createElement('div');
            progressOverlay.className = 'download-progress-overlay';
            fileCard.appendChild(progressOverlay);
        }

        progressOverlay.innerHTML = this.renderDownloadProgress(progress);
    }

    /**
     * Update selected files count display
     */
    updateSelectedCount() {
        const checkboxes = this.container.querySelectorAll('.file-checkbox:checked');
        const count = checkboxes.length;

        const countElement = this.container.querySelector('#selected-count');
        if (countElement) {
            countElement.textContent = count;
        }
    }

    /**
     * Show/hide bulk actions based on selected files
     */
    updateBulkActions() {
        const checkboxes = this.container.querySelectorAll('.file-checkbox:checked');
        const bulkActions = this.container.querySelector('.bulk-actions');

        if (bulkActions) {
            if (checkboxes.length > 0) {
                bulkActions.style.display = 'flex';
            } else {
                bulkActions.style.display = 'none';
            }
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const filesList = this.container.querySelector('#files-list');
        filesList.innerHTML = `
            <div class="error-state">
                <div class="error-icon">⚠️</div>
                <h3>Fehler</h3>
                <p>${escapeHtml(message)}</p>
                <button class="btn btn-primary" onclick="location.reload()">Seite neu laden</button>
            </div>
        `;
    }

    /**
     * Cleanup when component is destroyed
     */
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Clear any ongoing downloads
        this.downloadProgress.clear();
    }
}

/**
 * Status History Chart Component
 */
class StatusHistoryChart {
    constructor(containerId, printerId) {
        this.containerId = containerId;
        this.printerId = printerId;
        this.container = null;
        this.chart = null;
        this.updateInterval = null;
    }

    /**
     * Initialize the chart
     */
    async init() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            throw new Error(`Container with ID ${this.containerId} not found`);
        }

        this.render();
        await this.loadData();
        
        // Auto-refresh every 2 minutes
        this.updateInterval = setInterval(() => {
            this.loadData();
        }, 120000);
    }

    /**
     * Render chart container
     */
    render() {
        this.container.innerHTML = `
            <div class="status-history-chart">
                <div class="chart-header">
                    <h3>📊 Temperaturverlauf (24h)</h3>
                    <div class="chart-controls">
                        <select class="form-control chart-period" onchange="updateChartPeriod(this.value)">
                            <option value="1">1 Stunde</option>
                            <option value="6">6 Stunden</option>
                            <option value="24" selected>24 Stunden</option>
                            <option value="168">7 Tage</option>
                        </select>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="temperature-chart-${this.printerId}" width="400" height="200"></canvas>
                </div>
                <div class="chart-legend">
                    <div class="legend-item">
                        <span class="legend-color" style="background-color: #ef4444;"></span>
                        <span>Düse</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color" style="background-color: #3b82f6;"></span>
                        <span>Bett</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color" style="background-color: #10b981;"></span>
                        <span>Kammer</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Load historical data and update chart
     * Note: Status history feature is not yet implemented in the backend
     */
    async loadData(hours = 24) {
        // Status history tracking is not yet implemented in backend
        // Display a message instead of attempting to load data
        const canvas = this.container.querySelector(`#temperature-chart-${this.printerId}`);
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#6b7280';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('Statusverlauf noch nicht verfügbar', canvas.width / 2, canvas.height / 2 - 10);
            ctx.font = '14px Arial';
            ctx.fillText('Diese Funktion wird in einer zukünftigen Version hinzugefügt', canvas.width / 2, canvas.height / 2 + 15);
        }
    }

    /**
     * Update chart with new data (simplified implementation)
     */
    updateChart(data) {
        const canvas = this.container.querySelector(`#temperature-chart-${this.printerId}`);
        const ctx = canvas.getContext('2d');
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (!data || data.length === 0) {
            ctx.fillStyle = '#6b7280';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('Keine Daten verfügbar', canvas.width / 2, canvas.height / 2);
            return;
        }

        // Simple line chart implementation
        // Note: In production, you'd use a proper charting library like Chart.js
        this.drawSimpleChart(ctx, canvas, data);
    }

    /**
     * Draw a simple temperature chart
     */
    drawSimpleChart(ctx, canvas, data) {
        const margin = 40;
        const width = canvas.width - margin * 2;
        const height = canvas.height - margin * 2;
        
        // Find min/max temperatures
        let minTemp = 0;
        let maxTemp = 100;
        
        data.forEach(point => {
            if (point.temperature_nozzle) maxTemp = Math.max(maxTemp, point.temperature_nozzle);
            if (point.temperature_bed) maxTemp = Math.max(maxTemp, point.temperature_bed);
        });
        
        maxTemp += 10; // Add some padding
        
        // Draw axes
        ctx.strokeStyle = '#e5e7eb';
        ctx.beginPath();
        ctx.moveTo(margin, margin);
        ctx.lineTo(margin, margin + height);
        ctx.lineTo(margin + width, margin + height);
        ctx.stroke();
        
        // Draw temperature lines
        if (data.length > 1) {
            // Nozzle temperature (red)
            this.drawTemperatureLine(ctx, data, 'temperature_nozzle', '#ef4444', margin, width, height, minTemp, maxTemp);
            
            // Bed temperature (blue)
            this.drawTemperatureLine(ctx, data, 'temperature_bed', '#3b82f6', margin, width, height, minTemp, maxTemp);
        }
        
        // Draw labels
        ctx.fillStyle = '#6b7280';
        ctx.font = '12px Arial';
        ctx.textAlign = 'right';
        ctx.fillText(`${maxTemp}°C`, margin - 5, margin + 5);
        ctx.fillText(`${minTemp}°C`, margin - 5, margin + height + 5);
    }

    /**
     * Draw a temperature line on the chart
     */
    drawTemperatureLine(ctx, data, tempField, color, margin, width, height, minTemp, maxTemp) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        let firstPoint = true;
        data.forEach((point, index) => {
            if (point[tempField] !== undefined) {
                const x = margin + (index / (data.length - 1)) * width;
                const y = margin + height - ((point[tempField] - minTemp) / (maxTemp - minTemp)) * height;
                
                if (firstPoint) {
                    ctx.moveTo(x, y);
                    firstPoint = false;
                } else {
                    ctx.lineTo(x, y);
                }
            }
        });
        
        ctx.stroke();
    }

    /**
     * Show error state
     */
    showError(message) {
        const container = this.container.querySelector('.chart-container');
        container.innerHTML = `
            <div class="chart-error">
                <div class="error-icon">⚠️</div>
                <p>${escapeHtml(message)}</p>
            </div>
        `;
    }

    /**
     * Cleanup when component is destroyed
     */
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

/**
 * Search Component
 */
class SearchBox {
    constructor(placeholder, onSearch, debounceMs = 500) {
        this.placeholder = placeholder;
        this.onSearch = onSearch;
        this.debounceMs = debounceMs;
        this.element = null;
        this.searchTimeout = null;
    }

    /**
     * Render search box HTML
     */
    render() {
        this.element = document.createElement('div');
        this.element.className = 'search-box';
        
        this.element.innerHTML = `
            <div class="search-input-container">
                <input 
                    type="text" 
                    class="form-control search-input" 
                    placeholder="${escapeHtml(this.placeholder)}"
                >
                <button class="search-clear" title="Leeren" style="display: none;">×</button>
            </div>
        `;
        
        const input = this.element.querySelector('.search-input');
        const clearBtn = this.element.querySelector('.search-clear');
        
        // Search on input with debouncing
        input.addEventListener('input', (e) => {
            const value = e.target.value.trim();
            
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
            
            // Show/hide clear button
            clearBtn.style.display = value ? 'block' : 'none';
            
            this.searchTimeout = setTimeout(() => {
                this.onSearch(value);
            }, this.debounceMs);
        });
        
        // Clear search
        clearBtn.addEventListener('click', () => {
            input.value = '';
            clearBtn.style.display = 'none';
            this.onSearch('');
            input.focus();
        });
        
        // Search on Enter
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (this.searchTimeout) {
                    clearTimeout(this.searchTimeout);
                }
                this.onSearch(e.target.value.trim());
            }
        });
        
        return this.element;
    }

    /**
     * Get current search value
     */
    getValue() {
        const input = this.element?.querySelector('.search-input');
        return input ? input.value.trim() : '';
    }

    /**
     * Set search value
     */
    setValue(value) {
        const input = this.element?.querySelector('.search-input');
        const clearBtn = this.element?.querySelector('.search-clear');
        
        if (input) {
            input.value = value;
        }
        
        if (clearBtn) {
            clearBtn.style.display = value ? 'block' : 'none';
        }
    }

    /**
     * Focus search input
     */
    focus() {
        const input = this.element?.querySelector('.search-input');
        if (input) {
            input.focus();
        }
    }
}

// Export components for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        PrinterCard,
        JobListItem,
        FileListItem,
        StatCard,
        Pagination,
        SearchBox,
        DruckerDateienManager,
        StatusHistoryChart
    };
}