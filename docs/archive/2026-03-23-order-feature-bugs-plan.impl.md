# Implementation Plan: Fix New Order Feature Bugs

Based on `plan.md` — three files, three steps.

---

## Step 1 — Fix `src/database/repositories/order_repository.py`

### 1a. `create_order()` (lines 17-46)

Replace the SQL and params to match the actual `orders` table schema:

```python
sql = """
    INSERT INTO orders
    (id, title, customer_id, source_id, status, quoted_price,
     payment_status, notes, due_date, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
params = (
    data['id'],
    data['title'],
    data.get('customer_id'),
    data.get('source_id'),
    data.get('status', 'new'),         # was 'pending', schema CHECK is 'new'
    data.get('quoted_price'),
    data.get('payment_status', 'unpaid'),  # NEW — was missing
    data.get('notes'),
    data.get('due_date'),
    data.get('created_at', now),
    data.get('updated_at', now),
)
```

**Changes**: Remove `description`, `currency`. Add `payment_status`. Fix default status from `'pending'` to `'new'` (matches DB CHECK constraint).

### 1b. `update_order()` (lines 118-149)

Replace `allowed_fields` tuple (line 123-126):

```python
allowed_fields = (
    'title', 'status', 'customer_id', 'source_id',
    'quoted_price', 'payment_status', 'due_date', 'notes',
)
```

**Changes**: Remove `'description'`, `'currency'`. Add `'payment_status'`.

### 1c. `add_file()` (lines 206-231)

Replace SQL and params to match actual `order_files` schema:

```python
sql = """
    INSERT INTO order_files
    (id, order_id, file_id, url, filename, file_type, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""
params = (
    data['id'],
    data['order_id'],
    data.get('file_id'),       # replaces file_path
    data.get('url'),           # replaces file_size
    data['filename'],
    data.get('file_type'),     # replaces mime_type
    data.get('created_at', now),
)
```

**Changes**: Remove `file_path`, `file_size`, `mime_type`. Add `file_id`, `url`, `file_type`. Note: CHECK constraint requires at least one of `file_id` or `url` to be non-NULL — callers must ensure this.

---

## Step 2 — Add `createOrderModal` to `frontend/index.html`

Insert a new modal before `</body>`, following the existing `addPrinterModal` pattern (class="modal", modal-content, modal-header, modal-body, modal-footer).

**Modal ID**: `createOrderModal`

**Fields**:
| Field | Element | Notes |
|-------|---------|-------|
| Title | `<input type="text" id="orderTitle" required>` | |
| Customer | `<select id="orderCustomerSelect">` | Populated dynamically |
| Source | `<select id="orderSourceSelect">` | Populated dynamically |
| Quoted Price | `<input type="number" id="orderQuotedPrice" step="0.01" min="0">` | |
| Payment Status | `<select id="orderPaymentStatus">` with options: unpaid/partial/paid | Static options |
| Due Date | `<input type="date" id="orderDueDate">` | |
| Notes | `<textarea id="orderNotes">` | |
| Library Files | `<input type="text" id="orderFileSearch">` + `<div id="orderFilePickerList">` | Search + checkbox list |

**Footer**: Cancel → `closeModal('createOrderModal')`, Save → `ordersManager.submitCreateOrder()`

**Key detail**: Use `showModal()` (not `openModal()` — that's what the codebase actually uses per `frontend/js/utils.js`).

---

## Step 3 — Update `frontend/js/orders.js`

### 3a. Replace `showCreateModal()` (lines 166-169)

```javascript
showCreateModal() {
    // Populate customer select
    const custSelect = document.getElementById('orderCustomerSelect');
    custSelect.innerHTML = '<option value="">— None —</option>';
    this.customers.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name;
        custSelect.appendChild(opt);
    });

    // Populate source select
    const srcSelect = document.getElementById('orderSourceSelect');
    srcSelect.innerHTML = '<option value="">— None —</option>';
    this.sources.filter(s => s.is_active).forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = s.name;
        srcSelect.appendChild(opt);
    });

    // Reset form fields
    document.getElementById('orderTitle').value = '';
    document.getElementById('orderQuotedPrice').value = '';
    document.getElementById('orderPaymentStatus').value = 'unpaid';
    document.getElementById('orderDueDate').value = '';
    document.getElementById('orderNotes').value = '';
    document.getElementById('orderFileSearch').value = '';

    // Load library files
    this.loadLibraryFilesForPicker();

    showModal('createOrderModal');
}
```

### 3b. Add `submitCreateOrder()` (new method)

```javascript
async submitCreateOrder() {
    const title = document.getElementById('orderTitle').value.trim();
    if (!title) { showToast('error', 'Error', 'Title is required'); return; }

    const payload = {
        title,
        customer_id: document.getElementById('orderCustomerSelect').value || null,
        source_id: document.getElementById('orderSourceSelect').value || null,
        quoted_price: parseFloat(document.getElementById('orderQuotedPrice').value) || null,
        payment_status: document.getElementById('orderPaymentStatus').value,
        due_date: document.getElementById('orderDueDate').value || null,
        notes: document.getElementById('orderNotes').value.trim() || null,
    };

    try {
        const response = await fetch('/api/v1/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const order = await response.json();

        // Attach checked library files
        const checked = document.querySelectorAll('#orderFilePickerList input[type="checkbox"]:checked');
        for (const cb of checked) {
            await fetch(`/api/v1/orders/${order.id}/files`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_id: cb.value, filename: cb.dataset.filename })
            });
        }

        closeModal('createOrderModal');
        showToast('success', 'Order Created', `Order "${title}" created`);
        await this.load();
    } catch (error) {
        Logger.error('Failed to create order:', error);
        showToast('error', 'Error', 'Failed to create order');
    }
}
```

### 3c. Add `loadLibraryFilesForPicker()` (new method)

```javascript
async loadLibraryFilesForPicker(search = '') {
    const container = document.getElementById('orderFilePickerList');
    if (!container) return;
    container.innerHTML = '<span class="text-muted">Loading...</span>';

    try {
        const params = new URLSearchParams({ limit: '100' });
        if (search) params.set('search', search);
        const response = await fetch(`/api/v1/files?${params}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        const files = data.files || [];

        if (!files.length) {
            container.innerHTML = '<span class="text-muted">No files found.</span>';
            return;
        }

        container.innerHTML = files.map(f => `
            <label style="display:flex;align-items:center;gap:0.5rem;padding:0.25rem 0;">
                <input type="checkbox" value="${f.id}" data-filename="${this._escapeHtml(f.filename || f.name)}">
                ${this._escapeHtml(f.filename || f.name)}
            </label>
        `).join('');
    } catch (error) {
        Logger.error('Failed to load library files:', error);
        container.innerHTML = '<span class="text-muted">Failed to load files.</span>';
    }
}
```

Wire up the search input with a debounced `oninput` handler in the modal HTML or in `showCreateModal()`.

---

## Files Changed

| File | What |
|------|------|
| `src/database/repositories/order_repository.py` | Fix SQL in `create_order()`, `update_order()`, `add_file()` |
| `frontend/index.html` | Add `createOrderModal` HTML |
| `frontend/js/orders.js` | Replace `showCreateModal()`, add `submitCreateOrder()`, add `loadLibraryFilesForPicker()` |

## Risks / Notes

- The `status` default in `create_order()` was `'pending'` but the DB CHECK constraint only allows `'new', 'planned', 'printed', 'delivered'` — changing to `'new'`.
- `add_file()` callers must provide at least `file_id` or `url` to satisfy the DB CHECK constraint.
- The file search input needs debouncing (300ms) to avoid excessive API calls.
- No API router changes needed — the existing endpoints already accept the correct payload shapes.
