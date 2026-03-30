"""
Sistema de estilos moderno y profesional para Alfa & Omega
Colores corporativos, temas y componentes atractivos
"""

from tkinter import ttk
import tkinter as tk
from typing import Literal

# ===== COLORES CORPORATIVOS =====
class Colors:
    """Paleta de colores Alfa & Omega"""
    
    # Primarios
    PRIMARY = "#6B5B95"      # Púrpura corporativo
    SECONDARY = "#D946EF"    # Magenta destacado
    ACCENT = "#EC4899"       # Rosa vibrante
    
    # Neutros
    DARK = "#1F2937"         # Gris oscuro (casi negro)
    LIGHT = "#F9FAFB"        # Blanco roto
    BORDER = "#E5E7EB"       # Gris claro
    
    # Funcionales
    SUCCESS = "#10B981"      # Verde éxito
    WARNING = "#F59E0B"      # Ámbar advertencia
    DANGER = "#EF4444"       # Rojo error
    INFO = "#3B82F6"         # Azul información
    
    # Tonos
    GRAY_700 = "#374151"
    GRAY_600 = "#4B5563"
    GRAY_500 = "#6B7280"
    GRAY_400 = "#9CA3AF"
    
    # Fondo
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F3F4F6"
    
    # Texto
    TEXT_PRIMARY = "#111827"
    TEXT_SECONDARY = "#6B7280"


# ===== TEMA =====
CURRENT_MODE = 'light'

def aplicar_tema_moderno():
    """Aplica tema moderno a toda la aplicación"""
    
    style = ttk.Style()
    
    # Configurar tema base
    try:
        style.theme_use('clam')
    except:
        pass
    
    # ===== BOTONES =====
    style.configure('TButton',
        font=('Segoe UI', 10, 'bold'),
        padding=8,
        relief='flat',
        borderwidth=0
    )
    style.map('TButton',
        background=[('pressed', Colors.PRIMARY), ('active', Colors.SECONDARY)],
        foreground=[('pressed', 'white'), ('active', 'white')]
    )
    
    # Botones primarios (más destacados)
    style.configure('Accent.TButton',
        font=('Segoe UI', 10, 'bold'),
        padding=10,
        background=Colors.PRIMARY,
        foreground='white'
    )
    style.map('Accent.TButton',
        background=[('pressed', '#5A4A85'), ('active', Colors.SECONDARY)],
        foreground=[('pressed', 'white'), ('active', 'white')]
    )
    
    # Botones peligrosos (eliminar, etc)
    style.configure('Danger.TButton',
        font=('Segoe UI', 10, 'bold'),
        padding=8,
        background=Colors.DANGER,
        foreground='white'
    )
    style.map('Danger.TButton',
        background=[('pressed', '#DC2626'), ('active', '#B91C1C')],
        foreground=[('pressed', 'white'), ('active', 'white')]
    )
    
    # Botones de éxito
    style.configure('Success.TButton',
        font=('Segoe UI', 10, 'bold'),
        padding=8,
        background=Colors.SUCCESS,
        foreground='white'
    )
    style.map('Success.TButton',
        background=[('pressed', '#059669'), ('active', '#047857')],
        foreground=[('pressed', 'white'), ('active', 'white')]
    )
    
    # ===== LABELS =====
    style.configure('TLabel',
        font=('Segoe UI', 10),
        background=Colors.LIGHT,
        foreground=Colors.TEXT_PRIMARY
    )
    
    style.configure('Header.TLabel',
        font=('Segoe UI', 14, 'bold'),
        background=Colors.LIGHT,
        foreground=Colors.PRIMARY
    )
    
    style.configure('Subtitle.TLabel',
        font=('Segoe UI', 11),
        background=Colors.LIGHT,
        foreground=Colors.GRAY_600
    )
    
    # ===== ENTRY =====
    style.configure('TEntry',
        font=('Segoe UI', 10),
        padding=6,
        fieldbackground=Colors.BG_PRIMARY,
        background=Colors.BORDER,
        foreground=Colors.TEXT_PRIMARY
    )
    
    # ===== COMBOBOX =====
    style.configure('TCombobox',
        font=('Segoe UI', 10),
        padding=6,
        fieldbackground=Colors.BG_PRIMARY,
        background=Colors.PRIMARY,
        foreground=Colors.TEXT_PRIMARY
    )
    
    # ===== LABELFRAME =====
    style.configure('TLabelframe',
        font=('Segoe UI', 11, 'bold'),
        background=Colors.LIGHT,
        foreground=Colors.PRIMARY,
        bordercolor=Colors.BORDER,
        relief='ridge'
    )
    
    style.configure('TLabelframe.Label',
        font=('Segoe UI', 11, 'bold'),
        background=Colors.LIGHT,
        foreground=Colors.PRIMARY
    )
    
    # ===== NOTEBOOK (TABS) =====
    style.configure('TNotebook',
        background=Colors.LIGHT,
        borderwidth=0
    )
    
    style.configure('TNotebook.Tab',
        font=('Segoe UI', 10),
        padding=[12, 8],
        background=Colors.BG_SECONDARY,
        foreground=Colors.TEXT_SECONDARY
    )
    
    style.map('TNotebook.Tab',
        background=[('selected', Colors.PRIMARY)],
        foreground=[('selected', 'white')]
    )
    
    # ===== TREEVIEW =====
    style.configure('Treeview',
        font=('Segoe UI', 10),
        rowheight=28,
        background=Colors.BG_PRIMARY,
        foreground=Colors.TEXT_PRIMARY,
        fieldbackground=Colors.BG_PRIMARY,
        borderwidth=1
    )
    
    style.configure('Treeview.Heading',
        font=('Segoe UI', 10, 'bold'),
        background=Colors.PRIMARY,
        foreground='white',
        borderwidth=1
    )
    
    style.map('Treeview',
        background=[('selected', Colors.PRIMARY)],
        foreground=[('selected', 'white')]
    )
    
    # ===== FRAME =====
    style.configure('TFrame',
        background=Colors.LIGHT
    )
    
    # Frame destacado
    style.configure('Highlight.TFrame',
        background=Colors.PRIMARY,
        relief='flat',
        borderwidth=0
    )


def crear_frame_tarjeta(parent, titulo="", padx=10, pady=10, bg=None):
    """
    Crea un frame estilo "tarjeta" con sombra visual.
    Usado para agrupar elementos de forma atractiva.
    """
    if bg is None:
        bg = Colors.BG_PRIMARY
    
    frame = ttk.LabelFrame(parent, text=titulo, padding=padx)
    frame.configure(relief='flat', borderwidth=1)
    
    return frame


def crear_boton_primario(parent, text, command=None, width=None):
    """Crea un botón primario destacado"""
    return ttk.Button(
        parent,
        text=f"✓ {text}",
        command=command,
        style='Accent.TButton',
        width=width
    )


def crear_boton_danger(parent, text, command=None, width=None):
    """Crea un botón de peligro (eliminar, etc)"""
    return ttk.Button(
        parent,
        text=f"✕ {text}",
        command=command,
        style='Danger.TButton',
        width=width
    )


def crear_boton_success(parent, text, command=None, width=None):
    """Crea un botón de éxito"""
    return ttk.Button(
        parent,
        text=f"✓ {text}",
        command=command,
        style='Success.TButton',
        width=width
    )


def crear_label_titulo(parent, text):
    """Crea un label de título"""
    return ttk.Label(
        parent,
        text=text,
        style='Header.TLabel'
    )


def crear_label_subtitulo(parent, text):
    """Crea un label de subtítulo"""
    return ttk.Label(
        parent,
        text=text,
        style='Subtitle.TLabel'
    )


def aplicar_estilo_entry(entry, placeholder=""):
    """Aplica estilo a un Entry con placeholder"""
    if placeholder:
        entry.insert(0, placeholder)
        
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
        entry.config(foreground=Colors.GRAY_400)


def crear_linea_separadora(parent):
    """Crea una línea divisoria visual"""
    return ttk.Separator(parent, orient='horizontal')


def crear_frame_estatisticas(parent):
    """Crea un frame para mostrar estadísticas (4 columnas)"""
    frame = ttk.Frame(parent)
    
    # Configurar 4 columnas iguales
    for i in range(4):
        frame.grid_columnconfigure(i, weight=1)
    
    return frame


def crear_tarjeta_metrica(parent, titulo, valor, icono="", color=Colors.PRIMARY, row=0, col=0):
    """Crea una tarjeta de métrica individual"""
    
    # Canvas para fondo coloreado
    canvas = tk.Canvas(
        parent,
        bg=color,
        height=100,
        width=150,
        highlightthickness=0
    )
    canvas.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
    
    # Título
    canvas.create_text(
        75, 25,
        text=f"{icono} {titulo}",
        font=('Segoe UI', 9, 'bold'),
        fill='white'
    )
    
    # Valor
    canvas.create_text(
        75, 65,
        text=valor,
        font=('Segoe UI', 24, 'bold'),
        fill='white'
    )
    
    return canvas
