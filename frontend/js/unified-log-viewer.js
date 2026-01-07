/**
 * Unified Log Viewer Component
 *
 * Combines logs from multiple sources:
 * - Frontend logs (download, thumbnail, API, system) from localStorage
 * - Backend error logs from server API
 *
 * @class UnifiedLogViewer
 */
class UnifiedLogViewer {
    constructor() {
        this.logs = [];
        this.filteredLogs = [];
        this.currentPage = 1;
        this.perPage = 50;
        this.totalPages = 1;
        this.totalLogs = 0;
        this.activeSource = 'all';
        this.filters = {
            level: '',
            category: '',
            search: '',
            startDate: '',
            endDate: ''
        };
        this.statistics = null;
        this.categories = [];
        this.isLoading = false;
        this.modal = null;
    }

    /**
     * Show the unified log viewer modal
     */
    async show() {
        this.createModal();
        document.body.appendChild(this.modal);

        // Initialize
        await this.loadCategories();
        await this.loadLogs();

        // Close on backdrop click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.close();
        });

        // Close on Escape key
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
    }

    /**
     * Close the modal
     */
    close() {
        if (this.modal) {
            this.modal.remove();
            this.modal = null;
        }
        document.removeEventListener('keydown', this.handleKeyDown.bind(this));
    }

    /**
     * Handle keyboard events
     */
    handleKeyDown(e) {
        if (e.key === 'Escape') {
            this.close();
        }
    }

    /**
     * Create the modal DOM structure
     */
    createModal() {
        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.id = 'unified-log-viewer-modal';
        modal.innerHTML = `
            <div class="modal-content log-viewer-modal unified-log-viewer">
                <div class="modal-header">
                    <h3>System Logs</h3>
                    <button class="modal-close" onclick="unifiedLogViewer.close()">&times;</button>
                </div>
                <div class="modal-body log-viewer-body">
                    <!-- Statistics Bar -->
                    <div class="log-viewer-stats" id="unified-log-stats">
                        <div class="stat-item"><span class="stat-label">Gesamt:</span> <span class="stat-value" id="stat-total">-</span></div>
                        <div class="stat-item"><span class="stat-label">Letzte 24h:</span> <span class="stat-value" id="stat-recent">-</span></div>
                        <div class="stat-item"><span class="stat-label">Fehler:</span> <span class="stat-value stat-error" id="stat-errors">-</span></div>
                        <div class="stat-item"><span class="stat-label">Warnungen:</span> <span class="stat-value stat-warning" id="stat-warnings">-</span></div>
                    </div>

                    <!-- Source Tabs -->
                    <div class="log-source-tabs">
                        <button class="source-tab active" data-source="all" onclick="unifiedLogViewer.setSource('all')">Alle</button>
                        <button class="source-tab" data-source="frontend" onclick="unifiedLogViewer.setSource('frontend')">Frontend</button>
                        <button class="source-tab" data-source="backend" onclick="unifiedLogViewer.setSource('backend')">Backend</button>
                        <button class="source-tab" data-source="errors" onclick="unifiedLogViewer.setSource('errors')">Fehler</button>
                    </div>

                    <!-- Filters -->
                    <div class="log-viewer-filters">
                        <select id="unified-log-level-filter" class="form-control" onchange="unifiedLogViewer.filters.level = this.value">
                            <option value="">Alle Level</option>
                            <option value="debug">DEBUG</option>
                            <option value="info">INFO</option>
                            <option value="warn">WARNING</option>
                            <option value="error">ERROR</option>
                            <option value="critical">CRITICAL</option>
                        </select>
                        <select id="unified-log-category-filter" class="form-control" onchange="unifiedLogViewer.filters.category = this.value">
                            <option value="">Alle Kategorien</option>
                        </select>
                        <input type="text" id="unified-log-search" class="form-control" placeholder="Logs durchsuchen..."
                               onkeyup="unifiedLogViewer.filters.search = this.value; if(event.key === 'Enter') unifiedLogViewer.applyFilters()">
                        <input type="date" id="unified-log-start-date" class="form-control" title="Start Datum"
                               onchange="unifiedLogViewer.filters.startDate = this.value">
                        <input type="date" id="unified-log-end-date" class="form-control" title="End Datum"
                               onchange="unifiedLogViewer.filters.endDate = this.value">
                        <button class="btn btn-sm btn-primary" onclick="unifiedLogViewer.applyFilters()">Filtern</button>
                        <button class="btn btn-sm btn-secondary" onclick="unifiedLogViewer.resetFilters()">Zurucksetzen</button>
                    </div>

                    <!-- Table -->
                    <div class="log-viewer-table-container">
                        <table class="log-viewer-table">
                            <thead>
                                <tr>
                                    <th>Zeit</th>
                                    <th>Quelle</th>
                                    <th>Level</th>
                                    <th>Kategorie</th>
                                    <th>Nachricht</th>
                                </tr>
                            </thead>
                            <tbody id="unified-log-tbody">
                                <tr><td colspan="5" class="log-loading">Logs werden geladen...</td></tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Pagination -->
                    <div class="log-viewer-pagination" id="unified-log-pagination"></div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="unifiedLogViewer.clearLogs()">Logs loschen</button>
                    <button class="btn btn-secondary" onclick="unifiedLogViewer.exportCSV()">Export CSV</button>
                    <button class="btn btn-primary" onclick="unifiedLogViewer.exportJSON()">Export JSON</button>
                </div>
            </div>
        `;
        this.modal = modal;
    }

    /**
     * Load categories from API
     */
    async loadCategories() {
        try {
            const response = await fetch('/api/v1/logs/categories');
            if (response.ok) {
                this.categories = await response.json();
                this.updateCategoryDropdown();
            }
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }

    /**
     * Update the category dropdown with available categories
     */
    updateCategoryDropdown() {
        const select = document.getElementById('unified-log-category-filter');
        if (!select) return;

        // Keep first option (All)
        select.innerHTML = '<option value="">Alle Kategorien</option>';

        // Add frontend categories
        const frontendCategories = ['download', 'thumbnail', 'printer', 'api', 'system'];
        frontendCategories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat.charAt(0).toUpperCase() + cat.slice(1);
            select.appendChild(option);
        });

        // Add backend categories from API
        this.categories.forEach(cat => {
            if (!frontendCategories.includes(cat.toLowerCase())) {
                const option = document.createElement('option');
                option.value = cat;
                option.textContent = cat;
                select.appendChild(option);
            }
        });
    }

    /**
     * Load logs from API and merge with frontend logs
     */
    async loadLogs() {
        this.isLoading = true;
        this.updateTableLoading();

        try {
            // Build query params
            const params = new URLSearchParams();
            if (this.activeSource !== 'all') {
                params.set('source', this.activeSource);
            }
            if (this.filters.level) {
                params.set('level', this.filters.level);
            }
            if (this.filters.category) {
                params.set('category', this.filters.category);
            }
            if (this.filters.search) {
                params.set('search', this.filters.search);
            }
            if (this.filters.startDate) {
                params.set('start_date', new Date(this.filters.startDate).toISOString());
            }
            if (this.filters.endDate) {
                // Set end date to end of day
                const endDate = new Date(this.filters.endDate);
                endDate.setHours(23, 59, 59, 999);
                params.set('end_date', endDate.toISOString());
            }
            params.set('page', this.currentPage);
            params.set('per_page', this.perPage);

            // Fetch from API
            const response = await fetch(`/api/v1/logs?${params}`);
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const result = await response.json();

            // Store results
            this.logs = result.data || [];
            this.totalLogs = result.pagination?.total || 0;
            this.totalPages = result.pagination?.total_pages || 1;
            this.currentPage = result.pagination?.page || 1;
            this.statistics = result.statistics;

            // Merge with frontend logs if viewing all or frontend
            if (this.activeSource === 'all' || this.activeSource === 'frontend') {
                this.mergeFrontendLogs();
            }

            // Update UI
            this.updateStats();
            this.updateTable();
            this.updatePagination();

        } catch (error) {
            console.error('Failed to load logs:', error);
            this.showError('Fehler beim Laden der Logs');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Merge frontend logs from DownloadLogger
     */
    mergeFrontendLogs() {
        // Check if DownloadLogger is available
        if (typeof autoDownloadManager === 'undefined' || !autoDownloadManager.logger) {
            return;
        }

        const frontendLogs = autoDownloadManager.logger.logs || [];

        // Normalize frontend logs to unified format
        const normalizedFrontend = frontendLogs.map(log => ({
            id: log.id || `fe_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            source: 'frontend',
            timestamp: log.timestamp instanceof Date ? log.timestamp.toISOString() : log.timestamp,
            level: log.level || 'info',
            category: log.category || 'system',
            message: log.message || '',
            details: log.data || null
        }));

        // Apply filters to frontend logs
        let filtered = normalizedFrontend;

        if (this.filters.level) {
            const levelPriority = { debug: 0, info: 1, warn: 2, error: 3, critical: 4 };
            const minPriority = levelPriority[this.filters.level] || 0;
            filtered = filtered.filter(log => (levelPriority[log.level] || 0) >= minPriority);
        }

        if (this.filters.category) {
            const cat = this.filters.category.toLowerCase();
            filtered = filtered.filter(log => log.category.toLowerCase() === cat);
        }

        if (this.filters.search) {
            const search = this.filters.search.toLowerCase();
            filtered = filtered.filter(log =>
                log.message.toLowerCase().includes(search) ||
                log.category.toLowerCase().includes(search)
            );
        }

        if (this.filters.startDate) {
            const start = new Date(this.filters.startDate);
            filtered = filtered.filter(log => new Date(log.timestamp) >= start);
        }

        if (this.filters.endDate) {
            const end = new Date(this.filters.endDate);
            end.setHours(23, 59, 59, 999);
            filtered = filtered.filter(log => new Date(log.timestamp) <= end);
        }

        // Merge and sort
        this.logs = [...this.logs, ...filtered].sort((a, b) =>
            new Date(b.timestamp) - new Date(a.timestamp)
        );

        // Update totals (approximate since frontend logs aren't paginated server-side)
        this.totalLogs = this.logs.length;
        this.totalPages = Math.max(1, Math.ceil(this.totalLogs / this.perPage));

        // Paginate client-side
        const start = (this.currentPage - 1) * this.perPage;
        this.logs = this.logs.slice(start, start + this.perPage);
    }

    /**
     * Update statistics display
     */
    updateStats() {
        const stats = this.statistics || { total: 0, last_24h: 0, by_level: {} };

        document.getElementById('stat-total').textContent = this.totalLogs.toLocaleString();
        document.getElementById('stat-recent').textContent = (stats.last_24h || 0).toLocaleString();
        document.getElementById('stat-errors').textContent = (stats.by_level?.error || 0) + (stats.by_level?.critical || 0);
        document.getElementById('stat-warnings').textContent = stats.by_level?.warn || 0;
    }

    /**
     * Update table with loading state
     */
    updateTableLoading() {
        const tbody = document.getElementById('unified-log-tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5" class="log-loading">Logs werden geladen...</td></tr>';
        }
    }

    /**
     * Update the log table
     */
    updateTable() {
        const tbody = document.getElementById('unified-log-tbody');
        if (!tbody) return;

        if (!this.logs || this.logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="log-viewer-empty">Keine Logs gefunden</td></tr>';
            return;
        }

        tbody.innerHTML = this.logs.map(log => this.renderLogRow(log)).join('');
    }

    /**
     * Render a single log row
     */
    renderLogRow(log) {
        const timestamp = new Date(log.timestamp).toLocaleString('de-DE');
        const levelClass = `log-level-${log.level.toLowerCase()}`;
        const sourceClass = `log-source-badge ${log.source}`;
        const message = this.escapeHtml(log.message);

        // Source display names
        const sourceNames = {
            frontend: 'Frontend',
            backend: 'Backend',
            errors: 'Fehler'
        };
        const sourceName = sourceNames[log.source] || log.source;

        return `
            <tr class="log-entry ${levelClass}">
                <td class="log-timestamp">${timestamp}</td>
                <td class="log-source"><span class="${sourceClass}">${sourceName}</span></td>
                <td class="log-level"><span class="level-badge ${levelClass}">${log.level.toUpperCase()}</span></td>
                <td class="log-category">${this.escapeHtml(log.category)}</td>
                <td class="log-message" title="${message}">${message}</td>
            </tr>
        `;
    }

    /**
     * Update pagination controls
     */
    updatePagination() {
        const container = document.getElementById('unified-log-pagination');
        if (!container) return;

        if (this.totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = '<div class="pagination-controls">';

        // Previous button
        html += `<button class="btn btn-sm ${this.currentPage <= 1 ? 'btn-disabled' : 'btn-secondary'}"
                         ${this.currentPage <= 1 ? 'disabled' : ''}
                         onclick="unifiedLogViewer.goToPage(${this.currentPage - 1})">
                    &laquo; Zuruck
                 </button>`;

        // Page info
        html += `<span class="pagination-info">Seite ${this.currentPage} von ${this.totalPages}</span>`;

        // Next button
        html += `<button class="btn btn-sm ${this.currentPage >= this.totalPages ? 'btn-disabled' : 'btn-secondary'}"
                         ${this.currentPage >= this.totalPages ? 'disabled' : ''}
                         onclick="unifiedLogViewer.goToPage(${this.currentPage + 1})">
                    Weiter &raquo;
                 </button>`;

        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Go to a specific page
     */
    goToPage(page) {
        if (page < 1 || page > this.totalPages) return;
        this.currentPage = page;
        this.loadLogs();
    }

    /**
     * Set active source tab
     */
    setSource(source) {
        this.activeSource = source;
        this.currentPage = 1;

        // Update tab styling
        document.querySelectorAll('.source-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.source === source);
        });

        this.loadLogs();
    }

    /**
     * Apply filters and reload
     */
    applyFilters() {
        this.currentPage = 1;
        this.loadLogs();
    }

    /**
     * Reset all filters
     */
    resetFilters() {
        this.filters = {
            level: '',
            category: '',
            search: '',
            startDate: '',
            endDate: ''
        };

        // Reset form inputs
        document.getElementById('unified-log-level-filter').value = '';
        document.getElementById('unified-log-category-filter').value = '';
        document.getElementById('unified-log-search').value = '';
        document.getElementById('unified-log-start-date').value = '';
        document.getElementById('unified-log-end-date').value = '';

        this.currentPage = 1;
        this.loadLogs();
    }

    /**
     * Clear logs
     */
    async clearLogs() {
        if (!confirm('Mochten Sie wirklich alle Logs loschen?')) {
            return;
        }

        try {
            // Clear backend logs
            const params = this.activeSource !== 'all' ? `?source=${this.activeSource}` : '';
            const response = await fetch(`/api/v1/logs${params}`, { method: 'DELETE' });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            // Clear frontend logs if applicable
            if (this.activeSource === 'all' || this.activeSource === 'frontend') {
                if (typeof autoDownloadManager !== 'undefined' && autoDownloadManager.logger) {
                    autoDownloadManager.logger.clearLogs();
                }
            }

            // Reload
            this.currentPage = 1;
            await this.loadLogs();

            if (typeof showToast === 'function') {
                showToast('success', 'Logs geloscht', 'Alle Logs wurden erfolgreich geloscht');
            }
        } catch (error) {
            console.error('Failed to clear logs:', error);
            this.showError('Fehler beim Loschen der Logs');
        }
    }

    /**
     * Export logs as CSV
     */
    async exportCSV() {
        try {
            const params = this.buildExportParams();
            params.set('format', 'csv');

            const response = await fetch(`/api/v1/logs/export?${params}`);
            if (!response.ok) {
                throw new Error(`Export failed: ${response.status}`);
            }

            const blob = await response.blob();
            this.downloadBlob(blob, `printernizer_logs_${this.getDateString()}.csv`);

            if (typeof showToast === 'function') {
                showToast('success', 'Export erfolgreich', 'Logs wurden als CSV exportiert');
            }
        } catch (error) {
            console.error('Failed to export CSV:', error);
            this.showError('Fehler beim CSV-Export');
        }
    }

    /**
     * Export logs as JSON
     */
    async exportJSON() {
        try {
            const params = this.buildExportParams();
            params.set('format', 'json');

            const response = await fetch(`/api/v1/logs/export?${params}`);
            if (!response.ok) {
                throw new Error(`Export failed: ${response.status}`);
            }

            const blob = await response.blob();
            this.downloadBlob(blob, `printernizer_logs_${this.getDateString()}.json`);

            if (typeof showToast === 'function') {
                showToast('success', 'Export erfolgreich', 'Logs wurden als JSON exportiert');
            }
        } catch (error) {
            console.error('Failed to export JSON:', error);
            this.showError('Fehler beim JSON-Export');
        }
    }

    /**
     * Build export query parameters
     */
    buildExportParams() {
        const params = new URLSearchParams();
        if (this.activeSource !== 'all') {
            params.set('source', this.activeSource);
        }
        if (this.filters.level) {
            params.set('level', this.filters.level);
        }
        if (this.filters.category) {
            params.set('category', this.filters.category);
        }
        if (this.filters.search) {
            params.set('search', this.filters.search);
        }
        if (this.filters.startDate) {
            params.set('start_date', new Date(this.filters.startDate).toISOString());
        }
        if (this.filters.endDate) {
            const endDate = new Date(this.filters.endDate);
            endDate.setHours(23, 59, 59, 999);
            params.set('end_date', endDate.toISOString());
        }
        return params;
    }

    /**
     * Download a blob as file
     */
    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Get current date as string for filenames
     */
    getDateString() {
        return new Date().toISOString().split('T')[0];
    }

    /**
     * Show error message
     */
    showError(message) {
        if (typeof showToast === 'function') {
            showToast('error', 'Fehler', message);
        } else {
            alert(message);
        }
    }

    /**
     * Escape HTML entities
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global instance
let unifiedLogViewer = null;

/**
 * Show the unified log viewer
 */
function showUnifiedLogs() {
    if (unifiedLogViewer) {
        unifiedLogViewer.close();
    }
    unifiedLogViewer = new UnifiedLogViewer();
    unifiedLogViewer.show();
}
