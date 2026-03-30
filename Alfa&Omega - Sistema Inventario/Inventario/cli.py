#!/usr/bin/env python3
"""
CLI para tareas comunes del Sistema de Inventario.

Comandos:
  run-gui      - Inicia la aplicación GUI
  migrate-db   - Migra datos de SQLite a MySQL
  ensure-rbac  - Asegura roles, permisos y usuario admin

Ejemplo:
  python cli.py run-gui
  python cli.py ensure-rbac
"""

import argparse
import sys
import logging
from pathlib import Path

# Agregar src al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.core import configure_logging


def run_gui():
    """Inicia la aplicación GUI."""
    from main import main as run_main
    run_main()


def migrate_db():
    """Migra base de datos de SQLite a MySQL."""
    try:
        from tools.migrate_sqlite_to_mysql import main as migrate_main
        migrate_main()
    except ImportError as e:
        print(f"Error: No se encontró el migrador. {e}")
        sys.exit(1)


def ensure_rbac():
    """Asegura que RBAC esté configurado correctamente."""
    try:
        from tools.rbac_fix import ensure_rbac as ensure_rbac_main
        ensure_rbac_main()
        print("RBAC verificado/corregido exitosamente.")
    except ImportError as e:
        print(f"Error: No se encontró rbac_fix. {e}")
        sys.exit(1)


def main(argv=None):
    """Punto de entrada principal de la CLI."""
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Herramientas del Sistema de Inventario - Alfa & Omega"
    )
    
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("run-gui", help="Inicia la aplicación de escritorio (Tkinter)")
    sub.add_parser("migrate-db", help="Migra datos desde SQLite a MySQL")
    sub.add_parser("ensure-rbac", help="Asegura roles/permisos/usuario admin en la BD")

    args = parser.parse_args(argv)
    configure_logging()

    if args.command == "run-gui":
        run_gui()
    elif args.command == "migrate-db":
        migrate_db()
    elif args.command == "ensure-rbac":
        ensure_rbac()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
