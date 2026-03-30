# ROADMAP — Alfa & Omega ERP

## Phase 3 ✅ Completada — 2026-03-17

**Multi-tenant SaaS Core**

- Tarea 1: `connection.py` soporte dual SQLite/PostgreSQL con `SET search_path`
- Tarea 2: `tenant_provisioning.py` — `create/drop/list_tenants`
- Tarea 3A-C: FastAPI base + TenantMiddleware + JWT auth
- Tarea 4: Panel Super-Admin `/tenants` CRUD
- Tarea 5: `plans.py` — 4 planes (Free/Starter/Pro/Enterprise) + seeding
- Tarea 6: `api/routers/plans.py` — GET /plans/, POST /tenants/{id}/plan
- Tarea 7: Plan enforcement en services (límites usuarios/sucursales/productos)
- Tarea 8: `services/onboarding.py` — onboard_tenant() atómico
- Tarea 9: `api/routers/admin.py` — Panel Super-Admin 5 endpoints
- Tarea 10: Docker Compose dev local (Postgres 16 + pgAdmin)
- Tarea 11: Validación final Fase 3 — 18 tests pasando

---

## Phase 3.5 ✅ Completada — 2026-03-18

**Mejoras ERP + API Pública**

- Tarea 12: Dashboard rediseño — 4 zonas + KPIs reales (ventas_hoy, ticket, top-5)
- Tarea 13: Filtro temporal hoy/semana/mes en Dashboard
- Tarea 14: Módulo Finanzas — CxC, CxP, Flujo de caja
- Tarea 15: Notificaciones inteligentes — alertas stock SMTP + scheduler diario
- Tarea 16: API pública — 22 endpoints (productos/ventas/inventario/auth/admin)
- Tarea 17: Tests de negocio — suite completa, 69 tests pasando
- Tarea 18: Rate limiting in-memory + API Keys con hash SHA-256

---

## Phase 4 ⏳ Q4 2026 — Próxima

**Expansión y automatización**

- App móvil React Native (iOS / Android)
- Predicción de inventario con IA (Prophet / ARIMA)
- Sincronización e-commerce (WooCommerce / Shopify)
- Documentación API enriquecida (Swagger UI + Redoc + Postman collection)
- Dashboard analytics avanzado (cohortes, LTV, churn)
- Facturación electrónica DIAN (Colombia)
