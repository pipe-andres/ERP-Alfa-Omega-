"""Transfers API endpoints."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schemas import TransferCreate, TransferResponse
from app.services.services import TransferService
from src.database.orm import get_async_session


router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    transfer: TransferCreate,
    session: AsyncSession = Depends(get_async_session)
) -> TransferResponse:
    """
    Create a warehouse transfer.
    
    - **product_id**: ID of the product being transferred
    - **quantity**: Quantity to transfer (must be > 0)
    - **source_warehouse**: ID of the source warehouse
    - **target_warehouse**: ID of the target warehouse
    - **timestamp**: Optional transfer timestamp (defaults to now)
    
    Transfers inventory between warehouses using FIFO tracking.
    """
    try:
        service = TransferService(session)
        result = await service.register_transfer(
            product_id=transfer.product_id,
            quantity=transfer.quantity,
            source_warehouse=transfer.source_warehouse,
            target_warehouse=transfer.target_warehouse,
            timestamp=transfer.timestamp
        )
        
        async with session.begin():
            await session.commit()
        
        return TransferResponse(**result)
    
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


@router.get("/{transfer_id}", response_model=dict)
async def get_transfer(
    transfer_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Get transfer details by ID.
    
    - **transfer_id**: ID of the transfer to retrieve
    """
    try:
        from src.database.models import Document
        from sqlalchemy import select
        
        stmt = select(Document).where(Document.id == transfer_id)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transfer {transfer_id} not found"
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
