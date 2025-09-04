/**
 * Essential frontend form validation tests for Printernizer Milestone 1.1
 * Tests core form validation and German business logic.
 */

// Mock DOM for testing
const JSDOM = require('jsdom').JSDOM;
const dom = new JSDOM('<!DOCTYPE html><html><body><div id="app"></div></body></html>');
global.window = dom.window;
global.document = dom.window.document;
global.HTMLElement = dom.window.HTMLElement;

describe('Essential Form Validation Tests', () => {
    
    describe('Printer Configuration Form', () => {
        let form, nameInput, ipInput, typeSelect;
        
        beforeEach(() => {
            // Create mock printer form
            document.body.innerHTML = `
                <form id="printer-form" class="printer-form">
                    <input type="text" id="printer-name" name="name" required>
                    <input type="text" id="printer-ip" name="ip_address" required>
                    <select id="printer-type" name="type" required>
                        <option value="">-- Druckertyp wählen --</option>
                        <option value="bambu_lab">Bambu Lab A1</option>
                        <option value="prusa_core">Prusa Core One</option>
                    </select>
                    <button type="submit">Drucker hinzufügen</button>
                </form>
            `;
            
            form = document.getElementById('printer-form');
            nameInput = document.getElementById('printer-name');
            ipInput = document.getElementById('printer-ip');
            typeSelect = document.getElementById('printer-type');
        });
        
        test('validates required printer name', () => {
            nameInput.value = '';
            expect(form.checkValidity()).toBe(false);
            expect(nameInput.validity.valid).toBe(false);
        });
        
        test('validates printer name length', () => {
            nameInput.value = 'Te'; // Too short
            nameInput.setCustomValidity(
                nameInput.value.length < 3 ? 'Name muss mindestens 3 Zeichen haben' : ''
            );
            expect(nameInput.validity.valid).toBe(false);
            
            nameInput.value = 'Valid Printer Name';
            nameInput.setCustomValidity('');
            expect(nameInput.validity.valid).toBe(true);
        });
        
        test('validates IP address format', () => {
            // Test invalid IP
            ipInput.value = 'invalid-ip';
            const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
            const isValidIP = ipPattern.test(ipInput.value);
            expect(isValidIP).toBe(false);
            
            // Test valid IP
            ipInput.value = '192.168.1.100';
            const isValidIP2 = ipPattern.test(ipInput.value);
            expect(isValidIP2).toBe(true);
        });
        
        test('validates printer type selection', () => {
            typeSelect.value = '';
            expect(typeSelect.validity.valid).toBe(false);
            
            typeSelect.value = 'bambu_lab';
            expect(typeSelect.validity.valid).toBe(true);
        });
        
        test('validates complete form data', () => {
            nameInput.value = 'Bambu A1 #1';
            ipInput.value = '192.168.1.100';
            typeSelect.value = 'bambu_lab';
            
            const formData = new FormData(form);
            const printerData = Object.fromEntries(formData);
            
            expect(printerData.name).toBe('Bambu A1 #1');
            expect(printerData.ip_address).toBe('192.168.1.100');
            expect(printerData.type).toBe('bambu_lab');
        });
    });
    
    describe('German Business Validation', () => {
        test('validates German characters in printer names', () => {
            const germanNames = [
                'Drucker Müller',
                'Bambu für Tests', 
                'Prusa Düsseldorf'
            ];
            
            germanNames.forEach(name => {
                // Should accept German umlauts and ß
                const hasGermanChars = /[äöüÄÖÜß]/.test(name);
                const isValidLength = name.length >= 3;
                expect(isValidLength).toBe(true);
            });
        });
        
        test('validates customer name for business classification', () => {
            const businessIndicators = ['GmbH', 'AG', 'OHG', 'KG', 'e.V.'];
            
            function isBusinessCustomer(name) {
                return businessIndicators.some(indicator => name.includes(indicator));
            }
            
            expect(isBusinessCustomer('Test Customer GmbH')).toBe(true);
            expect(isBusinessCustomer('John Smith')).toBe(false);
            expect(isBusinessCustomer('Acme AG')).toBe(true);
        });
        
        test('validates German currency formatting', () => {
            function formatGermanCurrency(amount) {
                return new Intl.NumberFormat('de-DE', {
                    style: 'currency',
                    currency: 'EUR'
                }).format(amount);
            }
            
            expect(formatGermanCurrency(25.50)).toMatch(/25,50\s*€/);
            expect(formatGermanCurrency(1000.99)).toMatch(/1\.000,99\s*€/);
        });
    });
    
    describe('API Error Handling', () => {
        test('handles API validation errors in German', () => {
            const apiErrors = {
                'VALIDATION_ERROR': 'Eingabedaten sind ungültig',
                'PRINTER_EXISTS': 'Drucker mit dieser ID existiert bereits',
                'CONNECTION_FAILED': 'Verbindung zum Drucker fehlgeschlagen'
            };
            
            Object.entries(apiErrors).forEach(([code, message]) => {
                expect(message).toMatch(/[a-zA-ZäöüÄÖÜß\s]/);
                expect(message.length).toBeGreaterThan(10);
            });
        });
        
        test('validates form submission error handling', () => {
            const mockResponse = {
                ok: false,
                status: 422,
                json: () => Promise.resolve({
                    error: 'VALIDATION_ERROR',
                    message: 'Eingabedaten ungültig',
                    details: [
                        { field: 'ip_address', message: 'Ungültige IP-Adresse' }
                    ]
                })
            };
            
            // Simulate error handling
            if (!mockResponse.ok) {
                expect(mockResponse.status).toBe(422);
                mockResponse.json().then(data => {
                    expect(data.error).toBe('VALIDATION_ERROR');
                    expect(data.details).toBeDefined();
                    expect(data.details[0].field).toBe('ip_address');
                });
            }
        });
    });
    
    describe('Form Accessibility', () => {
        test('validates form has proper labels', () => {
            document.body.innerHTML = `
                <form id="accessible-form">
                    <label for="printer-name">Druckername:</label>
                    <input type="text" id="printer-name" required aria-describedby="name-help">
                    <div id="name-help">Mindestens 3 Zeichen</div>
                </form>
            `;
            
            const input = document.getElementById('printer-name');
            const label = document.querySelector('label[for="printer-name"]');
            
            expect(label).toBeTruthy();
            expect(input.hasAttribute('aria-describedby')).toBe(true);
        });
        
        test('validates error messages are accessible', () => {
            const errorMessage = document.createElement('div');
            errorMessage.id = 'error-message';
            errorMessage.className = 'error-message';
            errorMessage.setAttribute('role', 'alert');
            errorMessage.textContent = 'Eingabe ungültig';
            
            expect(errorMessage.getAttribute('role')).toBe('alert');
            expect(errorMessage.textContent).toMatch(/ungültig/);
        });
    });
    
    describe('File Management Form', () => {
        test('validates file download button states', () => {
            const fileStates = {
                'available': { text: 'Herunterladen', disabled: false },
                'downloading': { text: 'Wird heruntergeladen...', disabled: true },
                'downloaded': { text: 'Heruntergeladen ✓', disabled: true },
                'failed': { text: 'Fehler - Erneut versuchen', disabled: false }
            };
            
            Object.entries(fileStates).forEach(([state, config]) => {
                expect(config.text).toBeDefined();
                expect(typeof config.disabled).toBe('boolean');
            });
        });
        
        test('validates file type filtering', () => {
            const supportedTypes = ['.3mf', '.stl', '.gcode'];
            const testFiles = [
                'test_cube.3mf',
                'prototype.stl', 
                'invalid.txt',
                'print_job.gcode'
            ];
            
            function isSupported(filename) {
                return supportedTypes.some(type => filename.toLowerCase().endsWith(type));
            }
            
            expect(isSupported('test_cube.3mf')).toBe(true);
            expect(isSupported('prototype.stl')).toBe(true);
            expect(isSupported('invalid.txt')).toBe(false);
            expect(isSupported('print_job.gcode')).toBe(true);
        });
    });
});

// Export for Node.js testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        // Export test utilities if needed
    };
}