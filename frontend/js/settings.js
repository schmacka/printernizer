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

        // Generate QR code for iOS app
        this.generateServerQRCode();

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

            // Initialize tab-specific managers
            if (tabName === 'privacy' && typeof adminStats !== 'undefined') {
                adminStats.init();
            }

            // Initialize theme picker when appearance tab is selected
            if (tabName === 'appearance') {
                this.renderThemePicker();
            }

        } catch (error) {
            Logger.error('Error in switchTab:', error);
            showToast('error', t('common.error'), t('settings.tabSwitchFailed'));
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

            showToast('success', t('settings.exportSuccessTitle'), t('settings.exportSuccessMessage'));
        } catch (error) {
            Logger.error('Failed to export settings:', error);
            showToast('error', t('settings.exportFailedTitle'), t('settings.exportFailedMessage'));
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
                    t('settings.importConfirm', { filename: file.name, count: Object.keys(settings).length })
                );

                if (!confirmed) return;

                // Apply settings
                await api.updateApplicationSettings(settings);
                await this.loadSettings();

                showToast('success', t('settings.importSuccessTitle'),
                         t('settings.importSuccessMessage', { count: Object.keys(settings).length }));
            } catch (error) {
                Logger.error('Failed to import settings:', error);
                showToast('error', t('settings.importFailedTitle'),
                         t('settings.importFailedMessage'));
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
            showToast('info', t('settings.loadingTitle'), t('settings.loadingMessage'));

            this.currentSettings = await api.getApplicationSettings();
            this.populateSettingsForm();

            Logger.debug('Settings loaded:', this.currentSettings);

        } catch (error) {
            window.ErrorHandler?.handleSettingsError(error, { operation: 'load' });
            showToast('error', t('settings.loadFailedTitle'), t('settings.loadFailedMessage'));
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
                showToast('info', t('settings.noChangesTitle'), t('settings.noChangesMessage'));
                return;
            }

            const formData = this.collectFormData();
            Logger.debug('Collected form data:', formData);
            Logger.debug('Number of fields to save:', Object.keys(formData).length);

            if (Object.keys(formData).length === 0) {
                Logger.warn('No data collected - aborting save');
                showToast('warning', t('settings.noDataTitle'), t('settings.noDataMessage'));
                return;
            }

            showToast('info', t('settings.savingTitle'), t('settings.savingMessage'));

            const result = await api.updateApplicationSettings(formData);
            Logger.debug('Save result:', result);

            showToast('success', t('settings.savedTitle'),
                     t('settings.savedMessage', { count: result.updated_fields.length }));

            this.isDirty = false;
            this.updateSaveButton();

            // Reload settings to reflect any server-side changes
            Logger.debug('Reloading settings after save');
            await this.loadSettings();

            Logger.debug('=== SAVE SETTINGS COMPLETED ===');

        } catch (error) {
            Logger.error('Save settings error:', error);
            window.ErrorHandler?.handleSettingsError(error, { operation: 'save' });
            showToast('error', t('settings.saveFailedTitle'), t('settings.saveFailedMessage'));
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
                saveButton.innerHTML = `<span class="btn-icon">⚠️</span> ${t('settings.saveChanges')}`;
            } else {
                saveButton.classList.add('btn-primary');
                saveButton.classList.remove('btn-warning');
                saveButton.innerHTML = `<span class="btn-icon">💾</span> ${t('common.save')}`;
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
                    ${t('settings.systemInfoLoadFailed')}
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
        const statusText = health.status === 'healthy' ? t('settings.healthHealthy') : t('settings.healthDegraded');
        const statusClass = health.status === 'healthy' ? 'status-healthy' : 'status-warning';

        container.innerHTML = `
            <div class="system-status ${statusClass}">
                <div class="status-item">
                    <span class="status-label">${t('settings.systemStatus')}:</span>
                    <span class="status-value">${statusIcon} ${statusText}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">${t('settings.version')}:</span>
                    <span class="status-value">${health.version}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">${t('settings.environment')}:</span>
                    <span class="status-value">${health.environment}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">${t('settings.lastCheck')}:</span>
                    <span class="status-value">${new Date(health.timestamp).toLocaleString(getIntlLocale())}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">${t('settings.database')}:</span>
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
     * Generate QR code for iOS app setup
     */
    generateServerQRCode() {
        const container = document.getElementById('serverQRCode');
        const urlDisplay = document.getElementById('serverURLDisplay');

        if (!container) {
            Logger.debug('QR code container not found');
            return;
        }

        // Get current server URL from browser
        const serverURL = window.location.origin;

        try {
            // Clear any existing QR code
            container.innerHTML = '';

            // Generate QR code using qrcode-generator library
            const qr = qrcode(0, 'M');
            qr.addData(serverURL);
            qr.make();

            // Create QR code as img element with appropriate size
            container.innerHTML = qr.createImgTag(5, 0);

            // Display the URL below the QR code
            if (urlDisplay) {
                urlDisplay.textContent = serverURL;
            }

            Logger.debug('QR code generated for URL:', serverURL);
        } catch (error) {
            Logger.error('Failed to generate QR code:', error);
            container.innerHTML = `
                <div class="error-message">
                    <span class="error-icon">⚠️</span>
                    ${t('settings.qrCodeFailed')}
                </div>
            `;
        }
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
                    ${t('settings.watchFoldersLoadFailed')}
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
                    <input type="text" id="newWatchFolder" placeholder="${t('settings.addNewFolderPlaceholder')}" class="form-control">
                    <button class="btn btn-primary" onclick="addWatchFolder()">
                        <span class="btn-icon">➕</span>
                        ${t('common.add')}
                    </button>
                </div>
                <div class="supported-extensions">
                    <small class="form-text text-muted">
                        ${t('settings.supportedExtensions')}: ${settings.supported_extensions.join(', ')}
                    </small>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="empty-watch-folders">
                    <p>${t('settings.noWatchFolders')}</p>
                    <div class="watch-folder-add">
                        <input type="text" id="newWatchFolder" placeholder="${t('settings.addFolderPlaceholder')}" class="form-control">
                        <button class="btn btn-primary" onclick="addWatchFolder()">
                            <span class="btn-icon">➕</span>
                            ${t('common.add')}
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
        const confirmed = confirm(t('settings.resetConfirm'));
        if (!confirmed) return;

        try {
            showToast('info', t('settings.resettingTitle'), t('settings.resettingMessage'));

            await api.resetApplicationSettings();

            showToast('success', t('settings.resetSuccessTitle'), t('settings.resetSuccessMessage'));
            await this.loadSettings();

        } catch (error) {
            window.ErrorHandler?.handleSettingsError(error, { operation: 'reset' });
            showToast('error', t('common.error'), t('settings.resetFailedMessage'));
        }
    }

    /**
     * Render theme picker UI
     */
    renderThemePicker() {
        const container = document.getElementById('themePicker');
        if (!container) {
            Logger.warn('Theme picker container not found');
            return;
        }

        // Get themes from theme switcher
        if (!window.themeSwitcher) {
            Logger.warn('Theme switcher not initialized');
            return;
        }

        const themes = window.themeSwitcher.getThemeList();
        const currentTheme = window.themeSwitcher.getCurrentTheme();

        // Build theme cards HTML
        const html = themes.map(theme => `
            <div class="theme-card ${theme.id === currentTheme ? 'active' : ''}"
                 data-theme="${theme.id}"
                 onclick="settingsManager.selectTheme('${theme.id}')"
                 role="button"
                 tabindex="0"
                 aria-label="Select ${theme.name} theme"
                 aria-pressed="${theme.id === currentTheme}">
                <div class="theme-preview theme-preview-${theme.id}">
                    <div class="theme-preview-header"></div>
                    <div class="theme-preview-content">
                        <div class="theme-preview-card"></div>
                        <div class="theme-preview-card"></div>
                    </div>
                </div>
                <div class="theme-info">
                    <div class="theme-icon">${theme.icon}</div>
                    <div class="theme-details">
                        <div class="theme-name">${theme.name}</div>
                        <div class="theme-description">${theme.description}</div>
                    </div>
                    ${theme.id === currentTheme ? '<span class="theme-active-badge">Active</span>' : ''}
                </div>
            </div>
        `).join('');

        container.innerHTML = html;

        // Add keyboard support
        container.querySelectorAll('.theme-card').forEach(card => {
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.selectTheme(card.dataset.theme);
                }
            });
        });

        Logger.debug('Theme picker rendered');
    }

    /**
     * Select a theme
     * @param {string} themeId - Theme ID to select
     */
    selectTheme(themeId) {
        if (!window.themeSwitcher) {
            Logger.warn('Theme switcher not initialized');
            return;
        }

        window.themeSwitcher.setTheme(themeId);

        // Update active state in UI
        const container = document.getElementById('themePicker');
        if (container) {
            container.querySelectorAll('.theme-card').forEach(card => {
                const isActive = card.dataset.theme === themeId;
                card.classList.toggle('active', isActive);
                card.setAttribute('aria-pressed', isActive);

                // Update active badge
                const existingBadge = card.querySelector('.theme-active-badge');
                if (isActive && !existingBadge) {
                    const info = card.querySelector('.theme-info');
                    if (info) {
                        const badge = document.createElement('span');
                        badge.className = 'theme-active-badge';
                        badge.textContent = 'Active';
                        info.appendChild(badge);
                    }
                } else if (!isActive && existingBadge) {
                    existingBadge.remove();
                }
            });
        }

        showToast('success', 'Theme Changed', `Applied "${window.themeSwitcher.getTheme(themeId).name}" theme`);
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
        showToast('info', t('common.add'), t('settings.addingFolderMessage'));

        // Validate folder path first
        await api.validateWatchFolder(folderPath);

        // Add watch folder
        const result = await api.addWatchFolder(folderPath);

        showToast('success', t('settings.folderAddedTitle'),
                 t('settings.folderAddedMessage', { path: folderPath }));
        
        input.value = '';
        
        // Reload watch folder settings to reflect changes
        await settingsManager.loadWatchFolderSettings();
        
    } catch (error) {
        window.ErrorHandler?.handleSettingsError(error, { operation: 'add_watch_folder', path: folderPath });
        if (error instanceof ApiError) {
            showToast('error', t('settings.addFailedTitle'), error.getUserMessage());
        } else {
            showToast('error', t('common.error'), t('settings.addFolderFailedMessage'));
        }
    }
}

async function removeWatchFolderFromSettings(folderPath) {
    const confirmed = confirm(t('settings.removeFolderConfirm', { path: folderPath }));
    if (!confirmed) return;

    try {
        showToast('info', t('settings.removingFolderTitle'), t('settings.removingFolderMessage'));

        // Remove watch folder
        const result = await api.removeWatchFolder(folderPath);

        showToast('success', t('settings.folderRemovedTitle'),
                 t('settings.folderRemovedMessage', { path: folderPath }));

        // Reload watch folder settings to reflect changes
        await settingsManager.loadWatchFolderSettings();

    } catch (error) {
        window.ErrorHandler?.handleSettingsError(error, { operation: 'remove_watch_folder', path: folderPath });
        if (error instanceof ApiError) {
            showToast('error', t('settings.removeFailedTitle'), error.getUserMessage());
        } else {
            showToast('error', t('common.error'), t('settings.removeFolderFailedMessage'));
        }
    }
}

async function shutdownServer() {
    const confirmed = confirm(t('settings.shutdownConfirm'));
    if (!confirmed) return;

    try {
        showToast('warning', t('settings.shutdownInProgressTitle'), t('settings.shutdownInProgressMessage'), 3000);

        // Call shutdown API
        await api.shutdownServer();

        showToast('success', t('settings.shutdownSuccessTitle'),
                 t('settings.shutdownSuccessMessage'), 5000);

        // Optionally disable UI or show a message that server is down
        setTimeout(() => {
            document.body.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100vh; flex-direction: column; font-family: system-ui;">
                    <h1 style="color: #ef4444;">⏹️ ${t('settings.shutdownPageTitle')}</h1>
                    <p style="color: #6b7280; margin-top: 10px;">${t('settings.shutdownPageMessage')}</p>
                    <p style="color: #6b7280;">${t('settings.shutdownPageClose')}</p>
                </div>
            `;
        }, 2000);

    } catch (error) {
        window.ErrorHandler?.handleSettingsError(error, { operation: 'shutdown' });
        if (error instanceof ApiError) {
            showToast('error', t('settings.shutdownFailedTitle'), error.getUserMessage());
        } else {
            showToast('error', t('common.error'), t('settings.shutdownFailedMessage'));
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
        validationResult.innerHTML = `<span class="spinner-small"></span> ${t('settings.validating')}`;

        // Validate path
        const response = await api.validateDownloadsPath(folderPath);

        if (response.valid) {
            validationResult.className = 'validation-result success';
            validationResult.innerHTML = '<span class="icon">✓</span> ' + (response.message || t('settings.downloadsPathValid'));
        } else {
            validationResult.className = 'validation-result error';
            validationResult.innerHTML = '<span class="icon">✗</span> ' + (response.error || t('settings.downloadsPathInvalid'));
        }

    } catch (error) {
        Logger.error('Failed to validate downloads path:', error);
        validationResult.className = 'validation-result error';
        validationResult.innerHTML = `<span class="icon">✗</span> ${t('settings.validationFailed')}`;
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
        validationResult.innerHTML = `<span class="spinner-small"></span> ${t('settings.validating')}`;

        // Validate path
        const response = await api.validateLibraryPath(folderPath);

        if (response.valid) {
            validationResult.className = 'validation-result success';
            validationResult.innerHTML = '<span class="icon">✓</span> ' + (response.message || t('settings.libraryPathValid'));
        } else {
            validationResult.className = 'validation-result error';
            validationResult.innerHTML = '<span class="icon">✗</span> ' + (response.error || t('settings.libraryPathInvalid'));
        }

    } catch (error) {
        Logger.error('Failed to validate library path:', error);
        validationResult.className = 'validation-result error';
        validationResult.innerHTML = `<span class="icon">✗</span> ${t('settings.validationFailed')}`;
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
        resultDiv.innerHTML = `<span class="spinner-small"></span> ${t('settings.ffmpegChecking')}`;

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
                <strong>${t('settings.ffmpegInstalled')}</strong><br>
                <small style="margin-top: 0.25rem; display: block;">${result.version || t('settings.ffmpegVersionUnknown')}</small>
            `;
            showToast('success', t('settings.ffmpegFoundTitle'), t('settings.ffmpegFoundMessage'));
        } else {
            resultDiv.className = 'validation-result error';
            resultDiv.innerHTML = `
                <span class="icon">✗</span>
                <strong>${t('settings.ffmpegNotFound')}</strong><br>
                <small style="margin-top: 0.25rem; display: block;">${result.error || t('settings.ffmpegNotInPath')}</small>
            `;
            showToast('warning', t('settings.ffmpegMissingTitle'), t('settings.ffmpegMissingMessage'));
        }

    } catch (error) {
        Logger.error('Failed to check ffmpeg:', error);
        resultDiv.className = 'validation-result error';
        resultDiv.innerHTML = `<span class="icon">✗</span> ${t('settings.checkFailed')}`;
        showToast('error', t('common.error'), t('settings.ffmpegCheckFailedMessage'));
    }
}

// Export for use in main.js
if (typeof window !== 'undefined') {
    window.settingsManager = settingsManager;
}