import sys
import shutil
import subprocess
import os

print("--- PASO 1: COPIAR BD LIMPIA ---")
shutil.copy2('dist/inventario_clean.db', 'src/data/inventario.db')
print('BD limpia copiada')

print("\n--- PASO 2: BUILD PYTHON 3.11 ---")
try:
    res = subprocess.run([sys.executable, "-m", "PyInstaller", "AlfaOmega_v2.spec", "--clean", "--noconfirm"], capture_output=True, text=True, errors="replace")
    if res.returncode != 0:
        print(f"PyInstaller falló con código {res.returncode}")
        print("\n[Últimas 30 líneas del log]:")
        print('\n'.join(res.stderr.splitlines()[-30:]))
    else:
        print("Build OK sin errores.")
except Exception as e:
    print(f"Error: {e}")

print("\n--- PASO 3: RESTAURAR BD DEV ---")
shutil.copy2('src/data/inventario_DEV_BACKUP.db', 'src/data/inventario.db')
print('BD dev restaurada')

print("\n--- PASO 4: VERIFICAR ---")
exe = 'dist/AlfaOmega_ERP/AlfaOmega_ERP.exe'
if os.path.exists(exe):
    size = os.path.getsize(exe) / 1024 / 1024
    print(f'EXE OK: {exe} ({size:.1f} MB)')
else:
    import builtins
    print('ERROR: exe no encontrado')
