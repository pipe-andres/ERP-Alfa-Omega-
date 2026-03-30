#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para diagnosticar problemas de login en el sistema
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("🔍 DIAGNÓSTICO DE LOGIN")
print("=" * 60)

# 1. Verificar conexión a BD
print("\n1️⃣ Verificando conexión a base de datos...")
try:
    from src.database.connection import get_connection
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        print(f"   ✅ Conexión OK - {count} usuarios en BD")
except Exception as e:
    print(f"   ❌ Error de conexión: {e}")
    sys.exit(1)

# 2. Verificar que existe usuario admin
print("\n2️⃣ Verificando usuario admin...")
try:
    from src.database.connection import get_connection
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, name, active FROM users WHERE username=?", ("admin",))
        u = cur.fetchone()
        if u:
            print(f"   ✅ Usuario encontrado:")
            print(f"      - ID: {u[0]}")
            print(f"      - Username: {u[1]}")
            print(f"      - Name: {u[2]}")
            print(f"      - Active: {u[3]}")
        else:
            print(f"   ❌ Usuario 'admin' NO EXISTE")
except Exception as e:
    print(f"   ❌ Error consultando usuario: {e}")

# 3. Verificar contraseña
print("\n3️⃣ Verificando contraseña...")
try:
    from src.core.auth import _verify_password
    from src.database.connection import get_connection
    
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT pass_hash FROM users WHERE username=?", ("admin",))
        result = cur.fetchone()
        if result:
            pass_hash = result[0]
            print(f"   Hash almacenado: {pass_hash[:20]}...")
            
            # Probar contraseña
            password = "admin123"
            if _verify_password(pass_hash, password):
                print(f"   ✅ Contraseña 'admin123' es CORRECTA")
            else:
                print(f"   ❌ Contraseña 'admin123' NO coincide")
                
                # Intentar mostrar qué contraseñas funcionarían
                print("\n   💡 Intentando resetear la contraseña a 'admin123'...")
                from src.core.auth import reset_password
                try:
                    reset_password(1, "admin123")
                    print("   ✅ Contraseña reseteada a 'admin123'")
                except Exception as e:
                    print(f"   ❌ Error al resetear: {e}")
        else:
            print(f"   ❌ Usuario no encontrado")
except Exception as e:
    print(f"   ❌ Error verificando contraseña: {e}")
    import traceback
    traceback.print_exc()

# 4. Verificar roles
print("\n4️⃣ Verificando roles del usuario admin...")
try:
    from src.core.auth import _fetch_user_with_roles
    u = _fetch_user_with_roles("admin")
    if u:
        print(f"   ✅ Usuario encontrado con roles:")
        print(f"      - Roles: {u['roles']}")
    else:
        print(f"   ❌ Usuario no encontrado o inactivo")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# 5. Simular login
print("\n5️⃣ Simulando proceso de login...")
try:
    from src.core.auth import _fetch_user_with_roles, _verify_password
    
    username = "admin"
    password = "admin123"
    
    u = _fetch_user_with_roles(username)
    if not u:
        print(f"   ❌ Usuario '{username}' no existe o está inactivo")
    elif not _verify_password(u["pass_hash"], password):
        print(f"   ❌ Contraseña incorrecta")
    else:
        print(f"   ✅ LOGIN EXITOSO")
        print(f"      - ID: {u['id']}")
        print(f"      - Username: {u['username']}")
        print(f"      - Name: {u['name']}")
        print(f"      - Roles: {u['roles']}")
except Exception as e:
    print(f"   ❌ Error en login: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ Diagnóstico completado")
print("=" * 60)
