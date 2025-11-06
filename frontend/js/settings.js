/**
 * Settings Management
 * Handles application settings and configuration
 */

class SettingsManager {
    constructor() {
        this.currentSettings = null;
        this.watchFolders = [];
        this.isDirty = false;
        this.autoSaveTimeout = null;
    }

    /**
     * Initialize settings page
     */
    async init() {
        console.log('Initializing settings manager');
        
        // Load current settings
        await this.loadSettings();
        
        // Setup form handlers
        this.setupFormHandlers();
        
        // Load system info
        await this.loadSystemInfo();
        
        // Load watch folder settings
        await this.loadWatchFolderSettings();
        
        this.lastRefresh = new Date();
        console.log('Settings manager initialized');
    }

    /**
     * Cleanup when leaving page
     */
    cleanup() {
        if (this.autoSaveTimeout) {
            clearTimeout(this.autoSaveTimeout);
        }
    }

    /**
     * Load application settings
     */
    async loadSettings() {
        try {
            showToast('info', 'Lade Einstellungen', 'Aktuelle Konfiguration wird geladen');

            this.currentSettings = await api.getApplicationSettings();
            this.populateSettingsForm();

            console.log('Settings loaded:', this.currentSettings);

        } catch (error) {
            window.ErrorHandler?.handleSettingsError(error, { operation: 'load' });
            showToast('error', 'Fehler beim Laden', 'Einstellungen konnten nicht geladen werden');
        }
    }

    /**
     * Populate settings form with current values
     */
    populateSettingsForm() {
        if (!this.currentSettings) return;

        const form = document.getElementById('applicationSettingsForm');
        if (!form) return;

        // Set form values
        const elements = form.elements;
        for (let element of elements) {
            const key = element.name;
            if (key && this.currentSettings.hasOwnProperty(key)) {
                if (element.type === 'checkbox') {
                    element.checked = this.currentSettings[key];
                } else {
                    element.value = this.currentSettings[key];
                }
            }
        }

        this.isDirty = false;
        this.updateSaveButton();
    }

    /**
     * Save application settings
     */
    async saveSettings() {
        try {
            if (!this.isDirty) {
                showToast('info', 'Keine Änderungen', 'Es wurden keine Änderungen vorgenommen');
                return;
            }

            const formData = this.collectFormData();

            showToast('info', 'Speichere Einstellungen', 'Konfiguration wird gespeichert');

            const result = await api.updateApplicationSettings(formData);
            
            showToast('success', 'Einstellungen gespeichert', 
                     `${result.updated_fields.length} Einstellungen wurden aktualisiert`);
            
            this.isDirty = false;
            this.updateSaveButton();
            
            // Reload settings to reflect any server-side changes
            await this.loadSettings();

        } catch (error) {
            window.ErrorHandler?.handleSettingsError(error, { operation: 'save' });
            showToast('error', 'Fehler beim Speichern', 'Einstellungen konnten nicht gespeichert werden');
        }
    }

    /**
     * Collect form data for saving
     */
    collectFormData() {
        const form = document.getElementById('applicationSettingsForm');
        if (!form) return {};

        const formData = {};
        const elements = form.elements;

        for (let element of elements) {
            if (element.name && element.value !== '') {
                if (element.type === 'number') {
                    formData[element.name] = parseFloat(element.value);
                } else if (element.type === 'checkbox') {
                    formData[element.name] = element.checked;
                } else {
                    formData[element.name] = element.value;
                }
            }
        }

        return formData;
    }

    /**
     * Setup form change handlers
     */
    setupFormHandlers() {
        const form = document.getElementById('applicationSettingsForm');
        if (!form) return;

        // Track changes
        form.addEventListener('input', () => {
            this.isDirty = true;
            this.updateSaveButton();
            this.scheduleAutoSave();
        });

        form.addEventListener('change', () => {
            this.isDirty = true;
            this.updateSaveButton();
            this.scheduleAutoSave();
        });
    }

    /**
     * Update save button state
     */
    updateSaveButton() {
        const saveButton = document.querySelector('button[onclick="saveSettings()"]');
        if (saveButton) {
            if (this.isDirty) {
                saveButton.classList.add('btn-warning');
                saveButton.classList.remove('btn-primary');
                saveButton.innerHTML = '<span class="btn-icon">⚠️</span> Änderungen speichern';
            } else {
                saveButton.classList.add('btn-primary');
                saveButton.classList.remove('btn-warning');
                saveButton.innerHTML = '<span class="btn-icon">💾</span> Speichern';
            }
        }
    }

    /**
     * Schedule auto-save (delayed)
     */
    scheduleAutoSave() {
        if (this.autoSaveTimeout) {
            clearTimeout(this.autoSaveTimeout);
        }

        // Auto-save after 30 seconds of inactivity
        this.autoSaveTimeout = setTimeout(() => {
            if (this.isDirty) {
                console.log('Auto-saving settings...');
                this.saveSettings();
            }
        }, 30000);
    }

    /**
     * Load system information
     */
    async loadSystemInfo() {
        try {
            const health = await api.getHealth();
            this.displaySystemInfo(health);

        } catch (error) {
            window.ErrorHandler?.handleSettingsError(error, { operation: 'load_system_info' });
            document.getElementById('systemInfo').innerHTML = `
                <div class="error-message">
                    <span class="error-icon">⚠️</span>
                    Systemdaten konnten nicht geladen werden
                </div>
            `;
        }
    }

    /**
     * Display system information
     */
    displaySystemInfo(health) {
        const container = document.getElementById('systemInfo');
        if (!container) return;

        const statusIcon = health.status === 'healthy' ? '✅' : '⚠️';
        const statusText = health.status === 'healthy' ? 'Gesund' : 'Degradiert';
        const statusClass = health.status === 'healthy' ? 'status-healthy' : 'status-warning';

        container.innerHTML = `
            <div class="system-status ${statusClass}">
                <div class="status-item">
                    <span class="status-label">System-Status:</span>
                    <span class="status-value">${statusIcon} ${statusText}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Version:</span>
                    <span class="status-value">${health.version}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Umgebung:</span>
                    <span class="status-value">${health.environment}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Letzte Prüfung:</span>
                    <span class="status-value">${new Date(health.timestamp).toLocaleString('de-DE')}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Datenbank:</span>
                    <span class="status-value">
                        ${health.database.healthy ? '✅' : '❌'} 
                        ${health.database.type.toUpperCase()}
                    </span>
                </div>
            </div>
            <div class="services-status">
                <h4>Services</h4>
                ${Object.entries(health.services).map(([service, serviceInfo]) => `
                    <div class="service-item">
                        <span class="service-name">${service}:</span>
                        <span class="service-status ${serviceInfo.status === 'healthy' ? 'healthy' : 'unhealthy'}">
                            ${serviceInfo.status === 'healthy' ? '✅' : '❌'} ${serviceInfo.status}
                        </span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Load watch folder settings
     */
    async loadWatchFolderSettings() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/settings/watch-folders`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const watchFolderSettings = await response.json();
            this.displayWatchFolderSettings(watchFolderSettings);

        } catch (error) {
            window.ErrorHandler?.handleSettingsError(error, { operation: 'load_watch_folders' });
            document.getElementById('watchFoldersList').innerHTML = `
                <div class="error-message">
                    Verzeichniseinstellungen konnten nicht geladen werden
                </div>
            `;
        }
    }

    /**
     * Display watch folder settings
     */
    displayWatchFolderSettings(settings) {
        // Set checkboxes
        const enabledCheckbox = document.getElementById('watchFoldersEnabled');
        const recursiveCheckbox = document.getElementById('watchFoldersRecursive');
        
        if (enabledCheckbox) enabledCheckbox.checked = settings.enabled;
        if (recursiveCheckbox) recursiveCheckbox.checked = settings.recursive;

        // Display watch folders list
        const container = document.getElementById('watchFoldersList');
        if (!container) return;

        if (settings.watch_folders && settings.watch_folders.length > 0) {
            container.innerHTML = `
                <div class="watch-folders">
                    ${settings.watch_folders.map(folder => `
                        <div class="watch-folder-item">
                            <span class="folder-icon">📂</span>
                            <span class="folder-path">${folder}</span>
                            <button class="btn btn-small btn-danger" onclick="removeWatchFolderFromSettings('${folder}')">
                                <span class="btn-icon">🗑️</span>
                            </button>
                        </div>
                    `).join('')}
                </div>
                <div class="watch-folder-add">
                    <input type="text" id="newWatchFolder" placeholder="Neues Verzeichnis hinzufügen..." class="form-control">
                    <button class="btn btn-primary" onclick="addWatchFolder()">
                        <span class="btn-icon">➕</span>
                        Hinzufügen
                    </button>
                </div>
                <div class="supported-extensions">
                    <small class="form-text text-muted">
                        Unterstützte Dateierweiterungen: ${settings.supported_extensions.join(', ')}
                    </small>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="empty-watch-folders">
                    <p>Keine Verzeichnisse konfiguriert</p>
                    <div class="watch-folder-add">
                        <input type="text" id="newWatchFolder" placeholder="Verzeichnis hinzufügen..." class="form-control">
                        <button class="btn btn-primary" onclick="addWatchFolder()">
                            <span class="btn-icon">➕</span>
                            Hinzufügen
                        </button>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Reset settings to defaults
     */
    async resetToDefaults() {
        const confirmed = confirm('Sind Sie sicher, dass Sie alle Einstellungen auf die Standardwerte zurücksetzen möchten?');
        if (!confirmed) return;

        try {
            showToast('info', 'Zurücksetzen', 'Einstellungen werden zurückgesetzt');

            const response = await fetch(`${CONFIG.API_BASE_URL}/settings/reset`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            showToast('success', 'Zurückgesetzt', 'Einstellungen wurden auf Standardwerte zurückgesetzt');
            await this.loadSettings();

        } catch (error) {
            window.ErrorHandler?.handleSettingsError(error, { operation: 'reset' });
            showToast('error', 'Fehler', 'Einstellungen konnten nicht zurückgesetzt werden');
        }
    }
}

/**
 * Global settings manager instance
 */
const settingsManager = new SettingsManager();

/**
 * Global functions for settings page
 */
function loadSettings() {
    settingsManager.loadSettings();
}

function saveSettings() {
    settingsManager.saveSettings();
}

function resetSettings() {
    settingsManager.resetToDefaults();
}

async function addWatchFolder() {
    const input = document.getElementById('newWatchFolder');
    if (!input || !input.value.trim()) return;

    const folderPath = input.value.trim();
    
    try {
        showToast('info', 'Hinzufügen', 'Verzeichnis wird zur Überwachung hinzugefügt');
        
        // Validate folder path first
        await api.validateWatchFolder(folderPath);
        
        // Add watch folder
        const result = await api.addWatchFolder(folderPath);
        
        showToast('success', 'Erfolgreich hinzugefügt', 
                 `Verzeichnis "${folderPath}" wird jetzt überwacht`);
        
        input.value = '';
        
        // Reload watch folder settings to reflect changes
        await settingsManager.loadWatchFolderSettings();
        
    } catch (error) {
        window.ErrorHandler?.handleSettingsError(error, { operation: 'add_watch_folder', path: folderPath });
        if (error instanceof ApiError) {
            showToast('error', 'Fehler beim Hinzufügen', error.getUserMessage());
        } else {
            showToast('error', 'Fehler', 'Verzeichnis konnte nicht hinzugefügt werden');
        }
    }
}

async function removeWatchFolderFromSettings(folderPath) {
    const confirmed = confirm(`Verzeichnis "${folderPath}" aus der Überwachung entfernen?`);
    if (!confirmed) return;

    try {
        showToast('info', 'Entfernen', 'Verzeichnis wird aus der Überwachung entfernt');

        // Remove watch folder
        const result = await api.removeWatchFolder(folderPath);

        showToast('success', 'Erfolgreich entfernt',
                 `Verzeichnis "${folderPath}" wird nicht mehr überwacht`);

        // Reload watch folder settings to reflect changes
        await settingsManager.loadWatchFolderSettings();

    } catch (error) {
        window.ErrorHandler?.handleSettingsError(error, { operation: 'remove_watch_folder', path: folderPath });
        if (error instanceof ApiError) {
            showToast('error', 'Fehler beim Entfernen', error.getUserMessage());
        } else {
            showToast('error', 'Fehler', 'Verzeichnis konnte nicht entfernt werden');
        }
    }
}

async function shutdownServer() {
    const confirmed = confirm(
        'Sind Sie sicher, dass Sie den Server herunterfahren möchten?\n\n' +
        'Der Server wird ordnungsgemäß heruntergefahren und alle aktiven Verbindungen werden geschlossen.'
    );
    if (!confirmed) return;

    try {
        showToast('warning', 'Server wird heruntergefahren', 'Bitte warten Sie...', 3000);

        // Call shutdown API
        await api.shutdownServer();

        showToast('success', 'Server heruntergefahren',
                 'Der Server wurde erfolgreich heruntergefahren.', 5000);

        // Optionally disable UI or show a message that server is down
        setTimeout(() => {
            document.body.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100vh; flex-direction: column; font-family: system-ui;">
                    <h1 style="color: #ef4444;">⏹️ Server wurde heruntergefahren</h1>
                    <p style="color: #6b7280; margin-top: 10px;">Der Server wurde ordnungsgemäß heruntergefahren.</p>
                    <p style="color: #6b7280;">Sie können dieses Fenster jetzt schließen.</p>
                </div>
            `;
        }, 2000);

    } catch (error) {
        window.ErrorHandler?.handleSettingsError(error, { operation: 'shutdown' });
        if (error instanceof ApiError) {
            showToast('error', 'Fehler beim Herunterfahren', error.getUserMessage());
        } else {
            showToast('error', 'Fehler', 'Server konnte nicht heruntergefahren werden');
        }
    }
}

async function validateDownloadsPath() {
    const folderPathInput = document.getElementById('downloadsPath');
    const validationResult = document.getElementById('downloadsPathValidationResult');

    if (!folderPathInput || !validationResult) return;

    const folderPath = folderPathInput.value.trim();
    if (!folderPath) {
        validationResult.style.display = 'none';
        return;
    }

    try {
        // Show loading state
        validationResult.style.display = 'block';
        validationResult.className = 'validation-result loading';
        validationResult.innerHTML = '<span class="spinner-small"></span> Validiere...';

        // Validate path
        const response = await api.validateDownloadsPath(folderPath);

        if (response.valid) {
            validationResult.className = 'validation-result success';
            validationResult.innerHTML = '<span class="icon">✓</span> ' + (response.message || 'Download-Verzeichnis ist gültig und beschreibbar');
        } else {
            validationResult.className = 'validation-result error';
            validationResult.innerHTML = '<span class="icon">✗</span> ' + (response.error || 'Download-Verzeichnis ist ungültig');
        }

    } catch (error) {
        console.error('Failed to validate downloads path:', error);
        validationResult.className = 'validation-result error';
        validationResult.innerHTML = '<span class="icon">✗</span> Validierung fehlgeschlagen';
    }
}

// Export for use in main.js
if (typeof window !== 'undefined') {
    window.settingsManager = settingsManager;
}