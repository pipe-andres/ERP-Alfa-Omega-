import os
import re
import shutil
import subprocess
import zipfile
import sys

print("\n=== PASO 1 ===\n")
with open('AlfaOmega_v2.spec', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'console=\w+', 'console=False', content)
with open('AlfaOmega_v2.spec', 'w', encoding='utf-8') as f:
    f.write(content)
print("console=False restaurado")

print("\n=== PASO 2 ===\n")
shutil.copy2('dist/inventario_clean.db', 'src/data/inventario.db')
print('BD limpia copiada')

print("\n=== PASO 3 ===\n")
subprocess.run('subst A: .', shell=True)
print("Unidad A: montada. Iniciando PyInstaller en ruta corta...")
result = subprocess.run(
    [sys.executable, '-m', 'PyInstaller', 'A:/AlfaOmega_v2.spec', '--noconfirm'],
    cwd='A:\\', capture_output=True, text=True, errors="replace"
)
subprocess.run('subst A: /D', shell=True)
print('Build exit code:', result.returncode)
if result.returncode != 0:
    print(result.stderr[-1000:])

print("\n=== PASO 4 ===\n")
shutil.copy2('src/data/inventario_DEV_BACKUP.db', 'src/data/inventario.db')
print('BD dev restaurada')

print("\n=== PASO 5 ===\n")
zip_name = 'AlfaOmega_ERP_v3.5_Setup.zip'
carpeta_dist = 'dist/AlfaOmega_ERP'
docs = [
    'docs/INSTALACION.md',
    'docs/MANUAL_USUARIO.md', 
    'docs/GUIA_BETA_TESTER.md'
]
with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(carpeta_dist):
        for f in files:
            ruta = os.path.join(root, f)
            arcname = os.path.relpath(ruta, 'dist')
            z.write(ruta, arcname)
    for doc in docs:
        if os.path.exists(doc):
            z.write(doc, os.path.basename(doc))
print(f"ZIP: {zip_name}")
print(f"Tamaño: {os.path.getsize(zip_name)/1024/1024:.1f} MB")
