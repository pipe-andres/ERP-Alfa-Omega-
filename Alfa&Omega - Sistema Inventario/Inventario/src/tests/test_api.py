"""
src/tests/test_api.py
======================
Tarea 8 — Suite de tests para la API Fase 3.
No requiere Postgres — corre contra SQLite + fallbacks.

pytest -v src/tests/test_api.py
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import patch

# Garantizar que el motor es SQLite para todos los tests
os.environ.setdefault("DB_ENGINE", "sqlite")

from fastapi.testclient import TestClient
from api.main import app
from api.routers.auth import _create_token


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """TestClient de la app completa. Lifespan ejecuta init_db() en SQLite."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="session")
def user_token():
    """JWT de usuario normal (role=USER, tenant=empresa_test)."""
    return _create_token({
        "user_id":   99,
        "username":  "testuser",
        "role":      "USER",
        "tenant_id": "empresa_test",
    })


@pytest.fixture(scope="session")
def superadmin_token():
    """JWT de super-admin (role=ADMIN, tenant_id=public)."""
    return _create_token({
        "user_id":   1,
        "username":  "admin",
        "role":      "ADMIN",
        "tenant_id": "public",
    })


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

class TestAuth:

    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "engine" in body

    def test_login_valid(self, client):
        """Login con usuario real de la BD SQLite dev."""
        r = client.post("/auth/login", json={
            "username":  "admin",
            "password":  "admin123",
            "tenant_id": "empresa_test",
        })
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0

    def test_login_invalid(self, client):
        """Password incorrecto → 401 con mensaje genérico."""
        r = client.post("/auth/login", json={
            "username":  "admin",
            "password":  "WRONG_PASSWORD",
            "tenant_id": "empresa_test",
        })
        assert r.status_code == 401
        # mensaje NUNCA revela qué campo falló
        assert "Credenciales" in r.json()["detail"]

    def test_me_valid(self, client, user_token):
        """GET /auth/me con token válido → 200 con claims."""
        r = client.get("/auth/me", headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["username"] == "testuser"
        assert body["role"] == "USER"
        assert body["tenant_id"] == "empresa_test"
        assert "exp" not in body  # campo exp NUNCA se expone


# ─────────────────────────────────────────────
# PLANS
# ─────────────────────────────────────────────

class TestPlans:

    def test_list_plans_public(self, client):
        """GET /plans/ sin token → 200, retorna los 4 planes."""
        r = client.get("/plans/")
        assert r.status_code == 200
        plans = r.json()
        assert len(plans) == 4
        names = [p["name"] for p in plans]
        assert "free" in names
        assert "starter" in names
        assert "pro" in names
        assert "enterprise" in names
        # free plan → price_usd = 0 o None (depende de fallback)
        free = next(p for p in plans if p["name"] == "free")
        assert free["price_usd"] == 0.0 or free["price_usd"] is None

    def test_list_plans_order(self, client):
        """Planes vienen ordenados: free → starter → pro → enterprise."""
        r = client.get("/plans/")
        assert r.status_code == 200
        names = [p["name"] for p in r.json()]
        expected = ["free", "starter", "pro", "enterprise"]
        assert names == expected


# ─────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────

class TestMiddleware:

    def test_excluded_routes_no_token(self, client):
        """Rutas excluidas responden sin requerir token."""
        excluded = [
            ("GET",  "/health"),
            ("POST", "/auth/login"),
            ("GET",  "/plans/"),
            ("GET",  "/docs"),
        ]
        for method, path in excluded:
            r = client.request(method, path)
            # Cualquier respuesta es válida EXCEPTO 401
            assert r.status_code != 401, (
                f"{method} {path} no debería requerir token, "
                f"pero retornó {r.status_code}"
            )

    def test_protected_requires_token(self, client):
        """GET /auth/me sin token → 401."""
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_invalid_tenant_in_token(self, client):
        """
        JWT con tenant_id inválido (no pasa _SAFE_SCHEMA_RE) → 403.
        El middleware bloquea antes de llegar al handler.
        """
        bad_token = _create_token({
            "user_id":   42,
            "username":  "evil",
            "role":      "USER",
            "tenant_id": "../../evil",  # inválido para _SAFE_SCHEMA_RE
        })
        r = client.get("/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
        assert r.status_code == 403


# ─────────────────────────────────────────────
# ONBOARDING
# ─────────────────────────────────────────────

class TestOnboarding:

    def test_register_missing_fields(self, client):
        """POST /onboarding/register sin body → 422 (validación Pydantic)."""
        r = client.post("/onboarding/register", json={})
        assert r.status_code == 422

    def test_register_short_password(self, client):
        """admin_password < 8 chars → 422 (Field min_length=8)."""
        r = client.post("/onboarding/register", json={
            "tenant_id":      "empresa_x",
            "plan":           "free",
            "admin_username": "adminx",
            "admin_password": "123",        # < 8 — debe fallar en schema
            "company_name":   "Empresa X",
        })
        assert r.status_code == 422
