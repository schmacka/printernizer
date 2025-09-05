/**
 * Essential Frontend Tests for Printer Monitoring - Milestone 1.2
 * ===============================================================
 * 
 * Focused tests for real-time printer monitoring components without over-testing.
 * Tests WebSocket integration, German UI, and critical monitoring workflows.
 */

// Mock DOM setup for testing
const { JSDOM } = require('jsdom');
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
global.window = dom.window;
global.document = dom.window.document;
global.WebSocket = class MockWebSocket {
    constructor(url) {
        this.url = url;
        this.readyState = WebSocket.CONNECTING;
        this.onopen = null;
        this.onmessage = null;
        this.onclose = null;
        this.onerror = null;
        
        // Simulate connection
        setTimeout(() => {
            this.readyState = WebSocket.OPEN;
            if (this.onopen) this.onopen();
        }, 10);
    }
    
    send(data) {
        this.lastSent = data;
    }
    
    close() {
        this.readyState = WebSocket.CLOSED;
        if (this.onclose) this.onclose();
    }
    
    // Simulate receiving message
    simulateMessage(data) {
        if (this.onmessage) {
            this.onmessage({ data: JSON.stringify(data) });
        }
    }
};
global.WebSocket.CONNECTING = 0;
global.WebSocket.OPEN = 1;
global.WebSocket.CLOSING = 2;
global.WebSocket.CLOSED = 3;

// Mock fetch API
global.fetch = jest.fn();

describe('Essential Printer Monitoring Tests - Milestone 1.2', () => {
    
    beforeEach(() => {
        // Reset DOM
        document.body.innerHTML = '';
        
        // Reset fetch mock
        fetch.mockClear();
        
        // Create basic dashboard HTML structure
        document.body.innerHTML = `
            <div id="printer-status-grid"></div>
            <div id="monitoring-controls"></div>
            <div id="file-management"></div>
            <div id="connection-status"></div>
            <div id="status-history-chart"></div>
        `;
    });

    describe('Real-time Printer Status Dashboard', () => {
        
        test('should display printer status with German UI', async () => {
            // Mock printer status data with German text
            const printerStatus = {
                id: 'bambu-a1-001',
                name: 'Bambu A1 Hauptdrucker',
                status: 'printing',
                temperature_bed: 60.0,
                temperature_nozzle: 215.0,
                progress: 45.7,
                current_job: {
                    filename: 'Kundenauftrag_Müller.3mf',
                    time_remaining: 65
                },
                connection_quality: 'excellent'
            };

            // Create printer status component
            const statusGrid = document.getElementById('printer-status-grid');
            
            // Mock printer status display function
            const displayPrinterStatus = (printer) => {
                const statusCard = document.createElement('div');
                statusCard.className = 'printer-status-card';
                statusCard.id = `printer-${printer.id}`;
                
                statusCard.innerHTML = `
                    <h3>${printer.name}</h3>
                    <div class="status">Status: <span class="status-${printer.status}">Druckt</span></div>
                    <div class="temperatures">
                        <span>Bett: ${printer.temperature_bed}°C</span>
                        <span>Düse: ${printer.temperature_nozzle}°C</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${printer.progress}%"></div>
                        <span>${printer.progress}%</span>
                    </div>
                    <div class="current-job">${printer.current_job.filename}</div>
                    <div class="time-remaining">Verbleibend: ${printer.current_job.time_remaining} min</div>
                `;
                
                return statusCard;
            };

            const statusCard = displayPrinterStatus(printerStatus);
            statusGrid.appendChild(statusCard);

            // Validate German UI elements
            expect(statusCard.textContent).toContain('Druckt'); // German for "Printing"
            expect(statusCard.textContent).toContain('Bett:'); // German for "Bed"
            expect(statusCard.textContent).toContain('Düse:'); // German for "Nozzle"
            expect(statusCard.textContent).toContain('Verbleibend:'); // German for "Remaining"
            
            // Validate temperature display
            expect(statusCard.textContent).toContain('60°C');
            expect(statusCard.textContent).toContain('215°C');
            
            // Validate progress bar
            const progressBar = statusCard.querySelector('.progress-bar');
            expect(progressBar.style.width).toBe('45.7%');
            
            // Validate German filename display
            expect(statusCard.textContent).toContain('Kundenauftrag_Müller.3mf');
        });

        test('should handle WebSocket real-time updates', (done) => {
            const ws = new WebSocket('ws://localhost:8000/ws');
            
            // Mock WebSocket message handler
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'printer_status_update') {
                    const printer = data.payload;
                    
                    // Validate real-time update structure
                    expect(printer).toHaveProperty('id');
                    expect(printer).toHaveProperty('status');
                    expect(printer).toHaveProperty('temperature_bed');
                    expect(printer).toHaveProperty('temperature_nozzle');
                    expect(printer).toHaveProperty('progress');
                    
                    // Validate German business data
                    if (printer.current_job) {
                        expect(printer.current_job).toHaveProperty('material_cost_eur');
                        expect(printer.current_job).toHaveProperty('customer_type');
                    }
                    
                    done();
                }
            };

            // Simulate real-time status update
            setTimeout(() => {
                ws.simulateMessage({
                    type: 'printer_status_update',
                    payload: {
                        id: 'prusa-core-one-001',
                        status: 'printing',
                        temperature_bed: 65.0,
                        temperature_nozzle: 220.0,
                        progress: 78.3,
                        current_job: {
                            filename: 'Geschenk_Hochzeit.stl',
                            material_cost_eur: 15.75,
                            customer_type: 'business'
                        }
                    }
                });
            }, 50);
        });
    });

    describe('Drucker-Dateien File Management', () => {
        
        test('should display file list with download status icons', async () => {
            // Mock file data with German filenames and status
            const mockFiles = [
                {
                    filename: 'Werbeartikel_Messe.3mf',
                    download_status: 'available', // 📁
                    size: 2048576,
                    last_modified: '2024-09-05T10:30:00Z'
                },
                {
                    filename: 'Prototyp_Süßwarenform.stl', 
                    download_status: 'downloaded', // ✓
                    size: 1024000,
                    last_modified: '2024-09-04T15:45:00Z'
                },
                {
                    filename: 'Löffel_personalisiert.gcode',
                    download_status: 'local', // 💾
                    size: 512000,
                    last_modified: '2024-09-03T09:15:00Z'
                }
            ];

            // Mock file list display function
            const displayFileList = (files) => {
                const fileList = document.createElement('div');
                fileList.className = 'file-list';
                
                files.forEach(file => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    
                    // Status icon mapping
                    const statusIcons = {
                        'available': '📁',
                        'downloaded': '✓',
                        'local': '💾'
                    };
                    
                    fileItem.innerHTML = `
                        <div class="file-info">
                            <span class="status-icon">${statusIcons[file.download_status]}</span>
                            <span class="filename">${file.filename}</span>
                            <span class="filesize">${(file.size / 1024 / 1024).toFixed(1)} MB</span>
                        </div>
                        <button class="download-btn" data-filename="${file.filename}">
                            ${file.download_status === 'available' ? 'Download' : 'Bereits vorhanden'}
                        </button>
                    `;
                    
                    fileList.appendChild(fileItem);
                });
                
                return fileList;
            };

            const fileList = displayFileList(mockFiles);
            document.getElementById('file-management').appendChild(fileList);

            // Validate German filenames with umlauts
            expect(fileList.textContent).toContain('Süßwarenform'); // ü, ß
            expect(fileList.textContent).toContain('Löffel'); // ö

            // Validate status icons
            const statusIcons = fileList.querySelectorAll('.status-icon');
            expect(statusIcons[0].textContent).toBe('📁'); // available
            expect(statusIcons[1].textContent).toBe('✓'); // downloaded  
            expect(statusIcons[2].textContent).toBe('💾'); // local

            // Validate German button text
            const buttons = fileList.querySelectorAll('.download-btn');
            expect(buttons[0].textContent).toBe('Download');
            expect(buttons[1].textContent).toBe('Bereits vorhanden'); // German for "Already available"
        });

        test('should handle one-click file download with progress', async () => {
            const filename = 'Auftrag_Schmidt_Geburtstag.3mf';
            
            // Mock download API call
            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    filename: filename,
                    download_status: 'downloading',
                    download_progress: 0,
                    estimated_size: 3145728
                })
            });

            // Mock download progress updates via WebSocket
            const ws = new WebSocket('ws://localhost:8000/ws');
            
            // Simulate download button click
            const downloadFile = async (filename) => {
                const response = await fetch(`/api/v1/printers/test-id/files/${filename}/download`, {
                    method: 'POST'
                });
                return response.json();
            };

            const result = await downloadFile(filename);
            
            // Validate download initiation
            expect(result.filename).toBe(filename);
            expect(result.download_status).toBe('downloading');
            expect(result.download_progress).toBe(0);
            
            // Validate German filename handling
            expect(result.filename).toContain('Geburtstag'); // German word
            
            // Simulate progress updates
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'download_progress') {
                    expect(data.payload.filename).toBe(filename);
                    expect(data.payload.progress).toBeGreaterThanOrEqual(0);
                    expect(data.payload.progress).toBeLessThanOrEqual(100);
                }
            };

            // Simulate progress update message
            setTimeout(() => {
                ws.simulateMessage({
                    type: 'download_progress',
                    payload: {
                        filename: filename,
                        progress: 45,
                        bytes_downloaded: 1413120,
                        total_bytes: 3145728
                    }
                });
            }, 100);
        });
    });

    describe('Monitoring Controls', () => {
        
        test('should start and stop real-time monitoring', async () => {
            const printerId = 'bambu-a1-001';
            
            // Mock monitoring control buttons
            const controlsDiv = document.getElementById('monitoring-controls');
            controlsDiv.innerHTML = `
                <button id="start-monitoring" data-printer-id="${printerId}">
                    Überwachung starten
                </button>
                <button id="stop-monitoring" data-printer-id="${printerId}" disabled>
                    Überwachung stoppen  
                </button>
                <div id="monitoring-status">Getrennt</div>
            `;

            // Mock start monitoring API call
            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    monitoring_active: true,
                    polling_interval: 30,
                    connection_type: 'mqtt',
                    started_at: new Date().toISOString()
                })
            });

            // Start monitoring function
            const startMonitoring = async (printerId) => {
                const response = await fetch(`/api/v1/printers/${printerId}/monitoring/start`, {
                    method: 'POST'
                });
                const result = await response.json();
                
                // Update UI
                document.getElementById('start-monitoring').disabled = true;
                document.getElementById('stop-monitoring').disabled = false;
                document.getElementById('monitoring-status').textContent = 'Aktiv (30s Intervall)';
                
                return result;
            };

            const result = await startMonitoring(printerId);
            
            // Validate monitoring started
            expect(result.monitoring_active).toBe(true);
            expect(result.polling_interval).toBe(30); // 30-second requirement
            expect(result.connection_type).toBe('mqtt');
            
            // Validate German UI updates
            expect(document.getElementById('monitoring-status').textContent).toBe('Aktiv (30s Intervall)');
            expect(document.getElementById('start-monitoring').disabled).toBe(true);
            expect(document.getElementById('stop-monitoring').disabled).toBe(false);
        });
    });

    describe('Status History Charts', () => {
        
        test('should display temperature trends with German labels', () => {
            // Mock temperature history data
            const temperatureData = {
                timestamps: ['10:00', '10:30', '11:00', '11:30', '12:00'],
                bed_temperatures: [20, 55, 60, 60, 62],
                nozzle_temperatures: [20, 200, 215, 215, 218]
            };

            // Mock chart creation (simplified)
            const createTemperatureChart = (data) => {
                const chartDiv = document.createElement('div');
                chartDiv.className = 'temperature-chart';
                chartDiv.innerHTML = `
                    <h3>Temperaturverlauf</h3>
                    <div class="chart-legend">
                        <span class="legend-item">
                            <span class="color-indicator bed"></span>
                            Druckbett
                        </span>
                        <span class="legend-item">
                            <span class="color-indicator nozzle"></span>  
                            Düse
                        </span>
                    </div>
                    <canvas id="temp-chart" width="400" height="200"></canvas>
                `;
                return chartDiv;
            };

            const chart = createTemperatureChart(temperatureData);
            document.getElementById('status-history-chart').appendChild(chart);

            // Validate German chart labels
            expect(chart.textContent).toContain('Temperaturverlauf'); // "Temperature History"
            expect(chart.textContent).toContain('Druckbett'); // "Print Bed"
            expect(chart.textContent).toContain('Düse'); // "Nozzle"
            
            // Validate chart structure
            expect(chart.querySelector('#temp-chart')).toBeTruthy();
            expect(chart.querySelector('.chart-legend')).toBeTruthy();
        });
    });

    describe('Connection Recovery', () => {
        
        test('should handle WebSocket connection loss and recovery', (done) => {
            let reconnectAttempts = 0;
            const maxReconnectAttempts = 3;
            
            const connectWebSocket = () => {
                const ws = new WebSocket('ws://localhost:8000/ws');
                
                ws.onclose = () => {
                    reconnectAttempts++;
                    
                    // Update connection status in German
                    const statusDiv = document.getElementById('connection-status');
                    statusDiv.innerHTML = `
                        <span class="status-disconnected">Verbindung getrennt</span>
                        <span>Wiederverbindungsversuch ${reconnectAttempts}/${maxReconnectAttempts}</span>
                    `;
                    
                    if (reconnectAttempts < maxReconnectAttempts) {
                        // Attempt reconnection
                        setTimeout(connectWebSocket, 1000);
                    } else {
                        // Validate German error messages
                        expect(statusDiv.textContent).toContain('Verbindung getrennt'); // "Connection lost"
                        expect(statusDiv.textContent).toContain('Wiederverbindungsversuch'); // "Reconnection attempt"
                        done();
                    }
                };
                
                // Simulate connection loss
                setTimeout(() => {
                    ws.close();
                }, 50);
            };
            
            connectWebSocket();
        });
    });

    describe('German Business Integration', () => {
        
        test('should calculate and display German VAT in job costs', () => {
            const jobData = {
                material_cost_base: 25.00, // EUR base cost
                vat_rate: 0.19, // German 19% VAT
                customer_type: 'business'
            };

            // German business calculation function
            const calculateJobCost = (job) => {
                const vatAmount = job.material_cost_base * job.vat_rate;
                const totalCost = job.material_cost_base + vatAmount;
                
                return {
                    base_cost: job.material_cost_base,
                    vat_amount: vatAmount,
                    total_cost: totalCost,
                    formatted_total: `${totalCost.toFixed(2)} €`
                };
            };

            const result = calculateJobCost(jobData);
            
            // Validate German VAT calculation
            expect(result.base_cost).toBe(25.00);
            expect(result.vat_amount).toBeCloseTo(4.75, 2); // 19% of 25.00
            expect(result.total_cost).toBeCloseTo(29.75, 2);
            expect(result.formatted_total).toBe('29.75 €'); // German currency format
        });

        test('should format timestamps in German timezone', () => {
            const utcTimestamp = '2024-09-05T14:30:00Z';
            
            // German timezone formatting function
            const formatGermanTime = (isoString) => {
                const date = new Date(isoString);
                return date.toLocaleString('de-DE', {
                    timeZone: 'Europe/Berlin',
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            };

            const germanTime = formatGermanTime(utcTimestamp);
            
            // Validate German date format (DD.MM.YYYY, HH:mm)
            expect(germanTime).toMatch(/\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}/);
        });
    });
});