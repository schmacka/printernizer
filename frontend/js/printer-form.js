/**
 * Printer Form Validation and Handling
 * Enhanced form handling for printer configuration with real-time validation
 */

class PrinterFormHandler {
    constructor() {
        this.form = null;
        this.isSubmitting = false;
        this.setupEventListeners();
    }

    /**
     * Setup form event listeners
     */
    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.form = document.getElementById('addPrinterForm');
            if (this.form) {
                this.initializeForm();
            }
        });

        // Handle printer type changes globally
        document.addEventListener('change', (e) => {
            if (e.target.id === 'printerType') {
                this.handlePrinterTypeChange(e.target.value);
            }
        });

        // Handle form submission globally
        document.addEventListener('submit', (e) => {
            if (e.target.id === 'addPrinterForm') {
                e.preventDefault();
                this.handleSubmit(e);
            }
        });
    }

    /**
     * Initialize form with validation
     */
    initializeForm() {
        if (!this.form) return;

        // Add real-time validation to form fields
        const fields = this.form.querySelectorAll('input, select');
        fields.forEach(field => {
            // Validate on blur (when user leaves field)
            field.addEventListener('blur', () => {
                this.validateField(field);
            });

            // Clear errors on input (when user starts typing)
            field.addEventListener('input', () => {
                if (field.classList.contains('error')) {
                    this.clearFieldError(field);
                }
            });

            // Show success state for valid fields
            field.addEventListener('input', debounce(() => {
                if (field.value.trim() && !field.classList.contains('error')) {
                    this.validateField(field);
                }
            }, 500));
        });

        console.log('Printer form initialized with validation');
    }

    /**
     * Handle printer type selection change
     */
    handlePrinterTypeChange(printerType) {
        const bambuFields = document.getElementById('bambuFields');
        const prusaFields = document.getElementById('prusaFields');

        // Hide all specific fields first
        if (bambuFields) {
            bambuFields.style.display = 'none';
            this.setFieldsRequired(bambuFields, false);
        }
        if (prusaFields) {
            prusaFields.style.display = 'none';
            this.setFieldsRequired(prusaFields, false);
        }

        // Show relevant fields based on selection
        if (printerType === 'bambu_lab' && bambuFields) {
            bambuFields.style.display = 'block';
            this.setFieldsRequired(bambuFields, true);
        } else if (printerType === 'prusa_core' && prusaFields) {
            prusaFields.style.display = 'block';
            this.setFieldsRequired(prusaFields, true);
        }
    }

    /**
     * Set required attribute on fields within container
     */
    setFieldsRequired(container, required) {
        const fields = container.querySelectorAll('input');
        fields.forEach(field => {
            if (required) {
                field.setAttribute('required', 'required');
            } else {
                field.removeAttribute('required');
                this.clearFieldError(field);
            }
        });
    }

    /**
     * Validate individual field
     */
    validateField(field) {
        const value = field.value.trim();
        
        // Skip validation if field is not visible
        if (!this.isFieldVisible(field)) {
            return true;
        }

        // Check if required field is empty
        if (field.hasAttribute('required') && !value) {
            this.showFieldError(field, `${this.getFieldLabel(field)} ist erforderlich`);
            return false;
        }

        // Skip further validation if field is empty and not required
        if (!value) {
            this.clearFieldError(field);
            return true;
        }

        // Validate based on data-validate attribute
        const validationType = field.getAttribute('data-validate');
        let isValid = true;
        let errorMessage = '';

        switch (validationType) {
            case 'ip':
                if (!isValidIP(value)) {
                    isValid = false;
                    errorMessage = 'Ungültige IP-Adresse (Format: xxx.xxx.xxx.xxx)';
                }
                break;

            case 'printer-name':
                if (!isValidPrinterName(value)) {
                    isValid = false;
                    errorMessage = 'Druckername muss 3-50 Zeichen lang sein (Buchstaben, Zahlen, Leerzeichen)';
                }
                break;

            case 'access-code':
                if (!isValidAccessCode(value)) {
                    isValid = false;
                    errorMessage = 'Access Code muss genau 8 Ziffern enthalten';
                }
                break;

            case 'serial-number':
                if (!isValidSerialNumber(value)) {
                    isValid = false;
                    errorMessage = 'Seriennummer muss 8-12 Zeichen (Buchstaben und Zahlen) enthalten';
                }
                break;

            case 'api-key':
                if (!isValidApiKey(value)) {
                    isValid = false;
                    errorMessage = 'API Key muss zwischen 16 und 64 Zeichen lang sein';
                }
                break;
        }

        if (isValid) {
            this.clearFieldError(field);
            this.showFieldSuccess(field);
            return true;
        } else {
            this.showFieldError(field, errorMessage);
            return false;
        }
    }

    /**
     * Check if field is currently visible
     */
    isFieldVisible(field) {
        let element = field;
        while (element) {
            const style = window.getComputedStyle(element);
            if (style.display === 'none' || style.visibility === 'hidden') {
                return false;
            }
            element = element.parentElement;
        }
        return true;
    }

    /**
     * Get field label for error messages
     */
    getFieldLabel(field) {
        const label = document.querySelector(`label[for="${field.id}"]`);
        if (label) {
            return label.textContent.replace(':', '').trim();
        }
        return field.placeholder || field.name || field.id || 'Feld';
    }

    /**
     * Show field validation error
     */
    showFieldError(field, message) {
        field.classList.add('error');
        field.classList.remove('success');
        
        // Remove existing error message
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Add new error message
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = message;
        field.parentNode.appendChild(errorElement);
    }

    /**
     * Show field validation success
     */
    showFieldSuccess(field) {
        if (field.value.trim()) {
            field.classList.add('success');
        }
        field.classList.remove('error');
    }

    /**
     * Clear field validation error
     */
    clearFieldError(field) {
        field.classList.remove('error');
        field.classList.remove('success');
        
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
    }

    /**
     * Validate entire form
     */
    validateForm() {
        if (!this.form) return false;

        const fields = this.form.querySelectorAll('input[required], select[required]');
        let isValid = true;

        fields.forEach(field => {
            if (this.isFieldVisible(field)) {
                if (!this.validateField(field)) {
                    isValid = false;
                }
            }
        });

        return isValid;
    }

    /**
     * Handle form submission
     */
    async handleSubmit(event) {
        event.preventDefault();

        if (this.isSubmitting) return;

        // Validate form
        if (!this.validateForm()) {
            showToast('warning', 'Validierungsfehler', 'Bitte korrigieren Sie die Eingabefehler');
            return;
        }

        this.isSubmitting = true;
        this.setSubmitButtonState(true);

        try {
            // Collect form data
            const formData = this.collectFormData();
            
            // Validate printer connectivity before saving
            const connectivityCheck = await this.validatePrinterConnectivity(formData);
            if (!connectivityCheck.success) {
                showToast('warning', 'Verbindungswarnung', 
                    `Drucker ist nicht erreichbar: ${connectivityCheck.error}. Trotzdem hinzufügen?`);
                
                // Give user choice to continue or cancel
                const continueAnyway = confirm('Drucker ist nicht erreichbar. Trotzdem hinzufügen?');
                if (!continueAnyway) {
                    return;
                }
            }

            // Submit form data
            const response = await api.addPrinter(formData);
            
            if (response.success) {
                showToast('success', 'Erfolg', CONFIG.SUCCESS_MESSAGES.PRINTER_ADDED);
                closeModal('addPrinterModal');
                
                // Refresh printer lists
                if (typeof printerManager !== 'undefined' && printerManager.loadPrinters) {
                    printerManager.loadPrinters();
                }
                if (typeof dashboard !== 'undefined' && dashboard.loadPrinters) {
                    dashboard.loadPrinters();
                }
                
                // Reset form
                this.resetForm();
            } else {
                throw new Error(response.error || 'Unbekannter Fehler');
            }

        } catch (error) {
            console.error('Failed to add printer:', error);
            const message = error instanceof ApiError ? error.getUserMessage() : error.message;
            showToast('error', 'Fehler beim Hinzufügen', message);
        } finally {
            this.isSubmitting = false;
            this.setSubmitButtonState(false);
        }
    }

    /**
     * Collect form data
     */
    collectFormData() {
        const printerType = document.getElementById('printerType').value;
        const name = document.getElementById('printerName').value;
        const ipAddress = document.getElementById('printerIP').value;
        const isActive = document.getElementById('printerActive').checked;
        
        // Build connection config based on printer type
        const connectionConfig = {
            ip_address: ipAddress
        };

        // Add printer-specific fields to connection config
        if (printerType === 'bambu_lab') {
            connectionConfig.access_code = document.getElementById('accessCode').value;
            connectionConfig.serial_number = document.getElementById('serialNumber').value;
        } else if (printerType === 'prusa_core') {
            connectionConfig.api_key = document.getElementById('apiKey').value;
        }

        // Format data according to backend API expectations
        const data = {
            name: name,
            printer_type: printerType,
            connection_config: connectionConfig
        };

        // Add optional fields if needed
        if (!isActive) {
            data.is_enabled = false;
        }

        return data;
    }

    /**
     * Validate printer connectivity
     */
    async validatePrinterConnectivity(printerData) {
        try {
            // This would make a test connection to the printer
            // For now, just return success
            return { success: true };
        } catch (error) {
            return { 
                success: false, 
                error: error.message || 'Verbindung fehlgeschlagen' 
            };
        }
    }

    /**
     * Set submit button loading state
     */
    setSubmitButtonState(loading) {
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (submitButton) {
            if (loading) {
                submitButton.disabled = true;
                submitButton.innerHTML = `
                    <div class="spinner" style="width: 16px; height: 16px; margin-right: 8px;"></div>
                    Wird hinzugefügt...
                `;
            } else {
                submitButton.disabled = false;
                submitButton.innerHTML = `
                    <span class="btn-icon">➕</span>
                    Hinzufügen
                `;
            }
        }
    }

    /**
     * Reset form to initial state
     */
    resetForm() {
        if (!this.form) return;

        this.form.reset();
        
        // Clear all validation states
        const fields = this.form.querySelectorAll('input, select');
        fields.forEach(field => {
            this.clearFieldError(field);
        });

        // Hide specific fields
        const bambuFields = document.getElementById('bambuFields');
        const prusaFields = document.getElementById('prusaFields');
        
        if (bambuFields) {
            bambuFields.style.display = 'none';
            this.setFieldsRequired(bambuFields, false);
        }
        if (prusaFields) {
            prusaFields.style.display = 'none';
            this.setFieldsRequired(prusaFields, false);
        }
    }
}

// Initialize printer form handler
const printerFormHandler = new PrinterFormHandler();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PrinterFormHandler };
}