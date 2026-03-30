"""
src/services/onboarding.py
===========================
Tarea 6 — Fase 3 SaaS.

Orquestación completa de onboarding de un nuevo tenant.
Solo funciona con DB_ENGINE=postgres.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict

from passlib.context import CryptContext

from src.database.connection import _SAFE_SCHEMA_RE, get_connection
from src.database.tenant_provisioning import (
    _require_postgres,
    _ensure_tenants_table,
    create_tenant_schema,
)
from src.database.plans import assign_plan_to_tenant

_LOG = logging.getLogger(__name__)

_pwd = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.\-]+$")

_NEXT_STEPS = [
    "Inicia sesión en /auth/login con tus credenciales de administrador.",
    "Configura tu catálogo de productos en /productos.",
    "Invita usuarios adicionales desde el panel de administración.",
]


# ─────────────────────────────────────────────
# Rollback helper (interno, sin ACL)
# ─────────────────────────────────────────────

def _raw_drop_schema(conn, tenant_id: str) -> None:
    """
    DROP SCHEMA sin pasar por la capa ACL.
    Solo para uso en rollback de onboarding fallido.
    """
    cur = conn.cursor()
    cur.execute("SET search_path = public")
    cur.execute(f"DROP SCHEMA IF EXISTS {tenant_id} CASCADE")
    cur.execute(
        "UPDATE tenants SET active = FALSE WHERE schema_name = %s",
        (tenant_id,),
    )
    conn.commit()
    _LOG.warning("_raw_drop_schema: schema eliminado por rollback: %s", tenant_id)


# ─────────────────────────────────────────────
# DDL extra: columnas de onboarding en public.tenants
# ─────────────────────────────────────────────

def _ensure_onboarding_columns(conn) -> None:
    """Añade columnas extra a public.tenants si no existen (idempotente)."""
    cur = conn.cursor()
    cur.execute("SET search_path = public")
    extras = [
        ("company_name", "TEXT DEFAULT ''"),
        ("industry",     "TEXT DEFAULT ''"),
        ("currency",     "TEXT DEFAULT 'COP'"),
        ("timezone",     "TEXT DEFAULT 'America/Bogota'"),
    ]
    for col, definition in extras:
        cur.execute(
            f"ALTER TABLE tenants ADD COLUMN IF NOT EXISTS {col} {definition}"
        )
    conn.commit()


# ─────────────────────────────────────────────
# Validación de payload
# ─────────────────────────────────────────────

def _validate_payload(payload: Dict[str, Any]) -> None:
    required = ["tenant_id", "plan", "admin_username", "admin_password", "company_name"]
    for field in required:
        if not payload.get(field):
            raise ValueError(f"Campo requerido: {field!r}")

    if not _SAFE_SCHEMA_RE.match(payload["tenant_id"]):
        raise ValueError(f"tenant_id inválido: {payload['tenant_id']!r}")

    username = payload["admin_username"]
    if len(username) < 3 or len(username) > 50:
        raise ValueError("admin_username debe tener entre 3 y 50 caracteres.")
    if not _USERNAME_RE.match(username):
        raise ValueError("admin_username solo puede contener letras, números, _ . -")

    if len(payload["admin_password"]) < 6:
        raise ValueError("admin_password debe tener al menos 6 caracteres.")

    valid_plans = {"free", "starter", "pro", "enterprise"}
    if payload["plan"] not in valid_plans:
        raise ValueError(
            f"plan inválido: {payload['plan']!r}. Válidos: {sorted(valid_plans)}"
        )


# ─────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────

def onboard_tenant(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orquesta el onboarding completo de un nuevo tenant.

    Pasos:
      1. Validar payload
      2. create_tenant_schema(tenant_id, plan)
      3. assign_plan_to_tenant(tenant_id, plan)
      4. Crear usuario admin en schema del tenant
      5. Insertar rol ADMIN y asignar al usuario
      6. Registrar company_name / industry / currency / timezone
      7. Retornar resultado con next_steps

    Si algún paso falla después del paso 2, hace rollback del schema.
    """
    _validate_payload(payload)   # ValueError primero — antes de tocar la BD
    _require_postgres()

    tenant_id    = payload["tenant_id"]
    plan         = payload["plan"]
    username     = payload["admin_username"]
    password     = payload["admin_password"]
    company_name = payload["company_name"]
    industry     = payload.get("industry", "")
    currency     = payload.get("currency", "COP")
    tz           = payload.get("timezone", "America/Bogota")

    schema_created = False

    try:
        # ── Paso 2: crear schema + DDL ────────────────────────────
        create_tenant_schema(tenant_id, plan)
        schema_created = True

        # ── Paso 3: asignar plan ──────────────────────────────────
        assign_plan_to_tenant(tenant_id, plan)

        # ── Paso 3.5: verificar límite "users" del plan ───────────
        try:
            from src.database.plans import check_tenant_limit, LimitExceededError
            check_tenant_limit(tenant_id, "users")
        except LimitExceededError as e:
            raise RuntimeError(str(e)) from e

        # ── Pasos 4 & 5: usuario admin en schema del tenant ───────
        pass_hash = _pwd.hash(password)
        os.environ["TENANT_SCHEMA"] = tenant_id
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"SET search_path = {tenant_id}, public")

            # Rol ADMIN (idempotente)
            cur.execute(
                "INSERT INTO roles (name) VALUES (%s) "
                "ON CONFLICT (name) DO NOTHING",
                ("ADMIN",),
            )
            cur.execute("SELECT id FROM roles WHERE name = %s", ("ADMIN",))
            role_id = cur.fetchone()[0]

            # Usuario admin (idempotente)
            cur.execute(
                "INSERT INTO users (username, name, pass_hash, active) "
                "VALUES (%s, %s, %s, TRUE) "
                "ON CONFLICT (username) DO NOTHING "
                "RETURNING id",
                (username, company_name, pass_hash),
            )
            row = cur.fetchone()
            if row:
                user_id = row[0]
                cur.execute(
                    "INSERT INTO user_roles (user_id, role_id) "
                    "VALUES (%s, %s) "
                    "ON CONFLICT (user_id, role_id) DO NOTHING",
                    (user_id, role_id),
                )
            conn.commit()

        # ── Paso 6: metadata en public.tenants ────────────────────
        os.environ["TENANT_SCHEMA"] = "public"
        with get_connection() as conn:
            _ensure_tenants_table(conn)
            _ensure_onboarding_columns(conn)
            cur = conn.cursor()
            cur.execute("SET search_path = public")
            cur.execute(
                "UPDATE tenants SET "
                "  company_name = %s, industry = %s, "
                "  currency = %s, timezone = %s "
                "WHERE schema_name = %s",
                (company_name, industry, currency, tz, tenant_id),
            )
            conn.commit()

        # ── Paso 7: retornar resultado ────────────────────────────
        _LOG.info(
            "onboard_tenant OK: tenant=%r plan=%r user=%r",
            tenant_id, plan, username,
        )
        return {
            "tenant_id":      tenant_id,
            "plan":           plan,
            "admin_username": username,
            "onboarded_at":   datetime.now(timezone.utc).isoformat(),
            "next_steps":     _NEXT_STEPS,
        }

    except Exception as e:
        if schema_created:
            logging.warning(
                "onboard_tenant: fallo post-schema — iniciando rollback: %s", e
            )
            try:
                os.environ["TENANT_SCHEMA"] = "public"
                with get_connection() as conn:
                    _raw_drop_schema(conn, tenant_id)
            except Exception as rb_err:
                logging.warning(
                    "onboard_tenant: error en rollback tenant=%r: %s",
                    tenant_id, rb_err,
                )
        raise


def get_onboarding_status(tenant_id: str) -> Dict[str, Any]:
    """
    Verifica el estado de onboarding de un tenant.

    Returns:
        {tenant_id, schema_exists, has_admin, plan, active}
    """
    _require_postgres()
    if not _SAFE_SCHEMA_RE.match(tenant_id):
        raise ValueError(f"tenant_id inválido: {tenant_id!r}")

    try:
        os.environ["TENANT_SCHEMA"] = "public"
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SET search_path = public")

            # ¿Existe el schema?
            cur.execute(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = %s",
                (tenant_id,),
            )
            schema_exists = cur.fetchone() is not None

            # Info del tenant en tabla pública
            cur.execute(
                "SELECT plan, active FROM tenants WHERE schema_name = %s",
                (tenant_id,),
            )
            tenant_row = cur.fetchone()

            has_admin = False
            if schema_exists:
                # ¿Tiene al menos 1 usuario con rol ADMIN?
                cur.execute(
                    f"SELECT COUNT(*) FROM {tenant_id}.user_roles ur "
                    f"JOIN {tenant_id}.roles r ON r.id = ur.role_id "
                    f"WHERE r.name = 'ADMIN'"
                )
                count = cur.fetchone()[0]
                has_admin = count > 0

        return {
            "tenant_id":     tenant_id,
            "schema_exists": schema_exists,
            "has_admin":     has_admin,
            "plan":          tenant_row[0] if tenant_row else None,
            "active":        tenant_row[1] if tenant_row else False,
        }

    except Exception as e:
        logging.warning("get_onboarding_status(%r) error: %s", tenant_id, e)
        raise
