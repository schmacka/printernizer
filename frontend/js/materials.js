/**
 * Printernizer - Material Management Frontend
 * German UI for spool inventory and tracking
 */

class MaterialsManager {
    constructor() {
        this.materials = [];
        const storedView = localStorage.getItem('materialsViewMode');
        this.viewMode = storedView === 'cards' ? 'cards' : 'table';
        this.currentFilters = {
            type: '',
            brand: '',
            color: '',
            lowStock: false,
            search: ''
        };
        this.currentSort = {
            field: 'created_at',
            direction: 'desc'
        };
        this.enums = null;
        this.init();
    }

    async init() {
        try {
            // Load enum data for dropdowns
            await this.loadEnums();
            // Load materials
            await this.loadMaterials();
            // Setup event listeners
            this.setupEventListeners();
            // Render initial view
            this.render();
        } catch (error) {
            Logger.error('Failed to initialize materials manager:', error);
            this.showError('Fehler beim Laden der Filamente');
        }
    }

    async loadEnums() {
        try {
            // Use ApiClient which properly handles ingress paths
            this.enums = await api.get('materials/types');
        } catch (error) {
            Logger.error('Failed to load material types:', error);
            // Set default enums if fetch fails
            this.enums = {
                types: ['PLA', 'PETG', 'ABS', 'TPU', 'Nylon'],
                brands: [],
                colors: []
            };
        }
    }

    async loadMaterials() {
        try {
            // Build query string from filters
            const params = new URLSearchParams();
            if (this.currentFilters.type) params.append('material_type', this.currentFilters.type);
            if (this.currentFilters.brand) params.append('brand', this.currentFilters.brand);
            if (this.currentFilters.color) params.append('color', this.currentFilters.color);
            if (this.currentFilters.lowStock) params.append('low_stock', 'true');

            const url = `/api/v1/materials${params.toString() ? '?' + params.toString() : ''}`;
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            this.materials = await response.json();
            this.applyClientFilters();
            this.applySorting();
        } catch (error) {
            Logger.error('Failed to load materials:', error);
            this.showError('Fehler beim Laden der Filamente');
        }
    }

    applyClientFilters() {
        if (this.currentFilters.search) {
            const searchLower = this.currentFilters.search.toLowerCase();
            this.materials = this.materials.filter(m =>
                m.material_type.toLowerCase().includes(searchLower) ||
                m.brand.toLowerCase().includes(searchLower) ||
                m.color.toLowerCase().includes(searchLower) ||
                (m.notes && m.notes.toLowerCase().includes(searchLower))
            );
        }
    }

    applySorting() {
        const { field, direction } = this.currentSort;
        this.materials.sort((a, b) => {
            let aVal = a[field];
            let bVal = b[field];

            // Handle numeric fields
            if (field === 'remaining_weight' || field === 'weight') {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            }

            // Handle string fields
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }

            const result = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
            return direction === 'asc' ? result : -result;
        });
    }

    setupEventListeners() {
        // View mode toggle buttons are handled by inline onclick in HTML
        // Filter controls are handled by inline onchange in HTML
        // Add material button is handled by inline onclick in HTML
        // Search input is handled by inline oninput in HTML

        // Form submission
        const form = document.getElementById('materialForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveMaterial();
            });
        }

        // Modal close buttons
        const modal = document.getElementById('materialModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target.id === 'materialModal' || e.target.closest('.modal-close')) {
                    this.closeModal();
                }
            });
        }
    }

    setViewMode(mode) {
        if (!['cards', 'table'].includes(mode)) {
            mode = 'table';
        }

        this.viewMode = mode;
        localStorage.setItem('materialsViewMode', mode);
        this.updateViewButtons();
        this.render();
    }

    updateViewButtons() {
        const cardsBtn = document.getElementById('cardsViewBtn');
        const tableBtn = document.getElementById('tableViewBtn');
        if (cardsBtn) cardsBtn.classList.toggle('active', this.viewMode === 'cards');
        if (tableBtn) tableBtn.classList.toggle('active', this.viewMode === 'table');
    }

    async updateStats() {
        try {
            // Use ApiClient which properly handles ingress paths
            const stats = await api.get('materials/stats');

            // Update stat cards
            const statTotalSpools = document.getElementById('statTotalSpools');
            const statTotalWeight = document.getElementById('statTotalWeight');
            const statLowStock = document.getElementById('statLowStock');
            const statTotalValue = document.getElementById('statTotalValue');

            if (statTotalSpools) statTotalSpools.textContent = stats.total_spools || 0;
            if (statTotalWeight) statTotalWeight.textContent = `${(Number(stats.total_weight_g) / 1000 || 0).toFixed(2)}`;
            if (statLowStock) statLowStock.textContent = stats.low_stock_count || 0;
            if (statTotalValue) statTotalValue.textContent = `${Number(stats.total_value || 0).toFixed(2)}`;
        } catch (error) {
            Logger.error('Error updating stats:', error);
        }
    }

    render() {
        const cardsContainer = document.getElementById('materialsCardsView');
        const tableContainer = document.getElementById('materialsTableView');

        this.updateViewButtons();

        if (this.viewMode === 'cards') {
            // Show cards, hide table
            if (cardsContainer) {
                cardsContainer.style.display = '';
                cardsContainer.innerHTML = this.renderCardsView();
            }
            if (tableContainer) tableContainer.style.display = 'none';
        } else {
            // Show table, hide cards
            if (tableContainer) {
                tableContainer.style.display = '';
                tableContainer.innerHTML = this.renderTableView();
            }
            if (cardsContainer) cardsContainer.style.display = 'none';
        }

        // Update statistics
        this.updateStats();
    }

    renderCardsView() {
        if (this.materials.length === 0) {
            return `
                <div class="empty-state">
                    <div class="empty-state-icon">📦</div>
                    <h3>Keine Filamente gefunden</h3>
                    <p>Fügen Sie Ihre erste Filamentspule hinzu</p>
                    <button class="btn btn-primary" onclick="materialsManager.showAddModal()">
                        <span class="btn-icon">➕</span> Filament hinzufügen
                    </button>
                </div>
            `;
        }

        return `
            <div class="materials-cards">
                ${this.materials.map(m => this.renderCard(m)).join('')}
            </div>
        `;
    }

    renderCard(material) {
        const remaining = parseFloat(material.remaining_weight);
        const total = parseFloat(material.weight);
        const percentage = (remaining / total) * 100;
        const isLowStock = percentage < 20;

        return `
            <div class="material-card ${isLowStock ? 'low-stock' : ''}" data-id="${sanitizeAttribute(material.id)}">
                <div class="material-card-header">
                    <div class="material-type">${this.formatMaterialType(material.material_type)}</div>
                    <div class="material-actions">
                        <button class="btn-icon" onclick="materialsManager.editMaterial('${sanitizeAttribute(material.id)}')" title="Bearbeiten">
                            ✏️
                        </button>
                        <button class="btn-icon" onclick="materialsManager.deleteMaterial('${sanitizeAttribute(material.id)}')" title="Löschen">
                            🗑️
                        </button>
                    </div>
                </div>

                <div class="material-card-body">
                    <div class="material-brand">${escapeHtml(material.brand)}</div>
                    <div class="material-color">
                        <span class="color-indicator" style="background-color: ${sanitizeAttribute(this.getColorHex(material.color))}"></span>
                        ${escapeHtml(material.color)}
                    </div>

                    <div class="material-weight">
                        <strong>${remaining.toFixed(0)}g</strong> / ${total}g
                    </div>

                    <div class="progress-bar">
                        <div class="progress-fill ${isLowStock ? 'low' : ''}" style="width: ${percentage}%"></div>
                    </div>

                    ${material.notes ? `<div class="material-notes">${escapeHtml(material.notes)}</div>` : ''}
                </div>

                <div class="material-card-footer">
                    <span class="material-date">Gekauft: ${this.formatDate(material.purchase_date)}</span>
                    <span class="material-cost">${parseFloat(material.cost_per_kg).toFixed(2)} €/kg</span>
                </div>
            </div>
        `;
    }

    renderTableView() {
        if (this.materials.length === 0) {
            return `
                <div class="empty-state">
                    <div class="empty-state-icon">📦</div>
                    <h3>Keine Filamente gefunden</h3>
                    <p>Fügen Sie Ihre erste Filamentspule hinzu</p>
                    <button class="btn btn-primary" onclick="materialsManager.showAddModal()">
                        <span class="btn-icon">➕</span> Filament hinzufügen
                    </button>
                </div>
            `;
        }

        return `
            <div class="table-responsive">
                <table class="materials-table">
                    <thead id="materialsTableHead">
                        <tr>
                            <th data-sort="material_type">Typ ${this.getSortIcon('material_type')}</th>
                            <th data-sort="brand">Marke ${this.getSortIcon('brand')}</th>
                            <th data-sort="color">Farbe ${this.getSortIcon('color')}</th>
                            <th data-sort="remaining_weight">Restmenge ${this.getSortIcon('remaining_weight')}</th>
                            <th data-sort="cost_per_kg">Preis ${this.getSortIcon('cost_per_kg')}</th>
                            <th data-sort="purchase_date">Gekauft ${this.getSortIcon('purchase_date')}</th>
                            <th>Aktionen</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.materials.map(m => this.renderTableRow(m)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderTableRow(material) {
        const remaining = parseFloat(material.remaining_weight);
        const total = parseFloat(material.weight);
        const percentage = (remaining / total) * 100;
        const isLowStock = percentage < 20;

        return `
            <tr class="${isLowStock ? 'low-stock' : ''}" data-id="${sanitizeAttribute(material.id)}">
                <td>${this.formatMaterialType(material.material_type)}</td>
                <td>${escapeHtml(material.brand)}</td>
                <td>
                    <span class="color-indicator" style="background-color: ${sanitizeAttribute(this.getColorHex(material.color))}"></span>
                    ${escapeHtml(material.color)}
                </td>
                <td>
                    <strong>${remaining.toFixed(0)}g</strong> / ${total}g
                    <div class="progress-bar-mini">
                        <div class="progress-fill ${isLowStock ? 'low' : ''}" style="width: ${percentage}%"></div>
                    </div>
                </td>
                <td>${parseFloat(material.cost_per_kg).toFixed(2)} €/kg</td>
                <td>${this.formatDate(material.purchase_date)}</td>
                <td class="actions">
                    <button class="btn-icon" onclick="materialsManager.editMaterial('${sanitizeAttribute(material.id)}')" title="Bearbeiten">
                        ✏️
                    </button>
                    <button class="btn-icon" onclick="materialsManager.deleteMaterial('${sanitizeAttribute(material.id)}')" title="Löschen">
                        🗑️
                    </button>
                </td>
            </tr>
        `;
    }

    getSortIcon(field) {
        if (this.currentSort.field !== field) {
            return '<span class="sort-icon sort-inactive">↕️</span>';
        }
        return this.currentSort.direction === 'asc'
            ? '<span class="sort-icon sort-active">↑</span>'
            : '<span class="sort-icon sort-active">↓</span>';
    }

    showAddMaterialModal() {
        // Alias for HTML compatibility
        this.showAddModal();
    }

    showAddModal() {
        const modalTitle = document.getElementById('materialModalTitle');
        const form = document.getElementById('materialForm');
        const materialId = document.getElementById('materialId');

        if (modalTitle) modalTitle.textContent = 'Filament hinzufügen';
        if (form) form.reset();
        if (materialId) materialId.value = '';

        // Set default diameter
        const diameter = document.getElementById('materialDiameter');
        if (diameter) diameter.value = '1.75';

        // Populate type dropdown from enums
        if (this.enums && this.enums.types) {
            const typeSelect = document.getElementById('materialType');
            if (typeSelect) {
                typeSelect.innerHTML = '<option value="">Typ auswählen</option>';
                this.enums.types.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    typeSelect.appendChild(option);
                });
            }
        }

        // Show modal
        const modal = document.getElementById('materialModal');
        if (modal) {
            showModal('materialModal');
        }
    }

    async editMaterial(id) {
        const material = this.materials.find(m => m.id === id);
        if (!material) return;

        const modalTitle = document.getElementById('materialModalTitle');
        if (modalTitle) modalTitle.textContent = 'Filament bearbeiten';

        document.getElementById('materialId').value = material.id;

        // Populate type dropdown from enums first
        if (this.enums && this.enums.types) {
            const typeSelect = document.getElementById('materialType');
            if (typeSelect) {
                typeSelect.innerHTML = '<option value="">Typ auswählen</option>';
                this.enums.types.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    typeSelect.appendChild(option);
                });
            }
        }

        // Populate form with correct IDs
        // Convert kg to grams for display
        document.getElementById('materialType').value = material.material_type;
        document.getElementById('materialBrand').value = material.brand;
        document.getElementById('materialColor').value = material.color;
        document.getElementById('materialDiameter').value = material.diameter;
        document.getElementById('materialSpoolWeight').value = Math.round(material.weight * 1000);  // kg to g
        document.getElementById('materialRemainingWeight').value = Math.round(material.remaining_weight * 1000);  // kg to g
        document.getElementById('materialPricePerKg').value = material.cost_per_kg;
        document.getElementById('materialNotes').value = material.notes || '';

        // Show modal
        const modal = document.getElementById('materialModal');
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('show');
        }
    }

    populateFormDropdowns() {
        if (!this.enums) return;

        // Populate type dropdown
        const typeSelect = document.getElementById('materialType');
        typeSelect.innerHTML = '<option value="">Typ wählen</option>' +
            this.enums.types.map(t => `<option value="${t}">${this.formatMaterialType(t)}</option>`).join('');

        // Populate brand dropdown
        const brandSelect = document.getElementById('brand');
        brandSelect.innerHTML = '<option value="">Marke wählen</option>' +
            this.enums.brands.map(b => `<option value="${b}">${b}</option>`).join('');

        // Populate color dropdown
        const colorSelect = document.getElementById('color');
        colorSelect.innerHTML = '<option value="">Farbe wählen</option>' +
            this.enums.colors.map(c => `<option value="${c}">${c}</option>`).join('');
    }

    async saveMaterial() {
        const form = document.getElementById('materialForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const materialId = document.getElementById('materialId').value;

        // Get values from form with correct IDs
        const spoolWeightG = parseFloat(document.getElementById('materialSpoolWeight').value);
        const remainingWeightG = parseFloat(document.getElementById('materialRemainingWeight').value);
        const brandValue = document.getElementById('materialBrand').value.trim().toUpperCase();
        const colorValue = document.getElementById('materialColor').value.trim().toUpperCase();
        const pricePerKgValue = document.getElementById('materialPricePerKg').value.trim();

        // Validate and parse price if provided
        let pricePerKg = null;
        if (pricePerKgValue) {
            pricePerKg = parseFloat(pricePerKgValue);
            if (isNaN(pricePerKg) || pricePerKg < 0) {
                this.showError('Preis pro kg muss eine positive Zahl oder 0 sein');
                return;
            }
            // Round to 2 decimal places
            pricePerKg = Math.round(pricePerKg * 100) / 100;
        }

        // Valid enum values
        const validBrands = ['OVERTURE', 'PRUSAMENT', 'BAMBU', 'POLYMAKER', 'ESUN', 'OTHER'];
        const validColors = ['BLACK', 'WHITE', 'GREY', 'RED', 'BLUE', 'GREEN', 'YELLOW', 'ORANGE', 'PURPLE', 'PINK', 'TRANSPARENT', 'NATURAL', 'OTHER'];

        // Build request data based on operation
        let data;
        const colorHexInput = document.getElementById('materialColorHex');
        const locationInput = document.getElementById('materialLocation');
        const isActiveInput = document.getElementById('materialIsActive');

        if (materialId) {
            // PATCH: Only send MaterialUpdate fields
            data = {
                remaining_weight: remainingWeightG / 1000,  // Convert g to kg
                cost_per_kg: pricePerKg !== null ? pricePerKg : 0,
                notes: document.getElementById('materialNotes').value || null,
                color_hex: colorHexInput ? colorHexInput.value || null : null,
                location: locationInput ? locationInput.value || null : null,
                is_active: isActiveInput ? isActiveInput.checked : true
            };
        } else {
            // POST: Send full MaterialCreate
            data = {
                material_type: document.getElementById('materialType').value,
                brand: validBrands.includes(brandValue) ? brandValue : 'OTHER',
                color: validColors.includes(colorValue) ? colorValue : 'OTHER',
                diameter: parseFloat(document.getElementById('materialDiameter').value),
                weight: spoolWeightG / 1000,  // Convert g to kg
                remaining_weight: remainingWeightG / 1000,  // Convert g to kg
                cost_per_kg: pricePerKg !== null ? pricePerKg : 0,
                vendor: document.getElementById('materialBrand').value || 'Unknown',
                notes: document.getElementById('materialNotes').value || null,
                color_hex: colorHexInput ? colorHexInput.value || null : null,
                location: locationInput ? locationInput.value || null : null,
                is_active: isActiveInput ? isActiveInput.checked : true
            };
        }

        try {
            const url = materialId ? `/api/v1/materials/${materialId}` : '/api/v1/materials';
            const method = materialId ? 'PATCH' : 'POST';

            Logger.debug('Saving material:', { url, method, data });

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                Logger.error('Save failed:', { status: response.status, errorData });
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            this.closeModal();
            await this.loadMaterials();
            this.render();
            this.showSuccess(materialId ? 'Filament aktualisiert' : 'Filament hinzugefügt');
        } catch (error) {
            Logger.error('Failed to save material:', error);
            this.showError('Fehler beim Speichern: ' + error.message);
        }
    }

    async deleteMaterial(id) {
        if (!confirm('Filament wirklich löschen?')) return;

        try {
            const response = await fetch(`/api/v1/materials/${id}`, { method: 'DELETE' });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            await this.loadMaterials();
            this.render();
            this.showSuccess('Filament gelöscht');
        } catch (error) {
            Logger.error('Failed to delete material:', error);
            this.showError('Fehler beim Löschen');
        }
    }

    closeModal() {
        const modal = document.getElementById('materialModal');
        if (modal) {
            window.closeModal('materialModal');
        }
        // Reset form
        const form = document.getElementById('materialForm');
        if (form) form.reset();
    }

    applyFilters() {
        // Update current filters from UI
        const filterType = document.getElementById('filterMaterialType');
        const filterBrand = document.getElementById('filterMaterialBrand');
        const filterColor = document.getElementById('filterMaterialColor');
        const filterLowStock = document.getElementById('filterLowStock');
        const searchInput = document.getElementById('materialSearchInput');

        this.currentFilters = {
            type: filterType ? filterType.value : '',
            brand: filterBrand ? filterBrand.value : '',
            color: filterColor ? filterColor.value : '',
            lowStock: filterLowStock ? filterLowStock.checked : false,
            search: searchInput ? searchInput.value : ''
        };

        // Reload and re-render
        this.loadMaterials().then(() => this.render());
    }

    clearFilters() {
        this.currentFilters = {
            type: '',
            brand: '',
            color: '',
            lowStock: false,
            search: ''
        };

        const filterType = document.getElementById('filterMaterialType');
        const filterBrand = document.getElementById('filterMaterialBrand');
        const filterColor = document.getElementById('filterMaterialColor');
        const filterLowStock = document.getElementById('filterLowStock');
        const searchInput = document.getElementById('materialSearchInput');

        if (filterType) filterType.value = '';
        if (filterBrand) filterBrand.value = '';
        if (filterColor) filterColor.value = '';
        if (filterLowStock) filterLowStock.checked = false;
        if (searchInput) searchInput.value = '';

        this.loadMaterials().then(() => this.render());
    }

    formatMaterialType(type) {
        const typeMap = {
            'PLA': 'PLA',
            'PLA_ECO': 'PLA Eco',
            'PLA_MATTE': 'PLA Matte',
            'PLA_SILK': 'PLA Silk',
            'PLA_TURBO': 'PLA Turbo',
            'PETG': 'PETG',
            'TPU': 'TPU',
            'ABS': 'ABS',
            'ASA': 'ASA',
            'NYLON': 'Nylon',
            'PC': 'PC',
            'OTHER': 'Sonstiges'
        };
        return typeMap[type] || type;
    }

    getColorHex(colorName) {
        const colorMap = {
            'BLACK': '#000000',
            'WHITE': '#FFFFFF',
            'GREY': '#808080',
            'RED': '#FF0000',
            'BLUE': '#0000FF',
            'GREEN': '#008000',
            'YELLOW': '#FFFF00',
            'ORANGE': '#FFA500',
            'PURPLE': '#800080',
            'PINK': '#FFC0CB',
            'TRANSPARENT': 'transparent',
            'NATURAL': '#F5F5DC',
            'OTHER': '#CCCCCC'
        };
        return colorMap[colorName] || '#CCCCCC';
    }

    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('de-DE');
    }

    showSuccess(message) {
        Logger.debug('Success:', message);
        showToast('success', 'Erfolg', message);
    }

    showError(message) {
        Logger.error('Error:', message);
        showToast('error', 'Fehler', message);
    }
}

// Initialize when DOM is ready
let materialsManager;
document.addEventListener('DOMContentLoaded', () => {
    materialsManager = new MaterialsManager();
});
