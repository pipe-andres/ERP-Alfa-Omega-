import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import time
from src.app.components_luxury import Tooltip

from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography
from src.services.purchase_orders import (
    create_purchase_order, get_purchase_order, list_purchase_orders,
    receive_order, cancel_order
)
from src.services.partners import list_partners
from src.services.inventory import get_product
from src.database.connection import get_connection

_BG_DARK = getattr(Luxury2026Colors, "BG_DARKEST", "#0A0E27")
_BG_PANEL = getattr(Luxury2026Colors, "BG_SECONDARY", "#0D1117")
_ACCENT = getattr(Luxury2026Colors, "ACCENT", "#3B82F6")
_WARNING = getattr(Luxury2026Colors, "WARNING", "#D97706")
_DANGER = getattr(Luxury2026Colors, "DANGER", "#DC2626")

class PurchaseOrdersWindow(tk.Toplevel):
    """Gestión de órdenes de compra."""

    def __init__(self, parent, user=None, supplier_code=None):
        super().__init__(parent)
        self.title("Órdenes de Compra")
        self.geometry("1200x700")
        self.configure(bg=_BG_DARK)
        self.transient(parent)
        self.grab_set()
        self.user = user
        self.supplier_code = supplier_code  # Para preseleccionar proveedor
        self.selected_order = None
        self.order_items = []  # Para nueva orden
        self._build_ui()
        self._load_orders()

    def _build_ui(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)

        # Tab 1: Órdenes
        self.tab_ordenes = tk.Frame(self.tabs, bg=_BG_DARK)
        self.tabs.add(self.tab_ordenes, text="Órdenes")
        self._build_tab_ordenes(self.tab_ordenes)

        # Tab 2: Nueva Orden
        self.tab_nueva = tk.Frame(self.tabs, bg=_BG_DARK)
        self.tabs.add(self.tab_nueva, text="Nueva Orden")
        self._build_tab_nueva(self.tab_nueva)

        # Tab 3: Recepción
        self.tab_recepcion = tk.Frame(self.tabs, bg=_BG_DARK)
        self.tabs.add(self.tab_recepcion, text="Recepción")
        self._build_tab_recepcion(self.tab_recepcion)

    # --- TAB 1: ÓRDENES ---
    def _build_tab_ordenes(self, frame):
        # Filtros
        filters = tk.Frame(frame, bg=_BG_DARK)
        filters.pack(fill="x", pady=8)

        tk.Label(filters, text="Proveedor:", bg=_BG_DARK, fg="white").grid(row=0, column=0, padx=4, pady=2, sticky="e")
        self.var_supplier_filter = tk.StringVar()
        suppliers = [""] + [p["code"] for p in list_partners(kind="SUPPLIER")]
        self.cb_supplier_filter = ttk.Combobox(filters, textvariable=self.var_supplier_filter, values=suppliers, width=20)
        self.cb_supplier_filter.grid(row=0, column=1, padx=4, pady=2)
        self.cb_supplier_filter.bind("<<ComboboxSelected>>", lambda e: self._load_orders())

        tk.Label(filters, text="Estado:", bg=_BG_DARK, fg="white").grid(row=0, column=2, padx=4, pady=2, sticky="e")
        self.var_status_filter = tk.StringVar()
        self.cb_status_filter = ttk.Combobox(filters, textvariable=self.var_status_filter,
                                           values=["", "PENDIENTE", "PARCIAL", "RECIBIDA", "CANCELADA"], width=15)
        self.cb_status_filter.grid(row=0, column=3, padx=4, pady=2)
        self.cb_status_filter.bind("<<ComboboxSelected>>", lambda e: self._load_orders())

        tk.Label(filters, text="Desde:", bg=_BG_DARK, fg="white").grid(row=0, column=4, padx=4, pady=2, sticky="e")
        self.var_date_from = tk.StringVar()
        self.entry_date_from = tk.Entry(filters, textvariable=self.var_date_from, width=12)
        self.entry_date_from.grid(row=0, column=5, padx=4, pady=2)

        tk.Label(filters, text="Hasta:", bg=_BG_DARK, fg="white").grid(row=0, column=6, padx=4, pady=2, sticky="e")
        self.var_date_to = tk.StringVar()
        self.entry_date_to = tk.Entry(filters, textvariable=self.var_date_to, width=12)
        self.entry_date_to.grid(row=0, column=7, padx=4, pady=2)
        from src.app.styles.luxury_2026 import add_placeholder
        add_placeholder(self.entry_date_from, "📅 YYYY-MM-DD")
        add_placeholder(self.entry_date_to,   "📅 YYYY-MM-DD")

        ttk.Button(filters, text="Filtrar", command=self._load_orders).grid(row=0, column=8, padx=4, pady=2)
        ttk.Button(filters, text="Limpiar", command=self._clear_filters).grid(row=0, column=9, padx=4, pady=2)

        # Botones de acción
        actions = tk.Frame(frame, bg=_BG_DARK)
        actions.pack(fill="x", pady=4)
        ttk.Button(actions, text="Nueva OC", command=self._new_order).pack(side="left", padx=4)
        ttk.Button(actions, text="Recibir", command=self._receive_order).pack(side="left", padx=4)
        ttk.Button(actions, text="Cancelar", command=self._cancel_order).pack(side="left", padx=4)
        ttk.Button(actions, text="Ver detalle", command=self._view_detail).pack(side="left", padx=4)
        ttk.Button(actions, text="📥 Excel", command=self._exportar_ordenes).pack(side="left", padx=4)

        # Tabla de órdenes
        columns = ("numero", "supplier", "fecha", "total", "estado")
        self.tree_orders = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        for col, label in zip(columns, ["Número", "Proveedor", "Fecha", "Total", "Estado"]):
            self.tree_orders.heading(col, text=label)
            self.tree_orders.column(col, width=150)
        self.tree_orders.pack(fill="both", expand=True, pady=8)
        self.tree_orders.bind("<Double-1>", self._on_order_double_click)

        # Colores por estado
        STATUS_COLORS = {
            "PENDIENTE":  "#F59E0B",  # amarillo — atención
            "PARCIAL":    "#3B82F6",  # azul — en progreso
            "RECIBIDA":   "#10B981",  # verde — completo
            "CANCELADA":  "#6B7280",  # gris — inactivo
        }
        for estado, color in STATUS_COLORS.items():
            self.tree_orders.tag_configure(estado, foreground=color)

    def _load_orders(self):
        supplier = self.var_supplier_filter.get() or None
        status = self.var_status_filter.get() or None
        orders = list_purchase_orders(supplier_code=supplier, estado=status)

        self.tree_orders.delete(*self.tree_orders.get_children())
        for order in orders:
            estado = order["estado"]
            self.tree_orders.insert("", "end", values=(
                order["numero"],
                order["supplier_name"],
                order["fecha"][:10],  # Solo fecha
                f"${order['total']:.2f}",
                estado
            ), tags=(estado,))

    def _clear_filters(self):
        self.var_supplier_filter.set("")
        self.var_status_filter.set("")
        self.var_date_from.set("")
        self.var_date_to.set("")
        self._load_orders()

    def _on_order_double_click(self, event):
        item = self.tree_orders.focus()
        if not item:
            return
        numero = self.tree_orders.item(item)["values"][0]
        # Buscar la orden por número
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM documents WHERE numero = ? AND tipo = 'PURCHASE_ORDER'", (numero,))
            row = cur.fetchone()
            if row:
                self.selected_order = get_purchase_order(row[0])
                self._view_detail()

    def _new_order(self):
        self.tabs.select(self.tab_nueva)
        if self.supplier_code:
            self.var_supplier_new.set(self.supplier_code)

    def _receive_order(self):
        item = self.tree_orders.focus()
        if not item:
            messagebox.showinfo("Órdenes", "Selecciona una orden para recibir.")
            return
        numero = self.tree_orders.item(item)["values"][0]
        # Buscar orden
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM documents WHERE numero = ? AND tipo = 'PURCHASE_ORDER'", (numero,))
            row = cur.fetchone()
            if row:
                self.selected_order = get_purchase_order(row[0])
                self.tabs.select(self.tab_recepcion)
                self._load_reception_order()

    def _cancel_order(self):
        item = self.tree_orders.focus()
        if not item:
            messagebox.showinfo("Órdenes", "Selecciona una orden para cancelar.")
            return
        numero = self.tree_orders.item(item)["values"][0]

        if not messagebox.askyesno("Confirmar", f"¿Cancelar orden {numero}?"):
            return

        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id FROM documents WHERE numero = ? AND tipo = 'PURCHASE_ORDER'", (numero,))
                row = cur.fetchone()
                if row:
                    cancel_order(row[0], self.user.get("id") if self.user else None)
                    messagebox.showinfo("Éxito", f"Orden {numero} cancelada.")
                    self._load_orders()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cancelar orden: {e}")

    def _view_detail(self):
        if not self.selected_order:
            item = self.tree_orders.focus()
            if not item:
                messagebox.showinfo("Órdenes", "Selecciona una orden.")
                return
            numero = self.tree_orders.item(item)["values"][0]
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id FROM documents WHERE numero = ? AND tipo = 'PURCHASE_ORDER'", (numero,))
                row = cur.fetchone()
                if row:
                    self.selected_order = get_purchase_order(row[0])

        if self.selected_order:
            detail = f"Orden: {self.selected_order['numero']}\n"
            detail += f"Proveedor: {self.selected_order['supplier_name']}\n"
            detail += f"Fecha: {self.selected_order['fecha']}\n"
            detail += f"Estado: {self.selected_order['estado']}\n"
            detail += f"Notas: {self.selected_order['notas']}\n\n"
            detail += "Ítems:\n"
            for item in self.selected_order["items"]:
                detail += f"  {item['codigo']} - {item['product_name']}: {item['qty']} x ${item['unit_price']:.2f}\n"
            messagebox.showinfo("Detalle de Orden", detail)

    # --- TAB 2: NUEVA ORDEN ---
    def _build_tab_nueva(self, frame):
        # Selección de proveedor
        prov_frame = tk.Frame(frame, bg=_BG_DARK)
        prov_frame.pack(fill="x", pady=10)
        tk.Label(prov_frame, text="Proveedor*:", bg=_BG_DARK, fg="white").grid(row=0, column=0, sticky="e", padx=4, pady=2)
        self.var_supplier_new = tk.StringVar()
        suppliers = [p["code"] for p in list_partners(kind="SUPPLIER")]
        self.cb_supplier_new = ttk.Combobox(prov_frame, textvariable=self.var_supplier_new, values=suppliers, width=30)
        self.cb_supplier_new.grid(row=0, column=1, sticky="w", padx=4, pady=2)

        tk.Label(prov_frame, text="Notas:", bg=_BG_DARK, fg="white").grid(row=1, column=0, sticky="e", padx=4, pady=2)
        self.var_notas_new = tk.StringVar()
        tk.Entry(prov_frame, textvariable=self.var_notas_new, width=50).grid(row=1, column=1, sticky="w", padx=4, pady=2)

        # Tabla de ítems
        items_frame = tk.LabelFrame(frame, text="Ítems de la orden", bg=_BG_DARK, fg="white")
        items_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Controles para agregar ítem
        add_frame = tk.Frame(items_frame, bg=_BG_DARK)
        add_frame.pack(fill="x", pady=5)
        tk.Label(add_frame, text="Código:", bg=_BG_DARK, fg="white").grid(row=0, column=0, padx=2)
        self.var_codigo_add = tk.StringVar()
        tk.Entry(add_frame, textvariable=self.var_codigo_add, width=15).grid(row=0, column=1, padx=2)

        tk.Label(add_frame, text="Cantidad:", bg=_BG_DARK, fg="white").grid(row=0, column=2, padx=2)
        self.var_qty_add = tk.StringVar()
        tk.Entry(add_frame, textvariable=self.var_qty_add, width=10).grid(row=0, column=3, padx=2)

        tk.Label(add_frame, text="Precio:", bg=_BG_DARK, fg="white").grid(row=0, column=4, padx=2)
        self.var_price_add = tk.StringVar()
        tk.Entry(add_frame, textvariable=self.var_price_add, width=10).grid(row=0, column=5, padx=2)

        ttk.Button(add_frame, text="Agregar ítem", command=self._add_item).grid(row=0, column=6, padx=4)
        ttk.Button(add_frame, text="Quitar ítem", command=self._remove_item).grid(row=0, column=7, padx=4)

        # Tabla de ítems
        columns = ("codigo", "nombre", "qty", "price", "total")
        self.tree_items = ttk.Treeview(items_frame, columns=columns, show="headings", height=10)
        for col, label in zip(columns, ["Código", "Producto", "Cantidad", "Precio", "Total"]):
            self.tree_items.heading(col, text=label)
            self.tree_items.column(col, width=120)
        self.tree_items.pack(fill="both", expand=True, pady=5)

        # Total y botón crear
        total_frame = tk.Frame(frame, bg=_BG_DARK)
        total_frame.pack(fill="x", pady=10)
        self.lbl_total_new = tk.Label(total_frame, text="Total: $0.00", bg=_BG_DARK, fg="white", font=("Arial", 12, "bold"))
        self.lbl_total_new.pack(side="right", padx=10)
        Tooltip(self.lbl_total_new, "Total calculado de la orden:\nΣ (cantidad × precio unitario)")
        ttk.Button(total_frame, text="Crear Orden de Compra", command=self._create_order).pack(side="right", padx=4)

    def _add_item(self):
        codigo = self.var_codigo_add.get().strip()
        qty_str = self.var_qty_add.get().strip()
        price_str = self.var_price_add.get().strip()

        if not codigo:
            messagebox.showerror("Error", "Ingresa el código del producto.")
            return

        try:
            qty = float(qty_str)
            price = float(price_str)
        except ValueError:
            messagebox.showerror("Error", "Cantidad y precio deben ser números.")
            return

        if qty <= 0 or price < 0:
            messagebox.showerror("Error", "Cantidad > 0 y precio >= 0.")
            return

        # Verificar producto existe
        product = get_product(codigo)
        if not product:
            messagebox.showerror("Error", f"Producto {codigo} no existe.")
            return

        # Agregar a lista
        self.order_items.append({
            "codigo": codigo,
            "nombre": product["nombre"],
            "qty": qty,
            "unit_price": price
        })

        self._refresh_items_table()
        self.var_codigo_add.set("")
        self.var_qty_add.set("")
        self.var_price_add.set("")

    def _remove_item(self):
        item = self.tree_items.focus()
        if not item:
            messagebox.showinfo("Nueva Orden", "Selecciona un ítem para quitar.")
            return

        codigo = self.tree_items.item(item)["values"][0]
        self.order_items = [i for i in self.order_items if i["codigo"] != codigo]
        self._refresh_items_table()

    def _refresh_items_table(self):
        self.tree_items.delete(*self.tree_items.get_children())
        total = 0.0
        for item in self.order_items:
            item_total = item["qty"] * item["unit_price"]
            total += item_total
            self.tree_items.insert("", "end", values=(
                item["codigo"],
                item["nombre"],
                item["qty"],
                f"${item['unit_price']:.2f}",
                f"${item_total:.2f}"
            ))
        self.lbl_total_new.config(text=f"Total: ${total:.2f}")

    def _create_order(self):
        supplier_code = self.var_supplier_new.get()
        if not supplier_code:
            messagebox.showerror("Error", "Selecciona un proveedor.")
            return

        if not self.order_items:
            messagebox.showerror("Error", "Agrega al menos un ítem.")
            return

        try:
            doc_id, numero = create_purchase_order(
                supplier_code=supplier_code,
                items=self.order_items,
                notas=self.var_notas_new.get(),
                user_id=self.user.get("id") if self.user else None
            )
            messagebox.showinfo("Éxito", f"Orden {numero} creada exitosamente.")
            self._clear_new_order()
            self.tabs.select(self.tab_ordenes)
            self._load_orders()
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear orden: {e}")

    def _clear_new_order(self):
        self.var_supplier_new.set("")
        self.var_notas_new.set("")
        self.order_items = []
        self._refresh_items_table()

    # --- TAB 3: RECEPCIÓN ---
    def _build_tab_recepcion(self, frame):
        # Buscar orden
        search_frame = tk.Frame(frame, bg=_BG_DARK)
        search_frame.pack(fill="x", pady=10)
        tk.Label(search_frame, text="Número OC:", bg=_BG_DARK, fg="white").grid(row=0, column=0, padx=4, pady=2, sticky="e")
        self.var_oc_search = tk.StringVar()
        self.entry_oc_search = tk.Entry(search_frame, textvariable=self.var_oc_search, width=20)
        self.entry_oc_search.grid(row=0, column=1, padx=4, pady=2)
        from src.app.styles.luxury_2026 import add_placeholder
        add_placeholder(self.entry_oc_search, "🔍 Número de orden (ej: OC-001)")
        ttk.Button(search_frame, text="Buscar", command=self._search_order).grid(row=0, column=2, padx=4, pady=2)

        # Info de la orden
        info_frame = tk.LabelFrame(frame, text="Información de la Orden", bg=_BG_DARK, fg="white")
        info_frame.pack(fill="x", padx=10, pady=5)
        self.lbl_order_info = tk.Label(info_frame, text="", bg=_BG_DARK, fg="white", justify="left")
        self.lbl_order_info.pack(anchor="w", padx=10, pady=5)
        Tooltip(self.lbl_order_info, "Detalle completo de la orden seleccionada:\nproveedor, fecha, estado y líneas de productos")

        # Tabla de recepción
        recv_frame = tk.LabelFrame(frame, text="Recepción de Ítems", bg=_BG_DARK, fg="white")
        recv_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("codigo", "producto", "ordenado", "recibido")
        self.tree_reception = ttk.Treeview(recv_frame, columns=columns, show="headings", height=10)
        for col, label in zip(columns, ["Código", "Producto", "Ordenado", "Recibido"]):
            self.tree_reception.heading(col, text=label)
            self.tree_reception.column(col, width=120)
        self.tree_reception.pack(fill="both", expand=True, pady=5)

        # Botón confirmar
        ttk.Button(frame, text="Confirmar Recepción", command=self._confirm_reception).pack(pady=10)

    def _search_order(self):
        numero = self.var_oc_search.get().strip()
        _PH = "🔍 Número de orden (ej: OC-001)"
        if not numero or numero == _PH:
            messagebox.showerror("Error", "Ingresa el número de la OC.")
            return

        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id FROM documents WHERE numero = ? AND tipo = 'PURCHASE_ORDER'", (numero,))
                row = cur.fetchone()
                if not row:
                    messagebox.showerror("Error", f"Orden {numero} no encontrada.")
                    return

                self.selected_order = get_purchase_order(row[0])
                self._load_reception_order()
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar orden: {e}")

    def _load_reception_order(self):
        if not self.selected_order:
            return

        # Mostrar info
        info = f"Número: {self.selected_order['numero']}\n"
        info += f"Proveedor: {self.selected_order['supplier_name']}\n"
        info += f"Fecha: {self.selected_order['fecha']}\n"
        info += f"Estado: {self.selected_order['estado']}"
        self.lbl_order_info.config(text=info)

        # Cargar ítems
        self.tree_reception.delete(*self.tree_reception.get_children())
        for item in self.selected_order["items"]:
            self.tree_reception.insert("", "end", values=(
                item["codigo"],
                item["product_name"],
                item["qty"],
                0  # Cantidad recibida inicial
            ))

    def _confirm_reception(self):
        if not self.selected_order:
            messagebox.showerror("Error", "Primero busca una orden.")
            return

        # Recopilar cantidades recibidas
        items_received = []
        for item_id in self.tree_reception.get_children():
            values = self.tree_reception.item(item_id)["values"]
            codigo = values[0]
            try:
                qty_received = float(values[3])
                if qty_received > 0:
                    items_received.append({
                        "codigo": codigo,
                        "qty_received": qty_received
                    })
            except (ValueError, IndexError):
                continue

        if not items_received:
            messagebox.showerror("Error", "Ingresa al menos una cantidad recibida.")
            return

        if not messagebox.askyesno("Confirmar", "¿Confirmar recepción de ítems?"):
            return

        try:
            receive_order(
                doc_id=self.selected_order["id"],
                items_received=items_received,
                user_id=self.user.get("id") if self.user else None
            )
            messagebox.showinfo("Éxito", "Recepción registrada exitosamente.")
            self.tabs.select(self.tab_ordenes)
            self._load_orders()
        except Exception as e:
            messagebox.showerror("Error", f"Error en recepción: {e}")

    def show(self):
        self.deiconify()
        self.wait_window()

    def _exportar_ordenes(self):
        from tkinter import filedialog, messagebox
        import openpyxl
        cols = ["Número", "Proveedor", "Fecha", "Total", "Estado"]
        filas = [self.tree_orders.item(i)["values"] for i in self.tree_orders.get_children()]
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
            initialfile="ordenes_compra.xlsx", title="Exportar Órdenes"
        )
        if not path:
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Ordenes"
        ws.append(cols)
        for f in filas:
            ws.append(list(f))
        wb.save(path)
        messagebox.showinfo("✅ Exportado", f"Archivo guardado:\n{path}")