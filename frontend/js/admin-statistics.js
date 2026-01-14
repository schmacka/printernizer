/**
 * Admin Statistics Dashboard Manager
 * Displays global installation statistics from aggregation service
 * Phase 3: Usage Statistics Analytics Dashboard
 */

class AdminStatisticsManager {
    constructor() {
        this.aggregationUrl = null;
        this.apiKey = null;
        this.charts = {};
        this.data = null;
        this.initialized = false;
    }

    /**
     * Initialize the admin statistics dashboard
     */
    async init() {
        if (this.initialized) {
            return;
        }

        Logger.debug('Initializing admin statistics dashboard');

        try {
            this.loadConfig();

            // If we have saved config, try to connect automatically
            if (this.aggregationUrl && this.apiKey) {
                await this.connect();
            }

            this.initialized = true;
            Logger.debug('Admin statistics dashboard initialized');
        } catch (error) {
            Logger.error('Failed to initialize admin statistics:', error);
        }
    }

    /**
     * Load saved configuration from localStorage
     */
    loadConfig() {
        this.aggregationUrl = localStorage.getItem('aggregation_service_url');
        this.apiKey = localStorage.getItem('aggregation_api_key');

        // Populate form fields if elements exist
        const urlInput = document.getElementById('aggregationUrl');
        const keyInput = document.getElementById('aggregationApiKey');

        if (urlInput && this.aggregationUrl) {
            urlInput.value = this.aggregationUrl;
        }
        if (keyInput && this.apiKey) {
            keyInput.value = '********'; // Mask stored API key
        }
    }

    /**
     * Save configuration to localStorage
     */
    saveConfig() {
        const urlInput = document.getElementById('aggregationUrl');
        const keyInput = document.getElementById('aggregationApiKey');

        if (urlInput) {
            this.aggregationUrl = urlInput.value.trim();
        }

        // Only update API key if it was changed from mask
        if (keyInput && keyInput.value && keyInput.value !== '********') {
            this.apiKey = keyInput.value.trim();
        }

        if (this.aggregationUrl) {
            localStorage.setItem('aggregation_service_url', this.aggregationUrl);
        }
        if (this.apiKey) {
            localStorage.setItem('aggregation_api_key', this.apiKey);
        }
    }

    /**
     * Connect to aggregation service and load dashboard
     */
    async connect() {
        this.saveConfig();

        if (!this.aggregationUrl || !this.apiKey) {
            showToast('error', 'Configuration Required',
                'Please provide URL and API key');
            return;
        }

        // Show loading state
        this.showLoading();

        try {
            const response = await this.fetchStats('/stats/overview');

            // Hide config form, show dashboard
            const configEl = document.getElementById('aggregationServiceConfig');
            const dashboardEl = document.getElementById('globalStatsDashboard');

            if (configEl) configEl.style.display = 'none';
            if (dashboardEl) dashboardEl.style.display = 'block';

            // Render the dashboard
            await this.renderDashboard(response);

            showToast('success', 'Connected',
                'Successfully connected to aggregation service');

        } catch (error) {
            Logger.error('Failed to connect to aggregation service', error);
            this.showError(error.message);
            showToast('error', 'Connection Failed', error.message);
        }
    }

    /**
     * Fetch statistics from aggregation service
     */
    async fetchStats(endpoint) {
        const url = this.aggregationUrl.replace(/\/$/, '') + endpoint;

        const response = await fetch(url, {
            headers: {
                'X-API-Key': this.apiKey,
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Invalid API key');
            }
            if (response.status === 429) {
                throw new Error('Rate limit exceeded');
            }
            throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
    }

    /**
     * Refresh dashboard data
     */
    async refresh() {
        if (!this.aggregationUrl || !this.apiKey) {
            return;
        }

        try {
            const data = await this.fetchStats('/stats/overview');
            await this.renderDashboard(data);
            showToast('success', 'Refreshed', 'Statistics updated');
        } catch (error) {
            Logger.error('Failed to refresh statistics', error);
            showToast('error', 'Refresh Failed', error.message);
        }
    }

    /**
     * Render the complete dashboard
     */
    async renderDashboard(data) {
        this.data = data;

        // Update overview cards
        this.updateOverviewCards(data.installations);

        // Update timestamp
        this.updateTimestamp(data.last_updated);

        // Render anomaly alerts
        this.renderAnomalyAlerts(data.anomalies);

        // Render charts (only if Chart.js is loaded)
        if (typeof Chart !== 'undefined') {
            this.renderInstallationsChart(data.installations?.trend || []);
            this.renderDeploymentChart(data.deployment_modes);
            this.renderVersionsChart(data.versions);
            this.renderGeographyChart(data.geography);
            this.renderFeatureUsageChart(data.features);
        } else {
            Logger.warn('Chart.js not loaded, skipping chart rendering');
        }
    }

    /**
     * Update overview statistic cards
     */
    updateOverviewCards(installations) {
        if (!installations) return;

        const setCard = (id, value, isGrowth = false) => {
            const el = document.getElementById(id);
            if (!el) return;

            el.textContent = value;

            // Add color class for growth
            if (isGrowth) {
                el.classList.remove('positive', 'negative');
                const numValue = parseFloat(value);
                if (numValue > 0) {
                    el.classList.add('positive');
                } else if (numValue < 0) {
                    el.classList.add('negative');
                }
            }
        };

        setCard('totalInstallations', (installations.total || 0).toLocaleString());
        setCard('active7d', (installations.active_7d || 0).toLocaleString());
        setCard('active30d', (installations.active_30d || 0).toLocaleString());

        const growth = installations.growth_7d_percent || 0;
        setCard('growth7d', `${growth > 0 ? '+' : ''}${growth.toFixed(1)}%`, true);
    }

    /**
     * Update last updated timestamp
     */
    updateTimestamp(timestamp) {
        const el = document.getElementById('statsLastUpdated');
        if (!el || !timestamp) return;

        const date = new Date(timestamp);
        el.textContent = `Last updated: ${date.toLocaleString()}`;
    }

    /**
     * Render installations trend line chart
     */
    renderInstallationsChart(trendData) {
        const ctx = document.getElementById('installationsChart')?.getContext('2d');
        if (!ctx || !trendData.length) return;

        // Destroy existing chart if any
        if (this.charts.installations) {
            this.charts.installations.destroy();
        }

        // Get Chart.js colors based on theme
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
            document.body.classList.contains('dark-theme');

        this.charts.installations = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trendData.map(d => this.formatDate(d.date)),
                datasets: [
                    {
                        label: 'Total',
                        data: trendData.map(d => d.total),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Active',
                        data: trendData.map(d => d.active),
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.3
                    }
                ]
            },
            options: this.getChartOptions('Installations', isDark)
        });
    }

    /**
     * Render deployment mode doughnut chart
     */
    renderDeploymentChart(deploymentData) {
        const ctx = document.getElementById('deploymentChart')?.getContext('2d');
        if (!ctx || !deploymentData?.breakdown) return;

        if (this.charts.deployment) {
            this.charts.deployment.destroy();
        }

        const displayNames = deploymentData.display_names || {
            'homeassistant': 'Home Assistant',
            'docker': 'Docker',
            'standalone': 'Standalone',
            'pi': 'Raspberry Pi'
        };

        const labels = Object.keys(deploymentData.breakdown);
        const values = Object.values(deploymentData.breakdown);

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
            document.body.classList.contains('dark-theme');

        this.charts.deployment = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map(l => displayNames[l] || l),
                datasets: [{
                    data: values,
                    backgroundColor: [
                        '#3b82f6', // Blue - Home Assistant
                        '#10b981', // Green - Docker
                        '#f59e0b', // Amber - Standalone
                        '#ef4444', // Red - Pi
                        '#8b5cf6'  // Purple - Other
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: isDark ? '#e5e7eb' : '#374151'
                        }
                    }
                }
            }
        });
    }

    /**
     * Render version adoption horizontal bar chart
     */
    renderVersionsChart(versionsData) {
        const ctx = document.getElementById('versionsChart')?.getContext('2d');
        if (!ctx || !versionsData?.versions) return;

        if (this.charts.versions) {
            this.charts.versions.destroy();
        }

        // Take top 5 versions
        const top5 = versionsData.versions.slice(0, 5);

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
            document.body.classList.contains('dark-theme');

        this.charts.versions = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: top5.map(v => v.version),
                datasets: [{
                    label: 'Installations',
                    data: top5.map(v => v.count),
                    backgroundColor: '#3b82f6'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        ticks: { color: isDark ? '#9ca3af' : '#6b7280' },
                        grid: { color: isDark ? '#374151' : '#e5e7eb' }
                    },
                    y: {
                        ticks: { color: isDark ? '#9ca3af' : '#6b7280' },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Render geographic distribution horizontal bar chart
     */
    renderGeographyChart(geoData) {
        const ctx = document.getElementById('geographyChart')?.getContext('2d');
        if (!ctx || !geoData?.countries) return;

        if (this.charts.geography) {
            this.charts.geography.destroy();
        }

        // Take top 10 countries
        const top10 = geoData.countries.slice(0, 10);

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
            document.body.classList.contains('dark-theme');

        this.charts.geography = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: top10.map(c => c.name || c.code),
                datasets: [{
                    label: 'Installations',
                    data: top10.map(c => c.count),
                    backgroundColor: '#10b981'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        ticks: { color: isDark ? '#9ca3af' : '#6b7280' },
                        grid: { color: isDark ? '#374151' : '#e5e7eb' }
                    },
                    y: {
                        ticks: { color: isDark ? '#9ca3af' : '#6b7280' },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Render feature usage horizontal bar chart
     */
    renderFeatureUsageChart(featuresData) {
        const ctx = document.getElementById('featuresChart')?.getContext('2d');
        if (!ctx || !featuresData?.features) return;

        if (this.charts.features) {
            this.charts.features.destroy();
        }

        const features = featuresData.features.slice(0, 10);
        if (features.length === 0) return;

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
            document.body.classList.contains('dark-theme');

        // Format feature names for display
        const formatFeatureName = (name) => {
            return name.replace(/_/g, ' ')
                .replace(/\b\w/g, l => l.toUpperCase());
        };

        this.charts.features = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: features.map(f => formatFeatureName(f.feature)),
                datasets: [
                    {
                        label: 'Enabled',
                        data: features.map(f => f.enabled),
                        backgroundColor: '#10b981'
                    },
                    {
                        label: 'Disabled',
                        data: features.map(f => f.disabled),
                        backgroundColor: '#ef4444'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: isDark ? '#e5e7eb' : '#374151' }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        ticks: { color: isDark ? '#9ca3af' : '#6b7280' },
                        grid: { color: isDark ? '#374151' : '#e5e7eb' }
                    },
                    y: {
                        stacked: true,
                        ticks: { color: isDark ? '#9ca3af' : '#6b7280' },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Render anomaly alerts
     */
    renderAnomalyAlerts(anomalyData) {
        const container = document.getElementById('anomalyAlerts');
        if (!container) return;

        const anomalies = anomalyData?.anomalies || [];

        if (anomalies.length === 0) {
            container.innerHTML = `
                <div class="anomaly-status anomaly-ok">
                    <span class="anomaly-icon">&#x2705;</span>
                    <span>No anomalies detected</span>
                </div>
            `;
            return;
        }

        const severityIcons = {
            'high': '&#x1F534;',    // Red circle
            'medium': '&#x1F7E0;',  // Orange circle
            'info': '&#x1F535;'     // Blue circle
        };

        const severityClasses = {
            'high': 'anomaly-high',
            'medium': 'anomaly-medium',
            'info': 'anomaly-info'
        };

        container.innerHTML = anomalies.map(a => `
            <div class="anomaly-alert ${severityClasses[a.severity] || 'anomaly-info'}">
                <span class="anomaly-icon">${severityIcons[a.severity] || '&#x2139;'}</span>
                <div class="anomaly-content">
                    <div class="anomaly-message">${this.escapeHtml(a.message)}</div>
                    <div class="anomaly-type">${a.type.replace(/_/g, ' ')}</div>
                </div>
            </div>
        `).join('');
    }

    /**
     * Export dashboard data as JSON
     */
    async exportData() {
        if (!this.aggregationUrl || !this.apiKey) {
            showToast('error', 'Not Connected', 'Please connect to aggregation service first');
            return;
        }

        try {
            const data = await this.fetchStats('/stats/export');

            // Create and download JSON file
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `printernizer-stats-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showToast('success', 'Exported', 'Statistics exported successfully');
        } catch (error) {
            Logger.error('Failed to export data', error);
            showToast('error', 'Export Failed', error.message);
        }
    }

    /**
     * Get common chart options
     */
    getChartOptions(title, isDark) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: isDark ? '#e5e7eb' : '#374151'
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: isDark ? '#9ca3af' : '#6b7280' },
                    grid: { color: isDark ? '#374151' : '#e5e7eb' }
                },
                y: {
                    ticks: { color: isDark ? '#9ca3af' : '#6b7280' },
                    grid: { color: isDark ? '#374151' : '#e5e7eb' }
                }
            }
        };
    }

    /**
     * Format date for chart labels
     */
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    /**
     * Show loading state
     */
    showLoading() {
        const dashboardEl = document.getElementById('globalStatsDashboard');
        if (dashboardEl) {
            dashboardEl.innerHTML = `
                <div class="stats-loading">
                    <div class="spinner"></div>
                    <p>Loading statistics...</p>
                </div>
            `;
            dashboardEl.style.display = 'block';
        }

        const configEl = document.getElementById('aggregationServiceConfig');
        if (configEl) configEl.style.display = 'none';
    }

    /**
     * Show error state
     */
    showError(message) {
        const dashboardEl = document.getElementById('globalStatsDashboard');
        if (dashboardEl) {
            dashboardEl.innerHTML = `
                <div class="stats-error">
                    <div class="error-icon">&#x26A0;</div>
                    <div class="error-message">Connection Failed</div>
                    <div class="error-details">${this.escapeHtml(message)}</div>
                </div>
            `;
        }

        // Show config form again
        const configEl = document.getElementById('aggregationServiceConfig');
        if (configEl) configEl.style.display = 'block';
    }

    /**
     * Disconnect from aggregation service
     */
    disconnect() {
        // Clear stored credentials
        localStorage.removeItem('aggregation_service_url');
        localStorage.removeItem('aggregation_api_key');

        // Reset UI
        const dashboardEl = document.getElementById('globalStatsDashboard');
        const configEl = document.getElementById('aggregationServiceConfig');

        if (dashboardEl) {
            dashboardEl.style.display = 'none';
            // Reset dashboard content
            this.resetDashboardContent();
        }
        if (configEl) configEl.style.display = 'block';

        // Clear form fields
        const urlInput = document.getElementById('aggregationUrl');
        const keyInput = document.getElementById('aggregationApiKey');
        if (urlInput) urlInput.value = '';
        if (keyInput) keyInput.value = '';

        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};

        // Reset state
        this.aggregationUrl = null;
        this.apiKey = null;
        this.data = null;

        showToast('info', 'Disconnected', 'Aggregation service disconnected');
    }

    /**
     * Reset dashboard content to initial state (for reconnection)
     */
    resetDashboardContent() {
        const dashboardEl = document.getElementById('globalStatsDashboard');
        if (!dashboardEl) return;

        dashboardEl.innerHTML = `
            <!-- Overview Cards -->
            <div class="stats-overview-grid">
                <div class="stats-card">
                    <div class="stats-number" id="totalInstallations">-</div>
                    <div class="stats-label">Total Installations</div>
                </div>
                <div class="stats-card">
                    <div class="stats-number" id="active7d">-</div>
                    <div class="stats-label">Active (7 days)</div>
                </div>
                <div class="stats-card">
                    <div class="stats-number" id="active30d">-</div>
                    <div class="stats-label">Active (30 days)</div>
                </div>
                <div class="stats-card">
                    <div class="stats-number" id="growth7d">-</div>
                    <div class="stats-label">Growth (7 days)</div>
                </div>
            </div>

            <!-- Anomaly Alerts -->
            <div class="anomaly-alerts-section" id="anomalyAlerts">
                <div class="anomaly-status anomaly-ok">
                    <span class="anomaly-icon">&#x2705;</span>
                    <span>No anomalies detected</span>
                </div>
            </div>

            <!-- Charts Grid -->
            <div class="stats-charts-grid">
                <div class="chart-container">
                    <h4>Installations Over Time</h4>
                    <canvas id="installationsChart"></canvas>
                </div>
                <div class="chart-container">
                    <h4>Deployment Mode Distribution</h4>
                    <canvas id="deploymentChart"></canvas>
                </div>
                <div class="chart-container">
                    <h4>Version Adoption</h4>
                    <canvas id="versionsChart"></canvas>
                </div>
                <div class="chart-container">
                    <h4>Geographic Distribution</h4>
                    <canvas id="geographyChart"></canvas>
                </div>
                <div class="chart-container">
                    <h4>Feature Usage</h4>
                    <canvas id="featuresChart"></canvas>
                </div>
            </div>

            <!-- Timestamp and Actions -->
            <div class="stats-timestamp" id="statsLastUpdated"></div>
            <div class="stats-actions">
                <button class="btn btn-secondary" onclick="adminStats.exportData()">
                    <span class="btn-icon">&#x1F4E4;</span>
                    Export JSON
                </button>
                <button class="btn btn-secondary" onclick="adminStats.disconnect()">
                    <span class="btn-icon">&#x1F50C;</span>
                    Disconnect
                </button>
            </div>
        `;
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create global instance
const adminStats = new AdminStatisticsManager();
