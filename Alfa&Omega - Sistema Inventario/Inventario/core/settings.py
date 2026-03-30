# core/settings.py
from __future__ import annotations
from typing import Dict, Any
from .database import get_connection

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS company_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    company_name TEXT NOT NULL DEFAULT 'Mi Empresa',
    company_tax  TEXT NOT NULL DEFAULT 'NIT/RUC',
    company_addr TEXT NOT NULL DEFAULT 'Dirección',
    tax_included INTEGER NOT NULL DEFAULT 0,   -- 0=no, 1=sí
    tax_rate     REAL NOT NULL DEFAULT 0.0,    -- 0.19 => 19%
    logo_path    TEXT
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
    allowed = {"company_name","company_tax","company_addr","tax_included","tax_rate","logo_path"}
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
