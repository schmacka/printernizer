-- Migration: 030_repair_orders_tables
-- Description: Safety-net migration ensuring all orders tables exist with correct schema.
-- Idempotent: all statements use IF NOT EXISTS / OR IGNORE, safe to run in any state.
-- This repairs databases where migration 028/029 failed silently due to partial
-- transaction failures or interrupted startups.

CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);

CREATE TABLE IF NOT EXISTS order_sources (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

INSERT OR IGNORE INTO order_sources (id, name) VALUES ('source_email_dm', 'Email / DM');
INSERT OR IGNORE INTO order_sources (id, name) VALUES ('source_walk_in', 'Walk-in');
INSERT OR IGNORE INTO order_sources (id, name) VALUES ('source_online_shop', 'Online Shop');

CREATE TABLE IF NOT EXISTS orders (
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

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_source_id ON orders(source_id);
CREATE INDEX IF NOT EXISTS idx_orders_due_date ON orders(due_date);

CREATE TABLE IF NOT EXISTS order_files (
    id TEXT PRIMARY KEY NOT NULL,
    order_id TEXT NOT NULL,
    file_id TEXT,
    url TEXT,
    filename TEXT NOT NULL,
    file_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    CHECK (file_id IS NOT NULL OR url IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_order_files_order_id ON order_files(order_id);

ALTER TABLE jobs ADD COLUMN order_id TEXT REFERENCES orders(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_jobs_order_id ON jobs(order_id);
