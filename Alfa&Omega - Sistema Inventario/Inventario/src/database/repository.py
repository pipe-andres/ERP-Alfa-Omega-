"""Repository centralizado que encapsula queries frecuentes.
Utiliza `src.database.connection.get_connection` y expone funciones
útiles para evitar SELECT repetidos y para integrarse con caching.
"""
from __future__ import annotations
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import asdict

from src.database.connection import get_connection, DB_ENGINE
from src.core import caching

# helper to detect when we are running with JSON-backed storage
from src.database import json_store

def _use_json() -> bool:
    return DB_ENGINE == 'json'


def ensure_schema() -> None:
    """Crea tablas adicionales necesarias para v2 (categorías, atributos).
    Estas tablas son adiciones backward-compatible: no tocan las tablas
    existentes y sirven solo para funcionalidades nuevas.
    """
    from src.database.connection import DB_ENGINE
    
    # Skip for Postgres - Alembic manages schema
    if DB_ENGINE == 'postgres':
        return

    # if we are storing data in JSON files just ensure the files exist
    if _use_json():
        tables = [
            'productos', 'categories', 'category_attributes', 'product_attributes',
            'roles', 'permissions', 'role_permissions', 'user_roles',
            'warehouses', 'warehouse_stock', 'warehouse_transfers', 'kardex_moves',
            'company_settings'
        ]
        for t in tables:
            # load then save to create empty file if it doesn't exist
            json_store.save_table(t, json_store.load_table(t))
        return

    with get_connection() as conn:
        cur = conn.cursor()
        # categories
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER REFERENCES categories(id),
                name TEXT NOT NULL UNIQUE,
                slug TEXT
            )
        """)
        # category attributes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS category_attributes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL REFERENCES categories(id),
                attr_name TEXT NOT NULL,
                attr_type TEXT DEFAULT 'text',
                attr_options TEXT
            )
        """)
        # product_attributes (flexible attributes per product)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS product_attributes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT NOT NULL,
                attr_name TEXT NOT NULL,
                attr_value TEXT
            )
        """)
        conn.commit()

        # RBAC tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                description TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
                PRIMARY KEY (role_id, permission_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, role_id)
            )
        """)

        # Warehouses and stock
        cur.execute("""
            CREATE TABLE IF NOT EXISTS warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                location TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS warehouse_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT NOT NULL REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE RESTRICT,
                warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
                quantity REAL NOT NULL DEFAULT 0,
                UNIQUE(product_code, warehouse_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS warehouse_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT NOT NULL REFERENCES productos(codigo),
                from_wh INTEGER,
                to_wh INTEGER,
                quantity REAL NOT NULL,
                date TEXT NOT NULL,
                user_id INTEGER,
                notes TEXT
            )
        """)

        # Kardex moves
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kardex_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT NOT NULL REFERENCES productos(codigo),
                type TEXT NOT NULL,
                qty REAL NOT NULL,
                unit_cost REAL,
                total_cost REAL,
                balance_qty REAL,
                balance_cost REAL,
                balance_total REAL,
                date TEXT NOT NULL,
                warehouse_id INTEGER,
                ref_type TEXT,
                ref_id INTEGER
            )
        """)
        conn.commit()

        # Add activo column to productos if not exists
        try:
            cur.execute("ALTER TABLE productos ADD COLUMN activo INTEGER DEFAULT 1")
            conn.commit()
        except Exception:
            pass  # Column might already exist

        # Add avg_cost column to kardex_moves if not exists
        try:
            cur.execute("ALTER TABLE kardex_moves ADD COLUMN avg_cost REAL DEFAULT 0")
            conn.commit()
        except Exception:
            pass  # Column might already exist

        # Add indexes for kardex performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_kardex_product ON kardex_moves(product_code);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_kardex_date ON kardex_moves(date);")
        conn.commit()

        # ------------------------------------------------------------------
        # Tables for devoluciones/returns (nuevo módulo)
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL REFERENCES documents(id),
                document_id INTEGER NOT NULL REFERENCES documents(id),
                reason TEXT,
                total_refund REAL NOT NULL,
                created_by INTEGER,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS return_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL REFERENCES returns(id) ON DELETE CASCADE,
                product_code TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_cost REAL,
                subtotal REAL
            )
        """)
        conn.commit()


# ---------------------------
# Productos
# ---------------------------
# ``get_product_by_code`` está cacheado; la clave se construye como
# ``"src.database.repository.get_product_by_code:(codigo,)"``. Para borrar
# múltiples entradas (p.e. tras actualizar o eliminar varios productos) se
# puede usar ``caching.invalidate_prefix("src.database.repository.get_product_by_code")``.
# El decorador sigue funcionando sin cambios.
@caching.cached(ttl=120)
def get_product_by_code(codigo: str) -> Optional[Tuple]:
    if _use_json():
        prod = json_store.find_one('productos', lambda r: r.get('codigo') == codigo)
        if prod:
            return (
                prod.get('codigo'), prod.get('nombre'), prod.get('categoria',''),
                float(prod.get('precio',0)), int(prod.get('cantidad',0)),
                float(prod.get('avg_cost',0)), int(prod.get('stock_minimo', 5)),
                int(prod.get('reorder_qty', 10)), prod.get('proveedor_id')
            )
        return None

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT codigo, nombre, categoria, precio, cantidad, avg_cost, stock_minimo, reorder_qty, proveedor_id FROM productos WHERE codigo = ?", (codigo,))
        row = cur.fetchone()
        return tuple(row) if row else None


def insert_product(data: Dict[str, Any]) -> None:
    if _use_json():
        # JSON simply appends a dictionary; caller should ensure uniqueness
        json_store.insert('productos', {
            'codigo': data['codigo'],
            'nombre': data['nombre'],
            'categoria': data.get('categoria',''),
            'precio': float(data.get('precio',0.0)),
            'cantidad': int(data.get('cantidad',0)),
            'avg_cost': float(data.get('avg_cost', data.get('precio',0.0))),
            'stock_minimo': int(data.get('stock_minimo', 5)),
            'reorder_qty': int(data.get('reorder_qty', 10)),
            'proveedor_id': data.get('proveedor_id')
        })
        return

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO productos (codigo,nombre,categoria,precio,cantidad,avg_cost,stock_minimo,reorder_qty,proveedor_id)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (data['codigo'], data['nombre'], data.get('categoria',''), float(data.get('precio',0.0)), int(data.get('cantidad',0)), float(data.get('avg_cost', data.get('precio',0.0))), int(data.get('stock_minimo', 5)), int(data.get('reorder_qty', 10)), data.get('proveedor_id')))
        conn.commit()


def update_product_qty_price(codigo: str, cantidad: int, precio: float) -> None:
    if _use_json():
        def _up(r):
            r['cantidad'] = int(cantidad)
            r['precio'] = float(precio)
        json_store.update('productos', lambda r: r.get('codigo') == codigo, _up)
        caching.clear_cache(f"src.database.repository.get_product_by_code:{(codigo,)}")
        caching.clear_cache("src.database.repository.list_products")
        caching.clear_cache("src.database.repository.count_products")
        return

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE productos SET cantidad=?, precio=? WHERE codigo=?", (int(cantidad), float(precio), codigo))
        conn.commit()
        # invalidate cache
        caching.clear_cache(f"src.database.repository.get_product_by_code:{(codigo,)}")
        caching.clear_cache("src.database.repository.list_products")
        caching.clear_cache("src.database.repository.count_products")


@caching.cached(ttl=60)
def list_products(limit: int = 100, offset: int = 0, where_sql: str = "", params: Optional[List] = None) -> List[Tuple]:
    params = params or []
    if _use_json():
        # currently where_sql/params not supported; simple pagination
        rows = json_store.list_rows('productos', lambda r: r.get('activo', 1) == 1, order_key='nombre', limit=limit, offset=offset)
        return [(r.get('codigo'), r.get('nombre'), r.get('categoria',''), float(r.get('precio',0)), int(r.get('cantidad',0))) for r in rows]

    with get_connection() as conn:
        cur = conn.cursor()
        if where_sql:
            where_sql += " AND activo = 1"
        else:
            where_sql = "WHERE activo = 1"
        sql = f"SELECT codigo, nombre, categoria, precio, cantidad FROM productos {where_sql} ORDER BY nombre ASC LIMIT ? OFFSET ?"
        cur.execute(sql, params + [int(limit), int(offset)])
        return [tuple(r) for r in cur.fetchall()]


def count_products(where_sql: str = "", params: Optional[List] = None) -> int:
    params = params or []
    if _use_json():
        rows = json_store.list_rows('productos', lambda r: r.get('activo', 1) == 1)
        return len(rows)
    with get_connection() as conn:
        cur = conn.cursor()
        if where_sql:
            where_sql += " AND activo = 1"
        else:
            where_sql = "WHERE activo = 1"
        sql = f"SELECT COUNT(*) FROM productos {where_sql}"
        cur.execute(sql, params)
        return int(cur.fetchone()[0] or 0)


# ---------------------------
# Settings
# ---------------------------
@caching.cached(ttl=300)
def get_settings_cached() -> Dict[str, Any]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM company_settings")
        rows = cur.fetchall()
        return {r[0]: r[1] for r in rows}


def clear_settings_cache() -> None:
    caching.clear_cache("src.database.repository.get_settings_cached")


# ---------------------------
# Categorías
# ---------------------------
@caching.cached(ttl=300)
def get_categories_tree() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, parent_id, name, slug FROM categories ORDER BY parent_id NULLS FIRST, name ASC")
        rows = cur.fetchall()
        # build tree
        nodes = {r[0]: {'id': r[0], 'parent_id': r[1], 'name': r[2], 'slug': r[3], 'children': []} for r in rows}
        root: List[Dict[str, Any]] = []
        for n in nodes.values():
            pid = n['parent_id']
            if pid and pid in nodes:
                nodes[pid]['children'].append(n)
            else:
                root.append(n)
        return root


def get_category_by_id(cat_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, parent_id, name, slug FROM categories WHERE id=?", (int(cat_id),))
        r = cur.fetchone()
        if not r: return None
        return {'id': r[0], 'parent_id': r[1], 'name': r[2], 'slug': r[3]}


def get_category_attributes(category_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT attr_name, attr_type, attr_options FROM category_attributes WHERE category_id=?", (int(category_id),))
        return [{'name': r[0], 'type': r[1], 'options': r[2]} for r in cur.fetchall()]


def attach_attribute_to_product(product_code: str, attr_name: str, attr_value: str) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO product_attributes (product_code, attr_name, attr_value) VALUES (?,?,?)", (product_code, attr_name, str(attr_value)))
        conn.commit()
        caching.clear_cache("src.database.repository.list_products")


# ---------------------------
# RBAC helpers
# ---------------------------
def create_role(name: str) -> int:
    """Create a role and return its id."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO roles (name) VALUES (?) ON CONFLICT(name) DO NOTHING", (name,))
        conn.commit()
        cur.execute("SELECT id FROM roles WHERE name=?", (name,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Failed to create role '{name}'")
        return int(row[0])


def create_permission(code: str, description: str = "") -> int:
    """Create a permission and return its id."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO permissions (code, description) VALUES (?,?) ON CONFLICT(code) DO NOTHING", (code, description))
        conn.commit()
        cur.execute("SELECT id FROM permissions WHERE code=?", (code,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Failed to create permission '{code}'")
        return int(row[0])


def add_permission_to_role(role_id: int, permission_id: int) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO role_permissions (role_id, permission_id) VALUES (?,?) ON CONFLICT(role_id, permission_id) DO NOTHING", (role_id, permission_id))
        except Exception:
            # fallback for legacy schema using 'perm_id' column name
            cur.execute("INSERT INTO role_permissions (role_id, perm_id) VALUES (?,?) ON CONFLICT(role_id, perm_id) DO NOTHING", (role_id, permission_id))
        conn.commit()


def add_role_to_user(user_id: int, role_id: int) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?,?) ON CONFLICT(user_id, role_id) DO NOTHING", (int(user_id), int(role_id)))
        conn.commit()


def user_has_permission(user_id: int, perm_code: str) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()
        # try permission_id column first, fall back to perm_id for legacy schema
        try:
            cur.execute("""
                SELECT 1 FROM user_roles ur
                JOIN role_permissions rp ON rp.role_id = ur.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE ur.user_id = ? AND p.code = ? LIMIT 1
            """, (int(user_id), perm_code))
        except Exception:
            cur.execute("""
                SELECT 1 FROM user_roles ur
                JOIN role_permissions rp ON rp.role_id = ur.role_id
                JOIN permissions p ON p.id = rp.perm_id
                WHERE ur.user_id = ? AND p.code = ? LIMIT 1
            """, (int(user_id), perm_code))
        return cur.fetchone() is not None


# ---------------------------
# Warehouses / Transfers
# ---------------------------
def create_warehouse(name: str, location: str = "") -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        # First try INSERT (if new)
        cur.execute("INSERT INTO warehouses (name, location) VALUES (?,?) ON CONFLICT(name) DO NOTHING", (name, location))
        conn.commit()
        # If just inserted (rowcount=1), use lastrowid; otherwise fetch existing
        if cur.rowcount > 0:
            return int(cur.lastrowid)
        else:
            # Already exists, fetch it
            cur.execute("SELECT id FROM warehouses WHERE name=?", (name,))
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"Warehouse '{name}' not found and could not be created")
            return int(row[0])


def set_warehouse_stock(product_code: str, warehouse_id: int, quantity: float) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO warehouse_stock (product_code, warehouse_id, quantity)
            VALUES (?,?,?)
            ON CONFLICT(product_code, warehouse_id) DO UPDATE SET quantity=excluded.quantity
        """, (product_code, int(warehouse_id), float(quantity)))
        conn.commit()


def adjust_warehouse_stock(product_code: str, warehouse_id: int, delta: float) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM warehouse_stock WHERE product_code=? AND warehouse_id=?", (product_code, int(warehouse_id)))
        r = cur.fetchone()
        if r:
            new_q = float(r[0]) + float(delta)
            cur.execute("UPDATE warehouse_stock SET quantity=? WHERE product_code=? AND warehouse_id=?", (new_q, product_code, int(warehouse_id)))
        else:
            cur.execute("INSERT INTO warehouse_stock (product_code, warehouse_id, quantity) VALUES (?,?,?)", (product_code, int(warehouse_id), float(delta)))
        conn.commit()


def get_stock_by_warehouse(product_code: str, warehouse_id: int) -> float:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM warehouse_stock WHERE product_code=? AND warehouse_id=?", (product_code, int(warehouse_id)))
        r = cur.fetchone()
        return float(r[0]) if r else 0.0


def get_stock_total(product_code: str) -> float:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(quantity),0) FROM warehouse_stock WHERE product_code=?", (product_code,))
        return float(cur.fetchone()[0] or 0.0)


def record_warehouse_transfer(product_code: str, from_wh: int, to_wh: int, quantity: float, date: str, user_id: int = None, notes: str = None) -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO warehouse_transfers (product_code, from_wh, to_wh, quantity, date, user_id, notes)
            VALUES (?,?,?,?,?,?,?)
        """, (product_code, from_wh, to_wh, float(quantity), date, user_id, notes))
        conn.commit()
        transfer_id = cur.lastrowid
        return int(transfer_id)


# ---------------------------
# Kardex helpers
# ---------------------------
def record_kardex_move(product_code: str, move_type: str, qty: float, unit_cost: float, total_cost: float, balance_qty: float, balance_cost: float, balance_total: float, date: str, warehouse_id: int = None, ref_type: str = None, ref_id: int = None, avg_cost: float = None) -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO kardex_moves (product_code, type, qty, unit_cost, avg_cost, total_cost, balance_qty, balance_cost, balance_total, date, warehouse_id, ref_type, ref_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (product_code, move_type, float(qty), unit_cost, avg_cost if avg_cost is not None else unit_cost, total_cost, float(balance_qty), balance_cost, balance_total, date, warehouse_id, ref_type, ref_id))
        conn.commit()
        kardex_id = cur.lastrowid
        return int(kardex_id)


def get_kardex_moves(product_code: str, warehouse_id: int = None) -> list:
    with get_connection() as conn:
        cur = conn.cursor()
        if warehouse_id:
            cur.execute("SELECT * FROM kardex_moves WHERE product_code=? AND warehouse_id=? ORDER BY date ASC", (product_code, int(warehouse_id)))
        else:
            cur.execute("SELECT * FROM kardex_moves WHERE product_code=? ORDER BY date ASC", (product_code,))
        return [tuple(r) for r in cur.fetchall()]