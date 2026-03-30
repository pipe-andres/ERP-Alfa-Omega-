"""
src/services/finanzas.py
========================
Tarea 14 — Módulo Finanzas Básicas: CxC, CxP, Flujo de Caja.

Reglas:
- TODA la lógica aquí. Cero queries en GUI.
- with get_connection() as conn SIEMPRE.
- except Exception as e: logging.warning() — nunca bare except.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from src.database.connection import get_connection

_LOG = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def _row_to_dict(cur, row) -> Dict[str, Any]:
    """Convierte una row a dict usando description del cursor."""
    try:
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    except Exception:
        return {}


def _hoy() -> str:
    return date.today().isoformat()


# ─────────────────────────────────────────────────────────────────────
# CxC — Cuentas por Cobrar
# ─────────────────────────────────────────────────────────────────────

def get_cxc(estado: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista CxC. Filtra por estado si se provee ('PENDIENTE','PAGADO','VENCIDO')."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            if estado:
                cur.execute("""
                    SELECT c.*, p.name AS partner_name
                    FROM cuentas_cobrar c
                    LEFT JOIN partners p ON p.id = c.partner_id
                    WHERE c.estado = ?
                    ORDER BY c.fecha_vencimiento ASC
                """, (estado,))
            else:
                cur.execute("""
                    SELECT c.*, p.name AS partner_name
                    FROM cuentas_cobrar c
                    LEFT JOIN partners p ON p.id = c.partner_id
                    ORDER BY c.fecha_vencimiento ASC
                """)
            rows = cur.fetchall()
            return [_row_to_dict(cur, r) for r in rows]
    except Exception as e:
        logging.warning("get_cxc error: %s", e)
        raise


def registrar_cobro(cxc_id: int, monto: float) -> None:
    """
    Reduce el saldo de una CxC en `monto`.
    Cambia estado a 'PAGADO' si saldo llega a 0 o menos.
    """
    if monto <= 0:
        raise ValueError("El monto del cobro debe ser mayor a cero.")
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT saldo, estado FROM cuentas_cobrar WHERE id = ?", (cxc_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"CxC {cxc_id} no encontrada.")
            saldo_actual, estado = row[0], row[1]
            if estado == "PAGADO":
                raise ValueError("Esta CxC ya está completamente pagada.")
            nuevo_saldo = max(0.0, round(saldo_actual - monto, 4))
            nuevo_estado = "PAGADO" if nuevo_saldo <= 0 else estado
            cur.execute(
                "UPDATE cuentas_cobrar SET saldo = ?, estado = ? WHERE id = ?",
                (nuevo_saldo, nuevo_estado, cxc_id),
            )
            conn.commit()
            _LOG.info("Cobro registrado: cxc_id=%s monto=%.2f nuevo_saldo=%.2f", cxc_id, monto, nuevo_saldo)
    except Exception as e:
        logging.warning("registrar_cobro(%s) error: %s", cxc_id, e)
        raise


def get_resumen_cxc() -> Dict[str, Any]:
    """
    Retorna:
      total      — suma de saldos pendientes
      vencido    — saldo con fecha_vencimiento < hoy
      por_vencer — saldo con fecha_vencimiento >= hoy o NULL
      count      — número de CxC pendientes
    """
    try:
        hoy = _hoy()
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    COALESCE(SUM(saldo), 0)                                                              AS total,
                    COALESCE(SUM(CASE WHEN fecha_vencimiento < ?          THEN saldo ELSE 0 END), 0)     AS vencido,
                    COALESCE(SUM(CASE WHEN fecha_vencimiento >= ? OR fecha_vencimiento IS NULL
                                      THEN saldo ELSE 0 END), 0)                                         AS por_vencer,
                    COUNT(*)                                                                              AS cnt
                FROM cuentas_cobrar
                WHERE estado = 'PENDIENTE'
            """, (hoy, hoy))
            row = cur.fetchone()
            return {
                "total":      round(row[0], 2),
                "vencido":    round(row[1], 2),
                "por_vencer": round(row[2], 2),
                "count":      row[3],
            }
    except Exception as e:
        logging.warning("get_resumen_cxc error: %s", e)
        raise


# ─────────────────────────────────────────────────────────────────────
# CxP — Cuentas por Pagar
# ─────────────────────────────────────────────────────────────────────

def get_cxp(estado: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista CxP. Filtra por estado si se provee."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            if estado:
                cur.execute("""
                    SELECT c.*, p.name AS partner_name
                    FROM cuentas_pagar c
                    LEFT JOIN partners p ON p.id = c.partner_id
                    WHERE c.estado = ?
                    ORDER BY c.fecha_vencimiento ASC
                """, (estado,))
            else:
                cur.execute("""
                    SELECT c.*, p.name AS partner_name
                    FROM cuentas_pagar c
                    LEFT JOIN partners p ON p.id = c.partner_id
                    ORDER BY c.fecha_vencimiento ASC
                """)
            rows = cur.fetchall()
            return [_row_to_dict(cur, r) for r in rows]
    except Exception as e:
        logging.warning("get_cxp error: %s", e)
        raise


def registrar_pago(cxp_id: int, monto: float) -> None:
    """Reduce el saldo de una CxP. Cambia estado a 'PAGADO' si saldo = 0."""
    if monto <= 0:
        raise ValueError("El monto del pago debe ser mayor a cero.")
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT saldo, estado FROM cuentas_pagar WHERE id = ?", (cxp_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"CxP {cxp_id} no encontrada.")
            saldo_actual, estado = row[0], row[1]
            if estado == "PAGADO":
                raise ValueError("Esta CxP ya está completamente pagada.")
            nuevo_saldo = max(0.0, round(saldo_actual - monto, 4))
            nuevo_estado = "PAGADO" if nuevo_saldo <= 0 else estado
            cur.execute(
                "UPDATE cuentas_pagar SET saldo = ?, estado = ? WHERE id = ?",
                (nuevo_saldo, nuevo_estado, cxp_id),
            )
            conn.commit()
            _LOG.info("Pago registrado: cxp_id=%s monto=%.2f nuevo_saldo=%.2f", cxp_id, monto, nuevo_saldo)
    except Exception as e:
        logging.warning("registrar_pago(%s) error: %s", cxp_id, e)
        raise


def get_resumen_cxp() -> Dict[str, Any]:
    """Resumen CxP: total, vencido, por_vencer, count."""
    try:
        hoy = _hoy()
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    COALESCE(SUM(saldo), 0)                                                              AS total,
                    COALESCE(SUM(CASE WHEN fecha_vencimiento < ?          THEN saldo ELSE 0 END), 0)     AS vencido,
                    COALESCE(SUM(CASE WHEN fecha_vencimiento >= ? OR fecha_vencimiento IS NULL
                                      THEN saldo ELSE 0 END), 0)                                         AS por_vencer,
                    COUNT(*)                                                                              AS cnt
                FROM cuentas_pagar
                WHERE estado = 'PENDIENTE'
            """, (hoy, hoy))
            row = cur.fetchone()
            return {
                "total":      round(row[0], 2),
                "vencido":    round(row[1], 2),
                "por_vencer": round(row[2], 2),
                "count":      row[3],
            }
    except Exception as e:
        logging.warning("get_resumen_cxp error: %s", e)
        raise


# ─────────────────────────────────────────────────────────────────────
# Flujo de Caja
# ─────────────────────────────────────────────────────────────────────

def get_flujo_caja(dias: int = 30) -> List[Dict[str, Any]]:
    """
    Flujo de caja de los últimos `dias` días.
    ingresos = sum ventas  (SALE)     del día por documento_lines
    egresos  = sum compras (PURCHASE) del día por document_lines
    saldo_dia = ingresos - egresos
    """
    try:
        fecha_inicio = (date.today() - timedelta(days=dias)).isoformat()
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    substr(d.fecha, 1, 10)                                                          AS dia,
                    COALESCE(SUM(CASE WHEN d.tipo='SALE'     THEN dl.qty * dl.unit_price ELSE 0 END), 0) AS ingresos,
                    COALESCE(SUM(CASE WHEN d.tipo='PURCHASE' THEN dl.qty * dl.unit_cost  ELSE 0 END), 0) AS egresos
                FROM documents d
                JOIN document_lines dl ON dl.doc_id = d.id
                WHERE substr(d.fecha, 1, 10) >= ?
                  AND d.tipo IN ('SALE', 'PURCHASE')
                GROUP BY dia
                ORDER BY dia ASC
            """, (fecha_inicio,))
            resultado = []
            for row in cur.fetchall():
                ing = round(row[1], 2)
                egr = round(row[2], 2)
                resultado.append({
                    "fecha":     row[0],
                    "ingresos":  ing,
                    "egresos":   egr,
                    "saldo_dia": round(ing - egr, 2),
                })
            return resultado
    except Exception as e:
        logging.warning("get_flujo_caja(dias=%s) error: %s", dias, e)
        raise
