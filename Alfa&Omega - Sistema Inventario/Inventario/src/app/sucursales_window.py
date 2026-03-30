import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from typing import Dict, Any
from src.app.components_luxury import Tooltip

from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography
from src.app.styles import theme, scrollbars

from tkinter import filedialog
import csv

# Servicios de inventario
from src.services.warehouses import (
    create_warehouse, list_warehouses, delete_warehouse, 
    get_detailed_stock, get_stock_consolidado
)
from src.services.transfers import transfer_stock, get_recent_transfers
from src.services.inventory import list_products_page

_LOG = logging.getLogger(__name__)

class SucursalesWindow(tk.Toplevel):
    def __init__(self, master, current_user: Dict[str, Any]):
        super().__init__(master)
        self.title("🏢 Gestión Multi-sucursal")
        self.geometry("1000x750")
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        self.current_user = current_user
        
        # Header Enamorante
        hdr = tk.Frame(self, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        hdr.pack(fill="x", pady=0)
        tk.Label(hdr, text="Gestión Avanzada de Sucursales", font=ModernTypography.font_heading_lg(),
                 bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY).pack(anchor="center", padx=16, pady=16)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=12, pady=12)
        
        # Pestañas
        self.tab_sucursales = tk.Frame(self.nb, bg=Luxury2026Colors.BG_DARKEST)
        self.nb.add(self.tab_sucursales, text="🏢 Mis Sucursales")
        self._build_sucursales_tab(self.tab_sucursales)

        self.tab_stock = tk.Frame(self.nb, bg=Luxury2026Colors.BG_DARKEST)
        self.nb.add(self.tab_stock, text="📦 Stock por Sucursal")
        self._build_stock_tab(self.tab_stock)

        self.tab_transfer = tk.Frame(self.nb, bg=Luxury2026Colors.BG_DARKEST)
        self.nb.add(self.tab_transfer, text="🔁 Transferencias")
        self._build_transfer_tab(self.tab_transfer)
        
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_change)

        # Cargas iniciales principales
        self._load_sucursales()

        self.transient(master)
        self.grab_set()

    # ==========================
    # TAB 1: SUCURSALES
    # ==========================
    def _build_sucursales_tab(self, parent: tk.Frame):
        # Tools
        tb = tk.Frame(parent, bg=Luxury2026Colors.BG_DARKEST)
        tb.pack(fill="x", pady=(12, 6))
        
        ttk.Button(tb, text="✨ Nueva Sucursal", command=self._action_new_sucursal, style='Luxury.Primary.TButton').pack(side="left", padx=4)
        ttk.Button(tb, text="🗑️ Eliminar", command=self._action_del_sucursal, style='Luxury.Danger.TButton').pack(side="left", padx=4)
        
        # Tabla
        frame_tv = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame_tv.pack(fill="both", expand=True, pady=6)
        
        cols = ("id", "nombre", "ubicacion")
        self.tv_sucursales = ttk.Treeview(frame_tv, columns=cols, show="headings", height=15)
        for c in cols:
            self.tv_sucursales.heading(c, text=c.capitalize())
        self.tv_sucursales.column("id", width=60, anchor="center")
        self.tv_sucursales.column("nombre", width=300, anchor="w")
        self.tv_sucursales.column("ubicacion", width=450, anchor="w")
        
        self.tv_sucursales.pack(fill="both", expand=True, padx=2, pady=2)
        theme.aplicar_estilo_treeview(self.tv_sucursales)
        scrollbars.agregar_scrollbar(self.tv_sucursales, frame_tv)
        self.tv_sucursales.tag_configure("activa",   foreground="#10B981")
        self.tv_sucursales.tag_configure("inactiva", foreground="#6B7280")

    def _load_sucursales(self):
        for item in self.tv_sucursales.get_children():
            self.tv_sucursales.delete(item)
        try:
            sucs = list_warehouses()
            for s in sucs:
                tag = "activa" if s.get("active", True) else "inactiva"
                self.tv_sucursales.insert("", "end", values=(s['id'], s['name'], s['location']), tags=(tag,))
            # Alimentar combos
            self._update_combos_sucursales(sucs)
        except Exception as e:
            _LOG.error("Error al cargar sucursales: %s", e)
            messagebox.showerror("Error", f"Fallo al cargar memoria de sucursales: {e}")

    def _action_new_sucursal(self):
        name = simpledialog.askstring("Nueva Sucursal", "Nombre de la sucursal:", parent=self)
        if not name: return
        loc = simpledialog.askstring("Nueva Sucursal", "Ubicación (opcional):", parent=self) or ""
        try:
            create_warehouse(name, loc, self.current_user)
            messagebox.showinfo("Éxito", f"Sucursal '{name}' creada.")
            self._load_sucursales()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _action_del_sucursal(self):
        sel = self.tv_sucursales.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione una sucursal para eliminar.")
            return
        item = self.tv_sucursales.item(sel[0])
        wid = item['values'][0]
        wnm = item['values'][1]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar la sucursal '{wnm}'?"):
            try:
                delete_warehouse(wid, self.current_user["id"])
                messagebox.showinfo("Éxito", "Sucursal eliminada.")
                self._load_sucursales()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar (verifique si tiene stock asignado):\n{e}")

    # ==========================
    # TAB 2: STOCK POR SUCURSAL
    # ==========================
    def _build_stock_tab(self, parent: tk.Frame):
        filters = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        filters.pack(fill="x", pady=(12, 6))
        
        tk.Label(filters, text="🏢 Seleccione sucursal:", font=ModernTypography.font_body_bold(),
                 bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_PRIMARY).pack(side="left", padx=12, pady=12)
        
        self.cmb_stock_suc = ttk.Combobox(filters, state="readonly", width=40)
        self.cmb_stock_suc.pack(side="left", padx=4, pady=12)
        ttk.Button(filters, text="↻ Actualizar", command=self._load_stock_detail, style='Luxury.Primary.TButton').pack(side="left", padx=12, pady=12)
        ttk.Button(filters, text="📊 Ver Consolidado", command=self._open_consolidado_window, style='Luxury.Success.TButton').pack(side="left", padx=12, pady=12)

        # Tabla de stock
        frame_tv = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame_tv.pack(fill="both", expand=True, pady=6)
        
        cols = ("codigo", "producto", "stock")
        self.tv_stock = ttk.Treeview(frame_tv, columns=cols, show="headings")
        for c in cols:
            self.tv_stock.heading(c, text=c.capitalize())
        self.tv_stock.column("codigo", width=120, anchor="w")
        self.tv_stock.column("producto", width=500, anchor="w")
        self.tv_stock.column("stock", width=100, anchor="e")
        
        self.tv_stock.pack(fill="both", expand=True, padx=2, pady=2)
        theme.aplicar_estilo_treeview(self.tv_stock)
        scrollbars.agregar_scrollbar(self.tv_stock, frame_tv)
        self.tv_stock.tag_configure("critico", foreground="#EF4444")
        self.tv_stock.tag_configure("bajo",    foreground="#F59E0B")
        self.tv_stock.tag_configure("ok",      foreground="#10B981")

    def _load_stock_detail(self):
        val = self.cmb_stock_suc.get()
        if not val:
            return
        wid = int(val.split(" - ")[0])
        
        for item in self.tv_stock.get_children():
            self.tv_stock.delete(item)
            
        try:
            items = get_detailed_stock(wid)
            for it in items:
                qty = it.get('stock', 0)
                tag = "critico" if qty <= 0 else "bajo" if qty <= 5 else "ok"
                self.tv_stock.insert("", "end", values=(it['codigo'], it['producto'], it['stock']), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el stock:\n{e}")

    # ==========================
    # TAB 3: TRANSFERENCIAS
    # ==========================
    def _build_transfer_tab(self, parent: tk.Frame):
        form = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        form.pack(fill="x", pady=(12, 6))
        
        # Fila 1: Producto
        row1 = tk.Frame(form, bg=Luxury2026Colors.BG_SECONDARY)
        row1.pack(fill="x", padx=12, pady=(12, 4))
        tk.Label(row1, text="Código de Producto:", width=20, anchor="w", font=ModernTypography.font_body_bold(),
                 bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_PRIMARY).pack(side="left")
        self.ent_trans_prod = tk.Entry(row1, width=20, font=ModernTypography.font_body(),
                                       bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                       insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.ent_trans_prod.pack(side="left", padx=4)
        
        ttk.Button(row1, text="🔍 Buscar Prod.", command=self._search_product_for_transfer, style='Luxury.Secondary.TButton').pack(side="left", padx=4)
        self.lbl_trans_prod_name = tk.Label(row1, text="...", font=ModernTypography.font_body(),
                                            bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.ACCENT)
        self.lbl_trans_prod_name.pack(side="left", padx=12)
        Tooltip(self.lbl_trans_prod_name, "Nombre del producto a transferir\nentre sucursales")

        # Fila 2: Bodegas y Cantidad
        row2 = tk.Frame(form, bg=Luxury2026Colors.BG_SECONDARY)
        row2.pack(fill="x", padx=12, pady=4)
        
        tk.Label(row2, text="Origen:", font=ModernTypography.font_body(), bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_PRIMARY).pack(side="left")
        self.cmb_origen = ttk.Combobox(row2, state="readonly", width=25)
        self.cmb_origen.pack(side="left", padx=4)
        
        tk.Label(row2, text="Destino:", font=ModernTypography.font_body(), bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_PRIMARY).pack(side="left", padx=(16, 0))
        self.cmb_destino = ttk.Combobox(row2, state="readonly", width=25)
        self.cmb_destino.pack(side="left", padx=4)
        
        tk.Label(row2, text="Cant:", font=ModernTypography.font_body(), bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_PRIMARY).pack(side="left", padx=(16, 0))
        self.ent_trans_qty = tk.Entry(row2, width=8, font=ModernTypography.font_body(),
                                     bg=Luxury2026Colors.BG_TERTIARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                     insertbackground=Luxury2026Colors.PRIMARY, relief="solid", bd=1)
        self.ent_trans_qty.pack(side="left", padx=4)

        # Fila 3: Botón ejecutar
        row3 = tk.Frame(form, bg=Luxury2026Colors.BG_SECONDARY)
        row3.pack(fill="x", padx=12, pady=(4, 12))
        ttk.Button(row3, text="🚀 CONFIRMAR TRANSFERENCIA", command=self._action_transfer, style='Luxury.Primary.TButton').pack(side="left")

        # Historial de transferencias
        hist_title = tk.Label(parent, text="📋 Últimas Transferencias", font=ModernTypography.font_body_bold(),
                             bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.ACCENT)
        hist_title.pack(anchor="w", pady=(12, 4))
        
        frame_tv = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame_tv.pack(fill="both", expand=True)
        
        cols = ("fecha", "codigo", "producto", "origen", "destino", "cantidad")
        self.tv_transfer = ttk.Treeview(frame_tv, columns=cols, show="headings", height=8)
        for c in cols:
            self.tv_transfer.heading(c, text=c.capitalize())
        
        self.tv_transfer.column("fecha", width=140, anchor="center")
        self.tv_transfer.column("codigo", width=120, anchor="w")
        self.tv_transfer.column("producto", width=250, anchor="w")
        self.tv_transfer.column("origen", width=150, anchor="w")
        self.tv_transfer.column("destino", width=150, anchor="w")
        self.tv_transfer.column("cantidad", width=80, anchor="e")
        
        self.tv_transfer.pack(fill="both", expand=True, padx=2, pady=2)
        theme.aplicar_estilo_treeview(self.tv_transfer)
        scrollbars.agregar_scrollbar(self.tv_transfer, frame_tv)
        self.tv_transfer.tag_configure("PENDIENTE",  foreground="#F59E0B")
        self.tv_transfer.tag_configure("COMPLETADA", foreground="#10B981")
        self.tv_transfer.tag_configure("CANCELADA",  foreground="#6B7280")

    def _search_product_for_transfer(self):
        cod = self.ent_trans_prod.get().strip()
        if not cod: return
        res, _ = list_products_page(page=1, size=1, query=cod, filter_by="codigo")
        if res:
            self.lbl_trans_prod_name.config(text=res[0]['nombre'])
        else:
            self.lbl_trans_prod_name.config(text="❌ No encontrado")

    def _action_transfer(self):
        cod = self.ent_trans_prod.get().strip()
        ori = self.cmb_origen.get()
        des = self.cmb_destino.get()
        qty = self.ent_trans_qty.get()
        
        if not (cod and ori and des and qty):
            messagebox.showwarning("Incompleto", "Llene todos los campos de transferencia.")
            return
            
        try:
            ori_id = int(ori.split(" - ")[0])
            des_id = int(des.split(" - ")[0])
            v_qty = float(qty)
            if v_qty <= 0:
                raise ValueError("La cantidad debe ser mayor a 0")
                
            transfer_stock(cod, ori_id, des_id, v_qty, self.current_user["id"])
            messagebox.showinfo("Éxito", f"Se transfirieron {v_qty} de {cod} exitosamente.")
            
            # Limpiar
            self.ent_trans_qty.delete(0, 'end')
            self._load_transfers()
        except Exception as e:
            messagebox.showerror("Error de Transferencia", str(e))

    def _load_transfers(self):
        for item in self.tv_transfer.get_children():
            self.tv_transfer.delete(item)
        try:
            items = get_recent_transfers(20)
            for it in items:
                tag = it.get("estado", "PENDIENTE")
                self.tv_transfer.insert("", "end", values=(
                    it['fecha'], it['codigo'], it['producto'], it['origen'], it['destino'], it['cantidad']
                ), tags=(tag,))
        except Exception as e:
            _LOG.error("Error al historial transferencias: %s", e)

    # ==========================
    # UTILIDADES
    # ==========================
    def _update_combos_sucursales(self, sucs_list):
        opts = [f"{s['id']} - {s['name']}" for s in sucs_list]
        self.cmb_stock_suc['values'] = opts
        self.cmb_origen['values'] = opts
        self.cmb_destino['values'] = opts
        if opts:
            self.cmb_stock_suc.current(0)
            self.cmb_origen.current(0)
            if len(opts) > 1:
                self.cmb_destino.current(1)
            else:
                self.cmb_destino.current(0)

    def _on_tab_change(self, event=None):
        if hasattr(self, 'nb'):
            cur = self.nb.index("current")
            if cur == 1:
                self._load_stock_detail()
            elif cur == 2:
                self._load_transfers()

    def _open_consolidado_window(self):
        top = tk.Toplevel(self)
        top.title("📊 Reporte Consolidado de Stock")
        top.geometry("900x600")
        top.configure(bg=Luxury2026Colors.BG_DARKEST)
        top.transient(self)
        top.grab_set()

        # Header
        hdr = tk.Frame(top, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Stock Consolidado Multi-Sucursal", font=ModernTypography.font_heading(),
                 bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.PRIMARY).pack(pady=12)

        # Tools
        tb = tk.Frame(top, bg=Luxury2026Colors.BG_DARKEST)
        tb.pack(fill="x", padx=12, pady=(12, 6))
        
        # Tabla
        frame_tv = tk.Frame(top, bg=Luxury2026Colors.BG_SECONDARY, relief="solid", bd=1)
        frame_tv.pack(fill="both", expand=True, padx=12, pady=6)
        
        cols = ("codigo", "producto", "stock_total", "detalles")
        tv = ttk.Treeview(frame_tv, columns=cols, show="headings")
        tv.heading("codigo", text="Código")
        tv.heading("producto", text="Producto")
        tv.heading("stock_total", text="Stock Total")
        tv.heading("detalles", text="Distribución por Sucursal")
        
        tv.column("codigo", width=100, anchor="w")
        tv.column("producto", width=300, anchor="w")
        tv.column("stock_total", width=100, anchor="center")
        tv.column("detalles", width=350, anchor="w")
        
        tv.pack(fill="both", expand=True, padx=2, pady=2)
        theme.aplicar_estilo_treeview(tv)
        scrollbars.agregar_scrollbar(tv, frame_tv)

        # Cargar datos
        items = get_stock_consolidado()
        for it in items:
            dist = " | ".join([f"{s['sucursal']}: {s['stock']}" for s in it["por_sucursal"]])
            if not dist:
                dist = "Sin distribuir (Stock Base)"
            tv.insert("", "end", values=(it["codigo"], it["nombre"], it["stock_total"], dist))

        # Func export
        def _exportar_csv():
            if not items: return
            path = filedialog.asksaveasfilename(
                parent=top, title="Exportar Consolidado",
                defaultextension=".csv", filetypes=[("CSV Files", "*.csv")]
            )
            if not path: return
            try:
                with open(path, mode="w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Código", "Producto", "Stock Total", "Distribución"])
                    for row_id in tv.get_children():
                        writer.writerow(tv.item(row_id)['values'])
                messagebox.showinfo("Exportado", f"Archivo generado:\n{path}", parent=top)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar:\n{e}", parent=top)

        ttk.Button(tb, text="📥 Exportar CSV", command=_exportar_csv, style='Luxury.Secondary.TButton').pack(side="right")

