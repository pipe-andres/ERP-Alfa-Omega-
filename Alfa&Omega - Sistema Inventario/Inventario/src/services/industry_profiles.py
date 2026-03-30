"""
services/industry_profiles.py
=============================
Configuración declarativa por industria. Permite encender/apagar módulos
según el tipo de negocio sin usar if/else esparcidos.
"""
from __future__ import annotations
import logging

from src.database.connection import get_connection

_LOG = logging.getLogger(__name__)

# Definición declarativa pura de los perfiles soportados
PROFILES = {
    "retail": {
        "unidad_base": "unidad",
        "unidad_secundaria": None,
        "impuesto_default": 19.0,
        "modulo_citas": 0,
        "modulo_garantias": 1,
        "modulo_vencimientos": 0,
        "modulo_tallas_colores": 0,
        "modulo_serial": 0,
        "pos_label": "Venta"
    },
    "perfumeria": {
        "unidad_base": "ml",
        "unidad_secundaria": "frasco",
        "impuesto_default": 19.0,
        "modulo_citas": 0,
        "modulo_garantias": 0,
        "modulo_vencimientos": 0,
        "modulo_tallas_colores": 0,
        "modulo_serial": 0,
        "pos_label": "Venta"
    },
    "ropa": {
        "unidad_base": "prenda",
        "unidad_secundaria": None,
        "impuesto_default": 19.0,
        "modulo_citas": 0,
        "modulo_garantias": 1,
        "modulo_vencimientos": 0,
        "modulo_tallas_colores": 1,
        "modulo_serial": 0,
        "pos_label": "Venta"
    },
    "ferreteria": {
        "unidad_base": "unidad",
        "unidad_secundaria": "caja",
        "impuesto_default": 19.0,
        "modulo_citas": 0,
        "modulo_garantias": 1,
        "modulo_vencimientos": 0,
        "modulo_tallas_colores": 0,
        "modulo_serial": 0,
        "pos_label": "Cotización/Venta"
    },
    "minimarket": {
        "unidad_base": "unidad",
        "unidad_secundaria": "kg",
        "impuesto_default": 0.0,
        "modulo_citas": 0,
        "modulo_garantias": 0,
        "modulo_vencimientos": 1,
        "modulo_tallas_colores": 0,
        "modulo_serial": 0,
        "pos_label": "Ticket"
    },
    "tecnologia": {
        "unidad_base": "unidad",
        "unidad_secundaria": None,
        "impuesto_default": 19.0,
        "modulo_citas": 0,
        "modulo_garantias": 1,
        "modulo_vencimientos": 0,
        "modulo_tallas_colores": 0,
        "modulo_serial": 1,
        "pos_label": "Venta"
    },
    "barberia": {
        "unidad_base": "servicio",
        "unidad_secundaria": "producto",
        "impuesto_default": 0.0,
        "modulo_citas": 1,
        "modulo_garantias": 0,
        "modulo_vencimientos": 0,
        "modulo_tallas_colores": 0,
        "modulo_serial": 0,
        "pos_label": "Servicio"
    },
    "papeleria": {
        "unidad_base": "unidad",
        "unidad_secundaria": "resma",
        "impuesto_default": 19.0,
        "modulo_citas": 0,
        "modulo_garantias": 0,
        "modulo_vencimientos": 0,
        "modulo_tallas_colores": 0,
        "modulo_serial": 0,
        "pos_label": "Venta"
    },
    "repuestos": {
        "unidad_base": "unidad",
        "unidad_secundaria": "kit",
        "impuesto_default": 19.0,
        "modulo_citas": 0,
        "modulo_garantias": 1,
        "modulo_vencimientos": 0,
        "modulo_tallas_colores": 0,
        "modulo_serial": 1,
        "pos_label": "Venta"
    }
}

def get_profile(industry: str) -> dict:
    """Devuelve las flags y settings para un nombre de industria específico. Fallback a retail."""
    return PROFILES.get(industry.lower(), PROFILES["retail"])

def list_industries() -> list[str]:
    """Retorna los nombres de todas las industrias soportadas."""
    return list(PROFILES.keys())

def apply_profile(industry: str) -> None:
    """Toma el perfil dictado por `industry` y lo vuelca en la BD."""
    prof = get_profile(industry)
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO industry_config (
                id, industry, unidad_base, unidad_secundaria, impuesto_default,
                modulo_citas, modulo_garantias, modulo_vencimientos,
                modulo_tallas_colores, modulo_serial, pos_label
            ) VALUES (
                1, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?
            )
            ON CONFLICT(id) DO UPDATE SET
                industry=excluded.industry,
                unidad_base=excluded.unidad_base,
                unidad_secundaria=excluded.unidad_secundaria,
                impuesto_default=excluded.impuesto_default,
                modulo_citas=excluded.modulo_citas,
                modulo_garantias=excluded.modulo_garantias,
                modulo_vencimientos=excluded.modulo_vencimientos,
                modulo_tallas_colores=excluded.modulo_tallas_colores,
                modulo_serial=excluded.modulo_serial,
                pos_label=excluded.pos_label
            """, (
                industry.lower(),
                prof["unidad_base"],
                prof["unidad_secundaria"],
                prof["impuesto_default"],
                prof["modulo_citas"],
                prof["modulo_garantias"],
                prof["modulo_vencimientos"],
                prof["modulo_tallas_colores"],
                prof["modulo_serial"],
                prof["pos_label"]
            ))
            conn.commit()
            _LOG.info(f"Perfil de industria aplicado en BD: {industry}")
    except Exception as e:
        _LOG.warning(f"Error en apply_profile para '{industry}': {e}")

def get_current_profile() -> dict:
    """Lee desde BD la configuración local, fallback a 'retail' si tabla está vacía/incompleta."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT industry, unidad_base, unidad_secundaria, impuesto_default,
                   modulo_citas, modulo_garantias, modulo_vencimientos,
                   modulo_tallas_colores, modulo_serial, pos_label
            FROM industry_config WHERE id=1
            """)
            row = cur.fetchone()
            if row:
                return {
                    "industry": row[0],
                    "unidad_base": row[1],
                    "unidad_secundaria": row[2],
                    "impuesto_default": row[3],
                    "modulo_citas": bool(row[4]),
                    "modulo_garantias": bool(row[5]),
                    "modulo_vencimientos": bool(row[6]),
                    "modulo_tallas_colores": bool(row[7]),
                    "modulo_serial": bool(row[8]),
                    "pos_label": row[9]
                }
    except Exception as e:
        _LOG.warning(f"Error en get_current_profile: {e}")
    # Fallback default
    return get_profile("retail")

def module_enabled(module_name: str) -> bool:
    """Consulta ágil si un módulo específico está activo en el tenant local."""
    cfg = get_current_profile()
    return bool(cfg.get(f"modulo_{module_name}", False))
