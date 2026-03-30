# Arquitectura del Sistema de Inventario - Alfa & Omega

## Descripción General

El sistema ha sido reorganizado siguiendo una arquitectura moderna y escalable de Python, separando claramente las responsabilidades en capas:

- **Presentación (GUI)**: Interfaz de usuario con Tkinter
- **Servicios/Lógica de Negocio**: CRUD de productos, movimientos, documentos
- **Base de Datos**: Acceso a datos y configuración
- **Autenticación**: Control de acceso basado en roles (RBAC)
- **Utilidades**: Funciones auxiliares reutilizables

## Estructura de Carpetas

```
Inventario/
├── src/                              # Código fuente principal
│   ├── __init__.py
│   ├── app/                          # Interfaz gráfica de usuario
│   │   ├── __init__.py
│   │   ├── main_window.py            # Ventana principal (pendiente de crear)
│   │   └── styles/                   # Estilos y temas visuales
│   │       ├── __init__.py
│   │       ├── estilo.py
│   │       └── scrollbars.py
│   ├── core/                         # Lógica central
│   │   ├── __init__.py               # configure_logging()
│   │   └── auth.py                   # Autenticación, RBAC, dialogs de login
│   ├── database/                     # Acceso a datos
│   │   ├── __init__.py
│   │   ├── connection.py             # Conexiones SQLite/MySQL
│   │   └── settings.py               # Configuración de empresa
│   ├── services/                     # Servicios de negocio
│   │   ├── __init__.py
│   │   ├── inventory.py              # CRUD de productos, movimientos
│   │   ├── audit.py                  # Registro de auditoría
│   │   ├── documents.py              # Documentos y numeración de series
│   │   └── partners.py               # Clientes y proveedores
│   ├── models/                       # Modelos de datos (dataclasses, ORM)
│   │   └── __init__.py               # (Futuro uso)
│   ├── utils/                        # Funciones auxiliares
│   │   ├── __init__.py
│   │   └── backup.py                 # Backup y restauración
│   └── assets/                       # Imágenes, íconos, recursos
├── tests/                            # Pruebas unitarias
│   └── __init__.py
├── docs/                             # Documentación
│   └── ARCHITECTURE.md               # Este archivo
├── main.py                           # Punto de entrada (GUI)
├── cli.py                            # Interfaz de línea de comandos
├── requirements.txt                  # Dependencias
├── README.md                         # Documentación del usuario
└── data/
    └── inventario.db                 # Base de datos SQLite (centralizada)
```

## Componentes Principales

### 1. **src/database/** - Capa de Acceso a Datos

#### `connection.py`
- **Clase/Función**: `get_connection()` (context manager)
- **Responsabilidad**: Gestionar conexiones a SQLite/MySQL
- **Características**:
  - Pool de conexiones para MySQL
  - Context manager para manejo seguro
  - PRAGMA configuradas para SQLite (foreign_keys, WAL, synchronous)
- **Funciones de inicialización**:
  - `init_db()`: Crea todas las tablas
  - `init_rbac()`: Crea tablas de RBAC (usuarios, roles, permisos)

#### `settings.py`
- **Responsabilidad**: Gestionar configuración de la empresa
- **Funciones**:
  - `get_settings()`: Obtiene configuración actual
  - `update_settings()`: Actualiza valores
  - `ensure_schema()`: Asegura tabla de configuración

### 2. **src/core/** - Lógica Central

#### `__init__.py`
- **Función**: `configure_logging()` - Configura logging del proyecto

#### `auth.py`
- **Responsabilidad**: Autenticación y autorización
- **Funciones principales**:
  - `ensure_defaults()`: Crea roles/permisos/admin por defecto
  - `_hash_password()` / `_verify_password()`: Hashing SHA256 con salt
  - `create_user()`, `set_user_roles()`, `reset_password()`: Gestión de usuarios
  - `has_perm()`: Verificación de permisos
- **Diálogos GUI**:
  - `LoginDialog`: Diálogo de login
  - `ChangePasswordDialog`: Cambio de contraseña

### 3. **src/services/** - Servicios de Negocio

#### `inventory.py`
- **CRUD de Productos**:
  - `add_product()`, `update_product()`, `delete_product()`, `get_product()`
  - `list_products_page()`, `count_products()`
- **Movimientos de Stock**:
  - `post_purchase()`: Registra compra
  - `post_sale()`: Registra venta con cálculo de impuestos
  - `post_adjustment()`: Registra ajuste de stock
- **Importación/Exportación**:
  - `export_products_csv()`, `import_products_csv()`
  - `export_products_xlsx()`, `import_products_xlsx()`
  - `export_inventory_pdf()`, `export_low_stock_pdf()`

#### `documents.py`
- **Gestión de Documentos Comerciales**:
  - `ensure_schema()`: Crea tablas de documentos
  - `get_next_number()`: Obtiene siguiente número de serie
  - `seed_default_series()`: Crea series por defecto
- **Exportación**:
  - `export_purchase_pdf()`: PDF de compra
  - `export_sale_pdf()`: PDF de venta

#### `audit.py`
- **Bitácora de Auditoría**:
  - `log_event()`: Registra evento
  - `list_audit()`: Lista eventos con filtros
  - `export_audit_csv()`: Exporta auditoría a CSV

#### `partners.py`
- **Gestión de Clientes/Proveedores**:
  - `create_partner()`, `update_partner()`, `delete_partner()`
  - `get_partner_by_code()`, `list_partners()`
  - `ensure_schema()`: Crea tabla de partners

### 4. **src/app/** - Interfaz Gráfica

#### `main_window.py` (Pendiente de crear)
- Adaptación de `app/gui.py` con imports actualizados
- Importa desde estructura `src/*`

#### `styles/`
- `estilo.py`: Colores y configuración de temas
- `scrollbars.py`: Utilidades para agregar scrollbars

### 5. **src/utils/** - Utilidades

#### `backup.py`
- `backup_db()`: Crea backup de la BD
- `restore_db()`: Restaura desde backup

## Relaciones entre Módulos

```
┌─────────────────────────────────────────────────────────────┐
│  GUI (src/app/main_window.py)                               │
│  - Interfaz Tkinter                                          │
│  - Diálogos de login/cambio password                         │
└────────────────────┬────────────────────────────────────────┘
                     │ Importa servicios
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Services (src/services/)                                   │
│  ├─ inventory.py (productos, movimientos, PDFs)            │
│  ├─ documents.py (comprobantes, series)                     │
│  ├─ audit.py (bitácora)                                     │
│  └─ partners.py (clientes/proveedores)                      │
└────────────────────┬────────────────────────────────────────┘
                     │ Importa core + database
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Core + Database                                            │
│  ├─ core/auth.py (RBAC, usuarios)                           │
│  ├─ database/connection.py (BD)                             │
│  ├─ database/settings.py (config empresa)                   │
│  └─ utils/backup.py (backups)                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
             SQLite / MySQL
```

## Flujo de Datos

### 1. **Inicio de Aplicación** (main.py)
```
main()
  └─ configure_logging()
  └─ init_db()
  └─ ensure_defaults()          (crea RBAC)
  └─ ensure_partners_schema()   (crea partners)
  └─ ensure_settings_schema()   (crea settings)
  └─ InventarioApp(root)
      └─ LoginDialog()
```

### 2. **Login de Usuario**
```
LoginDialog._ok()
  └─ _fetch_user_with_roles()   (busca usuario + roles)
  └─ _verify_password()         (valida contraseña)
  └─ log_event()                (registra LOGIN en auditoría)
```

### 3. **Crear Producto**
```
GUI.crear_producto()
  └─ inventory.add_product()
      └─ get_connection().execute(INSERT)
      └─ log_event()            (registra PRODUCT_CREATE)
```

### 4. **Registrar Compra**
```
GUI.registrar_compra()
  └─ inventory.post_purchase()
      └─ documents.get_next_number()      (obtiene número de serie)
      └─ partners.get_partner_by_code()   (si aplica)
      └─ get_connection().execute(
           INSERT documents,
           INSERT document_lines,
           INSERT stock_movements,
           UPDATE productos
         )
      └─ log_event()            (registra DOC_PURCHASE)
```

### 5. **Exportar Reporte**
```
GUI.exportar_pdf()
  └─ inventory.export_inventory_pdf()
      └─ get_connection().execute(SELECT productos)
      └─ canvas.Canvas()         (crea PDF)
```

## Importes - Antes vs Después

### ANTES (Estructura antigua)
```python
from core.database import get_connection
from core.services import add_product, post_sale
from core.auth import LoginDialog, ensure_defaults
from core.audit import log_event
from diseño.estilo import aplicar_estilo_treeview
```

### DESPUÉS (Nueva estructura)
```python
from src.database.connection import get_connection, init_db
from src.services.inventory import add_product, post_sale
from src.core.auth import LoginDialog, ensure_defaults
from src.services.audit import log_event
from src.app.styles.estilo import aplicar_estilo_treeview
```

## Base de Datos - Tablas

### RBAC
- `users` (id, username, name, pass_hash, active)
- `roles` (id, name)
- `permissions` (id, code, description)
- `user_roles` (user_id, role_id)
- `role_permissions` (role_id, perm_id)

### Inventario
- `productos` (id, codigo, nombre, categoria, precio, cantidad, avg_cost)
- `partners` (id, code, kind, name, tax_id, phone, email, address, city, notes, active)
- `documents` (id, tipo, numero, fecha, notas, partner_id)
- `document_lines` (id, doc_id, codigo, qty, unit_cost, unit_price, reason)
- `stock_movements` (id, doc_id, codigo, qty, unit_cost, unit_price, tipo, reason, created_at)

### Sistema
- `company_settings` (id, company_name, company_tax, company_addr, tax_included, tax_rate, logo_path)
- `doc_series` (id, doc_type, series, prefix, next_no)
- `audit_log` (id, user_id, action, details, created_at)
- `historial` (id, codigo, nombre, accion, fecha)

## Configuración - Variables de Entorno

```bash
# Base de Datos
DB_ENGINE=sqlite          # or "mysql"
DB_PATH=src/database/inventario.db  # (SQLite)
DB_HOST=localhost         # (MySQL)
DB_NAME=inventario        # (MySQL)
DB_USER=root              # (MySQL)
DB_PASS=password          # (MySQL)
DB_POOL_SIZE=5            # (MySQL pool size)
```

## Migraciones - (Futuro)

Se planea crear `src/database/migrations.py` con:
- `create_tables_if_not_exist()`: Función idempotente
- Versionamiento de esquema
- Rollback de cambios

## Testing - (Futuro)

Ubicación: `tests/`
- Unit tests para servicios
- Integration tests para BD
- Tests de autenticación

## Pasos Siguientes

1. **Copiar app/gui.py → src/app/main_window.py** con imports actualizados
2. **Actualizar imports** en gui.py para usar `src.*`
3. **Crear modelo de datos** en `src/models/` (dataclasses)
4. **Implementar sistema de migraciones** en `src/database/migrations.py`
5. **Agregar tests** en `tests/`
6. **Documentación de API** en `docs/`

## Notas de Seguridad

- ✅ Contraseñas: SHA256 con salt (mejora: usar bcrypt)
- ✅ Auditoría: Todos los cambios se registran
- ✅ RBAC: Control granular de permisos
- ✅ SQL Injection: Uso de parámetros preparados
- ⚠️ Comunicación: Usar HTTPS en producción

## Compatibilidad

- Python 3.8+
- SQLite 3.7+
- MySQL 5.7+
- Tkinter (incluido con Python)
- Dependencias: mysql-connector-python, reportlab, openpyxl, bcrypt

---

**Última actualización**: 2025-11-30
**Versión**: 2.0.0
