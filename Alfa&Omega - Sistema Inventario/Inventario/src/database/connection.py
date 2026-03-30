# core/database.py
import os
import re as _re
import sqlite3
from contextlib import contextmanager

from src.core.context import tenant_schema_var

# Regex guard: only safe PostgreSQL schema identifiers are allowed
_SAFE_SCHEMA_RE = _re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]{0,62}$')

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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "src", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# configuration comes from central module
from config import settings

# supported engines: 'sqlite', 'mysql', 'postgres' (legacy sync) and 'json' (local json files)
DB_ENGINE = settings.DB_ENGINE
DB_PATH = os.path.join(DATA_DIR, "inventario.db")  # <- ruta explícita a src/data/inventario.db
# When using JSON mode we will store tables as <DATA_DIR>/<table>.json
DB_JSON_DIR = str(settings.DB_JSON_DIR)

# MySQL settings (used only if DB_ENGINE == 'mysql')
DB_HOST = os.getenv("DB_HOST", "localhost")  # still fall back to env for multi-host setups
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
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
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
        # Multi-tenant: set tenant schema search path from ContextVar (set by TenantMiddleware)
        _tenant_schema = tenant_schema_var.get()
        if not _SAFE_SCHEMA_RE.match(_tenant_schema):
            _pg_pool.putconn(conn)
            raise ValueError(f"TENANT_SCHEMA inválido: {_tenant_schema!r} — solo se permiten identificadores PostgreSQL válidos.")
        _sp_cur = conn.cursor()
        _sp_cur.execute(f"SET search_path = {_tenant_schema}, public")
        _sp_cur.close()
        conn.commit()
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

                def rollback(self):
                    return self._conn.rollback()

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
    elif DB_ENGINE == "json":
        # JSON mode does not use a SQL connection. callers should use the
        # helpers in src.database.json_store or repository functions that
        # automatically route to JSON storage. We return a dummy object so
        # that code which calls get_connection() still enters the context
        # manager but using it will raise if cursor() is accessed.
        class _Dummy:
            def cursor(self):
                raise RuntimeError("no cursor available in json mode; use json_store/repository")
            def commit(self):
                pass
            def close(self):
                pass
        yield _Dummy()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        try:
            yield conn
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
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
        # Migrate existing DB: remove restrictive CHECK constraint on documents.tipo
        # so RETURN/TRANSFER document types are accepted. No-op if already migrated.
        _migrate_documents_remove_check(conn)
        _migrate_documents_add_pos_fields(conn)

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
            tipo TEXT NOT NULL,
            numero TEXT,               -- impreso (serie + correlativo)
            fecha TEXT NOT NULL,
            notas TEXT,
            partner_id INTEGER NULL REFERENCES partners(id) ON DELETE SET NULL,
            payment_method TEXT,
            amount_paid REAL,
            change_given REAL
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_docs_fecha ON documents(fecha);")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_documents_numero ON documents(numero);")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_documents_partner ON documents(partner_id);")

        # Añadir columnas DIAN en documents de forma segura
        columnas_dian = [
            ("cufe", "TEXT"),
            ("dian_estado", "TEXT DEFAULT 'PENDIENTE'"),
            ("dian_xml", "TEXT"),
            ("dian_qr", "TEXT"),
            ("resolucion_dian", "TEXT"),
            ("numero_dian", "TEXT")
        ]
        for col, tipo in columnas_dian:
            try:
                cur.execute(f"ALTER TABLE documents ADD COLUMN {col} {tipo}")
            except Exception:
                pass # La columna ya existe

        # Añadir campos DIAN en company_settings
        columnas_dian_cfg = [
            ("dian_nit", "TEXT"),
            ("dian_razon_social", "TEXT"),
            ("dian_resolucion", "TEXT"),
            ("dian_prefijo", "TEXT DEFAULT 'FE'"),
            ("dian_consecutivo_actual", "TEXT DEFAULT '1'"),
            ("dian_ambiente", "INTEGER DEFAULT 2")
        ]
        for col, tipo in columnas_dian_cfg:
            try:
                cur.execute(f"ALTER TABLE company_settings ADD COLUMN {col} {tipo}")
            except Exception:
                pass

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

        # --- NUEVO: Agregar columnas de crédito si no existen ---
        cur.execute("PRAGMA table_info(partners)")
        cols = [r[1] for r in cur.fetchall()]
        if "credit_limit" not in cols:
            cur.execute("ALTER TABLE partners ADD COLUMN credit_limit REAL DEFAULT 0.0")
        if "credit_balance" not in cols:
            cur.execute("ALTER TABLE partners ADD COLUMN credit_balance REAL DEFAULT 0.0")

        # --- MIGRACIÓN de clientes legacy a partners ---
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='clientes'")
        if cur.fetchone()[0]:
            cur.execute("SELECT id, nombre, telefono, saldo FROM clientes")
            clientes = cur.fetchall()
            for cid, nombre, telefono, saldo in clientes:
                cur.execute(
                    "SELECT id FROM partners WHERE name=? AND (phone=? OR phone IS NULL)",
                    (nombre, telefono)
                )
                if cur.fetchone():
                    continue
                code = f'CUST-{cid}'
                cur.execute(
                    'INSERT INTO partners (code, kind, name, phone, active, credit_balance) VALUES (?, \'CUSTOMER\', ?, ?, 1, ?)',
                    (code, nombre, telefono, saldo if saldo is not None else 0.0)
                )
        conn.commit()
        # POS: Clientes
        cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            saldo REAL NOT NULL DEFAULT 0.0
        );
        """)

        # POS: Cash sessions
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cash_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            opening_amount REAL NOT NULL DEFAULT 0.0,
            closing_amount REAL,
            opened_at TEXT NOT NULL,
            closed_at TEXT,
            arqueo_declared REAL,
            arqueo_notes TEXT
        );
        """)

        # POS: Cash movements
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cash_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES cash_sessions(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
        );
        """)

        # API Keys (Tarea 18)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash         TEXT UNIQUE NOT NULL,
            tenant_id        TEXT NOT NULL,
            nombre           TEXT,
            activo           INTEGER DEFAULT 1,
            created_at       TEXT DEFAULT (datetime('now')),
            last_used        TEXT,
            requests_today   INTEGER DEFAULT 0,
            requests_total   INTEGER DEFAULT 0
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_api_keys_tenant ON api_keys(tenant_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_api_keys_hash   ON api_keys(key_hash)")

        # Industry Config (Tarea 30)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS industry_config (
            id INTEGER PRIMARY KEY CHECK(id=1),
            industry TEXT DEFAULT 'retail',
            unidad_base TEXT DEFAULT 'unidad',
            unidad_secundaria TEXT,
            impuesto_default REAL DEFAULT 19.0,
            modulo_citas INTEGER DEFAULT 0,
            modulo_garantias INTEGER DEFAULT 0,
            modulo_vencimientos INTEGER DEFAULT 0,
            modulo_tallas_colores INTEGER DEFAULT 0,
            modulo_serial INTEGER DEFAULT 0,
            pos_label TEXT DEFAULT 'Venta'
        );
        """)

        # Tarea 32: Auto-Reorder (stock mínimo)
        try:
            cur.execute("ALTER TABLE productos ADD COLUMN stock_minimo INTEGER DEFAULT 5")
            cur.execute("ALTER TABLE productos ADD COLUMN reorder_qty INTEGER DEFAULT 10")
            cur.execute("ALTER TABLE productos ADD COLUMN proveedor_id INTEGER REFERENCES partners(id)")
            conn.commit()
        except Exception:
            pass

        # RBAC / auditoría
        init_rbac(conn)
        
        # Tarea 38: Onboarding Tour
        try:
            cur.execute("ALTER TABLE users ADD COLUMN tour_completado INTEGER DEFAULT 0")
            conn.commit()
        except Exception:
            pass
            
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
        # POS schema migrations
        try:
            from src.services import pos_service as _pos
            _pos.ensure_schema()
        except Exception:
            pass
        # CxC — Cuentas por Cobrar
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cuentas_cobrar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners(id) ON DELETE SET NULL,
            documento TEXT,
            monto REAL NOT NULL,
            saldo REAL NOT NULL,
            fecha_emision TEXT NOT NULL,
            fecha_vencimiento TEXT,
            estado TEXT DEFAULT 'PENDIENTE',
            notas TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_cxc_partner ON cuentas_cobrar(partner_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_cxc_estado  ON cuentas_cobrar(estado)")

        # CxP — Cuentas por Pagar
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cuentas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners(id) ON DELETE SET NULL,
            documento TEXT,
            monto REAL NOT NULL,
            saldo REAL NOT NULL,
            fecha_emision TEXT NOT NULL,
            fecha_vencimiento TEXT,
            estado TEXT DEFAULT 'PENDIENTE',
            notas TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_cxp_partner ON cuentas_pagar(partner_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_cxp_estado  ON cuentas_pagar(estado)")

        # Notif Config — configuración SMTP y alertas
        cur.execute("""
        CREATE TABLE IF NOT EXISTS notif_config (
            id             INTEGER PRIMARY KEY CHECK(id=1),
            smtp_host      TEXT,
            smtp_port      INTEGER DEFAULT 587,
            smtp_user      TEXT,
            smtp_pass      TEXT,
            from_email     TEXT,
            to_emails      TEXT,
            activo         INTEGER DEFAULT 0,
            stock_critico  INTEGER DEFAULT 1,
            stock_bajo     INTEGER DEFAULT 1,
            resumen_diario INTEGER DEFAULT 1,
            hora_resumen   TEXT DEFAULT '08:00'
        )
        """)

        conn.commit()


        # Agregar columna estado a documents para órdenes de compra
        try:
            cur.execute("ALTER TABLE documents ADD COLUMN estado TEXT DEFAULT 'ACTIVO'")
        except Exception:
            pass  # Columna ya existe


def _migrate_documents_remove_check(conn) -> None:
    """
    Safe migration: if the 'documents' table has a CHECK constraint that restricts
    tipo to old values, recreates it without the constraint to allow RETURN/TRANSFER.
    Uses copy-rename pattern in a single transaction to avoid data loss.
    """
    cur = conn.cursor()
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='documents'")
    row = cur.fetchone()
    if not row:
        return  # Table doesn't exist yet; init_db will create it without constraint.
    table_sql = row[0] or ""
    if "CHECK" not in table_sql:
        return  # No CHECK constraint present — nothing to migrate.
    # Perform the migration inside this connection (caller must commit).
    cur.execute("PRAGMA foreign_keys = OFF")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            numero TEXT,
            fecha TEXT NOT NULL,
            notas TEXT,
            partner_id INTEGER NULL REFERENCES partners(id) ON DELETE SET NULL,
            payment_method TEXT,
            amount_paid REAL,
            change_given REAL
        )
    """)
    cur.execute("""
        INSERT INTO documents_new
        SELECT id, tipo, numero, fecha, notas, partner_id,
               CASE WHEN EXISTS(SELECT 1 FROM pragma_table_info('documents') WHERE name='payment_method') THEN payment_method ELSE NULL END,
               CASE WHEN EXISTS(SELECT 1 FROM pragma_table_info('documents') WHERE name='amount_paid') THEN amount_paid ELSE NULL END,
               CASE WHEN EXISTS(SELECT 1 FROM pragma_table_info('documents') WHERE name='change_given') THEN change_given ELSE NULL END
        FROM documents
    """)
    cur.execute("DROP TABLE documents")
    cur.execute("ALTER TABLE documents_new RENAME TO documents")
    # Recreate indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_docs_fecha ON documents(fecha)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_documents_numero ON documents(numero)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_documents_partner ON documents(partner_id)")
    cur.execute("PRAGMA foreign_keys = ON")
    conn.commit()

def _migrate_documents_add_pos_fields(conn) -> None:
    """Safely adds POS fields to the documents table if they don't exist."""
    cur = conn.cursor()
    if not _table_exists(conn, 'documents'):
        return
        
    # sqlite specific alter rules
    try:
        if not _column_exists(conn, 'documents', 'payment_method'):
            cur.execute("ALTER TABLE documents ADD COLUMN payment_method TEXT")
        if not _column_exists(conn, 'documents', 'amount_paid'):
            cur.execute("ALTER TABLE documents ADD COLUMN amount_paid REAL")
        if not _column_exists(conn, 'documents', 'change_given'):
            cur.execute("ALTER TABLE documents ADD COLUMN change_given REAL")
        conn.commit()
    except Exception as e:
        try:
            from src.core.error_handler import log_error
            log_error(e, context={"operation": "_migrate_documents_add_pos_fields"})
        except Exception:
            print(f"Error migrating documents POS fields: {e}")