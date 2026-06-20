/**
 * Model Generator — browser-side (JSCAD).
 *
 * Geometry is generated entirely in the browser with JSCAD, shown in a three.js
 * viewer, and the resulting STL is uploaded to the server to be stored in the
 * Library. Nothing CAD-related runs on the server, so this works on every
 * deployment architecture (incl. Raspberry Pi / aarch64).
 *
 * Loaded as an ES module; uses the global `api`, `showToast`, `t`, `escapeHtml`
 * and `THREE` provided by the classic scripts loaded before it.
 */
import jscad from 'https://cdn.jsdelivr.net/npm/@jscad/modeling@2/+esm';
import stlSerializer from 'https://cdn.jsdelivr.net/npm/@jscad/stl-serializer@2/+esm';

const { primitives, booleans, transforms, extrusions, geometries, maths } = jscad;
const { roundedRectangle, rectangle } = primitives;
const { extrudeLinear, extrudeFromSlices, slice } = extrusions;
const { subtract } = booleans;
const { translate } = transforms;
const { mat4 } = maths;
const { geom3 } = geometries;

// --- Bundled templates (build function + parameter schema) -------------------

function boxShell(w, d, h, r) {
    const profile = (r && r > 0)
        ? roundedRectangle({ size: [w, d], roundRadius: Math.min(r, Math.min(w, d) / 2 - 0.01) })
        : rectangle({ size: [w, d] });
    return extrudeLinear({ height: h }, profile);
}

function ringPoints(radius, facets) {
    const n = (facets && facets >= 3) ? facets : 64;
    const pts = [];
    for (let i = 0; i < n; i++) {
        const a = 2 * Math.PI * i / n;
        pts.push([radius * Math.cos(a), radius * Math.sin(a)]);
    }
    return pts;
}

function vaseSolid(baseRadius, p) {
    const base = slice.fromPoints(ringPoints(baseRadius, p.facets));
    return extrudeFromSlices({
        numberOfSlices: 48,
        callback: (progress) => {
            const s = 1 + (p.top_scale - 1) * progress;
            const ang = (p.twist * progress) * Math.PI / 180;
            const m = mat4.multiply(mat4.create(),
                mat4.fromTranslation(mat4.create(), [0, 0, p.height * progress]),
                mat4.multiply(mat4.create(),
                    mat4.fromZRotation(mat4.create(), ang),
                    mat4.fromScaling(mat4.create(), [s, s, 1])));
            return slice.transform(m, base);
        },
    }, base);
}

const TEMPLATES = {
    box: {
        name: 'Parametric Box',
        description: 'A rectangular box with configurable dimensions, wall thickness and rounded corners.',
        parameters: [
            { name: 'width', type: 'number', default: 80, min: 20, max: 300, step: 1, group: 'Dimensions', description: 'Inner width (mm)' },
            { name: 'depth', type: 'number', default: 60, min: 20, max: 300, step: 1, group: 'Dimensions', description: 'Inner depth (mm)' },
            { name: 'height', type: 'number', default: 40, min: 10, max: 300, step: 1, group: 'Dimensions', description: 'Inner height (mm)' },
            { name: 'wall_thickness', type: 'number', default: 2, min: 1, max: 8, step: 0.5, group: 'Dimensions', description: 'Wall thickness (mm)' },
            { name: 'corner_radius', type: 'number', default: 3, min: 0, max: 20, step: 0.5, group: 'Style', description: 'Corner rounding radius (mm, 0 = sharp)' },
            { name: 'closed_bottom', type: 'boolean', default: true, group: 'Style', description: 'Add a solid bottom' },
        ],
        build(p) {
            const ow = p.width + 2 * p.wall_thickness;
            const od = p.depth + 2 * p.wall_thickness;
            const oh = p.height + (p.closed_bottom ? p.wall_thickness : 0);
            const outer = boxShell(ow, od, oh, p.corner_radius);
            let inner = boxShell(p.width, p.depth, p.height + 1, Math.max(0, p.corner_radius - p.wall_thickness));
            inner = translate([0, 0, p.closed_bottom ? p.wall_thickness : -1], inner);
            return subtract(outer, inner);
        },
    },
    vase: {
        name: 'Parametric Vase',
        description: 'A round or faceted vase with configurable taper, twist and wall thickness.',
        parameters: [
            { name: 'diameter', type: 'number', default: 60, min: 20, max: 250, step: 1, group: 'Dimensions', description: 'Base diameter (mm)' },
            { name: 'height', type: 'number', default: 120, min: 20, max: 400, step: 1, group: 'Dimensions', description: 'Height (mm)' },
            { name: 'wall_thickness', type: 'number', default: 2, min: 1, max: 8, step: 0.5, group: 'Dimensions', description: 'Wall thickness (mm)' },
            { name: 'top_scale', type: 'number', default: 0.7, min: 0.2, max: 2, step: 0.05, group: 'Shape', description: 'Top radius relative to base (1 = straight)' },
            { name: 'facets', type: 'number', default: 0, min: 0, max: 12, step: 1, group: 'Shape', description: 'Number of sides (0 = round)' },
            { name: 'twist', type: 'number', default: 0, min: -360, max: 360, step: 5, group: 'Shape', description: 'Total twist over the height (degrees)' },
        ],
        build(p) {
            const outer = vaseSolid(p.diameter / 2, p);
            let inner = vaseSolid(p.diameter / 2 - p.wall_thickness, p);
            inner = translate([0, 0, p.wall_thickness], inner);
            return subtract(outer, inner);
        },
    },
};

// --- Manager ----------------------------------------------------------------

class GeneratorManager {
    constructor() {
        this.currentTemplateId = null;
        this.currentParameters = [];
        this.currentGeom = null;
        this.three = null;
        this._initialized = false;
    }

    _t(key, fallback) { return (typeof t === 'function') ? t(key) : fallback; }

    _toast(type, message) {
        if (typeof showToast === 'function') {
            showToast(type, this._t('generator.pageTitle', 'Generator'), message);
        } else {
            console.log(`[generator:${type}] ${message}`);
        }
    }

    async init() {
        this._revealNav();
        if (this._initialized) return;
        this._initialized = true;
        document.getElementById('generatorRenderBtn')?.addEventListener('click', () => this.generate());
        document.getElementById('generatorSaveBtn')?.addEventListener('click', () => this.saveToLibrary());
        this.renderTemplateList();
    }

    cleanup() { this._stopAnimation(); }

    // Generator is always available (browser-side engine); just reveal the nav.
    async checkStatus() { this._revealNav(); }

    _revealNav() {
        // Nav link is managed by navigation-preferences; only toggle page-level divs.
        const layout = document.getElementById('generatorLayout');
        if (layout) layout.style.display = '';
        const unavailable = document.getElementById('generatorUnavailable');
        if (unavailable) unavailable.style.display = 'none';
    }

    renderTemplateList() {
        const container = document.getElementById('generatorTemplates');
        if (!container) return;
        container.innerHTML = '';
        Object.entries(TEMPLATES).forEach(([id, tpl]) => {
            const card = document.createElement('button');
            card.type = 'button';
            card.className = 'generator-template-card';
            card.dataset.id = id;
            card.innerHTML = `<strong>${escapeHtml(tpl.name)}</strong>` +
                (tpl.description ? `<span>${escapeHtml(tpl.description)}</span>` : '');
            card.addEventListener('click', () => this.selectTemplate(id));
            container.appendChild(card);
        });
    }

    selectTemplate(templateId) {
        const tpl = TEMPLATES[templateId];
        if (!tpl) return;
        this.currentTemplateId = templateId;
        this.currentParameters = tpl.parameters;
        this.currentGeom = null;
        this.buildForm();
        this._highlightCard(templateId);
        document.getElementById('generatorRenderBtn').disabled = false;
        document.getElementById('generatorSaveBtn').disabled = true;
    }

    _highlightCard(id) {
        document.querySelectorAll('.generator-template-card').forEach((el) => {
            el.classList.toggle('active', el.dataset.id === id);
        });
    }

    buildForm() {
        const form = document.getElementById('generatorForm');
        if (!form) return;
        form.innerHTML = '';
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
        } else if (param.type === 'number') {
            input = document.createElement('input');
            input.type = 'number';
            if (param.min !== undefined) input.min = param.min;
            if (param.max !== undefined) input.max = param.max;
            if (param.step !== undefined) input.step = param.step;
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
            if (type === 'boolean') params[name] = el.checked;
            else if (type === 'number') params[name] = el.value === '' ? 0 : Number(el.value);
            else params[name] = el.value;
        });
        return params;
    }

    generate() {
        if (!this.currentTemplateId) return;
        const statusEl = document.getElementById('generatorViewerStatus');
        try {
            const tpl = TEMPLATES[this.currentTemplateId];
            const geom = tpl.build(this.collectParameters());
            this.currentGeom = geom;
            this._showGeom(geom);
            document.getElementById('generatorSaveBtn').disabled = false;
        } catch (e) {
            const msg = (e && e.message) ? e.message : this._t('generator.renderFailed', 'Generation failed');
            this._toast('error', msg);
            if (statusEl) { statusEl.style.display = 'block'; statusEl.textContent = msg; }
        }
    }

    async saveToLibrary() {
        if (!this.currentGeom) return;
        try {
            const data = stlSerializer.serialize({ binary: true }, this.currentGeom);
            const blob = new Blob(data, { type: 'model/stl' });
            const fd = new FormData();
            fd.append('file', blob, `${this.currentTemplateId}.stl`);
            fd.append('template_id', this.currentTemplateId);
            fd.append('parameters', JSON.stringify(this.collectParameters()));

            const base = api.baseURL.replace(/\/+$/, '');
            const resp = await fetch(`${base}/generator/save`, { method: 'POST', body: fd });
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.message || err.detail?.message || 'Save failed');
            }
            this._toast('success', this._t('generator.saved', 'Saved to library'));
        } catch (e) {
            this._toast('error', e.message || this._t('generator.saveFailed', 'Save failed'));
        }
    }

    // --- three.js viewer ----------------------------------------------------

    _geomToBufferGeometry(geom) {
        const polys = geom3.toPolygons(geom);
        const positions = [];
        for (const poly of polys) {
            const vs = poly.vertices;
            for (let i = 2; i < vs.length; i++) {
                positions.push(vs[0][0], vs[0][1], vs[0][2]);
                positions.push(vs[i - 1][0], vs[i - 1][1], vs[i - 1][2]);
                positions.push(vs[i][0], vs[i][1], vs[i][2]);
            }
        }
        const g = new THREE.BufferGeometry();
        g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        g.computeVertexNormals();
        return g;
    }

    _showGeom(geom) {
        const viewer = document.getElementById('generatorViewer');
        const statusEl = document.getElementById('generatorViewerStatus');
        if (statusEl) statusEl.style.display = 'none';
        if (typeof THREE === 'undefined') {
            this._toast('warning', this._t('generator.viewerUnavailable', '3D viewer unavailable'));
            return;
        }
        if (viewer) viewer.style.display = 'block';
        this._ensureThree();
        this._setMesh(this._geomToBufferGeometry(geom));
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
}

const generatorManager = new GeneratorManager();
// Expose to the classic-script app (main.js looks up window.generatorManager).
window.generatorManager = generatorManager;

document.addEventListener('DOMContentLoaded', () => {
    generatorManager.checkStatus().catch(() => {});
});
