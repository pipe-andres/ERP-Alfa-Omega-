"""Purchases API endpoints."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schemas import PurchaseCreate, PurchaseResponse
from app.services.services import PurchaseService
from src.database.orm import get_async_session


router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase(
    purchase: PurchaseCreate,
    session: AsyncSession = Depends(get_async_session)
) -> PurchaseResponse:
    """
    Create a new purchase.
    
    - **product_id**: ID of the product being purchased
    - **quantity**: Quantity to purchase (must be > 0)
    - **unit_cost**: Cost per unit
    - **warehouse_id**: ID of the warehouse receiving the purchase
    - **timestamp**: Optional purchase timestamp (defaults to now)
    """
    try:
        service = PurchaseService(session)
        result = await service.register_purchase(
            product_id=purchase.product_id,
            quantity=purchase.quantity,
            unit_cost=purchase.unit_cost,
            warehouse_id=purchase.warehouse_id,
            timestamp=purchase.timestamp
        )
        
        async with session.begin():
            await session.commit()
        
        return PurchaseResponse(**result)
    
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


@router.get("/{purchase_id}", response_model=dict)
async def get_purchase(
    purchase_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Get purchase details by ID.
    
    - **purchase_id**: ID of the purchase to retrieve
    """
    try:
        from src.database.models import Document
        from sqlalchemy import select
        
        stmt = select(Document).where(Document.id == purchase_id)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase {purchase_id} not found"
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
