"""
src/database/tenant_provisioning.py
====================================
Tarea 2 — Fase 3 SaaS multi-tenant.

Provisioning de schemas PostgreSQL por tenant.
Solo se activa cuando DB_ENGINE == 'postgres'.
No toca connection.py ni init_db().
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.database.connection import DB_ENGINE, _SAFE_SCHEMA_RE, get_connection
from src.core.acl import has_permission
from src.core.caching import cached, invalidate_prefix

_LOG = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────

def _require_postgres() -> None:
    if DB_ENGINE != "postgres":
        raise RuntimeError(
            "tenant_provisioning solo funciona con DB_ENGINE=postgres. "
            f"Motor actual: {DB_ENGINE!r}"
        )


def _validate_tenant_id(tenant_id: str) -> None:
    if not isinstance(tenant_id, str) or not _SAFE_SCHEMA_RE.match(tenant_id):
        raise ValueError(
            f"tenant_id inválido: {tenant_id!r}. "
            "Solo se permiten identificadores PostgreSQL válidos "
            "(letras, dígitos, guiones bajos; máx 63 chars; no empieza con dígito)."
        )


def _ensure_tenants_table(conn) -> None:
    """Crea la tabla public.tenants si no existe (idempotente)."""
    cur = conn.cursor()
    cur.execute("SET search_path = public")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id          SERIAL PRIMARY KEY,
            schema_name TEXT UNIQUE NOT NULL,
            plan        TEXT NOT NULL DEFAULT 'free',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            active      BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS ix_tenants_schema ON tenants(schema_name)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS ix_tenants_active ON tenants(active)"
    )
    cur.execute("""
        ALTER TABLE public.tenants 
        ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMPTZ 
        DEFAULT (NOW() + INTERVAL '14 days')
    """)
    cur.execute("""
        ALTER TABLE public.tenants 
        ADD COLUMN IF NOT EXISTS plan_expires_at TIMESTAMPTZ 
        DEFAULT NULL
    """)
    conn.commit()


def _provision_ddl(conn) -> None:
    """
    Ejecuta el DDL completo del proyecto dentro del schema activo (search_path ya seteado).
    Espejo de init_db() pero en sintaxis PostgreSQL (SERIAL, TIMESTAMPTZ, NUMERIC).
    Idempotente: usa CREATE TABLE IF NOT EXISTS.
    """
    cur = conn.cursor()

    # productos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id        SERIAL PRIMARY KEY,
            codigo    TEXT NOT NULL UNIQUE,
            nombre    TEXT NOT NULL,
            categoria TEXT,
            precio    NUMERIC(14,4) NOT NULL DEFAULT 0,
            cantidad  INTEGER NOT NULL DEFAULT 0,
            avg_cost  NUMERIC(14,4) NOT NULL DEFAULT 0
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prod_codigo    ON productos(codigo)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prod_nombre    ON productos(nombre)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prod_categoria ON productos(categoria)")

    # historial
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id     SERIAL PRIMARY KEY,
            codigo TEXT,
            nombre TEXT,
            accion TEXT,
            fecha  TEXT
        )
    """)

    # partners
    cur.execute("""
        CREATE TABLE IF NOT EXISTS partners (
            id             SERIAL PRIMARY KEY,
            code           TEXT UNIQUE NOT NULL,
            kind           TEXT NOT NULL,
            name           TEXT NOT NULL,
            tax_id         TEXT,
            phone          TEXT,
            email          TEXT,
            address        TEXT,
            city           TEXT,
            notes          TEXT,
            active         BOOLEAN NOT NULL DEFAULT TRUE,
            credit_limit   NUMERIC(14,4) DEFAULT 0.0,
            credit_balance NUMERIC(14,4) DEFAULT 0.0
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_kind   ON partners(kind)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_name   ON partners(name)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_tax_id ON partners(tax_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_partners_active ON partners(active)")

    # users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        SERIAL PRIMARY KEY,
            username  TEXT UNIQUE NOT NULL,
            name      TEXT NOT NULL,
            pass_hash TEXT NOT NULL,
            active    BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)

    # roles / permissions / RBAC
    cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id   SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id          SERIAL PRIMARY KEY,
            code        TEXT UNIQUE NOT NULL,
            description TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            perm_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
            PRIMARY KEY (role_id, perm_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, role_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
            action     TEXT NOT NULL,
            details    TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # documents
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id             SERIAL PRIMARY KEY,
            tipo           TEXT NOT NULL,
            numero         TEXT,
            fecha          TEXT NOT NULL,
            notas          TEXT,
            partner_id     INTEGER REFERENCES partners(id) ON DELETE SET NULL,
            payment_method TEXT,
            amount_paid    NUMERIC(14,4),
            change_given   NUMERIC(14,4),
            estado         TEXT DEFAULT 'ACTIVO'
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_docs_fecha       ON documents(fecha)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_documents_numero  ON documents(numero)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_documents_partner ON documents(partner_id)")

    # document_lines
    cur.execute("""
        CREATE TABLE IF NOT EXISTS document_lines (
            id         SERIAL PRIMARY KEY,
            doc_id     INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            codigo     TEXT NOT NULL,
            qty        NUMERIC(14,4) NOT NULL,
            unit_cost  NUMERIC(14,4),
            unit_price NUMERIC(14,4),
            reason     TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lines_doc    ON document_lines(doc_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lines_codigo ON document_lines(codigo)")

    # stock_movements
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id         SERIAL PRIMARY KEY,
            doc_id     INTEGER REFERENCES documents(id) ON DELETE SET NULL,
            codigo     TEXT NOT NULL,
            qty        NUMERIC(14,4) NOT NULL,
            unit_cost  NUMERIC(14,4),
            unit_price NUMERIC(14,4),
            tipo       TEXT NOT NULL,
            reason     TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_mov_codigo_fecha "
        "ON stock_movements(codigo, created_at)"
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mov_doc ON stock_movements(doc_id)")

    # doc_series
    cur.execute("""
        CREATE TABLE IF NOT EXISTS doc_series (
            id       SERIAL PRIMARY KEY,
            doc_type TEXT NOT NULL,
            series   TEXT NOT NULL,
            prefix   TEXT,
            next_no  INTEGER NOT NULL DEFAULT 1,
            UNIQUE(doc_type, series)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS ix_doc_series_type ON doc_series(doc_type)")

    # clientes (POS legacy)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id       SERIAL PRIMARY KEY,
            nombre   TEXT NOT NULL,
            telefono TEXT,
            saldo    NUMERIC(14,4) NOT NULL DEFAULT 0.0
        )
    """)

    # cash_sessions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cash_sessions (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER NOT NULL REFERENCES users(id),
            opening_amount  NUMERIC(14,4) NOT NULL DEFAULT 0.0,
            closing_amount  NUMERIC(14,4),
            opened_at       TIMESTAMPTZ NOT NULL,
            closed_at       TIMESTAMPTZ,
            arqueo_declared NUMERIC(14,4),
            arqueo_notes    TEXT
        )
    """)

    # cash_movements
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cash_movements (
            id          SERIAL PRIMARY KEY,
            session_id  INTEGER NOT NULL REFERENCES cash_sessions(id) ON DELETE CASCADE,
            type        TEXT NOT NULL,
            amount      NUMERIC(14,4) NOT NULL,
            description TEXT,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    conn.commit()


# ─────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────

def create_tenant_schema(tenant_id: str, plan: str = "free") -> Dict[str, Any]:
    """
    Crea el schema PostgreSQL para un tenant y lo registra en public.tenants.

    Idempotente: si el schema ya existe, no falla.
    Solo funciona con DB_ENGINE=postgres.

    Args:
        tenant_id: Identificador del tenant (= nombre del schema).
        plan:      Plan de suscripción ('free', 'pro', 'enterprise').

    Returns:
        dict con: tenant_id, schema_name, plan, created_at, already_existed.
    """
    _require_postgres()
    _validate_tenant_id(tenant_id)

    try:
        # 1. Trabajar en schema public para crear la tabla tenants y el schema nuevo
        os.environ["TENANT_SCHEMA"] = "public"
        with get_connection() as conn:
            _ensure_tenants_table(conn)
            cur = conn.cursor()
            cur.execute("SET search_path = public")

            # ¿Ya existe el schema?
            cur.execute(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = %s",
                (tenant_id,),
            )
            already_existed = cur.fetchone() is not None

            if not already_existed:
                cur.execute(f"CREATE SCHEMA {tenant_id}")
                conn.commit()
                _LOG.info("Schema creado: %s", tenant_id)

            # Registrar en public.tenants (idempotente via ON CONFLICT)
            cur.execute(
                "INSERT INTO tenants (schema_name, plan, trial_ends_at) "
                "VALUES (%s, %s, NOW() + INTERVAL '14 days') "
                "ON CONFLICT (schema_name) DO NOTHING",
                (tenant_id, plan),
            )
            conn.commit()

            cur.execute(
                "SELECT id, plan, created_at FROM tenants WHERE schema_name = %s",
                (tenant_id,),
            )
            row = cur.fetchone()

        # 2. Provisionar el DDL dentro del schema del tenant
        os.environ["TENANT_SCHEMA"] = tenant_id
        with get_connection() as conn:
            _provision_ddl(conn)
            _LOG.info("DDL provisionado en schema: %s", tenant_id)

        invalidate_prefix("tenants:")

        return {
            "tenant_id":      tenant_id,
            "schema_name":    tenant_id,
            "plan":           row[1] if row else plan,
            "created_at":     str(row[2]) if row else datetime.now(timezone.utc).isoformat(),
            "already_existed": already_existed,
        }

    except Exception as e:
        logging.warning("create_tenant_schema(%r) error: %s", tenant_id, e)
        raise


def drop_tenant_schema(tenant_id: str, requesting_user_id: int) -> bool:
    """
    Elimina el schema de un tenant (DROP SCHEMA … CASCADE).
    Marca tenant como active=False en public.tenants.
    NO borra el registro de auditoría.

    Requiere permiso 'tenant.admin'.

    Args:
        tenant_id:           Schema a eliminar.
        requesting_user_id:  ID del usuario que solicita la operación.

    Returns:
        True si se eliminó, False si el schema no existía.
    """
    _require_postgres()
    _validate_tenant_id(tenant_id)

    if not has_permission(requesting_user_id, "tenant.admin"):
        raise PermissionError(
            f"Usuario {requesting_user_id} no tiene permiso 'tenant.admin'."
        )

    try:
        os.environ["TENANT_SCHEMA"] = "public"
        with get_connection() as conn:
            _ensure_tenants_table(conn)
            cur = conn.cursor()
            cur.execute("SET search_path = public")

            # ¿Existe el schema?
            cur.execute(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = %s",
                (tenant_id,),
            )
            if cur.fetchone() is None:
                _LOG.warning("drop_tenant_schema: schema no existe: %s", tenant_id)
                return False

            cur.execute(f"DROP SCHEMA {tenant_id} CASCADE")
            cur.execute(
                "UPDATE tenants SET active = FALSE WHERE schema_name = %s",
                (tenant_id,),
            )
            conn.commit()
            _LOG.warning(
                "Schema eliminado: %s (usuario_id=%s)", tenant_id, requesting_user_id
            )

        invalidate_prefix("tenants:")
        return True

    except PermissionError:
        raise
    except Exception as e:
        logging.warning("drop_tenant_schema(%r) error: %s", tenant_id, e)
        raise


@cached(ttl=30)
def list_tenants() -> List[Dict[str, Any]]:
    """
    Lista todos los tenants registrados en public.tenants.
    Resultado cacheado 30 segundos.

    Returns:
        Lista de dicts con: id, schema_name, plan, created_at, active.
    """
    _require_postgres()

    try:
        os.environ["TENANT_SCHEMA"] = "public"
        with get_connection() as conn:
            _ensure_tenants_table(conn)
            cur = conn.cursor()
            cur.execute("SET search_path = public")
            cur.execute(
                "SELECT id, schema_name, plan, created_at, active "
                "FROM tenants ORDER BY created_at"
            )
            rows = cur.fetchall()
            return [
                {
                    "id":          r[0],
                    "schema_name": r[1],
                    "plan":        r[2],
                    "created_at":  str(r[3]),
                    "active":      r[4],
                }
                for r in rows
            ]
    except Exception as e:
        logging.warning("list_tenants() error: %s", e)
        raise
