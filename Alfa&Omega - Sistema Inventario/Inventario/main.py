
#!/usr/bin/env python3
"""
Alfa & Omega - Sistema de Inventario
Punto de entrada principal para la aplicación GUI.

Este archivo importa la estructura modular reorganizada en /src.
Con error handling robusto y backups automáticos.
"""

import sys
import tkinter as tk
from pathlib import Path

# Agregar src al path para importaciones
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# SISTEMA DE LOGGING Y ERROR HANDLING
from src.core.error_handler import logger, log_error

logger.info("=" * 70)
logger.info("INICIANDO SISTEMA ALFA & OMEGA")
logger.info("=" * 70)

# SISTEMA DE BACKUPS AUTOMÁTICO
from src.utils.database_backup import backup_database
from config import settings
DB_PATH = settings.DB_PATH

# Forzar inclusión de handlers dinámicos usados por passlib (PyInstaller misses dynamic imports)
try:
    import passlib.handlers.sha2_crypt  # pragma: no cover
except Exception:
    # Si no está instalado en el entorno, solo ignoramos para permitir ejecución en desarrollo
    pass

from src.database.connection import init_db
from src.core.auth import ensure_defaults
from src.services.partners import ensure_schema as ensure_partners_schema
from src.database.settings import ensure_schema as ensure_settings_schema
from src.database.repository import ensure_schema as ensure_repo_schema
from src.core import configure_logging
from src.core import license_manager

# Importar la aplicación GUI
try:
    from src.app.main_window import InventarioApp
except ImportError as e:
    logger.error(f"ERROR: No se encontró src/app/main_window.py - {e}")
    sys.exit(1)


def _show_activation_window(parent) -> bool:
    """Muestra ventana de activación cuando no hay licencia válida."""
    import tkinter as tk
    from tkinter import ttk, messagebox
    
    win = tk.Toplevel(parent)
    win.title("Activar Alfa & Omega ERP")
    win.geometry("500x400")
    win.resizable(False, False)
    win.grab_set()
    
    # Centrar ventana
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - 250
    y = (win.winfo_screenheight() // 2) - 200
    win.geometry(f"+{x}+{y}")
    
    activated = [False]
    
    # Header
    tk.Label(win, text="🔑 Activar Sistema",
             font=("Arial", 16, "bold")).pack(pady=(20,5))
    tk.Label(win, text="Para activar el sistema necesitas una licencia.",
             font=("Arial", 10)).pack()
    
    # Machine Hash
    tk.Label(win, text="Tu código de máquina:",
             font=("Arial", 10, "bold")).pack(pady=(15,2))
    
    machine_hash = license_manager._machine_hash()
    hash_var = tk.StringVar(value=machine_hash)
    hash_entry = tk.Entry(win, textvariable=hash_var, 
                          width=55, state="readonly",
                          font=("Courier", 8))
    hash_entry.pack(padx=20)
    
    def copiar_hash():
        win.clipboard_clear()
        win.clipboard_append(machine_hash)
        messagebox.showinfo("Copiado", 
            "Código copiado. Envíalo a tu proveedor para obtener tu licencia.",
            parent=win)
    
    tk.Button(win, text="📋 Copiar código", 
              command=copiar_hash).pack(pady=5)
    
    # Instrucción
    tk.Label(win, 
             text="Envía tu código al proveedor y pega la licencia aquí:",
             font=("Arial", 10)).pack(pady=(15,2))
    
    # Campo licencia
    lic_text = tk.Text(win, height=5, width=55, font=("Courier", 8))
    lic_text.pack(padx=20)
    
    def activar():
        lic_str = lic_text.get("1.0", "end").strip()
        if not lic_str:
            messagebox.showwarning("Vacío", 
                "Pega tu licencia primero.", parent=win)
            return
        if license_manager.activate_license(lic_str):
            if license_manager.validate_license():
                messagebox.showinfo("✅ Activado", 
                    "¡Licencia activada con éxito! El sistema iniciará.",
                    parent=win)
                activated[0] = True
                win.destroy()
            else:
                messagebox.showerror("Error", 
                    "Licencia inválida para esta máquina.", parent=win)
        else:
            messagebox.showerror("Error", 
                "Licencia incorrecta. Verifica el texto.", parent=win)
    
    def cancelar():
        win.destroy()
    
    # Botones
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="✅ Activar", command=activar,
              bg="#10B981", fg="white", 
              font=("Arial", 11, "bold"),
              padx=20).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancelar", command=cancelar,
              padx=20).pack(side="left", padx=5)
    
    win.wait_window()
    return activated[0]


def initialize_system():
    """Inicializa el sistema con manejo robusto de errores."""
    try:
        logger.info("1. Validando licencia...")
        if not license_manager.validate_license():
            logger.info("Mostrando ventana de activación...")
            import tkinter as tk
            from tkinter import messagebox
            root_lic = tk.Tk()
            root_lic.withdraw()
            activated = _show_activation_window(root_lic)
            root_lic.destroy()
            if not activated:
                return False
        logger.info("Licencia válida.")

        logger.info("2. Configurando logging...")
        configure_logging()

        logger.info("3. Verificando base de datos...")
        init_db()
        
        logger.info("4. Realizando backup automático de inicio...")
        backup_result = backup_database(DB_PATH, backup_type="startup")
        if backup_result:
            logger.info(f"   ✓ Backup creado: {backup_result.name}")
        else:
            logger.warning("   ⚠️ No se pudo crear backup de inicio (continuando)")
        
        logger.info("5. Inicializando valores por defecto...")
        ensure_defaults()
        # Note: ensure_schema() calls moved to init_db() for centralization
        # (ensure_partners_schema, ensure_settings_schema, ensure_repo_schema)
        
        logger.info("✓ Sistema inicializado correctamente")
        return True
    
    except Exception as e:
        log_error(e, context={"phase": "initialization"}, level="CRITICAL")
        logger.error("\n" + "=" * 70)
        logger.error("FALLO CRÍTICO EN INICIALIZACIÓN DEL SISTEMA")
        logger.error("=" * 70)
        logger.error(f"Error: {str(e)}")
        logger.error("Por favor, revisa el archivo logs/sistema.log para más detalles")
        logger.error("=" * 70)
        
        # Mostrar diálogo de error al usuario
        root = tk.Tk()
        root.withdraw()
        from tkinter import messagebox
        messagebox.showerror(
            "Error al inicializar sistema",
            f"No se pudo inicializar el sistemas:\n\n{str(e)}\n\n"
            "Por favor, verifica que la base de datos sea accesible."
        )
        root.destroy()
        
        return False


def main():
    """Punto de entrada principal con manejo global de errores."""
    try:
        # Inicializar sistema
        if not initialize_system():
            sys.exit(1)
        
        logger.info("\n5. Iniciando interfaz gráfica...")
        
        # FIX: DPI awareness para evitar pantalla negra en Windows con escala >100%
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # Crear y ejecutar interfaz
        root = tk.Tk()
        app = InventarioApp(root)
        root.update_idletasks()
        root.lift()
        root.focus_force()
        
        # Handler de cierre para backup al salir
        def on_closing():
            """Realiza backup automático antes de cerrar."""
            try:
                logger.info("Realizando backup automático de cierre...")
                backup_result = backup_database(DB_PATH, backup_type="shutdown")
                if backup_result:
                    logger.info(f"✓ Backup final creado: {backup_result.name}")
            except Exception as e:
                logger.warning(f"⚠️ Error en backup de cierre: {e}")
            finally:
                logger.info("Cerrando aplicación...")
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Notificaciones — arranca scheduler si está configurado
        try:
            from src.services.notificaciones import iniciar_scheduler
            iniciar_scheduler()
        except Exception:
            pass

        logger.info("✓ Interfaz iniciada correctamente")
        root.mainloop()
        
    except Exception as e:
        log_error(e, context={"phase": "main_execution"}, level="CRITICAL")
        logger.error("\n" + "=" * 70)
        logger.error("FALLO CRÍTICO EN EJECUCIÓN PRINCIPAL")
        logger.error("=" * 70)
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()