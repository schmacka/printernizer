/**
 * Printernizer Search Module
 * Unified cross-site search functionality for local files and ideas
 */

class SearchManager {
    constructor() {
        this.currentQuery = '';
        this.currentFilters = {};
        this.currentPage = 1;
        this.resultsPerPage = 50;
        this.searchTimeout = null;
        this.searchDebounceMs = 300;
    }

    /**
     * Initialize search functionality
     */
    async initialize() {
        this.renderSearchBar();
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
    }

    /**
     * Render search bar in navigation
     */
    renderSearchBar() {
        const navContainer = document.querySelector('.nav-container') || document.querySelector('nav');
        if (!navContainer) {
            Logger.warn('Navigation container not found for search bar');
            return;
        }

        const searchBarHTML = `
            <div class="search-bar-container">
                <div class="search-input-wrapper">
                    <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="m21 21-4.35-4.35"></path>
                    </svg>
                    <input
                        type="text"
                        id="global-search-input"
                        class="search-input"
                        placeholder="Search files, ideas... (Ctrl+K)"
                        autocomplete="off"
                    />
                    <button id="search-clear-btn" class="search-clear-btn" style="display: none;" title="Clear search">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <div id="search-suggestions" class="search-suggestions" style="display: none;"></div>
            </div>
        `;

        // Insert search bar into navigation
        const navList = navContainer.querySelector('ul');
        if (navList) {
            const searchLi = document.createElement('li');
            searchLi.className = 'nav-search-item';
            searchLi.innerHTML = searchBarHTML;
            navList.appendChild(searchLi);
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const searchInput = document.getElementById('global-search-input');
        const searchClearBtn = document.getElementById('search-clear-btn');

        if (searchInput) {
            // Input event with debounce
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value;

                // Show/hide clear button
                if (searchClearBtn) {
                    searchClearBtn.style.display = query ? 'block' : 'none';
                }

                // Debounce suggestions
                clearTimeout(this.searchTimeout);
                if (query.length >= 2) {
                    this.searchTimeout = setTimeout(() => {
                        this.showSuggestions(query);
                    }, this.searchDebounceMs);
                } else {
                    this.hideSuggestions();
                }
            });

            // Enter key to perform search
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const query = e.target.value.trim();
                    if (query) {
                        this.performSearch(query);
                    }
                }

                // Escape to close suggestions
                if (e.key === 'Escape') {
                    this.hideSuggestions();
                    searchInput.blur();
                }
            });

            // Focus to show recent searches
            searchInput.addEventListener('focus', () => {
                if (!searchInput.value) {
                    this.showRecentSearches();
                }
            });

            // Click outside to hide suggestions
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.search-bar-container')) {
                    this.hideSuggestions();
                }
            });
        }

        // Clear button
        if (searchClearBtn) {
            searchClearBtn.addEventListener('click', () => {
                searchInput.value = '';
                searchClearBtn.style.display = 'none';
                searchInput.focus();
                this.hideSuggestions();
            });
        }
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+K or Cmd+K to focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('global-search-input');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
        });
    }

    /**
     * Show search suggestions
     */
    async showSuggestions(query) {
        try {
            const suggestions = await api.getSearchSuggestions(query, 10);
            this.renderSuggestions(suggestions);
        } catch (error) {
            Logger.error('Failed to load suggestions:', error);
        }
    }

    /**
     * Show recent searches
     */
    async showRecentSearches() {
        try {
            const history = await api.getSearchHistory(5);
            if (history && history.length > 0) {
                const suggestions = history.map(entry => ({
                    text: entry.query,
                    type: 'history',
                    relevance: 1.0
                }));
                this.renderSuggestions(suggestions, 'Recent Searches');
            }
        } catch (error) {
            Logger.error('Failed to load search history:', error);
        }
    }

    /**
     * Render suggestions dropdown
     */
    renderSuggestions(suggestions, title = null) {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (!suggestionsContainer) return;

        if (!suggestions || suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }

        let html = '';
        if (title) {
            html += `<div class="suggestions-title">${title}</div>`;
        }

        suggestions.forEach(suggestion => {
            const icon = suggestion.type === 'history' ? '🕒' : '🔍';
            html += `
                <div class="suggestion-item" data-query="${escapeHtml(suggestion.text)}">
                    <span class="suggestion-icon">${icon}</span>
                    <span class="suggestion-text">${escapeHtml(suggestion.text)}</span>
                </div>
            `;
        });

        suggestionsContainer.innerHTML = html;
        suggestionsContainer.style.display = 'block';

        // Add click handlers
        suggestionsContainer.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                const query = item.dataset.query;
                document.getElementById('global-search-input').value = query;
                this.performSearch(query);
                this.hideSuggestions();
            });
        });
    }

    /**
     * Hide suggestions dropdown
     */
    hideSuggestions() {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (suggestionsContainer) {
            suggestionsContainer.style.display = 'none';
        }
    }

    /**
     * Perform search and navigate to results page
     */
    async performSearch(query, filters = {}) {
        this.currentQuery = query;
        this.currentFilters = filters;
        this.currentPage = 1;

        // Hide suggestions
        this.hideSuggestions();

        // Navigate to search results page
        showSection('search-results');

        // Load results
        await this.loadSearchResults();
    }

    /**
     * Load and display search results
     */
    async loadSearchResults() {
        const resultsContainer = document.getElementById('search-results-container');
        if (!resultsContainer) {
            Logger.error('Search results container not found');
            return;
        }

        // Show loading state
        resultsContainer.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Searching...</p>
            </div>
        `;

        try {
            const results = await api.unifiedSearch(
                this.currentQuery,
                this.currentFilters,
                this.currentPage,
                this.resultsPerPage
            );

            this.renderSearchResults(results);
        } catch (error) {
            Logger.error('Search failed:', error);
            resultsContainer.innerHTML = `
                <div class="error-state">
                    <p>Search failed: ${escapeHtml(error.message)}</p>
                    <button onclick="searchManager.loadSearchResults()">Retry</button>
                </div>
            `;
        }
    }

    /**
     * Render search results
     */
    renderSearchResults(results) {
        const resultsContainer = document.getElementById('search-results-container');
        if (!resultsContainer) return;

        // Update header
        const headerHTML = `
            <div class="search-results-header">
                <h2>Search Results for "${escapeHtml(this.currentQuery)}"</h2>
                <p class="search-meta">
                    ${results.total_results} results in ${results.search_time_ms}ms
                    ${results.cached ? '<span class="cached-badge">Cached</span>' : ''}
                </p>
            </div>
        `;

        // No results
        if (results.total_results === 0) {
            resultsContainer.innerHTML = headerHTML + `
                <div class="no-results">
                    <p>No results found for "${escapeHtml(this.currentQuery)}"</p>
                    <p class="suggestion">Try different keywords or check your filters</p>
                </div>
            `;
            return;
        }

        // Render grouped results
        let groupsHTML = '';
        for (const group of results.groups) {
            groupsHTML += this.renderResultGroup(group);
        }

        // Pagination
        const paginationHTML = this.renderPagination(results);

        resultsContainer.innerHTML = headerHTML + groupsHTML + paginationHTML;
    }

    /**
     * Render a result group
     */
    renderResultGroup(group) {
        const sourceLabels = {
            'local_files': '📁 Local Files',
            'ideas': '💡 Ideas',
            'makerworld': '🌐 Makerworld',
            'printables': '🌐 Printables'
        };

        const sourceLabel = sourceLabels[group.source] || group.source;

        let html = `
            <div class="search-result-group" data-source="${group.source}">
                <div class="result-group-header">
                    <h3>${sourceLabel}</h3>
                    <span class="result-count">${group.total_count} results</span>
                </div>
                <div class="result-group-items">
        `;

        for (const result of group.results) {
            html += this.renderResultCard(result);
        }

        html += `
                </div>
            </div>
        `;

        return html;
    }

    /**
     * Render a result card
     */
    renderResultCard(result) {
        if (result.result_type === 'file') {
            return this.renderFileCard(result);
        } else if (result.result_type === 'idea') {
            return this.renderIdeaCard(result);
        }
        return '';
    }

    /**
     * Render file result card
     */
    renderFileCard(result) {
        const metadata = result.metadata || {};
        const physicalProps = metadata.physical_properties || {};

        return `
            <div class="result-card file-card" data-id="${sanitizeAttribute(result.id)}">
                <div class="card-thumbnail">
                    ${result.thumbnail_url ?
                        `<img src="${sanitizeUrl(result.thumbnail_url)}" alt="${escapeHtml(result.title)}" />` :
                        '<div class="placeholder-thumbnail">📄</div>'
                    }
                </div>
                <div class="card-content">
                    <h4 class="card-title">${escapeHtml(result.title)}</h4>
                    <p class="card-source">📁 Local File</p>
                    <div class="card-metadata">
                        ${physicalProps.width && physicalProps.height ?
                            `<span class="metadata-item">📏 ${physicalProps.width}×${physicalProps.height}×${physicalProps.depth || 0}mm</span>` : ''
                        }
                        ${result.print_time_minutes ?
                            `<span class="metadata-item">🕐 ${formatDuration(result.print_time_minutes)}</span>` : ''
                        }
                        ${result.cost_eur !== null && result.cost_eur !== undefined ?
                            `<span class="metadata-item">💰 €${result.cost_eur.toFixed(2)}</span>` : ''
                        }
                    </div>
                    <div class="card-actions">
                        <button class="btn-primary btn-sm" onclick="viewFileDetails('${sanitizeAttribute(result.id)}')">View Details</button>
                    </div>
                </div>
                <div class="card-relevance">
                    <span class="relevance-score">${Math.round(result.relevance_score)}%</span>
                </div>
            </div>
        `;
    }

    /**
     * Render idea result card
     */
    renderIdeaCard(result) {
        const metadata = result.metadata || {};

        return `
            <div class="result-card idea-card" data-id="${sanitizeAttribute(result.id)}">
                <div class="card-thumbnail">
                    ${result.thumbnail_url ?
                        `<img src="${sanitizeUrl(result.thumbnail_url)}" alt="${escapeHtml(result.title)}" />` :
                        '<div class="placeholder-thumbnail">💡</div>'
                    }
                </div>
                <div class="card-content">
                    <h4 class="card-title">${escapeHtml(result.title)}</h4>
                    <p class="card-source">💡 Idea</p>
                    ${result.description ?
                        `<p class="card-description">${escapeHtml(result.description.substring(0, 150))}${result.description.length > 150 ? '...' : ''}</p>` : ''
                    }
                    <div class="card-metadata">
                        ${metadata.status ?
                            `<span class="metadata-item status-${sanitizeAttribute(metadata.status)}">${escapeHtml(metadata.status)}</span>` : ''
                        }
                        ${metadata.category ?
                            `<span class="metadata-item">📂 ${escapeHtml(metadata.category)}</span>` : ''
                        }
                        ${metadata.is_business ?
                            '<span class="metadata-item">🏢 Business</span>' : ''
                        }
                    </div>
                    <div class="card-actions">
                        <button class="btn-primary btn-sm" onclick="viewIdeaDetails('${sanitizeAttribute(result.id)}')">View Details</button>
                    </div>
                </div>
                <div class="card-relevance">
                    <span class="relevance-score">${Math.round(result.relevance_score)}%</span>
                </div>
            </div>
        `;
    }

    /**
     * Render pagination controls
     */
    renderPagination(results) {
        const totalPages = Math.ceil(results.total_results / this.resultsPerPage);

        if (totalPages <= 1) return '';

        let html = '<div class="pagination">';

        // Previous button
        if (this.currentPage > 1) {
            html += `<button class="btn-secondary" onclick="searchManager.goToPage(${this.currentPage - 1})">← Previous</button>`;
        }

        // Page info
        html += `<span class="page-info">Page ${this.currentPage} of ${totalPages}</span>`;

        // Next button
        if (this.currentPage < totalPages) {
            html += `<button class="btn-secondary" onclick="searchManager.goToPage(${this.currentPage + 1})">Next →</button>`;
        }

        html += '</div>';
        return html;
    }

    /**
     * Navigate to a specific page
     */
    async goToPage(page) {
        this.currentPage = page;
        await this.loadSearchResults();
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Initialize search manager
const searchManager = new SearchManager();

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => searchManager.initialize());
} else {
    searchManager.initialize();
}

// Helper function to format duration
function formatDuration(minutes) {
    if (minutes < 60) {
        return `${minutes}m`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
}

// Helper function to view file details (redirect to files page)
function viewFileDetails(fileId) {
    // Navigate to files page with this file selected
    window.location.href = `#files?file=${fileId}`;
}

// Helper function to view idea details (redirect to ideas page)
function viewIdeaDetails(ideaId) {
    // Navigate to ideas page with this idea selected
    window.location.href = `#ideas?idea=${ideaId}`;
}
