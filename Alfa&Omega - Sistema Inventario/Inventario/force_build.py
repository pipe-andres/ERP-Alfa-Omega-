import os
import sys
import shutil
import subprocess

print("--- PASO 1: FORZAR BORRADO ---")
subprocess.run("taskkill /F /IM AlfaOmega_ERP.exe", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
try:
    if os.path.exists("dist/AlfaOmega_ERP"):
        subprocess.run("rd /s /q dist\\AlfaOmega_ERP", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    if os.path.exists("build"):
        subprocess.run("rd /s /q build", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
except Exception as e:
    pass
print("Carpetas limpias")

print("\n--- PASO 2: VERIFICAR BORRADO ---")
print('dist/AlfaOmega_ERP existe:', os.path.exists('dist/AlfaOmega_ERP'))
print('build existe:', os.path.exists('build'))

print("\n--- PASO 3: COPIAR BD LIMPIA ---")
shutil.copy2('dist/inventario_clean.db', 'src/data/inventario.db')
print('BD limpia copiada')

print("\n--- PASO 4: COMPILAR SIN --clean ---")
try:
    res = subprocess.run([sys.executable, "-m", "PyInstaller", "AlfaOmega_v2.spec", "--noconfirm"], capture_output=True, text=True, errors="replace")
    print("\n[Últimas 5 líneas del log]:")
    print('\n'.join(res.stdout.splitlines()[-5:]))
    if res.returncode != 0:
        print("\n[PyInstaller falló]:")
        print('\n'.join(res.stderr.splitlines()[-20:]))
except Exception as e:
    print("Error:", e)

print("\n--- PASO 5: RESTAURAR BD DEV ---")
shutil.copy2('src/data/inventario_DEV_BACKUP.db', 'src/data/inventario.db')
print('BD dev restaurada')
