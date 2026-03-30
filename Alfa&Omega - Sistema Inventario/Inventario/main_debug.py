#!/usr/bin/env python3
"""
Alfa & Omega - Sistema de Inventario
Punto de entrada principal para la aplicación GUI.

Esta versión incluye debugging detallado para identificar problemas.
"""

import sys
import tkinter as tk
from pathlib import Path
import traceback

# Agregar src al path para importaciones
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Forzar inclusión de handlers dinámicos usados por passlib (PyInstaller misses dynamic imports)
try:
    import passlib.handlers.sha2_crypt  # pragma: no cover
except Exception:
    # Si no está instalado en el entorno, solo ignoramos para permitir ejecución en desarrollo
    pass

def debug_print(message):
    """Función para imprimir mensajes de debug"""
    print(f"[DEBUG] {message}")

def main():
    """Inicializa la aplicación y abre la ventana principal."""
    try:
        debug_print("Iniciando aplicación Alfa & Omega...")

        # Importar módulos con debug
        debug_print("Importando módulos de configuración...")
        from src.database.connection import init_db
        from src.core.auth import ensure_defaults
        from src.services.partners import ensure_schema as ensure_partners_schema
        from src.database.settings import ensure_schema as ensure_settings_schema
        from src.core import configure_logging
        debug_print("✅ Módulos de configuración importados")

        # Importar aplicación GUI
        debug_print("Importando aplicación GUI...")
        from src.app.main_window import InventarioApp
        debug_print("✅ Aplicación GUI importada")

        # Configurar logging
        debug_print("Configurando logging...")
        configure_logging()
        debug_print("✅ Logging configurado")

        # Inicializar base de datos
        debug_print("Inicializando base de datos...")
        init_db()
        ensure_defaults()
        ensure_partners_schema()
        ensure_settings_schema()
        debug_print("✅ Base de datos inicializada")

        # Crear ventana principal
        debug_print("Creando ventana principal...")
        root = tk.Tk()
        debug_print("✅ Ventana principal creada")

        # Crear aplicación
        debug_print("Creando aplicación InventarioApp...")
        app = InventarioApp(root)
        debug_print("✅ Aplicación InventarioApp creada")

        # Iniciar loop principal
        debug_print("Iniciando loop principal de tkinter...")
        debug_print("")
        debug_print("🎉 SISTEMA INICIADO CORRECTAMENTE")
        debug_print("Si no ves la ventana, busca en la barra de tareas")
        debug_print("Credenciales: admin / admin123")
        debug_print("")

        root.mainloop()

    except Exception as e:
        error_msg = f"❌ ERROR CRÍTICO EN LA INICIALIZACIÓN: {e}"
        print(error_msg)
        print("\nDETALLES DEL ERROR:")
        traceback.print_exc()

        # Mostrar error en ventana si es posible
        try:
            root = tk.Tk()
            root.title("Error - Alfa & Omega")
            root.geometry("500x300")

            import tkinter.messagebox as messagebox
            messagebox.showerror("Error de Inicialización", f"Error: {e}\n\nRevisa la consola para más detalles.")

            # Mostrar detalles en un text widget
            text = tk.Text(root, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text.insert(tk.END, f"Error: {e}\n\n")
            text.insert(tk.END, traceback.format_exc())

            root.mainloop()

        except:
            print("No se pudo mostrar la ventana de error")

if __name__ == "__main__":
    main()