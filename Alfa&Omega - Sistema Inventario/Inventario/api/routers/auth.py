"""
api/routers/auth.py
====================
Tarea 3B — Fase 3 SaaS.

Endpoints de autenticación JWT.
Reutiliza src/core/auth.py para verificación de credenciales.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field

# ── Reutilizar lógica existente de src/core/auth.py ──────────────────────────
from src.core.auth import _fetch_user_with_roles, _verify_password
from src.database.connection import _SAFE_SCHEMA_RE

_LOG = logging.getLogger(__name__)

# ── Configuración JWT (desde .env con fallback seguro para dev) ───────────────
_SECRET_KEY: str = os.getenv(
    "SECRET_KEY",
    "dev-only-secret-change-in-production-64chars-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
)
_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

router = APIRouter()
_bearer = HTTPBearer(auto_error=False)


# ─────────────────────────────────────────────
# Schemas Pydantic
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=63)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos


class MeResponse(BaseModel):
    user_id: int
    username: str
    role: str
    tenant_id: str


# ─────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────

def _create_token(payload: Dict[str, Any]) -> str:
    """Firma un JWT con SECRET_KEY."""
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=_EXPIRE_MINUTES)
    return jwt.encode(data, _SECRET_KEY, algorithm=_ALGORITHM)


def _decode_token(token: str) -> Dict[str, Any]:
    """Decodifica y valida un JWT. Lanza JWTError si inválido/expirado."""
    return jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Dict[str, Any]:
    """
    Dependencia FastAPI: extrae y valida el Bearer token.
    Retorna el payload del JWT.
    Lanza 401 si el token falta, es inválido o está expirado.
    """
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return _decode_token(creds.credentials)
    except JWTError as e:
        logging.warning("get_current_user JWTError: %s", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=200,
    summary="Iniciar sesión",
    description="Autentica a un usuario verificando sus credenciales (usuario, contraseña y tenant_id). Retorna un token JWT válido (access_token) si las credenciales son correctas."
)
async def login(body: LoginRequest) -> TokenResponse:
    """
    Autentica usuario y retorna JWT.
    El mensaje de error es genérico para no revelar qué campo falló.
    """
    _INVALID = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Validar tenant_id
    if not _SAFE_SCHEMA_RE.match(body.tenant_id):
        logging.warning("login: tenant_id inválido para usuario=%r", body.username)
        raise _INVALID

    # 2. Buscar usuario (reutiliza src/core/auth.py)
    try:
        user = _fetch_user_with_roles(body.username)
    except Exception as e:
        logging.warning("login: _fetch_user_with_roles error: %s", e)
        raise _INVALID

    if not user:
        logging.warning("login: usuario no encontrado o inactivo: %r", body.username)
        raise _INVALID

    # 3. Verificar password (reutiliza src/core/auth.py)
    try:
        ok = _verify_password(user["pass_hash"], body.password)
    except Exception as e:
        logging.warning("login: _verify_password error: %s", e)
        raise _INVALID

    if not ok:
        logging.warning("login: password incorrecto para usuario=%r", body.username)
        raise _INVALID

    # 4. Emitir JWT
    role = (user.get("roles") or ["USER"])[0]
    token = _create_token({
        "user_id":   user["id"],
        "username":  user["username"],
        "role":      role,
        "tenant_id": body.tenant_id,
    })

    _LOG.info("login OK: username=%r tenant=%r", body.username, body.tenant_id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=_EXPIRE_MINUTES * 60,
    )


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Información del usuario actual",
    description="Retorna los datos principales (claims) del usuario autenticado mediante el token JWT activo."
)
async def me(
    payload: Annotated[Dict[str, Any], Depends(get_current_user)],
) -> MeResponse:
    """Retorna los claims del token activo (sin exp)."""
    return MeResponse(
        user_id=payload["user_id"],
        username=payload["username"],
        role=payload["role"],
        tenant_id=payload["tenant_id"],
    )
