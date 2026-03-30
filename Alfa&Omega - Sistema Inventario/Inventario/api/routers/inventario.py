"""
api/routers/inventario.py
=========================
Tarea 16 — Stock actual y kardex vía API REST.
Reutiliza src/services/inventory.py y src/services/kardex.py.
"""
from __future__ import annotations
import logging
from typing import Annotated, Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from api.routers.auth import get_current_user
from src.database.connection import get_connection
from src.services.kardex import get_product_kardex

_LOG = logging.getLogger(__name__)
router = APIRouter(tags=["inventario"])


def require_auth(payload: Annotated[Dict[str, Any], Depends(get_current_user)]) -> Dict[str, Any]:
    """Solo exige JWT válido, sin restricción de rol."""
    return payload


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "/inventario/stock",
    response_model=Dict[str, Any],
    summary="Obtener stock actual",
    description="Retorna el stock actual de todos los productos ordenados por nombre, junto con el valor total acumulado del inventario."
)
async def stock_actual(_: Annotated[Dict, Depends(require_auth)]):
    """Stock actual de todos los productos con valor total del inventario."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT codigo, nombre, categoria, cantidad, precio, avg_cost "
                "FROM productos ORDER BY nombre"
            )
            rows = cur.fetchall()
        total_valor = sum((r[4] or 0) * (r[3] or 0) for r in rows)
        return {
            "total_productos": len(rows),
            "valor_total": round(total_valor, 2),
            "items": [
                {"codigo": r[0], "nombre": r[1], "categoria": r[2],
                 "cantidad": r[3], "precio": r[4], "avg_cost": r[5]}
                for r in rows
            ],
        }
    except Exception as e:
        logging.warning("stock_actual error: %s", e)
        raise HTTPException(status_code=500, detail="Error al obtener stock.")


@router.get(
    "/inventario/bajo-stock",
    response_model=Dict[str, Any],
    summary="Reporte de bajo stock",
    description="Obtiene una lista de productos cuya cantidad disponible en inventario es estrictamente menor a un umbral dado (por defecto 5)."
)
async def bajo_stock(
    _: Annotated[Dict, Depends(require_auth)],
    threshold: int = Query(5, ge=0, description="Umbral mínimo de stock"),
):
    """Productos con cantidad menor al umbral (default: 5)."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT codigo, nombre, categoria, cantidad, precio "
                "FROM productos WHERE cantidad < ? ORDER BY cantidad ASC",
                (threshold,),
            )
            rows = cur.fetchall()
        return {
            "threshold": threshold,
            "count": len(rows),
            "items": [
                {"codigo": r[0], "nombre": r[1], "categoria": r[2],
                 "cantidad": r[3], "precio": r[4]}
                for r in rows
            ],
        }
    except Exception as e:
        logging.warning("bajo_stock error: %s", e)
        raise HTTPException(status_code=500, detail="Error al obtener bajo stock.")


@router.get(
    "/inventario/kardex/{codigo}",
    response_model=Dict[str, Any],
    summary="Consultar kardex de producto",
    description="Obtiene el historial detallado de movimientos (kardex) para un producto específico, con opción de paginación y filtrado por fechas."
)
async def kardex_producto(
    codigo: str,
    _: Annotated[Dict, Depends(require_auth)],
    fecha_desde: Optional[str] = Query(None, description="YYYY-MM-DD"),
    fecha_hasta: Optional[str] = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Movimientos de un producto (kardex). Reutiliza kardex_svc.kardex_rows."""
    try:
        movs = get_product_kardex(codigo)
    except Exception as e:
        logging.warning("kardex_producto(%r) error: %s", codigo, e)
        raise HTTPException(status_code=500, detail="Error al obtener kardex.")
    if not movs:
        raise HTTPException(
            status_code=404,
            detail=f"Producto '{codigo}' sin movimientos o no existe.",
        )
    limited = movs[:limit]
    return {
        "codigo": codigo,
        "total_movimientos": len(movs),
        "limit": limit,
        "movimientos": limited,
    }
