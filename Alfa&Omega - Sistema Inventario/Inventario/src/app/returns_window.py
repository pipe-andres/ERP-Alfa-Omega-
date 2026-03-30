import tkinter as tk
from tkinter import ttk, messagebox

# import color/style constants from theme
from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography

_BG_DARK = getattr(Luxury2026Colors, "BG_DARKEST", "#0A0E27")
_BG_PANEL = getattr(Luxury2026Colors, "BG_SECONDARY", "#0D1117")
_ACCENT = getattr(Luxury2026Colors, "ACCENT", "#3B82F6")


class ReturnsWindow(tk.Toplevel):
    """Ventana para registrar devoluciones de una venta existente."""

    def __init__(self, parent, user: dict | None = None):
        super().__init__(parent)
        self.title("Devoluciones")
        self.geometry("700x500")
        self.configure(bg=_BG_DARK)
        self.transient(parent)
        self.grab_set()

        self.user = user
        self.line_vars: list[tuple[str, float, float, tk.StringVar]] = []

        self._build_ui()

    def _build_ui(self):
        main = tk.Frame(self, bg=_BG_DARK, padx=20, pady=20)
        main.pack(fill="both", expand=True)

        # --- búsqueda de venta ------------------------------------------------
        row = tk.Frame(main, bg=_BG_DARK)
        row.pack(fill="x", pady=(0, 10))
        tk.Label(row, text="ID de venta:", bg=_BG_DARK, fg="white").pack(side="left")
        self.var_sale_id = tk.StringVar()
        entry_sale = tk.Entry(row, textvariable=self.var_sale_id, width=10)
        entry_sale.pack(side="left", padx=(4, 8))
        from src.app.styles.luxury_2026 import add_placeholder
        add_placeholder(entry_sale, "🔍 ID de la venta a devolver")
        tk.Button(row, text="Buscar", command=self._load_sale).pack(side="left")

        # --- contenedor de líneas ------------------------------------------------
        self.lines_container = tk.Frame(main, bg=_BG_DARK)
        self.lines_container.pack(fill="both", expand=True)

        # encabezados
        hdr = tk.Frame(self.lines_container, bg=_BG_DARK)
        hdr.pack(fill="x")
        for text, width in [("Código", 15), ("Vendidas", 8), ("Devueltas", 8), ("A devolver", 10)]:
            tk.Label(hdr, text=text, bg=_BG_DARK, fg=_ACCENT, width=width, anchor="w").pack(side="left")

        # --- motivo
        tk.Label(main, text="Motivo de devolución:", bg=_BG_DARK, fg="white").pack(anchor="w", pady=(12, 2))
        self.txt_reason = tk.Text(main, height=3, bg=_BG_PANEL, fg="white")
        self.txt_reason.pack(fill="x")

        # --- botones
        btn_frame = tk.Frame(main, bg=_BG_DARK)
        btn_frame.pack(fill="x", pady=(12, 0))
        tk.Button(btn_frame, text="Registrar", bg=_ACCENT, fg="white",
                 command=self._register_return, padx=12, pady=4).pack(side="right")
        tk.Button(btn_frame, text="Cancelar", bg="gray", fg="white",
                 command=self.destroy, padx=12, pady=4).pack(side="right", padx=4)

    def _load_sale(self):
        sale_id_str = self.var_sale_id.get().strip()
        _PH = "🔍 ID de la venta a devolver"
        if not sale_id_str or sale_id_str == _PH:
            messagebox.showerror("Error", "Ingresa el ID de la venta")
            return
        if not sale_id_str.isdigit():
            messagebox.showerror("Error", "ID de venta inválido")
            return
        sale_id = int(sale_id_str)
        try:
            from src.database.connection import get_connection
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT codigo, qty, unit_price FROM document_lines WHERE doc_id=?", (sale_id,))
                sale_lines = {r[0]: {"qty": float(r[1] or 0), "unit_price": float(r[2] or 0)}
                              for r in cur.fetchall()}

                cur.execute(
                    "SELECT rl.product_code, SUM(rl.quantity) FROM return_lines rl "
                    "JOIN returns r ON rl.return_id = r.id "
                    "WHERE r.sale_id = ? GROUP BY rl.product_code", (sale_id,)
                )
                returned_sums = {r[0]: float(r[1] or 0) for r in cur.fetchall()}
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        if not sale_lines:
            messagebox.showinfo("Info", "Venta no encontrada o sin líneas")
            return

        # limpiar contenedor anterior
        for child in self.lines_container.winfo_children()[1:]:  # saltar encabezados
            child.destroy()
        self.line_vars.clear()

        for code, info in sale_lines.items():
            qtysold = info["qty"]
            qtyret = returned_sums.get(code, 0.0)
            var = tk.StringVar(value="0")
            row = tk.Frame(self.lines_container, bg=_BG_DARK)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=code, bg=_BG_DARK, fg="white", width=15, anchor="w").pack(side="left")
            tk.Label(row, text=f"{qtysold}", bg=_BG_DARK, fg="white", width=8, anchor="w").pack(side="left")
            tk.Label(row, text=f"{qtyret}", bg=_BG_DARK, fg="white", width=8, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, width=10).pack(side="left")
            self.line_vars.append((code, qtysold, qtyret, var))

    def _register_return(self):
        items = []
        for code, sold, ret, var in self.line_vars:
            try:
                qty = float(var.get() or 0)
            except ValueError:
                qty = 0.0
            if qty > 0:
                if qty + ret > sold + 1e-6:
                    messagebox.showerror("Error",
                                         f"Cantidad inválida para {code}: excede lo vendido")
                    return
                items.append({"codigo": code, "qty": qty})
        if not items:
            messagebox.showwarning("Aviso", "No hay artículos seleccionados para devolver")
            return
        reason = self.txt_reason.get("1.0", "end").strip() or "Devolución"
        try:
            from src.services.returns_service import post_return
            ret_id, credit_id = post_return(int(self.var_sale_id.get()), items, reason,
                                            user_id=(self.user["id"] if self.user else None))
            messagebox.showinfo("Éxito", f"Devolución registrada (id {ret_id})")
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
