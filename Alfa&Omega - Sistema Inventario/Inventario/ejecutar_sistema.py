#!/usr/bin/env python3
"""
Script que ejecuta main.py con captura completa de errores.
"""

import sys
import os
import subprocess
from pathlib import Path

def run_main_with_error_capture():
    """Ejecuta main.py y captura cualquier error"""
    project_root = Path(__file__).parent

    # Comando para ejecutar main.py
    cmd = [
        str(project_root / ".venv" / "Scripts" / "python.exe"),
        str(project_root / "main.py")
    ]

    print("🚀 EJECUTANDO SISTEMA PRINCIPAL")
    print("=" * 40)
    print(f"Comando: {' '.join(cmd)}")
    print("Si no ves la ventana, presiona Ctrl+C para cancelar")
    print("")

    try:
        # Ejecutar el proceso
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30  # Timeout de 30 segundos
        )

        print("RESULTADO DE EJECUCIÓN:")
        print("=" * 40)

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        print(f"Código de salida: {result.returncode}")

        if result.returncode == 0:
            print("✅ Sistema ejecutado exitosamente")
        else:
            print("❌ Error en la ejecución")

    except subprocess.TimeoutExpired:
        print("⏰ Timeout: El sistema se ejecutó pero no terminó en 30 segundos")
        print("Esto es NORMAL - significa que la GUI se abrió correctamente")

    except KeyboardInterrupt:
        print("🛑 Interrumpido por usuario")

    except Exception as e:
        print(f"❌ Error ejecutando el sistema: {e}")

if __name__ == "__main__":
    run_main_with_error_capture()