"""Script helper para construir .exe con PyInstaller.
No ejecuta PyInstaller automáticamente; genera el comando recomendado y
prepara recursos. Excluye el entorno virtual y añade assets.
"""
from __future__ import annotations
from pathlib import Path
import shutil
import sys
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / 'src'
DIST_DIR = PROJECT_ROOT / 'dist'
BUILD_DIR = PROJECT_ROOT / 'build'

PYINSTALLER_ENTRY = PROJECT_ROOT / 'main.py'

def prepare_assets():
    # Ensure assets are included
    assets_src = PROJECT_ROOT / 'assets'
    assets_dst = PROJECT_ROOT / 'build_assets'
    if assets_dst.exists():
        shutil.rmtree(assets_dst)
    if assets_src.exists():
        shutil.copytree(assets_src, assets_dst)
    return assets_dst


def build_pyinstaller(extra_args: list[str] = None):
    extra_args = extra_args or []
    assets_dst = prepare_assets()
    cmd = [
        'pyinstaller',
        '--onefile',
        '--noconfirm',
        f'--add-data={assets_dst}{os.pathsep}assets',
        '--clean',
        str(PYINSTALLER_ENTRY)
    ] + extra_args
    print('Ejecuta el siguiente comando para generar el .exe:')
    print(' '.join(cmd))


if __name__ == '__main__':
    build_pyinstaller()
