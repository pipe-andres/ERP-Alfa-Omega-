import os
import sys
import subprocess
import shutil

cwd = os.getcwd()

print("--- PASO 1: SYMLINK O SUBST ---")
build_dir = "C:\\AO"
used_symlink = False

# Intento 1: os.symlink
try:
    os.symlink(cwd, build_dir, target_is_directory=True)
    print("os.symlink creado")
    used_symlink = True
except Exception as e:
    print("Fallo os.symlink:", e)
    
if not used_symlink:
    print("\nIntentando SUBST A:...")
    try:
        # Array seguro para evitar inyección CMD por el '&' en la ruta 'Alfa&Omega'
        res_subst = subprocess.run(["subst", "A:", cwd], capture_output=True, text=True)
        if res_subst.stdout.strip(): print("CMD subst:", res_subst.stdout.strip())
        if res_subst.stderr.strip(): print("ERR subst:", res_subst.stderr.strip())
        build_dir = "A:\\"
    except Exception as e2:
        print("Fallo SUBST:", e2)

print(f"\n--- PASO 2: VERIFICAR RUTA {build_dir} ---")
main_py = os.path.join(build_dir, "main.py")
print(f"Existe {main_py}: {os.path.exists(main_py)}")

print("\n--- PASO 3: BUILD DESDE RUTA CORTA ---")
if os.path.exists(main_py):
    cmd = [sys.executable, "-m", "PyInstaller", "AlfaOmega_v2.spec", "--clean", "--noconfirm"]
    print(f"Ejecutando PyInstaller en ruta corta ({build_dir})...")
    
    res_build = subprocess.run(cmd, cwd=build_dir, capture_output=True, text=True, errors="replace")
    
    print(f"\nSalida Build Exit Code: {res_build.returncode}")
    if res_build.returncode != 0:
        print("\n[PyInstaller ERRORS (ultimas 30 lineas)]:")
        print("\n".join(res_build.stderr.splitlines()[-30:]))
    else:
        print("\nBuild finalizado exitosamente.")
else:
    print("Abortando build, la ruta corta no funcionó.")
    
# Cleanup subst si se usó
if build_dir == "A:\\":
    print("\nRemoviendo drive virtual A: temporal...")
    subprocess.run(["subst", "A:", "/D"])
