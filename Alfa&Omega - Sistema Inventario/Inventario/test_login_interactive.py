#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para probar el login e inicialización interactivamente
Muestra todos los errores en un cuadro de diálogo
"""

import sys
import os
import traceback
import tkinter as tk
from tkinter import messagebox

# Agregar la ruta para importar src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        print("=" * 80)
        print("INICIANDO PRUEBA DE LOGIN E INICIALIZACIÓN")
        print("=" * 80)
        
        # Crear raíz
        print("1. Creando ventana root...")
        root = tk.Tk()
        
        # Importar la aplicación
        print("2. Importando InventarioApp...")
        from src.app.main_window import InventarioApp
        
        # Crear instancia
        print("3. Creando instancia de InventarioApp...")
        app = InventarioApp(root)
        
        print("4. Iniciando mainloop...")
        root.mainloop()
        
        print("\n✅ EJECUCIÓN COMPLETADA SIN ERRORES")
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print("\n❌ ERROR CAPTURADO:")
        print(error_trace)
        
        # Mostrar error en messagebox
        try:
            root_temp = tk.Tk()
            root_temp.withdraw()
            messagebox.showerror(
                "ERROR CRÍTICO",
                f"Error durante la inicialización:\n\n{error_trace}"
            )
            root_temp.destroy()
        except:
            pass

if __name__ == "__main__":
    main()
