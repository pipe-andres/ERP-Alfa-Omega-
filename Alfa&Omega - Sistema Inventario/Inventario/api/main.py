"""
api/main.py
===========
Tarea 3A — Fase 3 SaaS multi-tenant.

FastAPI application entry point.
- Lifespan: init_db (SQLite) o validar conexión (Postgres)
- CORS configurado vía settings.ENV
- /health endpoint
- Routers auth y tenants incluidos cuando existan (Tareas 3B y 3C)
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.middleware.tenant import TenantMiddleware

from config import settings
from src.database.connection import DB_ENGINE, get_connection

_LOG = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown logic."""
    if DB_ENGINE == "sqlite":
        try:
            from src.database.connection import init_db
            init_db()
            _LOG.info("SQLite init_db() completado.")
        except Exception as e:
            logging.warning("lifespan init_db() error: %s", e)
            raise
    else:
        # Postgres: validar conexión y sembrar planes
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1")
            _LOG.info("Conexión PostgreSQL verificada.")
        except Exception as e:
            logging.warning("lifespan postgres check error: %s", e)
            raise
        try:
            from src.database.plans import seed_default_plans
            seed_default_plans()
            _LOG.info("Planes de suscripción sembrados.")
        except Exception as e:
            logging.warning("lifespan seed_default_plans error: %s", e)

    yield  # ← app corriendo

    _LOG.info("API shutdown.")


# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────

app = FastAPI(
    title="Alfa & Omega ERP — API",
    description="SaaS multi-tenant para perfumería colombiana. Fase 3.",
    version="3.0.0",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────

_ORIGINS_DEV = ["*"]
_ORIGINS_PROD = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGINS_DEV if settings.ENV == "dev" else _ORIGINS_PROD,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)

try:
    from api.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
    _LOG.info("RateLimitMiddleware registrado.")
except ImportError:
    _LOG.warning("api/middleware/rate_limit.py no encontrado.")

# ─────────────────────────────────────────────
# Routers (3B y 3C — se incluyen cuando existen)
# ─────────────────────────────────────────────

try:
    from api.routers.auth import router as auth_router
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    _LOG.info("Router /auth cargado.")
except ImportError:
    _LOG.warning("api/routers/auth.py no encontrado — pendiente Tarea 3B.")

try:
    from api.routers.tenants import router as tenants_router
    app.include_router(tenants_router, prefix="/tenants", tags=["tenants"])
    _LOG.info("Router /tenants cargado.")
except ImportError:
    _LOG.warning("api/routers/tenants.py no encontrado — pendiente Tarea 3C.")

try:
    from api.routers.plans import router as plans_router
    app.include_router(plans_router)  # sin prefix: /plans/ y /tenants/{id}/plan
    _LOG.info("Router plans cargado.")
except ImportError:
    _LOG.warning("api/routers/plans.py no encontrado.")

try:
    from api.routers.onboarding import router as onboarding_router
    app.include_router(onboarding_router, prefix="/onboarding", tags=["onboarding"])
    _LOG.info("Router /onboarding cargado.")
except ImportError:
    _LOG.warning("api/routers/onboarding.py no encontrado.")

try:
    from api.routers.admin import router as admin_router
    app.include_router(admin_router, prefix="/admin")
    _LOG.info("Router /admin cargado.")
except ImportError:
    _LOG.warning("api/routers/admin.py no encontrado.")

try:
    from api.routers.productos import router as productos_router
    app.include_router(productos_router)
    _LOG.info("Router /productos cargado.")
except ImportError:
    _LOG.warning("api/routers/productos.py no encontrado.")

try:
    from api.routers.ventas import router as ventas_router
    app.include_router(ventas_router)
    _LOG.info("Router /ventas cargado.")
except ImportError:
    _LOG.warning("api/routers/ventas.py no encontrado.")

try:
    from api.routers.inventario import router as inventario_router
    app.include_router(inventario_router)
    _LOG.info("Router /inventario cargado.")
except ImportError:
    _LOG.warning("api/routers/inventario.py no encontrado.")

# ─────────────────────────────────────────────
# Endpoints base
# ─────────────────────────────────────────────

@app.get("/health", tags=["infra"])
async def health() -> dict:
    """Health check: estado del servidor y motor de BD activo."""
    return {"status": "ok", "engine": DB_ENGINE, "env": settings.ENV}
