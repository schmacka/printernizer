/**
 * Navigation Preferences UI Manager
 * Handles the UI for customizing navigation bar sections
 */

class NavigationPreferencesUIManager {
    constructor() {
        this.draggedElement = null;
        this.draggedIndex = null;
    }

    /**
     * Initialize the navigation preferences UI
     */
    init() {
        this.renderNavigationSections();

        // Listen for preference changes
        window.addEventListener('navigationPreferencesChanged', () => {
            this.renderNavigationSections();
            this.updateNavigation();
        });
    }

    /**
     * Render the navigation sections list in settings
     */
    renderNavigationSections() {
        const container = document.getElementById('navigationSectionsList');
        if (!container) return;

        const sections = window.navigationPreferences.getPreferences();

        container.innerHTML = sections.map((section, index) => `
            <div class="navigation-section-item"
                 data-section-id="${sanitizeAttribute(section.id)}"
                 data-index="${index}"
                 draggable="true">
                <div class="navigation-section-handle" title="Ziehen zum Verschieben">
                    <span class="handle-icon">☰</span>
                </div>
                <div class="navigation-section-content">
                    <div class="navigation-section-icon">${section.icon}</div>
                    <div class="navigation-section-info">
                        <div class="navigation-section-label">${escapeHtml(section.label)}</div>
                        <div class="navigation-section-description">${escapeHtml(section.description)}</div>
                    </div>
                </div>
                <div class="navigation-section-controls">
                    <button class="btn-icon-small"
                            onclick="navigationPreferencesManager.moveSectionUp('${sanitizeAttribute(section.id)}')"
                            title="Nach oben"
                            ${index === 0 ? 'disabled' : ''}>
                        ⬆️
                    </button>
                    <button class="btn-icon-small"
                            onclick="navigationPreferencesManager.moveSectionDown('${sanitizeAttribute(section.id)}')"
                            title="Nach unten"
                            ${index === sections.length - 1 ? 'disabled' : ''}>
                        ⬇️
                    </button>
                    <label class="toggle-switch" title="${section.required ? 'Erforderliches Element kann nicht ausgeblendet werden' : 'Sichtbarkeit umschalten'}">
                        <input type="checkbox"
                               ${section.visible ? 'checked' : ''}
                               ${section.required ? 'disabled' : ''}
                               onchange="navigationPreferencesManager.toggleSectionVisibility('${sanitizeAttribute(section.id)}')">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
            </div>
        `).join('');

        // Setup drag and drop
        this.setupDragAndDrop();
    }

    /**
     * Setup drag and drop functionality
     */
    setupDragAndDrop() {
        const items = document.querySelectorAll('.navigation-section-item');

        items.forEach(item => {
            item.addEventListener('dragstart', (e) => this.handleDragStart(e));
            item.addEventListener('dragover', (e) => this.handleDragOver(e));
            item.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            item.addEventListener('drop', (e) => this.handleDrop(e));
            item.addEventListener('dragend', (e) => this.handleDragEnd(e));
        });
    }

    /**
     * Handle drag start
     */
    handleDragStart(e) {
        this.draggedElement = e.currentTarget;
        this.draggedIndex = parseInt(e.currentTarget.dataset.index);
        e.currentTarget.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.currentTarget.innerHTML);
    }

    /**
     * Handle drag over
     */
    handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        e.dataTransfer.dropEffect = 'move';

        const target = e.currentTarget;
        if (target !== this.draggedElement) {
            target.classList.add('drag-over');
        }

        return false;
    }

    /**
     * Handle drag leave
     */
    handleDragLeave(e) {
        const target = e.currentTarget;
        target.classList.remove('drag-over');
    }

    /**
     * Handle drop
     */
    handleDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }

        const target = e.currentTarget;
        const targetIndex = parseInt(target.dataset.index);

        if (this.draggedElement !== target && this.draggedIndex !== targetIndex) {
            // Reorder sections
            const sections = window.navigationPreferences.getPreferences();
            const newOrder = [...sections];

            // Remove dragged item
            const [draggedItem] = newOrder.splice(this.draggedIndex, 1);

            // Insert at new position
            newOrder.splice(targetIndex, 0, draggedItem);

            // Save new order
            const newOrderIds = newOrder.map(s => s.id);
            window.navigationPreferences.reorderSections(newOrderIds);
        }

        return false;
    }

    /**
     * Handle drag end
     */
    handleDragEnd(e) {
        e.currentTarget.classList.remove('dragging');

        // Remove drag-over class from all items
        document.querySelectorAll('.navigation-section-item').forEach(item => {
            item.classList.remove('drag-over');
        });
    }

    /**
     * Move section up
     */
    moveSectionUp(sectionId) {
        if (window.navigationPreferences.moveSectionUp(sectionId)) {
            this.showSuccess('Abschnitt nach oben verschoben');
        }
    }

    /**
     * Move section down
     */
    moveSectionDown(sectionId) {
        if (window.navigationPreferences.moveSectionDown(sectionId)) {
            this.showSuccess('Abschnitt nach unten verschoben');
        }
    }

    /**
     * Toggle section visibility
     */
    toggleSectionVisibility(sectionId) {
        if (window.navigationPreferences.toggleVisibility(sectionId)) {
            this.showSuccess('Sichtbarkeit aktualisiert');
        }
    }

    /**
     * Reset navigation preferences
     */
    resetNavigationPreferences() {
        if (confirm('Möchten Sie die Navigationsleiste auf die Standardeinstellungen zurücksetzen?')) {
            if (window.navigationPreferences.resetToDefaults()) {
                this.showSuccess('Navigation auf Standardeinstellungen zurückgesetzt');
            }
        }
    }

    /**
     * Update the actual navigation bar
     */
    updateNavigation() {
        const navMenu = document.querySelector('.nav-menu');
        if (!navMenu) return;

        const visibleSections = window.navigationPreferences.getVisibleSections();
        const currentPage = window.app?.currentPage || 'dashboard';

        // Close mobile menu if open
        const navToggle = document.getElementById('navToggle');
        if (navToggle) {
            navToggle.setAttribute('aria-expanded', 'false');
            navMenu.classList.remove('active');
        }

        // Clear existing nav links (but keep screen reader descriptions)
        const srOnly = navMenu.querySelector('.sr-only');
        navMenu.innerHTML = '';

        // Add sections in order
        visibleSections.forEach(section => {
            const link = document.createElement('a');
            link.href = `#${section.id}`;
            link.className = 'nav-link';
            link.setAttribute('data-page', section.id);
            link.setAttribute('role', 'button');
            link.setAttribute('aria-describedby', `nav-${section.id}-desc`);

            if (section.id === currentPage) {
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
            }

            const iconSpan = document.createElement('span');
            iconSpan.className = 'nav-icon';
            iconSpan.setAttribute('aria-hidden', 'true');
            iconSpan.textContent = section.icon;

            link.appendChild(iconSpan);
            link.appendChild(document.createTextNode('\n                    ' + section.label + '\n                '));

            navMenu.appendChild(link);
        });

        // Re-add screen reader descriptions if they exist
        if (srOnly) {
            navMenu.appendChild(srOnly);
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        if (window.showToast) {
            window.showToast('success', 'Navigation', message);
        } else {
            Logger.debug(message);
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        if (window.showToast) {
            window.showToast('error', 'Navigation', message);
        } else {
            Logger.error(message);
        }
    }
}

// Create global instance
window.navigationPreferencesManager = new NavigationPreferencesUIManager();

// Initialize when settings page loads
document.addEventListener('DOMContentLoaded', () => {
    window.navigationPreferencesManager.init();
});
