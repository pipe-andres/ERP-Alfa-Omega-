# Production Build - Fase 2

Guía para compilar la aplicación en Windows (.exe) usando PyInstaller.

1. Preparar entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller
```

2. Preparar assets (se hace automáticamente con `tools/build_exe.py`).

3. Ejecutar PyInstaller (desde `tools/build_exe.py` se muestra el comando recomendado):

```powershell
python tools/build_exe.py
# Luego copiar y ejecutar el comando mostrado por el script
```

4. Recomendaciones:
- Excluir paquetes de la venv si es necesario
- Validar que `data/inventario.db` se empaquete o se configure como recurso externo
- Configurar variables de entorno para MySQL si se usa en producción

