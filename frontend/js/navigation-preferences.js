/**
 * Navigation Preferences Manager
 * Handles customization of navigation bar sections (order and visibility)
 */

class NavigationPreferences {
    constructor() {
        this.storageKey = 'printernizer-navigation-preferences';

        // Default navigation sections in their default order
        // Labels/descriptions are stored as i18n keys and resolved lazily via t()
        // at render time, because this array is evaluated before i18n.init() completes.
        this.defaultSections = [
            {
                id: 'dashboard',
                icon: '📊',
                labelKey: 'nav.dashboard',
                descriptionKey: 'navDescriptions.dashboard',
                visible: true,
                required: true // Cannot be hidden
            },
            {
                id: 'library',
                icon: '🗄️',
                labelKey: 'nav.library',
                descriptionKey: 'navDescriptions.library',
                visible: true,
                required: false
            },
            {
                id: 'printers',
                icon: '🖨️',
                labelKey: 'nav.printers',
                descriptionKey: 'navDescriptions.printers',
                visible: true,
                required: false
            },
            {
                id: 'jobs',
                icon: '⚙️',
                labelKey: 'nav.jobs',
                descriptionKey: 'navDescriptions.jobs',
                visible: true,
                required: false
            },
            {
                id: 'timelapses',
                icon: '🎬',
                labelKey: 'nav.timelapses',
                descriptionKey: 'navDescriptions.timelapses',
                visible: true,
                required: false
            },
            {
                id: 'files',
                icon: '📁',
                labelKey: 'nav.files',
                descriptionKey: 'navDescriptions.files',
                visible: true,
                required: false
            },
            {
                id: 'materials',
                icon: '🧵',
                labelKey: 'nav.materials',
                descriptionKey: 'navDescriptions.materials',
                visible: true,
                required: false
            },
            {
                id: 'ideas',
                icon: '💡',
                labelKey: 'nav.ideas',
                descriptionKey: 'navDescriptions.ideas',
                visible: true,
                required: false
            },
            {
                id: 'tools',
                icon: '🛠️',
                labelKey: 'nav.tools',
                descriptionKey: 'navDescriptions.tools',
                visible: true,
                required: false
            },
            {
                id: 'generator',
                icon: '🧩',
                labelKey: 'nav.generator',
                descriptionKey: 'navDescriptions.generator',
                visible: true,
                required: false
            },
            {
                id: 'settings',
                icon: '⚙️',
                labelKey: 'nav.settings',
                descriptionKey: 'navDescriptions.settings',
                visible: true,
                required: true // Cannot be hidden
            },
            {
                id: 'debug',
                icon: '🐛',
                labelKey: 'nav.debug',
                descriptionKey: 'navDescriptions.debug',
                visible: true,
                required: false
            }
        ];
    }

    /**
     * Get current navigation preferences (merged with defaults)
     */
    getPreferences() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (!stored) {
                return this.defaultSections;
            }

            const preferences = JSON.parse(stored);

            // Merge stored preferences with defaults to handle new sections
            const merged = this.defaultSections.map(defaultSection => {
                const storedSection = preferences.find(p => p.id === defaultSection.id);
                return storedSection ? { ...defaultSection, ...storedSection } : defaultSection;
            });

            // Add any stored sections that don't exist in defaults (for backwards compatibility)
            preferences.forEach(storedSection => {
                if (!merged.find(m => m.id === storedSection.id)) {
                    merged.push(storedSection);
                }
            });

            return merged;
        } catch (error) {
            Logger.error('Error loading navigation preferences:', error);
            return this.defaultSections;
        }
    }

    /**
     * Save navigation preferences
     */
    savePreferences(preferences) {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(preferences));

            // Dispatch custom event for other components to react
            window.dispatchEvent(new CustomEvent('navigationPreferencesChanged', {
                detail: { preferences }
            }));

            return true;
        } catch (error) {
            Logger.error('Error saving navigation preferences:', error);
            return false;
        }
    }

    /**
     * Reset to default preferences
     */
    resetToDefaults() {
        try {
            localStorage.removeItem(this.storageKey);

            // Dispatch custom event
            window.dispatchEvent(new CustomEvent('navigationPreferencesChanged', {
                detail: { preferences: this.defaultSections }
            }));

            return true;
        } catch (error) {
            Logger.error('Error resetting navigation preferences:', error);
            return false;
        }
    }

    /**
     * Get visible sections in the correct order
     */
    getVisibleSections() {
        return this.getPreferences().filter(section => section.visible);
    }

    /**
     * Toggle visibility of a section
     */
    toggleVisibility(sectionId) {
        const preferences = this.getPreferences();
        const section = preferences.find(s => s.id === sectionId);

        if (!section) {
            Logger.error('Section not found:', sectionId);
            return false;
        }

        if (section.required) {
            Logger.warn('Cannot hide required section:', sectionId);
            return false;
        }

        section.visible = !section.visible;
        return this.savePreferences(preferences);
    }

    /**
     * Reorder sections
     */
    reorderSections(newOrder) {
        const preferences = this.getPreferences();
        const reordered = [];

        // Build new array based on newOrder (array of IDs)
        newOrder.forEach(id => {
            const section = preferences.find(s => s.id === id);
            if (section) {
                reordered.push(section);
            }
        });

        // Add any sections not in newOrder (shouldn't happen, but safety check)
        preferences.forEach(section => {
            if (!reordered.find(s => s.id === section.id)) {
                reordered.push(section);
            }
        });

        return this.savePreferences(reordered);
    }

    /**
     * Move a section up in the order
     */
    moveSectionUp(sectionId) {
        const preferences = this.getPreferences();
        const index = preferences.findIndex(s => s.id === sectionId);

        if (index <= 0) {
            return false; // Already at the top or not found
        }

        // Swap with previous section
        [preferences[index - 1], preferences[index]] = [preferences[index], preferences[index - 1]];

        return this.savePreferences(preferences);
    }

    /**
     * Move a section down in the order
     */
    moveSectionDown(sectionId) {
        const preferences = this.getPreferences();
        const index = preferences.findIndex(s => s.id === sectionId);

        if (index < 0 || index >= preferences.length - 1) {
            return false; // Already at the bottom or not found
        }

        // Swap with next section
        [preferences[index], preferences[index + 1]] = [preferences[index + 1], preferences[index]];

        return this.savePreferences(preferences);
    }
}

// Create global instance
window.navigationPreferences = new NavigationPreferences();
