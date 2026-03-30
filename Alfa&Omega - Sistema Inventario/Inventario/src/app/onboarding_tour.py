"""
src/app/onboarding_tour.py
==========================
Onboarding Tour interactivo para el primer login del usuario.
Blueprint 7.3.
"""
import tkinter as tk
from tkinter import ttk

from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography
from src.database.connection import get_connection

class OnboardingTour(tk.Toplevel):
    def __init__(self, parent, user: dict, app_ref):
        super().__init__(parent)
        self.user = user
        self.app = app_ref
        
        self.title("Tour de Bienvenida")
        self.geometry("700x500")
        self.resizable(False, False)
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        
        # Bloquear ventana debajo
        self.transient(parent)
        self.grab_set()
        
        # Centrar ventana
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (700 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (500 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.current_step = 0
        self.steps = [
            {
                "title": "Bienvenido a Alfa & Omega ERP",
                "icon": "🎉",
                "desc": "Este es el panel principal de control para gestionar todo tu negocio.\nTe guiaremos en los primeros pasos esenciales para empezar a operar.",
                "action_text": "Siguiente ->",
                "action_cmd": self.next_step
            },
            {
                "title": "Configura tu inventario",
                "icon": "📦",
                "desc": "El primer paso es añadir productos a tu catálogo.\nPuedes hacerlo manualmente o usando la importación de Excel/CSV.",
                "action_text": "Siguiente ->",
                "action_cmd": self.next_step
            },
            {
                "title": "Realiza tu primera venta",
                "icon": "💰",
                "desc": "Usa la caja registradora Punto de Venta (POS) para cobrar y generar el recibo rápidamente.",
                "action_text": "Siguiente ->",
                "action_cmd": self.next_step
            },
            {
                "title": "Configura tu perfil de industria",
                "icon": "🏭",
                "desc": "El ERP se adaptará a ti.\nPuedes seleccionar tu industria para activar módulos específicos desde Parámetros.",
                "action_text": "Siguiente ->",
                "action_cmd": self.next_step
            },
            {
                "title": "¡Listo para empezar!",
                "icon": "✅",
                "desc": "Ya conoces las herramientas principales.\nSi tienes dudas, revisa los reportes o utiliza el Historial.",
                "action_text": "Comenzar",
                "action_cmd": self.finish_tour
            }
        ]
        
        self.build_ui()
        self.show_step(0)
        
    def build_ui(self):
        # Bottom controls primero (Tkinter: side="bottom" debe ir antes de expand)
        self.bottom_frame = tk.Frame(self, bg=Luxury2026Colors.BG_DARKEST)
        self.bottom_frame.pack(side="bottom", fill="x", padx=30, pady=20)

        # Container principal después
        self.main_frame = tk.Frame(self, bg=Luxury2026Colors.BG_DARKEST)
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=(30,0))
        
        # Header (Icon + Title)
        self.lbl_icon = tk.Label(self.main_frame, text="", font=("Segoe UI Emoji", 48), bg=Luxury2026Colors.BG_DARKEST)
        self.lbl_icon.pack(pady=(10, 5))
        
        self.lbl_title = tk.Label(self.main_frame, text="", font=ModernTypography.font_heading(), 
                                  bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.PRIMARY)
        self.lbl_title.pack(pady=5)
        
        # Descripción
        self.lbl_desc = tk.Label(self.main_frame, text="", font=ModernTypography.font_body(),
                                 bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.TEXT_SECONDARY,
                                 justify="center", wraplength=580)
        self.lbl_desc.pack(pady=20, fill="x")
        
        # (bottom_frame ya declarado arriba)
        
        self.btn_skip = tk.Button(self.bottom_frame, text="Omitir tour", font=ModernTypography.font_body(),
                                  bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.TEXT_TERTIARY, 
                                  relief="flat", cursor="hand2", command=self.finish_tour)
        self.btn_skip.pack(side="left")
        
        self.btn_prev = tk.Button(self.bottom_frame, text="<- Anterior", font=ModernTypography.font_body_bold(),
                                  bg=Luxury2026Colors.BG_SECONDARY, fg=Luxury2026Colors.TEXT_PRIMARY,
                                  relief="flat", cursor="hand2", command=self.prev_step)
        
        self.btn_action = tk.Button(self.bottom_frame, text="", font=ModernTypography.font_heading(),
                                    bg=Luxury2026Colors.PRIMARY, fg=Luxury2026Colors.BG_DARKEST,
                                    relief="flat", cursor="hand2")
        self.btn_action.pack(side="right")
        
        # Dots indicator
        self.dots_frame = tk.Frame(self.bottom_frame, bg=Luxury2026Colors.BG_DARKEST)
        self.dots_frame.pack(side="top", pady=10)
        self.dots = []
        for _ in range(5):
            lbl = tk.Label(self.dots_frame, text="●", font=("Arial", 14), bg=Luxury2026Colors.BG_DARKEST, fg=Luxury2026Colors.BORDER)
            lbl.pack(side="left", padx=2)
            self.dots.append(lbl)

    def show_step(self, index: int):
        self.current_step = index
        step = self.steps[index]
        
        self.lbl_icon.config(text=step["icon"])
        self.lbl_title.config(text=step["title"])
        self.lbl_desc.config(text=step["desc"])
        
        self.btn_action.config(text=step["action_text"], command=step["action_cmd"])
        
        if index > 0:
            self.btn_prev.pack(side="left", padx=15)
        else:
            self.btn_prev.pack_forget()
            
        # Update dots
        for i, dot in enumerate(self.dots):
            if i == index:
                dot.config(fg=Luxury2026Colors.PRIMARY)
            else:
                dot.config(fg=Luxury2026Colors.BORDER)

    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.show_step(self.current_step + 1)
            
    def prev_step(self):
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
            
    def mark_completed(self):
        if self.user:
            try:
                with get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("UPDATE users SET tour_completado = 1 WHERE id = ?", (self.user["id"],))
                    conn.commit()
            except Exception as e:
                print("Error updating tour status:", e)

    def finish_tour(self):
        self.mark_completed()
        self.destroy()
        
    def _go_to_tab(self, index):
        self.finish_tour()
        if hasattr(self.app, "nb_main"):
            self.app.nb_main.select(index)
            
    def _open_pos(self):
        self.finish_tour()
        if hasattr(self.app, "_open_pos_window"):
            self.app._open_pos_window()
            
    def _go_settings(self):
        self.finish_tour()
        if hasattr(self.app, "nb_main"):
            tabs = self.app.nb_main.tabs()
            for idx, tab_id in enumerate(tabs):
                if "Parámetros" in self.app.nb_main.tab(tab_id, "text"):
                    self.app.nb_main.select(idx)
                    break
