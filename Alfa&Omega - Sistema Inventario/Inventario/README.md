# Alfa & Omega ERP

**Sistema de Gestión Empresarial para Pequeños Negocios LATAM**

[![Tests](https://img.shields.io/badge/tests-81%20passed-brightgreen)]()
[![Version](https://img.shields.io/badge/version-3.5.0-blue)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-Propietario-red)]()

---

## ¿Qué es Alfa & Omega ERP?

Sistema de gestión empresarial desktop para tiendas, perfumerías y 
pequeños negocios en Colombia y LATAM. Controla inventario, ventas, 
clientes, proveedores y finanzas — sin servidores, sin internet, 
sin complicaciones.

## Características principales

- 🛒 **Punto de Venta (POS)** — ventas rápidas con control de caja
- 📦 **Inventario** — kardex, predicción IA de quiebre de stock
- 👥 **CRM Clientes** — historial, crédito, segmentación A/B/C
- 🏭 **Proveedores** — órdenes de compra, recepción de mercancía
- 📊 **Reportes** — P&L, ABC, márgenes, rotación
- 💰 **Finanzas** — CxC, CxP, flujo de caja proyectado
- 🧠 **Inteligencia de Negocio** — canasta, precios dinámicos, anomalías
- 🏢 **Multi-sucursal** — stock por bodega, transferencias
- 🔐 **Licencias** — sistema de activación por máquina
- 🌐 **API REST** — 22 endpoints FastAPI + JWT
- ☁️ **SaaS Multi-tenant** — PostgreSQL schema-per-tenant

## Inicio rápido

### Requisitos
- Windows 10/11 (64-bit)
- Python 3.11+
- 4GB RAM mínimo

### Instalación
```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/ERP-Alfa-Omega.git
cd ERP-Alfa-Omega/Inventario

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Inicializar y ejecutar
py -3.11 main.py
```

### Credenciales por defecto
- **Usuario:** `admin`
- **Contraseña:** `admin123`

> ⚠️ Cambia la contraseña en el primer inicio.

## Estructura del proyecto

```
Inventario/
├── src/
│   ├── app/          # GUI Tkinter (ventanas)
│   ├── services/     # Lógica de negocio (33 servicios)
│   ├── database/     # connection.py, repository.py
│   └── core/         # auth, acl, caching, licencias
├── api/
│   └── routers/      # FastAPI endpoints (9 routers)
├── tools/            # Scripts de instalación y licencias
├── docs/             # Documentación completa
├── .github/          # CI/CD GitHub Actions
├── main.py           # Punto de entrada
└── requirements.txt
```

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [docs/INSTALACION.md](docs/INSTALACION.md) | Guía de instalación paso a paso |
| [docs/MANUAL_USUARIO.md](docs/MANUAL_USUARIO.md) | Manual completo de usuario |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitectura del sistema |
| [docs/DATABASE.md](docs/DATABASE.md) | Schema de base de datos |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Estado actual y roadmap |

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| F1 | Punto de Venta |
| F3 | CRM Clientes |
| F4 | Control de Caja |
| F5 | Refrescar |
| F6 | Reportes |
| F7 | Órdenes de Compra |
| F8 | Finanzas |
| F9 | Inteligencia de Negocio |

## API REST

El sistema incluye una API REST completa (FastAPI):
```bash
# Iniciar el servidor API
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Documentación interactiva
http://localhost:8000/docs
```

## Planes de suscripción

| Plan | Precio | Usuarios | Productos |
|------|--------|----------|-----------|
| Free | Gratis | 1 | 100 |
| Starter | $29/mes | 3 | 1,000 |
| Pro | $79/mes | 10 | Ilimitados |
| Enterprise | A medida | Ilimitados | Ilimitados |

## Herramientas incluidas

```bash
# Generar licencia para cliente
py tools/generate_client_license.py

# Script de instalación para cliente
py tools/instalar_cliente.py

# Datos de ejemplo (tienda de ropa)
py tools/seed_tienda_ropa.py

# Resetear BD para producción
py tools/reset_demo_data.py
```

## Tests

```bash
py -3.13 -m pytest src/tests/ -v
# 81 passed ✅
```

## Tecnologías

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Base de datos:** SQLite (desktop) / PostgreSQL (SaaS)
- **GUI:** Tkinter + Luxury2026 Design System
- **Reportes:** ReportLab (PDF), OpenPyXL (Excel)
- **IA:** statsmodels (predicción Holt-Winters)
- **Auth:** passlib, python-jose (JWT)
- **Empaquetado:** PyInstaller (.exe)

## Licencia

Propietario — Alfa & Omega ERP © 2026  
Todos los derechos reservados.

## Soporte

📧 soporte@alfaomega.co
