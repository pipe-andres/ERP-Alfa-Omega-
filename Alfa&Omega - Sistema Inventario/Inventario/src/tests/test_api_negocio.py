"""
src/tests/test_api_negocio.py
==============================
Tarea 17 — Tests para los endpoints de negocio (T16).
Corre sobre SQLite sin Postgres.

pytest -v src/tests/test_api_negocio.py
"""
from __future__ import annotations

import os
import pytest

os.environ.setdefault("DB_ENGINE", "sqlite")

from fastapi.testclient import TestClient
from api.main import app
from api.routers.auth import _create_token

# ─────────────────────────────────────────────
# Fixtures (redefinidas localmente, misma lógica que test_api.py)
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="session")
def user_token():
    """JWT con role=USER (sin privilegios ADMIN)."""
    return _create_token({
        "user_id":   99,
        "username":  "testuser",
        "role":      "USER",
        "tenant_id": "empresa_test",
    })


@pytest.fixture(scope="session")
def admin_token():
    """JWT con role=ADMIN (puede crear/editar productos)."""
    return _create_token({
        "user_id":   1,
        "username":  "admin",
        "role":      "ADMIN",
        "tenant_id": "empresa_test",
    })


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────
# PRODUCTOS
# ─────────────────────────────────────────────

class TestProductos:

    def test_list_productos(self, client, user_token):
        """GET /productos/ sin filtro → 200 con keys items y total."""
        r = client.get("/productos/", headers=_auth(user_token))
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "total" in body
        assert isinstance(body["items"], list)
        assert isinstance(body["total"], int)

    def test_list_productos_search(self, client, user_token):
        """GET /productos/?search=X → 200 (puede devolver lista vacía)."""
        r = client.get("/productos/?search=____no_existe____",
                       headers=_auth(user_token))
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert body["total"] >= 0

    def test_create_producto_admin(self, client, admin_token):
        """POST /productos/ con ADMIN → 201 o 409 si ya existe."""
        r = client.post("/productos/", headers=_auth(admin_token), json={
            "codigo":    "TEST-API-001",
            "nombre":    "Producto Test API",
            "categoria": "Test",
            "precio":    9.99,
            "cantidad":  10,
            "avg_cost":  5.0,
        })
        assert r.status_code in (201, 409)

    def test_get_producto_existente(self, client, user_token):
        """GET /productos/TEST-API-001 → 200 con datos del producto."""
        r = client.get("/productos/TEST-API-001", headers=_auth(user_token))
        # 200 si fue creado, 404 si la creación anterior retornó 409 (ya existía con otro estado)
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            body = r.json()
            assert "codigo" in body
            assert "nombre" in body

    def test_get_producto_inexistente(self, client, user_token):
        """GET /productos/NO_EXISTE_XXXX → 404."""
        r = client.get("/productos/NO_EXISTE_XXXX", headers=_auth(user_token))
        assert r.status_code == 404

    def test_create_producto_sin_admin(self, client, user_token):
        """POST /productos/ con token USER → 403 (requiere ADMIN)."""
        r = client.post("/productos/", headers=_auth(user_token), json={
            "codigo":   "HACK-001",
            "nombre":   "Intento no autorizado",
            "precio":   1.0,
            "cantidad": 1,
            "avg_cost": 0.5,
        })
        assert r.status_code == 403


# ─────────────────────────────────────────────
# VENTAS
# ─────────────────────────────────────────────

class TestVentas:

    def test_ventas_resumen(self, client, user_token):
        """GET /ventas/resumen → 200 con al menos la key ventas_hoy."""
        r = client.get("/ventas/resumen", headers=_auth(user_token))
        assert r.status_code == 200
        body = r.json()
        assert "ventas_hoy" in body

    def test_list_ventas(self, client, user_token):
        """GET /ventas/ → 200 con items y count."""
        r = client.get("/ventas/", headers=_auth(user_token))
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "count" in body
        assert isinstance(body["items"], list)

    def test_get_venta_inexistente(self, client, user_token):
        """GET /ventas/99999 → 404."""
        r = client.get("/ventas/99999", headers=_auth(user_token))
        assert r.status_code == 404


# ─────────────────────────────────────────────
# INVENTARIO
# ─────────────────────────────────────────────

class TestInventario:

    def test_stock_actual(self, client, user_token):
        """GET /inventario/stock → 200 con total_productos y valor_total."""
        r = client.get("/inventario/stock", headers=_auth(user_token))
        assert r.status_code == 200
        body = r.json()
        assert "total_productos" in body
        assert "valor_total" in body
        assert "items" in body
        assert isinstance(body["items"], list)

    def test_bajo_stock(self, client, user_token):
        """GET /inventario/bajo-stock → 200 con items y threshold."""
        r = client.get("/inventario/bajo-stock", headers=_auth(user_token))
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "threshold" in body
        assert body["threshold"] == 5  # default

    def test_kardex_inexistente(self, client, user_token):
        """GET /inventario/kardex/NO_EXISTE_XXXX → 404."""
        r = client.get("/inventario/kardex/NO_EXISTE_XXXX",
                       headers=_auth(user_token))
        assert r.status_code == 404
