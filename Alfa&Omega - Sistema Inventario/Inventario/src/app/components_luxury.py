"""
Componentes ENAMORANTES - Estilo Notion/Figma/Linear 2026
Interfaz que hace que el usuario se enamore del sistema
"""

import tkinter as tk
from tkinter import ttk
from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography


class EncabezadoLuxury(ttk.Frame):
    """Encabezado enamorante tipo Notion/Figma"""
    
    def __init__(self, parent, titulo="", subtitulo="", logo_img=None, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.configure(height=140, relief='flat', borderwidth=0, bg=Luxury2026Colors.BG_DARKEST)
        
        # Contenedor principal con padding generoso
        contenedor = ttk.Frame(self, style='TFrame')
        contenedor.pack(fill='both', expand=True, padx=32, pady=24)
        
        # Row 1: Logo + Títulos
        row_header = ttk.Frame(contenedor, style='TFrame')
        row_header.pack(fill='x', pady=(0, 16))
        
        if logo_img:
            label_logo = ttk.Label(row_header, image=logo_img, background=Luxury2026Colors.BG_DARKEST)
            label_logo.pack(side='left', padx=(0, 20))
        
        # Grupo de texto
        text_group = ttk.Frame(row_header, style='TFrame')
        text_group.pack(side='left', fill='both', expand=True)
        
        # Título principal (Grande y vibrante)
        if titulo:
            ttk.Label(text_group, 
                     text=titulo, 
                     style='Display.TLabel',
                     foreground=Luxury2026Colors.TEXT_PRIMARY,
                     background=Luxury2026Colors.BG_DARKEST).pack(anchor='w')
        
        # Subtítulo (Gris suave)
        if subtitulo:
            ttk.Label(text_group, 
                     text=subtitulo, 
                     style='Secondary.TLabel',
                     background=Luxury2026Colors.BG_DARKEST).pack(anchor='w', pady=(8, 0))
        
        # Línea divisoria sutil
        divider = ttk.Frame(contenedor, height=1, relief='solid', borderwidth=1)
        divider.pack(fill='x', pady=(12, 0))


class KPICard(ttk.Frame):
    """
    Tarjeta KPI enamorante con JERARQUÍA VISUAL
    - Métrica principal: DOMINA visualmente (32px bold, color vibrante)
    - Info secundaria: Discreta (14px gris)
    - El ojo automáticamente ve lo importante
    """
    
    def __init__(self, parent, icono="", label="", valor="", 
                 valor_secundario="", trend="", color=Luxury2026Colors.PRIMARY, 
                 es_principal=False, **kwargs):
        super().__init__(parent, style='Card.TFrame', **kwargs)
        self.configure(bg=Luxury2026Colors.BG_SECONDARY, relief='flat', borderwidth=0, padding=16)
        
        # Contenedor vertical
        content = ttk.Frame(self, style='TFrame')
        content.pack(fill='both', expand=True)
        
        # Fila superior: Icono + Label (PEQUEÑO, para que sobresalga el valor)
        header = ttk.Frame(content, style='TFrame')
        header.pack(fill='x', pady=(0, 12))
        
        if icono:
            ttk.Label(header, text=icono, font=ModernTypography.font_heading_sm(),
                     background=Luxury2026Colors.BG_SECONDARY,
                     foreground=color).pack(side='left', padx=(0, 8))
        
        ttk.Label(header, text=label, style='Secondary.TLabel',
                 background=Luxury2026Colors.BG_SECONDARY).pack(side='left')
        
        # VALOR PRINCIPAL - DOMINA la tarjeta
        if es_principal:
            # Principal: 32px, bold, color vibrante
            ttk.Label(content, text=str(valor),
                     font=('Arial', 32, 'bold'),
                     background=Luxury2026Colors.BG_SECONDARY,
                     foreground=color).pack(anchor='w', pady=(8, 4))
        else:
            # Normal: 24px bold
            ttk.Label(content, text=str(valor),
                     font=ModernTypography.font_heading_xl(),
                     background=Luxury2026Colors.BG_SECONDARY,
                     foreground=color).pack(anchor='w', pady=(8, 4))
        
        # Info secundaria: pequeña y discreta
        secondary_frame = ttk.Frame(content, style='TFrame')
        secondary_frame.pack(fill='x', pady=(8, 0))
        
        if valor_secundario:
            ttk.Label(secondary_frame, text=str(valor_secundario),
                     font=('Arial', 12),
                     background=Luxury2026Colors.BG_SECONDARY,
                     foreground=Luxury2026Colors.TEXT_TERTIARY).pack(anchor='w')
        
        # Trend (si existe)
        if trend:
            trend_color = Luxury2026Colors.SUCCESS if trend.startswith('+') else Luxury2026Colors.DANGER
            ttk.Label(secondary_frame, text=trend,
                     font=('Arial', 12, 'bold'),
                     background=Luxury2026Colors.BG_SECONDARY,
                     foreground=trend_color).pack(anchor='w', pady=(4, 0))


class DashboardKPIs(ttk.Frame):
    """Grid de KPIs enamorantes"""
    
    def __init__(self, parent, kpis_data=None, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        
        if kpis_data is None:
            kpis_data = []
        
        # Grid de KPIs (3 columnas responsive)
        for idx, kpi in enumerate(kpis_data):
            card = KPICard(self, 
                          icono=kpi.get('icono', ''),
                          label=kpi.get('label', ''),
                          valor=kpi.get('valor', ''),
                          color=kpi.get('color', Luxury2026Colors.PRIMARY))
            
            row = idx // 3
            col = idx % 3
            card.grid(row=row, column=col, padx=8, pady=8, sticky='ew')
        
        # Configurar pesos de columnas
        for col in range(3):
            self.columnconfigure(col, weight=1)


class BotonGrande(ttk.Button):
    """Botón grande y enamorante para acciones principales"""
    
    def __init__(self, parent, text="", icono="", comando=None, estilo="primary", **kwargs):
        style_map = {
            'primary': 'Luxury.Primary.TButton',
            'secondary': 'Luxury.Secondary.TButton',
            'accent': 'Luxury.Accent.TButton',
            'danger': 'Luxury.Danger.TButton'
        }
        
        label = f"{icono} {text}".strip()
        
        super().__init__(parent, 
                        text=label,
                        command=comando,
                        style=style_map.get(estilo, 'Luxury.Primary.TButton'),
                        width=20,
                        **kwargs)


class SectionTitle(ttk.Label):
    """Título de sección enamorante"""
    
    def __init__(self, parent, text="", **kwargs):
        super().__init__(parent, text=text, style='Heading.TLabel',
                        background=Luxury2026Colors.BG_DARKEST,
                        foreground=Luxury2026Colors.TEXT_PRIMARY, **kwargs)


class EmptyState(ttk.Frame):
    """Estado vacío hermoso (cuando no hay datos)"""
    
    def __init__(self, parent, icono="", titulo="", subtexto="", **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.configure(bg=Luxury2026Colors.BG_DARKEST, height=200)
        
        # Contenedor centrado
        frame = ttk.Frame(self, style='TFrame')
        frame.pack(expand=True, pady=40)
        
        # Icono grande
        ttk.Label(frame, text=icono, font=('Arial', 48),
                 background=Luxury2026Colors.BG_DARKEST,
                 foreground=Luxury2026Colors.TEXT_TERTIARY).pack()
        
        # Título
        ttk.Label(frame, text=titulo,
                 font=ModernTypography.font_heading(),
                 background=Luxury2026Colors.BG_DARKEST,
                 foreground=Luxury2026Colors.TEXT_PRIMARY).pack(pady=(16, 8))
        
        # Subtexto
        ttk.Label(frame, text=subtexto,
                 style='Secondary.TLabel',
                 background=Luxury2026Colors.BG_DARKEST).pack()


class LoadingSpinner(ttk.Frame):
    """Spinner de carga enamorante"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        
        # Animación
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current = 0
        
        frame = ttk.Frame(self, style='TFrame')
        frame.pack(expand=True)
        
        self.label = ttk.Label(frame, text=self.frames[0],
                              font=('Arial', 24),
                              background=Luxury2026Colors.BG_DARKEST,
                              foreground=Luxury2026Colors.PRIMARY)
        self.label.pack(pady=20)
        
        ttk.Label(frame, text="Cargando...",
                 style='Secondary.TLabel',
                 background=Luxury2026Colors.BG_DARKEST).pack()
        
        self._animate()
    
    def _animate(self):
        self.label.config(text=self.frames[self.current])
        self.current = (self.current + 1) % len(self.frames)
        self.after(100, self._animate)


class StatsRow(ttk.Frame):
    """Fila de estadísticas horizontal"""
    
    def __init__(self, parent, stats_list=None, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        
        if stats_list is None:
            stats_list = []
        
        for idx, stat in enumerate(stats_list):
            # Separador
            if idx > 0:
                sep = ttk.Frame(self, height=30, relief='solid', borderwidth=1)
                sep.pack(side='left', padx=16, fill='y')
            
            # Stat item
            item = ttk.Frame(self, style='TFrame')
            item.pack(side='left', padx=12, fill='both', expand=True)
            
            # Número
            ttk.Label(item, text=str(stat.get('valor', '0')),
                     font=ModernTypography.font_heading_lg(),
                     background=Luxury2026Colors.BG_DARKEST,
                     foreground=stat.get('color', Luxury2026Colors.PRIMARY)).pack(anchor='w')
            
            # Label
            ttk.Label(item, text=stat.get('label', ''),
                     style='Secondary.TLabel',
                     background=Luxury2026Colors.BG_DARKEST).pack(anchor='w', pady=(4, 0))


class NotificationBanner(ttk.Frame):
    """Banner de notificación hermoso"""
    
    def __init__(self, parent, tipo="info", titulo="", mensaje="", **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        
        colores = {
            'success': Luxury2026Colors.ACCENT,
            'error': Luxury2026Colors.DANGER,
            'warning': Luxury2026Colors.WARNING,
            'info': Luxury2026Colors.PRIMARY
        }
        
        color = colores.get(tipo, Luxury2026Colors.INFO)
        
        self.configure(bg=Luxury2026Colors.BG_SECONDARY, relief='solid', borderwidth=1, padding=16)
        
        # Barra de color a la izquierda (simulada con etiqueta)
        content = ttk.Frame(self, style='TFrame')
        content.pack(fill='both', expand=True)
        
        # Título
        if titulo:
            ttk.Label(content, text=titulo,
                     font=ModernTypography.font_body_bold(),
                     background=Luxury2026Colors.BG_SECONDARY,
                     foreground=color).pack(anchor='w')
        
        # Mensaje
        if mensaje:
            ttk.Label(content, text=mensaje,
                     style='Secondary.TLabel',
                     background=Luxury2026Colors.BG_SECONDARY).pack(anchor='w', pady=(4, 0))


class FeatureGrid(ttk.Frame):
    """Grid de características enamorante"""
    
    def __init__(self, parent, features=None, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        
        if features is None:
            features = []
        
        for idx, feature in enumerate(features):
            card = ttk.Frame(self, style='Card.TFrame')
            card.grid(row=idx//2, column=idx%2, padx=12, pady=12, sticky='ew')
            
            # Icono
            ttk.Label(card, text=feature.get('icono', '✓'),
                     font=('Arial', 20),
                     background=Luxury2026Colors.BG_SECONDARY,
                     foreground=feature.get('color', Luxury2026Colors.ACCENT)).pack(anchor='w')
            
            # Título
            ttk.Label(card, text=feature.get('titulo', ''),
                     font=ModernTypography.font_body_bold(),
                     background=Luxury2026Colors.BG_SECONDARY,
                     foreground=Luxury2026Colors.TEXT_PRIMARY).pack(anchor='w', pady=(8, 4))
            
            # Descripción
            ttk.Label(card, text=feature.get('desc', ''),
                     style='Secondary.TLabel',
                     background=Luxury2026Colors.BG_SECONDARY).pack(anchor='w')
        
        # Configurar pesos
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

class Tooltip:
    """Tooltip simple que aparece al hacer hover sobre un widget."""
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=self.text,
            font=("Arial", 9),
            bg="#1E2A45", fg="#E2E8F0",
            relief="flat", padx=8, pady=4,
            wraplength=280, justify="left"
        ).pack()

    def _hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
