"""
api/routers/productos.py
========================
Tarea 16 — CRUD de productos vía API REST.
Reutiliza src/services/inventory.py.
"""
from __future__ import annotations
import logging
from typing import Annotated, Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from api.routers.auth import get_current_user
from src.services import inventory

_LOG = logging.getLogger(__name__)
router = APIRouter(tags=["productos"])

# ── Schemas ────────────────────────────────────────────────────────────────────

class ProductoCreate(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=200)
    categoria: Optional[str] = None
    precio: float = Field(..., ge=0)
    cantidad: int = Field(0, ge=0)
    avg_cost: float = Field(0.0, ge=0)

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    precio: Optional[float] = Field(None, ge=0)
    cantidad: Optional[int] = Field(None, ge=0)
    avg_cost: Optional[float] = Field(None, ge=0)

# ── Dependencias ───────────────────────────────────────────────────────────────

def require_auth(payload: Annotated[Dict[str, Any], Depends(get_current_user)]) -> Dict[str, Any]:
    """Solo exige JWT válido, sin restricción de rol."""
    return payload

def require_admin(payload: Annotated[Dict[str, Any], Depends(get_current_user)]) -> Dict[str, Any]:
    if payload.get("role") != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol ADMIN.")
    return payload

# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "/productos/",
    response_model=Dict[str, Any],
    summary="Listar productos",
    description="Obtiene una lista paginada de productos, con opción de búsqueda por código o nombre."
)
async def list_productos(
    _: Annotated[Dict, Depends(require_auth)],
    search: str = Query("", description="Búsqueda por código o nombre"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Lista productos con paginación y búsqueda opcional."""
    try:
        page = offset // limit + 1
        rows = inventory.list_products_page(page=page, page_size=limit, q=search)
        total = inventory.count_products(q=search)
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [
                {"codigo": r[0], "nombre": r[1], "categoria": r[2],
                 "precio": r[3], "cantidad": r[4],
                 "avg_cost": r[5] if len(r) > 5 else 0.0}
                for r in rows
            ],
        }
    except Exception as e:
        logging.warning("list_productos error: %s", e)
        raise HTTPException(status_code=500, detail="Error al listar productos.")


@router.get(
    "/productos/{codigo}",
    response_model=Dict[str, Any],
    summary="Obtener producto por código",
    description="Retorna los detalles completos de un producto específico mediante su código único."
)
async def get_producto(
    codigo: str,
    _: Annotated[Dict, Depends(require_auth)],
):
    """Detalle de un producto por código."""
    try:
        row = inventory.get_product(codigo)
    except Exception as e:
        logging.warning("get_producto(%r) error: %s", codigo, e)
        raise HTTPException(status_code=500, detail="Error al obtener producto.")
    if not row:
        raise HTTPException(status_code=404, detail=f"Producto '{codigo}' no encontrado.")
    return {
        "codigo": row[0], "nombre": row[1], "categoria": row[2],
        "precio": row[3], "cantidad": row[4],
        "avg_cost": row[5] if len(row) > 5 else 0.0,
    }


@router.post(
    "/productos/", 
    response_model=Dict[str, Any], 
    status_code=201,
    summary="Crear producto",
    description="Crea un nuevo producto en el inventario. Se valida que el código sea único. Requiere permisos de administrador (rol ADMIN)."
)
async def create_producto(
    body: ProductoCreate,
    payload: Annotated[Dict, Depends(require_admin)],
):
    """Crea un producto. Requiere rol ADMIN."""
    try:
        inventory.add_product(
            body.codigo, body.nombre, body.categoria or "",
            body.precio, body.cantidad, body.avg_cost,
            user_id=payload.get("user_id"),
        )
        return {"created": body.codigo}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logging.warning("create_producto error: %s", e)
        raise HTTPException(status_code=500, detail="Error al crear producto.")


@router.put(
    "/productos/{codigo}",
    response_model=Dict[str, Any],
    summary="Actualizar producto",
    description="Actualiza los campos de un producto existente. Los campos no proporcionados se mantendrán iguales. Requiere permisos de administrador (rol ADMIN)."
)
async def update_producto(
    codigo: str,
    body: ProductoUpdate,
    payload: Annotated[Dict, Depends(require_admin)],
):
    """Actualiza campos de un producto. Requiere rol ADMIN."""
    try:
        inventory.update_product(
            codigo,
            nombre=body.nombre,
            categoria=body.categoria,
            precio=body.precio,
            cantidad=body.cantidad,
            avg_cost=body.avg_cost,
            user_id=payload.get("user_id"),
        )
        return {"updated": codigo}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.warning("update_producto(%r) error: %s", codigo, e)
        raise HTTPException(status_code=500, detail="Error al actualizar producto.")
