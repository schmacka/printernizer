/**
 * Model-centric detail view (Slicer Phase 3b).
 * Shows a library model's derived print files and a slice panel with inline
 * progress. Rendered as a view-swap inside the #library page.
 */
class ModelDetailView {
    constructor() {
        this.el = null;
        this.checksum = null;
        this._poll = null;
        this._printerCache = null;
        this._profileCache = null;
        this._slicerId = null;
    }

    _container() {
        if (!this.el) {
            this.el = document.getElementById('modelDetailView');
            if (!this.el) {
                this.el = document.createElement('div');
                this.el.id = 'modelDetailView';
                this.el.className = 'model-detail';
                this.el.style.display = 'none';
                (document.getElementById('library') || document.body).appendChild(this.el);
            }
        }
        return this.el;
    }

    _toggleList(show) {
        const grid = document.getElementById('libraryFilesGrid');
        if (grid) grid.style.display = show ? '' : 'none';
        const stats = document.getElementById('libraryStats');
        if (stats) stats.style.display = show ? '' : 'none';
    }

    async open(checksum) {
        this.checksum = checksum;
        this._toggleList(false);
        const c = this._container();
        c.style.display = 'block';
        c.innerHTML = '<div class="loading">Loading…</div>';
        try {
            const res = await fetch(`${CONFIG.API_BASE_URL}/library/files/${checksum}`);
            if (!res.ok) throw new Error('not found');
            const model = await res.json();
            c.innerHTML = this._renderShell(model);
            c.querySelector('[data-act="back"]').addEventListener('click', () => this.close());
            const delBtn = c.querySelector('[data-act="delete"]');
            if (delBtn) delBtn.addEventListener('click', () => this._delete(model.display_name || model.filename || model.checksum));
            await this.refreshPrintfiles();
            await this.renderSlicePanel();
        } catch (e) {
            c.innerHTML = '<div class="error">Failed to load model.</div>';
        }
    }

    async _delete(label) {
        if (!confirm(`Delete "${label}"?\nThis removes the model from the library.`)) return;
        try {
            const r = await fetch(`${CONFIG.API_BASE_URL}/library/files/${this.checksum}`, { method: 'DELETE' });
            if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || 'delete failed');
            showToast('success', 'Library', 'Model deleted');
            this.close();
            if (window.libraryManager && typeof window.libraryManager.loadFiles === 'function') {
                window.libraryManager.loadFiles();
            }
        } catch (e) {
            showToast('error', 'Delete', e.message);
        }
    }

    close() {
        if (this._poll) { clearInterval(this._poll); this._poll = null; }
        const c = this._container();
        c.style.display = 'none';
        c.innerHTML = '';
        this._toggleList(true);
    }

    _renderShell(model) {
        const name = model.display_name || model.filename || model.checksum;
        const dims = (model.model_width && model.model_height)
            ? `${Math.round(model.model_width)}×${Math.round(model.model_depth || 0)}×${Math.round(model.model_height)} mm`
            : '';
        const fmtBytes = (b) => {
            if (b === null || b === undefined || b === '') return '';
            const u = ['B', 'KB', 'MB', 'GB']; let i = 0, n = Number(b);
            while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
            return `${n.toFixed(i ? 1 : 0)} ${u[i]}`;
        };
        const rows = [
            ['Type', model.file_type || ''],
            ['Dimensions', dims],
            ['Size', fmtBytes(model.file_size)],
            ['Source', model.sources || ''],
            ['Added', (model.added_to_library || '').slice(0, 10)],
            ['Checksum', model.checksum ? model.checksum.slice(0, 12) + '…' : ''],
        ].filter(([, v]) => v);
        const info = rows.map(([k, v]) => `<div class="md-info-row"><span class="md-info-k">${k}</span><span class="md-info-v">${v}</span></div>`).join('');
        const err = model.analysis_error
            ? `<div class="md-info-row md-info-error"><span class="md-info-k">Analysis</span><span class="md-info-v">${model.analysis_error}</span></div>`
            : '';
        return `
          <div class="model-detail-header">
            <button class="btn btn-secondary" data-act="back">← Library</button>
            <img class="model-detail-thumb" src="${CONFIG.API_BASE_URL}/library/files/${model.checksum}/thumbnail" onerror="this.style.display='none'"/>
            <div class="model-detail-title">
              <h2>${name}</h2>
              <div class="model-detail-meta">${dims}${dims ? ' · ' : ''}${model.file_type || ''}</div>
              <div class="model-detail-actions">
                <a class="btn btn-secondary" href="${CONFIG.API_BASE_URL}/library/files/${model.checksum}/download">Download</a>
                <button class="btn btn-danger" data-act="delete">Delete</button>
              </div>
            </div>
          </div>
          <section class="model-detail-info">${info}${err}</section>
          <section class="model-detail-slice"><h3>Slice</h3><div id="mdSlice"></div></section>
          <section class="model-detail-printfiles"><h3>Print files</h3><div id="mdPrintfiles"></div></section>`;
    }

    async _printers() {
        if (this._printerCache) return this._printerCache;
        try {
            const r = await fetch(`${CONFIG.API_BASE_URL}/printers`);
            const d = await r.json();
            this._printerCache = d.printers || (Array.isArray(d) ? d : []);
        } catch (e) {
            this._printerCache = [];
        }
        return this._printerCache;
    }

    async _profiles() {
        if (this._profileCache) return this._profileCache;
        this._profileCache = [];
        try {
            const sl = await (await fetch(`${CONFIG.API_BASE_URL}/slicing`)).json();
            const slicers = sl.slicers || [];
            const slicer = slicers.find(s => s.is_available) || slicers[0];
            if (slicer) {
                this._slicerId = slicer.id;
                const pf = await (await fetch(`${CONFIG.API_BASE_URL}/slicing/${slicer.id}/profiles`)).json();
                this._profileCache = pf.profiles || [];
            }
        } catch (e) { /* none */ }
        return this._profileCache;
    }

    async _nameMaps() {
        const [printers, profiles] = await Promise.all([this._printers(), this._profiles()]);
        const pmap = {}, fmap = {};
        printers.forEach(x => { pmap[x.id] = x.name; });
        profiles.forEach(x => { fmap[x.id] = x.profile_name; });
        return { pmap, fmap };
    }

    async refreshPrintfiles() {
        const host = document.getElementById('mdPrintfiles');
        if (!host) return;
        host.innerHTML = '<div class="loading">Loading…</div>';
        let printfiles = [];
        try {
            const r = await fetch(`${CONFIG.API_BASE_URL}/library/files/${this.checksum}/printfiles`);
            printfiles = (await r.json()).printfiles || [];
        } catch (e) { /* empty */ }
        if (!printfiles.length) {
            host.innerHTML = '<div class="empty">No print files yet. Slice this model below.</div>';
            return;
        }
        const printers = await this._printers();
        const { pmap, fmap } = await this._nameMaps();
        const rows = printfiles.map(p => {
            const t = p.estimated_print_time ? `${Math.round(p.estimated_print_time / 60)} min` : '—';
            const fil = p.filament_used ? `${Number(p.filament_used).toFixed(1)} g` : '—';
            const printerName = pmap[p.target_printer_id] || (p.target_printer_id ? 'Unknown printer' : '—');
            const profileName = fmap[p.profile_id] || p.profile_name || '—';
            const pr = printers.length
                ? `<select class="md-printer">${printers.map(x => `<option value="${x.id}">${x.name}</option>`).join('')}</select>`
                : '';
            return `<tr data-cs="${p.checksum}">
              <td>${printerName}</td><td>${profileName}</td>
              <td>${t}</td><td>${fil}</td>
              <td><button class="btn btn-sm" data-dl="${p.checksum}">Download</button>
                  ${pr} <button class="btn btn-sm" data-print="${p.checksum}">Print</button></td></tr>`;
        }).join('');
        host.innerHTML = `<table class="md-table"><thead><tr><th>Printer</th><th>Profile</th><th>Time</th><th>Filament</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table>`;
        host.querySelectorAll('[data-dl]').forEach(b => b.addEventListener('click', () => {
            window.open(`${CONFIG.API_BASE_URL}/library/files/${b.dataset.dl}/download`, '_blank');
        }));
        host.querySelectorAll('[data-print]').forEach(b => b.addEventListener('click', async () => {
            const tr = b.closest('tr');
            const sel = tr.querySelector('.md-printer');
            const printerId = sel ? sel.value : null;
            if (!printerId) { showToast('error', 'Print', 'No printer available'); return; }
            try {
                const r = await fetch(`${CONFIG.API_BASE_URL}/library/files/${b.dataset.print}/print`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ printer_id: printerId })
                });
                if (!r.ok) throw new Error((await r.json()).detail || 'failed');
                showToast('success', 'Print', 'Sent to printer');
            } catch (e) { showToast('error', 'Print', e.message); }
        }));
    }

    async renderSlicePanel() {
        const host = document.getElementById('mdSlice');
        if (!host) return;
        const profiles = await this._profiles();
        if (!this._slicerId || !profiles.length) {
            host.innerHTML = '<div class="empty">No slicer or profile available yet. Start the slicer add-on and configure its URL.</div>';
            return;
        }
        const printers = await this._printers();

        // Group profiles by printer model so the picker reads as names, not IDs.
        const groups = {};
        profiles.forEach(p => { (groups[p.printer_model || 'Other'] = groups[p.printer_model || 'Other'] || []).push(p); });
        const profileOptions = Object.keys(groups).sort().map(model =>
            `<optgroup label="${model}">` +
            groups[model].map(p => `<option value="${p.id}">${p.profile_name}</option>`).join('') +
            `</optgroup>`).join('');

        host.innerHTML = `
          <div class="md-slice-form">
            <label class="md-field">Profile
              <select id="mdProfile">${profileOptions}</select>
            </label>
            <label class="md-field">Target printer
              <select id="mdSlicePrinter"><option value="">— choose when printing —</option>${printers.map(x => `<option value="${x.id}">${x.name}</option>`).join('')}</select>
            </label>
            <div class="md-slice-actions">
              <button class="btn btn-primary" id="mdSliceBtn">Slice</button>
              <button class="btn btn-secondary" id="mdSlicePrintBtn">Slice &amp; Print</button>
            </div>
          </div>
          <div id="mdProfileMeta" class="md-profile-meta"></div>
          <div id="mdSliceStatus"></div>`;

        const sel = host.querySelector('#mdProfile');
        const meta = host.querySelector('#mdProfileMeta');
        const updateMeta = () => {
            const p = profiles.find(x => x.id === sel.value);
            if (!p) { meta.textContent = ''; return; }
            const src = p.is_builtin ? 'built-in' : (p.source || 'custom');
            meta.innerHTML = `<span class="md-chip">${p.printer_model || 'Generic'}</span><span class="md-chip md-chip-soft">${src}</span>`;
        };
        sel.addEventListener('change', updateMeta);
        updateMeta();
        host.querySelector('#mdSliceBtn').addEventListener('click', () => this._slice(false));
        host.querySelector('#mdSlicePrintBtn').addEventListener('click', () => this._slice(true));
    }

    async _slice(andPrint) {
        const profileId = document.getElementById('mdProfile').value;
        const printerId = document.getElementById('mdSlicePrinter').value;
        if (andPrint && !printerId) { showToast('error', 'Slice', 'Pick a printer for Slice & Print'); return; }
        const status = document.getElementById('mdSliceStatus');
        status.innerHTML = '<div class="md-progress"><div></div></div><div class="md-status">Queued…</div>';
        try {
            let job;
            if (andPrint) {
                const r = await fetch(`${CONFIG.API_BASE_URL}/slicing/slice-and-print`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file_checksum: this.checksum, slicer_id: this._slicerId,
                        profile_id: profileId, printer_id: printerId, auto_start: true
                    })
                });
                job = await r.json();
            } else {
                const body = { file_checksum: this.checksum, slicer_id: this._slicerId, profile_id: profileId };
                if (printerId) body.target_printer_id = printerId;
                const r = await fetch(`${CONFIG.API_BASE_URL}/slicing/library/${this.checksum}/slice`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
                });
                job = await r.json();
            }
            if (!job.id) throw new Error(job.detail || 'slice failed to start');
            this._pollJob(job.id);
        } catch (e) {
            status.innerHTML = `<div class="error">${e.message}</div>`;
        }
    }

    _pollJob(jobId) {
        if (this._poll) clearInterval(this._poll);
        const status = document.getElementById('mdSliceStatus');
        this._poll = setInterval(async () => {
            try {
                const j = await (await fetch(`${CONFIG.API_BASE_URL}/slicing/jobs/${jobId}`)).json();
                const bar = status.querySelector('.md-progress > div');
                if (bar) bar.style.width = `${j.progress || 0}%`;
                const lbl = status.querySelector('.md-status');
                if (lbl) lbl.textContent = `${j.status} (${j.progress || 0}%)`;
                if (j.status === 'completed') {
                    clearInterval(this._poll); this._poll = null;
                    showToast('success', 'Slice', 'Slicing complete');
                    status.innerHTML = '';
                    await this.refreshPrintfiles();
                } else if (j.status === 'failed') {
                    clearInterval(this._poll); this._poll = null;
                    status.innerHTML = `<div class="error">${j.error_message || 'Slicing failed'}</div>`;
                }
            } catch (e) { /* keep polling */ }
        }, 1500);
    }
}
window.modelDetailView = new ModelDetailView();
