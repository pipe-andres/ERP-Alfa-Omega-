Instrucciones para generar el instalador Windows (Inno Setup)

Resumen:
- Ya se generó el ejecutable en modo "one-folder" con PyInstaller.
- Carpeta de salida: `Inventario/dist/Inventario/` (contiene `Inventario.exe`).
- ZIP lista para envío: `Inventario/dist/Inventario_Installer_Package.zip`.

Opciones para crear instalador (.exe):

1) Usar Inno Setup (recomendado):
  - Instalar Inno Setup: https://jrsoftware.org/isinfo.php
  - Abrir `installer.iss` en el directorio del proyecto y ajustar `SourcePath` si quieres usar macro.
  - Compilar con Inno Setup Compiler (ISCC.exe):
    ```powershell
    & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "C:\ruta\a\proyecto\installer.iss"
    ```
  - Resultado: `Inventario_Setup_v1.0.exe` (instalador). 

2) Si no quieres compilar un instalador ahora:
  - Envía `Inventario/dist/Inventario_Installer_Package.zip` al cliente.
  - Cliente extrae y ejecuta `Inventario.exe` o crea acceso directo manual.

Notas:
- El instalador creado por Inno Setup incluye desinstalador y accesos directos.
- Si quieres, puedo instalar Inno Setup en este entorno y compilar el instalador por ti (necesitaría permiso para descargar/instalar). 

