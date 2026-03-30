#!/usr/bin/env python3
"""
Cleanup script - Remove old directory structure after successful migration to /src

Este script elimina los directorios antiguos que ya han sido migrados a /src:
- core/     → src/core/ + src/services/ + src/database/
- app/      → src/app/
- diseño/   → src/app/styles/
- tools/    → (mantener: contiene herramientas de migración)
"""

import os
import shutil
from pathlib import Path

def cleanup_old_folders():
    """Remove old folder structure after migration."""
    
    PROJECT_ROOT = Path(__file__).parent
    folders_to_remove = ["core", "app", "diseño"]
    
    print("=" * 60)
    print("Limpieza de Directorios Antiguos - Migración a /src")
    print("=" * 60)
    
    folders_found = []
    for folder in folders_to_remove:
        folder_path = PROJECT_ROOT / folder
        if folder_path.exists():
            folders_found.append(folder)
            print(f"\n✓ Encontrado: {folder}/")
    
    if not folders_found:
        print("\n✓ No hay directorios antiguos para limpiar.")
        print("  La migración ya fue completada.")
        return
    
    print(f"\n{'─' * 60}")
    print(f"Se eliminarán los siguientes directorios:")
    for folder in folders_found:
        print(f"  • {folder}/")
    print(f"{'─' * 60}")
    
    response = input("\n¿Deseas continuar? (s/n): ").lower().strip()
    
    if response != 's':
        print("\nLimpieza cancelada.")
        return
    
    # Perform cleanup
    for folder in folders_found:
        folder_path = PROJECT_ROOT / folder
        try:
            shutil.rmtree(folder_path)
            print(f"✓ Eliminado: {folder}/")
        except Exception as e:
            print(f"✗ Error al eliminar {folder}/: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Limpieza completada exitosamente")
    print("=" * 60)
    print("\nPróximos pasos:")
    print("  1. Verificar que la aplicación sigue funcionando: python main.py")
    print("  2. Ejecutar tests si existen: python -m pytest tests/")
    print("  3. Confirmar que no falta nada en /src/")
    print("\n")

if __name__ == "__main__":
    cleanup_old_folders()
