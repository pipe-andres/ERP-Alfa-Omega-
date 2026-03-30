"""Genera ejecutable de Windows usando PyInstaller.

Uso:
    python scripts/build_installer.py

Requiere PyInstaller instalado en el entorno.
"""
import os
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build_py"
SPEC_FILE = PROJECT_ROOT / "AlfaOmega.spec"
INPUT_SCRIPT = PROJECT_ROOT / "main.py"


def main():
    try:
        import PyInstaller.__main__
    except ImportError:
        print("PyInstaller no está instalado. Ejecuta 'pip install pyinstaller'")
        sys.exit(1)

    # limpiar directorios previos
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if SPEC_FILE.exists():
        SPEC_FILE.unlink()

    opts = [
        str(INPUT_SCRIPT),
        "--onedir",
        "--noconsole",
        f"--name=AlfaOmega",
        # f"--add-data=src;src",
        f"--add-data=config;config",
        f"--add-data=version.json;.",
    ]
    print("Ejecutando PyInstaller, esto puede tardar...")
    PyInstaller.__main__.run(opts)
    print("Construcción completada. Revisa la carpeta 'dist' para el ejecutable.")


if __name__ == "__main__":
    main()
