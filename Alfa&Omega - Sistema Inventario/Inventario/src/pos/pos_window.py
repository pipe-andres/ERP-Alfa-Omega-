import tkinter as tk
from tkinter import ttk, messagebox
import datetime

from src.services.inventory import get_product, post_sale
from src.services.pos_service import (
    get_current_session, open_cash_session, close_cash_session,
    register_cash_movement, get_session_summary
)
# FIX 1: import correcto del tema real del proyecto
from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography

# FIX 2: alias para colores que no existen en Luxury2026Colors
_BG_PANEL = getattr(Luxury2026Colors, "BG_SECONDARY",  "#0D1117")
_BG_DARK  = getattr(Luxury2026Colors, "BG_DARKEST",    "#0A0E27")
_ACCENT   = getattr(Luxury2026Colors, "PRIMARY",        "#3B82F6")
_TXT_SEC  = getattr(Luxury2026Colors, "TEXT_SECONDARY", "#94A3B8")
_SUCCESS  = getattr(Luxury2026Colors, "SUCCESS",        "#16A34A")
_DANGER   = getattr(Luxury2026Colors, "DANGER",         "#DC2626")
_WARNING  = getattr(Luxury2026Colors, "WARNING",        "#D97706")


# ─────────────────────────────────────────────────────────────────────────────
# Dialog: Cobro
# ─────────────────────────────────────────────────────────────────────────────
class CheckoutDialog(tk.Toplevel):
    def __init__(self, parent, total, on_confirm):
        super().__init__(parent)
        self.title("Cobrar Venta")
        self.geometry("420x520")
        self.configure(bg=_BG_DARK)
        self.transient(parent)
        self.grab_set()

        self.total          = total
        self.on_confirm     = on_confirm
        self.payment_method = tk.StringVar(value="efectivo")
        self.amount_paid    = tk.DoubleVar(value=self.total)
        self.clients_list   = []

        self._build_ui()
        self.focus_amount()

    def _build_ui(self):
        main = tk.Frame(self, bg=_BG_DARK, padx=20, pady=20)
        main.pack(fill="both", expand=True)

        tk.Label(main, text=f"Total a Pagar: ${self.total:.2f}",
                 font=("Arial", 24, "bold"), bg=_BG_DARK, fg=_ACCENT).pack(pady=(0, 20))

        tk.Label(main, text="Metodo de Pago:", bg=_BG_DARK, fg="white").pack(anchor="w")
        for text, val in [("Efectivo","efectivo"),("Tarjeta","tarjeta"),
                          ("Transferencia","transferencia"),("Credito","credito")]:
            tk.Radiobutton(main, text=text, variable=self.payment_method, value=val,
                           bg=_BG_DARK, fg="white", selectcolor=_BG_PANEL,
                           command=self._on_method_change).pack(anchor="w")

        # Frame efectivo
        self.frame_efectivo = tk.Frame(main, bg=_BG_DARK)
        tk.Label(self.frame_efectivo, text="Paga con:", bg=_BG_DARK, fg="white").pack(side="left")
        self.entry_monto = ttk.Entry(self.frame_efectivo, textvariable=self.amount_paid,
                                     font=("Arial", 16))
        self.entry_monto.pack(side="right", fill="x", expand=True, padx=(10, 0))
        self.amount_paid.trace_add("write", self._calc_change)

        self.lbl_vuelto = tk.Label(main, text="Vuelto: $0.00",
                                   font=("Arial", 16, "bold"), bg=_BG_DARK, fg=_SUCCESS)
        self.lbl_vuelto.pack(pady=5)

        # Frame credito
        self.frame_credito = tk.Frame(main, bg=_BG_DARK)
        tk.Label(self.frame_credito, text="Cliente:", bg=_BG_DARK, fg="white").pack(anchor="w")
        self.combo_clientes = ttk.Combobox(self.frame_credito, state="readonly")
        self.combo_clientes.pack(fill="x")
        self._load_clients()

        # Botones
        btn_frame = tk.Frame(main, bg=_BG_DARK)
        btn_frame.pack(fill="x", side="bottom", pady=20)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(btn_frame, text="CONFIRMAR PAGO", command=self._confirm).pack(side="right", expand=True, fill="x", padx=5)

        self._on_method_change()

    def focus_amount(self):
        self.entry_monto.focus_set()
        self.entry_monto.select_range(0, tk.END)

    def _load_clients(self):
        try:
            # Usar solo partners con kind='CUSTOMER'
            from src.database.connection import get_connection
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, code, name, phone FROM partners WHERE kind='CUSTOMER' AND active=1 ORDER BY name ASC")
                rows = cur.fetchall()
                self.clients_list = [
                    {"id": r[0], "code": r[1], "nombre": r[2], "telefono": r[3]}
                    for r in rows
                ]
                self.combo_clientes["values"] = [f"{c['id']} - {c['nombre']}" for c in self.clients_list]
        except Exception:
            self.clients_list = []

    def _on_method_change(self):
        m = self.payment_method.get()
        if m == "efectivo":
            self.frame_efectivo.pack(fill="x", pady=10)
            self.lbl_vuelto.pack(pady=5)
            self.frame_credito.pack_forget()
        elif m == "credito":
            self.frame_efectivo.pack_forget()
            self.lbl_vuelto.pack_forget()
            self.frame_credito.pack(fill="x", pady=10)
        else:
            self.frame_efectivo.pack_forget()
            self.lbl_vuelto.pack_forget()
            self.frame_credito.pack_forget()

    def _calc_change(self, *args):
        try:
            change = self.amount_paid.get() - self.total
            if change >= 0:
                self.lbl_vuelto.config(text=f"Vuelto: ${change:.2f}", fg=_SUCCESS)
            else:
                self.lbl_vuelto.config(text=f"Faltan: ${abs(change):.2f}", fg=_DANGER)
        except (ValueError, tk.TclError):
            self.lbl_vuelto.config(text="Vuelto: ---", fg="white")

    def _confirm(self):
        m      = self.payment_method.get()
        paid   = self.total
        change = 0.0
        client_id = None

        if m == "efectivo":
            try:
                paid = float(self.amount_paid.get())
            except (ValueError, tk.TclError):
                messagebox.showerror("Error", "Monto de pago invalido.")
                return
            if paid < self.total:
                messagebox.showerror("Error", "El monto pagado es insuficiente.")
                return
            change = paid - self.total
        elif m == "credito":
            sel = self.combo_clientes.get()
            if not sel:
                messagebox.showerror("Error", "Debe seleccionar un cliente para ventas a credito.")
                return
            try:
                client_id = int(sel.split(" - ")[0])
            except (ValueError, IndexError):
                messagebox.showerror("Error", "Cliente invalido.")
                return

        self.on_confirm(m, paid, change, client_id)
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Dialog: Cierre de caja
# ─────────────────────────────────────────────────────────────────────────────
class CloseSessionDialog(tk.Toplevel):
    def __init__(self, parent, session: dict, on_closed):
        super().__init__(parent)
        self.title("Cierre de Caja")
        self.geometry("460x420")
        self.configure(bg=_BG_DARK)
        self.transient(parent)
        self.grab_set()
        self.session   = session
        self.on_closed = on_closed
        self._build_ui()

    def _build_ui(self):
        main = tk.Frame(self, bg=_BG_DARK, padx=24, pady=20)
        main.pack(fill="both", expand=True)

        tk.Label(main, text="Cierre de Caja", font=("Arial", 18, "bold"),
                 bg=_BG_DARK, fg=_ACCENT).pack(anchor="w", pady=(0, 16))

        try:
            summary = get_session_summary(self.session["id"])
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.destroy()
            return

        rows = [
            ("Apertura",         f"${summary['opening']:.2f}"),
            ("Ventas en efectivo",f"${summary['sales']:.2f}"),
            ("Gastos",           f"${summary['expenses']:.2f}"),
            ("Retiros",          f"${summary['withdrawals']:.2f}"),
            ("Esperado en caja", f"${summary['expected_closing']:.2f}"),
        ]
        for label, val in rows:
            row = tk.Frame(main, bg=_BG_DARK)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, bg=_BG_DARK, fg=_TXT_SEC,
                     font=("Arial", 11)).pack(side="left")
            tk.Label(row, text=val, bg=_BG_DARK, fg="white",
                     font=("Arial", 11, "bold")).pack(side="right")

        tk.Label(main, text="Monto real en caja:", bg=_BG_DARK, fg="white",
                 font=("Arial", 12)).pack(anchor="w", pady=(16, 4))
        self.var_closing = tk.DoubleVar(value=round(summary["expected_closing"], 2))
        ttk.Entry(main, textvariable=self.var_closing, font=("Arial", 14)).pack(fill="x")

        btn_frame = tk.Frame(main, bg=_BG_DARK)
        btn_frame.pack(fill="x", pady=(20, 0))
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cerrar Caja", command=self._do_close).pack(side="right", padx=4)

    def _do_close(self):
        try:
            amount = float(self.var_closing.get())
        except (ValueError, tk.TclError):
            messagebox.showerror("Error", "Monto invalido.")
            return
        try:
            summary = close_cash_session(self.session["id"], amount)
            diff = summary.get("difference", 0.0) or 0.0
            diff_txt = f"Sobrante: ${diff:.2f}" if diff >= 0 else f"Faltante: ${abs(diff):.2f}"
            messagebox.showinfo("Caja cerrada",
                f"Sesion cerrada correctamente.\n"
                f"Esperado: ${summary['expected_closing']:.2f}\n"
                f"Real: ${amount:.2f}\n"
                f"{diff_txt}")
            self.on_closed()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Ventana principal POS
# ─────────────────────────────────────────────────────────────────────────────
class POSWindow(tk.Toplevel):
    def __init__(self, parent, user: dict):
        super().__init__(parent)
        self.title("Punto de Venta (POS) - Alfa & Omega")
        self.geometry("1100x720")
        self.state("zoomed")
        self.configure(bg=_BG_DARK)
        self.user  = user
        self.cart  = {}   # codigo -> {nombre, precio, qty, stock_disp}
        self.total = 0.0

        # Sesion de caja
        self.session = get_current_session(user["id"])
        if not self.session:
            self._prompt_open_session()

        self._build_ui()

        # FIX 3: bind en self (Toplevel), no en self.root (inexistente)
        self.bind("<Return>", lambda e: self._on_barcode_scan())
        self.bind("<F12>",    lambda e: self._checkout())
        self.bind("<F10>",    lambda e: self._close_session_dialog())
        self.bind("<F11>",    lambda e: self._open_returns_window())

    def _prompt_open_session(self):
        from tkinter.simpledialog import askfloat
        monto = askfloat("Apertura de Caja",
                         "Ingrese monto inicial en caja (Efectivo):",
                         minvalue=0.0, initialvalue=0.0, parent=self)
        if monto is not None:
            try:
                open_cash_session(self.user["id"], monto)
                self.session = get_current_session(self.user["id"])
            except Exception as e:
                messagebox.showerror("Caja", str(e))
        else:
            messagebox.showwarning("Caja",
                "POS funciona sin caja abierta pero las ventas en efectivo "
                "no se registraran en el arqueo.")

    def _open_returns_window(self):
        """Launch the returns dialog from POS."""
        try:
            from src.app.returns_window import ReturnsWindow
            ReturnsWindow(self)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la ventana de devoluciones: {e}")

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=_BG_PANEL, height=56)
        header.pack(fill="x")
        header.propagate(False)

        tk.Label(header, text="PUNTO DE VENTA",
                 font=("Arial", 16, "bold"), bg=_BG_PANEL, fg="white"
                 ).pack(side="left", padx=20, pady=14)

        estado_txt  = "Caja Abierta" if self.session else "Sin Caja"
        estado_col  = _SUCCESS if self.session else _WARNING
        tk.Label(header, text=f"{estado_txt}  |  {self.user['name']}",
                 font=("Arial", 11), bg=_BG_PANEL, fg=estado_col
                 ).pack(side="right", padx=20)

        if self.session:
            tk.Button(header, text="Cerrar Caja [F10]", font=("Arial", 10),
                      bg=_DANGER, fg="white", bd=0, padx=8,
                      command=self._close_session_dialog
                      ).pack(side="right", padx=8, pady=10)
            # nuevo botón para iniciar devolución
            tk.Button(header, text="Devolución [F11]", font=("Arial", 10),
                      bg=_ACCENT, fg="white", bd=0, padx=8,
                      command=self._open_returns_window
                      ).pack(side="right", padx=8, pady=10)

        # ── Content ───────────────────────────────────────────────────────────
        content = tk.Frame(self, bg=_BG_DARK)
        content.pack(fill="both", expand=True, padx=16, pady=12)

        # Panel izquierdo: scanner + tabla carrito
        left = tk.Frame(content, bg=_BG_DARK)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        scan_frame = tk.Frame(left, bg=_BG_PANEL, padx=10, pady=8)
        scan_frame.pack(fill="x", pady=(0, 8))
        tk.Label(scan_frame, text="Codigo de barras / SKU:",
                 bg=_BG_PANEL, fg="white", font=("Arial", 13)).pack(side="left")
        self.var_barcode   = tk.StringVar()
        self.entry_barcode = ttk.Entry(scan_frame, textvariable=self.var_barcode,
                                       font=("Arial", 18))
        self.entry_barcode.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.entry_barcode.focus_set()
        self.entry_barcode.bind("<Return>", lambda e: self._on_barcode_scan())

        cols = ("Cant", "Codigo", "Descripcion", "P.Unit", "Subtotal")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=18)
        widths = {"Cant": 55, "Codigo": 110, "Descripcion": 280, "P.Unit": 110, "Subtotal": 110}
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col],
                             anchor="center" if col == "Cant" else "e" if col in ("P.Unit","Subtotal") else "w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Delete>", self._remove_selected)
        self.tree.bind("<Double-1>", self._edit_qty)

        # Panel derecho: total + botones
        right = tk.Frame(content, bg=_BG_PANEL, width=280, padx=20, pady=20)
        right.pack(side="right", fill="y")
        right.propagate(False)

        tk.Label(right, text="Total", font=("Arial", 14),
                 bg=_BG_PANEL, fg=_TXT_SEC).pack(anchor="w")
        self.lbl_total = tk.Label(right, text="$0.00", font=("Arial", 44, "bold"),
                                   bg=_BG_PANEL, fg=_ACCENT)
        self.lbl_total.pack(anchor="w", pady=(0, 24))

        tk.Button(right, text="COBRAR  [F12]", font=("Arial", 15, "bold"),
                  bg=_SUCCESS, fg="white", height=3, bd=0,
                  command=self._checkout).pack(fill="x", pady=(0, 8))
        ttk.Button(right, text="Limpiar venta",
                   command=self._clear_cart).pack(fill="x", pady=4)

        tk.Label(right, bg=_BG_PANEL, fg=_TXT_SEC, justify="left",
                 text="\n[Enter]  Agregar producto\n[Supr]   Quitar seleccionado\n[Doble-clic] Editar cantidad\n[F12]    Cobrar\n[F10]    Cerrar caja"
                 ).pack(side="bottom", anchor="sw")

    # ── Logica del carrito ────────────────────────────────────────────────────
    def _on_barcode_scan(self):
        codigo = self.var_barcode.get().strip()
        if not codigo:
            return

        prod = get_product(codigo)
        if not prod:
            messagebox.showwarning("No encontrado", f"Producto '{codigo}' no encontrado.")
            self.entry_barcode.select_range(0, tk.END)
            return

        # FIX 4: get_product puede retornar dict o tupla — manejar ambos
        if isinstance(prod, dict):
            p_cod    = prod.get("codigo", codigo)
            p_nom    = prod.get("nombre", "")
            p_precio = float(prod.get("precio", 0))
            stock    = int(prod.get("cantidad", 0))
        else:
            p_cod    = prod[0]
            p_nom    = prod[1]
            p_precio = float(prod[3])
            stock    = int(prod[4])

        if p_cod in self.cart:
            if self.cart[p_cod]["qty"] >= stock:
                messagebox.showwarning("Stock", f"Stock insuficiente para '{p_nom}'.")
                return
            self.cart[p_cod]["qty"] += 1
        else:
            if stock <= 0:
                messagebox.showwarning("Stock", f"Stock agotado para '{p_nom}'.")
                return
            self.cart[p_cod] = {"nombre": p_nom, "precio": p_precio,
                                  "qty": 1, "stock_disp": stock}

        self.var_barcode.set("")
        self._refresh_cart()

    def _remove_selected(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        cod = self.tree.item(sel[0])["values"][1]
        if cod in self.cart:
            del self.cart[cod]
            self._refresh_cart()

    def _edit_qty(self, event=None):
        """Doble-clic sobre una fila para editar la cantidad."""
        sel = self.tree.selection()
        if not sel:
            return
        cod  = self.tree.item(sel[0])["values"][1]
        item = self.cart.get(cod)
        if not item:
            return
        from tkinter.simpledialog import askinteger
        nueva = askinteger("Cantidad", f"Nueva cantidad para '{item['nombre']}':",
                           minvalue=1, maxvalue=item["stock_disp"],
                           initialvalue=item["qty"], parent=self)
        if nueva is not None:
            self.cart[cod]["qty"] = nueva
            self._refresh_cart()

    def _refresh_cart(self):
        self.tree.delete(*self.tree.get_children())
        total = 0.0
        for cod, data in self.cart.items():
            subt = data["qty"] * data["precio"]
            total += subt
            self.tree.insert("", "end", values=(
                data["qty"], cod, data["nombre"],
                f"${data['precio']:.2f}", f"${subt:.2f}"
            ))
        self.total = total
        self.lbl_total.config(text=f"${total:.2f}")

    def _clear_cart(self):
        self.cart.clear()
        self._refresh_cart()
        self.entry_barcode.focus_set()

    # ── Cobro ─────────────────────────────────────────────────────────────────
    def _checkout(self):
        if not self.cart:
            messagebox.showinfo("POS", "El carrito esta vacio.")
            self.entry_barcode.focus_set()
            return
        CheckoutDialog(self, self.total, self._process_sale)

    def _process_sale(self, payment_method, amount_paid, change, client_id):
        items = [
            {"codigo": c, "qty": d["qty"], "unit_price": d["precio"], "nombre": d["nombre"]}
            for c, d in self.cart.items()
        ]
        # Nuevo: obtener el code del cliente seleccionado
        selected = self.combo_clientes.get()
        if selected:
            idx = self.combo_clientes['values'].index(selected)
            client_code = self.clients_list[idx]['code']
        else:
            client_code = None
        try:
            doc_id, num, totals = post_sale(
                numero=None, fecha=None, items=items, notas="Venta POS",
                payment_method=payment_method, amount_paid=amount_paid,
                change_given=change, partner_code=client_code, user_id=self.user["id"]
            )
            # Registrar movimiento de caja si hay sesion abierta y es efectivo
            if self.session and payment_method == "efectivo":
                try:
                    register_cash_movement(
                        self.session["id"], "sale", totals.get("total", amount_paid),
                        note=f"Venta {num}"
                    )
                except Exception as e:
                    pass  # No bloquear la venta si falla el registro de caja

            # Intentar imprimir ticket
            try:
                from src.reports.ticket_printer import imprimir_ticket_venta
                imprimir_ticket_venta(doc_id, items, totals["total"],
                                      payment_method, change, amount_paid)
            except ImportError:
                pass  # Ticket printer opcional
            except Exception as e:
                messagebox.showwarning("Ticket", f"Venta guardada pero no se pudo imprimir ticket:\n{e}")

            self._clear_cart()
            messagebox.showinfo("Exito", f"Venta {num} registrada correctamente.")
        except Exception as e:
            messagebox.showerror("Error al guardar venta", str(e))

    # ── Cierre de caja ────────────────────────────────────────────────────────
    def _close_session_dialog(self):
        if not self.session:
            messagebox.showinfo("Caja", "No hay sesion de caja abierta.")
            return
        CloseSessionDialog(self, self.session, self._on_session_closed)

    def _on_session_closed(self):
        self.session = None
        messagebox.showinfo("Caja", "Caja cerrada. El POS seguira abierto en modo sin caja.")
        self._build_ui()  # reconstruye el header para actualizar estado