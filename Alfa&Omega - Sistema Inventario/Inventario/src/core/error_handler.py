# src/core/error_handler.py
"""
Sistema robusto de manejo de errores a nivel de aplicación.
Garantiza que NUNCA haya fallos silenciosos.
"""

import logging
import traceback
import sys
from datetime import datetime
from typing import Optional, Callable, Any
from pathlib import Path

# Crear directorio de logs si no existe
from config import settings
LOG_DIR = settings.LOG_DIR
LOG_DIR.mkdir(exist_ok=True)

# Logger configurado
logger = logging.getLogger("AlfaOmega")
logger.setLevel(logging.DEBUG)

# Handler de archivo (todo se registra)
file_handler = logging.FileHandler(LOG_DIR / "sistema.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_formatter)

# Handler de consola (solo warnings y superiores)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


class AlfaOmegaException(Exception):
    """Excepción base para el sistema."""
    pass


class DataIntegrityException(AlfaOmegaException):
    """Error crítico: integridad de datos comprometida."""
    pass


class SecurityException(AlfaOmegaException):
    """Error de seguridad: acceso no autorizado o validación fallida."""
    pass


class DatabaseException(AlfaOmegaException):
    """Error de base de datos que requiere intervención."""
    pass


def log_error(
    error: Exception,
    context: Optional[dict] = None,
    level: str = "ERROR"
) -> None:
    """
    Registra un error de forma estructurada.
    
    Args:
        error: Excepción capturada
        context: Contexto adicional (usuario, acción, etc.)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    message = f"{type(error).__name__}: {str(error)}"
    
    if context:
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        message += f" | CONTEXT: {context_str}"
    
    # Log con traceback
    if level == "CRITICAL":
        logger.critical(message, exc_info=True)
    elif level == "ERROR":
        logger.error(message, exc_info=True)
    elif level == "WARNING":
        logger.warning(message, exc_info=True)
    else:
        logger.info(message, exc_info=False)


def safe_execute(
    func: Callable,
    *args,
    error_message: str = "Error ejecutando operación",
    fallback: Any = None,
    critical: bool = False,
    log_context: Optional[dict] = None,
    **kwargs
) -> Any:
    """
    Ejecuta una función con manejo seguro de errores.
    
    Args:
        func: Función a ejecutar
        error_message: Mensaje de error a mostrar
        fallback: Valor a retornar si falla
        critical: Si True, los errores se loguean como CRÍTICOS
        log_context: Contexto para logging
        
    Returns:
        Resultado de func o fallback si falla
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        level = "CRITICAL" if critical else "ERROR"
        log_error(e, context=log_context, level=level)
        
        if critical:
            raise AlfaOmegaException(error_message) from e
        
        return fallback


def validate_database_integrity() -> bool:
    """
    Valida la integridad de la base de datos.
    Retorna True si está OK, False si hay problemas.
    """
    try:
        from src.database.connection import get_connection
        
        with get_connection() as conn:
            cur = conn.cursor()
            
            # Ejecutar PRAGMA integrity_check para SQLite
            cur.execute("PRAGMA integrity_check")
            result = cur.fetchone()
            
            if result and result[0] == "ok":
                logger.info("Database integrity check: PASSED")
                return True
            else:
                logger.critical(f"Database integrity check: FAILED - {result}")
                return False
                
    except Exception as e:
        log_error(e, context={"operation": "integrity_check"}, level="CRITICAL")
        return False


def get_logger() -> logging.Logger:
    """Retorna el logger configurado."""
    return logger
