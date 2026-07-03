/**
 * Camera functionality for Printernizer
 * Handles camera streams, snapshots, and gallery
 */

class CameraManager {
    constructor() {
        this.cameraStatus = new Map(); // printer_id -> camera status
        this.activeStreams = new Set(); // Active stream URLs
        this.previewIntervals = new Map(); // printer_id -> interval ID for auto-refresh
        this.lastRefreshTime = new Map(); // printer_id -> last refresh timestamp
    }

    /**
     * Check camera status for a printer
     */
    async getCameraStatus(printerId) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/printers/${printerId}/camera/status`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const status = await response.json();
            this.cameraStatus.set(printerId, status);

            // Initialize auto-refresh for preview mode
            this.initializePreviewAutoRefresh(printerId);

            return status;
        } catch (error) {
            // Safe error logging - check if Logger exists first
            const errorMsg = `Failed to get camera status for printer ${printerId}:`;
            if (typeof Logger !== 'undefined') {
                Logger.error(errorMsg, error);
            } else {
                console.error(errorMsg, error);
            }
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
            const response = await fetch(`${CONFIG.API_BASE_URL}/printers/${printerId}/camera/snapshot`, {
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
            showNotification(t('camera.snapshotSuccess'), 'success');
            
            return snapshot;
        } catch (error) {
            // Safe error logging - check if Logger exists first
            const errorMsg = `Failed to take snapshot for printer ${printerId}:`;
            if (typeof Logger !== 'undefined') {
                Logger.error(errorMsg, error);
            } else {
                console.error(errorMsg, error);
            }
            showNotification(t('camera.snapshotError', { message: error.message }), 'error');
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
        const cameraStatus = this.cameraStatus.get(printer.id);

        // Loading state
        if (!cameraStatus) {
            return `
                <div class="info-section camera-section">
                    <h4>📷 ${t('camera.title')}</h4>
                    <div class="info-item">
                        <span class="text-muted">${t('common.loading')}</span>
                    </div>
                </div>
            `;
        }

        // Check for external webcam
        const hasExternalWebcam = cameraStatus.has_external_webcam;
        const hasBuiltinCamera = cameraStatus.has_camera;
        const ffmpegRequired = cameraStatus.ffmpeg_required;
        const ffmpegAvailable = cameraStatus.ffmpeg_available;

        // No camera and no external webcam
        if (!hasBuiltinCamera && !hasExternalWebcam) {
            return `
                <div class="info-section camera-section">
                    <h4>📷 ${t('camera.title')}</h4>
                    <div class="info-item">
                        <span class="text-muted">${t('camera.noCameraAvailable')}</span>
                    </div>
                </div>
            `;
        }

        // Camera not available (error state)
        if (!cameraStatus.is_available) {
            // Special handling for ffmpeg missing with RTSP
            const isFfmpegIssue = ffmpegRequired && !ffmpegAvailable;
            return `
                <div class="info-section camera-section">
                    <h4>📷 ${t('camera.title')}</h4>
                    <div class="info-item">
                        <span class="text-warning">${isFfmpegIssue ? '⚠️ ' + t('camera.rtspUnavailable') : t('camera.notAvailable')}</span>
                        ${cameraStatus.error_message ? `<br><small class="text-muted">${escapeHtml(cameraStatus.error_message)}</small>` : ''}
                        ${isFfmpegIssue ? `<br><code style="font-size: 0.8em; background: #f8f9fa; padding: 2px 6px; border-radius: 3px;">apt-get install ffmpeg</code>` : ''}
                    </div>
                </div>
            `;
        }

        let html = `<div class="info-section camera-section"><h4>📷 ${t('camera.title')}</h4>`;

        // Render external webcam if configured
        if (hasExternalWebcam) {
            const externalPreviewUrl = `${CONFIG.API_BASE_URL}/printers/${printer.id}/camera/external-preview?t=${Date.now()}`;
            html += `
                <div class="camera-controls" style="margin-bottom: 12px;">
                    <div style="font-size: 0.9em; color: #6c757d; margin-bottom: 4px;">📹 External Webcam</div>
                    <div class="camera-preview-container">
                        <img id="external-camera-${printer.id}"
                             class="camera-stream"
                             src="${externalPreviewUrl}"
                             alt="External Webcam"
                             onerror="this.style.display='none'; var e=this.parentElement.querySelector('.stream-error'); if(e)e.style.display='block';"
                             onload="this.style.display='block'; var e=this.parentElement.querySelector('.stream-error'); if(e)e.style.display='none';"
                             style="width: 100%; height: auto; border-radius: 4px; margin-bottom: 8px;">
                        <div class="stream-error" style="display: none;">
                            <span class="text-muted">External webcam not available</span>
                        </div>
                        <div class="camera-timestamp" id="external-timestamp-${printer.id}" style="font-size: 0.85em; color: #6c757d; text-align: center; margin-top: 4px;">
                            ${t('camera.updatedAt')} ${new Date().toLocaleTimeString(getIntlLocale())}
                        </div>
                    </div>
                    <div class="camera-actions" style="display: flex; gap: 8px; margin-top: 8px;">
                        <button class="btn btn-sm btn-secondary"
                                onclick="cameraManager.refreshExternalPreview('${printer.id}')"
                                title="Refresh external webcam">
                            🔄 Refresh
                        </button>
                    </div>
                </div>
            `;
        }

        // Render built-in camera if available
        if (hasBuiltinCamera && cameraStatus.stream_url) {
            const hasValidUrl = cameraStatus.stream_url !== 'null' && cameraStatus.stream_url !== 'undefined';

            if (hasValidUrl) {
                const isPreview = cameraStatus.stream_url.includes('/camera/preview');
                const imageUrl = isPreview
                    ? `${cameraStatus.stream_url}?t=${Date.now()}`
                    : cameraStatus.stream_url;

                html += `
                    <div class="camera-controls">
                        ${hasExternalWebcam ? '<div style="font-size: 0.9em; color: #6c757d; margin-bottom: 4px;">🖨️ Printer Camera</div>' : ''}
                        <div class="camera-preview-container">
                            <img id="camera-stream-${printer.id}"
                                 class="camera-stream"
                                 src="${imageUrl}"
                                 alt="${t('camera.previewAlt')}"
                                 onerror="this.style.display='none'; var e=this.parentElement.querySelector('.stream-error'); if(e)e.style.display='block';"
                                 onload="this.style.display='block'; var e=this.parentElement.querySelector('.stream-error'); if(e)e.style.display='none';"
                                 style="width: 100%; height: auto; border-radius: 4px; margin-bottom: 8px;">
                            <div class="stream-error" style="display: none;">
                                <span class="text-muted">${t('camera.imageUnavailable')}</span>
                            </div>
                            ${isPreview ? `
                                <div class="camera-timestamp" id="camera-timestamp-${printer.id}" style="font-size: 0.85em; color: #6c757d; text-align: center; margin-top: 4px;">
                                    ${t('camera.updatedAt')} ${new Date().toLocaleTimeString(getIntlLocale())}
                                </div>
                            ` : ''}
                        </div>
                        <div class="camera-actions" style="display: flex; gap: 8px; margin-top: 8px;">
                            <button class="btn btn-sm btn-primary"
                                    onclick="cameraManager.takeSnapshotFromCard('${printer.id}')"
                                    title="${t('camera.takeSnapshot')}">
                                📸 Snapshot
                            </button>
                            ${isPreview ? `
                                <button class="btn btn-sm btn-secondary"
                                        onclick="cameraManager.refreshPreview('${printer.id}', true)"
                                        title="${t('camera.refreshPreviewTitle')}">
                                    🔄 ${t('common.refresh')}
                                </button>
                            ` : ''}
                            <button class="btn btn-sm btn-secondary"
                                    onclick="cameraManager.showCameraModal('${printer.id}')"
                                    title="${t('camera.fullscreenTitle')}">
                                🔍 ${t('camera.fullscreen')}
                            </button>
                        </div>
                    </div>
                `;
            }
        }

        html += '</div>';
        return html;
    }

    /**
     * Refresh external webcam preview
     */
    refreshExternalPreview(printerId) {
        const imageElement = document.getElementById(`external-camera-${printerId}`);
        const timestampElement = document.getElementById(`external-timestamp-${printerId}`);

        if (imageElement) {
            imageElement.src = `${CONFIG.API_BASE_URL}/printers/${printerId}/camera/external-preview?t=${Date.now()}`;
            if (timestampElement) {
                timestampElement.textContent = `${t('camera.updatedAt')} ${new Date().toLocaleTimeString(getIntlLocale())}`;
            }
        }
    }

    /**
     * Start auto-refresh for preview (30 seconds)
     */
    startPreviewAutoRefresh(printerId) {
        // Stop existing interval if any
        this.stopPreviewAutoRefresh(printerId);

        const intervalId = setInterval(() => {
            this.refreshPreview(printerId, false);  // Silent refresh
        }, 30000);  // 30 seconds

        this.previewIntervals.set(printerId, intervalId);
        Logger.debug(`Started auto-refresh for printer ${printerId}`);
    }

    /**
     * Stop auto-refresh for preview
     */
    stopPreviewAutoRefresh(printerId) {
        const intervalId = this.previewIntervals.get(printerId);
        if (intervalId) {
            clearInterval(intervalId);
            this.previewIntervals.delete(printerId);
            Logger.debug(`Stopped auto-refresh for printer ${printerId}`);
        }
    }

    /**
     * Refresh preview image manually or via auto-refresh
     */
    async refreshPreview(printerId, showFeedback = true) {
        const cameraStatus = this.cameraStatus.get(printerId);
        if (!cameraStatus || !cameraStatus.stream_url) return;

        const isPreview = cameraStatus.stream_url.includes('/camera/preview');
        if (!isPreview) return;

        const imageElement = document.getElementById(`camera-stream-${printerId}`);
        const timestampElement = document.getElementById(`camera-timestamp-${printerId}`);

        if (imageElement) {
            // Update image src with new timestamp for cache-busting
            const newUrl = `${cameraStatus.stream_url}?t=${Date.now()}`;
            imageElement.src = newUrl;

            // Update timestamp display
            if (timestampElement) {
                const now = new Date();
                timestampElement.textContent = `${t('camera.updatedAt')} ${now.toLocaleTimeString(getIntlLocale())}`;
            }

            this.lastRefreshTime.set(printerId, Date.now());

            if (showFeedback) {
                showNotification(t('camera.previewRefreshed'), 'success');
            }
        }
    }

    /**
     * Initialize auto-refresh after camera status is loaded
     */
    initializePreviewAutoRefresh(printerId) {
        const cameraStatus = this.cameraStatus.get(printerId);
        if (!cameraStatus || !cameraStatus.is_available) return;

        const isPreview = cameraStatus.stream_url &&
                         cameraStatus.stream_url.includes('/camera/preview');

        if (isPreview) {
            this.startPreviewAutoRefresh(printerId);
        }
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
    showCameraModal(printerId) {
        const cameraStatus = this.cameraStatus.get(printerId);

        // Validate camera status
        if (!cameraStatus) {
            showNotification(t('camera.statusUnavailable'), 'error');
            return;
        }

        if (!cameraStatus.is_available || !cameraStatus.stream_url) {
            showNotification(t('camera.notAvailable'), 'error');
            return;
        }

        // Check for valid URL (not null/undefined)
        if (cameraStatus.stream_url === 'null' ||
            cameraStatus.stream_url === 'undefined' ||
            !cameraStatus.stream_url) {
            showNotification(t('camera.invalidUrl'), 'error');
            return;
        }

        const printer = printerManager.printers.get(printerId);
        const printerName = printer ? printer.data.name : printerId;

        const isPreview = cameraStatus.stream_url.includes('/camera/preview');
        const imageUrl = isPreview
            ? `${cameraStatus.stream_url}?t=${Date.now()}`
            : cameraStatus.stream_url;

        const modal = document.createElement('div');
        modal.className = 'modal camera-modal';
        modal.style.display = 'block';
        modal.innerHTML = `
            <div class="modal-content camera-modal-content">
                <div class="modal-header">
                    <h3>📷 ${escapeHtml(printerName)} - ${t('camera.title')}</h3>
                    ${isPreview ? `
                        <span class="badge badge-secondary" id="modal-timestamp" style="margin-left: 10px;">
                            ${t('camera.updatedAt')} ${new Date().toLocaleTimeString(getIntlLocale())}
                        </span>
                    ` : ''}
                    <button class="btn btn-sm btn-secondary" onclick="this.closest('.modal').remove()">
                        ✕
                    </button>
                </div>
                <div class="modal-body">
                    <div class="camera-full-view">
                        <img id="modal-camera-stream"
                             class="camera-stream-full"
                             src="${imageUrl}"
                             alt="${t('camera.title')}"
                             style="width: 100%; height: auto;">
                    </div>
                    <div class="camera-modal-controls" style="margin-top: 16px; display: flex; gap: 8px; justify-content: center;">
                        ${isPreview ? `
                            <button class="btn btn-secondary"
                                    onclick="cameraManager.refreshModalPreview('${printerId}')">
                                🔄 ${t('common.refresh')}
                            </button>
                        ` : ''}
                        <button class="btn btn-primary"
                                onclick="cameraManager.takeSnapshotFromCard('${printerId}')">
                            📸 ${t('camera.takeSnapshot')}
                        </button>
                        <button class="btn btn-secondary"
                                onclick="cameraManager.showSnapshotHistory('${printerId}')">
                            🖼️ ${t('camera.snapshotHistory')}
                        </button>
                        <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">
                            ${t('common.close')}
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Start auto-refresh for preview mode in modal (30 seconds)
        if (isPreview) {
            const modalIntervalId = setInterval(() => {
                // Check if modal still exists
                if (!document.body.contains(modal)) {
                    clearInterval(modalIntervalId);
                    return;
                }
                this.refreshModalPreview(printerId);
            }, 30000);  // 30 seconds

            // Store interval ID for cleanup
            modal.dataset.intervalId = modalIntervalId;
        }

        // Cleanup on modal close
        const closeButton = modal.querySelector('[onclick*="remove()"]');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                if (modal.dataset.intervalId) {
                    clearInterval(parseInt(modal.dataset.intervalId));
                }
            });
        }
    }

    /**
     * Refresh preview in modal
     */
    refreshModalPreview(printerId) {
        const cameraStatus = this.cameraStatus.get(printerId);
        if (!cameraStatus || !cameraStatus.stream_url) return;

        const imageElement = document.getElementById('modal-camera-stream');
        const timestampElement = document.getElementById('modal-timestamp');

        if (imageElement) {
            const newUrl = `${cameraStatus.stream_url}?t=${Date.now()}`;
            imageElement.src = newUrl;

            if (timestampElement) {
                const now = new Date();
                timestampElement.textContent = `${t('camera.updatedAt')} ${now.toLocaleTimeString(getIntlLocale())}`;
            }
        }
    }

    /**
     * Show snapshot history modal
     */
    async showSnapshotHistory(printerId) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/printers/${printerId}/snapshots`);
            const snapshots = response.ok ? await response.json() : [];
            
            const modal = document.createElement('div');
            modal.className = 'modal snapshots-modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>🖼️ ${t('camera.snapshotHistory')}</h3>
                        <button class="btn btn-sm btn-secondary" onclick="this.closest('.modal').remove()">
                            ✕
                        </button>
                    </div>
                    <div class="modal-body">
                        ${snapshots.length > 0 ? this.renderSnapshotGrid(snapshots) : `<p class="text-muted">${t('camera.noSnapshots')}</p>`}
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
        } catch (error) {
            // Safe error logging - check if Logger exists first
            if (typeof Logger !== 'undefined') {
                Logger.error('Failed to load snapshot history:', error);
            } else {
                console.error('Failed to load snapshot history:', error);
            }
            showNotification(t('camera.historyLoadError'), 'error');
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
                               title="${t('common.download')}">
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
            'manual': '👆 ' + t('camera.triggerManual'),
            'auto': '🤖 ' + t('camera.triggerAuto'),
            'job_start': '▶️ ' + t('camera.triggerJobStart'),
            'job_complete': '✅ ' + t('camera.triggerJobComplete'),
            'job_failed': '❌ ' + t('camera.triggerJobFailed')
        };
        return triggers[trigger] || trigger;
    }

    /**
     * Cleanup camera resources for a printer
     */
    cleanup(printerId) {
        this.stopPreviewAutoRefresh(printerId);
        this.cameraStatus.delete(printerId);
        this.lastRefreshTime.delete(printerId);
        Logger.debug(`Cleaned up camera resources for printer ${printerId}`);
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

// Make cameraManager globally available (similar to Logger)
window.cameraManager = cameraManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize camera status after a short delay to let printers load
    setTimeout(() => {
        cameraManager.initializeCameraStatus();
    }, 1000);
});