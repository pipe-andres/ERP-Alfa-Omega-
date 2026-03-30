from typing import Dict, List
from src.database.connection import get_connection
from src.services.price_simulator import simular_precio

def calcular_rotacion_producto(codigo: str, dias: int = 90) -> Dict:
    with get_connection() as conn:
        cur = conn.cursor()
        # Obtiene ventas y días distintos de ventas del kardex/stock moves
        cur.execute(f"""
            SELECT 
                COALESCE(SUM(qty), 0) AS unidades_vendidas,
                COUNT(DISTINCT date(created_at)) AS dias_con_ventas
            FROM stock_movements
            WHERE codigo = ? AND tipo = 'SALE' AND created_at >= date('now', '-{int(dias)} days')
        """, (codigo,))
        row = cur.fetchone()
        
    unidades_vendidas = float(row[0]) if row and row[0] else 0.0
    dias_con_ventas = int(row[1]) if row and row[1] else 0
    velocidad_diaria = unidades_vendidas / dias if dias > 0 else 0.0
    
    if velocidad_diaria >= 1:
        clasificacion = "ALTO"
    elif velocidad_diaria >= 0.1:
        clasificacion = "MEDIO"
    elif velocidad_diaria > 0:
        clasificacion = "BAJO"
    else:
        clasificacion = "CERO"
        
    return {
        "codigo": codigo,
        "unidades_vendidas": unidades_vendidas,
        "dias_con_ventas": dias_con_ventas,
        "velocidad_diaria": velocidad_diaria,
        "clasificacion": clasificacion
    }

def sugerir_precio(codigo: str) -> Dict:
    rotacion = calcular_rotacion_producto(codigo)
    clasificacion = rotacion["clasificacion"]
    
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT nombre, precio FROM productos WHERE codigo = ?", (codigo,))
        prod = cur.fetchone()
        if not prod:
            raise ValueError(f"Producto {codigo} no encontrado")
            
        nombre = prod[0]
        precio_actual = float(prod[1]) if prod[1] else 0.0
        
    if clasificacion in ["CERO", "BAJO"]:
        variacion_pct = -15.0
        razon = "Baja/Cero rotación, reducir para liquidar"
    elif clasificacion == "ALTO":
        variacion_pct = 10.0
        razon = "Alta rotación, aumentar para capturar margen"
    else:
        variacion_pct = 0.0
        razon = "Rotación estable, mantener precio actual"
        
    precio_sugerido = precio_actual * (1 + (variacion_pct / 100.0))
    
    # Se genera simulación del impacto del precio sugerido.
    # Envolvemos en try/except por seguridad en si hay cero costo, etc.
    try:
        simulacion = simular_precio(codigo, precio_sugerido)
    except Exception as e:
        simulacion = {"error": str(e)}
    
    return {
        "codigo": codigo,
        "nombre": nombre,
        "precio_actual": round(precio_actual, 2),
        "precio_sugerido": round(precio_sugerido, 2),
        "variacion_pct": round(variacion_pct, 2),
        "rotacion": clasificacion,
        "velocidad_diaria": round(rotacion["velocidad_diaria"], 4),
        "razon": razon,
        "simulacion": simulacion
    }

def get_sugerencias_pricing() -> List[Dict]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT codigo FROM productos WHERE avg_cost > 0")
        rows = cur.fetchall()
        
    sugerencias = []
    for row in rows:
        cod = row[0]
        try:
            sug = sugerir_precio(cod)
            sugerencias.append(sug)
        except Exception:
            pass
            
    # Ordenar por variacion_pct ASC (primero los que más deben bajar de precio)
    sugerencias.sort(key=lambda x: x["variacion_pct"])
    return sugerencias
