#!/usr/bin/env python3
"""
Alfa & Omega - Sistema de Inventario
Punto de entrada principal para la aplicación GUI.

Este archivo importa la estructura modular reorganizada en /src.
"""

import sys
import tkinter as tk
from pathlib import Path

# Agregar src al path para importaciones
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.database.connection import init_db
from src.core.auth import ensure_defaults
from src.services.partners import ensure_schema as ensure_partners_schema
from src.database.settings import ensure_schema as ensure_settings_schema
from src.core import configure_logging

# Importar la aplicación GUI (pendiente de crear)
try:
    from src.app.main_window import InventarioApp
except ImportError:
    print("ERROR: No se encontró src/app/main_window.py")
    print("Por favor, copia y adapta app/gui.py a src/app/main_window.py con los imports actualizados")
    sys.exit(1)


def main():
    """Inicializa la aplicación y abre la ventana principal."""
    configure_logging()
    
    # Inicializar base de datos
    init_db()
    ensure_defaults()
    ensure_partners_schema()
    ensure_settings_schema()

    # Crear y ejecutar interfaz
    root = tk.Tk()
    app = InventarioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
