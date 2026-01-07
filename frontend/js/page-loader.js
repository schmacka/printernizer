/**
 * Page Loader - Loads the main application shell with page context
 *
 * This script is used by standalone page HTML files (jobs.html, materials.html, etc.)
 * to bootstrap the main application with the correct initial page.
 *
 * Usage: Include this script with a data-page attribute:
 *   <script src="js/page-loader.js" data-page="jobs"></script>
 */
(function() {
    'use strict';

    function loadAppShell() {
        // Get the target page from the script's data attribute
        var scripts = document.getElementsByTagName('script');
        var currentScript = scripts[scripts.length - 1];
        var targetPage = currentScript.getAttribute('data-page') || 'dashboard';

        window.__INITIAL_PAGE__ = targetPage;
        window.__ENTRY_PATH__ = window.location.pathname;

        fetch('index.html', { cache: 'no-store' })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Failed to load application shell');
                }
                return response.text();
            })
            .then(function(html) {
                document.open();
                document.write(html);
                document.close();
            })
            .catch(function(error) {
                document.body.innerHTML = '<main class="standalone-error">' +
                    '<h1>Printernizer</h1>' +
                    '<p>Die Anwendung konnte nicht geladen werden.</p>' +
                    '<pre>' + (error.message || error) + '</pre>' +
                    '</main>';
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadAppShell);
    } else {
        loadAppShell();
    }
})();
