"""
src/app/dian_config_window.py
=============================
Ventana UI para configuración DIAN (Credenciales, Resoluciones, Estado).
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging

from src.database.connection import get_connection
from src.services.dian import get_dian_config

_LOG = logging.getLogger(__name__)

class DianConfigWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Configuración Facturación Electrónica (DIAN)")
        self.geometry("650x500")
        self.grab_set()

        # Variables de Configuración
        self.var_nit = tk.StringVar()
        self.var_razon = tk.StringVar()
        self.var_res = tk.StringVar()
        self.var_prefijo = tk.StringVar()
        self.var_consecutivo = tk.StringVar()
        self.var_ambiente = tk.IntVar(value=2) # 1=Prod, 2=Test

        self._build_ui()
        self._load_config()

    def _build_ui(self):
        main_frame = ttk.Notebook(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tab_config = ttk.Frame(main_frame)
        tab_status = ttk.Frame(main_frame)
        
        main_frame.add(tab_config, text="Configuración Empresa")
        main_frame.add(tab_status, text="Estado Facturas")

        # --- Tab Configuración ---
        form = ttk.Frame(tab_config, padding=15)
        form.pack(fill="both", expand=True)

        ttk.Label(form, text="NIT Empresa:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.var_nit, width=30).grid(row=0, column=1, pady=5)

        ttk.Label(form, text="Razón Social:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.var_razon, width=40).grid(row=1, column=1, pady=5)

        ttk.Label(form, text="Resolución DIAN:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.var_res, width=30).grid(row=2, column=1, pady=5)

        ttk.Label(form, text="Prefijo:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.var_prefijo, width=15).grid(row=3, column=1, sticky="w", pady=5)

        ttk.Label(form, text="Consecutivo Actual:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.var_consecutivo, width=15).grid(row=4, column=1, sticky="w", pady=5)

        ttk.Label(form, text="Ambiente:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="w", pady=5)
        frame_amb = ttk.Frame(form)
        frame_amb.grid(row=5, column=1, sticky="w", pady=5)
        ttk.Radiobutton(frame_amb, text="Habilitación (TEST)", variable=self.var_ambiente, value=2).pack(side="left")
        ttk.Radiobutton(frame_amb, text="Producción (PROD)", variable=self.var_ambiente, value=1).pack(side="left", padx=15)

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=25)
        ttk.Button(btn_frame, text="💾 Guardar Configuración", command=self._save_config).pack()

        # --- Tab Estado ---
        status_form = ttk.Frame(tab_status, padding=10)
        status_form.pack(fill="both", expand=True)

        ttk.Button(status_form, text="🔄 Ver Últimas 20 Facturas", command=self._load_status).pack(pady=10)

        cols = ("id", "numero", "estado", "cufe")
        self.tree = ttk.Treeview(status_form, columns=cols, show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("numero", text="Núm DIAN")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("cufe", text="CUFE")
        
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("numero", width=100, anchor="center")
        self.tree.column("estado", width=120, anchor="center")
        self.tree.column("cufe", width=300)
        
        self.tree.pack(fill="both", expand=True)

    def _load_config(self):
        c = get_dian_config()
        self.var_nit.set(c.get("nit", ""))
        self.var_razon.set(c.get("razon_social", ""))
        self.var_res.set(c.get("resolucion", ""))
        self.var_prefijo.set(c.get("prefijo", "FE"))
        self.var_consecutivo.set(c.get("consecutivo_actual", "1"))
        self.var_ambiente.set(c.get("ambiente", 2))

    def _save_config(self):
        datos = {
            "dian_nit": self.var_nit.get().strip(),
            "dian_razon_social": self.var_razon.get().strip(),
            "dian_resolucion": self.var_res.get().strip(),
            "dian_prefijo": self.var_prefijo.get().strip(),
            "dian_consecutivo_actual": self.var_consecutivo.get().strip(),
            "dian_ambiente": str(self.var_ambiente.get())
        }
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                for k, v in datos.items():
                    cur.execute("SELECT 1 FROM company_settings WHERE clave = ?", (k,))
                    if cur.fetchone():
                        cur.execute("UPDATE company_settings SET valor = ? WHERE clave = ?", (v, k))
                    else:
                        cur.execute("INSERT INTO company_settings (clave, valor) VALUES (?, ?)", (k, v))
                conn.commit()
            messagebox.showinfo("Éxito", "Configuración DIAN guardada correctamente.", parent=self)
        except Exception as e:
            _LOG.error("Error guardando config DIAN: %s", e)
            messagebox.showerror("Error", f"No se pudo guardar la configuración.\n{e}", parent=self)

    def _load_status(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, numero_dian, dian_estado, cufe FROM documents ORDER BY id DESC LIMIT 20"
                )
                for row in cur.fetchall():
                    self.tree.insert("", "end", values=(
                        row[0], row[1] or "", row[2] or "PENDIENTE", row[3] or "N/A"
                    ))
        except Exception as e:
            _LOG.error("Error cargando estado facturas DIAN: %s", e)
