# Migración de SQLite a PostgreSQL - Guía Paso a Paso

## Introducción

Esta guía documenta cómo migrar la base de datos de inventario desde **SQLite** (configuración de desarrollo actual) a **PostgreSQL** (para producción/staging). Todo está preparado con SQLAlchemy async y Alembic para que la migración sea fluida.

## Prerequisitos

### 1. Instalar PostgreSQL
- **Windows**: Descargar desde [postgresql.org](https://www.postgresql.org/download/windows/)
- **macOS**: `brew install postgresql@15`
- **Linux**: `sudo apt-get install postgresql postgresql-contrib`

Verificar instalación:
```bash
psql --version
```

### 2. Crear usuario y base de datos PostgreSQL

```bash
# Conectarse como superuser
psql -U postgres

# En la consola psql:
CREATE USER inv_user WITH PASSWORD 'secure_password_here';
CREATE DATABASE inventario_db OWNER inv_user;
GRANT ALL PRIVILEGES ON DATABASE inventario_db TO inv_user;
\q
```

Verificar que el usuario puede conectarse:
```bash
psql -U inv_user -d inventario_db -h localhost
```

### 3. Instalar dependencias Python

Las dependencias async para PostgreSQL ya están en `requirements.txt`:
```bash
pip install asyncpg psycopg2-binary
```

Si aún no instalaste:
```bash
pip install -r requirements.txt
```

## Pasos de Migración

### Paso 1: Actualizar variable de entorno `.env`

Cambiar la `DATABASE_URL` de SQLite a PostgreSQL:

**Antes (SQLite - desarrollo actual):**
```env
DATABASE_URL=sqlite+aiosqlite:///./data/inventario_temp.db
```

**Después (PostgreSQL):**
```env
DATABASE_URL=postgresql+asyncpg://inv_user:secure_password_here@localhost:5432/inventario_db
```

### Paso 2: Verificar conexión

Crear un script de prueba rápido (`test_pg_connection.py`):

```python
import asyncio
from src.database.orm import engine

async def test_connection():
    async with engine.begin() as conn:
        result = await conn.execute("SELECT 1")
        print("✓ Conexión a PostgreSQL exitosa")

asyncio.run(test_connection())
```

Ejecutar:
```bash
python test_pg_connection.py
```

### Paso 3: Crear esquema en PostgreSQL

Si es la primera vez que usas PostgreSQL, ejecutar Alembic para crear todas las tablas:

```bash
alembic upgrade head
```

Esto aplicará todas las migraciones existentes (incluyendo la inicial `a1ef4fc0ca35_init.py`) a PostgreSQL.

**Nota:** Si ya tienes datos en SQLite y deseas migrarlos, ver Paso 5 (Migración de datos).

### Paso 4: Cambiar el DSN en código (si es necesario)

La mayoría del código lee `DATABASE_URL` de `.env`, así que solo cambiar el archivo `.env` es suficiente. Verificar:

- `src/database/orm.py` usa `os.getenv('DATABASE_URL')` ✓
- Alembic env.py lee `DATABASE_URL` del `.env` ✓

### Paso 5: Migración de datos (opcional - solo si tienes datos en SQLite)

Si deseas preservar datos de SQLite, seguir estos pasos:

#### Opción A: Exportar desde SQLite e importar en PostgreSQL

```bash
# 1. Exportar todas las tablas de SQLite como SQL
# (Usar un cliente SQLite o herramientas como DB Browser)

# 2. Importar en PostgreSQL
psql -U inv_user -d inventario_db < dump.sql
```

#### Opción B: Usar un script Python para sincronizar

Crear `scripts/migrate_data.py`:

```python
import asyncio
from src.database.orm import get_async_session
from src.database.models import Product, Partner, Document, etc.
from sqlalchemy import select

async def migrate():
    async with get_async_session() as session:
        # Leer desde vieja conexión (SQLite)
        # Escribir a nueva conexión (PostgreSQL)
        # Implementar lógica de sincronización
        pass

asyncio.run(migrate())
```

## Rollback (Volver a SQLite)

Si necesitas revertir a SQLite para desarrollo:

1. Cambiar `.env`:
```env
DATABASE_URL=sqlite+aiosqlite:///./data/inventario_temp.db
```

2. El código ya soporta ambos drivers sin cambios adicionales.

## Verificación Post-Migración

### 1. Validar esquema
```bash
psql -U inv_user -d inventario_db

# En psql:
\dt  # Listar todas las tablas
\d productos  # Describir tabla específica
SELECT COUNT(*) FROM productos;  # Contar registros
```

### 2. Ejecutar smoke test
```bash
python scripts/smoke_check.py
```

Esperado:
```
✓ Inserción exitosa
✓ Lectura exitosa
✓ Total de productos: X
```

### 3. Ejecutar tests
```bash
pytest tests/test_async_transactions_v2.py -v
```

Esperado: 7/7 tests PASANDO

## Troubleshooting

### Error: `psycopg2.OperationalError: FATAL: role "inv_user" does not exist`

Solución: Crear usuario en PostgreSQL
```bash
psql -U postgres
CREATE USER inv_user WITH PASSWORD 'secure_password_here';
```

### Error: `asyncpg.exceptions.DuplicateTableError: table "productos" already exists`

Solución: Las tablas ya existen. Si necesitas limpiar:
```bash
psql -U inv_user -d inventario_db
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

Luego re-ejecutar:
```bash
alembic upgrade head
```

### Error: `sqlalchemy.exc.NotImplementedError: Asyncio layer requires python 3.7+`

Solución: Actualizar Python a 3.7+ (recomendado: 3.10+)

## Consideraciones de Producción

### 1. Variables de entorno seguras

**NO** commitar credenciales en `.env`. Usar:
- AWS Secrets Manager
- HashiCorp Vault
- Variables de entorno del servidor
- `.env.example` (template sin valores reales)

### 2. Backups PostgreSQL

```bash
# Backup completo
pg_dump -U inv_user -d inventario_db > backup.sql

# Restore
psql -U inv_user -d inventario_db < backup.sql
```

### 3. Índices y optimización

Para producción, considerar:
```sql
-- Índices para queries frecuentes
CREATE INDEX idx_producto_codigo ON productos(codigo);
CREATE INDEX idx_documento_tipo ON documents(tipo);
CREATE INDEX idx_kardex_producto ON kardex_moves(product_code);
```

### 4. Connection pooling

Para aplicaciones multi-usuario, usar pgbouncer o similar:
```bash
sudo apt-get install pgbouncer
# Configurar /etc/pgbouncer/pgbouncer.ini
```

## Próximos pasos

1. **FASE 2: REST API** - Crear capa HTTP con FastAPI
2. **FASE 2: UI async** - Refactorizar Tkinter para usar async services
3. **FASE 2: RBAC avanzado** - Implementar control de roles y permisos
4. **FASE 2: Docker** - Containerizar app + PostgreSQL para deployment

## Referencia rápida

| Acción | Comando |
|--------|---------|
| Crear migración nueva | `alembic revision --autogenerate -m "nombre"` |
| Aplicar migraciones | `alembic upgrade head` |
| Ver historial | `alembic history` |
| Revertir última migración | `alembic downgrade -1` |
| Conectarse a DB | `psql -U inv_user -d inventario_db` |

## Soporte

Para preguntas o problemas:
- Revisar logs de Alembic: `alembic current`
- Revisar estado de SQLAlchemy: `python -c "from src.database.orm import engine; print(engine)"`
- Consultar documentación oficial: [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
