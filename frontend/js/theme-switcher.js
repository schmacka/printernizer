/**
 * Theme Switcher for Printernizer
 * Handles multi-theme switching with localStorage persistence
 */

class ThemeSwitcher {
    constructor() {
        this.THEME_KEY = 'printernizer-theme';

        // Available themes with metadata
        this.THEMES = [
            {
                id: 'light',
                name: 'Classic Light',
                description: 'Clean, professional light theme',
                icon: '☀️',
                isDark: false
            },
            {
                id: 'dark',
                name: 'Classic Dark',
                description: 'Easy on the eyes dark theme',
                icon: '🌙',
                isDark: true
            },
            {
                id: 'industrial',
                name: 'Industrial',
                description: 'Workshop vibe with yellow accents',
                icon: '🏭',
                isDark: true
            },
            {
                id: 'refined',
                name: 'Refined',
                description: 'Elegant, minimal aesthetic',
                icon: '✨',
                isDark: false
            },
            {
                id: 'soft',
                name: 'Soft',
                description: 'Friendly pastel gradients',
                icon: '🌸',
                isDark: false
            },
            {
                id: 'brutalist',
                name: 'Brutalist',
                description: 'Bold, raw typography',
                icon: '🔲',
                isDark: false
            },
            {
                id: 'retro',
                name: 'Retro-Futuristic',
                description: 'Cyberpunk neon aesthetic',
                icon: '🎮',
                isDark: true
            }
        ];

        this.DEFAULT_THEME = 'light';

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

        // Validate theme exists
        const validTheme = this.isValidTheme(preferredTheme) ? preferredTheme : this.DEFAULT_THEME;

        // Apply theme immediately (before page renders)
        this.applyTheme(validTheme, false);

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
     * Check if a theme ID is valid
     * @param {string} themeId - Theme ID to check
     * @returns {boolean} True if valid
     */
    isValidTheme(themeId) {
        return this.THEMES.some(t => t.id === themeId);
    }

    /**
     * Get theme metadata by ID
     * @param {string} themeId - Theme ID
     * @returns {object|null} Theme object or null
     */
    getTheme(themeId) {
        return this.THEMES.find(t => t.id === themeId) || null;
    }

    /**
     * Get all available themes
     * @returns {array} Array of theme objects
     */
    getThemeList() {
        return [...this.THEMES];
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
            return 'dark';
        }
        return 'light';
    }

    /**
     * Apply theme to document
     * @param {string} themeId - Theme ID to apply
     * @param {boolean} animate - Whether to animate the transition
     */
    applyTheme(themeId, animate = true) {
        // Validate theme
        if (!this.isValidTheme(themeId)) {
            Logger.warn(`Invalid theme: ${themeId}. Using default.`);
            themeId = this.DEFAULT_THEME;
        }

        const html = document.documentElement;
        const theme = this.getTheme(themeId);

        // Disable transitions temporarily if not animating
        if (!animate) {
            html.classList.add('no-transition');
        }

        // Set theme attribute
        html.setAttribute('data-theme', themeId);

        // Also set dark/light mode class for components that need it
        if (theme.isDark) {
            html.classList.add('dark-mode');
            html.classList.remove('light-mode');
        } else {
            html.classList.add('light-mode');
            html.classList.remove('dark-mode');
        }

        // Update toggle button if it exists
        this.updateToggleButton(themeId);

        // Re-enable transitions after a frame
        if (!animate) {
            requestAnimationFrame(() => {
                html.classList.remove('no-transition');
            });
        }

        // Save theme preference
        this.saveTheme(themeId);

        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChange', {
            detail: {
                theme: themeId,
                themeData: theme
            }
        }));

        Logger.info(`Theme applied: ${theme.name} (${themeId})`);
    }

    /**
     * Cycle to next theme in list
     */
    cycleTheme() {
        const currentTheme = this.getCurrentTheme();
        const currentIndex = this.THEMES.findIndex(t => t.id === currentTheme);
        const nextIndex = (currentIndex + 1) % this.THEMES.length;
        this.applyTheme(this.THEMES[nextIndex].id, true);
    }

    /**
     * Toggle between light and dark themes (legacy support)
     */
    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const theme = this.getTheme(currentTheme);

        // If current theme is dark, switch to light; otherwise switch to dark
        if (theme && theme.isDark) {
            this.applyTheme('light', true);
        } else {
            this.applyTheme('dark', true);
        }
    }

    /**
     * Update toggle button UI
     * @param {string} themeId - Current theme ID
     */
    updateToggleButton(themeId) {
        const toggleBtn = document.getElementById('themeToggle');
        const toggleIcon = document.getElementById('themeIcon');
        const toggleText = document.getElementById('themeText');

        const theme = this.getTheme(themeId);
        if (!theme) return;

        if (toggleBtn && toggleIcon) {
            toggleIcon.textContent = theme.icon;

            if (toggleText) {
                toggleText.textContent = theme.name;
            }

            toggleBtn.setAttribute('aria-label', `Current theme: ${theme.name}. Click to change.`);
            toggleBtn.setAttribute('title', `Theme: ${theme.name}`);
        }
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        const toggleBtn = document.getElementById('themeToggle');
        if (toggleBtn) {
            // Click cycles through themes
            toggleBtn.addEventListener('click', (e) => {
                // If Shift is held, open theme picker (if exists)
                if (e.shiftKey) {
                    this.openThemePicker();
                } else {
                    this.cycleTheme();
                }
            });
            Logger.debug('Theme toggle button initialized');
        } else {
            Logger.warn('Theme toggle button not found in DOM');
        }
    }

    /**
     * Open theme picker modal/dropdown
     */
    openThemePicker() {
        // Dispatch event for settings page or modal to handle
        window.dispatchEvent(new CustomEvent('openThemePicker'));
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
                    // or if they're using a classic light/dark theme
                    const savedTheme = this.getSavedTheme();
                    if (!savedTheme || savedTheme === 'light' || savedTheme === 'dark') {
                        const newTheme = e.matches ? 'dark' : 'light';
                        this.applyTheme(newTheme, true);
                    }
                });
            } else {
                // Fallback for older browsers
                darkModeQuery.addListener((e) => {
                    const savedTheme = this.getSavedTheme();
                    if (!savedTheme || savedTheme === 'light' || savedTheme === 'dark') {
                        const newTheme = e.matches ? 'dark' : 'light';
                        this.applyTheme(newTheme, true);
                    }
                });
            }
        }
    }

    /**
     * Get current theme ID
     * @returns {string} Current theme ID
     */
    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || this.DEFAULT_THEME;
    }

    /**
     * Get current theme data
     * @returns {object} Current theme object
     */
    getCurrentThemeData() {
        return this.getTheme(this.getCurrentTheme());
    }

    /**
     * Check if dark theme is active
     * @returns {boolean} True if current theme is dark
     */
    isDarkTheme() {
        const theme = this.getCurrentThemeData();
        return theme ? theme.isDark : false;
    }

    /**
     * Set theme explicitly
     * @param {string} themeId - Theme ID to set
     */
    setTheme(themeId) {
        if (this.isValidTheme(themeId)) {
            this.applyTheme(themeId, true);
        } else {
            Logger.warn(`Invalid theme: ${themeId}. Available themes: ${this.THEMES.map(t => t.id).join(', ')}`);
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
