/**
 * Printernizer Timelapses Management Page
 * Handles timelapse video gallery, playback, and management
 */

class TimelapseManager {
    constructor() {
        this.timelapses = new Map();
        this.refreshInterval = null;
        this.currentFilters = {};
        this.videoPlayerModal = null;
    }

    /**
     * Initialize timelapses management page
     */
    init() {
        Logger.debug('Initializing timelapses management');

        // Load timelapses
        this.loadTimelapses();

        // Load stats
        this.loadStats();

        // Setup filter handlers
        this.setupFilterHandlers();

        // Set up refresh interval
        this.startAutoRefresh();

        // Setup WebSocket listeners
        this.setupWebSocketListeners();
    }

    /**
     * Cleanup timelapses manager resources
     */
    cleanup() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }

        // Clean up video player
        if (this.videoPlayerModal) {
            this.videoPlayerModal.cleanup();
            this.videoPlayerModal = null;
        }
    }

    /**
     * Load and display timelapses
     */
    async loadTimelapses() {
        try {
            const timelapsesList = document.getElementById('timelapsesList');
            if (!timelapsesList) return;

            setLoadingState(timelapsesList, true);

            // Prepare filters
            const filters = {
                ...this.currentFilters,
                limit: 100  // Show all for gallery view
            };

            // Load timelapses from API
            const response = await api.getTimelapses(filters);

            // Clear existing
            this.timelapses.clear();
            timelapsesList.innerHTML = '';

            if (response && response.length > 0) {
                // Create timelapse cards
                response.forEach(timelapse => {
                    const card = new TimelapseCard(timelapse, this);
                    const cardElement = card.render();
                    timelapsesList.appendChild(cardElement);

                    // Store for updates
                    this.timelapses.set(timelapse.id, card);
                });

            } else {
                // Show empty state
                timelapsesList.innerHTML = this.renderEmptyState();
            }

        } catch (error) {
            Logger.error('Failed to load timelapses:', error);
            const timelapsesList = document.getElementById('timelapsesList');
            if (timelapsesList) {
                timelapsesList.innerHTML = '<div class="error-message">Fehler beim Laden der Zeitraffer-Videos</div>';
            }
        }
    }

    /**
     * Load statistics
     */
    async loadStats() {
        try {
            const stats = await api.getTimelapseStats();

            if (stats) {
                this.updateStats(stats);
            }

        } catch (error) {
            Logger.error('Failed to load timelapse stats:', error);
        }
    }

    /**
     * Update stats display
     */
    updateStats(stats) {
        document.getElementById('statTotalVideos').textContent = stats.total_videos || 0;
        document.getElementById('statProcessing').textContent = stats.processing_count || 0;
        document.getElementById('statCompleted').textContent = stats.completed_count || 0;

        // Format storage size
        const sizeGB = (stats.total_size_bytes || 0) / (1024 * 1024 * 1024);
        if (sizeGB >= 1) {
            document.getElementById('statStorageSize').textContent = `${sizeGB.toFixed(2)} GB`;
        } else {
            const sizeMB = (stats.total_size_bytes || 0) / (1024 * 1024);
            document.getElementById('statStorageSize').textContent = `${sizeMB.toFixed(1)} MB`;
        }

        document.getElementById('statCleanupCandidates').textContent = stats.cleanup_candidates_count || 0;

        // Show/hide processing queue based on stats
        const processingQueue = document.getElementById('processingQueue');
        if (stats.processing_count > 0) {
            processingQueue.style.display = 'block';
        } else {
            processingQueue.style.display = 'none';
        }
    }

    /**
     * Setup filter event handlers
     */
    setupFilterHandlers() {
        // Status filter
        const statusFilter = document.getElementById('timelapseStatusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.currentFilters.status = e.target.value || null;
                this.loadTimelapses();
            });
        }

        // Linked only checkbox
        const linkedOnlyFilter = document.getElementById('timelapseLinkedOnly');
        if (linkedOnlyFilter) {
            linkedOnlyFilter.addEventListener('change', (e) => {
                this.currentFilters.linked_only = e.target.checked;
                this.loadTimelapses();
            });
        }
    }

    /**
     * Setup WebSocket event listeners
     */
    setupWebSocketListeners() {
        if (!window.websocketManager) return;

        // Listen for timelapse events
        window.websocketManager.on('timelapse.discovered', (data) => this.handleTimelapseUpdate(data));
        window.websocketManager.on('timelapse.pending', (data) => this.handleTimelapseUpdate(data));
        window.websocketManager.on('timelapse.processing', (data) => this.handleTimelapseUpdate(data));
        window.websocketManager.on('timelapse.completed', (data) => this.handleTimelapseUpdate(data));
        window.websocketManager.on('timelapse.failed', (data) => this.handleTimelapseUpdate(data));
        window.websocketManager.on('timelapse.deleted', (data) => this.handleTimelapseDeleted(data));
    }

    /**
     * Handle timelapse update from WebSocket
     */
    handleTimelapseUpdate(data) {
        Logger.debug('Timelapse update:', data);

        // Reload timelapses and stats
        this.loadTimelapses();
        this.loadStats();
    }

    /**
     * Handle timelapse deleted from WebSocket
     */
    handleTimelapseDeleted(data) {
        Logger.debug('Timelapse deleted:', data);

        // Remove from display
        const card = this.timelapses.get(data.id);
        if (card) {
            card.remove();
            this.timelapses.delete(data.id);
        }

        // Reload stats
        this.loadStats();
    }

    /**
     * Start auto-refresh timer
     */
    startAutoRefresh() {
        // Refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadTimelapses();
            this.loadStats();
        }, 30000);
    }

    /**
     * Manual trigger processing for a timelapse
     */
    async triggerProcessing(timelapseId) {
        try {
            await api.triggerTimelapseProcessing(timelapseId);
            showToast('Verarbeitung gestartet', 'success');
            this.loadTimelapses();
            this.loadStats();
        } catch (error) {
            Logger.error('Failed to trigger processing:', error);
            showToast('Fehler beim Starten der Verarbeitung', 'error');
        }
    }

    /**
     * Delete timelapse
     */
    async deleteTimelapse(timelapseId) {
        if (!confirm('Möchten Sie dieses Zeitraffer-Video wirklich löschen?')) {
            return;
        }

        try {
            await api.deleteTimelapse(timelapseId);
            showToast('Zeitraffer gelöscht', 'success');

            // Remove from display
            const card = this.timelapses.get(timelapseId);
            if (card) {
                card.remove();
                this.timelapses.delete(timelapseId);
            }

            this.loadStats();
        } catch (error) {
            Logger.error('Failed to delete timelapse:', error);
            showToast('Fehler beim Löschen', 'error');
        }
    }

    /**
     * Toggle pin status
     */
    async togglePin(timelapseId) {
        try {
            await api.toggleTimelapsePin(timelapseId);
            this.loadTimelapses();
        } catch (error) {
            Logger.error('Failed to toggle pin:', error);
            showToast('Fehler beim Ändern des Pin-Status', 'error');
        }
    }

    /**
     * Play video in modal
     */
    playVideo(timelapse) {
        if (!this.videoPlayerModal) {
            this.videoPlayerModal = new VideoPlayerModal();
        }
        this.videoPlayerModal.show(timelapse);
    }

    /**
     * Render empty state
     */
    renderEmptyState() {
        return `
            <div class="empty-state">
                <div class="empty-icon">🎬</div>
                <h3>Keine Zeitraffer-Videos</h3>
                <p>Es wurden noch keine Zeitraffer-Videos gefunden.</p>
                <p class="text-muted">
                    Zeitraffer werden automatisch erkannt, wenn Bilder in konfigurierten Ordnern gefunden werden.
                </p>
            </div>
        `;
    }
}


/**
 * TimelapseCard Component
 * Displays a single timelapse in the gallery
 */
class TimelapseCard {
    constructor(timelapse, manager) {
        this.timelapse = timelapse;
        this.manager = manager;
        this.element = null;
    }

    /**
     * Render the card
     */
    render() {
        const div = document.createElement('div');
        div.className = 'timelapse-card';
        div.dataset.timelapseId = this.timelapse.id;

        // Status badge
        const statusBadge = this.renderStatusBadge();

        // Thumbnail or placeholder
        const thumbnail = this.renderThumbnail();

        // Metadata
        const metadata = this.renderMetadata();

        // Actions
        const actions = this.renderActions();

        div.innerHTML = `
            ${statusBadge}
            ${thumbnail}
            <div class="card-content">
                <h3 class="card-title" title="${this.escapeHtml(this.timelapse.folder_name)}">
                    ${this.escapeHtml(this.timelapse.folder_name)}
                </h3>
                ${metadata}
                ${actions}
            </div>
        `;

        this.element = div;
        return div;
    }

    /**
     * Render status badge
     */
    renderStatusBadge() {
        const statusIcons = {
            'discovered': '🔍',
            'pending': '⏳',
            'processing': '⚙️',
            'completed': '✅',
            'failed': '❌'
        };

        const statusLabels = {
            'discovered': 'Entdeckt',
            'pending': 'Wartend',
            'processing': 'Verarbeitung',
            'completed': 'Fertig',
            'failed': 'Fehlgeschlagen'
        };

        const icon = statusIcons[this.timelapse.status] || '❓';
        const label = statusLabels[this.timelapse.status] || this.timelapse.status;

        return `<div class="status-badge status-${this.timelapse.status}">${icon} ${label}</div>`;
    }

    /**
     * Render thumbnail
     */
    renderThumbnail() {
        if (this.timelapse.status === 'completed' && this.timelapse.output_video_path) {
            // Video thumbnail/player
            return `
                <div class="card-thumbnail video-thumbnail" onclick="timelapseManager.playVideo(${JSON.stringify(this.timelapse).replace(/"/g, '&quot;')})">
                    <div class="play-overlay">
                        <div class="play-button">▶</div>
                    </div>
                    <div class="video-duration">${this.formatDuration(this.timelapse.video_duration)}</div>
                </div>
            `;
        } else {
            // Processing or pending placeholder
            return `
                <div class="card-thumbnail placeholder-thumbnail">
                    <div class="thumbnail-icon">🎬</div>
                    <div class="thumbnail-text">${this.timelapse.image_count || 0} Bilder</div>
                </div>
            `;
        }
    }

    /**
     * Render metadata
     */
    renderMetadata() {
        const parts = [];

        // Image count
        if (this.timelapse.image_count) {
            parts.push(`<span>📷 ${this.timelapse.image_count} Bilder</span>`);
        }

        // File size
        if (this.timelapse.file_size_bytes) {
            const sizeMB = (this.timelapse.file_size_bytes / (1024 * 1024)).toFixed(1);
            parts.push(`<span>💾 ${sizeMB} MB</span>`);
        }

        // Created date
        if (this.timelapse.created_at) {
            const date = new Date(this.timelapse.created_at);
            parts.push(`<span>📅 ${this.formatDate(date)}</span>`);
        }

        // Pinned status
        if (this.timelapse.pinned) {
            parts.push(`<span>📌 Angepinnt</span>`);
        }

        // Error message
        if (this.timelapse.error_message) {
            parts.push(`<span class="error-text">⚠️ ${this.escapeHtml(this.timelapse.error_message)}</span>`);
        }

        return `<div class="card-metadata">${parts.join('')}</div>`;
    }

    /**
     * Render action buttons
     */
    renderActions() {
        const buttons = [];

        // Play button (only for completed)
        if (this.timelapse.status === 'completed') {
            buttons.push(`
                <button class="btn btn-primary btn-sm" onclick="timelapseManager.playVideo(${JSON.stringify(this.timelapse).replace(/"/g, '&quot;')})">
                    ▶️ Abspielen
                </button>
            `);
        }

        // Trigger processing (only for discovered or failed)
        if (this.timelapse.status === 'discovered' || this.timelapse.status === 'failed') {
            buttons.push(`
                <button class="btn btn-secondary btn-sm" onclick="timelapseManager.triggerProcessing('${this.timelapse.id}')">
                    ⚙️ Verarbeiten
                </button>
            `);
        }

        // Pin/Unpin button
        const pinIcon = this.timelapse.pinned ? '📍' : '📌';
        const pinLabel = this.timelapse.pinned ? 'Lösen' : 'Anpinnen';
        buttons.push(`
            <button class="btn btn-secondary btn-sm" onclick="timelapseManager.togglePin('${this.timelapse.id}')">
                ${pinIcon} ${pinLabel}
            </button>
        `);

        // Delete button
        buttons.push(`
            <button class="btn btn-danger btn-sm" onclick="timelapseManager.deleteTimelapse('${this.timelapse.id}')">
                🗑️ Löschen
            </button>
        `);

        return `<div class="card-actions">${buttons.join('')}</div>`;
    }

    /**
     * Remove card from DOM
     */
    remove() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }

    /**
     * Format duration in seconds to mm:ss
     */
    formatDuration(seconds) {
        if (!seconds) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    /**
     * Format date
     */
    formatDate(date) {
        return date.toLocaleDateString('de-DE', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}


/**
 * Video Player Modal
 * Full-screen video playback with metadata
 */
class VideoPlayerModal {
    constructor() {
        this.modal = null;
        this.video = null;
        this.timelapse = null;
        this.createModal();
    }

    /**
     * Create modal element
     */
    createModal() {
        const modalHTML = `
            <div id="videoPlayerModal" class="modal" style="display: none;">
                <div class="modal-backdrop" onclick="videoPlayerModal.hide()"></div>
                <div class="modal-content modal-video">
                    <div class="modal-header">
                        <h2 id="videoPlayerTitle">Zeitraffer-Video</h2>
                        <button class="modal-close" onclick="videoPlayerModal.hide()">✕</button>
                    </div>
                    <div class="modal-body">
                        <div class="video-player-container">
                            <video id="videoPlayer" controls autoplay>
                                Ihr Browser unterstützt keine HTML5 Videos.
                            </video>
                        </div>
                        <div id="videoPlayerMetadata" class="video-metadata"></div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" id="downloadVideoBtn">
                            💾 Herunterladen
                        </button>
                        <button class="btn btn-secondary" onclick="videoPlayerModal.hide()">
                            Schließen
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('videoPlayerModal');
        this.video = document.getElementById('videoPlayer');

        // Store reference globally
        window.videoPlayerModal = this;
    }

    /**
     * Show modal with timelapse video
     */
    show(timelapse) {
        this.timelapse = timelapse;

        // Set video source
        if (timelapse.output_video_path) {
            // Build video URL
            const videoUrl = `/api/v1/timelapses/${timelapse.id}/video`;
            this.video.src = videoUrl;
        }

        // Set title
        document.getElementById('videoPlayerTitle').textContent = timelapse.folder_name;

        // Set metadata
        this.renderMetadata(timelapse);

        // Set download button
        document.getElementById('downloadVideoBtn').onclick = () => this.downloadVideo();

        // Show modal
        this.modal.style.display = 'flex';

        // Play video
        this.video.play();
    }

    /**
     * Hide modal
     */
    hide() {
        // Pause and clear video
        if (this.video) {
            this.video.pause();
            this.video.src = '';
        }

        // Hide modal
        if (this.modal) {
            this.modal.style.display = 'none';
        }
    }

    /**
     * Render metadata
     */
    renderMetadata(timelapse) {
        const metadata = [];

        if (timelapse.image_count) {
            metadata.push(`<div class="metadata-item"><strong>Bilder:</strong> ${timelapse.image_count}</div>`);
        }

        if (timelapse.video_duration) {
            const duration = this.formatDuration(timelapse.video_duration);
            metadata.push(`<div class="metadata-item"><strong>Dauer:</strong> ${duration}</div>`);
        }

        if (timelapse.file_size_bytes) {
            const sizeMB = (timelapse.file_size_bytes / (1024 * 1024)).toFixed(1);
            metadata.push(`<div class="metadata-item"><strong>Größe:</strong> ${sizeMB} MB</div>`);
        }

        if (timelapse.created_at) {
            const date = new Date(timelapse.created_at);
            metadata.push(`<div class="metadata-item"><strong>Erstellt:</strong> ${date.toLocaleString('de-DE')}</div>`);
        }

        if (timelapse.job_id) {
            metadata.push(`<div class="metadata-item"><strong>Verknüpft:</strong> <a href="#jobs/${sanitizeAttribute(timelapse.job_id)}">Auftrag anzeigen</a></div>`);
        }

        document.getElementById('videoPlayerMetadata').innerHTML = metadata.join('');
    }

    /**
     * Download video
     */
    downloadVideo() {
        if (this.timelapse && this.timelapse.id) {
            const downloadUrl = `/api/v1/timelapses/${this.timelapse.id}/video?download=true`;
            window.open(downloadUrl, '_blank');
        }
    }

    /**
     * Format duration
     */
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    /**
     * Cleanup
     */
    cleanup() {
        this.hide();
    }
}


// Global functions
let timelapseManager = null;

/**
 * Initialize timelapses page
 */
function initTimelapsesPage() {
    if (!timelapseManager) {
        timelapseManager = new TimelapseManager();
    }
    timelapseManager.init();
}

/**
 * Cleanup timelapses page
 */
function cleanupTimelapsesPage() {
    if (timelapseManager) {
        timelapseManager.cleanup();
    }
}

/**
 * Refresh timelapses
 */
function refreshTimelapses() {
    if (timelapseManager) {
        timelapseManager.loadTimelapses();
        timelapseManager.loadStats();
    }
}
