from pydantic import BaseModel
from typing import List, Optional


class LineItem(BaseModel):
    codigo: str
    qty: float
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None


class PurchaseRequest(BaseModel):
    numero: Optional[str] = None
    fecha: str
    items: List[LineItem]
    notas: Optional[str] = None
    partner_code: Optional[str] = None
    series: Optional[str] = None


class SaleRequest(BaseModel):
    numero: Optional[str] = None
    fecha: str
    items: List[LineItem]
    notas: Optional[str] = None
    allow_negative: Optional[bool] = False


class TransferRequest(BaseModel):
    product_code: str
    from_warehouse: int
    to_warehouse: int
    quantity: float
    notas: Optional[str] = None


class BasicResponse(BaseModel):
    ok: bool
    detail: Optional[str] = None
    doc_id: Optional[int] = None
    numero: Optional[str] = None
