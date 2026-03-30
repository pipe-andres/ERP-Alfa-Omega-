"""Servicios para realizar transferencias entre bodegas.

Registra movimientos en `warehouse_transfers`, actualiza `warehouse_stock` y
registra entradas/salidas en `kardex_moves` vía repository.
"""
from __future__ import annotations
from typing import Optional, List, Dict
from datetime import datetime

from src.database import repository
from src.database.connection import get_connection
from src.services.audit import log_event


def transfer_stock(product_code: str, from_warehouse: int, to_warehouse: int, quantity: float, user_id: Optional[int] = None, notes: Optional[str] = None) -> int:
    """Transfer quantity from one warehouse to another.

    Returns transfer_id.
    """
    if int(from_warehouse) == int(to_warehouse):
        raise ValueError("Origen y destino deben ser diferentes.")
    # check availability in origin
    available = repository.get_stock_by_warehouse(product_code, int(from_warehouse))
    if available + 1e-9 < float(quantity):
        raise ValueError(f"Stock insuficiente en bodega {from_warehouse}: {available} < {quantity}")

    # debit origin
    repository.adjust_warehouse_stock(product_code, int(from_warehouse), -float(quantity))
    # credit destination
    repository.adjust_warehouse_stock(product_code, int(to_warehouse), float(quantity))

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    transfer_id = repository.record_warehouse_transfer(product_code, int(from_warehouse), int(to_warehouse), float(quantity), fecha, user_id, notes)

    # record kardex moves for transfer out/in
    try:
        repository.record_kardex_move(product_code, 'TRANSFER_OUT', -float(quantity), None, None, repository.get_stock_total(product_code), None, None, fecha, int(from_warehouse), 'TRANSFER', transfer_id)
        repository.record_kardex_move(product_code, 'TRANSFER_IN', float(quantity), None, None, repository.get_stock_total(product_code), None, None, fecha, int(to_warehouse), 'TRANSFER', transfer_id)
    except Exception:
        pass

    log_event(user_id, "WAREHOUSE_TRANSFER", {"id": transfer_id, "product": product_code, "from": from_warehouse, "to": to_warehouse, "qty": quantity})
    return transfer_id


def get_recent_transfers(limit: int = 20) -> List[Dict]:
    """Retorna las transferencias recientes para la tabla Historial."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT t.date, t.product_code, p.nombre, w1.name, w2.name, t.quantity
            FROM warehouse_transfers t
            LEFT JOIN productos p ON p.codigo = t.product_code
            LEFT JOIN warehouses w1 ON w1.id = t.from_wh
            LEFT JOIN warehouses w2 ON w2.id = t.to_wh
            ORDER BY t.date DESC
            LIMIT ?
        ''', (int(limit),))
        
        return [{
            "fecha": r[0], 
            "codigo": r[1], 
            "producto": r[2] or 'N/A', 
            "origen": r[3] or 'N/A', 
            "destino": r[4] or 'N/A', 
            "cantidad": r[5]
        } for r in cur.fetchall()]
