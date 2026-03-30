#!/usr/bin/env python3
"""
Script de diagnóstico para probar el login del sistema de inventario.
Ejecuta este script para verificar que el login funciona correctamente.
"""

import sys
import os
from pathlib import Path

# Agregar src al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def test_login():
    """Prueba el sistema de login"""
    print("🔍 DIAGNÓSTICO DEL SISTEMA DE LOGIN")
    print("=" * 50)

    try:
        # Importar módulos necesarios
        print("📦 Importando módulos...")
        from src.database.connection import init_db
        from src.core.auth import ensure_defaults, _fetch_user_with_roles, _verify_password
        from src.services.partners import ensure_schema as ensure_partners_schema
        from src.services.documents import ensure_schema as ensure_doc_series, seed_default_series
        print("✅ Módulos importados correctamente")

        # Inicializar base de datos
        print("🗄️ Inicializando base de datos...")
        init_db()
        ensure_defaults()
        ensure_partners_schema()
        ensure_doc_series()
        seed_default_series()
        print("✅ Base de datos inicializada")

        # Verificar usuario admin
        print("👤 Verificando usuario admin...")
        user = _fetch_user_with_roles('admin')
        if user:
            print(f"✅ Usuario encontrado: {user['username']} - {user['name']}")
            print(f"   Roles: {user['roles']}")

            # Probar contraseña
            valid = _verify_password(user['pass_hash'], 'admin123')
            if valid:
                print("✅ Contraseña 'admin123' es correcta")
            else:
                print("❌ Contraseña incorrecta")
        else:
            print("❌ Usuario admin no encontrado")

        # Probar tkinter
        print("🖥️ Probando tkinter...")
        import tkinter as tk
        root = tk.Tk()
        root.title("Test")
        root.after(100, root.destroy)
        root.mainloop()
        print("✅ Tkinter funciona correctamente")

        # Probar LoginDialog
        print("🔐 Probando LoginDialog...")
        from src.core.auth import LoginDialog
        root = tk.Tk()
        root.title("Test Login")
        dlg = LoginDialog(root)
        if dlg.result:
            print(f"✅ Login exitoso: {dlg.result['username']}")
        else:
            print("⚠️ Login cancelado")
        root.destroy()

        print("\n" + "=" * 50)
        print("🎉 DIAGNÓSTICO COMPLETADO")
        print("\n📋 CREDENCIALES DE ACCESO:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("\n💡 Si el sistema no se abre, ejecuta: python main.py")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login()