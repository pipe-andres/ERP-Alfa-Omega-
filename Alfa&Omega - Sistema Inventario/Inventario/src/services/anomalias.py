"""
src/services/anomalias.py
=========================
Detección de anomalías en ventas basada en desviación estándar histórica.
Blueprint 8.2.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

from src.database.connection import get_connection

_LOG = logging.getLogger(__name__)

def calcular_estadisticas_ventas(dias: int = 90) -> Dict[str, Dict[str, Any]]:
    """
    Calcula promedio, max, min y desviación estándar de las ventas diarias
    por producto en los últimos N días.
    Retorna: {codigo_producto: {promedio_diario, desviacion, max_venta_dia, min_venta_dia, dias_con_ventas}}
    """
    fecha_inicio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    
    # 1. Obtener suma de unidades vendidas por día por producto
    # Se agrupa por fecha(YYYY-MM-DD) y código.
    query = """
    SELECT 
        l.codigo,
        DATE(d.fecha) as dia,
        SUM(l.qty) as total_dia
    FROM document_lines l
    JOIN documents d ON l.doc_id = d.id
    WHERE d.tipo = 'SALE' AND d.fecha >= ?
    GROUP BY l.codigo, DATE(d.fecha)
    """
    
    ventas_historicas: Dict[str, List[float]] = {}
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (fecha_inicio,))
            for codigo, dia, total_dia in cur.fetchall():
                if codigo not in ventas_historicas:
                    ventas_historicas[codigo] = []
                ventas_historicas[codigo].append(float(total_dia or 0))
    except Exception as e:
        _LOG.warning("calcular_estadisticas_ventas error: %s", e)
        return {}

    # 2. Calcular estadísticos en Python puro
    estadisticas = {}
    for codigo, ventas_diarias in ventas_historicas.items():
        n = len(ventas_diarias)
        if n == 0:
            continue
            
        promedio = sum(ventas_diarias) / n
        max_v = max(ventas_diarias)
        min_v = min(ventas_diarias)
        
        # Desviación estándar muestral (n-1) o poblacional (n)
        if n > 1:
            varianza = sum((x - promedio) ** 2 for x in ventas_diarias) / (n - 1)
            std_dev = math.sqrt(varianza)
        else:
            std_dev = 0.0
            
        estadisticas[codigo] = {
            "promedio_diario": promedio,
            "desviacion": std_dev,
            "max_venta_dia": max_v,
            "min_venta_dia": min_v,
            "dias_con_ventas": n
        }
        
    return estadisticas

def detectar_anomalias(umbral_sigma: float = 2.0) -> List[Dict[str, Any]]:
    """
    Detecta si las ventas de HOY son anómalas (muy altas o muy bajas)
    respecto a las estadísticas históricas de los últimos 90 días.
    Sólo procesa productos con >= 7 días de historial de ventas.
    """
    hoy = datetime.now().strftime("%Y-%m-%d")
    estadisticas = calcular_estadisticas_ventas(dias=90)
    
    # Ventas de hoy
    query_hoy = """
    SELECT 
        l.codigo,
        MAX(p.nombre) as nombre,
        SUM(l.qty) as total_hoy
    FROM document_lines l
    JOIN documents d ON l.doc_id = d.id
    LEFT JOIN productos p ON l.codigo = p.codigo
    WHERE d.tipo = 'SALE' AND DATE(d.fecha) = ?
    GROUP BY l.codigo
    """
    
    anomalias = []
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query_hoy, (hoy,))
            for codigo, nombre, total_hoy in cur.fetchall():
                total_hoy = float(total_hoy or 0)
                nombre = nombre or codigo
                
                stats = estadisticas.get(codigo)
                # Graceful degradation: ignorar si no hay historial suficiente
                if not stats or stats["dias_con_ventas"] < 7:
                    continue
                    
                promedio = stats["promedio_diario"]
                desviacion = stats["desviacion"]
                
                # Para evitar división por cero o anomalias muy sensibles por baja dispersión
                if desviacion < 0.1:
                    desviacion = 0.1
                    
                # Calcular límite alto y bajo
                limite_alto = promedio + (umbral_sigma * desviacion)
                limite_bajo = promedio - (umbral_sigma * desviacion)
                if limite_bajo < 0:
                    limite_bajo = 0
                    
                es_alta = total_hoy > limite_alto
                es_baja = total_hoy < limite_bajo and total_hoy > 0 # Solo si vendió algo, no reporta ceros como anomalía hoy
                
                if es_alta or es_baja:
                    severidad = (total_hoy - promedio) / desviacion
                    anomalias.append({
                        "codigo": str(codigo),
                        "nombre": str(nombre),
                        "venta_hoy": total_hoy,
                        "promedio_historico": round(promedio, 2),
                        "desviacion": round(desviacion, 2),
                        "tipo": "ALTA" if es_alta else "BAJA",
                        "severidad": round(severidad, 2)
                    })
                    
    except Exception as e:
        _LOG.warning("detectar_anomalias error: %s", e)
        return []
        
    # Ordenar por severidad absoluta descendente
    anomalias.sort(key=lambda x: abs(x["severidad"]), reverse=True)
    return anomalias

def get_resumen_anomalias() -> Dict[str, Any]:
    """
    Retorna un resumen de las anomalías detectadas hoy.
    """
    anomalias = detectar_anomalias()
    
    altas = sum(1 for a in anomalias if a["tipo"] == "ALTA")
    bajas = sum(1 for a in anomalias if a["tipo"] == "BAJA")
    
    return {
        "total_anomalias": len(anomalias),
        "altas": altas,
        "bajas": bajas,
        "productos": anomalias[:5] # Primeros 5 casos
    }
