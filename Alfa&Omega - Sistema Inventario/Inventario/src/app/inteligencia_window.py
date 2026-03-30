import tkinter as tk
from tkinter import ttk, messagebox

from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography
from src.app.styles import theme

from src.services.anomalias import detectar_anomalias
from src.services.market_basket import calcular_asociaciones
from src.services.customer_reminders import get_clientes_sin_comprar, enviar_recordatorios
from src.services.dynamic_pricing import get_sugerencias_pricing


class InteligenciaWindow(tk.Toplevel):
    def __init__(self, parent, user=None):
        super().__init__(parent)
        self.title("🧠 Inteligencia de Negocio")
        self.geometry("1100x650")
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        self.transient(parent)
        self.grab_set()
        self.user = user
        import logging
        self._log = logging.getLogger(__name__)
        self._build_ui()

    def _build_ui(self):
        # Título principal
        tk.Label(
            self, text="🧠 Inteligencia de Negocio",
            font=ModernTypography.font_heading(),
            bg=Luxury2026Colors.BG_DARKEST,
            fg=Luxury2026Colors.PRIMARY
        ).pack(pady=(20, 10))

        # Cuaderno de pestañas
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        # 1. Anomalías
        self.tab_ano = ttk.Frame(self.nb)
        self.nb.add(self.tab_ano, text="🚨 Anomalías")
        self._build_tab_anomalias(self.tab_ano)

        # 2. Canasta
        self.tab_mb = ttk.Frame(self.nb)
        self.nb.add(self.tab_mb, text="🛒 Canasta")
        self._build_tab_canasta(self.tab_mb)

        # 3. Clientes
        self.tab_cli = ttk.Frame(self.nb)
        self.nb.add(self.tab_cli, text="👥 Clientes")
        self._build_tab_clientes(self.tab_cli)

        # 4. Precios
        self.tab_pre = ttk.Frame(self.nb)
        self.nb.add(self.tab_pre, text="💰 Precios")
        self._build_tab_precios(self.tab_pre)

    # ---------------- 🚨 Pestaña: Anomalías ----------------
    def _build_tab_anomalias(self, frame):
        tk.Label(
            frame, 
            text="Detección de picos inusuales de venta comparado con los últimos 90 días.",
            font=ModernTypography.font_body(),
            bg=Luxury2026Colors.BG_SECONDARY,
            fg=Luxury2026Colors.TEXT_SECONDARY
        ).pack(anchor="w", padx=10, pady=10)

        btn_frame = tk.Frame(frame, bg=Luxury2026Colors.BG_SECONDARY)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="🔍 Detectar Anomalías (Hoy)", command=self.load_anomalias, style="Luxury.Primary.TButton").pack(side="left")
        ttk.Button(btn_frame, text="📥 Exportar Excel",
            command=lambda: self._exportar_excel(
                "Anomalias",
                ["Código","Nombre","Venta Hoy","Promedio","Desviación","Tipo","Severidad"],
                [self.tree_ano.item(r)["values"] for r in self.tree_ano.get_children()]
            )).pack(side="left", padx=(10,0))

        # Tabla
        cols = ("Código", "Nombre", "Venta Hoy", "Promedio", "Desviación", "Tipo", "Severidad")
        self.tree_ano = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for c in cols:
            self.tree_ano.heading(c, text=c)
            anchor = "w" if c == "Nombre" else "center"
            self.tree_ano.column(c, width=120, anchor=anchor)
        self.tree_ano.column("Nombre", width=250)
        
        self.tree_ano.pack(fill="both", expand=True, padx=10, pady=10)
        theme.aplicar_estilo_treeview(self.tree_ano)
        self.tree_ano.tag_configure("ALTA",  foreground="#EF4444")
        self.tree_ano.tag_configure("BAJA",  foreground="#3B82F6")
        self.tree_ano.tag_configure("NORMAL",foreground="#10B981")

    def load_anomalias(self):
        for row in self.tree_ano.get_children():
            self.tree_ano.delete(row)
        try:
            datos = detectar_anomalias()
            for d in datos:
                self.tree_ano.insert("", "end", values=(
                    d["codigo"], d["nombre"], d["venta_hoy"],
                    d["promedio_historico"], d["desviacion"],
                    d["tipo"], d["severidad"]
                ), tags=(d["tipo"],))
        except Exception as e:
            self._log.exception("Error en load_anomalias")
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")

    # ---------------- 🛒 Pestaña: Canasta (Market Basket) ----------------
    def _build_tab_canasta(self, frame):
        tk.Label(
            frame, 
            text="Asociaciones de co-ocurrencia: Productos comprados juntos frecuentemente.",
            font=ModernTypography.font_body(),
            bg=Luxury2026Colors.BG_SECONDARY,
            fg=Luxury2026Colors.TEXT_SECONDARY
        ).pack(anchor="w", padx=10, pady=10)

        btn_frame = tk.Frame(frame, bg=Luxury2026Colors.BG_SECONDARY)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(btn_frame, text="Soporte Mínimo (tickets):", bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_PRIMARY).pack(side="left", padx=(0,5))
        self.entry_support = tk.Entry(btn_frame, width=5)
        self.entry_support.insert(0, "2")
        self.entry_support.pack(side="left", padx=(0,10))
        
        ttk.Button(btn_frame, text="🛒 Analizar Asociaciones", command=self.load_canasta, style="Luxury.Primary.TButton").pack(side="left")
        ttk.Button(btn_frame, text="📥 Exportar Excel",
            command=lambda: self._exportar_excel(
                "Canasta",
                ["Producto Ancla","Comprado Con","Frecuencia","Confianza %"],
                [self.tree_mb.item(r)["values"] for r in self.tree_mb.get_children()]
            )).pack(side="left", padx=(10,0))

        cols = ("Producto Ancla", "Comprado Con", "Frecuencia (Soporte)", "Confianza %")
        self.tree_mb = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for c in cols:
            self.tree_mb.heading(c, text=c)
            self.tree_mb.column(c, anchor="center")
        self.tree_mb.pack(fill="both", expand=True, padx=10, pady=10)
        theme.aplicar_estilo_treeview(self.tree_mb)

    def load_canasta(self):
        for row in self.tree_mb.get_children():
            self.tree_mb.delete(row)
        try:
            sup = int(self.entry_support.get() or "2")
            datos = calcular_asociaciones(min_support=sup)
            for d in datos:
                conf_pct = f"{d['confianza'] * 100:.1f}%"
                self.tree_mb.insert("", "end", values=(
                    d["producto_a"], d["producto_b"], d["support"], conf_pct
                ))
        except Exception as e:
            self._log.exception("Error en load_canasta")
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")

    # ---------------- 👥 Pestaña: Clientes ----------------
    def _build_tab_clientes(self, frame):
        tk.Label(
            frame, 
            text="Retención de clientes: Detecta clientes inactivos para re-enganche.",
            font=ModernTypography.font_body(),
            bg=Luxury2026Colors.BG_SECONDARY,
            fg=Luxury2026Colors.TEXT_SECONDARY
        ).pack(anchor="w", padx=10, pady=10)

        btn_frame = tk.Frame(frame, bg=Luxury2026Colors.BG_SECONDARY)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(btn_frame, text="Días Inactividad:", bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_PRIMARY).pack(side="left", padx=(0,5))
        self.entry_dias = tk.Entry(btn_frame, width=5)
        self.entry_dias.insert(0, "30")
        self.entry_dias.pack(side="left", padx=(0,10))
        
        ttk.Button(btn_frame, text="👥 Analizar Inactivos", command=self.load_clientes, style="Luxury.Primary.TButton").pack(side="left", padx=(0,10))
        ttk.Button(btn_frame, text="📧 Enviar Recordatorios", command=self.enviar_reminders, style="Luxury.Secondary.TButton").pack(side="left")
        ttk.Button(btn_frame, text="📥 Exportar Excel",
            command=lambda: self._exportar_excel(
                "Clientes_Inactivos",
                ["ID","Cliente","Email","Días Inactivo","Última Compra","Histórico Tx","Total Gastado"],
                [self.tree_cli.item(r)["values"] for r in self.tree_cli.get_children()]
            )).pack(side="left", padx=(10,0))

        cols = ("ID", "Cliente", "Email", "Días Inactivo", "Última Compra", "Histórico Tx", "Total Gastado")
        self.tree_cli = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for c in cols:
            self.tree_cli.heading(c, text=c)
            self.tree_cli.column(c, width=120, anchor="w" if c in ("Cliente", "Email") else "center")
        self.tree_cli.column("Cliente", width=200)
        self.tree_cli.pack(fill="both", expand=True, padx=10, pady=10)
        theme.aplicar_estilo_treeview(self.tree_cli)
        self.tree_cli.tag_configure("urgente", foreground="#EF4444")
        self.tree_cli.tag_configure("medio",   foreground="#F59E0B")
        self.tree_cli.tag_configure("reciente",foreground="#10B981")

    def load_clientes(self):
        for row in self.tree_cli.get_children():
            self.tree_cli.delete(row)
        try:
            dias = int(self.entry_dias.get() or "30")
            datos = get_clientes_sin_comprar(dias)
            for d in datos:
                total_usd = f"${d['total_gastado']:,.2f}"
                dias_sin = d["dias_sin_comprar"]
                tag = "urgente" if dias_sin > 60 else "medio" if dias_sin > 30 else "reciente"
                self.tree_cli.insert("", "end", values=(
                    d["partner_id"], d["nombre"], d["email"] or "N/A",
                    dias_sin, d["ultima_compra"],
                    d["total_compras_historicas"], total_usd
                ), tags=(tag,))
        except Exception as e:
            self._log.exception("Error en load_clientes")
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")

    def enviar_reminders(self):
        try:
            dias = int(self.entry_dias.get() or "30")
            res = enviar_recordatorios(dias)
            msg = f"Resumen de envío:\n\n"
            msg += f"Total elegibles: {res['total_elegibles']}\n"
            msg += f"Enviados con éxito: {res['enviados']}\n"
            msg += f"Omitidos (sin email): {res['sin_email']}\n"
            if res.get("errores"):
                msg += f"Errores: {len(res['errores'])}\n"
            messagebox.showinfo("Recordatorios de Retención", msg)
        except Exception as e:
            self._log.exception("Error en enviar_reminders")
            messagebox.showerror("Error de Envío", str(e))

    # ---------------- 💰 Pestaña: Precios ----------------
    def _build_tab_precios(self, frame):
        tk.Label(
            frame, 
            text="Sugerencias inteligentes de ajuste de precio basado en rotación histórica.",
            font=ModernTypography.font_body(),
            bg=Luxury2026Colors.BG_SECONDARY,
            fg=Luxury2026Colors.TEXT_SECONDARY
        ).pack(anchor="w", padx=10, pady=10)

        btn_frame = tk.Frame(frame, bg=Luxury2026Colors.BG_SECONDARY)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="💰 Generar Sugerencias", command=self.load_precios, style="Luxury.Primary.TButton").pack(side="left")
        ttk.Button(btn_frame, text="📥 Exportar Excel",
            command=lambda: self._exportar_excel(
                "Sugerencias_Precio",
                ["Código","Producto","Rotación","PV Actual","PV Sugerido","Var %","Razón"],
                [self.tree_pre.item(r)["values"] for r in self.tree_pre.get_children()]
            )).pack(side="left", padx=(10,0))

        cols = ("Código", "Producto", "Rotación", "PV Actual", "PV Sugerido", "Var %", "Razón")
        self.tree_pre = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for c in cols:
            self.tree_pre.heading(c, text=c)
            self.tree_pre.column(c, width=120, anchor="w" if c in ("Producto", "Razón") else "center")
        self.tree_pre.column("Producto", width=180)
        self.tree_pre.column("Razón", width=250)
        self.tree_pre.pack(fill="both", expand=True, padx=10, pady=10)
        theme.aplicar_estilo_treeview(self.tree_pre)
        self.tree_pre.tag_configure("subir",  foreground="#10B981")
        self.tree_pre.tag_configure("bajar",  foreground="#EF4444")

    def load_precios(self):
        for row in self.tree_pre.get_children():
            self.tree_pre.delete(row)
        try:
            datos = get_sugerencias_pricing()
            for d in datos:
                act = f"${d['precio_actual']:,.2f}"
                sug = f"${d['precio_sugerido']:,.2f}"
                var = f"{d['variacion_pct']:+.1f}%"
                tag = "subir" if d['variacion_pct'] > 0 else "bajar"
                self.tree_pre.insert("", "end", values=(
                    d["codigo"], d["nombre"], d["rotacion"],
                    act, sug, var, d["razon"]
                ), tags=(tag,))
        except Exception as e:
            self._log.exception("Error en load_precios")
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")

    def _exportar_excel(self, titulo: str, columnas: list, filas: list) -> None:
        """Exporta cualquier lista de filas a Excel via filedialog."""
        from tkinter import filedialog
        import openpyxl
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"{titulo}.xlsx",
            title=f"Exportar {titulo}"
        )
        if not path:
            return
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = titulo[:30]
            ws.append(columnas)
            for fila in filas:
                ws.append(list(fila))
            wb.save(path)
            from tkinter import messagebox
            messagebox.showinfo("Exportado", f"Archivo guardado:\n{path}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")
