-- PostgreSQL Schema for Alfa & Omega - Sistema de Inventario
-- This schema is managed by Alembic migrations
-- Generated automatically via: alembic upgrade head

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- RBAC Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    pass_hash TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- ============================================================================
-- Audit & Logging
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Products & Categories
-- ============================================================================

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    name TEXT NOT NULL UNIQUE,
    slug TEXT UNIQUE,
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS category_attributes (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    attr_name TEXT NOT NULL,
    attr_type TEXT DEFAULT 'text' CHECK (attr_type IN ('text', 'number', 'boolean', 'date')),
    attr_options JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    categoria TEXT,
    precio NUMERIC(12, 2) NOT NULL DEFAULT 0,
    cantidad BIGINT NOT NULL DEFAULT 0,
    avg_cost NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prod_codigo ON productos(codigo);
CREATE INDEX idx_prod_nombre ON productos(nombre);
CREATE INDEX idx_prod_categoria ON productos(categoria);
CREATE INDEX idx_prod_active ON productos(created_at);

CREATE TABLE IF NOT EXISTS product_attributes (
    id SERIAL PRIMARY KEY,
    product_code TEXT NOT NULL REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE CASCADE,
    attr_name TEXT NOT NULL,
    attr_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Partners (Customers & Suppliers)
-- ============================================================================

CREATE TABLE IF NOT EXISTS partners (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('CUSTOMER', 'SUPPLIER')),
    name TEXT NOT NULL,
    tax_id TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    notes TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_partners_kind ON partners(kind);
CREATE INDEX ix_partners_name ON partners(name);
CREATE INDEX ix_partners_tax_id ON partners(tax_id);
CREATE INDEX ix_partners_active ON partners(active);

-- ============================================================================
-- Documents (Purchases, Sales, Adjustments)
-- ============================================================================

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('PURCHASE', 'SALE', 'ADJUST', 'OPENING', 'IMPORT')),
    numero TEXT UNIQUE,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notas TEXT,
    partner_id INTEGER REFERENCES partners(id) ON DELETE SET NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_documents_numero ON documents(numero);
CREATE INDEX ix_documents_partner ON documents(partner_id);
CREATE INDEX ix_documents_fecha ON documents(fecha);
CREATE INDEX ix_documents_tipo ON documents(tipo);

CREATE TABLE IF NOT EXISTS document_series (
    id SERIAL PRIMARY KEY,
    doc_type TEXT NOT NULL CHECK (doc_type IN ('PURCHASE', 'SALE', 'ADJUST')),
    series TEXT NOT NULL,
    prefix TEXT,
    next_no BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(doc_type, series)
);

CREATE INDEX ix_doc_series_type ON document_series(doc_type);

CREATE TABLE IF NOT EXISTS document_lines (
    id SERIAL PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    codigo TEXT NOT NULL REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE RESTRICT,
    qty NUMERIC(12, 4) NOT NULL,
    unit_cost NUMERIC(12, 2),
    unit_price NUMERIC(12, 2),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_lines_doc ON document_lines(doc_id);
CREATE INDEX ix_lines_codigo ON document_lines(codigo);

-- ============================================================================
-- Stock Movements & Transactions
-- ============================================================================

CREATE TABLE IF NOT EXISTS stock_movements (
    id SERIAL PRIMARY KEY,
    doc_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    codigo TEXT NOT NULL REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE RESTRICT,
    qty NUMERIC(12, 4) NOT NULL,
    unit_cost NUMERIC(12, 2),
    unit_price NUMERIC(12, 2),
    tipo TEXT NOT NULL CHECK (tipo IN ('PURCHASE', 'SALE', 'ADJUST+', 'ADJUST-', 'TRANSFER_IN', 'TRANSFER_OUT')),
    reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_mov_codigo_fecha ON stock_movements(codigo, created_at);
CREATE INDEX ix_mov_doc ON stock_movements(doc_id);
CREATE INDEX ix_mov_tipo ON stock_movements(tipo);

-- ============================================================================
-- Kardex (Transaction History)
-- ============================================================================

CREATE TABLE IF NOT EXISTS kardex_moves (
    id SERIAL PRIMARY KEY,
    product_code TEXT NOT NULL REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('IN', 'OUT', 'TRANSFER_IN', 'TRANSFER_OUT')),
    qty NUMERIC(12, 4) NOT NULL,
    unit_cost NUMERIC(12, 2),
    total_cost NUMERIC(15, 2),
    balance_qty NUMERIC(12, 4),
    balance_cost NUMERIC(15, 2),
    balance_total NUMERIC(15, 2),
    warehouse_id INTEGER,
    ref_type TEXT CHECK (ref_type IN ('PURCHASE', 'SALE', 'ADJUST', 'TRANSFER', 'IMPORT')),
    ref_id INTEGER,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_kardex_product ON kardex_moves(product_code);
CREATE INDEX ix_kardex_date ON kardex_moves(date);
CREATE INDEX ix_kardex_warehouse ON kardex_moves(warehouse_id);

-- ============================================================================
-- Warehouses
-- ============================================================================

CREATE TABLE IF NOT EXISTS warehouses (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    location TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse_stock (
    id SERIAL PRIMARY KEY,
    product_code TEXT NOT NULL REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE RESTRICT,
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity NUMERIC(12, 4) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_code, warehouse_id)
);

CREATE INDEX ix_warehouse_stock_product ON warehouse_stock(product_code);
CREATE INDEX ix_warehouse_stock_warehouse ON warehouse_stock(warehouse_id);

CREATE TABLE IF NOT EXISTS warehouse_transfers (
    id SERIAL PRIMARY KEY,
    product_code TEXT NOT NULL REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE RESTRICT,
    from_wh INTEGER REFERENCES warehouses(id) ON DELETE SET NULL,
    to_wh INTEGER REFERENCES warehouses(id) ON DELETE SET NULL,
    quantity NUMERIC(12, 4) NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_transfers_from ON warehouse_transfers(from_wh);
CREATE INDEX ix_transfers_to ON warehouse_transfers(to_wh);
CREATE INDEX ix_transfers_product ON warehouse_transfers(product_code);

-- ============================================================================
-- Settings & Configuration
-- ============================================================================

CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Views
-- ============================================================================

CREATE OR REPLACE VIEW v_stock_actual AS
    SELECT p.codigo,
           COALESCE(SUM(sm.qty), 0) AS stock
    FROM productos p
    LEFT JOIN stock_movements sm ON sm.codigo = p.codigo
    GROUP BY p.codigo;

CREATE OR REPLACE VIEW v_low_stock AS
    SELECT p.codigo,
           p.nombre,
           p.categoria,
           p.precio,
           p.cantidad,
           5 AS threshold
    FROM productos p
    WHERE p.cantidad <= 5
    ORDER BY p.cantidad ASC;

CREATE OR REPLACE VIEW v_stock_by_warehouse AS
    SELECT ws.product_code,
           ws.warehouse_id,
           w.name AS warehouse_name,
           ws.quantity
    FROM warehouse_stock ws
    JOIN warehouses w ON w.id = ws.warehouse_id
    ORDER BY ws.product_code, w.name;

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX ix_users_username ON users(username);
CREATE INDEX ix_users_active ON users(active);
CREATE INDEX ix_roles_name ON roles(name);
CREATE INDEX ix_permissions_code ON permissions(code);

CREATE INDEX ix_audit_user ON audit_log(user_id);
CREATE INDEX ix_audit_action ON audit_log(action);
CREATE INDEX ix_audit_date ON audit_log(created_at DESC);

CREATE INDEX ix_categories_parent ON categories(parent_id);
CREATE INDEX ix_categories_active ON categories(active);

CREATE INDEX ix_documents_created_by ON documents(created_by);
CREATE INDEX ix_documents_created_at ON documents(created_at DESC);

-- ============================================================================
-- Constraints
-- ============================================================================

ALTER TABLE users ADD CONSTRAINT ck_username_not_empty CHECK (LENGTH(TRIM(username)) > 0);
ALTER TABLE roles ADD CONSTRAINT ck_role_name_not_empty CHECK (LENGTH(TRIM(name)) > 0);
ALTER TABLE productos ADD CONSTRAINT ck_codigo_not_empty CHECK (LENGTH(TRIM(codigo)) > 0);
ALTER TABLE productos ADD CONSTRAINT ck_precio_non_negative CHECK (precio >= 0);
ALTER TABLE productos ADD CONSTRAINT ck_cantidad_non_negative CHECK (cantidad >= 0);
ALTER TABLE warehouse_stock ADD CONSTRAINT ck_quantity_non_negative CHECK (quantity >= 0);

-- ============================================================================
-- Grants (for application user)
-- ============================================================================

-- Assuming 'inventario_user' role exists
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO inventario_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO inventario_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO inventario_user;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE productos IS 'Catálogo de productos del inventario';
COMMENT ON TABLE documents IS 'Documentos de movimiento: compras, ventas, ajustes';
COMMENT ON TABLE kardex_moves IS 'Histórico de movimientos para valuación (FIFO/LIFO)';
COMMENT ON TABLE audit_log IS 'Registro de auditoría de todas las operaciones del sistema';

-- ============================================================================
-- Seed Data (optional)
-- ============================================================================

-- Default settings
INSERT INTO settings (key, value, description) 
VALUES 
    ('tax_rate', '0.19', 'Tasa de impuesto (IVA)'),
    ('tax_included', 'false', 'Si los precios incluyen impuesto'),
    ('currency', 'COP', 'Moneda por defecto'),
    ('max_product_code_length', '50', 'Longitud máxima del código de producto')
ON CONFLICT (key) DO NOTHING;

-- Default warehouse
INSERT INTO warehouses (name, location, active)
VALUES ('Principal', 'Bodega principal', true)
ON CONFLICT (name) DO NOTHING;

-- Default roles
INSERT INTO roles (name, description)
VALUES 
    ('ADMIN', 'Administrador del sistema'),
    ('USER', 'Usuario estándar'),
    ('AUDITOR', 'Auditor de operaciones')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- EOF
-- ============================================================================
