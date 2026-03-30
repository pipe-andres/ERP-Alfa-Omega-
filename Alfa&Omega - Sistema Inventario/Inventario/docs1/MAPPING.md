# MAPEO COMPLETO DE REORGANIZACIÓN - Alfa & Omega Sistema Inventario

## Resumen de Cambios

Este documento detalla la reorganización completa del proyecto de una estructura desorganizada a una arquitectura moderna y escalable.

---

## MAPEO DE ARCHIVOS: ORIGEN → DESTINO

### Base de Datos y Conexiones
| Origen | Destino | Estado | Cambios Principales |
|--------|---------|--------|----------------------|
| `core/database.py` | `src/database/connection.py` | ✅ Creado | Importes actualizados, rutas centralizadas |
| `core/settings.py` | `src/database/settings.py` | ✅ Creado | Importes de connection actualizados |

### Autenticación y RBAC
| Origen | Destino | Estado | Cambios Principales |
|--------|---------|--------|----------------------|
| `core/auth.py` | `src/core/auth.py` | ✅ Creado | Importes de database actualizados |
| `core/__init__.py` | `src/core/__init__.py` | ✅ Recreado | Función configure_logging |

### Servicios de Negocio
| Origen | Destino | Estado | Cambios Principales |
|--------|---------|--------|----------------------|
| `core/services.py` | `src/services/inventory.py` | ✅ Creado | Lógica de productos y movimientos |
| `core/audit.py` | `src/services/audit.py` | ✅ Creado | Sistema de auditoría |
| `core/documents.py` | `src/services/documents.py` | ✅ Creado | Documentos y numeración de series |
| `core/partners.py` | `src/services/partners.py` | ✅ Creado | Gestión de clientes/proveedores |
| `core/backup.py` | `src/utils/backup.py` | ✅ Creado | Backup y restauración |
| `core/reports.py` | *(Pendiente)* | ⏳ Pendiente | Se integrará en inventory.py y services/reports.py |

### Interfaz Gráfica
| Origen | Destino | Estado | Cambios Principales |
|--------|---------|--------|----------------------|
| `app/gui.py` | `src/app/main_window.py` | ⏳ Pendiente | Requiere copiar y actualizar imports |
| `diseño/estilo.py` | `src/app/styles/estilo.py` | ✅ Creado | Sin cambios funcionales |
| `diseño/scrollbars.py` | `src/app/styles/scrollbars.py` | ✅ Creado | Sin cambios funcionales |

### Herramientas y Utilidades
| Origen | Destino | Estado | Cambios Principales |
|--------|---------|--------|----------------------|
| `tools/rbac_fix.py` | *(Mantener)* | ⏳ Mantener | Actualizar importes según necesidad |
| `tools/migrate_sqlite_to_mysql.py` | *(Mantener)* | ⏳ Mantener | Actualizar importes según necesidad |

### Puntos de Entrada
| Origen | Destino | Estado | Cambios Principales |
|--------|---------|--------|----------------------|
| `main.py` | `main.py` | ✅ Actualizado | Apunta a src/*; error handling |
| `cli.py` | `cli.py` | ✅ Actualizado | Apunta a src/*; error handling |

---

## ESTRUCTURA CREADA

### Directorios Nuevos
```
src/
├── __init__.py
├── app/
│   ├── __init__.py
│   ├── main_window.py        (⏳ Pendiente: copiar app/gui.py)
│   └── styles/
│       ├── __init__.py
│       ├── estilo.py         (✅ Creado)
│       └── scrollbars.py     (✅ Creado)
├── core/
│   ├── __init__.py           (✅ Recreado)
│   └── auth.py               (✅ Creado)
├── database/
│   ├── __init__.py           (✅ Creado)
│   ├── connection.py         (✅ Creado)
│   └── settings.py           (✅ Creado)
├── models/
│   └── __init__.py           (✅ Creado - futuro uso)
├── services/
│   ├── __init__.py           (✅ Creado)
│   ├── inventory.py          (✅ Creado)
│   ├── audit.py              (✅ Creado)
│   ├── documents.py          (✅ Creado)
│   └── partners.py           (✅ Creado)
├── utils/
│   ├── __init__.py           (✅ Creado)
│   └── backup.py             (✅ Creado)
└── assets/                   (✅ Creado - vacío)

tests/
├── __init__.py               (✅ Creado - vacío)

docs/
└── ARCHITECTURE.md           (✅ Creado)
```

---

## CAMBIOS EN IMPORTES

### Patrón de Actualización

**ANTES:**
```python
from core.database import get_connection, init_db
from core.auth import LoginDialog, ensure_defaults
from core.services import add_product, post_sale
from core.audit import log_event
from diseño.estilo import aplicar_estilo_treeview
```

**DESPUÉS:**
```python
from src.database.connection import get_connection, init_db
from src.core.auth import LoginDialog, ensure_defaults
from src.services.inventory import add_product, post_sale
from src.services.audit import log_event
from src.app.styles.estilo import aplicar_estilo_treeview
```

### Listado de Cambios por Archivo

#### **src/database/connection.py**
- `from .database import get_connection` → (dentro del archivo)
- Rutas centralizadas: `DB_PATH = os.path.join(DATA_DIR, "inventario.db")`

#### **src/core/auth.py**
- `from .database import get_connection` → `from ..database.connection import get_connection`
- Importes relativos (`..database`) para subpaquetes

#### **src/services/inventory.py**
- `from .database import get_connection` → `from ..database.connection import get_connection`
- `from .audit import log_event` → `from .audit import log_event` (relativo local)
- `from .documents import get_next_number` → mismo nivel
- `from .partners import get_partner_by_code` → mismo nivel
- `from .settings import get_settings` → `from ..database.settings import get_settings`

#### **src/services/audit.py**
- `from .database import get_connection` → `from ..database.connection import get_connection`

#### **src/services/documents.py**
- `from .database import get_connection` → `from ..database.connection import get_connection`

#### **src/services/partners.py**
- `from .database import get_connection` → `from ..database.connection import get_connection`

#### **src/utils/backup.py**
- `from ..database.connection import get_connection, DB_PATH, DB_ENGINE`

---

## CAMBIOS EN RUTAS DE ARCHIVOS

### Rutas de Base de Datos
- **ANTES**: `data/inventario.db` (ruta relativa variable)
- **DESPUÉS**: `src/database/inventario.db` (centralizado)
- **Configuración**: Via ENV `DB_PATH` o default centralizado

### Rutas de Logos/Assets
- **ANTES**: `../assets/` (relativas desde app/gui.py)
- **DESPUÉS**: `src/assets/` (relativas desde main.py)
- **En GUI**: Se calculará en `main_window.py` como:
  ```python
  ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
  ```

---

## FUNCIONALIDAD PRESERVADA

✅ **Se mantiene sin cambios**:
- Lógica de negocio (CRUD, movimientos)
- Autenticación y RBAC
- Cálculo de impuestos
- Sistema de numeración de documentos
- Auditoría y logging
- Exportaciones (CSV, XLSX, PDF)
- Backups

⚠️ **En revisión**:
- GUI (app/gui.py debe copiarse a src/app/main_window.py)
- Reportes (core/reports.py debe integrarse)

---

## PENDIENTES (TODO)

### 1. **Copiar y Adaptar GUI**
```bash
# Copiar app/gui.py a src/app/main_window.py
# Actualizar imports:
#   from core.* → from src.core.*
#   from diseño.* → from src.app.styles.*
```

### 2. **Crear/Integrar reports.py**
- Leer `core/reports.py` (función `kardex_rows`, exportaciones)
- Crear `src/services/reports.py`
- Actualizar imports

### 3. **Limpieza de Archivos Antiguos**
- Eliminar `core/` (duplicado en src/core)
- Eliminar `app/gui.py` (reemplazado por src/app)
- Eliminar `diseño/` (reemplazado por src/app/styles)
- Eliminar backups: `.venv/`, `__pycache__/`, `main copy.py`
- Consolidar `data/inventario.db` a `src/database/`

### 4. **Tests**
- Crear tests en `tests/test_inventory.py`
- Crear tests en `tests/test_auth.py`
- Crear tests en `tests/test_documents.py`

### 5. **Migraciones**
- Crear `src/database/migrations.py`
- Función `migrate()` que sea idempotente

### 6. **Documentación**
- Actualizar README.md con nuevos paths
- Crear CONTRIBUTING.md
- Crear API.md

---

## MODELO DE IMPORTES EN `main.py`

```python
import sys
from pathlib import Path

# Agregar src al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Ahora se puede importar directamente
from src.database.connection import init_db
from src.core.auth import ensure_defaults
from src.services.partners import ensure_schema as ensure_partners_schema
```

---

## VARIABLES DE ENTORNO

### Antes (no centralizado)
```bash
DB_ENGINE=sqlite
DB_PATH=data/inventario.db
DB_HOST=localhost
DB_USER=root
DB_PASS=password
```

### Después (mismo, pero paths mejor documentados)
```bash
DB_ENGINE=sqlite
DB_PATH=src/database/inventario.db      # Centralizado
DB_HOST=localhost
DB_USER=root
DB_PASS=password
DB_POOL_SIZE=5
```

---

## MATRIZ DE ESTADO

| Tarea | Estado | Prioridad | Responsabilidad |
|-------|--------|-----------|-----------------|
| Crear estructura /src | ✅ 100% | 🔴 Crítica | COMPLETADO |
| Mover database.py | ✅ 100% | 🔴 Crítica | COMPLETADO |
| Mover auth.py | ✅ 100% | 🔴 Crítica | COMPLETADO |
| Mover services (inventory) | ✅ 100% | 🔴 Crítica | COMPLETADO |
| Mover audit.py | ✅ 100% | 🔴 Crítica | COMPLETADO |
| Mover documents.py | ✅ 100% | 🔴 Crítica | COMPLETADO |
| Mover partners.py | ✅ 100% | 🔴 Crítica | COMPLETADO |
| Mover backup.py | ✅ 100% | 🟡 Alta | COMPLETADO |
| Mover styles | ✅ 100% | 🟡 Alta | COMPLETADO |
| Copiar app/gui.py | ⏳ 0% | 🔴 Crítica | PENDIENTE |
| Actualizar main.py | ✅ 100% | 🔴 Crítica | COMPLETADO |
| Actualizar cli.py | ✅ 100% | 🔴 Crítica | COMPLETADO |
| Crear docs/ARCHITECTURE.md | ✅ 100% | 🟡 Alta | COMPLETADO |
| Crear mapping | ✅ 100% | 🟡 Alta | COMPLETADO |
| Limpiar archivos antiguos | ⏳ 0% | 🟢 Media | PENDIENTE |
| Crear tests | ⏳ 0% | 🟢 Media | PENDIENTE |
| Crear migraciones | ⏳ 0% | 🟢 Media | PENDIENTE |

---

## INSTRUCCIONES PARA COMPLETAR LA REORGANIZACIÓN

### Paso 1: Copiar GUI (CRÍTICO)
```bash
# Copiar app/gui.py a src/app/
cp app/gui.py src/app/main_window.py

# Actualizar imports en main_window.py
# - from core.* → from src.core.*
# - from diseño.* → from src.app.styles.*
# - from app.* → local imports
```

### Paso 2: Integrar Reports
```bash
# Leer core/reports.py
# Crear src/services/reports.py con:
#   - kardex_rows()
#   - export_kardex_xlsx()
#   - export_kardex_pdf()

# Actualizar src/services/__init__.py con exports
```

### Paso 3: Probar Aplicación
```bash
cd /path/to/Inventario
python main.py
```

### Paso 4: Limpiar
```bash
# Eliminar estructura antigua
rm -rf core/ app/gui.py diseño/
rm -f main\ copy.py

# Mantener archivos en tools/ (utilitarios)
```

### Paso 5: Actualizar .gitignore
```
.venv/
__pycache__/
*.pyc
*.db-journal
data/*.db
src/assets/        # Si tiene imágenes grandes
```

---

## NOTAS IMPORTANTES

### ⚠️ Cambios que Requieren Atención

1. **Rutas de Base de Datos**:
   - La BD ahora se busca en `src/database/inventario.db`
   - Si ya existe en `data/inventario.db`, copiar manualmente:
     ```bash
     cp data/inventario.db src/database/
     ```

2. **Rutas de Assets (Logo)**:
   - El logo debe estar en `src/assets/`
   - Actualizar la ruta en src/app/main_window.py

3. **Importes Relativos**:
   - Dentro de `src/*`, usar importes relativos: `from ..database.connection`
   - En archivos raíz (main.py, cli.py), usar: `from src.database.connection`

4. **Variables de Entorno**:
   - Si usabas ENV vars para DB_PATH, asegúrate que apunten a `src/database/`

### ✅ Lo Que Funciona Igual

- Toda la lógica de negocio
- Sistema de RBAC
- Auditoría
- Backups
- Exportaciones

### 🔧 Lo Que Necesita Actualización Manual

- GUI (app/gui.py → src/app/main_window.py)
- Reports (core/reports.py → src/services/reports.py)
- Rutas de assets (logos, imágenes)

---

## PRÓXIMAS MEJORAS

1. **Actualizar Hash de Contraseñas**: SHA256 → bcrypt
2. **ORM**: Considerar SQLAlchemy en src/models/
3. **API REST**: Agregar FastAPI como alternativa a Tkinter
4. **Tests**: 100% cobertura en src/services/
5. **CI/CD**: GitHub Actions para testing automático
6. **Documentación**: Swagger para APIs

---

**Última actualización**: 2025-11-30
**Responsable**: Reorganización Arquitectónica
**Versión del Proyecto**: 2.0.0
