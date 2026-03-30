"""Async inventory services with atomic transactions.

This module provides async versions of inventory operations (purchases, sales, adjustments)
that guarantee atomicity: all operations happen in a single transaction or none at all.

Functions in this module use `get_async_session()` and ensure rollback on any failure.
"""
from __future__ import annotations
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from src.database.orm import get_async_session
from src.database.models import (
    Product, Document, DocumentLine, StockMovement, 
    Partner, KardexMove
)
from src.services.audit import log_event


D = Decimal
FMT2 = lambda x: float(D(str(x)).quantize(D("0.01"), rounding=ROUND_HALF_UP))


async def post_purchase_async(
    numero: Optional[str],
    fecha: Optional[str],
    items: List[Dict],
    notas: Optional[str] = None,
    partner_code: Optional[str] = None,
    series: Optional[str] = "C01",
    user_id: Optional[int] = None,
) -> tuple[int, str]:
    """Register a purchase atomically.
    
    Args:
        numero: document number (auto-generated if None)
        fecha: document date (now if None)
        items: list of {"codigo", "qty", "unit_cost", "unit_price"(optional)}
        notas: notes
        partner_code: supplier code (optional)
        series: series code
        user_id: user performing the operation
    
    Returns:
        (doc_id, numero_final)
    
    Raises:
        ValueError: if partner not found or product invalid
        IntegrityError: if transaction fails (e.g., FK violation)
    
    Atomicity: all operations (document, lines, stock updates, kardex) 
    commit together or rollback on any error.
    """
    # Get or auto-generate document number
    numero_final = (numero or "").strip()
    if not numero_final:
        # TODO: integrate with get_next_number from documents service
        numero_final = f"{series}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    partner_id = None
    fecha_ok = fecha or datetime.now().isoformat()
    
    async with get_async_session() as session:
        async with session.begin():
            # Get partner if specified
            if partner_code:
                stmt = select(Partner).where(Partner.code == partner_code)
                result = await session.execute(stmt)
                partner = result.scalar_one_or_none()
                if not partner:
                    raise ValueError(f"Partner '{partner_code}' not found.")
                partner_id = partner.id
            
            # Create document
            doc = Document(
                tipo="PURCHASE",
                numero=numero_final,
                fecha=fecha_ok,
                notas=notas,
                partner_id=partner_id
            )
            session.add(doc)
            await session.flush()  # Get doc.id without committing
            doc_id = doc.id
            
            # Process each line item
            for item in items:
                codigo = item["codigo"]
                qty = float(item["qty"])
                unit_cost = float(item.get("unit_cost") or 0.0)
                unit_price = item.get("unit_price")
                
                # Get or create product
                stmt = select(Product).where(Product.codigo == codigo)
                result = await session.execute(stmt)
                prod = result.scalar_one_or_none()
                
                if not prod:
                    # Auto-create if missing
                    prod = Product(
                        codigo=codigo,
                        nombre=codigo,
                        categoria="",
                        precio=unit_cost,
                        cantidad=int(qty),
                        avg_cost=unit_cost
                    )
                    session.add(prod)
                    await session.flush()
                else:
                    # Update product quantity and cost
                    old_qty = float(prod.cantidad or 0)
                    old_cost = float(prod.precio or 0)
                    new_qty = old_qty + qty
                    new_cost = (old_qty * old_cost + qty * unit_cost) / new_qty if new_qty > 0 else unit_cost
                    prod.cantidad = int(new_qty)
                    prod.precio = new_cost
                    prod.avg_cost = new_cost
                
                # Add document line
                line = DocumentLine(
                    doc_id=doc_id,
                    codigo=codigo,
                    qty=qty,
                    unit_cost=unit_cost,
                    unit_price=unit_price,
                    reason=""
                )
                session.add(line)
                
                # Add stock movement
                movement = StockMovement(
                    doc_id=doc_id,
                    codigo=codigo,
                    qty=qty,
                    unit_cost=unit_cost,
                    unit_price=unit_price,
                    tipo="PURCHASE",
                    reason="",
                    created_at=fecha_ok
                )
                session.add(movement)
                
                # Add kardex move
                balance_qty = float(prod.cantidad or 0)
                kardex = KardexMove(
                    product_code=codigo,
                    type="IN",
                    qty=qty,
                    unit_cost=unit_cost,
                    total_cost=unit_cost * qty,
                    balance_qty=balance_qty,
                    balance_cost=None,
                    balance_total=None,
                    date=fecha_ok,
                    warehouse_id=None,
                    ref_type="PURCHASE",
                    ref_id=doc_id
                )
                session.add(kardex)
            
            # Commit happens automatically at end of `async with session.begin():`
    
    log_event(user_id, "DOC_PURCHASE_ASYNC", {"doc_id": doc_id, "numero": numero_final})
    return doc_id, numero_final


async def post_sale_async(
    numero: Optional[str],
    fecha: Optional[str],
    items: List[Dict],
    notas: Optional[str] = None,
    partner_code: Optional[str] = None,
    series: Optional[str] = "V01",
    allow_negative: bool = False,
    user_id: Optional[int] = None,
) -> tuple[int, str, dict]:
    """Register a sale atomically.
    
    Args:
        numero: document number (auto-generated if None)
        fecha: document date (now if None)
        items: list of {"codigo", "qty", "unit_price"}
        notas: notes
        partner_code: customer code (optional)
        series: series code
        allow_negative: if False, raises on insufficient stock
        user_id: user performing the operation
    
    Returns:
        (doc_id, numero_final, totals_dict)
    
    Raises:
        ValueError: if product not found, insufficient stock, or partner not found
        IntegrityError: if transaction fails
    
    Atomicity: all operations commit together or rollback on any error.
    """
    numero_final = (numero or "").strip()
    if not numero_final:
        numero_final = f"{series}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    partner_id = None
    fecha_ok = fecha or datetime.now().isoformat()
    
    # Calculate totals (will be refined per settings in future)
    tax_rate = 0.0  # TODO: read from settings
    tax_included = False
    subtotal = D("0.00")
    
    for item in items:
        qty = D(str(item.get("qty") or 0))
        price = D(str(item.get("unit_price") or 0))
        subtotal += qty * price
    
    neto = subtotal
    tax = D("0.00")
    total = subtotal
    
    async with get_async_session() as session:
        async with session.begin():
            # Get partner if specified
            if partner_code:
                stmt = select(Partner).where(Partner.code == partner_code)
                result = await session.execute(stmt)
                partner = result.scalar_one_or_none()
                if not partner:
                    raise ValueError(f"Partner '{partner_code}' not found.")
                partner_id = partner.id
            
            # Create document
            doc = Document(
                tipo="SALE",
                numero=numero_final,
                fecha=fecha_ok,
                notas=notas,
                partner_id=partner_id
            )
            session.add(doc)
            await session.flush()
            doc_id = doc.id
            
            # Process each line item
            for item in items:
                codigo = item["codigo"]
                qty = float(item["qty"])
                unit_price = float(item.get("unit_price") or 0.0)
                
                # Get product (must exist)
                stmt = select(Product).where(Product.codigo == codigo)
                result = await session.execute(stmt)
                prod = result.scalar_one_or_none()
                
                if not prod:
                    raise ValueError(f"Product '{codigo}' not found.")
                
                # Check stock
                old_qty = float(prod.cantidad or 0)
                new_qty = old_qty - qty
                
                if new_qty < -1e-6 and not allow_negative:
                    raise ValueError(
                        f"Insufficient stock for '{codigo}'. Available: {old_qty}, Required: {qty}"
                    )
                
                # Update product quantity (use average cost for valuation)
                avg_cost = float(prod.precio or 0)
                prod.cantidad = int(new_qty)
                
                # Add document line
                line = DocumentLine(
                    doc_id=doc_id,
                    codigo=codigo,
                    qty=qty,
                    unit_cost=None,
                    unit_price=unit_price,
                    reason=""
                )
                session.add(line)
                
                # Add stock movement
                movement = StockMovement(
                    doc_id=doc_id,
                    codigo=codigo,
                    qty=-qty,
                    unit_cost=avg_cost,
                    unit_price=unit_price,
                    tipo="SALE",
                    reason="",
                    created_at=fecha_ok
                )
                session.add(movement)
                
                # Add kardex move
                kardex = KardexMove(
                    product_code=codigo,
                    type="OUT",
                    qty=-qty,
                    unit_cost=avg_cost,
                    total_cost=avg_cost * qty,
                    balance_qty=float(new_qty),
                    balance_cost=None,
                    balance_total=None,
                    date=fecha_ok,
                    warehouse_id=None,
                    ref_type="SALE",
                    ref_id=doc_id
                )
                session.add(kardex)
    
    log_event(user_id, "DOC_SALE_ASYNC", {"doc_id": doc_id, "numero": numero_final})
    
    return doc_id, numero_final, {
        "subtotal": float(FMT2(subtotal)),
        "neto": float(FMT2(neto)),
        "impuesto": float(FMT2(tax)),
        "total": float(FMT2(total)),
        "tax_included": tax_included,
        "tax_rate": tax_rate,
    }


async def post_adjustment_async(
    fecha: Optional[str],
    items: List[Dict],
    notas: Optional[str] = None,
    user_id: Optional[int] = None,
) -> int:
    """Register a stock adjustment atomically.
    
    Args:
        fecha: adjustment date (now if None)
        items: list of {"codigo", "qty", "reason", "unit_cost"(optional)}
        notas: notes
        user_id: user performing the operation
    
    Returns:
        doc_id
    
    Raises:
        ValueError: if product not found or insufficient stock on negative adjustments
        IntegrityError: if transaction fails
    
    Atomicity: all operations commit together or rollback on any error.
    """
    fecha_ok = fecha or datetime.now().isoformat()
    
    async with get_async_session() as session:
        async with session.begin():
            # Create adjustment document
            doc = Document(
                tipo="ADJUST",
                numero=None,
                fecha=fecha_ok,
                notas=notas,
                partner_id=None
            )
            session.add(doc)
            await session.flush()
            doc_id = doc.id
            
            # Process each adjustment item
            for item in items:
                codigo = item["codigo"]
                qty = float(item["qty"])
                reason = (item.get("reason") or "").strip()
                unit_cost_in = item.get("unit_cost")
                
                # Get product (must exist)
                stmt = select(Product).where(Product.codigo == codigo)
                result = await session.execute(stmt)
                prod = result.scalar_one_or_none()
                
                if not prod:
                    raise ValueError(f"Product '{codigo}' not found.")
                
                old_qty = float(prod.cantidad or 0)
                avg_cost = float(prod.precio or 0)
                
                # Add document line
                line = DocumentLine(
                    doc_id=doc_id,
                    codigo=codigo,
                    qty=qty,
                    unit_cost=unit_cost_in,
                    unit_price=None,
                    reason=reason
                )
                session.add(line)
                
                if qty >= 0:
                    # Positive adjustment (add stock)
                    if unit_cost_in is None:
                        unit_cost_in = avg_cost
                    else:
                        unit_cost_in = float(unit_cost_in)
                    
                    new_qty = old_qty + qty
                    new_cost = (old_qty * avg_cost + qty * unit_cost_in) / new_qty if new_qty > 0 else unit_cost_in
                    
                    prod.cantidad = int(new_qty)
                    prod.precio = new_cost
                    prod.avg_cost = new_cost
                    
                    movement = StockMovement(
                        doc_id=doc_id,
                        codigo=codigo,
                        qty=qty,
                        unit_cost=unit_cost_in,
                        unit_price=None,
                        tipo="ADJUST+",
                        reason=reason,
                        created_at=fecha_ok
                    )
                    session.add(movement)
                else:
                    # Negative adjustment (remove stock)
                    new_qty = old_qty + qty
                    
                    if new_qty < -1e-6:
                        raise ValueError(
                            f"Insufficient stock to adjust '{codigo}'. Available: {old_qty}, Removing: {-qty}"
                        )
                    
                    prod.cantidad = int(new_qty)
                    
                    movement = StockMovement(
                        doc_id=doc_id,
                        codigo=codigo,
                        qty=qty,
                        unit_cost=avg_cost,
                        unit_price=None,
                        tipo="ADJUST-",
                        reason=reason,
                        created_at=fecha_ok
                    )
                    session.add(movement)
    
    log_event(user_id, "DOC_ADJUST_ASYNC", {"doc_id": doc_id, "items": len(items)})
    return doc_id
