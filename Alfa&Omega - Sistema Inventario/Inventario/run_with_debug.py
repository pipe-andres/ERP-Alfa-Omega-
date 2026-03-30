#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para iniciar el sistema con debug del login
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(__file__))

print("🚀 INICIANDO SISTEMA CON DEBUG")
print("=" * 60)

try:
    print("\n1️⃣ Importando módulos principales...")
    import tkinter as tk
    from src.app.main_window import InventarioApp
    from src.database.connection import init_db
    from src.core.auth import ensure_defaults
    
    print("   ✅ Módulos importados correctamente")
    
    print("\n2️⃣ Inicializando base de datos...")
    init_db()
    ensure_defaults()
    print("   ✅ Base de datos lista")
    
    print("\n3️⃣ Creando ventana principal...")
    root = tk.Tk()
    print("   ✅ Ventana Tkinter creada")
    
    print("\n4️⃣ Iniciando aplicación Inventario...")
    app = InventarioApp(root)
    print("   ✅ Aplicación creada exitosamente")
    
    print("\n5️⃣ Iniciando loop de eventos Tkinter...")
    root.mainloop()
    print("   ℹ️  Aplicación cerrada por el usuario")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTRACEBACK COMPLETO:")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Sistema cerrado correctamente")
