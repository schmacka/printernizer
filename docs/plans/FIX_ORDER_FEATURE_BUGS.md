# Fix: New Order Feature Bugs

## Context

The orders feature (merged PR #326, commit `0d80ca5`) has multiple bugs that prevent it from working:
1. **Can't save a new order** — `OrderRepository` INSERT statements use columns that don't exist in the actual DB schema (migration `028_add_orders_tables.sql`)
2. **Can't attach library files** — same schema mismatch in `add_file()`, plus no frontend UI
3. **No customer/source fields in create modal** — `showCreateModal()` is just a `prompt()` for title only

The repository layer was written against a different schema than what the migration created. The frontend was left as placeholder `prompt()` dialogs.

---

## Critical Files

| File | Role |
|------|------|
| `src/database/repositories/order_repository.py` | 5 broken methods |
| `frontend/index.html` | Add `createOrderModal` |
| `frontend/js/orders.js` | Replace `showCreateModal`, add submit + file picker |
| `migrations/028_add_orders_tables.sql` | Source of truth for schema (read-only reference) |

---

## Step 1 — Fix `order_repository.py` (5 methods)

### 1a. `create_order()` — lines 17–46

**Current SQL (WRONG):**
```sql
INSERT INTO orders
(id, title, description, status, customer_id, source_id,
 quoted_price, currency, due_date, notes, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

**Fixed SQL:**
```sql
INSERT INTO orders
(id, title, customer_id, source_id, status,
 quoted_price, payment_status, due_date, notes, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

**Fixed params tuple (11 values):**
```python
params = (
    data['id'],
    data['title'],
    data.get('customer_id'),
    data.get('source_id'),
    data.get('status', 'new'),          # fix default: 'pending' → 'new'
    data.get('quoted_price'),
    data.get('payment_status', 'unpaid'),  # was missing entirely
    data.get('due_date'),
    data.get('notes'),
    data.get('created_at', now),
    data.get('updated_at', now),
)
```

### 1b. `update_order()` — lines 118–149

**Current `allowed_fields` (WRONG):**
```python
allowed_fields = (
    'title', 'description', 'status', 'customer_id', 'source_id',
    'quoted_price', 'currency', 'due_date', 'notes',
)
```

**Fixed:**
```python
allowed_fields = (
    'title', 'status', 'customer_id', 'source_id',
    'quoted_price', 'payment_status', 'due_date', 'notes',
)
```

### 1c. `add_file()` — lines 206–231

**Current SQL (WRONG):**
```sql
INSERT INTO order_files
(id, order_id, filename, file_path, file_size, mime_type, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
```

**Fixed SQL:**
```sql
INSERT INTO order_files
(id, order_id, file_id, url, filename, file_type, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
```

**Fixed params tuple:**
```python
params = (
    data['id'],
    data['order_id'],
    data.get('file_id'),
    data.get('url'),
    data['filename'],
    data.get('file_type'),
    data.get('created_at', now),
)
```

### 1d. `create_source()` — lines 254–277

**Current SQL (WRONG):**
```sql
INSERT INTO order_sources
(id, name, description, is_active, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?)
```

**Fixed SQL:**
```sql
INSERT INTO order_sources
(id, name, is_active, created_at, updated_at)
VALUES (?, ?, ?, ?, ?)
```

**Fixed params tuple (5 values, remove `description`):**
```python
params = (
    data['id'],
    data['name'],
    1 if data.get('is_active', True) else 0,
    data.get('created_at', now),
    data.get('updated_at', now),
)
```

### 1e. `update_source()` — line 305

**Current `allowed_fields` (WRONG):**
```python
allowed_fields = ('name', 'description', 'is_active')
```

**Fixed:**
```python
allowed_fields = ('name', 'is_active')
```

---

## Step 2 — Add `createOrderModal` to `frontend/index.html`

Insert a modal before the closing `</body>` tag, following the existing pattern of `addPrinterModal` (line ~2216).

**Modal ID:** `createOrderModal`

**Fields:**
| Field | Element | Name |
|-------|---------|------|
| Title | `<input type="text" required>` | `orderTitle` |
| Customer | `<select>` (option: "— no customer —") | `orderCustomerSelect` |
| Order Source | `<select>` (option: "— no source —") | `orderSourceSelect` |
| Quoted Price | `<input type="number" min="0" step="0.01">` | `orderQuotedPrice` |
| Payment Status | `<select>` unpaid/partial/paid | `orderPaymentStatus` |
| Due Date | `<input type="date">` | `orderDueDate` |
| Notes | `<textarea rows="3">` | `orderNotes` |
| Library file picker | search `<input>` + `<div id="orderFilePickerList">` scrollable checkboxes | `orderFileSearch` |

**Footer buttons:**
- Cancel: `onclick="closeModal('createOrderModal')"`
- Save: `onclick="ordersManager.submitCreateOrder()"`

**Structure** (follows addPrinterModal pattern):
```html
<div id="createOrderModal" class="modal">
  <div class="modal-content">
    <div class="modal-header">
      <h3>New Order</h3>
      <button class="modal-close" onclick="closeModal('createOrderModal')">&times;</button>
    </div>
    <form id="createOrderForm" class="modal-body">
      <!-- fields listed above -->
      <div class="form-group">
        <label>Attach Library Files</label>
        <input type="text" id="orderFileSearch" class="form-control"
               placeholder="Search files..." oninput="ordersManager.loadLibraryFilesForPicker(this.value)">
        <div id="orderFilePickerList" style="max-height:180px;overflow-y:auto;margin-top:0.5rem;"></div>
      </div>
    </form>
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" onclick="closeModal('createOrderModal')">Cancel</button>
      <button type="button" class="btn btn-primary" onclick="ordersManager.submitCreateOrder()">
        <span class="btn-icon">➕</span> Save Order
      </button>
    </div>
  </div>
</div>
```

---

## Step 3 — Update `frontend/js/orders.js` (3 changes)

### 3a. Replace `showCreateModal()` (lines 166–169)

```javascript
showCreateModal() {
    // Populate dropdowns from already-loaded data
    const custSel = document.getElementById('orderCustomerSelect');
    custSel.innerHTML = '<option value="">— no customer —</option>' +
        this.customers.map(c => `<option value="${c.id}">${this._escapeHtml(c.name)}</option>`).join('');

    const srcSel = document.getElementById('orderSourceSelect');
    srcSel.innerHTML = '<option value="">— no source —</option>' +
        this.sources.map(s => `<option value="${s.id}">${this._escapeHtml(s.name)}</option>`).join('');

    // Reset form fields
    document.getElementById('createOrderForm').reset();
    document.getElementById('orderFilePickerList').innerHTML = '';

    // Load library files into picker
    this.loadLibraryFilesForPicker('');

    openModal('createOrderModal');
}
```

### 3b. Add `submitCreateOrder()` (new method)

```javascript
async submitCreateOrder() {
    const title = document.getElementById('orderTitle').value.trim();
    if (!title) { showToast('error', 'Validation', 'Title is required'); return; }

    const data = {
        title,
        customer_id: document.getElementById('orderCustomerSelect').value || null,
        source_id: document.getElementById('orderSourceSelect').value || null,
        quoted_price: parseFloat(document.getElementById('orderQuotedPrice').value) || null,
        payment_status: document.getElementById('orderPaymentStatus').value || 'unpaid',
        due_date: document.getElementById('orderDueDate').value || null,
        notes: document.getElementById('orderNotes').value.trim() || null,
    };

    try {
        const response = await fetch('/api/v1/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const order = await response.json();

        // Attach any checked library files
        const checked = document.querySelectorAll('#orderFilePickerList input[type=checkbox]:checked');
        for (const cb of checked) {
            await fetch(`/api/v1/orders/${order.id}/files`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_id: cb.value, filename: cb.dataset.filename })
            });
        }

        closeModal('createOrderModal');
        showToast('success', 'Order Created', `Order "${data.title}" created`);
        await this.load();
    } catch (error) {
        Logger.error('Failed to create order:', error);
        showToast('error', 'Error', 'Failed to create order');
    }
}
```

### 3c. Add `loadLibraryFilesForPicker(search)` (new method)

```javascript
async loadLibraryFilesForPicker(search = '') {
    const container = document.getElementById('orderFilePickerList');
    if (!container) return;
    try {
        const params = new URLSearchParams({ limit: '100' });
        if (search) params.set('search', search);
        const response = await fetch(`/api/v1/files?${params}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        const files = data.files || [];
        if (!files.length) {
            container.innerHTML = '<p class="text-muted" style="padding:0.5rem;">No files found.</p>';
            return;
        }
        container.innerHTML = files.map(f => `
            <label style="display:flex;align-items:center;gap:0.5rem;padding:0.25rem 0;cursor:pointer;">
                <input type="checkbox" value="${f.id}" data-filename="${this._escapeHtml(f.filename)}">
                <span>${this._escapeHtml(f.filename)}</span>
                <small class="text-muted">${f.file_type || ''}</small>
            </label>
        `).join('');
    } catch (error) {
        Logger.error('Failed to load library files for picker:', error);
    }
}
```

---

## Verification

1. **Backend — create order**: POST `/api/v1/orders` with `{"title":"Test","payment_status":"unpaid"}` → expect 201, no SQL error
2. **Backend — update payment**: PUT `/api/v1/orders/{id}` with `{"payment_status":"paid"}` → verify field persists
3. **Backend — attach file**: POST `/api/v1/orders/{id}/files` with `{"file_id":"...","filename":"test.stl"}` → expect 201, no constraint violation
4. **Backend — create source**: POST `/api/v1/order-sources` with `{"name":"WhatsApp"}` → expect 201, no SQL error
5. **Frontend — create modal**: Click "New Order" → proper modal appears with all fields and file picker
6. **Frontend — file picker**: Typing in search box filters library files
7. **Frontend — save with files**: Fill form, check 1+ files, click Save → order created and files attached
