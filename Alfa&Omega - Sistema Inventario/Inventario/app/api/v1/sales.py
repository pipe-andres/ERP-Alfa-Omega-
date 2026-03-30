"""Sales API endpoints."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schemas import SaleCreate, SaleResponse
from app.services.services import SalesService
from src.database.orm import get_async_session


router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale: SaleCreate,
    session: AsyncSession = Depends(get_async_session)
) -> SaleResponse:
    """
    Create a new sale with FIFO costing.
    
    - **product_id**: ID of the product being sold
    - **quantity**: Quantity to sell (must be > 0)
    - **warehouse_id**: ID of the warehouse from which to sell
    - **timestamp**: Optional sale timestamp (defaults to now)
    
    Returns the sale details including FIFO layers consumed and total cost.
    """
    try:
        service = SalesService(session)
        result = await service.register_sale(
            product_id=sale.product_id,
            quantity=sale.quantity,
            warehouse_id=sale.warehouse_id,
            timestamp=sale.timestamp
        )
        
        async with session.begin():
            await session.commit()
        
        return SaleResponse(**result)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{sale_id}", response_model=dict)
async def get_sale(
    sale_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Get sale details by ID.
    
    - **sale_id**: ID of the sale to retrieve
    """
    try:
        from src.database.models import Document
        from sqlalchemy import select
        
        stmt = select(Document).where(Document.id == sale_id)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sale {sale_id} not found"
            )
        
        return {
            "id": doc.id,
            "tipo": doc.tipo,
            "fecha": doc.fecha,
            "numero": doc.numero,
            "notas": doc.notas
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
