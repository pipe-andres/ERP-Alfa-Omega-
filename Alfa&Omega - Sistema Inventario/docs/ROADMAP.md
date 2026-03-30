# Roadmap

## Phase 1 ✅ Q1 2026
- Devoluciones/nota de crédito
- Control de caja GUI completa
- 13 bugs corregidos, schema unificado
- Caché LRU thread-safe

## Phase 2 ✅ Q2 2026
- CRM Clientes
- Proveedores completo
- Órdenes de compra
- Reportes avanzados (P&L, ABC, Márgenes, Rotación)

## Phase 3 ✅ Completada — 2026-03-17
**Multi-tenant SaaS Core**
- Tarea 1: connection.py soporte dual SQLite/PostgreSQL con SET search_path
- Tarea 2: tenant_provisioning.py — create/drop/list_tenants
- Tarea 3A-C: FastAPI base + TenantMiddleware + JWT auth
- Tarea 4: Panel Super-Admin /tenants CRUD
- Tarea 5: plans.py — 4 planes (Free/Starter/Pro/Enterprise) + seeding
- Tarea 6: api/routers/plans.py — GET /plans/, POST /tenants/{id}/plan
- Tarea 7: Plan enforcement en services (límites usuarios/sucursales/productos)
- Tarea 8: services/onboarding.py — onboard_tenant() atómico
- Tarea 9: api/routers/admin.py — Panel Super-Admin 5 endpoints
- Tarea 10: Docker Compose dev local (Postgres 16 + pgAdmin)
- Tarea 11: Validación final Fase 3 — 18 tests pasando

---

## Phase 3.5 ✅ COMPLETADA — 2026-03-27
**ERP Completo + API Pública + UX Profesional**

### ERP Core (Tareas 12-25)
- Tarea 12: Dashboard rediseño — 4 zonas + KPIs reales
- Tarea 13: Filtro temporal hoy/semana/mes en Dashboard
- Tarea 14: Módulo Finanzas — CxC, CxP, Flujo de caja
- Tarea 15: Notificaciones inteligentes — alertas stock SMTP
- Tarea 16: API pública — 22 endpoints
- Tarea 17: Tests de negocio — suite completa
- Tarea 18: Rate limiting in-memory + API Keys SHA-256
- Tarea 19-25: Multi-sucursal, Predicción IA, DIAN, .exe PyInstaller

### Blueprint Cleanup (Tareas 43-48)
- Tarea 43: Compras período + Descuentos en dashboard ✅
- Tarea 44: Reportes consolidados multi-sucursal ✅
- Tarea 45: MRR/Churn + Impersonar tenant (audit log) ✅
- Tarea 46: Enforcement de planes por rol (ADMIN=enterprise) ✅
- Tarea 47: Línea de meta en gráfico de ventas ✅
- Tarea 48: Tour onboarding — botones con acciones reales ✅

**Estado final: 81 tests pasando · Blueprint 100% limpio**

---

## Phase 4 🔄 EN PROGRESO — 2026-03-28
**Infraestructura SaaS + UX Profesional**

### Infraestructura (Tareas 49-51)
- Tarea 49: CI/CD GitHub Actions (ci.yml + release.yml con .exe) ✅
- Tarea 50: API Docs completos Swagger v3.5.0 (summary/description) ✅
- Tarea 51: Sistema Trial 14 días + plan_expires_at en tenants ✅

### Inteligencia de Negocio (Tarea 52)
- Tarea 52: Ventana Inteligencia de Negocio ✅
  - Tab Anomalías (detección por desviación estándar)
  - Tab Canasta (market basket analysis)
  - Tab Clientes inactivos (retención)
  - Tab Precios dinámicos (sugerencias por rotación)
  - Exportar Excel en las 4 tabs

### UX Profesional (Tareas 53-64)
- Tarea 53: Tooltips en KPI cards Zona B y D del dashboard ✅
- Tarea 54: Atajos de teclado globales F1-F9 + accelerators en menú ✅
- Tarea 55: Exportar Excel en Inteligencia de Negocio ✅
- Tarea 56: Placeholder text en todos los campos de búsqueda ✅
- Tarea 57: Colores de estado en Órdenes de Compra ✅
- Tarea 58: Colores de estado en CRM, Proveedores, Caja ✅
- Tarea 59: Colores de estado en Sucursales (3 treeviews) ✅
- Tarea 60: Placeholder en Purchase Orders y Returns ✅
- Tarea 61: Export Excel en CRM, Proveedores, Órdenes ✅
- Tarea 62: Export Excel en Finanzas + Colores en Inteligencia ✅
- Tarea 63: Tooltips en Finanzas (11 cards) y CRM (historial) ✅
- Tarea 64: Tooltips en Suppliers, Purchase Orders, Sucursales ✅

### Pendiente Fase 4
- Redis real (reemplazar caché in-memory)
- Frontend React 18 + Vite + TailwindCSS
- App móvil React Native (iOS / Android)
- E-commerce sync (WooCommerce / Shopify)
- GitHub Actions — activar con push a repositorio remoto
- pgBouncer connection pooling

---

## Phase 5 ⏳ 2027
**Expansión LATAM**
- Marketplace de integraciones
- White-label para revendedores
- Franquicias multi-región
- Facturación electrónica DIAN Colombia (base implementada)
- Expansión: México (CFDI), Perú (OSE), Chile (SII)

---

## UX Standards (implementados — no regresar)
- Tooltips en KPIs: from src.app.components_luxury import Tooltip
- Placeholder en búsquedas: add_placeholder() de luxury_2026.py
- Colores de estado: tag_configure() en todos los treeviews
- Export Excel: patrón _exportar_excel() de inteligencia_window.py
- Atajos globales: F1=POS F3=CRM F4=Caja F6=Reportes F7=OC F8=Finanzas F9=Inteligencia

---

## Métricas Actuales — 2026-03-29
- Tests pasando: 81
- Tests fallando: 0
- Endpoints API: 22
- Ventanas GUI: 15+
- Servicios: 33 en src/services/
- Cobertura UX: Tooltips ✅ Placeholders ✅ Colores ✅ Export ✅