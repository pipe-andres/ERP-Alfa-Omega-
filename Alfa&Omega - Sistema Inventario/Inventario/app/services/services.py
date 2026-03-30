"""Business logic services for inventory operations."""
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repositories import (
    PurchaseRepository, SalesRepository, TransferRepository, KardexRepository
)
from src.services.kardex import get_product_kardex


class PurchaseService:
    """Service for purchase operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PurchaseRepository(session)
    
    async def register_purchase(
        self,
        product_id: int,
        quantity: float,
        unit_cost: float,
        warehouse_id: int,
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """Register a purchase in the system."""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Validate product exists
        product = await self.repo.get_product(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        # Validate warehouse exists
        warehouse = await self.repo.get_warehouse(warehouse_id)
        if not warehouse:
            raise ValueError(f"Warehouse {warehouse_id} not found")
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if unit_cost < 0:
            raise ValueError("Unit cost cannot be negative")
        
        # Create purchase document
        purchase_data = await self.repo.create_purchase_document(
            product_id, quantity, unit_cost, warehouse_id, timestamp
        )
        
        # Get updated kardex
        kardex = get_product_kardex(str(product_id), warehouse_id)
        
        return {
            **purchase_data,
            "kardex_status": kardex[-1] if kardex else None
        }


class SalesService:
    """Service for sales operations with FIFO costing."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SalesRepository(session)
        self.kardex_repo = KardexRepository(session)
    
    async def register_sale(
        self,
        product_id: int,
        quantity: float,
        warehouse_id: int,
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """Register a sale with FIFO costing."""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Validate product exists
        product = await self.repo.get_product(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        # Validate warehouse exists
        warehouse = await self.repo.get_warehouse(warehouse_id)
        if not warehouse:
            raise ValueError(f"Warehouse {warehouse_id} not found")
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        # Get kardex with FIFO calculation
        kardex_moves = get_product_kardex(str(product_id), warehouse_id)
        
        # Calculate FIFO cost and consumed layers
        fifo_cost, layers = self._calculate_fifo_cost(kardex_moves, quantity)
        
        # Create sale document
        sale_data = await self.repo.create_sale_document(
            product_id, quantity, warehouse_id, timestamp, fifo_cost, layers
        )
        
        return sale_data
    
    def _calculate_fifo_cost(self, kardex_moves: List[Dict], quantity: float) -> tuple:
        """Calculate FIFO cost from kardex moves."""
        layers = []
        total_cost = 0.0
        remaining = quantity
        
        for move in kardex_moves:
            if remaining <= 0:
                break
            
            move_type = move.get("type", "").upper()
            if move_type in ("IN", "PURCHASE", "ADJUST+", "TRANSFER_IN"):
                # This is an inbound move, add to available layers
                layers.append({
                    "layer_qty": float(move.get("qty", 0)),
                    "layer_unit_cost": float(move.get("unit_cost", 0) or 0),
                    "layer_total_cost": float(move.get("total_cost", 0) or 0),
                    "available": float(move.get("qty", 0))
                })
        
        # Consume layers FIFO style
        consumed_layers = []
        for layer in layers:
            if remaining <= 0:
                break
            
            take = min(remaining, layer["available"])
            layer_cost = take * layer["layer_unit_cost"]
            total_cost += layer_cost
            remaining -= take
            
            consumed_layers.append({
                "layer_qty": take,
                "layer_unit_cost": layer["layer_unit_cost"],
                "layer_total_cost": layer_cost
            })
        
        if remaining > 1e-6:
            raise ValueError(f"Insufficient stock. Need {quantity}, only {quantity - remaining} available")
        
        return total_cost, consumed_layers


class TransferService:
    """Service for warehouse transfers."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TransferRepository(session)
    
    async def register_transfer(
        self,
        product_id: int,
        quantity: float,
        source_warehouse: int,
        target_warehouse: int,
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """Register a warehouse transfer."""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Validate product exists
        product = await self.repo.get_product(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        # Validate warehouses exist
        source_wh = await self.repo.get_warehouse(source_warehouse)
        if not source_wh:
            raise ValueError(f"Source warehouse {source_warehouse} not found")
        
        target_wh = await self.repo.get_warehouse(target_warehouse)
        if not target_wh:
            raise ValueError(f"Target warehouse {target_warehouse} not found")
        
        if source_warehouse == target_warehouse:
            raise ValueError("Source and target warehouse cannot be the same")
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        # Get kardex to validate sufficient stock
        kardex = get_product_kardex(str(product_id), source_warehouse)
        available = sum(
            float(m.get("qty", 0)) for m in kardex 
            if m.get("type", "").upper() in ("IN", "PURCHASE", "ADJUST+", "TRANSFER_IN")
        )
        
        if available < quantity:
            raise ValueError(
                f"Insufficient stock in source warehouse. Available: {available}, Required: {quantity}"
            )
        
        # Create transfer document
        transfer_data = await self.repo.create_transfer(
            product_id, quantity, source_warehouse, target_warehouse, timestamp
        )
        
        return transfer_data
