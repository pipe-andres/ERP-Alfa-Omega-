"""Instalador automático del sistema.
Crea carpetas, verifica dependencias, genera .env y prepara la base de datos.
"""
import sys
from pathlib import Path

# agregar raíz del proyecto al path para poder importar paquetes de src y config
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_dependency(module_name: str):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def create_env_file(path: Path):
    if path.exists():
        print(f".env ya existe en {path}")
        return
    content = [
        "# configuración de entorno para Alfa & Omega Inventario",
        "# Cambia valores según tu instalación",
        "",
        "ENV=prod",
        "DEBUG=0",
        "DB_ENGINE=sqlite",
        "DB_PATH=./src/data/inventario.db",
        "LOG_DIR=./logs",
        "BACKUP_DIR=./backups",
        "LOG_LEVEL=INFO",
        "PORT=8000",
    ]
    path.write_text("\n".join(content))
    print(f"Archivo .env creado en {path}")


def verify_dirs():
    from config import settings
    for d in (settings.DATA_DIR, settings.LOG_DIR, settings.BACKUP_DIR):
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print(f"Carpeta creada: {d}")
        else:
            print(f"Carpeta existente: {d}")


def main():
    print("=== Instalador Alfa & Omega Inventario ===")
    # Verificar Python mínimo
    if sys.version_info < (3, 8):
        print("Python 3.8+ es requerido.")
        sys.exit(1)

    # dependencies
    print("Verificando dependencias...")
    needed = ["sqlite3", "dotenv"]
    missing = []
    for mod in needed:
        if not check_dependency(mod):
            missing.append(mod)
    if missing:
        print(f"Dependencias faltantes: {missing}")
        print("Instala con pip antes de continuar: pip install -r requirements.txt")
        sys.exit(1)
    else:
        print("Todas las dependencias están presentes.")

    # crear .env
    env_path = Path(__file__).parent.parent / ".env"
    create_env_file(env_path)

    # crear directorios
    verify_dirs()

    # configurar base de datos
    from scripts.setup_database import main as db_setup
    db_setup()

    print("Instalación completada. Ejecuta 'python main.py' para iniciar el sistema.")


if __name__ == "__main__":
    main()
