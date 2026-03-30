"""
api/routers/onboarding.py
==========================
Tarea 6 — Fase 3 SaaS.

Endpoints públicos de onboarding de tenants.
No requieren autenticación (el tenant aún no existe).
Reutiliza src/services/onboarding.py sin duplicar lógica.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.onboarding import onboard_tenant, get_onboarding_status

_LOG = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class OnboardRequest(BaseModel):
    tenant_id:       str  = Field(..., min_length=1, max_length=63)
    plan:            str  = Field(..., pattern="^(free|starter|pro|enterprise)$")
    admin_username:  str  = Field(..., min_length=3, max_length=50)
    admin_password:  str  = Field(..., min_length=8, max_length=128)  # ≥8 chars
    company_name:    str  = Field(..., min_length=1, max_length=120)
    industry:        str  = Field("", max_length=80)
    currency:        str  = Field("COP", max_length=10)
    timezone:        str  = Field("America/Bogota", max_length=60)


class OnboardResponse(BaseModel):
    tenant_id:      str
    plan:           str
    admin_username: str
    onboarded_at:   str
    next_steps:     List[str]


class OnboardStatusResponse(BaseModel):
    tenant_id:     str
    schema_exists: bool
    has_admin:     bool
    plan:          str | None
    active:        bool


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post(
    "/register",
    response_model=OnboardResponse,
    status_code=201,
    tags=["onboarding"],
)
async def register(body: OnboardRequest) -> OnboardResponse:
    """
    Registra un nuevo tenant completo:
    crea schema, DDL, usuario admin y asigna plan.
    Idempotente — si el schema ya existe retorna 409.
    Solo disponible con DB_ENGINE=postgres.
    """
    try:
        result: Dict[str, Any] = onboard_tenant(body.model_dump())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        # DB_ENGINE=sqlite u otro error de infraestructura
        logging.warning("POST /onboarding/register RuntimeError: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Esta operación requiere DB_ENGINE=postgres.",
        )
    except Exception as e:
        logging.warning("POST /onboarding/register error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el proceso de onboarding.",
        )

    return OnboardResponse(**result)


@router.get(
    "/{tenant_id}/status",
    response_model=OnboardStatusResponse,
    tags=["onboarding"],
)
async def onboarding_status(tenant_id: str) -> OnboardStatusResponse:
    """
    Estado del onboarding de un tenant.
    Requiere token válido (protegido por TenantMiddleware).
    """
    try:
        result = get_onboarding_status(tenant_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        logging.warning("GET /onboarding/%s/status RuntimeError: %s", tenant_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Esta operación requiere DB_ENGINE=postgres.",
        )
    except Exception as e:
        logging.warning("GET /onboarding/%s/status error: %s", tenant_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar el estado del tenant.",
        )

    return OnboardStatusResponse(**result)
