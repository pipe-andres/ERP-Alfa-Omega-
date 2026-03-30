"""Integration tests for async transaction services.

Tests validate that operations are atomic: all succeed or all rollback on failure.
"""
import pytest
import asyncio
import uuid
from datetime import datetime

from src.database.orm import get_async_session
from src.database.models import Product, Document, StockMovement, KardexMove
from src.services.inventory_async import post_purchase_async, post_sale_async, post_adjustment_async
from src.services.transfers_async import transfer_stock_async
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_post_purchase_atomic_single_item(db_session):
    """Test that a purchase creates document, lines, stock movements, and kardex atomically."""
    # Setup
    prod_code = f"P-{uuid.uuid4().hex[:8]}"
    items = [
        {"codigo": prod_code, "qty": 10, "unit_cost": 100.0, "unit_price": 150.0}
    ]
    
    # Execute
    doc_id, numero = await post_purchase_async(
        numero=None,
        fecha="2025-12-01",
        items=items,
        notas="Test purchase",
        partner_code=None,
        series="C01"
    )
    
    # Verify: document exists
    async with get_async_session() as session:
        stmt = select(Document).where(Document.id == doc_id)
        result = await session.execute(stmt)
        doc = result.scalar_one()
        assert doc.tipo == "PURCHASE"
        assert doc.numero == numero
        
        # Verify: product quantity updated
        stmt = select(Product).where(Product.codigo == prod_code)
        result = await session.execute(stmt)
        prod = result.scalar_one()
        assert prod.cantidad == 10
        assert prod.precio == 100.0
        # Verify: stock movement created
        stmt = select(StockMovement).where(StockMovement.doc_id == doc_id)
        result = await session.execute(stmt)
        movements = result.scalars().all()
        assert len(movements) == 1
        assert movements[0].qty == 10
        assert movements[0].tipo == "PURCHASE"
        
        # Verify: kardex move created
        stmt = select(KardexMove).where(
            KardexMove.product_code == prod_code,
            KardexMove.ref_type == "PURCHASE"
        )
        result = await session.execute(stmt)
        kardex = result.scalars().all()
        assert len(kardex) == 1
        assert kardex[0].qty == 10
        assert kardex[0].type == "IN"


@pytest.mark.asyncio
async def test_post_purchase_multi_item_atomicity(db_session):
    """Test that multi-item purchase is atomic: all items or none."""
    prod_code_1 = f"P-{uuid.uuid4().hex[:8]}"
    prod_code_2 = f"P-{uuid.uuid4().hex[:8]}"
    items = [
        {"codigo": prod_code_1, "qty": 5, "unit_cost": 50.0},
        {"codigo": prod_code_2, "qty": 10, "unit_cost": 100.0},
    ]
    
    doc_id, numero = await post_purchase_async(
        numero="PO-001",
        fecha="2025-12-01",
        items=items,
        notas="Multi-item purchase",
        series="C01"
    )
    
    # Verify both items processed
    async with get_async_session() as session:
        stmt = select(StockMovement).where(StockMovement.doc_id == doc_id)
        result = await session.execute(stmt)
        movements = result.scalars().all()
        assert len(movements) == 2
        
        stmt = select(Product).where(Product.codigo == prod_code_1)
        result = await session.execute(stmt)
        p1 = result.scalar_one()
        assert p1.cantidad == 5
        
        stmt = select(Product).where(Product.codigo == prod_code_2)
        result = await session.execute(stmt)
        p2 = result.scalar_one()
        assert p2.cantidad == 10


@pytest.mark.asyncio
async def test_post_sale_atomic_success(db_session):
    """Test that a sale is atomic: document, lines, stock updates, kardex all succeed together."""
    prod_code = f"S-{uuid.uuid4().hex[:8]}"
    # Setup: create a product with stock
    async with get_async_session() as session:
        async with session.begin():
            prod = Product(codigo=prod_code, nombre="Sale Product", precio=100.0, cantidad=20)
            session.add(prod)
    
    # Execute sale
    items = [
        {"codigo": prod_code, "qty": 5, "unit_price": 150.0}
    ]
    
    doc_id, numero, totals = await post_sale_async(
        numero="V-001",
        fecha="2025-12-01",
        items=items,
        notas="Test sale",
        allow_negative=False
    )
    
    # Verify
    async with get_async_session() as session:
        # Document exists
        stmt = select(Document).where(Document.id == doc_id)
        result = await session.execute(stmt)
        doc = result.scalar_one()
        assert doc.tipo == "SALE"
        
        # Product quantity decreased
        stmt = select(Product).where(Product.codigo == prod_code)
        result = await session.execute(stmt)
        prod = result.scalar_one()
        assert prod.cantidad == 15  # 20 - 5
        
        # Stock movement created
        stmt = select(StockMovement).where(StockMovement.doc_id == doc_id)
        result = await session.execute(stmt)
        movements = result.scalars().all()
        assert len(movements) == 1
        assert movements[0].qty == -5
        assert movements[0].tipo == "SALE"
        
        # Kardex OUT created
        stmt = select(KardexMove).where(
            KardexMove.product_code == prod_code,
            KardexMove.ref_type == "SALE"
        )
        result = await session.execute(stmt)
        kardex = result.scalars().all()
        assert len(kardex) == 1
        assert kardex[0].qty == -5
        assert kardex[0].type == "OUT"


@pytest.mark.asyncio
async def test_post_sale_insufficient_stock_rollback(db_session):
    """Test that sale fails and rolls back if insufficient stock."""
    prod_code = f"S-{uuid.uuid4().hex[:8]}"
    # Setup
    async with get_async_session() as session:
        async with session.begin():
            prod = Product(codigo=prod_code, nombre="Low Stock", precio=100.0, cantidad=3)
            session.add(prod)
    
    # Try to sell more than available
    items = [
        {"codigo": prod_code, "qty": 10, "unit_price": 150.0}
    ]
    
    with pytest.raises(ValueError, match="Insufficient stock"):
        await post_sale_async(
            numero="V-002",
            fecha="2025-12-01",
            items=items,
            allow_negative=False
        )
    
    # Verify: stock unchanged (rollback worked)
    async with get_async_session() as session:
        stmt = select(Product).where(Product.codigo == prod_code)
        result = await session.execute(stmt)
        prod = result.scalar_one()
        assert prod.cantidad == 3  # Still 3, not modified


@pytest.mark.asyncio
async def test_post_adjustment_positive(db_session):
    """Test positive adjustment (add stock) is atomic."""
    prod_code = f"ADJ-{uuid.uuid4().hex[:8]}"
    # Setup
    async with get_async_session() as session:
        async with session.begin():
            prod = Product(codigo=prod_code, nombre="Adj Product", precio=50.0, cantidad=10)
            session.add(prod)
    
    # Execute adjustment
    items = [
        {"codigo": prod_code, "qty": 5, "reason": "Correction"}
    ]
    
    doc_id = await post_adjustment_async(
        fecha="2025-12-01",
        items=items,
        notas="Test adjustment"
    )
    
    # Verify
    async with get_async_session() as session:
        stmt = select(Product).where(Product.codigo == prod_code)
        result = await session.execute(stmt)
        prod = result.scalar_one()
        assert prod.cantidad == 15  # 10 + 5
        
        stmt = select(Document).where(Document.id == doc_id)
        result = await session.execute(stmt)
        doc = result.scalar_one()
        assert doc.tipo == "ADJUST"


@pytest.mark.asyncio
async def test_post_adjustment_negative_insufficient_rollback(db_session):
    """Test negative adjustment fails and rolls back if insufficient stock."""
    prod_code = f"ADJ-{uuid.uuid4().hex[:8]}"
    # Setup
    async with get_async_session() as session:
        async with session.begin():
            prod = Product(codigo=prod_code, nombre="Low Adj", precio=50.0, cantidad=3)
            session.add(prod)
    
    # Try to remove more than available
    items = [
        {"codigo": prod_code, "qty": -10, "reason": "Correction"}
    ]
    
    with pytest.raises(ValueError, match="Insufficient stock"):
        await post_adjustment_async(
            fecha="2025-12-01",
            items=items
        )
    
    # Verify: stock unchanged
    async with get_async_session() as session:
        stmt = select(Product).where(Product.codigo == prod_code)
        result = await session.execute(stmt)
        prod = result.scalar_one()
        assert prod.cantidad == 3  # Still 3


@pytest.mark.asyncio
async def test_transfer_stock_atomic_success(db_session):
    """Test warehouse transfer is atomic: debit, credit, transfer record, kardex all succeed."""
    from src.database.models import Warehouse, WarehouseStock
    
    # Unique warehouse IDs (convert UUID to int)
    wh1_id = int(uuid.uuid4().int % 1000000)
    wh2_id = int(uuid.uuid4().int % 1000000)
    prod_code = f"T-{uuid.uuid4().hex[:8]}"
    wh1_name = f"WH-{uuid.uuid4().hex[:8]}"
    wh2_name = f"WH-{uuid.uuid4().hex[:8]}"
    
    # Setup: create warehouses and stock
    async with get_async_session() as session:
        async with session.begin():
            wh1 = Warehouse(id=wh1_id, name=wh1_name, location="Location A")
            wh2 = Warehouse(id=wh2_id, name=wh2_name, location="Location B")
            prod = Product(codigo=prod_code, nombre="Transfer Product", precio=50.0, cantidad=100)
            
            session.add(wh1)
            session.add(wh2)
            session.add(prod)
            await session.flush()
            
            stock1 = WarehouseStock(product_code=prod_code, warehouse_id=wh1_id, quantity=50)
            stock2 = WarehouseStock(product_code=prod_code, warehouse_id=wh2_id, quantity=20)
            session.add(stock1)
            session.add(stock2)
    
    # Execute transfer
    transfer_id = await transfer_stock_async(
        product_code=prod_code,
        from_warehouse=wh1_id,
        to_warehouse=wh2_id,
        quantity=10
    )
    
    # Verify
    async with get_async_session() as session:
        # Origin debited
        stmt = select(WarehouseStock).where(
            WarehouseStock.product_code == prod_code,
            WarehouseStock.warehouse_id == wh1_id
        )
        result = await session.execute(stmt)
        stock1 = result.scalar_one()
        assert stock1.quantity == 40  # 50 - 10
        
        # Destination credited
        stmt = select(WarehouseStock).where(
            WarehouseStock.product_code == prod_code,
            WarehouseStock.warehouse_id == wh2_id
        )
        result = await session.execute(stmt)
        stock2 = result.scalar_one()
        assert stock2.quantity == 30  # 20 + 10
        
        # Transfer record created
        from src.database.models import WarehouseTransfer
        stmt = select(WarehouseTransfer).where(WarehouseTransfer.id == transfer_id)
        result = await session.execute(stmt)
        transfer = result.scalar_one()
        assert transfer.quantity == 10
        
        # Kardex moves created
        stmt = select(KardexMove).where(
            KardexMove.product_code == prod_code,
            KardexMove.ref_type == "TRANSFER"
        )
        result = await session.execute(stmt)
        kardex = result.scalars().all()
        assert len(kardex) == 2  # IN and OUT


@pytest.mark.asyncio
async def test_transfer_insufficient_stock_rollback(db_session):
    """Test transfer fails and rolls back if insufficient stock in origin."""
    from src.database.models import Warehouse, WarehouseStock
    
    # Unique warehouse IDs (convert UUID to int)
    wh3_id = int(uuid.uuid4().int % 1000000)
    wh4_id = int(uuid.uuid4().int % 1000000)
    prod_code = f"T-{uuid.uuid4().hex[:8]}"
    wh3_name = f"WH-{uuid.uuid4().hex[:8]}"
    wh4_name = f"WH-{uuid.uuid4().hex[:8]}"
    
    # Setup
    async with get_async_session() as session:
        async with session.begin():
            wh1 = Warehouse(id=wh3_id, name=wh3_name)
            wh2 = Warehouse(id=wh4_id, name=wh4_name)
            prod = Product(codigo=prod_code, nombre="Low Stock Transfer", precio=50.0, cantidad=5)
            
            session.add(wh1)
            session.add(wh2)
            session.add(prod)
            await session.flush()
            
            stock = WarehouseStock(product_code=prod_code, warehouse_id=wh3_id, quantity=3)
            session.add(stock)
    
    # Try to transfer more than available
    with pytest.raises(ValueError, match="Insufficient stock"):
        await transfer_stock_async(
            product_code=prod_code,
            from_warehouse=wh3_id,
            to_warehouse=wh4_id,
            quantity=10
        )
    
    # Verify: stocks unchanged
    async with get_async_session() as session:
        stmt = select(WarehouseStock).where(
            WarehouseStock.product_code == prod_code,
            WarehouseStock.warehouse_id == wh3_id
        )
        result = await session.execute(stmt)
        stock = result.scalar_one()
        assert stock.quantity == 3  # Unchanged

