import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import time
from src.app.components_luxury import Tooltip

from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography
from src.services.partners import (
    list_partners, create_partner, update_partner, get_partner_by_code, set_partner_active,
    get_supplier_history, get_supplier_orders
)
from src.database.connection import get_connection

_BG_DARK = getattr(Luxury2026Colors, "BG_DARKEST", "#0A0E27")
_BG_PANEL = getattr(Luxury2026Colors, "BG_SECONDARY", "#0D1117")
_ACCENT = getattr(Luxury2026Colors, "ACCENT", "#3B82F6")
_WARNING = getattr(Luxury2026Colors, "WARNING", "#D97706")
_DANGER = getattr(Luxury2026Colors, "DANGER", "#DC2626")

class SuppliersWindow(tk.Toplevel):
    """Gestión de proveedores."""

    def __init__(self, parent, user=None):
        super().__init__(parent)
        self.title("Gestión de Proveedores")
        self.geometry("1000x600")
        self.configure(bg=_BG_DARK)
        self.transient(parent)
        self.grab_set()
        self.user = user
        self.selected_partner = None
        self._build_ui()
        self._load_suppliers()

    def _build_ui(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)

        # Tab 1: Proveedores
        self.tab_proveedores = tk.Frame(self.tabs, bg=_BG_DARK)
        self.tabs.add(self.tab_proveedores, text="Proveedores")
        self._build_tab_proveedores(self.tab_proveedores)

        # Tab 2: Detalle
        self.tab_detalle = tk.Frame(self.tabs, bg=_BG_DARK)
        self.tabs.add(self.tab_detalle, text="Detalle")
        self._build_tab_detalle(self.tab_detalle)

        # Tab 3: Órdenes
        self.tab_ordenes = tk.Frame(self.tabs, bg=_BG_DARK)
        self.tabs.add(self.tab_ordenes, text="Órdenes")
        self._build_tab_ordenes(self.tab_ordenes)

    # --- TAB 1: PROVEEDORES ---
    def _build_tab_proveedores(self, frame):
        top = tk.Frame(frame, bg=_BG_DARK)
        top.pack(fill="x", pady=8)
        tk.Label(top, text="Buscar:", bg=_BG_DARK, fg="white").pack(side="left")
        self.var_search = tk.StringVar()
        entry = tk.Entry(top, textvariable=self.var_search, width=50)
        entry.pack(side="left", padx=4)
        from src.app.styles.luxury_2026 import add_placeholder
        add_placeholder(entry, "🔍 Buscar proveedor por nombre o NIT...")
        entry.bind("<KeyRelease>", lambda e: self._filter_suppliers())
        ttk.Button(top, text="Nuevo proveedor", command=self._new_supplier).pack(side="right", padx=4)
        ttk.Button(top, text="Editar", command=self._edit_supplier).pack(side="right", padx=4)
        ttk.Button(top, text="Activar/Desactivar", command=self._toggle_active).pack(side="right", padx=4)
        ttk.Button(top, text="📥 Excel", command=self._exportar_proveedores).pack(side="right", padx=4)

        columns = ("code", "name", "phone", "email", "city", "tax_id", "active")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=18)
        for col, label in zip(columns, ["Código", "Nombre", "Teléfono", "Email", "Ciudad", "RUC/NIT", "Estado"]):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=120 if col != "name" else 180)
        self.tree.pack(fill="both", expand=True, pady=8)
        self.tree.bind("<Double-1>", self._on_row_double_click)
        self.tree.tag_configure("activo",   foreground="#10B981")
        self.tree.tag_configure("inactivo", foreground="#6B7280")

    def _load_suppliers(self):
        self.suppliers = list_partners(kind="SUPPLIER")
        self.filtered_suppliers = self.suppliers
        self._refresh_tree()

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for s in self.filtered_suppliers:
            estado = "Activo" if s.get("active", 1) else "Inactivo"
            tag = "activo" if s.get("active", 1) else "inactivo"
            self.tree.insert("", "end", values=(
                s.get("code"), s.get("name"), s.get("phone"), s.get("email"),
                s.get("city"), s.get("tax_id"), estado
            ), tags=(tag,))

    def _filter_suppliers(self):
        q = self.var_search.get().strip().lower()
        if q == "🔍 buscar proveedor por nombre o nit...":
            q = ""
        if not q:
            self.filtered_suppliers = self.suppliers
        else:
            self.filtered_suppliers = [
                s for s in self.suppliers
                if q in (s.get("name") or "").lower()
                or q in (s.get("phone") or "").lower()
                or q in (s.get("code") or "").lower()
            ]
        self._refresh_tree()

    def _on_row_double_click(self, event):
        item = self.tree.focus()
        if not item:
            return
        code = self.tree.item(item)["values"][0]
        self.selected_partner = get_partner_by_code(code)
        self._load_partner_detail()
        self.tabs.select(self.tab_detalle)

    def _new_supplier(self):
        self._open_supplier_form()

    def _edit_supplier(self):
        item = self.tree.focus()
        if not item:
            messagebox.showinfo("Proveedores", "Selecciona un proveedor para editar.")
            return
        code = self.tree.item(item)["values"][0]
        partner = get_partner_by_code(code)
        self._open_supplier_form(partner)

    def _toggle_active(self):
        item = self.tree.focus()
        if not item:
            messagebox.showinfo("Proveedores", "Selecciona un proveedor.")
            return
        code = self.tree.item(item)["values"][0]
        partner = get_partner_by_code(code)
        if not partner:
            return
        is_active = bool(partner[10])
        set_partner_active(code, not is_active)
        self._load_suppliers()

    # --- TAB 2: DETALLE ---
    def _build_tab_detalle(self, frame):
        self.detail_vars = {k: tk.StringVar() for k in [
            "name", "phone", "email", "address", "city", "tax_id", "notes", "delivery_days", "payment_terms"
        ]}
        form = tk.Frame(frame, bg=_BG_DARK)
        form.pack(fill="x", pady=10)
        row = 0
        for label, key in [
            ("Nombre*", "name"), ("Teléfono", "phone"), ("Email", "email"),
            ("Dirección", "address"), ("Ciudad", "city"), ("RUC/NIT", "tax_id"),
            ("Plazo de entrega (días)", "delivery_days"), ("Condiciones de pago", "payment_terms"),
            ("Notas", "notes")
        ]:
            tk.Label(form, text=label, bg=_BG_DARK, fg="white").grid(row=row, column=0, sticky="e", pady=2, padx=4)
            tk.Entry(form, textvariable=self.detail_vars[key], width=40).grid(row=row, column=1, sticky="w", pady=2)
            row += 1

        ttk.Button(form, text="Guardar cambios", command=self._save_partner_detail).grid(row=row, column=1, sticky="e", pady=8)

        # Historial de compras al proveedor
        hist_frame = tk.LabelFrame(frame, text="Historial de compras al proveedor", bg=_BG_DARK, fg="white")
        hist_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("fecha", "numero", "total", "estado")
        self.tree_hist = ttk.Treeview(hist_frame, columns=columns, show="headings", height=8)
        for col, label in zip(columns, ["Fecha", "Número", "Total", "Estado"]):
            self.tree_hist.heading(col, text=label)
            self.tree_hist.column(col, width=120)
        self.tree_hist.pack(fill="both", expand=True, pady=4)
        self.lbl_total_hist = tk.Label(hist_frame, text="", bg=_BG_DARK, fg="white")
        self.lbl_total_hist.pack(anchor="w", padx=8, pady=2)
        Tooltip(self.lbl_total_hist, "Suma total invertida en compras\na este proveedor")
        self.lbl_ult_compra = tk.Label(hist_frame, text="", bg=_BG_DARK, fg="white")
        self.lbl_ult_compra.pack(anchor="w", padx=8, pady=2)
        Tooltip(self.lbl_ult_compra, "Fecha de la última orden de compra\nrecibida de este proveedor")

    def _load_partner_detail(self):
        if not self.selected_partner:
            return
        # partner: (id, code, kind, name, tax_id, phone, email, address, city, notes, active)
        p = self.selected_partner
        self.detail_vars["name"].set(p[3] or "")
        self.detail_vars["tax_id"].set(p[4] or "")
        self.detail_vars["phone"].set(p[5] or "")
        self.detail_vars["email"].set(p[6] or "")
        self.detail_vars["address"].set(p[7] or "")
        self.detail_vars["city"].set(p[8] or "")
        self.detail_vars["notes"].set(p[9] or "")
        
        # Campos adicionales (delivery_days, payment_terms) desde extra_data o BD
        # Por ahora placeholders vacíos; Fase 2 ampliar BD
        self.detail_vars["delivery_days"].set("")
        self.detail_vars["payment_terms"].set("")
        
        self._load_historial_compras(p[0])

    def _save_partner_detail(self):
        if not self.selected_partner:
            return
        code = self.selected_partner[1]
        update_partner(
            code,
            name=self.detail_vars["name"].get(),
            tax_id=self.detail_vars["tax_id"].get(),
            phone=self.detail_vars["phone"].get(),
            email=self.detail_vars["email"].get(),
            address=self.detail_vars["address"].get(),
            city=self.detail_vars["city"].get(),
            notes=self.detail_vars["notes"].get()
        )
        messagebox.showinfo("Proveedores", "Datos actualizados.")
        self._load_suppliers()

    def _load_historial_compras(self, partner_id):
        history = get_supplier_history(partner_id)
        self.tree_hist.delete(*self.tree_hist.get_children())
        total_hist = 0.0
        fechas = []
        for row in history:
            # row: (fecha, numero, total, estado)
            self.tree_hist.insert("", "end", values=row)
            total_hist += row[2] or 0.0
            fechas.append(row[0])
        self.lbl_total_hist.config(text=f"Total comprado: ${total_hist:.2f}")
        if fechas:
            self.lbl_ult_compra.config(text=f"Última compra: {fechas[0]}")
        else:
            self.lbl_ult_compra.config(text="Última compra: -")

    # --- TAB 3: ÓRDENES ---
    def _build_tab_ordenes(self, frame):
        top = tk.Frame(frame, bg=_BG_DARK)
        top.pack(fill="x", pady=8)
        ttk.Button(top, text="Nueva orden", command=self._new_order).pack(side="right", padx=4)

        columns = ("fecha", "numero", "total", "estado")
        self.tree_ordenes = ttk.Treeview(frame, columns=columns, show="headings", height=18)
        for col, label in zip(columns, ["Fecha", "Número", "Total", "Estado"]):
            self.tree_ordenes.heading(col, text=label)
            self.tree_ordenes.column(col, width=150)
        self.tree_ordenes.pack(fill="both", expand=True, pady=8)

    def _load_ordenes(self):
        if not self.selected_partner:
            return
        ordenes = get_supplier_orders(self.selected_partner[0])
        self.tree_ordenes.delete(*self.tree_ordenes.get_children())
        for o in ordenes:
            # o: (fecha, numero, total, estado)
            self.tree_ordenes.insert("", "end", values=o)

    def _new_order(self):
        """Abre la ventana de órdenes de compra con el proveedor preseleccionado."""
        import traceback
        try:
            from src.app.purchase_orders_window import PurchaseOrdersWindow
            supplier_code = self.selected_partner[1] if self.selected_partner else None
            win = PurchaseOrdersWindow(self, self.user, supplier_code)
            self.wait_window(win)
        except Exception as e:
            import sys
            traceback.print_exc(file=sys.stdout)
            messagebox.showerror("Error", f"No se pudo abrir Órdenes de Compra:\n{e}")

    # --- FORMULARIO NUEVO/EDITAR PROVEEDOR ---
    def _open_supplier_form(self, partner=None):
        win = tk.Toplevel(self)
        win.title("Nuevo proveedor" if partner is None else "Editar proveedor")
        win.geometry("400x350")
        win.configure(bg=_BG_DARK)
        vars = {k: tk.StringVar() for k in [
            "name", "phone", "email", "address", "city", "tax_id", "notes"
        ]}
        row = 0
        for label, key in [
            ("Nombre*", "name"), ("Teléfono", "phone"), ("Email", "email"),
            ("Dirección", "address"), ("Ciudad", "city"), ("RUC/NIT", "tax_id"), ("Notas", "notes")
        ]:
            tk.Label(win, text=label, bg=_BG_DARK, fg="white").grid(row=row, column=0, sticky="e", pady=2, padx=4)
            tk.Entry(win, textvariable=vars[key], width=30).grid(row=row, column=1, sticky="w", pady=2)
            row += 1
        if partner:
            # partner: (id, code, kind, name, tax_id, phone, email, address, city, notes, active)
            vars["name"].set(partner[3] or "")
            vars["tax_id"].set(partner[4] or "")
            vars["phone"].set(partner[5] or "")
            vars["email"].set(partner[6] or "")
            vars["address"].set(partner[7] or "")
            vars["city"].set(partner[8] or "")
            vars["notes"].set(partner[9] or "")
        def guardar():
            nombre = vars["name"].get().strip()
            if not nombre:
                messagebox.showerror("Proveedores", "El nombre es obligatorio.")
                return
            code = partner[1] if partner else f"SUPP-{int(time.time())}"
            if partner:
                update_partner(
                    code,
                    name=nombre,
                    tax_id=vars["tax_id"].get(),
                    phone=vars["phone"].get(),
                    email=vars["email"].get(),
                    address=vars["address"].get(),
                    city=vars["city"].get(),
                    notes=vars["notes"].get()
                )
            else:
                create_partner(
                    code=code,
                    kind="SUPPLIER",
                    name=nombre,
                    tax_id=vars["tax_id"].get(),
                    phone=vars["phone"].get(),
                    email=vars["email"].get(),
                    address=vars["address"].get(),
                    city=vars["city"].get(),
                    notes=vars["notes"].get(),
                    active=True
                )
            messagebox.showinfo("Proveedores", "Proveedor guardado.")
            win.destroy()
            self._load_suppliers()
        ttk.Button(win, text="Guardar", command=guardar).grid(row=row, column=1, sticky="e", pady=8)
        ttk.Button(win, text="Cancelar", command=win.destroy).grid(row=row, column=0, sticky="w", pady=8)

    def show(self):
        self.deiconify()
        self.wait_window()

    def _exportar_proveedores(self):
        from tkinter import filedialog, messagebox
        import openpyxl
        cols = ["Código", "Nombre", "Teléfono", "Email", "Ciudad", "RUC/NIT", "Estado"]
        filas = [self.tree.item(i)["values"] for i in self.tree.get_children()]
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
            initialfile="proveedores.xlsx", title="Exportar Proveedores"
        )
        if not path:
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Proveedores"
        ws.append(cols)
        for f in filas:
            ws.append(list(f))
        wb.save(path)
        messagebox.showinfo("✅ Exportado", f"Archivo guardado:\n{path}")
