# core/database.py
import os
import sqlite3
from contextlib import contextmanager

# Postgres sync façade support
try:
    import psycopg2
    from psycopg2 import pool as _psycopg2_pool
except Exception:
    psycopg2 = None
    _psycopg2_pool = None

_pg_pool = None


class CursorWrapper:
    """Wraps a psycopg2 cursor to accept '?' placeholders and SQLite helpers.

    - Translates '?' -> '%s'
    - Translates SELECT last_insert_rowid() -> SELECT LASTVAL()
    """
    def __init__(self, cur):
        self._cur = cur

    def execute(self, sql, params=None):
        if params is None:
            params = ()
        sql2 = sql.replace('?', '%s')
        sql2 = sql2.replace('SELECT last_insert_rowid()', 'SELECT LASTVAL()')
        return self._cur.execute(sql2, params)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    @property
    def rowcount(self):
        return getattr(self._cur, 'rowcount', -1)

    def lastrowid(self):
        try:
            self._cur.execute('SELECT LASTVAL()')
            return self._cur.fetchone()[0]
        except Exception:
            return None

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Config via env
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()  # 'sqlite' or 'mysql'
DB_PATH = os.getenv("DB_PATH", os.path.join(DATA_DIR, "inventario.db"))

# MySQL settings (used only if DB_ENGINE == 'mysql')
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "inventario")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))

_mysql_pool = None

try:
    import mysql.connector
    from mysql.connector import pooling
except Exception:
    mysql = None
    pooling = None


@contextmanager
def get_connection():
    """Context manager that yields a DB connection.
    By default uses SQLite. Set env `DB_ENGINE=mysql` to use MySQL.
    """
    # DEPRECATION NOTICE: this module provides a legacy sync DB access layer.
    # The project now uses SQLAlchemy async (see `src/database/orm.py`) and
    # async services in `src/services/*_async.py`. This module will be
    # removed in a future release. Prefer the async API and update callers.
    # See docs/MIGRATION_TO_POSTGRES.md for migration instructions.

    if DB_ENGINE == "mysql":
        if pooling is None:
            raise RuntimeError("mysql-connector-python is required for MySQL support. Install it in your environment.")
        global _mysql_pool
        if _mysql_pool is None:
            _mysql_pool = pooling.MySQLConnectionPool(
                pool_name="inventario_pool",
                pool_size=DB_POOL_SIZE,
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                charset="utf8mb4",
                use_unicode=True,
            )
        conn = _mysql_pool.get_connection()
        try:
            yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass
    elif DB_ENGINE == "postgres":
        # Synchronous fallback façade for legacy sync code using psycopg2 pool.
        if _psycopg2_pool is None:
            raise RuntimeError("psycopg2 is required for Postgres sync support. Install it in your environment.")
        global _pg_pool
        if _pg_pool is None:
            _pg_pool = _psycopg2_pool.SimpleConnectionPool(
                1,
                DB_POOL_SIZE,
                user=DB_USER,
                password=DB_PASS,
                host=DB_HOST,
                port=int(os.getenv('DB_PORT', '5432')),
                database=DB_NAME,
            )
        conn = _pg_pool.getconn()
        try:
            cur = conn.cursor()
            wrapper = CursorWrapper(cur)

            class _ConnProxy:
                def __init__(self, conn, wrapper, raw_cursor):
                    self._conn = conn
                    self._wrapper = wrapper
                    self._raw = raw_cursor

                def cursor(self):
                    return self._wrapper

                def commit(self):
                    return self._conn.commit()

                def close(self):
                    try:
                        try:
                            self._raw.close()
                        except Exception:
                            pass
                    except Exception:
                        pass

            try:
                yield _ConnProxy(conn, wrapper, cur)
            finally:
                try:
                    _pg_pool.putconn(conn)
                except Exception:
                    try:
                        conn.close()
                    except Exception:
                        pass
        finally:
            pass
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        try:
            yield conn
        finally:
            conn.close()

def _column_exists(conn, table: str, column: str) -> bool:
    """Check if a column exists in a table. Works with SQLite and Postgres."""
    if DB_ENGINE == 'postgres':
        query = """
        SELECT 1 FROM information_schema.columns 
        WHERE table_name=%s AND column_name=%s
        """
        cur = conn.cursor() if hasattr(conn, 'cursor') else conn
        cur.execute(query, (table, column))
        return cur.fetchone() is not None
    else:
        # SQLite
        cur = conn.execute(f"PRAGMA table_info({table})")
        return any(row["name"] == column for row in cur.fetchall())

def _table_exists(conn, name: str) -> bool:
    """Check if a table exists. Works with SQLite and Postgres."""
    if DB_ENGINE == 'postgres':
        query = "SELECT 1 FROM information_schema.tables WHERE table_name=%s"
        cur = conn.cursor() if hasattr(conn, 'cursor') else conn
        cur.execute(query, (name,))
        return cur.fetchone() is not None
    else:
        # SQLite
        cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?;", (name,))
        return cur.fetchone() is not None

def init_rbac(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        pass_hash TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    );
    """)
    cur.execute("""CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        description TEXT
    );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS role_permissions (
        role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
        perm_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
        PRIMARY KEY (role_id, perm_id)
    );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS user_roles (
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
        PRIMARY KEY (user_id, role_id)
    );""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        action TEXT NOT NULL,
        details TEXT,
        created_at TEXT NOT NULL
    );
    """)
    conn.commit()

def init_db():
    # If running against Postgres, skip inline DDL; Alembic will manage schema
    if DB_ENGINE == 'postgres':
        return

    with get_connection() as conn:
        cur = conn.cursor()

        # Productos
        cur.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            categoria TEXT,
            precio REAL NOT NULL DEFAULT 0,     -- usamos 'precio' como costo promedio
            cantidad INTEGER NOT NULL DEFAULT 0,
            avg_cost REAL NOT NULL DEFAULT 0    -- reserva futura (coherente)
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prod_codigo ON productos(codigo);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prod_nombre ON productos(nombre);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prod_categoria ON productos(categoria);")

        # Historial simple (altas/mods/imports) – opcional
        cur.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            nombre TEXT,
            accion TEXT,
            fecha TEXT
        );
        """)

        # Documents (alineado con services.py y documentos.py)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL CHECK (tipo IN ('PURCHASE','SALE','ADJUST','OPENING','IMPORT')),
            numero TEXT,               -- impreso (serie + correlativo)
            fecha TEXT NOT NULL,
            notas TEXT,
            partner_id INTEGER NULL REFERENCES partners(id) ON DELETE SET NULL
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_docs_fecha ON documents(fecha);")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_documents_numero ON documents(numero);")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_documents_partner ON documents(partner_id);")

        # Document lines (usa doc_id y razón)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS document_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            codigo TEXT NOT NULL REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE RESTRICT,
            qty REAL NOT NULL,
            unit_cost REAL,
            unit_price REAL,
            reason TEXT
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lines_doc ON document_lines(doc_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lines_codigo ON document_lines(codigo);")

        # Stock movements (coherente con services.py)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
            codigo TEXT NOT NULL REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE RESTRICT,
            qty REAL NOT NULL,            -- +entrada / -salida
            unit_cost REAL,               -- costo aplicado para valorización
            unit_price REAL,              -- precio venta si aplica
            tipo TEXT NOT NULL,           -- 'PURCHASE'|'SALE'|'ADJUST+'|'ADJUST-'
            reason TEXT,
            created_at TEXT NOT NULL
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mov_codigo_fecha ON stock_movements(codigo, created_at);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mov_doc ON stock_movements(doc_id);")

        # Vista de stock actual por movimientos (opcional; tu GUI usa productos.cantidad)
        cur.execute("""
        CREATE VIEW IF NOT EXISTS v_stock_actual AS
        SELECT p.codigo AS codigo,
               COALESCE(SUM(m.qty), 0) AS stock
        FROM productos p
        LEFT JOIN stock_movements m ON m.codigo = p.codigo
        GROUP BY p.codigo;
        """)

        # Numeradores: doc_series (si documentos.ensure_schema no corrió aún)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS doc_series (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_type  TEXT NOT NULL,    -- 'PURCHASE' | 'SALE'
            series    TEXT NOT NULL,    -- 'C01', 'V01', etc.
            prefix    TEXT,
            next_no   INTEGER NOT NULL DEFAULT 1,
            UNIQUE(doc_type, series)
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_doc_series_type ON doc_series(doc_type);")

        # Partners (para cliente/proveedor) – por si aún no corriste ensure_schema()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS partners (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            code      TEXT UNIQUE NOT NULL,
            kind      TEXT NOT NULL,           -- 'CUSTOMER' | 'SUPPLIER'
            name      TEXT NOT NULL,
            tax_id    TEXT,
            phone     TEXT,
            email     TEXT,
            address   TEXT,
            city      TEXT,
            notes     TEXT,
            active    INTEGER NOT NULL DEFAULT 1
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_kind   ON partners(kind)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_name   ON partners(name)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_tax_id ON partners(tax_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_active ON partners(active)")

        # RBAC / auditoría
        init_rbac(conn)
        # Ensure auxiliary schemas from other modules are present (settings, repository)
        try:
            # import locally to avoid top-level circular imports
            from src.database import settings as _settings
            _settings.ensure_schema()
        except Exception:
            # if settings module not available, ignore (tests will surface errors)
            pass
        try:
            from src.database import repository as _repo
            _repo.ensure_schema()
        except Exception:
            pass
        conn.commit()
