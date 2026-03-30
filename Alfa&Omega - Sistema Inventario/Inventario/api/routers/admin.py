"""
api/routers/admin.py
=====================
Tarea 9 — Fase 3 SaaS.

Endpoints del Panel Super-Admin.
Todos requieren role=ADMIN (via require_superadmin).
Lógica en src/services/admin.py — el router solo valida y delega.
"""
from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.routers.tenants import require_superadmin
from src.services import admin as admin_svc

_LOG = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class TenantSummary(BaseModel):
    tenant_id: str
    plan: str
    active: bool
    onboarded_at: str


class UsageInfo(BaseModel):
    products: int
    sales: int
    users: int


class TenantDetail(BaseModel):
    tenant_id: str
    plan: str
    active: bool
    onboarded_at: str
    usage: UsageInfo


class PatchTenantRequest(BaseModel):
    active: Optional[bool] = None
    plan: Optional[str] = Field(None, pattern="^(free|starter|pro|enterprise)$")


class PatchTenantResponse(BaseModel):
    tenant_id: str
    active: Optional[bool]
    plan: Optional[str]


class GlobalMetrics(BaseModel):
    total_tenants:   int
    active_tenants:  int
    tenants_by_plan: Dict[str, int]
    new_last_30d:    int
    mrr:             float
    churn_last_30d:  int
    new_last_7d:     int
    trial_tenants:   int


class ImpersonateResponse(BaseModel):
    token:      str
    tenant_id:  str
    expires_in: int


class AuditEntry(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    details: Optional[str]
    created_at: str


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.get("/tenants", response_model=List[TenantSummary])
async def list_admin_tenants(
    _: Annotated[Dict[str, Any], Depends(require_superadmin)],
) -> List[TenantSummary]:
    """Lista todos los tenants (sin datos sensibles de cada schema)."""
    try:
        return [TenantSummary(**t) for t in admin_svc.get_all_tenants()]
    except Exception as e:
        logging.warning("GET /admin/tenants error: %s", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al listar tenants.")


@router.get("/tenants/{tenant_id}", response_model=TenantDetail)
async def get_admin_tenant(
    tenant_id: str,
    _: Annotated[Dict[str, Any], Depends(require_superadmin)],
) -> TenantDetail:
    """Detalle de un tenant + métricas de uso (productos, ventas, usuarios)."""
    try:
        detail = admin_svc.get_tenant_detail(tenant_id)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logging.warning("GET /admin/tenants/%s error: %s", tenant_id, e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al consultar el tenant.")
    return TenantDetail(**detail)


@router.patch("/tenants/{tenant_id}", response_model=PatchTenantResponse)
async def patch_admin_tenant(
    tenant_id: str,
    body: PatchTenantRequest,
    _: Annotated[Dict[str, Any], Depends(require_superadmin)],
) -> PatchTenantResponse:
    """Cambia el estado (active) y/o el plan de un tenant."""
    try:
        result = admin_svc.patch_tenant(tenant_id, body.active, body.plan)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except RuntimeError as e:
        logging.warning("PATCH /admin/tenants/%s RuntimeError: %s", tenant_id, e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Esta operación requiere DB_ENGINE=postgres.")
    except Exception as e:
        logging.warning("PATCH /admin/tenants/%s error: %s", tenant_id, e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al actualizar el tenant.")
    return PatchTenantResponse(**result)


@router.get("/metrics", response_model=GlobalMetrics)
async def global_metrics(
    _: Annotated[Dict[str, Any], Depends(require_superadmin)],
) -> GlobalMetrics:
    """Métricas globales del SaaS: totales, por plan, nuevos en 30 días."""
    try:
        return GlobalMetrics(**admin_svc.get_global_metrics())
    except RuntimeError as e:
        logging.warning("GET /admin/metrics RuntimeError: %s", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Esta operación requiere DB_ENGINE=postgres.")
    except Exception as e:
        logging.warning("GET /admin/metrics error: %s", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al obtener métricas.")


@router.get("/audit", response_model=List[AuditEntry])
async def audit_log(
    _: Annotated[Dict[str, Any], Depends(require_superadmin)],
    tenant_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
) -> List[AuditEntry]:
    """Entradas del audit_log público. Filtra por tenant_id si se indica."""
    try:
        entries = admin_svc.get_audit_log(tenant_id, limit)
        return [AuditEntry(**e) for e in entries]
    except RuntimeError as e:
        logging.warning("GET /admin/audit RuntimeError: %s", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Esta operación requiere DB_ENGINE=postgres.")
    except Exception as e:
        logging.warning("GET /admin/audit error: %s", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al obtener el audit log.")


@router.post("/tenants/{tenant_id}/impersonate", response_model=ImpersonateResponse)
async def impersonate_tenant(
    tenant_id: int,
    payload: Annotated[Dict[str, Any], Depends(require_superadmin)],
) -> ImpersonateResponse:
    """Genera un token temporal como un tenant. Solo super-admin. Deja audit trail."""
    admin_user_id = str(payload.get("username") or payload.get("sub", "unknown"))
    try:
        result = admin_svc.impersonate_tenant(tenant_id, admin_user_id)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        logging.warning("POST /admin/tenants/%s/impersonate RuntimeError: %s", tenant_id, e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Esta operación requiere DB_ENGINE=postgres.")
    except Exception as e:
        logging.warning("POST /admin/tenants/%s/impersonate error: %s", tenant_id, e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al impersonar el tenant.")
    return ImpersonateResponse(**result)
