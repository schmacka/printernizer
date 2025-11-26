/**
 * Navigation Preferences Manager
 * Handles customization of navigation bar sections (order and visibility)
 */

class NavigationPreferences {
    constructor() {
        this.storageKey = 'printernizer-navigation-preferences';

        // Default navigation sections in their default order
        this.defaultSections = [
            {
                id: 'dashboard',
                icon: '📊',
                label: 'Dashboard',
                description: 'Übersichtsseite mit Druckerstatus und aktuellen Aufträgen',
                visible: true,
                required: true // Cannot be hidden
            },
            {
                id: 'library',
                icon: '🗄️',
                label: 'Bibliothek',
                description: 'Zentrale Bibliothek für alle 3D-Dateien mit Metadaten',
                visible: true,
                required: false
            },
            {
                id: 'printers',
                icon: '🖨️',
                label: 'Drucker',
                description: 'Verwaltung und Konfiguration der 3D-Drucker',
                visible: true,
                required: false
            },
            {
                id: 'jobs',
                icon: '⚙️',
                label: 'Aufträge',
                description: 'Übersicht und Verwaltung der Druckaufträge',
                visible: true,
                required: false
            },
            {
                id: 'timelapses',
                icon: '🎬',
                label: 'Zeitraffer',
                description: 'Zeitraffer-Videos von Druckaufträgen',
                visible: true,
                required: false
            },
            {
                id: 'files',
                icon: '📁',
                label: 'Dateien',
                description: 'Dateiverwaltung und Downloads von den Druckern',
                visible: true,
                required: false
            },
            {
                id: 'materials',
                icon: '🧵',
                label: 'Filamente',
                description: 'Filament-Verwaltung und Bestandsübersicht',
                visible: true,
                required: false
            },
            {
                id: 'ideas',
                icon: '💡',
                label: 'Ideen',
                description: 'Ideenverwaltung, Lesezeichen und Modell-Entdeckung',
                visible: true,
                required: false
            },
            {
                id: 'settings',
                icon: '⚙️',
                label: 'Einstellungen',
                description: 'Anwendungseinstellungen und Konfiguration',
                visible: true,
                required: true // Cannot be hidden
            },
            {
                id: 'debug',
                icon: '🐛',
                label: 'Debug',
                description: 'Debug-Informationen und Systemprotokolle',
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
