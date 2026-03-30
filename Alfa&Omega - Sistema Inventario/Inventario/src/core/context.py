"""
src/core/context.py
====================
Variables de contexto por request (ContextVar).
Módulo neutral importable desde cualquier capa sin importaciones circulares.
"""
from contextvars import ContextVar

# Schema del tenant activo en este request/coroutine.
# Default "public" es seguro si no hay middleware activo (modo dev SQLite).
tenant_schema_var: ContextVar[str] = ContextVar("tenant_schema", default="public")
