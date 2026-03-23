# Orders Tracking Feature

**Version**: 2.30.0
**Status**: In Progress (bugs pending fix — see Known Issues)

## Overview

The Orders feature provides customer order management for commercial 3D printing operations. It tracks orders from intake through delivery, links print jobs and library files to orders, and provides basic business analytics.

## Data Model

### Tables (migration `028_add_orders_tables.sql`)

#### `orders`
| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID |
| `title` | TEXT NOT NULL | Order name |
| `customer_id` | TEXT FK | References `customers(id)` ON DELETE SET NULL |
| `source_id` | TEXT FK | References `order_sources(id)` ON DELETE RESTRICT |
| `status` | TEXT NOT NULL | `new` → `planned` → `printed` → `delivered` (forward-only) |
| `quoted_price` | REAL | Nullable |
| `payment_status` | TEXT NOT NULL | `unpaid` / `partial` / `paid` |
| `notes` | TEXT | Nullable |
| `due_date` | TEXT | ISO8601 date string, nullable |
| `created_at` | TIMESTAMP | Auto |
| `updated_at` | TIMESTAMP | Auto |

#### `customers`
| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID |
| `name` | TEXT NOT NULL | |
| `email` | TEXT | Nullable |
| `phone` | TEXT | Nullable |
| `address` | TEXT | Nullable |
| `notes` | TEXT | Nullable |
| `created_at` | TIMESTAMP | Auto |
| `updated_at` | TIMESTAMP | Auto |

#### `order_sources`
| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID |
| `name` | TEXT NOT NULL UNIQUE | e.g. "Email / DM", "Walk-in" |
| `is_active` | INTEGER | 1 = active, 0 = inactive |
| `created_at` | TIMESTAMP | Auto |
| `updated_at` | TIMESTAMP | Auto |

Default sources seeded: `Email / DM`, `Walk-in`, `Online Shop`.

#### `order_files`
| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID |
| `order_id` | TEXT NOT NULL FK | References `orders(id)` ON DELETE CASCADE |
| `file_id` | TEXT | Nullable — references library file |
| `url` | TEXT | Nullable — external URL |
| `filename` | TEXT NOT NULL | Display name |
| `file_type` | TEXT | Nullable — stl, 3mf, gcode, etc. |
| `created_at` | TIMESTAMP | Auto |

Constraint: `CHECK (file_id IS NOT NULL OR url IS NOT NULL)` — at least one must be set.

#### `jobs.order_id` (added column)
Foreign key added to existing `jobs` table: `order_id TEXT REFERENCES orders(id) ON DELETE SET NULL`.

---

## Status Transitions

Status is **forward-only**. Enforced in `OrderService._validate_status_transition()`.

```
new → planned → printed → delivered
```

Attempting to reverse or skip a status returns HTTP 422.

---

## API Endpoints

All routes use empty string `""` for root (no trailing slash), per project routing standards.

### Orders — `/api/v1/orders`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/orders` | List orders. Query params: `status`, `customer_id`, `source_id`, `due_before`, `due_after`, `limit`, `offset` |
| POST | `/api/v1/orders` | Create order |
| GET | `/api/v1/orders/{id}` | Get full order with nested customer, source, jobs, files, costs |
| PUT | `/api/v1/orders/{id}` | Update order (status transitions validated) |
| DELETE | `/api/v1/orders/{id}` | Delete order (files cascade, jobs unlinked) |
| POST | `/api/v1/orders/{id}/jobs` | Link existing job (`job_id`) or create draft (`auto_create=true`) |
| DELETE | `/api/v1/orders/{id}/jobs/{job_id}` | Unlink job from order |
| POST | `/api/v1/orders/{id}/files` | Attach library file (`file_id`) or external URL (`url`) |
| DELETE | `/api/v1/orders/{id}/files/{file_id}` | Detach file from order |

### Customers — `/api/v1/customers`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/customers` | List customers. Query param: `search` (name/email/phone) |
| POST | `/api/v1/customers` | Create customer |
| GET | `/api/v1/customers/{id}` | Get customer with order history |
| PUT | `/api/v1/customers/{id}` | Update customer |
| DELETE | `/api/v1/customers/{id}` | Delete (orders.customer_id set to NULL) |

### Order Sources — `/api/v1/order-sources`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/order-sources` | List sources. Query param: `all=true` to include inactive |
| POST | `/api/v1/order-sources` | Create source |
| PUT | `/api/v1/order-sources/{id}` | Update source (name, is_active) |
| DELETE | `/api/v1/order-sources/{id}` | Delete source (409 if referenced by orders) |

### Analytics — `/api/v1/analytics/orders`

Returns: `total_orders`, `orders_by_status`, `total_quoted_eur`, `total_paid_eur`, `outstanding_eur`, `orders_by_source`, `avg_fulfillment_days`.

---

## Architecture

```
API Router (orders.py / customers.py / order_sources.py)
    ↓
OrderService (src/services/order_service.py)
    ↓
OrderRepository / CustomerRepository
(src/database/repositories/order_repository.py)
(src/database/repositories/customer_repository.py)
    ↓
SQLite (orders, customers, order_sources, order_files tables)
```

`OrderService` is instantiated per-request via `get_order_service()` dependency in `src/utils/dependencies.py`, receiving the shared `Database` instance via `database._connection`.

---

## Frontend

**Page**: Orders (`#orders` in `frontend/index.html`, managed by `frontend/js/orders.js`)

**Class**: `OrdersManager` — singleton `ordersManager`

**Sections**:
- Orders table with status/customer/source/price/payment/due-date columns
- Customers sub-section with search
- Order Sources managed via Settings → Orders tab

---

## Known Issues (pending fix on branch `claude/fix-order-feature-bugs-VKV3I`)

### Backend — `order_repository.py` schema mismatch

The repository was written against a different schema than the migration. Five methods are broken:

| Method | Bug | Effect |
|--------|-----|--------|
| `create_order()` | INSERT uses non-existent columns `description`, `currency`; omits `payment_status`; wrong default status `'pending'` | Every order creation fails with SQL error |
| `update_order()` | `allowed_fields` includes `description`, `currency`; missing `payment_status` | `payment_status` can never be updated |
| `add_file()` | INSERT uses `file_path`, `file_size`, `mime_type` (don't exist); missing `file_id`, `url`, `file_type`; violates CHECK constraint | Every file attachment fails |
| `create_source()` | INSERT includes non-existent column `description` | Source creation fails |
| `update_source()` | `allowed_fields` includes non-existent `description` | Source updates silently drop valid fields |

### Frontend — incomplete create modals

| Issue | Detail |
|-------|--------|
| `showCreateModal()` uses `prompt()` | Only captures title; no customer, source, price, dates, notes, or file picker |
| No proper modal form | No `createOrderModal` HTML exists yet |
| No library file selector | `attach_file` / `detach_file` methods exist but no UI triggers them |

### Fix plan

See [`docs/plans/FIX_ORDER_FEATURE_BUGS.md`](../plans/FIX_ORDER_FEATURE_BUGS.md) for the full implementation plan covering:
1. Fix 5 methods in `order_repository.py`
2. Add `createOrderModal` to `frontend/index.html`
3. Replace `showCreateModal()`, add `submitCreateOrder()` and `loadLibraryFilesForPicker()` in `frontend/js/orders.js`
