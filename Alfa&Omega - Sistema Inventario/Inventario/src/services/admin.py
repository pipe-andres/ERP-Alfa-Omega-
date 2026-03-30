"""
src/services/admin.py
======================
Tarea 9 — Fase 3 SaaS.

Lógica de negocio del Panel Super-Admin.
Solo funciona plenamente con DB_ENGINE=postgres.
En SQLite, las métricas de uso retornan 0 (graceful degradation).
"""
from __future__ import annotations

import logging
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.database.connection import DB_ENGINE, _SAFE_SCHEMA_RE, get_connection
from src.database.tenant_provisioning import (
    _ensure_tenants_table,
    _require_postgres,
    list_tenants,
)
from src.database.plans import assign_plan_to_tenant
from api.routers.auth import _SECRET_KEY, _ALGORITHM
from jose import jwt

_LOG = logging.getLogger(__name__)

VALID_PLANS = {"free", "starter", "pro", "enterprise"}


# ─────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────

def _count_in_schema(conn, tenant_id: str, table: str) -> int:
    """Cuenta filas en una tabla del schema del tenant. Retorna 0 si falla."""
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {tenant_id}.{table}")
        row = cur.fetchone()
        return int(row[0]) if row else 0
    except Exception as e:
        logging.warning("_count_in_schema(%r, %r) error: %s", tenant_id, table, e)
        return 0


# ─────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────

def get_all_tenants() -> List[Dict[str, Any]]:
    """
    Lista todos los tenants con: tenant_id, plan, active, onboarded_at.
    Reutiliza list_tenants() cacheado 30s.
    """
    rows = list_tenants()
    return [
        {
            "tenant_id":    r["schema_name"],
            "plan":         r["plan"],
            "active":       r["active"],
            "onboarded_at": r.get("created_at", ""),
        }
        for r in rows
    ]


def get_tenant_detail(tenant_id: str) -> Dict[str, Any]:
    """
    Detalle de un tenant + métricas de uso (productos, ventas, usuarios).
    En SQLite los contadores son 0 (degradación graciosa).
    """
    if not _SAFE_SCHEMA_RE.match(tenant_id):
        raise ValueError(f"tenant_id inválido: {tenant_id!r}")

    rows = list_tenants()
    match = next((r for r in rows if r["schema_name"] == tenant_id), None)
    if not match:
        raise LookupError(f"Tenant no encontrado: {tenant_id!r}")

    n_prods = n_sales = n_users = 0
    if DB_ENGINE == "postgres":
        try:
            os.environ["TENANT_SCHEMA"] = tenant_id
            with get_connection() as conn:
                n_prods = _count_in_schema(conn, tenant_id, "productos")
                n_sales = _count_in_schema(conn, tenant_id, "ventas")
                n_users = _count_in_schema(conn, tenant_id, "users")
        except Exception as e:
            logging.warning("get_tenant_detail(%r) usage query error: %s", tenant_id, e)

    return {
        "tenant_id":    match["schema_name"],
        "plan":         match["plan"],
        "active":       match["active"],
        "onboarded_at": match.get("created_at", ""),
        "usage": {
            "products": n_prods,
            "sales":    n_sales,
            "users":    n_users,
        },
    }


def patch_tenant(tenant_id: str, active: Optional[bool], plan: Optional[str]) -> Dict[str, Any]:
    """
    Cambia el estado (active) y/o el plan de un tenant.
    Al menos uno de los dos debe estar presente.
    """
    if not _SAFE_SCHEMA_RE.match(tenant_id):
        raise ValueError(f"tenant_id inválido: {tenant_id!r}")
    if active is None and plan is None:
        raise ValueError("Se requiere al menos 'active' o 'plan' en el body.")
    if plan is not None and plan not in VALID_PLANS:
        raise ValueError(f"plan inválido: {plan!r}. Válidos: {sorted(VALID_PLANS)}")

    _require_postgres()

    os.environ["TENANT_SCHEMA"] = "public"
    with get_connection() as conn:
        _ensure_tenants_table(conn)
        cur = conn.cursor()
        cur.execute("SET search_path = public")

        cur.execute("SELECT id FROM tenants WHERE schema_name = %s", (tenant_id,))
        if not cur.fetchone():
            raise LookupError(f"Tenant no encontrado: {tenant_id!r}")

        if active is not None:
            cur.execute(
                "UPDATE tenants SET active = %s WHERE schema_name = %s",
                (active, tenant_id),
            )
        conn.commit()

    if plan is not None:
        assign_plan_to_tenant(tenant_id, plan)

    _LOG.info("patch_tenant: %r active=%r plan=%r", tenant_id, active, plan)
    return {"tenant_id": tenant_id, "active": active, "plan": plan}


def get_global_metrics() -> Dict[str, Any]:
    """
    Métricas globales del SaaS:
      total_tenants, active_tenants, tenants_by_plan, new_last_30d,
      mrr, churn_last_30d, new_last_7d, trial_tenants.
    """
    _require_postgres()
    os.environ["TENANT_SCHEMA"] = "public"
    with get_connection() as conn:
        _ensure_tenants_table(conn)
        cur = conn.cursor()
        cur.execute("SET search_path = public")

        cur.execute("SELECT COUNT(*) FROM tenants")
        total = int(cur.fetchone()[0])

        cur.execute("SELECT COUNT(*) FROM tenants WHERE active = TRUE")
        active = int(cur.fetchone()[0])

        cur.execute("SELECT plan, COUNT(*) FROM tenants GROUP BY plan")
        by_plan: Dict[str, int] = {row[0]: int(row[1]) for row in cur.fetchall()}

        cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)
        cur.execute(
            "SELECT COUNT(*) FROM tenants WHERE created_at >= %s",
            (cutoff_30d,),
        )
        new_30d = int(cur.fetchone()[0])

        # Nuevas métricas:
        
        # MRR
        cur.execute("""
            SELECT COALESCE(SUM(sp.price_usd), 0.0) 
            FROM tenants t
            JOIN subscription_plans sp ON t.plan = sp.name
            WHERE t.active = TRUE
        """)
        mrr = float(cur.fetchone()[0])
        
        # Churn last 30d
        try:
            cur.execute("""
                SELECT COUNT(*) FROM tenants 
                WHERE active = FALSE AND updated_at >= NOW() - INTERVAL '30 days'
            """)
            churn_last_30d = int(cur.fetchone()[0])
        except Exception as e:
            # Fallback a 0 si public.tenants aún no tiene la columna updated_at
            conn.rollback()
            logging.warning("get_global_metrics churn query error (¿falta updated_at?): %s", e)
            churn_last_30d = 0

        # Nuevos últimos 7 días
        cur.execute("""
            SELECT COUNT(*) FROM tenants 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        new_last_7d = int(cur.fetchone()[0])

        # Trial tenants
        cur.execute("""
            SELECT COUNT(*) FROM tenants 
            WHERE plan = 'free' AND active = TRUE
        """)
        trial_tenants = int(cur.fetchone()[0])

    return {
        "total_tenants":   total,
        "active_tenants":  active,
        "tenants_by_plan": {
            "free":       by_plan.get("free", 0),
            "starter":    by_plan.get("starter", 0),
            "pro":        by_plan.get("pro", 0),
            "enterprise": by_plan.get("enterprise", 0),
        },
        "new_last_30d":   new_30d,
        "mrr":            mrr,
        "churn_last_30d": churn_last_30d,
        "new_last_7d":    new_last_7d,
        "trial_tenants":  trial_tenants,
    }


def get_audit_log(tenant_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retorna entradas del audit_log en schema público.
    Filtra por tenant_id si se proporciona.
    """
    _require_postgres()
    limit = max(1, min(limit, 500))
    os.environ["TENANT_SCHEMA"] = "public"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SET search_path = public")
        if tenant_id:
            cur.execute(
                "SELECT id, user_id, action, details, created_at "
                "FROM audit_log WHERE tenant_id = %s "
                "ORDER BY created_at DESC LIMIT %s",
                (tenant_id, limit),
            )
        else:
            cur.execute(
                "SELECT id, user_id, action, details, created_at "
                "FROM audit_log "
                "ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
        rows = cur.fetchall()

    return [
        {
            "id":         r[0],
            "user_id":    r[1],
            "action":     r[2],
            "details":    r[3],
            "created_at": str(r[4]),
        }
        for r in rows
    ]


def impersonate_tenant(tenant_id: int, admin_user_id: str) -> Dict[str, Any]:
    """
    Fuerza la sesión como un tenant específico para soporte.
    Genera un token temporal y lo registra en el audit_log público.
    """
    _require_postgres()
    
    os.environ["TENANT_SCHEMA"] = "public"
    with get_connection() as conn:
        _ensure_tenants_table(conn)
        cur = conn.cursor()
        cur.execute("SET search_path = public")
        
        # 1. Verificar tenant activo
        cur.execute("SELECT active, schema_name FROM tenants WHERE id = %s", (tenant_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Tenant no encontrado: {tenant_id!r}")
        if not row[0]:
            raise ValueError(f"El tenant {tenant_id!r} no está activo.")
            
        real_schema_name = row[1]
            
        # 2. Registrar en audit_log antes de generar el token
        detalles_json = json.dumps({"tenant_id": tenant_id})
        try:
            # Dado que la firma asume un str para user_id pero la BD lo guarda como INT, 
            # asume un casteo en Postgres o se almacena de forma compatible.
            cur.execute("""
                INSERT INTO audit_log (user_id, action, details)
                VALUES (%s, %s, %s)
            """, (admin_user_id, "IMPERSONATE", detalles_json))
        except Exception as e:
            conn.rollback()
            _LOG.warning("impersonate_tenant audit_log insert error: %s", e)
            raise
            
        conn.commit()

    # 3. Emitir JWT
    payload = {
        "sub": admin_user_id,
        "tenant_id": real_schema_name,  # Debe ir el nombre del schema
        "role": "ADMIN",
        "impersonated_by": admin_user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    
    # Creamos el token directamente para respetar 'exp'
    token = jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)
    
    _LOG.info("Tenant impersonado: tenant_id=%r admin_user_id=%r", tenant_id, admin_user_id)
    return {
        "token": token,
        "tenant_id": tenant_id,
        "expires_in": 3600
    }


def check_tenant_trial(tenant_id: str) -> Dict[str, Any]:
    """
    Retorna estado de trial y expiración de un tenant.
    Solo funciona con DB_ENGINE=postgres.

    Returns:
        dict con: in_trial, trial_ends_at, trial_days_left, plan_active.
    """
    if not _SAFE_SCHEMA_RE.match(tenant_id):
        raise ValueError(f"tenant_id inválido: {tenant_id!r}")

    _require_postgres()

    os.environ["TENANT_SCHEMA"] = "public"
    try:
        with get_connection() as conn:
            _ensure_tenants_table(conn)
            cur = conn.cursor()
            cur.execute("SET search_path = public")

            cur.execute("""
                SELECT
                    (trial_ends_at > NOW())                                           AS in_trial,
                    trial_ends_at,
                    GREATEST(0, EXTRACT(DAY FROM (trial_ends_at - NOW())))::int       AS trial_days_left,
                    (active AND (plan_expires_at IS NULL OR plan_expires_at > NOW())) AS plan_active
                FROM tenants
                WHERE schema_name = %s
            """, (tenant_id,))

            row = cur.fetchone()
            if not row:
                raise LookupError(f"Tenant {tenant_id!r} no encontrado.")

            in_trial, trial_ends_at, trial_days_left, plan_active = row

            return {
                "in_trial":        bool(in_trial),
                "trial_ends_at":   trial_ends_at.isoformat() if trial_ends_at else None,
                "trial_days_left": int(trial_days_left) if trial_days_left else 0,
                "plan_active":     bool(plan_active),
            }
    except (LookupError, ValueError):
        raise
    except Exception as e:
        logging.warning("check_tenant_trial(%r) error: %s", tenant_id, e)
        raise
