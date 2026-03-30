"""
DISEÑO PREMIUM EMPRESARIAL - Alfa & Omega
Sistema de diseño sofisticado con gradientes, sombras, y componentes de nivel profesional
Inspirado en: Figma, Linear, Stripe, GitHub Enterprise
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from PIL import Image, ImageDraw, ImageTk
import io

# ===== PALETA DE COLORES PREMIUM =====
class PremiumColors:
    """Colores profesionales nivel enterprise"""
    
    # Primarios (Gradientes de azul profesional)
    PRIMARY_DARK = "#0F172A"       # Azul navy oscuro
    PRIMARY = "#1E293B"            # Azul profesional profundo
    PRIMARY_LIGHT = "#334155"      # Azul gris
    PRIMARY_LIGHTEST = "#F1F5F9"   # Azul muy claro
    
    # Acentos (Verde moderno profesional)
    ACCENT = "#10B981"             # Verde éxito profesional
    ACCENT_LIGHT = "#D1FAE5"       # Verde muy claro
    
    # Secundarios (Púrpura sofisticado)
    SECONDARY = "#8B5CF6"          # Púrpura
    SECONDARY_LIGHT = "#EDE9FE"    # Púrpura muy claro
    
    # Funcionales con mayor contraste
    SUCCESS = "#059669"            # Verde confirmado
    WARNING = "#D97706"            # Ámbar profesional
    DANGER = "#DC2626"             # Rojo crítico
    INFO = "#0284C7"               # Azul información
    
    # Grises de calidad (No puros, con matiz)
    GRAY_950 = "#030712"
    GRAY_900 = "#111827"
    GRAY_800 = "#1F2937"
    GRAY_700 = "#374151"
    GRAY_600 = "#4B5563"
    GRAY_500 = "#6B7280"
    GRAY_400 = "#9CA3AF"
    GRAY_300 = "#D1D5DB"
    GRAY_200 = "#E5E7EB"
    GRAY_100 = "#F3F4F6"
    GRAY_50 = "#F9FAFB"
    WHITE = "#FFFFFF"
    
    # Fondos
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F8FAFC"
    BG_TERTIARY = "#F1F5F9"
    BG_DARK = "#0F172A"
    
    # Texto
    TEXT_PRIMARY = "#0F172A"
    TEXT_SECONDARY = "#475569"
    TEXT_TERTIARY = "#78716C"
    TEXT_INVERSE = "#FFFFFF"
    
    # Bordes
    BORDER_LIGHT = "#E2E8F0"
    BORDER = "#CBD5E1"
    BORDER_DARK = "#94A3B8"


# ===== SOMBRAS Y EFECTOS =====
class Effects:
    """Efectos visuales sofisticados"""
    
    # Shadow levels (para distintos componentes)
    SHADOW_SM = "0 1px 2px 0 rgba(15, 23, 42, 0.05)"
    SHADOW_MD = "0 4px 6px -1px rgba(15, 23, 42, 0.1)"
    SHADOW_LG = "0 10px 15px -3px rgba(15, 23, 42, 0.15)"
    SHADOW_XL = "0 20px 25px -5px rgba(15, 23, 42, 0.2)"
    
    # Blur radii
    BLUR_SMALL = 4
    BLUR_MEDIUM = 12
    BLUR_LARGE = 24


# ===== TIPOGRAFÍA PROFESIONAL =====
class Typography:
    """Sistema de tipografía consistente"""
    
    FONT_FAMILY = "Segoe UI"
    FONT_FAMILY_MONO = "Consolas"
    
    # Tamaños
    SIZE_XS = 11
    SIZE_SM = 12
    SIZE_BASE = 13
    SIZE_LG = 14
    SIZE_XL = 15
    SIZE_2XL = 16
    SIZE_3XL = 18
    SIZE_4XL = 20
    
    @staticmethod
    def font_display_xl():
        return tkFont.Font(family=Typography.FONT_FAMILY, size=24, weight="bold")
    
    @staticmethod
    def font_display_lg():
        return tkFont.Font(family=Typography.FONT_FAMILY, size=20, weight="bold")
    
    @staticmethod
    def font_heading_xl():
        return tkFont.Font(family=Typography.FONT_FAMILY, size=18, weight="bold")
    
    @staticmethod
    def font_heading_lg():
        return tkFont.Font(family=Typography.FONT_FAMILY, size=16, weight="bold")
    
    @staticmethod
    def font_heading():
        return tkFont.Font(family=Typography.FONT_FAMILY, size=14, weight="bold")
    
    @staticmethod
    def font_body_semibold():
        return tkFont.Font(family=Typography.FONT_FAMILY, size=13, weight="bold")
    
    @staticmethod
    def font_body():
        return tkFont.Font(family=Typography.FONT_FAMILY, size=13)
    
    @staticmethod
    def font_body_small():
        return tkFont.Font(family=Typography.FONT_FAMILY, size=12)
    
    @staticmethod
    def font_caption():
        return tkFont.Font(family=Typography.FONT_FAMILY, size=11)
    
    @staticmethod
    def font_code():
        return tkFont.Font(family=Typography.FONT_FAMILY_MONO, size=11)


# ===== CREAR IMÁGENES PARA BOTONES Y COMPONENTES =====
def crear_boton_gradiente(ancho, alto, color_inicio, color_fin, radio=8):
    """Crea una imagen con gradiente para botones modernos"""
    img = Image.new('RGBA', (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Dibujar gradiente
    for y in range(alto):
        ratio = y / alto
        # Interpolación RGB
        r = int(int(color_inicio[1:3], 16) * (1 - ratio) + int(color_fin[1:3], 16) * ratio)
        g = int(int(color_inicio[3:5], 16) * (1 - ratio) + int(color_fin[3:5], 16) * ratio)
        b = int(int(color_inicio[5:7], 16) * (1 - ratio) + int(color_fin[5:7], 16) * ratio)
        color = f"#{r:02x}{g:02x}{b:02x}"
        draw.line([(0, y), (ancho, y)], fill=color)
    
    # Bordes redondeados
    draw.rounded_rectangle([(0, 0), (ancho - 1, alto - 1)], radius=radio, outline=color_fin)
    
    return ImageTk.PhotoImage(img)


# ===== APLICAR TEMA PREMIUM =====
def aplicar_tema_premium():
    """Aplica tema premium a toda la aplicación - NIVEL ENTERPRISE"""
    
    style = ttk.Style()
    style.theme_use('clam')
    
    # ===== COLORES BASE =====
    style.configure('.', 
        background=PremiumColors.BG_PRIMARY,
        foreground=PremiumColors.TEXT_PRIMARY
    )
    
    # ===== BOTONES PREMIUM =====
    # Botón primario (Acción principal - Verde profesional)
    style.configure('Primary.TButton',
        font=Typography.font_body_semibold(),
        background=PremiumColors.ACCENT,
        foreground=PremiumColors.WHITE,
        borderwidth=0,
        padding=10,
        relief='flat',
        focuscolor='none'
    )
    style.map('Primary.TButton',
        background=[('active', '#059669'), ('pressed', '#047857'), ('disabled', PremiumColors.GRAY_400)],
        foreground=[('disabled', PremiumColors.GRAY_600)]
    )
    
    # Botón secundario (Acciones menos importantes)
    style.configure('Secondary.TButton',
        font=Typography.font_body_semibold(),
        background=PremiumColors.GRAY_100,
        foreground=PremiumColors.PRIMARY,
        borderwidth=1,
        padding=10,
        relief='solid',
        focuscolor='none',
        bordercolor=PremiumColors.BORDER
    )
    style.map('Secondary.TButton',
        background=[('active', PremiumColors.GRAY_200), ('pressed', PremiumColors.GRAY_300)],
        bordercolor=[('active', PremiumColors.PRIMARY)]
    )
    
    # Botón peligroso (Eliminar, etc)
    style.configure('Danger.TButton',
        font=Typography.font_body_semibold(),
        background=PremiumColors.DANGER,
        foreground=PremiumColors.WHITE,
        borderwidth=0,
        padding=10,
        relief='flat',
        focuscolor='none'
    )
    style.map('Danger.TButton',
        background=[('active', '#B91C1C'), ('pressed', '#991B1B')],
    )
    
    # Botón éxito
    style.configure('Success.TButton',
        font=Typography.font_body_semibold(),
        background=PremiumColors.SUCCESS,
        foreground=PremiumColors.WHITE,
        borderwidth=0,
        padding=10,
        relief='flat'
    )
    style.map('Success.TButton',
        background=[('active', '#047857'), ('pressed', '#065F46')]
    )
    
    # ===== CAMPOS DE ENTRADA =====
    style.configure('TEntry',
        font=Typography.font_body(),
        padding=8,
        background=PremiumColors.BG_PRIMARY,
        foreground=PremiumColors.TEXT_PRIMARY,
        fieldbackground=PremiumColors.BG_PRIMARY,
        borderwidth=1,
        relief='solid'
    )
    style.map('TEntry',
        fieldbackground=[('focus', PremiumColors.BG_SECONDARY)],
        borderwidth=[('focus', 2)],
    )
    
    # ===== LABELS =====
    style.configure('Title.TLabel',
        font=Typography.font_display_lg(),
        background=PremiumColors.BG_PRIMARY,
        foreground=PremiumColors.PRIMARY_DARK
    )
    
    style.configure('Heading.TLabel',
        font=Typography.font_heading_lg(),
        background=PremiumColors.BG_PRIMARY,
        foreground=PremiumColors.PRIMARY
    )
    
    style.configure('Subheading.TLabel',
        font=Typography.font_heading(),
        background=PremiumColors.BG_PRIMARY,
        foreground=PremiumColors.TEXT_PRIMARY
    )
    
    style.configure('TLabel',
        font=Typography.font_body(),
        background=PremiumColors.BG_PRIMARY,
        foreground=PremiumColors.TEXT_PRIMARY
    )
    
    style.configure('Secondary.TLabel',
        font=Typography.font_body_small(),
        background=PremiumColors.BG_PRIMARY,
        foreground=PremiumColors.TEXT_SECONDARY
    )
    
    # ===== FRAMES =====
    style.configure('TFrame',
        background=PremiumColors.BG_PRIMARY,
        relief='flat',
        borderwidth=0
    )
    
    style.configure('Card.TFrame',
        background=PremiumColors.BG_PRIMARY,
        relief='solid',
        borderwidth=1,
        bordercolor=PremiumColors.BORDER_LIGHT,
        padding=12
    )
    
    # ===== TREEVIEW (Tablas) =====
    style.configure('Treeview',
        font=Typography.font_body_small(),
        rowheight=32,
        background=PremiumColors.BG_PRIMARY,
        foreground=PremiumColors.TEXT_PRIMARY,
        fieldbackground=PremiumColors.BG_PRIMARY,
        borderwidth=1,
        relief='solid'
    )
    
    style.configure('Treeview.Heading',
        font=Typography.font_body_semibold(),
        background=PremiumColors.PRIMARY,
        foreground=PremiumColors.WHITE,
        borderwidth=1,
        relief='solid',
        padding=8
    )
    
    style.map('Treeview',
        background=[('selected', PremiumColors.ACCENT)],
        foreground=[('selected', PremiumColors.WHITE)],
        fieldbackground=[('selected', PremiumColors.ACCENT)]
    )
    
    style.map('Treeview.Heading',
        background=[('active', PremiumColors.PRIMARY_LIGHT)]
    )
    
    # ===== COMBOBOX =====
    style.configure('TCombobox',
        font=Typography.font_body(),
        padding=8,
        background=PremiumColors.BG_PRIMARY,
        foreground=PremiumColors.TEXT_PRIMARY,
        fieldbackground=PremiumColors.BG_PRIMARY,
        borderwidth=1,
        relief='solid'
    )
    
    # ===== NOTEBOOK (Tabs) =====
    style.configure('TNotebook',
        background=PremiumColors.BG_PRIMARY,
        borderwidth=0
    )
    
    style.configure('TNotebook.Tab',
        font=Typography.font_body_semibold(),
        padding=[12, 8],
        background=PremiumColors.GRAY_100,
        foreground=PremiumColors.TEXT_SECONDARY,
        borderwidth=1,
        relief='flat'
    )
    
    style.map('TNotebook.Tab',
        background=[('selected', PremiumColors.ACCENT)],
        foreground=[('selected', PremiumColors.WHITE)]
    )
    
    # ===== SCROLLBAR =====
    style.configure('Vertical.TScrollbar',
        background=PremiumColors.GRAY_100,
        troughcolor=PremiumColors.BG_SECONDARY,
        borderwidth=0,
        arrowcolor=PremiumColors.PRIMARY,
        darkcolor=PremiumColors.GRAY_300,
        lightcolor=PremiumColors.GRAY_200
    )
    
    style.map('Vertical.TScrollbar',
        background=[('active', PremiumColors.GRAY_300)]
    )


# ===== CREAR COMPONENTES PERSONALIZADOS PREMIUM =====
class FrameCard(ttk.Frame):
    """Frame con estilo card - sombra y bordes redondeados simulados"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='Card.TFrame', **kwargs)
        self.configure(
            relief='solid',
            borderwidth=1,
            padding=12
        )


class BotonPrimario(ttk.Button):
    """Botón con estilo primario"""
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('style', 'Primary.TButton')
        super().__init__(parent, **kwargs)


class BotonSecundario(ttk.Button):
    """Botón con estilo secundario"""
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('style', 'Secondary.TButton')
        super().__init__(parent, **kwargs)


class BotonPeligro(ttk.Button):
    """Botón con estilo peligro"""
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('style', 'Danger.TButton')
        super().__init__(parent, **kwargs)


class EncabezadoPrincipal(ttk.Label):
    """Encabezado principal de página"""
    def __init__(self, parent, text="", **kwargs):
        super().__init__(parent, text=text, style='Title.TLabel', **kwargs)


class EncabezadoSeccion(ttk.Label):
    """Encabezado de sección"""
    def __init__(self, parent, text="", **kwargs):
        super().__init__(parent, text=text, style='Heading.TLabel', **kwargs)


class TextoSecundario(ttk.Label):
    """Texto de ayuda o contexto"""
    def __init__(self, parent, text="", **kwargs):
        super().__init__(parent, text=text, style='Secondary.TLabel', **kwargs)


# ===== PALETA DE DEMOSTRACIÓN =====
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Paleta de Colores Premium")
    root.geometry("800x600")
    
    aplicar_tema_premium()
    
    # Mostrar colores
    frame = ttk.Frame(root)
    frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    ttk.Label(frame, text="Colores Premium Alfa & Omega", style='Title.TLabel').pack(pady=10)
    
    # Paleta primaria
    colors_to_show = [
        ("PRIMARY_DARK", PremiumColors.PRIMARY_DARK),
        ("PRIMARY", PremiumColors.PRIMARY),
        ("PRIMARY_LIGHT", PremiumColors.PRIMARY_LIGHT),
        ("ACCENT", PremiumColors.ACCENT),
        ("SECONDARY", PremiumColors.SECONDARY),
        ("SUCCESS", PremiumColors.SUCCESS),
        ("WARNING", PremiumColors.WARNING),
        ("DANGER", PremiumColors.DANGER),
    ]
    
    for name, color in colors_to_show:
        f = ttk.Frame(frame)
        f.pack(fill='x', pady=5)
        
        canvas = tk.Canvas(f, width=50, height=50, bg=color, highlightthickness=0)
        canvas.pack(side='left', padx=5)
        
        ttk.Label(f, text=f"{name}: {color}").pack(side='left', padx=5)
