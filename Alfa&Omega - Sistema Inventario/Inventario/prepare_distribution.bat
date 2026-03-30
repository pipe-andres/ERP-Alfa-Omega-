@echo off
REM Crear estructura Portable para distribuir al cliente

setlocal enabledelayedexpansion

set "SOURCE_DIR=%~dp0"
set "DIST_DIR=%SOURCE_DIR%Inventario_v1.0"
set "ZIP_FILE=%SOURCE_DIR%..\Inventario_v1.0_Portable.zip"

echo.
echo ============================================================
echo   PREPARANDO DISTRIBUCION PORTABLE PARA CLIENTE
echo ============================================================
echo.

REM 1. Limpiar directorio anterior
if exist "%DIST_DIR%" (
    echo [1/5] Limpiando directorio anterior...
    rmdir /s /q "%DIST_DIR%"
)
echo.

REM 2. Crear estructura
echo [2/5] Creando estructura de carpetas...
mkdir "%DIST_DIR%"
mkdir "%DIST_DIR%\src"
mkdir "%DIST_DIR%\assets"
mkdir "%DIST_DIR%\.venv"
echo.

REM 3. Copiar archivos
echo [3/5] Copiando archivos...
copy "%SOURCE_DIR%main.py" "%DIST_DIR%\" >nul
copy "%SOURCE_DIR%inventario.db" "%DIST_DIR%\" >nul
copy "%SOURCE_DIR%README_CLIENTE.md" "%DIST_DIR%\" >nul
copy "%SOURCE_DIR%requirements.txt" "%DIST_DIR%\" >nul
xcopy "%SOURCE_DIR%src" "%DIST_DIR%\src" /e /i /q >nul
xcopy "%SOURCE_DIR%assets" "%DIST_DIR%\assets" /e /i /q >nul
xcopy "%SOURCE_DIR%.venv" "%DIST_DIR%\.venv" /e /i /q >nul
echo.

REM 4. Crear script run.bat
echo [4/5] Creando script de ejecucion...
(
echo @echo off
echo REM Inventario Alfa ^& Omega v1.0
echo REM Ejecuta la aplicacion
echo.
echo cd /d "%%~dp0"
echo .venv\Scripts\python.exe main.py
echo pause
) > "%DIST_DIR%\run.bat"

REM 5. Crear ZIP
echo [5/5] Creando archivo ZIP...
REM Nota: Esto requiere 7-Zip o similar. Mostrar instruccion manual si no existe.

echo.
echo ============================================================
echo   DISTRIBUCION LISTA
echo ============================================================
echo.
echo Carpeta: %DIST_DIR%
echo.
echo Proximos pasos:
echo   1. Copiar "%DIST_DIR%" a comprimir
echo   2. O compartir toda la carpeta por Google Drive / OneDrive
echo   3. Cliente extrae y ejecuta run.bat
echo.
echo Tamaño estimado: 600-700 MB
echo.
pause
