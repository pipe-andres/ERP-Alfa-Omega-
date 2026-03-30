import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta

from src.app.styles.luxury_2026 import Luxury2026Colors

_BG = getattr(Luxury2026Colors, "BG_DARKEST", "#0A0E27")
_FG = "white"
_ACCENT = getattr(Luxury2026Colors, "ACCENT", "#3B82F6")


class ReportsWindow(tk.Toplevel):
    def __init__(self, parent, user=None):
        super().__init__(parent)
        self.title("Reportes Avanzados")
        self.geometry("1100x650")
        self.configure(bg=_BG)
        self.transient(parent)
        self.grab_set()
        self.user = user
        
        # Guard de plan: ¿tiene reportes avanzados?
        self._advanced_ok = self._check_advanced_reports()
        
        self._build_ui()

    def _check_advanced_reports(self) -> bool:
        """Verifica si el plan del usuario actual incluye reportes avanzados."""
        try:
            from src.services.plans import check_feature_local
            # En SQLite fallback a 'free' si no hay user
            return check_feature_local(self.user or {"plan": "free"}, "advanced_reports")
        except Exception as e:
            import logging; logging.warning("reports_window plan check error: %s", e)
            return False  # Conservador por defecto

    def _build_ui(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)
        
        # Tabs controladas por el plan
        if self._advanced_ok:
            self._build_tab_pl()
            self._build_tab_abc()
            self._build_tab_margins()
        else:
            self._build_tab_upgrade_prompt()
            
        # Esta siempre está disponible
        self._build_tab_rotation()

    def _build_tab_upgrade_prompt(self):
        f = tk.Frame(self.tabs, bg=_BG)
        self.tabs.add(f, text="🔒 Reportes Avanzados")
        tk.Label(f, text="🔒", font=("Segoe UI Emoji", 48), bg=_BG, fg="#888").pack(pady=(80, 10))
        tk.Label(f, text="Reportes Avanzados no disponibles en tu plan actual",
                 font=("Arial", 16, "bold"), bg=_BG, fg="white").pack()
        tk.Label(f, text="Actualiza a Pro o Enterprise para desbloquear P&L, ABC y Márgenes.",
                 font=("Arial", 11), bg=_BG, fg="#888").pack(pady=8)

    def _build_tab_pl(self):
        f = tk.Frame(self.tabs, bg=_BG)
        self.tabs.add(f, text="📊 P&L")
        top = tk.Frame(f, bg=_BG)
        top.pack(fill="x", padx=10, pady=8)
        tk.Label(top, text="Desde:", bg=_BG, fg=_FG).pack(side="left")
        self.pl_from = tk.Entry(top, width=12)
        self.pl_from.insert(0, (datetime.now()-timedelta(days=30)).strftime("%Y-%m-%d"))
        self.pl_from.pack(side="left", padx=4)
        tk.Label(top, text="Hasta:", bg=_BG, fg=_FG).pack(side="left")
        self.pl_to = tk.Entry(top, width=12)
        self.pl_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.pl_to.pack(side="left", padx=4)
        ttk.Button(top, text="Generar", command=self._load_pl).pack(side="left", padx=8)
        ttk.Button(top, text="Exportar PDF", command=self._export_pl_pdf).pack(side="right", padx=4)
        ttk.Button(top, text="Exportar Excel", command=self._export_pl_excel).pack(side="right", padx=4)
        kpi_frame = tk.Frame(f, bg=_BG)
        kpi_frame.pack(fill="x", padx=10, pady=4)
        self.pl_kpis = {}
        for key, label in [("ventas","Ventas Brutas"),("costo","Costo Ventas"),
                           ("margen","Margen Bruto"),("margen_pct","Margen %"),
                           ("transacciones","Transacciones"),("ticket","Ticket Prom.")]:
            col = tk.Frame(kpi_frame, bg="#1a1f3a", relief="raised", bd=1)
            col.pack(side="left", expand=True, fill="both", padx=4, pady=4)
            tk.Label(col, text=label, bg="#1a1f3a", fg="#888", font=("Arial",8)).pack(pady=(6,0))
            lbl = tk.Label(col, text="—", bg="#1a1f3a", fg=_ACCENT, font=("Arial",14,"bold"))
            lbl.pack(pady=(0,6))
            self.pl_kpis[key] = lbl
        cols = ("period","num_sales","total_qty","total_sales","total_cost","total_margin","margin_pct")
        headers = ("Período","Ventas","Cant.","Ingresos","Costo","Margen","Margen%")
        self.tree_pl = ttk.Treeview(f, columns=cols, show="headings", height=12)
        for c, h in zip(cols, headers):
            self.tree_pl.heading(c, text=h)
            self.tree_pl.column(c, width=130)
        self.tree_pl.pack(fill="both", expand=True, padx=10, pady=6)

    def _load_pl(self):
        from src.services.reports import report_sales_by_period
        try:
            rows = report_sales_by_period(self.pl_from.get(), self.pl_to.get())
            self.tree_pl.delete(*self.tree_pl.get_children())
            total_v = total_c = total_m = total_t = 0
            for r in rows:
                self.tree_pl.insert("", "end", values=(
                    r["period"], r["num_sales"], f"{r['total_qty']:.0f}",
                    f"${r['total_sales']:,.0f}", f"${r['total_cost']:,.0f}",
                    f"${r['total_margin']:,.0f}", f"{r['margin_pct']:.1f}%"
                ))
                total_v += r["total_sales"]; total_c += r["total_cost"]
                total_m += r["total_margin"]; total_t += r["num_sales"]
            self.pl_kpis["ventas"].config(text=f"${total_v:,.0f}")
            self.pl_kpis["costo"].config(text=f"${total_c:,.0f}")
            self.pl_kpis["margen"].config(text=f"${total_m:,.0f}")
            self.pl_kpis["margen_pct"].config(text=f"{(total_m/total_v*100) if total_v else 0:.1f}%")
            self.pl_kpis["transacciones"].config(text=str(total_t))
            self.pl_kpis["ticket"].config(text=f"${(total_v/total_t) if total_t else 0:,.0f}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_pl_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if not path: return
        try:
            from src.services.reports import report_sales_by_period
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            rows_data = report_sales_by_period(self.pl_from.get(), self.pl_to.get())
            doc = SimpleDocTemplate(path, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = [Paragraph("Reporte P&L — Alfa & Omega", styles["Title"]),
                       Paragraph(f"Período: {self.pl_from.get()} al {self.pl_to.get()}", styles["Normal"]),
                       Spacer(1,12)]
            data = [["Período","Ventas","Ingresos","Costo","Margen","Margen%"]]
            for r in rows_data:
                data.append([r["period"], r["num_sales"], f"${r['total_sales']:,.0f}",
                            f"${r['total_cost']:,.0f}", f"${r['total_margin']:,.0f}",
                            f"{r['margin_pct']:.1f}%"])
            t = Table(data)
            t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#3B82F6")),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.5,colors.grey),
                ("FONTSIZE",(0,0),(-1,-1),8)]))
            elements.append(t)
            doc.build(elements)
            messagebox.showinfo("PDF", f"Exportado: {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_pl_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not path: return
        try:
            from src.services.reports import report_sales_by_period
            import openpyxl
            rows_data = report_sales_by_period(self.pl_from.get(), self.pl_to.get())
            wb = openpyxl.Workbook(); ws = wb.active; ws.title = "P&L"
            ws.append(["Período","Num Ventas","Cantidad","Ingresos","Costo","Margen","Margen%"])
            for r in rows_data:
                ws.append([r["period"],r["num_sales"],r["total_qty"],
                          r["total_sales"],r["total_cost"],r["total_margin"],r["margin_pct"]])
            wb.save(path)
            messagebox.showinfo("Excel", f"Exportado: {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _build_tab_abc(self):
        f = tk.Frame(self.tabs, bg=_BG)
        self.tabs.add(f, text="🔤 ABC Productos")
        top = tk.Frame(f, bg=_BG)
        top.pack(fill="x", padx=10, pady=8)
        tk.Label(top, text="Meses:", bg=_BG, fg=_FG).pack(side="left")
        self.abc_months = tk.Entry(top, width=5)
        self.abc_months.insert(0, "12")
        self.abc_months.pack(side="left", padx=4)
        ttk.Button(top, text="Generar", command=self._load_abc).pack(side="left", padx=8)
        ttk.Button(top, text="Exportar Excel", command=self._export_abc_excel).pack(side="right", padx=4)
        sum_frame = tk.Frame(f, bg=_BG)
        sum_frame.pack(fill="x", padx=10, pady=4)
        self.abc_summary = {}
        for cat, color in [("A","#16a34a"),("B","#d97706"),("C","#dc2626")]:
            col = tk.Frame(sum_frame, bg="#1a1f3a", relief="raised", bd=1)
            col.pack(side="left", expand=True, fill="both", padx=4)
            tk.Label(col, text=f"Categoría {cat}", bg="#1a1f3a",
                    fg=color, font=("Arial",12,"bold")).pack(pady=(6,0))
            lbl = tk.Label(col, text="—", bg="#1a1f3a", fg=_FG, font=("Arial",10))
            lbl.pack(pady=(0,6))
            self.abc_summary[cat] = lbl
        cols = ("codigo","nombre","ventas","pct","acum","categoria")
        headers = ("Código","Nombre","Ventas $","% Total","% Acum.","Cat.")
        self.tree_abc = ttk.Treeview(f, columns=cols, show="headings", height=14)
        for c, h in zip(cols, headers):
            self.tree_abc.heading(c, text=h)
            self.tree_abc.column(c, width=150 if c=="nombre" else 100)
        self.tree_abc.pack(fill="both", expand=True, padx=10, pady=6)
        self.tree_abc.tag_configure("A", foreground="#16a34a")
        self.tree_abc.tag_configure("B", foreground="#d97706")
        self.tree_abc.tag_configure("C", foreground="#dc2626")

    def _load_abc(self):
        from src.services.reports import report_abc_analysis
        try:
            data = report_abc_analysis(int(self.abc_months.get() or 12))
            self.tree_abc.delete(*self.tree_abc.get_children())
            total = data.get("total_sales", 1) or 1
            for cat in ["A","B","C"]:
                prods = data.get(cat, [])
                cat_sales = sum(p.get("ventas",0) for p in prods)
                self.abc_summary[cat].config(
                    text=f"{len(prods)} productos\n${cat_sales:,.0f} ({cat_sales/total*100:.1f}%)")
                for p in prods:
                    self.tree_abc.insert("", "end", tags=(cat,), values=(
                        p.get("codigo",""), p.get("nombre",""),
                        f"${p.get('ventas',0):,.0f}", f"{p.get('pct',0):.1f}%",
                        f"{p.get('acum',0):.1f}%", cat))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_abc_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not path: return
        try:
            from src.services.reports import report_abc_analysis
            import openpyxl
            data = report_abc_analysis(int(self.abc_months.get() or 12))
            wb = openpyxl.Workbook(); ws = wb.active; ws.title = "ABC"
            ws.append(["Categoría","Código","Nombre","Ventas","% Total","% Acum."])
            for cat in ["A","B","C"]:
                for p in data.get(cat,[]):
                    ws.append([cat,p.get("codigo"),p.get("nombre"),
                              p.get("ventas",0),p.get("pct",0),p.get("acum",0)])
            wb.save(path)
            messagebox.showinfo("Excel", f"Exportado: {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _build_tab_margins(self):
        f = tk.Frame(self.tabs, bg=_BG)
        self.tabs.add(f, text="💰 Márgenes")
        top = tk.Frame(f, bg=_BG)
        top.pack(fill="x", padx=10, pady=8)
        tk.Label(top, text="Desde:", bg=_BG, fg=_FG).pack(side="left")
        self.mg_from = tk.Entry(top, width=12)
        self.mg_from.insert(0, (datetime.now()-timedelta(days=30)).strftime("%Y-%m-%d"))
        self.mg_from.pack(side="left", padx=4)
        tk.Label(top, text="Hasta:", bg=_BG, fg=_FG).pack(side="left")
        self.mg_to = tk.Entry(top, width=12)
        self.mg_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.mg_to.pack(side="left", padx=4)
        tk.Label(top, text="Top:", bg=_BG, fg=_FG).pack(side="left")
        self.mg_limit = tk.Entry(top, width=5)
        self.mg_limit.insert(0, "20")
        self.mg_limit.pack(side="left", padx=4)
        ttk.Button(top, text="Generar", command=self._load_margins).pack(side="left", padx=8)
        ttk.Button(top, text="Exportar Excel", command=self._export_margins_excel).pack(side="right", padx=4)
        cols = ("codigo","nombre","qty","ventas","num_sales")
        headers = ("Código","Nombre","Cant.","Ventas $","Num Ventas")
        self.tree_mg = ttk.Treeview(f, columns=cols, show="headings", height=18)
        for c, h in zip(cols, headers):
            self.tree_mg.heading(c, text=h)
            self.tree_mg.column(c, width=150 if c=="nombre" else 110)
        self.tree_mg.pack(fill="both", expand=True, padx=10, pady=6)

    def _load_margins(self):
        from src.services.reports import report_top_products
        try:
            rows = report_top_products(int(self.mg_limit.get() or 20),
                                      self.mg_from.get(), self.mg_to.get())
            self.tree_mg.delete(*self.tree_mg.get_children())
            for r in rows:
                self.tree_mg.insert("", "end", values=(
                    r.get("codigo"), r.get("nombre"),
                    f"{r.get('qty',0):.0f}",
                    f"${r.get('ventas',0):,.0f}",
                    r.get("num_sales",0)))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_margins_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not path: return
        try:
            from src.services.reports import report_top_products
            import openpyxl
            rows = report_top_products(int(self.mg_limit.get() or 20),
                                      self.mg_from.get(), self.mg_to.get())
            wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Margenes"
            ws.append(["Código","Nombre","Cantidad","Ventas","Num Ventas"])
            for r in rows:
                ws.append([r.get("codigo"),r.get("nombre"),
                          r.get("qty"),r.get("ventas"),r.get("num_sales")])
            wb.save(path)
            messagebox.showinfo("Excel", f"Exportado: {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _build_tab_rotation(self):
        f = tk.Frame(self.tabs, bg=_BG)
        self.tabs.add(f, text="🔄 Rotación")
        top = tk.Frame(f, bg=_BG)
        top.pack(fill="x", padx=10, pady=8)
        tk.Label(top, text="Meses:", bg=_BG, fg=_FG).pack(side="left")
        self.rot_months = tk.Entry(top, width=5)
        self.rot_months.insert(0, "12")
        self.rot_months.pack(side="left", padx=4)
        ttk.Button(top, text="Generar", command=self._load_rotation).pack(side="left", padx=8)
        ttk.Button(top, text="Exportar Excel", command=self._export_rotation_excel).pack(side="right", padx=4)
        kpi_frame = tk.Frame(f, bg=_BG)
        kpi_frame.pack(fill="x", padx=10, pady=4)
        self.rot_kpis = {}
        for key, label in [("turnover","Turnover Rate"),("days","Días para vender"),
                           ("active","Productos activos"),("slow","Productos lentos")]:
            col = tk.Frame(kpi_frame, bg="#1a1f3a", relief="raised", bd=1)
            col.pack(side="left", expand=True, fill="both", padx=4)
            tk.Label(col, text=label, bg="#1a1f3a", fg="#888", font=("Arial",8)).pack(pady=(6,0))
            lbl = tk.Label(col, text="—", bg="#1a1f3a", fg=_ACCENT, font=("Arial",14,"bold"))
            lbl.pack(pady=(0,6))
            self.rot_kpis[key] = lbl
        tk.Label(f, text="Productos de lenta rotación:", bg=_BG, fg=_FG,
                font=("Arial",10,"bold")).pack(anchor="w", padx=10)
        cols = ("codigo","nombre","stock","ventas_period","dias_cobertura")
        headers = ("Código","Nombre","Stock actual","Ventas período","Días cobertura")
        self.tree_rot = ttk.Treeview(f, columns=cols, show="headings", height=12)
        for c, h in zip(cols, headers):
            self.tree_rot.heading(c, text=h)
            self.tree_rot.column(c, width=160 if c=="nombre" else 110)
        self.tree_rot.pack(fill="both", expand=True, padx=10, pady=6)

    def _load_rotation(self):
        from src.services.reports import report_inventory_rotation
        try:
            data = report_inventory_rotation(int(self.rot_months.get() or 12))
            self.rot_kpis["turnover"].config(text=f"{data.get('turnover_rate',0):.2f}x")
            self.rot_kpis["days"].config(text=f"{data.get('days_to_sell',0):.0f}")
            self.rot_kpis["active"].config(text=str(data.get("active_products",0)))
            slow = data.get("slow_moving_products", [])
            self.rot_kpis["slow"].config(text=str(len(slow)))
            self.tree_rot.delete(*self.tree_rot.get_children())
            for p in slow:
                self.tree_rot.insert("", "end", values=(
                    p.get("codigo",""), p.get("nombre",""),
                    f"{p.get('stock',0):.0f}",
                    f"{p.get('ventas_period',0):.0f}",
                    f"{p.get('dias_cobertura',0):.0f}"))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_rotation_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not path: return
        try:
            from src.services.reports import report_inventory_rotation
            import openpyxl
            data = report_inventory_rotation(int(self.rot_months.get() or 12))
            wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Rotacion"
            ws.append(["Código","Nombre","Stock","Ventas Período","Días Cobertura"])
            for p in data.get("slow_moving_products", []):
                ws.append([p.get("codigo"),p.get("nombre"),
                          p.get("stock"),p.get("ventas_period"),p.get("dias_cobertura")])
            wb.save(path)
            messagebox.showinfo("Excel", f"Exportado: {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
