#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de parseo de sintaxis pura - No ejecuta, solo parsea AST
"""

import sys
import os
import ast

def test_syntax():
    """Verifica sintaxis sin ejecutar"""
    
    print("=" * 80)
    print("ANÁLISIS DE SINTAXIS AST")
    print("=" * 80)
    
    file_path = os.path.join(
        os.path.dirname(__file__),
        "src/app/main_window.py"
    )
    
    try:
        print(f"\n1. Leyendo {file_path}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        print("   ✓ Archivo leído")
        
        print("\n2. Parseando AST...")
        tree = ast.parse(code)
        print("   ✓ AST parseado exitosamente")
        
        print("\n3. Buscando clase InventarioApp...")
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "InventarioApp":
                print(f"   ✓ Clase encontrada")
                print(f"     - Línea: {node.lineno}")
                print(f"     - Métodos:")
                method_count = 0
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_count += 1
                        if method_count <= 5 or "_build_tab" in item.name:
                            print(f"       - {item.name} (línea {item.lineno})")
                    if method_count > 20 and "_build_tab" not in item.name:
                        if method_count == 21:
                            print(f"       ... ({method_count} métodos en total)")
                        continue
                        
                print(f"   - Total de métodos: {method_count}")
                
                # Buscar métodos de tabs nuevos
                new_tab_methods = [
                    "_build_tab_devoluciones",
                    "_build_tab_descuentos",
                    "_build_tab_margenes",
                    "_build_tab_reportes_avanzados"
                ]
                
                print(f"\n4. Verificando métodos nuevos:")
                for method_name in new_tab_methods:
                    found = any(
                        isinstance(item, ast.FunctionDef) and item.name == method_name
                        for item in node.body
                    )
                    status = "✓" if found else "✗"
                    print(f"   {status} {method_name}")
                
        print("\n5. Buscando clase ProductoDialog...")
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "ProductoDialog":
                print(f"   ✓ Clase encontrada en línea {node.lineno}")
                break
        
        print("\n✅ ANÁLISIS SINTÁCTICO COMPLETADO")
        return True
        
    except SyntaxError as e:
        print(f"\n❌ ERROR DE SINTAXIS:")
        print(f"   Línea {e.lineno}: {e.msg}")
        print(f"   {e.text}")
        return False
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_syntax()
    sys.exit(0 if success else 1)
