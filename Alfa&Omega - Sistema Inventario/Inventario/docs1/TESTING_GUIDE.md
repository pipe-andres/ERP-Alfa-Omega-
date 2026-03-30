# Guía rápida de testing

Este proyecto usa `pytest` y una base de datos SQLite temporal para ejecutar tests de integración de forma aislada.

- Estrategia de tests:
  - Cada test se ejecuta con una base de datos SQLite temporal única (`DB_PATH` apuntando a un fichero temporal). Esto evita colisiones entre ejecuciones paralelas y mantiene los datos aislados.
  - La fixture principal `use_temp_db` en `tests/conftest.py` se encarga de crear el fichero temporal, establecer las variables de entorno necesarias (`DB_ENGINE`, `DB_PATH`), recargar el módulo `src.database.connection` y ejecutar `init_db()`.
  - Por diseño, los tests son independientes (scope `function`). Si un test necesita datos iniciales, debe crearlos explícitamente (ej. `add_product(...)`).

- Ejecutar tests localmente:

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
```

- Detección y formateo de código:
  - El CI ejecuta `black --check .` para asegurar estilo de código. Ejecuta `black .` localmente para aplicar el formato.

- Notas para desarrolladores:
  - Si añades nuevas tablas de esquema en `src/database`, añade una llamada a su `ensure_schema()` dentro de `src.database.connection.init_db()` si quieres que los tests las creen automáticamente.
  - Evita depender del orden de ejecución de tests; cada test debe preparar su propio estado.

Si quieres que cambie la política (por ejemplo, usar `scope=module` para agrupar tests por archivo), dímelo y adapto los tests o la fixture según prefieras.
# Testing Guide - Fase 2

Se añadieron tests con `pytest` en la carpeta `/tests`.

Pautas:
- Los tests usan una DB temporal creada por `tests/conftest.py`.
- Nunca modifican la BD real durante pruebas.
- Ejecutar:

```bash
pip install -r requirements.txt
pytest -q
```

- Crear nuevos tests en `/tests` y usar fixtures de `conftest.py`.
- Para pruebas de integración más largas, marcar con `@pytest.mark.integration`.

