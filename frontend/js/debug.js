/**
 * Debug Management
 * Handles debug information, logs, and system health monitoring
 */

class DebugManager {
    constructor() {
        this.logs = [];
        this.healthData = null;
        this.metricsData = null;
        this.apiTests = [];
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;
        this.logLevelFilter = '';
        this.maxLogEntries = 1000;
    }

    /**
     * Initialize debug page
     */
    async init() {
        console.log('Initializing debug manager');

        // Load all debug information with individual error handling
        await Promise.allSettled([
            this.refreshHealthInfo(),
            this.loadApplicationLogs(),
            this.loadPerformanceMetrics(),
            this.loadThumbnailLog(),
            this.runAPITests()
        ]).then(results => {
            results.forEach((result, index) => {
                if (result.status === 'rejected') {
                    console.error(`Failed to load component ${index}:`, result.reason);
                }
            });
        });

        // Setup form handlers and auto-refresh
        this.setupEventHandlers();
        this.startAutoRefresh();

        this.lastRefresh = new Date();
        console.log('Debug manager initialized');
    }

    /**
     * Cleanup when leaving page
     */
    cleanup() {
        this.stopAutoRefresh();
    }

    /**
     * Setup event handlers
     */
    setupEventHandlers() {
        // Auto-refresh checkbox
        const autoRefreshCheckbox = document.getElementById('autoRefreshLogs');
        if (autoRefreshCheckbox) {
            autoRefreshCheckbox.addEventListener('change', (e) => {
                this.autoRefreshEnabled = e.target.checked;
                if (this.autoRefreshEnabled) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }

        // Log level filter
        const logLevelFilter = document.getElementById('logLevelFilter');
        if (logLevelFilter) {
            logLevelFilter.addEventListener('change', (e) => {
                this.logLevelFilter = e.target.value;
                this.filterAndDisplayLogs();
            });
        }
    }

    /**
     * Start auto-refresh interval
     */
    startAutoRefresh() {
        this.stopAutoRefresh(); // Clear any existing interval
        
        if (this.autoRefreshEnabled) {
            this.refreshInterval = setInterval(() => {
                this.refreshDebugInfo();
            }, 10000); // Refresh every 10 seconds
        }
    }

    /**
     * Stop auto-refresh interval
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Refresh all debug information
     */
    async refreshDebugInfo() {
        try {
            await Promise.allSettled([
                this.refreshHealthInfo(),
                this.loadApplicationLogs(),
                this.loadPerformanceMetrics(),
                this.loadThumbnailLog(),
                this.runAPITests()
            ]).then(results => {
                results.forEach((result, index) => {
                    if (result.status === 'rejected') {
                        console.error(`Failed to refresh component ${index}:`, result.reason);
                    }
                });
            });

            this.lastRefresh = new Date();
            console.log('Debug info refreshed');

        } catch (error) {
            console.error('Failed to refresh debug info:', error);
        }
    }

    /**
     * Load and display system health information
     */
    async refreshHealthInfo() {
        try {
            this.healthData = await api.getHealth();
            this.displayHealthInfo();

        } catch (error) {
            console.error('Failed to load health info:', error);
            this.displayHealthError();
        }
    }

    /**
     * Display system health information
     */
    displayHealthInfo() {
        const container = document.getElementById('healthInfo');
        if (!container || !this.healthData) return;

        const statusIcon = this.getStatusIcon(this.healthData.status);
        const statusClass = `health-status-${this.healthData.status}`;

        container.innerHTML = `
            <div class="health-overview ${statusClass}">
                <div class="health-header">
                    <span class="health-icon">${statusIcon}</span>
                    <h4>System-Status: ${this.healthData.status.toUpperCase()}</h4>
                    <span class="health-timestamp">
                        Letzte Aktualisierung: ${new Date(this.healthData.timestamp).toLocaleString('de-DE')}
                    </span>
                </div>
                
                <div class="health-grid">
                    <div class="health-card">
                        <h5>🎯 Anwendung</h5>
                        <div class="health-details">
                            <div class="detail-item">
                                <span class="label">Version:</span>
                                <span class="value">${this.healthData.version}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Umgebung:</span>
                                <span class="value">${this.healthData.environment}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="health-card">
                        <h5>🗄️ Datenbank</h5>
                        <div class="health-details">
                            <div class="detail-item">
                                <span class="label">Status:</span>
                                <span class="value ${this.healthData.database.healthy ? 'healthy' : 'unhealthy'}">
                                    ${this.healthData.database.healthy ? '✅ Gesund' : '❌ Problematisch'}
                                </span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Typ:</span>
                                <span class="value">${this.healthData.database.type.toUpperCase()}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Verbindungen:</span>
                                <span class="value">${this.healthData.database.connection_count || 0}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="health-card">
                        <h5>🔧 Services</h5>
                        <div class="health-details">
                            ${Object.entries(this.healthData.services).map(([service, serviceInfo]) => `
                                <div class="detail-item">
                                    <span class="label">${service}:</span>
                                    <span class="value ${serviceInfo.status === 'healthy' ? 'healthy' : 'unhealthy'}">
                                        ${serviceInfo.status === 'healthy' ? '✅' : '❌'} ${serviceInfo.status}
                                    </span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Display health error message
     */
    displayHealthError() {
        const container = document.getElementById('healthInfo');
        if (!container) return;

        container.innerHTML = `
            <div class="health-error">
                <div class="error-icon">❌</div>
                <h4>System-Status nicht verfügbar</h4>
                <p>Die Gesundheitsinformationen konnten nicht abgerufen werden.</p>
                <button class="btn btn-secondary" onclick="debugManager.refreshHealthInfo()">
                    <span class="btn-icon">🔄</span>
                    Erneut versuchen
                </button>
            </div>
        `;
    }

    /**
     * Load application logs
     */
    async loadApplicationLogs() {
        try {
            // For now, simulate logs since we don't have a logs endpoint yet
            // In a real implementation, this would fetch from /api/v1/system/logs
            this.simulateLogEntries();
            this.filterAndDisplayLogs();

        } catch (error) {
            console.error('Failed to load logs:', error);
            this.displayLogsError();
        }
    }

    /**
     * Simulate log entries (for development)
     */
    simulateLogEntries() {
        const currentTime = new Date();
        const logLevels = ['INFO', 'WARNING', 'ERROR', 'DEBUG'];
        const logMessages = [
            'Application started successfully',
            'Printer connection established: Bambu Lab A1',
            'Job monitoring started for printer: prusa-001',
            'File download completed: test_model.3mf',
            'Database connection healthy',
            'WebSocket connection opened',
            'Settings updated by user',
            'Health check completed',
            'Performance metrics collected'
        ];

        // Add some sample logs if empty
        if (this.logs.length === 0) {
            for (let i = 0; i < 20; i++) {
                const timestamp = new Date(currentTime.getTime() - (i * 60000)); // 1 minute apart
                const level = logLevels[Math.floor(Math.random() * logLevels.length)];
                const message = logMessages[Math.floor(Math.random() * logMessages.length)];
                
                this.logs.unshift({
                    timestamp: timestamp.toISOString(),
                    level: level,
                    message: message,
                    logger: 'printernizer.main'
                });
            }
        }

        // Add a new recent log entry
        this.logs.unshift({
            timestamp: currentTime.toISOString(),
            level: 'INFO',
            message: 'Debug page refreshed',
            logger: 'printernizer.debug'
        });

        // Keep only the latest entries
        if (this.logs.length > this.maxLogEntries) {
            this.logs = this.logs.slice(0, this.maxLogEntries);
        }
    }

    /**
     * Filter and display logs based on current filter
     */
    filterAndDisplayLogs() {
        let filteredLogs = this.logs;

        // Apply level filter
        if (this.logLevelFilter) {
            const levelPriority = { 'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3 };
            const minPriority = levelPriority[this.logLevelFilter];
            
            filteredLogs = this.logs.filter(log => {
                const logPriority = levelPriority[log.level];
                return logPriority >= minPriority;
            });
        }

        this.displayLogs(filteredLogs);
    }

    /**
     * Display logs in the viewer
     */
    displayLogs(logs) {
        const container = document.getElementById('logViewer');
        if (!container) return;

        if (logs.length === 0) {
            container.innerHTML = `
                <div class="logs-empty">
                    <div class="empty-icon">📄</div>
                    <h4>Keine Protokolle gefunden</h4>
                    <p>Keine Protokolleinträge entsprechen dem aktuellen Filter.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="logs-header">
                <span class="logs-count">${logs.length} Einträge gefunden</span>
                <span class="logs-updated">Letzte Aktualisierung: ${new Date().toLocaleString('de-DE')}</span>
            </div>
            <div class="logs-list">
                ${logs.map(log => this.formatLogEntry(log)).join('')}
            </div>
        `;
    }

    /**
     * Format a single log entry
     */
    formatLogEntry(log) {
        const timestamp = new Date(log.timestamp).toLocaleString('de-DE');
        const levelClass = `log-level-${log.level.toLowerCase()}`;
        const levelIcon = this.getLogLevelIcon(log.level);

        return `
            <div class="log-entry ${levelClass}">
                <div class="log-timestamp">${timestamp}</div>
                <div class="log-level">
                    <span class="level-icon">${levelIcon}</span>
                    ${log.level}
                </div>
                <div class="log-logger">${log.logger}</div>
                <div class="log-message">${log.message}</div>
            </div>
        `;
    }

    /**
     * Load performance metrics
     */
    async loadPerformanceMetrics() {
        try {
            // For now, simulate metrics since we don't have a metrics endpoint yet
            // In a real implementation, this would fetch from /api/v1/system/metrics
            this.simulateMetrics();
            this.displayMetrics();

        } catch (error) {
            console.error('Failed to load metrics:', error);
            this.displayMetricsError();
        }
    }

    /**
     * Simulate performance metrics (for development)
     */
    simulateMetrics() {
        this.metricsData = {
            requests_total: Math.floor(Math.random() * 10000) + 5000,
            requests_per_minute: Math.floor(Math.random() * 50) + 10,
            response_time_avg: (Math.random() * 200 + 50).toFixed(2),
            active_connections: Math.floor(Math.random() * 10) + 1,
            memory_usage: Math.floor(Math.random() * 30 + 40), // %
            cpu_usage: Math.floor(Math.random() * 20 + 5), // %
            disk_usage: Math.floor(Math.random() * 15 + 25), // %
            uptime: Math.floor(Date.now() / 1000 - Math.random() * 86400) // seconds
        };
    }

    /**
     * Display performance metrics
     */
    displayMetrics() {
        const container = document.getElementById('performanceMetrics');
        if (!container || !this.metricsData) return;

        const uptimeFormatted = this.formatUptime(this.metricsData.uptime);

        container.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-icon">📊</span>
                        <h5>Anfragen</h5>
                    </div>
                    <div class="metric-value">${this.metricsData.requests_total.toLocaleString()}</div>
                    <div class="metric-label">Gesamt</div>
                    <div class="metric-detail">${this.metricsData.requests_per_minute}/min aktuell</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-icon">⚡</span>
                        <h5>Antwortzeit</h5>
                    </div>
                    <div class="metric-value">${this.metricsData.response_time_avg}ms</div>
                    <div class="metric-label">Durchschnitt</div>
                    <div class="metric-detail">${this.metricsData.active_connections} aktive Verbindungen</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-icon">🧠</span>
                        <h5>Speicher</h5>
                    </div>
                    <div class="metric-value">${this.metricsData.memory_usage}%</div>
                    <div class="metric-label">Verbrauch</div>
                    <div class="metric-progress">
                        <div class="progress-bar" style="width: ${this.metricsData.memory_usage}%"></div>
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-icon">🔋</span>
                        <h5>CPU</h5>
                    </div>
                    <div class="metric-value">${this.metricsData.cpu_usage}%</div>
                    <div class="metric-label">Auslastung</div>
                    <div class="metric-progress">
                        <div class="progress-bar" style="width: ${this.metricsData.cpu_usage}%"></div>
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-icon">💾</span>
                        <h5>Festplatte</h5>
                    </div>
                    <div class="metric-value">${this.metricsData.disk_usage}%</div>
                    <div class="metric-label">Belegt</div>
                    <div class="metric-progress">
                        <div class="progress-bar" style="width: ${this.metricsData.disk_usage}%"></div>
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-icon">⏰</span>
                        <h5>Betriebszeit</h5>
                    </div>
                    <div class="metric-value">${uptimeFormatted.value}</div>
                    <div class="metric-label">${uptimeFormatted.unit}</div>
                    <div class="metric-detail">Seit letztem Neustart</div>
                </div>
            </div>
        `;
    }

    /**
     * Run API endpoint tests
     */
    async runAPITests() {
        const endpoints = [
            { name: 'Health', url: `${CONFIG.API_BASE_URL}/health`, method: 'GET' },
            { name: 'Printers', url: `${CONFIG.API_BASE_URL}/printers`, method: 'GET' },
            { name: 'Jobs', url: `${CONFIG.API_BASE_URL}/jobs`, method: 'GET' },
            { name: 'Files', url: `${CONFIG.API_BASE_URL}/files`, method: 'GET' },
            { name: 'Settings', url: `${CONFIG.API_BASE_URL}/settings/application`, method: 'GET' }
        ];

        const testResults = [];

        for (const endpoint of endpoints) {
            try {
                const startTime = performance.now();
                const response = await fetch(endpoint.url, { method: endpoint.method });
                const endTime = performance.now();
                const responseTime = Math.round(endTime - startTime);

                testResults.push({
                    name: endpoint.name,
                    url: endpoint.url,
                    method: endpoint.method,
                    status: response.status,
                    responseTime: responseTime,
                    success: response.ok
                });

            } catch (error) {
                testResults.push({
                    name: endpoint.name,
                    url: endpoint.url,
                    method: endpoint.method,
                    status: 'ERROR',
                    responseTime: '-',
                    success: false,
                    error: error.message
                });
            }
        }

        this.apiTests = testResults;
        this.displayAPITests();
    }

    /**
     * Display API test results
     */
    displayAPITests() {
        const container = document.getElementById('apiTests');
        if (!container) return;

        container.innerHTML = `
            <div class="api-tests-header">
                <h4>Endpoint-Tests</h4>
                <button class="btn btn-small btn-secondary" onclick="debugManager.runAPITests()">
                    <span class="btn-icon">🔄</span>
                    Tests ausführen
                </button>
            </div>
            <div class="api-tests-list">
                ${this.apiTests.map(test => `
                    <div class="api-test-item ${test.success ? 'test-success' : 'test-failure'}">
                        <div class="test-status">
                            ${test.success ? '✅' : '❌'}
                        </div>
                        <div class="test-info">
                            <div class="test-name">${test.name}</div>
                            <div class="test-details">
                                <span class="test-method">${test.method}</span>
                                <span class="test-url">${test.url}</span>
                                <span class="test-status-code ${test.success ? 'status-ok' : 'status-error'}">
                                    ${test.status}
                                </span>
                                <span class="test-response-time">${test.responseTime}ms</span>
                            </div>
                            ${test.error ? `<div class="test-error">${test.error}</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Helper methods
     */
    getStatusIcon(status) {
        switch (status) {
            case 'healthy': return '✅';
            case 'degraded': return '⚠️';
            case 'unhealthy': return '❌';
            default: return '❓';
        }
    }

    getLogLevelIcon(level) {
        switch (level) {
            case 'DEBUG': return '🐛';
            case 'INFO': return 'ℹ️';
            case 'WARNING': return '⚠️';
            case 'ERROR': return '❌';
            default: return '📝';
        }
    }

    formatUptime(seconds) {
        if (seconds < 60) {
            return { value: Math.round(seconds), unit: 'Sekunden' };
        } else if (seconds < 3600) {
            return { value: Math.round(seconds / 60), unit: 'Minuten' };
        } else if (seconds < 86400) {
            return { value: Math.round(seconds / 3600), unit: 'Stunden' };
        } else {
            return { value: Math.round(seconds / 86400), unit: 'Tage' };
        }
    }

    /**
     * Display error messages
     */
    /**
     * Refresh thumbnail processing log (alias for button onclick)
     */
    async refreshThumbnailLog() {
        await this.loadThumbnailLog();
    }

    /**
     * Load thumbnail processing log
     */
    async loadThumbnailLog() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/debug/thumbnail-processing-log`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.thumbnailLog = await response.json();
            this.displayThumbnailLog();
        } catch (error) {
            console.error('Failed to load thumbnail processing log:', error);
            this.displayThumbnailLogError();
        }
    }

    /**
     * Display thumbnail processing log
     */
    displayThumbnailLog() {
        const container = document.getElementById('thumbnailLogViewer');
        if (!container) return;

        if (!this.thumbnailLog || !this.thumbnailLog.recent_attempts || this.thumbnailLog.recent_attempts.length === 0) {
            container.innerHTML = `
                <div class="thumbnail-log-empty">
                    <div class="empty-icon">📷</div>
                    <h4>Keine Thumbnail-Verarbeitungsaktivität</h4>
                    <p>Es wurden noch keine Thumbnails verarbeitet.</p>
                </div>
            `;
            return;
        }

        // Display summary statistics
        const stats = this.thumbnailLog.summary;
        const statsHtml = `
            <div class="thumbnail-stats">
                <div class="stat-item">
                    <span class="stat-label">Gesamt:</span>
                    <span class="stat-value">${stats.total_entries}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Erfolgreich:</span>
                    <span class="stat-value success">${stats.successful}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Fehlgeschlagen:</span>
                    <span class="stat-value error">${stats.failed}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Erfolgsrate:</span>
                    <span class="stat-value">${stats.success_rate}%</span>
                </div>
            </div>
        `;

        // Display file type breakdown
        let fileTypesHtml = '';
        if (stats.file_types && Object.keys(stats.file_types).length > 0) {
            const fileTypesList = Object.entries(stats.file_types)
                .map(([type, count]) => `<span class="file-type-badge">${type}: ${count}</span>`)
                .join('');
            fileTypesHtml = `
                <div class="file-types">
                    <span class="file-types-label">Dateitypen:</span>
                    ${fileTypesList}
                </div>
            `;
        }

        // Display log entries
        const entriesHtml = this.thumbnailLog.recent_attempts.map(entry => {
            const timestamp = new Date(entry.timestamp).toLocaleString('de-DE');
            const statusClass = entry.success ? 'success' : 'error';
            const statusIcon = entry.success ? '✅' : '❌';
            const errorInfo = entry.error ? `<div class="error-details">${entry.error}</div>` : '';
            
            return `
                <div class="thumbnail-log-entry ${statusClass}">
                    <div class="entry-header">
                        <span class="entry-timestamp">${timestamp}</span>
                        <span class="entry-status">
                            <span class="status-icon">${statusIcon}</span>
                            ${entry.success ? 'Erfolgreich' : 'Fehlgeschlagen'}
                        </span>
                    </div>
                    <div class="entry-details">
                        <span class="file-name">${entry.filename}</span>
                        <span class="file-type-badge">${entry.file_type}</span>
                        ${entry.dimensions ? `<span class="dimensions">${entry.dimensions.width}x${entry.dimensions.height}</span>` : ''}
                    </div>
                    ${errorInfo}
                </div>
            `;
        }).join('');

        container.innerHTML = `
            <div class="thumbnail-log-content">
                ${statsHtml}
                ${fileTypesHtml}
                <div class="thumbnail-log-entries">
                    ${entriesHtml}
                </div>
            </div>
        `;
    }

    /**
     * Display thumbnail processing log error
     */
    displayThumbnailLogError() {
        const container = document.getElementById('thumbnailLogViewer');
        if (!container) return;

        container.innerHTML = `
            <div class="thumbnail-log-error">
                <div class="error-icon">⚠️</div>
                <h4>Thumbnail-Protokoll nicht verfügbar</h4>
                <p>Das Thumbnail-Verarbeitungsprotokoll konnte nicht geladen werden.</p>
            </div>
        `;
    }

    displayLogsError() {
        const container = document.getElementById('logViewer');
        if (!container) return;

        container.innerHTML = `
            <div class="logs-error">
                <div class="error-icon">⚠️</div>
                <h4>Protokolle nicht verfügbar</h4>
                <p>Die Anwendungsprotokolle konnten nicht geladen werden.</p>
            </div>
        `;
    }

    displayMetricsError() {
        const container = document.getElementById('performanceMetrics');
        if (!container) return;

        container.innerHTML = `
            <div class="metrics-error">
                <div class="error-icon">📊</div>
                <h4>Metriken nicht verfügbar</h4>
                <p>Die Performance-Metriken konnten nicht geladen werden.</p>
            </div>
        `;
    }
}

/**
 * Global debug manager instance
 */
const debugManager = new DebugManager();

/**
 * Global functions for debug page
 */
function refreshDebugInfo() {
    debugManager.refreshDebugInfo();
}

function refreshThumbnailLog() {
    debugManager.refreshThumbnailLog();
}

function clearLogs() {
    const confirmed = confirm('Sind Sie sicher, dass Sie alle Protokolle löschen möchten?');
    if (confirmed) {
        debugManager.logs = [];
        debugManager.filterAndDisplayLogs();
        showToast('success', 'Protokolle gelöscht', 'Alle Protokolleinträge wurden entfernt');
    }
}

function downloadLogs() {
    if (debugManager.logs.length === 0) {
        showToast('info', 'Keine Protokolle', 'Es sind keine Protokolle zum Herunterladen verfügbar');
        return;
    }

    const logText = debugManager.logs.map(log => 
        `${log.timestamp} [${log.level}] ${log.logger}: ${log.message}`
    ).join('\n');

    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `printernizer-logs-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('success', 'Protokolle heruntergeladen', 'Protokolldatei wurde gespeichert');
}

// Export for use in main.js
if (typeof window !== 'undefined') {
    window.debugManager = debugManager;
}