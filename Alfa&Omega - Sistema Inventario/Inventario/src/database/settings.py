# core/settings.py
from __future__ import annotations
from typing import Dict, Any
from src.database.connection import get_connection

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS company_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    company_name TEXT NOT NULL DEFAULT 'Mi Empresa',
    company_tax  TEXT NOT NULL DEFAULT 'NIT/RUC',
    company_addr TEXT NOT NULL DEFAULT 'Dirección',
    tax_included INTEGER NOT NULL DEFAULT 0,   -- 0=no, 1=sí
    tax_rate     REAL NOT NULL DEFAULT 0.0,    -- 0.19 => 19%
    logo_path    TEXT,
    dian_nit     TEXT DEFAULT '',
    dian_razon_social TEXT DEFAULT '',
    dian_resolucion TEXT DEFAULT '',
    dian_prefijo TEXT DEFAULT 'FE',
    dian_consecutivo_actual TEXT DEFAULT '1',
    dian_ambiente INTEGER DEFAULT 2
);

"""

DEFAULTS = {
    "company_name": "Mi Empresa",
    "company_tax":  "NIT/RUC",
    "company_addr": "Dirección",
    "tax_included": 0,
    "tax_rate":     0.0,
    "logo_path":    None,
}

def ensure_schema() -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.executescript(SCHEMA_SQL)
        # Inserta fila única id=1 si no existe
        cur.execute("SELECT 1 FROM company_settings WHERE id=1")
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO company_settings
                (id, company_name, company_tax, company_addr, tax_included, tax_rate, logo_path)
                VALUES (1, ?, ?, ?, ?, ?, ?)
            """, (DEFAULTS["company_name"], DEFAULTS["company_tax"], DEFAULTS["company_addr"],
                  DEFAULTS["tax_included"], DEFAULTS["tax_rate"], DEFAULTS["logo_path"]))
        conn.commit()

def get_settings() -> Dict[str, Any]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT company_name, company_tax, company_addr, tax_included, tax_rate, logo_path
            FROM company_settings WHERE id=1
        """)
        row = cur.fetchone()
        if not row:
            ensure_schema()
            return DEFAULTS.copy()
        return {
            "company_name": row[0],
            "company_tax":  row[1],
            "company_addr": row[2],
            "tax_included": int(row[3] or 0),
            "tax_rate":     float(row[4] or 0.0),
            "logo_path":    row[5],
        }

def update_settings(**kwargs) -> None:
    allowed = {"company_name","company_tax","company_addr","tax_included","tax_rate","logo_path",
               "dian_nit","dian_razon_social","dian_resolucion","dian_prefijo","dian_consecutivo_actual","dian_ambiente"}
    sets = []; params = []
    for k, v in kwargs.items():
        if k in allowed:
            sets.append(f"{k}=?")
            params.append(v)
    if not sets:
        return
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"UPDATE company_settings SET {', '.join(sets)} WHERE id=1", params)
        conn.commit()


# ─── Notificaciones ────────────────────────────────────────────────

_NOTIF_DEFAULTS: dict = {
    "smtp_host": "", "smtp_port": 587, "smtp_user": "", "smtp_pass": "",
    "from_email": "", "to_emails": "", "activo": 0,
    "stock_critico": 1, "stock_bajo": 1, "resumen_diario": 1,
    "hora_resumen": "08:00",
}


def get_notif_config() -> Dict[str, Any]:
    """Lee la configuración SMTP/notificaciones. Crea la fila si no existe."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT smtp_host, smtp_port, smtp_user, smtp_pass, from_email,
                   to_emails, activo, stock_critico, stock_bajo,
                   resumen_diario, hora_resumen
            FROM notif_config WHERE id=1
        """)
        row = cur.fetchone()
        if not row:
            return _NOTIF_DEFAULTS.copy()
        keys = ["smtp_host", "smtp_port", "smtp_user", "smtp_pass",
                "from_email", "to_emails", "activo",
                "stock_critico", "stock_bajo", "resumen_diario", "hora_resumen"]
        return dict(zip(keys, row))


def save_notif_config(cfg: dict) -> None:
    """Upsert de notif_config id=1."""
    allowed = set(_NOTIF_DEFAULTS.keys())
    data = {k: cfg.get(k, _NOTIF_DEFAULTS[k]) for k in allowed}
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM notif_config WHERE id=1")
        exists = cur.fetchone()
        if exists:
            sets = ", ".join(f"{k}=?" for k in data)
            cur.execute(
                f"UPDATE notif_config SET {sets} WHERE id=1",
                list(data.values())
            )
        else:
            cols  = ", ".join(["id"] + list(data.keys()))
            slots = ", ".join(["1"] + ["?" for _ in data])
            cur.execute(
                f"INSERT INTO notif_config ({cols}) VALUES ({slots})",
                list(data.values())
            )
        conn.commit()
