#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simula el login sin GUI - Prueba el flujo de autenticación
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.auth import User, fetch_user_with_roles, verify_password

def test_auth_flow():
    """Simula exactamente lo que pasa en LoginDialog._ok()"""
    
    print("=" * 80)
    print("PRUEBA DE FLUJO DE AUTENTICACIÓN")
    print("=" * 80)
    
    username = "admin"
    password = "admin123"
    
    print(f"\n1. Intentando autenticar usuario: {username}")
    print(f"   Contraseña: {password}")
    
    try:
        # Paso 1: Buscar usuario
        print("\n2. Buscando usuario en base de datos...")
        user = fetch_user_with_roles(username)
        
        if user is None:
            print(f"   ❌ Usuario '{username}' no encontrado")
            return False
        
        print(f"   ✓ Usuario encontrado: {user['name']}")
        print(f"     - ID: {user['id']}")
        print(f"     - Roles: {user['roles']}")
        
        # Paso 2: Verificar contraseña
        print("\n3. Verificando contraseña...")
        if not verify_password(password, user['password_hash']):
            print("   ❌ Contraseña incorrecta")
            return False
        
        print("   ✓ Contraseña válida")
        
        # Paso 3: Retornar usuario (sin el hash)
        print("\n4. Preparando resultado del login...")
        user_result = User(
            id=user['id'],
            username=user['username'],
            name=user['name'],
            roles=user['roles']
        )
        
        print(f"   ✓ Usuario listo para retornar")
        print(f"     - ID: {user_result['id']}")
        print(f"     - Username: {user_result['username']}")
        print(f"     - Name: {user_result['name']}")
        print(f"     - Roles: {user_result['roles']}")
        
        print("\n✅ FLUJO DE AUTENTICACIÓN EXITOSO")
        return True
        
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: {str(e)}")
        print("\nTRACEBACK COMPLETO:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_auth_flow()
    sys.exit(0 if success else 1)
