# API Reference — Alfa & Omega ERP

Base URL: `http://localhost:8005` (dev) · `https://api.alfaomega.co` (prod)

## Autenticación

Todos los endpoints (salvo los marcados como 🟢 público) requieren:

```
Authorization: Bearer <JWT>
```

O bien una API Key en el header:

```
X-API-Key: <tu_api_key>
```

---

## Endpoints

### 🔑 Auth

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/auth/login` | 🟢 público | Autentica usuario → retorna JWT |
| GET | `/auth/me` | JWT | Claims del token activo (sin `exp`) |

**POST /auth/login — body:**
```json
{
  "username": "admin",
  "password": "admin123",
  "tenant_id": "empresa_demo"
}
```
**Respuesta:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### 📦 Productos

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/productos/` | JWT | Lista productos (paginado, búsqueda) |
| GET | `/productos/{codigo}` | JWT | Detalle de un producto |
| POST | `/productos/` | JWT+ADMIN | Crear producto |
| PUT | `/productos/{codigo}` | JWT+ADMIN | Actualizar producto |

**GET /productos/** — query params: `search`, `limit` (max 500), `offset`

**POST /productos/ — body:**
```json
{
  "codigo": "PERF-001",
  "nombre": "Perfume Clásico 100ml",
  "categoria": "Perfumes",
  "precio": 85000,
  "cantidad": 50,
  "avg_cost": 42000
}
```

---

### 💰 Ventas

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/ventas/resumen` | JWT | KPIs del día (ventas_hoy, ticket_promedio) |
| GET | `/ventas/` | JWT | Lista ventas con filtro de fechas |
| GET | `/ventas/{doc_id}` | JWT | Detalle de venta con líneas |

**GET /ventas/** — query params: `fecha_desde` (YYYY-MM-DD), `fecha_hasta`, `limit`

---

### 📊 Inventario

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/inventario/stock` | JWT | Stock actual + valor total del inventario |
| GET | `/inventario/bajo-stock` | JWT | Productos bajo umbral (default: 5 uds) |
| GET | `/inventario/kardex/{codigo}` | JWT | Movimientos de un producto |

**GET /inventario/bajo-stock** — query param: `threshold` (default: 5)

**GET /inventario/kardex/{codigo}** — query params: `fecha_desde`, `fecha_hasta`, `limit`

---

### 🏢 Tenants (Super-Admin)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/tenants/` | ADMIN+public | Crear schema de tenant |
| GET | `/tenants/` | ADMIN+public | Listar todos los tenants |
| DELETE | `/tenants/{tenant_id}` | ADMIN+public | Desactivar tenant (soft delete) |

> Requiere `role=ADMIN` y `tenant_id=public` en el JWT.

---

### 📋 Planes

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/plans/` | 🟢 público | Lista los 4 planes disponibles |
| POST | `/tenants/{tenant_id}/plan` | ADMIN+public | Asigna plan a un tenant |

**Planes disponibles:**

| Plan | Precio | Usuarios | Productos | API |
|------|--------|----------|-----------|-----|
| free | $0 | 2 | 100 | ✅ |
| starter | $29/mes | 5 | 1,000 | ✅ |
| pro | $79/mes | 20 | 100,000 | ✅ |
| enterprise | Acordado | ∞ | ∞ | ✅ |

---

### 🚀 Onboarding

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/onboarding/register` | 🟢 público | Registra tenant + admin en un solo paso |

**Body:**
```json
{
  "tenant_id": "mi_empresa",
  "plan": "starter",
  "admin_username": "admin",
  "admin_password": "MiPass1234",
  "company_name": "Mi Empresa SAS",
  "industry": "retail",
  "currency": "COP",
  "timezone": "America/Bogota"
}
```

---

### 🔧 Admin (Super-Admin)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/admin/tenants` | ADMIN+public | Lista todos los tenants con estado |
| GET | `/admin/tenants/{tenant_id}` | ADMIN+public | Detalle + métricas de uso |
| PATCH | `/admin/tenants/{tenant_id}` | ADMIN+public | Cambiar plan/estado |
| GET | `/admin/metrics` | ADMIN+public | Métricas globales del SaaS |
| GET | `/admin/audit` | ADMIN+public | Audit log (filtra por tenant) |

---

### ❤️ Infra

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/health` | 🟢 público | Estado del servidor y motor de BD |

---

## API Keys

Las API Keys permiten autenticar sin JWT (útil para integraciones server-to-server).

### Generar una API Key

```python
from src.services.api_keys import generate_api_key
key = generate_api_key("mi_empresa", "nombre_app")
# La key SOLO se muestra esta vez. Guárdala en lugar seguro.
```

### Usar la API Key

```bash
curl -H "X-API-Key: <tu_key>" http://localhost:8005/productos/
```

### Revocar

```python
from src.services.api_keys import revoke_api_key
revoke_api_key(key_id=1)
```

---

## Rate Limits

| Plan | Límite |
|------|--------|
| free | 100 req/hora |
| starter | 1,000 req/hora |
| pro | 10,000 req/hora |
| enterprise | Sin límite |

Rutas excluidas: `/health`, `/docs`, `/openapi.json`, `/redoc`.

**Respuesta al superar el límite:**
```json
HTTP 429
{
  "error": "rate_limit_exceeded",
  "retry_after": 3542
}
```
Header: `Retry-After: 3542`

---

## Ejemplos curl completos

```bash
BASE=http://localhost:8005

# 1. Login
TOKEN=$(curl -sX POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","tenant_id":"empresa_demo"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Listar productos
curl -H "Authorization: Bearer $TOKEN" $BASE/productos/

# 3. KPIs del día
curl -H "Authorization: Bearer $TOKEN" $BASE/ventas/resumen

# 4. Bajo stock
curl -H "Authorization: Bearer $TOKEN" "$BASE/inventario/bajo-stock?threshold=10"

# 5. Health (sin auth)
curl $BASE/health
```
