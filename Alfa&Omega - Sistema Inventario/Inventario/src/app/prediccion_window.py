"""
src/app/prediccion_window.py
=============================
Tarea 20 — Ventana de Predicción IA de inventario.
Tabs: Resumen | Detalle por producto.
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk, messagebox

from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography
from src.app.styles import theme, scrollbars
from src.services.prediccion import predecir_demanda, get_resumen_predicciones

_LOG = logging.getLogger(__name__)

_COLOR_CRITICO = "#FF4444"
_COLOR_BAJO    = "#FF8800"
_COLOR_OK      = "#22CC66"


class PrediccionWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("🔮 Predicción IA de Inventario")
        self.geometry("960x640")
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        self.resizable(True, True)

        # Header
        tk.Label(
            self, text="🔮 Predicción IA de Inventario",
            font=ModernTypography.font_heading_lg(),
            bg=Luxury2026Colors.BG_DARKEST,
            fg=Luxury2026Colors.PRIMARY,
        ).pack(anchor="w", padx=16, pady=(12, 0))
        tk.Label(
            self,
            text="Basado en Holt-Winters (statsmodels) · últimos 90 días de kardex",
            font=ModernTypography.font_body_small(),
            bg=Luxury2026Colors.BG_DARKEST,
            fg=Luxury2026Colors.TEXT_TERTIARY,
        ).pack(anchor="w", padx=16, pady=(0, 8))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=6)

        # Tab Resumen
        self._tab_resumen = ttk.Frame(nb)
        nb.add(self._tab_resumen, text="📋 Resumen")
        self._build_resumen(self._tab_resumen)

        # Tab Detalle
        self._tab_detalle = ttk.Frame(nb)
        nb.add(self._tab_detalle, text="🔍 Detalle por Producto")
        self._build_detalle(self._tab_detalle)

        self._cargar_resumen()

    # ── Tab Resumen ────────────────────────────────────────────────────────────

    def _build_resumen(self, parent):
        btn_frame = tk.Frame(parent, bg=Luxury2026Colors.BG_DARKEST)
        btn_frame.pack(fill="x", padx=8, pady=6)
        ttk.Button(btn_frame, text="↻ Actualizar", command=self._cargar_resumen).pack(side="left")
        self._lbl_status = tk.Label(
            btn_frame, text="",
            font=ModernTypography.font_body_small(),
            bg=Luxury2026Colors.BG_DARKEST,
            fg=Luxury2026Colors.TEXT_SECONDARY,
        )
        self._lbl_status.pack(side="left", padx=12)

        frame_tree = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY)
        frame_tree.pack(fill="both", expand=True, padx=8, pady=4)

        cols = ("codigo", "nombre", "stock", "dias", "alerta", "quiebre")
        heads = {
            "codigo": "Código", "nombre": "Producto",
            "stock": "Stock", "dias": "Días cobertura",
            "alerta": "Alerta", "quiebre": "Quiebre estimado",
        }
        widths = {
            "codigo": 100, "nombre": 220, "stock": 70,
            "dias": 110, "alerta": 80, "quiebre": 130,
        }

        self._tree_res = ttk.Treeview(frame_tree, columns=cols, show="headings")
        for c in cols:
            self._tree_res.heading(c, text=heads[c])
            self._tree_res.column(c, width=widths[c], anchor="center")
        self._tree_res.column("nombre", anchor="w")

        theme.aplicar_estilo_treeview(self._tree_res)
        scrollbars.agregar_scrollbar(self._tree_res, frame_tree)
        self._tree_res.pack(fill="both", expand=True)

        self._tree_res.tag_configure("CRITICO", foreground=_COLOR_CRITICO)
        self._tree_res.tag_configure("BAJO",    foreground=_COLOR_BAJO)
        self._tree_res.tag_configure("OK",      foreground=_COLOR_OK)

    def _cargar_resumen(self):
        self._lbl_status.config(text="Calculando predicciones…")
        self.update_idletasks()
        try:
            datos = get_resumen_predicciones()
            for item in self._tree_res.get_children():
                self._tree_res.delete(item)
            for r in datos:
                tag = r["alerta"]
                self._tree_res.insert("", "end", values=(
                    r["codigo"], r["nombre"], r["stock_actual"],
                    r["dias_cobertura"], r["alerta"],
                    r["fecha_quiebre"] or "—",
                ), tags=(tag,))
            self._lbl_status.config(text=f"{len(datos)} productos analizados.")
        except Exception as e:
            logging.warning("PrediccionWindow _cargar_resumen: %s", e)
            messagebox.showerror("Error", f"No se pudieron cargar predicciones:\n{e}", parent=self)

    # ── Tab Detalle ────────────────────────────────────────────────────────────

    def _build_detalle(self, parent):
        ctrl = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY)
        ctrl.pack(fill="x", padx=8, pady=8)
        tk.Label(
            ctrl, text="Código producto:",
            font=ModernTypography.font_body(),
            bg=Luxury2026Colors.BG_SECONDARY,
            fg=Luxury2026Colors.TEXT_PRIMARY,
        ).pack(side="left")
        self._entry_cod = tk.Entry(
            ctrl, width=18,
            font=ModernTypography.font_body(),
            bg=Luxury2026Colors.BG_TERTIARY,
            fg=Luxury2026Colors.TEXT_PRIMARY,
            insertbackground=Luxury2026Colors.PRIMARY,
            relief="solid", bd=1,
        )
        self._entry_cod.pack(side="left", padx=8)
        ttk.Button(ctrl, text="🔎 Predecir", command=self._cargar_detalle).pack(side="left")

        # KPIs
        kpi_frame = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        kpi_frame.pack(fill="x", padx=8, pady=4)
        self._lbl_nombre = tk.Label(
            kpi_frame, text="—",
            font=ModernTypography.font_body_bold(),
            bg=Luxury2026Colors.BG_SECONDARY,
            fg=Luxury2026Colors.PRIMARY,
        )
        self._lbl_nombre.pack(anchor="w", padx=12, pady=(8, 0))

        kpi_row = tk.Frame(kpi_frame, bg=Luxury2026Colors.BG_SECONDARY)
        kpi_row.pack(fill="x", padx=12, pady=(4, 8))

        for attr, label in [
            ("_lbl_stock",   "Stock actual"),
            ("_lbl_avg",     "Prom. diario"),
            ("_lbl_cob",     "Días cobertura"),
            ("_lbl_alerta",  "Alerta"),
            ("_lbl_quiebre", "Quiebre estimado"),
        ]:
            col = tk.Frame(kpi_row, bg=Luxury2026Colors.BG_SECONDARY)
            col.pack(side="left", padx=16)
            tk.Label(
                col, text=label,
                font=ModernTypography.font_caption(),
                bg=Luxury2026Colors.BG_SECONDARY,
                fg=Luxury2026Colors.TEXT_SECONDARY,
            ).pack()
            lbl = tk.Label(
                col, text="—",
                font=ModernTypography.font_body_bold(),
                bg=Luxury2026Colors.BG_SECONDARY,
                fg=Luxury2026Colors.TEXT_PRIMARY,
            )
            lbl.pack()
            setattr(self, attr, lbl)

        # Tabla predicción día a día
        frame_det = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY)
        frame_det.pack(fill="both", expand=True, padx=8, pady=4)

        cols_d = ("fecha", "qty_predicha")
        self._tree_det = ttk.Treeview(frame_det, columns=cols_d, show="headings", height=20)
        self._tree_det.heading("fecha", text="Fecha")
        self._tree_det.heading("qty_predicha", text="Demanda predicha (uds)")
        self._tree_det.column("fecha", width=160, anchor="center")
        self._tree_det.column("qty_predicha", width=200, anchor="center")
        theme.aplicar_estilo_treeview(self._tree_det)
        scrollbars.agregar_scrollbar(self._tree_det, frame_det)
        self._tree_det.pack(fill="both", expand=True)

    def _cargar_detalle(self):
        codigo = self._entry_cod.get().strip()
        if not codigo:
            messagebox.showwarning("Atención", "Ingresa el código del producto.", parent=self)
            return
        try:
            r = predecir_demanda(codigo)
        except Exception as e:
            logging.warning("PrediccionWindow _cargar_detalle: %s", e)
            messagebox.showerror("Error", str(e), parent=self)
            return

        if "error" in r:
            messagebox.showinfo(
                "Datos insuficientes",
                f"El producto '{codigo}' tiene solo {r.get('dias_datos', 0)} días con datos.\n"
                "Se necesitan al menos 14 días para predecir.",
                parent=self,
            )
            return

        color_alerta = {"CRITICO": _COLOR_CRITICO, "BAJO": _COLOR_BAJO, "OK": _COLOR_OK}
        self._lbl_nombre.config(text=f"{r['nombre']} ({r['codigo']})")
        self._lbl_stock.config(text=str(r["stock_actual"]))
        self._lbl_avg.config(text=f"{r['promedio_diario']:.2f}")
        self._lbl_cob.config(text=str(r["dias_cobertura"]))
        self._lbl_alerta.config(text=r["alerta"], fg=color_alerta.get(r["alerta"], "#FFFFFF"))
        self._lbl_quiebre.config(text=r.get("fecha_quiebre") or "—")

        for item in self._tree_det.get_children():
            self._tree_det.delete(item)
        for p in r.get("prediccion", []):
            self._tree_det.insert("", "end", values=(p["fecha"], p["qty_predicha"]))
