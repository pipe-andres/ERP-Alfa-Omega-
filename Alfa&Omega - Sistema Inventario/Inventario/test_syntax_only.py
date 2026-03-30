#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test sin interfaz: Solo verifica que la clase pueda importarse
"""

import sys
import os
import traceback

# Agregar la ruta para importar src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Verifica que todos los módulos se importen correctamente"""
    print("=" * 80)
    print("VERIFICACIÓN DE IMPORTS Y SINTAXIS")
    print("=" * 80)
    
    try:
        print("\n✓ Importando módulos...")
        
        print("  - sqlite3...", end=" ")
        import sqlite3
        print("✓")
        
        print("  - tkinter...", end=" ")
        import tkinter as tk
        from tkinter import ttk
        print("✓")
        
        print("  - src.core.database...", end=" ")
        from src.core.database import Database
        print("✓")
        
        print("  - src.core.auth...", end=" ")
        from src.core.auth import LoginDialog, User
        print("✓")
        
        print("  - src.app.main_window...", end=" ")
        from src.app.main_window import InventarioApp
        print("✓")
        
        print("\n✅ TODOS LOS IMPORTS CORRECTOS")
        
        # Verificar que InventarioApp tenga el método __init__
        print("\nVerificando estructura de InventarioApp...")
        print(f"  - __init__: {'✓' if hasattr(InventarioApp, '__init__') else '✗'}")
        print(f"  - _build_tab_devoluciones: {'✓' if hasattr(InventarioApp, '_build_tab_devoluciones') else '✗'}")
        print(f"  - _build_tab_descuentos: {'✓' if hasattr(InventarioApp, '_build_tab_descuentos') else '✗'}")
        print(f"  - _build_tab_margenes: {'✓' if hasattr(InventarioApp, '_build_tab_margenes') else '✗'}")
        print(f"  - _build_tab_reportes_avanzados: {'✓' if hasattr(InventarioApp, '_build_tab_reportes_avanzados') else '✗'}")
        
        print("\n✅ VERIFICACIÓN COMPLETADA EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
