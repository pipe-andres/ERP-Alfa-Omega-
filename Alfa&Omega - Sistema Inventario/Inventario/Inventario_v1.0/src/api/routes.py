from fastapi import APIRouter, HTTPException
from src.api.schemas import PurchaseRequest, SaleRequest, TransferRequest, BasicResponse
from src.services import (
    post_purchase_async,
    post_sale_async,
    transfer_stock_async,
)

router = APIRouter()


@router.post("/purchases", response_model=BasicResponse)
async def create_purchase(req: PurchaseRequest):
    try:
        doc_id, numero = await post_purchase_async(
            numero=req.numero,
            fecha=req.fecha,
            items=[item.dict() for item in req.items],
            notas=req.notas,
            partner_code=req.partner_code,
            series=req.series,
        )
        return BasicResponse(ok=True, doc_id=doc_id, numero=numero)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sales", response_model=BasicResponse)
async def create_sale(req: SaleRequest):
    try:
        doc_id, numero, totals = await post_sale_async(
            numero=req.numero,
            fecha=req.fecha,
            items=[item.dict() for item in req.items],
            notas=req.notas,
            allow_negative=req.allow_negative,
        )
        return BasicResponse(ok=True, doc_id=doc_id, numero=numero)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transfers", response_model=BasicResponse)
async def create_transfer(req: TransferRequest):
    try:
        transfer_id = await transfer_stock_async(
            product_code=req.product_code,
            from_warehouse=req.from_warehouse,
            to_warehouse=req.to_warehouse,
            quantity=req.quantity,
            notas=req.notas if hasattr(req, 'notas') else None,
        )
        return BasicResponse(ok=True, doc_id=transfer_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
