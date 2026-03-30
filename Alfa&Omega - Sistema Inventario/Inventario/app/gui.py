# app/gui.py
import os
import tkinter as tk
from typing import Optional
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from diseño import estilo, scrollbars

# Audit / Auth
from core.audit import log_event, list_audit
from core.auth import ensure_defaults, has_perm
from core.auth import LoginDialog, ChangePasswordDialog
from core.auth import (
    list_users, list_roles, create_user,
    set_user_active, reset_password, set_user_roles
)

# Servicios del inventario y movimientos
from core.services import (
    add_product, update_product, delete_product, get_product,
    list_products_page, count_products, stock_global_sum, low_stock_count,
    export_products_csv, import_products_csv, export_products_xlsx, import_products_xlsx,
    export_inventory_pdf, export_low_stock_pdf,
    post_purchase, post_sale, post_adjustment
)

# Reportes
from core.reports import kardex_rows, export_kardex_xlsx, export_kardex_pdf

# Documentos comerciales (PDF comprobantes)
from core.documents import export_purchase_pdf, export_sale_pdf
from core.documents import ensure_schema as ensure_doc_series, seed_default_series

# Partners (clientes/proveedores)
from core.partners import ensure_schema as ensure_partners_schema

# Parámetros (company_settings)
from core.settings import get_settings, update_settings

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
        bg = getattr(estilo, "COLOR_FONDO", "#F6F8FA")
        self.root.configure(bg=bg)

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
        frame_logo = ttk.Frame(self.root)
        frame_logo.pack(pady=8, fill="x")
        if self.logo:
            self.root.iconphoto(False, self.logo)
            ttk.Label(
                frame_logo,
                image=self.logo,
                text="  Alfa & Omega Inventario",
                compound="left",
                font=("Helvetica", 16, "bold"),
            ).pack()
        else:
            ttk.Label(frame_logo, text="Alfa & Omega Inventario", font=("Helvetica", 16, "bold")).pack()

        # ===== Notebook principal =====
        self.nb_main = ttk.Notebook(self.root)
        self.nb_main.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        # Tab Inventario
        self.tab_inv = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_inv, text="Inventario")
        self._build_tab_inventario(self.tab_inv)

        # Tab Movimientos
        self.tab_mov = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_mov, text="Movimientos")
        self._build_tab_movimientos(self.tab_mov)

        # Tab Historial (altas/mods/imports)
        self.tab_hist = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_hist, text="Historial")
        self._build_tab_hist(self.tab_hist)

        # Tab Reportes (Kardex)
        self.tab_reports = ttk.Frame(self.nb_main)
        self.nb_main.add(self.tab_reports, text="Reportes")
        self._build_tab_reportes(self.tab_reports)

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

            # Pestaña Par�metros (company_settings)
            self.tab_settings = ttk.Frame(self.nb_main)
            self.nb_main.add(self.tab_settings, text="Parámetros")
            self._build_tab_settings(self.tab_settings)

        # Atajos
        self.root.bind("<Return>", lambda e: self.buscar_producto())
        self.root.bind("<F5>", lambda e: self.refrescar_todo())
        self.root.bind("<Delete>", lambda e: self.eliminar_producto())
        self.root.bind("<F2>", lambda e: self.editar_producto())
        self.root.bind("<Control-e>", lambda e: self.editar_producto())
        self.root.bind("<Control-n>", lambda e: self.nuevo_producto())

        # Carga inicial
        self.refrescar_todo()

    # =========================
    # Construcción de pestañas
    # =========================
    def _build_tab_inventario(self, parent: ttk.Frame):
        # Estadísticas
        frame_stats = ttk.LabelFrame(parent, text="Estadísticas (global)")
        frame_stats.pack(fill="x", padx=2, pady=4)
        self.lbl_total_productos = ttk.Label(frame_stats, text="Total de productos: 0", font=("Helvetica", 10, "bold"))
        self.lbl_total_stock = ttk.Label(frame_stats, text="Stock total: 0", font=("Helvetica", 10, "bold"))
        self.lbl_stock_bajo = ttk.Label(
            frame_stats, text=f"Stock bajo (≤ {UMBRAL_STOCK_BAJO}): 0", font=("Helvetica", 10, "bold")
        )
        self.lbl_total_productos.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.lbl_total_stock.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.lbl_stock_bajo.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        for i in range(3):
            frame_stats.grid_columnconfigure(i, weight=1)

        # Buscar
        frame_search = ttk.LabelFrame(parent, text="Buscar Producto")
        frame_search.pack(fill="x", padx=2, pady=4)
        ttk.Label(frame_search, text="Buscar por:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.combo_filtro = ttk.Combobox(frame_search, values=["Código", "Nombre", "Categoría"], state="readonly")
        self.combo_filtro.current(0)
        self.combo_filtro.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        self.entry_buscar = ttk.Entry(frame_search)
        self.entry_buscar.grid(row=0, column=2, padx=5, pady=5, sticky="we")
        ttk.Button(frame_search, text="Buscar", command=self.buscar_producto).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(frame_search, text="Limpiar", command=self.limpiar_busqueda).grid(row=0, column=4, padx=5, pady=5)
        for i in (1, 2):
            frame_search.grid_columnconfigure(i, weight=1)

        # Tabla
        frame_list = ttk.LabelFrame(parent, text="Productos")
        frame_list.pack(fill="both", expand=True, padx=2, pady=4)
        columns = ("codigo", "nombre", "categoria", "precio", "cantidad")
        self.tree = ttk.Treeview(frame_list, columns=columns, show="headings")
        for c in columns:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("codigo", width=140, anchor="w", stretch=True)
        self.tree.column("nombre", width=260, anchor="w", stretch=True)
        self.tree.column("categoria", width=170, anchor="w", stretch=True)
        self.tree.column("precio", width=100, anchor="e", stretch=False)
        self.tree.column("cantidad", width=100, anchor="center", stretch=False)
        self.tree.pack(fill="both", expand=True)
        estilo.aplicar_estilo_treeview(self.tree)
        scrollbars.agregar_scrollbar(self.tree, frame_list)
        self.tree.bind("<Double-1>", lambda e: self.editar_producto())

        # Acciones
        actions = ttk.Frame(parent)
        actions.pack(fill="x", pady=(6, 0))
        ttk.Button(actions, text="Nuevo…", command=self.nuevo_producto).pack(side="left")
        ttk.Button(actions, text="Editar", command=self.editar_producto).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="Eliminar", command=self.eliminar_producto).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="Exportar CSV…", command=self.exportar_csv).pack(side="right", padx=(0, 6))
        ttk.Button(actions, text="Importar CSV…", command=self.importar_csv).pack(side="right", padx=(0, 6))
        ttk.Button(actions, text="Exportar Excel…", command=self.exportar_excel).pack(side="right", padx=(0, 6))
        ttk.Button(actions, text="Importar Excel…", command=self.importar_excel).pack(side="right", padx=(0, 6))
        ttk.Button(actions, text="Exportar PDF…", command=self.exportar_pdf).pack(side="right", padx=(0, 6))
        ttk.Button(actions, text="Stock bajo PDF…", command=self.exportar_pdf_stock_bajo).pack(side="right")

        # Paginación
        frame_pager = ttk.Frame(parent)
        frame_pager.pack(fill="x", pady=(6, 4))
        ttk.Button(frame_pager, text="<<", width=3, command=self.first_page).pack(side="left")
        ttk.Button(frame_pager, text="<", width=3, command=self.prev_page).pack(side="left", padx=(4, 0))
        ttk.Button(frame_pager, text=">", width=3, command=self.next_page).pack(side="left", padx=(4, 0))
        ttk.Button(frame_pager, text=">>", width=3, command=self.last_page).pack(side="left", padx=(4, 8))
        ttk.Label(frame_pager, text="Por página:").pack(side="left")
        self.combo_page_size = ttk.Combobox(frame_pager, values=PAGE_SIZE_OPTIONS, width=5, state="readonly")
        self.combo_page_size.set(DEFAULT_PAGE_SIZE)
        self.combo_page_size.pack(side="left", padx=(4, 8))
        self.combo_page_size.bind("<<ComboboxSelected>>", lambda e: self.change_page_size())
        self.lbl_range = ttk.Label(frame_pager, text="Mostrando 0–0 de 0 (pág. 0)")
        self.lbl_range.pack(side="left", padx=8)

    def _build_tab_movimientos(self, parent: ttk.Frame):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        # ---- Compras ----
        tab_c = ttk.Frame(nb)
        nb.add(tab_c, text="Compras")
        form = ttk.LabelFrame(tab_c, text="Cabecera")
        form.pack(fill="x", padx=6, pady=6)
        ttk.Label(form, text="Nº Doc:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.comp_num = ttk.Entry(form, width=14)
        self.comp_num.grid(row=0, column=1, sticky="w")
        ttk.Label(form, text="Fecha (YYYY-MM-DD HH:MM:SS)").grid(row=0, column=2, sticky="e")
        self.comp_fecha = ttk.Entry(form, width=20)
        self.comp_fecha.grid(row=0, column=3, sticky="w")
        ttk.Label(form, text="Notas:").grid(row=0, column=4, sticky="e")
        self.comp_notas = ttk.Entry(form, width=30)
        self.comp_notas.grid(row=0, column=5, sticky="w")

        ttk.Label(form, text="Serie").grid(row=1, column=0, sticky="e", padx=4)
        self.comp_serie = ttk.Combobox(form, values=["C01"], width=8, state="readonly")
        self.comp_serie.set("C01")
        self.comp_serie.grid(row=1, column=1, sticky="w")
        ttk.Label(form, text="Proveedor (código)").grid(row=1, column=2, sticky="e", padx=4)
        self.comp_partner = ttk.Entry(form, width=22)
        self.comp_partner.grid(row=1, column=3, sticky="w")

        lines = ttk.LabelFrame(tab_c, text="Líneas")
        lines.pack(fill="x", padx=6, pady=6)
        self.comp_lines = []
        self._line_builder(lines, self.comp_lines, purchase=True)

        btns = ttk.Frame(tab_c)
        btns.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Button(btns, text="Registrar compra", command=self._comp_registrar).pack(side="left")
        ttk.Button(btns, text="Limpiar", command=lambda: self._lines_clear(self.comp_lines)).pack(side="left", padx=(6, 0))
        ttk.Button(btns, text="PDF del último…", command=self._comp_pdf_last).pack(side="right")

        # ---- Ventas ----
        tab_v = ttk.Frame(nb)
        nb.add(tab_v, text="Ventas")
        form2 = ttk.LabelFrame(tab_v, text="Cabecera")
        form2.pack(fill="x", padx=6, pady=6)
        ttk.Label(form2, text="Nº Doc:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.sale_num = ttk.Entry(form2, width=14)
        self.sale_num.grid(row=0, column=1, sticky="w")
        ttk.Label(form2, text="Fecha (YYYY-MM-DD HH:MM:SS)").grid(row=0, column=2, sticky="e")
        self.sale_fecha = ttk.Entry(form2, width=20)
        self.sale_fecha.grid(row=0, column=3, sticky="w")
        ttk.Label(form2, text="Notas:").grid(row=0, column=4, sticky="e")
        self.sale_notas = ttk.Entry(form2, width=30)
        self.sale_notas.grid(row=0, column=5, sticky="w")

        ttk.Label(form2, text="Serie").grid(row=1, column=0, sticky="e", padx=4)
        self.sale_serie = ttk.Combobox(form2, values=["V01"], width=8, state="readonly")
        self.sale_serie.set("V01")
        self.sale_serie.grid(row=1, column=1, sticky="w")
        ttk.Label(form2, text="Cliente (código)").grid(row=1, column=2, sticky="e", padx=4)
        self.sale_partner = ttk.Entry(form2, width=22)
        self.sale_partner.grid(row=1, column=3, sticky="w")

        lines2 = ttk.LabelFrame(tab_v, text="Líneas")
        lines2.pack(fill="x", padx=6, pady=6)
        self.sale_lines = []
        self._line_builder(lines2, self.sale_lines, purchase=False)

        btns2 = ttk.Frame(tab_v)
        btns2.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Button(btns2, text="Registrar venta", command=self._sale_registrar).pack(side="left")
        ttk.Button(btns2, text="Limpiar", command=lambda: self._lines_clear(self.sale_lines)).pack(side="left", padx=(6, 0))
        ttk.Button(btns2, text="PDF del último…", command=self._sale_pdf_last).pack(side="right")

        # ---- Ajustes ----
        tab_a = ttk.Frame(nb)
        nb.add(tab_a, text="Ajustes")
        adj = ttk.LabelFrame(tab_a, text="Ajustes")
        adj.pack(fill="x", padx=6, pady=6)
        self.adj_lines = []
        self._adjust_builder(adj, self.adj_lines)
        btns3 = ttk.Frame(tab_a)
        btns3.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Button(btns3, text="Registrar ajuste", command=self._adj_registrar).pack(side="left")
        ttk.Button(btns3, text="Limpiar", command=lambda: self._adj_clear(self.adj_lines)).pack(side="left", padx=(6, 0))

    def _build_tab_hist(self, parent: ttk.Frame):
        frame = ttk.LabelFrame(parent, text="Historial (altas/modificaciones/importaciones)")
        frame.pack(fill="both", expand=True, padx=6, pady=6)
        cols = ("codigo", "nombre", "accion", "fecha")
        self.tree_hist = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.tree_hist.heading(c, text=c.capitalize())
            self.tree_hist.column(c, width=180, anchor="w")
        self.tree_hist.pack(fill="both", expand=True)
        estilo.aplicar_estilo_treeview(self.tree_hist)
        scrollbars.agregar_scrollbar(self.tree_hist, frame)

    def _build_tab_reportes(self, parent: ttk.Frame):
        box = ttk.LabelFrame(parent, text="Kardex por producto")
        box.pack(fill="x", pady=6, padx=6)
        ttk.Label(box, text="Código").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self.kx_cod = ttk.Entry(box, width=18)
        self.kx_cod.grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(box, text="Nombre").grid(row=0, column=2, padx=4, pady=4, sticky="e")
        self.kx_name = ttk.Label(box, text="—", width=30)
        self.kx_name.grid(row=0, column=3, padx=4, pady=4, sticky="w")
        ttk.Label(box, text="Desde (YYYY-MM-DD)").grid(row=1, column=0, padx=4, pady=4, sticky="e")
        self.kx_from = ttk.Entry(box, width=18)
        self.kx_from.grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(box, text="Hasta (YYYY-MM-DD)").grid(row=1, column=2, padx=4, pady=4, sticky="e")
        self.kx_to = ttk.Entry(box, width=18)
        self.kx_to.grid(row=1, column=3, padx=4, pady=4, sticky="w")
        btns = ttk.Frame(box)
        btns.grid(row=0, column=4, rowspan=2, padx=6, pady=4, sticky="ns")
        ttk.Button(btns, text="Generar", command=self._kx_generate).pack(fill="x")
        ttk.Button(btns, text="Exportar Excel…", command=self._kx_export_xlsx).pack(fill="x", pady=(4, 0))
        ttk.Button(btns, text="Exportar PDF…", command=self._kx_export_pdf).pack(fill="x", pady=(4, 0))

        frame = ttk.LabelFrame(parent, text="Resultados")
        frame.pack(fill="both", expand=True, padx=6, pady=6)
        cols = (
            "fecha",
            "doc_no",
            "tipo",
            "qty_in",
            "qty_out",
            "unit_cost",
            "unit_price",
            "motivo",
            "saldo_qty",
            "saldo_cost",
            "saldo_total",
        )
        heads = {
            "fecha": "Fecha",
            "doc_no": "Doc Nº",
            "tipo": "Tipo",
            "qty_in": "Ent.",
            "qty_out": "Sal.",
            "unit_cost": "Costo u.",
            "unit_price": "Precio u.",
            "motivo": "Motivo",
            "saldo_qty": "Saldo",
            "saldo_cost": "Costo prom.",
            "saldo_total": "Valorización",
        }
        widths = {
            "fecha": 150,
            "doc_no": 120,
            "tipo": 90,
            "qty_in": 80,
            "qty_out": 80,
            "unit_cost": 90,
            "unit_price": 90,
            "motivo": 200,
            "saldo_qty": 90,
            "saldo_cost": 100,
            "saldo_total": 110,
        }
        self.kx_tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.kx_tree.heading(c, text=heads[c])
            self.kx_tree.column(c, width=widths[c], anchor="w" if c in ("fecha", "doc_no", "tipo", "motivo") else "e")
        self.kx_tree.pack(fill="both", expand=True)
        estilo.aplicar_estilo_treeview(self.kx_tree)
        scrollbars.agregar_scrollbar(self.kx_tree, frame)
        self.kx_summary = ttk.Label(parent, text="—")
        self.kx_summary.pack(anchor="e", padx=12, pady=(0, 6))
        self.kx_cod.bind("<FocusOut>", lambda e: self._kx_autoname())

    def _build_tab_auditoria(self, parent: ttk.Frame):
        self.audit_filters = {
            "user_q": None,
            "action_q": None,
            "text_q": None,
            "date_from": None,
            "date_to": None,
            "limit": 50,
            "offset": 0,
        }
        top = ttk.LabelFrame(parent, text="Filtros")
        top.pack(fill="x", pady=5, padx=6)
        ttk.Label(top, text="Usuario").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self.af_user = ttk.Entry(top, width=16)
        self.af_user.grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(top, text="Acción").grid(row=0, column=2, padx=4, pady=4, sticky="e")
        self.af_action = ttk.Entry(top, width=16)
        self.af_action.grid(row=0, column=3, padx=4, pady=4)
        ttk.Label(top, text="Texto").grid(row=0, column=4, padx=4, pady=4, sticky="e")
        self.af_text = ttk.Entry(top, width=22)
        self.af_text.grid(row=0, column=5, padx=4, pady=4, sticky="we")
        ttk.Label(top, text="Desde").grid(row=1, column=0, padx=4, pady=4, sticky="e")
        self.af_from = ttk.Entry(top, width=16)
        self.af_from.grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(top, text="Hasta").grid(row=1, column=2, padx=4, pady=4, sticky="e")
        self.af_to = ttk.Entry(top, width=16)
        self.af_to.grid(row=1, column=3, padx=4, pady=4)
        ttk.Button(top, text="Buscar", command=lambda: self._audit_reload(reset=True)).grid(row=1, column=4, padx=4, pady=4)
        ttk.Button(top, text="Limpiar", command=self._audit_clear).grid(row=1, column=5, padx=4, pady=4, sticky="w")
        for i in (5,):
            top.grid_columnconfigure(i, weight=1)

        frame = ttk.LabelFrame(parent, text="Eventos")
        frame.pack(fill="both", expand=True, pady=6, padx=6)
        cols = ("fecha", "usuario", "accion", "detalles")
        self.audit_tree = ttk.Treeview(frame, columns=cols, show="headings")
        heads = {"fecha": "Fecha", "usuario": "Usuario", "accion": "Acción", "detalles": "Detalles"}
        widths = {"fecha": 160, "usuario": 140, "accion": 160, "detalles": 600}
        for c in cols:
            self.audit_tree.heading(c, text=heads[c])
            self.audit_tree.column(c, width=widths[c], anchor="w")
        self.audit_tree.pack(fill="both", expand=True)
        estilo.aplicar_estilo_treeview(self.audit_tree)
        scrollbars.agregar_scrollbar(self.audit_tree, frame)

        pager = ttk.Frame(parent)
        pager.pack(fill="x", padx=6, pady=(2, 8))
        ttk.Button(pager, text="<<", command=lambda: self._audit_jump("first")).pack(side="left")
        ttk.Button(pager, text="<", command=lambda: self._audit_jump("prev")).pack(side="left", padx=(4, 0))
        ttk.Button(pager, text=">", command=lambda: self._audit_jump("next")).pack(side="left", padx=(4, 0))
        ttk.Button(pager, text=">>", command=lambda: self._audit_jump("last")).pack(side="left", padx=(4, 8))
        self.audit_lbl = ttk.Label(pager, text="Mostrando 0–0 de 0")
        self.audit_lbl.pack(side="left")

        self._audit_do_list = lambda: list_audit(
            user_q=self.audit_filters["user_q"],
            action_q=self.audit_filters["action_q"],
            text_q=self.audit_filters["text_q"],
            date_from=self.audit_filters["date_from"],
            date_to=self.audit_filters["date_to"],
            limit=self.audit_filters["limit"],
            offset=self.audit_filters["offset"],
            order_desc=True,
        )
        self._audit_total = 0
        self._audit_reload(reset=True)

    def _build_tab_users(self, parent: ttk.Frame):
        """
        Administración de Usuarios y Roles
        """
        wrapper = ttk.Notebook(parent)
        wrapper.pack(fill="both", expand=True, padx=6, pady=6)

        tab_users = ttk.Frame(wrapper)
        wrapper.add(tab_users, text="Usuarios")

        # Lista de usuarios
        cols = ("id", "username", "name", "active", "roles")
        self.users_tree = ttk.Treeview(tab_users, columns=cols, show="headings", height=12)
        heads = {"id": "ID", "username": "Usuario", "name": "Nombre", "active": "Activo", "roles": "Roles"}
        widths = {"id": 60, "username": 140, "name": 220, "active": 80, "roles": 260}
        for c in cols:
            self.users_tree.heading(c, text=heads[c])
            self.users_tree.column(c, width=widths[c], anchor="w")
        self.users_tree.pack(fill="both", expand=True, padx=6, pady=6)
        estilo.aplicar_estilo_treeview(self.users_tree)
        scrollbars.agregar_scrollbar(self.users_tree, tab_users)

        # Formulario simple
        frm = ttk.LabelFrame(tab_users, text="Nuevo / Edición rápida")
        frm.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Label(frm, text="Usuario").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.u_username = ttk.Entry(frm, width=20)
        self.u_username.grid(row=0, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(frm, text="Nombre").grid(row=0, column=2, sticky="e", padx=4, pady=4)
        self.u_name = ttk.Entry(frm, width=30)
        self.u_name.grid(row=0, column=3, sticky="w", padx=4, pady=4)

        ttk.Button(frm, text="Crear usuario", command=self._user_create).grid(row=0, column=4, padx=4, pady=4)
        ttk.Button(frm, text="Activar", command=lambda: self._user_active(True)).grid(row=0, column=5, padx=4, pady=4)
        ttk.Button(frm, text="Desactivar", command=lambda: self._user_active(False)).grid(row=0, column=6, padx=4, pady=4)
        ttk.Button(frm, text="Reset pass", command=self._user_reset_pwd).grid(row=0, column=7, padx=4, pady=4)

        # Roles
        frm_roles = ttk.LabelFrame(tab_users, text="Asignar roles al usuario seleccionado")
        frm_roles.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Label(frm_roles, text="Roles disponibles (Ctrl+clic para varios)").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.roles_list = tk.Listbox(frm_roles, selectmode="multiple", height=6, exportselection=False)
        self.roles_list.grid(row=1, column=0, sticky="we", padx=4, pady=4)
        frm_roles.grid_columnconfigure(0, weight=1)
        ttk.Button(frm_roles, text="Guardar roles", command=self._user_save_roles).grid(row=1, column=1, sticky="ns", padx=6, pady=4)

    def _users_reload(self):
        # limpiar tabla
        for i in self.users_tree.get_children():
            self.users_tree.delete(i)

        data = list_users()  # puede devolver tuplas o dicts

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

            # normalizar roles (puede venir como lista/tupla o string)
            if isinstance(roles_raw, (list, tuple, set)):
                roles = ", ".join(str(x) for x in roles_raw)
            else:
                roles = str(roles_raw or "")

            self.users_tree.insert("", "end", values=(uid, username, name, active, roles))

        # Cargar catálogo de roles
        self.roles_list.delete(0, tk.END)
        for ro in list_roles():
            self.roles_list.insert(tk.END, ro)

    def _build_tab_settings(self, parent: ttk.Frame):
        box = ttk.LabelFrame(parent, text="Datos de la empresa")
        box.pack(fill="x", padx=8, pady=8)

        s = get_settings()
        ttk.Label(box, text="Nombre empresa").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.st_name = ttk.Entry(box, width=40)
        self.st_name.grid(row=0, column=1, sticky="w", padx=4, pady=4)
        self.st_name.insert(0, s["company_name"])

        ttk.Label(box, text="NIT/RUC").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        self.st_tax = ttk.Entry(box, width=30)
        self.st_tax.grid(row=1, column=1, sticky="w", padx=4, pady=4)
        self.st_tax.insert(0, s["company_tax"])

        ttk.Label(box, text="Dirección").grid(row=2, column=0, sticky="e", padx=4, pady=4)
        self.st_addr = ttk.Entry(box, width=50)
        self.st_addr.grid(row=2, column=1, sticky="w", padx=4, pady=4)
        self.st_addr.insert(0, s["company_addr"])

        ttk.Label(box, text="Logo (ruta opcional)").grid(row=3, column=0, sticky="e", padx=4, pady=4)
        self.st_logo = ttk.Entry(box, width=50)
        self.st_logo.grid(row=3, column=1, sticky="w", padx=4, pady=4)
        if s.get("logo_path"):
            self.st_logo.insert(0, s["logo_path"])
        ttk.Button(box, text="Buscar…", command=self._st_pick_logo).grid(row=3, column=2, padx=4, pady=4)

        opts = ttk.LabelFrame(parent, text="Impuestos")
        opts.pack(fill="x", padx=8, pady=8)
        self.st_tax_included = tk.BooleanVar(value=bool(s["tax_included"]))
        ttk.Checkbutton(opts, text="Precios incluyen impuestos", variable=self.st_tax_included).grid(
            row=0, column=0, sticky="w", padx=4, pady=4
        )
        ttk.Label(opts, text="Tasa de impuesto (ej. 0.19 para 19%)").grid(row=0, column=1, sticky="e", padx=4, pady=4)
        self.st_tax_rate = ttk.Entry(opts, width=10)
        self.st_tax_rate.grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.st_tax_rate.insert(0, str(s["tax_rate"]))

        # sección de configuración del sistema
        sysbox = ttk.LabelFrame(parent, text="Configuración del sistema")
        sysbox.pack(fill="x", padx=8, pady=8)
        # información del sistema (se usa módulo dedicado para facilitar pruebas)
        from src.core.system_info import get_system_info
        info = get_system_info()
        lic_valid = "sí" if info.get("license_valid") else "no"
        ttk.Label(sysbox, text=f"Licencia válida: {lic_valid}").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        # versión local
        ver = info.get("local_version", "?")
        ttk.Label(sysbox, text=f"Versión del software: {ver}").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        # backups
        ttk.Label(sysbox, text=f"Backups disponibles: {info.get('backup_count', 0)}").grid(row=2, column=0, sticky="w", padx=4, pady=2)
        # logs recientes
        ttk.Label(sysbox, text="Últimos logs:").grid(row=3, column=0, sticky="w", padx=4, pady=2)
        txt = tk.Text(sysbox, height=3, width=60)
        txt.grid(row=4, column=0, columnspan=3, padx=4, pady=2)
        txt.insert("1.0", info.get("recent_logs", ""))
        txt.config(state="disabled")


        btns = ttk.Frame(parent)
        btns.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(btns, text="Guardar", command=self._st_save).pack(side="left")
        ttk.Button(btns, text="Restaurar valores actuales", command=self._st_reload).pack(side="left", padx=(6, 0))

    # =========================
    # Inventario: handlers
    # =========================
    def refrescar_todo(self):
        self._total_items = count_products(self._filter_by, self._filter_q)
        self._page = 1
        self._load_page()
        self._load_hist()
        self._update_stats()

    def _load_page(self):
        rows = list_products_page(
            self._page, self._page_size, self._filter_by, self._filter_q, self._order_by, self._asc
        )
        for r in self.tree.get_children():
            self.tree.delete(r)
        for i, p in enumerate(rows):
            tag = "par" if i % 2 == 0 else "impar"
            if p[4] <= UMBRAL_STOCK_BAJO:
                tag = "baja"
            self.tree.insert("", "end", values=p, tags=(tag,))
        total_pages = max(1, (self._total_items + self._page_size - 1) // self._page_size)
        start = 0 if self._total_items == 0 else (self._page - 1) * self._page_size + 1
        end = min(self._page * self._page_size, self._total_items)
        self.lbl_range.config(text=f"Mostrando {start}–{end} de {self._total_items} (pág. {self._page} de {total_pages})")

    def _update_stats(self):
        self.lbl_total_productos.config(text=f"Total de productos: {count_products()}")
        self.lbl_total_stock.config(text=f"Stock total: {int(stock_global_sum())}")
        self.lbl_stock_bajo.config(text=f"Stock bajo (≤ {UMBRAL_STOCK_BAJO}): {low_stock_count(UMBRAL_STOCK_BAJO)}")

    def buscar_producto(self):
        self._filter_by = self.combo_filtro.get()
        self._filter_q = self.entry_buscar.get().strip()
        self._total_items = count_products(self._filter_by, self._filter_q)
        self._page = 1
        self._load_page()

    def limpiar_busqueda(self):
        self.combo_filtro.current(0)
        self.entry_buscar.delete(0, tk.END)
        self._filter_by = None
        self._filter_q = ""
        self._total_items = count_products()
        self._page = 1
        self._load_page()

    def first_page(self):
        self._page = 1
        self._load_page()

    def prev_page(self):
        self._page = max(1, self._page - 1)
        self._load_page()

    def next_page(self):
        total_pages = max(1, (self._total_items + self._page_size - 1) // self._page_size)
        self._page = min(total_pages, self._page + 1)
        self._load_page()

    def last_page(self):
        self._page = max(1, (self._total_items + self._page_size - 1) // self._page_size)
        self._load_page()

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
            add_product(**dlg.result, user_id=self.user["id"])
            self.refrescar_todo()
        except Exception as e:
            messagebox.showerror("Nuevo producto", str(e))

    def editar_producto(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Editar", "Selecciona un producto.")
            return
        codigo = self.tree.item(sel[0])["values"][0]
        p = get_product(codigo)
        dlg = ProductoDialog(
            self.root,
            initial={"codigo": p[0], "nombre": p[1], "categoria": p[2], "precio": p[3], "cantidad": p[4]},
            editable_code=False,
            title="Editar producto",
        )
        if not dlg.result:
            return
        try:
            update_product(codigo, **{k: v for k, v in dlg.result.items() if k != "codigo"}, user_id=self.user["id"])
            self.refrescar_todo()
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
            self.refrescar_todo()
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
            messagebox.showinfo("Compra registrada", f"Compra Nº: {num}")
            self.refrescar_todo()
        except Exception as e:
            messagebox.showerror("Compra", str(e))

    def _sale_registrar(self):
        items = self._lines_parse(self.sale_lines, purchase=False)
        if not items:
            messagebox.showerror("Venta", "Agrega al menos una línea."); return
        numero = self.sale_num.get().strip() or None
        fecha  = self.sale_fecha.get().strip() or None
        notas  = self.sale_notas.get().strip() or None
        serie  = self.sale_serie.get().strip() or "V01"
        cli    = self.sale_partner.get().strip() or None
        try:
            doc_id, num, totals = post_sale(numero, fecha, items, notas, partner_code=cli, series=serie, allow_negative=False)
            self.last_sale_doc_id = doc_id
            msg = (
                f"Venta Nº: {num}\n\n"
                f"Subtotal: {totals['neto']:.2f}\n"
                f"Impuesto: {totals['impuesto']:.2f}\n"
                f"TOTAL:    {totals['total']:.2f}\n"
                f"(Incluye impuesto: {'Sí' if totals['tax_included'] else 'No'} @ {totals['tax_rate']*100:.2f}%)"
            )
            messagebox.showinfo("Venta registrada", msg)
            self.refrescar_todo()
        except Exception as e:
            messagebox.showerror("Venta", str(e))
            items = self._lines_parse(self.sale_lines, purchase=False)
            if not items:
                messagebox.showerror("Venta", "Agrega al menos una línea.")
                return
            numero = self.sale_num.get().strip() or None
            fecha = self.sale_fecha.get().strip() or None
            notas = self.sale_notas.get().strip() or None
            serie = self.sale_serie.get().strip() or "V01"
            cli = self.sale_partner.get().strip() or None
            try:
                doc_id, num = post_sale(numero, fecha, items, notas, partner_code=cli, series=serie, allow_negative=False)
                self.last_sale_doc_id = doc_id
                messagebox.showinfo("Venta registrada", f"Venta Nº: {num}")
                self.refrescar_todo()
            except Exception as e:
                messagebox.showerror("Venta", str(e))

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
            if not getattr(self, "last_sale_doc_id", None):
                messagebox.showinfo("Venta", "Aún no has registrado una venta en esta sesión.")
                return
            path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                initialfile=f"venta_{self.last_sale_doc_id}.pdf",
            )
            if not path:
                return
            s = get_settings()
            logo_path = s.get("logo_path")
            try:
                export_sale_pdf(
                    self.last_sale_doc_id,
                    path,
                    logo_path=logo_path,
                    company_name=s["company_name"],
                    company_tax=s["company_tax"],
                    company_addr=s["company_addr"],
                    tax_rate=float(s["tax_rate"] or 0.0),
                    tax_included=bool(s["tax_included"]),
                )
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
            from core.database import DB_PATH
            import shutil

            shutil.copyfile(DB_PATH, path)
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
            from core.database import DB_PATH
            import shutil

            shutil.copyfile(path, DB_PATH)
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
            from core.auth import change_password

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
            messagebox.showinfo("Parámetros", "Parámetros guardados.")
        except Exception as e:
            messagebox.showerror("Parámetros", str(e))

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


# =========================
# Diálogo producto (crear/editar)
# =========================
class ProductoDialog(tk.Toplevel):
    def __init__(self, master, initial: Optional[dict] = None, editable_code: bool = True, title: str = "Producto"):
        super().__init__(master)
        self.title(title)
        self.result = None
        self.resizable(False, False)
        init = initial or {}
        frm = ttk.Frame(self, padding=10)
        frm.grid(sticky="nsew")
        ttk.Label(frm, text="Código").grid(row=0, column=0, sticky="e", padx=4, pady=6)
        self.e_cod = ttk.Entry(frm, width=22)
        self.e_cod.grid(row=0, column=1, padx=4, pady=6)
        ttk.Label(frm, text="Nombre").grid(row=1, column=0, sticky="e", padx=4, pady=6)
        self.e_nom = ttk.Entry(frm, width=36)
        self.e_nom.grid(row=1, column=1, padx=4, pady=6)
        ttk.Label(frm, text="Categoría").grid(row=2, column=0, sticky="e", padx=4, pady=6)
        self.e_cat = ttk.Entry(frm, width=22)
        self.e_cat.grid(row=2, column=1, padx=4, pady=6)
        ttk.Label(frm, text="Precio/Costo").grid(row=3, column=0, sticky="e", padx=4, pady=6)
        self.e_pre = ttk.Entry(frm, width=12)
        self.e_pre.grid(row=3, column=1, sticky="w", padx=4, pady=6)
        ttk.Label(frm, text="Cantidad").grid(row=4, column=0, sticky="e", padx=4, pady=6)
        self.e_can = ttk.Entry(frm, width=12)
        self.e_can.grid(row=4, column=1, sticky="w", padx=4, pady=6)
        if init:
            self.e_cod.insert(0, init.get("codigo", ""))
            self.e_nom.insert(0, init.get("nombre", ""))
            self.e_cat.insert(0, init.get("categoria", ""))
            self.e_pre.insert(0, str(init.get("precio", "")))
            self.e_can.insert(0, str(init.get("cantidad", "")))
        if not editable_code:
            self.e_cod.configure(state="disabled")
        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btns, text="Guardar", command=self._ok).pack(side="right")
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(master)
        self.grab_set()
        self.wait_window(self)

    def _ok(self):
        try:
            # ensure the expected widgets exist; if not, initialization failed
            if not hasattr(self, 'e_cod'):
                raise RuntimeError("widget e_cod no creado")
            data = {
                "codigo": (self.e_cod.get() or "").strip(),
                "nombre": (self.e_nom.get() or "").strip(),
                "categoria": (self.e_cat.get() or "").strip(),
                "precio": float(self.e_pre.get() or 0.0),
                "cantidad": int(float(self.e_can.get() or 0)),
            }
            if not data["codigo"] or not data["nombre"]:
                raise ValueError("Código y Nombre son obligatorios.")
            self.result = data
            self.destroy()
        except Exception as e:
            messagebox.showerror("Validación", str(e))
