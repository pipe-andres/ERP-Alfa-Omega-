"""Core package utilities.

Provee `configure_logging()` para centralizar la configuración de logging
en el proyecto. Llamar temprano (p. ej. en `main.py` o `cli.py`).
"""
import logging


def configure_logging(level=logging.INFO, fmt='%(levelname)s: %(message)s'):
    """Configura logging básico si aún no hay handlers registrados.

    Esto evita configurar logging múltiples veces cuando se importan
    módulos desde tests o herramientas.
    """
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level, format=fmt)


__all__ = ["configure_logging"]
