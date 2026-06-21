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
const { roundedRectangle, rectangle, cylinder, cuboid } = primitives;
const { extrudeLinear, extrudeFromSlices, slice } = extrusions;
const { subtract, union } = booleans;
const { translate } = transforms;
const { mat4 } = maths;
const { geom3, geom2 } = geometries;

// --- Lazy module loader ------------------------------------------------------
// Heavier per-template dependencies (fonts, QR, SVG parsing) are imported from a
// CDN only the first time a template that needs them is built, and the import
// promise is cached so subsequent builds reuse it.
const _moduleCache = new Map();
function loadModule(url) {
    if (!_moduleCache.has(url)) _moduleCache.set(url, import(/* @vite-ignore */ url));
    return _moduleCache.get(url);
}

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

// --- QR matrix → row-merged module runs --------------------------------------
// Merge horizontally-adjacent "on" modules in each row into runs, which keeps
// the geometry to a few hundred boxes instead of one box per module.
function qrModuleRuns(qr, invert) {
    const n = qr.getModuleCount();
    const on = (r, c) => (invert ? !qr.isDark(r, c) : qr.isDark(r, c));
    const runs = [];
    for (let r = 0; r < n; r++) {
        let c = 0;
        while (c < n) {
            if (!on(r, c)) { c++; continue; }
            let c1 = c;
            while (c1 + 1 < n && on(r, c1 + 1)) c1++;
            runs.push([r, c, c1]);
            c = c1 + 1;
        }
    }
    return { n, runs };
}

// --- Text → geometry (opentype.js, lazy-loaded) ------------------------------

let _fontPromise = null;
function loadFont() {
    if (!_fontPromise) {
        _fontPromise = (async () => {
            const mod = await loadModule('https://cdn.jsdelivr.net/npm/opentype.js@1/+esm');
            const opentype = mod.default || mod;
            const url = new URL('../assets/fonts/LiberationSans-Regular.ttf', import.meta.url).href;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error('Could not load font');
            return opentype.parse(await resp.arrayBuffer());
        })().catch((e) => { _fontPromise = null; throw e; });
    }
    return _fontPromise;
}

// Flatten an opentype path into closed contours of [x, y] points. The font
// y-axis points down, so we negate y to get a conventional (y-up) outline.
function glyphContours(font, text, size, curveSteps) {
    const cmds = font.getPath(text, 0, 0, size).commands;
    const steps = curveSteps || 8;
    const contours = [];
    let cur = null;
    let px = 0, py = 0;
    const moveTo = (x, y) => { px = x; py = y; cur.push([x, -y]); };
    for (const c of cmds) {
        if (c.type === 'M') {
            if (cur && cur.length) contours.push(cur);
            cur = [];
            moveTo(c.x, c.y);
        } else if (c.type === 'L') {
            moveTo(c.x, c.y);
        } else if (c.type === 'C') {
            const x0 = px, y0 = py;
            for (let i = 1; i <= steps; i++) {
                const t = i / steps, m = 1 - t;
                const x = m*m*m*x0 + 3*m*m*t*c.x1 + 3*m*t*t*c.x2 + t*t*t*c.x;
                const y = m*m*m*y0 + 3*m*m*t*c.y1 + 3*m*t*t*c.y2 + t*t*t*c.y;
                cur.push([x, -y]);
            }
            px = c.x; py = c.y;
        } else if (c.type === 'Q') {
            const x0 = px, y0 = py;
            for (let i = 1; i <= steps; i++) {
                const t = i / steps, m = 1 - t;
                const x = m*m*x0 + 2*m*t*c.x1 + t*t*c.x;
                const y = m*m*y0 + 2*m*t*c.y1 + t*t*c.y;
                cur.push([x, -y]);
            }
            px = c.x; py = c.y;
        } else if (c.type === 'Z') {
            if (cur && cur.length) contours.push(cur);
            cur = null;
        }
    }
    if (cur && cur.length) contours.push(cur);
    return contours.filter((p) => p.length >= 3);
}

function signedArea(poly) {
    let a = 0;
    for (let i = 0; i < poly.length; i++) {
        const [x1, y1] = poly[i];
        const [x2, y2] = poly[(i + 1) % poly.length];
        a += x1 * y2 - x2 * y1;
    }
    return a / 2;
}

function pointInPoly([x, y], poly) {
    let inside = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
        const [xi, yi] = poly[i];
        const [xj, yj] = poly[j];
        if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) inside = !inside;
    }
    return inside;
}

// Build an extruded, origin-centered solid from text. Holes (letter counters)
// are detected by even-odd containment, not winding, so it is font-agnostic.
function textToSolid(font, text, size, height, curveSteps) {
    const contours = glyphContours(font, text, size, curveSteps);
    if (!contours.length) throw new Error('No printable glyphs in text');
    const solids = [], holes = [];
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    contours.forEach((c, i) => {
        let depth = 0;
        contours.forEach((o, j) => { if (i !== j && pointInPoly(c[0], o)) depth++; });
        const poly = signedArea(c) < 0 ? c.slice().reverse() : c;
        for (const [x, y] of poly) {
            if (x < minX) minX = x; if (x > maxX) maxX = x;
            if (y < minY) minY = y; if (y > maxY) maxY = y;
        }
        const solid = extrudeLinear({ height }, geom2.fromPoints(poly));
        (depth % 2 === 0 ? solids : holes).push(solid);
    });
    let result = solids.length > 1 ? union(solids) : solids[0];
    if (holes.length) result = subtract(result, holes.length > 1 ? union(holes) : holes[0]);
    const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    return { geom: translate([-cx, -cy, 0], result), width: maxX - minX, height: maxY - minY };
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
    text: {
        name: 'Text / Nameplate / Keychain',
        description: 'Embossed or debossed text on an optional plate, with a keychain hole.',
        parameters: [
            { name: 'text', type: 'text', default: 'Porcus3D', group: 'Text', description: 'Text to render' },
            { name: 'font_size', type: 'number', default: 12, min: 4, max: 80, step: 1, group: 'Text', description: 'Text height (mm)' },
            { name: 'text_depth', type: 'number', default: 1.5, min: 0.4, max: 10, step: 0.1, group: 'Text', description: 'Emboss height / deboss depth (mm)' },
            { name: 'mode', type: 'select', default: 'emboss', group: 'Text', description: 'Raised above or cut into the plate', options: [{ value: 'emboss', label: 'Raised (emboss)' }, { value: 'deboss', label: 'Recessed (deboss)' }] },
            { name: 'plate', type: 'select', default: 'rounded', group: 'Plate', description: 'Backing plate style', options: [{ value: 'rounded', label: 'Rounded plate' }, { value: 'rect', label: 'Rectangular plate' }, { value: 'none', label: 'Text only (no plate)' }] },
            { name: 'margin', type: 'number', default: 6, min: 0, max: 40, step: 1, group: 'Plate', description: 'Plate margin around text (mm)' },
            { name: 'plate_thickness', type: 'number', default: 2, min: 0.6, max: 12, step: 0.2, group: 'Plate', description: 'Plate thickness (mm)' },
            { name: 'corner_radius', type: 'number', default: 3, min: 0, max: 30, step: 0.5, group: 'Plate', description: 'Plate corner radius (mm)' },
            { name: 'keychain_hole', type: 'boolean', default: false, group: 'Keychain', description: 'Add a keychain hole (top-left corner)' },
            { name: 'hole_diameter', type: 'number', default: 4, min: 2, max: 15, step: 0.5, group: 'Keychain', description: 'Keychain hole diameter (mm)' },
        ],
        async build(p) {
            const font = await loadFont();
            const noPlate = p.plate === 'none';
            const depth = (p.mode === 'deboss' && !noPlate)
                ? Math.min(p.text_depth, p.plate_thickness - 0.4)
                : p.text_depth;
            const t = textToSolid(font, p.text || ' ', p.font_size, Math.max(depth, 0.2), 8);
            if (noPlate) return t.geom;

            const pw = t.width + 2 * p.margin;
            const ph = t.height + 2 * p.margin;
            const profile = (p.plate === 'rounded' && p.corner_radius > 0)
                ? roundedRectangle({ size: [pw, ph], roundRadius: Math.min(p.corner_radius, Math.min(pw, ph) / 2 - 0.01) })
                : rectangle({ size: [pw, ph] });
            let plate = extrudeLinear({ height: p.plate_thickness }, profile);
            if (p.keychain_hole) {
                const off = Math.max(p.margin / 2, p.hole_diameter / 2 + 1);
                const hole = cylinder({ radius: p.hole_diameter / 2, height: p.plate_thickness + 2,
                    center: [-pw / 2 + off, ph / 2 - off, p.plate_thickness / 2] });
                plate = subtract(plate, hole);
            }
            if (p.mode === 'deboss') {
                return subtract(plate, translate([0, 0, p.plate_thickness - depth], t.geom));
            }
            return union(plate, translate([0, 0, p.plate_thickness], t.geom));
        },
    },
    qr_tag: {
        name: 'QR Tag',
        description: 'A scannable QR code on a plate — e.g. a link back to this model in your Printernizer library.',
        parameters: [
            { name: 'text', type: 'text', default: 'https://github.com/schmacka/printernizer', group: 'Code', description: 'URL or text to encode (e.g. a link to this model in your library)' },
            { name: 'error_correction', type: 'select', default: 'M', group: 'Code', description: 'Error correction (higher = more robust, denser)', options: [{ value: 'L', label: 'L — 7%' }, { value: 'M', label: 'M — 15%' }, { value: 'Q', label: 'Q — 25%' }, { value: 'H', label: 'H — 30%' }] },
            { name: 'mode', type: 'select', default: 'emboss', group: 'Code', description: 'Raised modules or recessed into the plate', options: [{ value: 'emboss', label: 'Raised (emboss)' }, { value: 'deboss', label: 'Recessed (deboss)' }] },
            { name: 'invert', type: 'boolean', default: false, group: 'Code', description: 'Invert (build light modules instead of dark)' },
            { name: 'module_size', type: 'number', default: 2, min: 0.8, max: 6, step: 0.1, group: 'Dimensions', description: 'Size of one QR module (mm)' },
            { name: 'module_height', type: 'number', default: 0.8, min: 0.2, max: 6, step: 0.1, group: 'Dimensions', description: 'Emboss height / deboss depth (mm)' },
            { name: 'plate_thickness', type: 'number', default: 2, min: 0.8, max: 12, step: 0.2, group: 'Dimensions', description: 'Plate thickness (mm)' },
            { name: 'border', type: 'number', default: 4, min: 0, max: 20, step: 0.5, group: 'Dimensions', description: 'Quiet-zone border around the code (mm)' },
            { name: 'corner_radius', type: 'number', default: 2, min: 0, max: 20, step: 0.5, group: 'Style', description: 'Plate corner radius (mm)' },
        ],
        async build(p) {
            // qrcode-generator is already loaded globally (UMD) in index.html;
            // fall back to a lazy CDN import if that ever changes.
            const qrcode = (typeof window !== 'undefined' && window.qrcode)
                ? window.qrcode
                : ((await loadModule('https://cdn.jsdelivr.net/npm/qrcode-generator@1/+esm')).default);
            const qr = qrcode(0, p.error_correction || 'M');
            qr.addData(p.text || ' ');
            qr.make();
            const { n, runs } = qrModuleRuns(qr, p.invert);
            const ms = p.module_size;
            const qrW = n * ms;
            const plateW = qrW + 2 * p.border;
            const plateThk = p.plate_thickness;
            const modH = Math.max(0.2, p.mode === 'deboss' ? Math.min(p.module_height, plateThk - 0.4) : p.module_height);
            const profile = (p.corner_radius > 0)
                ? roundedRectangle({ size: [plateW, plateW], roundRadius: Math.min(p.corner_radius, plateW / 2 - 0.01) })
                : rectangle({ size: [plateW, plateW] });
            const plate = extrudeLinear({ height: plateThk }, profile);
            if (!runs.length) return plate;

            const zc = p.mode === 'deboss' ? plateThk - modH / 2 : plateThk + modH / 2;
            const boxes = runs.map(([r, c0, c1]) => {
                const w = (c1 - c0 + 1) * ms;
                const cx = -qrW / 2 + ((c0 + c1 + 1) / 2) * ms;
                const cy = qrW / 2 - (r + 0.5) * ms;
                return cuboid({ size: [w, ms, modH], center: [cx, cy, zc] });
            });
            if (p.mode === 'deboss') {
                return subtract(plate, boxes.length > 1 ? union(boxes) : boxes[0]);
            }
            // Emboss: merge plate + raised modules into one polygon soup (fast; the
            // boxes sit on top of the plate and the slicer unions the volumes).
            return geom3.create([
                ...geom3.toPolygons(plate),
                ...boxes.flatMap((b) => geom3.toPolygons(b)),
            ]);
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
        } else if (param.type === 'select') {
            input = document.createElement('select');
            (param.options || []).forEach((opt) => {
                const value = (opt && typeof opt === 'object') ? opt.value : opt;
                const text = (opt && typeof opt === 'object') ? (opt.label ?? opt.value) : opt;
                const o = document.createElement('option');
                o.value = value;
                o.textContent = text;
                input.appendChild(o);
            });
            if (param.default !== undefined) input.value = param.default;
        } else if (param.type === 'file') {
            input = document.createElement('input');
            input.type = 'file';
            if (param.accept) input.accept = param.accept;
            // Read the file once on selection and stash the result on the element so
            // collectParameters() can read it synchronously at build time.
            input.addEventListener('change', () => {
                const file = input.files && input.files[0];
                if (!file) { input._fileData = null; return; }
                const reader = new FileReader();
                const asText = /svg|text|json/i.test(file.type) || /\.svg$/i.test(file.name);
                reader.onload = () => {
                    input._fileData = {
                        name: file.name,
                        type: file.type,
                        text: asText ? reader.result : null,
                        dataURL: asText ? null : reader.result,
                    };
                };
                if (asText) reader.readAsText(file);
                else reader.readAsDataURL(file);
            });
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
            else if (type === 'file') params[name] = el._fileData || null;
            else params[name] = el.value;
        });
        return params;
    }

    async generate() {
        if (!this.currentTemplateId) return;
        const statusEl = document.getElementById('generatorViewerStatus');
        const renderBtn = document.getElementById('generatorRenderBtn');
        if (renderBtn) renderBtn.disabled = true;
        if (statusEl) { statusEl.style.display = 'block'; statusEl.textContent = this._t('generator.generating', 'Generating…'); }
        try {
            const tpl = TEMPLATES[this.currentTemplateId];
            // build() may be sync or async (templates that load fonts/images/SVG).
            const geom = await tpl.build(this.collectParameters());
            this.currentGeom = geom;
            this._showGeom(geom);
            document.getElementById('generatorSaveBtn').disabled = false;
        } catch (e) {
            const msg = (e && e.message) ? e.message : this._t('generator.renderFailed', 'Generation failed');
            this._toast('error', msg);
            if (statusEl) { statusEl.style.display = 'block'; statusEl.textContent = msg; }
        } finally {
            if (renderBtn) renderBtn.disabled = false;
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
