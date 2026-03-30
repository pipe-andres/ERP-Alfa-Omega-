#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar la estructura de clases en main_window.py
"""

with open('src/app/main_window.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar clases
print("BÚSQUEDA DE CLASES Y MÉTODOS:")
print("=" * 60)

class_stack = []  # Para rastrear clases anidadas
current_indent = 0

for i, line in enumerate(lines):
    stripped = line.lstrip()
    indent = len(line) - len(stripped)
    
    # Detectar clases
    if stripped.startswith('class '):
        class_name = stripped.split('(')[0].replace('class ', '').strip(':')
        print(f"Línea {i+1:4d} (indent {indent}): CLASS {class_name}")
        class_stack.append((class_name, indent))
    
    # Detectar métodos _build_tab_*
    if stripped.startswith('def _build_tab_'):
        method_name = stripped.split('(')[0].replace('def ', '')
        in_class = class_stack[-1][0] if class_stack else "GLOBAL"
        print(f"Línea {i+1:4d} (indent {indent}): METHOD {method_name} en {in_class}")

print("\n" + "=" * 60)
print("\nVERIFICACIÓN:")

# Buscar específicamente _build_tab_devoluciones
for i, line in enumerate(lines):
    if 'def _build_tab_devoluciones' in line:
        indent = len(line) - len(line.lstrip())
        print(f"\n_build_tab_devoluciones encontrado en línea {i+1}")
        print(f"Indentación: {indent} espacios")
        print(f"Es método de clase: {indent >= 4}")
        
        # Mostrar contexto
        print(f"\nContexto (líneas {max(1,i-3)} a {min(len(lines),i+5)}):")
        for j in range(max(0, i-3), min(len(lines), i+5)):
            marker = ">>>" if j == i else "   "
            print(f"{marker} {j+1:4d}: {lines[j].rstrip()}")
