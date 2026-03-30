"""
Componentes de interfaz premium y profesionales
Encabezados, navegación, y elementos visuales sofisticados
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from src.app.styles.premium import PremiumColors, Typography, FrameCard


class EncabezadoProfesional(ttk.Frame):
    """
    Encabezado profesional con logo, título, y barra de información
    Estilo: Figma / GitHub Enterprise
    """
    
    def __init__(self, parent, titulo="", subtitulo="", logo_img=None, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.configure(height=120, relief='solid', borderwidth=0)
        
        # Contenedor principal
        contenedor = ttk.Frame(self, style='TFrame')
        contenedor.pack(fill='both', expand=True, padx=20, pady=16)
        
        # Row 1: Logo + Título
        row_header = ttk.Frame(contenedor, style='TFrame')
        row_header.pack(fill='x', pady=(0, 12))
        
        if logo_img:
            label_logo = ttk.Label(row_header, image=logo_img)
            label_logo.pack(side='left', padx=(0, 16))
        
        # Grupo de texto
        text_group = ttk.Frame(row_header, style='TFrame')
        text_group.pack(side='left', fill='both', expand=True)
        
        # Título
        if titulo:
            ttk.Label(text_group, 
                     text=titulo, 
                     style='Title.TLabel',
                     foreground=PremiumColors.PRIMARY_DARK).pack(anchor='w')
        
        # Subtítulo
        if subtitulo:
            ttk.Label(text_group, 
                     text=subtitulo, 
                     style='Secondary.TLabel').pack(anchor='w', pady=(2, 0))
        
        # Row 2: Línea divisoria
        separador = ttk.Frame(contenedor, height=1)
        separador.pack(fill='x', pady=(8, 0))


class BarraInformacion(ttk.Frame):
    """
    Barra con estadísticas clave (KPIs)
    Muestra: Total productos, Stock bajo, Última actualización, etc.
    """
    
    def __init__(self, parent, kpis=None, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.kpis = kpis or {}
        self._crear_kpis()
    
    def _crear_kpis(self):
        """Crea los widgets de KPI"""
        for idx, (label, valor, icono) in enumerate(self.kpis.items()):
            self._crear_kpi_item(label, valor, icono)
    
    def _crear_kpi_item(self, label, valor, icono):
        """Crea un item individual de KPI"""
        frame = ttk.Frame(self)
        frame.pack(side='left', padx=12, pady=8, fill='both', expand=True)
        
        # Icono + Valor
        row1 = ttk.Frame(frame, style='TFrame')
        row1.pack(anchor='w')
        
        if icono:
            ttk.Label(row1, text=icono, font=('Arial', 16)).pack(side='left', padx=(0, 6))
        
        ttk.Label(row1, text=str(valor), 
                 font=Typography.font_heading_lg(),
                 foreground=PremiumColors.PRIMARY).pack(side='left')
        
        # Label
        ttk.Label(frame, text=label, style='Secondary.TLabel').pack(anchor='w')


class TarjetaEstadistica(FrameCard):
    """
    Tarjeta para mostrar una estadística o métrica
    Estilo card moderno con sombra simulada
    """
    
    def __init__(self, parent, titulo="", valor="", subtexto="", color_primario=PremiumColors.ACCENT, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Contenedor principal
        contenedor = ttk.Frame(self, style='TFrame')
        contenedor.pack(fill='both', expand=True)
        
        # Línea de color arriba
        ttk.Frame(contenedor, height=3, relief='solid', borderwidth=0).pack(fill='x')
        
        # Contenido
        content = ttk.Frame(contenedor, style='TFrame')
        content.pack(fill='both', expand=True, padx=12, pady=12)
        
        # Valor principal
        if valor:
            ttk.Label(content, 
                     text=str(valor),
                     font=Typography.font_display_lg(),
                     foreground=color_primario).pack(anchor='w')
        
        # Título
        if titulo:
            ttk.Label(content, 
                     text=titulo,
                     font=Typography.font_body_semibold(),
                     foreground=PremiumColors.TEXT_PRIMARY).pack(anchor='w', pady=(4, 0))
        
        # Subtexto
        if subtexto:
            ttk.Label(content,
                     text=subtexto,
                     style='Secondary.TLabel').pack(anchor='w', pady=(2, 0))


class BarraAccionesRapidas(ttk.Frame):
    """
    Barra de acciones rápidas con botones principales
    Facilita acceso a operaciones frecuentes
    """
    
    def __init__(self, parent, acciones=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.acciones = acciones or {}
        self._crear_botones()
    
    def _crear_botones(self):
        """Crea los botones de acción rápida"""
        for icono, label, comando in self.acciones:
            btn = ttk.Button(self, 
                            text=f"{icono} {label}",
                            command=comando,
                            style='Primary.TButton',
                            width=15)
            btn.pack(side='left', padx=6, pady=8)


class PanelBusquedaAvanzada(FrameCard):
    """
    Panel para búsqueda y filtrado avanzado
    Con campos de entrada estilizados
    """
    
    def __init__(self, parent, campos=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.campos = campos or {}
        self.variables = {}
        
        # Título
        ttk.Label(self, text="🔍 Búsqueda Avanzada", 
                 style='Heading.TLabel').pack(anchor='w', pady=(0, 12))
        
        # Crear campos
        for nombre, tipo in self.campos.items():
            frame = ttk.Frame(self)
            frame.pack(fill='x', pady=6)
            
            ttk.Label(frame, text=f"{nombre}:", 
                     style='Secondary.TLabel').pack(anchor='w')
            
            if tipo == 'text':
                var = tk.StringVar()
                ttk.Entry(frame, textvariable=var).pack(fill='x', pady=(2, 0))
                self.variables[nombre] = var
            
            elif tipo == 'number':
                var = tk.StringVar()
                ttk.Entry(frame, textvariable=var).pack(fill='x', pady=(2, 0))
                self.variables[nombre] = var
            
            elif tipo == 'select':
                var = tk.StringVar()
                ttk.Combobox(frame, textvariable=var).pack(fill='x', pady=(2, 0))
                self.variables[nombre] = var
    
    def obtener_filtros(self):
        """Retorna un dict con los filtros ingresados"""
        return {k: v.get() for k, v in self.variables.items() if v.get()}


class NotificacionFlotante(tk.Toplevel):
    """
    Notificación flotante estilo Toast
    Se desvanece automáticamente
    """
    
    def __init__(self, parent, mensaje="", tipo="info", duracion=3000):
        super().__init__(parent)
        self.wm_overrideredirect(True)
        self.wm_attributes('-topmost', True)
        
        # Colores según tipo
        colores = {
            'success': PremiumColors.SUCCESS,
            'error': PremiumColors.DANGER,
            'warning': PremiumColors.WARNING,
            'info': PremiumColors.INFO
        }
        
        bg_color = colores.get(tipo, PremiumColors.INFO)
        
        # Contenedor
        container = ttk.Frame(self)
        container.pack(fill='both', expand=True, padx=12, pady=8)
        
        # Mensaje
        ttk.Label(container, text=mensaje,
                 font=Typography.font_body_semibold(),
                 background=bg_color,
                 foreground=PremiumColors.WHITE).pack()
        
        # Posición: abajo derecha
        self.geometry(f"+{parent.winfo_screenwidth() - 350}+{parent.winfo_screenheight() - 100}")
        
        # Auto-cierre
        self.after(duracion, self.destroy)


class IndicadorCarga(ttk.Frame):
    """
    Indicador de carga animado
    Muestra progreso de operaciones
    """
    
    def __init__(self, parent, texto="Cargando...", **kwargs):
        super().__init__(parent, **kwargs)
        
        # Frame centrado
        frame = ttk.Frame(self, style='TFrame')
        frame.pack(expand=True)
        
        # Animación ASCII
        self.animacion = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.indice = 0
        
        # Label animado
        self.label_anim = ttk.Label(frame,
                                   text=self.animacion[0],
                                   font=('Arial', 24))
        self.label_anim.pack()
        
        # Texto
        ttk.Label(frame, text=texto, 
                 style='Secondary.TLabel').pack(pady=8)
        
        self._animar()
    
    def _animar(self):
        """Anima el indicador de carga"""
        self.label_anim.config(text=self.animacion[self.indice])
        self.indice = (self.indice + 1) % len(self.animacion)
        self.after(100, self._animar)


class TablaMetricas(ttk.Frame):
    """
    Tabla de métricas estilizada
    Muestra datos en formato tabla con colores
    """
    
    def __init__(self, parent, columnas=None, datos=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.columnas = columnas or []
        
        # Crear Treeview
        self.tree = ttk.Treeview(self,
                                columns=self.columnas,
                                height=8,
                                show='headings')
        
        # Configurar columnas
        for col in self.columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')
        
        self.tree.pack(fill='both', expand=True)
        
        # Agregar datos
        if datos:
            for fila in datos:
                self.tree.insert('', 'end', values=fila)
