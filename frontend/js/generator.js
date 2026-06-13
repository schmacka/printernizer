/**
 * OpenSCAD Generator page manager.
 *
 * Lists bundled parametric templates and accepts arbitrary .scad uploads,
 * builds a dynamic form from each script's discovered parameters, renders a
 * PNG preview / STL via the backend, shows the STL in an interactive three.js
 * viewer, and saves results into the Library.
 */
class GeneratorManager {
    constructor() {
        this.available = false;
        this.templates = [];
        this.currentSourceRef = null;
        this.currentParameters = [];
        this.lastRenderId = null;
        this.three = null; // { renderer, scene, camera, controls, mesh, animationId }
        this._initialized = false;
    }

    _t(key, fallback) {
        return (typeof t === 'function') ? t(key) : fallback;
    }

    _toast(type, message) {
        if (typeof showToast === 'function') {
            showToast(type, this._t('generator.pageTitle', 'Generator'), message);
        } else {
            console.log(`[generator:${type}] ${message}`);
        }
    }

    async init() {
        // Re-check availability each time the page is opened.
        await this.checkStatus();
        if (!this.available) return;
        if (this._initialized) return;
        this._initialized = true;

        document.getElementById('generatorPreviewBtn')?.addEventListener('click', () => this.render('png'));
        document.getElementById('generatorRenderBtn')?.addEventListener('click', () => this.render('stl'));
        document.getElementById('generatorSaveBtn')?.addEventListener('click', () => this.saveToLibrary());
        document.getElementById('generatorUpload')?.addEventListener('change', (e) => this.handleUpload(e));

        await this.loadTemplates();
    }

    cleanup() {
        this._stopAnimation();
    }

    async checkStatus() {
        try {
            const status = await api.get('/generator/status');
            this.available = !!status.available;
        } catch (e) {
            this.available = false;
        }
        const layout = document.getElementById('generatorLayout');
        const unavailable = document.getElementById('generatorUnavailable');
        const navLink = document.getElementById('nav-generator-link');
        if (navLink) navLink.style.display = this.available ? '' : 'none';
        if (layout) layout.style.display = this.available ? '' : 'none';
        if (unavailable) unavailable.style.display = this.available ? 'none' : 'block';
    }

    async loadTemplates() {
        try {
            this.templates = await api.get('/generator/templates');
            this.renderTemplateList();
        } catch (e) {
            this._toast('error', this._t('generator.loadFailed', 'Failed to load templates'));
        }
    }

    renderTemplateList() {
        const container = document.getElementById('generatorTemplates');
        if (!container) return;
        container.innerHTML = '';
        this.templates.forEach((tpl) => {
            const card = document.createElement('button');
            card.type = 'button';
            card.className = 'generator-template-card';
            card.dataset.id = tpl.id;
            card.innerHTML = `<strong>${escapeHtml(tpl.name)}</strong>` +
                (tpl.description ? `<span>${escapeHtml(tpl.description)}</span>` : '');
            card.addEventListener('click', () => this.selectTemplate(tpl.id));
            container.appendChild(card);
        });
    }

    async selectTemplate(templateId) {
        try {
            const tpl = await api.get(`/generator/templates/${encodeURIComponent(templateId)}`);
            this.setActiveSource(tpl.id, tpl.parameters);
            this._highlightCard(tpl.id);
        } catch (e) {
            this._toast('error', this._t('generator.loadFailed', 'Failed to load template'));
        }
    }

    _highlightCard(id) {
        document.querySelectorAll('.generator-template-card').forEach((el) => {
            el.classList.toggle('active', el.dataset.id === id);
        });
    }

    setActiveSource(sourceRef, parameters) {
        this.currentSourceRef = sourceRef;
        this.currentParameters = parameters || [];
        this.lastRenderId = null;
        this.buildForm();
        document.getElementById('generatorPreviewBtn').disabled = false;
        document.getElementById('generatorRenderBtn').disabled = false;
        document.getElementById('generatorSaveBtn').disabled = true;
    }

    buildForm() {
        const form = document.getElementById('generatorForm');
        if (!form) return;
        form.innerHTML = '';

        // Group parameters by their section.
        const groups = new Map();
        this.currentParameters.forEach((p) => {
            const key = p.group || '';
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push(p);
        });

        groups.forEach((params, groupName) => {
            const fieldset = document.createElement('fieldset');
            fieldset.className = 'generator-fieldset';
            if (groupName) {
                const legend = document.createElement('legend');
                legend.textContent = groupName;
                fieldset.appendChild(legend);
            }
            params.forEach((p) => fieldset.appendChild(this._buildField(p)));
            form.appendChild(fieldset);
        });
    }

    _buildField(param) {
        const wrap = document.createElement('div');
        wrap.className = 'generator-field';
        const label = document.createElement('label');
        label.textContent = param.description || param.name;
        label.htmlFor = `gen_${param.name}`;
        wrap.appendChild(label);

        let input;
        if (param.type === 'boolean') {
            input = document.createElement('input');
            input.type = 'checkbox';
            input.checked = !!param.default;
        } else if (param.type === 'enum') {
            input = document.createElement('select');
            (param.options || []).forEach((opt) => {
                const o = document.createElement('option');
                o.value = String(opt);
                o.textContent = String(opt);
                if (String(opt) === String(param.default)) o.selected = true;
                input.appendChild(o);
            });
        } else if (param.type === 'number') {
            input = document.createElement('input');
            input.type = 'number';
            if (param.min !== null && param.min !== undefined) input.min = param.min;
            if (param.max !== null && param.max !== undefined) input.max = param.max;
            if (param.step !== null && param.step !== undefined) input.step = param.step;
            input.value = param.default ?? '';
        } else {
            input = document.createElement('input');
            input.type = 'text';
            input.value = param.default ?? '';
        }
        input.id = `gen_${param.name}`;
        input.dataset.param = param.name;
        input.dataset.type = param.type;
        input.className = 'generator-input';
        wrap.appendChild(input);
        return wrap;
    }

    collectParameters() {
        const params = {};
        document.querySelectorAll('#generatorForm [data-param]').forEach((el) => {
            const name = el.dataset.param;
            const type = el.dataset.type;
            if (type === 'boolean') {
                params[name] = el.checked;
            } else if (type === 'number') {
                if (el.value !== '') params[name] = Number(el.value);
            } else if (type === 'enum') {
                const num = Number(el.value);
                params[name] = (el.value !== '' && !Number.isNaN(num)) ? num : el.value;
            } else {
                params[name] = el.value;
            }
        });
        return params;
    }

    async render(format) {
        if (!this.currentSourceRef) return;
        const statusEl = document.getElementById('generatorViewerStatus');
        const setBusy = (busy) => {
            document.getElementById('generatorPreviewBtn').disabled = busy;
            document.getElementById('generatorRenderBtn').disabled = busy;
        };
        setBusy(true);
        if (statusEl) {
            statusEl.style.display = 'block';
            statusEl.textContent = this._t('generator.rendering', 'Rendering…');
        }
        try {
            const result = await api.post('/generator/render', {
                source_ref: this.currentSourceRef,
                parameters: this.collectParameters(),
                format,
            });
            this.lastRenderId = result.render_id;
            if (format === 'png') {
                this._showPreviewImage(result.render_id);
            } else {
                document.getElementById('generatorSaveBtn').disabled = false;
                await this._showStl(result.render_id);
            }
        } catch (e) {
            const msg = (e && e.message) ? e.message : this._t('generator.renderFailed', 'Render failed');
            this._toast('error', msg);
            if (statusEl) { statusEl.style.display = 'block'; statusEl.textContent = msg; }
        } finally {
            setBusy(false);
        }
    }

    _artifactUrl(renderId, name) {
        return `${api.baseURL.replace(/\/+$/, '')}/generator/render/${renderId}/${name}`;
    }

    _showPreviewImage(renderId) {
        const img = document.getElementById('generatorPreviewImage');
        const viewer = document.getElementById('generatorViewer');
        const statusEl = document.getElementById('generatorViewerStatus');
        if (viewer) viewer.style.display = 'none';
        this._stopAnimation();
        if (img) {
            img.src = this._artifactUrl(renderId, 'preview.png') + `?t=${Date.now()}`;
            img.style.display = 'block';
        }
        if (statusEl) statusEl.style.display = 'none';
    }

    async _showStl(renderId) {
        const img = document.getElementById('generatorPreviewImage');
        const viewer = document.getElementById('generatorViewer');
        const statusEl = document.getElementById('generatorViewerStatus');
        if (img) img.style.display = 'none';

        if (typeof THREE === 'undefined' || typeof THREE.STLLoader === 'undefined') {
            // Fallback: no WebGL libs available, show a PNG preview instead.
            this._toast('warning', this._t('generator.viewerUnavailable', '3D viewer unavailable, showing image'));
            await this.render('png');
            return;
        }
        if (viewer) viewer.style.display = 'block';
        if (statusEl) statusEl.style.display = 'none';
        this._ensureThree();

        const loader = new THREE.STLLoader();
        loader.load(this._artifactUrl(renderId, 'model.stl') + `?t=${Date.now()}`, (geometry) => {
            this._setMesh(geometry);
        }, undefined, () => {
            this._toast('error', this._t('generator.renderFailed', 'Failed to load model'));
        });
    }

    _ensureThree() {
        const container = document.getElementById('generatorViewer');
        if (!container || this.three) return;
        const width = container.clientWidth || 600;
        const height = container.clientHeight || 400;

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x1e1e24);
        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 5000);
        camera.position.set(120, 120, 120);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(width, height);
        container.innerHTML = '';
        container.appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        const dir = new THREE.DirectionalLight(0xffffff, 0.8);
        dir.position.set(1, 1, 1);
        scene.add(dir);

        let controls = null;
        if (typeof THREE.OrbitControls !== 'undefined') {
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
        }

        this.three = { renderer, scene, camera, controls, mesh: null, animationId: null };
        const animate = () => {
            this.three.animationId = requestAnimationFrame(animate);
            if (controls) controls.update();
            renderer.render(scene, camera);
        };
        animate();
    }

    _setMesh(geometry) {
        const { scene, camera, controls } = this.three;
        if (this.three.mesh) {
            scene.remove(this.three.mesh);
            this.three.mesh.geometry.dispose();
            this.three.mesh.material.dispose();
        }
        geometry.computeBoundingBox();
        geometry.center();
        const material = new THREE.MeshPhongMaterial({ color: 0x4a9eda, specular: 0x111111, shininess: 30 });
        const mesh = new THREE.Mesh(geometry, material);
        scene.add(mesh);
        this.three.mesh = mesh;

        // Frame the model.
        const size = new THREE.Vector3();
        geometry.boundingBox.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z) || 50;
        camera.position.set(maxDim * 1.6, maxDim * 1.6, maxDim * 1.6);
        camera.lookAt(0, 0, 0);
        if (controls) { controls.target.set(0, 0, 0); controls.update(); }
    }

    _stopAnimation() {
        if (this.three && this.three.animationId) {
            cancelAnimationFrame(this.three.animationId);
            this.three.animationId = null;
        }
    }

    async saveToLibrary() {
        if (!this.lastRenderId) return;
        try {
            await api.post(`/generator/render/${this.lastRenderId}/save`, {});
            this._toast('success', this._t('generator.saved', 'Saved to library'));
        } catch (e) {
            const msg = (e && e.message) ? e.message : this._t('generator.saveFailed', 'Save failed');
            this._toast('error', msg);
        }
    }

    async handleUpload(event) {
        const file = event.target.files && event.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch(`${api.baseURL.replace(/\/+$/, '')}/generator/upload`, {
                method: 'POST', body: formData,
            });
            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.message || err.detail?.message || 'Upload failed');
            }
            const tpl = await response.json();
            this.setActiveSource(tpl.id, tpl.parameters);
            this._highlightCard(null);
            this._toast('success', this._t('generator.uploaded', 'File uploaded'));
        } catch (e) {
            this._toast('error', e.message);
        } finally {
            event.target.value = '';
        }
    }
}

const generatorManager = new GeneratorManager();

// Reveal the nav entry on startup when OpenSCAD is available.
document.addEventListener('DOMContentLoaded', () => {
    if (typeof api !== 'undefined') {
        generatorManager.checkStatus().catch(() => {});
    }
});
