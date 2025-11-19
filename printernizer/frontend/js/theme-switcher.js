/**
 * Theme Switcher for Printernizer
 * Handles light/dark theme switching with localStorage persistence
 */

class ThemeSwitcher {
    constructor() {
        this.THEME_KEY = 'printernizer-theme';
        this.THEME_LIGHT = 'light';
        this.THEME_DARK = 'dark';

        // Initialize theme on page load
        this.init();
    }

    /**
     * Initialize theme system
     */
    init() {
        // Apply saved theme or detect system preference
        const savedTheme = this.getSavedTheme();
        const preferredTheme = savedTheme || this.detectSystemTheme();

        // Apply theme immediately (before page renders)
        this.applyTheme(preferredTheme, false);

        // Set up event listeners after DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }

        // Listen for system theme changes
        this.watchSystemTheme();
    }

    /**
     * Get saved theme from localStorage
     * @returns {string|null} Saved theme or null
     */
    getSavedTheme() {
        try {
            return localStorage.getItem(this.THEME_KEY);
        } catch (error) {
            Logger.warn('Could not access localStorage', error);
            return null;
        }
    }

    /**
     * Save theme to localStorage
     * @param {string} theme - Theme to save
     */
    saveTheme(theme) {
        try {
            localStorage.setItem(this.THEME_KEY, theme);
        } catch (error) {
            Logger.warn('Could not save theme to localStorage', error);
        }
    }

    /**
     * Detect system theme preference
     * @returns {string} 'light' or 'dark'
     */
    detectSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return this.THEME_DARK;
        }
        return this.THEME_LIGHT;
    }

    /**
     * Apply theme to document
     * @param {string} theme - Theme to apply
     * @param {boolean} animate - Whether to animate the transition
     */
    applyTheme(theme, animate = true) {
        const html = document.documentElement;

        // Disable transitions temporarily if not animating
        if (!animate) {
            html.classList.add('no-transition');
        }

        // Set theme attribute
        html.setAttribute('data-theme', theme);

        // Update toggle button if it exists
        this.updateToggleButton(theme);

        // Re-enable transitions after a frame
        if (!animate) {
            requestAnimationFrame(() => {
                html.classList.remove('no-transition');
            });
        }

        // Save theme preference
        this.saveTheme(theme);

        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChange', { detail: { theme } }));

        Logger.info(`Theme applied: ${theme}`);
    }

    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === this.THEME_DARK ? this.THEME_LIGHT : this.THEME_DARK;
        this.applyTheme(newTheme, true);
    }

    /**
     * Update toggle button UI
     * @param {string} theme - Current theme
     */
    updateToggleButton(theme) {
        const toggleBtn = document.getElementById('themeToggle');
        const toggleIcon = document.getElementById('themeIcon');
        const toggleText = document.getElementById('themeText');

        if (toggleBtn && toggleIcon) {
            if (theme === this.THEME_DARK) {
                toggleIcon.textContent = '☀️';
                if (toggleText) toggleText.textContent = 'Hell';
                toggleBtn.setAttribute('aria-label', 'Zum hellen Modus wechseln');
                toggleBtn.setAttribute('title', 'Zum hellen Modus wechseln');
            } else {
                toggleIcon.textContent = '🌙';
                if (toggleText) toggleText.textContent = 'Dunkel';
                toggleBtn.setAttribute('aria-label', 'Zum dunklen Modus wechseln');
                toggleBtn.setAttribute('title', 'Zum dunklen Modus wechseln');
            }
        }
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        const toggleBtn = document.getElementById('themeToggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleTheme());
            Logger.debug('Theme toggle button initialized');
        } else {
            Logger.warn('Theme toggle button not found in DOM');
        }
    }

    /**
     * Watch for system theme changes
     */
    watchSystemTheme() {
        if (window.matchMedia) {
            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');

            // Use modern API if available
            if (darkModeQuery.addEventListener) {
                darkModeQuery.addEventListener('change', (e) => {
                    // Only update if user hasn't manually set a preference
                    if (!this.getSavedTheme()) {
                        const newTheme = e.matches ? this.THEME_DARK : this.THEME_LIGHT;
                        this.applyTheme(newTheme, true);
                    }
                });
            } else {
                // Fallback for older browsers
                darkModeQuery.addListener((e) => {
                    if (!this.getSavedTheme()) {
                        const newTheme = e.matches ? this.THEME_DARK : this.THEME_LIGHT;
                        this.applyTheme(newTheme, true);
                    }
                });
            }
        }
    }

    /**
     * Get current theme
     * @returns {string} Current theme
     */
    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || this.THEME_LIGHT;
    }

    /**
     * Check if dark theme is active
     * @returns {boolean} True if dark theme is active
     */
    isDarkTheme() {
        return this.getCurrentTheme() === this.THEME_DARK;
    }

    /**
     * Set theme explicitly
     * @param {string} theme - Theme to set ('light' or 'dark')
     */
    setTheme(theme) {
        if (theme === this.THEME_LIGHT || theme === this.THEME_DARK) {
            this.applyTheme(theme, true);
        } else {
            Logger.warn(`Invalid theme: ${theme}. Use 'light' or 'dark'.`);
        }
    }
}

// Add CSS class for disabling transitions during initial load
const style = document.createElement('style');
style.textContent = `
    .no-transition,
    .no-transition * {
        transition: none !important;
    }
`;
document.head.appendChild(style);

// Initialize theme switcher
const themeSwitcher = new ThemeSwitcher();

// Expose to global scope for debugging and external access
window.themeSwitcher = themeSwitcher;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeSwitcher;
}
