# CLAUDE.md  Alfa & Omega ERP

## Project Overview
ERP desktop para perfumería colombiana. Gestiona inventario, ventas POS,
clientes, proveedores y caja. Objetivo: convertirse en SaaS LATAM multi-tenant.
App: Python/Tkinter desktop → futura web/móvil.
Estado actual: Fase 4 EN PROGRESO — 81 tests pasando — 2026-03-28

## Technology Stack
- Python 3.11 | Tkinter | SQLite → PostgreSQL (Fase 3)
- SQLAlchemy + Alembic | FastAPI + JWT
- reportlab (PDF) | openpyxl (Excel) | passlib (auth) | pytest
- matplotlib (gráficos dashboard) | statsmodels (predicción IA)

## Project Structure
src/app/        GUI Tkinter (ventanas)
src/services/   Lógica de negocio (NUNCA poner lógica en GUI)
src/database/   connection.py (init_db, get_connection) | repository.py
src/core/       caching.py | auth.py | acl.py
api/routers/    FastAPI endpoints (auth, productos, ventas, inventario,
                admin, plans, tenants, onboarding)
src/tests/      pytest suite (81 tests)
docs/           documentación detallada
.github/        CI/CD GitHub Actions (ci.yml + release.yml)

## Key Modules
POS              pos_window.py + inventory.post_sale()
CRM              crm_window.py + partners.py
Suppliers        suppliers_window.py + partners.py
Cash             cash_manager_window.py + pos_service.py
Returns          returns_window.py + returns_service.py
Purchase Orders  purchase_orders_window.py + purchase_orders.py
Reports          reports_window.py + reports.py
Finanzas         finanzas_window.py + finanzas.py
Notificaciones   notif_config_window.py + notificaciones.py
Inteligencia     inteligencia_window.py + anomalias/market_basket/
                 customer_reminders/dynamic_pricing
Planes           src/services/plans.py + src/database/plans.py
Admin SaaS       api/routers/admin.py + src/services/admin.py

## Critical Coding Rules
1. Ventanas: class XWindow(tk.Toplevel), NUNCA _register() como método
2. BD: SIEMPRE with get_connection() as conn — BD única: src/data/inventario.db
3. Lógica: SIEMPRE en src/services/, NUNCA en GUI
4. Errores: except Exception as e: logging.warning() — NUNCA bare except:pass
5. Caché: @cached(ttl=N) en queries, invalidate_prefix() tras writes
6. Estilos: Luxury2026Colors + ModernTypography desde src/app/styles/luxury_2026.py
7. UX — El usuario NUNCA debe adivinar:
   - Todo gráfico tiene leyenda + nota explicativa debajo
   - Todo KPI/número tiene Tooltip explicando cómo se calcula
   - Todo campo de búsqueda tiene placeholder text via add_placeholder()
   - Todo bloqueo por plan muestra mensaje claro de upgrade
   - Todo estado en treeview tiene color via tag_configure()
8. Estados en treeview — SIEMPRE colorizar con tag_configure():
   PENDIENTE=#F59E0B | ACTIVO/RECIBIDA=#10B981 | PARCIAL=#3B82F6
   CANCELADA/INACTIVO=#6B7280 | CRITICO=#EF4444 | BAJO=#F59E0B
9. Planes — enforcement en GUI:
   get_plan_limits_local(user) y check_plan_limit_local() desde
   src/services/plans.py — roles ADMIN/AUDITOR tienen acceso enterprise
10. API endpoints: SIEMPRE agregar summary= y description= en cada router

## UX Patterns (OBLIGATORIOS en toda ventana nueva)
- Tooltips en KPIs: from src.app.components_luxury import Tooltip
- Placeholder en búsquedas: from src.app.styles.luxury_2026 import add_placeholder
- Colorización de estados: tree.tag_configure(estado, foreground=color)
- Exportar Excel: usar patrón _exportar_excel() de inteligencia_window.py
- Atajos de teclado: documentar con accelerator= en add_command()

## New Window Pattern
class XWindow(tk.Toplevel):
    def __init__(self, parent, user=None):
        super().__init__(parent)
        self.title("Título")
        self.geometry("1000x600")
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        self.transient(parent)
        self.grab_set()
        self.user = user
        self._build_ui()

## Open Window from main_window
def _open_xwindow(self):
    import traceback
    try:
        from src.app.x_window import XWindow
        win = XWindow(self.root, self.user)
        self.root.wait_window(win)
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Error", f"No se pudo abrir:\n{e}")

## Instructions for AI
- Leer CLAUDE.md + doc relevante en docs/ antes de escribir código
- No proponer cambios de arquitectura ni de stack
- No duplicar lógica que ya existe en services/
- Mostrar diff antes de aplicar cambios — Un archivo a la vez
- Esperar confirmación ("OK APLICAR") antes de modificar cualquier archivo
- Seguir UX Rules: tooltips, placeholders, colores de estado, exportación
- Código completo sin truncar — nunca usar "..." para omitir secciones
- Correr pytest después de cada tarea y mostrar tail -3
- 81 tests deben seguir pasando — si alguno falla, reportar antes de continuar

## Keyboard Shortcuts (Globales)
F1=POS | F2=Editar producto | F3=CRM | F4=Caja | F5=Refrescar
F6=Reportes | F7=Órdenes de compra | F8=Finanzas | F9=Inteligencia
F10=POS cobrar | F11=Devolución | F12=Cerrar caja
Ctrl+N=Nuevo | Ctrl+E=Editar | Ctrl+B=Backup | Ctrl+L=Logout

## SaaS Architecture (Fase 3 — Completada)
- PostgreSQL schema-per-tenant — DB_ENGINE=postgres en producción
- JWT auth con tenant_id claim — TenantMiddleware inyecta TENANT_SCHEMA
- Planes: free|starter($29)|pro($79)|enterprise
- Enforcement: max_users, max_products, max_branches, pos, reportes, api
- Trial: 14 días — columnas trial_ends_at + plan_expires_at en tenants
- Super-Admin: GET/PATCH /admin/tenants, GET /admin/metrics (mrr/churn)
- Impersonar: POST /admin/tenants/{id}/impersonate (audit log obligatorio)
- _require_postgres() en toda función que requiera Postgres

## Additional Documentation
docs/ARCHITECTURE.md  capas, flujo de datos
docs/DATABASE.md      schema completo, relaciones
docs/MODULES.md       módulos, archivos, servicios, tablas
docs/DEVELOPMENT.md   patrones, reglas, tareas comunes + UX Rule
docs/ROADMAP.md       estado actual (Fase 4 en progreso), pendientes