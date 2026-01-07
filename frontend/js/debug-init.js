/**
 * Debug Page Initialization
 *
 * Initializes the debug page with proper ingress path support.
 */
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        // Set dashboard link with ingress path support
        var dashboardLink = document.getElementById('dashboardLink');
        if (dashboardLink && typeof CONFIG !== 'undefined') {
            dashboardLink.href = CONFIG.BASE_PATH ? CONFIG.BASE_PATH + '/' : '/';
        }

        // Initialize the debug manager
        if (typeof debugManager !== 'undefined' && debugManager.init) {
            debugManager.init();
        }
    });
})();
