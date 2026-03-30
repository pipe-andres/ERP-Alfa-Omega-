"""Async warehouse transfer service with atomic transactions.

This module provides atomic warehouse transfers: debit origin, credit destination,
and register transfer + kardex moves all in a single transaction.
"""
from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlalchemy import select

from src.database.orm import get_async_session
from src.database.models import (
    Warehouse, WarehouseStock, WarehouseTransfer, KardexMove, Product
)
from src.services.audit import log_event


async def transfer_stock_async(
    product_code: str,
    from_warehouse: int,
    to_warehouse: int,
    quantity: float,
    user_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> int:
    """Transfer stock between warehouses atomically.
    
    Args:
        product_code: product codigo
        from_warehouse: origin warehouse id
        to_warehouse: destination warehouse id
        quantity: amount to transfer
        user_id: user performing the transfer
        notes: optional notes
    
    Returns:
        transfer_id
    
    Raises:
        ValueError: if origin == destination, or insufficient stock
        IntegrityError: if transaction fails
    
    Atomicity: origin debit, destination credit, transfer record, and kardex moves
    all happen in a single transaction or none at all.
    """
    from_wh = int(from_warehouse)
    to_wh = int(to_warehouse)
    qty = float(quantity)
    
    if from_wh == to_wh:
        raise ValueError("Origin and destination warehouses must be different.")
    
    fecha = datetime.now().isoformat()
    
    async with get_async_session() as session:
        async with session.begin():
            # Get origin warehouse stock
            stmt = select(WarehouseStock).where(
                WarehouseStock.product_code == product_code,
                WarehouseStock.warehouse_id == from_wh
            )
            result = await session.execute(stmt)
            origin_stock = result.scalar_one_or_none()
            
            available = float(origin_stock.quantity or 0) if origin_stock else 0.0
            if available + 1e-9 < qty:
                raise ValueError(
                    f"Insufficient stock in warehouse {from_wh}: {available} < {qty}"
                )
            
            # Debit origin
            if origin_stock:
                origin_stock.quantity -= qty
            else:
                # Should not happen if validation above is correct, but be safe
                raise ValueError(f"No stock record for product '{product_code}' in warehouse {from_wh}")
            
            # Credit destination
            stmt = select(WarehouseStock).where(
                WarehouseStock.product_code == product_code,
                WarehouseStock.warehouse_id == to_wh
            )
            result = await session.execute(stmt)
            dest_stock = result.scalar_one_or_none()
            
            if dest_stock:
                dest_stock.quantity += qty
            else:
                # Create new stock record if doesn't exist
                dest_stock = WarehouseStock(
                    product_code=product_code,
                    warehouse_id=to_wh,
                    quantity=qty
                )
                session.add(dest_stock)
            
            # Register transfer
            transfer = WarehouseTransfer(
                product_code=product_code,
                from_wh=from_wh,
                to_wh=to_wh,
                quantity=qty,
                date=fecha,
                user_id=user_id,
                notes=notes
            )
            session.add(transfer)
            await session.flush()
            transfer_id = transfer.id
            
            # Get product for kardex (optional, for balance tracking)
            stmt = select(Product).where(Product.codigo == product_code)
            result = await session.execute(stmt)
            product = result.scalar_one_or_none()
            total_stock = 0.0
            if product:
                total_stock = float(product.cantidad or 0)
            
            # Register kardex moves
            kardex_out = KardexMove(
                product_code=product_code,
                type="TRANSFER_OUT",
                qty=-qty,
                unit_cost=None,
                total_cost=None,
                balance_qty=available - qty,
                balance_cost=None,
                balance_total=None,
                date=fecha,
                warehouse_id=from_wh,
                ref_type="TRANSFER",
                ref_id=transfer_id
            )
            session.add(kardex_out)
            
            kardex_in = KardexMove(
                product_code=product_code,
                type="TRANSFER_IN",
                qty=qty,
                unit_cost=None,
                total_cost=None,
                balance_qty=available + qty,
                balance_cost=None,
                balance_total=None,
                date=fecha,
                warehouse_id=to_wh,
                ref_type="TRANSFER",
                ref_id=transfer_id
            )
            session.add(kardex_in)
    
    log_event(user_id, "WAREHOUSE_TRANSFER_ASYNC", {
        "transfer_id": transfer_id,
        "product": product_code,
        "from_wh": from_wh,
        "to_wh": to_wh,
        "qty": qty
    })
    
    return transfer_id
