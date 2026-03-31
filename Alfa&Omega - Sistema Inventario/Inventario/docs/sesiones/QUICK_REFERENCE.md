# ⚡ REFERENCIA RÁPIDA - Alfa & Omega v2.0

## 🟢 Estado: LISTO PARA PRODUCCIÓN

---

## ⚡ Comandos Principales

| Comando | Descripción |
|---------|-------------|
| `python main.py` | 🚀 Inicia la aplicación GUI |
| `python cli.py run-gui` | Inicia GUI desde CLI |
| `python cli.py ensure-rbac` | Configura/verifica RBAC |
| `python cli.py migrate-db` | Migra BD de SQLite a MySQL |
| `python cleanup.py` | Elimina directorios antiguos |
| `pip install -r requirements.txt` | Instala todas las dependencias |

---

## 👤 Credenciales Iniciales

```
Usuario: admin
Contraseña: admin123
```

⚠️ **Cambiar en producción**

---

## 📂 Estructura Clave

```
src/                  ← NUEVO (v2.0)
├── database/         BD y settings
├── core/             Auth y RBAC
├── services/         Lógica de negocio
├── app/              GUI Tkinter
└── utils/            Funciones auxiliares

docs/                 ← Documentación
├── ARCHITECTURE.md   Documentación técnica
└── MIGRATION_SUMMARY.md  Cambios v2.0
```

---

## 📚 Documentos Principales

| Documento | Leer cuando... |
|-----------|---|
| **DOCUMENTACION.md** | Necesitas orientación general |
| **README.md** | Quieres usar la aplicación |
| **docs/ARCHITECTURE.md** | Necesitas entender la estructura |
| **FINAL_REPORT.md** | Quieres ver métricas completas |
| **READY_FOR_PRODUCTION.md** | Necesitas quick start |

---

## 🐍 Importes Principales (v2.0)

```python
# Base de datos
from src.database.connection import get_connection, init_db
from src.database.settings import get_settings, update_settings

# Autenticación
from src.core.auth import LoginDialog, ensure_defaults, has_perm

# Servicios
from src.services.inventory import add_product, post_sale
from src.services.documents import ensure_schema
from src.services.audit import log_event
from src.services.partners import create_partner
from src.services.reports import kardex_rows

# Utilidades
from src.utils.backup import backup_db, restore_db

# Logging
from src.core import configure_logging
```

---

## 🔧 Variables de Entorno (Opcional)

```bash
# Para MySQL
export DB_ENGINE=mysql
export DB_HOST=localhost
export DB_USER=root
export DB_PASS=password
export DB_NAME=inventario
export DB_POOL_SIZE=5

# Para SQLite (por defecto)
# DB_ENGINE=sqlite
# DB_PATH=data/inventario.db
```

---

## ✅ Checklist de Validación

- [ ] `python main.py` inicia sin errores
- [ ] Login con `admin/admin123` funciona
- [ ] Puedo crear un producto
- [ ] Puedo registrar una venta
- [ ] Puedo ver reportes
- [ ] CLI funciona: `python cli.py --help`

---

## 🆘 Problemas Comunes

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| No se inicia GUI | Verifica tkinter: Linux: `sudo apt install python3-tk` |
| BD corrupta | `rm data/inventario.db && python main.py` |
| Puerto ocupado | Cambia `DB_PORT` en variables de entorno |

---

## 📊 Características (100% Funcionales)

✅ Gestión de productos (CRUD)  
✅ Compras, ventas y ajustes  
✅ Numeración de series  
✅ Auditoría de eventos  
✅ Reportes (Kardex, inventario)  
✅ RBAC (usuarios, roles, permisos)  
✅ Backup/restauración  
✅ Exportación CSV/XLSX/PDF  

---

## 🚀 Siguiente Paso

```bash
python main.py
```

**¡Listo para usar!**

---

**v2.0** | 2025-01-15 | ✅ Producción
