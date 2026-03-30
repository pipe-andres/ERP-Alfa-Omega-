"""
api/routers/ventas.py
=====================
Tarea 16 — Consulta de ventas vía API REST.
Reutiliza src/services/reports.py y query directa a documents/document_lines.
"""
from __future__ import annotations
import logging
from datetime import date, timedelta
from typing import Annotated, Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from api.routers.auth import get_current_user
from src.database.connection import get_connection
from src.services import reports

_LOG = logging.getLogger(__name__)
router = APIRouter(tags=["ventas"])


def require_auth(payload: Annotated[Dict[str, Any], Depends(get_current_user)]) -> Dict[str, Any]:
    """Solo exige JWT válido, sin restricción de rol."""
    return payload


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "/ventas/resumen",
    response_model=Dict[str, Any],
    summary="Obtener resumen de ventas",
    description="Retorna los KPIs principales del día actual, incluyendo total de ventas del día, ventas del mes en curso y el ticket promedio."
)
async def ventas_resumen(_: Annotated[Dict, Depends(require_auth)]):
    """KPIs del día: ventas_hoy, ventas_mes, ticket_promedio."""
    try:
        return reports.get_kpis_hoy()
    except Exception as e:
        logging.warning("ventas_resumen error: %s", e)
        raise HTTPException(status_code=500, detail="Error al obtener resumen.")


@router.get(
    "/ventas/",
    response_model=Dict[str, Any],
    summary="Listar ventas",
    description="Obtiene una lista de ventas (documentos de tipo SALE) con opciones de paginación y filtro por rango de fechas opcional."
)
async def list_ventas(
    _: Annotated[Dict, Depends(require_auth)],
    fecha_desde: Optional[str] = Query(None, description="YYYY-MM-DD"),
    fecha_hasta: Optional[str] = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=500),
):
    """Lista ventas (tipo=SALE) con filtro de fechas opcional."""
    desde = fecha_desde or str(date.today() - timedelta(days=30))
    hasta = fecha_hasta or str(date.today())
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT d.id, d.numero, d.fecha, d.notas,
                       d.amount_paid, d.payment_method,
                       p.name AS partner
                FROM documents d
                LEFT JOIN partners p ON p.id = d.partner_id
                WHERE d.tipo = 'SALE'
                  AND d.fecha >= ? AND d.fecha <= ?
                ORDER BY d.fecha DESC, d.id DESC
                LIMIT ?
                """,
                (desde, hasta, limit),
            )
            rows = cur.fetchall()
        return {
            "fecha_desde": desde,
            "fecha_hasta": hasta,
            "count": len(rows),
            "items": [
                {"id": r[0], "numero": r[1], "fecha": r[2],
                 "notas": r[3], "amount_paid": r[4],
                 "payment_method": r[5], "partner": r[6]}
                for r in rows
            ],
        }
    except Exception as e:
        logging.warning("list_ventas error: %s", e)
        raise HTTPException(status_code=500, detail="Error al listar ventas.")


@router.get(
    "/ventas/{doc_id}",
    response_model=Dict[str, Any],
    summary="Obtener detalle de venta",
    description="Retorna los detalles completos de una venta específica mediante su ID interno de documento, incluyendo cada una de las líneas asociadas a la venta."
)
async def get_venta(
    doc_id: int,
    _: Annotated[Dict, Depends(require_auth)],
):
    """Detalle de una venta con sus líneas."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT d.id, d.numero, d.fecha, d.notas,
                       d.amount_paid, d.payment_method, p.name
                FROM documents d
                LEFT JOIN partners p ON p.id = d.partner_id
                WHERE d.id = ? AND d.tipo = 'SALE'
                """,
                (doc_id,),
            )
            doc = cur.fetchone()
            if not doc:
                raise HTTPException(status_code=404, detail=f"Venta {doc_id} no encontrada.")
            cur.execute(
                "SELECT codigo, qty, unit_price, reason FROM document_lines WHERE doc_id = ?",
                (doc_id,),
            )
            lines = cur.fetchall()
        return {
            "id": doc[0], "numero": doc[1], "fecha": doc[2],
            "notas": doc[3], "amount_paid": doc[4],
            "payment_method": doc[5], "partner": doc[6],
            "lineas": [
                {"codigo": l[0], "qty": l[1], "unit_price": l[2], "reason": l[3]}
                for l in lines
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.warning("get_venta(%s) error: %s", doc_id, e)
        raise HTTPException(status_code=500, detail="Error al obtener venta.")
