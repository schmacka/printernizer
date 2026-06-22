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
const { roundedRectangle, rectangle, cylinder, cuboid, circle } = primitives;
const { extrudeLinear, extrudeFromSlices, slice } = extrusions;
const { subtract, union } = booleans;
const { translate, rotate } = transforms;
const { mat4 } = maths;
const { geom3, geom2, path2, poly3 } = geometries;

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

// Extrude a set of 2D outlines into a solid, treating nested loops as holes by
// even-odd containment (winding-agnostic). Shared by the text and SVG templates.
function outlinesToSolid(outlines, height) {
    const loops = outlines.filter((o) => o.length >= 3);
    if (!loops.length) throw new Error('No closed regions to extrude');
    const solids = [], holes = [];
    loops.forEach((c, i) => {
        let depth = 0;
        loops.forEach((o, j) => { if (i !== j && pointInPoly(c[0], o)) depth++; });
        const poly = signedArea(c) < 0 ? c.slice().reverse() : c;
        (depth % 2 === 0 ? solids : holes).push(extrudeLinear({ height }, geom2.fromPoints(poly)));
    });
    let result = solids.length > 1 ? union(solids) : solids[0];
    if (holes.length) result = subtract(result, holes.length > 1 ? union(holes) : holes[0]);
    return result;
}

function boundsOf(outlines) {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const o of outlines) for (const [x, y] of o) {
        if (x < minX) minX = x; if (x > maxX) maxX = x;
        if (y < minY) minY = y; if (y > maxY) maxY = y;
    }
    return { minX, maxX, minY, maxY };
}

// Build an extruded, origin-centered solid from text. Holes (letter counters)
// are detected by even-odd containment, so it is font-agnostic.
function textToSolid(font, text, size, height, curveSteps) {
    const contours = glyphContours(font, text, size, curveSteps);
    if (!contours.length) throw new Error('No printable glyphs in text');
    const b = boundsOf(contours);
    const cx = (b.minX + b.maxX) / 2, cy = (b.minY + b.maxY) / 2;
    return {
        geom: translate([-cx, -cy, 0], outlinesToSolid(contours, height)),
        width: b.maxX - b.minX,
        height: b.maxY - b.minY,
    };
}

// Decompose a JSCAD svg-deserializer result (path2 + clean geom2 primitives)
// into 2D outlines, with Y negated so the part is not mirrored.
function svgOutlines(geoms) {
    const arr = Array.isArray(geoms) ? geoms : [geoms];
    const outlines = [];
    for (const x of arr) {
        if (x && x.points !== undefined) {
            const pts = path2.toPoints(x);
            if (pts.length >= 3) outlines.push(pts.map((q) => [q[0], -q[1]]));
        } else if (x && x.sides) {
            try {
                for (const loop of geom2.toOutlines(x)) {
                    if (loop.length >= 3) outlines.push(loop.map((q) => [q[0], -q[1]]));
                }
            } catch (e) { /* skip a region the deserializer left unclosed */ }
        }
    }
    return outlines;
}

// Turn a row-major grid of heights into a watertight geom3: top surface,
// perimeter walls down to z=0, and a fanned flat bottom.
function heightmapToGeom3(heights, cellW, cellH) {
    const rows = heights.length, cols = heights[0].length;
    const X = (c) => c * cellW;
    const Y = (r) => (rows - 1 - r) * cellH;        // image row 0 at the top (+Y)
    const topV = (c, r) => [X(c), Y(r), heights[r][c]];
    const botV = (c, r) => [X(c), Y(r), 0];
    const polys = [];
    const tri = (a, b, c) => polys.push(poly3.create([a, b, c]));
    for (let r = 0; r < rows - 1; r++) {
        for (let c = 0; c < cols - 1; c++) {
            const v00 = topV(c, r), v10 = topV(c + 1, r), v01 = topV(c, r + 1), v11 = topV(c + 1, r + 1);
            tri(v00, v11, v10); tri(v00, v01, v11);
        }
    }
    const peri = [];
    for (let c = 0; c < cols; c++) peri.push([c, 0]);
    for (let r = 1; r < rows; r++) peri.push([cols - 1, r]);
    for (let c = cols - 2; c >= 0; c--) peri.push([c, rows - 1]);
    for (let r = rows - 2; r >= 1; r--) peri.push([0, r]);
    for (let i = 0; i < peri.length; i++) {
        const [ca, ra] = peri[i], [cb, rb] = peri[(i + 1) % peri.length];
        tri(topV(ca, ra), topV(cb, rb), botV(cb, rb));
        tri(topV(ca, ra), botV(cb, rb), botV(ca, ra));
    }
    const [c0, r0] = peri[0];
    for (let i = 1; i < peri.length - 1; i++) {
        const [c1, r1] = peri[i], [c2, r2] = peri[i + 1];
        tri(botV(c0, r0), botV(c2, r2), botV(c1, r1));
    }
    return geom3.create(polys);
}

// --- Functional-part helpers -------------------------------------------------

// CCW perimeter points of a rounded rectangle centered at the origin.
function roundedRectPoints(w, d, r, seg) {
    r = Math.max(0.05, Math.min(r, Math.min(w, d) / 2 - 0.01));
    const s = seg || 8;
    const hx = w / 2 - r, hy = d / 2 - r;
    const corners = [[hx, hy, 0], [-hx, hy, 90], [-hx, -hy, 180], [hx, -hy, 270]];
    const pts = [];
    for (const [cx, cy, a0] of corners) {
        for (let i = 0; i <= s; i++) {
            const a = (a0 + 90 * i / s) * Math.PI / 180;
            pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
        }
    }
    return pts;
}

// Gridfinity constants and the standard base "foot" profile (bottom → top):
// 0.8mm @45°, 1.8mm straight, 2.15mm @45°. Built by lofting a rounded-rect
// outline that is inset toward the bottom. Reused (positive) by the bin and
// (as a slightly oversized cutter) by the baseplate.
const GF = { GRID: 42, HEIGHT_UNIT: 7, BASE_H: 4.75, CLEAR: 0.5, OUTER_R: 4 };
const GF_FOOT_KP = [
    { z: 0, inset: 2.95 },
    { z: 0.8, inset: 2.15 },
    { z: 2.6, inset: 2.15 },
    { z: GF.BASE_H, inset: 0 },
];
function gridfinityFoot(topSize, topR) {
    const sliceAt = (kp) => {
        const w = topSize - 2 * kp.inset;
        const r = Math.max(0.1, topR - kp.inset);
        const m = mat4.fromTranslation(mat4.create(), [0, 0, kp.z]);
        return slice.transform(m, slice.fromPoints(roundedRectPoints(w, w, r, 8)));
    };
    return extrudeFromSlices({
        numberOfSlices: GF_FOOT_KP.length,
        callback: (progress, i) => sliceAt(GF_FOOT_KP[Math.min(i, GF_FOOT_KP.length - 1)]),
    }, sliceAt(GF_FOOT_KP[0]));
}

// Grid of cell centers, centered on the origin (spacing = GF.GRID).
function cellCenters(gx, gy) {
    const out = [];
    for (let i = 0; i < gx; i++) {
        for (let j = 0; j < gy; j++) {
            out.push([(i - (gx - 1) / 2) * GF.GRID, (j - (gy - 1) / 2) * GF.GRID]);
        }
    }
    return out;
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
    gridfinity_bin: {
        name: 'Gridfinity Bin',
        description: 'A Gridfinity-compatible storage bin (42mm grid, 7mm height units) with optional magnet/screw holes.',
        parameters: [
            { name: 'grid_x', type: 'number', default: 1, min: 1, max: 6, step: 1, group: 'Grid', description: 'Width in grid units (× 42mm)' },
            { name: 'grid_y', type: 'number', default: 2, min: 1, max: 6, step: 1, group: 'Grid', description: 'Depth in grid units (× 42mm)' },
            { name: 'height_units', type: 'number', default: 3, min: 2, max: 14, step: 1, group: 'Grid', description: 'Height in units (× 7mm)' },
            { name: 'wall_thickness', type: 'number', default: 1.2, min: 0.8, max: 4, step: 0.1, group: 'Walls', description: 'Wall thickness (mm)' },
            { name: 'magnet_holes', type: 'boolean', default: false, group: 'Base', description: 'Add 6mm magnet holes' },
            { name: 'screw_holes', type: 'boolean', default: false, group: 'Base', description: 'Add 3mm screw holes' },
        ],
        build(p) {
            const { GRID, HEIGHT_UNIT, BASE_H, CLEAR, OUTER_R } = GF;
            const outerW = p.grid_x * GRID - CLEAR;
            const outerD = p.grid_y * GRID - CLEAR;
            const totalH = p.height_units * HEIGHT_UNIT;
            const offsets = [[13, 13], [13, -13], [-13, 13], [-13, -13]];
            const feet = cellCenters(p.grid_x, p.grid_y).map(([cx, cy]) => {
                let foot = gridfinityFoot(GRID - CLEAR, OUTER_R);
                const cutters = [];
                // Spec (gridfinity-rebuilt): 6.5mm magnet ×2.4mm deep, 3mm screw,
                // holes 8mm in from each cell edge → 13mm from the cell centre.
                offsets.forEach(([ox, oy]) => {
                    if (p.magnet_holes) cutters.push(cylinder({ radius: 3.25, height: 2.4, segments: 32, center: [ox, oy, 1.2] }));
                    if (p.screw_holes) cutters.push(cylinder({ radius: 1.5, height: BASE_H + 1, segments: 24, center: [ox, oy, (BASE_H + 1) / 2] }));
                });
                if (cutters.length) foot = subtract(foot, cutters.length > 1 ? union(cutters) : cutters[0]);
                return translate([cx, cy, 0], foot);
            });
            const base = feet.length > 1 ? union(feet) : feet[0];
            const upper = translate([0, 0, BASE_H], extrudeLinear({ height: totalH - BASE_H },
                roundedRectangle({ size: [outerW, outerD], roundRadius: OUTER_R })));
            const body = union(base, upper);
            const cavity = translate([0, 0, BASE_H], extrudeLinear({ height: totalH },
                roundedRectangle({ size: [outerW - 2 * p.wall_thickness, outerD - 2 * p.wall_thickness], roundRadius: Math.max(0.5, OUTER_R - p.wall_thickness) })));
            return subtract(body, cavity);
        },
    },
    gridfinity_baseplate: {
        name: 'Gridfinity Baseplate',
        description: 'A Gridfinity baseplate that bins drop into (42mm grid).',
        parameters: [
            { name: 'grid_x', type: 'number', default: 2, min: 1, max: 8, step: 1, group: 'Grid', description: 'Width in grid units (× 42mm)' },
            { name: 'grid_y', type: 'number', default: 2, min: 1, max: 8, step: 1, group: 'Grid', description: 'Depth in grid units (× 42mm)' },
            { name: 'floor_thickness', type: 'number', default: 1, min: 0.6, max: 6, step: 0.2, group: 'Base', description: 'Solid floor under the cells (mm)' },
            { name: 'screw_holes', type: 'boolean', default: false, group: 'Base', description: 'Add 3mm mounting screw holes' },
        ],
        build(p) {
            const { GRID, BASE_H, CLEAR, OUTER_R } = GF;
            const outerW = p.grid_x * GRID;
            const outerD = p.grid_y * GRID;
            const plateH = BASE_H + p.floor_thickness;
            const block = extrudeLinear({ height: plateH },
                roundedRectangle({ size: [outerW, outerD], roundRadius: OUTER_R }));
            const centers = cellCenters(p.grid_x, p.grid_y);
            const pockets = centers.map(([cx, cy]) =>
                translate([cx, cy, plateH - BASE_H], gridfinityFoot(GRID - CLEAR + 0.25, OUTER_R)));
            let plate = subtract(block, pockets.length > 1 ? union(pockets) : pockets[0]);
            if (p.screw_holes) {
                const holes = centers.map(([cx, cy]) =>
                    cylinder({ radius: 1.5, height: plateH + 2, segments: 24, center: [cx, cy, plateH / 2] }));
                plate = subtract(plate, holes.length > 1 ? union(holes) : holes[0]);
            }
            return plate;
        },
    },
    bracket: {
        name: 'Bracket / Mounting Plate',
        description: 'A flat mounting plate or right-angle (L) bracket with corner bolt holes.',
        parameters: [
            { name: 'shape', type: 'select', default: 'flat', group: 'Shape', description: 'Plate style', options: [{ value: 'flat', label: 'Flat plate' }, { value: 'L', label: 'L-bracket' }] },
            { name: 'length', type: 'number', default: 60, min: 15, max: 300, step: 1, group: 'Shape', description: 'Base length, X (mm)' },
            { name: 'width', type: 'number', default: 40, min: 15, max: 300, step: 1, group: 'Shape', description: 'Width, Y (mm)' },
            { name: 'leg_height', type: 'number', default: 40, min: 15, max: 300, step: 1, group: 'Shape', description: 'Vertical leg height, Z — L only (mm)' },
            { name: 'thickness', type: 'number', default: 4, min: 1.5, max: 20, step: 0.5, group: 'Shape', description: 'Material thickness (mm)' },
            { name: 'hole_diameter', type: 'number', default: 5, min: 2, max: 20, step: 0.5, group: 'Holes', description: 'Bolt hole diameter (mm)' },
            { name: 'hole_inset', type: 'number', default: 8, min: 4, max: 40, step: 0.5, group: 'Holes', description: 'Hole inset from edges (mm)' },
            { name: 'countersink', type: 'boolean', default: false, group: 'Holes', description: 'Counterbore the top of flat-plate holes' },
        ],
        build(p) {
            const th = p.thickness, hr = p.hole_diameter / 2, ins = p.hole_inset;
            // Vertical (Z-axis) holes through a plate occupying z 0..th.
            const vHole = (x, y) => {
                const c = [cylinder({ radius: hr, height: th + 2, segments: 24, center: [x, y, th / 2] })];
                if (p.countersink) c.push(cylinder({ radius: hr + 1.4, height: th * 0.5 + 0.1, segments: 24, center: [x, y, th - th * 0.25 + 0.05] }));
                return c.length > 1 ? union(c) : c[0];
            };
            const cornerXY = (lx, ly) => [
                [lx / 2 - ins, ly / 2 - ins], [lx / 2 - ins, -(ly / 2 - ins)],
                [-(lx / 2 - ins), ly / 2 - ins], [-(lx / 2 - ins), -(ly / 2 - ins)],
            ];
            const legA = extrudeLinear({ height: th }, roundedRectangle({ size: [p.length, p.width], roundRadius: 2 }));
            const aHoles = cornerXY(p.length, p.width).map(([x, y]) => vHole(x, y));
            let plate = subtract(legA, union(aHoles));
            if (p.shape === 'flat') return plate;
            // L-bracket: vertical leg rising at the back edge (x = -length/2).
            const legB = cuboid({ size: [th, p.width, p.leg_height], center: [-p.length / 2 + th / 2, 0, p.leg_height / 2] });
            let geom = union(plate, legB);
            // Horizontal (X-axis) holes through the vertical leg.
            const bHole = (y, z) => rotate([0, Math.PI / 2, 0],
                cylinder({ radius: hr, height: th + 2, segments: 24, center: [z, y, -p.length / 2 + th / 2] }));
            const bHoles = [[p.width / 2 - ins, p.leg_height - ins], [-(p.width / 2 - ins), p.leg_height - ins]]
                .map(([y, z]) => bHole(y, z));
            return subtract(geom, union(bHoles));
        },
    },
    standoff: {
        name: 'Standoff / Spacer',
        description: 'A round or hex standoff/spacer, optionally with a through hole.',
        parameters: [
            { name: 'shape', type: 'select', default: 'round', group: 'Body', description: 'Outer shape', options: [{ value: 'round', label: 'Round' }, { value: 'hex', label: 'Hex' }] },
            { name: 'outer_size', type: 'number', default: 8, min: 3, max: 40, step: 0.5, group: 'Body', description: 'Outer diameter / across-flats (mm)' },
            { name: 'height', type: 'number', default: 10, min: 2, max: 100, step: 0.5, group: 'Body', description: 'Height (mm)' },
            { name: 'through_hole', type: 'boolean', default: true, group: 'Bore', description: 'Add a through hole' },
            { name: 'inner_diameter', type: 'number', default: 3.2, min: 1, max: 30, step: 0.1, group: 'Bore', description: 'Bore diameter (mm)' },
        ],
        build(p) {
            const isHex = p.shape === 'hex';
            const outerR = isHex ? p.outer_size / Math.sqrt(3) : p.outer_size / 2;
            let body = cylinder({ radius: outerR, height: p.height, segments: isHex ? 6 : 48, center: [0, 0, p.height / 2] });
            if (p.through_hole) {
                body = subtract(body, cylinder({ radius: p.inner_diameter / 2, height: p.height + 2, segments: 48, center: [0, 0, p.height / 2] }));
            }
            return body;
        },
    },
    cable_clip: {
        name: 'Cable Clip',
        description: 'A snap-over cable clip on a screw-down foot, for routing cables along a surface.',
        parameters: [
            { name: 'cable_diameter', type: 'number', default: 6, min: 2, max: 40, step: 0.5, group: 'Clip', description: 'Cable diameter (mm)' },
            { name: 'wall', type: 'number', default: 2, min: 1, max: 8, step: 0.5, group: 'Clip', description: 'Ring wall thickness (mm)' },
            { name: 'clip_width', type: 'number', default: 8, min: 3, max: 40, step: 1, group: 'Clip', description: 'Clip width along the cable (mm)' },
            { name: 'opening', type: 'number', default: 0.6, min: 0.2, max: 0.95, step: 0.05, group: 'Clip', description: 'Snap opening (fraction of cable diameter)' },
            { name: 'base_thickness', type: 'number', default: 3, min: 1.5, max: 10, step: 0.5, group: 'Foot', description: 'Foot thickness (mm)' },
            { name: 'screw_diameter', type: 'number', default: 4, min: 0, max: 12, step: 0.5, group: 'Foot', description: 'Screw hole diameter (0 = none)' },
        ],
        build(p) {
            const Ri = p.cable_diameter / 2, Ro = Ri + p.wall, cw = p.clip_width, bt = p.base_thickness;
            const gap = Math.max(1.5, p.cable_diameter * p.opening);
            let ring2d = subtract(circle({ radius: Ro, segments: 48 }), circle({ radius: Ri, segments: 48 }));
            ring2d = subtract(ring2d, rectangle({ size: [gap, Ro + 5], center: [0, Ro / 2 + 2.5] }));
            // Extrude the annulus, center it, then lay the tube axis along Y; the
            // top opening ends up facing up (+Z).
            let ring = rotate([Math.PI / 2, 0, 0], translate([0, 0, -cw / 2], extrudeLinear({ height: cw }, ring2d)));
            ring = translate([0, 0, Ro + bt], ring);
            const footW = Ro * 2 + 6, footL = cw + 4;
            const foot = extrudeLinear({ height: bt }, roundedRectangle({ size: [footW, footL], roundRadius: Math.min(3, bt) }));
            let body = union(foot, ring);
            if (p.screw_diameter > 0) {
                const sr = p.screw_diameter / 2;
                const holes = [footL / 2 - sr - 1.5, -(footL / 2 - sr - 1.5)].map((y) => union(
                    cylinder({ radius: sr, height: bt + 2, segments: 24, center: [0, y, bt / 2] }),
                    cylinder({ radius: sr + 1.2, height: bt * 0.5 + 0.1, segments: 24, center: [0, y, bt - bt * 0.25 + 0.05] }),
                ));
                body = subtract(body, union(holes));
            }
            return body;
        },
    },
    svg_extrude: {
        name: 'SVG → Extrude',
        description: 'Turn an uploaded SVG (logo, icon, outline) into a 3D part. Holes are preserved.',
        parameters: [
            { name: 'file', type: 'file', accept: '.svg,image/svg+xml', group: 'Source', description: 'SVG file to extrude' },
            { name: 'height', type: 'number', default: 3, min: 0.4, max: 50, step: 0.2, group: 'Extrude', description: 'Extrude height (mm)' },
            { name: 'target_size', type: 'number', default: 60, min: 0, max: 300, step: 1, group: 'Extrude', description: 'Scale longest side to (mm, 0 = keep SVG size)' },
            { name: 'base_thickness', type: 'number', default: 0, min: 0, max: 20, step: 0.2, group: 'Base', description: 'Backing plate thickness (mm, 0 = none)' },
            { name: 'base_margin', type: 'number', default: 3, min: 0, max: 30, step: 0.5, group: 'Base', description: 'Backing plate margin (mm)' },
        ],
        async build(p) {
            if (!p.file || !p.file.text) throw new Error('Upload an SVG file first');
            const mod = await loadModule('https://cdn.jsdelivr.net/npm/@jscad/svg-deserializer@2/+esm');
            const deserialize = mod.deserialize || (mod.default && mod.default.deserialize);
            if (typeof deserialize !== 'function') throw new Error('SVG parser unavailable');
            const outlines = svgOutlines(deserialize({ output: 'geometry', target: 'path2' }, p.file.text));
            if (!outlines.length) throw new Error('No usable shapes found in the SVG');
            const b = boundsOf(outlines);
            const maxDim = Math.max(b.maxX - b.minX, b.maxY - b.minY) || 1;
            const sf = p.target_size > 0 ? p.target_size / maxDim : 1;
            const cx = (b.minX + b.maxX) / 2, cy = (b.minY + b.maxY) / 2;
            const placed = outlines.map((o) => o.map(([x, y]) => [(x - cx) * sf, (y - cy) * sf]));
            let solid = outlinesToSolid(placed, p.height);
            if (p.base_thickness > 0) {
                const sb = boundsOf(placed);
                const w = (sb.maxX - sb.minX) + 2 * p.base_margin;
                const d = (sb.maxY - sb.minY) + 2 * p.base_margin;
                const plate = extrudeLinear({ height: p.base_thickness },
                    roundedRectangle({ size: [w, d], roundRadius: Math.min(2, p.base_margin || 0.1) }));
                solid = union(plate, translate([0, 0, p.base_thickness], solid));
            }
            return solid;
        },
    },
    lithophane: {
        name: 'Lithophane',
        description: 'Convert a photo into a backlit lithophane — darker areas print thicker.',
        parameters: [
            { name: 'file', type: 'file', accept: 'image/*', group: 'Source', description: 'Image to convert' },
            { name: 'width', type: 'number', default: 100, min: 20, max: 250, step: 1, group: 'Size', description: 'Width (mm, height follows aspect)' },
            { name: 'min_thickness', type: 'number', default: 0.8, min: 0.4, max: 5, step: 0.1, group: 'Thickness', description: 'Thinnest (brightest) areas (mm)' },
            { name: 'max_thickness', type: 'number', default: 3, min: 1, max: 12, step: 0.1, group: 'Thickness', description: 'Thickest (darkest) areas (mm)' },
            { name: 'resolution', type: 'number', default: 200, min: 40, max: 350, step: 10, group: 'Quality', description: 'Samples across the width (higher = finer, slower)' },
            { name: 'invert', type: 'boolean', default: false, group: 'Thickness', description: 'Invert (bright areas print thicker)' },
        ],
        async build(p) {
            if (!p.file || !p.file.dataURL) throw new Error('Upload an image first');
            if (typeof document === 'undefined') throw new Error('Image decoding needs a browser');
            const img = new Image();
            img.src = p.file.dataURL;
            await img.decode();
            const cols = Math.max(2, Math.min(Math.round(p.resolution), 400));
            const rows = Math.max(2, Math.round(cols * img.height / img.width));
            const canvas = document.createElement('canvas');
            canvas.width = cols; canvas.height = rows;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, cols, rows);
            const data = ctx.getImageData(0, 0, cols, rows).data;
            const minT = p.min_thickness, maxT = Math.max(p.max_thickness, minT + 0.1);
            const heights = [];
            for (let r = 0; r < rows; r++) {
                const row = [];
                for (let c = 0; c < cols; c++) {
                    const i = (r * cols + c) * 4;
                    const a = data[i + 3] / 255;
                    let lum = (0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2]) / 255;
                    lum = lum * a + (1 - a);                 // transparent → bright (thin)
                    const t = p.invert ? lum : (1 - lum);    // default: dark → thick
                    row.push(minT + t * (maxT - minT));
                }
                heights.push(row);
            }
            const cell = p.width / (cols - 1);
            const geom = heightmapToGeom3(heights, cell, cell);
            return translate([-(cols - 1) * cell / 2, -(rows - 1) * cell / 2, 0], geom);
        },
    },
    custom_jscad: {
        name: 'Custom (JSCAD code)',
        description: 'Advanced: write JSCAD code that returns a solid. Runs only in your browser.',
        parameters: [
            { name: 'code', type: 'textarea', rows: 12, group: 'Code', description: 'Return a JSCAD geom3. `jscad` and `params` are in scope.',
                default: "const { primitives, booleans, transforms } = jscad;\nconst { cuboid, sphere, cylinder } = primitives;\n\nconst body = cuboid({ size: [30, 30, 30] });\nconst hole = sphere({ radius: 19 });\n\nreturn booleans.subtract(body, hole);" },
        ],
        build(p) {
            if (!p.code || !p.code.trim()) throw new Error('Enter some JSCAD code');
            let fn;
            try { fn = new Function('jscad', 'params', p.code); }
            catch (e) { throw new Error('Code syntax error: ' + e.message); }
            const result = fn(jscad, p);
            if (!result || !result.polygons) throw new Error('Your code must return a 3D solid (geom3)');
            return result;
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
        } else if (param.type === 'textarea') {
            input = document.createElement('textarea');
            input.rows = param.rows || 8;
            input.spellcheck = false;
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
