"""
Barra de Acceso Rápido - Interfaz optimizada para UX
Botones grandes y claros para funciones principales
"""

import tkinter as tk
from tkinter import ttk
from src.app.styles.modern import Colors

class BarraAccesoRapido:
    """
    Barra de acceso rápido con 4-6 funciones principales.
    Haz que sea fácil acceder a lo más importante.
    """
    
    def __init__(self, parent, callbacks=None):
        self.parent = parent
        self.callbacks = callbacks or {}
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", padx=10, pady=10)
        
        self._build_barra()
    
    def _build_barra(self):
        """Construye la barra con botones principales"""
        
        # Título
        titulo = ttk.Label(
            self.frame,
            text="⚡ Acciones Rápidas",
            font=("Segoe UI", 12, "bold")
        )
        titulo.pack(pady=(0, 8))
        
        # Frame con botones en grid (3 filas x 3 columnas máximo)
        frame_botones = ttk.Frame(self.frame)
        frame_botones.pack(fill="x")
        
        # Acciones: (icono, texto, callback_key, color)
        acciones = [
            ("📦", "NUEVO PRODUCTO", "nuevo_producto", Colors.SUCCESS),
            ("💰", "REGISTRAR VENTA", "registrar_venta", Colors.INFO),
            ("📥", "REGISTRAR COMPRA", "registrar_compra", Colors.WARNING),
            ("📊", "VER REPORTES", "ver_reportes", Colors.PRIMARY),
            ("🔍", "BUSCAR RÁPIDO", "buscar_rapido", Colors.GRAY_600),
            ("⚙️", "CONFIGURACIÓN", "configuracion", Colors.DARK),
        ]
        
        for i, (icono, texto, callback_key, color) in enumerate(acciones):
            btn = self._crear_boton_rapido(
                frame_botones,
                f"{icono} {texto}",
                color,
                i % 3,
                i // 3
            )
            
            # Asignar callback
            if callback_key in self.callbacks:
                btn.config(command=self.callbacks[callback_key])
    
    def _crear_boton_rapido(self, parent, texto, color, col, row):
        """Crea un botón individual de la barra rápida"""
        
        # Botón personalizado en Canvas
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        canvas = tk.Canvas(
            btn_frame,
            bg=color,
            height=70,
            width=140,
            highlightthickness=0,
            relief="flat"
        )
        canvas.pack(fill="both", expand=True)
        
        # Texto centrado
        canvas.create_text(
            70, 35,
            text=texto,
            font=("Segoe UI", 9, "bold"),
            fill="white",
            justify="center"
        )
        
        # Efecto hover
        def on_enter(event):
            canvas.config(bg=self._oscurecer_color(color))
        
        def on_leave(event):
            canvas.config(bg=color)
        
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        
        # Hacer clickeable
        class ClickableCanvas(tk.Canvas):
            def __init__(self, *args, **kwargs):
                tk.Canvas.__init__(self, *args, **kwargs)
                self.command = None
            
            def config(self, **kwargs):
                if "command" in kwargs:
                    self.command = kwargs.pop("command")
                tk.Canvas.config(self, **kwargs)
        
        return canvas
    
    @staticmethod
    def _oscurecer_color(color_hex):
        """Oscurece un color hexadecimal en 20%"""
        try:
            color_hex = color_hex.lstrip('#')
            r = int(color_hex[0:2], 16) - 20
            g = int(color_hex[2:4], 16) - 20
            b = int(color_hex[4:6], 16) - 20
            
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color_hex


class WidgetOptimizado:
    """Utilidades para widgets optimizados"""
    
    @staticmethod
    def crear_entry_buscador(parent, placeholder="🔍 Buscar..."):
        """Crea un entry con estilos de buscador"""
        entry = ttk.Entry(parent)
        entry.insert(0, placeholder)
        entry.config(foreground=Colors.GRAY_400)
        
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(foreground=Colors.TEXT_PRIMARY)
        
        def on_focus_out(event):
            if entry.get() == "":
                entry.insert(0, placeholder)
                entry.config(foreground=Colors.GRAY_400)
        
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        
        return entry
    
    @staticmethod
    def crear_boton_flotante(parent, texto, comando, color=Colors.PRIMARY):
        """Crea un botón flotante para acciones principales"""
        btn = tk.Canvas(
            parent,
            bg=color,
            height=50,
            width=180,
            highlightthickness=0,
            relief="flat"
        )
        btn.create_text(
            90, 25,
            text=texto,
            font=("Segoe UI", 11, "bold"),
            fill="white"
        )
        
        btn.bind("<Button-1>", lambda e: comando() if callable(comando) else None)
        
        # Hover effect
        def on_enter(event):
            btn.config(bg=WidgetOptimizado._oscurecer_color(color))
        
        def on_leave(event):
            btn.config(bg=color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    @staticmethod
    def _oscurecer_color(color_hex):
        """Oscurece un color hexadecimal"""
        try:
            color_hex = color_hex.lstrip('#')
            r = int(color_hex[0:2], 16) - 20
            g = int(color_hex[2:4], 16) - 20
            b = int(color_hex[4:6], 16) - 20
            
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color_hex


class NotificacionFlotante:
    """Notificaciones tipo Toast mejoradas"""
    
    @staticmethod
    def mostrar(parent, mensaje, tipo="info", duracion=3000):
        """
        Muestra una notificación flotante.
        tipo: 'success', 'error', 'warning', 'info'
        """
        colores = {
            'success': Colors.SUCCESS,
            'error': Colors.DANGER,
            'warning': Colors.WARNING,
            'info': Colors.INFO
        }
        
        color = colores.get(tipo, Colors.INFO)
        
        # Crear popup
        popup = tk.Toplevel(parent)
        popup.attributes('-topmost', True)
        popup.geometry("300x60+100+100")
        popup.overrideredirect(True)
        popup.config(bg=color)
        
        # Label
        label = tk.Label(
            popup,
            text=mensaje,
            font=("Segoe UI", 10, "bold"),
            bg=color,
            fg="white"
        )
        label.pack(fill="both", expand=True)
        
        # Auto-close
        popup.after(duracion, popup.destroy)
