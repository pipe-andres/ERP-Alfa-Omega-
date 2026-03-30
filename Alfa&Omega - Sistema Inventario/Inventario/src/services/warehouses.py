"""Servicios para gestión de bodegas y stock por bodega.

Provee funciones para crear bodegas, asignar stock inicial y consultar stock.
Utiliza `src.database.repository` para operaciones SQL.
"""
from __future__ import annotations
from typing import Optional, List, Dict
from datetime import datetime

from src.database import repository
from src.database.connection import get_connection
from src.services.audit import log_event


def create_warehouse(name: str, location: str = "", user: dict = None) -> int:
    """Create a warehouse and return its id."""
    # ── Guard de plan: límite de sucursales ──────────────────────────────────
    try:
        from src.services.plans import check_plan_limit_local
        current = len(list_warehouses())
        check_plan_limit_local(user or {"plan": "free"}, "branches", current)
    except PermissionError:
        raise  # propagar para que la GUI muestre messagebox
    except Exception as e:
        import logging as _log
        _log.warning("create_warehouse plan check error: %s", e)
    # ── Lógica original intacta ──────────────────────────────────────────────
    wid = repository.create_warehouse(name, location)
    log_event(None, "WAREHOUSE_CREATE", {"id": wid, "name": name})
    return wid


def set_stock(product_code: str, warehouse_id: int, quantity: float, user_id: Optional[int] = None) -> None:
    """Set absolute quantity for a product in a warehouse."""
    repository.set_warehouse_stock(product_code, warehouse_id, float(quantity))
    log_event(user_id, "WAREHOUSE_SET_STOCK", {"product": product_code, "warehouse": warehouse_id, "quantity": quantity})


def adjust_stock(product_code: str, warehouse_id: int, delta: float, user_id: Optional[int] = None) -> None:
    repository.adjust_warehouse_stock(product_code, warehouse_id, float(delta))
    log_event(user_id, "WAREHOUSE_ADJUST_STOCK", {"product": product_code, "warehouse": warehouse_id, "delta": delta})


def get_stock(product_code: str, warehouse_id: Optional[int] = None) -> float:
    if warehouse_id is None:
        return repository.get_stock_total(product_code)
    return repository.get_stock_by_warehouse(product_code, int(warehouse_id))


def list_warehouses() -> List[Dict]:
    # lightweight listing
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, location FROM warehouses ORDER BY name ASC")
        return [{"id": r[0], "name": r[1], "location": r[2]} for r in cur.fetchall()]


def delete_warehouse(warehouse_id: int, user_id: Optional[int] = None) -> None:
    """Elimina una sucursal por su ID."""
    with get_connection() as conn:
        conn.execute("DELETE FROM warehouses WHERE id = ?", (int(warehouse_id),))
        conn.commit()
    log_event(user_id, "WAREHOUSE_DELETE", {"id": warehouse_id})


def get_detailed_stock(warehouse_id: int) -> List[Dict]:
    """Retorna el inventario detallado de una sucursal para la tabla GUI."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT p.codigo, p.nombre, ws.quantity
            FROM warehouse_stock ws
            JOIN productos p ON p.codigo = ws.product_code
            WHERE ws.warehouse_id = ? AND ws.quantity > 0
            ORDER BY p.nombre ASC
        ''', (int(warehouse_id),))
        return [{"codigo": r[0], "producto": r[1], "stock": r[2]} for r in cur.fetchall()]


def get_stock_consolidado() -> List[Dict]:
    """Retorna stock consolidado agrupado por producto para todas las sucursales."""
    with get_connection() as conn:
        cur = conn.cursor()

        # 1. Obtener productos activos
        cur.execute("SELECT codigo, nombre, cantidad FROM productos WHERE activo = 1 ORDER BY nombre ASC")
        productos = cur.fetchall()

        # 2. Obtener distribución en sucursales
        cur.execute('''
            SELECT ws.product_code, w.name, ws.quantity
            FROM warehouse_stock ws
            JOIN warehouses w ON ws.warehouse_id = w.id
            WHERE ws.quantity > 0
        ''')
        stock_rows = cur.fetchall()

        dist_map = {}
        for row in stock_rows:
            code, w_name, qty = row[0], row[1], float(row[2])
            if code not in dist_map:
                dist_map[code] = []
            dist_map[code].append({"sucursal": w_name, "stock": qty})

        result = []
        for p in productos:
            code, name, base_qty = p[0], p[1], float(p[2])
            sucursales = dist_map.get(code, [])

            # Si no hay distribución, se asume la base manual del producto
            if sucursales:
                total_stock = sum(s["stock"] for s in sucursales)
            else:
                total_stock = base_qty

            result.append({
                "codigo": code,
                "nombre": name,
                "stock_total": total_stock,
                "por_sucursal": sucursales
            })

        return result


def get_resumen_sucursales() -> List[Dict]:
    """Retorna resumen estadístico de cada sucursal (total ítems y valoración)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT w.id, w.name, w.location,
                   COUNT(ws.product_code) as total_productos,
                   SUM(ws.quantity * p.precio) as valor_stock
            FROM warehouses w
            LEFT JOIN warehouse_stock ws ON w.id = ws.warehouse_id AND ws.quantity > 0
            LEFT JOIN productos p ON ws.product_code = p.codigo
            GROUP BY w.id, w.name, w.location
            ORDER BY w.name ASC
        ''')
        return [{
            "id": r[0],
            "nombre": r[1],
            "ubicacion": r[2],
            "total_productos": r[3] or 0,
            "valor_stock": float(r[4] or 0.0)
        } for r in cur.fetchall()]
