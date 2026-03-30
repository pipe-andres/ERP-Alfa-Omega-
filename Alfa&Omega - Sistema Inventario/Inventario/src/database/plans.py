"""
src/database/plans.py
======================
Tarea 5 — Fase 3 SaaS multi-tenant.

Gestión de planes de suscripción en schema public.
Solo funciona con DB_ENGINE=postgres.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from src.database.connection import DB_ENGINE, get_connection
from src.database.tenant_provisioning import _ensure_tenants_table, _require_postgres
from src.core.caching import cached, invalidate_prefix

_LOG = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# DDL helpers
# ─────────────────────────────────────────────

def _ensure_plans_table(conn) -> None:
    """Crea public.subscription_plans si no existe (idempotente)."""
    cur = conn.cursor()
    cur.execute("SET search_path = public")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id                   SERIAL PRIMARY KEY,
            name                 TEXT UNIQUE NOT NULL,
            price_usd            NUMERIC(10,2),
            max_users            INTEGER NOT NULL DEFAULT 1,
            max_branches         INTEGER NOT NULL DEFAULT 1,
            max_products         INTEGER NOT NULL DEFAULT 100,
            has_pos              BOOLEAN NOT NULL DEFAULT FALSE,
            has_advanced_reports BOOLEAN NOT NULL DEFAULT FALSE,
            has_api              BOOLEAN NOT NULL DEFAULT FALSE,
            support_level        TEXT NOT NULL DEFAULT 'community',
            sla_percent          NUMERIC(5,2),
            active               BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS ix_plans_name ON subscription_plans(name)"
    )
    conn.commit()


# ─────────────────────────────────────────────
# Datos por defecto (Blueprint)
# ─────────────────────────────────────────────

_DEFAULT_PLANS: List[Dict[str, Any]] = [
    {
        "name": "free",
        "price_usd": 0.00,
        "max_users": 1,
        "max_branches": 1,
        "max_products": 100,
        "has_pos": False,
        "has_advanced_reports": False,
        "has_api": False,
        "support_level": "community",
        "sla_percent": None,
    },
    {
        "name": "starter",
        "price_usd": 29.00,
        "max_users": 5,
        "max_branches": 1,
        "max_products": 500,
        "has_pos": True,
        "has_advanced_reports": False,
        "has_api": False,
        "support_level": "email",
        "sla_percent": 99.00,
    },
    {
        "name": "pro",
        "price_usd": 79.00,
        "max_users": 20,
        "max_branches": 3,
        "max_products": 5000,
        "has_pos": True,
        "has_advanced_reports": True,
        "has_api": True,
        "support_level": "priority",
        "sla_percent": 99.50,
    },
    {
        "name": "enterprise",
        "price_usd": None,
        "max_users": -1,
        "max_branches": -1,
        "max_products": -1,
        "has_pos": True,
        "has_advanced_reports": True,
        "has_api": True,
        "support_level": "dedicated",
        "sla_percent": 99.90,
    },
]


# ─────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────

def seed_default_plans() -> None:
    """
    Inserta los 4 planes del Blueprint si no existen.
    Idempotente: ON CONFLICT DO NOTHING.
    Llamar desde el lifespan de api/main.py en modo Postgres.
    """
    _require_postgres()
    try:
        os.environ["TENANT_SCHEMA"] = "public"
        with get_connection() as conn:
            _ensure_plans_table(conn)
            cur = conn.cursor()
            cur.execute("SET search_path = public")
            for p in _DEFAULT_PLANS:
                cur.execute("""
                    INSERT INTO subscription_plans
                        (name, price_usd, max_users, max_branches, max_products,
                         has_pos, has_advanced_reports, has_api,
                         support_level, sla_percent)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (name) DO NOTHING
                """, (
                    p["name"], p["price_usd"], p["max_users"], p["max_branches"],
                    p["max_products"], p["has_pos"], p["has_advanced_reports"],
                    p["has_api"], p["support_level"], p["sla_percent"],
                ))
            conn.commit()
            _LOG.info("seed_default_plans() completado.")
        invalidate_prefix("plans:")
    except Exception as e:
        logging.warning("seed_default_plans() error: %s", e)
        raise


@cached(ttl=300)
def get_plan(name: str) -> Optional[Dict[str, Any]]:
    """
    Retorna el plan por nombre, o None si no existe.
    Cacheado 5 minutos.
    """
    _require_postgres()
    try:
        os.environ["TENANT_SCHEMA"] = "public"
        with get_connection() as conn:
            _ensure_plans_table(conn)
            cur = conn.cursor()
            cur.execute("SET search_path = public")
            cur.execute(
                "SELECT id, name, price_usd, max_users, max_branches, "
                "max_products, has_pos, has_advanced_reports, has_api, "
                "support_level, sla_percent, active "
                "FROM subscription_plans WHERE name = %s",
                (name,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return _row_to_dict(row)
    except Exception as e:
        logging.warning("get_plan(%r) error: %s", name, e)
        raise


@cached(ttl=300)
def list_plans() -> List[Dict[str, Any]]:
    """
    Lista todos los planes activos ordenados por precio.
    Cacheado 5 minutos.
    """
    _require_postgres()
    try:
        os.environ["TENANT_SCHEMA"] = "public"
        with get_connection() as conn:
            _ensure_plans_table(conn)
            cur = conn.cursor()
            cur.execute("SET search_path = public")
            cur.execute(
                "SELECT id, name, price_usd, max_users, max_branches, "
                "max_products, has_pos, has_advanced_reports, has_api, "
                "support_level, sla_percent, active "
                "FROM subscription_plans "
                "WHERE active = TRUE "
                "ORDER BY COALESCE(price_usd, 999999)"
            )
            return [_row_to_dict(r) for r in cur.fetchall()]
    except Exception as e:
        logging.warning("list_plans() error: %s", e)
        raise


def assign_plan_to_tenant(tenant_id: str, plan_name: str) -> Dict[str, Any]:
    """
    Asigna un plan a un tenant en public.tenants.

    - Valida que plan_name existe en subscription_plans.
    - Actualiza public.tenants.plan.
    - Invalida caché de tenants.
    - Solo Postgres.

    Returns:
        dict con tenant_id y plan asignado.
    """
    _require_postgres()
    from src.database.connection import _SAFE_SCHEMA_RE
    if not _SAFE_SCHEMA_RE.match(tenant_id):
        raise ValueError(f"tenant_id inválido: {tenant_id!r}")

    try:
        plan = get_plan(plan_name)
        if plan is None:
            raise ValueError(f"Plan no encontrado: {plan_name!r}")

        os.environ["TENANT_SCHEMA"] = "public"
        with get_connection() as conn:
            _ensure_tenants_table(conn)
            cur = conn.cursor()
            cur.execute("SET search_path = public")
            cur.execute(
                "UPDATE tenants SET plan = %s WHERE schema_name = %s",
                (plan_name, tenant_id),
            )
            if cur.rowcount == 0:
                raise ValueError(f"Tenant no encontrado: {tenant_id!r}")
            conn.commit()
            _LOG.info(
                "assign_plan_to_tenant: tenant=%r plan=%r", tenant_id, plan_name
            )

        invalidate_prefix("tenants:")
        return {"tenant_id": tenant_id, "plan": plan_name}

    except (ValueError, RuntimeError):
        raise
    except Exception as e:
        logging.warning(
            "assign_plan_to_tenant(%r, %r) error: %s", tenant_id, plan_name, e
        )
        raise


# ─────────────────────────────────────────────
# Helper interno
# ─────────────────────────────────────────────

def _row_to_dict(row) -> Dict[str, Any]:
    return {
        "id":                   row[0],
        "name":                 row[1],
        "price_usd":            float(row[2]) if row[2] is not None else None,
        "max_users":            row[3],
        "max_branches":         row[4],
        "max_products":         row[5],
        "has_pos":              bool(row[6]),
        "has_advanced_reports": bool(row[7]),
        "has_api":              bool(row[8]),
        "support_level":        row[9],
        "sla_percent":          float(row[10]) if row[10] is not None else None,
        "active":               bool(row[11]),
    }


# ─────────────────────────────────────────────
# Excepción propia
# ─────────────────────────────────────────────

class LimitExceededError(Exception):
    """Se lanza cuando el tenant supera el límite de su plan."""
    def __init__(self, resource: str, current: int, limit: int, plan: str):
        self.resource = resource
        self.current  = current
        self.limit    = limit
        self.plan     = plan
        super().__init__(
            f"Límite de {resource!r} alcanzado para plan {plan!r}: "
            f"{current}/{limit}."
        )

class FeatureNotAvailableError(Exception):
    """Se lanza cuando el tenant intenta usar una feature no incluida en su plan."""
    def __init__(self, feature: str, plan: str):
        self.feature = feature
        self.plan = plan
        super().__init__(f"Feature {feature!r} no disponible para plan {plan!r}.")


# ─────────────────────────────────────────────
# Limits helpers
# ─────────────────────────────────────────────

# Límites canónicos por plan (fuente de verdad = _DEFAULT_PLANS)
_LIMITS_BY_PLAN: Dict[str, Dict[str, Any]] = {
    p["name"]: {
        "users":                p["max_users"],
        "products":             p["max_products"],
        "branches":             p["max_branches"],
        "has_pos":              p["has_pos"],
        "has_advanced_reports": p["has_advanced_reports"],
        "has_api":              p["has_api"],
    }
    for p in _DEFAULT_PLANS
}


def get_plan_limits(plan_name: str) -> Dict[str, Any]:
    """
    Retorna los límites del plan: {"users": N, "products": N, "branches": N, "has_pos": bool, ...}.
    -1 significa ilimitado.
    No requiere Postgres.
    Lanza ValueError si el plan no existe.
    """
    limits = _LIMITS_BY_PLAN.get(plan_name)
    if limits is None:
        raise ValueError(f"Plan desconocido: {plan_name!r}")
    return dict(limits)


def check_feature_access(tenant_id: str, feature: str) -> None:
    """
    Verifica que el tenant tenga acceso a la feature.
    feature ∈ {"pos", "advanced_reports", "api"}
    Lanza FeatureNotAvailableError si no la tiene.
    """
    _VALID_FEATURES = {"pos": "has_pos", "advanced_reports": "has_advanced_reports", "api": "has_api"}
    if feature not in _VALID_FEATURES:
        raise ValueError(f"Feature desconocida: {feature!r}")

    _require_postgres()
    import os as _os
    from src.database.connection import _SAFE_SCHEMA_RE as _re
    if not _re.match(tenant_id):
        raise ValueError(f"tenant_id inválido: {tenant_id!r}")

    _os.environ["TENANT_SCHEMA"] = "public"
    with get_connection() as conn:
        _ensure_tenants_table(conn)
        cur = conn.cursor()
        cur.execute("SET search_path = public")
        cur.execute("SELECT plan FROM tenants WHERE schema_name = %s", (tenant_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Tenant no encontrado: {tenant_id!r}")
        plan_name = row[0]

    limits = get_plan_limits(plan_name)
    feature_key = _VALID_FEATURES[feature]
    if not limits.get(feature_key):
        raise FeatureNotAvailableError(feature, plan_name)
    
    _LOG.info("check_feature_access OK: tenant=%r feature=%r", tenant_id, feature)


def check_tenant_limit(tenant_id: str, resource: str) -> None:
    """
    Verifica que el tenant NO ha superado el límite de 'resource'.
    resource ∈ {"users", "products", "branches"}

    - Consulta public.tenants para obtener el plan del tenant.
    - Cuenta las filas actuales en tenant_id.<tabla>.
    - Si current >= limit (y limit != -1) → lanza LimitExceededError.
    - Solo DB_ENGINE=postgres.
    """
    import os as _os

    _RESOURCE_TABLE = {"users": "users", "products": "productos", "branches": "warehouses"}
    if resource not in _RESOURCE_TABLE:
        raise ValueError(f"Recurso desconocido: {resource!r}")

    _require_postgres()
    from src.database.connection import _SAFE_SCHEMA_RE as _re
    if not _re.match(tenant_id):
        raise ValueError(f"tenant_id inválido: {tenant_id!r}")

    _os.environ["TENANT_SCHEMA"] = "public"
    with get_connection() as conn:
        _ensure_tenants_table(conn)
        cur = conn.cursor()
        cur.execute("SET search_path = public")
        cur.execute("SELECT plan FROM tenants WHERE schema_name = %s", (tenant_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Tenant no encontrado: {tenant_id!r}")
        plan_name = row[0]

    limits = get_plan_limits(plan_name)
    limit = limits[resource]
    if limit == -1:
        return  # ilimitado

    # Contar uso actual en schema del tenant
    table = _RESOURCE_TABLE[resource]
    _os.environ["TENANT_SCHEMA"] = tenant_id
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {tenant_id}.{table}")
        current = int(cur.fetchone()[0])

    if current >= limit:
        raise LimitExceededError(resource, current, limit, plan_name)

    _LOG.info(
        "check_tenant_limit OK: tenant=%r resource=%r %d/%d",
        tenant_id, resource, current, limit,
    )

