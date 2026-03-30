"""Repositories for database operations."""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Product, Document, DocumentLine, StockMovement, KardexMove, Warehouse


class PurchaseRepository:
    """Repository for purchase operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_product(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_warehouse(self, warehouse_id: int) -> Optional[Warehouse]:
        """Get warehouse by ID."""
        stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_purchase_document(
        self,
        product_id: int,
        quantity: float,
        unit_cost: float,
        warehouse_id: int,
        timestamp: datetime
    ) -> Dict:
        """Create a purchase document and return purchase details."""
        # Create document
        doc = Document(
            tipo="PURCHASE",
            fecha=timestamp,
            numero=None,  # Auto-generated
            notas=f"API purchase for product {product_id}",
            partner_id=None
        )
        self.session.add(doc)
        await self.session.flush()
        
        # Create document line
        line = DocumentLine(
            doc_id=doc.id,
            codigo=str(product_id),
            qty=quantity,
            unit_cost=unit_cost,
            unit_price=None,
            reason="API purchase"
        )
        self.session.add(line)
        
        # Create stock movement
        movement = StockMovement(
            doc_id=doc.id,
            codigo=str(product_id),
            qty=quantity,
            unit_cost=unit_cost,
            unit_price=None,
            tipo="PURCHASE",
            reason="API purchase",
            created_at=timestamp
        )
        self.session.add(movement)
        
        # Create kardex move
        kardex = KardexMove(
            product_code=str(product_id),
            type="IN",
            qty=quantity,
            unit_cost=unit_cost,
            total_cost=quantity * unit_cost,
            balance_qty=None,
            balance_cost=None,
            balance_total=None,
            date=timestamp,
            warehouse_id=warehouse_id,
            ref_type="PURCHASE",
            ref_id=doc.id
        )
        self.session.add(kardex)
        await self.session.flush()
        
        return {
            "purchase_id": doc.id,
            "product_id": product_id,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "total_cost": quantity * unit_cost,
            "warehouse_id": warehouse_id,
            "timestamp": timestamp
        }


class SalesRepository:
    """Repository for sales operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_product(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_warehouse(self, warehouse_id: int) -> Optional[Warehouse]:
        """Get warehouse by ID."""
        stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_sale_document(
        self,
        product_id: int,
        quantity: float,
        warehouse_id: int,
        timestamp: datetime,
        fifo_cost: float,
        fifo_layers: List[Dict]
    ) -> Dict:
        """Create a sale document and return sale details."""
        # Create document
        doc = Document(
            tipo="SALE",
            fecha=timestamp,
            numero=None,  # Auto-generated
            notas=f"API sale for product {product_id}",
            partner_id=None
        )
        self.session.add(doc)
        await self.session.flush()
        
        # Create document line
        line = DocumentLine(
            doc_id=doc.id,
            codigo=str(product_id),
            qty=quantity,
            unit_cost=None,
            unit_price=None,
            reason="API sale"
        )
        self.session.add(line)
        
        # Create stock movement
        movement = StockMovement(
            doc_id=doc.id,
            codigo=str(product_id),
            qty=-quantity,
            unit_cost=fifo_cost / quantity if quantity > 0 else 0,
            unit_price=None,
            tipo="SALE",
            reason="API sale",
            created_at=timestamp
        )
        self.session.add(movement)
        
        # Create kardex move
        kardex = KardexMove(
            product_code=str(product_id),
            type="OUT",
            qty=-quantity,
            unit_cost=(fifo_cost / quantity if quantity > 0 else 0),
            total_cost=fifo_cost,
            balance_qty=None,
            balance_cost=None,
            balance_total=None,
            date=timestamp,
            warehouse_id=warehouse_id,
            ref_type="SALE",
            ref_id=doc.id
        )
        self.session.add(kardex)
        await self.session.flush()
        
        return {
            "sale_id": doc.id,
            "product_id": product_id,
            "quantity_sold": quantity,
            "warehouse_id": warehouse_id,
            "total_cost": fifo_cost,
            "fifo_layers_consumed": fifo_layers,
            "timestamp": timestamp
        }


class TransferRepository:
    """Repository for transfer operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_product(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_warehouse(self, warehouse_id: int) -> Optional[Warehouse]:
        """Get warehouse by ID."""
        stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_transfer(
        self,
        product_id: int,
        quantity: float,
        source_warehouse: int,
        target_warehouse: int,
        timestamp: datetime
    ) -> Dict:
        """Create a transfer record between warehouses."""
        # Create document
        doc = Document(
            tipo="TRANSFER",
            fecha=timestamp,
            numero=None,
            notas=f"API transfer for product {product_id}",
            partner_id=None
        )
        self.session.add(doc)
        await self.session.flush()
        
        # Create document lines (one for each warehouse)
        line_out = DocumentLine(
            doc_id=doc.id,
            codigo=str(product_id),
            qty=-quantity,
            unit_cost=None,
            unit_price=None,
            reason=f"Transfer from WH{source_warehouse} to WH{target_warehouse}"
        )
        self.session.add(line_out)
        
        line_in = DocumentLine(
            doc_id=doc.id,
            codigo=str(product_id),
            qty=quantity,
            unit_cost=None,
            unit_price=None,
            reason=f"Transfer from WH{source_warehouse} to WH{target_warehouse}"
        )
        self.session.add(line_in)
        
        # Create stock movements
        movement_out = StockMovement(
            doc_id=doc.id,
            codigo=str(product_id),
            qty=-quantity,
            unit_cost=None,
            unit_price=None,
            tipo="TRANSFER_OUT",
            reason=f"Transfer from WH{source_warehouse} to WH{target_warehouse}",
            created_at=timestamp
        )
        self.session.add(movement_out)
        
        movement_in = StockMovement(
            doc_id=doc.id,
            codigo=str(product_id),
            qty=quantity,
            unit_cost=None,
            unit_price=None,
            tipo="TRANSFER_IN",
            reason=f"Transfer from WH{source_warehouse} to WH{target_warehouse}",
            created_at=timestamp
        )
        self.session.add(movement_in)
        
        # Create kardex moves
        kardex_out = KardexMove(
            product_code=str(product_id),
            type="TRANSFER_OUT",
            qty=-quantity,
            unit_cost=None,
            total_cost=None,
            balance_qty=None,
            balance_cost=None,
            balance_total=None,
            date=timestamp,
            warehouse_id=source_warehouse,
            ref_type="TRANSFER",
            ref_id=doc.id
        )
        self.session.add(kardex_out)
        
        kardex_in = KardexMove(
            product_code=str(product_id),
            type="TRANSFER_IN",
            qty=quantity,
            unit_cost=None,
            total_cost=None,
            balance_qty=None,
            balance_cost=None,
            balance_total=None,
            date=timestamp,
            warehouse_id=target_warehouse,
            ref_type="TRANSFER",
            ref_id=doc.id
        )
        self.session.add(kardex_in)
        await self.session.flush()
        
        return {
            "transfer_id": doc.id,
            "product_id": product_id,
            "quantity": quantity,
            "source_warehouse": source_warehouse,
            "target_warehouse": target_warehouse,
            "timestamp": timestamp
        }


class KardexRepository:
    """Repository for kardex operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_kardex(self, product_code: str, warehouse_id: Optional[int] = None) -> List[Dict]:
        """Get kardex moves for a product."""
        stmt = select(KardexMove).where(
            KardexMove.product_code == product_code
        )
        if warehouse_id:
            stmt = stmt.where(KardexMove.warehouse_id == warehouse_id)
        stmt = stmt.order_by(KardexMove.date)
        
        result = await self.session.execute(stmt)
        moves = result.scalars().all()
        
        return [
            {
                "id": m.id,
                "product_code": m.product_code,
                "type": m.type,
                "qty": float(m.qty or 0),
                "unit_cost": float(m.unit_cost or 0) if m.unit_cost else None,
                "total_cost": float(m.total_cost or 0) if m.total_cost else None,
                "balance_qty": float(m.balance_qty or 0) if m.balance_qty else None,
                "balance_cost": float(m.balance_cost or 0) if m.balance_cost else None,
                "date": m.date,
                "warehouse_id": m.warehouse_id,
                "ref_type": m.ref_type,
                "ref_id": m.ref_id
            }
            for m in moves
        ]
