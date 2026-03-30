#!/usr/bin/env python
"""
Script para crear ejecutable distributable para cliente
Usa PyInstaller para empaquetar la aplicación
"""
import os
import sys
import shutil
from pathlib import Path

def main():
    print("=" * 60)
    print("🔨 CONSTRUYENDO EJECUTABLE PARA CLIENTE")
    print("=" * 60)
    
    # Verificar PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("\n❌ PyInstaller no está instalado.")
        print("   Ejecuta: pip install pyinstaller")
        sys.exit(1)
    
    # Rutas
    root_dir = Path(__file__).parent
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"
    
    # Limpiar builds anteriores
    print("\n📦 Limpiando builds anteriores...")
    for d in [dist_dir, build_dir]:
        if d.exists():
            shutil.rmtree(d)
    
    # Crear spec file
    print("\n📝 Creando configuración PyInstaller...")
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    [r'{root_dir}/main.py'],
    pathex=[r'{root_dir}'],
    binaries=[],
    datas=[
        (r'{root_dir}/src', 'src'),
        (r'{root_dir}/assets', 'assets'),
        (r'{root_dir}/inventario.db', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'PIL',
        'sqlalchemy',
        'aiosqlite',
        'bcrypt',
        'passlib',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Inventario_AlfaOmega',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    spec_file = root_dir / "build_inventario.spec"
    spec_file.write_text(spec_content)
    print(f"   ✅ Spec file: {spec_file}")
    
    # Ejecutar PyInstaller
    print("\n🚀 Ejecutando PyInstaller...")
    print("   (esto puede tomar 1-2 minutos)...\n")
    
    os.system(f'"{sys.executable}" -m PyInstaller "{spec_file}" --distpath "{dist_dir}"')
    
    # Verificar resultado
    exe_path = dist_dir / "Inventario_AlfaOmega" / "Inventario_AlfaOmega.exe"
    if exe_path.exists():
        print("\n" + "=" * 60)
        print("✅ EJECUTABLE CREADO EXITOSAMENTE")
        print("=" * 60)
        print(f"\n📁 Ubicación: {exe_path}")
        print(f"\n📊 Tamaño: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        print("\n🎯 Próximos pasos:")
        print("   1. Crear ZIP para distribución")
        print("   2. Incluir README_CLIENTE.md")
        print("   3. Enviar al cliente")
        return 0
    else:
        print("\n❌ Error: No se pudo crear el ejecutable")
        return 1

if __name__ == "__main__":
    sys.exit(main())
