"""
src/app/finanzas_window.py
===========================
Tarea 14 — GUI del módulo Finanzas.

class FinanzasWindow(tk.Toplevel)
Tabs: CxC | CxP | Flujo de Caja
Cero queries en GUI — toda la lógica en src/services/finanzas.py
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from src.app.components_luxury import Tooltip
from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography
from src.services.finanzas import (
    get_cxc, get_cxp, get_flujo_caja,
    get_resumen_cxc, get_resumen_cxp,
    registrar_cobro, registrar_pago,
)

_LOG = logging.getLogger(__name__)

C = Luxury2026Colors
T = ModernTypography

_ESTADO_COLORES = {
    "PENDIENTE": C.WARNING,
    "PAGADO":    C.ACCENT,
    "VENCIDO":   C.DANGER,
}


class FinanzasWindow(tk.Toplevel):
    """Ventana principal de Finanzas: CxC, CxP y Flujo de Caja."""

    def __init__(self, master):
        super().__init__(master)
        self.title("💰 Finanzas — CxC · CxP · Flujo de Caja")
        self.geometry("1100x720")
        self.configure(bg=C.BG_DARKEST)
        self.resizable(True, True)

        # Encabezado
        hdr = tk.Frame(self, bg=C.BG_DARK)
        hdr.pack(fill="x", padx=0, pady=0)
        tk.Label(
            hdr, text="💰 Finanzas",
            font=T.font_heading_xl(),
            bg=C.BG_DARK, fg=C.PRIMARY
        ).pack(side="left", padx=16, pady=10)
        tk.Label(
            hdr, text="Cuentas por Cobrar · Cuentas por Pagar · Flujo de Caja",
            font=T.font_body_small(),
            bg=C.BG_DARK, fg=C.TEXT_SECONDARY
        ).pack(side="left", padx=4, pady=10)

        # Notebook
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=10, pady=8)

        self._build_tab_cxc()
        self._build_tab_cxp()
        self._build_tab_flujo()

        # Carga inicial
        self._reload_cxc()
        self._reload_cxp()
        self._reload_flujo()

    # ──────────────────────────────────────────────
    # Tab CxC
    # ──────────────────────────────────────────────
    def _build_tab_cxc(self):
        tab = tk.Frame(self._nb, bg=C.BG_DARKEST)
        self._nb.add(tab, text="📥 Cuentas × Cobrar")

        # Resumen cards
        frm = tk.Frame(tab, bg=C.BG_SECONDARY, relief="solid", bd=1)
        frm.pack(fill="x", padx=6, pady=6)
        tk.Label(frm, text="📊 Resumen CxC",
                 font=T.font_body_bold(), bg=C.BG_SECONDARY, fg=C.PRIMARY
                 ).pack(anchor="w", padx=12, pady=(8, 0))
        cards_row = tk.Frame(frm, bg=C.BG_SECONDARY)
        cards_row.pack(fill="x", padx=12, pady=(4, 12))
        self._lbl_cxc_total   = self._make_card(cards_row, "Total CxC",   "$0.00", C.PRIMARY)
        self._lbl_cxc_vencido = self._make_card(cards_row, "Vencido",     "$0.00", C.DANGER)
        self._lbl_cxc_xvencer = self._make_card(cards_row, "Por Vencer",  "$0.00", C.WARNING)
        self._lbl_cxc_count   = self._make_card(cards_row, "Documentos",  "0",     C.TEXT_SECONDARY)
        Tooltip(self._lbl_cxc_total, "Suma total de facturas pendientes de cobro")
        Tooltip(self._lbl_cxc_vencido, "Documentos cuya fecha de vencimiento ya pasó\n⚠️ Requieren gestión urgente de cobro")
        Tooltip(self._lbl_cxc_xvencer, "Documentos que vencen en los próximos 30 días\nProgramar recordatorios a clientes")
        Tooltip(self._lbl_cxc_count, "Número total de documentos\npendientes de cobro")

        # Filtro
        filter_row = tk.Frame(tab, bg=C.BG_DARKEST)
        filter_row.pack(fill="x", padx=6, pady=(0, 4))
        tk.Label(filter_row, text="Estado:", font=T.font_body_small(),
                 bg=C.BG_DARKEST, fg=C.TEXT_SECONDARY).pack(side="left")
        self._combo_cxc_estado = ttk.Combobox(
            filter_row, values=["Todos", "PENDIENTE", "PAGADO", "VENCIDO"],
            state="readonly", width=12
        )
        self._combo_cxc_estado.set("Todos")
        self._combo_cxc_estado.pack(side="left", padx=6)
        self._combo_cxc_estado.bind("<<ComboboxSelected>>", lambda e: self._reload_cxc())

        # Tabla
        cols  = ("id", "partner_name", "documento", "monto", "saldo", "fecha_vencimiento", "estado")
        heads = ("ID", "Cliente", "Documento", "Monto", "Saldo", "Vencimiento", "Estado")
        widths = (50, 200, 120, 100, 100, 110, 90)
        self._tree_cxc, _ = self._make_tree(tab, cols, heads, widths)

        # Botones
        btns = tk.Frame(tab, bg=C.BG_DARKEST)
        btns.pack(fill="x", padx=6, pady=6)
        ttk.Button(btns, text="✅ Registrar Cobro",
                   command=self._accion_cobro,
                   style="Luxury.Primary.TButton").pack(side="left", padx=4)
        ttk.Button(btns, text="↻ Actualizar",
                   command=self._reload_cxc,
                   style="Luxury.Secondary.TButton").pack(side="left", padx=4)
        ttk.Button(btns, text="📥 Excel",
                   command=self._exportar_cxc,
                   style="Luxury.Secondary.TButton").pack(side="right", padx=4)

    # ──────────────────────────────────────────────
    # Tab CxP
    # ──────────────────────────────────────────────
    def _build_tab_cxp(self):
        tab = tk.Frame(self._nb, bg=C.BG_DARKEST)
        self._nb.add(tab, text="📤 Cuentas × Pagar")

        frm = tk.Frame(tab, bg=C.BG_SECONDARY, relief="solid", bd=1)
        frm.pack(fill="x", padx=6, pady=6)
        tk.Label(frm, text="📊 Resumen CxP",
                 font=T.font_body_bold(), bg=C.BG_SECONDARY, fg=C.PRIMARY
                 ).pack(anchor="w", padx=12, pady=(8, 0))
        cards_row = tk.Frame(frm, bg=C.BG_SECONDARY)
        cards_row.pack(fill="x", padx=12, pady=(4, 12))
        self._lbl_cxp_total   = self._make_card(cards_row, "Total CxP",  "$0.00", C.PRIMARY)
        self._lbl_cxp_vencido = self._make_card(cards_row, "Vencido",    "$0.00", C.DANGER)
        self._lbl_cxp_xvencer = self._make_card(cards_row, "Por Vencer", "$0.00", C.WARNING)
        self._lbl_cxp_count   = self._make_card(cards_row, "Documentos", "0",     C.TEXT_SECONDARY)
        Tooltip(self._lbl_cxp_total, "Suma total de facturas pendientes de pago\na proveedores")
        Tooltip(self._lbl_cxp_vencido, "Pagos vencidos a proveedores\n⚠️ Riesgo de bloqueo de crédito")
        Tooltip(self._lbl_cxp_xvencer, "Pagos que vencen en los próximos 30 días\nPlanificar flujo de caja")
        Tooltip(self._lbl_cxp_count, "Número total de documentos\npendientes de pago")

        filter_row = tk.Frame(tab, bg=C.BG_DARKEST)
        filter_row.pack(fill="x", padx=6, pady=(0, 4))
        tk.Label(filter_row, text="Estado:", font=T.font_body_small(),
                 bg=C.BG_DARKEST, fg=C.TEXT_SECONDARY).pack(side="left")
        self._combo_cxp_estado = ttk.Combobox(
            filter_row, values=["Todos", "PENDIENTE", "PAGADO", "VENCIDO"],
            state="readonly", width=12
        )
        self._combo_cxp_estado.set("Todos")
        self._combo_cxp_estado.pack(side="left", padx=6)
        self._combo_cxp_estado.bind("<<ComboboxSelected>>", lambda e: self._reload_cxp())

        cols  = ("id", "partner_name", "documento", "monto", "saldo", "fecha_vencimiento", "estado")
        heads = ("ID", "Proveedor", "Documento", "Monto", "Saldo", "Vencimiento", "Estado")
        widths = (50, 200, 120, 100, 100, 110, 90)
        self._tree_cxp, _ = self._make_tree(tab, cols, heads, widths)

        btns = tk.Frame(tab, bg=C.BG_DARKEST)
        btns.pack(fill="x", padx=6, pady=6)
        ttk.Button(btns, text="💸 Registrar Pago",
                   command=self._accion_pago,
                   style="Luxury.Primary.TButton").pack(side="left", padx=4)
        ttk.Button(btns, text="↻ Actualizar",
                   command=self._reload_cxp,
                   style="Luxury.Secondary.TButton").pack(side="left", padx=4)
        ttk.Button(btns, text="📥 Excel",
                   command=self._exportar_cxp,
                   style="Luxury.Secondary.TButton").pack(side="right", padx=4)

    # ──────────────────────────────────────────────
    # Tab Flujo de Caja
    # ──────────────────────────────────────────────
    def _build_tab_flujo(self):
        tab = tk.Frame(self._nb, bg=C.BG_DARKEST)
        self._nb.add(tab, text="📈 Flujo de Caja")

        # Controles periodo
        ctrl = tk.Frame(tab, bg=C.BG_SECONDARY, relief="solid", bd=1)
        ctrl.pack(fill="x", padx=6, pady=6)
        tk.Label(ctrl, text="📅 Periodo", font=T.font_body_bold(),
                 bg=C.BG_SECONDARY, fg=C.PRIMARY).pack(anchor="w", padx=12, pady=(8, 0))
        btn_row = tk.Frame(ctrl, bg=C.BG_SECONDARY)
        btn_row.pack(fill="x", padx=12, pady=(4, 12))
        self._dias_flujo = tk.IntVar(value=30)
        for label, dias in [("Últimos 7d", 7), ("Últimos 15d", 15), ("Últimos 30d", 30)]:
            ttk.Radiobutton(
                btn_row, text=label, variable=self._dias_flujo, value=dias,
                command=self._reload_flujo
            ).pack(side="left", padx=8)

        # Totales
        tot_frm = tk.Frame(tab, bg=C.BG_SECONDARY, relief="solid", bd=1)
        tot_frm.pack(fill="x", padx=6, pady=(0, 6))
        tk.Label(tot_frm, text="💹 Totales del periodo",
                 font=T.font_body_bold(), bg=C.BG_SECONDARY, fg=C.PRIMARY
                 ).pack(anchor="w", padx=12, pady=(8, 0))
        tot_row = tk.Frame(tot_frm, bg=C.BG_SECONDARY)
        tot_row.pack(fill="x", padx=12, pady=(4, 12))
        self._lbl_flujo_ing = self._make_card(tot_row, "Total Ingresos", "$0.00", C.ACCENT)
        self._lbl_flujo_egr = self._make_card(tot_row, "Total Egresos",  "$0.00", C.DANGER)
        self._lbl_flujo_net = self._make_card(tot_row, "Flujo Neto",     "$0.00", C.PRIMARY)
        Tooltip(self._lbl_flujo_ing, "Total de ingresos en el período seleccionado")
        Tooltip(self._lbl_flujo_egr, "Total de egresos en el período seleccionado")
        Tooltip(self._lbl_flujo_net, "Flujo neto = Ingresos - Egresos\nPositivo=superávit · Negativo=déficit")

        # Tabla
        cols  = ("fecha", "ingresos", "egresos", "saldo_dia")
        heads = ("Fecha", "Ingresos", "Egresos", "Saldo Día")
        widths = (130, 140, 140, 140)
        self._tree_flujo, _ = self._make_tree(tab, cols, heads, widths)

    # ──────────────────────────────────────────────
    # Recargas
    # ──────────────────────────────────────────────
    def _reload_cxc(self):
        try:
            sel = self._combo_cxc_estado.get()
            estado = None if sel == "Todos" else sel
            rows    = get_cxc(estado)
            resumen = get_resumen_cxc()

            self._lbl_cxc_total.config(text=f"${resumen['total']:,.2f}")
            self._lbl_cxc_vencido.config(text=f"${resumen['vencido']:,.2f}")
            self._lbl_cxc_xvencer.config(text=f"${resumen['por_vencer']:,.2f}")
            self._lbl_cxc_count.config(text=str(resumen["count"]))

            self._tree_cxc.delete(*self._tree_cxc.get_children())
            for r in rows:
                tag = r.get("estado", "")
                self._tree_cxc.insert("", "end", values=(
                    r.get("id", ""),
                    r.get("partner_name") or "—",
                    r.get("documento") or "—",
                    f"${r.get('monto', 0):,.2f}",
                    f"${r.get('saldo', 0):,.2f}",
                    r.get("fecha_vencimiento") or "—",
                    tag,
                ), tags=(tag,))
            for etag, color in _ESTADO_COLORES.items():
                self._tree_cxc.tag_configure(etag, foreground=color)
        except Exception as e:
            logging.warning("_reload_cxc error: %s", e)
            messagebox.showerror("Error CxC", str(e), parent=self)

    def _reload_cxp(self):
        try:
            sel = self._combo_cxp_estado.get()
            estado = None if sel == "Todos" else sel
            rows    = get_cxp(estado)
            resumen = get_resumen_cxp()

            self._lbl_cxp_total.config(text=f"${resumen['total']:,.2f}")
            self._lbl_cxp_vencido.config(text=f"${resumen['vencido']:,.2f}")
            self._lbl_cxp_xvencer.config(text=f"${resumen['por_vencer']:,.2f}")
            self._lbl_cxp_count.config(text=str(resumen["count"]))

            self._tree_cxp.delete(*self._tree_cxp.get_children())
            for r in rows:
                tag = r.get("estado", "")
                self._tree_cxp.insert("", "end", values=(
                    r.get("id", ""),
                    r.get("partner_name") or "—",
                    r.get("documento") or "—",
                    f"${r.get('monto', 0):,.2f}",
                    f"${r.get('saldo', 0):,.2f}",
                    r.get("fecha_vencimiento") or "—",
                    tag,
                ), tags=(tag,))
            for etag, color in _ESTADO_COLORES.items():
                self._tree_cxp.tag_configure(etag, foreground=color)
        except Exception as e:
            logging.warning("_reload_cxp error: %s", e)
            messagebox.showerror("Error CxP", str(e), parent=self)

    def _reload_flujo(self):
        try:
            dias = self._dias_flujo.get()
            rows = get_flujo_caja(dias)

            total_ing = sum(r["ingresos"] for r in rows)
            total_egr = sum(r["egresos"]  for r in rows)
            neto      = round(total_ing - total_egr, 2)

            self._lbl_flujo_ing.config(text=f"${total_ing:,.2f}")
            self._lbl_flujo_egr.config(text=f"${total_egr:,.2f}")
            self._lbl_flujo_net.config(
                text=f"${neto:,.2f}",
                fg=C.ACCENT if neto >= 0 else C.DANGER
            )

            self._tree_flujo.delete(*self._tree_flujo.get_children())
            for r in rows:
                saldo = r["saldo_dia"]
                tag = "pos" if saldo >= 0 else "neg"
                self._tree_flujo.insert("", "end", values=(
                    r["fecha"],
                    f"${r['ingresos']:,.2f}",
                    f"${r['egresos']:,.2f}",
                    f"${saldo:,.2f}",
                ), tags=(tag,))
            self._tree_flujo.tag_configure("pos", foreground=C.ACCENT)
            self._tree_flujo.tag_configure("neg", foreground=C.DANGER)
        except Exception as e:
            logging.warning("_reload_flujo error: %s", e)
            messagebox.showerror("Error Flujo", str(e), parent=self)

    # ──────────────────────────────────────────────
    # Acciones
    # ──────────────────────────────────────────────
    def _accion_cobro(self):
        sel = self._tree_cxc.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona una CxC primero.", parent=self)
            return
        cxc_id = int(self._tree_cxc.item(sel[0])["values"][0])
        monto_str = simpledialog.askstring(
            "Registrar Cobro", "Monto a cobrar:", parent=self
        )
        if not monto_str:
            return
        try:
            monto = float(monto_str.replace(",", "."))
            registrar_cobro(cxc_id, monto)
            messagebox.showinfo("✅ Cobro registrado", f"Cobro de ${monto:,.2f} registrado.", parent=self)
            self._reload_cxc()
        except Exception as e:
            logging.warning("_accion_cobro error: %s", e)
            messagebox.showerror("Error", str(e), parent=self)

    def _accion_pago(self):
        sel = self._tree_cxp.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona una CxP primero.", parent=self)
            return
        cxp_id = int(self._tree_cxp.item(sel[0])["values"][0])
        monto_str = simpledialog.askstring(
            "Registrar Pago", "Monto a pagar:", parent=self
        )
        if not monto_str:
            return
        try:
            monto = float(monto_str.replace(",", "."))
            registrar_pago(cxp_id, monto)
            messagebox.showinfo("✅ Pago registrado", f"Pago de ${monto:,.2f} registrado.", parent=self)
            self._reload_cxp()
        except Exception as e:
            logging.warning("_accion_pago error: %s", e)
            messagebox.showerror("Error", str(e), parent=self)

    # ──────────────────────────────────────────────
    # Helpers UI
    # ──────────────────────────────────────────────
    def _exportar_cxc(self):
        from tkinter import filedialog, messagebox
        import openpyxl
        cols = ["ID", "Cliente", "Documento", "Monto", "Saldo", "Vencimiento", "Estado"]
        filas = [self._tree_cxc.item(i)["values"] for i in self._tree_cxc.get_children()]
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
            initialfile="cuentas_por_cobrar.xlsx", title="Exportar CxC"
        )
        if not path: return
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "CxC"
        ws.append(cols)
        for f in filas: ws.append(list(f))
        wb.save(path)
        messagebox.showinfo("✅ Exportado", f"Archivo guardado:\n{path}", parent=self)

    def _exportar_cxp(self):
        from tkinter import filedialog, messagebox
        import openpyxl
        cols = ["ID", "Proveedor", "Documento", "Monto", "Saldo", "Vencimiento", "Estado"]
        filas = [self._tree_cxp.item(i)["values"] for i in self._tree_cxp.get_children()]
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
            initialfile="cuentas_por_pagar.xlsx", title="Exportar CxP"
        )
        if not path: return
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "CxP"
        ws.append(cols)
        for f in filas: ws.append(list(f))
        wb.save(path)
        messagebox.showinfo("✅ Exportado", f"Archivo guardado:\n{path}", parent=self)

    def _make_card(self, parent, label: str, valor: str, color: str) -> tk.Label:
        """Mini-card con etiqueta + valor grande. Retorna el Label del valor."""
        frame = tk.Frame(parent, bg=C.BG_TERTIARY, relief="solid", bd=1)
        frame.pack(side="left", padx=6, pady=4, ipadx=12, ipady=8)
        tk.Label(frame, text=label, font=T.font_caption(),
                 bg=C.BG_TERTIARY, fg=C.TEXT_SECONDARY).pack(anchor="w")
        lbl_val = tk.Label(frame, text=valor, font=T.font_heading(),
                           bg=C.BG_TERTIARY, fg=color)
        lbl_val.pack(anchor="w")
        return lbl_val

    def _make_tree(self, parent, cols, heads, widths):
        """Treeview con scrollbar. Retorna (tree, frame)."""
        frame = tk.Frame(parent, bg=C.BG_SECONDARY, relief="solid", bd=1)
        frame.pack(fill="both", expand=True, padx=6, pady=4)
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col, head, w in zip(cols, heads, widths):
            tree.heading(col, text=head)
            tree.column(col, width=w,
                        anchor="w" if col in ("partner_name", "documento", "fecha") else "e")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        return tree, frame
