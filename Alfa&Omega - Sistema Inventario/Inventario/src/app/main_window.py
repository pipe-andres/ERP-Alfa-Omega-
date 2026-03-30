# app/gui.py
import os
import tkinter as tk
from typing import Optional
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from src.app.styles import theme, scrollbars
from src.app.styles.luxury_2026 import aplicar_tema_luxury_2026, Luxury2026Colors, ModernTypography
from src.app.components_premium import EncabezadoProfesional, BarraInformacion
from src.app.components_memorable import CopyPersonalidad, EmptyStateHermoso, ErrorElegante, ConfirmacionHermosa

# Audit / Auth
from src.services.audit import log_event, list_audit
from src.core.auth import ensure_defaults, has_perm
from src.core.auth import LoginDialog, ChangePasswordDialog
from src.core.auth import (
    list_users, list_roles, create_user,
    set_user_active, reset_password, set_user_roles
)

# Servicios del inventario y movimientos
from src.services.inventory import (
    add_product, update_product, delete_product, get_product,
    list_products_page, count_products, stock_global_sum, low_stock_count,
    export_products_csv, import_products_csv, export_products_xlsx, import_products_xlsx,
    export_inventory_pdf, export_low_stock_pdf,
    post_purchase, post_sale, post_adjustment
)
# ``post_return`` lives in a dedicated module now; GUI components will import it via returns_window


# ventana especializada para manejar devoluciones
try:
    from src.app import returns_window
except ImportError:
    returns_window = None  # sicurezza durante pruebas o entornos antiguos

# Reportes
from src.services.reports import kardex_rows, export_kardex_xlsx, export_kardex_pdf

# Documentos comerciales (PDF comprobantes)
from src.services.documents import export_purchase_pdf, export_sale_pdf
from src.services.documents import ensure_schema as ensure_doc_series, seed_default_series

# Partners (clientes/proveedores)
from src.services.partners import ensure_schema as ensure_partners_schema

# Parámetros (company_settings)
from src.database.settings import get_settings, update_settings

# Dashboard
from src.app.dashboard import DashboardTab

APP_TITLE = "Inventario de Perfumes — Alfa & Omega"
VENTANA_INICIAL = "1100x760"
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
LOGO_FILENAME = "Logo de Alfa & Omega Perfumes.png"
UMBRAL_STOCK_BAJO = 5
PAGE_SIZE_OPTIONS = [10, 25, 50, 100]
DEFAULT_PAGE_SIZE = 25


def cargar_logo_seguro(path):
    try:
        from PIL import Image, ImageTk
        img = Image.open(path)
        base_width = 150
        w_percent = (base_width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


# ---------------------- Aplicación principal ----------------------
class InventarioApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(VENTANA_INICIAL)
        # Dark mode luxury 2026
        self.root.configure(bg="#0A0E27")

        # ✨ APLICAR TEMA LUXURY 2026 (ENAMORANTE)
        aplicar_tema_luxury_2026()

        # Inicialización base
        try:
            ensure_defaults()
            ensure_partners_schema()
            ensure_doc_series()
            seed_default_series()
        except Exception as e:
            messagebox.showerror("Inicialización", str(e))

        # Login
        dlg = LoginDialog(self.root)
        if not dlg.result:
            self.root.destroy()
            return
        self.user = dlg.result  # {id, username, name, roles: [...]}
        self.root.title(APP_TITLE + f" — {self.user['name']} ({', '.join(self.user['roles'])})")
        log_event(self.user["id"], "LOGIN", {"username": self.user["username"], "roles": self.user["roles"]})

        # Menú principal
        menubar = tk.Menu(self.root)

        # Archivo
        m_arch = tk.Menu(menubar, tearoff=0)
        m_arch.add_command(label="Crear backup…", command=self._menu_backup)
        m_arch.add_command(label="Restaurar backup…", command=self._menu_restore)
        m_arch.add_separator()
        m_arch.add_command(label="Cerrar sesión", command=self._menu_logout)
        m_arch.add_command(label="Salir", command=self.root.destroy)
        menubar.add_cascade(label="Archivo", menu=m_arch)

        # Mi cuenta
        m_cuenta = tk.Menu(menubar, tearoff=0)
        m_cuenta.add_command(label="Cambiar contraseña…", command=self._menu_change_password)
        menubar.add_cascade(label="Mi cuenta", menu=m_cuenta)

        # Módulo POS
        m_pos = tk.Menu(menubar, tearoff=0)
        m_pos.add_command(label="Abrir Caja / POS", command=self._open_pos_window, accelerator="F1")
        m_pos.add_command(label="💰 Caja", command=self._open_cash_manager_window, accelerator="F4")
        menubar.add_cascade(label="Punto de Venta", menu=m_pos)

        # CRM Clientes
        m_crm = tk.Menu(menubar, tearoff=0)
        m_crm.add_command(label="👥 Clientes", command=self._open_crm_window, accelerator="F3")
        menubar.add_cascade(label="Clientes", menu=m_crm)

        # Proveedores
        m_proveedores = tk.Menu(menubar, tearoff=0)
        m_proveedores.add_command(label="🏭 Proveedores", command=self._open_suppliers_window)
        menubar.add_cascade(label="Proveedores", menu=m_proveedores)
        # Reportes
        m_rep = tk.Menu(menubar, tearoff=0)
        m_rep.add_command(label="📈 Reportes Avanzados", command=self._open_reports_window, accelerator="F6")
        m_rep.add_command(label="🧠 Inteligencia de Negocio", command=self._open_inteligencia_window, accelerator="F9")
        m_rep.add_command(label="🔮 Predicción IA", command=self._open_prediccion_window)
        m_rep.add_command(label="💹 Simulador de Precio", command=self._open_price_simulator_window)
        menubar.add_cascade(label="Reportes", menu=m_rep)

        # Sucursales
        m_suc = tk.Menu(menubar, tearoff=0)
        m_suc.add_command(label="🏢 Gestión Multi-sucursal", command=self._open_sucursales_window)
        menubar.add_cascade(label="Sucursales", menu=m_suc)
        
        # Inventario
        m_inv = tk.Menu(menubar, tearoff=0)
        m_inv.add_command(label="📥 Importar", command=self._open_import_productos_window)
        menubar.add_cascade(label="Inventario", menu=m_inv)
    
        # Compras
        m_compras = tk.Menu(menubar, tearoff=0)
        m_compras.add_command(label="📦 Órdenes de Compra", command=self._open_purchase_orders_window, accelerator="F7")
        m_compras.add_command(label="🤖 Auto-Reorder (stock mínimo)", command=self._open_auto_reorder_window)
        menubar.add_cascade(label="Compras", menu=m_compras)

        # Finanzas
        m_fin = tk.Menu(menubar, tearoff=0)
        m_fin.add_command(label="💰 CxC · CxP · Flujo de Caja", command=self._open_finanzas_window, accelerator="F8")
        menubar.add_cascade(label="Finanzas", menu=m_fin)

        # Configuración
        m_conf = tk.Menu(menubar, tearoff=0)
        m_conf.add_command(label="\U0001f514 Notificaciones Email",
                           command=self._open_notif_config_window)
        m_conf.add_command(
            label="🇨🇴 Facturación Electrónica DIAN",
            command=self._open_dian_config_window
        )
        m_conf.add_command(
            label="🏭 Perfil de Industria",
            command=self._open_industry_window
        )
        menubar.add_cascade(label="Configuraci\u00f3n", menu=m_conf)

        self.root.config(menu=menubar)

        # Estado de listado
        self._filter_by = None
        self._filter_q = ""
        self._order_by = "nombre"
        self._asc = True
        self._page_size = DEFAULT_PAGE_SIZE
        self._page = 1
        self._total_items = 0

        # Logo
        ruta_logo = os.path.join(ASSETS_DIR, LOGO_FILENAME)
        self.logo = cargar_logo_seguro(ruta_logo)
        
        # ===== ENCABEZADO PROFESIONAL =====
        self.encabezado = EncabezadoProfesional(
            self.root,
            titulo="📊 Inventario Alfa & Omega",
            subtitulo="Sistema de Gestión de Perfumería Profesional",
            logo_img=self.logo
        )
        self.encabezado.pack(fill='x', padx=0, pady=0)
        
        if self.logo:
            self.root.iconphoto(False, self.logo)

        # ===== Notebook principal =====
        self.nb_main = ttk.Notebook(self.root)
        self.nb_main.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        # Tab Dashboard (PRIMERA PESTAÑA)
        self.tab_dashboard = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_dashboard, text="📊 Dashboard")
        self.dashboard = DashboardTab(self.tab_dashboard)

        # Tab Inventario
        self.tab_inv = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_inv, text="Inventario")
        self._build_tab_inventario(self.tab_inv)
        print('tab_inv OK')

        # Tab Movimientos
        self.tab_mov = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_mov, text="Movimientos")
        self._build_tab_movimientos(self.tab_mov)
        print('tab_mov OK')

        # Tab Historial (altas/mods/imports)
        self.tab_hist = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_hist, text="Historial")
        self._build_tab_hist(self.tab_hist)
        print('tab_hist OK')

        # Tab Reportes (Kardex)
        self.tab_reports = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_reports, text="Reportes")
        self._build_tab_reportes(self.tab_reports)
        print('tab_reports OK')

        # Tab Devoluciones (NUEVO)
        self.tab_returns = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_returns, text="💔 Devoluciones")
        self._build_tab_devoluciones(self.tab_returns)
        print('tab_returns OK')

        # Tab Descuentos (NUEVO)
        self.tab_discounts = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_discounts, text="💰 Descuentos")
        self._build_tab_descuentos(self.tab_discounts)
        print('tab_discounts OK')

        # Tab Márgenes (NUEVO)
        self.tab_margins = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_margins, text="📈 Márgenes")
        self._build_tab_margenes(self.tab_margins)
        print('tab_margins OK')

        # Tab Reportes Avanzados (NUEVO)
        self.tab_advanced_reports = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_advanced_reports, text="🎯 Análisis Avanzado")
        self._build_tab_reportes_avanzados(self.tab_advanced_reports)
        print('tab_advanced OK')

        # Tab Auditoría (si tiene permiso)
        if has_perm(self.user, "VIEW_AUDIT") or has_perm(self.user, "ADMIN"):
            self.tab_audit = ttk.Frame(self.nb_main)
            self.nb_main.add(self.tab_audit, text="Auditoría")
            self._build_tab_auditoria(self.tab_audit)

        # Tab Administración (Usuarios & Roles) — si ADMIN
        if has_perm(self.user, "ADMIN"):
            self.tab_admin = ttk.Frame(self.nb_main)
            self.nb_main.add(self.tab_admin, text="Administración")
            self._build_tab_users(self.tab_admin)
            # Cargar usuarios al abrir la interfaz
            self._users_reload()

            # Pestaña Parámetros (company_settings)
            self.tab_settings = ttk.Frame(self.nb_main)
            self.nb_main.add(self.tab_settings, text="Parámetros")
            self._build_tab_settings(self.tab_settings)

        # Atajos
        self.root.bind("<Return>", lambda e: self.buscar_producto())
        self.root.bind("<F5>", lambda e: self.refrescar_todo())
        # Atajos globales de navegación
        self.root.bind("<F1>",  lambda e: self._open_pos_window())
        self.root.bind("<F3>",  lambda e: self._open_crm_window())
        self.root.bind("<F4>",  lambda e: self._open_cash_manager_window())
        self.root.bind("<F6>",  lambda e: self._open_reports_window())
        self.root.bind("<F7>",  lambda e: self._open_purchase_orders_window())
        self.root.bind("<F8>",  lambda e: self._open_finanzas_window())
        self.root.bind("<F9>",  lambda e: self._open_inteligencia_window())
        self.root.bind("<Control-b>", lambda e: self._menu_backup())
        self.root.bind("<Control-l>", lambda e: self._menu_logout())
        self.root.bind("<Delete>", lambda e: self.eliminar_producto())
        self.root.bind("<F2>", lambda e: self.editar_producto())
        self.root.bind("<Control-e>", lambda e: self.editar_producto())
        self.root.bind("<Control-n>", lambda e: self.nuevo_producto())

        # Carga inicial
        self.refrescar_todo()

        # Tarea 38: Tour interactivo de onboarding
        if getattr(self, "user", None):
            try:
                from src.database.connection import get_connection
                with get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT tour_completado FROM users WHERE id=?", (self.user["id"],))
                    row = cur.fetchone()
                    if row and not row[0]:
                        self.root.after(500, self._show_tour)
            except Exception as e:
                print("Error verificando onboarding tour:", e)

    def _show_tour(self):
        try:
            from src.app.onboarding_tour import OnboardingTour
            OnboardingTour(self.root, self.user, self)
        except Exception as e:
            print("Error cargando tour interactivo:", e)

    def _open_import_productos_window(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Importación Asistida de Productos")
        dlg.geometry("700x500")
        dlg.configure(bg=Luxury2026Colors.BG_DARKEST)
        dlg.transient(self.root)
        dlg.grab_set()
        
        # UI
        tk.Label(dlg, text="📥 Asistente de Importación CSV/Excel", font=ModernTypography.font_heading(),
                 bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.PRIMARY).pack(pady=(20, 10))
                 
        tk.Label(dlg, text="Seleccione un archivo (.csv, .xlsx)", font=ModernTypography.font_body(),
                 bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.TEXT_SECONDARY).pack(pady=(0, 15))
                 
        # Frame del archivo
        file_frame = tk.Frame(dlg, bg=Luxury2026Colors.BG_SECONDARY)
        file_frame.pack(fill="x", padx=20)
        
        lbl_file = tk.Label(file_frame, text="Ningún archivo seleccionado", font=ModernTypography.font_body_small(),
                          bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_TERTIARY, relief="solid", bd=1)
        lbl_file.pack(side="left", fill="x", expand=True, padx=10, ipady=5)
        
        selected_file = {"path": None}
        
        def on_browse():
            path = filedialog.askopenfilename(
                title="Seleccionar archivo",
                filetypes=[("Excel / CSV", "*.xlsx *.csv"), ("Todos", "*.*")]
            )
            if not path:
                return
            selected_file["path"] = path
            lbl_file.config(text=os.path.basename(path), fg=Luxury2026Colors.TEXT_PRIMARY)
            _preview_file(path)
            
        ttk.Button(file_frame, text="📁 Examinar", command=on_browse, style='Luxury.Secondary.TButton').pack(side="right", padx=10)
        
        # Preview
        tk.Label(dlg, text="Vista previa (primeras 5 filas):", font=ModernTypography.font_body_bold(),
                 bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.PRIMARY).pack(anchor="w", padx=20, pady=(15, 5))
                 
        preview_frame = tk.Frame(dlg, bg=Luxury2026Colors.BG_DARKEST)
        preview_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        tree = ttk.Treeview(preview_frame, show="headings", height=5)
        tree.pack(fill="both", expand=True)
        theme.aplicar_estilo_treeview(tree)
        
        def _preview_file(path):
            tree.delete(*tree.get_children())
            ext = os.path.splitext(path)[1].lower()
            try:
                headers = []
                rows = []
                if ext == '.csv':
                    import csv
                    with open(path, newline="", encoding="utf-8-sig") as f:
                        reader = csv.reader(f)
                        headers = next(reader, [])
                        for i, r in enumerate(reader):
                            if i >= 5: break
                            rows.append(r)
                elif ext == '.xlsx':
                    import openpyxl
                    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
                    ws = wb.active
                    for i, r in enumerate(ws.iter_rows(values_only=True)):
                        if i == 0:
                            headers = [str(x) if x else "" for x in r]
                        elif i <= 5:
                            rows.append([str(x) if x is not None else "" for x in r])
                        else:
                            break
                            
                tree["columns"] = list(range(len(headers)))
                for j, h in enumerate(headers):
                    tree.heading(j, text=str(h)[:15])
                    tree.column(j, width=100)
                for r in rows:
                    tree.insert("", "end", values=r)
            except Exception as e:
                lbl_file.config(text=f"Error leyendo prev: {str(e)[:30]}")
        
        def on_import():
            if not selected_file["path"]:
                messagebox.showwarning("Aviso", "Seleccione un archivo primero")
                return
            from src.services.inventory import import_from_file
            res = import_from_file(selected_file["path"], self.user["id"])
            
            msg = f"Importación completada:\n\n"
            msg += f"📦 Total procesados: {res['total']}\n"
            msg += f"✅ Insertados: {res['insertados']}\n"
            msg += f"♻️ Actualizados: {res['actualizados']}\n"
            
            if res["errores"]:
                msg += f"\n❌ Errores ({len(res['errores'])}):\n"
                for err in res["errores"][:5]:
                    msg += f" Fila {err['fila']}: {err['error']}\n"
                if len(res["errores"]) > 5:
                    msg += " ... (ver logs para más detalles)"
                    
                messagebox.showwarning("Importación con Advertencias", msg)
            else:
                self.show_success("Importación Exitosa", msg)
                
            self.refrescar_todo()
            dlg.destroy()
            
        btn_frame = tk.Frame(dlg, bg=Luxury2026Colors.BG_DARKEST)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="✅ Iniciar Importación", command=on_import, style='Luxury.Primary.TButton').pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancelar", command=dlg.destroy, style='Luxury.Secondary.TButton').pack(side="left", padx=10)

    def _open_inteligencia_window(self):
        try:
            from src.app.inteligencia_window import InteligenciaWindow
            InteligenciaWindow(self.root, self.user)
        except Exception as e:
            import logging
            logging.warning("_open_inteligencia_window error: %s", e)
            self.show_error("Error", f"No se pudo abrir Inteligencia de Negocio:\n{e}")

    def _open_prediccion_window(self):
        try:
            from src.app.prediccion_window import PrediccionWindow
            PrediccionWindow(self.root)
        except Exception as e:
            import logging
            logging.warning("_open_prediccion_window error: %s", e)
            messagebox.showerror("Error", f"No se pudo abrir Predicción IA:\n{e}")

    def _open_price_simulator_window(self):
        try:
            from src.services.price_simulator import simular_precio
        except ImportError:
            self.show_error("Error", "Servicio de Simulador no disponible.")
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("Simulador de Precio")
        dlg.geometry("500x620")
        dlg.resizable(False, False)
        dlg.configure(bg=Luxury2026Colors.BG_DARKEST)
        dlg.transient(self.root)
        dlg.grab_set()

        # Titulo
        tk.Label(dlg, text="💹 Simulador de Precio", font=ModernTypography.font_heading(),
                 bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.PRIMARY).pack(pady=(20, 10))

        # Controles
        frame_inputs = tk.Frame(dlg, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame_inputs.pack(fill="x", padx=30, pady=10)

        tk.Label(frame_inputs, text="Código del Producto:", font=ModernTypography.font_body_small(),
                 bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=0, sticky="e", padx=10, pady=10)
        
        entry_codigo = tk.Entry(frame_inputs, width=20, font=ModernTypography.font_body(),
                                bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        entry_codigo.grid(row=0, column=1, sticky="w", padx=10, pady=10)

        tk.Label(frame_inputs, text="Nuevo Precio:", font=ModernTypography.font_body_small(),
                 bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=1, column=0, sticky="e", padx=10, pady=(0, 10))

        entry_precio = tk.Entry(frame_inputs, width=20, font=ModernTypography.font_body(),
                                bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        entry_precio.grid(row=1, column=1, sticky="w", padx=10, pady=(0, 10))

        # Panel de resultados
        frame_res = tk.Frame(dlg, bg=Luxury2026Colors.BG_DARKEST)
        frame_res.pack(fill="both", expand=True, padx=30, pady=10)
        
        tree = ttk.Treeview(frame_res, columns=("Campo", "Valor"), show="headings", height=9)
        tree.heading("Campo", text="Variable")
        tree.heading("Valor", text="Resultado")
        tree.column("Campo", width=220, anchor="w")
        tree.column("Valor", width=180, anchor="e")
        tree.pack(fill="both", expand=True)
        theme.aplicar_estilo_treeview(tree)

        lbl_alerta = tk.Label(dlg, text="", font=ModernTypography.font_body_bold(),
                              bg=Luxury2026Colors.BG_DARKEST, wraplength=440)
        lbl_alerta.pack(pady=10)

        def on_simular():
            cod = entry_codigo.get().strip()
            if not cod:
               self.show_warning("Atención", "Ingrese un código")
               return
            val = entry_precio.get().strip()
            try:
                np = float(val)
            except ValueError:
                self.show_error("Error", "Precio inválido")
                return
            
            try:
                res = simular_precio(cod, np)
            except Exception as e:
                self.show_error("Error de Simulación", str(e))
                return

            # Update table
            tree.delete(*tree.get_children())
            tree.insert("", "end", values=("Nombre", res["nombre"]))
            tree.insert("", "end", values=("Costo Promedio", f"${res['avg_cost']:,.2f}"))
            tree.insert("", "end", values=("Precio Actual", f"${res['precio_actual']:,.2f}"))
            tree.insert("", "end", values=("Margen Actual %", f"{res['margen_actual_pct']}%"))
            tree.insert("", "end", values=("Nuevo Precio", f"${res['nuevo_precio']:,.2f}"))
            tree.insert("", "end", values=("Margen Nuevo %", f"{res['margen_nuevo_pct']}%"))
            tree.insert("", "end", values=("Variación Precio %", f"{res['variacion_precio_pct']}%"))
            tree.insert("", "end", values=("Δ Volumen Necesario %", f"{res['aumento_volumen_pct']}%"))
            tree.insert("", "end", values=("Unid. Mensuales Nec.", f"{res['unidades_necesarias']} (act: {res['ventas_promedio_mes']})"))

            if res["es_viable"]:
                lbl_alerta.config(text="SIMULACIÓN VIABLE", fg=Luxury2026Colors.SUCCESS)
            else:
                alerta_msg = res["alerta"] if res["alerta"] else "NO VIABLE (Margen Negativo)"
                lbl_alerta.config(text=alerta_msg, fg=Luxury2026Colors.DANGER)

        btn_sim = ttk.Button(dlg, text="⚡ Simular", command=on_simular, style='Luxury.Primary.TButton')
        btn_sim.pack(pady=(0, 20))

    def _open_sucursales_window(self):
        try:
            from src.app.sucursales_window import SucursalesWindow
            SucursalesWindow(self.root, self.user)
        except Exception as e:
            import logging
            logging.warning("_open_sucursales_window error: %s", e)
            self.show_error("Error", f"No se pudo abrir panel de sucursales:\n{e}")

    def _open_dian_config_window(self):
        try:
            from src.app.dian_config_window import DianConfigWindow
            DianConfigWindow(self.root)
        except Exception as e:
            import logging
            logging.warning("_open_dian_config_window error: %s", e)
            messagebox.showerror("DIAN", str(e))

    def _open_industry_window(self):
        try:
            from src.services.industry_profiles import list_industries, apply_profile, get_current_profile
            
            dlg = tk.Toplevel(self.root)
            dlg.title("Configuración de Industria")
            dlg.geometry("500x400")
            dlg.resizable(False, False)
            dlg.configure(bg=Luxury2026Colors.BG_DARKEST)
            dlg.transient(self.root)
            dlg.grab_set()

            # Titulo
            tk.Label(dlg, text="🏭 Perfil de Industria", font=ModernTypography.font_heading(),
                     bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.PRIMARY).pack(pady=(20, 10))

            # Mapeo de descripciones
            descmap = {
                "perfumeria": "Perfumería / Cosméticos",
                "ropa": "Ropa / Textiles",
                "ferreteria": "Ferretería / Materiales",
                "minimarket": "Minimarket / Abarrotes",
                "tecnologia": "Tecnología / Electrónica",
                "barberia": "Barbería / Salón de belleza",
                "papeleria": "Papelería / Librería",
                "repuestos": "Repuestos / Autopartes",
                "retail": "Comercio general (default)"
            }

            # Estado actual
            current = get_current_profile()
            current_ind = current.get("industry", "retail")
            current_desc = descmap.get(current_ind, descmap["retail"])
            
            info_frame = tk.Frame(dlg, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
            info_frame.pack(fill="x", padx=40, pady=20)
            tk.Label(info_frame, text=f"Industria Actual: {current_desc}",
                     font=ModernTypography.font_body_bold(),
                     bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT).pack(pady=10)

            # Selector
            tk.Label(dlg, text="Selecciona el tipo de negocio:", font=ModernTypography.font_body(),
                     bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.TEXT_SECONDARY).pack(pady=(10, 5))

            inds = list_industries()
            opciones = [descmap.get(i, i) for i in inds]
            
            # Find index of current
            try:
                curr_idx = inds.index(current_ind)
            except ValueError:
                curr_idx = 0

            var_sel = tk.StringVar(value=opciones[curr_idx])
            selector = ttk.Combobox(dlg, textvariable=var_sel, values=opciones, state="readonly", width=35)
            selector.pack(pady=5)

            def on_aplicar():
                idx = selector.current()
                if idx < 0:
                    return
                selected_ind = inds[idx]
                apply_profile(selected_ind)
                messagebox.showinfo(
                    "Perfil Aplicado", 
                    f"El perfil '{descmap.get(selected_ind, selected_ind)}' ha sido aplicado correctamente.\n"
                    "Es posible que necesites reiniciar las pantallas afectadas para ver los cambios."
                )
                dlg.destroy()

            # Botones
            btn_frame = tk.Frame(dlg, bg=Luxury2026Colors.BG_DARKEST)
            btn_frame.pack(pady=30)

            btn_frame.columnconfigure(0, weight=1)
            btn_frame.columnconfigure(1, weight=1)

            ttk.Button(
                btn_frame,
                text="Aplicar",
                command=on_aplicar,
                style="Luxury.Primary.TButton"
            ).grid(row=0, column=0, padx=10)

            ttk.Button(
                btn_frame,
                text="Cancelar",
                command=dlg.destroy,
                style="Luxury.Secondary.TButton"
            ).grid(row=0, column=1, padx=10)
            
        except Exception as e:
            import logging
            logging.warning("_open_industry_window error: %s", e)
            messagebox.showerror("Error", f"No se pudo abrir el elector de industria:\n{e}")

    # =========================
    # Helpers para notificaciones emocionales 🔥
    # =========================
    def _show_toast(self, titulo, mensaje, tipo="success", duracion=2000):
        """Toast emocional con feedback visual - FIRMA DEL SISTEMA
        tipo: 'success' (✅ verde), 'error' (❌ rojo), 'info' (ℹ️ azul), 'warning' (⚠️ ámbar)
        """
        dlg = tk.Toplevel(self.root)
        dlg.wm_overrideredirect(True)
        dlg.wm_attributes('-topmost', True)
        
        # Colores por tipo
        color_map = {
            'success': (Luxury2026Colors.SUCCESS, '✅'),
            'error': (Luxury2026Colors.DANGER, '❌'),
            'info': (Luxury2026Colors.PRIMARY, 'ℹ️'),
            'warning': (Luxury2026Colors.WARNING, '⚠️')
        }
        color, emoji = color_map.get(tipo, color_map['info'])
        
        # Frame elegante con borde de color
        frame = tk.Frame(dlg, bg=Luxury2026Colors.BG_SECONDARY, bd=2, relief="solid", highlightbackground=color, highlightthickness=1)
        frame.pack(padx=12, pady=12)
        
        # Header: emoji + título
        header_frame = tk.Frame(frame, bg=Luxury2026Colors.BG_SECONDARY)
        header_frame.pack(fill="x", padx=12, pady=(8, 0))
        
        tk.Label(header_frame, text=f"{emoji} {titulo}", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=color).pack(anchor="w", side="left")
        
        # Mensaje
        tk.Label(frame, text=mensaje, font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(4, 8))
        
        # Posición esquina inferior derecha
        dlg.geometry(f"+{self.root.winfo_screenwidth() - 380}+{self.root.winfo_screenheight() - 140}")
        dlg.after(duracion, dlg.destroy)
    
    def show_success(self, titulo, mensaje):
        """Confirmación hermosa con feedback emocional ✅"""
        self._show_toast(titulo, mensaje, tipo='success', duracion=2000)
    
    def show_error(self, titulo, mensaje):
        """Error amable con visual claro ❌"""
        self._show_toast(titulo, mensaje, tipo='error', duracion=3000)
    
    def show_info(self, titulo, mensaje):
        """Información con visual amigable ℹ️"""
        self._show_toast(titulo, mensaje, tipo='info', duracion=2000)
    
    def show_warning(self, titulo, mensaje):
        """Advertencia con visual prominente ⚠️"""
        self._show_toast(titulo, mensaje, tipo='warning', duracion=2500)
    
    def _add_separator(self, parent, text="", padx=6, pady=6):
        """Separador elegante con firma Luxury - MICRO-DETALLE REPETIBLE
        Línea delgada PRIMARY con label opcional - elemento de personalidad
        """
        sep_frame = tk.Frame(parent, bg=Luxury2026Colors.BG_DARKEST)
        sep_frame.pack(fill="x", padx=padx, pady=pady)
        
        if text:
            sep_inner = tk.Frame(sep_frame, bg=Luxury2026Colors.BG_DARKEST)
            sep_inner.pack(fill="x", padx=0, pady=4)
            tk.Label(sep_inner, text=text, font=ModernTypography.font_body_small(),
                    bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.TEXT_TERTIARY).pack(anchor="w", side="left", padx=2)
        
        # Línea decorativa sutil
        line = tk.Frame(sep_frame, height=1, bg=Luxury2026Colors.PRIMARY)
        line.pack(fill="x", padx=0, pady=(2, 0))

    # =========================
    # Construcción de pestañas
    # =========================
    def _build_tab_inventario(self, parent: ttk.Frame):
        # HÉROE VISUAL: Stock Total dominante - 36px PRIMARY
        frame_hero = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame_hero.pack(fill="x", padx=2, pady=4)
        
        tk.Label(frame_hero, text="Stock total disponible", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(8, 0))
        
        self.lbl_total_stock_hero = tk.Label(frame_hero, text="0", font=("Arial", 36, "bold"),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY)
        self.lbl_total_stock_hero.pack(anchor="w", padx=12, pady=(0, 12))
        
        # Estadísticas adicionales - MEJORADO
        frame_stats = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame_stats.pack(fill="x", padx=2, pady=4)
        
        # Título
        tk.Label(frame_stats, text="📊 Estadísticas (global)", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY).pack(anchor="w", padx=12, pady=(8, 0))
        
        # Contenedor de stats
        stats_container = tk.Frame(frame_stats, bg=Luxury2026Colors.BG_SECONDARY)
        stats_container.pack(fill="x", padx=12, pady=(8, 12))
        
        # Total de productos
        tk.Label(stats_container, text="Total", font=ModernTypography.font_caption(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=0, sticky="w")
        self.lbl_total_productos = tk.Label(stats_container, text="0", font=ModernTypography.font_heading(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY)
        self.lbl_total_productos.grid(row=1, column=0, sticky="w", pady=(4, 0))
        
        # Stock bajo
        tk.Label(stats_container, text=f"Stock bajo ≤ {UMBRAL_STOCK_BAJO}", font=ModernTypography.font_caption(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=1, sticky="w", padx=(32, 0))
        self.lbl_stock_bajo = tk.Label(stats_container, text="0", font=ModernTypography.font_heading(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.DANGER)
        self.lbl_stock_bajo.grid(row=1, column=1, sticky="w", pady=(4, 0), padx=(32, 0))

        # Buscar - MEJORADO
        frame_search = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame_search.pack(fill="x", padx=2, pady=4)
        
        tk.Label(frame_search, text="🔍 Buscar Producto", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(8, 0))
        
        search_row = tk.Frame(frame_search, bg=Luxury2026Colors.BG_SECONDARY)
        search_row.pack(fill="x", padx=12, pady=(8, 12))
        
        tk.Label(search_row, text="Filtro:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(side="left")
        self.combo_filtro = ttk.Combobox(search_row, values=["Código", "Nombre", "Categoría"], state="readonly", width=10)
        self.combo_filtro.current(0)
        self.combo_filtro.pack(side="left", padx=(6, 12))
        
        tk.Label(search_row, text="Buscar:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(side="left")
        self.entry_buscar = tk.Entry(search_row, width=30, font=ModernTypography.font_body(),
                                    bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                    insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.entry_buscar.pack(side="left", padx=(6, 12), fill="x", expand=True)
        from src.app.styles.luxury_2026 import add_placeholder
        add_placeholder(self.entry_buscar, "🔍 Buscar producto por código o nombre...")
        
        ttk.Button(search_row, text="🔎 Buscar", command=self.buscar_producto, style='Luxury.Primary.TButton').pack(side="left", padx=4)
        ttk.Button(search_row, text="↻ Limpiar", command=self.limpiar_busqueda, style='Luxury.Secondary.TButton').pack(side="left")

        # ===== BARRA DE ACCIONES ARRIBA DE LA TABLA =====
        actions_bar = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        actions_bar.pack(fill="x", padx=2, pady=4)
        
        tk.Label(actions_bar, text="⚡ Acciones Rápidas", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY).pack(anchor="w", padx=12, pady=(8, 0))
        
        actions_row = tk.Frame(actions_bar, bg=Luxury2026Colors.BG_SECONDARY)
        actions_row.pack(fill="x", padx=12, pady=(8, 12))
        
        # Botones principales
        ttk.Button(actions_row, text="✨ Nuevo Producto", command=self.nuevo_producto, style='Luxury.Primary.TButton').pack(side="left", padx=4)
        ttk.Button(actions_row, text="✏️ Editar Producto", command=self.editar_producto, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        ttk.Button(actions_row, text="🗑️ Eliminar Producto", command=self.eliminar_producto, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        
        # Separador visual
        sep = tk.Frame(actions_row, width=2, bg=Luxury2026Colors.TEXT_TERTIARY)
        sep.pack(side="left", padx=8, fill="y")
        
        # Botones de importación
        ttk.Button(actions_row, text="📥 Importar CSV", command=self.importar_csv, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        ttk.Button(actions_row, text="📥 Importar Excel", command=self.importar_excel, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        
        # Separador
        sep2 = tk.Frame(actions_row, width=2, bg=Luxury2026Colors.TEXT_TERTIARY)
        sep2.pack(side="left", padx=8, fill="y")
        
        # Botones de exportación
        ttk.Button(actions_row, text="📤 Exportar CSV", command=self.exportar_csv, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        ttk.Button(actions_row, text="📤 Exportar Excel", command=self.exportar_excel, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        ttk.Button(actions_row, text="📄 Exportar PDF", command=self.exportar_pdf, style='Luxury.Secondary.TButton').pack(side="left", padx=4)

        # Tabla - ENAMORANTE  
        self.frame_list = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        self.frame_list.pack(fill="both", expand=True, padx=2, pady=4)
        
        # Encabezado de tabla
        tk.Label(self.frame_list, text="📦 Productos", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY).pack(anchor="w", padx=12, pady=(8, 4))
        
        # Frame interior para manejar tabla o empty state
        self.table_container = tk.Frame(self.frame_list, bg=Luxury2026Colors.BG_DARKEST)
        self.table_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        columns = ("codigo", "nombre", "categoria", "precio", "cantidad")
        self.tree = ttk.Treeview(self.table_container, columns=columns, show="headings", height=15)
        for c in columns:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("codigo", width=140, anchor="w", stretch=True)
        self.tree.column("nombre", width=260, anchor="w", stretch=True)
        self.tree.column("categoria", width=170, anchor="w", stretch=True)
        self.tree.column("precio", width=100, anchor="e", stretch=False)
        self.tree.column("cantidad", width=100, anchor="center", stretch=False)
        self.tree.pack(fill="both", expand=True)
        theme.aplicar_estilo_treeview(self.tree)
        scrollbars.agregar_scrollbar(self.tree, self.table_container)
        self.tree.bind("<Double-1>", lambda e: self.editar_producto())

        # Acciones - ENAMORANTES
        actions = tk.Frame(parent, bg=Luxury2026Colors.BG_DARKEST, pady=8)
        actions.pack(fill="x", pady=(6, 0))
        
        # Izquierda: Acciones primarias (NEW, EDIT, DELETE)
        left_actions = tk.Frame(actions, bg=Luxury2026Colors.BG_DARKEST)
        left_actions.pack(side="left")
        ttk.Button(left_actions, text="✨ Nuevo", command=self.nuevo_producto, style='Luxury.Primary.TButton').pack(side="left", padx=4)
        ttk.Button(left_actions, text="✏️  Editar", command=self.editar_producto, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        ttk.Button(left_actions, text="🗑️  Eliminar", command=self.eliminar_producto, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        
        # Derecha: Exportar/Importar  
        right_actions = tk.Frame(actions, bg=Luxury2026Colors.BG_DARKEST)
        right_actions.pack(side="right")
        ttk.Button(right_actions, text="📄 Stock PDF", command=self.exportar_pdf_stock_bajo, style='Luxury.Secondary.TButton').pack(side="right", padx=4)
        ttk.Button(right_actions, text="📊 Inv. PDF", command=self.exportar_pdf, style='Luxury.Secondary.TButton').pack(side="right", padx=4)
        ttk.Button(right_actions, text="📥 Import Excel", command=self.importar_excel, style='Luxury.Secondary.TButton').pack(side="right", padx=4)
        ttk.Button(right_actions, text="📤 Export Excel", command=self.exportar_excel, style='Luxury.Secondary.TButton').pack(side="right", padx=4)
        ttk.Button(right_actions, text="📥 Import CSV", command=self.importar_csv, style='Luxury.Secondary.TButton').pack(side="right", padx=4)
        ttk.Button(right_actions, text="📤 Export CSV", command=self.exportar_csv, style='Luxury.Secondary.TButton').pack(side="right", padx=4)

        # Paginación - MEJORADA
        frame_pager = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame_pager.pack(fill="x", pady=(6, 4), padx=2)
        
        tk.Label(frame_pager, text="📄 Paginación", font=ModernTypography.font_caption(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(6, 0))
        
        controls = tk.Frame(frame_pager, bg=Luxury2026Colors.BG_SECONDARY)
        controls.pack(fill="x", padx=12, pady=(6, 12))
        
        ttk.Button(controls, text="⏮ Inicio", width=8, command=self.first_page, style='Luxury.Secondary.TButton').pack(side="left", padx=2)
        ttk.Button(controls, text="◀ Anterior", width=8, command=self.prev_page, style='Luxury.Secondary.TButton').pack(side="left", padx=2)
        ttk.Button(controls, text="Siguiente ▶", width=8, command=self.next_page, style='Luxury.Secondary.TButton').pack(side="left", padx=2)
        ttk.Button(controls, text="Fin ⏭", width=8, command=self.last_page, style='Luxury.Secondary.TButton').pack(side="left", padx=2)
        
        tk.Label(controls, text="Por página:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(side="left", padx=(16, 4))
        self.combo_page_size = ttk.Combobox(controls, values=PAGE_SIZE_OPTIONS, width=5, state="readonly")
        self.combo_page_size.set(DEFAULT_PAGE_SIZE)
        self.combo_page_size.pack(side="left", padx=4)
        self.combo_page_size.bind("<<ComboboxSelected>>", lambda e: self.change_page_size())
        
        self.lbl_range = tk.Label(controls, text="Mostrando 0–0 de 0 (pág. 0)", 
                                 font=ModernTypography.font_body_small(),
                                 bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY)
        self.lbl_range.pack(side="right", padx=12)

    def _build_tab_movimientos(self, parent: ttk.Frame):
        """Movimientos: Compras, Ventas, Ajustes - ENAMORANTE"""
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        # ---- COMPRAS ----
        tab_c = tk.Frame(nb, bg=Luxury2026Colors.BG_DARKEST)
        nb.add(tab_c, text="🛍️  Compras")
        
        # Encabezado
        title_c = tk.Label(tab_c, text="📥 Registro de Compras", font=ModernTypography.font_heading_lg(),
                          bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.PRIMARY)
        title_c.pack(anchor="w", padx=12, pady=(12, 20))
        
        # Cabecera
        form_c = tk.Frame(tab_c, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        form_c.pack(fill="x", padx=6, pady=6)
        tk.Label(form_c, text="📋 Cabecera", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY).pack(anchor="w", padx=12, pady=(8, 0))
        
        # Grid for header fields
        hdr_frame = tk.Frame(form_c, bg=Luxury2026Colors.BG_SECONDARY)
        hdr_frame.pack(fill="x", padx=12, pady=(8, 12))
        
        tk.Label(hdr_frame, text="Nº Doc:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.comp_num = tk.Entry(hdr_frame, width=16, font=ModernTypography.font_body(),
                                bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.comp_num.grid(row=1, column=0, sticky="we", pady=(0, 12))
        
        tk.Label(hdr_frame, text="Fecha (YYYY-MM-DD HH:MM:SS)", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        self.comp_fecha = tk.Entry(hdr_frame, width=22, font=ModernTypography.font_body(),
                                  bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                  insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.comp_fecha.grid(row=1, column=1, sticky="we", padx=(12, 0), pady=(0, 12))
        
        tk.Label(hdr_frame, text="Proveedor (código)", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=2, sticky="w", padx=(12, 0), pady=(0, 4))
        self.comp_partner = tk.Entry(hdr_frame, width=18, font=ModernTypography.font_body(),
                                    bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                    insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.comp_partner.grid(row=1, column=2, sticky="we", padx=(12, 0), pady=(0, 12))
        
        tk.Label(hdr_frame, text="Serie", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=3, sticky="w", padx=(12, 0), pady=(0, 4))
        self.comp_serie = ttk.Combobox(hdr_frame, values=["C01"], width=8, state="readonly")
        self.comp_serie.set("C01")
        self.comp_serie.grid(row=1, column=3, sticky="we", padx=(12, 0), pady=(0, 12))
        
        tk.Label(hdr_frame, text="Notas:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=4, sticky="w", padx=(12, 0), pady=(0, 4))
        self.comp_notas = tk.Entry(hdr_frame, width=25, font=ModernTypography.font_body(),
                                  bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                  insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.comp_notas.grid(row=1, column=4, sticky="we", padx=(12, 0), pady=(0, 12))
        
        for i in range(5):
            hdr_frame.grid_columnconfigure(i, weight=1)
        
        # Líneas
        lines_c = tk.Frame(tab_c, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        lines_c.pack(fill="both", expand=True, padx=6, pady=6)
        tk.Label(lines_c, text="📦 Líneas de compra", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(8, 0))
        
        self.comp_lines = []
        self._line_builder(lines_c, self.comp_lines, purchase=True)
        
        # Botones
        btns_c = tk.Frame(tab_c, bg=Luxury2026Colors.BG_DARKEST)
        btns_c.pack(fill="x", padx=6, pady=6)
        ttk.Button(btns_c, text="✅ Registrar compra", command=self._comp_registrar, style='Luxury.Primary.TButton').pack(side="left", padx=4)
        ttk.Button(btns_c, text="↻ Limpiar", command=lambda: self._lines_clear(self.comp_lines), style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        ttk.Button(btns_c, text="📄 PDF último", command=self._comp_pdf_last, style='Luxury.Secondary.TButton').pack(side="right", padx=4)

        # ---- VENTAS ----
        tab_v = tk.Frame(nb, bg=Luxury2026Colors.BG_DARKEST)
        nb.add(tab_v, text="💳 Ventas")
        
        # Encabezado
        title_v = tk.Label(tab_v, text="📤 Registro de Ventas", font=ModernTypography.font_heading_lg(),
                          bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.SUCCESS)
        title_v.pack(anchor="w", padx=12, pady=(12, 20))
        
        # Cabecera
        form_v = tk.Frame(tab_v, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        form_v.pack(fill="x", padx=6, pady=6)
        tk.Label(form_v, text="📋 Cabecera", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.SUCCESS).pack(anchor="w", padx=12, pady=(8, 0))
        
        # Grid for header fields (similar to compras)
        hdr_frame_v = tk.Frame(form_v, bg=Luxury2026Colors.BG_SECONDARY)
        hdr_frame_v.pack(fill="x", padx=12, pady=(8, 12))
        
        tk.Label(hdr_frame_v, text="Nº Doc:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.sale_num = tk.Entry(hdr_frame_v, width=16, font=ModernTypography.font_body(),
                                bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.sale_num.grid(row=1, column=0, sticky="we", pady=(0, 12))
        
        tk.Label(hdr_frame_v, text="Fecha (YYYY-MM-DD HH:MM:SS)", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        self.sale_fecha = tk.Entry(hdr_frame_v, width=22, font=ModernTypography.font_body(),
                                  bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                  insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.sale_fecha.grid(row=1, column=1, sticky="we", padx=(12, 0), pady=(0, 12))
        
        tk.Label(hdr_frame_v, text="Cliente (código)", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=2, sticky="w", padx=(12, 0), pady=(0, 4))
        self.sale_partner = tk.Entry(hdr_frame_v, width=18, font=ModernTypography.font_body(),
                                    bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                    insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.sale_partner.grid(row=1, column=2, sticky="we", padx=(12, 0), pady=(0, 12))
        
        tk.Label(hdr_frame_v, text="Serie", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=3, sticky="w", padx=(12, 0), pady=(0, 4))
        self.sale_serie = ttk.Combobox(hdr_frame_v, values=["V01"], width=8, state="readonly")
        self.sale_serie.set("V01")
        self.sale_serie.grid(row=1, column=3, sticky="we", padx=(12, 0), pady=(0, 12))
        
        tk.Label(hdr_frame_v, text="Notas:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=4, sticky="w", padx=(12, 0), pady=(0, 4))
        self.sale_notas = tk.Entry(hdr_frame_v, width=25, font=ModernTypography.font_body(),
                                  bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                  insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.sale_notas.grid(row=1, column=4, sticky="we", padx=(12, 0), pady=(0, 12))
        
        for i in range(5):
            hdr_frame_v.grid_columnconfigure(i, weight=1)
        
        # Líneas
        lines_v = tk.Frame(tab_v, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        lines_v.pack(fill="both", expand=True, padx=6, pady=6)
        tk.Label(lines_v, text="📦 Líneas de venta", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.SUCCESS).pack(anchor="w", padx=12, pady=(8, 0))
        
        self.sale_lines = []
        self._line_builder(lines_v, self.sale_lines, purchase=False)
        
        # Botones
        btns_v = tk.Frame(tab_v, bg=Luxury2026Colors.BG_DARKEST)
        btns_v.pack(fill="x", padx=6, pady=6)
        ttk.Button(btns_v, text="✅ Registrar venta", command=self._sale_registrar, style='Luxury.Primary.TButton').pack(side="left", padx=4)
        ttk.Button(btns_v, text="↻ Limpiar", command=lambda: self._lines_clear(self.sale_lines), style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        ttk.Button(btns_v, text="📄 PDF último", command=self._sale_pdf_last, style='Luxury.Secondary.TButton').pack(side="right", padx=4)

        # ---- AJUSTES ----
        tab_a = tk.Frame(nb, bg=Luxury2026Colors.BG_DARKEST)
        nb.add(tab_a, text="⚙️ Ajustes")
        
        # Encabezado
        title_a = tk.Label(tab_a, text="🔧 Ajustes de Stock", font=ModernTypography.font_heading_lg(),
                          bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.WARNING)
        title_a.pack(anchor="w", padx=12, pady=(12, 20))
        
        # Ajustes
        adj = tk.Frame(tab_a, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        adj.pack(fill="both", expand=True, padx=6, pady=6)
        tk.Label(adj, text="📋 Líneas de ajuste", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.WARNING).pack(anchor="w", padx=12, pady=(8, 0))
        
        self.adj_lines = []
        self._adjust_builder(adj, self.adj_lines)
        
        # Botones
        btns_a = tk.Frame(tab_a, bg=Luxury2026Colors.BG_DARKEST)
        btns_a.pack(fill="x", padx=6, pady=6)
        ttk.Button(btns_a, text="✅ Registrar ajuste", command=self._adj_registrar, style='Luxury.Primary.TButton').pack(side="left", padx=4)
        ttk.Button(btns_a, text="↻ Limpiar", command=lambda: self._adj_clear(self.adj_lines), style='Luxury.Secondary.TButton').pack(side="left", padx=4)

    def _build_tab_hist(self, parent: ttk.Frame):
        frame = ttk.LabelFrame(parent, text="Historial (altas/modificaciones/importaciones)")
        frame.pack(fill="both", expand=True, padx=6, pady=6)
        cols = ("codigo", "nombre", "accion", "fecha")
        self.tree_hist = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.tree_hist.heading(c, text=c.capitalize())
            self.tree_hist.column(c, width=180, anchor="w")
        self.tree_hist.pack(fill="both", expand=True)
        theme.aplicar_estilo_treeview(self.tree_hist)
        scrollbars.agregar_scrollbar(self.tree_hist, frame)

    def _build_tab_reportes(self, parent: ttk.Frame):
        """Kardex de productos - ENAMORANTE"""
        # HÉROE VISUAL: Movimientos totales - 36px
        frame_hero = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame_hero.pack(fill="x", padx=2, pady=4)
        
        tk.Label(frame_hero, text="Movimientos registrados", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(8, 0))
        
        self.kx_hero_count = tk.Label(frame_hero, text="0", font=("Arial", 36, "bold"),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT)
        self.kx_hero_count.pack(anchor="w", padx=12, pady=(0, 12))
        
        # Encabezado
        title = tk.Label(parent, text="📊 Kardex de Productos", font=ModernTypography.font_heading_lg(),
                        bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.PRIMARY)
        title.pack(anchor="w", padx=12, pady=(12, 20))
        
        # Filtros
        box = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        box.pack(fill="x", pady=6, padx=6)
        
        tk.Label(box, text="🔍 Seleccionar producto", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY).pack(anchor="w", padx=12, pady=(8, 0))
        
        filter_frame = tk.Frame(box, bg=Luxury2026Colors.BG_SECONDARY)
        filter_frame.pack(fill="x", padx=12, pady=(8, 0))
        
        tk.Label(filter_frame, text="Código:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.kx_cod = tk.Entry(filter_frame, width=16, font=ModernTypography.font_body(),
                              bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                              insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.kx_cod.grid(row=1, column=0, sticky="we", pady=(0, 12))
        
        tk.Label(filter_frame, text="Nombre:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        self.kx_name = tk.Label(filter_frame, text="—", font=ModernTypography.font_body(),
                               bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT)
        self.kx_name.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=(0, 12))
        
        # Rango de fechas
        tk.Label(box, text="📅 Rango de fechas (opcional)", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(12, 0))
        
        date_frame = tk.Frame(box, bg=Luxury2026Colors.BG_SECONDARY)
        date_frame.pack(fill="x", padx=12, pady=(8, 12))
        
        tk.Label(date_frame, text="Desde (YYYY-MM-DD):", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.kx_from = tk.Entry(date_frame, width=18, font=ModernTypography.font_body(),
                               bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                               insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.kx_from.grid(row=1, column=0, sticky="we", pady=(0, 12))
        
        tk.Label(date_frame, text="Hasta (YYYY-MM-DD):", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        self.kx_to = tk.Entry(date_frame, width=18, font=ModernTypography.font_body(),
                             bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                             insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.kx_to.grid(row=1, column=1, sticky="we", padx=(12, 0), pady=(0, 12))
        
        for i in range(2):
            date_frame.grid_columnconfigure(i, weight=1)
        
        # Botones
        btns = tk.Frame(box, bg=Luxury2026Colors.BG_SECONDARY)
        btns.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(btns, text="🔎 Generar Kardex", command=self._kx_generate, style='Luxury.Primary.TButton').pack(side="left", padx=4)
        ttk.Button(btns, text="📊 Exportar Excel", command=self._kx_export_xlsx, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        ttk.Button(btns, text="📄 Exportar PDF", command=self._kx_export_pdf, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        
        # Resultados
        frame = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        tk.Label(frame, text="📈 Resultados", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.SUCCESS).pack(anchor="w", padx=12, pady=(8, 0))
        
        cols = ("fecha", "doc_no", "tipo", "qty_in", "qty_out", "unit_cost", "unit_price", "motivo", "saldo_qty", "saldo_cost", "saldo_total")
        heads = {
            "fecha": "Fecha",
            "doc_no": "Doc Nº",
            "tipo": "Tipo",
            "qty_in": "Entrada",
            "qty_out": "Salida",
            "unit_cost": "Costo u.",
            "unit_price": "Precio u.",
            "motivo": "Motivo",
            "saldo_qty": "Saldo Qty",
            "saldo_cost": "Costo Prom.",
            "saldo_total": "Valorización",
        }
        widths = {
            "fecha": 130, "doc_no": 100, "tipo": 80, "qty_in": 90, "qty_out": 90,
            "unit_cost": 90, "unit_price": 90, "motivo": 150, "saldo_qty": 90, "saldo_cost": 100, "saldo_total": 110,
        }
        
        tree_frame = tk.Frame(frame, bg=Luxury2026Colors.BG_DARKEST)
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        
        self.kx_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)
        for c in cols:
            self.kx_tree.heading(c, text=heads[c])
            self.kx_tree.column(c, width=widths[c], anchor="w" if c in ("fecha", "doc_no", "tipo", "motivo") else "e")
        self.kx_tree.pack(fill="both", expand=True)
        theme.aplicar_estilo_treeview(self.kx_tree)
        scrollbars.agregar_scrollbar(self.kx_tree, tree_frame)
        
        # Resumen
        summary_frame = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        summary_frame.pack(fill="x", padx=6, pady=6)
        tk.Label(summary_frame, text="📌 Resumen", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(8, 0))
        
        self.kx_summary = tk.Label(summary_frame, text="—", font=ModernTypography.font_body_small(),
                                  bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY)
        self.kx_summary.pack(anchor="w", padx=12, pady=(8, 12))
        
        self.kx_cod.bind("<FocusOut>", lambda e: self._kx_autoname())

    def _build_tab_auditoria(self, parent: ttk.Frame):
        """Auditoría y Historial - ENAMORANTE"""
        
        # Encabezado
        title = tk.Label(parent, text="🔍 Auditoría del Sistema", font=ModernTypography.font_heading_lg(),
                        bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.DANGER)
        title.pack(anchor="w", padx=12, pady=(12, 20))
        
        self.audit_filters = {
            "user_q": None, "action_q": None, "text_q": None,
            "date_from": None, "date_to": None, "limit": 50, "offset": 0,
        }
        
        # FILTROS
        filter_box = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        filter_box.pack(fill="x", padx=6, pady=6)
        
        tk.Label(filter_box, text="🔎 Filtros de búsqueda", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(8, 0))
        
        filter_frame = tk.Frame(filter_box, bg=Luxury2026Colors.BG_SECONDARY)
        filter_frame.pack(fill="x", padx=12, pady=(8, 12))
        
        # Fila 1: Usuario, Acción, Texto
        tk.Label(filter_frame, text="Usuario:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.af_user = tk.Entry(filter_frame, width=16, font=ModernTypography.font_body(),
                               bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                               insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.af_user.grid(row=1, column=0, sticky="we", pady=(0, 12))
        
        tk.Label(filter_frame, text="Acción:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        self.af_action = tk.Entry(filter_frame, width=16, font=ModernTypography.font_body(),
                                 bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                 insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.af_action.grid(row=1, column=1, sticky="we", padx=(12, 0), pady=(0, 12))
        
        tk.Label(filter_frame, text="Texto:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=2, sticky="w", padx=(12, 0), pady=(0, 4))
        self.af_text = tk.Entry(filter_frame, width=20, font=ModernTypography.font_body(),
                               bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                               insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.af_text.grid(row=1, column=2, sticky="we", padx=(12, 0), pady=(0, 12))
        
        # Fila 2: Fechas
        tk.Label(filter_frame, text="Desde (YYYY-MM-DD):", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.af_from = tk.Entry(filter_frame, width=16, font=ModernTypography.font_body(),
                               bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                               insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.af_from.grid(row=3, column=0, sticky="we", pady=(0, 12))
        
        tk.Label(filter_frame, text="Hasta (YYYY-MM-DD):", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=2, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        self.af_to = tk.Entry(filter_frame, width=16, font=ModernTypography.font_body(),
                             bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                             insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.af_to.grid(row=3, column=1, sticky="we", padx=(12, 0), pady=(0, 12))
        
        for i in range(3):
            filter_frame.grid_columnconfigure(i, weight=1)
        
        # Botones
        btn_frame = tk.Frame(filter_frame, bg=Luxury2026Colors.BG_SECONDARY)
        btn_frame.grid(row=3, column=2, sticky="e", padx=(12, 0))
        ttk.Button(btn_frame, text="🔎 Buscar", command=lambda: self._audit_reload(reset=True), style='Luxury.Primary.TButton').pack(side="left", padx=4)
        ttk.Button(btn_frame, text="↻ Limpiar", command=self._audit_clear, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        
        for i in range(3):
            filter_frame.grid_columnconfigure(i, weight=1)
        
        # TABLA DE EVENTOS
        events_box = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        events_box.pack(fill="both", expand=True, padx=6, pady=6)
        
        tk.Label(events_box, text="📅 Eventos del Sistema", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.DANGER).pack(anchor="w", padx=12, pady=(8, 0))
        
        cols = ("fecha", "usuario", "accion", "detalles")
        heads = {"fecha": "Fecha", "usuario": "Usuario", "accion": "Acción", "detalles": "Detalles"}
        widths = {"fecha": 160, "usuario": 140, "accion": 140, "detalles": 500}
        tree_frame = tk.Frame(events_box, bg=Luxury2026Colors.BG_DARKEST)
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        self.audit_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for c in cols:
            self.audit_tree.heading(c, text=heads[c])
            self.audit_tree.column(c, width=widths[c], anchor="w")
        self.audit_tree.pack(fill="both", expand=True)
        theme.aplicar_estilo_treeview(self.audit_tree)
        scrollbars.agregar_scrollbar(self.audit_tree, tree_frame)
        
        # PAGINACIÓN
        pager = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        pager.pack(fill="x", padx=6, pady=6)
        
        tk.Label(pager, text="📄 Navegación", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(8, 0))
        
        pager_controls = tk.Frame(pager, bg=Luxury2026Colors.BG_SECONDARY)
        pager_controls.pack(fill="x", padx=12, pady=(8, 12))
        
        ttk.Button(pager_controls, text="⏮ Inicio", command=lambda: self._audit_jump("first"), style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        ttk.Button(pager_controls, text="◀ Anterior", command=lambda: self._audit_jump("prev"), style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        ttk.Button(pager_controls, text="Siguiente ▶", command=lambda: self._audit_jump("next"), style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        ttk.Button(pager_controls, text="Fin ⏭", command=lambda: self._audit_jump("last"), style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        
        self.audit_lbl = tk.Label(pager_controls, text="Mostrando 0–0 de 0", font=ModernTypography.font_body_small(),
                                 bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY)
        self.audit_lbl.pack(side="right", padx=12)
        
        self._audit_do_list = lambda: list_audit(
            user_q=self.audit_filters["user_q"], action_q=self.audit_filters["action_q"],
            text_q=self.audit_filters["text_q"], date_from=self.audit_filters["date_from"],
            date_to=self.audit_filters["date_to"], limit=self.audit_filters["limit"],
            offset=self.audit_filters["offset"], order_desc=True,
        )
        self._audit_total = 0
        self._audit_reload(reset=True)

    def _build_tab_users(self, parent: ttk.Frame):
        """Administración de Usuarios y Roles - layout con scroll para que los botones siempre sean visibles"""

        # ── Canvas + scrollbar vertical para toda la pestaña ──────────────
        canvas = tk.Canvas(parent, bg=Luxury2026Colors.BG_DARKEST, highlightthickness=0)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=Luxury2026Colors.BG_DARKEST)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_resize(e):
            canvas.itemconfig(inner_id, width=e.width)
        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_canvas_resize)
        # scroll con rueda del mouse
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # ── HÉROE: Usuarios activos ────────────────────────────────────────
        frame_hero = tk.Frame(inner, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame_hero.pack(fill="x", padx=2, pady=4)
        tk.Label(frame_hero, text="Usuarios activos en el sistema",
                font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY
                ).pack(anchor="w", padx=12, pady=(8, 0))
        self.u_hero_active = tk.Label(frame_hero, text="0", font=("Arial", 36, "bold"),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.SUCCESS)
        self.u_hero_active.pack(anchor="w", padx=12, pady=(0, 12))

        tk.Label(inner, text="👥 Gestión de Usuarios", font=ModernTypography.font_heading_lg(),
                bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.PRIMARY
                ).pack(anchor="w", padx=12, pady=(12, 8))

        # ── FILA SUPERIOR: Crear usuario | Acciones | Roles (lado a lado) ──
        top_row = tk.Frame(inner, bg=Luxury2026Colors.BG_DARKEST)
        top_row.pack(fill="x", padx=6, pady=4)

        # COLUMNA IZQUIERDA: Crear usuario
        create_box = tk.Frame(top_row, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        create_box.pack(side="left", fill="both", expand=True, padx=(0, 4))
        tk.Label(create_box, text="➕ Crear Nuevo Usuario", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.SUCCESS
                ).pack(anchor="w", padx=12, pady=(8, 0))

        create_frame = tk.Frame(create_box, bg=Luxury2026Colors.BG_SECONDARY)
        create_frame.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(create_frame, text="Usuario:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY
                ).pack(anchor="w")
        self.u_username = tk.Entry(create_frame, font=ModernTypography.font_body(),
                                  bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                  insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.u_username.pack(fill="x", pady=(2, 6))
        tk.Label(create_frame, text="Nombre:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY
                ).pack(anchor="w")
        self.u_name = tk.Entry(create_frame, font=ModernTypography.font_body(),
                              bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                              insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.u_name.pack(fill="x", pady=(2, 8))
        ttk.Button(create_box, text="✨ Crear usuario", command=self._user_create,
                  style='Luxury.Primary.TButton').pack(anchor="w", padx=12, pady=(0, 12))

        # COLUMNA CENTRAL: Acciones sobre usuario seleccionado
        actions_box = tk.Frame(top_row, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        actions_box.pack(side="left", fill="both", padx=(0, 4))
        tk.Label(actions_box, text="⚙️ Acciones", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.WARNING
                ).pack(anchor="w", padx=12, pady=(8, 4))
        tk.Label(actions_box, text="(selecciona un usuario)", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_TERTIARY
                ).pack(anchor="w", padx=12, pady=(0, 8))
        ttk.Button(actions_box, text="✅ Activar",
                  command=lambda: self._user_active(True),
                  style='Luxury.Secondary.TButton').pack(fill="x", padx=12, pady=2)
        ttk.Button(actions_box, text="❌ Desactivar",
                  command=lambda: self._user_active(False),
                  style='Luxury.Secondary.TButton').pack(fill="x", padx=12, pady=2)
        ttk.Button(actions_box, text="🔑 Reset Password",
                  command=self._user_reset_pwd,
                  style='Luxury.Secondary.TButton').pack(fill="x", padx=12, pady=(2, 12))

        # COLUMNA DERECHA: Gestión de roles
        roles_box = tk.Frame(top_row, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        roles_box.pack(side="left", fill="both", expand=True)
        tk.Label(roles_box, text="🎭 Roles", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PURPLE
                ).pack(anchor="w", padx=12, pady=(8, 0))
        tk.Label(roles_box, text="Ctrl+clic para múltiples", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY
                ).pack(anchor="w", padx=12, pady=(2, 4))
        list_frame = tk.Frame(roles_box, bg=Luxury2026Colors.BG_DARKEST, relief="solid", bd=1)
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.roles_list = tk.Listbox(list_frame, selectmode="multiple", height=4,
                                    exportselection=False,
                                    font=ModernTypography.font_body_small(),
                                    bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                    highlightthickness=0, relief="solid", bd=1)
        self.roles_list.pack(fill="both", expand=True, padx=4, pady=4)
        ttk.Button(roles_box, text="💾 Guardar Roles", command=self._user_save_roles,
                  style='Luxury.Primary.TButton').pack(anchor="w", padx=12, pady=(0, 12))

        # ── SECCIÓN 2: Lista de usuarios ───────────────────────────────────
        users_box = tk.Frame(inner, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        users_box.pack(fill="both", expand=True, padx=6, pady=6)
        tk.Label(users_box, text="📋 Lista de Usuarios", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT
                ).pack(anchor="w", padx=12, pady=(8, 0))

        cols = ("id", "username", "name", "active", "roles")
        heads = {"id": "ID", "username": "Usuario", "name": "Nombre", "active": "Estado", "roles": "Roles"}
        widths = {"id": 50, "username": 120, "name": 200, "active": 80, "roles": 260}

        tree_frame = tk.Frame(users_box, bg=Luxury2026Colors.BG_DARKEST)
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        self.users_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=10)
        for c in cols:
            self.users_tree.heading(c, text=heads[c])
            self.users_tree.column(c, width=widths[c], anchor="w")
        self.users_tree.pack(fill="both", expand=True)
        theme.aplicar_estilo_treeview(self.users_tree)
        scrollbars.agregar_scrollbar(self.users_tree, tree_frame)
        self.users_tree.bind("<<TreeviewSelect>>", lambda e: self._sync_selected_user_roles())

    def _users_reload(self):
        # limpiar tabla
        for i in self.users_tree.get_children():
            self.users_tree.delete(i)

        data = list_users()  # puede devolver tuplas o dicts
        active_count = 0

        for r in data:
            if isinstance(r, dict):
                uid = r.get("id")
                username = r.get("username") or r.get("user")
                name = r.get("name") or r.get("fullname")
                active_raw = r.get("active", 0)
                roles_raw = r.get("roles", "")
            else:
                # tupla esperada: (id, username, name, active, roles)
                uid = r[0] if len(r) > 0 else None
                username = r[1] if len(r) > 1 else ""
                name = r[2] if len(r) > 2 else ""
                active_raw = r[3] if len(r) > 3 else 0
                roles_raw = r[4] if len(r) > 4 else ""

            # normalizar activo
            active = "Sí" if active_raw in (1, True, "1", "true", "True", "YES", "Sí", "Si") else "No"
            if active == "Sí":
                active_count += 1

            # normalizar roles (puede venir como lista/tupla o string)
            if isinstance(roles_raw, (list, tuple, set)):
                roles = ", ".join(str(x) for x in roles_raw)
            else:
                roles = str(roles_raw or "")

            self.users_tree.insert("", "end", values=(uid, username, name, active, roles))

        # Actualizar héroe visual
        self.u_hero_active.config(text=str(active_count))

        # Cargar catálogo de roles
        self.roles_list.delete(0, tk.END)
        for ro in list_roles():
            self.roles_list.insert(tk.END, ro)

    def _build_tab_settings(self, parent: ttk.Frame):
        """Configuración del Sistema - ENAMORANTE"""
        
        # Encabezado
        title = tk.Label(parent, text="⚙️ Parámetros del Sistema", font=ModernTypography.font_heading_lg(),
                        bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.PRIMARY)
        title.pack(anchor="w", padx=12, pady=(12, 20))
        
        s = get_settings()
        
        # GRUPO 1: Datos de la Empresa
        box = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        box.pack(fill="x", padx=6, pady=6)
        
        tk.Label(box, text="🏢 Datos de la Empresa", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY).pack(anchor="w", padx=12, pady=(8, 0))
        
        company_frame = tk.Frame(box, bg=Luxury2026Colors.BG_SECONDARY)
        company_frame.pack(fill="x", padx=12, pady=(8, 12))
        
        tk.Label(company_frame, text="Nombre de la empresa:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.st_name = tk.Entry(company_frame, width=40, font=ModernTypography.font_body(),
                               bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                               insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.st_name.grid(row=1, column=0, sticky="we", pady=(0, 12))
        self.st_name.insert(0, s["company_name"])
        
        tk.Label(company_frame, text="NIT/RUC:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        self.st_tax = tk.Entry(company_frame, width=28, font=ModernTypography.font_body(),
                              bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                              insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.st_tax.grid(row=1, column=1, sticky="we", padx=(12, 0), pady=(0, 12))
        self.st_tax.insert(0, s["company_tax"])
        
        tk.Label(company_frame, text="Dirección:", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.st_addr = tk.Entry(company_frame, width=55, font=ModernTypography.font_body(),
                               bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                               insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.st_addr.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, 12))
        self.st_addr.insert(0, s["company_addr"])
        
        tk.Label(company_frame, text="Logo (ruta opcional):", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 4))
        logo_row = tk.Frame(company_frame, bg=Luxury2026Colors.BG_SECONDARY)
        logo_row.grid(row=5, column=0, columnspan=2, sticky="we", pady=(0, 12))
        self.st_logo = tk.Entry(logo_row, width=48, font=ModernTypography.font_body(),
                               bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                               insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.st_logo.pack(side="left", fill="x", expand=True)
        if s.get("logo_path"):
            self.st_logo.insert(0, s["logo_path"])
        ttk.Button(logo_row, text="🖼️ Buscar…", command=self._st_pick_logo, style='Luxury.Secondary.TButton').pack(side="left", padx=(6, 0))
        
        company_frame.grid_columnconfigure(0, weight=1)
        company_frame.grid_columnconfigure(1, weight=1)
        
        # GRUPO 2: Impuestos
        opts = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        opts.pack(fill="x", padx=6, pady=6)
        
        tk.Label(opts, text="💰 Configuración de Impuestos", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.SUCCESS).pack(anchor="w", padx=12, pady=(8, 0))
        
        tax_frame = tk.Frame(opts, bg=Luxury2026Colors.BG_SECONDARY)
        tax_frame.pack(fill="x", padx=12, pady=(8, 12))
        
        self.st_tax_included = tk.BooleanVar(value=bool(s["tax_included"]))
        tax_check = tk.Checkbutton(tax_frame, text="Precios incluyen impuestos", variable=self.st_tax_included,
                                  font=ModernTypography.font_body_small(),
                                  bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                  activebackground=Luxury2026Colors.BG_HOVER,
                                  selectcolor=Luxury2026Colors.PRIMARY, highlightthickness=0)
        tax_check.pack(anchor="w", pady=(0, 12))
        
        tk.Label(tax_frame, text="Tasa de impuesto (ej. 0.19 para 19%):", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.st_tax_rate = tk.Entry(tax_frame, width=12, font=ModernTypography.font_body(),
                                   bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                   insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.st_tax_rate.pack(anchor="w")
        self.st_tax_rate.insert(0, str(s["tax_rate"]))
        
        # BOTONES
        btns = tk.Frame(parent, bg=Luxury2026Colors.BG_DARKEST)
        btns.pack(fill="x", padx=6, pady=6)
        ttk.Button(btns, text="💾 Guardar Cambios", command=self._st_save, style='Luxury.Primary.TButton').pack(side="left", padx=4)
        ttk.Button(btns, text="↻ Restaurar valores actuales", command=self._st_reload, style='Luxury.Secondary.TButton').pack(side="left", padx=4)

    # =========================
    # Inventario: handlers
    # =========================
    def refrescar_todo(self):
        from src.core import caching
        caching.clear_cache("src.database.repository.list_products")
        caching.clear_cache("src.database.repository.count_products")
        caching.clear_cache("src.database.repository.get_product_by_code")
        self._total_items = count_products(self._filter_by, self._filter_q)
        self._page = 1
        self._load_page()
        self._load_hist()
        self._update_stats()
        # Refresca el dashboard
        if hasattr(self, 'dashboard'):
            self.dashboard.update()
        # Recargar usuarios si la pestaña de administración existe
        if hasattr(self, 'users_tree'):
            self._users_reload()

    def _load_page(self):
        # refrescar conteo en cada carga para evitar cachés desfasados
        self._total_items = count_products(self._filter_by, self._filter_q)

        rows = list_products_page(
            self._page, self._page_size, self._filter_by, self._filter_q, self._order_by, self._asc
        )
        
        # Limpiar tabla anterior
        self.tree.delete(*self.tree.get_children())
        
        # Si no hay filas para mostrar, mostrar empty state
        if not rows:
            # Ocultar tabla
            self.tree.pack_forget()
            
            # Mostrar empty state hermoso
            for child in self.table_container.winfo_children():
                if isinstance(child, tk.Frame):
                    child.destroy()
            
            empty_frame = tk.Frame(self.table_container, bg=Luxury2026Colors.BG_DARKEST)
            empty_frame.pack(fill="both", expand=True)
            
            # Icono grande
            tk.Label(
                empty_frame,
                text="📦",
                font=("Arial", 64),
                bg=Luxury2026Colors.BG_DARKEST,
                fg=Luxury2026Colors.TEXT_SECONDARY
            ).pack(pady=(40, 20))
            
            # Título
            tk.Label(
                empty_frame,
                text="Sin productos aún",
                font=ModernTypography.font_heading_lg(),
                bg=Luxury2026Colors.BG_DARKEST,
                fg=Luxury2026Colors.TEXT_PRIMARY
            ).pack()
            
            # Subtítulo
            tk.Label(
                empty_frame,
                text="Crea tu primer producto y verás la magia suceder",
                font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_DARKEST,
                fg=Luxury2026Colors.TEXT_SECONDARY
            ).pack(pady=(8, 32))
            
            # Botón CTA
            ttk.Button(
                empty_frame,
                text="✨ Crear primer producto",
                command=self.nuevo_producto
            ).pack()
        else:
            # Mostrar tabla
            if not self.tree.winfo_viewable():
                self.tree.pack(fill="both", expand=True)
            
            # Cargar datos
            for i, p in enumerate(rows):
                tag = "par" if i % 2 == 0 else "impar"
                if p[4] <= UMBRAL_STOCK_BAJO:
                    tag = "baja"
                self.tree.insert("", "end", values=p, tags=(tag,))
        
        # Actualizar stats de paginación
        total_pages = max(1, (self._total_items + self._page_size - 1) // self._page_size)
        start = 0 if self._total_items == 0 else (self._page - 1) * self._page_size + 1
        end = min(self._page * self._page_size, self._total_items)
        self.lbl_range.config(text=f"Mostrando {start}–{end} de {self._total_items} (pág. {self._page} de {total_pages})")

    def _update_stats(self):
        self.lbl_total_productos.config(text=str(count_products()))
        stock_total = str(int(stock_global_sum()))
        self.lbl_total_stock_hero.config(text=stock_total)
        self.lbl_stock_bajo.config(text=str(low_stock_count(UMBRAL_STOCK_BAJO)))

    def refresh_products(self):
        """Refresca la tabla de productos y el dashboard"""
        from src.core import caching
        caching.clear_cache("src.database.repository.list_products")
        caching.clear_cache("src.database.repository.count_products")
        caching.clear_cache("src.database.repository.get_product_by_code")
        # asegurarnos siempre de tener el conteo real antes de cargar
        self._total_items = count_products(self._filter_by, self._filter_q)
        self._load_page()
        self._update_stats()
        if hasattr(self, 'dashboard') and self.dashboard:
            self.dashboard.update()

    def buscar_producto(self):
        self._filter_by = self.combo_filtro.get()
        self._filter_q = self.entry_buscar.get().strip()
        if self._filter_q == "🔍 Buscar producto por código o nombre...":
            self._filter_q = ""
        self._total_items = count_products(self._filter_by, self._filter_q)
        self._page = 1
        self.refresh_products()

    def limpiar_busqueda(self):
        self.combo_filtro.current(0)
        self.entry_buscar.delete(0, tk.END)
        self.entry_buscar.insert(0, "🔍 Buscar producto por código o nombre...")
        self.entry_buscar.config(fg="#6B7280")
        self._filter_by = None
        self._filter_q = ""
        self._total_items = count_products()
        self._page = 1
        self.refresh_products()

    def first_page(self):
        self._page = 1
        self.refresh_products()

    def prev_page(self):
        self._page = max(1, self._page - 1)
        self.refresh_products()

    def next_page(self):
        total_pages = max(1, (self._total_items + self._page_size - 1) // self._page_size)
        self._page = min(total_pages, self._page + 1)
        self.refresh_products()

    def last_page(self):
        self._page = max(1, (self._total_items + self._page_size - 1) // self._page_size)
        self.refresh_products()

    def change_page_size(self):
        try:
            self._page_size = int(self.combo_page_size.get())
        except Exception:
            self._page_size = DEFAULT_PAGE_SIZE
        self.first_page()

    def nuevo_producto(self):
        dlg = ProductoDialog(self.root, title="Nuevo producto")
        if not dlg.result:
            return
        try:
            # Extraer warehouse_id
            warehouse_id = dlg.result.pop("warehouse_id", None)
            
            # Crear producto
            add_product(**dlg.result, user_id=self.user["id"])
            
            # Si hay stock inicial y warehouse, asignar stock
            if dlg.result["cantidad"] > 0 and warehouse_id:
                from src.services.warehouses import set_stock
                set_stock(dlg.result["codigo"], warehouse_id, dlg.result["cantidad"], user_id=self.user["id"])
            
            # Set filter exactly to the new product so it is visible on page 1
            self.combo_filtro.set("Código")
            self.entry_buscar.delete(0, tk.END)
            self.entry_buscar.insert(0, dlg.result["codigo"])
            self._filter_by = "Código"
            self._filter_q = dlg.result["codigo"]

            # Resetear a la primera página y recargar
            self._page = 1
            self._total_items = count_products(self._filter_by, self._filter_q)
            self.refresh_products()
            # seleccionar y hacer scroll hacia el nuevo registro
            for iid in self.tree.get_children():
                if self.tree.item(iid)["values"][0] == dlg.result["codigo"]:
                    self.tree.selection_set(iid)
                    self.tree.see(iid)
                    break
            self.show_success("✅ Producto creado", f"Código: {dlg.result['codigo']} ✨")
        except Exception as e:
            messagebox.showerror("Nuevo producto", str(e))

    def editar_producto(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Editar", "Selecciona un producto.")
            return
        codigo = self.tree.item(sel[0])["values"][0]
        p = get_product(codigo)
        # Obtener avg_cost de la BD (asumiendo que repository lo devuelve)
        from src.database import repository
        full_p = repository.get_product_by_code(codigo)
        avg_cost = full_p[5] if full_p and len(full_p) > 5 else 0.0
        dlg = ProductoDialog(
            self.root,
            initial={"codigo": p[0], "nombre": p[1], "categoria": p[2], "precio": p[3], "cantidad": p[4], "avg_cost": avg_cost},
            editable_code=False,
            title="Editar producto",
        )
        if not dlg.result:
            return
        try:
            # Remover avg_cost y warehouse_id del update, ya que update_product no los maneja
            update_data = {k: v for k, v in dlg.result.items() if k not in ["codigo", "avg_cost", "warehouse_id"]}
            update_product(codigo, **update_data, user_id=self.user["id"])
            # Recargar la página actual sin cambiar de página
            self.refresh_products()
            self.show_success("✅ Producto actualizado", "Cambios guardados ✨")
        except Exception as e:
            messagebox.showerror("Editar producto", str(e))

    def eliminar_producto(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Eliminar", "Selecciona un producto.")
            return
        codigo = self.tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Eliminar", f"¿Eliminar el producto {codigo}?"):
            return
        try:
            delete_product(codigo, user_id=self.user["id"])
            # Recargar la página para ocultar el producto desactivado
            self.refresh_products()
            messagebox.showinfo("Eliminar", "El producto fue desactivado correctamente.")
        except Exception as e:
            messagebox.showerror("Eliminar", str(e))

    def exportar_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"productos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not path:
            return
        n = export_products_csv(path)
        messagebox.showinfo("Exportar CSV", f"Se exportaron {n} filas.")

    def importar_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return
        n = import_products_csv(path, upsert=True, user_id=self.user["id"])
        messagebox.showinfo("Importar CSV", f"Se importaron {n} filas.")
        self.refrescar_todo()

    def exportar_excel(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"productos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )
        if not path:
            return
        n = export_products_xlsx(path)
        messagebox.showinfo("Exportar Excel", f"Se exportaron {n} filas.")

    def importar_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        n = import_products_xlsx(path, upsert=True, user_id=self.user["id"])
        messagebox.showinfo("Importar Excel", f"Se importaron {n} filas.")
        self.refrescar_todo()

    def exportar_pdf(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )
        if not path:
            return
        s = get_settings()
        logo = s.get("logo_path")
        export_inventory_pdf(path, logo_path=logo, title=f"Inventario — {s['company_name']}")
        messagebox.showinfo("PDF", "Inventario exportado.")

    def exportar_pdf_stock_bajo(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"stock_bajo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )
        if not path:
            return
        s = get_settings()
        logo = s.get("logo_path")
        export_low_stock_pdf(path, threshold=UMBRAL_STOCK_BAJO, logo_path=logo, title=f"Stock bajo — {s['company_name']}")
        messagebox.showinfo("PDF", "Stock bajo exportado.")

    def _load_hist(self):
        for r in self.tree_hist.get_children():
            self.tree_hist.delete(r)

    # =========================
    # Movimientos: handlers
    # =========================
    def _line_builder(self, parent, store_list: list, purchase: bool):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        e_cod = ttk.Entry(row, width=18)
        e_cod.pack(side="left", padx=4)
        e_qty = ttk.Entry(row, width=8)
        e_qty.pack(side="left", padx=4)
        e_price = ttk.Entry(row, width=10)
        e_price.pack(side="left", padx=4)
        if purchase:
            ttk.Label(row, text="Código  Cantidad  Costo").pack(side="left", padx=8)
        else:
            ttk.Label(row, text="Código  Cantidad  Precio").pack(side="left", padx=8)
        store_list.append({"e_cod": e_cod, "e_qty": e_qty, "e_price": e_price})

        bar = ttk.Frame(parent)
        bar.pack(fill="x")
        ttk.Button(bar, text="Agregar línea", command=lambda: self._line_builder(parent, store_list, purchase)).pack(
            side="left", padx=(2, 0)
        )

    def _lines_clear(self, store_list):
        for d in store_list:
            for w in d.values():
                if hasattr(w, "delete"):
                    w.delete(0, tk.END)
        store_list[:] = []

    def _lines_parse(self, store_list, purchase: bool):
        out = []
        for d in store_list:
            code = d["e_cod"].get().strip()
            if not code:
                continue
            qty = float(d["e_qty"].get() or 0)
            price = float(d["e_price"].get() or 0)
            if purchase:
                out.append({"codigo": code, "qty": qty, "unit_cost": price, "unit_price": None})
            else:
                out.append({"codigo": code, "qty": qty, "unit_price": price})
        return out

    def _comp_registrar(self):
        items = self._lines_parse(self.comp_lines, purchase=True)
        if not items:
            messagebox.showerror("Compra", "Agrega al menos una línea.")
            return
        numero = self.comp_num.get().strip() or None
        fecha = self.comp_fecha.get().strip() or None
        notas = self.comp_notas.get().strip() or None
        serie = self.comp_serie.get().strip() or "C01"
        prov = self.comp_partner.get().strip() or None
        try:
            doc_id, num = post_purchase(numero, fecha, items, notas, partner_code=prov, series=serie)
            self.last_purchase_doc_id = doc_id
            self.show_success("Compra registrada", f"Compra Nº {num} guardada exitosamente.")
            self.refrescar_todo()
        except Exception as e:
            self.show_error("Error en compra", str(e))

    def _sale_registrar(self):
        items = self._lines_parse(self.sale_lines, purchase=False)
        if not items:
            messagebox.showerror("Venta", "Agrega al menos una línea.")
            return
        numero = self.sale_num.get().strip() or None
        fecha  = self.sale_fecha.get().strip() or None
        notas  = self.sale_notas.get().strip() or None
        serie  = self.sale_serie.get().strip() or "V01"
        cli    = self.sale_partner.get().strip() or None
        try:
            doc_id, num, totals = post_sale(numero, fecha, items, notas, partner_code=cli, series=serie, allow_negative=False)
            self.last_sale_doc_id = doc_id
            msg = f"Venta Nº {num} | Total: ${totals['total']:.2f}"
            self.show_success("Venta registrada", msg)
            self.refrescar_todo()
        except Exception as e:
            self.show_error("Error en venta", str(e))

    def _comp_pdf_last(self):
        if not getattr(self, "last_purchase_doc_id", None):
            messagebox.showinfo("Compra", "Aún no has registrado una compra en esta sesión.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"compra_{self.last_purchase_doc_id}.pdf",
        )
        if not path:
            return
        s = get_settings()
        logo_path = s.get("logo_path")
        try:
            export_purchase_pdf(
                self.last_purchase_doc_id,
                path,
                logo_path=logo_path,
                company_name=s["company_name"],
                company_tax=s["company_tax"],
                company_addr=s["company_addr"],
            )
            messagebox.showinfo("Compra", "PDF generado.")
        except Exception as e:
            messagebox.showerror("Compra", str(e))

    def _sale_pdf_last(self):
        if not getattr(self, "last_sale_doc_id", None):
            messagebox.showinfo("Venta", "Aún no has registrado una venta en esta sesión."); return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")], initialfile=f"venta_{self.last_sale_doc_id}.pdf")
        if not path: return
        logo_path = os.path.join(ASSETS_DIR, LOGO_FILENAME);  logo_path = logo_path if os.path.exists(logo_path) else None
        try:
            # ahora el PDF lee tax_included/tax_rate de settings por defecto
            export_sale_pdf(self.last_sale_doc_id, path, logo_path=logo_path)
            messagebox.showinfo("Venta", "PDF generado.")
        except Exception as e:
            messagebox.showerror("Venta", str(e))

    def _adjust_builder(self, parent, store_list):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        e_cod = ttk.Entry(row, width=18)
        e_cod.pack(side="left", padx=4)
        e_qty = ttk.Entry(row, width=8)
        e_qty.pack(side="left", padx=4)
        e_cost = ttk.Entry(row, width=10)
        e_cost.pack(side="left", padx=4)
        ttk.Label(row, text="Código  Cantidad (+/-)  Costo (solo para entradas)").pack(side="left", padx=8)
        store_list.append({"e_cod": e_cod, "e_qty": e_qty, "e_cost": e_cost})
        bar = ttk.Frame(parent)
        bar.pack(fill="x")
        ttk.Button(bar, text="Agregar línea", command=lambda: self._adjust_builder(parent, store_list)).pack(
            side="left", padx=(2, 0)
        )

    def _adj_clear(self, store_list):
        for d in store_list:
            d["e_cod"].delete(0, tk.END)
            d["e_qty"].delete(0, tk.END)
            d["e_cost"].delete(0, tk.END)
        store_list[:] = []

    def _adj_registrar(self):
        items = []
        for d in self.adj_lines:
            code = d["e_cod"].get().strip()
            if not code:
                continue
            qty = float(d["e_qty"].get() or 0)
            cost = d["e_cost"].get().strip()
            unit_cost = float(cost) if cost else None
            items.append({"codigo": code, "qty": qty, "reason": "Ajuste manual", "unit_cost": unit_cost})
        if not items:
            messagebox.showerror("Ajuste", "Agrega al menos una línea.")
            return
        try:
            post_adjustment(None, items, notas="Ajuste manual")
            self.refrescar_todo()
            messagebox.showinfo("Ajuste", "Ajuste registrado.")
        except Exception as e:
            messagebox.showerror("Ajuste", str(e))

    # =========================
    # Reportes Kardex
    # =========================
    def _kx_autoname(self):
        code = self.kx_cod.get().strip()
        if not code:
            self.kx_name.config(text="—")
            return
        p = get_product(code)
        self.kx_name.config(text=(p[1] if p else "(no existe)"))

    def _kx_generate(self):
        code = self.kx_cod.get().strip()
        if not code:
            messagebox.showerror("Kardex", "Ingresa un código de producto.")
            return
        try:
            rows, summary = kardex_rows(code, self.kx_from.get().strip() or None, self.kx_to.get().strip() or None)
        except Exception as e:
            messagebox.showerror("Kardex", str(e))
            return
        for i in self.kx_tree.get_children():
            self.kx_tree.delete(i)
        for r in rows:
            self.kx_tree.insert(
                "",
                "end",
                values=(
                    r["fecha"],
                    r["doc_no"],
                    r["tipo"],
                    f"{r['qty_in']:.2f}",
                    f"{r['qty_out']:.2f}",
                    f"{r['unit_cost']:.2f}",
                    f"{(r['unit_price'] or 0):.2f}" if r["unit_price"] is not None else "",
                    r["motivo"],
                    f"{r['saldo_qty']:.2f}",
                    f"{r['saldo_cost']:.2f}",
                    f"{r['saldo_total']:.2f}",
                ),
            )
        # Actualizar héroe: count de movimientos
        self.kx_hero_count.config(text=str(len(rows)))
        self.kx_summary.config(
            text=f"Saldo: {summary['saldo_qty']:.2f} u | Costo prom.: {summary['saldo_cost']:.2f} | Valorización: {summary['saldo_total']:.2f}"
        )

    def _kx_export_xlsx(self):
        code = self.kx_cod.get().strip()
        if not code:
            messagebox.showerror("Kardex", "Ingresa un código.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"kardex_{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )
        if not path:
            return
        n = export_kardex_xlsx(path, code, self.kx_from.get().strip() or None, self.kx_to.get().strip() or None)
        messagebox.showinfo("Kardex", f"Exportado a Excel ({n} filas).")

    def _kx_export_pdf(self):
        code = self.kx_cod.get().strip()
        if not code:
            messagebox.showerror("Kardex", "Ingresa un código.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"kardex_{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )
        if not path:
            return
        s = get_settings()
        logo_path = s.get("logo_path")
        n = export_kardex_pdf(
            path,
            code,
            self.kx_from.get().strip() or None,
            self.kx_to.get().strip() or None,
            title=f"Kardex de producto — {s['company_name']}",
            logo_path=logo_path,
        )
        messagebox.showinfo("Kardex", f"Exportado a PDF ({n} filas).")

    # =========================
    # Auditoría: handlers
    # =========================
    def _audit_clear(self):
        self.af_user.delete(0, tk.END)
        self.af_action.delete(0, tk.END)
        self.af_text.delete(0, tk.END)
        self.af_from.delete(0, tk.END)
        self.af_to.delete(0, tk.END)
        self._audit_reload(reset=True)

    def _audit_reload(self, reset=False):
        if reset:
            self.audit_filters["user_q"] = self.af_user.get().strip() or None
            self.audit_filters["action_q"] = self.af_action.get().strip() or None
            self.audit_filters["text_q"] = self.af_text.get().strip() or None
            self.audit_filters["date_from"] = self.af_from.get().strip() or None
            self.audit_filters["date_to"] = self.af_to.get().strip() or None
            self.audit_filters["offset"] = 0
        for i in self.audit_tree.get_children():
            self.audit_tree.delete(i)
        rows, total = self._audit_do_list()
        self._audit_total = total
        for r in rows:
            self.audit_tree.insert("", "end", values=r)
        start = 0 if total == 0 else (self.audit_filters["offset"] + 1)
        end = min(self.audit_filters["offset"] + len(rows), total)
        self.audit_lbl.config(text=f"Mostrando {start}–{end} de {total}")

    def _audit_jump(self, where: str):
        limit = self.audit_filters["limit"]
        offset = self.audit_filters["offset"]
        total = self._audit_total
        if where == "first":
            offset = 0
        elif where == "prev":
            offset = max(0, offset - limit)
        elif where == "next":
            offset = min(max(0, total - 1), offset + limit)
        elif where == "last":
            offset = max(0, (total // limit) * limit)
        self.audit_filters["offset"] = offset
        self._audit_reload(reset=False)

    # =========================
    # Menús: backup/restore/logout/password
    # =========================
    def _menu_backup(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("Todos", "*.*")],
            initialfile=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
        )
        if not path:
            return
        try:
            from config import settings as _settings
            import shutil

            shutil.copyfile(str(_settings.DB_PATH), path)
            messagebox.showinfo("Backup", "Copia de seguridad creada.")
        except Exception as e:
            messagebox.showerror("Backup", str(e))

    def _menu_restore(self):
        if not messagebox.askyesno("Restaurar", "Esto reemplazará la base actual. ¿Continuar?"):
            return
        path = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db"), ("Todos", "*.*")])
        if not path:
            return
        try:
            from config import settings as _settings
            import shutil

            shutil.copyfile(path, str(_settings.DB_PATH))
            messagebox.showinfo("Restaurar", "Base de datos restaurada. Reinicia la aplicación.")
        except Exception as e:
            messagebox.showerror("Restaurar", str(e))

    def _menu_logout(self):
        self.root.destroy()

    def _menu_change_password(self):
        dlg = ChangePasswordDialog(self.root)
        if not dlg.result:
            return
        old, new1, new2 = dlg.result
        if new1 != new2:
            messagebox.showerror("Cambiar contraseña", "La nueva contraseña no coincide.")
            return
        try:
            from src.core.auth import change_password

            change_password(self.user["id"], old, new1)
            log_event(self.user["id"], "USER_CHANGE_PASSWORD", {})
            messagebox.showinfo("Cambiar contraseña", "Contraseña actualizada.")
        except Exception as e:
            messagebox.showerror("Cambiar contraseña", str(e))

    # =========================
    # Pestaña Usuarios: actions
    # =========================
    def _sync_selected_user_roles(self):
        """Marca en la lista los roles del usuario seleccionado."""
        sel = self.users_tree.selection()
        if not sel:
            return
        uid = self.users_tree.item(sel[0])["values"][0]
        # Cargar roles actuales del usuario de la tabla
        # (roles vienen como texto en la columna 5)
        roles_text = self.users_tree.item(sel[0])["values"][4] or ""
        user_roles = [r.strip() for r in roles_text.split(",") if r.strip()]
        # Limpiar selección
        self.roles_list.selection_clear(0, tk.END)
        # Marcar los que correspondan
        for i in range(self.roles_list.size()):
            rname = self.roles_list.get(i)
            if rname in user_roles:
                self.roles_list.selection_set(i)

    def _user_create(self):
        username = (self.u_username.get() or "").strip()
        name = (self.u_name.get() or "").strip()
        if not username or not name:
            messagebox.showerror("Usuarios", "Usuario y Nombre son obligatorios.")
            return
        try:
            new_id, temp_pass = create_user(username, name)
            messagebox.showinfo(
                "Usuarios",
                f"Usuario creado (ID {new_id}). Contraseña temporal:\n\n{temp_pass}\n\nPídale que la cambie en su primer ingreso.",
            )
            self._users_reload()
        except Exception as e:
            messagebox.showerror("Usuarios", str(e))

    def _user_active(self, active: bool):
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showinfo("Usuarios", "Selecciona un usuario.")
            return
        uid = self.users_tree.item(sel[0])["values"][0]
        try:
            set_user_active(uid, active)
            self._users_reload()
        except Exception as e:
            messagebox.showerror("Usuarios", str(e))

    def _user_reset_pwd(self):
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showinfo("Usuarios", "Selecciona un usuario.")
            return
        uid = self.users_tree.item(sel[0])["values"][0]
        try:
            new_pass = reset_password(uid)
            messagebox.showinfo("Usuarios", f"Contraseña temporal:\n\n{new_pass}")
            self._users_reload()
        except Exception as e:
            messagebox.showerror("Usuarios", str(e))

    def _user_save_roles(self):
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showinfo("Usuarios", "Selecciona un usuario.")
            return
        uid = self.users_tree.item(sel[0])["values"][0]
        picks = [self.roles_list.get(i) for i in self.roles_list.curselection()]
        try:
            set_user_roles(uid, picks)
            self._users_reload()
        except Exception as e:
            messagebox.showerror("Usuarios", str(e))

    # =========================
    # Parámetros: handlers
    # =========================
    def _st_pick_logo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("Todos", "*.*")]
        )
        if path:
            self.st_logo.delete(0, tk.END)
            self.st_logo.insert(0, path)

    def _st_save(self):
        try:
            tax_rate = float(self.st_tax_rate.get() or 0.0)
            update_settings(
                company_name=self.st_name.get().strip() or "Mi Empresa",
                company_tax=self.st_tax.get().strip() or "NIT/RUC",
                company_addr=self.st_addr.get().strip() or "Dirección",
                logo_path=(self.st_logo.get().strip() or None),
                tax_included=1 if self.st_tax_included.get() else 0,
                tax_rate=tax_rate,
            )
            self.show_success("Parámetros actualizados", "Los cambios se han guardado exitosamente.")
        except Exception as e:
            self.show_error("Error al guardar", str(e))

    def _st_reload(self):
        s = get_settings()
        self.st_name.delete(0, tk.END)
        self.st_name.insert(0, s["company_name"])
        self.st_tax.delete(0, tk.END)
        self.st_tax.insert(0, s["company_tax"])
        self.st_addr.delete(0, tk.END)
        self.st_addr.insert(0, s["company_addr"])
        self.st_logo.delete(0, tk.END)
        if s.get("logo_path"):
            self.st_logo.insert(0, s["logo_path"])
        self.st_tax_included.set(bool(s["tax_included"]))
        self.st_tax_rate.delete(0, tk.END)
        self.st_tax_rate.insert(0, str(s["tax_rate"]))

    # ============================================
    # NUEVAS PESTAÑAS: Devoluciones, Descuentos, Márgenes, Reportes Avanzados
    # ============================================

    def _build_tab_devoluciones(self, parent: ttk.Frame):
        """La pestaña sólo abre la ventana independiente de devoluciones."""
        frame_main = tk.Frame(parent, bg=Luxury2026Colors.BG_DARKEST)
        frame_main.pack(fill="both", expand=True, padx=6, pady=6)

        tk.Label(frame_main, text="💔 Devoluciones", font=ModernTypography.font_heading(),
                 bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(12, 0))

        tk.Button(frame_main, text="Abrir ventana de devoluciones", font=ModernTypography.font_body_bold(),
                 bg=Luxury2026Colors.PRIMARY, fg="white",
                 command=self._open_returns_window,
                 relief="flat", bd=0, padx=12, pady=8).pack(anchor="w", padx=12, pady=24)

    def _build_tab_descuentos(self, parent: ttk.Frame):
        """Pestaña para aplicar descuentos a documentos"""
        frame_main = tk.Frame(parent, bg=Luxury2026Colors.BG_DARKEST)
        frame_main.pack(fill="both", expand=True, padx=6, pady=6)

        tk.Label(frame_main, text="💰 Sistema de Descuentos", font=ModernTypography.font_heading(),
                bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(12, 0))

        entry_frame = tk.Frame(frame_main, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        entry_frame.pack(fill="x", padx=12, pady=(12, 12))

        tk.Label(entry_frame, text="ID de Documento", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(8, 4))
        entry_doc_id = tk.Entry(entry_frame, width=40, font=ModernTypography.font_body(),
                               bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                               insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        entry_doc_id.pack(anchor="w", padx=12, fill="x", pady=(0, 12))

        tk.Label(entry_frame, text="Porcentaje (%)", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(0, 4))
        entry_pct = tk.Entry(entry_frame, width=40, font=ModernTypography.font_body(),
                            bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                            insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        entry_pct.pack(anchor="w", padx=12, fill="x", pady=(0, 12))

        tk.Label(entry_frame, text="Razón", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(0, 4))
        text_razon = tk.Text(entry_frame, height=3, font=ModernTypography.font_body(),
                            bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                            insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        text_razon.pack(anchor="w", padx=12, fill="x", pady=(0, 12))

        def aplicar_desc():
            try:
                doc_id = entry_doc_id.get().strip()
                pct = float(entry_pct.get())
                razon = text_razon.get("1.0", "end").strip()

                if not doc_id or pct <= 0 or pct > 100:
                    messagebox.showerror("Validación", "Verifica datos (0-100%)")
                    return

                from src.services.inventory import apply_discount
                apply_discount(doc_id, pct, razon)
                messagebox.showinfo("Éxito", f"Descuento {pct}% aplicado")
                entry_doc_id.delete(0, tk.END)
                entry_pct.delete(0, tk.END)
                text_razon.delete("1.0", tk.END)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = tk.Frame(frame_main, bg=Luxury2026Colors.BG_DARKEST)
        btn_frame.pack(fill="x", padx=12, pady=12)

        tk.Button(btn_frame, text="✓ Aplicar Descuento", font=ModernTypography.font_body_bold(),
                 bg=Luxury2026Colors.PRIMARY, fg="white", command=aplicar_desc,
                 relief="flat", bd=0, padx=12, pady=8).pack(side="left", padx=(0, 8))

    def _build_tab_margenes(self, parent: ttk.Frame):
        """Pestaña para analizar márgenes de rentabilidad"""
        frame_main = tk.Frame(parent, bg=Luxury2026Colors.BG_DARKEST)
        frame_main.pack(fill="both", expand=True, padx=6, pady=6)

        tk.Label(frame_main, text="📈 Análisis de Márgenes", font=ModernTypography.font_heading(),
                bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(12, 0))

        input_frame = tk.Frame(frame_main, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        input_frame.pack(fill="x", padx=12, pady=(12, 12))

        tk.Label(input_frame, text="Código del Producto", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(8, 4))
        entry_prod = tk.Entry(input_frame, width=40, font=ModernTypography.font_body(),
                             bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                             insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        entry_prod.pack(anchor="w", padx=12, fill="x", pady=(0, 12))

        def calcular_margen():
            try:
                codigo = entry_prod.get().strip()
                if not codigo:
                    messagebox.showerror("Validación", "Ingresa código")
                    return

                from src.services.inventory import calculate_cogs
                from src.database.connection import get_connection
                # Obtener el último documento de tipo SALE para ese producto
                doc_id = None
                with get_connection() as _conn:
                    _cur = _conn.cursor()
                    _cur.execute(
                        """SELECT d.id FROM documents d
                           JOIN document_lines l ON l.doc_id = d.id
                           WHERE d.tipo = 'SALE' AND l.codigo = ?
                           ORDER BY d.fecha DESC LIMIT 1""",
                        (codigo,)
                    )
                    _row = _cur.fetchone()
                    if _row:
                        doc_id = _row[0]
                if doc_id is None:
                    messagebox.showwarning("Márgen", f"No hay ventas registradas para el producto '{codigo}'.")
                    return
                margen = calculate_cogs(doc_id)
                result_text.configure(state="normal")
                result_text.delete("1.0", tk.END)
                result_text.insert("1.0", f"Margen calculado:\n{str(margen)}")
                result_text.configure(state="disabled")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = tk.Frame(frame_main, bg=Luxury2026Colors.BG_DARKEST)
        btn_frame.pack(fill="x", padx=12, pady=12)

        tk.Button(btn_frame, text="✓ Calcular Margen", font=ModernTypography.font_body_bold(),
                 bg=Luxury2026Colors.PRIMARY, fg="white", command=calcular_margen,
                 relief="flat", bd=0, padx=12, pady=8).pack(side="left", padx=(0, 8))

        result_frame = tk.Frame(frame_main, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        result_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        tk.Label(result_frame, text="Resultado", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(8, 4))

        result_text = tk.Text(result_frame, height=10, font=("Courier", 9),
                             bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_SECONDARY,
                             relief="solid", bd=1, state="disabled")
        result_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _build_tab_reportes_avanzados(self, parent: ttk.Frame):
        """Pestaña para reportes avanzados de análisis"""
        frame_main = tk.Frame(parent, bg=Luxury2026Colors.BG_DARKEST)
        frame_main.pack(fill="both", expand=True, padx=6, pady=6)

        tk.Label(frame_main, text="🎯 Reportes Avanzados", font=ModernTypography.font_heading(),
                bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(12, 0))

        input_frame = tk.Frame(frame_main, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        input_frame.pack(fill="x", padx=12, pady=(12, 12))

        tk.Label(input_frame, text="Tipo de Análisis", font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(8, 4))

        analysis_var = tk.StringVar(value="abc")
        ttk.Combobox(input_frame, textvariable=analysis_var,
                    values=["abc", "rotacion", "ventas_periodo"],
                    state="readonly", width=37).pack(anchor="w", padx=12, fill="x", pady=(0, 12))

        def ejecutar_reporte():
            try:
                tipo = analysis_var.get()
                from src.services.reports import report_abc_analysis, report_inventory_rotation, report_sales_by_period
                
                if tipo == "abc":
                    resultado = report_abc_analysis()
                elif tipo == "rotacion":
                    resultado = report_inventory_rotation()
                else:
                    resultado = report_sales_by_period("2024-01-01", "2024-12-31")

                output_text.configure(state="normal")
                output_text.delete("1.0", tk.END)
                output_text.insert("1.0", str(resultado))
                output_text.configure(state="disabled")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = tk.Frame(frame_main, bg=Luxury2026Colors.BG_DARKEST)
        btn_frame.pack(fill="x", padx=12, pady=12)

        tk.Button(btn_frame, text="✓ Ejecutar Reporte", font=ModernTypography.font_body_bold(),
                 bg=Luxury2026Colors.PRIMARY, fg="white", command=ejecutar_reporte,
                 relief="flat", bd=0, padx=12, pady=8).pack(side="left", padx=(0, 8))

        output_frame = tk.Frame(frame_main, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        output_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        tk.Label(output_frame, text="📊 Resultado", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(8, 4))

        output_text = tk.Text(output_frame, height=14, font=("Courier", 9),
                             bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_SECONDARY,
                             relief="solid", bd=1, state="disabled")
        output_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    # =========================
    # POS Integration
    # =========================
    def _open_pos_window(self):
        from src.pos.pos_window import POSWindow
        try:
            pos_window = POSWindow(self.root, self.user)
            # Refrescar DB al cerrar caja para ver movimientos en backend stock
            self.root.wait_window(pos_window)
            self.refrescar_todo()
        except Exception as e:
            messagebox.showerror("POS Error", str(e))

    def _open_returns_window(self):
        """Abre la ventana de devoluciones con wait_window e incluye traceback."""
        import traceback
        try:
            from src.app.returns_window import ReturnsWindow
            ret_window = ReturnsWindow(self.root, self.user)
            # Esperar a que se cierre la ventana
            self.root.wait_window(ret_window)
            # Refrescar stock al cerrar devolución
            self.refrescar_todo()
        except Exception as e:
            import sys
            traceback.print_exc(file=sys.stdout)  # Mostrar error en consola
            messagebox.showerror("Error en Devoluciones", f"No se pudo abrir la ventana:\n{e}\n\nVer consola para detalles completos.")

    def _open_crm_window(self):
        """Abre la ventana CRM de clientes con manejo de errores e imprime traceback."""
        import traceback
        try:
            from src.app.crm_window import CrmWindow
            win = CrmWindow(self.root, self.user)
            self.root.wait_window(win)
        except Exception as e:
            import sys
            traceback.print_exc(file=sys.stdout)
            messagebox.showerror("Error en CRM", f"No se pudo abrir la ventana:\n{e}\n\nVer consola para detalles completos.")

    def _open_suppliers_window(self):
        """Abre la ventana de gestión de proveedores con manejo de errores e imprime traceback."""
        import traceback
        try:
            from src.app.suppliers_window import SuppliersWindow
            win = SuppliersWindow(self.root, self.user)
            self.root.wait_window(win)
        except Exception as e:
            import sys
            traceback.print_exc(file=sys.stdout)
            messagebox.showerror("Error en Proveedores", f"No se pudo abrir la ventana:\n{e}\n\nVer consola para detalles completos.")

    def _open_purchase_orders_window(self):
        """Abre la ventana de órdenes de compra con manejo de errores e imprime traceback."""
        import traceback
        try:
            from src.app.purchase_orders_window import PurchaseOrdersWindow
            win = PurchaseOrdersWindow(self.root, self.user)
            self.root.wait_window(win)
        except Exception as e:
            import sys
            traceback.print_exc(file=sys.stdout)
            messagebox.showerror("Error en Órdenes de Compra", f"No se pudo abrir la ventana:\n{e}\n\nVer consola para detalles completos.")

    def _open_reports_window(self):
        import traceback
        try:
            from src.app.reports_window import ReportsWindow
            win = ReportsWindow(self.root, self.user)
            self.root.wait_window(win)
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"No se pudo abrir reportes:\n{e}")

    def _open_cash_manager_window(self):
        import traceback
        try:
            from src.app.cash_manager_window import CashManagerWindow
            win = CashManagerWindow(self.root, self.user)
            self.root.wait_window(win)
        except Exception as e:
            import sys
            traceback.print_exc(file=sys.stdout)
            messagebox.showerror("Error en Caja", f"No se pudo abrir la ventana:\n{e}\n\nVer consola para detalles completos.")

    def _open_finanzas_window(self):
        try:
            from src.app.finanzas_window import FinanzasWindow
            FinanzasWindow(self.root)
        except Exception as e:
            logging.warning("_open_finanzas_window error: %s", e)
            messagebox.showerror("Finanzas", str(e))

    def _open_notif_config_window(self):
        try:
            from src.app.notif_config_window import NotifConfigWindow
            NotifConfigWindow(self.root)
        except Exception as e:
            logging.warning("_open_notif_config_window error: %s", e)
            messagebox.showerror("Notificaciones", str(e))

    def _open_auto_reorder_window(self):
        """Abre la ventana para procesar el auto-reorder de inventario."""
        try:
            from src.services.auto_reorder import get_productos_bajo_reorder, ejecutar_reorder_automatico
            
            dlg = tk.Toplevel(self.root)
            dlg.title("Auto-Reorder (Stock Mínimo)")
            dlg.geometry("700x600")
            dlg.resizable(False, False)
            dlg.configure(bg=Luxury2026Colors.BG_DARKEST)
            dlg.transient(self.root)
            dlg.grab_set()

            # Heading
            tk.Label(
                dlg, text="📉 Productos bajo Stock Mínimo",
                font=ModernTypography.font_heading(),
                bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.PRIMARY
            ).pack(pady=(20, 10))
            
            # Tabla
            columns = ("codigo", "nombre", "stock", "min", "reorder")
            tv = ttk.Treeview(dlg, columns=columns, show="headings", height=12)
            tv.heading("codigo", text="Código")
            tv.heading("nombre", text="Producto")
            tv.heading("stock", text="Stock")
            tv.heading("min", text="Mínimo")
            tv.heading("reorder", text="A Pedir")
            
            tv.column("codigo", width=100, anchor="center")
            tv.column("nombre", width=250, anchor="w")
            tv.column("stock", width=80, anchor="center")
            tv.column("min", width=80, anchor="center")
            tv.column("reorder", width=80, anchor="center")
            tv.pack(fill="x", padx=30, pady=10)

            # Cargar datos
            bajo_stock = get_productos_bajo_reorder()
            for p in bajo_stock:
                tv.insert("", "end", values=(
                    p["codigo"], p["nombre"],
                    p["cantidad"], p["stock_minimo"], p["reorder_qty"]
                ))
            
            if not bajo_stock:
                # Si no hay nada, mostrar info visual
                tk.Label(
                    dlg, text="✅ Todos los productos tienen buen nivel de stock.",
                    font=ModernTypography.font_body(12, True),
                    bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.TEXT_SECONDARY
                ).pack(pady=20)
            
            def accionar_reorder():
                res = ejecutar_reorder_automatico()
                msg = f"✅ Órdenes generadas automáticamente: {res['total_creadas']}\n"
                
                if res['sin_proveedor']:
                    msg += f"\n⚠️ {len(res['sin_proveedor'])} productos omitidos por no tener proveedor_id."
                
                from tkinter import messagebox
                messagebox.showinfo("Resultado Auto-Reorder", msg, parent=dlg)
                dlg.destroy()

            btn_frame = tk.Frame(dlg, bg=Luxury2026Colors.BG_DARKEST)
            btn_frame.pack(pady=20)
            btn_frame.columnconfigure(0, weight=1)
            btn_frame.columnconfigure(1, weight=1)

            btn_exec = ttk.Button(
                btn_frame, text="✅ Crear OCs Automáticamente",
                command=accionar_reorder,
                style="Luxury.Primary.TButton",
                state="normal" if bajo_stock else "disabled"
            )
            btn_exec.grid(row=0, column=0, padx=10)

            ttk.Button(
                btn_frame, text="Cancelar", command=dlg.destroy, style="Luxury.Secondary.TButton"
            ).grid(row=0, column=1, padx=10)
            
        except Exception as e:
            import logging
            from tkinter import messagebox
            logging.error(f"Error al abrir auto-reorder: {e}")
            messagebox.showerror("Error", str(e), parent=self.root)

# =========================
# Diálogo producto (crear/editar) - ENAMORANTE 2026
# =========================
class ProductoDialog(tk.Toplevel):
    def __init__(self, master, initial: Optional[dict] = None, editable_code: bool = True, title: str = "Producto"):
        super().__init__(master)
        self.title(title)
        self.result = None
        self.resizable(False, False)
        # Estilo Luxury 2026
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        
        init = initial or {}
        
        # CONTENEDOR PRINCIPAL
        main_frame = tk.Frame(self, bg=Luxury2026Colors.BG_DARKEST)
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        # ENCABEZADO
        title_lbl = tk.Label(
            main_frame,
            text=title,
            font=ModernTypography.font_heading_lg(),
            bg=Luxury2026Colors.BG_DARKEST,
            fg=Luxury2026Colors.TEXT_PRIMARY
        )
        title_lbl.pack(anchor="w", pady=(0, 20))
        
        # GRUPO 1: Identificación
        grp1 = tk.Frame(main_frame, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        grp1.pack(fill="x", pady=(0, 16))
        tk.Label(grp1, text="📋 Identificación", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY).pack(anchor="w", padx=12, pady=(8, 0))
        
        # Código
        self._build_field(grp1, "Código", "e_cod", 22, init.get("codigo", ""), 
                         disabled=not editable_code)
        # Nombre
        self._build_field(grp1, "Nombre", "e_nom", 40, init.get("nombre", ""))
        
        # GRUPO 2: Clasificación
        grp2 = tk.Frame(main_frame, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        grp2.pack(fill="x", pady=(0, 16))
        tk.Label(grp2, text="🏷️  Clasificación", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT).pack(anchor="w", padx=12, pady=(8, 0))
        # Categoría
        self._build_field(grp2, "Categoría", "e_cat", 28, init.get("categoria", ""))
        
        # GRUPO 3: Valores
        grp3 = tk.Frame(main_frame, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        grp3.pack(fill="x", pady=(0, 16))
        tk.Label(grp3, text="💰 Valores y Stock", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.SUCCESS).pack(anchor="w", padx=12, pady=(8, 0))
        
        # Contenedor para precio, costo promedio, cantidad
        vals_frame = tk.Frame(grp3, bg=Luxury2026Colors.BG_SECONDARY)
        vals_frame.pack(fill="x", padx=12, pady=(8, 12))
        
        # Precio
        lbl_pre = tk.Label(vals_frame, text="Precio de Venta", font=ModernTypography.font_body_small(),
                          bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY)
        lbl_pre.grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.e_pre = tk.Entry(vals_frame, width=14, font=ModernTypography.font_body(),
                             bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                             insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.e_pre.grid(row=1, column=0, sticky="we", padx=(0, 6))
        if init.get("precio"):
            self.e_pre.insert(0, str(init.get("precio", "")))
        
        # Costo Promedio
        lbl_avg = tk.Label(vals_frame, text="Costo Promedio (vacío = usar precio)", font=ModernTypography.font_body_small(),
                          bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY)
        lbl_avg.grid(row=0, column=1, sticky="w", pady=(0, 4))
        self.e_avg = tk.Entry(vals_frame, width=14, font=ModernTypography.font_body(),
                             bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                             insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.e_avg.grid(row=1, column=1, sticky="we", padx=(0, 6))
        if init.get("avg_cost"):
            self.e_avg.insert(0, str(init.get("avg_cost", "")))
        
        # Cantidad (Stock Inicial)
        lbl_can = tk.Label(vals_frame, text="Stock Inicial", font=ModernTypography.font_body_small(),
                          bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY)
        lbl_can.grid(row=0, column=2, sticky="w", pady=(0, 4))
        self.e_can = tk.Entry(vals_frame, width=14, font=ModernTypography.font_body(),
                             bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                             insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.e_can.grid(row=1, column=2, sticky="we")
        if init.get("cantidad"):
            self.e_can.insert(0, str(init.get("cantidad", "")))
        
        vals_frame.grid_columnconfigure(0, weight=1)
        vals_frame.grid_columnconfigure(1, weight=1)
        vals_frame.grid_columnconfigure(2, weight=1)
        
        # GRUPO 4: Almacén
        grp4 = tk.Frame(main_frame, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        grp4.pack(fill="x", pady=(0, 20))
        tk.Label(grp4, text="🏭 Almacén", font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.WARNING).pack(anchor="w", padx=12, pady=(8, 0))
        
        # Combo de almacenes
        from src.services.warehouses import list_warehouses
        warehouses = list_warehouses()
        warehouse_options = [""] + [f"{w['id']} - {w['name']}" for w in warehouses]
        
        lbl_wh = tk.Label(grp4, text="Almacén", font=ModernTypography.font_body_small(),
                         bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY)
        lbl_wh.pack(anchor="w", padx=12, pady=(8, 4))
        self.combo_wh = ttk.Combobox(grp4, values=warehouse_options, state="readonly", width=30)
        self.combo_wh.pack(anchor="w", padx=12, pady=(0, 12))
        # Seleccionar por defecto el primero si hay
        if warehouse_options:
            self.combo_wh.current(0)
        # Si hay initial warehouse_id, seleccionar
        if init.get("warehouse_id"):
            for i, opt in enumerate(warehouse_options):
                if opt.startswith(str(init.get("warehouse_id"))):
                    self.combo_wh.current(i)
                    break
        
        # BOTONES
        btn_frame = tk.Frame(main_frame, bg=Luxury2026Colors.BG_DARKEST)
        btn_frame.pack(fill="x", pady=(8, 0))
        
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text="✨ Guardar", command=self._ok).pack(side="right")
        
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.transient(master)
        self.grab_set()
        self.wait_window(self)

    def _build_field(self, parent, label, attr_name, width, value="", disabled=False):
        """Helper para construir campos uniformes

        Normalize `attr_name` so callers can pass either "e_cod" or "self.e_cod".
        """
        lbl = tk.Label(parent, text=label, font=ModernTypography.font_body_small(),
                      bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_SECONDARY)
        lbl.pack(anchor="w", padx=12, pady=(8, 4))
        
        entry = tk.Entry(parent, width=width, font=ModernTypography.font_body(),
                        bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                        insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        entry.pack(anchor="w", padx=12, fill="x")
        
        if value:
            entry.insert(0, str(value))
        if disabled:
            entry.configure(state="disabled")
        # strip any leading "self."
        attr = attr_name.split('.')[-1]
        setattr(self, attr, entry)

    def _ok(self):
        try:
            # Parse warehouse_id from combo
            wh_text = self.combo_wh.get()
            warehouse_id = None
            if wh_text and wh_text.strip():
                try:
                    warehouse_id = int(wh_text.split(" - ")[0])
                except:
                    pass
            
            precio = float(self.e_pre.get() or 0.0)
            avg_cost_raw = self.e_avg.get().strip()
            # FIX: si avg_cost vacío, usar precio como fallback para que el dashboard muestre valor real
            avg_cost = float(avg_cost_raw) if avg_cost_raw else precio

            data = {
                "codigo": (self.e_cod.get() or "").strip(),
                "nombre": (self.e_nom.get() or "").strip(),
                "categoria": (self.e_cat.get() or "").strip(),
                "precio": precio,
                "avg_cost": avg_cost,
                "cantidad": int(float(self.e_can.get() or 0)),
                "warehouse_id": warehouse_id,
            }
            if not data["codigo"] or not data["nombre"]:
                raise ValueError("Código y Nombre son obligatorios.")
            if data["precio"] < 0:
                raise ValueError("El precio no puede ser negativo.")
            if data["avg_cost"] < 0:
                raise ValueError("El costo promedio no puede ser negativo.")
            if data["cantidad"] < 0:
                raise ValueError("La cantidad no puede ser negativa.")
            self.result = data
            self.destroy()
        except Exception as e:
            messagebox.showerror("Validación", str(e))