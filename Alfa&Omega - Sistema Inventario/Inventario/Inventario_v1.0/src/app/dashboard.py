"""
Dashboard con gráficos y métricas para Alfa & Omega Inventario
Proporciona visualización de datos en tiempo real
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from src.services.inventory import count_products, stock_global_sum, low_stock_count
from src.services.reports import kardex_rows
from src.app.styles.modern import Colors
from src.app.styles.luxury_2026 import Luxury2026Colors, ModernTypography


class DashboardTab:
    """Tab de Dashboard con métricas y gráficos profesionales"""
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._build_dashboard()
    
    def _build_dashboard(self):
        """Construye el dashboard con JERARQUÍA VISUAL MEMORABLE"""
        
        # ===== FILA 1: MÉTRICA PRINCIPAL (DOMINA) =====
        frame_principal = tk.Frame(self.frame, bg=Luxury2026Colors.BG_SECONDARY, relief="flat")
        frame_principal.pack(fill="x", pady=(0, 20), padx=0)
        
        # Obtener datos
        total_productos = count_products()
        stock_total = stock_global_sum()
        bajo_stock = low_stock_count()
        valor_inventario = self._calcular_valor_inventario()
        
        # Label pequeño: "Valor Total del Inventario"
        label_principal = tk.Label(
            frame_principal,
            text="Valor Total del Inventario",
            font=ModernTypography.font_body_small(),
            bg=Luxury2026Colors.BG_SECONDARY,
            fg=Luxury2026Colors.TEXT_SECONDARY
        )
        label_principal.pack(anchor="w", padx=24, pady=(16, 4))
        
        # NÚMERO GRANDE QUE DOMINA: 32px, bold, color PRIMARY
        valor_label = tk.Label(
            frame_principal,
            text=f"${valor_inventario:,.0f}",
            font=("Arial", 36, "bold"),
            bg=Luxury2026Colors.BG_SECONDARY,
            fg=Luxury2026Colors.PRIMARY
        )
        valor_label.pack(anchor="w", padx=24, pady=(0, 8))
        
        # Info secundaria: tendencia o actualización
        info_label = tk.Label(
            frame_principal,
            text=f"📦 {total_productos} productos | 📊 {stock_total} unidades en stock",
            font=ModernTypography.font_body_small(),
            bg=Luxury2026Colors.BG_SECONDARY,
            fg=Luxury2026Colors.TEXT_TERTIARY
        )
        info_label.pack(anchor="w", padx=24, pady=(0, 16))
        
        # ===== FILA 2: MÉTRICAS SECUNDARIAS (3 columnas) =====
        frame_metrics = ttk.Frame(self.frame)
        frame_metrics.pack(fill="x", pady=(0, 20))
        
        # Métrica 2: Stock Total
        self._create_metric_box_mejorada(
            frame_metrics, 
            "📈",
            "Stock Total",
            str(stock_total),
            Luxury2026Colors.SUCCESS,
            0
        )
        
        # Métrica 3: Bajo Stock (ALERTA)
        self._create_metric_box_mejorada(
            frame_metrics,
            "⚠️",
            "Bajo Stock",
            str(bajo_stock),
            Luxury2026Colors.DANGER,
            1
        )
        
        # Métrica 4: Productos Activos
        self._create_metric_box_mejorada(
            frame_metrics,
            "✅",
            "Activos",
            str(total_productos),
            Luxury2026Colors.ACCENT,
            2
        )
        
        # ===== FILA 3: Gráficos =====
        frame_graficos = ttk.LabelFrame(self.frame, text="📈 Análisis Detallado", padding=10)
        frame_graficos.pack(fill="both", expand=True, pady=(0, 15))
        
        # Crear frame para gráficos lado a lado
        frame_left = ttk.Frame(frame_graficos)
        frame_left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        frame_right = ttk.Frame(frame_graficos)
        frame_right.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Gráfico 1: Movimientos últimos 30 días
        self._create_sales_chart(frame_left)
        
        # Gráfico 2: Top 5 productos
        self._create_top_products_chart(frame_right)
        
        # ===== FILA 4: Alertas =====
        frame_alertas = ttk.LabelFrame(self.frame, text="🔔 Alertas", padding=10)
        frame_alertas.pack(fill="x")
        
        self._create_alerts(frame_alertas)
    
    def _create_metric_box_mejorada(self, parent, icono, titulo, valor, color, col):
        """Crea una caja de métrica MEJORADA con jerarquía"""
        frame = tk.Frame(parent, bg=Luxury2026Colors.BG_SECONDARY, relief="flat", bd=0)
        frame.grid(row=0, column=col, padx=8, pady=8, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        
        # Icono pequeño + título (12px, gris)
        header_frame = tk.Frame(frame, bg=Luxury2026Colors.BG_SECONDARY)
        header_frame.pack(anchor="w", padx=12, pady=(12, 4))
        
        ttk.Label(
            header_frame,
            text=f"{icono} {titulo}",
            font=ModernTypography.font_body_small(),
            background=Luxury2026Colors.BG_SECONDARY,
            foreground=Luxury2026Colors.TEXT_SECONDARY
        ).pack(anchor="w")
        
        # VALOR IMPORTANTE (24px bold, color)
        ttk.Label(
            frame,
            text=valor,
            font=("Arial", 24, "bold"),
            background=Luxury2026Colors.BG_SECONDARY,
            foreground=color
        ).pack(anchor="w", padx=12, pady=(0, 12))
    
    def _create_metric_box(self, parent, titulo, valor, color, row, col):
        """Crea una caja de métrica bonita"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Fondo coloreado
        canvas = tk.Canvas(
            frame,
            bg=color,
            height=100,
            width=150,
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True)
        
        # Título
        canvas.create_text(
            75, 30,
            text=titulo,
            font=("Helvetica", 10, "bold"),
            fill="white"
        )
        
        # Valor
        canvas.create_text(
            75, 65,
            text=valor,
            font=("Helvetica", 28, "bold"),
            fill="white"
        )
    
    def _calcular_valor_inventario(self):
        """Calcula el valor aproximado del inventario"""
        try:
            from src.database.connection import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            # Suma: cantidad * precio_promedio (o precio_costo si existe)
            cursor.execute("""
                SELECT COALESCE(SUM(cantidad * precio_venta * 0.7), 0)
                FROM productos
                WHERE estado = 1
            """)
            resultado = cursor.fetchone()
            conn.close()
            return resultado[0] if resultado else 0.0
        except Exception:
            return 0.0
    
    def _create_sales_chart(self, parent):
        """Crea gráfico de ventas últimos 30 días"""
        try:
            # Obtener datos de ventas
            datos_ventas = self._obtener_ventas_por_dia()
            
            if not datos_ventas:
                ttk.Label(parent, text="Sin datos de ventas").pack(pady=20)
                return
            
            if not MATPLOTLIB_AVAILABLE:
                # Mostrar tabla simple sin matplotlib
                self._create_simple_chart(parent, "Ventas Últimos 30 Días", datos_ventas)
                return
            
            # Crear figura con matplotlib
            fig = Figure(figsize=(5, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            # Ordenar por fecha
            fechas = sorted(datos_ventas.keys())
            valores = [datos_ventas[f] for f in fechas]
            
            # Gráfico de línea con área
            ax.fill_between(range(len(fechas)), valores, alpha=0.3, color="#2196F3")
            ax.plot(range(len(fechas)), valores, marker='o', color="#2196F3", linewidth=2)
            
            # Configurar eje X
            ax.set_xticks([0, len(fechas)//2, len(fechas)-1])
            ax.set_xticklabels([fechas[0].strftime('%d/%m'), fechas[len(fechas)//2].strftime('%d/%m'), fechas[-1].strftime('%d/%m')])
            
            # Labels
            ax.set_title("Ventas Últimos 30 Días", fontsize=12, fontweight='bold')
            ax.set_ylabel("Cantidad Vendida", fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # Integrar en Tkinter
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            ttk.Label(parent, text=f"Error: {str(e)}").pack(pady=20)
    
    def _create_top_products_chart(self, parent):
        """Crea gráfico de top 5 productos vendidos"""
        try:
            # Obtener top productos
            top_productos = self._obtener_top_productos()
            
            if not top_productos:
                ttk.Label(parent, text="Sin datos de productos").pack(pady=20)
                return
            
            if not MATPLOTLIB_AVAILABLE:
                # Mostrar tabla simple sin matplotlib
                self._create_simple_bar_chart(parent, "Top 5 Productos Vendidos", top_productos)
                return
            
            # Crear figura con matplotlib
            fig = Figure(figsize=(5, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            # Extraer nombres y cantidades
            nombres = [p[0][:15] for p in top_productos]  # Limitar nombre a 15 chars
            cantidades = [p[1] for p in top_productos]
            
            # Gráfico de barras horizontal
            colores = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#F44336"]
            bars = ax.barh(nombres, cantidades, color=colores[:len(nombres)])
            
            # Añadir valores en las barras
            for i, (bar, valor) in enumerate(zip(bars, cantidades)):
                ax.text(valor + 1, i, str(int(valor)), va='center', fontsize=9)
            
            # Labels
            ax.set_title("Top 5 Productos Vendidos", fontsize=12, fontweight='bold')
            ax.set_xlabel("Cantidad", fontsize=10)
            ax.set_xlim(0, max(cantidades) * 1.15)
            
            # Integrar en Tkinter
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            ttk.Label(parent, text=f"Error: {str(e)}").pack(pady=20)
    
    def _obtener_ventas_por_dia(self):
        """Obtiene ventas agrupadas por día (últimos 30 días)"""
        try:
            from src.database.connection import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            # Últimos 30 días
            hace_30_dias = datetime.now() - timedelta(days=30)
            
            cursor.execute("""
                SELECT DATE(fecha) as fecha, SUM(cantidad) as total
                FROM kardex
                WHERE tipo = 'Venta' AND fecha >= ?
                GROUP BY DATE(fecha)
                ORDER BY fecha
            """, (hace_30_dias.isoformat(),))
            
            resultado = {}
            for row in cursor.fetchall():
                if row[0]:
                    fecha = datetime.fromisoformat(row[0])
                    resultado[fecha] = row[1] if row[1] else 0
            
            # Llenar días sin ventas
            fecha_actual = hace_30_dias.date()
            while fecha_actual <= datetime.now().date():
                if fecha_actual not in resultado:
                    resultado[fecha_actual] = 0
                fecha_actual = (datetime.combine(fecha_actual, datetime.min.time()) + timedelta(days=1)).date()
            
            conn.close()
            return resultado
            
        except Exception:
            return {}
    
    def _obtener_top_productos(self):
        """Obtiene top 5 productos más vendidos"""
        try:
            from src.database.connection import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.nombre, COALESCE(SUM(k.cantidad), 0) as total
                FROM productos p
                LEFT JOIN kardex k ON p.id = k.producto_id AND k.tipo = 'Venta'
                WHERE p.estado = 1
                GROUP BY p.id, p.nombre
                ORDER BY total DESC
                LIMIT 5
            """)
            
            resultado = cursor.fetchall()
            conn.close()
            return resultado
            
        except Exception:
            return []
    
    def _create_alerts(self, parent):
        """Crea panel de alertas"""
        try:
            alertas = []
            
            # Alerta 1: Stock bajo
            bajo_stock = low_stock_count()
            if bajo_stock > 0:
                alertas.append(("⚠️ STOCK BAJO", f"{bajo_stock} productos con stock bajo (<5 unidades)", "#FF9800"))
            
            # Alerta 2: Sin productos
            total_productos = count_products()
            if total_productos == 0:
                alertas.append(("❌ CATÁLOGO VACÍO", "No hay productos registrados", "#F44336"))
            
            # Alerta 3: Stock crítico
            stock_critico = self._contar_stock_critico()
            if stock_critico > 0:
                alertas.append(("🚨 STOCK CRÍTICO", f"{stock_critico} productos sin stock", "#F44336"))
            
            if not alertas:
                alertas.append(("✅ TODO BIEN", "No hay alertas activas", "#4CAF50"))
            
            # Mostrar alertas
            for titulo, mensaje, color in alertas:
                frame_alerta = ttk.Frame(parent)
                frame_alerta.pack(fill="x", pady=5)
                
                # Canvas coloreado
                canvas = tk.Canvas(
                    frame_alerta,
                    bg=color,
                    height=50,
                    highlightthickness=0
                )
                canvas.pack(fill="x")
                
                # Texto
                canvas.create_text(
                    15, 25,
                    text=titulo,
                    font=("Helvetica", 11, "bold"),
                    fill="white",
                    anchor="w"
                )
                canvas.create_text(
                    15, 40,
                    text=mensaje,
                    font=("Helvetica", 9),
                    fill="white",
                    anchor="w"
                )
        
        except Exception as e:
            ttk.Label(parent, text=f"Error en alertas: {str(e)}").pack(pady=10)
    
    def _contar_stock_critico(self):
        """Cuenta productos sin stock (cantidad = 0)"""
        try:
            from src.database.connection import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM productos WHERE cantidad = 0 AND estado = 1")
            resultado = cursor.fetchone()
            conn.close()
            return resultado[0] if resultado else 0
        except Exception:
            return 0
    
    def _create_simple_chart(self, parent, titulo, datos):
        """Crea un gráfico simple de ventas sin matplotlib"""
        frame = ttk.LabelFrame(parent, text=titulo, padding=10)
        frame.pack(fill="both", expand=True)
        
        # Canvas para dibujar
        canvas = tk.Canvas(frame, bg="white", height=200, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        if not datos:
            canvas.create_text(200, 100, text="Sin datos", font=("Helvetica", 12))
            return
        
        # Dibujar título y referencia
        canvas.create_text(10, 20, text=f"{titulo} (últimos 30 días)", font=("Helvetica", 10, "bold"), anchor="w")
        
        # Crear barras simples
        valores = list(datos.values())
        if valores:
            max_val = max(valores) if valores else 1
            canvas.create_text(10, 180, text=f"Max: {max_val}", font=("Helvetica", 8), anchor="w")
        
        canvas.create_text(10, 195, text="Gráfico de líneas no disponible sin matplotlib", 
                          font=("Helvetica", 9), anchor="w", fill="#666")
    
    def _create_simple_bar_chart(self, parent, titulo, productos):
        """Crea un gráfico simple de barras sin matplotlib"""
        frame = ttk.LabelFrame(parent, text=titulo, padding=10)
        frame.pack(fill="both", expand=True)
        
        # Crear tabla simple
        for i, (nombre, cantidad) in enumerate(productos):
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill="x", pady=2)
            
            # Nombre
            ttk.Label(row_frame, text=nombre[:20], width=20).pack(side="left")
            
            # Barra (usando X's)
            barra_width = min(int(cantidad / 5), 30)
            barra = "█" * max(barra_width, 1)
            
            # Cantidad
            ttk.Label(row_frame, text=f"{barra} {int(cantidad)}", width=40).pack(side="left")
    
    def refresh(self):
        """Refresca el dashboard con datos actualizados"""
        # Limpiar frame
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        # Reconstruir
        self._build_dashboard()
