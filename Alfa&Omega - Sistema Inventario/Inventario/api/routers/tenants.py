"""
api/routers/tenants.py
========================
Tarea 4 — Fase 3 SaaS.

Super-Admin API para gestión de tenants.
Reutiliza:
  - get_current_user  de api/routers/auth.py
  - create_tenant_schema, drop_tenant_schema, list_tenants
    de src/database/tenant_provisioning.py
"""
from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, List, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.routers.auth import get_current_user
from src.database.tenant_provisioning import (
    create_tenant_schema,
    drop_tenant_schema,
    list_tenants,
)
import src.services.admin as admin_svc

_LOG = logging.getLogger(__name__)
router = APIRouter()

PlanType = Literal["free", "starter", "pro", "enterprise"]


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class CreateTenantRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1, max_length=63)
    plan: PlanType = "free"


class TenantResponse(BaseModel):
    tenant_id: str
    schema_name: str
    plan: str
    created_at: str
    already_existed: bool


class TenantStatusResponse(BaseModel):
    id: int
    schema_name: str
    plan: str
    created_at: str
    active: bool


class DropResponse(BaseModel):
    dropped: str
    status: str


class TenantTrialStatusResponse(BaseModel):
    in_trial: bool
    trial_ends_at: str | None
    trial_days_left: int
    plan_active: bool


def require_auth(
    payload: Annotated[Dict[str, Any], Depends(get_current_user)],
) -> Dict[str, Any]:
    """Solo exige JWT válido, sin restricción de rol ni tenant."""
    return payload


# ─────────────────────────────────────────────
# Seguridad: require_superadmin
# ─────────────────────────────────────────────

def require_superadmin(
    payload: Annotated[Dict[str, Any], Depends(get_current_user)],
) -> Dict[str, Any]:
    """
    Dependencia: solo permite acceso a usuarios con
      role == "ADMIN"  Y  tenant_id == "public".
    Registra cada intento no autorizado en warning.
    """
    role = payload.get("role", "")
    tenant = payload.get("tenant_id", "")
    if role != "ADMIN" or tenant != "public":
        logging.warning(
            "require_superadmin: acceso denegado — username=%r role=%r tenant_id=%r",
            payload.get("username"), role, tenant,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a super-administradores.",
        )
    return payload


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post("/", response_model=TenantResponse, status_code=201)
async def create_tenant(
    body: CreateTenantRequest,
    _admin: Annotated[Dict[str, Any], Depends(require_superadmin)],
) -> TenantResponse:
    """Crea un nuevo tenant (schema + DDL + registro en public.tenants)."""
    try:
        result = create_tenant_schema(body.tenant_id, body.plan)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(e))
    except Exception as e:
        logging.warning("POST /tenants/ error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al crear el tenant.")

    if result.get("already_existed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El tenant '{body.tenant_id}' ya existe.",
        )

    _LOG.info("Tenant creado: %r plan=%r", body.tenant_id, body.plan)
    return TenantResponse(**result)


@router.get("/", response_model=List[TenantStatusResponse])
async def get_tenants(
    _admin: Annotated[Dict[str, Any], Depends(require_superadmin)],
) -> List[TenantStatusResponse]:
    """Lista todos los tenants registrados en public.tenants."""
    try:
        rows = list_tenants()
    except Exception as e:
        logging.warning("GET /tenants/ error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al listar tenants.")
    return [TenantStatusResponse(**r) for r in rows]


@router.delete("/{tenant_id}", response_model=DropResponse)
async def delete_tenant(
    tenant_id: str,
    payload: Annotated[Dict[str, Any], Depends(require_superadmin)],
) -> DropResponse:
    """Elimina el schema de un tenant (CASCADE) y lo marca inactivo."""
    user_id: int = payload["user_id"]
    try:
        dropped = drop_tenant_schema(tenant_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(e))
    except PermissionError as e:
        logging.warning("DELETE /tenants/%s PermissionError: %s", tenant_id, e)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Sin permiso para eliminar tenants.")
    except Exception as e:
        logging.warning("DELETE /tenants/%s error: %s", tenant_id, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al eliminar el tenant.")

    if not dropped:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' no encontrado.",
        )

    _LOG.warning("Tenant eliminado: %r (por user_id=%s)", tenant_id, user_id)
    return DropResponse(dropped=tenant_id, status="deactivated")


@router.get("/{tenant_id}/status", response_model=TenantStatusResponse)
async def tenant_status(
    tenant_id: str,
    _admin: Annotated[Dict[str, Any], Depends(require_superadmin)],
) -> TenantStatusResponse:
    """Retorna info del tenant: plan, active, created_at, schema_name."""
    try:
        rows = list_tenants()  # cacheado 30s
    except Exception as e:
        logging.warning("GET /tenants/%s/status error: %s", tenant_id, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al consultar el tenant.")

    match = next((r for r in rows if r["schema_name"] == tenant_id), None)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' no encontrado.",
        )
    return TenantStatusResponse(**match)


@router.get(
    "/{tenant_id}/trial-status",
    response_model=TenantTrialStatusResponse,
    summary="Estado de trial del tenant",
    description=(
        "Consulta si el tenant se encuentra en período de prueba (trial), "
        "cuántos días le quedan, y si su plan está activo. "
        "Requiere JWT válido (cualquier rol)."
    ),
)
async def tenant_trial_status(
    tenant_id: str,
    _: Annotated[Dict[str, Any], Depends(require_auth)],
) -> TenantTrialStatusResponse:
    """Retorna estado de trial y expiración del plan para el tenant indicado."""
    try:
        result = admin_svc.check_tenant_trial(tenant_id)
        return TenantTrialStatusResponse(**result)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logging.warning("GET /tenants/%s/trial-status error: %s", tenant_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar estado de trial.",
        )
