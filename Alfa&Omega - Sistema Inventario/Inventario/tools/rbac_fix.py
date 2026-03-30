# tools/rbac_fix.py
import os
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()
if DB_ENGINE == 'postgres':
    print("\u26a0 rbac_fix.py is SQLite-specific and not compatible with Postgres.")
    print("  Please use the new RBAC management system in the GUI instead.")
    raise SystemExit(0)

from core.database import get_connection
import bcrypt
import logging

logger = logging.getLogger(__name__)

PERMISSIONS = [
    "PRODUCT_CREATE","PRODUCT_UPDATE","PRODUCT_DELETE",
    "PURCHASE_POST","SALE_POST","ADJUST_POST",
    "EXPORT_DATA","VIEW_COST","VIEW_AUDIT","ADMIN"
]
DEFAULT_ROLES = {
    "Admin": PERMISSIONS,
    "Gerente": ["PRODUCT_CREATE","PRODUCT_UPDATE","PURCHASE_POST","SALE_POST","ADJUST_POST","EXPORT_DATA","VIEW_COST"],
    "Operador": ["PRODUCT_CREATE","PRODUCT_UPDATE","PURCHASE_POST","SALE_POST","ADJUST_POST"],
    "Cajero": ["SALE_POST"],
    "Auditor": ["EXPORT_DATA","VIEW_AUDIT"]
}

def ensure_rbac():
    with get_connection() as conn:
        cur = conn.cursor()

        # Tablas mínimas (por si faltan)
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            pass_hash TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            perm_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
            PRIMARY KEY (role_id, perm_id)
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, role_id)
        )""")

        # Inserta permisos
        for code in PERMISSIONS:
            cur.execute("INSERT INTO permissions (code, description) VALUES (?, ?) ON CONFLICT(code) DO NOTHING",
                        (code, code.replace("_"," ").title()))

        # Inserta roles y mapea permisos
        for role, perms in DEFAULT_ROLES.items():
            cur.execute("INSERT INTO roles (name) VALUES (?) ON CONFLICT(name) DO NOTHING", (role,))
            cur.execute("SELECT id FROM roles WHERE name=?", (role,))
            role_id = cur.fetchone()[0]
            for p in perms:
                cur.execute("SELECT id FROM permissions WHERE code=?", (p,))
                perm_id = cur.fetchone()[0]
                cur.execute("INSERT INTO role_permissions (role_id, perm_id) VALUES (?,?) ON CONFLICT(role_id, perm_id) DO NOTHING", (role_id, perm_id))

        # Usuario admin por defecto
        cur.execute("SELECT id FROM users WHERE username='admin'")
        row = cur.fetchone()
        if row is None:
            # crea admin/admin123
            pass_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cur.execute("INSERT INTO users (username, name, pass_hash, active) VALUES (?,?,?,1)",
                        ("admin","Administrador", pass_hash))
            admin_id = cur.lastrowid
        else:
            admin_id = row[0]
            # lo activamos por si acaso
            cur.execute("UPDATE users SET active=1 WHERE id=?", (admin_id,))

        # Asegura que admin tenga rol “Admin”
        cur.execute("SELECT id FROM roles WHERE name='Admin'")
        role_row = cur.fetchone()
        if role_row:
            rid = role_row[0]
            cur.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?,?) ON CONFLICT(user_id, role_id) DO NOTHING", (admin_id, rid))

        conn.commit()

if __name__ == "__main__":
    ensure_rbac()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger.info("RBAC verificado/corregido. Intenta iniciar sesión como admin.")
