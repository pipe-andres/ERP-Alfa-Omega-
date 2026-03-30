"""
src/tests/test_limits.py
=========================
Tarea 10 — Tests de enforcement de límites por plan.
Sin Postgres — usa _DEFAULT_PLANS y mocks.

pytest -v src/tests/test_limits.py
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("DB_ENGINE", "sqlite")

from src.database.plans import (
    LimitExceededError,
    FeatureNotAvailableError,
    get_plan_limits,
    check_tenant_limit,
    check_feature_access,
)


class TestGetPlanLimits:

    def test_free_plan_limits(self):
        limits = get_plan_limits("free")
        assert limits["users"]    == 1
        assert limits["products"] == 100

    def test_enterprise_no_limits(self):
        limits = get_plan_limits("enterprise")
        assert limits["users"]    == -1   # ilimitado
        assert limits["products"] == -1   # ilimitado

    def test_unknown_plan_raises(self):
        with pytest.raises(ValueError, match="Plan desconocido"):
            get_plan_limits("platinum")

    def test_get_plan_limits_includes_features(self):
        limits = get_plan_limits("free")
        assert limits["has_pos"] is False
        assert limits["branches"] == 1

    def test_starter_has_pos(self):
        limits = get_plan_limits("starter")
        assert limits["has_pos"] is True


class TestCheckTenantLimit:

    def _mock_conn(self, plan: str, current_count: int):
        """Devuelve un mock de get_connection() → cursor con plan y count."""
        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [(plan,), (current_count,)]
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: mock_conn
        mock_conn.__exit__  = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cur
        return mock_conn

    def test_check_limit_ok(self):
        """Tenant free con 0 usuarios — no lanza."""
        conn = self._mock_conn("free", 0)
        with patch("src.database.plans._require_postgres"):
            with patch("src.database.plans.get_connection", return_value=conn):
                with patch("src.database.plans._ensure_tenants_table"):
                    check_tenant_limit("empresa_ok", "users")  # no lanza

    def test_check_limit_exceeded(self):
        """Tenant free ya tiene 1 usuario (límite) — lanza LimitExceededError."""
        conn = self._mock_conn("free", 1)
        with patch("src.database.plans._require_postgres"):
            with patch("src.database.plans.get_connection", return_value=conn):
                with patch("src.database.plans._ensure_tenants_table"):
                    with pytest.raises(LimitExceededError) as exc_info:
                        check_tenant_limit("empresa_full", "users")

        err = exc_info.value
        assert err.resource == "users"
        assert err.current  == 1
        assert err.limit    == 1
        assert err.plan     == "free"

    def test_enterprise_unlimited_never_raises(self):
        """Enterprise (-1) nunca lanza aunque tenga miles de usuarios."""
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = ("enterprise",)
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: mock_conn
        mock_conn.__exit__  = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cur
        with patch("src.database.plans._require_postgres"):
            with patch("src.database.plans.get_connection", return_value=mock_conn):
                with patch("src.database.plans._ensure_tenants_table"):
                    check_tenant_limit("empresa_enterprise", "users")  # no lanza

    def test_unknown_resource_raises(self):
        with patch("src.database.plans._require_postgres"):
            with pytest.raises(ValueError, match="Recurso desconocido"):
                check_tenant_limit("any", "unknown_resource")

class TestCheckFeatureAccess:

    def _mock_conn(self, plan: str):
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (plan,)
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: mock_conn
        mock_conn.__exit__  = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cur
        return mock_conn

    def test_feature_not_available(self):
        conn = self._mock_conn("free")
        with patch("src.database.plans._require_postgres"):
            with patch("src.database.plans.get_connection", return_value=conn):
                with patch("src.database.plans._ensure_tenants_table"):
                    with pytest.raises(FeatureNotAvailableError) as exc_info:
                        check_feature_access("empresa_free", "pos")
        assert exc_info.value.feature == "pos"
        assert exc_info.value.plan == "free"

    def test_feature_available(self):
        conn = self._mock_conn("pro")
        with patch("src.database.plans._require_postgres"):
            with patch("src.database.plans.get_connection", return_value=conn):
                with patch("src.database.plans._ensure_tenants_table"):
                    check_feature_access("empresa_pro", "api")  # no lanza
