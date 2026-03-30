"""
src/app/notif_config_window.py
================================
Tarea 15 — GUI configuración notificaciones SMTP.
class NotifConfigWindow(tk.Toplevel)
Cero lógica de negocio aquí; todo en src/services/notificaciones.py
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography
from src.database.settings import get_notif_config, save_notif_config
from src.services.notificaciones import test_conexion_smtp, iniciar_scheduler

_LOG = logging.getLogger(__name__)
C   = Luxury2026Colors
T   = ModernTypography


class NotifConfigWindow(tk.Toplevel):
    """Ventana de configuración de notificaciones por email."""

    def __init__(self, master):
        super().__init__(master)
        self.title("🔔 Configuración de Notificaciones")
        self.geometry("650x850")
        self.configure(bg=C.BG_DARKEST)
        self.resizable(False, False)

        # Encabezado
        hdr = tk.Frame(self, bg=C.BG_DARK)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🔔 Notificaciones Email",
                 font=T.font_heading_xl(), bg=C.BG_DARK, fg=C.PRIMARY
                 ).pack(side="left", padx=16, pady=10)
        tk.Label(hdr, text="SMTP · Alertas · Resumen diario",
                 font=T.font_body_small(), bg=C.BG_DARK, fg=C.TEXT_SECONDARY
                 ).pack(side="left", padx=4)

        # Canvas con scroll
        canvas = tk.Canvas(self, bg=C.BG_DARKEST, highlightthickness=0)
        scr    = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._frm = tk.Frame(canvas, bg=C.BG_DARKEST)
        self._frm.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._frm, anchor="nw")
        canvas.configure(yscrollcommand=scr.set)
        canvas.pack(side="left", fill="both", expand=True)
        scr.pack(side="right", fill="y")

        self._vars: dict[str, tk.Variable] = {}
        self._build_form()
        self._load()

    # ── Construcción del formulario ────────────────────────────────

    def _build_form(self):
        pad = {"padx": 20, "pady": 6}

        # Toggle activo
        activo_frm = tk.Frame(self._frm, bg=C.BG_SECONDARY, relief="solid", bd=1)
        activo_frm.pack(fill="x", **pad)
        v_activo = tk.IntVar(value=0)
        self._vars["activo"] = v_activo
        tk.Checkbutton(
            activo_frm, text="  ✅  Notificaciones activas",
            variable=v_activo, onvalue=1, offvalue=0,
            font=T.font_body_bold(),
            bg=C.BG_SECONDARY, fg=C.TEXT_PRIMARY,
            activebackground=C.BG_SECONDARY, selectcolor=C.BG_TERTIARY
        ).pack(anchor="w", padx=12, pady=10)

        # SMTP
        self._section("🌐 Servidor SMTP")
        self._field("smtp_host", "Servidor (host)", "smtp.gmail.com")
        self._field("smtp_port", "Puerto",          "587", width=8)
        self._field("smtp_user", "Usuario / email", "tu@gmail.com")
        self._field("smtp_pass", "Contraseña",      "", show="*")

        # Direcciones
        self._section("📧 Direcciones")
        self._field("from_email", "Email remitente", "tu@gmail.com")
        self._field("to_emails",
                    "Destinatarios (separados por coma)",
                    "dest1@mail.com, dest2@mail.com", width=46)

        # Tipos de alerta
        self._section("🔔 Tipos de notificación")
        self._check("stock_critico",  "⚠️  Alerta stock crítico (cantidad = 0)")
        self._check("stock_bajo",     "🟡  Alerta stock bajo (cantidad < 5)")
        self._check("resumen_diario", "📊  Resumen diario de KPIs")

        # Hora
        self._section("⏰ Hora de envío del resumen")
        hora_frm = tk.Frame(self._frm, bg=C.BG_DARKEST)
        hora_frm.pack(fill="x", **pad)
        tk.Label(hora_frm, text="Hora (HH:MM):", font=T.font_body_small(),
                 bg=C.BG_DARKEST, fg=C.TEXT_SECONDARY).pack(side="left")
        v_hora = tk.StringVar(value="08:00")
        self._vars["hora_resumen"] = v_hora
        tk.Entry(hora_frm, textvariable=v_hora, width=8,
                 bg=C.BG_SECONDARY, fg=C.TEXT_PRIMARY,
                 insertbackground=C.TEXT_PRIMARY).pack(side="left", padx=8)
        tk.Label(hora_frm, text="(formato 24h)", font=T.font_caption(),
                 bg=C.BG_DARKEST, fg=C.TEXT_SECONDARY).pack(side="left")

        # Botones
        btn_frm = tk.Frame(self._frm, bg=C.BG_DARKEST)
        btn_frm.pack(fill="x", padx=20, pady=16)
        ttk.Button(btn_frm, text="📡 Probar conexión",
                   command=self._probar,
                   style="Luxury.Secondary.TButton").pack(side="left", padx=4)
        ttk.Button(btn_frm, text="💾 Guardar",
                   command=self._guardar,
                   style="Luxury.Primary.TButton").pack(side="left", padx=4)
        ttk.Button(btn_frm, text="✖ Cancelar",
                   command=self.destroy,
                   style="Luxury.Secondary.TButton").pack(side="right", padx=4)

    # ── Helpers UI ─────────────────────────────────────────────────

    def _section(self, titulo: str):
        frm = tk.Frame(self._frm, bg=C.BG_SECONDARY, relief="solid", bd=1)
        frm.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(frm, text=titulo, font=T.font_body_bold(),
                 bg=C.BG_SECONDARY, fg=C.PRIMARY).pack(anchor="w", padx=12, pady=6)

    def _field(self, key: str, label: str, placeholder: str = "",
               show: str = "", width: int = 38):
        row = tk.Frame(self._frm, bg=C.BG_DARKEST)
        row.pack(fill="x", padx=24, pady=3)
        tk.Label(row, text=label, font=T.font_body_small(), width=30, anchor="w",
                 bg=C.BG_DARKEST, fg=C.TEXT_SECONDARY).pack(side="left")
        v = tk.StringVar(value=placeholder)
        self._vars[key] = v
        tk.Entry(row, textvariable=v, width=width, show=show,
                 bg=C.BG_SECONDARY, fg=C.TEXT_PRIMARY,
                 insertbackground=C.TEXT_PRIMARY).pack(side="left", padx=4)

    def _check(self, key: str, label: str):
        row = tk.Frame(self._frm, bg=C.BG_DARKEST)
        row.pack(fill="x", padx=24, pady=2)
        v = tk.IntVar(value=1)
        self._vars[key] = v
        tk.Checkbutton(row, text=label, variable=v, onvalue=1, offvalue=0,
                       font=T.font_body_small(),
                       bg=C.BG_DARKEST, fg=C.TEXT_PRIMARY,
                       activebackground=C.BG_DARKEST,
                       selectcolor=C.BG_SECONDARY).pack(anchor="w")

    # ── Carga / Guardar ────────────────────────────────────────────

    def _load(self):
        try:
            cfg = get_notif_config()
            for k, v in self._vars.items():
                if k in cfg and cfg[k] is not None:
                    v.set(cfg[k])
        except Exception as e:
            _LOG.warning("NotifConfigWindow._load error: %s", e)

    def _guardar(self):
        try:
            cfg = {k: v.get() for k, v in self._vars.items()}
            cfg["smtp_port"]      = int(cfg.get("smtp_port") or 587)
            cfg["activo"]         = int(cfg.get("activo") or 0)
            cfg["stock_critico"]  = int(cfg.get("stock_critico") or 0)
            cfg["stock_bajo"]     = int(cfg.get("stock_bajo") or 0)
            cfg["resumen_diario"] = int(cfg.get("resumen_diario") or 0)
            save_notif_config(cfg)
            iniciar_scheduler()
            messagebox.showinfo("✅ Guardado",
                                "Configuración guardada correctamente.", parent=self)
            self.destroy()
        except Exception as e:
            _LOG.warning("NotifConfigWindow._guardar error: %s", e)
            messagebox.showerror("Error", str(e), parent=self)

    def _probar(self):
        try:
            cfg = {k: v.get() for k, v in self._vars.items()}
            cfg["smtp_port"] = int(cfg.get("smtp_port") or 587)
            save_notif_config(cfg)
            resultado = test_conexion_smtp()
            if resultado["ok"]:
                messagebox.showinfo("✅ Conexión OK",
                                    resultado["mensaje"], parent=self)
            else:
                messagebox.showerror("❌ Error SMTP",
                                     resultado["mensaje"], parent=self)
        except Exception as e:
            _LOG.warning("NotifConfigWindow._probar error: %s", e)
            messagebox.showerror("Error", str(e), parent=self)
