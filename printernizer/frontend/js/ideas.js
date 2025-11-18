/**
 * Ideas Management JavaScript Module
 * Handles idea creation, editing, filtering, and external platform integration
 */

// API Configuration - Use centralized config that handles HA Ingress mode
// CONFIG.API_BASE_URL includes '/api/v1', so we strip it since this file adds it back
const API_BASE_URL = CONFIG.API_BASE_URL.replace('/api/v1', '');

// Ideas global state
let ideasState = {
    currentTab: 'my-ideas',
    currentView: 'grid', // 'grid' or 'list'
    filters: {
        status: '',
        type: '', // business/personal
        source: '',
        platform: 'all'
    },
    ideas: [],
    bookmarks: [],
    trending: [],
    statistics: {}
};

// Helper function to show error in container
function showErrorInContainer(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="error-message">
                <span class="error-icon">⚠️</span>
                <span class="error-text">${message}</span>
            </div>
        `;
    }
}

// Helper function to show loading
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="loading-placeholder">
                <div class="spinner"></div>
                <p>Lade...</p>
            </div>
        `;
    }
}

// Initialize Ideas page
function initializeIdeas() {
    Logger.debug('Initializing Ideas page...');

    try {
        // Initialize event listeners
        setupIdeasEventListeners();

        // Load initial data
        loadIdeasStatistics().catch(error => {
            Logger.warn('Failed to load ideas statistics:', error);
        });

        loadMyIdeas().catch(error => {
            Logger.warn('Failed to load ideas:', error);
        });

        // Set up periodic refresh for trending content
        setInterval(refreshTrendingIfActive, 5 * 60 * 1000); // Every 5 minutes

        Logger.debug('Ideas page initialized successfully');
    } catch (error) {
        Logger.error('Error initializing Ideas page:', error);
    }
}

// Set up event listeners
function setupIdeasEventListeners() {
    try {
        // Tab navigation
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                if (tabName) {
                    showIdeasTab(tabName);
                }
            });
        });

        // Filter change listeners
        const filters = ['ideaStatusFilter', 'ideaTypeFilter', 'ideaSourceFilter'];
        filters.forEach(filterId => {
            const filterElement = document.getElementById(filterId);
            if (filterElement) {
                filterElement.addEventListener('change', applyIdeasFilters);
            } else {
                Logger.warn(`Filter element not found: ${filterId}`);
            }
        });

        // Form submissions
        setupFormSubmissions();

        // Business checkbox listeners for customer info toggle
        setupBusinessCheckboxListeners();

        Logger.debug('Ideas event listeners setup completed');
    } catch (error) {
        Logger.error('Error setting up Ideas event listeners:', error);
    }
}

// Setup form submissions
function setupFormSubmissions() {
    try {
        // Add Idea Form
        const addIdeaForm = document.getElementById('addIdeaForm');
        if (addIdeaForm) {
            addIdeaForm.addEventListener('submit', handleAddIdea);
            Logger.debug('Add idea form listener attached');
        } else {
            Logger.warn('Add idea form not found');
        }

        // Edit Idea Form
        const editIdeaForm = document.getElementById('editIdeaForm');
        if (editIdeaForm) {
            editIdeaForm.addEventListener('submit', handleEditIdea);
            Logger.debug('Edit idea form listener attached');
        } else {
            Logger.warn('Edit idea form not found');
        }

        // Import Idea Form
        const importIdeaForm = document.getElementById('importIdeaForm');
        if (importIdeaForm) {
            importIdeaForm.addEventListener('submit', handleImportIdea);
            Logger.debug('Import idea form listener attached');
        } else {
            Logger.warn('Import idea form not found');
        }
    } catch (error) {
        Logger.error('Error setting up form submissions:', error);
    }
}

// Setup business checkbox listeners
function setupBusinessCheckboxListeners() {
    const businessCheckboxes = [
        { checkbox: 'ideaIsBusiness', group: 'customerInfoGroup' },
        { checkbox: 'editIdeaIsBusiness', group: 'editCustomerInfoGroup' },
        { checkbox: 'importIsBusiness', group: null }
    ];

    businessCheckboxes.forEach(({ checkbox, group }) => {
        const checkboxElement = document.getElementById(checkbox);
        if (checkboxElement && group) {
            checkboxElement.addEventListener('change', () => {
                const groupElement = document.getElementById(group);
                if (groupElement) {
                    groupElement.style.display = checkboxElement.checked ? 'block' : 'none';
                }
            });
        }
    });
}

// Tab Management
function showIdeasTab(tabName) {
    // Update active tab button
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update active tab content
    document.querySelectorAll('.ideas-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Update state and load appropriate content
    ideasState.currentTab = tabName;

    switch (tabName) {
        case 'my-ideas':
            loadMyIdeas();
            break;
        case 'bookmarks':
            loadBookmarks();
            break;
        case 'trending':
            loadTrending();
            break;
    }
}

// Data Loading Functions
async function loadIdeasStatistics() {
    try {
        Logger.debug('Loading ideas statistics...');
        const response = await fetch(`${API_BASE_URL}/api/v1/ideas/stats/overview`);
        if (response.ok) {
            const stats = await response.json();
            Logger.debug('Statistics loaded:', stats);
            ideasState.statistics = stats;
            displayIdeasStatistics(stats);
        } else {
            Logger.error('Failed to load statistics:', response.status, response.statusText);
            showErrorInContainer('ideasStats', 'Fehler beim Laden der Statistiken');
        }
    } catch (error) {
        Logger.error('Error loading ideas statistics:', error);
        showErrorInContainer('ideasStats', 'Fehler beim Laden der Statistiken');
    }
}

async function loadMyIdeas() {
    try {
        Logger.debug('Loading my ideas...');
        showLoading('myIdeasContainer');

        const queryParams = new URLSearchParams();
        if (ideasState.filters.status) queryParams.set('status', ideasState.filters.status);
        if (ideasState.filters.type) {
            queryParams.set('is_business', ideasState.filters.type === 'business');
        }
        if (ideasState.filters.source) queryParams.set('source_type', ideasState.filters.source);

        const url = `${API_BASE_URL}/api/v1/ideas/?${queryParams}`;
        Logger.debug('Fetching ideas from:', url);

        const response = await fetch(url);
        if (response.ok) {
            const data = await response.json();
            Logger.debug('Ideas loaded:', data);
            ideasState.ideas = data.ideas || [];
            displayMyIdeas(ideasState.ideas);
        } else {
            Logger.error('Failed to load ideas:', response.status, response.statusText);
            showErrorInContainer('myIdeasContainer', 'Fehler beim Laden der Ideen');
        }
    } catch (error) {
        Logger.error('Error loading ideas:', error);
        showErrorInContainer('myIdeasContainer', 'Fehler beim Laden der Ideen');
    }
}

async function loadBookmarks() {
    try {
        showLoading('bookmarksContainer');

        // Load ideas with external source types
        const response = await fetch(`${API_BASE_URL}/api/v1/ideas/?source_type=makerworld,printables`);
        if (response.ok) {
            const data = await response.json();
            ideasState.bookmarks = data.ideas || [];
            displayBookmarks(ideasState.bookmarks);
        } else {
            throw new Error('Failed to load bookmarks');
        }
    } catch (error) {
        Logger.error('Error loading bookmarks:', error);
        showError('bookmarksContainer', 'Fehler beim Laden der Lesezeichen');
    }
}

async function loadTrending() {
    try {
        showLoading('trendingContainer');

        const platform = ideasState.filters.platform === 'all' ? 'all' : ideasState.filters.platform;
        const response = await fetch(`${API_BASE_URL}/api/v1/ideas/trending/${platform}`);
        if (response.ok) {
            const trending = await response.json();
            ideasState.trending = trending;
            displayTrending(trending);
        } else {
            throw new Error('Failed to load trending models');
        }
    } catch (error) {
        Logger.error('Error loading trending models:', error);
        showError('trendingContainer', 'Fehler beim Laden der Trending-Modelle');
    }
}

// Display Functions
function displayIdeasStatistics(stats) {
    const container = document.getElementById('ideasStats');
    if (!container) return;

    const html = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">${stats.total_ideas || stats.idea_count || 0}</div>
                <div class="stat-label">Gesamt Ideen</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.active_ideas || 0}</div>
                <div class="stat-label">Aktive Ideen</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.business_ideas || 0}</div>
                <div class="stat-label">Geschäftlich</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.completed_ideas || 0}</div>
                <div class="stat-label">Abgeschlossen</div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

function displayMyIdeas(ideas) {
    try {
        Logger.debug('Displaying ideas:', ideas);
        const container = document.getElementById('myIdeasContainer');
        if (!container) {
            Logger.error('myIdeasContainer not found');
            return;
        }

        if (!ideas || ideas.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">💡</div>
                    <h3>Keine Ideen gefunden</h3>
                    <p>Erstellen Sie Ihre erste Idee oder passen Sie die Filter an.</p>
                    <button class="btn btn-primary" onclick="showAddIdeaDialog()">
                        <span class="btn-icon">➕</span>
                        Neue Idee
                    </button>
                </div>
            `;
            return;
        }

        const viewClass = ideasState.currentView === 'grid' ? 'ideas-grid' : 'ideas-list';
        const itemsHtml = ideas.map(idea => {
            try {
                return createIdeaCard(idea);
            } catch (cardError) {
                Logger.error('Error creating idea card:', cardError, idea);
                return `<div class="error-card">Error loading idea: ${idea.title || 'Unknown'}</div>`;
            }
        }).join('');

        container.innerHTML = `
            <div class="${viewClass}">
                ${itemsHtml}
            </div>
        `;
        Logger.debug('Ideas displayed successfully');
    } catch (error) {
        Logger.error('Error displaying ideas:', error);
        showErrorInContainer('myIdeasContainer', 'Fehler beim Anzeigen der Ideen');
    }
}

function displayBookmarks(bookmarks) {
    const container = document.getElementById('bookmarksContainer');
    if (!container) return;

    if (bookmarks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔖</div>
                <h3>Keine Lesezeichen gefunden</h3>
                <p>Importieren Sie Modelle aus externen Plattformen.</p>
                <button class="btn btn-primary" onclick="showImportDialog()">
                    <span class="btn-icon">🔗</span>
                    Aus URL importieren
                </button>
            </div>
        `;
        return;
    }

    const itemsHtml = bookmarks.map(bookmark => createBookmarkCard(bookmark)).join('');
    container.innerHTML = `<div class="bookmarks-grid">${itemsHtml}</div>`;
}

function displayTrending(trending) {
    const container = document.getElementById('trendingContainer');
    if (!container) return;

    if (trending.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📈</div>
                <h3>Keine Trending-Modelle gefunden</h3>
                <p>Aktualisieren Sie die Trending-Daten oder überprüfen Sie Ihre Internetverbindung.</p>
                <button class="btn btn-secondary" onclick="refreshTrending()">
                    <span class="btn-icon">🔄</span>
                    Aktualisieren
                </button>
            </div>
        `;
        return;
    }

    const itemsHtml = trending.map(item => createTrendingCard(item)).join('');
    container.innerHTML = `<div class="trending-grid">${itemsHtml}</div>`;
}

// Card Creation Functions
function createIdeaCard(idea) {
    const statusEmoji = getStatusEmoji(idea.status);
    const priorityStars = '★'.repeat(idea.priority || 1);
    const businessIcon = idea.is_business ? '🏢' : '👤';
    const sourceIcon = getSourceIcon(idea.source_type);

    return `
        <div class="idea-card" data-idea-id="${sanitizeAttribute(idea.id)}">
            <div class="card-header">
                <div class="card-status">
                    <span class="status-badge status-${sanitizeAttribute(idea.status)}">${statusEmoji} ${escapeHtml(idea.status)}</span>
                </div>
                <div class="card-priority">
                    <span class="priority-stars">${priorityStars}</span>
                </div>
            </div>

            <div class="card-content">
                <h3 class="card-title">${escapeHtml(idea.title)}</h3>

                ${idea.description ? `<p class="card-description">${escapeHtml(idea.description)}</p>` : ''}

                <div class="card-meta">
                    <div class="meta-item">
                        <span class="meta-icon">${businessIcon}</span>
                        <span class="meta-text">${idea.is_business ? 'Geschäftlich' : 'Privat'}</span>
                    </div>

                    ${idea.category ? `
                        <div class="meta-item">
                            <span class="meta-icon">📂</span>
                            <span class="meta-text">${escapeHtml(idea.category)}</span>
                        </div>
                    ` : ''}

                    ${idea.estimated_print_time ? `
                        <div class="meta-item">
                            <span class="meta-icon">⏱️</span>
                            <span class="meta-text">${formatPrintTime(idea.estimated_print_time)}</span>
                        </div>
                    ` : ''}

                    <div class="meta-item">
                        <span class="meta-icon">${sourceIcon}</span>
                        <span class="meta-text">${formatSource(idea.source_type)}</span>
                    </div>
                </div>

                ${idea.tags && idea.tags.length > 0 ? `
                    <div class="card-tags">
                        ${idea.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                    </div>
                ` : ''}
            </div>

            <div class="card-actions">
                <button class="btn btn-small btn-secondary" onclick="viewIdeaDetails('${sanitizeAttribute(idea.id)}')">
                    <span class="btn-icon">👁️</span>
                    Details
                </button>
                <button class="btn btn-small btn-secondary" onclick="editIdea('${sanitizeAttribute(idea.id)}')">
                    <span class="btn-icon">✏️</span>
                    Bearbeiten
                </button>
                ${idea.status === 'idea' ? `
                    <button class="btn btn-small btn-primary" onclick="planIdea('${sanitizeAttribute(idea.id)}')">
                        <span class="btn-icon">📅</span>
                        Planen
                    </button>
                ` : ''}
                ${idea.status === 'planned' ? `
                    <button class="btn btn-small btn-primary" onclick="startPrint('${sanitizeAttribute(idea.id)}')">
                        <span class="btn-icon">🖨️</span>
                        Drucken
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

function createBookmarkCard(bookmark) {
    const platformIcon = getSourceIcon(bookmark.source_type);
    const businessIcon = bookmark.is_business ? '🏢' : '👤';

    return `
        <div class="bookmark-card" data-idea-id="${sanitizeAttribute(bookmark.id)}">
            <div class="card-thumbnail">
                ${bookmark.thumbnail_path ? `
                    <img src="${sanitizeUrl(bookmark.thumbnail_path)}" alt="${escapeHtml(bookmark.title)}" loading="lazy">
                ` : `
                    <div class="placeholder-thumbnail">
                        <span class="placeholder-icon">${platformIcon}</span>
                    </div>
                `}
            </div>

            <div class="card-content">
                <h3 class="card-title">${escapeHtml(bookmark.title)}</h3>

                <div class="card-meta">
                    <div class="meta-item">
                        <span class="meta-icon">${platformIcon}</span>
                        <span class="meta-text">${formatSource(bookmark.source_type)}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-icon">${businessIcon}</span>
                        <span class="meta-text">${bookmark.is_business ? 'Geschäftlich' : 'Privat'}</span>
                    </div>
                </div>

                ${bookmark.tags && bookmark.tags.length > 0 ? `
                    <div class="card-tags">
                        ${bookmark.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                    </div>
                ` : ''}
            </div>

            <div class="card-actions">
                <button class="btn btn-small btn-secondary" onclick="openExternalUrl('${sanitizeAttribute(bookmark.source_url)}')">
                    <span class="btn-icon">🔗</span>
                    Öffnen
                </button>
                <button class="btn btn-small btn-secondary" onclick="editIdea('${sanitizeAttribute(bookmark.id)}')">
                    <span class="btn-icon">✏️</span>
                    Bearbeiten
                </button>
                <button class="btn btn-small btn-primary" onclick="planIdea('${sanitizeAttribute(bookmark.id)}')">
                    <span class="btn-icon">📅</span>
                    Planen
                </button>
            </div>
        </div>
    `;
}

function createTrendingCard(item) {
    const platformIcon = getSourceIcon(item.platform);

    return `
        <div class="trending-card" data-trending-id="${sanitizeAttribute(item.id)}">
            <div class="card-thumbnail">
                ${item.thumbnail_local_path ? `
                    <img src="${sanitizeUrl(item.thumbnail_local_path)}" alt="${escapeHtml(item.title)}" loading="lazy">
                ` : `
                    <div class="placeholder-thumbnail">
                        <span class="placeholder-icon">${platformIcon}</span>
                    </div>
                `}
            </div>

            <div class="card-content">
                <h3 class="card-title">${escapeHtml(item.title)}</h3>

                <div class="card-meta">
                    <div class="meta-item">
                        <span class="meta-icon">${platformIcon}</span>
                        <span class="meta-text">${formatSource(item.platform)}</span>
                    </div>
                    ${item.creator ? `
                        <div class="meta-item">
                            <span class="meta-icon">👤</span>
                            <span class="meta-text">${escapeHtml(item.creator)}</span>
                        </div>
                    ` : ''}
                    ${item.downloads ? `
                        <div class="meta-item">
                            <span class="meta-icon">📥</span>
                            <span class="meta-text">${formatNumber(item.downloads)}</span>
                        </div>
                    ` : ''}
                    ${item.likes ? `
                        <div class="meta-item">
                            <span class="meta-icon">❤️</span>
                            <span class="meta-text">${formatNumber(item.likes)}</span>
                        </div>
                    ` : ''}
                </div>
            </div>

            <div class="card-actions">
                <button class="btn btn-small btn-secondary" onclick="openExternalUrl('${sanitizeAttribute(item.url)}')">
                    <span class="btn-icon">🔗</span>
                    Öffnen
                </button>
                <button class="btn btn-small btn-primary" onclick="saveTrendingAsIdea('${sanitizeAttribute(item.id)}')">
                    <span class="btn-icon">💾</span>
                    Speichern
                </button>
            </div>
        </div>
    `;
}

// Action Functions
function showAddIdeaDialog() {
    try {
        Logger.debug('Opening add idea dialog...');
        clearIdeaForm('addIdeaForm');
        if (typeof showModal === 'function') {
            showModal('addIdeaModal');
        } else {
            Logger.error('showModal function not available');
            // Fallback: show modal manually
            const modal = document.getElementById('addIdeaModal');
            if (modal) {
                modal.style.display = 'block';
                modal.classList.add('show');
            }
        }
    } catch (error) {
        Logger.error('Error opening add idea dialog:', error);
    }
}

function showImportDialog(context = 'ideas') {
    clearIdeaForm('importIdeaForm');
    
    // Store the import context for later use
    document.getElementById('importIdeaModal').setAttribute('data-context', context);
    
    // Update modal title based on context
    const modalTitle = document.querySelector('#importIdeaModal .modal-header h3');
    if (modalTitle) {
        if (context === 'bookmarks') {
            modalTitle.textContent = 'Lesezeichen aus URL importieren';
        } else {
            modalTitle.textContent = 'Modell aus URL importieren';
        }
    }
    
    showModal('importIdeaModal');
}

async function editIdea(ideaId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/ideas/${ideaId}`);
        if (response.ok) {
            const idea = await response.json();
            populateEditForm(idea);
            showModal('editIdeaModal');
        } else {
            throw new Error('Failed to load idea details');
        }
    } catch (error) {
        Logger.error('Error loading idea for editing:', error);
        showNotification('Fehler beim Laden der Idee', 'error');
    }
}

async function viewIdeaDetails(ideaId) {
    try {
        showModal('ideaDetailsModal');
        showLoading('ideaDetailsContent');

        const response = await fetch(`${API_BASE_URL}/api/v1/ideas/${ideaId}`);
        if (response.ok) {
            const idea = await response.json();
            displayIdeaDetails(idea);
        } else {
            throw new Error('Failed to load idea details');
        }
    } catch (error) {
        Logger.error('Error loading idea details:', error);
        showError('ideaDetailsContent', 'Fehler beim Laden der Details');
    }
}

async function planIdea(ideaId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/ideas/${ideaId}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'planned' })
        });

        if (response.ok) {
            showNotification('Idee wurde geplant', 'success');
            loadMyIdeas(); // Refresh the list
        } else {
            throw new Error('Failed to plan idea');
        }
    } catch (error) {
        Logger.error('Error planning idea:', error);
        showNotification('Fehler beim Planen der Idee', 'error');
    }
}

async function startPrint(ideaId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/ideas/${ideaId}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'printing' })
        });

        if (response.ok) {
            showNotification('Druckstatus wurde aktualisiert', 'success');
            loadMyIdeas(); // Refresh the list
        } else {
            throw new Error('Failed to start print');
        }
    } catch (error) {
        Logger.error('Error starting print:', error);
        showNotification('Fehler beim Starten des Drucks', 'error');
    }
}

async function saveTrendingAsIdea(trendingId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/ideas/trending/${trendingId}/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: '',
                priority: 3,
                is_business: false,
                tags: []
            })
        });

        if (response.ok) {
            showNotification('Trending-Modell als Idee gespeichert', 'success');
            showIdeasTab('my-ideas'); // Switch to my ideas tab
        } else {
            throw new Error('Failed to save trending as idea');
        }
    } catch (error) {
        Logger.error('Error saving trending as idea:', error);
        showNotification('Fehler beim Speichern', 'error');
    }
}

// Form Handlers
async function handleAddIdea(event) {
    event.preventDefault();

    try {
        const formData = new FormData(event.target);
        const ideaData = Object.fromEntries(formData.entries());

        // Process tags - handle empty string
        if (ideaData.tags && ideaData.tags.trim()) {
            ideaData.tags = ideaData.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
        } else {
            ideaData.tags = [];
        }

        // Convert checkbox
        ideaData.is_business = formData.has('is_business');

        // Convert priority to number
        ideaData.priority = parseInt(ideaData.priority) || 3;

        // Convert estimated time to number - handle empty string
        if (ideaData.estimated_print_time && ideaData.estimated_print_time.trim()) {
            ideaData.estimated_print_time = parseInt(ideaData.estimated_print_time);
        } else {
            // Remove the field if empty to let the API use its default (null)
            delete ideaData.estimated_print_time;
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/ideas/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(ideaData)
        });

        if (response.ok) {
            Logger.debug('Idea created successfully');
            try {
                if (typeof showNotification === 'function') {
                    showNotification('Idee erfolgreich erstellt', 'success');
                } else {
                    Logger.debug('Idee erfolgreich erstellt');
                }
                if (typeof closeModal === 'function') {
                    closeModal('addIdeaModal');
                }
                loadMyIdeas();
                loadIdeasStatistics();
            } catch (notifError) {
                Logger.error('Error with notification/modal:', notifError);
            }
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create idea');
        }
    } catch (error) {
        Logger.error('Error creating idea:', error);
        try {
            if (typeof showNotification === 'function') {
                showNotification('Fehler beim Erstellen der Idee: ' + error.message, 'error');
            } else {
                alert('Fehler beim Erstellen der Idee: ' + error.message);
            }
        } catch (notifError) {
            Logger.error('Error showing notification:', notifError);
        }
    }
}

async function handleEditIdea(event) {
    event.preventDefault();

    try {
        const formData = new FormData(event.target);
        const ideaData = Object.fromEntries(formData.entries());
        const ideaId = ideaData.ideaId;
        delete ideaData.ideaId;

        // Process tags - handle empty string
        if (ideaData.tags && ideaData.tags.trim()) {
            ideaData.tags = ideaData.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
        } else {
            ideaData.tags = [];
        }

        // Convert checkbox
        ideaData.is_business = formData.has('is_business');

        // Convert priority to number
        ideaData.priority = parseInt(ideaData.priority) || 3;

        // Convert estimated time to number - handle empty string
        if (ideaData.estimated_print_time && ideaData.estimated_print_time.trim()) {
            ideaData.estimated_print_time = parseInt(ideaData.estimated_print_time);
        } else {
            // Remove the field if empty to let the API use its default (null)
            delete ideaData.estimated_print_time;
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/ideas/${ideaId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(ideaData)
        });

        if (response.ok) {
            showNotification('Idee erfolgreich aktualisiert', 'success');
            closeModal('editIdeaModal');
            loadMyIdeas();
            loadIdeasStatistics();
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update idea');
        }
    } catch (error) {
        Logger.error('Error updating idea:', error);
        showNotification('Fehler beim Aktualisieren der Idee: ' + error.message, 'error');
    }
}

async function handleImportIdea(event) {
    event.preventDefault();

    try {
        const formData = new FormData(event.target);
        const importData = Object.fromEntries(formData.entries());

        // Get the import context from the modal
        const modal = document.getElementById('importIdeaModal');
        const context = modal.getAttribute('data-context') || 'ideas';

        // Process tags
        if (importData.tags) {
            importData.tags = importData.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
        }

        // Convert checkbox
        importData.is_business = formData.has('is_business');

        // Convert priority to number
        importData.priority = parseInt(importData.priority) || 3;

        const response = await fetch(`${API_BASE_URL}/api/v1/ideas/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(importData)
        });

        if (response.ok) {
            if (context === 'bookmarks') {
                showNotification('Lesezeichen erfolgreich importiert', 'success');
                closeModal('importIdeaModal');
                loadBookmarks(); // Reload bookmarks instead of ideas
            } else {
                showNotification('Modell erfolgreich importiert', 'success');
                closeModal('importIdeaModal');
                loadMyIdeas();
                loadIdeasStatistics();
            }
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to import idea');
        }
    } catch (error) {
        Logger.error('Error importing idea:', error);
        showNotification('Fehler beim Importieren: ' + error.message, 'error');
    }
}

// Utility Functions
function clearIdeaForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();

        // Hide customer info groups
        const customerGroups = form.querySelectorAll('[id$="CustomerInfoGroup"]');
        customerGroups.forEach(group => {
            group.style.display = 'none';
        });
    }
}

function populateEditForm(idea) {
    // Set basic fields
    document.getElementById('editIdeaId').value = idea.id;
    document.getElementById('editIdeaTitle').value = idea.title || '';
    document.getElementById('editIdeaDescription').value = idea.description || '';
    document.getElementById('editIdeaCategory').value = idea.category || '';
    document.getElementById('editIdeaPriority').value = idea.priority || 3;
    document.getElementById('editIdeaStatus').value = idea.status || 'idea';

    // Set optional fields
    if (idea.estimated_print_time) {
        document.getElementById('editIdeaEstimatedTime').value = idea.estimated_print_time;
    }

    if (idea.planned_date) {
        document.getElementById('editIdeaPlannedDate').value = idea.planned_date;
    }

    if (idea.completed_date) {
        document.getElementById('editIdeaCompletedDate').value = idea.completed_date;
    }

    document.getElementById('editIdeaMaterialNotes').value = idea.material_notes || '';
    document.getElementById('editIdeaCustomerInfo').value = idea.customer_info || '';

    // Set tags
    if (idea.tags && idea.tags.length > 0) {
        document.getElementById('editIdeaTags').value = idea.tags.join(', ');
    }

    // Set business checkbox and show/hide customer info
    const businessCheckbox = document.getElementById('editIdeaIsBusiness');
    businessCheckbox.checked = idea.is_business || false;

    const customerGroup = document.getElementById('editCustomerInfoGroup');
    if (customerGroup) {
        customerGroup.style.display = idea.is_business ? 'block' : 'none';
    }
}

function displayIdeaDetails(idea) {
    const container = document.getElementById('ideaDetailsContent');
    if (!container) return;

    const statusEmoji = getStatusEmoji(idea.status);
    const businessIcon = idea.is_business ? '🏢' : '👤';
    const sourceIcon = getSourceIcon(idea.source_type);

    const html = `
        <div class="idea-details">
            <div class="details-header">
                <h2>${escapeHtml(idea.title)}</h2>
                <div class="details-meta">
                    <span class="status-badge status-${idea.status}">${statusEmoji} ${idea.status}</span>
                    <span class="business-badge">${businessIcon} ${idea.is_business ? 'Geschäftlich' : 'Privat'}</span>
                    <span class="source-badge">${sourceIcon} ${formatSource(idea.source_type)}</span>
                </div>
            </div>

            ${idea.description ? `
                <div class="details-section">
                    <h3>Beschreibung</h3>
                    <p>${escapeHtml(idea.description)}</p>
                </div>
            ` : ''}

            <div class="details-grid">
                ${idea.category ? `
                    <div class="detail-item">
                        <label>Kategorie</label>
                        <span>${escapeHtml(idea.category)}</span>
                    </div>
                ` : ''}

                <div class="detail-item">
                    <label>Priorität</label>
                    <span>${'★'.repeat(idea.priority || 1)} (${idea.priority || 1}/5)</span>
                </div>

                ${idea.estimated_print_time ? `
                    <div class="detail-item">
                        <label>Geschätzte Druckzeit</label>
                        <span>${formatPrintTime(idea.estimated_print_time)}</span>
                    </div>
                ` : ''}

                ${idea.planned_date ? `
                    <div class="detail-item">
                        <label>Geplantes Datum</label>
                        <span>${formatDate(idea.planned_date)}</span>
                    </div>
                ` : ''}

                ${idea.completed_date ? `
                    <div class="detail-item">
                        <label>Abgeschlossen am</label>
                        <span>${formatDate(idea.completed_date)}</span>
                    </div>
                ` : ''}

                <div class="detail-item">
                    <label>Erstellt am</label>
                    <span>${formatDateTime(idea.created_at)}</span>
                </div>
            </div>

            ${idea.material_notes ? `
                <div class="details-section">
                    <h3>Material-Notizen</h3>
                    <p>${escapeHtml(idea.material_notes)}</p>
                </div>
            ` : ''}

            ${idea.customer_info ? `
                <div class="details-section">
                    <h3>Kunden-Informationen</h3>
                    <p>${escapeHtml(idea.customer_info)}</p>
                </div>
            ` : ''}

            ${idea.tags && idea.tags.length > 0 ? `
                <div class="details-section">
                    <h3>Tags</h3>
                    <div class="tags-list">
                        ${idea.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                    </div>
                </div>
            ` : ''}

            ${idea.source_url ? `
                <div class="details-section">
                    <h3>Externe Quelle</h3>
                    <a href="${idea.source_url}" target="_blank" class="external-link">
                        ${idea.source_url}
                        <span class="external-icon">🔗</span>
                    </a>
                </div>
            ` : ''}

            <div class="details-actions">
                <button class="btn btn-secondary" onclick="editIdea('${idea.id}')">
                    <span class="btn-icon">✏️</span>
                    Bearbeiten
                </button>
                ${idea.source_url ? `
                    <button class="btn btn-secondary" onclick="openExternalUrl('${idea.source_url}')">
                        <span class="btn-icon">🔗</span>
                        Quelle öffnen
                    </button>
                ` : ''}
                ${idea.status === 'idea' ? `
                    <button class="btn btn-primary" onclick="planIdea('${idea.id}')">
                        <span class="btn-icon">📅</span>
                        Planen
                    </button>
                ` : ''}
                ${idea.status === 'planned' ? `
                    <button class="btn btn-primary" onclick="startPrint('${idea.id}')">
                        <span class="btn-icon">🖨️</span>
                        Drucken
                    </button>
                ` : ''}
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// Filter and View Functions
function applyIdeasFilters() {
    ideasState.filters.status = document.getElementById('ideaStatusFilter').value;
    ideasState.filters.type = document.getElementById('ideaTypeFilter').value;
    ideasState.filters.source = document.getElementById('ideaSourceFilter').value;

    // Reload current tab content
    switch (ideasState.currentTab) {
        case 'my-ideas':
            loadMyIdeas();
            break;
        case 'bookmarks':
            loadBookmarks();
            break;
        case 'trending':
            loadTrending();
            break;
    }
}

function filterBookmarksByPlatform(platform) {
    // Update active platform button
    document.querySelectorAll('.platform-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-platform="${platform}"]`).classList.add('active');

    ideasState.filters.platform = platform;
    loadBookmarks();
}

function filterTrendingByPlatform(platform) {
    // Update active platform button
    document.querySelectorAll('.trending-platform-filter .platform-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.trending-platform-filter [data-platform="${platform}"]`).classList.add('active');

    ideasState.filters.platform = platform;
    loadTrending();
}

function setIdeasView(view) {
    ideasState.currentView = view;

    // Update view buttons
    document.querySelectorAll('.ideas-view-controls .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(view === 'grid' ? 'gridViewBtn' : 'listViewBtn').classList.add('active');

    // Reload current ideas
    displayMyIdeas(ideasState.ideas);
}

// Refresh Functions
function refreshIdeas() {
    switch (ideasState.currentTab) {
        case 'my-ideas':
            loadMyIdeas();
            break;
        case 'bookmarks':
            loadBookmarks();
            break;
        case 'trending':
            loadTrending();
            break;
    }
    loadIdeasStatistics();
}

async function refreshTrending() {
    try {
        showLoading('trendingContainer');

        // Force refresh trending cache
        await fetch(`${API_BASE_URL}/api/v1/ideas/trending/refresh`, { method: 'POST' });

        // Load fresh trending data
        await loadTrending();

        showNotification('Trending-Daten aktualisiert', 'success');
    } catch (error) {
        Logger.error('Error refreshing trending:', error);
        showNotification('Fehler beim Aktualisieren der Trending-Daten', 'error');
    }
}

function refreshTrendingIfActive() {
    if (ideasState.currentTab === 'trending') {
        loadTrending();
    }
}

// URL Preview Function
async function previewImportUrl() {
    const urlInput = document.getElementById('importUrl');
    const previewDiv = document.getElementById('urlPreview');

    if (!urlInput.value) {
        showNotification('Bitte geben Sie eine URL ein', 'warning');
        return;
    }

    try {
        // This would call a URL parsing service endpoint
        // For now, show a simple preview
        previewDiv.style.display = 'block';
        document.getElementById('previewTitle').textContent = 'URL-Vorschau wird geladen...';
        document.getElementById('previewDescription').textContent = 'Lade Metadaten...';

        // In a real implementation, this would fetch metadata from the URL
        setTimeout(() => {
            document.getElementById('previewTitle').textContent = 'Modell von externem Link';
            document.getElementById('previewDescription').textContent = 'Vorschau wird in zukünftigen Versionen verfügbar sein.';
            document.getElementById('previewCreator').textContent = 'Ersteller: Unbekannt';
            document.getElementById('previewPlatform').textContent = 'Plattform: ' + extractPlatformFromUrl(urlInput.value);
        }, 1000);

    } catch (error) {
        Logger.error('Error previewing URL:', error);
        showNotification('Fehler beim Laden der URL-Vorschau', 'error');
    }
}

// Utility Helper Functions
function getStatusEmoji(status) {
    const emojis = {
        'idea': '💡',
        'planned': '📅',
        'printing': '🖨️',
        'completed': '✅',
        'archived': '📦'
    };
    return emojis[status] || '💡';
}

function getSourceIcon(sourceType) {
    const icons = {
        'manual': '✍️',
        'makerworld': '🌍',
        'printables': '🔧',
        'thingiverse': '🔷',
        'myminifactory': '🏭',
        'cults3d': '🎭'
    };
    return icons[sourceType] || '📄';
}

function formatSource(sourceType) {
    const names = {
        'manual': 'Manuell',
        'makerworld': 'Makerworld',
        'printables': 'Printables',
        'thingiverse': 'Thingiverse',
        'myminifactory': 'MyMiniFactory',
        'cults3d': 'Cults3D'
    };
    return names[sourceType] || sourceType;
}

function formatPrintTime(minutes) {
    if (!minutes) return '';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
        return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatDate(dateString) {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('de-DE');
}

function formatDateTime(dateString) {
    if (!dateString) return '';
    return new Date(dateString).toLocaleString('de-DE');
}

function extractPlatformFromUrl(url) {
    if (url.includes('makerworld.com')) return 'Makerworld';
    if (url.includes('printables.com')) return 'Printables';
    if (url.includes('thingiverse.com')) return 'Thingiverse';
    if (url.includes('myminifactory.com')) return 'MyMiniFactory';
    if (url.includes('cults3d.com')) return 'Cults3D';
    return 'Unbekannt';
}

function openExternalUrl(url) {
    window.open(url, '_blank');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="loading-placeholder">
                <div class="spinner"></div>
                <p>Lade...</p>
            </div>
        `;
    }
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="error-placeholder">
                <div class="error-icon">⚠️</div>
                <p>${escapeHtml(message)}</p>
            </div>
        `;
    }
}

// Export functions for global access
window.initializeIdeas = initializeIdeas;
window.showIdeasTab = showIdeasTab;
window.refreshIdeas = refreshIdeas;
window.refreshTrending = refreshTrending;
window.showAddIdeaDialog = showAddIdeaDialog;
window.showImportDialog = showImportDialog;
window.editIdea = editIdea;
window.viewIdeaDetails = viewIdeaDetails;
window.planIdea = planIdea;
window.startPrint = startPrint;
window.saveTrendingAsIdea = saveTrendingAsIdea;
window.filterBookmarksByPlatform = filterBookmarksByPlatform;
window.filterTrendingByPlatform = filterTrendingByPlatform;
window.setIdeasView = setIdeasView;
window.previewImportUrl = previewImportUrl;
window.openExternalUrl = openExternalUrl;