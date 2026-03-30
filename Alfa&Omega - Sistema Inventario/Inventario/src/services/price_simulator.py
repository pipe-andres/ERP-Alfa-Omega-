from typing import Dict
from src.database.connection import get_connection

def simular_precio(codigo: str, nuevo_precio: float) -> Dict:
    with get_connection() as conn:
        cur = conn.cursor()
        
        # 1. Obtener producto
        cur.execute("SELECT nombre, precio, avg_cost, cantidad FROM productos WHERE codigo = ?", (codigo,))
        prod = cur.fetchone()
        if not prod:
            raise ValueError(f"Producto {codigo} no encontrado")
            
        nombre = prod[0]
        precio_actual = float(prod[1]) if prod[1] else 0.0
        avg_cost = float(prod[2]) if prod[2] else 0.0
        
        # 2. Obtener ventas promedio estimadas de los últimos 3 meses (tipo 'SALE')
        cur.execute("""
            SELECT COALESCE(SUM(qty), 0) / 3.0
            FROM stock_movements
            WHERE codigo = ? AND tipo = 'SALE' AND created_at >= date('now', '-3 months')
        """, (codigo,))
        ventas_row = cur.fetchone()
        ventas_promedio_mes = float(ventas_row[0]) if ventas_row else 0.0
        
    # 3. Cálculos requeridos
    margen_actual_pct = ((precio_actual - avg_cost) / precio_actual * 100) if precio_actual > 0 else 0.0
    margen_nuevo_pct = ((nuevo_precio - avg_cost) / nuevo_precio * 100) if nuevo_precio > 0 else 0.0
    variacion_precio_pct = ((nuevo_precio - precio_actual) / precio_actual * 100) if precio_actual > 0 else 0.0
    
    utilidad_actual_mes = (precio_actual - avg_cost) * ventas_promedio_mes
    
    # Para mantener la misma utilidad bruta
    margen_nominal_nuevo = nuevo_precio - avg_cost
    if margen_nominal_nuevo > 0:
        unidades_necesarias = utilidad_actual_mes / margen_nominal_nuevo
    else:
        unidades_necesarias = float('inf')  # inalcanzable si hay pérdida por unidad
        
    if ventas_promedio_mes > 0:
        aumento_volumen_pct = ((unidades_necesarias / ventas_promedio_mes) - 1) * 100
    else:
        aumento_volumen_pct = 0.0
        
    es_viable = margen_nuevo_pct > 0
    alerta = ""
    if nuevo_precio < avg_cost:
        alerta = "El precio nuevo está por debajo del costo promedio. Se generarán pérdidas."
    elif nuevo_precio == avg_cost:
        alerta = "El precio nuevo es igual al costo. Margen 0%."
        
    return {
        "codigo": codigo,
        "nombre": nombre,
        "precio_actual": round(precio_actual, 2),
        "nuevo_precio": round(nuevo_precio, 2),
        "avg_cost": round(avg_cost, 2),
        "margen_actual_pct": round(margen_actual_pct, 2),
        "margen_nuevo_pct": round(margen_nuevo_pct, 2),
        "variacion_precio_pct": round(variacion_precio_pct, 2),
        "ventas_promedio_mes": round(ventas_promedio_mes, 2),
        "unidades_necesarias": round(unidades_necesarias, 2) if unidades_necesarias != float('inf') else 999999.99,
        "aumento_volumen_pct": round(aumento_volumen_pct, 2),
        "es_viable": es_viable,
        "alerta": alerta
    }

def get_precio_optimo(codigo: str) -> Dict:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT avg_cost FROM productos WHERE codigo = ?", (codigo,))
        prod = cur.fetchone()
        if not prod:
            raise ValueError(f"Producto {codigo} no encontrado")
        avg_cost = float(prod[0]) if prod[0] else 0.0
        
    # Precio óptimo al 30% de margen
    precio_optimo = avg_cost / (1 - 0.30) if avg_cost > 0 else 0.0
    return simular_precio(codigo, precio_optimo)
