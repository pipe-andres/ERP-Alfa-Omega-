"""
api/middleware/tenant.py
=========================
Tarea 3C — Fase 3 SaaS.

TenantMiddleware: extrae tenant_id del JWT Bearer y lo inyecta
en tenant_schema_var (ContextVar) para que get_connection() Postgres
use el schema correcto sin tocar os.environ.
"""
from __future__ import annotations

import logging
import os

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.core.context import tenant_schema_var
from src.database.connection import _SAFE_SCHEMA_RE

_LOG = logging.getLogger(__name__)

_SECRET_KEY: str = os.getenv(
    "SECRET_KEY",
    "dev-only-secret-change-in-production-64chars-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
)
_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

# Rutas que NO requieren JWT / tenant
_EXCLUDED: frozenset[str] = frozenset({
    "/health",
    "/auth/login",
    "/plans/",         # público — no requiere JWT
    "/onboarding/register",  # público — tenant aún no existe
    "/docs",
    "/openapi.json",
    "/redoc",
})


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Por cada request:
    1. Si la ruta está excluida → pass through.
    2. Extrae Bearer token → 401 si falta.
    3. Decodifica JWT         → 401 si inválido/expirado.
    4. Valida tenant_id       → 403 si no pasa _SAFE_SCHEMA_RE.
    5. Inyecta en ContextVar  → llama call_next → reset en finally.
    """

    async def dispatch(self, request: Request, call_next):
        # ── Rutas excluidas ──────────────────────────────────────
        if request.url.path in _EXCLUDED:
            return await call_next(request)

        # ── Extraer Bearer token ─────────────────────────────────
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Token requerido"},
            )
        token = auth_header.removeprefix("Bearer ").strip()

        # ── Decodificar JWT ──────────────────────────────────────
        try:
            payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        except JWTError as exc:
            logging.warning("TenantMiddleware: JWT inválido (%s)", type(exc).__name__)
            return JSONResponse(
                status_code=401,
                content={"detail": "Token inválido"},
            )

        # ── Validar tenant_id ────────────────────────────────────
        tenant_id: str = payload.get("tenant_id", "")
        if not tenant_id or not _SAFE_SCHEMA_RE.match(tenant_id):
            logging.warning(
                "TenantMiddleware: tenant_id inválido=%r path=%s",
                tenant_id, request.url.path,
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Tenant inválido"},
            )

        # ── Inyectar ContextVar y procesar request ───────────────
        ctx_token = tenant_schema_var.set(tenant_id)
        try:
            return await call_next(request)
        except Exception as exc:
            logging.warning("TenantMiddleware: error en handler: %s", exc)
            raise
        finally:
            tenant_schema_var.reset(ctx_token)  # restaura el valor anterior
