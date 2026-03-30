"""
Dashboard con 4 zonas y KPIs reales — Tarea 12
Toda la lógica de datos vive en src/services/reports.py
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from datetime import datetime

try:
    import matplotlib.pyplot as plt  # noqa: F401
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# ── Servicios (cero queries aquí) ──────────────────────────────────────────
from src.services.inventory import count_products, stock_global_sum
from src.services.reports import (
    get_kpis_hoy,
    get_top_rentabilidad,
    get_sin_movimiento_30d,
    get_ventas_por_dia_30d,
    get_valor_inventario,
    get_alertas_inventario,
    get_top_clientes,
)
from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography
from src.app.components_luxury import Tooltip


# ── Paleta KPI cards ───────────────────────────────────────────────────────
_KPI_COLORS = [
    Luxury2026Colors.PRIMARY,
    Luxury2026Colors.SUCCESS,
    Luxury2026Colors.ACCENT,
    Luxury2026Colors.SUCCESS,  # <-- utilidad_neta (dinámico)
    "#8B5CF6",   # violeta ticket
    Luxury2026Colors.DANGER,
]


class DashboardTab:
    """Tab de Dashboard — 4 zonas: A Alertas | B KPIs | C Análisis | D Inventario"""

    def __init__(self, parent):
        self.parent = parent
        # Frame con scrollbar por si el contenido es alto
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="both", expand=True)
        self._periodo = "hoy"          # período activo del filtro
        self._btn_periodo: dict = {}   # {key: tk.Label} para resaltar activo
        self._build_dashboard()

    # ──────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────────────────

    def refresh(self):
        """Refresca el dashboard con datos actualizados."""
        try:
            self._update_zona_a()
            self._update_zona_b()
            self._update_zona_d()
        except Exception:
            # Si los widgets fueron destruidos, reconstruir completo
            for w in self.frame.winfo_children():
                w.destroy()
            self._build_dashboard()

    def update(self):
        """Alias de refresh() — compatibilidad con main_window.py."""
        self.refresh()

    # ──────────────────────────────────────────────────────────────────────
    # CONSTRUCTION
    # ──────────────────────────────────────────────────────────────────────


    def _build_dashboard(self):
        bg = Luxury2026Colors.BG_SECONDARY

        # ── ZONA A — Barra de alertas ─────────────────────────────────────
        self._frm_a = tk.Frame(self.frame, bg="#1E1E2E", pady=6)
        self._frm_a.pack(fill="x", padx=0, pady=(0, 6))
        self._lbl_critico   = tk.Label(self._frm_a, font=ModernTypography.font_body_small(),
                                       bg="#1E1E2E", fg=Luxury2026Colors.DANGER)
        self._lbl_bajo      = tk.Label(self._frm_a, font=ModernTypography.font_body_small(),
                                       bg="#1E1E2E", fg="#FF9800")
        self._lbl_pendiente = tk.Label(self._frm_a, font=ModernTypography.font_body_small(),
                                       bg="#1E1E2E", fg=Luxury2026Colors.TEXT_SECONDARY)
        for lbl in (self._lbl_critico, self._lbl_bajo, self._lbl_pendiente):
            lbl.pack(side="left", padx=16)
        self._update_zona_a()

        # ── BARRA FILTRO TEMPORAL ─────────────────────────────────────────
        self._frm_filtro = tk.Frame(self.frame, bg=Luxury2026Colors.BG_DARK)
        self._frm_filtro.pack(fill="x", padx=8, pady=(0, 4))
        for label, key in [("Hoy", "hoy"), ("Semana", "semana"), ("Mes", "mes")]:
            btn = tk.Label(
                self._frm_filtro, text=label, cursor="hand2",
                font=ModernTypography.font_body_small(),
                bg=Luxury2026Colors.BG_DARK,
                fg=Luxury2026Colors.TEXT_SECONDARY,
                padx=14, pady=4,
            )
            btn.pack(side="left", padx=(0, 2))
            btn.bind("<Button-1>", lambda e, k=key: self._set_periodo(k))
            self._btn_periodo[key] = btn
        self._highlight_periodo()

        # ── ZONA B — 6 KPI cards ──────────────────────────────────────────
        self._frm_b = tk.Frame(self.frame, bg=bg)
        self._frm_b.pack(fill="x", padx=8, pady=(0, 8))
        for i in range(6):
            self._frm_b.columnconfigure(i, weight=1)

        kpi_defs = [
            ("💰", "Ventas hoy",    "ventas_hoy",          "${v:,.0f}"),
            ("💵", "Caja",          "caja_disponible",      "${v:,.0f}"),
            ("📊", "Margen bruto",  "margen_bruto_pct",     "{v:.1f}%"),
            ("📈", "Utilidad Neta", "utilidad_neta",        "${v:,.0f}"),
            ("🧾", "Ticket prom.", "ticket_promedio",       "${v:,.0f}"),
            ("🔄", "Devoluciones",  "tasa_devolucion_pct",  "{v:.1f}%"),
        ]
        self._kpi_labels: list[tk.Label] = []
        for col, (ico, titulo, _key, _fmt) in enumerate(kpi_defs):
            frm = tk.Frame(self._frm_b, bg=Luxury2026Colors.BG_SECONDARY,
                           relief="flat", bd=0)
            frm.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")
            tk.Label(frm, text=f"{ico} {titulo}",
                     font=ModernTypography.font_body_small(),
                     bg=Luxury2026Colors.BG_SECONDARY,
                     fg=Luxury2026Colors.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(10, 2))
            val_lbl = tk.Label(frm, text="—",
                               font=("Arial", 22, "bold"),
                               bg=Luxury2026Colors.BG_SECONDARY,
                               fg=_KPI_COLORS[col])
            val_lbl.pack(anchor="w", padx=12, pady=(0, 10))

            tooltips = {
                "ventas_hoy":          "Total vendido en el período seleccionado\n(sin devoluciones)",
                "caja_disponible":     "Saldo disponible en caja al momento actual",
                "margen_bruto_pct":    "% de ganancia sobre el costo:\n(Ventas - Costo) / Ventas × 100",
                "utilidad_neta":       "Ventas - Costo de ventas del período",
                "ticket_promedio":     "Valor promedio por transacción:\nTotal ventas / Nº de tickets",
                "tasa_devolucion_pct": "% de ventas devueltas:\nDevoluciones / Ventas brutas × 100",
            }
            tip_text = tooltips.get(_key, "")
            if tip_text:
                Tooltip(frm, tip_text)
                Tooltip(val_lbl, tip_text)

            self._kpi_labels.append(val_lbl)
        self._kpi_defs = kpi_defs
        self._update_zona_b()

        # ── ZONA C — Análisis (gráfico izq + rentabilidad der) ────────────
        frm_c = ttk.LabelFrame(self.frame, text="📈 Análisis", padding=8)
        frm_c.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._frm_c_inner = tk.Frame(frm_c, bg=Luxury2026Colors.BG_SECONDARY)
        self._frm_c_inner.pack(fill="both", expand=True)
        self._refresh_zona_c()

        # ── ZONA D — Inventario (fila inferior) ───────────────────────────
        self._frm_d = tk.Frame(self.frame, bg=bg)
        self._frm_d.pack(fill="x", padx=8, pady=(0, 8))
        for i in range(6):
            self._frm_d.columnconfigure(i, weight=1)

        d_defs = [
            ("🏦", "Valor inventario"),
            ("💤", "Sin movimiento 30d"),
            ("📦", "Stock total"),
            ("🛒", "Compras"),
            ("🏷️", "Descuentos"),
            ("👥", "Top Clientes"),
        ]
        self._zona_d_labels: list[tk.Label] = []
        
        d_tooltips = {
            "Valor inventario":   "Capital total inmovilizado en mercancía\n(cantidad × costo promedio de cada producto)",
            "Sin movimiento 30d": "Productos sin ninguna venta en los últimos 30 días\n(riesgo de obsolescencia — revisar precios)",
            "Stock total":        "Suma de unidades disponibles de todos los productos activos",
            "Compras":            "Total invertido en compras a proveedores en el período seleccionado",
            "Descuentos":         "Porcentaje de descuentos otorgados sobre ventas brutas\n(0% si no hay columna discount implementada)",
            "Top Clientes":       "Ver ranking de clientes por volumen de compras\n(clic para abrir reporte detallado)",
        }
        
        for col, (ico, titulo) in enumerate(d_defs):
            frm = tk.Frame(self._frm_d, bg=Luxury2026Colors.BG_SECONDARY)
            frm.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")
            
            lbl_tit = tk.Label(frm, text=f"{ico} {titulo}",
                               font=ModernTypography.font_body_small(),
                               bg=Luxury2026Colors.BG_SECONDARY,
                               fg=Luxury2026Colors.TEXT_SECONDARY)
            lbl_tit.pack(anchor="w", padx=12, pady=(10, 2))
            
            lbl = tk.Label(frm, text="—",
                           font=("Arial", 20, "bold"),
                           bg=Luxury2026Colors.BG_SECONDARY,
                           fg=Luxury2026Colors.PRIMARY)
            lbl.pack(anchor="w", padx=12, pady=(0, 10))
            
            tip = d_tooltips.get(titulo, "")
            if tip:
                Tooltip(frm, tip)
                Tooltip(lbl_tit, tip)
                Tooltip(lbl, tip)
            
            if col == 5:
                # Configurar clic en la card Top Clientes
                frm.config(cursor="hand2")
                lbl_tit.config(cursor="hand2")
                lbl.config(text="Ver →", cursor="hand2")
                
                lbl.bind("<Button-1>", lambda e: self._show_top_clientes())
                lbl_tit.bind("<Button-1>", lambda e: self._show_top_clientes())
                frm.bind("<Button-1>", lambda e: self._show_top_clientes())
            else:
                self._zona_d_labels.append(lbl)
                
        self._update_zona_d()

    # ──────────────────────────────────────────────────────────────────────
    # UPDATE HELPERS
    # ──────────────────────────────────────────────────────────────────────

    def _update_zona_a(self):
        alertas = get_alertas_inventario()
        critico   = alertas.get("critico", 0)
        bajo      = alertas.get("bajo_stock", 0)
        pendiente = alertas.get("pendientes", 0)

        self._lbl_critico.config(
            text=f"🚨 Stock crítico: {critico}" if critico else "✅ Sin críticos"
        )
        self._lbl_bajo.config(
            text=f"⚠️ Bajo stock: {bajo}" if bajo else "✅ Stock OK"
        )
        self._lbl_pendiente.config(
            text=f"📋 Pedidos pendientes: {pendiente}"
        )

    def _update_zona_b(self):
        kpis = get_kpis_hoy(self._periodo)
        keys = ["ventas_hoy", "caja_disponible", "margen_bruto_pct",
                "utilidad_neta", "ticket_promedio", "tasa_devolucion_pct"]
        fmts = ["${v:,.0f}", "${v:,.0f}", "{v:.1f}%", "${v:,.0f}", "${v:,.0f}", "{v:.1f}%"]
        for col, (lbl, key, fmt) in enumerate(zip(self._kpi_labels, keys, fmts)):
            v = kpis.get(key, 0.0)
            try:
                lbl.config(text=fmt.format(v=v))
            except Exception:
                lbl.config(text=str(v))
            
            # Dynamic color for Utilidad Neta
            if key == "utilidad_neta":
                color = Luxury2026Colors.SUCCESS if v >= 0 else Luxury2026Colors.DANGER
                lbl.config(fg=color)

    def _update_zona_d(self):
        valor    = get_valor_inventario()
        sin_mov  = get_sin_movimiento_30d()
        stock    = stock_global_sum()
        kpis     = get_kpis_hoy(self._periodo)
        compras  = kpis.get("compras_periodo", 0.0)
        desc     = kpis.get("descuentos_pct", 0.0)

        valores  = [
            f"${valor:,.0f}", 
            str(sin_mov), 
            str(stock),
            f"${compras:,.0f}",
            f"{desc:.1f}%"
        ]
        for lbl, val in zip(self._zona_d_labels, valores):
            lbl.config(text=val)

    # ──────────────────────────────────────────────────────────────────────
    # ZONA C — gráficos
    # ──────────────────────────────────────────────────────────────────────

    def _build_grafico_ventas(self, parent):
        """Gráfico de área — ventas Σ(qty*price) últimos 30 días."""
        datos = get_ventas_por_dia_30d(self._periodo)
        if not datos:
            ttk.Label(parent, text="Sin datos de ventas").pack(pady=20)
            return

        if not MATPLOTLIB_AVAILABLE:
            self._fallback_ventas(parent, datos)
            return

        fechas = sorted(datos.keys())
        valores = [datos[f] for f in fechas]

        if len(fechas) < 2:
            ttk.Label(parent, text="Datos insuficientes").pack(pady=20)
            return

        fig = Figure(figsize=(5, 3.5), dpi=95)
        fig.patch.set_facecolor("#1A1A2E")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1A1A2E")

        ax.fill_between(range(len(fechas)), valores, alpha=0.25, color="#7C3AED")
        ax.plot(range(len(fechas)), valores, color="#7C3AED", linewidth=2, label="Ventas reales")

        # Línea de meta: promedio del período × 1.2
        if valores:
            meta = (sum(valores) / len(valores)) * 1.2
            ax.axhline(
                y=meta,
                color="#F59E0B",
                linewidth=1.5,
                linestyle="--",
                alpha=0.8,
                label=f"Meta ${meta:,.0f}"
            )
            ax.legend(
                loc="upper left",
                fontsize=7,
                facecolor="#1A1A2E",
                edgecolor="#555",
                labelcolor="#DDD"
            )

        mid = len(fechas) // 2
        ax.set_xticks([0, mid, len(fechas) - 1])
        ax.set_xticklabels(
            [fechas[0].strftime("%d/%m"), fechas[mid].strftime("%d/%m"),
             fechas[-1].strftime("%d/%m")],
            color="#AAA", fontsize=8
        )
        ax.tick_params(axis="y", colors="#AAA", labelsize=8)
        ax.set_title("Ventas 30 días — línea amarilla = meta sugerida", fontsize=9, color="#DDD", pad=6)
        ax.grid(True, alpha=0.15, color="#555")
        for spine in ax.spines.values():
            spine.set_visible(False)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        tk.Label(
            parent,
            text="💡 Meta = promedio diario × 1.2  |  Morada = ventas reales",
            font=("Arial", 8),
            bg=Luxury2026Colors.BG_DARKEST,
            fg=Luxury2026Colors.TEXT_TERTIARY
        ).pack(pady=(0, 4))

    def _build_top_rentabilidad(self, parent):
        """Top 5 por rentabilidad = (precio - costo) × qty."""
        top = get_top_rentabilidad(5, self._periodo)

        title_lbl = tk.Label(parent, text="🏆 Top 5 — Rentabilidad",
                             font=ModernTypography.font_body_small(),
                             bg=Luxury2026Colors.BG_SECONDARY,
                             fg=Luxury2026Colors.TEXT_SECONDARY)
        title_lbl.pack(anchor="w", pady=(4, 6))

        if not top:
            ttk.Label(parent, text="Sin datos de ventas").pack(pady=20)
            return

        max_rent = max((r["rentabilidad"] for r in top), default=1) or 1
        bar_colors = ["#7C3AED", "#6D28D9", "#5B21B6", "#4C1D95", "#3B0764"]

        for i, row in enumerate(top):
            frm = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY)
            frm.pack(fill="x", pady=3)

            nombre = (row["nombre"] or "?")[:22]
            tk.Label(frm, text=nombre,
                     font=("Arial", 9),
                     bg=Luxury2026Colors.BG_SECONDARY,
                     fg=Luxury2026Colors.TEXT_PRIMARY,
                     width=22, anchor="w").pack(side="left")

            # mini barra proporcional
            bar_w = max(4, int(row["rentabilidad"] / max_rent * 120))
            bar_cv = tk.Canvas(frm, width=bar_w, height=14,
                               bg=bar_colors[i % len(bar_colors)],
                               highlightthickness=0)
            bar_cv.pack(side="left", padx=(4, 6))

            tk.Label(frm, text=f"${row['rentabilidad']:,.0f}",
                     font=("Arial", 9, "bold"),
                     bg=Luxury2026Colors.BG_SECONDARY,
                     fg=Luxury2026Colors.SUCCESS).pack(side="left")

    # ──────────────────────────────────────────────────────────────────────
    # FALLBACK sin matplotlib
    # ──────────────────────────────────────────────────────────────────────

    def _fallback_ventas(self, parent, datos: dict):
        frm = ttk.LabelFrame(parent, text="Ventas 30 días", padding=8)
        frm.pack(fill="both", expand=True)
        cv = tk.Canvas(frm, bg="#1A1A2E", height=160, highlightthickness=0)
        cv.pack(fill="both", expand=True)
        vals = list(datos.values())
        max_v = max(vals) if vals else 1
        cv.create_text(10, 20, text=f"Máx: ${max_v:,.0f}",
                       font=("Arial", 9), anchor="w", fill="#AAA")
        cv.create_text(10, 145, text="(instala matplotlib para gráfico)",
                       font=("Arial", 8), anchor="w", fill="#666")

    # ──────────────────────────────────────────────────────────────────────
    # FILTRO TEMPORAL
    # ──────────────────────────────────────────────────────────────────────

    def _set_periodo(self, periodo: str) -> None:
        """Cambia el período activo y refresca solo Zona B y C (A y D sin cambios)."""
        self._periodo = periodo
        self._highlight_periodo()
        self._update_zona_b()
        self._refresh_zona_c()

    def _highlight_periodo(self) -> None:
        """Resalta el botón de filtro activo con PRIMARY, los demás con TEXT_SECONDARY."""
        for key, btn in self._btn_periodo.items():
            if key == self._periodo:
                btn.config(fg=Luxury2026Colors.PRIMARY,
                           font=("Segoe UI", 13, "bold"))
            else:
                btn.config(fg=Luxury2026Colors.TEXT_SECONDARY,
                           font=ModernTypography.font_body_small())

    def _refresh_zona_c(self) -> None:
        """Destruye y reconstruye solo el contenido de Zona C respetando el período."""
        if not hasattr(self, "_frm_c_inner") or not self._frm_c_inner.winfo_exists():
            return
        for w in self._frm_c_inner.winfo_children():
            w.destroy()
        frm_izq = ttk.Frame(self._frm_c_inner)
        frm_izq.pack(side="left", fill="both", expand=True, padx=(0, 6))
        frm_der = ttk.Frame(self._frm_c_inner)
        frm_der.pack(side="right", fill="both", expand=True, padx=(6, 0))
        self._build_grafico_ventas(frm_izq)
        self._build_top_rentabilidad(frm_der)

    def _show_top_clientes(self):
        """Muestra ventana con el reporte de Top Clientes por Volumen usando ttk.Treeview."""
        top = get_top_clientes(5, self._periodo)
        
        top_win = tk.Toplevel(self.parent)
        top_win.title("Top Clientes")
        top_win.geometry("500x320")
        top_win.configure(bg=Luxury2026Colors.BG_DARKEST)
        top_win.resizable(False, False)
        top_win.transient(self.parent)
        top_win.grab_set()

        lbl_tit = tk.Label(top_win, text=f"Top 5 Clientes ({self._periodo.capitalize()})",
                           font=ModernTypography.font_title(),
                           bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.TEXT_PRIMARY)
        lbl_tit.pack(pady=10)

        # Style para el Treeview
        style = ttk.Style(top_win)
        style.theme_use("clam")
        style.configure("Treeview", 
                        background=Luxury2026Colors.BG_SECONDARY,
                        fieldbackground=Luxury2026Colors.BG_SECONDARY,
                        foreground=Luxury2026Colors.TEXT_PRIMARY,
                        rowheight=30)
        style.configure("Treeview.Heading", 
                        background=Luxury2026Colors.BG_DARKEST, 
                        foreground=Luxury2026Colors.TEXT_SECONDARY,
                        font=ModernTypography.font_body_small())

        cols = ("nombre", "trans", "total", "pct")
        tree = ttk.Treeview(top_win, columns=cols, show="headings", height=5)
        tree.heading("nombre", text="Cliente")
        tree.heading("trans", text="Trans.")
        tree.heading("total", text="Volumen ($)")
        tree.heading("pct", text="% Total")

        tree.column("nombre", width=190, anchor="w")
        tree.column("trans", width=60, anchor="center")
        tree.column("total", width=120, anchor="e")
        tree.column("pct", width=80, anchor="e")
        tree.pack(padx=15, pady=5, fill="both", expand=True)

        for row in top:
            tree.insert("", "end", values=(
                row["nombre"],
                row["transacciones"],
                f"${row['total']:,.0f}",
                f"{row['porcentaje']:.1f}%"
            ))
        
        # Si no hay ventas, mostramos row vacio o aviso
        if not top:
            tree.insert("", "end", values=("Sin datos en este período", "-", "-", "-"))
        
        btn_close = ttk.Button(top_win, text="Cerrar", command=top_win.destroy)
        btn_close.pack(pady=15)