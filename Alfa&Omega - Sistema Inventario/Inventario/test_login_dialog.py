#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar el diálogo de login interactivamente
"""
import tkinter as tk
from src.core.auth import LoginDialog

print('Abriendo diálogo de login...')
print('Por favor ingresa: admin / admin123')
print('')

root = tk.Tk()
root.withdraw()  # Ocultar ventana principal

dlg = LoginDialog(root)
print(f'Resultado del login: {dlg.result}')

if dlg.result:
    print('✅ LOGIN EXITOSO')
    print(f'  - Usuario: {dlg.result["username"]}')
    print(f'  - Nombre: {dlg.result["name"]}')
    print(f'  - Roles: {dlg.result["roles"]}')
else:
    print('❌ Login cancelado o fallido')

root.destroy()
