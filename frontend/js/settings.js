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
        this.currentTab = 'general';
        this.allSettings = [];
    }

    /**
     * Initialize settings page
     */
    async init() {
        Logger.debug('Initializing settings manager');

        // Load current settings
        await this.loadSettings();

        // Setup form handlers
        this.setupFormHandlers();

        // Load system info
        await this.loadSystemInfo();

        // Load watch folder settings
        await this.loadWatchFolderSettings();

        // Initialize navigation preferences UI
        if (window.navigationPreferencesManager) {
            window.navigationPreferencesManager.init();
        }

        // Index all settings for search
        this.indexSettings();

        this.lastRefresh = new Date();
        Logger.debug('Settings manager initialized');
    }

    /**
     * Switch between settings tabs
     */
    switchTab(tabName) {
        Logger.debug('Switching to tab:', tabName);

        try {
            // Validate tab name
            if (!tabName || typeof tabName !== 'string') {
                Logger.error('Invalid tab name:', tabName);
                return;
            }

            // Update tab buttons - remove active from all tabs
            const allTabs = document.querySelectorAll('.settings-tab');
            Logger.debug(`Found ${allTabs.length} tab buttons`);
            allTabs.forEach(tab => {
                tab.classList.remove('active');
                tab.setAttribute('aria-selected', 'false');
            });

            // Add active to the clicked tab
            const activeTab = document.querySelector(`.settings-tab[data-tab="${tabName}"]`);
            if (activeTab) {
                activeTab.classList.add('active');
                activeTab.setAttribute('aria-selected', 'true');
                Logger.debug(`Activated tab button: ${tabName}`);
            } else {
                Logger.error(`Tab button not found for: ${tabName}`);
                return;
            }

            // Update tab content - remove active from all panes
            const allPanes = document.querySelectorAll('.tab-pane');
            Logger.debug(`Found ${allPanes.length} tab panes`);
            allPanes.forEach(pane => {
                pane.classList.remove('active');
                pane.style.display = 'none';  // Explicitly set display none
                pane.setAttribute('aria-hidden', 'true');
            });

            // Add active to the target pane
            const activePane = document.getElementById(`${tabName}-tab`);
            if (activePane) {
                activePane.classList.add('active');
                activePane.style.display = 'block';  // Explicitly set display block
                activePane.setAttribute('aria-hidden', 'false');
                Logger.debug(`Activated tab pane: ${tabName}-tab`);
            } else {
                Logger.error(`Tab pane not found for: ${tabName}-tab`);
                return;
            }

            // Update current tab tracking
            this.currentTab = tabName;
            Logger.debug(`Successfully switched to tab: ${tabName}`);

        } catch (error) {
            Logger.error('Error in switchTab:', error);
            showToast('error', 'Fehler', 'Tab konnte nicht gewechselt werden');
        }
    }

    /**
     * Index all settings for search functionality
     */
    indexSettings() {
        this.allSettings = [
            // General settings
            { id: 'logLevel', tab: 'general', keywords: ['log', 'level', 'debug', 'protokoll'] },
            { id: 'monitoringInterval', tab: 'general', keywords: ['monitoring', 'interval', 'überwachung', 'polling'] },
            { id: 'connectionTimeout', tab: 'general', keywords: ['timeout', 'verbindung', 'connection'] },
            { id: 'vatRate', tab: 'general', keywords: ['vat', 'mwst', 'steuer', 'tax'] },

            // Jobs & G-Code
            { id: 'jobCreationAutoCreate', tab: 'jobs', keywords: ['job', 'auto', 'automatisch', 'auftrag'] },
            { id: 'gcodeOptimizePrintOnly', tab: 'jobs', keywords: ['gcode', 'optimize', 'print', 'optimierung'] },
            { id: 'gcodeOptimizationMaxLines', tab: 'jobs', keywords: ['gcode', 'lines', 'zeilen', 'max'] },
            { id: 'gcodeRenderMaxLines', tab: 'jobs', keywords: ['gcode', 'render', 'rendering', 'vorschau'] },

            // Library
            { id: 'libraryEnabled', tab: 'library', keywords: ['library', 'bibliothek', 'enable'] },
            { id: 'libraryPath', tab: 'library', keywords: ['library', 'path', 'pfad', 'verzeichnis'] },
            { id: 'libraryAutoOrganize', tab: 'library', keywords: ['library', 'organize', 'auto', 'organisation'] },
            { id: 'libraryAutoExtractMetadata', tab: 'library', keywords: ['library', 'metadata', 'extract', 'metadaten'] },
            { id: 'libraryAutoDeduplicate', tab: 'library', keywords: ['library', 'duplicate', 'duplikat', 'deduplicate'] },
            { id: 'libraryPreserveOriginals', tab: 'library', keywords: ['library', 'preserve', 'original', 'bewahren'] },
            { id: 'libraryChecksumAlgorithm', tab: 'library', keywords: ['library', 'checksum', 'algorithm', 'prüfsumme'] },
            { id: 'libraryProcessingWorkers', tab: 'library', keywords: ['library', 'workers', 'threads', 'parallel'] },
            { id: 'librarySearchEnabled', tab: 'library', keywords: ['library', 'search', 'suche'] },
            { id: 'librarySearchMinLength', tab: 'library', keywords: ['library', 'search', 'length', 'länge'] },

            // Files
            { id: 'downloadsPath', tab: 'files', keywords: ['download', 'path', 'pfad', 'verzeichnis'] },
            { id: 'maxFileSize', tab: 'files', keywords: ['download', 'size', 'größe', 'max'] },
            { id: 'enableUpload', tab: 'files', keywords: ['upload', 'hochladen', 'enable'] },
            { id: 'maxUploadSizeMb', tab: 'files', keywords: ['upload', 'size', 'größe', 'max'] },
            { id: 'allowedUploadExtensions', tab: 'files', keywords: ['upload', 'extensions', 'erweiterungen', 'format'] },

            // Timelapse
            { id: 'timelapseEnabled', tab: 'timelapse', keywords: ['timelapse', 'video', 'enable'] },
            { id: 'timelapseSourceFolder', tab: 'timelapse', keywords: ['timelapse', 'source', 'quelle', 'folder'] },
            { id: 'timelapseOutputFolder', tab: 'timelapse', keywords: ['timelapse', 'output', 'ausgabe', 'folder'] },
            { id: 'timelapseOutputStrategy', tab: 'timelapse', keywords: ['timelapse', 'strategy', 'strategie'] },
            { id: 'timelapseAutoProcessTimeout', tab: 'timelapse', keywords: ['timelapse', 'timeout', 'auto', 'process'] },
            { id: 'timelapseCleanupAgeDays', tab: 'timelapse', keywords: ['timelapse', 'cleanup', 'clean', 'age', 'days'] },

            // Watch folders
            { id: 'watchFoldersEnabled', tab: 'watch', keywords: ['watch', 'folder', 'überwachung', 'verzeichnis'] },
            { id: 'watchFoldersRecursive', tab: 'watch', keywords: ['watch', 'recursive', 'rekursiv', 'unterordner'] }
        ];
    }

    /**
     * Filter settings based on search query
     */
    filterSettings(query) {
        if (!query || query.trim().length < 2) {
            // Show all tabs and settings
            document.querySelectorAll('.settings-tab').forEach(tab => tab.style.display = 'flex');
            document.querySelectorAll('.settings-section').forEach(section => section.style.display = 'block');
            document.querySelectorAll('.form-group').forEach(group => group.style.display = 'block');
            return;
        }

        const searchTerms = query.toLowerCase().trim().split(' ');
        const matchedSettings = new Set();
        const matchedTabs = new Set();

        // Find matching settings
        this.allSettings.forEach(setting => {
            const matches = searchTerms.every(term =>
                setting.id.toLowerCase().includes(term) ||
                setting.keywords.some(keyword => keyword.includes(term))
            );

            if (matches) {
                matchedSettings.add(setting.id);
                matchedTabs.add(setting.tab);
            }
        });

        // Hide/show tabs
        document.querySelectorAll('.settings-tab').forEach(tab => {
            const tabName = tab.getAttribute('data-tab');
            if (matchedTabs.has(tabName)) {
                tab.style.display = 'flex';
            } else {
                tab.style.display = 'none';
            }
        });

        // Hide/show form groups
        document.querySelectorAll('.form-group').forEach(group => {
            const input = group.querySelector('input, select');
            if (input && matchedSettings.has(input.id)) {
                group.style.display = 'block';
                group.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
                group.style.borderRadius = '8px';
                group.style.padding = '0.5rem';
            } else {
                group.style.display = 'none';
            }
        });

        // Switch to first matched tab if current tab has no matches
        if (matchedTabs.size > 0 && !matchedTabs.has(this.currentTab)) {
            const firstMatchedTab = Array.from(matchedTabs)[0];
            this.switchTab(firstMatchedTab);
        }
    }

    /**
     * Export settings to JSON file
     */
    async exportSettings() {
        try {
            const settings = await api.getApplicationSettings();
            const dataStr = JSON.stringify(settings, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });

            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `printernizer-settings-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            showToast('success', 'Export erfolgreich', 'Einstellungen wurden exportiert');
        } catch (error) {
            Logger.error('Failed to export settings:', error);
            showToast('error', 'Export fehlgeschlagen', 'Einstellungen konnten nicht exportiert werden');
        }
    }

    /**
     * Import settings from JSON file
     */
    async importSettings() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'application/json';

        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            try {
                const text = await file.text();
                const settings = JSON.parse(text);

                // Confirm import
                const confirmed = confirm(
                    `Einstellungen aus "${file.name}" importieren?\n\n` +
                    `Dies wird ${Object.keys(settings).length} Einstellungen überschreiben.`
                );

                if (!confirmed) return;

                // Apply settings
                await api.updateApplicationSettings(settings);
                await this.loadSettings();

                showToast('success', 'Import erfolgreich',
                         `${Object.keys(settings).length} Einstellungen wurden importiert`);
            } catch (error) {
                Logger.error('Failed to import settings:', error);
                showToast('error', 'Import fehlgeschlagen',
                         'Einstellungen konnten nicht importiert werden. Prüfen Sie das Dateiformat.');
            }
        };

        input.click();
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

            Logger.debug('Settings loaded:', this.currentSettings);

        } catch (error) {
            window.ErrorHandler?.handleSettingsError(error, { operation: 'load' });
            showToast('error', 'Fehler beim Laden', 'Einstellungen konnten nicht geladen werden');
        }
    }

    /**
     * Populate settings form with current values
     */
    populateSettingsForm() {
        if (!this.currentSettings) {
            Logger.warn('No current settings to populate');
            return;
        }

        const form = document.getElementById('applicationSettingsForm');
        if (!form) {
            Logger.error('Settings form not found');
            return;
        }

        Logger.debug('Populating settings form with:', this.currentSettings);

        // Set form values (inputs inside the form)
        const elements = form.elements;
        for (let element of elements) {
            const key = element.name;
            if (key && this.currentSettings.hasOwnProperty(key)) {
                if (element.type === 'checkbox') {
                    element.checked = this.currentSettings[key];
                    Logger.debug(`Populated form element: ${key} = ${this.currentSettings[key]} (checkbox)`);
                } else {
                    element.value = this.currentSettings[key];
                    Logger.debug(`Populated form element: ${key} = ${this.currentSettings[key]}`);
                }
            }
        }

        // Also populate inputs associated with the form (using form attribute)
        const associatedInputs = document.querySelectorAll('input[form="applicationSettingsForm"]');
        Logger.debug(`Populating ${associatedInputs.length} form-associated inputs`);

        associatedInputs.forEach(element => {
            const key = element.name;
            if (key && this.currentSettings.hasOwnProperty(key)) {
                if (element.type === 'checkbox') {
                    element.checked = this.currentSettings[key];
                    Logger.debug(`Populated associated input: ${key} = ${this.currentSettings[key]} (checkbox)`);
                } else {
                    element.value = this.currentSettings[key];
                    Logger.debug(`Populated associated input: ${key} = ${this.currentSettings[key]}`);
                }
            } else if (key) {
                Logger.warn(`Associated input ${key} not found in settings`);
            }
        });

        this.isDirty = false;
        this.updateSaveButton();
        Logger.debug('Form population complete');
    }

    /**
     * Save application settings
     */
    async saveSettings() {
        try {
            Logger.debug('=== SAVE SETTINGS STARTED ===');
            Logger.debug('isDirty:', this.isDirty);

            if (!this.isDirty) {
                Logger.warn('No changes detected - aborting save');
                showToast('info', 'Keine Änderungen', 'Es wurden keine Änderungen vorgenommen');
                return;
            }

            const formData = this.collectFormData();
            Logger.debug('Collected form data:', formData);
            Logger.debug('Number of fields to save:', Object.keys(formData).length);

            if (Object.keys(formData).length === 0) {
                Logger.warn('No data collected - aborting save');
                showToast('warning', 'Keine Daten', 'Keine Formulardaten gefunden');
                return;
            }

            showToast('info', 'Speichere Einstellungen', 'Konfiguration wird gespeichert');

            const result = await api.updateApplicationSettings(formData);
            Logger.debug('Save result:', result);

            showToast('success', 'Einstellungen gespeichert',
                     `${result.updated_fields.length} Einstellungen wurden aktualisiert`);

            this.isDirty = false;
            this.updateSaveButton();

            // Reload settings to reflect any server-side changes
            Logger.debug('Reloading settings after save');
            await this.loadSettings();

            Logger.debug('=== SAVE SETTINGS COMPLETED ===');

        } catch (error) {
            Logger.error('Save settings error:', error);
            window.ErrorHandler?.handleSettingsError(error, { operation: 'save' });
            showToast('error', 'Fehler beim Speichern', 'Einstellungen konnten nicht gespeichert werden');
        }
    }

    /**
     * Collect form data for saving
     */
    collectFormData() {
        const form = document.getElementById('applicationSettingsForm');
        if (!form) {
            Logger.warn('Settings form not found');
            return {};
        }

        const formData = {};

        // Collect from form elements (inputs inside the form)
        const elements = form.elements;
        for (let element of elements) {
            if (!element.name) continue;

            if (element.type === 'checkbox') {
                // Always collect checkbox state
                formData[element.name] = element.checked;
                Logger.debug(`Collected form element: ${element.name} = ${element.checked} (checkbox)`);
            } else if (element.type === 'number') {
                // Collect number if not empty
                const value = element.value.trim();
                if (value !== '') {
                    formData[element.name] = parseFloat(value);
                    Logger.debug(`Collected form element: ${element.name} = ${value} (number)`);
                }
            } else if (element.type === 'text' || element.type === 'select-one') {
                // Collect text/select if not empty
                const value = element.value.trim();
                if (value !== '') {
                    formData[element.name] = value;
                    Logger.debug(`Collected form element: ${element.name} = ${value} (${element.type})`);
                }
            }
        }

        // Also collect from inputs associated with the form (using form attribute)
        // These are inputs outside the form but logically part of it (like library settings)
        const associatedInputs = document.querySelectorAll('input[form="applicationSettingsForm"]');
        Logger.debug(`Found ${associatedInputs.length} form-associated inputs`);

        associatedInputs.forEach(element => {
            if (!element.name) return;

            if (element.type === 'checkbox') {
                // Always collect checkbox state
                formData[element.name] = element.checked;
                Logger.debug(`Collected associated input: ${element.name} = ${element.checked} (checkbox)`);
            } else if (element.type === 'number') {
                // Collect number if not empty
                const value = element.value.trim();
                if (value !== '') {
                    formData[element.name] = parseFloat(value);
                    Logger.debug(`Collected associated input: ${element.name} = ${value} (number)`);
                }
            } else if (element.type === 'text') {
                // Collect text if not empty
                const value = element.value.trim();
                if (value !== '') {
                    formData[element.name] = value;
                    Logger.debug(`Collected associated input: ${element.name} = ${value} (text)`);
                } else {
                    Logger.debug(`Skipped empty associated input: ${element.name} (text)`);
                }
            }
        });

        Logger.debug('Final form data to be saved:', formData);
        return formData;
    }

    /**
     * Setup form change handlers
     */
    setupFormHandlers() {
        const form = document.getElementById('applicationSettingsForm');
        if (!form) {
            Logger.error('Settings form not found - cannot setup handlers');
            return;
        }

        Logger.debug('Setting up form change handlers');

        // Handler function for marking form as dirty
        const markDirty = (event) => {
            Logger.debug(`Form changed: ${event.target.name || event.target.id} = ${event.target.value || event.target.checked}`);
            this.isDirty = true;
            this.updateSaveButton();
            this.scheduleAutoSave();
        };

        // Track changes on form itself (for inputs inside the form)
        form.addEventListener('input', markDirty);
        form.addEventListener('change', markDirty);
        Logger.debug('Attached event listeners to main form');

        // Also track changes on inputs associated with the form (using form attribute)
        // This includes library settings that are visually separate but logically part of the form
        const associatedInputs = document.querySelectorAll('input[form="applicationSettingsForm"]');
        Logger.debug(`Found ${associatedInputs.length} form-associated inputs for event listeners`);

        associatedInputs.forEach(input => {
            Logger.debug(`Attaching listeners to: ${input.name || input.id} (${input.type})`);
            input.addEventListener('input', markDirty);
            input.addEventListener('change', markDirty);
        });

        Logger.debug('Form change handlers setup complete');
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
                Logger.debug('Auto-saving settings...');
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
        Logger.error('Failed to validate downloads path:', error);
        validationResult.className = 'validation-result error';
        validationResult.innerHTML = '<span class="icon">✗</span> Validierung fehlgeschlagen';
    }
}

async function validateLibraryPath() {
    const folderPathInput = document.getElementById('libraryPath');
    const validationResult = document.getElementById('libraryPathValidationResult');

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
        const response = await api.validateLibraryPath(folderPath);

        if (response.valid) {
            validationResult.className = 'validation-result success';
            validationResult.innerHTML = '<span class="icon">✓</span> ' + (response.message || 'Bibliothek-Verzeichnis ist gültig und beschreibbar');
        } else {
            validationResult.className = 'validation-result error';
            validationResult.innerHTML = '<span class="icon">✗</span> ' + (response.error || 'Bibliothek-Verzeichnis ist ungültig');
        }

    } catch (error) {
        Logger.error('Failed to validate library path:', error);
        validationResult.className = 'validation-result error';
        validationResult.innerHTML = '<span class="icon">✗</span> Validierung fehlgeschlagen';
    }
}

async function checkFfmpegInstallation() {
    const resultDiv = document.getElementById('ffmpegCheckResult');

    if (!resultDiv) {
        Logger.error('FFmpeg result div not found');
        return;
    }

    try {
        // Show loading state
        resultDiv.style.display = 'block';
        resultDiv.className = 'validation-result loading';
        resultDiv.innerHTML = '<span class="spinner-small"></span> Prüfe FFmpeg-Installation...';

        // Check ffmpeg availability
        const response = await fetch(`${CONFIG.API_BASE_URL}/settings/ffmpeg-check`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.installed) {
            resultDiv.className = 'validation-result success';
            resultDiv.innerHTML = `
                <span class="icon">✓</span>
                <strong>FFmpeg ist installiert!</strong><br>
                <small style="margin-top: 0.25rem; display: block;">${result.version || 'Version unbekannt'}</small>
            `;
            showToast('success', 'FFmpeg gefunden', 'FFmpeg ist installiert und einsatzbereit');
        } else {
            resultDiv.className = 'validation-result error';
            resultDiv.innerHTML = `
                <span class="icon">✗</span>
                <strong>FFmpeg nicht gefunden</strong><br>
                <small style="margin-top: 0.25rem; display: block;">${result.error || 'FFmpeg ist nicht installiert oder nicht im PATH'}</small>
            `;
            showToast('warning', 'FFmpeg fehlt', 'FFmpeg ist nicht installiert. Timelapse-Funktion wird nicht funktionieren.');
        }

    } catch (error) {
        Logger.error('Failed to check ffmpeg:', error);
        resultDiv.className = 'validation-result error';
        resultDiv.innerHTML = '<span class="icon">✗</span> Prüfung fehlgeschlagen';
        showToast('error', 'Fehler', 'FFmpeg-Prüfung konnte nicht durchgeführt werden');
    }
}

// Export for use in main.js
if (typeof window !== 'undefined') {
    window.settingsManager = settingsManager;
}