-- Migration: 029_add_cancelled_order_status
-- Description: Add 'cancelled' as a valid order status value
-- SQLite requires table recreation to modify CHECK constraints

PRAGMA foreign_keys = OFF;

CREATE TABLE orders_new (
    id TEXT PRIMARY KEY NOT NULL,
    title TEXT NOT NULL,
    customer_id TEXT REFERENCES customers(id) ON DELETE SET NULL,
    source_id TEXT REFERENCES order_sources(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'planned', 'printed', 'delivered', 'cancelled')),
    quoted_price REAL,
    payment_status TEXT NOT NULL DEFAULT 'unpaid'
        CHECK (payment_status IN ('unpaid', 'partial', 'paid')),
    notes TEXT,
    due_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Use explicit column list (not SELECT *) so this migration is robust against future schema additions
INSERT INTO orders_new (id, title, customer_id, source_id, status, quoted_price, payment_status, notes, due_date, created_at, updated_at)
    SELECT id, title, customer_id, source_id, status, quoted_price, payment_status, notes, due_date, created_at, updated_at
    FROM orders;

DROP TABLE orders;
ALTER TABLE orders_new RENAME TO orders;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_source_id ON orders(source_id);
CREATE INDEX IF NOT EXISTS idx_orders_due_date ON orders(due_date);

PRAGMA foreign_key_check;
PRAGMA foreign_keys = ON;
