"""
Purchase Orders Service
Gestión de órdenes de compra a proveedores.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import time

from src.database.connection import get_connection
from src.services.partners import get_partner_by_code
from src.services.inventory import post_purchase


def create_purchase_order(
    supplier_code: str,
    items: List[Dict],
    notas: str = "",
    user_id: Optional[int] = None
) -> Tuple[int, str]:
    """
    Crea una orden de compra.
    Args:
        supplier_code: Código del proveedor
        items: Lista de dicts [{"codigo": str, "qty": float, "unit_price": float}]
        notas: Notas de la orden
        user_id: ID del usuario que crea la orden
    Returns:
        (doc_id, numero) de la orden creada
    """
    if not items:
        raise ValueError("La orden debe tener al menos un ítem.")

    # Validar proveedor
    supplier = get_partner_by_code(supplier_code)
    if not supplier:
        raise ValueError(f"Proveedor '{supplier_code}' no existe.")
    if supplier[2] != "SUPPLIER":
        raise ValueError(f"'{supplier_code}' no es un proveedor.")

    # Generar número automático
    fecha = datetime.now()
    seq = int(time.time())  # timestamp como secuencia simple
    numero = f"OC-{fecha.strftime('%Y%m%d')}-{seq}"

    with get_connection() as conn:
        cur = conn.cursor()

        # Insertar documento
        cur.execute("""
            INSERT INTO documents (tipo, numero, fecha, notas, partner_id, estado)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "PURCHASE_ORDER",
            numero,
            fecha.strftime("%Y-%m-%d %H:%M:%S"),
            notas,
            supplier[0],  # partner_id
            "PENDIENTE"
        ))
        doc_id = cur.lastrowid

        # Insertar líneas
        for item in items:
            codigo = item["codigo"].strip()
            qty = float(item["qty"])
            unit_price = float(item.get("unit_price", 0))

            if qty <= 0:
                raise ValueError(f"Cantidad debe ser > 0 para {codigo}")

            cur.execute("""
                INSERT INTO document_lines (doc_id, codigo, qty, unit_price)
                VALUES (?, ?, ?, ?)
            """, (doc_id, codigo, qty, unit_price))

        conn.commit()
        return doc_id, numero


def get_purchase_order(doc_id: int) -> Optional[Dict]:
    """
    Obtiene una orden de compra completa con sus líneas.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # Obtener documento
        cur.execute("""
            SELECT d.id, d.numero, d.fecha, d.notas, d.partner_id, d.estado,
                   p.code as supplier_code, p.name as supplier_name
            FROM documents d
            JOIN partners p ON d.partner_id = p.id
            WHERE d.id = ? AND d.tipo = 'PURCHASE_ORDER'
        """, (doc_id,))
        doc_row = cur.fetchone()
        if not doc_row:
            return None

        # Obtener líneas
        cur.execute("""
            SELECT dl.codigo, dl.qty, dl.unit_price,
                   pr.nombre as product_name
            FROM document_lines dl
            JOIN productos pr ON dl.codigo = pr.codigo
            WHERE dl.doc_id = ?
        """, (doc_id,))
        lines = cur.fetchall()

        return {
            "id": doc_row[0],
            "numero": doc_row[1],
            "fecha": doc_row[2],
            "notas": doc_row[3],
            "partner_id": doc_row[4],
            "estado": doc_row[5],
            "supplier_code": doc_row[6],
            "supplier_name": doc_row[7],
            "items": [
                {
                    "codigo": row[0],
                    "qty": row[1],
                    "unit_price": row[2],
                    "product_name": row[3]
                }
                for row in lines
            ]
        }


def list_purchase_orders(
    supplier_code: Optional[str] = None,
    estado: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Lista órdenes de compra con filtros opcionales.
    """
    where = ["d.tipo = 'PURCHASE_ORDER'"]
    params = []

    if supplier_code:
        where.append("p.code = ?")
        params.append(supplier_code)

    if estado:
        where.append("d.estado = ?")
        params.append(estado)

    where_sql = " AND ".join(where)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT d.id, d.numero, d.fecha, d.estado,
                   p.code as supplier_code, p.name as supplier_name,
                   SUM(dl.qty * dl.unit_price) as total
            FROM documents d
            JOIN partners p ON d.partner_id = p.id
            LEFT JOIN document_lines dl ON d.id = dl.doc_id
            WHERE {where_sql}
            GROUP BY d.id, d.numero, d.fecha, d.estado, p.code, p.name
            ORDER BY d.fecha DESC
            LIMIT ?
        """, params + [limit])
        rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "numero": row[1],
                "fecha": row[2],
                "estado": row[3],
                "supplier_code": row[4],
                "supplier_name": row[5],
                "total": row[6] or 0
            }
            for row in rows
        ]


def receive_order(
    doc_id: int,
    items_received: List[Dict],
    user_id: Optional[int] = None
) -> None:
    """
    Recibe una orden de compra parcialmente o completamente.
    Args:
        doc_id: ID de la orden
        items_received: [{"codigo": str, "qty_received": float}]
        user_id: ID del usuario que recibe
    """
    # Obtener orden
    order = get_purchase_order(doc_id)
    if not order:
        raise ValueError(f"Orden {doc_id} no encontrada.")
    if order["estado"] in ["RECIBIDA", "CANCELADA"]:
        raise ValueError(f"Orden {order['numero']} ya está {order['estado'].lower()}.")

    # Validar ítems recibidos
    received_by_code = {item["codigo"]: float(item["qty_received"]) for item in items_received}
    order_items = {item["codigo"]: item for item in order["items"]}

    # Preparar ítems para post_purchase (solo los que se reciben)
    purchase_items = []
    all_received = True

    for codigo, order_item in order_items.items():
        qty_received = received_by_code.get(codigo, 0)
        if qty_received > order_item["qty"]:
            raise ValueError(f"Cantidad recibida de {codigo} excede la ordenada.")

        if qty_received > 0:
            purchase_items.append({
                "codigo": codigo,
                "qty": qty_received,
                "unit_cost": order_item["unit_price"]
            })

        if qty_received < order_item["qty"]:
            all_received = False

    if not purchase_items:
        raise ValueError("No se recibió ningún ítem.")

    # Registrar la compra usando post_purchase
    doc_id_compra, numero_compra = post_purchase(
        numero=None,  # Generar automático
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        items=purchase_items,
        notas=f"Recepción de OC {order['numero']}",
        partner_code=order["supplier_code"],
        user_id=user_id
    )

    # Actualizar estado de la orden
    nuevo_estado = "RECIBIDA" if all_received else "PARCIAL"

    with get_connection() as conn:
        conn.execute(
            "UPDATE documents SET estado = ? WHERE id = ?",
            (nuevo_estado, doc_id)
        )
        conn.commit()


def cancel_order(doc_id: int, user_id: Optional[int] = None) -> None:
    """
    Cancela una orden de compra.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE documents SET estado = 'CANCELADA' WHERE id = ? AND tipo = 'PURCHASE_ORDER'",
            (doc_id,)
        )
        if cur.rowcount == 0:
            raise ValueError(f"Orden {doc_id} no encontrada o no es una orden de compra.")
        conn.commit()