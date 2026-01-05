/**
 * File Tags Management
 * Handles tag display, picker UI, and tag operations
 */

class TagsManager {
    constructor() {
        this.allTags = [];
        this.isInitialized = false;
    }

    /**
     * Initialize tags manager - load all available tags
     */
    async initialize() {
        if (this.isInitialized) return;

        try {
            await this.loadAllTags();
            this.isInitialized = true;
            Logger.info('Tags manager initialized', { tagCount: this.allTags.length });
        } catch (error) {
            Logger.error('Failed to initialize tags manager', error);
        }
    }

    /**
     * Load all available tags from the API
     */
    async loadAllTags() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/tags?sort_by=name&sort_order=asc`);
            if (!response.ok) throw new Error('Failed to fetch tags');

            const data = await response.json();
            this.allTags = data.tags || [];
        } catch (error) {
            Logger.error('Failed to load tags', error);
            this.allTags = [];
        }
    }

    /**
     * Get tags for a specific file
     * @param {string} fileChecksum - File checksum
     * @returns {Promise<Array>} Array of tags
     */
    async getFileTags(fileChecksum) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/tags/file/${fileChecksum}`);
            if (!response.ok) return [];

            const data = await response.json();
            return data.tags || [];
        } catch (error) {
            Logger.error('Failed to get file tags', { fileChecksum, error });
            return [];
        }
    }

    /**
     * Render tags display for a file card (compact view)
     * @param {Array} tags - Array of tag objects
     * @returns {string} HTML string
     */
    renderTagsCompact(tags) {
        if (!tags || tags.length === 0) return '';

        const displayTags = tags.slice(0, 3);
        const moreCount = tags.length - 3;

        return `
            <div class="file-tags-compact">
                ${displayTags.map(tag => `
                    <span class="tag-badge" style="background-color: ${tag.color}20; border-color: ${tag.color}; color: ${tag.color}">
                        ${escapeHtml(tag.name)}
                    </span>
                `).join('')}
                ${moreCount > 0 ? `<span class="tag-more">+${moreCount}</span>` : ''}
            </div>
        `;
    }

    /**
     * Render full tags section with edit capability
     * @param {string} fileChecksum - File checksum
     * @param {Array} tags - Array of tag objects
     * @returns {string} HTML string
     */
    renderTagsSection(fileChecksum, tags) {
        return `
            <div class="tags-section" data-file-checksum="${fileChecksum}">
                <div class="tags-header">
                    <span class="tags-label">Tags</span>
                    <button class="btn-icon btn-edit-tags" onclick="window.tagsManager.openTagPicker('${fileChecksum}')" title="Edit tags">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
                <div class="tags-list">
                    ${tags && tags.length > 0 ? tags.map(tag => `
                        <span class="tag-badge tag-removable"
                              style="background-color: ${tag.color}20; border-color: ${tag.color}; color: ${tag.color}"
                              data-tag-id="${tag.id}"
                              onclick="window.tagsManager.removeTagFromFile('${fileChecksum}', '${tag.id}')">
                            ${escapeHtml(tag.name)}
                            <span class="tag-remove">×</span>
                        </span>
                    `).join('') : '<span class="no-tags">No tags</span>'}
                </div>
            </div>
        `;
    }

    /**
     * Open the tag picker modal
     * @param {string} fileChecksum - File checksum to edit tags for
     */
    async openTagPicker(fileChecksum) {
        await this.initialize();

        const fileTags = await this.getFileTags(fileChecksum);
        const fileTagIds = new Set(fileTags.map(t => t.id));

        const modal = document.createElement('div');
        modal.className = 'modal-overlay tag-picker-modal';
        modal.id = 'tagPickerModal';
        modal.innerHTML = `
            <div class="modal-content tag-picker-content">
                <div class="modal-header">
                    <h3>Manage Tags</h3>
                    <button class="btn-close" onclick="window.tagsManager.closeTagPicker()">×</button>
                </div>
                <div class="modal-body">
                    <div class="tag-picker-search">
                        <input type="text" id="tagSearchInput" placeholder="Search or create tag..." class="form-control">
                    </div>
                    <div class="tag-picker-list">
                        ${this.allTags.map(tag => `
                            <label class="tag-picker-item ${fileTagIds.has(tag.id) ? 'selected' : ''}" data-tag-id="${tag.id}">
                                <input type="checkbox" ${fileTagIds.has(tag.id) ? 'checked' : ''}
                                       onchange="window.tagsManager.toggleTag('${fileChecksum}', '${tag.id}', this.checked)">
                                <span class="tag-color" style="background-color: ${tag.color}"></span>
                                <span class="tag-name">${escapeHtml(tag.name)}</span>
                                <span class="tag-count">${tag.usage_count}</span>
                            </label>
                        `).join('')}
                    </div>
                    <div class="tag-picker-create">
                        <button class="btn btn-secondary btn-sm" id="createTagBtn" onclick="window.tagsManager.showCreateTagForm()">
                            <i class="fas fa-plus"></i> Create New Tag
                        </button>
                    </div>
                    <div class="tag-create-form" id="tagCreateForm" style="display: none;">
                        <input type="text" id="newTagName" placeholder="Tag name" class="form-control" maxlength="50">
                        <input type="color" id="newTagColor" value="#6b7280" class="color-picker">
                        <button class="btn btn-primary btn-sm" onclick="window.tagsManager.createTag('${fileChecksum}')">Add</button>
                        <button class="btn btn-secondary btn-sm" onclick="window.tagsManager.hideCreateTagForm()">Cancel</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Setup search filter
        const searchInput = modal.querySelector('#tagSearchInput');
        searchInput.addEventListener('input', (e) => this.filterTagList(e.target.value));

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeTagPicker();
        });
    }

    /**
     * Close the tag picker modal
     */
    closeTagPicker() {
        const modal = document.getElementById('tagPickerModal');
        if (modal) {
            modal.remove();
            // Refresh the library view to show updated tags
            if (window.libraryManager) {
                window.libraryManager.loadFiles();
            }
        }
    }

    /**
     * Filter tag list in picker
     * @param {string} query - Search query
     */
    filterTagList(query) {
        const items = document.querySelectorAll('.tag-picker-item');
        const lowerQuery = query.toLowerCase();

        items.forEach(item => {
            const name = item.querySelector('.tag-name').textContent.toLowerCase();
            item.style.display = name.includes(lowerQuery) ? '' : 'none';
        });
    }

    /**
     * Toggle a tag on/off for a file
     * @param {string} fileChecksum - File checksum
     * @param {string} tagId - Tag ID
     * @param {boolean} isChecked - Whether to add or remove
     */
    async toggleTag(fileChecksum, tagId, isChecked) {
        try {
            const endpoint = isChecked ? 'assign' : 'remove';
            const response = await fetch(`${CONFIG.API_BASE_URL}/tags/file/${fileChecksum}/${endpoint}?tag_ids=${tagId}`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error(`Failed to ${endpoint} tag`);

            // Update visual state
            const item = document.querySelector(`.tag-picker-item[data-tag-id="${tagId}"]`);
            if (item) {
                item.classList.toggle('selected', isChecked);
            }

            showToast('success', isChecked ? 'Tag Added' : 'Tag Removed', '', 2000);
        } catch (error) {
            Logger.error('Failed to toggle tag', { fileChecksum, tagId, error });
            showToast('error', 'Error', 'Failed to update tag');
        }
    }

    /**
     * Remove a tag from a file (from file detail view)
     * @param {string} fileChecksum - File checksum
     * @param {string} tagId - Tag ID
     */
    async removeTagFromFile(fileChecksum, tagId) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/tags/file/${fileChecksum}/remove?tag_ids=${tagId}`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to remove tag');

            // Remove tag badge from UI
            const badge = document.querySelector(`.tags-section[data-file-checksum="${fileChecksum}"] .tag-badge[data-tag-id="${tagId}"]`);
            if (badge) {
                badge.remove();
            }

            // Check if any tags remaining
            const section = document.querySelector(`.tags-section[data-file-checksum="${fileChecksum}"] .tags-list`);
            if (section && section.querySelectorAll('.tag-badge').length === 0) {
                section.innerHTML = '<span class="no-tags">No tags</span>';
            }

            showToast('success', 'Tag Removed', '', 2000);
        } catch (error) {
            Logger.error('Failed to remove tag', { fileChecksum, tagId, error });
            showToast('error', 'Error', 'Failed to remove tag');
        }
    }

    /**
     * Show create tag form
     */
    showCreateTagForm() {
        const form = document.getElementById('tagCreateForm');
        const btn = document.getElementById('createTagBtn');
        if (form) form.style.display = 'flex';
        if (btn) btn.style.display = 'none';
    }

    /**
     * Hide create tag form
     */
    hideCreateTagForm() {
        const form = document.getElementById('tagCreateForm');
        const btn = document.getElementById('createTagBtn');
        if (form) {
            form.style.display = 'none';
            document.getElementById('newTagName').value = '';
        }
        if (btn) btn.style.display = '';
    }

    /**
     * Create a new tag and optionally assign to file
     * @param {string} fileChecksum - Optional file to assign to
     */
    async createTag(fileChecksum) {
        const nameInput = document.getElementById('newTagName');
        const colorInput = document.getElementById('newTagColor');

        const name = nameInput?.value?.trim();
        const color = colorInput?.value || '#6b7280';

        if (!name) {
            showToast('warning', 'Missing Name', 'Please enter a tag name');
            return;
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/tags`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, color })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create tag');
            }

            const newTag = await response.json();
            this.allTags.push(newTag);

            // Optionally assign to current file
            if (fileChecksum) {
                await this.toggleTag(fileChecksum, newTag.id, true);
            }

            // Refresh picker
            this.closeTagPicker();
            this.openTagPicker(fileChecksum);

            showToast('success', 'Tag Created', `Created tag "${name}"`);
        } catch (error) {
            Logger.error('Failed to create tag', error);
            showToast('error', 'Error', error.message || 'Failed to create tag');
        }
    }

    /**
     * Render tag filter dropdown for library
     * @returns {string} HTML string
     */
    renderTagFilter() {
        if (this.allTags.length === 0) return '';

        return `
            <select id="filterTag" class="form-control filter-select">
                <option value="">All Tags</option>
                ${this.allTags.map(tag => `
                    <option value="${tag.id}" style="color: ${tag.color}">
                        ${escapeHtml(tag.name)} (${tag.usage_count})
                    </option>
                `).join('')}
            </select>
        `;
    }
}

// Create global instance
window.tagsManager = new TagsManager();
