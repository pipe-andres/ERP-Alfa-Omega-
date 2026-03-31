# Guía de Instalación para Cliente

Este documento está dirigido a usuarios NO técnicos que han adquirido el sistema de inventario de Alfa & Omega.

## Requisitos Previos

- **Windows 10/11** (soporta también Linux/macOS con Python 3.8+)
- **Python 3.8 o superior** instalado en el equipo.
- Espacio en disco: mínimo 100 MB.
- Permisos para ejecutar archivos y crear carpetas.

## Proceso de Instalación

1. **Descargar el paquete** que le ha suministrado Alfa & Omega y descomprimirlo en la carpeta de su elección.
2. **Abrir una terminal** (PowerShell en Windows) y navegar al directorio raíz del paquete.
3. Ejecutar el instalador:
   ```bash
   python scripts/install.py
   ```
   - El instalador verificará dependencias, creará la base de datos y estructuras necesarias.
   - Generará un archivo `.env` con valores por defecto.
4. Cuando el proceso termine verá un mensaje "Instalación completada".
5. **Iniciar la aplicación** con:
   ```bash
   python main.py
   ```
   Se abrirá la interfaz gráfica de usuario.

---

## Empaquetado para Distribución

Los desarrolladores pueden generar un ejecutable independiente que los clientes simplemente ejecutan, sin requerir Python ni dependencias:

```bash
pip install pyinstaller          # sólo en el entorno de desarrollo
python scripts/build_installer.py
```

El binario resultante se encuentra en `dist/AlfaOmega.exe` y es el artefacto entregable. Para procedimientos alternativos existen los preexistentes `build_exe.bat` y `build_executable.py`.

## Post-Instalación

- Un registro de instalación se guarda en `logs/sistema.log`.
- Las bases de datos y backups se almacenan en la carpeta `src/data` y `backups` respectivamente.

> Nota: El software puede instalarse en una unidad USB o carpeta compartida, siempre que Python pueda ejecutarse desde allí.

## Resolución de Problemas

- Si la instalación falla por dependencias faltantes, ejecute:
  ```bash
  pip install -r requirements.txt
  ```
- Si recibe errores de permisos, asegúrese de tener derechos de escritura en la carpeta de instalación.

Gracias por elegir Alfa & Omega. Para asistencia técnica contacte a soporte@alfaomega.com.
