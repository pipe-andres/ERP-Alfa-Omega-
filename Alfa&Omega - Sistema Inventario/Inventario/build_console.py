import subprocess
import os
import sys

# Montar unidad virtual segura para MAX_PATH avoid
subprocess.run(['subst', 'A:', os.getcwd()])

print("Unidad A: montada")

try:
    # Compilar
    result = subprocess.run(
        [sys.executable, '-m', 'PyInstaller', 'A:/AlfaOmega_v2.spec', '--noconfirm'],
        capture_output=True, text=True, cwd='A:\\', errors="replace"
    )
    print('Pyinstaller devolvió Exit code:', result.returncode)

    # Guardar log
    with open('build_console_log.txt', 'w', encoding='utf-8') as f:
        if result.stdout: f.write(result.stdout)
        if result.stderr: f.write(result.stderr)
    print('Log guardado en build_console_log.txt')
finally:
    # Desmontar siempre, incluso si crashea
    subprocess.run(['subst', 'A:', '/D'])
    print("Unidad A: desmontada")
