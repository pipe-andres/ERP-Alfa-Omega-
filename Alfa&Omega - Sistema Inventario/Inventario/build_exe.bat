@echo off
REM Script para empaquetar la app para distribuir al cliente
REM Usa PyInstaller

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set VENV=%SCRIPT_DIR%.venv\Scripts\

echo.
echo ============================================================
echo.   CONSTRUCCION DE EJECUTABLE PARA CLIENTE
echo.
echo ============================================================
echo.

REM Verificar PyInstaller
%VENV%python.exe -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Error: PyInstaller no esta instalado
    echo Ejecuta: .venv\Scripts\pip.exe install pyinstaller
    pause
    exit /b 1
)

echo [1/4] Limpiando builds anteriores...
if exist "%SCRIPT_DIR%dist" rmdir /s /q "%SCRIPT_DIR%dist" 2>nul
if exist "%SCRIPT_DIR%build" rmdir /s /q "%SCRIPT_DIR%build" 2>nul
echo.

echo [2/4] Creando configuracion PyInstaller...
REM Crear spec file dinamicamente
(
echo # -*- mode: python ; coding: utf-8 -*-
echo import sys
echo from pathlib import Path
echo.
echo a = Analysis(
echo     [r'%SCRIPT_DIR%main.py'],
echo     pathex=[r'%SCRIPT_DIR%'],
echo     binaries=[],
echo     datas=[
echo         (r'%SCRIPT_DIR%src', 'src'),
echo         (r'%SCRIPT_DIR%assets', 'assets'),
echo         (r'%SCRIPT_DIR%inventario.db', '.'),
echo     ],
echo     hiddenimports=['tkinter', 'PIL', 'sqlalchemy', 'aiosqlite', 'bcrypt', 'passlib'],
echo     hookspath=[],
echo     runtime_hooks=[],
echo     excludedimports=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo )
echo.
echo pyz = PYZ(a.pure, a.zipped_data)
echo.
echo exe = EXE(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     [],
echo     name='Inventario_AlfaOmega',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     console=False,
echo )
) > "%SCRIPT_DIR%build_spec.spec"
echo.

echo [3/4] Ejecutando PyInstaller (esto toma 1-2 minutos)...
echo.
%VENV%python.exe -m PyInstaller "%SCRIPT_DIR%build_spec.spec" --distpath "%SCRIPT_DIR%dist" --workpath "%SCRIPT_DIR%build"

if errorlevel 1 (
    echo.
    echo Error: No se pudo crear el ejecutable
    pause
    exit /b 1
)

echo.
echo [4/4] Verificando resultado...
if exist "%SCRIPT_DIR%dist\Inventario_AlfaOmega\Inventario_AlfaOmega.exe" (
    echo.
    echo ============================================================
    echo.   SUCCESS! Ejecutable creado exitosamente
    echo.
    echo ============================================================
    echo.
    echo Ubicacion: %SCRIPT_DIR%dist\Inventario_AlfaOmega\
    echo.
    echo Proximos pasos:
    echo   1. Copiar carpeta dist\Inventario_AlfaOmega
    echo   2. Renombrar a: Inventario_AlfaOmega_v1.0
    echo   3. Incluir README_CLIENTE.md
    echo   4. Comprimir en ZIP
    echo   5. Enviar al cliente
    echo.
    pause
) else (
    echo.
    echo Error: No se encontro el ejecutable
    pause
    exit /b 1
)
