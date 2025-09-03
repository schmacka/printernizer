/**
 * Printernizer UI Components
 * Reusable UI components for consistent interface elements
 */

/**
 * Printer Card Component
 */
class PrinterCard {
    constructor(printer) {
        this.printer = printer;
        this.element = null;
    }

    /**
     * Render printer card HTML
     */
    render() {
        const status = getStatusConfig('printer', this.printer.status);
        const printerType = CONFIG.PRINTER_TYPES[this.printer.type] || { label: this.printer.type };
        
        this.element = document.createElement('div');
        this.element.className = `printer-card card status-${this.printer.status}`;
        this.element.setAttribute('data-printer-id', this.printer.id);
        
        this.element.innerHTML = `
            <div class="printer-header">
                <div class="printer-title">
                    <h3>${escapeHtml(this.printer.name)}</h3>
                    <span class="printer-type">${printerType.label}</span>
                </div>
                <div class="printer-actions">
                    <button class="btn btn-sm btn-secondary" onclick="showPrinterDetails('${this.printer.id}')" title="Details anzeigen">
                        <span class="btn-icon">👁️</span>
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="editPrinter('${this.printer.id}')" title="Bearbeiten">
                        <span class="btn-icon">✏️</span>
                    </button>
                </div>
            </div>
            <div class="printer-body">
                <div class="printer-status-row">
                    <div class="printer-status-info">
                        <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
                        <span class="printer-ip text-muted">${this.printer.ip_address}</span>
                    </div>
                    <span class="printer-last-seen text-muted">
                        ${this.printer.last_seen ? `Zuletzt gesehen: ${getRelativeTime(this.printer.last_seen)}` : 'Nie gesehen'}
                    </span>
                </div>
                
                ${this.renderCurrentJob()}
                ${this.renderTemperatures()}
            </div>
        `;
        
        return this.element;
    }

    /**
     * Render current job section
     */
    renderCurrentJob() {
        if (!this.printer.current_job) {
            return '<p class="text-muted text-center">Kein aktiver Auftrag</p>';
        }

        const job = this.printer.current_job;
        const jobStatus = getStatusConfig('job', job.status);
        
        return `
            <div class="current-job" data-job-id="${job.id}">
                <div class="job-name">${escapeHtml(job.name)}</div>
                <div class="job-status">
                    <span class="status-badge ${jobStatus.class}">${jobStatus.icon} ${jobStatus.label}</span>
                </div>
                
                ${job.progress !== undefined ? `
                    <div class="job-progress">
                        <div class="progress-info">
                            <span class="progress-percentage">${formatPercentage(job.progress)}</span>
                            <span class="progress-time estimated-time">
                                ${job.estimated_remaining ? `Noch ${formatDuration(job.estimated_remaining)}` : ''}
                            </span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar" style="width: ${job.progress}%"></div>
                        </div>
                    </div>
                ` : ''}
                
                ${job.layer_current && job.layer_total ? `
                    <div class="layer-info">
                        <span>Schicht: ${job.layer_current}/${job.layer_total}</span>
                        <span>Start: ${job.started_at ? formatTime(job.started_at) : '-'}</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Render temperatures section
     */
    renderTemperatures() {
        if (!this.printer.temperatures) {
            return '';
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
            return '';
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
            tempValue = `${temperature.current}°C`;
            if (temperature.target) {
                tempTarget = `<div class="temp-target">Ziel: ${temperature.target}°C</div>`;
            }
        } else {
            tempValue = `${temperature}°C`;
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
     * Update printer card with new data
     */
    update(printerData) {
        this.printer = { ...this.printer, ...printerData };
        const oldElement = this.element;
        this.render();
        if (oldElement && oldElement.parentNode) {
            oldElement.parentNode.replaceChild(this.element, oldElement);
        }
        return this.element;
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
                    <div class="data-item-title">${escapeHtml(this.job.job_name)}</div>
                    <div class="data-item-subtitle">
                        ${escapeHtml(this.job.printer_name)} • 
                        ${this.job.start_time ? formatDateTime(this.job.start_time) : 'Nicht gestartet'}
                        ${this.job.is_business ? ' • Geschäftlich' : ''}
                    </div>
                </div>
                
                <div class="data-item-meta">
                    <div class="data-item-meta-label">Status</div>
                    <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
                </div>
                
                ${this.renderProgress()}
                
                <div class="data-item-meta">
                    <div class="data-item-meta-label">Kosten</div>
                    <div class="data-item-meta-value">
                        ${this.job.costs ? formatCurrency(this.job.costs.total_cost) : '-'}
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
        if (this.job.status === 'printing' && this.job.progress !== undefined) {
            return `
                <div class="data-item-meta">
                    <div class="data-item-meta-label">Fortschritt</div>
                    <div class="job-progress-container">
                        <div class="progress">
                            <div class="progress-bar" style="width: ${this.job.progress}%"></div>
                        </div>
                        <div class="progress-text">${formatPercentage(this.job.progress)}</div>
                        ${this.job.estimated_completion ? `
                            <div class="estimated-time text-muted">
                                Fertig: ${formatTime(this.job.estimated_completion)}
                            </div>
                        ` : ''}
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
     * Render job action buttons
     */
    renderJobActions() {
        const actions = [];
        
        // View details
        actions.push(`
            <button class="btn btn-sm btn-secondary" onclick="showJobDetails(${this.job.id})" title="Details anzeigen">
                <span class="btn-icon">👁️</span>
            </button>
        `);
        
        // Cancel job if active
        if (['printing', 'queued', 'preparing'].includes(this.job.status)) {
            actions.push(`
                <button class="btn btn-sm btn-warning" onclick="cancelJob(${this.job.id})" title="Auftrag abbrechen">
                    <span class="btn-icon">⏹️</span>
                </button>
            `);
        }
        
        // Edit job info
        actions.push(`
            <button class="btn btn-sm btn-secondary" onclick="editJob(${this.job.id})" title="Bearbeiten">
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
            <div class="file-icon">${this.getFileIcon()}</div>
            
            <div class="file-info">
                <div class="file-name">${escapeHtml(this.file.filename)}</div>
                <div class="file-details">
                    <span class="file-size">${formatBytes(this.file.file_size)}</span>
                    ${this.file.printer_name ? `<span class="file-printer">${escapeHtml(this.file.printer_name)}</span>` : ''}
                    <span class="file-date">
                        ${this.file.created_on_printer ? formatDateTime(this.file.created_on_printer) : formatDateTime(this.file.last_accessed)}
                    </span>
                </div>
            </div>
            
            <div class="file-status">
                <span class="status-badge ${status.class}">${status.icon} ${status.label}</span>
            </div>
            
            ${this.renderDownloadProgress()}
            
            <div class="file-actions">
                ${this.renderFileActions()}
            </div>
        `;
        
        return this.element;
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
        SearchBox
    };
}