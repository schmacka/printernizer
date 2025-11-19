/**
 * Enhanced File Metadata Component
 * Phase 2: Frontend Display Enhancement (Issue #43, #45)
 * 
 * Provides comprehensive metadata display with:
 * - Physical properties (dimensions, volume, objects)
 * - Print settings (layer height, nozzle, infill)
 * - Material requirements (filament weight, colors)
 * - Cost breakdown (material and energy costs)
 * - Quality metrics (complexity score, difficulty)
 * - Compatibility information (printers, slicer info)
 */

class EnhancedFileMetadata {
    constructor(fileId) {
        this.fileId = fileId;
        this.metadata = null;
        this.isLoading = false;
        this.error = null;
        this.cache = new Map();
        this.cacheTimeout = 300000; // 5 minutes
    }

    /**
     * Load enhanced metadata from API
     */
    async loadMetadata(forceRefresh = false) {
        // Check cache first
        if (!forceRefresh && this.cache.has(this.fileId)) {
            const cached = this.cache.get(this.fileId);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                this.metadata = cached.data;
                return this.metadata;
            }
        }

        this.isLoading = true;
        this.error = null;

        try {
            const response = await fetch(
                `${CONFIG.API_BASE_URL}/files/${this.fileId}/metadata/enhanced?force_refresh=${forceRefresh}`
            );

            if (!response.ok) {
                throw new Error(`Failed to load metadata: ${response.statusText}`);
            }

            this.metadata = await response.json();
            
            // Cache the result
            this.cache.set(this.fileId, {
                data: this.metadata,
                timestamp: Date.now()
            });

            return this.metadata;

        } catch (error) {
            Logger.error('Failed to load enhanced metadata:', error);
            this.error = error.message;
            return null;
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Render complete enhanced metadata display
     */
    render() {
        if (this.isLoading) {
            return this.renderLoading();
        }

        if (this.error) {
            return this.renderError();
        }

        if (!this.metadata || this.isEmptyMetadata()) {
            return this.renderEmpty();
        }

        return `
            <div class="enhanced-file-metadata">
                ${this.renderSummaryCards()}
                ${this.renderDetailedSections()}
            </div>
        `;
    }

    /**
     * Check if metadata is empty
     */
    isEmptyMetadata() {
        if (!this.metadata) return true;
        
        const hasData = 
            this.metadata.physical_properties ||
            this.metadata.print_settings ||
            this.metadata.material_requirements ||
            this.metadata.cost_breakdown ||
            this.metadata.quality_metrics ||
            this.metadata.compatibility_info;
        
        return !hasData;
    }

    /**
     * Render summary cards at the top
     */
    renderSummaryCards() {
        const cards = [];

        // Physical dimensions card
        if (this.metadata.physical_properties) {
            const props = this.metadata.physical_properties;
            if (props.width && props.depth && props.height) {
                cards.push({
                    icon: '📐',
                    value: `${props.width}×${props.depth}×${props.height}`,
                    label: 'Abmessungen (mm)',
                    unit: ''
                });
            }
        }

        // Total cost card
        if (this.metadata.cost_breakdown && this.metadata.cost_breakdown.total_cost) {
            cards.push({
                icon: '💰',
                value: this.metadata.cost_breakdown.total_cost.toFixed(2),
                label: 'Gesamtkosten',
                unit: '€'
            });
        }

        // Quality score card
        if (this.metadata.quality_metrics && this.metadata.quality_metrics.complexity_score) {
            cards.push({
                icon: '⭐',
                value: this.metadata.quality_metrics.complexity_score,
                label: 'Qualitätsscore',
                unit: '/10'
            });
        }

        // Object count card
        if (this.metadata.physical_properties && this.metadata.physical_properties.object_count) {
            cards.push({
                icon: '🧩',
                value: this.metadata.physical_properties.object_count,
                label: 'Objekte',
                unit: ''
            });
        }

        if (cards.length === 0) {
            return '';
        }

        return `
            <div class="metadata-summary-cards">
                ${cards.map(card => `
                    <div class="summary-card">
                        <div class="summary-card-icon">${card.icon}</div>
                        <div class="summary-card-value">${card.value}${card.unit}</div>
                        <div class="summary-card-label">${card.label}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Render detailed information sections
     */
    renderDetailedSections() {
        const sections = [];

        // Physical Properties
        const physicalSection = this.renderPhysicalProperties();
        if (physicalSection) sections.push(physicalSection);

        // Print Settings
        const settingsSection = this.renderPrintSettings();
        if (settingsSection) sections.push(settingsSection);

        // Material Requirements
        const materialSection = this.renderMaterialRequirements();
        if (materialSection) sections.push(materialSection);

        // Cost Breakdown
        const costSection = this.renderCostBreakdown();
        if (costSection) sections.push(costSection);

        // Quality Metrics
        const qualitySection = this.renderQualityMetrics();
        if (qualitySection) sections.push(qualitySection);

        // Compatibility Info
        const compatSection = this.renderCompatibilityInfo();
        if (compatSection) sections.push(compatSection);

        if (sections.length === 0) {
            return '';
        }

        return `
            <div class="metadata-detail-grid">
                ${sections.join('')}
            </div>
        `;
    }

    /**
     * Render physical properties section
     */
    renderPhysicalProperties() {
        const props = this.metadata.physical_properties;
        if (!props) return null;

        const items = [];

        if (props.width) {
            items.push({ label: 'Breite', value: `${props.width.toFixed(1)} mm` });
        }
        if (props.depth) {
            items.push({ label: 'Tiefe', value: `${props.depth.toFixed(1)} mm` });
        }
        if (props.height) {
            items.push({ label: 'Höhe', value: `${props.height.toFixed(1)} mm` });
        }
        if (props.volume) {
            items.push({ label: 'Volumen', value: `${props.volume.toFixed(2)} cm³` });
        }
        if (props.surface_area) {
            items.push({ label: 'Oberfläche', value: `${props.surface_area.toFixed(2)} cm²` });
        }
        if (props.object_count) {
            items.push({ label: 'Anzahl Objekte', value: props.object_count });
        }

        if (items.length === 0) return null;

        return `
            <div class="metadata-section">
                <div class="metadata-section-header">
                    <span class="metadata-section-icon">📋</span>
                    <h4 class="metadata-section-title">Modell-Informationen</h4>
                </div>
                <div class="metadata-items">
                    ${items.map(item => `
                        <div class="metadata-item">
                            <span class="metadata-item-label">${item.label}:</span>
                            <span class="metadata-item-value">${item.value}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Render print settings section
     */
    renderPrintSettings() {
        const settings = this.metadata.print_settings;
        if (!settings) return null;

        const items = [];

        if (settings.layer_height) {
            let label = `Schichthöhe: ${settings.layer_height} mm`;
            if (settings.total_layer_count) {
                label += ` (${settings.total_layer_count} Schichten)`;
            }
            items.push({ label: 'Schichthöhe', value: label });
        }
        if (settings.nozzle_diameter) {
            items.push({ label: 'Düsendurchmesser', value: `${settings.nozzle_diameter} mm` });
        }
        if (settings.wall_count || settings.wall_thickness) {
            const value = settings.wall_thickness 
                ? `${settings.wall_thickness} mm${settings.wall_count ? ` (${settings.wall_count} Wände)` : ''}`
                : `${settings.wall_count} Wände`;
            items.push({ label: 'Wandstärke', value });
        }
        if (settings.infill_density !== null && settings.infill_density !== undefined) {
            const value = settings.infill_pattern 
                ? `${settings.infill_density}% (${settings.infill_pattern})`
                : `${settings.infill_density}%`;
            items.push({ label: 'Füllung', value });
        }
        if (settings.support_used !== null && settings.support_used !== undefined) {
            items.push({ label: 'Stützen', value: settings.support_used ? 'Ja' : 'Nicht erforderlich' });
        }
        if (settings.nozzle_temperature) {
            items.push({ label: 'Düsentemperatur', value: `${settings.nozzle_temperature}°C` });
        }
        if (settings.bed_temperature) {
            items.push({ label: 'Betttemperatur', value: `${settings.bed_temperature}°C` });
        }
        if (settings.print_speed) {
            items.push({ label: 'Druckgeschwindigkeit', value: `${settings.print_speed} mm/s` });
        }

        if (items.length === 0) return null;

        return `
            <div class="metadata-section">
                <div class="metadata-section-header">
                    <span class="metadata-section-icon">⚙️</span>
                    <h4 class="metadata-section-title">Druckeinstellungen</h4>
                </div>
                <div class="metadata-items">
                    ${items.map(item => `
                        <div class="metadata-item">
                            <span class="metadata-item-label">${item.label}:</span>
                            <span class="metadata-item-value">${item.value}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Render material requirements section
     */
    renderMaterialRequirements() {
        const material = this.metadata.material_requirements;
        if (!material) return null;

        const items = [];

        if (material.total_weight) {
            items.push({ label: 'Gesamtgewicht', value: `${material.total_weight.toFixed(1)} g` });
        }
        if (material.filament_length) {
            items.push({ label: 'Filamentlänge', value: `${material.filament_length.toFixed(2)} m` });
        }
        if (material.material_types && material.material_types.length > 0) {
            items.push({ label: 'Material', value: material.material_types.join(', ') });
        }
        if (material.waste_weight) {
            items.push({ label: 'Abfall (geschätzt)', value: `${material.waste_weight.toFixed(1)} g` });
        }
        if (material.multi_material) {
            items.push({ label: 'Multi-Material', value: 'Ja' });
        }

        // Color tags
        let colorTags = '';
        if (material.filament_colors && material.filament_colors.length > 0) {
            colorTags = `
                <div class="metadata-tags">
                    ${material.filament_colors.map(color => `
                        <span class="metadata-tag color">🎨 ${color}</span>
                    `).join('')}
                </div>
            `;
        }

        if (items.length === 0 && !colorTags) return null;

        return `
            <div class="metadata-section">
                <div class="metadata-section-header">
                    <span class="metadata-section-icon">🧵</span>
                    <h4 class="metadata-section-title">Materialanforderungen</h4>
                </div>
                <div class="metadata-items">
                    ${items.map(item => `
                        <div class="metadata-item">
                            <span class="metadata-item-label">${item.label}:</span>
                            <span class="metadata-item-value">${item.value}</span>
                        </div>
                    `).join('')}
                </div>
                ${colorTags}
            </div>
        `;
    }

    /**
     * Render cost breakdown section
     */
    renderCostBreakdown() {
        const cost = this.metadata.cost_breakdown;
        if (!cost) return null;

        const items = [];

        if (cost.material_cost) {
            items.push({ label: 'Materialkosten', value: `€${cost.material_cost.toFixed(2)}` });
        }
        if (cost.energy_cost) {
            items.push({ label: 'Energiekosten', value: `€${cost.energy_cost.toFixed(2)}` });
        }
        if (cost.cost_per_gram) {
            items.push({ label: 'Kosten pro Gramm', value: `€${cost.cost_per_gram.toFixed(3)}` });
        }

        // Add detailed breakdown if available
        if (cost.breakdown) {
            Object.entries(cost.breakdown).forEach(([key, value]) => {
                if (typeof value === 'number') {
                    items.push({ 
                        label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()), 
                        value: `€${value.toFixed(2)}` 
                    });
                }
            });
        }

        if (items.length === 0 && !cost.total_cost) return null;

        return `
            <div class="metadata-section">
                <div class="metadata-section-header">
                    <span class="metadata-section-icon">💰</span>
                    <h4 class="metadata-section-title">Kostenaufschlüsselung</h4>
                </div>
                <div class="cost-breakdown">
                    ${items.map(item => `
                        <div class="cost-item">
                            <span class="cost-label">${item.label}</span>
                            <span class="cost-value">${item.value}</span>
                        </div>
                    `).join('')}
                    ${cost.total_cost ? `
                        <div class="cost-item">
                            <span class="cost-label">Gesamtkosten</span>
                            <span class="cost-value">€${cost.total_cost.toFixed(2)}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Render quality metrics section
     */
    renderQualityMetrics() {
        const quality = this.metadata.quality_metrics;
        if (!quality) return null;

        const items = [];

        if (quality.complexity_score) {
            const scoreClass = quality.complexity_score >= 8 ? 'excellent' : 
                             quality.complexity_score >= 6 ? 'good' : 
                             quality.complexity_score >= 4 ? 'moderate' : 'low';
            items.push({ 
                label: 'Komplexitätsscore', 
                value: `<span class="quality-score ${scoreClass}">${quality.complexity_score}/10</span>`,
                raw: true
            });
        }

        if (quality.difficulty_level) {
            const difficultyClass = quality.difficulty_level.toLowerCase();
            const difficultyMap = {
                'beginner': 'Anfänger',
                'intermediate': 'Fortgeschritten',
                'advanced': 'Experte',
                'expert': 'Profi'
            };
            items.push({ 
                label: 'Schwierigkeitsgrad', 
                value: `<span class="difficulty-badge ${difficultyClass}">${difficultyMap[difficultyClass] || quality.difficulty_level}</span>`,
                raw: true
            });
        }

        if (quality.success_probability !== null && quality.success_probability !== undefined) {
            const probability = quality.success_probability;
            const progressClass = probability >= 80 ? '' : probability >= 60 ? 'warning' : 'danger';
            items.push({ 
                label: 'Erfolgswahrscheinlichkeit', 
                value: `
                    <div>
                        ${probability.toFixed(0)}%
                        <div class="metadata-progress">
                            <div class="metadata-progress-bar ${progressClass}" style="width: ${probability}%"></div>
                        </div>
                    </div>
                `,
                raw: true
            });
        }

        if (quality.overhang_percentage) {
            items.push({ label: 'Überhang-Anteil', value: `${quality.overhang_percentage.toFixed(1)}%` });
        }

        if (items.length === 0) return null;

        return `
            <div class="metadata-section">
                <div class="metadata-section-header">
                    <span class="metadata-section-icon">⭐</span>
                    <h4 class="metadata-section-title">Qualitätsmetriken</h4>
                </div>
                <div class="metadata-items">
                    ${items.map(item => `
                        <div class="metadata-item">
                            <span class="metadata-item-label">${item.label}:</span>
                            <span class="metadata-item-value">${item.raw ? item.value : escapeHtml(item.value)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Render compatibility information section
     */
    renderCompatibilityInfo() {
        const compat = this.metadata.compatibility_info;
        if (!compat) return null;

        const items = [];

        if (compat.slicer_name) {
            const value = compat.slicer_version 
                ? `${compat.slicer_name} ${compat.slicer_version}`
                : compat.slicer_name;
            items.push({ label: 'Slicer', value });
        }

        if (compat.profile_name) {
            items.push({ label: 'Profil', value: compat.profile_name });
        }

        if (compat.bed_type) {
            items.push({ label: 'Druckbett-Typ', value: compat.bed_type });
        }

        // Compatible printers
        let printersList = '';
        if (compat.compatible_printers && compat.compatible_printers.length > 0) {
            printersList = `
                <div class="compatibility-list">
                    ${compat.compatible_printers.map(printer => `
                        <div class="compatibility-item">
                            <span class="compatibility-icon compatible">✓</span>
                            <span>${escapeHtml(printer)}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // Required features
        let featuresTags = '';
        if (compat.required_features && compat.required_features.length > 0) {
            featuresTags = `
                <div class="metadata-tags">
                    ${compat.required_features.map(feature => `
                        <span class="metadata-tag feature">⚡ ${escapeHtml(feature)}</span>
                    `).join('')}
                </div>
            `;
        }

        if (items.length === 0 && !printersList && !featuresTags) return null;

        return `
            <div class="metadata-section">
                <div class="metadata-section-header">
                    <span class="metadata-section-icon">🖨️</span>
                    <h4 class="metadata-section-title">Kompatibilität</h4>
                </div>
                <div class="metadata-items">
                    ${items.map(item => `
                        <div class="metadata-item">
                            <span class="metadata-item-label">${item.label}:</span>
                            <span class="metadata-item-value">${escapeHtml(item.value)}</span>
                        </div>
                    `).join('')}
                </div>
                ${printersList}
                ${featuresTags}
            </div>
        `;
    }

    /**
     * Render loading state
     */
    renderLoading() {
        return `
            <div class="metadata-loading">
                <div class="metadata-loading-spinner"></div>
                <p>Lade erweiterte Metadaten...</p>
            </div>
        `;
    }

    /**
     * Render error state
     */
    renderError() {
        return `
            <div class="metadata-empty">
                <div class="metadata-empty-icon">⚠️</div>
                <p class="metadata-empty-text">Fehler beim Laden der Metadaten</p>
                <small class="metadata-empty-hint">${escapeHtml(this.error || 'Unbekannter Fehler')}</small>
            </div>
        `;
    }

    /**
     * Render empty state
     */
    renderEmpty() {
        return `
            <div class="metadata-empty">
                <div class="metadata-empty-icon">📋</div>
                <p class="metadata-empty-text">Keine erweiterten Metadaten verfügbar</p>
                <small class="metadata-empty-hint">Metadaten werden beim ersten Laden extrahiert</small>
            </div>
        `;
    }

    /**
     * Clear cache for this file
     */
    clearCache() {
        this.cache.delete(this.fileId);
    }

    /**
     * Clear all cached metadata
     */
    static clearAllCache() {
        if (window.metadataCache) {
            window.metadataCache.clear();
        }
    }
}

// Helper function to safely escape HTML
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.EnhancedFileMetadata = EnhancedFileMetadata;
}
