# 📖 Índice de Documentación - Alfa & Omega v2.0

Bienvenido a la versión reorganizada de Alfa & Omega. Esta guía te ayudará a navegar la documentación.

---

## 🚀 Comenzar Rápido (2 minutos)

> 📦 **Empaquetado**
> Para crear un instalador profesional simplemente ejecutes:
> ```bash
> pip install pyinstaller            # entorno dev
> python scripts/build_installer.py
> ```
> Aparecerá `dist/AlfaOmega.exe` listo para distribuir.
>
> 🔒 **Licencias & Actualizaciones**
> El software verifica que exista un archivo `config/license.key` válido y consulta `version.json` para detectar nuevas versiones. Usa `src/core/license_manager.py` y `src/core/update_manager.py`.
>
> 📈 **Métricas**
> Eventos y contadores se registran en `logs/metrics.log` mediante `src/core/metrics.py`. Útil para análisis y soporte.

## 🚀 Comenzar Rápido (2 minutos)

1. **Iniciar la aplicación**:
   ```bash
   python main.py
   ```
   - Usuario: `admin`
   - Contraseña: `admin123`

2. **Leer**: 
   - 📄 [`READY_FOR_PRODUCTION.md`](READY_FOR_PRODUCTION.md) - Guía rápida de inicio

---

## 📚 Documentación Principal

### Para Usuarios
- 📄 [`README.md`](README.md) - Guía general de uso, instalación y CLI

### Para Desarrolladores
- 📄 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - **Documentación técnica detallada**
  - Estructura de directorios (`/src`)
  - Componentes principales
  - Relaciones entre módulos
  - Flujos de datos
  - Esquema de base de datos
  - Importes (antes vs después)

- 📄 [`docs/MIGRATION_SUMMARY.md`](docs/MIGRATION_SUMMARY.md) - **Resumen de cambios v2.0**
  - Qué cambió
  - Archivos movidos
  - Importes actualizados
  - Validaciones realizadas
  - Próximos pasos

- 📄 [`FINAL_REPORT.md`](FINAL_REPORT.md) - **Informe completo de la migración**
  - Métricas del proyecto
  - Cambios realizados
  - Funcionalidades preservadas
  - Tests realizados
  - Guía de uso

---

## 🎯 Búscate en Esta Categoría

### Soy usuario final y quiero iniciar la aplicación
→ Leer: [`README.md`](README.md) sección "Uso"

### Soy desarrollador y necesito entender la arquitectura
→ Leer: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

### Quiero conocer qué cambió en esta versión
→ Leer: [`docs/MIGRATION_SUMMARY.md`](docs/MIGRATION_SUMMARY.md)

### Necesito verificar que todo funciona
→ Leer: [`READY_FOR_PRODUCTION.md`](READY_FOR_PRODUCTION.md)

### Tengo un problema o error
→ Ver sección "Troubleshooting" en [`README.md`](README.md)

### Quiero migrar código antiguo
→ Ver "[Importes - Antes vs Después]" en [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

### Debo limpiar directorios antiguos
→ Ejecutar: `python cleanup.py`

---

## 📁 Estructura de Directorios Rápida

```
src/                          # Código nuevo (v2.0)
├── database/                 # Acceso a datos
├── core/                     # Lógica central
├── services/                 # Servicios de negocio
├── app/                      # GUI (Tkinter)
└── utils/                    # Funciones auxiliares

docs/                         # Documentación técnica
├── ARCHITECTURE.md           # Arquitectura del sistema
└── MIGRATION_SUMMARY.md      # Resumen de cambios

README.md                     # Guía principal
READY_FOR_PRODUCTION.md       # Quick start
FINAL_REPORT.md               # Informe completo
cleanup.py                    # Script para limpieza
```

---

## ⚡ Comandos Útiles

```bash
# Iniciar aplicación
python main.py

# Usar CLI
python cli.py run-gui                 # Inicia GUI
python cli.py ensure-rbac             # Configura RBAC  
python cli.py migrate-db              # Migra a MySQL

# Limpiar directorios antiguos
python cleanup.py

# Validar que todo funciona
python -c "from src.core import configure_logging; print('✓ OK')"
```

---

## 🔍 Búsqueda de Documentación

| Busco... | Archivo | Sección |
|----------|---------|---------|
| Cómo iniciar | README.md | "Uso" |
| Estructura técnica | ARCHITECTURE.md | "Estructura de Carpetas" |
| Cambios v2.0 | MIGRATION_SUMMARY.md | "Cambios Realizados" |
| Importes actualizados | ARCHITECTURE.md | "Importes - Antes vs Después" |
| Base de datos | ARCHITECTURE.md | "Base de Datos - Tablas" |
| CLI disponible | README.md | "Comandos disponibles en la CLI" |
| Troubleshooting | README.md | "Troubleshooting" |
| Credenciales | README.md | "Credenciales por defecto" |
| Variables de entorno | README.md | "Configuración - Variables de Entorno" |
| Próximos pasos | FINAL_REPORT.md | "Próximos Pasos Recomendados" |

---

## 📞 Soporte Rápido

### Error: "ModuleNotFoundError"
→ Ejecutar: `pip install -r requirements.txt`

### Error: "No se encuentra tkinter"
→ Ver README.md: "Error: No module named 'tkinter'"

### No se inicia la GUI
→ Ver README.md: "Troubleshooting"

### Necesito cambiar contraseña
→ Ver ARCHITECTURE.md: "LoginDialog"

### Quiero usar MySQL
→ Ver README.md: "Configuración de variables de entorno" → "Ejemplo: usar MySQL"

---

## ✅ Validación

**¿Cómo sé que está todo bien?**

Ejecutar:
```bash
python -c "from src.database.connection import init_db; from src.core.auth import ensure_defaults; init_db(); ensure_defaults(); print('✅ SISTEMA VALIDADO')"
```

Deberías ver: `✅ SISTEMA VALIDADO`

---

## 🎉 Conclusión

La reorganización v2.0 está completa y lista para producción.

**Próximo paso**: [`README.md`](README.md) → "Uso" → `python main.py`

---

**Última actualización**: 2025-01-15  
**Versión**: 2.0.0  
**Estado**: ✅ Producción lista
