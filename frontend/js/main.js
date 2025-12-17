/**
 * Printernizer Main Application
 * Handles page routing, navigation, and application initialization
 */

const AVAILABLE_PAGES = [
    'dashboard',
    'printers',
    'jobs',
    'timelapses',
    'files',
    'library',
    'materials',
    'ideas',
    'settings',
    'debug'
];

// Main application class
class PrinternizerApp {
    constructor() {
        this.availablePages = AVAILABLE_PAGES;
        this.entryPath = window.__ENTRY_PATH__ || window.location.pathname;
        this.currentPage = this.resolveInitialPage();
        this.pageManagers = {
            dashboard: typeof dashboard !== 'undefined' ? dashboard : null,
            printers: typeof printerManager !== 'undefined' ? printerManager : null,
            jobs: typeof jobManager !== 'undefined' ? jobManager : null,
            timelapses: typeof timelapseManager !== 'undefined' ? timelapseManager : null,
            files: typeof fileManager !== 'undefined' ? fileManager : null,
            library: typeof libraryManager !== 'undefined' ? libraryManager : null,
            materials: typeof materialsManager !== 'undefined' ? materialsManager : null,
            ideas: typeof initializeIdeas !== 'undefined' ? { init: initializeIdeas } : null,
            settings: typeof settingsManager !== 'undefined' ? settingsManager : null,
            debug: typeof debugManager !== 'undefined' ? debugManager : null
        };
    }

    /**
     * Initialize the application
     */
    init() {
        Logger.debug('Initializing Printernizer application');

        // Apply navigation preferences
        if (window.navigationPreferencesManager) {
            window.navigationPreferencesManager.updateNavigation();
        }

        // Setup navigation
        this.setupNavigation();

        // Initialize global drag and drop
        if (window.globalDragDropManager) {
            window.globalDragDropManager.init();
        }

        // Initialize current page without creating duplicate history entries
        this.showPage(this.currentPage, false);

        // Setup global error handling
        this.setupErrorHandling();

        // Check initial connection
        this.checkSystemHealth();

        // Check if setup wizard should be shown
        this.checkSetupWizard();

        Logger.debug('Printernizer application initialized');
    }

    /**
     * Check if setup wizard should be shown
     */
    async checkSetupWizard() {
        try {
            if (window.setupWizard) {
                const shown = await window.setupWizard.checkAndShow();
                if (shown) {
                    Logger.info('Setup wizard displayed');
                }
            }
        } catch (error) {
            Logger.error('Failed to check setup wizard status:', error);
            // Don't block app initialization on wizard check failure
        }
    }

    /**
     * Setup navigation event handlers
     */
    setupNavigation() {
        // Handle hamburger menu toggle
        const navToggle = document.getElementById('navToggle');
        const navMenu = document.querySelector('.nav-menu');

        if (navToggle && navMenu) {
            navToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
                navToggle.setAttribute('aria-expanded', !isExpanded);
                navMenu.classList.toggle('active');
            });

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
                    navToggle.setAttribute('aria-expanded', 'false');
                    navMenu.classList.remove('active');
                }
            });

            // Close menu when clicking a nav link (mobile)
            navMenu.addEventListener('click', (e) => {
                if (e.target.classList.contains('nav-link')) {
                    navToggle.setAttribute('aria-expanded', 'false');
                    navMenu.classList.remove('active');
                }
            });
        }

        // Handle navigation clicks
        document.addEventListener('click', (e) => {
            const navLink = e.target.closest('.nav-link[data-page]');
            if (navLink) {
                e.preventDefault();
                const page = navLink.getAttribute('data-page');
                this.showPage(page);
            }
        });

        // Handle back/forward browser navigation
        window.addEventListener('popstate', (e) => {
            const page = this.isValidPage(e.state?.page) ? e.state.page : this.resolveInitialPage();
            this.showPage(page, false);
        });

        // Handle hash changes (for direct navigation and E2E tests)
        window.addEventListener('hashchange', () => {
            const newHash = window.location.hash.slice(1);
            if (this.isValidPage(newHash) && newHash !== this.currentPage) {
                this.showPage(newHash, false);
            }
        });

        this.updateHistoryState(this.currentPage, 'replace');
    }

    /**
     * Show specific page
     */
    showPage(pageName, updateHistory = true) {
        if (!this.isValidPage(pageName)) {
            Logger.error('Invalid page name:', pageName);
            return;
        }
        
        // Clean up current page manager
        const currentManager = this.pageManagers[this.currentPage];
        if (currentManager && typeof currentManager.cleanup === 'function') {
            currentManager.cleanup();
        }
        
        // Hide all pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Show selected page
        // Try page-prefixed ID first (for E2E test compatibility), then fall back to pageName
        let pageElement = document.getElementById(`page-${pageName}`);
        if (!pageElement) {
            pageElement = document.getElementById(pageName);
        }
        const navElement = document.querySelector(`[data-page="${pageName}"]`);
        
        if (pageElement) {
            pageElement.classList.add('active');
        } else {
            Logger.error(`Could not find page element for: ${pageName}`);
        }
        
        if (navElement) {
            navElement.classList.add('active');
        }
        
        // Update current page
        this.currentPage = pageName;
        window.currentPage = pageName; // Global reference for other modules
        
        // Update browser history
        if (updateHistory) {
            this.updateHistoryState(pageName, 'push');
        }
        
        // Initialize new page manager
        const newManager = this.pageManagers[pageName];
        if (newManager && typeof newManager.init === 'function') {
            // Small delay to allow DOM updates
            setTimeout(() => {
                newManager.init();
            }, 50);
        } else if (!newManager) {
            Logger.warn(`Page manager for '${pageName}' not found or not loaded yet`);
            // Try to get manager from global scope
            const globalManagerName = pageName === 'settings' ? 'settingsManager' : 
                                    pageName === 'debug' ? 'debugManager' : null;
            if (globalManagerName && typeof window[globalManagerName] !== 'undefined') {
                this.pageManagers[pageName] = window[globalManagerName];
                if (typeof window[globalManagerName].init === 'function') {
                    setTimeout(() => {
                        window[globalManagerName].init();
                    }, 50);
                }
            }
        }
        
        Logger.debug(`Navigated to page: ${pageName}`);
    }

    /**
     * Setup global error handling
     */
    setupErrorHandling() {
        // Handle uncaught errors
        window.addEventListener('error', (e) => {
            Logger.error('Global error:', e.error);
            showToast('error', 'Anwendungsfehler', 'Ein unerwarteter Fehler ist aufgetreten');
        });
        
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (e) => {
            Logger.error('Unhandled promise rejection:', e.reason);
            showToast('error', 'Anwendungsfehler', 'Ein unerwarteter Fehler ist aufgetreten');
        });
    }

    /**
     * Check system health on startup
     */
    async checkSystemHealth() {
        try {
            const health = await api.getHealth();
            Logger.debug('System health check:', health);

            if (health.status === 'healthy') {
                Logger.debug('System is healthy');
                // Store backend status globally for other components
                window.printernizer = window.printernizer || {};
                window.printernizer.backendHealthy = true;
            } else {
                window.printernizer = window.printernizer || {};
                window.printernizer.backendHealthy = false;
                showToast('warning', 'System-Warnung', 'System ist möglicherweise nicht voll funktionsfähig', CONFIG.TOAST_DURATION, {
                    uniqueKey: CONFIG.NOTIFICATION_KEYS.SYSTEM_WARNING,
                    deduplicateMode: 'update'
                });
            }
        } catch (error) {
            Logger.error('Health check failed:', error);
            window.printernizer = window.printernizer || {};
            window.printernizer.backendHealthy = false;
            showToast('error', 'Verbindungsfehler', 'Backend-Server ist nicht erreichbar', CONFIG.TOAST_DURATION, {
                uniqueKey: CONFIG.NOTIFICATION_KEYS.BACKEND_OFFLINE,
                deduplicateMode: 'update'
            });
        }
    }

    /**
     * Show loading state for entire application
     */
    setGlobalLoading(loading = true) {
        if (loading) {
            document.body.classList.add('app-loading');
        } else {
            document.body.classList.remove('app-loading');
        }
    }

    isValidPage(pageName) {
        return typeof pageName === 'string' && this.availablePages.includes(pageName);
    }

    resolveInitialPage() {
        const coercedInitial = typeof window.__INITIAL_PAGE__ === 'string'
            ? window.__INITIAL_PAGE__.trim()
            : null;
        if (this.isValidPage(coercedInitial)) {
            return coercedInitial;
        }

        const hashPage = window.location.hash.slice(1);
        if (this.isValidPage(hashPage)) {
            return hashPage;
        }

        const pathPage = this.getPageFromPath(window.location.pathname);
        if (this.isValidPage(pathPage)) {
            return pathPage;
        }

        return 'dashboard';
    }

    getPageFromPath(pathname = '') {
        if (!pathname) {
            return null;
        }
        const segments = pathname.split('/').filter(Boolean);
        if (!segments.length) {
            return null;
        }
        const lastSegment = segments[segments.length - 1];
        if (!lastSegment || lastSegment === 'index.html') {
            return null;
        }
        const cleanSegment = lastSegment.endsWith('.html')
            ? lastSegment.replace('.html', '')
            : lastSegment;
        return cleanSegment;
    }

    updateHistoryState(page, mode = 'push') {
        const basePath = (this.entryPath || window.location.pathname || '/').split('#')[0] || '/';
        const url = `${basePath}#${page}`;
        const state = { page };

        if (mode === 'replace') {
            history.replaceState(state, '', url);
        } else {
            history.pushState(state, '', url);
        }
    }
}

/**
 * Global Application Functions
 */

/**
 * Show specific page (global function)
 */
function showPage(pageName) {
    app.showPage(pageName);
}

/**
 * Refresh current page
 */
function refreshCurrentPage() {
    const currentManager = app.pageManagers[app.currentPage];
    if (currentManager) {
        // Call appropriate refresh method based on page
        switch (app.currentPage) {
            case 'dashboard':
                if (typeof refreshDashboard === 'function') refreshDashboard();
                break;
            case 'printers':
                if (typeof refreshPrinters === 'function') refreshPrinters();
                break;
            case 'jobs':
                if (typeof refreshJobs === 'function') refreshJobs();
                break;
            case 'timelapses':
                if (typeof refreshTimelapses === 'function') refreshTimelapses();
                break;
            case 'files':
                if (typeof refreshFiles === 'function') refreshFiles();
                break;
            case 'settings':
                if (typeof loadSettings === 'function') loadSettings();
                break;
            case 'debug':
                if (typeof refreshDebugInfo === 'function') refreshDebugInfo();
                break;
        }
    }
}

/**
 * Handle keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + R: Refresh current page
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            refreshCurrentPage();
        }
        
        // Alt + 1-4: Navigate to pages
        if (e.altKey) {
            switch (e.key) {
                case '1':
                    e.preventDefault();
                    showPage('dashboard');
                    break;
                case '2':
                    e.preventDefault();
                    showPage('printers');
                    break;
                case '3':
                    e.preventDefault();
                    showPage('jobs');
                    break;
                case '4':
                    e.preventDefault();
                    showPage('files');
                    break;
                case '5':
                    e.preventDefault();
                    showPage('settings');
                    break;
                case '6':
                    e.preventDefault();
                    showPage('debug');
                    break;
            }
        }
    });
}

/**
 * Application initialization
 */
document.addEventListener('DOMContentLoaded', () => {
    Logger.debug('DOM loaded, initializing application...');

    // Create global app instance
    window.app = new PrinternizerApp();

    // Initialize application
    app.init();

    // Setup keyboard shortcuts
    setupKeyboardShortcuts();

    // Load version after app initialization (with delay to ensure DOM is ready)
    setTimeout(() => {
        Logger.debug('[Main] Loading app version after initialization');
        if (typeof loadAppVersion === 'function') {
            loadAppVersion();
        } else {
            Logger.error('[Main] loadAppVersion function not found');
        }
    }, 500);

    // Show welcome message
    setTimeout(() => {
        showToast('info', 'Willkommen', 'Printernizer wurde erfolgreich geladen', CONFIG.TOAST_DURATION, {
            uniqueKey: CONFIG.NOTIFICATION_KEYS.APP_WELCOME,
            deduplicateMode: 'prevent' // Don't show duplicate welcome messages
        });
    }, 1000);
});

/**
 * Handle page visibility changes
 */
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page became hidden - pause refresh intervals
        Logger.debug('Page hidden, pausing refresh intervals');
    } else {
        // Page became visible - resume refresh intervals
        Logger.debug('Page visible, resuming refresh intervals');
        
        // Refresh current page if it's been a while
        const currentManager = app.pageManagers[app.currentPage];
        if (currentManager && currentManager.lastRefresh) {
            const timeSinceRefresh = Date.now() - currentManager.lastRefresh.getTime();
            if (timeSinceRefresh > 60000) { // Refresh if more than 1 minute
                refreshCurrentPage();
            }
        }
    }
});

/**
 * Global utility functions available to all modules
 */

/**
 * Show add printer modal (global function)
 */
function showAddPrinter() {
    // This function is defined in dashboard.js but made available globally
    showModal('addPrinterModal');
    
    // Reset form
    const form = document.getElementById('addPrinterForm');
    if (form) {
        form.reset();
        
        // Hide all printer-specific fields
        const specificFields = document.querySelectorAll('.printer-specific-fields');
        specificFields.forEach(field => {
            field.style.display = 'none';
        });
        
        // Reset printer type selection handler
        const printerTypeSelect = document.getElementById('printerType');
        if (printerTypeSelect) {
            printerTypeSelect.dispatchEvent(new Event('change'));
        }
    }
}

/**
 * Handle printer type change in add printer form
 */
document.addEventListener('change', (e) => {
    if (e.target.id === 'printerType') {
        const printerType = e.target.value;
        const bambuFields = document.getElementById('bambuFields');
        const prusaFields = document.getElementById('prusaFields');
        
        // Hide all fields first
        if (bambuFields) bambuFields.style.display = 'none';
        if (prusaFields) prusaFields.style.display = 'none';
        
        // Show relevant fields
        if (printerType === 'bambu_lab' && bambuFields) {
            bambuFields.style.display = 'block';
        } else if (printerType === 'prusa' && prusaFields) {
            prusaFields.style.display = 'block';
        }
    }
});

/**
 * Global state management
 */
window.printernizer = {
    // Application state
    version: 'loading...',  // Will be loaded from /api/v1/health
    currentPage: 'dashboard',
    connectionStatus: 'connecting',

    // System information
    systemInfo: null,
    
    // User preferences (could be stored in localStorage)
    preferences: {
        theme: 'light',
        language: 'de',
        refreshInterval: 30000,
        showNotifications: true
    },
    
    // API client reference
    api: api,
    
    // WebSocket client reference
    ws: wsClient
};

/**
 * Show full thumbnail in modal (global function for printer tiles)
 */
function showFullThumbnail(fileId, filename) {
    const modal = document.createElement('div');
    modal.className = 'thumbnail-modal';
    modal.innerHTML = `
        <div class="thumbnail-modal-content">
            <div class="thumbnail-modal-header">
                <h3>${escapeHtml(filename || 'Thumbnail')}</h3>
                <button class="thumbnail-modal-close" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</button>
            </div>
            <div class="thumbnail-modal-body">
                <img src="${api.baseURL}/files/${sanitizeAttribute(fileId)}/thumbnail"
                     alt="Full size thumbnail"
                     class="full-thumbnail-image"
                     onerror="this.nextElementSibling.style.display='block'; this.style.display='none'">
                <div class="thumbnail-error" style="display: none">
                    <p>Unable to load thumbnail</p>
                </div>
            </div>
        </div>
    `;

    // Add click outside to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });

    // Add escape key to close
    const handleKeydown = (e) => {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', handleKeydown);
        }
    };
    document.addEventListener('keydown', handleKeydown);

    document.body.appendChild(modal);
}

// Export for debugging purposes
Logger.debug('Printernizer application ready');
Logger.debug('Available global objects:', {
    app: window.app,
    api: window.api || api,
    wsClient: window.wsClient || wsClient,
    printernizer: window.printernizer
});