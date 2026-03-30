"""
src/services/market_basket.py
==================================
Tarea 35 - Market Basket Analysis.
Descubre asociaciones entre productos frecuentemente comprados juntos
utilizando procesamiento SQL sin dependencias algorítmicas pesadas.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Any

from src.database.connection import get_connection

_LOG = logging.getLogger(__name__)

def calcular_asociaciones(min_support: int = 2) -> List[Dict[str, Any]]:
    """
    Calcula la co-ocurrencia de productos en documentos de venta.
    Retorna pares dirigidos A -> B donde el soporte superó la valla estipulada.
    Se limita a bases de datos con un historial maduro (>= 10 facturas).
    """
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Validar madurez histórica (Graceful degradation)
        cur.execute("SELECT COUNT(id) FROM documents WHERE tipo='SALE'")
        row = cur.fetchone()
        if not row or row[0] < 10:
            return []
            
        # 1. Calcular soporte individual de cada producto
        cur.execute("""
            SELECT L.codigo, COUNT(DISTINCT L.doc_id) 
            FROM document_lines L
            JOIN documents D ON L.doc_id = D.id
            WHERE D.tipo = 'SALE'
            GROUP BY L.codigo
        """)
        individual_support = {r[0]: r[1] for r in cur.fetchall()}
        
        # 2. Calcular soporte conjunto (co-ocurrencia par a par)
        #    Se usa != para capturar el cruce en ambas direcciones sin sesgo
        cur.execute("""
            SELECT 
                L1.codigo as producto_a,
                L2.codigo as producto_b,
                COUNT(DISTINCT L1.doc_id) as support
            FROM document_lines L1
            JOIN document_lines L2 
              ON L1.doc_id = L2.doc_id AND L1.codigo != L2.codigo
            JOIN documents D 
              ON L1.doc_id = D.id
            WHERE D.tipo = 'SALE'
            GROUP BY L1.codigo, L2.codigo
            HAVING COUNT(DISTINCT L1.doc_id) >= ?
            ORDER BY support DESC
        """, (min_support,))
        
        pairs = cur.fetchall()
        
        resultados = []
        for prop_a, prop_b, support in pairs:
            supp_a = individual_support.get(prop_a, 1)
            confianza = support / supp_a if supp_a > 0 else 0.0
            
            resultados.append({
                "producto_a": prop_a,
                "producto_b": prop_b,
                "support": support,
                "confianza": round(confianza, 4)
            })
            
        return resultados

def get_recomendaciones(codigo: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Retorna los productos que son frecuentemente comprados junto con `codigo`.
    Ideal para módulos de cross-selling o sugerencias rápidas en el POS.
    """
    # Cosechar asociaciones base
    asociaciones = calcular_asociaciones(min_support=2)
    
    # Filtrar solo la canasta donde el producto requerido es el ancla
    rels = [a for a in asociaciones if a["producto_a"] == codigo]
    
    # Ordenar priorizando la Confianza del cliente (cometido principal) -> Soporte
    rels.sort(key=lambda x: (x["confianza"], x["support"]), reverse=True)
    rels = rels[:max_results]
    
    if not rels:
        return []
        
    # Enriquecer la presentación trayendo el nombre original de los productos
    codigos_b = [r["producto_b"] for r in rels]
    placeholders = ",".join(["?"] * len(codigos_b))
    nombres_dict = {}
    
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT codigo, nombre FROM productos WHERE codigo IN ({placeholders})", tuple(codigos_b))
        for c, n in cur.fetchall():
            nombres_dict[c] = n
                
    # Compilar dataset final
    recomendaciones = []
    for r in rels:
        recomendaciones.append({
            "codigo": r["producto_b"],
            "nombre": nombres_dict.get(r["producto_b"], "Desconocido"),
            "support": r["support"],
            "confianza": r["confianza"]
        })
        
    return recomendaciones
