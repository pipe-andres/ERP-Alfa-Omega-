#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test: Simplemente intenta crear una instancia minimal de InventarioApp
"""

import sys
import os
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_instantiation():
    """Intenta crear InventarioApp"""
    
    print("=" * 80)
    print("PRUEBA DE INSTANCIACIÓN DE INVENTARIOAPP")
    print("=" * 80)
    
    try:
        print("\n1. Creando ventana root Tk...")
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana
        print("   ✓ Ventana root creada")
        
        print("\n2. Importando InventarioApp...")
        from src.app.main_window import InventarioApp
        print("   ✓ InventarioApp importado")
        
        print("\n3. Creando instancia de InventarioApp...")
        # Esto abrirá el LoginDialog
        app = InventarioApp(root)
        print("   ✓ Instancia creada")
        
        print("\n✅ INSTANCIACIÓN EXITOSA")
        return True
        
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: {str(e)}")
        print("\nTRACEBACK COMPLETO:")
        traceback.print_exc()
        return False
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    success = test_instantiation()
    sys.exit(0 if success else 1)
