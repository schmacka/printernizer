/**
 * Camera functionality for Printernizer
 * Handles camera streams, snapshots, and gallery
 */

class CameraManager {
    constructor() {
        this.cameraStatus = new Map(); // printer_id -> camera status
        this.activeStreams = new Set(); // Active stream URLs
    }

    /**
     * Check camera status for a printer
     */
    async getCameraStatus(printerId) {
        try {
            const response = await fetch(`/api/v1/printers/${printerId}/camera/status`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const status = await response.json();
            this.cameraStatus.set(printerId, status);
            return status;
        } catch (error) {
            Logger.error(`Failed to get camera status for printer ${printerId}:`, error);
            this.cameraStatus.set(printerId, {
                has_camera: false,
                is_available: false,
                error_message: error.message
            });
            return this.cameraStatus.get(printerId);
        }
    }

    /**
     * Take a snapshot from printer camera
     */
    async takeSnapshot(printerId, jobId = null, trigger = 'manual', notes = null) {
        try {
            const response = await fetch(`/api/v1/printers/${printerId}/camera/snapshot`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    printer_id: printerId,
                    job_id: jobId,
                    capture_trigger: trigger,
                    notes: notes
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const snapshot = await response.json();
            Logger.debug('Snapshot captured:', snapshot);
            
            // Show success notification
            showNotification('Snapshot erfolgreich aufgenommen', 'success');
            
            return snapshot;
        } catch (error) {
            Logger.error(`Failed to take snapshot for printer ${printerId}:`, error);
            showNotification(`Snapshot-Fehler: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Get camera stream URL for a printer
     */
    async getStreamUrl(printerId) {
        const status = await this.getCameraStatus(printerId);
        return status.is_available ? status.stream_url : null;
    }

    /**
     * Render camera section for printer card
     */
    renderCameraSection(printer) {
        const cameraStatus = this.cameraStatus.get(printer.id) || { has_camera: false, is_available: false };
        
        if (!cameraStatus.has_camera) {
            return `
                <div class="info-section camera-section">
                    <h4>📷 Kamera</h4>
                    <div class="info-item">
                        <span class="text-muted">Keine Kamera verfügbar</span>
                    </div>
                </div>
            `;
        }

        if (!cameraStatus.is_available) {
            return `
                <div class="info-section camera-section">
                    <h4>📷 Kamera</h4>
                    <div class="info-item">
                        <span class="text-warning">Kamera nicht verfügbar</span>
                        ${cameraStatus.error_message ? `<br><small class="text-muted">${escapeHtml(cameraStatus.error_message)}</small>` : ''}
                    </div>
                </div>
            `;
        }

        return `
            <div class="info-section camera-section">
                <h4>📷 Kamera</h4>
                <div class="camera-controls">
                    <div class="camera-preview-container">
                        <img id="camera-stream-${printer.id}" 
                             class="camera-stream" 
                             src="${cameraStatus.stream_url}" 
                             alt="Live Stream" 
                             onerror="this.style.display='none'; this.parentElement.querySelector('.stream-error').style.display='block';"
                             onload="this.style.display='block'; this.parentElement.querySelector('.stream-error').style.display='none';">
                        <div class="stream-error" style="display: none;">
                            <span class="text-muted">Stream nicht verfügbar</span>
                        </div>
                    </div>
                    <div class="camera-actions">
                        <button class="btn btn-sm btn-primary" 
                                onclick="cameraManager.takeSnapshotFromCard('${printer.id}')"
                                title="Snapshot aufnehmen">
                            📸 Snapshot
                        </button>
                        <button class="btn btn-sm btn-secondary" 
                                onclick="cameraManager.showCameraModal('${printer.id}')"
                                title="Vollbild anzeigen">
                            🔍 Vollbild
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Take snapshot from printer card
     */
    async takeSnapshotFromCard(printerId) {
        const printer = printerManager.printers.get(printerId);
        const currentJobId = printer?.data?.current_job?.id || null;
        
        try {
            await this.takeSnapshot(printerId, currentJobId);
            // Optionally refresh snapshot gallery or show in modal
        } catch (error) {
            // Error already handled in takeSnapshot
        }
    }

    /**
     * Show camera modal with full view
     */
    async showCameraModal(printerId) {
        const printer = printerManager.printers.get(printerId);
        if (!printer) return;

        const status = await this.getCameraStatus(printerId);
        if (!status.is_available) {
            showNotification('Kamera nicht verfügbar', 'warning');
            return;
        }

        const modal = document.createElement('div');
        modal.className = 'modal camera-modal';
        modal.innerHTML = `
            <div class="modal-content camera-modal-content">
                <div class="modal-header">
                    <h3>📷 ${escapeHtml(printer.data.name)} - Kamera</h3>
                    <button class="btn btn-sm btn-secondary" onclick="this.closest('.modal').remove()">
                        ✕
                    </button>
                </div>
                <div class="modal-body">
                    <div class="camera-full-view">
                        <img class="camera-stream-full" 
                             src="${sanitizeUrl(status.stream_url)}" 
                             alt="Live Stream" 
                             onerror="this.style.display='none'; this.parentElement.querySelector('.stream-error').style.display='block';">
                        <div class="stream-error" style="display: none;">
                            <p>Stream nicht verfügbar</p>
                            <button class="btn btn-secondary" onclick="this.previousElementSibling.src='${sanitizeUrl(status.stream_url)}'; this.previousElementSibling.style.display='block'; this.style.display='none';">
                                🔄 Erneut versuchen
                            </button>
                        </div>
                    </div>
                    <div class="camera-modal-controls">
                        <button class="btn btn-primary" 
                                onclick="cameraManager.takeSnapshot('${sanitizeAttribute(printerId)}', null, 'manual')">
                            📸 Snapshot aufnehmen
                        </button>
                        <button class="btn btn-secondary" 
                                onclick="cameraManager.showSnapshotHistory('${sanitizeAttribute(printerId)}')">
                            🖼️ Snapshot-Historie
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        // Auto-refresh stream every 10 seconds
        const refreshInterval = setInterval(() => {
            const img = modal.querySelector('.camera-stream-full');
            if (img && modal.parentElement) {
                const currentSrc = img.src;
                img.src = currentSrc + '?t=' + Date.now();
            } else {
                clearInterval(refreshInterval);
            }
        }, 10000);
    }

    /**
     * Show snapshot history modal
     */
    async showSnapshotHistory(printerId) {
        try {
            const response = await fetch(`/api/v1/printers/${printerId}/snapshots`);
            const snapshots = response.ok ? await response.json() : [];
            
            const modal = document.createElement('div');
            modal.className = 'modal snapshots-modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>🖼️ Snapshot-Historie</h3>
                        <button class="btn btn-sm btn-secondary" onclick="this.closest('.modal').remove()">
                            ✕
                        </button>
                    </div>
                    <div class="modal-body">
                        ${snapshots.length > 0 ? this.renderSnapshotGrid(snapshots) : '<p class="text-muted">Keine Snapshots vorhanden</p>'}
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
        } catch (error) {
            Logger.error('Failed to load snapshot history:', error);
            showNotification('Fehler beim Laden der Snapshot-Historie', 'error');
        }
    }

    /**
     * Render snapshot grid
     */
    renderSnapshotGrid(snapshots) {
        return `
            <div class="snapshot-grid">
                ${snapshots.map(snapshot => `
                    <div class="snapshot-item">
                        <div class="snapshot-preview">
                            <img src="${api.baseURL}/snapshots/${snapshot.id}/download"
                                 alt="Snapshot"
                                 onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDIwMCAxNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIiBmaWxsPSIjZjNmNGY2Ii8+CjxwYXRoIGQ9Im03NSA2MCA2IDAgMCAxIDEyIDAgNiA2IDAgMCAxIDAgMTIgNiA2IDAgMCAxLTEyIDAgNiA2IDAgMCAxIDAtMTJaTTk5IDkwbC0zNi0zNiA5LTkgMjcgMjcgNjMtNjMgOS05LTcyIDcyWiIgZmlsbD0iIzZiNzI4MCIvPgo8L3N2Zz4K';">
                        </div>
                        <div class="snapshot-info">
                            <div class="snapshot-date">${formatDateTime(snapshot.captured_at)}</div>
                            <div class="snapshot-trigger">${this.formatTrigger(snapshot.capture_trigger)}</div>
                            ${snapshot.job_name ? `<div class="snapshot-job">📝 ${escapeHtml(snapshot.job_name)}</div>` : ''}
                            ${snapshot.notes ? `<div class="snapshot-notes">${escapeHtml(snapshot.notes)}</div>` : ''}
                        </div>
                        <div class="snapshot-actions">
                            <a href="${api.baseURL}/snapshots/${snapshot.id}/download"
                               class="btn btn-sm btn-secondary"
                               download="${snapshot.filename}"
                               title="Herunterladen">
                                💾
                            </a>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Format trigger type for display
     */
    formatTrigger(trigger) {
        const triggers = {
            'manual': '👆 Manuell',
            'auto': '🤖 Automatisch',
            'job_start': '▶️ Auftrag gestartet',
            'job_complete': '✅ Auftrag fertig',
            'job_failed': '❌ Auftrag fehlgeschlagen'
        };
        return triggers[trigger] || trigger;
    }

    /**
     * Initialize camera status for all printers
     */
    async initializeCameraStatus() {
        if (printerManager && printerManager.printers) {
            for (const [printerId, printerInfo] of printerManager.printers) {
                await this.getCameraStatus(printerId);
            }
        }
    }
}

// Global camera manager instance
const cameraManager = new CameraManager();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize camera status after a short delay to let printers load
    setTimeout(() => {
        cameraManager.initializeCameraStatus();
    }, 1000);
});