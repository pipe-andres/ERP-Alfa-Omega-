"""
Módulo de acceso a datos y configuración de base de datos.
"""

from .connection import (
    get_connection,
    init_db,
    init_rbac,
    DB_ENGINE,
    DB_PATH,
)

__all__ = [
    "get_connection",
    "init_db",
    "init_rbac",
    "DB_ENGINE",
    "DB_PATH",
]
