import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from src.services.pos_service import (
    get_current_session, open_cash_session, close_cash_session,
    register_cash_movement, get_session_summary, list_movements,
    get_session_history, get_session_detail, save_arqueo
)

# estilo/theme
from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography

_BG_DARK = getattr(Luxury2026Colors, "BG_DARKEST", "#0A0E27")
_BG_PANEL = getattr(Luxury2026Colors, "BG_SECONDARY", "#0D1117")
_ACCENT = getattr(Luxury2026Colors, "ACCENT", "#3B82F6")
_SUCCESS = getattr(Luxury2026Colors, "SUCCESS", "#16A34A")
_DANGER = getattr(Luxury2026Colors, "DANGER", "#DC2626")


class CashManagerWindow(tk.Toplevel):
    """Ventana independiente para control total de la caja de efectivo."""

    def __init__(self, parent, user: dict | None = None):
        super().__init__(parent)
        self.title("Control de Caja")
        self.geometry("900x700")
        self.configure(bg=_BG_DARK)
        self.transient(parent)
        self.grab_set()

        self.user = user
        self.session = get_current_session(user["id"]) if user else None

        # vars para paneles
        self.var_status = tk.StringVar()
        self.var_cashier = tk.StringVar()
        self.var_opened = tk.StringVar()
        self.var_opening_amount = tk.StringVar()

        self.mov_type = tk.StringVar(value="Ingreso")
        self.mov_amount = tk.DoubleVar(value=0.0)
        self.mov_description = tk.StringVar()

        self.arq_expected = tk.DoubleVar(value=0.0)
        self.arq_declared = tk.DoubleVar(value=0.0)
        self.arq_diff = tk.StringVar(value="0.00")

        # build ui
        self._build_ui()
        self._refresh_session_info()

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_control = ttk.Frame(nb)
        nb.add(self.tab_control, text="Control")
        self.tab_history = ttk.Frame(nb)
        nb.add(self.tab_history, text="Historial")

        self._build_control_tab(self.tab_control)
        self._build_history_tab(self.tab_history)

    # ---------- panel control ---------------------------------------------
    def _build_control_tab(self, parent: ttk.Frame):
        # Panel 1: Estado
        frame1 = tk.Frame(parent, bg=_BG_PANEL, bd=1, relief="solid", padx=12, pady=12)
        frame1.pack(fill="x", pady=(0, 10))

        tk.Label(frame1, text="Estado de Sesión", font=("Arial", 14, "bold"),
                 bg=_BG_PANEL, fg=_ACCENT).grid(row=0, column=0, columnspan=2, sticky="w")

        tk.Label(frame1, text="Cajero:", bg=_BG_PANEL, fg="white").grid(row=1, column=0, sticky="w")
        tk.Label(frame1, textvariable=self.var_cashier, bg=_BG_PANEL, fg="white").grid(row=1, column=1, sticky="w")

        tk.Label(frame1, text="Apertura:", bg=_BG_PANEL, fg="white").grid(row=2, column=0, sticky="w")
        tk.Label(frame1, textvariable=self.var_opened, bg=_BG_PANEL, fg="white").grid(row=2, column=1, sticky="w")

        tk.Label(frame1, text="Monto inicial:", bg=_BG_PANEL, fg="white").grid(row=3, column=0, sticky="w")
        tk.Label(frame1, textvariable=self.var_opening_amount, bg=_BG_PANEL, fg="white").grid(row=3, column=1, sticky="w")

        tk.Label(frame1, textvariable=self.var_status, bg=_BG_PANEL, fg=_SUCCESS).grid(row=0, column=2, padx=20)

        btn_frame = tk.Frame(frame1, bg=_BG_PANEL)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=(10,0))
        tk.Button(btn_frame, text="Abrir sesión", command=self._open_session).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Cerrar sesión", command=self._close_session).pack(side="left", padx=4)

        # Panel 2: Movimientos manuales
        frame2 = tk.Frame(parent, bg=_BG_PANEL, bd=1, relief="solid", padx=12, pady=12)
        frame2.pack(fill="x", pady=(0, 10))
        tk.Label(frame2, text="Movimientos Manuales", font=("Arial", 12, "bold"), bg=_BG_PANEL, fg=_ACCENT).grid(row=0, columnspan=4, sticky="w")
        tk.Label(frame2, text="Tipo:", bg=_BG_PANEL, fg="white").grid(row=1, column=0, sticky="w")
        tipos = ["Ingreso", "Gasto", "Retiro"]
        ttk.Combobox(frame2, textvariable=self.mov_type, values=tipos, state="readonly", width=12).grid(row=1, column=1, sticky="w")
        tk.Label(frame2, text="Monto:", bg=_BG_PANEL, fg="white").grid(row=1, column=2, sticky="w")
        ttk.Entry(frame2, textvariable=self.mov_amount, width=12).grid(row=1, column=3, sticky="w")
        tk.Label(frame2, text="Descripción:", bg=_BG_PANEL, fg="white").grid(row=2, column=0, sticky="w", pady=(4,0))
        ttk.Entry(frame2, textvariable=self.mov_description, width=40).grid(row=2, column=1, columnspan=3, sticky="w", pady=(4,0))
        tk.Button(frame2, text="Registrar movimiento", command=self._register_movement).grid(row=3, column=0, columnspan=4, pady=(8,0))

        # tabla de movimientos
        cols = ("Tipo","Monto","Nota","Hora")
        self.tree_mov = ttk.Treeview(frame2, columns=cols, show="headings", height=5)
        for c in cols:
            self.tree_mov.heading(c, text=c)
            self.tree_mov.column(c, width=100)
        self.tree_mov.grid(row=4, column=0, columnspan=4, pady=(8,0))
        self.tree_mov.tag_configure("sale",       foreground="#10B981")  # ingreso — verde
        self.tree_mov.tag_configure("income",     foreground="#10B981")
        self.tree_mov.tag_configure("expense",    foreground="#EF4444")  # gasto — rojo
        self.tree_mov.tag_configure("withdrawal", foreground="#F59E0B")  # retiro — amarillo
        self.tree_mov.tag_configure("opening",    foreground="#3B82F6")  # apertura — azul
        self.tree_mov.tag_configure("closing",    foreground="#F59E0B")  # cierre — amarillo

        # Panel 3: Arqueo
        frame3 = tk.Frame(parent, bg=_BG_PANEL, bd=1, relief="solid", padx=12, pady=12)
        frame3.pack(fill="x", pady=(0, 10))
        tk.Label(frame3, text="Arqueo", font=("Arial", 12, "bold"), bg=_BG_PANEL, fg=_ACCENT).grid(row=0, columnspan=4, sticky="w")
        tk.Label(frame3, text="Esperado:", bg=_BG_PANEL, fg="white").grid(row=1, column=0, sticky="w")
        tk.Label(frame3, textvariable=self.arq_expected, bg=_BG_PANEL, fg="white").grid(row=1, column=1, sticky="w")
        tk.Label(frame3, text="Declarado:", bg=_BG_PANEL, fg="white").grid(row=1, column=2, sticky="w")
        ent_decl = ttk.Entry(frame3, textvariable=self.arq_declared, width=12)
        ent_decl.grid(row=1, column=3, sticky="w")
        self.arq_declared.trace_add("write", self._update_diff)
        tk.Label(frame3, text="Diferencia:", bg=_BG_PANEL, fg="white").grid(row=2, column=0, sticky="w")
        self.lbl_diff = tk.Label(frame3, textvariable=self.arq_diff, bg=_BG_PANEL, fg="white")
        self.lbl_diff.grid(row=2, column=1, sticky="w")
        tk.Button(frame3, text="Guardar arqueo", command=self._save_arqueo).grid(row=3, column=0, columnspan=4, pady=(8,0))

    # ---------- historial tab ---------------------------------------------
    def _build_history_tab(self, parent: ttk.Frame):
        filter_frame = tk.Frame(parent, bg=_BG_PANEL, padx=12, pady=8)
        filter_frame.pack(fill="x")
        tk.Label(filter_frame, text="Desde (YYYY-MM-DD):", bg=_BG_PANEL, fg="white").pack(side="left")
        self.var_from = tk.StringVar()
        tk.Entry(filter_frame, textvariable=self.var_from, width=12).pack(side="left", padx=4)
        tk.Label(filter_frame, text="Hasta:", bg=_BG_PANEL, fg="white").pack(side="left", padx=(12,0))
        self.var_to = tk.StringVar()
        tk.Entry(filter_frame, textvariable=self.var_to, width=12).pack(side="left", padx=4)
        tk.Button(filter_frame, text="Filtrar", command=self._filter_history).pack(side="left", padx=8)

        cols = ("ID","Fecha","Cajero","Inicio","Ventas","Egresos","Diferencia","Estado")
        self.tree_hist = ttk.Treeview(parent, columns=cols, show="headings", height=10)
        for c in cols:
            self.tree_hist.heading(c, text=c)
            self.tree_hist.column(c, width=100)
        self.tree_hist.pack(fill="both", expand=True, padx=12, pady=8)
        self.tree_hist.bind("<Double-1>", self._on_history_select)

    # ---------- helpers --------------------------------------------------
    def _refresh_session_info(self):
        if self.session:
            self.var_cashier.set(str(self.user.get("name", "?")))
            self.var_opened.set(self.session.get("opened_at", ""))
            self.var_opening_amount.set(f"{self.session.get('opening_amount',0):.2f}")
            self.var_status.set("● ABIERTA")
            self.var_status.set("● ABIERTA")
            self.var_status_label_color = _SUCCESS
            self._refresh_movements_table()
            summ = get_session_summary(self.session["id"])
            self.arq_expected.set(round(summ.get("expected_closing",0),2))
            self.arq_diff.set("0.00")
        else:
            self.var_cashier.set("-")
            self.var_opened.set("-")
            self.var_opening_amount.set("0.00")
            self.var_status.set("● CERRADA")
            self.arq_expected.set(0.0)
            self.arq_declared.set(0.0)
            self.arq_diff.set("0.00")
            self.tree_mov.delete(*self.tree_mov.get_children())

    def _open_session(self):
        if self.session:
            messagebox.showinfo("Caja", "Ya hay una sesión abierta.")
            return
        from tkinter.simpledialog import askfloat
        monto = askfloat("Apertura de Caja", "Monto inicial:", minvalue=0.0, parent=self)
        if monto is None:
            return
        try:
            sid = open_cash_session(self.user["id"], monto)
            self.session = get_current_session(self.user["id"])
            self._refresh_session_info()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _close_session(self):
        if not self.session:
            messagebox.showinfo("Caja", "No hay sesión abierta.")
            return
        resp = messagebox.askyesno("Cerrar", "¿Desea cerrar la sesión?")
        if not resp:
            return
        try:
            amount = float(self.arq_declared.get()) if self.arq_declared.get() else 0.0
            close_cash_session(self.session["id"], amount)
            self.session = None
            messagebox.showinfo("Caja", "Sesión cerrada.")
            self._refresh_session_info()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _refresh_movements_table(self):
        self.tree_mov.delete(*self.tree_mov.get_children())
        if not self.session:
            return
        for m in list_movements(self.session["id"]):
            self.tree_mov.insert("", "end", values=(
                m["type"], f"{m['amount']:.2f}", m["description"], m["created_at"]
            ), tags=(m["type"],))

    def _register_movement(self):
        if not self.session:
            messagebox.showerror("Error", "No hay sesión abierta")
            return
        mov = self.mov_type.get().lower()
        mapping = {"ingreso":"sale", "gasto":"expense", "retiro":"withdrawal"}
        mov_type = mapping.get(mov)
        try:
            amount = float(self.mov_amount.get())
        except Exception:
            messagebox.showerror("Error","Monto inválido")
            return
        description = self.mov_description.get()
        try:
            register_cash_movement(self.session["id"], mov_type, amount, description)
            self.mov_amount.set(0.0)
            self.mov_description.set("")
            self._refresh_movements_table()
            # update expected
            summ = get_session_summary(self.session["id"])
            self.arq_expected.set(round(summ.get("expected_closing",0),2))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _update_diff(self, *args):
        try:
            expected = self.arq_expected.get()
            declared = self.arq_declared.get()
            diff = declared - expected
            self.arq_diff.set(f"{diff:.2f}")
            self.lbl_diff.config(fg=_SUCCESS if abs(diff) < 0.001 else _DANGER)
        except Exception:
            self.arq_diff.set("---")

    def _save_arqueo(self):
        if not self.session:
            return
        try:
            save_arqueo(self.session["id"], self.arq_declared.get(), notes="manual")
            messagebox.showinfo("Arqueo", "Arqueo guardado.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _filter_history(self):
        frm = self.var_from.get().strip()
        to = self.var_to.get().strip()
        hist = get_session_history(from_date=frm or None, to_date=to or None)
        self.tree_hist.delete(*self.tree_hist.get_children())
        for h in hist:
            self.tree_hist.insert("", "end", values=(
                h["session_id"], h.get("opened_at"), h.get("user_id"),
                f"{h.get('opening',0):.2f}", f"{h.get('sales',0):.2f}",
                f"{h.get('expenses',0):.2f}", f"{h.get('arqueo_declared',0):.2f}",
                h.get("estado", ""),
            ))

    def _on_history_select(self, event):
        sel = self.tree_hist.selection()
        if not sel:
            return
        sid = self.tree_hist.item(sel[0])["values"][0]
        details = get_session_detail(sid)
        lines = "\n".join(f"{m['created_at']} {m['type']} {m['amount']} {m['description']}" for m in details)
        messagebox.showinfo("Detalle sesión", lines or "sin movimientos")
