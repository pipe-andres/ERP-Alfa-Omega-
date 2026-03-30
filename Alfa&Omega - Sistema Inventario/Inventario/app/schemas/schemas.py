"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== Compras ====================
class PurchaseCreate(BaseModel):
    """Schema for creating a purchase."""
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: float = Field(..., gt=0, description="Quantity to purchase")
    unit_cost: float = Field(..., ge=0, description="Cost per unit")
    warehouse_id: int = Field(..., gt=0, description="Warehouse ID")
    timestamp: Optional[datetime] = Field(None, description="Purchase timestamp (default: now)")


class PurchaseResponse(BaseModel):
    """Response for purchase creation."""
    purchase_id: int
    product_id: int
    quantity: float
    unit_cost: float
    total_cost: float
    warehouse_id: int
    timestamp: datetime
    message: str = "Purchase registered successfully"

    class Config:
        from_attributes = True


# ==================== Ventas ====================
class SaleCreate(BaseModel):
    """Schema for creating a sale."""
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: float = Field(..., gt=0, description="Quantity to sell")
    warehouse_id: int = Field(..., gt=0, description="Warehouse ID")
    timestamp: Optional[datetime] = Field(None, description="Sale timestamp (default: now)")


class SaleLineItem(BaseModel):
    """Individual line item in sale (FIFO layer consumed)."""
    layer_qty: float = Field(..., description="Quantity from this layer")
    layer_unit_cost: float = Field(..., description="Unit cost of this layer")
    layer_total_cost: float = Field(..., description="Total cost from this layer")


class SaleResponse(BaseModel):
    """Response for sale creation."""
    sale_id: int
    product_id: int
    quantity_sold: float
    warehouse_id: int
    total_cost: float
    fifo_layers_consumed: List[SaleLineItem]
    timestamp: datetime
    message: str = "Sale registered successfully with FIFO costing"

    class Config:
        from_attributes = True


# ==================== Transferencias ====================
class TransferCreate(BaseModel):
    """Schema for warehouse transfer."""
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: float = Field(..., gt=0, description="Quantity to transfer")
    source_warehouse: int = Field(..., gt=0, description="Source warehouse ID")
    target_warehouse: int = Field(..., gt=0, description="Target warehouse ID")
    timestamp: Optional[datetime] = Field(None, description="Transfer timestamp (default: now)")


class TransferResponse(BaseModel):
    """Response for transfer creation."""
    transfer_id: int
    product_id: int
    quantity: float
    source_warehouse: int
    target_warehouse: int
    timestamp: datetime
    message: str = "Transfer completed successfully"

    class Config:
        from_attributes = True


# ==================== Errors ====================
class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int
