"""
DETALLES INVISIBLES - Lo que hace memorable a un sistema
Estados vacíos, focus states, disabled states, errores bellos, jerarquía visual
Esto es lo que diferencia Linear/Figma/Notion de software común
"""

import tkinter as tk
from tkinter import ttk
from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography


# ===== COPY CON PERSONALIDAD =====
class CopyPersonalidad:
    """Textos que comunican con tono amable, cercano, nunca robótico"""
    
    # Estados Vacíos - El lugar donde la mayoría de sistemas aburre
    EMPTY_STATES = {
        'productos': {
            'icono': '📦',
            'titulo': 'Sin productos aún',
            'subtitle': 'Crea tu primer producto y verás la magia suceder',
            'cta': 'Crear primer producto'
        },
        'ventas': {
            'icono': '💰',
            'titulo': 'Sin ventas registradas',
            'subtitle': 'Tus ventas aparecerán aquí. ¡Paciencia!',
            'cta': 'Registrar venta'
        },
        'stock_bajo': {
            'icono': '⚠️',
            'titulo': 'Inventario en óptimas condiciones',
            'subtitle': 'No hay productos con stock bajo. ¡Excelente!',
            'cta': None
        },
        'dashboard_inicio': {
            'icono': '✨',
            'titulo': 'Bienvenido a tu inventario',
            'subtitle': 'Aquí verás tus métricas más importantes en tiempo real',
            'cta': None
        }
    }
    
    # Mensajes de Error - No asustan, guían
    ERROR_MESSAGES = {
        'producto_no_encontrado': {
            'titulo': '🔍 Producto no encontrado',
            'mensaje': 'El producto que buscas no existe. ¿Crearlo?',
            'tono': 'amable'
        },
        'stock_insuficiente': {
            'titulo': '⚠️ Stock insuficiente',
            'mensaje': 'No hay suficiente stock para completar esta operación.',
            'sugerencia': 'Stock disponible: {disponible}',
            'tono': 'informativo'
        },
        'campo_requerido': {
            'titulo': '📝 Campo obligatorio',
            'mensaje': 'Por favor completa este campo para continuar',
            'tono': 'cercano'
        },
        'error_generico': {
            'titulo': '⚡ Algo salió mal',
            'mensaje': 'No te preocupes, nuestro equipo lo revisa.',
            'codigo': 'Error: {codigo}',
            'tono': 'tranquilizador'
        }
    }
    
    # Confirmaciones - Tranquilizan
    CONFIRMACIONES = {
        'producto_creado': {
            'titulo': '✅ Producto creado',
            'mensaje': 'Ya está en tu inventario',
            'tiempo': 3000
        },
        'producto_eliminado': {
            'titulo': '🗑️ Producto eliminado',
            'mensaje': 'Se eliminó correctamente',
            'tiempo': 3000
        },
        'cambios_guardados': {
            'titulo': '💾 Cambios guardados',
            'mensaje': 'Todo está actualizado',
            'tiempo': 2000
        },
        'operacion_exitosa': {
            'titulo': '🎉 Listo',
            'mensaje': 'Operación completada con éxito',
            'tiempo': 2500
        }
    }
    
    # Focus Messages - Ayudan sin ser intrusivos
    FOCUS_HINTS = {
        'nombre_producto': 'Ej: Eau de Parfum Premium',
        'precio': 'Precio de venta (sin decimales)',
        'cantidad': 'Stock inicial en unidades',
        'categoria': 'Selecciona o crea una nueva',
        'descripcion': 'Notas, aroma, característica especial...'
    }


# ===== JERARQUÍA VISUAL - EL OJO SABE QUÉ MIRAR =====
class JerarquiaVisual:
    """Tamaños y pesos que guían al ojo automáticamente"""
    
    # Niveles de Importancia (como en Figma/Linear)
    NIVEL_CRITICO = {
        'tamanio': 32,
        'peso': 'bold',
        'color': Luxury2026Colors.PRIMARY,
        'ejemplo': 'Ventas Totales: $XXX,XXX'
    }
    
    NIVEL_IMPORTANTE = {
        'tamanio': 24,
        'peso': 'bold',
        'color': Luxury2026Colors.TEXT_PRIMARY,
        'ejemplo': 'Top 5 Productos'
    }
    
    NIVEL_SECUNDARIO = {
        'tamanio': 16,
        'peso': 'normal',
        'color': Luxury2026Colors.TEXT_PRIMARY,
        'ejemplo': 'Stock disponible'
    }
    
    NIVEL_TERCIARIO = {
        'tamanio': 14,
        'peso': 'normal',
        'color': Luxury2026Colors.TEXT_SECONDARY,
        'ejemplo': 'Última actualización: hace 2 minutos'
    }
    
    NIVEL_DETALLE = {
        'tamanio': 12,
        'peso': 'normal',
        'color': Luxury2026Colors.TEXT_TERTIARY,
        'ejemplo': 'Editado por: admin@sistema.com'
    }


# ===== ESTADOS VISUALES ELEGANTES =====
class EstadosVisuales:
    """Focus, Disabled, Loading, Error - Todos bellos, nunca feos"""
    
    @staticmethod
    def crear_focus_style():
        """Focus que brilla, no que asusta"""
        return {
            'borderwidth': 2,
            'bordercolor': Luxury2026Colors.PRIMARY,
            'sombra': '0 0 0 3px rgba(99, 102, 241, 0.1)',  # Halo suave
        }
    
    @staticmethod
    def crear_disabled_style():
        """Disabled que comunica "no disponible ahora", no "roto"."""
        return {
            'background': Luxury2026Colors.BG_TERTIARY,
            'foreground': Luxury2026Colors.TEXT_TERTIARY,
            'opacity': 0.5,
            'cursor': 'not-allowed'
        }
    
    @staticmethod
    def crear_loading_style():
        """Loading que es elegante, no que distrae"""
        return {
            'color_primario': Luxury2026Colors.PRIMARY,
            'color_secundario': Luxury2026Colors.BG_TERTIARY,
            'velocidad': 0.8,  # segundos por frame
            'caracteres': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        }
    
    @staticmethod
    def crear_error_style():
        """Errores que informan sin asustar"""
        return {
            'background': Luxury2026Colors.BG_SECONDARY,
            'border': Luxury2026Colors.DANGER,
            'borderwidth': 1,
            'icon': '⚠️',
            'timeout': 5000  # 5 segundos
        }


# ===== EMPTY STATE COMPONENT HERMOSO =====
class EmptyStateHermoso(ttk.Frame):
    """Estado vacío que enamora, no que deprime"""
    
    def __init__(self, parent, tipo='productos', **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        
        data = CopyPersonalidad.EMPTY_STATES.get(tipo, {})
        
        # Contenedor centrado
        container = ttk.Frame(self, style='TFrame')
        container.pack(expand=True, pady=60)
        
        # Icono grande y suave (no amenazante)
        ttk.Label(container, 
                 text=data.get('icono', '✨'),
                 font=('Arial', 64),
                 background=Luxury2026Colors.BG_DARKEST,
                 foreground=Luxury2026Colors.TEXT_SECONDARY).pack(pady=(0, 20))
        
        # Título
        ttk.Label(container, 
                 text=data.get('titulo', ''),
                 font=ModernTypography.font_heading_lg(),
                 background=Luxury2026Colors.BG_DARKEST,
                 foreground=Luxury2026Colors.TEXT_PRIMARY).pack(pady=(0, 8))
        
        # Subtítulo (el copy personal)
        ttk.Label(container, 
                 text=data.get('subtitle', ''),
                 style='Secondary.TLabel',
                 background=Luxury2026Colors.BG_DARKEST).pack(pady=(0, 24))
        
        # CTA si existe
        if data.get('cta'):
            btn = ttk.Button(container, text=f"✨ {data['cta']}", 
                           style='Luxury.Primary.TButton')
            btn.pack()


# ===== JERARQUÍA EN DASHBOARD =====
class DashboardJerarquico(ttk.Frame):
    """Dashboard donde el ojo sabe qué es importante"""
    
    def __init__(self, parent, datos=None, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        
        if datos is None:
            datos = {}
        
        # NIVEL CRÍTICO - Métrica principal enorme
        main_frame = ttk.Frame(self, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=32, pady=32)
        
        # Métrica crítica (venta total, etc)
        if 'metrica_principal' in datos:
            metric = datos['metrica_principal']
            
            ttk.Label(main_frame, 
                     text=metric.get('label', ''),
                     style='Secondary.TLabel',
                     background=Luxury2026Colors.BG_DARKEST).pack(anchor='w')
            
            ttk.Label(main_frame, 
                     text=str(metric.get('valor', '')),
                     font=ModernTypography.font_display(),
                     background=Luxury2026Colors.BG_DARKEST,
                     foreground=Luxury2026Colors.PRIMARY).pack(anchor='w', pady=(4, 24))
        
        # NIVEL IMPORTANTE - Secundarias (3 columnas)
        secondary_frame = ttk.Frame(main_frame, style='TFrame')
        secondary_frame.pack(fill='x', pady=(24, 0))
        
        secundarias = datos.get('metricas_secundarias', [])
        for idx, metric in enumerate(secundarias[:3]):
            col = ttk.Frame(secondary_frame, style='TFrame')
            col.pack(side='left', fill='both', expand=True, padx=(0, 16 if idx < 2 else 0))
            
            ttk.Label(col,
                     text=metric.get('label', ''),
                     style='Secondary.TLabel',
                     background=Luxury2026Colors.BG_DARKEST).pack(anchor='w')
            
            ttk.Label(col,
                     text=str(metric.get('valor', '')),
                     font=ModernTypography.font_heading_xl(),
                     background=Luxury2026Colors.BG_DARKEST,
                     foreground=metric.get('color', Luxury2026Colors.ACCENT)).pack(anchor='w', pady=(4, 0))


# ===== FOCUS STATE INDICADOR =====
class FocusIndicador(ttk.Frame):
    """Cuando un campo está focused, parece que brilla"""
    
    def __init__(self, parent, label="", placeholder="", hint="", **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        
        # Label
        ttk.Label(self, text=label,
                 font=ModernTypography.font_body_small(),
                 background=Luxury2026Colors.BG_DARKEST,
                 foreground=Luxury2026Colors.TEXT_PRIMARY).pack(anchor='w', pady=(0, 4))
        
        # Entry con hint
        entry_frame = ttk.Frame(self, style='TFrame')
        entry_frame.pack(fill='x')
        
        entry = ttk.Entry(entry_frame)
        entry.pack(fill='x')
        entry.insert(0, placeholder)
        
        # Hint debajo (solo visible cuando está focused)
        hint_label = ttk.Label(entry_frame,
                              text=hint,
                              style='Secondary.TLabel',
                              background=Luxury2026Colors.BG_DARKEST)
        hint_label.pack(anchor='w', pady=(4, 0))
        
        # Mostrar/ocultar hint según focus
        def on_focus(event):
            hint_label.config(foreground=Luxury2026Colors.TEXT_SECONDARY)
        
        def on_blur(event):
            hint_label.config(foreground=Luxury2026Colors.TEXT_TERTIARY)
        
        entry.bind('<FocusIn>', on_focus)
        entry.bind('<FocusOut>', on_blur)


# ===== ERROR ELEGANTE =====
class ErrorElegante(ttk.Frame):
    """Errores que guían, no que asustan"""
    
    def __init__(self, parent, tipo='campo_requerido', **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        
        data = CopyPersonalidad.ERROR_MESSAGES.get(tipo, {})
        
        self.configure(bg=Luxury2026Colors.BG_SECONDARY, 
                      relief='solid', borderwidth=1, padding=12)
        
        # Título
        ttk.Label(self, text=data.get('titulo', ''),
                 font=ModernTypography.font_body_bold(),
                 background=Luxury2026Colors.BG_SECONDARY,
                 foreground=Luxury2026Colors.DANGER).pack(anchor='w')
        
        # Mensaje
        ttk.Label(self, text=data.get('mensaje', ''),
                 style='Secondary.TLabel',
                 background=Luxury2026Colors.BG_SECONDARY).pack(anchor='w', pady=(4, 0))


# ===== CONFIRMACIÓN HERMOSA =====
class ConfirmacionHermosa(tk.Toplevel):
    """Confirmación que se siente bien"""
    
    def __init__(self, parent, tipo='producto_creado', **kwargs):
        super().__init__(parent)
        self.wm_overrideredirect(True)
        self.wm_attributes('-topmost', True)
        
        data = CopyPersonalidad.CONFIRMACIONES.get(tipo, {})
        
        # Frame principal
        frame = ttk.Frame(self, style='Card.TFrame')
        frame.pack(fill='both', expand=True, padx=16, pady=16)
        
        # Título
        ttk.Label(frame, text=data.get('titulo', ''),
                 font=ModernTypography.font_body_bold(),
                 background=Luxury2026Colors.BG_SECONDARY,
                 foreground=Luxury2026Colors.SUCCESS).pack(anchor='w')
        
        # Mensaje
        ttk.Label(frame, text=data.get('mensaje', ''),
                 style='Secondary.TLabel',
                 background=Luxury2026Colors.BG_SECONDARY).pack(anchor='w', pady=(4, 0))
        
        # Posición: abajo derecha
        self.geometry(f"+{parent.winfo_screenwidth() - 350}+{parent.winfo_screenheight() - 120}")
        
        # Auto-cierre
        tiempo = data.get('tiempo', 3000)
        self.after(tiempo, self.destroy)


# ===== TABLA CON JERARQUÍA =====
class TablaJerarquica(ttk.Treeview):
    """Tabla donde columnas importantes destacan"""
    
    def __init__(self, parent, columnas_config=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # columnas_config ejemplo:
        # {'nombre': {'peso': 'importante'}, 'precio': {'peso': 'importante'}, 'stock': {'peso': 'secundario'}}
        
        if columnas_config is None:
            columnas_config = {}
        
        # Configurar estilos por columna
        for col, config in columnas_config.items():
            peso = config.get('peso', 'normal')
            if peso == 'importante':
                # Columna importante: fuente bold
                self.heading(col, text=col)
            elif peso == 'secundario':
                # Columna secundaria: gris
                self.heading(col, text=col)
