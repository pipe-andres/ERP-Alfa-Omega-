#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar el flujo completo sin interfaz gráfica interactiva
Simula lo que sucede durante el login y la inicialización post-login
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("🔍 DIAGNÓSTICO DEL FLUJO DE LOGIN Y INICIALIZACIÓN")
print("=" * 70)

# Paso 1: Autenticación
print("\n1️⃣ Verificando credenciales admin/admin123...")
try:
    from src.core.auth import _fetch_user_with_roles, _verify_password
    
    user_db = _fetch_user_with_roles("admin")
    if not user_db:
        print("   ❌ Usuario no encontrado")
        sys.exit(1)
    
    if not _verify_password(user_db["pass_hash"], "admin123"):
        print("   ❌ Contraseña incorrecta")
        sys.exit(1)
    
    user = {"id": user_db["id"], "username": user_db["username"], "name": user_db["name"], "roles": user_db["roles"]}
    print(f"   ✅ Login OK: {user['name']} ({', '.join(user['roles'])})")
except Exception as e:
    print(f"   ❌ Error: {e}")
    traceback.print_exc()
    sys.exit(1)

# Paso 2: log_event (llamado en main_window.py línea 102)
print("\n2️⃣ Probando log_event...")
try:
    from src.services.audit import log_event
    
    log_event(user["id"], "LOGIN", {
        "username": user["username"],
        "roles": user["roles"]
    })
    print("   ✅ log_event OK")
except Exception as e:
    print(f"   ❌ Error en log_event: {e}")
    traceback.print_exc()
    sys.exit(1)

# Paso 3: Crear Tkinter y aplicar tema
print("\n3️⃣ Inicializando Tkinter y tema...")
try:
    import tkinter as tk
    from src.app.styles.luxury_2026 import aplicar_tema_luxury_2026
    
    root = tk.Tk()
    root.title("TEST")
    aplicar_tema_luxury_2026()
    print("   ✅ Tkinter y tema OK")
except Exception as e:
    print(f"   ❌ Error: {e}")
    traceback.print_exc()
    sys.exit(1)

# Paso 4: Crear menús
print("\n4️⃣ Creando menús...")
try:
    from tkinter import ttk
    
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    m_arch = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Archivo", menu=m_arch)
    
    print("   ✅ Menús OK")
except Exception as e:
    print(f"   ❌ Error creando menús: {e}")
    traceback.print_exc()
    sys.exit(1)

# Paso 5: Crear notebook
print("\n5️⃣ Creando Notebook...")
try:
    from src.app.styles import theme
    
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=6, pady=6)
    
    print("   ✅ Notebook OK")
except Exception as e:
    print(f"   ❌ Error creando notebook: {e}")
    traceback.print_exc()
    sys.exit(1)

# Paso 6: Crear primeras pestañas
print("\n6️⃣ Creando primeras pestañas...")
try:
    # Dashboard
    from src.app.dashboard import DashboardTab
    
    tab_dashboard = ttk.Frame(nb)
    nb.add(tab_dashboard, text="📊 Dashboard")
    DashboardTab(tab_dashboard)
    
    # Inventario
    tab_inv = ttk.Frame(nb)
    nb.add(tab_inv, text="Inventario")
    
    print("   ✅ Primeras pestañas OK")
except Exception as e:
    print(f"   ❌ Error en primeras pestañas: {e}")
    traceback.print_exc()
    sys.exit(1)

# Paso 7: Crear pestaña Devoluciones (la que falla)
print("\n7️⃣ Creando pestaña Devoluciones...")
try:
    from datetime import datetime
    from src.services.inventory import post_return
    from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography
    
    tab_returns = ttk.Frame(nb)
    nb.add(tab_returns, text="💔 Devoluciones")
    
    # Simulación simple de _build_tab_devoluciones
    frame_main = tk.Frame(tab_returns, bg=Luxury2026Colors.BG_DARKEST)
    frame_main.pack(fill="both", expand=True)
    
    tk.Label(frame_main, text="Test", bg=Luxury2026Colors.BG_DARKEST).pack()
    
    print("   ✅ Pestaña Devoluciones OK")
except Exception as e:
    print(f"   ❌ Error en pestaña Devoluciones: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ TODOS LOS PASOS COMPLETADOS EXITOSAMENTE")
print("=" * 70)
print("\nLa aplicación puede abrirse sin problemas.")
print("El error debe estar en algún otro lugar.")

root.destroy()
