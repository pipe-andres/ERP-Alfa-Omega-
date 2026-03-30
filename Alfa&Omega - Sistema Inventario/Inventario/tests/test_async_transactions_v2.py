"""Integration tests for async transaction services - Version 2.

Tests validate that operations are atomic: all succeed or all rollback on failure.
Using UUID-based IDs to avoid conflicts between tests.
"""
import pytest
import uuid
from datetime import datetime

from src.database.orm import get_async_session
from src.database.models import (
    Product, Document, StockMovement, KardexMove,
    Warehouse, WarehouseStock, WarehouseTransfer
)
from src.services.inventory_async import post_purchase_async, post_sale_async, post_adjustment_async
from src.services.transfers_async import transfer_stock_async
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_post_purchase_single_item(db_session):
    """Test purchase creates document, lines, and stock updates atomically."""
    prod_code = f"P-{uuid.uuid4().hex[:8]}"
    items = [{"codigo": prod_code, "qty": 10, "unit_cost": 100.0}]
    
    doc_id, numero = await post_purchase_async(
        numero=None, fecha="2025-12-01", items=items,
        notas="Test", series="C01"
    )
    
    async with get_async_session() as session:
        stmt = select(Document).where(Document.id == doc_id)
        doc = (await session.execute(stmt)).scalar_one()
        assert doc.tipo == "PURCHASE"
        
        stmt = select(Product).where(Product.codigo == prod_code)
        prod = (await session.execute(stmt)).scalar_one()
        assert prod.cantidad == 10


@pytest.mark.asyncio
async def test_post_sale_success(db_session):
    """Test sale reduces stock atomically."""
    prod_code = f"S-{uuid.uuid4().hex[:8]}"
    
    # Create product with stock
    async with get_async_session() as session:
        async with session.begin():
            prod = Product(codigo=prod_code, nombre="Test", precio=100.0, cantidad=20)
            session.add(prod)
    
    # Execute sale
    items = [{"codigo": prod_code, "qty": 5, "unit_price": 150.0}]
    doc_id, numero, totals = await post_sale_async(
        numero="V-001", fecha="2025-12-01", items=items, allow_negative=False
    )
    
    # Verify stock decreased
    async with get_async_session() as session:
        stmt = select(Product).where(Product.codigo == prod_code)
        prod = (await session.execute(stmt)).scalar_one()
        assert prod.cantidad == 15  # 20 - 5


@pytest.mark.asyncio
async def test_post_sale_insufficient_stock_rollback(db_session):
    """Test sale fails and rolls back on insufficient stock."""
    prod_code = f"S-{uuid.uuid4().hex[:8]}"
    
    # Create product with low stock
    async with get_async_session() as session:
        async with session.begin():
            prod = Product(codigo=prod_code, nombre="Test", precio=100.0, cantidad=3)
            session.add(prod)
    
    # Try to sell more than available
    items = [{"codigo": prod_code, "qty": 10, "unit_price": 150.0}]
    
    with pytest.raises(ValueError, match="Insufficient stock"):
        await post_sale_async(
            numero="V-002", fecha="2025-12-01", items=items, allow_negative=False
        )
    
    # Verify stock unchanged (rollback worked)
    async with get_async_session() as session:
        stmt = select(Product).where(Product.codigo == prod_code)
        prod = (await session.execute(stmt)).scalar_one()
        assert prod.cantidad == 3  # Unchanged


@pytest.mark.asyncio
async def test_post_adjustment_positive(db_session):
    """Test positive adjustment increases stock atomically."""
    prod_code = f"ADJ-{uuid.uuid4().hex[:8]}"
    
    # Create product
    async with get_async_session() as session:
        async with session.begin():
            prod = Product(codigo=prod_code, nombre="Test", precio=50.0, cantidad=10)
            session.add(prod)
    
    # Execute adjustment
    items = [{"codigo": prod_code, "qty": 5, "reason": "Correction"}]
    doc_id = await post_adjustment_async(
        fecha="2025-12-01", items=items, notas="Test"
    )
    
    # Verify stock increased
    async with get_async_session() as session:
        stmt = select(Product).where(Product.codigo == prod_code)
        prod = (await session.execute(stmt)).scalar_one()
        assert prod.cantidad == 15  # 10 + 5


@pytest.mark.asyncio
async def test_post_adjustment_insufficient_rollback(db_session):
    """Test negative adjustment fails and rolls back on insufficient stock."""
    prod_code = f"ADJ-{uuid.uuid4().hex[:8]}"
    
    # Create product with low stock
    async with get_async_session() as session:
        async with session.begin():
            prod = Product(codigo=prod_code, nombre="Test", precio=50.0, cantidad=3)
            session.add(prod)
    
    # Try to remove more than available
    items = [{"codigo": prod_code, "qty": -10, "reason": "Correction"}]
    
    with pytest.raises(ValueError, match="Insufficient stock"):
        await post_adjustment_async(fecha="2025-12-01", items=items)
    
    # Verify stock unchanged
    async with get_async_session() as session:
        stmt = select(Product).where(Product.codigo == prod_code)
        prod = (await session.execute(stmt)).scalar_one()
        assert prod.cantidad == 3


@pytest.mark.asyncio
async def test_transfer_stock_success(db_session):
    """Test warehouse transfer is atomic."""
    # Unique warehouse IDs (convert UUID to int)
    wh1_id = int(uuid.uuid4().int % 1000000)
    wh2_id = int(uuid.uuid4().int % 1000000)
    prod_code = f"T-{uuid.uuid4().hex[:8]}"
    wh1_name = f"WH-{uuid.uuid4().hex[:8]}"
    wh2_name = f"WH-{uuid.uuid4().hex[:8]}"
    
    # Create warehouses and stock
    async with get_async_session() as session:
        async with session.begin():
            wh1 = Warehouse(id=wh1_id, name=wh1_name, location="Loc A")
            wh2 = Warehouse(id=wh2_id, name=wh2_name, location="Loc B")
            prod = Product(codigo=prod_code, nombre="Test", precio=50.0, cantidad=100)
            
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
    
    # Verify both warehouses updated atomically
    async with get_async_session() as session:
        stmt = select(WarehouseStock).where(
            WarehouseStock.product_code == prod_code,
            WarehouseStock.warehouse_id == wh1_id
        )
        stock1 = (await session.execute(stmt)).scalar_one()
        assert stock1.quantity == 40  # 50 - 10
        
        stmt = select(WarehouseStock).where(
            WarehouseStock.product_code == prod_code,
            WarehouseStock.warehouse_id == wh2_id
        )
        stock2 = (await session.execute(stmt)).scalar_one()
        assert stock2.quantity == 30  # 20 + 10


@pytest.mark.asyncio
async def test_transfer_insufficient_rollback(db_session):
    """Test transfer fails and rolls back on insufficient stock."""
    # Unique warehouse IDs (convert UUID to int)
    wh3_id = int(uuid.uuid4().int % 1000000)
    wh4_id = int(uuid.uuid4().int % 1000000)
    prod_code = f"T-{uuid.uuid4().hex[:8]}"
    wh3_name = f"WH-{uuid.uuid4().hex[:8]}"
    wh4_name = f"WH-{uuid.uuid4().hex[:8]}"
    
    # Create warehouses with low stock in origin
    async with get_async_session() as session:
        async with session.begin():
            wh3 = Warehouse(id=wh3_id, name=wh3_name)
            wh4 = Warehouse(id=wh4_id, name=wh4_name)
            prod = Product(codigo=prod_code, nombre="Test", precio=50.0, cantidad=5)
            
            session.add(wh3)
            session.add(wh4)
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
    
    # Verify stock unchanged
    async with get_async_session() as session:
        stmt = select(WarehouseStock).where(
            WarehouseStock.product_code == prod_code,
            WarehouseStock.warehouse_id == wh3_id
        )
        stock = (await session.execute(stmt)).scalar_one()
        assert stock.quantity == 3  # Unchanged
