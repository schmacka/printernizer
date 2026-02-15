/**
 * Tools & Helpers Page Manager
 * Displays curated external links useful for 3D printing.
 *
 * To add a new link, append an object to the TOOLS_DATA array below.
 */

const TOOLS_DATA = [
    {
        id: 'gridfinity-layout',
        title: 'Gridfinity Layout Tool',
        description: 'Design and plan Gridfinity storage layouts for your workshop. Create custom bin configurations with an interactive visual editor.',
        url: 'https://www.gridfinitylayouttool.com/l/G3rQIfJ2eXsu/untitled-layout',
        icon: '📐',
        category: 'Gridfinity'
    },
    {
        id: 'bento3d-gridfinity',
        title: 'Bento3D Gridfinity',
        description: 'Create custom 3D-printable Gridfinity boxes in minutes. Design and export personalized storage containers with an intuitive web interface.',
        url: 'https://bento3d.design/gridfinity',
        icon: '📦',
        category: 'Gridfinity'
    },
    {
        id: 'tooltrace-ai',
        title: 'ToolTrace AI',
        description: 'AI-powered assistant for 3D printing. Get help with print settings, troubleshooting, and model optimization.',
        url: 'https://www.tooltrace.ai/',
        icon: '🤖',
        category: 'AI Assistant'
    },
    {
        id: '3dbenchy',
        title: 'Official 3DBenchy',
        description: 'Download the official 3DBenchy torture test model — the gold standard benchmark for calibrating and testing 3D printers.',
        url: 'https://www.3dbenchy.com/download/',
        icon: '🚢',
        category: 'Calibration'
    },
    {
        id: 'organic-relief-plate',
        title: 'Organic Relief Plate Generator',
        description: 'OpenSCAD-based generator for creating organic relief plates. Customize parameters to produce unique decorative 3D-printable plates.',
        url: 'https://makerworld.com/de/models/2339750-organic-relief-plate-generator-openscad',
        icon: '🎨',
        category: 'Design'
    },
    {
        id: 'web-openscad-editor',
        title: 'Web OpenSCAD Editor',
        description: 'Browser-based OpenSCAD editor that lets you create and preview parametric 3D models directly in the browser — no local installation required.',
        url: 'https://github.com/yawkat/web-openscad-editor',
        icon: '🖥️',
        category: 'Design'
    }
];

class ToolsManager {
    constructor() {
        this.tools = TOOLS_DATA;
        this.currentFilter = '';
    }

    init() {
        Logger.debug('Initializing Tools & Helpers page');
        this.populateCategoryFilter();
        this.setupEventListeners();
        this.renderTools();
    }

    cleanup() {
        // Static page — nothing to tear down
    }

    /**
     * Build category filter options dynamically from the tools data
     */
    populateCategoryFilter() {
        const select = document.getElementById('toolsCategoryFilter');
        if (!select) return;

        const categories = [...new Set(this.tools.map(t => t.category))].sort();

        // Keep the "All" option, rebuild the rest
        select.innerHTML = '<option value="">All Categories</option>';
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            select.appendChild(opt);
        });

        // Restore previous selection if still valid
        if (this.currentFilter && categories.includes(this.currentFilter)) {
            select.value = this.currentFilter;
        }
    }

    setupEventListeners() {
        const select = document.getElementById('toolsCategoryFilter');
        if (select) {
            select.onchange = (e) => {
                this.currentFilter = e.target.value;
                this.renderTools();
            };
        }
    }

    renderTools() {
        const container = document.getElementById('toolsGrid');
        if (!container) return;

        const filtered = this.currentFilter
            ? this.tools.filter(t => t.category === this.currentFilter)
            : this.tools;

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">🔧</span>
                    <p>No tools found for this category.</p>
                </div>`;
            return;
        }

        container.innerHTML = filtered.map(tool => this.renderCard(tool)).join('');
    }

    renderCard(tool) {
        return `
            <div class="card tool-card" data-tool-id="${sanitizeAttribute(tool.id)}">
                <div class="card-header">
                    <h3>${escapeHtml(tool.title)}</h3>
                    <span class="card-icon">${tool.icon}</span>
                </div>
                <div class="card-body">
                    <span class="tool-category-tag">${escapeHtml(tool.category)}</span>
                    <p class="tool-description">${escapeHtml(tool.description)}</p>
                    <a href="${sanitizeAttribute(tool.url)}" target="_blank" rel="noopener noreferrer"
                       class="btn btn-primary tool-open-btn">
                        Open
                    </a>
                </div>
            </div>`;
    }
}

const toolsManager = new ToolsManager();
