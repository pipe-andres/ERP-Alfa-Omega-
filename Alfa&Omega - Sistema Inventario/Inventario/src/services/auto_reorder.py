"""
Auto Reorder Service
Gestiona la creación automática de órdenes de compra según el stock mínimo.
"""
from typing import List, Dict, Optional
from src.database.connection import get_connection
from src.services.inventory import get_product
from src.services.purchase_orders import create_purchase_order

def get_productos_bajo_reorder() -> List[Dict]:
    """Obtiene productos activos cuyo stock haya alcanzado o perforado su nivel mínimo."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT codigo, nombre, cantidad, stock_minimo, reorder_qty, proveedor_id
            FROM productos
            WHERE activo = 1 
              AND stock_minimo > 0 
              AND cantidad <= stock_minimo
            ORDER BY (stock_minimo - cantidad) DESC
        """)
        rows = cur.fetchall()
        return [
            {
                "codigo": r[0],
                "nombre": r[1],
                "cantidad": r[2],
                "stock_minimo": r[3],
                "reorder_qty": r[4],
                "proveedor_id": r[5]
            }
            for r in rows
        ]

def crear_oc_automatica(codigo: str) -> Dict:
    """Crea una OC para el producto dado si tiene proveedor asignado."""
    prod = get_product(codigo)
    if not prod:
        raise ValueError(f"Producto {codigo} no existe.")

    # La tupla es: codigo, nombre, categoria, precio, cantidad, avg_cost, stock_minimo, reorder_qty, proveedor_id
    avg_cost = prod[5]
    reorder_qty = prod[7]
    proveedor_id = prod[8]

    if not proveedor_id:
        raise ValueError(f"Producto {codigo} sin proveedor asignado.")

    with get_connection() as conn:
        cur = conn.cursor()
        # Obtener el código del proveedor (supplier_code)
        cur.execute("SELECT code FROM partners WHERE id = ?", (proveedor_id,))
        supplier_row = cur.fetchone()
        if not supplier_row:
            raise ValueError(f"Proveedor ID {proveedor_id} del producto {codigo} no existe en la BD.")
        supplier_code = supplier_row[0]

    items = [{"codigo": codigo, "qty": reorder_qty, "unit_price": avg_cost}]
    doc_id, numero = create_purchase_order(
        supplier_code=supplier_code,
        items=items,
        notas="OC Automática — stock bajo mínimo"
    )

    return {
        "oc_id": doc_id,
        "numero": numero,
        "codigo": codigo,
        "qty": reorder_qty,
        "proveedor_id": proveedor_id
    }

def ejecutar_reorder_automatico() -> Dict:
    """Procesa todos los productos bajo reorder y genera las órdenes que correspondan."""
    creadas = []
    sin_proveedor = []

    bajo_stock = get_productos_bajo_reorder()
    for p in bajo_stock:
        if not p.get("proveedor_id"):
            sin_proveedor.append(p["codigo"])
        else:
            try:
                res = crear_oc_automatica(p["codigo"])
                creadas.append(res)
            except Exception as e:
                import logging
                logging.error(f"Falla al automatizar OC para {p['codigo']}: {e}")
                sin_proveedor.append(p["codigo"])

    return {
        "creadas": creadas,
        "sin_proveedor": sin_proveedor,
        "total_creadas": len(creadas)
    }
