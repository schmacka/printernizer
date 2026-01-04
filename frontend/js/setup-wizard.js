/**
 * Setup Wizard Manager
 * Handles the first-run setup wizard for Printernizer
 */

class SetupWizardManager {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 5;
        this.wizardData = {
            printer: null,
            paths: {
                downloads: '',
                library: ''
            },
            features: {
                timelapse: false,
                timelapseSourceFolder: '',
                timelapseOutputFolder: '',
                watchFolders: false,
                watchFolderPath: '',
                mqtt: false,
                mqttHost: '',
                mqttPort: 1883
            }
        };
        this.defaults = null;
        this.isInitialized = false;
    }

    /**
     * Initialize the setup wizard
     */
    async init() {
        if (this.isInitialized) return;
        
        Logger.debug('Initializing setup wizard');
        
        // Bind event handlers
        this.bindEvents();
        
        // Load defaults
        await this.loadDefaults();
        
        this.isInitialized = true;
        Logger.debug('Setup wizard initialized');
    }

    /**
     * Check if wizard should be shown and display it
     */
    async checkAndShow() {
        try {
            const status = await api.getSetupStatus();
            
            if (status.should_show_wizard) {
                Logger.info('Setup wizard should be shown', { reason: status.reason });
                await this.show();
                return true;
            }
            
            return false;
        } catch (error) {
            Logger.error('Failed to check setup status', error);
            return false;
        }
    }

    /**
     * Show the setup wizard
     */
    async show() {
        await this.init();
        
        const overlay = document.getElementById('setupWizardOverlay');
        if (overlay) {
            overlay.classList.add('show');
            this.goToStep(1);
            
            // Hide the main navigation
            document.querySelector('.navbar')?.classList.add('hidden');
        }
    }

    /**
     * Hide the setup wizard
     */
    hide() {
        const overlay = document.getElementById('setupWizardOverlay');
        if (overlay) {
            overlay.classList.remove('show');
        }
        
        // Show the main navigation
        document.querySelector('.navbar')?.classList.remove('hidden');
    }

    /**
     * Bind event handlers for wizard interactions
     */
    bindEvents() {
        // Navigation buttons
        document.addEventListener('click', (e) => {
            // Back button
            if (e.target.closest('#wizardBtnBack')) {
                this.previousStep();
            }
            // Next/Continue button
            if (e.target.closest('#wizardBtnNext')) {
                this.nextStep();
            }
            // Skip button
            if (e.target.closest('#wizardBtnSkip')) {
                this.skipStep();
            }
            // Skip entire wizard
            if (e.target.closest('#wizardBtnSkipAll')) {
                this.skipWizard();
            }
            // Finish button
            if (e.target.closest('#wizardBtnFinish')) {
                this.finishWizard();
            }
            // Progress dots (for going back)
            if (e.target.closest('.progress-dot.clickable')) {
                const step = parseInt(e.target.closest('.progress-dot').dataset.step);
                if (step < this.currentStep) {
                    this.goToStep(step);
                }
            }
            // Printer type selection
            if (e.target.closest('.printer-type-card')) {
                this.selectPrinterType(e.target.closest('.printer-type-card'));
            }
            // Discover printers button
            if (e.target.closest('#wizardDiscoverBtn')) {
                this.discoverPrinters();
            }
            // Test connection button
            if (e.target.closest('#wizardTestConnection')) {
                this.testConnection();
            }
            // Select discovered printer
            if (e.target.closest('.discovered-printer-select')) {
                this.selectDiscoveredPrinter(e.target.closest('.discovered-printer-select'));
            }
            // Resume setup banner
            if (e.target.closest('.resume-btn')) {
                this.show();
            }
            // Dismiss banner
            if (e.target.closest('.dismiss-btn')) {
                this.dismissBanner();
            }
            // Re-run wizard from settings
            if (e.target.closest('#rerunSetupWizard')) {
                this.resetAndShow();
            }
        });

        // Feature toggles
        document.addEventListener('change', (e) => {
            if (e.target.closest('#wizardTimelapseToggle')) {
                this.toggleFeatureConfig('timelapse', e.target.checked);
            }
            if (e.target.closest('#wizardWatchFoldersToggle')) {
                this.toggleFeatureConfig('watchFolders', e.target.checked);
            }
            if (e.target.closest('#wizardMqttToggle')) {
                this.toggleFeatureConfig('mqtt', e.target.checked);
            }
        });

        // Path validation on blur
        document.addEventListener('blur', (e) => {
            if (e.target.id === 'wizardDownloadsPath') {
                this.validatePath('downloads', e.target.value);
            }
            if (e.target.id === 'wizardLibraryPath') {
                this.validatePath('library', e.target.value);
            }
        }, true);
    }

    /**
     * Load default configuration values
     */
    async loadDefaults() {
        try {
            this.defaults = await api.getSetupDefaults();
            
            // Pre-fill paths with defaults
            if (this.defaults.paths) {
                this.wizardData.paths.downloads = this.defaults.paths.downloads || '';
                this.wizardData.paths.library = this.defaults.paths.library || '';
            }
            
            // Pre-fill feature settings
            if (this.defaults.features) {
                this.wizardData.features.timelapse = this.defaults.features.timelapse_enabled || false;
                this.wizardData.features.timelapseSourceFolder = this.defaults.features.timelapse_source_folder || '';
                this.wizardData.features.timelapseOutputFolder = this.defaults.features.timelapse_output_folder || '';
            }
            
            Logger.debug('Setup defaults loaded', this.defaults);
        } catch (error) {
            Logger.error('Failed to load setup defaults', error);
            // Use empty defaults
            this.defaults = { environment: 'standalone', paths: {}, features: {} };
        }
    }

    /**
     * Go to a specific step
     */
    goToStep(step) {
        if (step < 1 || step > this.totalSteps) return;
        
        this.currentStep = step;
        
        // Update step visibility
        document.querySelectorAll('.wizard-step').forEach(el => {
            el.classList.remove('active');
        });
        document.getElementById(`wizardStep${step}`)?.classList.add('active');
        
        // Update progress dots
        document.querySelectorAll('.progress-dot').forEach((dot, index) => {
            dot.classList.remove('active', 'completed', 'clickable');
            const dotStep = index + 1;
            if (dotStep === step) {
                dot.classList.add('active');
            } else if (dotStep < step) {
                dot.classList.add('completed', 'clickable');
            }
        });
        
        // Update step indicator
        const indicator = document.getElementById('wizardStepIndicator');
        if (indicator) {
            indicator.textContent = `Schritt ${step} von ${this.totalSteps}`;
        }
        
        // Update navigation buttons
        this.updateNavigation();
        
        // Step-specific initialization
        this.initStep(step);
    }

    /**
     * Initialize step-specific content
     */
    initStep(step) {
        switch (step) {
            case 1:
                // Welcome step - no special init needed
                break;
            case 2:
                // Printer step - load discovery results if any
                this.initPrinterStep();
                break;
            case 3:
                // Paths step - populate with defaults
                this.initPathsStep();
                break;
            case 4:
                // Features step - set toggle states
                this.initFeaturesStep();
                break;
            case 5:
                // Summary step - generate summary
                this.generateSummary();
                break;
        }
    }

    /**
     * Initialize printer step
     */
    initPrinterStep() {
        // Set current values if any
        if (this.wizardData.printer) {
            const typeCard = document.querySelector(`.printer-type-card[data-type="${this.wizardData.printer.type}"]`);
            if (typeCard) {
                this.selectPrinterType(typeCard, false);
            }
            
            // Fill in form fields
            const nameInput = document.getElementById('wizardPrinterName');
            const ipInput = document.getElementById('wizardPrinterIp');
            
            if (nameInput) nameInput.value = this.wizardData.printer.name || '';
            if (ipInput) ipInput.value = this.wizardData.printer.ip || '';
            
            if (this.wizardData.printer.type === 'bambu_lab') {
                const accessCode = document.getElementById('wizardBambuAccessCode');
                const serial = document.getElementById('wizardBambuSerial');
                if (accessCode) accessCode.value = this.wizardData.printer.access_code || '';
                if (serial) serial.value = this.wizardData.printer.serial || '';
            } else if (this.wizardData.printer.type === 'prusa') {
                const apiKey = document.getElementById('wizardPrusaApiKey');
                if (apiKey) apiKey.value = this.wizardData.printer.api_key || '';
            }
        }
    }

    /**
     * Initialize paths step
     */
    initPathsStep() {
        const downloadsInput = document.getElementById('wizardDownloadsPath');
        const libraryInput = document.getElementById('wizardLibraryPath');
        
        if (downloadsInput && !downloadsInput.value) {
            downloadsInput.value = this.wizardData.paths.downloads;
        }
        if (libraryInput && !libraryInput.value) {
            libraryInput.value = this.wizardData.paths.library;
        }
        
        // Show environment info
        const envInfo = document.getElementById('wizardEnvInfo');
        if (envInfo && this.defaults) {
            envInfo.textContent = this.getEnvironmentLabel(this.defaults.environment);
        }
    }

    /**
     * Initialize features step
     */
    initFeaturesStep() {
        const timelapseToggle = document.getElementById('wizardTimelapseToggle');
        const watchFoldersToggle = document.getElementById('wizardWatchFoldersToggle');
        const mqttToggle = document.getElementById('wizardMqttToggle');
        
        if (timelapseToggle) {
            timelapseToggle.checked = this.wizardData.features.timelapse;
            this.toggleFeatureConfig('timelapse', this.wizardData.features.timelapse);
        }
        if (watchFoldersToggle) {
            watchFoldersToggle.checked = this.wizardData.features.watchFolders;
            this.toggleFeatureConfig('watchFolders', this.wizardData.features.watchFolders);
        }
        if (mqttToggle) {
            mqttToggle.checked = this.wizardData.features.mqtt;
            this.toggleFeatureConfig('mqtt', this.wizardData.features.mqtt);
        }
    }

    /**
     * Get human-readable environment label
     */
    getEnvironmentLabel(env) {
        const labels = {
            'standalone': 'Standalone (Python)',
            'docker': 'Docker',
            'home_assistant': 'Home Assistant Add-on'
        };
        return labels[env] || env;
    }

    /**
     * Update navigation buttons based on current step
     */
    updateNavigation() {
        const backBtn = document.getElementById('wizardBtnBack');
        const nextBtn = document.getElementById('wizardBtnNext');
        const skipBtn = document.getElementById('wizardBtnSkip');
        const skipAllBtn = document.getElementById('wizardBtnSkipAll');
        const finishBtn = document.getElementById('wizardBtnFinish');
        
        // Hide all buttons first
        [backBtn, nextBtn, skipBtn, skipAllBtn, finishBtn].forEach(btn => {
            if (btn) btn.style.display = 'none';
        });
        
        // Show appropriate buttons based on step
        switch (this.currentStep) {
            case 1:
                // Welcome: Skip All, Start (Next)
                if (skipAllBtn) skipAllBtn.style.display = 'inline-flex';
                if (nextBtn) {
                    nextBtn.style.display = 'inline-flex';
                    nextBtn.innerHTML = '<span>Einrichtung starten</span> <span>→</span>';
                }
                break;
            case 2:
            case 3:
            case 4:
                // Middle steps: Back, Skip, Continue
                if (backBtn) backBtn.style.display = 'inline-flex';
                if (skipBtn) skipBtn.style.display = 'inline-flex';
                if (nextBtn) {
                    nextBtn.style.display = 'inline-flex';
                    nextBtn.innerHTML = '<span>Weiter</span> <span>→</span>';
                }
                break;
            case 5:
                // Summary: Back, Finish
                if (backBtn) backBtn.style.display = 'inline-flex';
                if (finishBtn) finishBtn.style.display = 'inline-flex';
                break;
        }
    }

    /**
     * Go to next step
     */
    async nextStep() {
        // Validate current step before proceeding
        const isValid = await this.validateCurrentStep();
        if (!isValid) return;
        
        // Collect data from current step
        this.collectStepData();
        
        if (this.currentStep < this.totalSteps) {
            this.goToStep(this.currentStep + 1);
        }
    }

    /**
     * Go to previous step
     */
    previousStep() {
        if (this.currentStep > 1) {
            this.goToStep(this.currentStep - 1);
        }
    }

    /**
     * Skip current step
     */
    skipStep() {
        // Use defaults for skipped step
        if (this.currentStep < this.totalSteps) {
            this.goToStep(this.currentStep + 1);
        }
    }

    /**
     * Skip entire wizard
     */
    async skipWizard() {
        try {
            await api.completeSetup(true);
            this.hide();
            showToast('info', 'Setup übersprungen', 'Du kannst den Setup-Assistenten jederzeit in den Einstellungen erneut starten.');
        } catch (error) {
            Logger.error('Failed to skip wizard', error);
            showToast('error', 'Fehler', 'Konnte Setup nicht überspringen');
        }
    }

    /**
     * Validate current step data
     */
    async validateCurrentStep() {
        switch (this.currentStep) {
            case 1:
                // Welcome - always valid
                return true;
            case 2:
                // Printer - optional, but if filled, validate
                return this.validatePrinterStep();
            case 3:
                // Paths - validate paths exist and are writable
                return await this.validatePathsStep();
            case 4:
                // Features - validate feature configurations
                return this.validateFeaturesStep();
            case 5:
                // Summary - always valid
                return true;
            default:
                return true;
        }
    }

    /**
     * Validate printer step
     */
    validatePrinterStep() {
        const selectedType = document.querySelector('.printer-type-card.selected');
        
        // If no type selected, that's fine (skipping)
        if (!selectedType) {
            this.wizardData.printer = null;
            return true;
        }
        
        const type = selectedType.dataset.type;
        const name = document.getElementById('wizardPrinterName')?.value.trim();
        const ip = document.getElementById('wizardPrinterIp')?.value.trim();
        
        // If type selected but no name/IP, clear validation errors and allow skip
        if (!name && !ip) {
            this.wizardData.printer = null;
            return true;
        }
        
        // If partially filled, validate required fields
        if (!name) {
            this.showFieldError('wizardPrinterName', 'Bitte gib einen Namen für den Drucker ein');
            return false;
        }
        
        if (!ip) {
            this.showFieldError('wizardPrinterIp', 'Bitte gib die IP-Adresse ein');
            return false;
        }
        
        // Validate IP format
        const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
        if (!ipRegex.test(ip)) {
            this.showFieldError('wizardPrinterIp', 'Ungültiges IP-Adressformat');
            return false;
        }
        
        // Type-specific validation
        if (type === 'bambu_lab') {
            const accessCode = document.getElementById('wizardBambuAccessCode')?.value.trim();
            if (!accessCode) {
                this.showFieldError('wizardBambuAccessCode', 'Bitte gib den Zugangscode ein');
                return false;
            }
            if (accessCode.length !== 8) {
                this.showFieldError('wizardBambuAccessCode', 'Der Zugangscode muss 8 Zeichen lang sein');
                return false;
            }
        } else if (type === 'prusa') {
            const apiKey = document.getElementById('wizardPrusaApiKey')?.value.trim();
            if (!apiKey) {
                this.showFieldError('wizardPrusaApiKey', 'Bitte gib den API-Key ein');
                return false;
            }
        }
        
        return true;
    }

    /**
     * Validate paths step
     */
    async validatePathsStep() {
        const downloadsPath = document.getElementById('wizardDownloadsPath')?.value.trim();
        const libraryPath = document.getElementById('wizardLibraryPath')?.value.trim();
        
        // Paths can use defaults if empty
        if (!downloadsPath && !libraryPath) {
            return true;
        }
        
        let isValid = true;
        
        if (downloadsPath) {
            const result = await this.validatePath('downloads', downloadsPath);
            if (!result) isValid = false;
        }
        
        if (libraryPath) {
            const result = await this.validatePath('library', libraryPath);
            if (!result) isValid = false;
        }
        
        return isValid;
    }

    /**
     * Validate features step
     */
    validateFeaturesStep() {
        // If timelapse enabled, validate paths
        if (this.wizardData.features.timelapse) {
            const sourceFolder = document.getElementById('wizardTimelapseSource')?.value.trim();
            const outputFolder = document.getElementById('wizardTimelapseOutput')?.value.trim();
            
            // Allow empty for defaults
            this.wizardData.features.timelapseSourceFolder = sourceFolder;
            this.wizardData.features.timelapseOutputFolder = outputFolder;
        }
        
        // If watch folders enabled, validate path
        if (this.wizardData.features.watchFolders) {
            const watchPath = document.getElementById('wizardWatchFolderPath')?.value.trim();
            this.wizardData.features.watchFolderPath = watchPath;
        }
        
        // If MQTT enabled, validate host
        if (this.wizardData.features.mqtt) {
            const mqttHost = document.getElementById('wizardMqttHost')?.value.trim();
            const mqttPort = document.getElementById('wizardMqttPort')?.value.trim();
            
            if (!mqttHost) {
                this.showFieldError('wizardMqttHost', 'Bitte gib den MQTT-Host ein');
                return false;
            }
            
            this.wizardData.features.mqttHost = mqttHost;
            this.wizardData.features.mqttPort = parseInt(mqttPort) || 1883;
        }
        
        return true;
    }

    /**
     * Collect data from current step
     */
    collectStepData() {
        switch (this.currentStep) {
            case 2:
                this.collectPrinterData();
                break;
            case 3:
                this.collectPathsData();
                break;
            case 4:
                this.collectFeaturesData();
                break;
        }
    }

    /**
     * Collect printer data
     */
    collectPrinterData() {
        const selectedType = document.querySelector('.printer-type-card.selected');
        if (!selectedType) {
            this.wizardData.printer = null;
            return;
        }
        
        const type = selectedType.dataset.type;
        const name = document.getElementById('wizardPrinterName')?.value.trim();
        const ip = document.getElementById('wizardPrinterIp')?.value.trim();
        
        if (!name || !ip) {
            this.wizardData.printer = null;
            return;
        }
        
        this.wizardData.printer = {
            type: type,
            name: name,
            ip: ip
        };
        
        if (type === 'bambu_lab') {
            this.wizardData.printer.access_code = document.getElementById('wizardBambuAccessCode')?.value.trim();
            this.wizardData.printer.serial = document.getElementById('wizardBambuSerial')?.value.trim();
        } else if (type === 'prusa') {
            this.wizardData.printer.api_key = document.getElementById('wizardPrusaApiKey')?.value.trim();
        }
    }

    /**
     * Collect paths data
     */
    collectPathsData() {
        const downloadsPath = document.getElementById('wizardDownloadsPath')?.value.trim();
        const libraryPath = document.getElementById('wizardLibraryPath')?.value.trim();
        
        if (downloadsPath) {
            this.wizardData.paths.downloads = downloadsPath;
        }
        if (libraryPath) {
            this.wizardData.paths.library = libraryPath;
        }
    }

    /**
     * Collect features data
     */
    collectFeaturesData() {
        this.wizardData.features.timelapse = document.getElementById('wizardTimelapseToggle')?.checked || false;
        this.wizardData.features.watchFolders = document.getElementById('wizardWatchFoldersToggle')?.checked || false;
        this.wizardData.features.mqtt = document.getElementById('wizardMqttToggle')?.checked || false;
        
        if (this.wizardData.features.timelapse) {
            this.wizardData.features.timelapseSourceFolder = document.getElementById('wizardTimelapseSource')?.value.trim() || '';
            this.wizardData.features.timelapseOutputFolder = document.getElementById('wizardTimelapseOutput')?.value.trim() || '';
        }
        
        if (this.wizardData.features.watchFolders) {
            this.wizardData.features.watchFolderPath = document.getElementById('wizardWatchFolderPath')?.value.trim() || '';
        }
        
        if (this.wizardData.features.mqtt) {
            this.wizardData.features.mqttHost = document.getElementById('wizardMqttHost')?.value.trim() || '';
            this.wizardData.features.mqttPort = parseInt(document.getElementById('wizardMqttPort')?.value) || 1883;
        }
    }

    /**
     * Select printer type
     */
    selectPrinterType(card, resetFields = true) {
        // Remove selection from all cards
        document.querySelectorAll('.printer-type-card').forEach(c => {
            c.classList.remove('selected');
        });
        
        // Add selection to clicked card
        card.classList.add('selected');
        
        const type = card.dataset.type;
        
        // Show/hide type-specific fields
        const bambuFields = document.getElementById('wizardBambuFields');
        const prusaFields = document.getElementById('wizardPrusaFields');
        const printerForm = document.getElementById('wizardPrinterForm');
        
        if (printerForm) printerForm.style.display = 'block';
        if (bambuFields) bambuFields.style.display = type === 'bambu_lab' ? 'block' : 'none';
        if (prusaFields) prusaFields.style.display = type === 'prusa' ? 'block' : 'none';
        
        if (resetFields) {
            // Clear form fields
            document.getElementById('wizardPrinterName')?.value && (document.getElementById('wizardPrinterName').value = '');
            document.getElementById('wizardPrinterIp')?.value && (document.getElementById('wizardPrinterIp').value = '');
        }
    }

    /**
     * Discover printers on the network
     */
    async discoverPrinters() {
        const btn = document.getElementById('wizardDiscoverBtn');
        const list = document.getElementById('wizardDiscoveredList');
        
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="wizard-spinner" style="width:16px;height:16px;margin-right:8px;"></span> Suche...';
        }
        
        try {
            const result = await api.discoverPrinters();
            
            if (list) {
                if (result.discovered && result.discovered.length > 0) {
                    // Filter to only show printers not already added
                    const newPrinters = result.discovered.filter(p => !p.already_added);

                    if (newPrinters.length > 0) {
                        list.innerHTML = newPrinters.map(printer => `
                            <div class="discovered-printer-item">
                                <div class="discovered-printer-info">
                                    <span class="printer-icon">${printer.type === 'bambu_lab' ? '🖨️' : '🦎'}</span>
                                    <div>
                                        <strong>${escapeHtml(printer.name || printer.ip)}</strong>
                                        <div style="font-size: 0.85em; color: var(--gray-500);">${escapeHtml(printer.ip)}</div>
                                    </div>
                                </div>
                                <button class="btn btn-sm btn-primary discovered-printer-select"
                                        data-type="${printer.type}"
                                        data-name="${escapeHtml(printer.name || '')}"
                                        data-ip="${escapeHtml(printer.ip)}"
                                        data-serial="${escapeHtml(printer.serial || '')}">
                                    Auswählen
                                </button>
                            </div>
                        `).join('');
                    } else {
                        // All discovered printers are already added
                        list.innerHTML = '<p style="text-align:center;color:var(--gray-500);padding:1rem;">Alle gefundenen Drucker sind bereits hinzugefügt. Du kannst die Daten manuell eingeben.</p>';
                    }
                } else {
                    list.innerHTML = '<p style="text-align:center;color:var(--gray-500);padding:1rem;">Keine Drucker gefunden. Du kannst die Daten manuell eingeben.</p>';
                }
            }
        } catch (error) {
            Logger.error('Printer discovery failed', error);
            if (list) {
                list.innerHTML = '<p style="text-align:center;color:var(--error-color);padding:1rem;">Drucker-Suche fehlgeschlagen. Bitte gib die Daten manuell ein.</p>';
            }
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '🔍 Netzwerk durchsuchen';
            }
        }
    }

    /**
     * Select a discovered printer
     */
    selectDiscoveredPrinter(btn) {
        const type = btn.dataset.type;
        const name = btn.dataset.name;
        const ip = btn.dataset.ip;
        const serial = btn.dataset.serial;
        
        // Select the appropriate type card
        const typeCard = document.querySelector(`.printer-type-card[data-type="${type}"]`);
        if (typeCard) {
            this.selectPrinterType(typeCard, false);
        }
        
        // Fill in the form
        const nameInput = document.getElementById('wizardPrinterName');
        const ipInput = document.getElementById('wizardPrinterIp');
        
        if (nameInput) nameInput.value = name;
        if (ipInput) ipInput.value = ip;
        
        if (type === 'bambu_lab' && serial) {
            const serialInput = document.getElementById('wizardBambuSerial');
            if (serialInput) serialInput.value = serial;
        }
        
        showToast('success', 'Drucker ausgewählt', `${name || ip} wurde übernommen`);
    }

    /**
     * Test printer connection
     */
    async testConnection() {
        const btn = document.getElementById('wizardTestConnection');
        const result = document.getElementById('wizardConnectionResult');
        
        // Collect current form data
        this.collectPrinterData();
        
        if (!this.wizardData.printer) {
            if (result) {
                result.className = 'connection-test-result error';
                result.innerHTML = '<span>❌</span> Bitte fülle zuerst alle Pflichtfelder aus';
            }
            return;
        }
        
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="wizard-spinner" style="width:16px;height:16px;margin-right:8px;"></span> Teste...';
        }
        
        if (result) {
            result.className = 'connection-test-result pending';
            result.innerHTML = '<span>⏳</span> Verbindung wird getestet...';
        }
        
        try {
            // Build printer config for test
            const printerConfig = {
                name: this.wizardData.printer.name,
                type: this.wizardData.printer.type,
                ip_address: this.wizardData.printer.ip,
                is_active: true
            };
            
            if (this.wizardData.printer.type === 'bambu_lab') {
                printerConfig.access_code = this.wizardData.printer.access_code;
                printerConfig.serial_number = this.wizardData.printer.serial;
            } else if (this.wizardData.printer.type === 'prusa') {
                printerConfig.api_key = this.wizardData.printer.api_key;
            }
            
            // Test connection
            const testResult = await api.testPrinterConnection(printerConfig);
            
            if (result) {
                if (testResult.success) {
                    result.className = 'connection-test-result success';
                    result.innerHTML = '<span>✅</span> Verbindung erfolgreich!';
                } else {
                    result.className = 'connection-test-result error';
                    result.innerHTML = `<span>❌</span> ${escapeHtml(testResult.message || 'Verbindung fehlgeschlagen')}`;
                }
            }
        } catch (error) {
            Logger.error('Connection test failed', error);
            if (result) {
                result.className = 'connection-test-result error';
                result.innerHTML = '<span>❌</span> Verbindungstest fehlgeschlagen';
            }
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '🔌 Verbindung testen';
            }
        }
    }

    /**
     * Validate a path
     */
    async validatePath(type, path) {
        if (!path) return true;
        
        const validationEl = document.getElementById(`wizard${type.charAt(0).toUpperCase() + type.slice(1)}Validation`);
        
        try {
            let result;
            if (type === 'downloads') {
                result = await api.validateDownloadsPath(path);
            } else {
                result = await api.validateLibraryPath(path);
            }
            
            if (validationEl) {
                if (result.valid) {
                    validationEl.className = 'path-validation valid';
                    validationEl.innerHTML = '<span>✓</span> Pfad ist gültig und beschreibbar';
                } else {
                    validationEl.className = 'path-validation invalid';
                    validationEl.innerHTML = `<span>✗</span> ${escapeHtml(result.message || 'Ungültiger Pfad')}`;
                }
            }
            
            return result.valid;
        } catch (error) {
            Logger.error('Path validation failed', error);
            if (validationEl) {
                validationEl.className = 'path-validation invalid';
                validationEl.innerHTML = '<span>✗</span> Pfadvalidierung fehlgeschlagen';
            }
            return false;
        }
    }

    /**
     * Toggle feature configuration visibility
     */
    toggleFeatureConfig(feature, enabled) {
        const configEl = document.getElementById(`wizard${feature.charAt(0).toUpperCase() + feature.slice(1)}Config`);
        if (configEl) {
            configEl.style.display = enabled ? 'block' : 'none';
        }
    }

    /**
     * Generate summary for final step
     */
    generateSummary() {
        // Printer summary
        const printerSummary = document.getElementById('wizardSummaryPrinter');
        if (printerSummary) {
            if (this.wizardData.printer) {
                printerSummary.innerHTML = `
                    <div class="summary-item">
                        <span class="summary-item-label">Name</span>
                        <span class="summary-item-value">${escapeHtml(this.wizardData.printer.name)}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-item-label">Typ</span>
                        <span class="summary-item-value">${this.wizardData.printer.type === 'bambu_lab' ? 'Bambu Lab' : 'Prusa Core One'}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-item-label">IP-Adresse</span>
                        <span class="summary-item-value">${escapeHtml(this.wizardData.printer.ip)}</span>
                    </div>
                `;
            } else {
                printerSummary.innerHTML = `
                    <div class="summary-item">
                        <span class="summary-item-label">Status</span>
                        <span class="summary-item-value warning">Später konfigurieren</span>
                    </div>
                `;
            }
        }
        
        // Paths summary
        const pathsSummary = document.getElementById('wizardSummaryPaths');
        if (pathsSummary) {
            pathsSummary.innerHTML = `
                <div class="summary-item">
                    <span class="summary-item-label">Downloads</span>
                    <span class="summary-item-value">${escapeHtml(this.wizardData.paths.downloads || this.defaults?.paths?.downloads || 'Standard')}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-item-label">Bibliothek</span>
                    <span class="summary-item-value">${escapeHtml(this.wizardData.paths.library || this.defaults?.paths?.library || 'Standard')}</span>
                </div>
            `;
        }
        
        // Features summary
        const featuresSummary = document.getElementById('wizardSummaryFeatures');
        if (featuresSummary) {
            const enabledFeatures = [];
            if (this.wizardData.features.timelapse) enabledFeatures.push('Zeitraffer');
            if (this.wizardData.features.watchFolders) enabledFeatures.push('Watch-Ordner');
            if (this.wizardData.features.mqtt) enabledFeatures.push('MQTT');
            
            if (enabledFeatures.length > 0) {
                featuresSummary.innerHTML = enabledFeatures.map(f => `
                    <div class="summary-item">
                        <span class="summary-item-label">${escapeHtml(f)}</span>
                        <span class="summary-item-value success">Aktiviert</span>
                    </div>
                `).join('');
            } else {
                featuresSummary.innerHTML = `
                    <div class="summary-item">
                        <span class="summary-item-label">Status</span>
                        <span class="summary-item-value">Keine optionalen Features aktiviert</span>
                    </div>
                `;
            }
        }
    }

    /**
     * Finish the wizard and apply settings
     */
    async finishWizard() {
        const finishBtn = document.getElementById('wizardBtnFinish');
        
        if (finishBtn) {
            finishBtn.disabled = true;
            finishBtn.innerHTML = '<span class="wizard-spinner" style="width:16px;height:16px;margin-right:8px;"></span> Speichere...';
        }
        
        try {
            // Apply settings
            await this.applySettings();
            
            // Mark setup as complete
            await api.completeSetup(false);
            
            // Hide wizard
            this.hide();
            
            // Show success toast
            showToast('success', 'Einrichtung abgeschlossen', 'Willkommen bei Printernizer! 🎉');
            
            // Refresh the current page to show new data
            if (window.app) {
                window.app.showPage('dashboard');
            }
        } catch (error) {
            Logger.error('Failed to finish wizard', error);
            showToast('error', 'Fehler', 'Einrichtung konnte nicht abgeschlossen werden');
        } finally {
            if (finishBtn) {
                finishBtn.disabled = false;
                finishBtn.innerHTML = '✓ Einrichtung abschließen';
            }
        }
    }

    /**
     * Apply all wizard settings
     */
    async applySettings() {
        // Add printer if configured
        if (this.wizardData.printer) {
            const printerData = {
                name: this.wizardData.printer.name,
                type: this.wizardData.printer.type,
                ip_address: this.wizardData.printer.ip,
                is_active: true
            };
            
            if (this.wizardData.printer.type === 'bambu_lab') {
                printerData.access_code = this.wizardData.printer.access_code;
                printerData.serial_number = this.wizardData.printer.serial;
            } else if (this.wizardData.printer.type === 'prusa') {
                printerData.api_key = this.wizardData.printer.api_key;
            }
            
            try {
                await api.addPrinter(printerData);
                Logger.info('Printer added from wizard', { name: printerData.name });
            } catch (error) {
                Logger.error('Failed to add printer from wizard', error);
                throw error;
            }
        }
        
        // Update path settings
        const settingsUpdate = {};
        
        if (this.wizardData.paths.downloads) {
            settingsUpdate.downloads_path = this.wizardData.paths.downloads;
        }
        if (this.wizardData.paths.library) {
            settingsUpdate.library_path = this.wizardData.paths.library;
            settingsUpdate.library_enabled = true;
        }
        
        // Update feature settings
        if (this.wizardData.features.timelapse) {
            settingsUpdate.timelapse_enabled = true;
            if (this.wizardData.features.timelapseSourceFolder) {
                settingsUpdate.timelapse_source_folder = this.wizardData.features.timelapseSourceFolder;
            }
            if (this.wizardData.features.timelapseOutputFolder) {
                settingsUpdate.timelapse_output_folder = this.wizardData.features.timelapseOutputFolder;
            }
        }
        
        // Apply settings if any were changed
        if (Object.keys(settingsUpdate).length > 0) {
            try {
                await api.updateApplicationSettings(settingsUpdate);
                Logger.info('Settings updated from wizard', settingsUpdate);
            } catch (error) {
                Logger.error('Failed to update settings from wizard', error);
                // Don't throw - printer might have been added successfully
            }
        }
        
        // Add watch folder if configured
        if (this.wizardData.features.watchFolders && this.wizardData.features.watchFolderPath) {
            try {
                await api.addWatchFolder(this.wizardData.features.watchFolderPath);
                Logger.info('Watch folder added from wizard', { path: this.wizardData.features.watchFolderPath });
            } catch (error) {
                Logger.error('Failed to add watch folder from wizard', error);
                // Don't throw - other settings might have been applied
            }
        }
    }

    /**
     * Show field error
     */
    showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        field.classList.add('error');
        
        // Find or create error message element
        let errorEl = field.parentElement.querySelector('.form-error');
        if (!errorEl) {
            errorEl = document.createElement('div');
            errorEl.className = 'form-error';
            field.parentElement.appendChild(errorEl);
        }
        errorEl.textContent = message;
        
        // Focus the field
        field.focus();
    }

    /**
     * Reset wizard and show it again
     */
    async resetAndShow() {
        try {
            await api.resetSetup();
            
            // Reset wizard state
            this.currentStep = 1;
            this.wizardData = {
                printer: null,
                paths: { downloads: '', library: '' },
                features: {
                    timelapse: false,
                    timelapseSourceFolder: '',
                    timelapseOutputFolder: '',
                    watchFolders: false,
                    watchFolderPath: '',
                    mqtt: false,
                    mqttHost: '',
                    mqttPort: 1883
                }
            };
            
            await this.loadDefaults();
            await this.show();
        } catch (error) {
            Logger.error('Failed to reset wizard', error);
            showToast('error', 'Fehler', 'Konnte Setup-Assistenten nicht zurücksetzen');
        }
    }

    /**
     * Show incomplete setup banner
     */
    showBanner() {
        const banner = document.getElementById('setupIncompleteBanner');
        if (banner) {
            banner.classList.add('show');
        }
    }

    /**
     * Dismiss incomplete setup banner
     */
    dismissBanner() {
        const banner = document.getElementById('setupIncompleteBanner');
        if (banner) {
            banner.classList.remove('show');
        }
    }
}

// Create global instance
window.setupWizard = new SetupWizardManager();
