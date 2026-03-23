# Fix Plan: New Order Feature Bugs

## Root Cause Summary

Three categories of bugs:

### 1. Backend: `order_repository.py` — schema mismatch

The repository was written against a different schema than what the migration actually created.

| Method | Problem |
|--------|---------|
| `create_order()` | INSERT uses non-existent columns `description`, `currency`; omits actual column `payment_status` |
| `update_order()` | `allowed_fields` includes `description`, `currency` (don't exist); excludes `payment_status` (can't be updated) |
| `add_file()` | INSERT uses non-existent columns `file_path`, `file_size`, `mime_type`; omits actual columns `file_id`, `url`, `file_type`; also violates DB CHECK constraint `(file_id IS NOT NULL OR url IS NOT NULL)` |

Actual `orders` table columns: `id, title, customer_id, source_id, status, quoted_price, payment_status, notes, due_date, created_at, updated_at`

Actual `order_files` table columns: `id, order_id, file_id, url, filename, file_type, created_at`

### 2. Frontend: No proper "New Order" modal

`showCreateModal()` uses a bare `prompt()` — no customer field, no source, no price, no dates, no file picker.

### 3. Frontend: No library file selector

No UI to browse/select library files for an order anywhere.

---

## Fix Plan

### Step 1 — Fix `order_repository.py` (3 changes)

**`create_order()` SQL** — replace the INSERT:
- Remove: `description`, `currency`
- Add: `payment_status`
- Fix params tuple to match (11 columns → 11 values)

**`update_order()` allowed_fields** — replace the tuple:
- Remove: `'description'`, `'currency'`
- Add: `'payment_status'`

**`add_file()` SQL** — replace the INSERT:
- Remove: `file_path`, `file_size`, `mime_type`
- Add: `file_id`, `url`, `file_type`
- Fix params tuple accordingly

### Step 2 — Add `createOrderModal` to `frontend/index.html`

Insert a proper modal (following existing `addPrinterModal` pattern) before the closing `</body>` tag.

Fields:
- **Title** — required text input
- **Customer** — `<select id="orderCustomerSelect">` populated dynamically
- **Order Source** — `<select id="orderSourceSelect">` populated dynamically
- **Quoted Price** — number input (step 0.01, min 0)
- **Payment Status** — select: unpaid / partial / paid
- **Due Date** — date input
- **Notes** — textarea
- **Attach library files** — search input + scrollable file list with checkboxes (populated from `GET /api/v1/files`)

Footer: Cancel + Save buttons.

### Step 3 — Update `frontend/js/orders.js`

**Replace `showCreateModal()`**:
- Call `openModal('createOrderModal')` instead of `prompt()`
- Populate `#orderCustomerSelect` from `this.customers`
- Populate `#orderSourceSelect` from `this.sources`
- Load library files into the picker via `GET /api/v1/files?limit=200`

**Add `submitCreateOrder()`** (called by modal Save button):
1. Read all form fields
2. POST to `/api/v1/orders` with full payload
3. For each checked library file, POST to `/api/v1/orders/{id}/files` with `file_id` and `filename`
4. Close modal, reload orders list, show success toast

**Add `loadLibraryFilesForPicker(search = '')`**:
- Fetches `GET /api/v1/files?search=...&limit=100`
- Renders checkboxes into `#orderFilePickerList`

---

## Files Changed

| File | Change |
|------|--------|
| `src/database/repositories/order_repository.py` | Fix `create_order()`, `update_order()`, `add_file()` |
| `frontend/index.html` | Add `createOrderModal` |
| `frontend/js/orders.js` | Replace `showCreateModal()`, add `submitCreateOrder()`, add `loadLibraryFilesForPicker()` |
