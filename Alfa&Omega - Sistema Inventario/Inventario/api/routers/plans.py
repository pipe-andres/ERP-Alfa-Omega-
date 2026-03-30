"""
api/routers/plans.py
=====================
Tarea 5B — Fase 3 SaaS.

Endpoints de planes de suscripción (montado sin prefix en main.py).
  GET  /plans/                     → público, fallback SQLite
  POST /tenants/{tenant_id}/plan   → require_superadmin
"""
from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.routers.tenants import PlanType, require_superadmin
from src.database.plans import (
    _DEFAULT_PLANS,
    assign_plan_to_tenant,
    list_plans,
)

_LOG = logging.getLogger(__name__)
router = APIRouter()

_VALID_PLANS = {"free", "starter", "pro", "enterprise"}

# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class PlanResponse(BaseModel):
    id: Optional[int] = None
    name: str
    price_usd: Optional[float]
    max_users: int
    max_branches: int
    max_products: int
    has_pos: bool
    has_advanced_reports: bool
    has_api: bool
    support_level: str
    sla_percent: Optional[float]
    active: bool = True


class AssignPlanRequest(BaseModel):
    plan_name: PlanType


class AssignPlanResponse(BaseModel):
    tenant_id: str
    plan: str
    updated: bool = True


# ─────────────────────────────────────────────
# Fallback hardcodeado para SQLite / dev
# ─────────────────────────────────────────────

_FALLBACK_PLANS: List[Dict[str, Any]] = [
    {**p, "id": i + 1, "active": True}
    for i, p in enumerate(_DEFAULT_PLANS)
]


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.get("/plans/", response_model=List[PlanResponse], tags=["plans"])
async def get_plans() -> List[PlanResponse]:
    """
    Lista los planes de suscripción disponibles.
    Público — no requiere token.
    En modo SQLite retorna los 4 planes hardcodeados
    para que el endpoint nunca falle en desarrollo.
    """
    try:
        rows = list_plans()
        return [PlanResponse(**r) for r in rows]
    except RuntimeError:
        # SQLite dev: fallback hardcodeado — nunca falla
        _LOG.warning("GET /plans/: usando fallback hardcodeado (SQLite/dev).")
        return [PlanResponse(**p) for p in _FALLBACK_PLANS]
    except Exception as e:
        logging.warning("GET /plans/ error inesperado: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los planes.",
        )


@router.post(
    "/tenants/{tenant_id}/plan",
    response_model=AssignPlanResponse,
    status_code=200,
    tags=["plans"],
)
async def assign_plan(
    tenant_id: str,
    body: AssignPlanRequest,
    _admin: Annotated[Dict[str, Any], Depends(require_superadmin)],
) -> AssignPlanResponse:
    """
    Asigna un plan a un tenant existente.
    Requiere role=ADMIN y tenant_id=public en el JWT.
    """
    if body.plan_name not in _VALID_PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan inválido: {body.plan_name!r}. "
                   f"Válidos: {sorted(_VALID_PLANS)}",
        )
    try:
        result = assign_plan_to_tenant(tenant_id, body.plan_name)
    except ValueError as e:
        detail = str(e)
        code = (
            status.HTTP_404_NOT_FOUND
            if "Tenant no encontrado" in detail
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=detail)
    except RuntimeError as e:
        # SQLite dev: assign_plan_to_tenant requiere Postgres
        logging.warning(
            "POST /tenants/%s/plan RuntimeError (SQLite?): %s", tenant_id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Esta operación requiere DB_ENGINE=postgres.",
        )
    except Exception as e:
        logging.warning("POST /tenants/%s/plan error: %s", tenant_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al asignar el plan.",
        )

    _LOG.info("Plan asignado: tenant=%r plan=%r", tenant_id, body.plan_name)
    return AssignPlanResponse(
        tenant_id=result["tenant_id"],
        plan=result["plan"],
        updated=True,
    )
