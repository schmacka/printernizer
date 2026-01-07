/**
 * Milestone 1.2: Enhanced Functions for Real-time Printer Integration
 * Global functions for UI components and real-time features
 */

// Global component instances
let druckerDateienManager = null;
let printerStatusCharts = new Map();
let activePrinterCards = new Map();

/**
 * Toggle printer monitoring on/off
 */
async function togglePrinterMonitoring(printerId) {
    const printerCard = activePrinterCards.get(printerId);
    if (!printerCard) {
        Logger.error(`Printer card not found for ID: ${printerId}`);
        return;
    }

    try {
        if (printerCard.isMonitoring) {
            await printerCard.stopRealtimeMonitoring();
            showToast('Überwachung gestoppt', 'success');
        } else {
            await printerCard.startRealtimeMonitoring();
            showToast('Überwachung gestartet', 'success');
        }
    } catch (error) {
        Logger.error('Failed to toggle monitoring:', error);
        showToast(`Fehler: ${error.message}`, 'error');
    }
}

/**
 * Show printer files (Drucker-Dateien) modal
 */
async function showPrinterFiles(printerId) {
    try {
        // Create modal for printer files
        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h3>📁 Drucker-Dateien</h3>
                    <button class="modal-close" onclick="closeDynamicModal(this)">×</button>
                </div>
                <div class="modal-body" style="padding: 0; max-height: 80vh;">
                    <div id="printer-files-manager"></div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Initialize DruckerDateienManager for specific printer
        const fileManager = new DruckerDateienManager('printer-files-manager', printerId);
        await fileManager.init();

        // Store reference for cleanup and global access
        modal.fileManager = fileManager;
        druckerDateienManager = fileManager;

    } catch (error) {
        Logger.error('Failed to show printer files:', error);
        showToast('Fehler beim Laden der Dateien', 'error');
    }
}

/**
 * Show global Drucker-Dateien manager
 */
async function showDruckerDateienManager() {
    try {
        // Create full-screen modal for all files
        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 95vw; max-height: 95vh;">
                <div class="modal-header">
                    <h3>📁 Drucker-Dateien - Alle Drucker</h3>
                    <button class="modal-close" onclick="closeDynamicModal(this)">×</button>
                </div>
                <div class="modal-body" style="padding: 0; max-height: 85vh;">
                    <div id="global-files-manager"></div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Initialize global DruckerDateienManager
        const fileManager = new DruckerDateienManager('global-files-manager', null);
        await fileManager.init();

        // Store reference for cleanup and global access
        modal.fileManager = fileManager;
        druckerDateienManager = fileManager;

    } catch (error) {
        Logger.error('Failed to show file manager:', error);
        showToast('Fehler beim Laden des Datei-Managers', 'error');
    }
}

/**
 * Close modal and cleanup components
 */
function closeDynamicModal(closeButton) {
    const modal = closeButton.closest('.modal');
    if (!modal) return;

    // Cleanup any component instances
    if (modal.fileManager) {
        modal.fileManager.destroy();
        // Reset global reference if this was the active manager
        if (druckerDateienManager === modal.fileManager) {
            druckerDateienManager = null;
        }
    }
    if (modal.statusChart) {
        modal.statusChart.destroy();
    }

    modal.remove();
}

/**
 * Show printer status history chart
 */
async function showPrinterStatusHistory(printerId) {
    try {
        const printer = await api.getPrinter(printerId);
        
        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h3>📊 Statusverlauf - ${escapeHtml(printer.name)}</h3>
                    <button class="modal-close" onclick="closeDynamicModal(this)">×</button>
                </div>
                <div class="modal-body" style="padding: 0;">
                    <div id="printer-status-chart-${printerId}"></div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Initialize status chart
        const chart = new StatusHistoryChart(`printer-status-chart-${printerId}`, printerId);
        await chart.init();

        // Store reference for cleanup
        modal.statusChart = chart;

    } catch (error) {
        Logger.error('Failed to show status history:', error);
        showToast('Fehler beim Laden der Verlaufsdaten', 'error');
    }
}

/**
 * Register printer card instance for monitoring
 */
function registerPrinterCard(printerId, printerCard) {
    activePrinterCards.set(printerId, printerCard);
}

/**
 * Unregister printer card instance
 */
function unregisterPrinterCard(printerId) {
    const printerCard = activePrinterCards.get(printerId);
    if (printerCard) {
        printerCard.destroy();
        activePrinterCards.delete(printerId);
    }
}

/**
 * Download file from printer with progress tracking
 */
async function downloadFile(fileId) {
    if (druckerDateienManager) {
        await druckerDateienManager.downloadFile(fileId);
    } else {
        Logger.error('DruckerDateienManager not initialized');
        showToast('Datei-Manager nicht verfügbar', 'error');
    }
}

/**
 * Download all available files
 */
async function downloadAllAvailable() {
    if (!druckerDateienManager) {
        Logger.error('DruckerDateienManager not initialized');
        return;
    }

    const availableFiles = druckerDateienManager.files.filter(f => f.status === 'available');

    if (availableFiles.length === 0) {
        showToast('Keine Dateien zum Herunterladen verfügbar', 'info');
        return;
    }

    const confirmed = confirm(`${availableFiles.length} Dateien herunterladen?`);
    if (!confirmed) return;

    let successCount = 0;
    let errorCount = 0;

    for (const file of availableFiles) {
        try {
            await druckerDateienManager.downloadFile(file.id);
            successCount++;
        } catch (error) {
            Logger.error(`Failed to download ${file.filename}:`, error);
            errorCount++;
        }
    }

    const message = `${successCount} Dateien erfolgreich heruntergeladen` +
                   (errorCount > 0 ? `, ${errorCount} Fehler` : '');
    showToast(message, errorCount > 0 ? 'warning' : 'success');
}

/**
 * Download selected files based on checked checkboxes
 */
async function downloadSelected() {
    // Find the active modal and its file manager
    const activeModal = document.querySelector('.modal.show');
    if (!activeModal || !activeModal.fileManager) {
        Logger.error('DruckerDateienManager not initialized');
        showToast('Datei-Manager nicht verfügbar', 'error');
        return;
    }

    const fileManager = activeModal.fileManager;

    // Get all checked file checkboxes
    const checkboxes = activeModal.querySelectorAll('.file-checkbox:checked');
    const selectedFileIds = Array.from(checkboxes).map(cb => cb.value);

    console.log('Selected file IDs:', selectedFileIds);
    console.log('Total files in fileManager:', fileManager.files.length);
    console.log('All file IDs:', fileManager.files.map(f => f.id));
    console.log('=== DOWNLOAD DEBUG ===');
    console.log('All files:', fileManager.files.map(f => ({
        id: f.id,
        filename: f.filename,
        printer_id: f.printer_id,
        status: f.status,
        has_printer_id: !!f.printer_id
    })));
    console.log('Selected IDs:', selectedFileIds);

    if (selectedFileIds.length === 0) {
        showToast('Keine Dateien ausgewählt', 'info');
        return;
    }

    // Filter to only include selected files that are available for download (not already downloaded)
    const selectedFiles = fileManager.files.filter(f => {
        const isSelected = selectedFileIds.includes(f.id);
        // Allow download unless explicitly downloaded or currently downloading
        // Accept null, undefined, 'available', or any other status
        const canDownload = f.status !== 'downloaded' && f.status !== 'downloading';
        console.log(`Filter: "${f.filename}" | id:'${f.id}' selected:${isSelected} status:'${f.status}' canDownload:${canDownload} | printer_id:'${f.printer_id}'`);
        return isSelected && canDownload;
    });

    console.log('Files to download:', selectedFiles.length, selectedFiles.map(f => f.filename));

    if (selectedFiles.length === 0) {
        // Provide detailed reason
        const allStatuses = fileManager.files
            .filter(f => selectedFileIds.includes(f.id))
            .map(f => f.status)
            .filter((v, i, a) => a.indexOf(v) === i);  // unique

        console.error('No files can be downloaded. Statuses:', allStatuses);

        let message = 'Keine der ausgewählten Dateien kann heruntergeladen werden';
        if (allStatuses.some(s => s === 'downloaded')) {
            message += ' (bereits heruntergeladen)';
        } else if (allStatuses.some(s => s === 'downloading')) {
            message += ' (Download läuft bereits)';
        }

        showToast(message, 'warning');
        return;
    }

    // Show confirmation dialog
    const confirmed = confirm(
        `${selectedFiles.length} ausgewählte Dateien herunterladen?\n\n` +
        selectedFiles.map(f => f.filename).join('\n')
    );
    if (!confirmed) return;

    let successCount = 0;
    let errorCount = 0;
    const errors = [];

    // Download each selected file
    for (const file of selectedFiles) {
        try {
            await fileManager.downloadFile(file.id);
            successCount++;

            // Uncheck the checkbox after successful download
            const checkbox = activeModal.querySelector(`.file-checkbox[value="${file.id}"]`);
            if (checkbox) {
                checkbox.checked = false;
            }
        } catch (error) {
            Logger.error(`Failed to download ${file.filename}:`, error);
            console.error('DOWNLOAD ERROR DETAILS:', {
                file_id: file.id,
                filename: file.filename,
                printer_id: file.printer_id,
                error_message: error.message,
                error_stack: error.stack,
                error_object: error
            });
            errorCount++;
            errors.push(`${file.filename}: ${error.message || 'Unbekannter Fehler'}`);
        }
    }

    // Update selected count display
    fileManager.updateSelectedCount();
    fileManager.updateBulkActions();

    // Show summary message
    let message = `${successCount} Dateien erfolgreich heruntergeladen`;
    if (errorCount > 0) {
        message += `, ${errorCount} Fehler`;
        Logger.error('Download errors:', errors);
    }

    showToast(message, errorCount > 0 ? 'warning' : 'success');
}

/**
 * Refresh files in DruckerDateienManager
 */
async function refreshFiles() {
    if (druckerDateienManager) {
        await druckerDateienManager.loadFiles();
        showToast('Dateien aktualisiert', 'success');
    }
}

/**
 * Select all files in the current view
 */
function selectAllFiles() {
    // Find the active modal and its file manager
    const activeModal = document.querySelector('.modal.show');
    if (!activeModal || !activeModal.fileManager) {
        Logger.warn('No active file manager found');
        return;
    }

    const fileManager = activeModal.fileManager;
    const checkboxes = activeModal.querySelectorAll('.file-checkbox:not(:disabled)');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });

    fileManager.updateSelectedCount();
    fileManager.updateBulkActions();
}

/**
 * Clear all file selections
 */
function selectNone() {
    // Find the active modal and its file manager
    const activeModal = document.querySelector('.modal.show');
    if (!activeModal || !activeModal.fileManager) {
        Logger.warn('No active file manager found');
        return;
    }

    const fileManager = activeModal.fileManager;
    const checkboxes = activeModal.querySelectorAll('.file-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });

    fileManager.updateSelectedCount();
    fileManager.updateBulkActions();
}

/**
 * Select only available files
 */
function selectAvailable() {
    // Find the active modal and its file manager
    const activeModal = document.querySelector('.modal.show');
    if (!activeModal || !activeModal.fileManager) {
        Logger.warn('No active file manager found');
        return;
    }

    const fileManager = activeModal.fileManager;
    const checkboxes = activeModal.querySelectorAll('.file-checkbox');
    checkboxes.forEach(checkbox => {
        const fileCard = checkbox.closest('.file-card');
        const isAvailable = fileCard && fileCard.classList.contains('available');
        checkbox.checked = isAvailable && !checkbox.disabled;
    });

    fileManager.updateSelectedCount();
    fileManager.updateBulkActions();
}

/**
 * Preview file in fullscreen 3D preview modal
 * Shows animated GIF for STL/3MF, static preview for GCODE/BGCODE
 * @param {string|Object} fileData - File ID, checksum, or file object
 */
function previewFile(fileData) {
    // Use the 3D preview manager if available
    if (window.preview3DManager) {
        window.preview3DManager.open(fileData, 'auto');
    } else {
        // Fallback if preview manager not initialized
        Logger.warn('Preview3D manager not available');
        showToast('Preview not available', 'info');
    }
}

/**
 * Open local file in explorer
 */
function openLocalFile(fileId) {
    // TODO: Implement local file opening
    showToast('Lokale Datei-Funktion wird in einer späteren Version verfügbar sein', 'info');
}

/**
 * Delete local file
 */
async function deleteLocalFile(fileId) {
    const confirmed = confirm('Lokale Datei wirklich löschen?');
    if (!confirmed) return;

    try {
        await api.deleteFile(fileId);
        if (druckerDateienManager) {
            await druckerDateienManager.loadFiles();
        }
        showToast('Datei erfolgreich gelöscht', 'success');
    } catch (error) {
        Logger.error('Failed to delete file:', error);
        showToast('Fehler beim Löschen der Datei', 'error');
    }
}

/**
 * Update chart period
 */
function updateChartPeriod(hours) {
    // This would be called by the chart component
    // Implementation would depend on which chart is active
    Logger.debug(`Updating chart period to ${hours} hours`);
}

/**
 * Enhanced toast notification for real-time features
 */
function showRealtimeToast(message, type = 'info', duration = 3000, persistent = false) {
    const toast = createToastElement(message, type);
    
    if (!persistent) {
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
    
    document.querySelector('.toast-container').appendChild(toast);
    
    // Auto-remove after animation
    setTimeout(() => {
        toast.classList.add('fade-out');
    }, duration - 300);
}

/**
 * Create toast element
 */
function createToastElement(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const typeIcons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    toast.innerHTML = `
        <div class="toast-header">
            <span class="toast-title">${typeIcons[type]} ${type.charAt(0).toUpperCase() + type.slice(1)}</span>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="toast-body">${escapeHtml(message)}</div>
    `;
    
    return toast;
}

/**
 * Initialize Milestone 1.2 features on page load
 */
async function initializeMilestone12Features() {
    try {
        // Create toast container if it doesn't exist
        if (!document.querySelector('.toast-container')) {
            const toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        // Initialize WebSocket connections for real-time updates
        if (typeof WebSocketManager !== 'undefined' && window.wsManager) {
            window.wsManager.addMessageHandler('printer_status', handleRealtimePrinterUpdate);
            window.wsManager.addMessageHandler('file_update', handleRealtimeFileUpdate);
            window.wsManager.addMessageHandler('job_update', handleRealtimeJobUpdate);
        }

        Logger.debug('Milestone 1.2 features initialized successfully');
        
    } catch (error) {
        Logger.error('Failed to initialize Milestone 1.2 features:', error);
    }
}

/**
 * Handle real-time printer status updates via WebSocket
 */
function handleRealtimePrinterUpdate(data) {
    const printerCard = activePrinterCards.get(data.printer_id);
    if (printerCard && printerCard.isMonitoring) {
        printerCard.updateRealtimeData(data);
    }
}

/**
 * Handle real-time file updates via WebSocket
 */
function handleRealtimeFileUpdate(data) {
    if (druckerDateienManager) {
        // Update file status in the manager
        const file = druckerDateienManager.files.find(f => f.id === data.file_id);
        if (file) {
            file.status = data.status;
            druckerDateienManager.applyFilters();
        }
    }
}

/**
 * Handle real-time job updates via WebSocket
 */
function handleRealtimeJobUpdate(data) {
    const printerCard = activePrinterCards.get(data.printer_id);
    if (printerCard && data.current_job) {
        printerCard.updateJobProgress(data.current_job);
    }
}

/**
 * Enhanced error handling for Milestone 1.2 features
 */
function handleMilestone12Error(error, context = '') {
    Logger.error(`Milestone 1.2 Error ${context}:`, error);
    
    let userMessage = 'Ein unerwarteter Fehler ist aufgetreten';
    
    if (error instanceof ApiError) {
        userMessage = error.getUserMessage();
    } else if (error.message) {
        userMessage = error.message;
    }
    
    showRealtimeToast(userMessage, 'error', 5000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializeMilestone12Features);

// Export functions for global access
window.togglePrinterMonitoring = togglePrinterMonitoring;
window.showPrinterFiles = showPrinterFiles;
window.showDruckerDateienManager = showDruckerDateienManager;
window.closeDynamicModal = closeDynamicModal;
window.showPrinterStatusHistory = showPrinterStatusHistory;
window.registerPrinterCard = registerPrinterCard;
window.unregisterPrinterCard = unregisterPrinterCard;
window.downloadFile = downloadFile;
window.downloadSelected = downloadSelected;
window.downloadAllAvailable = downloadAllAvailable;
window.refreshFiles = refreshFiles;
window.selectAllFiles = selectAllFiles;
window.selectNone = selectNone;
window.selectAvailable = selectAvailable;
window.previewFile = previewFile;
window.openLocalFile = openLocalFile;
window.deleteLocalFile = deleteLocalFile;
window.updateChartPeriod = updateChartPeriod;
window.showRealtimeToast = showRealtimeToast;
window.handleMilestone12Error = handleMilestone12Error;