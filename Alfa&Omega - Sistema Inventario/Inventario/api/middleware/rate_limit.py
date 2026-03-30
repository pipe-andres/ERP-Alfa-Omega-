"""
api/middleware/rate_limit.py
=============================
Tarea 18 — Rate limiting por tenant/API-key.

- Límites in-memory (thread-safe), reset cada hora.
- Lee X-API-Key header o extrae tenant_id del JWT.
- Rutas excluidas: /health, /docs, /openapi.json, /redoc.
- Supera límite → 429 con Retry-After.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from typing import Dict, Tuple

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.services.api_keys import validate_api_key

_LOG = logging.getLogger(__name__)

_SECRET_KEY: str = os.getenv(
    "SECRET_KEY",
    "dev-only-secret-change-in-production-64chars-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
)
_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

# Límites por plan (requests / hora). 0 = sin límite.
_PLAN_LIMITS: Dict[str, int] = {
    "free":        100,
    "starter":   1_000,
    "pro":      10_000,
    "enterprise":    0,   # sin límite
}
_DEFAULT_LIMIT = 100

_EXCLUDED: frozenset[str] = frozenset({
    "/health", "/docs", "/openapi.json", "/redoc",
})

# {identity_key: (count, window_start_ts)}
_buckets: Dict[str, Tuple[int, float]] = {}
_lock = threading.Lock()
_WINDOW = 3600.0  # 1 hora en segundos


def _get_limit(plan: str) -> int:
    return _PLAN_LIMITS.get(plan.lower(), _DEFAULT_LIMIT)


def _check_and_increment(identity: str, limit: int) -> Tuple[bool, int]:
    """
    Retorna (allowed, retry_after_seconds).
    Si limit==0 → siempre permitido (enterprise).
    """
    if limit == 0:
        return True, 0
    now = time.time()
    with _lock:
        count, window_start = _buckets.get(identity, (0, now))
        if now - window_start >= _WINDOW:
            count, window_start = 0, now
        count += 1
        _buckets[identity] = (count, window_start)
        if count > limit:
            retry_after = int(_WINDOW - (now - window_start)) + 1
            return False, retry_after
    return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Por cada request (no excluido):
    1. Lee X-API-Key → valida via api_keys.validate_api_key.
    2. Si no hay X-API-Key → extrae tenant_id del JWT (sin rechazar).
    3. Aplica bucket in-memory. 429 si supera límite.
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _EXCLUDED:
            return await call_next(request)

        identity = "anonymous"
        plan = "free"

        # ── 1. Intentar X-API-Key ────────────────────────────────
        api_key_raw = request.headers.get("X-API-Key", "").strip()
        if api_key_raw:
            key_info = validate_api_key(api_key_raw)
            if key_info:
                identity = f"apikey:{key_info['tenant_id']}"
                plan = "pro"   # API keys de producción → plan pro por defecto
            else:
                logging.warning(
                    "RateLimitMiddleware: API key inválida desde %s",
                    request.client.host if request.client else "?",
                )
                return JSONResponse(
                    status_code=401,
                    content={"detail": "API key inválida."},
                )

        # ── 2. Fallback a tenant_id del JWT ─────────────────────
        if identity == "anonymous":
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth.removeprefix("Bearer ").strip()
                try:
                    payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
                    tenant_id = payload.get("tenant_id", "")
                    if tenant_id:
                        identity = f"jwt:{tenant_id}"
                        plan = payload.get("plan", "free")
                except JWTError:
                    pass  # TenantMiddleware lo rechazará si es obligatorio

        # ── 3. Aplicar rate limit ───────────────────────────────
        limit = _get_limit(plan)
        allowed, retry_after = _check_and_increment(identity, limit)
        if not allowed:
            _LOG.warning(
                "RateLimitMiddleware: 429 identity=%r plan=%r retry_after=%ss",
                identity, plan, retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
