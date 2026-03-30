"""
LUXURY 2026 - Sistema de Diseño Enamorante
Inspirado en: Notion, Figma, Linear, Discord
Estilo: Minimalista moderno, dark mode premium, enamorante
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from PIL import Image, ImageDraw, ImageTk

# ===== PALETA LUXURY 2026 =====
class Luxury2026Colors:
    """Colores minimalistas 2026 - Enamorantes"""
    
    # Fondos Dark Mode (Profesional + Hermoso)
    BG_DARKEST = "#0A0E27"     # Negro profundo - Fondo base
    BG_DARK = "#111528"        # Azul oscuro muy profundo
    BG_SECONDARY = "#16213E"   # Azul oscuro secundario
    BG_TERTIARY = "#1A2744"    # Azul gris oscuro
    BG_HOVER = "#252F4A"       # Hover overlay oscuro
    
    # Primarios (Vibrantes pero controlados)
    PRIMARY = "#6366F1"        # Indigo vibrante (como Linear)
    PRIMARY_LIGHT = "#818CF8"  # Indigo claro
    PRIMARY_DARK = "#4F46E5"   # Indigo oscuro
    
    # Secundarios (Complementarios hermosos)
    ACCENT = "#10B981"         # Verde esmeralda (como Figma)
    ACCENT_LIGHT = "#34D399"   # Verde claro
    
    # Terciarios (Vibrancia sutil)
    PURPLE = "#A855F7"         # Púrpura vibrante
    PINK = "#EC4899"           # Rosa magenta
    CYAN = "#06B6D4"           # Cyan hermoso
    
    # Estados Funcionales
    SUCCESS = "#10B981"        # Verde confirmación
    WARNING = "#F59E0B"        # Ámbar advertencia
    DANGER = "#EF4444"         # Rojo error
    INFO = "#3B82F6"           # Azul info
    
    # Textos
    TEXT_PRIMARY = "#F8F9FA"   # Blanco suave
    TEXT_SECONDARY = "#A1A5B1" # Gris claro
    TEXT_TERTIARY = "#7A7F8C"  # Gris medio
    
    # Bordes
    BORDER_LIGHT = "#2D3B5F"   # Borde azul oscuro sutil
    BORDER = "#3F4B66"         # Borde más visible
    BORDER_DARK = "#495578"    # Borde prominente
    
    # Especiales
    SHADOW = "rgba(0, 0, 0, 0.4)"
    OVERLAY = "rgba(10, 14, 39, 0.8)"


# ===== EFECTOS MODERNOS 2026 =====
class ModernEffects:
    """Efectos visuales enamorantes"""
    
    # Blur y sombras suaves (Notion/Figma style)
    SHADOW_SM = "0 1px 3px 0 rgba(0, 0, 0, 0.3)"
    SHADOW_MD = "0 4px 12px 0 rgba(0, 0, 0, 0.4)"
    SHADOW_LG = "0 12px 24px 0 rgba(0, 0, 0, 0.5)"
    SHADOW_XL = "0 20px 40px 0 rgba(0, 0, 0, 0.6)"
    
    # Bordes redondeados (Moderno 2026)
    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 12
    RADIUS_XL = 16
    RADIUS_FULL = 24
    
    # Transiciones (Animaciones suaves)
    TRANSITION_FAST = "0.15s ease"
    TRANSITION_NORMAL = "0.3s ease"
    TRANSITION_SLOW = "0.5s ease"


# ===== TIPOGRAFÍA MODERNA 2026 =====
class ModernTypography:
    """Tipografía hermosa y clara"""
    
    # Familia (Inter es la fuente moderna por defecto)
    FAMILY = "Segoe UI"
    FAMILY_MONO = "Consolas"
    
    # Tamaños Generosos (Espaciado vertical)
    SIZE_XS = 12
    SIZE_SM = 13
    SIZE_BASE = 14
    SIZE_LG = 15
    SIZE_XL = 16
    SIZE_2XL = 18
    SIZE_3XL = 20
    SIZE_4XL = 24
    SIZE_5XL = 28
    
    # Pesos
    WEIGHT_LIGHT = 300
    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700
    
    @staticmethod
    def font_display():
        return tkFont.Font(family=ModernTypography.FAMILY, size=28, weight="bold")
    
    @staticmethod
    def font_heading_xl():
        return tkFont.Font(family=ModernTypography.FAMILY, size=24, weight="bold")
    
    @staticmethod
    def font_heading_lg():
        return tkFont.Font(family=ModernTypography.FAMILY, size=20, weight="bold")
    
    @staticmethod
    def font_heading():
        return tkFont.Font(family=ModernTypography.FAMILY, size=18, weight="bold")
    
    @staticmethod
    def font_title():
        return tkFont.Font(family=ModernTypography.FAMILY, size=16, weight="bold")
    
    @staticmethod
    def font_body_bold():
        return tkFont.Font(family=ModernTypography.FAMILY, size=14, weight="bold")
    
    @staticmethod
    def font_body():
        return tkFont.Font(family=ModernTypography.FAMILY, size=14)
    
    @staticmethod
    def font_body_small():
        return tkFont.Font(family=ModernTypography.FAMILY, size=13)
    
    @staticmethod
    def font_caption():
        return tkFont.Font(family=ModernTypography.FAMILY, size=12)
    
    @staticmethod
    def font_code():
        return tkFont.Font(family=ModernTypography.FAMILY_MONO, size=12)


# ===== APLICAR TEMA LUXURY 2026 =====
def aplicar_tema_luxury_2026():
    """Aplica tema enamorante estilo Notion/Figma/Linear"""
    
    style = ttk.Style()
    style.theme_use('clam')
    
    # ===== COLORES BASE =====
    style.configure('.', 
        background=Luxury2026Colors.BG_DARKEST,
        foreground=Luxury2026Colors.TEXT_PRIMARY
    )
    
    # ===== BOTONES - ENAMORANTES =====
    # Botón Primario (Indigo vibrante - Estilo Linear)
    style.configure('Luxury.Primary.TButton',
        font=ModernTypography.font_body_bold(),
        background=Luxury2026Colors.PRIMARY,
        foreground=Luxury2026Colors.TEXT_PRIMARY,
        borderwidth=0,
        padding=12,
        relief='flat',
        focuscolor='none'
    )
    style.map('Luxury.Primary.TButton',
        background=[
            ('active', Luxury2026Colors.PRIMARY_LIGHT),
            ('pressed', Luxury2026Colors.PRIMARY_DARK),
            ('disabled', Luxury2026Colors.BG_TERTIARY)
        ],
        foreground=[('disabled', Luxury2026Colors.TEXT_TERTIARY)]
    )
    
    # Botón Secundario (Transparente con borde)
    style.configure('Luxury.Secondary.TButton',
        font=ModernTypography.font_body_bold(),
        background=Luxury2026Colors.BG_TERTIARY,
        foreground=Luxury2026Colors.TEXT_PRIMARY,
        borderwidth=1,
        padding=12,
        relief='solid',
        focuscolor='none',
        bordercolor=Luxury2026Colors.BORDER
    )
    style.map('Luxury.Secondary.TButton',
        background=[
            ('active', Luxury2026Colors.BG_HOVER),
            ('pressed', Luxury2026Colors.BG_TERTIARY)
        ]
    )
    
    # Botón Accent (Verde esmeralda - Estilo Figma)
    style.configure('Luxury.Accent.TButton',
        font=ModernTypography.font_body_bold(),
        background=Luxury2026Colors.ACCENT,
        foreground=Luxury2026Colors.TEXT_PRIMARY,
        borderwidth=0,
        padding=12,
        relief='flat'
    )
    style.map('Luxury.Accent.TButton',
        background=[
            ('active', Luxury2026Colors.ACCENT_LIGHT),
            ('pressed', '#059669')
        ]
    )
    
    # Botón Danger (Rojo - pero suave)
    style.configure('Luxury.Danger.TButton',
        font=ModernTypography.font_body_bold(),
        background=Luxury2026Colors.DANGER,
        foreground=Luxury2026Colors.TEXT_PRIMARY,
        borderwidth=0,
        padding=12,
        relief='flat'
    )
    style.map('Luxury.Danger.TButton',
        background=[
            ('active', '#DC2626'),
            ('pressed', '#B91C1C')
        ]
    )
    
    # ===== ENTRADAS (Inputs) =====
    style.configure('TEntry',
        font=ModernTypography.font_body(),
        padding=10,
        background=Luxury2026Colors.BG_SECONDARY,
        foreground=Luxury2026Colors.TEXT_PRIMARY,
        fieldbackground=Luxury2026Colors.BG_SECONDARY,
        borderwidth=1,
        relief='solid',
        insertcolor=Luxury2026Colors.PRIMARY
    )
    style.map('TEntry',
        fieldbackground=[
            ('focus', Luxury2026Colors.BG_TERTIARY)
        ],
        borderwidth=[('focus', 2)],
        bordercolor=[('focus', Luxury2026Colors.PRIMARY)]
    )
    
    # ===== COMBOBOX =====
    style.configure('TCombobox',
        font=ModernTypography.font_body(),
        padding=10,
        background=Luxury2026Colors.BG_SECONDARY,
        foreground=Luxury2026Colors.TEXT_PRIMARY,
        fieldbackground=Luxury2026Colors.BG_SECONDARY,
        borderwidth=1,
        relief='solid'
    )
    
    # ===== LABELS =====
    style.configure('Display.TLabel',
        font=ModernTypography.font_display(),
        background=Luxury2026Colors.BG_DARKEST,
        foreground=Luxury2026Colors.TEXT_PRIMARY
    )
    
    style.configure('Heading.TLabel',
        font=ModernTypography.font_heading_lg(),
        background=Luxury2026Colors.BG_DARKEST,
        foreground=Luxury2026Colors.TEXT_PRIMARY
    )
    
    style.configure('Title.TLabel',
        font=ModernTypography.font_title(),
        background=Luxury2026Colors.BG_DARKEST,
        foreground=Luxury2026Colors.PRIMARY
    )
    
    style.configure('TLabel',
        font=ModernTypography.font_body(),
        background=Luxury2026Colors.BG_DARKEST,
        foreground=Luxury2026Colors.TEXT_PRIMARY
    )
    
    style.configure('Secondary.TLabel',
        font=ModernTypography.font_body_small(),
        background=Luxury2026Colors.BG_DARKEST,
        foreground=Luxury2026Colors.TEXT_SECONDARY
    )
    
    # ===== FRAMES =====
    style.configure('TFrame',
        background=Luxury2026Colors.BG_DARKEST,
        relief='flat',
        borderwidth=0
    )
    
    style.configure('Card.TFrame',
        background=Luxury2026Colors.BG_SECONDARY,
        relief='solid',
        borderwidth=1,
        bordercolor=Luxury2026Colors.BORDER_LIGHT,
        padding=16
    )
    
    # ===== TREEVIEW (Tablas) =====
    style.configure('Treeview',
        font=ModernTypography.font_body_small(),
        rowheight=40,
        background=Luxury2026Colors.BG_SECONDARY,
        foreground=Luxury2026Colors.TEXT_PRIMARY,
        fieldbackground=Luxury2026Colors.BG_SECONDARY,
        borderwidth=1,
        relief='solid'
    )
    
    style.configure('Treeview.Heading',
        font=ModernTypography.font_body_bold(),
        background=Luxury2026Colors.PRIMARY,
        foreground=Luxury2026Colors.TEXT_PRIMARY,
        borderwidth=0,
        relief='flat',
        padding=12
    )
    
    style.map('Treeview',
        background=[
            ('selected', Luxury2026Colors.PRIMARY),
            ('alternate', Luxury2026Colors.BG_TERTIARY)
        ],
        foreground=[('selected', Luxury2026Colors.TEXT_PRIMARY)]
    )
    
    # ===== NOTEBOOK (Tabs) =====
    style.configure('TNotebook',
        background=Luxury2026Colors.BG_DARKEST,
        borderwidth=0
    )
    
    style.configure('TNotebook.Tab',
        font=ModernTypography.font_body_bold(),
        padding=[16, 12],
        background=Luxury2026Colors.BG_SECONDARY,
        foreground=Luxury2026Colors.TEXT_SECONDARY,
        borderwidth=0,
        relief='flat'
    )
    
    style.map('TNotebook.Tab',
        background=[
            ('selected', Luxury2026Colors.BG_TERTIARY),
            ('active', Luxury2026Colors.BG_HOVER)
        ],
        foreground=[
            ('selected', Luxury2026Colors.PRIMARY)
        ]
    )
    
    # ===== SCROLLBAR =====
    style.configure('Vertical.TScrollbar',
        background=Luxury2026Colors.BG_SECONDARY,
        troughcolor=Luxury2026Colors.BG_DARKEST,
        borderwidth=0,
        arrowcolor=Luxury2026Colors.PRIMARY,
        darkcolor=Luxury2026Colors.BORDER,
        lightcolor=Luxury2026Colors.BORDER_LIGHT
    )
    
    style.map('Vertical.TScrollbar',
        background=[('active', Luxury2026Colors.BORDER)]
    )


# ===== COMPONENTES VISUALES ENAMORANTES =====
class CardLuxury(ttk.Frame):
    """Card moderno minimalista"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='Card.TFrame', **kwargs)


class BotonPrimario(ttk.Button):
    """Botón primario indigo vibrante"""
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('style', 'Luxury.Primary.TButton')
        super().__init__(parent, **kwargs)


class BotonSecundario(ttk.Button):
    """Botón secundario transparente"""
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('style', 'Luxury.Secondary.TButton')
        super().__init__(parent, **kwargs)


class BotonAccent(ttk.Button):
    """Botón accent verde esmeralda"""
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('style', 'Luxury.Accent.TButton')
        super().__init__(parent, **kwargs)


class BotonPeligro(ttk.Button):
    """Botón peligro rojo suave"""
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('style', 'Luxury.Danger.TButton')
        super().__init__(parent, **kwargs)


class TituloDisplay(ttk.Label):
    """Título display enamorante"""
    def __init__(self, parent, text="", **kwargs):
        super().__init__(parent, text=text, style='Display.TLabel', **kwargs)


class TituloEncabezado(ttk.Label):
    """Encabezado enamorante"""
    def __init__(self, parent, text="", **kwargs):
        super().__init__(parent, text=text, style='Heading.TLabel', **kwargs)


class TextoSecundario(ttk.Label):
    """Texto secundario gris"""
    def __init__(self, parent, text="", **kwargs):
        super().__init__(parent, text=text, style='Secondary.TLabel', **kwargs)

def add_placeholder(entry: "tk.Entry", text: str,
                    fg_placeholder: str = "#6B7280",
                    fg_normal: str = "#E2E8F0") -> None:
    """Agrega placeholder text a un tk.Entry.
    El texto desaparece al hacer foco y vuelve si queda vacío."""
    entry.insert(0, text)
    entry.config(fg=fg_placeholder)

    def on_focus_in(event):
        if entry.get() == text:
            entry.delete(0, "end")
            entry.config(fg=fg_normal)

    def on_focus_out(event):
        if not entry.get().strip():
            entry.insert(0, text)
            entry.config(fg=fg_placeholder)

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
