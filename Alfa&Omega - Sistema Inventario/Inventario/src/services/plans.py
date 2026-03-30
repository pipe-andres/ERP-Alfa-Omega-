"""
src/services/plans.py
=====================
Tarea 46 — Wrapper SQLite-safe para enforcement de planes en la GUI.
Delega a src/database/plans.py sin requerir Postgres.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from src.database.plans import (
    get_plan_limits,
    LimitExceededError,
    FeatureNotAvailableError,
)

_LOG = logging.getLogger(__name__)


def get_plan_limits_local(user: dict) -> Dict[str, Any]:
    """
    Retorna límites del plan del usuario actual (SQLite-safe).
    user dict tiene clave 'plan' o usa 'free' por defecto.
    -1 = ilimitado.
    """
    roles = (user or {}).get("roles", [])
    plan  = (user or {}).get("plan", "")
    # ADMIN o AUDITOR sin plan definido → enterprise
    if not plan:
        roles_upper = [r.upper() for r in roles]
        if "ADMIN" in roles_upper or "AUDITOR" in roles_upper:
            plan = "enterprise"
        else:
            plan = "free"
    return get_plan_limits(plan)


def check_plan_limit_local(user: dict, resource: str, current_count: int) -> None:
    """
    Lanza PermissionError si current_count >= límite del plan.
    resource: 'branches' | 'products' | 'users'
    """
    limits = get_plan_limits_local(user)
    max_val = limits.get(resource, -1)
    if max_val != -1 and current_count >= max_val:
        raise PermissionError(
            f"Límite de plan alcanzado: {resource} "
            f"({current_count}/{max_val}). "
            f"Actualiza tu plan para continuar."
        )


def check_feature_local(user: dict, feature: str) -> bool:
    """
    Retorna True si el plan tiene acceso al feature.
    feature: 'pos' | 'advanced_reports' | 'api'
    """
    limits = get_plan_limits_local(user)
    key_map = {
        "pos":              "has_pos",
        "advanced_reports": "has_advanced_reports",
        "api":              "has_api",
    }
    key = key_map.get(feature, feature)
    return bool(limits.get(key, False))
