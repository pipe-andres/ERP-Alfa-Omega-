@echo off
echo ========================================
echo    ALFA & OMEGA - SISTEMA DE INVENTARIO
echo ========================================
echo.
echo Credenciales de acceso:
echo Usuario: admin
echo Contrasena: admin123
echo.
echo Iniciando sistema...
echo.
echo Si no ves la ventana del sistema, revisa:
echo 1. Que no haya ventanas minimizadas
echo 2. Que el antivirus no bloquee la aplicacion
echo 3. Que tengas permisos de administrador
echo.
echo Presiona cualquier tecla para continuar...
pause > nul

cd /d "%~dp0"
call .venv\Scripts\activate.bat
python main.py

echo.
echo Sistema cerrado.
pause