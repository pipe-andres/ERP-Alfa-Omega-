# core/partners.py
from __future__ import annotations
from typing import Optional, List, Dict, Tuple
from src.database.connection import get_connection, DB_ENGINE

# -----------------------------------
# Esquema y migraciones mínimas
# -----------------------------------

def ensure_schema() -> None:
    """
    Crea la tabla partners si no existe (solo en SQLite).
    Postgres schema es manejado por Alembic.
    """
    # If running against Postgres, skip inline DDL; Alembic manages schema
    if DB_ENGINE == 'postgres':
        return

    with get_connection() as conn:
        cur = conn.cursor()

        # Tabla de partners (clientes/proveedores)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS partners (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            code      TEXT UNIQUE NOT NULL,
            kind      TEXT NOT NULL,
            name      TEXT NOT NULL,
            tax_id    TEXT,
            phone     TEXT,
            email     TEXT,
            address   TEXT,
            city      TEXT,
            notes     TEXT,
            active    INTEGER NOT NULL DEFAULT 1
        )
        """)

        # Índices recomendados
        cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_kind      ON partners(kind)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_name      ON partners(name)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_tax_id    ON partners(tax_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_active    ON partners(active)")

        # Agregar partner_id a documents si falta (SQLite only)
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            if cur.fetchone():
                cur.execute("PRAGMA table_info(documents)")
                cols = [r[1] for r in cur.fetchall()]
                if "partner_id" not in cols:
                    cur.execute("ALTER TABLE documents ADD COLUMN partner_id INTEGER")
                    cur.execute("CREATE INDEX IF NOT EXISTS ix_documents_partner ON documents(partner_id)")
        except Exception:
            pass

        conn.commit()

# -----------------------------------
# Utilidades
# -----------------------------------

def _norm_code(code: str) -> str:
    c = (code or "").strip()
    if not c:
        raise ValueError("El código es obligatorio.")
    return c.upper()

def _norm_kind(kind: str) -> str:
    k = (kind or "").strip().upper()
    if k not in ("CUSTOMER", "SUPPLIER"):
        raise ValueError("kind debe ser 'CUSTOMER' o 'SUPPLIER'.")
    return k

# -----------------------------------
# CRUD
# -----------------------------------

def create_partner(
    code: str,
    name: str,
    kind: str,
    tax_id: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    notes: Optional[str] = None,
    active: bool = True,
) -> int:
    """
    Crea un partner (cliente/proveedor). Retorna ID.
    code: único (ej. CLI-0001, PROV-0001)
    kind: 'CUSTOMER' o 'SUPPLIER'
    """
    code = _norm_code(code)
    kind = _norm_kind(kind)
    if not name or not name.strip():
        raise ValueError("El nombre es obligatorio.")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO partners
            (code, kind, name, tax_id, phone, email, address, city, notes, active)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (code, kind, name.strip(), tax_id, phone, email, address, city, notes, 1 if active else 0))
        conn.commit()
        return cur.lastrowid

def update_partner(
    code: str,
    *,
    name: Optional[str] = None,
    tax_id: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    notes: Optional[str] = None,
    kind: Optional[str] = None,   # permitido cambiar CUSTOMER<->SUPPLIER
) -> None:
    """Actualiza campos del partner identificado por code."""
    code = _norm_code(code)
    sets = []
    params = []
    if name is not None:
        sets.append("name = ?"); params.append(name.strip())
    if tax_id is not None:
        sets.append("tax_id = ?"); params.append(tax_id)
    if phone is not None:
        sets.append("phone = ?"); params.append(phone)
    if email is not None:
        sets.append("email = ?"); params.append(email)
    if address is not None:
        sets.append("address = ?"); params.append(address)
    if city is not None:
        sets.append("city = ?"); params.append(city)
    if notes is not None:
        sets.append("notes = ?"); params.append(notes)
    if kind is not None:
        sets.append("kind = ?"); params.append(_norm_kind(kind))

    if not sets:
        return

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM partners WHERE code=?", (code,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"No existe partner con código {code}.")
        sql = f"UPDATE partners SET {', '.join(sets)} WHERE code=?"
        cur.execute(sql, params + [code])
        conn.commit()

def set_partner_active(code: str, active: bool) -> None:
    code = _norm_code(code)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE partners SET active=? WHERE code=?", (1 if active else 0, code))
        if cur.rowcount == 0:
            raise ValueError(f"No existe partner con código {code}.")
        conn.commit()

def delete_partner(code: str, *, hard: bool = False) -> None:
    """
    Elimina partner.
    Por defecto es 'soft' (active=0). Si hard=True, borra la fila solo si
    no está referenciada por documents (partner_id).
    """
    code = _norm_code(code)
    with get_connection() as conn:
        cur = conn.cursor()
        if not hard:
            cur.execute("UPDATE partners SET active=0 WHERE code=?", (code,))
            if cur.rowcount == 0:
                raise ValueError(f"No existe partner con código {code}.")
        else:
            # Verificar referencias
            cur.execute("SELECT id FROM partners WHERE code=?", (code,))
            r = cur.fetchone()
            if not r:
                raise ValueError(f"No existe partner con código {code}.")
            pid = r[0]
            cur.execute("SELECT COUNT(*) FROM documents WHERE partner_id=?", (pid,))
            ref = cur.fetchone()[0]
            if ref > 0:
                raise ValueError("No se puede borrar: hay documentos que lo referencian.")
            cur.execute("DELETE FROM partners WHERE id=?", (pid,))
        conn.commit()

# -----------------------------------
# Lecturas y búsqueda
# -----------------------------------

def get_partner_by_code(code: str) -> Optional[Tuple]:
    code = _norm_code(code)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, code, kind, name, tax_id, phone, email, address, city, notes, active
            FROM partners WHERE code=?
        """, (code,))
        row = cur.fetchone()
        return tuple(row) if row else None

def list_partners(
    kind: Optional[str] = None,    # 'CUSTOMER' | 'SUPPLIER' | None
    q: Optional[str] = None,       # busca en code, name, tax_id, email, phone
    active: Optional[bool] = None, # None = todos
    order_by: str = "name",
    asc: bool = True,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    allowed_order = {"code","name","kind","city","active","tax_id"}
    if order_by not in allowed_order:
        order_by = "name"
    order_sql = "ASC" if asc else "DESC"

    where = []; params = []
    if kind:
        where.append("kind = ?"); params.append(_norm_kind(kind))
    if q:
        like = f"%{q.strip()}%"
        where.append("(code LIKE ? OR name LIKE ? OR tax_id LIKE ? OR email LIKE ? OR phone LIKE ?)")
        params += [like, like, like, like, like]
    if active is not None:
        where.append("active = ?"); params.append(1 if active else 0)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, code, kind, name, tax_id, phone, email, address, city, notes, active
            FROM partners
            {where_sql}
            ORDER BY {order_by} {order_sql}
            LIMIT ? OFFSET ?
        """, params + [int(limit), int(offset)])
        rows = cur.fetchall()

    out = []
    for r in rows:
        out.append({
            "id": r[0], "code": r[1], "kind": r[2], "name": r[3], "tax_id": r[4],
            "phone": r[5], "email": r[6], "address": r[7], "city": r[8],
            "notes": r[9], "active": bool(r[10])
        })
    return out

def count_partners(kind: Optional[str] = None, q: Optional[str] = None, active: Optional[bool] = None) -> int:
    where = []; params = []
    if kind:
        where.append("kind = ?"); params.append(_norm_kind(kind))
    if q:
        like = f"%{q.strip()}%"
        where.append("(code LIKE ? OR name LIKE ? OR tax_id LIKE ? OR email LIKE ? OR phone LIKE ?)")
        params += [like, like, like, like, like]
    if active is not None:
        where.append("active = ?"); params.append(1 if active else 0)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM partners {where_sql}", params)
        return cur.fetchone()[0]
