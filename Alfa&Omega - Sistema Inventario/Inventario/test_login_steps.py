#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar paso a paso qué sucede después del login
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("🔍 PRUEBA PASO A PASO DEL LOGIN")
print("=" * 60)

# Paso 1: Importar y probar LoginDialog
print("\n1️⃣ Probando LoginDialog...")
try:
    import tkinter as tk
    from src.core.auth import LoginDialog
    
    root = tk.Tk()
    root.withdraw()
    
    print("   ℹ️  Por favor ingresa: admin / admin123 y presiona Entrar")
    print("   (Si no quieres, presiona Cancelar)")
    
    dlg = LoginDialog(root)
    
    if not dlg.result:
        print("   ℹ️  Login cancelado por usuario")
        root.destroy()
        sys.exit(0)
    
    user = dlg.result
    print(f"   ✅ Login exitoso!")
    print(f"      - Usuario: {user['username']}")
    print(f"      - Nombre: {user['name']}")
    print(f"      - Roles: {user['roles']}")
    
except Exception as e:
    print(f"   ❌ Error en LoginDialog: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Paso 2: Probar log_event
print("\n2️⃣ Probando log_event...")
try:
    from src.services.audit import log_event
    
    log_event(user["id"], "LOGIN_TEST", {
        "username": user["username"], 
        "roles": user["roles"]
    })
    print("   ✅ log_event funcionó correctamente")
except Exception as e:
    print(f"   ❌ Error en log_event: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Paso 3: Probar cambio de título
print("\n3️⃣ Probando cambio de título...")
try:
    title = f"Inventario — {user['name']} ({', '.join(user['roles'])})"
    root.deiconify()
    root.title(title)
    print(f"   ✅ Título actualizado: {title}")
except Exception as e:
    print(f"   ❌ Error cambiando título: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Paso 4: Probar crear frame para dashboard
print("\n4️⃣ Probando creación de frames...")
try:
    from tkinter import ttk
    from src.app.styles.luxury_2026 import aplicar_tema_luxury_2026
    
    aplicar_tema_luxury_2026()
    
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True)
    
    frame_test = ttk.Frame(nb)
    nb.add(frame_test, text="Test")
    
    print("   ✅ Frames creados correctamente")
except Exception as e:
    print(f"   ❌ Error creando frames: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Todos los pasos completados exitosamente")
print("=" * 60)

# Dejar la ventana abierta para inspeccionar
print("\nVentana abierta. Presiona Ctrl+C para cerrar.")
try:
    root.mainloop()
except KeyboardInterrupt:
    print("\nCerrando...")
    root.destroy()
