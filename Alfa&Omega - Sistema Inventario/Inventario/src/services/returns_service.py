from __future__ import annotations
from typing import List, Dict, Optional
from datetime import datetime

from src.database.connection import get_connection
from src.services.documents import get_next_number
from src.services.audit import log_event
from src.services.inventory import get_product


# NOTE: we intentionally do not import inventory.post_return here because
# this module is the new canonical implementation.  Older callers in
# inventory.py remain untouched for backward compatibility.


def post_return(sale_id: int, items: List[Dict], reason: str, user_id: Optional[int] = None) -> tuple[int, int]:
    """Registra una devolución vinculada a una venta existente.

    Args:
        sale_id: id del documento de venta (tipo 'SALE').
        items: lista de dicts con keys ``codigo`` y ``qty`` (cantidad a devolver).
        reason: motivo de la devolución.
        user_id: id del usuario que realiza la operación (opcional).

    Returns:
        (return_id, credit_doc_id)

    Se crean dos filas en la base de datos:
      * tabla ``returns`` con la información de alto nivel de la devolución.
      * tabla ``return_lines`` con cada línea devuelta.

    Además se genera un documento de tipo "NOTA_CREDITO" en ``documents``
    y se actualiza el stock, los movimientos y el kardex como en una compra
    inversa. Si la venta original fue en efectivo se registra un movimiento
    de caja tipo ``expense`` para reflejar el reembolso.
    """
    if not sale_id:
        raise ValueError("sale_id es obligatorio.")
    if not items:
        raise ValueError("La devolución debe tener al menos una línea.")
    reason = (reason or "").strip() or "Devolución"

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_refund = 0.0

    with get_connection() as conn:
        cur = conn.cursor()
        # validar existencia de la venta
        cur.execute("SELECT tipo, payment_method FROM documents WHERE id=?", (sale_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Venta {sale_id} no encontrada.")
        if (row[0] or "").upper() != "SALE":
            raise ValueError("El documento indicado no es una venta.")
        payment_method = row[1]

        # obtener líneas de la venta y cantidades ya devueltas
        cur.execute("SELECT codigo, qty, unit_price FROM document_lines WHERE doc_id=?", (sale_id,))
        sale_lines = {r[0]: {"qty": float(r[1] or 0), "unit_price": float(r[2] or 0)} for r in cur.fetchall()}

        cur.execute(
            "SELECT rl.product_code, SUM(rl.quantity) FROM return_lines rl "
            "JOIN returns r ON rl.return_id = r.id "
            "WHERE r.sale_id = ? GROUP BY rl.product_code", (sale_id,)
        )
        returned_sums = {r[0]: float(r[1] or 0) for r in cur.fetchall()}

        # validaciones por ítem y cálculo de monto total
        for it in items:
            code = (it.get("codigo") or "").strip()
            qty = float(it.get("qty") or 0)
            if not code or qty <= 0:
                raise ValueError("Item inválido en la devolución.")
            orig = sale_lines.get(code)
            if not orig:
                raise ValueError(f"Producto '{code}' no pertenece a la venta {sale_id}.")
            max_allowed = orig["qty"] - returned_sums.get(code, 0.0)
            if qty > max_allowed + 1e-6:
                raise ValueError(
                    f"Cantidad a devolver para '{code}' excede la vendida. \n"
                    f"(vendido: {orig['qty']}, ya devuelto: {returned_sums.get(code,0):.2f})"
                )
            # calculamos el reembolso con el precio de venta original
            total_refund += qty * orig["unit_price"]

        # crear documento de nota de crédito
        credit_num = get_next_number("NOTA_CREDITO", "NC01")
        cur.execute(
            "INSERT INTO documents (tipo, fecha, numero, notas, partner_id) "
            "VALUES (?,?,?,?,NULL) RETURNING id",
            ("NOTA_CREDITO", fecha, credit_num, reason)
        )
        credit_doc_id = int(cur.fetchone()[0])

        # insertar cabecera de devolución
        cur.execute(
            "INSERT INTO returns (sale_id, document_id, reason, total_refund, created_by, created_at, status) "
            "VALUES (?,?,?,?,?,?,?) RETURNING id",
            (sale_id, credit_doc_id, reason, float(total_refund), user_id, fecha, "completed")
        )
        return_id = int(cur.fetchone()[0])

        # procesar cada línea: stock + movimientos/kardex + tabla return_lines
        for it in items:
            code = it["codigo"].strip()
            qty = float(it["qty"])
            cur.execute("SELECT cantidad, avg_cost FROM productos WHERE codigo=?", (code,))
            prod = cur.fetchone()
            if not prod:
                raise ValueError(f"Producto '{code}' no existe.")
            old_qty, avg_cost = float(prod[0] or 0), float(prod[1] or 0)
            new_qty = old_qty + qty
            cur.execute("UPDATE productos SET cantidad=? WHERE codigo=?", (int(new_qty), code))

            cur.execute(
                "INSERT INTO return_lines (return_id, product_code, quantity, unit_cost, subtotal) "
                "VALUES (?,?,?,?,?)",
                (return_id, code, qty, avg_cost, qty * avg_cost)
            )

            cur.execute(
                """INSERT INTO stock_movements (doc_id, codigo, qty, unit_cost, unit_price, tipo, reason, created_at) """
                "VALUES (?,?,?,?,?,?,?,?)",
                (credit_doc_id, code, qty, avg_cost, None, "RETURN", reason, fecha)
            )

            cur.execute(
                """INSERT INTO kardex_moves (product_code, type, qty, unit_cost, avg_cost, total_cost, """
                "balance_qty, balance_cost, balance_total, date, warehouse_id, ref_type, ref_id) """
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (code, 'IN', float(qty), avg_cost, avg_cost, avg_cost * qty,
                 float(new_qty), new_qty * avg_cost, new_qty * avg_cost,
                 fecha, None, 'RETURN', credit_doc_id)
            )
        conn.commit()

    # invalidar caché global
    from src.core import caching
    caching.clear_cache("src.database.repository.list_products")
    caching.clear_cache("src.database.repository.count_products")
    caching.clear_cache("src.database.repository.get_product_by_code")

    # registrar movimiento de caja si la venta fue en efectivo
    if user_id and payment_method == "efectivo":
        try:
            from src.services.pos_service import get_current_session, register_cash_movement
            session = get_current_session(user_id)
            if session:
                register_cash_movement(session["id"], "expense", float(total_refund), note=f"Reembolso venta {sale_id}")
        except Exception as exc:
            from src.core.error_handler import log_error
            log_error(exc, {"operation": "pos_refund_registration"}, level="ERROR")

    log_event(user_id, "DOC_RETURN", {"return_id": return_id, "sale_id": sale_id, "credit_doc": credit_doc_id})
    return return_id, credit_doc_id


def get_return_by_sale(sale_id: int) -> Optional[Dict]:
    """Devuelve la devolución asociada a una venta (o ``None`` si no existe)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, document_id, reason, total_refund, created_by, created_at, status "
            "FROM returns WHERE sale_id=?", (sale_id,)
        )
        r = cur.fetchone()
        if not r:
            return None
        result = {
            "id": r[0],
            "sale_id": sale_id,
            "document_id": r[1],
            "reason": r[2],
            "total_refund": r[3],
            "created_by": r[4],
            "created_at": r[5],
            "status": r[6],
            "lines": [],
        }
        cur.execute(
            "SELECT product_code, quantity, unit_cost, subtotal FROM return_lines WHERE return_id=?", (r[0],)
        )
        for ln in cur.fetchall():
            result["lines"].append({
                "product_code": ln[0],
                "quantity": ln[1],
                "unit_cost": ln[2],
                "subtotal": ln[3],
            })
        return result


def list_returns(filters: Optional[Dict] = None) -> List[Dict]:
    """Lista devoluciones con filtros opcionales.

    Filtros soportados: ``start_date`` (>=), ``end_date`` (<=), ``user_id``, ``product_code``.
    """
    filters = filters or {}
    sql = ("SELECT r.id, r.sale_id, r.document_id, r.reason, r.total_refund, "
           "r.created_by, r.created_at, r.status FROM returns r")
    params: List = []
    where: List[str] = []
    if filters.get("product_code"):
        sql += " JOIN return_lines rl ON rl.return_id = r.id"
        where.append("rl.product_code = ?")
        params.append(filters["product_code"])
    if filters.get("start_date"):
        where.append("r.created_at >= ?")
        params.append(filters["start_date"])
    if filters.get("end_date"):
        where.append("r.created_at <= ?")
        params.append(filters["end_date"])
    if filters.get("user_id"):
        where.append("r.created_by = ?")
        params.append(filters["user_id"])
    if where:
        sql += " WHERE " + " AND ".join(where)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        items = []
        for r in cur.fetchall():
            items.append({
                "id": r[0],
                "sale_id": r[1],
                "document_id": r[2],
                "reason": r[3],
                "total_refund": r[4],
                "created_by": r[5],
                "created_at": r[6],
                "status": r[7],
            })
        return items
