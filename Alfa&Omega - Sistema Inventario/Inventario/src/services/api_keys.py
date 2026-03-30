"""
src/services/api_keys.py
=========================
Tarea 18 — Gestión de API keys.

- Genera keys aleatorias (32 bytes hex)
- Guarda solo el hash SHA-256 en BD
- Nunca retorna el hash, solo ID/nombre/estado
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import date
from typing import Any, Dict, List, Optional

from src.database.connection import get_connection
from src.core.caching import cached, invalidate_prefix

_LOG = logging.getLogger(__name__)
_PREFIX = "api_keys:"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def generate_api_key(tenant_id: str, nombre: str = "") -> str:
    """
    Genera una API key aleatoria para el tenant.
    Persiste en BD solo el hash SHA-256.
    Retorna la key en claro — solo se muestra esta vez.
    """
    key = secrets.token_hex(32)          # 64 chars hex, 256 bits
    key_hash = _sha256(key)
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO api_keys (key_hash, tenant_id, nombre) VALUES (?, ?, ?)",
                (key_hash, tenant_id, nombre or ""),
            )
            conn.commit()
        invalidate_prefix(_PREFIX + tenant_id)
        _LOG.info("API key generada para tenant=%r nombre=%r", tenant_id, nombre)
        return key
    except Exception as e:
        logging.warning("generate_api_key error: %s", e)
        raise


def validate_api_key(key: str) -> Optional[Dict[str, Any]]:
    """
    Valida una API key.
    Retorna {tenant_id, nombre} si activa, None si inválida/revocada.
    Actualiza last_used y requests_today/total.
    """
    key_hash = _sha256(key)
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, tenant_id, nombre, activo FROM api_keys WHERE key_hash=?",
                (key_hash,),
            )
            row = cur.fetchone()
            if not row:
                return None
            key_id, tenant_id, nombre, activo = row[0], row[1], row[2], int(row[3])
            if not activo:
                return None
            # Actualizar métricas de uso
            today = date.today().isoformat()
            cur.execute(
                """UPDATE api_keys
                   SET last_used=?,
                       requests_today = CASE
                           WHEN substr(last_used,1,10)=? THEN requests_today+1
                           ELSE 1
                       END,
                       requests_total = requests_total+1
                   WHERE id=?""",
                (today, today, key_id),
            )
            conn.commit()
        return {"tenant_id": tenant_id, "nombre": nombre}
    except Exception as e:
        logging.warning("validate_api_key error: %s", e)
        return None


def revoke_api_key(key_id: int) -> None:
    """Desactiva una API key por ID."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE api_keys SET activo=0 WHERE id=?", (int(key_id),)
            )
            if cur.rowcount == 0:
                raise ValueError(f"API key id={key_id} no encontrada.")
            cur.execute("SELECT tenant_id FROM api_keys WHERE id=?", (int(key_id),))
            row = cur.fetchone()
            conn.commit()
        if row:
            invalidate_prefix(_PREFIX + row[0])
        _LOG.info("API key revocada: id=%s", key_id)
    except Exception as e:
        logging.warning("revoke_api_key error: %s", e)
        raise


@cached(ttl=60)
def list_api_keys(tenant_id: str) -> List[Dict[str, Any]]:
    """
    Lista las API keys de un tenant.
    NO retorna key_hash — solo metadatos.
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT id, tenant_id, nombre, activo,
                          created_at, last_used,
                          requests_today, requests_total
                   FROM api_keys WHERE tenant_id=? ORDER BY created_at""",
                (tenant_id,),
            )
            return [
                {
                    "id":             r[0],
                    "tenant_id":      r[1],
                    "nombre":         r[2],
                    "activo":         bool(r[3]),
                    "created_at":     r[4],
                    "last_used":      r[5],
                    "requests_today": r[6],
                    "requests_total": r[7],
                }
                for r in cur.fetchall()
            ]
    except Exception as e:
        logging.warning("list_api_keys error: %s", e)
        raise
