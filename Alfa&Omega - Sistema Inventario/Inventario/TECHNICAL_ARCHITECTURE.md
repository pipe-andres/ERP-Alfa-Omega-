# Arquitectura Técnica del Sistema

Este documento describe la estructura interna del software, dirigido a desarrolladores o responsables técnicos.

## Componentes Principales

- **`main.py`**: punto de entrada; inicializa configuraciones y lanza la interfaz.
- **`config/settings.py`**: centraliza todas las variables de configuración (entorno, rutas, base de datos, logging, puertos).
- **`src/database/`**:
  - `connection.py`: adaptador legacy para SQLite/MySQL/Postgres.
  - `create_indexes.py`: script de optimización de índices.
  - `settings.py`: gestión de parámetros de empresa (tax, nombre, logo).
  - `orm.py` (no modificado en esta fase) ofrece la capa SQLAlchemy asincrónica.
- **`src/core/`**:
  - `validators.py`: validación de entradas.
  - `error_handler.py`: logger y excepciones personalizadas.
  - `auth.py` y `acl.py`: autenticación y control de acceso.
  - `caching.py`: cache en memoria opcional.
- **`src/services/`**: lógica de negocio (inventario, facturación, usuarios, etc.).
- **`src/utils/`**: utilidades como backups.
- **`app/gui.py`**: interfaz Tkinter.

## Flujo de Datos

1. El usuario interactúa con la GUI.
2. Los eventos invocan funciones en `src/services/*`.
3. Los servicios validan entradas mediante `src/core/validators`.
4. Las operaciones se ejecutan sobre la base de datos a través de la capa `connection` o `orm`.
5. Todas las operaciones críticas registran auditoría y errores en `logs/sistema.log`.
6. Backups automáticos son generados por `src/utils/database_backup`.

## Configuración y Entornos

- Las variables se cargan desde `config/settings.py`, que a su vez lee `.env` si existe.
- Cambiar de `ENV=dev` a `ENV=prod` en `.env` ajusta `DEBUG`, `LOG_LEVEL` y otras banderas sin tocar el código.
- La migración a PostgreSQL o MySQL se controla con `DB_ENGINE` en el mismo archivo.

## Extensibilidad

- **Modularidad**: cada prestación está separada en servicios y módulos.
- **Base de datos**: para escalar se puede cambiar a PostgreSQL mediante la variable de entorno; la lógica de datos es agnóstica.
- **Migraciones**: el proyecto incluye soporte Alembic para futuras versiones.

## Escalabilidad

- Aunque el core es sincrónico, el proyecto dispone de rutas async/SQLAlchemy para un eventual paso a servidores web.
- La separación de configuración y dependencias facilita el despliegue en contenedores o VPS.

---
Este documento debería acompañar la entrega técnica y aclarar a futuros desarrolladores cómo está construido el producto.
