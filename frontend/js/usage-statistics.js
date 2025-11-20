/**
 * Usage Statistics Manager
 * Handles privacy-first anonymous usage statistics collection
 */

class UsageStatisticsManager {
    constructor() {
        this.currentStats = null;
        this.optedIn = false;
    }

    /**
     * Initialize usage statistics manager
     */
    async init() {
        Logger.debug('Initializing usage statistics manager');

        try {
            // Load current status
            await this.loadStatus();

            // Load local statistics
            await this.refreshLocalStats();

            Logger.debug('Usage statistics manager initialized');
        } catch (error) {
            Logger.error('Failed to initialize usage statistics:', error);
        }
    }

    /**
     * Load usage statistics status
     */
    async loadStatus() {
        try {
            const response = await fetch('/api/v1/usage-stats/status');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const status = await response.json();

            // Update opt-in checkbox
            const checkbox = document.getElementById('usageStatsOptIn');
            if (checkbox) {
                checkbox.checked = status.opted_in;
                this.optedIn = status.opted_in;
            }

            Logger.debug('Usage statistics status loaded', status);
        } catch (error) {
            Logger.error('Failed to load usage statistics status:', error);
            this.showMessage('Fehler beim Laden des Status', 'alert-danger');
        }
    }

    /**
     * Toggle opt-in/opt-out
     */
    async toggleOptIn() {
        const checkbox = document.getElementById('usageStatsOptIn');
        const shouldOptIn = checkbox.checked;

        try {
            let response;

            if (shouldOptIn) {
                // Opt in
                response = await fetch('/api/v1/usage-stats/opt-in', {
                    method: 'POST'
                });
            } else {
                // Opt out
                response = await fetch('/api/v1/usage-stats/opt-out', {
                    method: 'POST'
                });
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.optedIn = shouldOptIn;

                // Show success message
                this.showMessage(result.message, 'alert-success');

                // Refresh stats to show installation ID if opted in
                await this.refreshLocalStats();

                Logger.info(shouldOptIn ? 'Opted in to usage statistics' : 'Opted out of usage statistics');
            } else {
                throw new Error(result.message || 'Unknown error');
            }

        } catch (error) {
            Logger.error('Failed to toggle opt-in:', error);

            // Revert checkbox
            checkbox.checked = !shouldOptIn;

            this.showMessage(
                `Fehler beim ${shouldOptIn ? 'Aktivieren' : 'Deaktivieren'}: ${error.message}`,
                'alert-danger'
            );
        }
    }

    /**
     * Refresh local statistics display
     */
    async refreshLocalStats() {
        const container = document.getElementById('usageStatsLocalData');

        if (!container) {
            return;
        }

        try {
            // Show loading
            container.innerHTML = `
                <div class="loading-placeholder">
                    <div class="spinner"></div>
                    <p>Lade Statistiken...</p>
                </div>
            `;

            const response = await fetch('/api/v1/usage-stats/local');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const stats = await response.json();
            this.currentStats = stats;

            // Display statistics
            this.displayLocalStats(stats);

            Logger.debug('Local statistics refreshed', stats);

        } catch (error) {
            Logger.error('Failed to load local statistics:', error);

            container.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Fehler:</strong> Statistiken konnten nicht geladen werden.
                    <br><small>${error.message}</small>
                </div>
            `;
        }
    }

    /**
     * Display local statistics
     */
    displayLocalStats(stats) {
        const container = document.getElementById('usageStatsLocalData');

        if (!container) {
            return;
        }

        const firstSeen = stats.first_seen
            ? new Date(stats.first_seen).toLocaleDateString('de-DE')
            : 'Nie';

        const lastSubmission = stats.last_submission
            ? new Date(stats.last_submission).toLocaleDateString('de-DE')
            : 'Nie';

        container.innerHTML = `
            <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px;">
                <div class="stat-card">
                    <div class="stat-label">Installations-ID</div>
                    <div class="stat-value" style="font-size: 0.9rem; font-family: monospace; word-break: break-all;">
                        ${stats.installation_id}
                    </div>
                    <small class="text-muted">Anonyme Kennung</small>
                </div>

                <div class="stat-card">
                    <div class="stat-label">Erste Nutzung</div>
                    <div class="stat-value">${firstSeen}</div>
                    <small class="text-muted">Erste aufgezeichnete Aktivität</small>
                </div>

                <div class="stat-card">
                    <div class="stat-label">Status</div>
                    <div class="stat-value">
                        <span class="status-badge ${stats.opt_in_status === 'enabled' ? 'badge-success' : 'badge-secondary'}">
                            ${stats.opt_in_status === 'enabled' ? '✓ Aktiv' : '○ Inaktiv'}
                        </span>
                    </div>
                    <small class="text-muted">Übermittlungs-Status</small>
                </div>

                <div class="stat-card">
                    <div class="stat-label">Gesammelte Events</div>
                    <div class="stat-value">${stats.total_events.toLocaleString('de-DE')}</div>
                    <small class="text-muted">Lokale Ereignisse</small>
                </div>
            </div>

            <div class="stats-section" style="margin-top: 20px;">
                <h4 style="font-size: 1rem; margin-bottom: 15px;">Diese Woche</h4>
                <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div class="stat-card">
                        <div class="stat-label">Druckaufträge</div>
                        <div class="stat-value">${(stats.this_week.job_count || 0).toLocaleString('de-DE')}</div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-label">Datei-Downloads</div>
                        <div class="stat-value">${(stats.this_week.file_count || 0).toLocaleString('de-DE')}</div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-label">Fehler</div>
                        <div class="stat-value">${(stats.this_week.error_count || 0).toLocaleString('de-DE')}</div>
                    </div>
                </div>
            </div>

            <div class="stats-section" style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border-color);">
                <div class="stat-info">
                    <strong>Letzte Übermittlung:</strong> ${lastSubmission}
                    ${stats.opt_in_status === 'disabled' ? '<br><small class="text-muted">Übermittlung ist deaktiviert. Daten werden nur lokal gespeichert.</small>' : ''}
                </div>
            </div>
        `;
    }

    /**
     * Export statistics data
     */
    async exportData() {
        try {
            Logger.info('Exporting usage statistics...');

            const response = await fetch('/api/v1/usage-stats/export');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            // Download the JSON file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `usage-statistics-export-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.showMessage('Statistiken erfolgreich exportiert', 'alert-success');

            Logger.info('Usage statistics exported successfully');

        } catch (error) {
            Logger.error('Failed to export usage statistics:', error);
            this.showMessage(`Fehler beim Exportieren: ${error.message}`, 'alert-danger');
        }
    }

    /**
     * Delete all local statistics
     */
    async deleteAllData() {
        // Confirm deletion
        if (!confirm(
            'Möchten Sie wirklich alle lokalen Nutzungsstatistiken löschen?\n\n' +
            'Diese Aktion kann nicht rückgängig gemacht werden. ' +
            'Falls Sie Daten bereits übermittelt haben, bleiben diese auf dem Server gespeichert.'
        )) {
            return;
        }

        try {
            Logger.info('Deleting all usage statistics...');

            const response = await fetch('/api/v1/usage-stats', {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.showMessage(
                    `Alle lokalen Statistiken gelöscht (${result.deleted_events} Events)`,
                    'alert-success'
                );

                // Refresh display
                await this.refreshLocalStats();

                Logger.info('Usage statistics deleted successfully', result);
            } else {
                throw new Error(result.message || 'Unknown error');
            }

        } catch (error) {
            Logger.error('Failed to delete usage statistics:', error);
            this.showMessage(`Fehler beim Löschen: ${error.message}`, 'alert-danger');
        }
    }

    /**
     * Show status message
     */
    showMessage(message, alertClass = 'alert-info') {
        const messageContainer = document.getElementById('usageStatsOptInMessage');

        if (!messageContainer) {
            return;
        }

        messageContainer.className = `alert ${alertClass}`;
        messageContainer.textContent = message;
        messageContainer.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageContainer.style.display = 'none';
        }, 5000);
    }
}

// Initialize global instance
const usageStatistics = new UsageStatisticsManager();

// Auto-initialize when settings page is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the settings page
    const settingsPage = document.getElementById('settings');

    if (settingsPage) {
        // Initialize when settings tab is visible
        const observer = new MutationObserver(() => {
            if (settingsPage.classList.contains('active')) {
                usageStatistics.init();
                observer.disconnect();
            }
        });

        observer.observe(settingsPage, { attributes: true, attributeFilter: ['class'] });

        // Also check immediately in case already visible
        if (settingsPage.classList.contains('active')) {
            usageStatistics.init();
        }
    }
});
