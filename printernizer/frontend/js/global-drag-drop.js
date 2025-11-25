/**
 * Global Drag and Drop Manager
 * Enables file upload via drag-and-drop from anywhere in the application
 */

class GlobalDragDropManager {
    constructor() {
        this.dragCounter = 0;
        this.allowedExtensions = ['.3mf', '.stl', '.gcode', '.obj', '.ply'];
        this.dropOverlay = null;
        this.isInternalDrag = false; // Track if drag is from internal elements
    }

    /**
     * Initialize global drag and drop
     */
    init() {
        Logger.debug('Initializing global drag-and-drop manager');

        // Create drop overlay
        this.createDropOverlay();

        // Setup event listeners on document
        this.setupEventListeners();

        Logger.debug('Global drag-and-drop enabled');
    }

    /**
     * Create the drop overlay element
     */
    createDropOverlay() {
        this.dropOverlay = document.createElement('div');
        this.dropOverlay.id = 'globalDropOverlay';
        this.dropOverlay.className = 'global-drop-overlay';
        this.dropOverlay.innerHTML = `
            <div class="drop-overlay-content">
                <div class="drop-icon">📁</div>
                <div class="drop-text">Drop files here to upload</div>
                <div class="drop-subtext">Supports .3mf, .stl, .gcode, .obj, .ply</div>
            </div>
        `;
        document.body.appendChild(this.dropOverlay);
    }

    /**
     * Setup drag and drop event listeners
     */
    setupEventListeners() {
        // Prevent default drag behaviors on document
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.addEventListener(eventName, (e) => {
                // Check if this is an internal drag (like navigation reordering)
                if (this.isInternalDragEvent(e)) {
                    this.isInternalDrag = true;
                    // CRITICAL: Must preventDefault on dragover for drops to work
                    // Without this, the browser blocks the drop and drop event never fires
                    if (eventName === 'dragover') {
                        e.preventDefault();
                    }
                    return; // Let internal drag events pass through
                }

                // Only handle file drags
                if (this.hasFiles(e)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            }, false);
        });

        // Track when files enter the window
        document.addEventListener('dragenter', (e) => {
            if (this.isInternalDragEvent(e)) return;
            if (this.hasFiles(e)) {
                this.dragCounter++;
                this.showDropOverlay();
            }
        }, false);

        // Track when files leave the window
        document.addEventListener('dragleave', (e) => {
            if (this.isInternalDragEvent(e)) return;
            if (this.hasFiles(e)) {
                this.dragCounter--;
                if (this.dragCounter === 0) {
                    this.hideDropOverlay();
                }
            }
        }, false);

        // Handle file drop
        document.addEventListener('drop', async (e) => {
            if (this.isInternalDragEvent(e)) {
                this.isInternalDrag = false;
                return;
            }

            if (this.hasFiles(e)) {
                this.dragCounter = 0;
                this.hideDropOverlay();

                const files = Array.from(e.dataTransfer.files);
                if (files.length > 0) {
                    await this.handleFileDrop(files);
                }
            }
        }, false);

        // Reset internal drag flag on dragend
        document.addEventListener('dragend', () => {
            this.isInternalDrag = false;
        }, false);
    }

    /**
     * Check if this is an internal drag event (like navigation reordering)
     * Internal drags are identified by draggable elements with data-draggable attribute
     */
    isInternalDragEvent(e) {
        // Check if we're already tracking an internal drag
        if (this.isInternalDrag) return true;

        // Check if the drag originated from a draggable element
        if (e.target && e.target.closest('[draggable="true"]')) {
            return true;
        }

        // Check dataTransfer types - internal drags won't have Files
        if (e.dataTransfer && e.dataTransfer.types) {
            // If it has Files type, it's an external file drag
            if (e.dataTransfer.types.includes('Files')) {
                return false;
            }
            // If it has other types but not Files, it's likely internal
            if (e.dataTransfer.types.length > 0 && !e.dataTransfer.types.includes('Files')) {
                return true;
            }
        }

        return false;
    }

    /**
     * Check if drag event contains files
     */
    hasFiles(e) {
        if (!e.dataTransfer) return false;

        // Check if dataTransfer has files
        if (e.dataTransfer.types) {
            return e.dataTransfer.types.includes('Files');
        }

        return false;
    }

    /**
     * Show the drop overlay
     */
    showDropOverlay() {
        if (this.dropOverlay) {
            this.dropOverlay.classList.add('visible');
        }
    }

    /**
     * Hide the drop overlay
     */
    hideDropOverlay() {
        if (this.dropOverlay) {
            this.dropOverlay.classList.remove('visible');
        }
    }

    /**
     * Handle dropped files
     */
    async handleFileDrop(files) {
        Logger.debug('Files dropped globally:', files.length);

        // Validate files
        const validFiles = [];
        const invalidFiles = [];

        files.forEach(file => {
            const ext = this.getFileExtension(file.name);
            if (this.allowedExtensions.includes(ext)) {
                validFiles.push(file);
            } else {
                invalidFiles.push({
                    name: file.name,
                    error: `Invalid file type: ${ext}`
                });
            }
        });

        // Show errors for invalid files
        if (invalidFiles.length > 0) {
            const errorMsg = `Invalid file types:\n${invalidFiles.map(f => `- ${f.name}`).join('\n')}\n\nSupported formats: ${this.allowedExtensions.join(', ')}`;
            this.showToast(errorMsg, 'error');
        }

        // Upload valid files
        if (validFiles.length > 0) {
            await this.uploadFiles(validFiles);
        }
    }

    /**
     * Get file extension (lowercase with dot)
     */
    getFileExtension(filename) {
        const lastDot = filename.lastIndexOf('.');
        if (lastDot === -1) return '';
        return filename.substring(lastDot).toLowerCase();
    }

    /**
     * Upload files to the server
     */
    async uploadFiles(files) {
        Logger.debug('Uploading files globally:', files.length);

        // Show upload overlay
        this.showUploadOverlay(files);

        // Create FormData
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        formData.append('is_business', 'false');

        try {
            // Upload files
            const response = await fetch(`${api.baseURL}/files/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail?.message || 'Upload failed');
            }

            const result = await response.json();
            Logger.debug('Upload result:', result);

            // Show success message
            if (result.success_count > 0) {
                this.showToast(
                    `Successfully uploaded ${result.success_count} file(s)`,
                    'success'
                );
            }

            // Show errors for failed uploads
            if (result.failed_files && result.failed_files.length > 0) {
                result.failed_files.forEach(failed => {
                    this.showToast(`Failed: ${failed.filename} - ${failed.error}`, 'error');
                });
            }

            // Refresh library if on library page
            if (window.libraryManager && window.currentPage === 'library') {
                await window.libraryManager.loadFiles();
                await window.libraryManager.loadStatistics();
            }

        } catch (error) {
            Logger.error('Upload error:', error);
            this.showToast(`Upload failed: ${error.message}`, 'error');
        } finally {
            this.hideUploadOverlay();
        }
    }

    /**
     * Show upload progress overlay
     */
    showUploadOverlay(files) {
        let overlay = document.getElementById('uploadOverlay');
        if (!overlay) {
            // Create overlay if it doesn't exist
            overlay = document.createElement('div');
            overlay.id = 'uploadOverlay';
            overlay.className = 'upload-overlay';
            overlay.innerHTML = `
                <div class="upload-content">
                    <div class="upload-header">
                        <h3>⬆️ Uploading Files</h3>
                    </div>
                    <div class="upload-files" id="uploadFilesList">
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
        }

        // Add file list
        const filesList = document.getElementById('uploadFilesList');
        filesList.innerHTML = files.map(file => `
            <div class="upload-file-item">
                <span class="upload-file-name">${escapeHtml(file.name)}</span>
                <span class="upload-file-size">${this.formatFileSize(file.size)}</span>
                <span class="upload-spinner">⏳</span>
            </div>
        `).join('');

        overlay.classList.add('visible');
    }

    /**
     * Hide upload progress overlay
     */
    hideUploadOverlay() {
        const overlay = document.getElementById('uploadOverlay');
        if (overlay) {
            overlay.classList.remove('visible');
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
            }, 300);
        }
    }

    /**
     * Format file size for display
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Use the global toast function if available
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            // Fallback to console
            Logger.debug(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

// Create global instance
const globalDragDropManager = new GlobalDragDropManager();

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.globalDragDropManager = globalDragDropManager;
}
