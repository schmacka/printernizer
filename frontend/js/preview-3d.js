/**
 * 3D File Preview Module
 * Provides fullscreen preview functionality for 3D model files (STL, 3MF, GCODE, BGCODE)
 */

class Preview3DManager {
    constructor() {
        this.modal = null;
        this.imageWrapper = null;
        this.infoContainer = null;
        this.closeButton = null;
        this.currentFile = null;
        this.isOpen = false;
    }

    /**
     * Initialize the preview manager
     */
    initialize() {
        this.modal = document.getElementById('preview3dFullscreen');
        if (!this.modal) {
            Logger.warn('Preview3D: Modal element not found');
            return;
        }

        this.imageWrapper = this.modal.querySelector('.preview-3d-image-wrapper');
        this.infoContainer = this.modal.querySelector('.preview-3d-info');
        this.closeButton = this.modal.querySelector('.preview-3d-close');

        this.setupEventListeners();
        Logger.info('Preview3D: Initialized');
    }

    /**
     * Setup event listeners for closing the modal
     */
    setupEventListeners() {
        // Close button
        if (this.closeButton) {
            this.closeButton.addEventListener('click', () => this.close());
        }

        // Click on backdrop to close
        if (this.modal) {
            this.modal.addEventListener('click', (e) => {
                // Only close if clicking on the backdrop itself, not on content
                if (e.target === this.modal || e.target.classList.contains('preview-3d-container')) {
                    this.close();
                }
            });
        }

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    /**
     * Open preview for a file
     * @param {Object|string} fileData - File object or file identifier
     * @param {string} source - 'library' or 'printer' to determine API endpoint
     */
    async open(fileData, source = 'auto') {
        if (!this.modal) {
            Logger.error('Preview3D: Modal not initialized');
            showToast('Preview not available', 'error');
            return;
        }

        // Normalize file data
        const file = this.normalizeFileData(fileData);
        if (!file) {
            Logger.error('Preview3D: Invalid file data', fileData);
            showToast('Invalid file data', 'error');
            return;
        }

        this.currentFile = file;

        // Show modal with loading state
        this.showLoading();
        this.modal.classList.add('show');
        this.isOpen = true;
        document.body.style.overflow = 'hidden'; // Prevent background scrolling

        // Determine file type and load appropriate preview
        const fileType = this.getFileType(file.filename);
        const supportsAnimation = ['stl', '3mf'].includes(fileType);

        try {
            // Build thumbnail URL based on source
            const baseUrl = this.getBaseUrl(file, source);
            const thumbnailUrl = supportsAnimation
                ? `${baseUrl}/thumbnail/animated`
                : `${baseUrl}/thumbnail`;

            // Load and display the preview
            await this.loadPreview(thumbnailUrl, file, fileType, supportsAnimation);

        } catch (error) {
            Logger.error('Preview3D: Failed to load preview', error);
            this.showError(file, error.message);
        }
    }

    /**
     * Normalize file data from various sources
     */
    normalizeFileData(fileData) {
        if (typeof fileData === 'string') {
            // Just an ID/checksum - create minimal file object
            return {
                id: fileData,
                checksum: fileData,
                filename: 'Unknown file'
            };
        }

        if (typeof fileData === 'object' && fileData !== null) {
            return {
                id: fileData.id || fileData.checksum,
                checksum: fileData.checksum || fileData.id,
                filename: fileData.filename || fileData.name || 'Unknown file',
                file_type: fileData.file_type,
                file_size: fileData.file_size
            };
        }

        return null;
    }

    /**
     * Get file type from filename
     */
    getFileType(filename) {
        if (!filename) return 'unknown';
        const ext = filename.split('.').pop().toLowerCase();
        return ext;
    }

    /**
     * Get base URL for thumbnail API
     */
    getBaseUrl(file, source) {
        const apiBase = typeof CONFIG !== 'undefined' ? CONFIG.API_BASE_URL : '/api/v1';

        // Auto-detect: if it looks like a checksum (long hex string), use library API
        if (source === 'auto') {
            const id = file.checksum || file.id;
            // Checksums are typically 32+ hex characters
            if (id && /^[a-f0-9]{32,}$/i.test(id)) {
                source = 'library';
            } else {
                source = 'files';
            }
        }

        if (source === 'library') {
            return `${apiBase}/library/files/${file.checksum || file.id}`;
        } else {
            return `${apiBase}/files/${file.id}`;
        }
    }

    /**
     * Show loading state
     */
    showLoading() {
        if (this.imageWrapper) {
            this.imageWrapper.innerHTML = `
                <div class="preview-3d-loading">
                    <div class="spinner"></div>
                    <p>Loading preview...</p>
                </div>
            `;
        }
        if (this.infoContainer) {
            this.infoContainer.innerHTML = '';
        }
    }

    /**
     * Load and display preview image
     */
    async loadPreview(url, file, fileType, isAnimated) {
        return new Promise((resolve, reject) => {
            const img = new Image();

            img.onload = () => {
                // Successfully loaded
                this.imageWrapper.innerHTML = '';
                img.className = 'preview-3d-image';
                img.alt = `3D Preview: ${file.filename}`;
                this.imageWrapper.appendChild(img);

                // Show file info
                this.showFileInfo(file, fileType, isAnimated);
                resolve();
            };

            img.onerror = () => {
                // Try fallback to static thumbnail if animated failed
                if (isAnimated && url.includes('/animated')) {
                    const staticUrl = url.replace('/animated', '');
                    Logger.info('Preview3D: Animated preview failed, trying static', { staticUrl });

                    const fallbackImg = new Image();
                    fallbackImg.onload = () => {
                        this.imageWrapper.innerHTML = '';
                        fallbackImg.className = 'preview-3d-image';
                        fallbackImg.alt = `3D Preview: ${file.filename}`;
                        this.imageWrapper.appendChild(fallbackImg);
                        this.showFileInfo(file, fileType, false);
                        resolve();
                    };
                    fallbackImg.onerror = () => {
                        reject(new Error('Failed to load preview image'));
                    };
                    fallbackImg.src = staticUrl;
                } else {
                    reject(new Error('Failed to load preview image'));
                }
            };

            img.src = url;
        });
    }

    /**
     * Show file info below the preview
     */
    showFileInfo(file, fileType, isAnimated) {
        if (!this.infoContainer) return;

        const fileSize = file.file_size ? this.formatFileSize(file.file_size) : '';
        const animatedBadge = isAnimated ? '<span class="preview-3d-badge">Animated</span>' : '';
        const typeBadge = `<span class="preview-3d-badge">${fileType.toUpperCase()}</span>`;

        this.infoContainer.innerHTML = `
            <h3 class="preview-3d-filename">${this.escapeHtml(file.filename)}</h3>
            <div class="preview-3d-meta">
                ${typeBadge}
                ${animatedBadge}
                ${fileSize ? `<span>${fileSize}</span>` : ''}
            </div>
        `;
    }

    /**
     * Show error state
     */
    showError(file, message) {
        if (this.imageWrapper) {
            this.imageWrapper.innerHTML = `
                <div class="preview-3d-error">
                    <div class="preview-3d-error-icon">📷</div>
                    <p>Preview not available</p>
                    <p style="font-size: 0.8em; opacity: 0.6;">${this.escapeHtml(message || 'Unable to load preview')}</p>
                </div>
            `;
        }
        if (this.infoContainer && file) {
            this.infoContainer.innerHTML = `
                <h3 class="preview-3d-filename">${this.escapeHtml(file.filename)}</h3>
            `;
        }
    }

    /**
     * Close the preview modal
     */
    close() {
        if (this.modal) {
            this.modal.classList.remove('show');
        }
        this.isOpen = false;
        this.currentFile = null;
        document.body.style.overflow = ''; // Restore scrolling
        Logger.debug('Preview3D: Closed');
    }

    /**
     * Format file size for display
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create global instance
const preview3DManager = new Preview3DManager();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    preview3DManager.initialize();
});

// Export for use in other modules
window.preview3DManager = preview3DManager;

/**
 * Global function to open 3D preview
 * Can be called from onclick handlers
 * @param {Object|string} fileData - File object or identifier
 * @param {string} source - 'library', 'files', or 'auto'
 */
window.open3DPreview = function(fileData, source = 'auto') {
    preview3DManager.open(fileData, source);
};
