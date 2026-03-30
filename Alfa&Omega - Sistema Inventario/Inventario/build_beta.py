import sys
import os
import shutil
import subprocess
import zipfile

print("--- PASO 1: APLICAR BD LIMPIA ---")
dst = 'src/data/inventario.db'
shutil.copy2('dist/inventario_clean.db', dst)
print('BD limpia copiada')

print("\n--- PASO 2: COMPILAR PYINSTALLER ---")
try:
    # Capturar log output sin romper consola Windows
    res = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "AlfaOmega_v2.spec", "--clean", "--noconfirm"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    print("PyInstaller Exit Code:", res.returncode)
    # Mostramos los últimos warning/errors si falló o al final
    print("\n[Últimas 30 líneas del build log]:")
    print('\n'.join(res.stdout.splitlines()[-30:]))
    if res.returncode != 0:
        print("\n[ERROR TRACE]:")
        print('\n'.join(res.stderr.splitlines()[-40:]))
except Exception as e:
    print("Error lanzando pyinstaller:", e)

print("\n--- PASO 3: RESTAURAR BD DE DESARROLLO ---")
# Esto se ejecuta SIEMPRE ya que la excepción fue capturada arriba
shutil.copy2('src/data/inventario_DEV_BACKUP.db', dst)
print('BD dev restaurada')

print("\n--- PASO 4: CREAR ZIP ---")
zip_name = 'AlfaOmega_ERP_v3.5_Setup.zip'
carpeta_dist = 'dist/AlfaOmega_ERP'
docs = ['docs/INSTALACION.md', 'docs/MANUAL_USUARIO.md', 'docs/GUIA_BETA_TESTER.md']

if os.path.exists(carpeta_dist):
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(carpeta_dist):
            for f in files:
                ruta = os.path.join(root, f)
                arcname = os.path.relpath(ruta, 'dist')
                z.write(ruta, arcname)
        for doc in docs:
            if os.path.exists(doc):
                z.write(doc, os.path.basename(doc))
    print(f'ZIP creado: {zip_name}')
    print(f'Tamaño: {os.path.getsize(zip_name)/1024/1024:.1f} MB')
else:
    print('Error: carpeta dist/AlfaOmega_ERP no existe para empaquetar.')
