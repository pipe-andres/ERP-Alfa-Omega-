import tkinter as tk
from tkinter import ttk, messagebox
from src.app.components_luxury import Tooltip
from datetime import datetime
import time

from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography
from src.services.partners import (
    list_partners, create_partner, update_partner, get_partner_by_code, set_partner_active
)
from src.database.connection import get_connection

_BG_DARK = getattr(Luxury2026Colors, "BG_DARKEST", "#0A0E27")
_BG_PANEL = getattr(Luxury2026Colors, "BG_SECONDARY", "#0D1117")
_ACCENT = getattr(Luxury2026Colors, "ACCENT", "#3B82F6")
_SUCCESS = getattr(Luxury2026Colors, "SUCCESS", "#10B981")
_WARNING = getattr(Luxury2026Colors, "WARNING", "#D97706")
_DANGER = getattr(Luxury2026Colors, "DANGER", "#DC2626")

from src.services.customer_segments import calcular_segmentos, get_resumen_segmentos

class CrmWindow(tk.Toplevel):
    """Gestión de clientes CRM."""

    def __init__(self, parent, user=None):
        super().__init__(parent)
        self.title("CRM de Clientes")
        self.geometry("1000x600")
        self.configure(bg=_BG_DARK)
        self.transient(parent)
        self.grab_set()
        self.user = user
        self.selected_partner = None
        self._build_ui()
        self._load_clients()

    def _build_ui(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)

        # Tab 1: Clientes
        self.tab_clientes = tk.Frame(self.tabs, bg=_BG_DARK)
        self.tabs.add(self.tab_clientes, text="Clientes")
        self._build_tab_clientes(self.tab_clientes)

        # Tab 2: Detalle
        self.tab_detalle = tk.Frame(self.tabs, bg=_BG_DARK)
        self.tabs.add(self.tab_detalle, text="Detalle")
        self._build_tab_detalle(self.tab_detalle)

        # Tab 3: Crédito
        self.tab_credito = tk.Frame(self.tabs, bg=_BG_DARK)
        self.tabs.add(self.tab_credito, text="Crédito")
        self._build_tab_credito(self.tab_credito)

        # Tab 4: Segmentación
        self.tab_segmentacion = tk.Frame(self.tabs, bg=_BG_DARK)
        self.tabs.add(self.tab_segmentacion, text="📊 Segmentación A/B/C")
        self._build_tab_segmentacion(self.tab_segmentacion)

    # --- TAB 1: CLIENTES ---
    def _build_tab_clientes(self, frame):
        top = tk.Frame(frame, bg=_BG_DARK)
        top.pack(fill="x", pady=8)
        tk.Label(top, text="Buscar:", bg=_BG_DARK, fg="white").pack(side="left")
        self.var_search = tk.StringVar()
        entry = tk.Entry(top, textvariable=self.var_search, width=50)
        entry.pack(side="left", padx=4)
        from src.app.styles.luxury_2026 import add_placeholder
        add_placeholder(entry, "🔍 Buscar por nombre, email o teléfono...")
        entry.bind("<KeyRelease>", lambda e: self._filter_clients())
        ttk.Button(top, text="Nuevo cliente", command=self._new_client).pack(side="right", padx=4)
        ttk.Button(top, text="Editar", command=self._edit_client).pack(side="right", padx=4)
        ttk.Button(top, text="Activar/Desactivar", command=self._toggle_active).pack(side="right", padx=4)
        ttk.Button(top, text="📥 Excel", command=self._exportar_clientes).pack(side="right", padx=4)

        columns = ("code", "name", "phone", "email", "city", "credit_limit", "credit_balance", "active")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=18)
        for col, label in zip(columns, ["Código", "Nombre", "Teléfono", "Email", "Ciudad", "Crédito límite", "Saldo crédito", "Estado"]):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=120 if col != "name" else 180)
        self.tree.pack(fill="both", expand=True, pady=8)
        self.tree.bind("<Double-1>", self._on_row_double_click)
        self.tree.tag_configure("activo",   foreground="#10B981")
        self.tree.tag_configure("inactivo", foreground="#6B7280")

    def _load_clients(self):
        self.clients = list_partners(kind="CUSTOMER")
        self.filtered_clients = self.clients
        self._refresh_tree()

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for c in self.filtered_clients:
            estado = "Activo" if c.get("active", 1) else "Inactivo"
            tag = "activo" if c.get("active", 1) else "inactivo"
            self.tree.insert("", "end", values=(
                c.get("code"), c.get("name"), c.get("phone"), c.get("email"),
                c.get("city"), c.get("credit_limit", 0.0), c.get("credit_balance", 0.0), estado
            ), tags=(tag,))

    def _filter_clients(self):
        q = self.var_search.get().strip().lower()
        if q == "🔍 buscar por nombre, email o teléfono...":
            q = ""
        if not q:
            self.filtered_clients = self.clients
        else:
            self.filtered_clients = [
                c for c in self.clients
                if q in (c.get("name") or "").lower()
                or q in (c.get("phone") or "").lower()
                or q in (c.get("code") or "").lower()
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

    def _new_client(self):
        self._open_client_form()

    def _edit_client(self):
        item = self.tree.focus()
        if not item:
            messagebox.showinfo("CRM", "Selecciona un cliente para editar.")
            return
        code = self.tree.item(item)["values"][0]
        partner = get_partner_by_code(code)
        self._open_client_form(partner)

    def _toggle_active(self):
        item = self.tree.focus()
        if not item:
            messagebox.showinfo("CRM", "Selecciona un cliente.")
            return
        code = self.tree.item(item)["values"][0]
        partner = get_partner_by_code(code)
        if not partner:
            return
        is_active = bool(partner[10])
        set_partner_active(code, not is_active)
        self._load_clients()

    # --- TAB 2: DETALLE ---
    def _build_tab_detalle(self, frame):
        self.detail_vars = {k: tk.StringVar() for k in [
            "name", "phone", "email", "address", "city", "tax_id", "notes"
        ]}
        form = tk.Frame(frame, bg=_BG_DARK)
        form.pack(fill="x", pady=10)
        row = 0
        for label, key in [
            ("Nombre*", "name"), ("Teléfono", "phone"), ("Email", "email"),
            ("Dirección", "address"), ("Ciudad", "city"), ("RUC/NIT", "tax_id"), ("Notas", "notes")
        ]:
            tk.Label(form, text=label, bg=_BG_DARK, fg="white").grid(row=row, column=0, sticky="e", pady=2, padx=4)
            tk.Entry(form, textvariable=self.detail_vars[key], width=40).grid(row=row, column=1, sticky="w", pady=2)
            row += 1

        ttk.Button(form, text="Guardar cambios", command=self._save_partner_detail).grid(row=row, column=1, sticky="e", pady=8)

        # Historial de compras
        hist_frame = tk.LabelFrame(frame, text="Historial de compras", bg=_BG_DARK, fg="white")
        hist_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("fecha", "numero", "total", "metodo")
        self.tree_hist = ttk.Treeview(hist_frame, columns=columns, show="headings", height=8)
        for col, label in zip(columns, ["Fecha", "Número", "Total", "Método pago"]):
            self.tree_hist.heading(col, text=label)
            self.tree_hist.column(col, width=120)
        self.tree_hist.pack(fill="both", expand=True, pady=4)
        self.lbl_total_hist = tk.Label(hist_frame, text="", bg=_BG_DARK, fg="white")
        self.lbl_total_hist.pack(anchor="w", padx=8, pady=2)
        Tooltip(self.lbl_total_hist, "Suma total de todas las compras\nrealizadas por este cliente")
        self.lbl_ult_compra = tk.Label(hist_frame, text="", bg=_BG_DARK, fg="white")
        self.lbl_ult_compra.pack(anchor="w", padx=8, pady=2)
        Tooltip(self.lbl_ult_compra, "Fecha de la última transacción\nregistrada para este cliente")
        self.lbl_ticket_prom = tk.Label(hist_frame, text="", bg=_BG_DARK, fg="white")
        self.lbl_ticket_prom.pack(anchor="w", padx=8, pady=2)
        Tooltip(self.lbl_ticket_prom, "Valor promedio por compra:\nTotal comprado / Número de transacciones")

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
        messagebox.showinfo("CRM", "Datos actualizados.")
        self._load_clients()

    def _load_historial_compras(self, partner_id):
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT d.fecha, d.numero, "
                "(SELECT SUM(dl.qty * dl.unit_price) FROM document_lines dl WHERE dl.doc_id = d.id) as total, "
                "d.payment_method "
                "FROM documents d WHERE d.tipo='SALE' AND d.partner_id=? "
                "ORDER BY d.fecha DESC LIMIT 20", (partner_id,)
            )
            rows = cur.fetchall()
            self.tree_hist.delete(*self.tree_hist.get_children())
            total_hist = 0.0
            fechas = []
            for r in rows:
                self.tree_hist.insert("", "end", values=(r[0], r[1], r[2], r[3]))
                total_hist += r[2] or 0.0
                fechas.append(r[0])
            self.lbl_total_hist.config(text=f"Total comprado: ${total_hist:.2f}")
            if fechas:
                self.lbl_ult_compra.config(text=f"Última compra: {fechas[0]}")
            else:
                self.lbl_ult_compra.config(text="Última compra: -")
            ticket_prom = (total_hist / len(rows)) if rows else 0.0
            self.lbl_ticket_prom.config(text=f"Ticket promedio: ${ticket_prom:.2f}")

    # --- TAB 3: CRÉDITO ---
    def _build_tab_credito(self, frame):
        self.var_credit_limit = tk.DoubleVar()
        self.var_credit_balance = tk.DoubleVar()
        self.lbl_alerta = tk.Label(frame, text="", bg=_BG_DARK, fg="white", font=("Arial", 12, "bold"))
        self.lbl_alerta.pack(pady=8)
        row = tk.Frame(frame, bg=_BG_DARK)
        row.pack(fill="x", pady=4)
        tk.Label(row, text="Límite de crédito:", bg=_BG_DARK, fg="white").pack(side="left")
        tk.Entry(row, textvariable=self.var_credit_limit, width=10).pack(side="left", padx=4)
        ttk.Button(row, text="Ajustar límite", command=self._ajustar_limite).pack(side="left", padx=4)
        row2 = tk.Frame(frame, bg=_BG_DARK)
        row2.pack(fill="x", pady=4)
        tk.Label(row2, text="Saldo actual:", bg=_BG_DARK, fg="white").pack(side="left")
        tk.Label(row2, textvariable=self.var_credit_balance, bg=_BG_DARK, fg="white").pack(side="left", padx=4)
        ttk.Button(row2, text="Registrar pago", command=self._registrar_pago).pack(side="left", padx=4)
        # Historial de movimientos
        hist = tk.LabelFrame(frame, text="Movimientos de crédito", bg=_BG_DARK, fg="white")
        hist.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("fecha", "tipo", "monto", "detalle")
        self.tree_credit_hist = ttk.Treeview(hist, columns=columns, show="headings", height=8)
        for col, label in zip(columns, ["Fecha", "Tipo", "Monto", "Detalle"]):
            self.tree_credit_hist.heading(col, text=label)
            self.tree_credit_hist.column(col, width=120)
        self.tree_credit_hist.pack(fill="both", expand=True, pady=4)

    def _load_credito(self):
        if not self.selected_partner:
            return
        code = self.selected_partner[1]
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT credit_limit, credit_balance FROM partners WHERE code=?", (code,))
            row = cur.fetchone()
            if row:
                self.var_credit_limit.set(row[0] or 0.0)
                self.var_credit_balance.set(row[1] or 0.0)
        self._load_credit_historial(code)
        self._update_credit_alerta()

    def _ajustar_limite(self):
        if not self.selected_partner:
            return
        code = self.selected_partner[1]
        new_limit = self.var_credit_limit.get()
        with get_connection() as conn:
            conn.execute("UPDATE partners SET credit_limit=? WHERE code=?", (new_limit, code))
            conn.commit()
        messagebox.showinfo("CRM", "Límite de crédito actualizado.")
        self._load_credito()
        self._load_clients()

    def _registrar_pago(self):
        if not self.selected_partner:
            return
        code = self.selected_partner[1]
        pago = tk.simpledialog.askfloat("Registrar pago", "Monto del pago:")
        if not pago or pago <= 0:
            return
        with get_connection() as conn:
            # Registrar movimiento de pago (tipo='PAGO')
            conn.execute(
                "INSERT INTO credit_movements (partner_code, fecha, tipo, monto, detalle) VALUES (?, ?, 'PAGO', ?, ?)",
                (code, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pago, "Pago registrado manualmente")
            )
            # Actualizar saldo
            conn.execute(
                "UPDATE partners SET credit_balance=credit_balance-? WHERE code=?",
                (pago, code)
            )
            conn.commit()
        messagebox.showinfo("CRM", "Pago registrado.")
        self._load_credito()
        self._load_clients()

    def _load_credit_historial(self, code):
        with get_connection() as conn:
            cur = conn.cursor()
            # Ventas a crédito
            cur.execute(
                "SELECT fecha, 'VENTA', monto, numero FROM credit_movements WHERE partner_code=? AND tipo='VENTA' ORDER BY fecha DESC LIMIT 20",
                (code,)
            )
            ventas = cur.fetchall()
            # Pagos
            cur.execute(
                "SELECT fecha, 'PAGO', monto, detalle FROM credit_movements WHERE partner_code=? AND tipo='PAGO' ORDER BY fecha DESC LIMIT 20",
                (code,)
            )
            pagos = cur.fetchall()
        self.tree_credit_hist.delete(*self.tree_credit_hist.get_children())
        for r in ventas + pagos:
            self.tree_credit_hist.insert("", "end", values=r)

    def _update_credit_alerta(self):
        limit = self.var_credit_limit.get()
        saldo = self.var_credit_balance.get()
        if limit <= 0:
            self.lbl_alerta.config(text="", bg=_BG_DARK)
            return
        ratio = saldo / limit if limit else 0
        if ratio >= 1.0:
            self.lbl_alerta.config(text="¡Límite de crédito alcanzado!", bg=_DANGER)
        elif ratio >= 0.8:
            self.lbl_alerta.config(text="Advertencia: saldo supera el 80% del límite", bg=_WARNING)
        else:
            self.lbl_alerta.config(text="", bg=_BG_DARK)

    # --- FORMULARIO NUEVO/EDITAR CLIENTE ---
    def _open_client_form(self, partner=None):
        win = tk.Toplevel(self)
        win.title("Nuevo cliente" if partner is None else "Editar cliente")
        win.geometry("400x400")
        win.configure(bg=_BG_DARK)
        vars = {k: tk.StringVar() for k in [
            "name", "phone", "email", "address", "city", "tax_id", "notes", "credit_limit"
        ]}
        row = 0
        for label, key in [
            ("Nombre*", "name"), ("Teléfono", "phone"), ("Email", "email"),
            ("Dirección", "address"), ("Ciudad", "city"), ("RUC/NIT", "tax_id"), ("Notas", "notes"),
            ("Límite de crédito", "credit_limit")
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
            # Cargar límite de crédito
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT credit_limit FROM partners WHERE code=?", (partner[1],))
                rowc = cur.fetchone()
                if rowc:
                    vars["credit_limit"].set(str(rowc[0] or "0.0"))
        def guardar():
            nombre = vars["name"].get().strip()
            if not nombre:
                messagebox.showerror("CRM", "El nombre es obligatorio.")
                return
            code = partner[1] if partner else f"CUST-{int(time.time())}"
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
                with get_connection() as conn:
                    conn.execute("UPDATE partners SET credit_limit=? WHERE code=?", (float(vars["credit_limit"].get() or 0.0), code))
                    conn.commit()
            else:
                create_partner(
                    code=code,
                    kind="CUSTOMER",
                    name=nombre,
                    tax_id=vars["tax_id"].get(),
                    phone=vars["phone"].get(),
                    email=vars["email"].get(),
                    address=vars["address"].get(),
                    city=vars["city"].get(),
                    notes=vars["notes"].get(),
                    active=True
                )
                with get_connection() as conn:
                    conn.execute("UPDATE partners SET credit_limit=? WHERE code=?", (float(vars["credit_limit"].get() or 0.0), code))
                    conn.commit()
            messagebox.showinfo("CRM", "Cliente guardado.")
            win.destroy()
            self._load_clients()
        ttk.Button(win, text="Guardar", command=guardar).grid(row=row, column=1, sticky="e", pady=8)
        ttk.Button(win, text="Cancelar", command=win.destroy).grid(row=row, column=0, sticky="w", pady=8)

    # --- TAB 4: SEGMENTACIÓN ---
    def _build_tab_segmentacion(self, frame):
        top = tk.Frame(frame, bg=_BG_DARK)
        top.pack(fill="x", pady=8, padx=10)
        ttk.Button(top, text="Actualizar segmentación", command=self._refresh_segmentation).pack(side="left")

        self.seg_container = tk.Frame(frame, bg=_BG_DARK)
        self.seg_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 3 columnas
        self.seg_container.columnconfigure(0, weight=1)
        self.seg_container.columnconfigure(1, weight=1)
        self.seg_container.columnconfigure(2, weight=1)
        self.seg_container.rowconfigure(0, weight=1)
        
        # Frame A
        self.frame_a = tk.Frame(self.seg_container, bg=_BG_PANEL, bd=1, relief="solid")
        self.frame_a.grid(row=0, column=0, sticky="nsew", padx=4)
        self.lbl_a = tk.Label(self.frame_a, text="Segmento A — 0 clientes", bg=_SUCCESS, fg="white", font=("Arial", 11, "bold"))
        self.lbl_a.pack(fill="x")
        self.tree_a = ttk.Treeview(self.frame_a, columns=("name", "total"), show="headings", height=15)
        self.tree_a.heading("name", text="Nombre")
        self.tree_a.heading("total", text="Total comprado")
        self.tree_a.column("name", anchor="w", width=120)
        self.tree_a.column("total", anchor="e", width=80)
        self.tree_a.pack(fill="both", expand=True, padx=4, pady=4)

        # Frame B
        self.frame_b = tk.Frame(self.seg_container, bg=_BG_PANEL, bd=1, relief="solid")
        self.frame_b.grid(row=0, column=1, sticky="nsew", padx=4)
        self.lbl_b = tk.Label(self.frame_b, text="Segmento B — 0 clientes", bg=_WARNING, fg="white", font=("Arial", 11, "bold"))
        self.lbl_b.pack(fill="x")
        self.tree_b = ttk.Treeview(self.frame_b, columns=("name", "total"), show="headings", height=15)
        self.tree_b.heading("name", text="Nombre")
        self.tree_b.heading("total", text="Total comprado")
        self.tree_b.column("name", anchor="w", width=120)
        self.tree_b.column("total", anchor="e", width=80)
        self.tree_b.pack(fill="both", expand=True, padx=4, pady=4)

        # Frame C
        self.frame_c = tk.Frame(self.seg_container, bg=_BG_PANEL, bd=1, relief="solid")
        self.frame_c.grid(row=0, column=2, sticky="nsew", padx=4)
        self.lbl_c = tk.Label(self.frame_c, text="Segmento C — 0 clientes", bg=_DANGER, fg="white", font=("Arial", 11, "bold"))
        self.lbl_c.pack(fill="x")
        self.tree_c = ttk.Treeview(self.frame_c, columns=("name", "total"), show="headings", height=15)
        self.tree_c.heading("name", text="Nombre")
        self.tree_c.heading("total", text="Total comprado")
        self.tree_c.column("name", anchor="w", width=120)
        self.tree_c.column("total", anchor="e", width=80)
        self.tree_c.pack(fill="both", expand=True, padx=4, pady=4)

        # Cargar datos iniciales
        self.after(100, self._refresh_segmentation)

    def _refresh_segmentation(self):
        try:
            data = calcular_segmentos()
            
            # Limpiar trees
            for tree in (self.tree_a, self.tree_b, self.tree_c):
                tree.delete(*tree.get_children())
                
            # A
            for c in data.get("A", []):
                self.tree_a.insert("", "end", values=(c["nombre"], f"${c['total']:,.2f}"))
            self.lbl_a.config(text=f"Segmento A — {data['resumen'].get('total_A', 0)} clientes")

            # B
            for c in data.get("B", []):
                self.tree_b.insert("", "end", values=(c["nombre"], f"${c['total']:,.2f}"))
            self.lbl_b.config(text=f"Segmento B — {data['resumen'].get('total_B', 0)} clientes")

            # C
            for c in data.get("C", []):
                self.tree_c.insert("", "end", values=(c["nombre"], f"${c['total']:,.2f}"))
            self.lbl_c.config(text=f"Segmento C — {data['resumen'].get('total_C', 0)} clientes")

        except Exception as e:
            import logging
            logging.warning(f"Error cargando segmentacion en UI: {e}")

    def show(self):
        self.deiconify()
        self.wait_window()

    def _exportar_clientes(self):
        from tkinter import filedialog, messagebox
        import openpyxl
        cols = ["Código", "Nombre", "Teléfono", "Email", "Ciudad", "Límite Crédito", "Saldo Crédito", "Estado"]
        filas = [self.tree.item(i)["values"] for i in self.tree.get_children()]
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
            initialfile="clientes.xlsx", title="Exportar Clientes"
        )
        if not path:
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Clientes"
        ws.append(cols)
        for f in filas:
            ws.append(list(f))
        wb.save(path)
        messagebox.showinfo("✅ Exportado", f"Archivo guardado:\n{path}")
