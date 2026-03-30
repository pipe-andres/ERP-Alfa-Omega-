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


def create_warehouse(name: str, location: str = "") -> int:
    """Create a warehouse and return its id."""
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
