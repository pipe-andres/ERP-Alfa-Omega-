# Architecture

## Layers
UI (src/app/)
  ↓ llama a
Services (src/services/)
  ↓ llama a
Data Access (src/database/repository.py + connection.py)
  ↓ accede a
Database (src/data/inventario.db)

## Rules
- UI solo llama servicios, nunca accede a BD directamente
- Servicios contienen toda la lógica de negocio
- repository.py contiene queries reutilizables con caché
- connection.py es la ÚNICA fuente de verdad del schema

## Cache Layer
src/core/caching.py → CacheManager LRU 256 entradas, TTL configurable,
thread-safe RLock. Decorador @cached sobre funciones de repository.
Invalidar con invalidate_prefix("prefijo:") tras writes.

## Auth/RBAC
Login: auth.LoginDialog → verifica usuarios tabla → crea sesión user dict
Permisos: acl.has_permission(user, "permiso") antes de acciones críticas
Roles: ADMIN (todo), USER (operación), AUDITOR (solo lectura)

## Application Flow
main.py → init_db() → LoginDialog → InventarioApp(main_window)
  → menús → _open_Xwindow() → XWindow(root, user) → wait_window()