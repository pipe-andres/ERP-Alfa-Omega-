"""
src/services/customer_segments.py
==================================
Tarea 33 - Segmentación automática de clientes A/B/C.
Clasifica a los partners con kind='CUSTOMER' basándose en su
actividad de compras (RFM simplificado) en los últimos 365 días.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Any

from src.database.connection import get_connection

_LOG = logging.getLogger(__name__)

def calcular_segmentos(dias_inactivo: int = 90) -> Dict[str, Any]:
    """
    Calcula los segmentos A, B y C consultando el historial de ventas.
    - A: frecuencia >= 5 Y total >= promedio_total
    - B: frecuencia >= 2 O dias_desde_ultima < dias_inactivo
    - C: dias_desde_ultima >= dias_inactivo O sin compras
    """
    limit_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    hoy = datetime.now()
    
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Filtramos partners activos que sean CUSTOMER
        # Cruzamos con documentos tipo SALE >= limit_date
        cur.execute("""
            SELECT 
                p.id, 
                p.name, 
                SUM(COALESCE(d.amount_paid, 0)) as total_comprado,
                COUNT(d.id) as frecuencia,
                MAX(d.fecha) as ultima_compra
            FROM partners p
            LEFT JOIN documents d ON d.partner_id = p.id 
                AND d.tipo = 'SALE' 
                AND d.fecha >= ?
            WHERE p.kind = 'CUSTOMER' AND p.active = 1
            GROUP BY p.id, p.name
        """, (limit_date,))
        rows = cur.fetchall()
        
    clientes = []
    total_compradores = 0
    suma_total = 0.0
    
    # Pre-procesado de las métricas de cliente
    for row in rows:
        pid, nombre, total, freq, ult_compra = row
        total = float(total or 0.0)
        freq = int(freq or 0)
        
        # Cálculo unificado de "días desde la última compra"
        dias_desde = 999
        if ult_compra:
            try:
                if isinstance(ult_compra, str):
                    dt_ult = datetime.strptime(ult_compra[:10], "%Y-%m-%d")
                    dias_desde = (hoy - dt_ult).days
                elif isinstance(ult_compra, datetime):
                    dias_desde = (hoy - ult_compra.replace(tzinfo=None)).days
                elif isinstance(ult_compra, date):
                    dt_ult = datetime.combine(ult_compra, datetime.min.time())
                    dias_desde = (hoy - dt_ult).days
            except Exception as e:
                _LOG.warning(f"Error procesando fecha {ult_compra}: {e}")
                dias_desde = 999
                
        # Estructura del cliente enriquecida
        c_dict = {
            "partner_id": pid,
            "nombre": nombre,
            "total": total,
            "frecuencia": freq,
            "ultima_compra": str(ult_compra) if ult_compra else None,
            "dias_desde_ultima": dias_desde
        }
        clientes.append(c_dict)
        
        if freq > 0:
            suma_total += total
            total_compradores += 1
            
    # Promedio basándose en aquellos que han comprado
    promedio_total = (suma_total / total_compradores) if total_compradores > 0 else 0.0
    
    # Clasificación en buckets
    res = {
        "A": [],
        "B": [],
        "C": []
    }
    
    for c in clientes:
        # A: Muy frecuentes y buen volumen
        if c["frecuencia"] >= 5 and c["total"] >= promedio_total:
            res["A"].append(c)
        # B: Recurrentes o recientes
        elif c["frecuencia"] >= 2 or c["dias_desde_ultima"] < dias_inactivo:
            res["B"].append(c)
        # C: Inactivos / Sin compras en el último año (dias_desde = 999)
        else:
            res["C"].append(c)
            
    # Bloque de resumen agregado
    res["resumen"] = {
        "total_A": len(res["A"]),
        "total_B": len(res["B"]),
        "total_C": len(res["C"])
    }
    
    return res

def get_clientes_segmento(segmento: str) -> List[Dict[str, Any]]:
    """Obtiene la lista concreta de clientes para el segmento requerido (A, B o C)."""
    segmentos = calcular_segmentos()
    return segmentos.get(segmento.upper(), [])

def get_resumen_segmentos() -> Dict[str, int]:
    """Retorna únicamente las métricas agregadas."""
    segmentos = calcular_segmentos()
    return segmentos.get("resumen", {})
