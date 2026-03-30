# core/audit.py
from __future__ import annotations
import json
from typing import List, Tuple, Optional
from datetime import datetime
import csv

from .database import get_connection

# ---------------------------
# Escribir eventos
# ---------------------------
def log_event(user_id: Optional[int], action: str, details: dict | None = None) -> int:
    """
    Inserta un evento en audit_log.
    - user_id puede ser None (acciones del sistema).
    - action: string corto, ej.: "LOGIN", "PRODUCT_CREATE"
    - details: dict serializado a JSON (puede ser None)
    Retorna id del evento.
    """
    if not action or not action.strip():
        raise ValueError("action es obligatorio")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details_json = json.dumps(details or {}, ensure_ascii=False)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_log (user_id, action, details, created_at)
            VALUES (?,?,?,?) RETURNING id
        """, (user_id, action.strip(), details_json, created_at))
        conn.commit()
        return int(cur.fetchone()[0])

# ---------------------------
# Leer / listar con filtros
# ---------------------------
def list_audit(
    *,
    user_q: Optional[str] = None,   # filtra por username o name similar
    action_q: Optional[str] = None, # filtra por subcadena en action
    text_q: Optional[str] = None,   # busca en details JSON
    date_from: Optional[str] = None, # "YYYY-MM-DD" (inclusive)
    date_to: Optional[str] = None,   # "YYYY-MM-DD" (inclusive)
    limit: int = 50,
    offset: int = 0,
    order_desc: bool = True
) -> Tuple[List[Tuple], int]:
    """
    Retorna (rows, total) donde rows son tuplas:
    (created_at, usuario, action, details_text)
    """
    where = []
    params = []

    # join con users para mostrar nombre
    join = "LEFT JOIN users u ON u.id = a.user_id"

    if user_q:
        where.append("(LOWER(u.username) LIKE ? OR LOWER(u.name) LIKE ?)")
        like = f"%{user_q.strip().lower()}%"
        params += [like, like]

    if action_q:
        where.append("LOWER(a.action) LIKE ?")
        params.append(f"%{action_q.strip().lower()}%")

    if text_q:
        where.append("LOWER(a.details) LIKE ?")
        params.append(f"%{text_q.strip().lower()}%")

    if date_from:
        where.append("a.created_at >= ?")
        # permitir solo fecha -> expandir a 00:00:00
        df = (date_from.strip() + " 00:00:00") if len(date_from.strip()) == 10 else date_from.strip()
        params.append(df)

    if date_to:
        where.append("a.created_at <= ?")
        dt = (date_to.strip() + " 23:59:59") if len(date_to.strip()) == 10 else date_to.strip()
        params.append(dt)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    order_sql = "DESC" if order_desc else "ASC"

    with get_connection() as conn:
        cur = conn.cursor()

        # total
        cur.execute(f"SELECT COUNT(*) FROM audit_log a {join} {where_sql}", params)
        total = int(cur.fetchone()[0] or 0)

        # rows
        cur.execute(f"""
            SELECT a.created_at,
                   COALESCE(u.username, '(sistema)') AS usuario,
                   a.action,
                   a.details
            FROM audit_log a
            {join}
            {where_sql}
            ORDER BY a.created_at {order_sql}, a.id {order_sql}
            LIMIT ? OFFSET ?
        """, params + [int(limit), int(offset)])
        fetched = cur.fetchall()

    # adaptar a lo que espera tu GUI (strings legibles)
    out_rows = []
    for created_at, usuario, action, details in fetched:
        # pretty details (una línea corta)
        try:
            d = json.loads(details) if details else {}
            # compactar a "k1=v1; k2=v2"
            txt = "; ".join(f"{k}={v}" for k, v in d.items())
        except Exception:
            txt = (details or "")[:500]
        out_rows.append((str(created_at), str(usuario), str(action), txt))

    return out_rows, total

# ---------------------------
# Exportaciones
# ---------------------------
def export_audit_csv(
    path: str,
    *,
    user_q: Optional[str] = None,
    action_q: Optional[str] = None,
    text_q: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> int:
    """
    Exporta a CSV los resultados con los filtros (sin paginación).
    Retorna número de filas exportadas.
    """
    where = []
    params = []
    join = "LEFT JOIN users u ON u.id = a.user_id"

    if user_q:
        like = f"%{user_q.strip().lower()}%"
        where.append("(LOWER(u.username) LIKE ? OR LOWER(u.name) LIKE ?)")
        params += [like, like]
    if action_q:
        where.append("LOWER(a.action) LIKE ?")
        params.append(f"%{action_q.strip().lower()}%")
    if text_q:
        where.append("LOWER(a.details) LIKE ?")
        params.append(f"%{text_q.strip().lower()}%")
    if date_from:
        df = (date_from.strip() + " 00:00:00") if len(date_from.strip()) == 10 else date_from.strip()
        where.append("a.created_at >= ?"); params.append(df)
    if date_to:
        dt = (date_to.strip() + " 23:59:59") if len(date_to.strip()) == 10 else date_to.strip()
        where.append("a.created_at <= ?"); params.append(dt)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    with get_connection() as conn, open(path, "w", newline="", encoding="utf-8") as f:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT a.created_at,
                   COALESCE(u.username, '(sistema)') AS usuario,
                   a.action,
                   a.details
            FROM audit_log a
            {join}
            {where_sql}
            ORDER BY a.created_at DESC, a.id DESC
        """, params)
        rows = cur.fetchall()
        w = csv.writer(f)
        w.writerow(["fecha", "usuario", "accion", "detalles_json"])
        for r in rows:
            w.writerow(r)
        return len(rows)

def export_audit_pdf(
    path: str,
    *,
    user_q: Optional[str] = None,
    action_q: Optional[str] = None,
    text_q: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    title: str = "Bitácora de auditoría"
) -> int:
    """
    Exporta a PDF con filtros (sin paginación). Retorna filas impresas.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm

    where = []
    params = []
    join = "LEFT JOIN users u ON u.id = a.user_id"

    if user_q:
        like = f"%{user_q.strip().lower()}%"
        where.append("(LOWER(u.username) LIKE ? OR LOWER(u.name) LIKE ?)")
        params += [like, like]
    if action_q:
        where.append("LOWER(a.action) LIKE ?")
        params.append(f"%{action_q.strip().lower()}%")
    if text_q:
        where.append("LOWER(a.details) LIKE ?")
        params.append(f"%{text_q.strip().lower()}%")
    if date_from:
        df = (date_from.strip() + " 00:00:00") if len(date_from.strip()) == 10 else date_from.strip()
        where.append("a.created_at >= ?"); params.append(df)
    if date_to:
        dt = (date_to.strip() + " 23:59:59") if len(date_to.strip()) == 10 else date_to.strip()
        where.append("a.created_at <= ?"); params.append(dt)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT a.created_at,
                   COALESCE(u.username, '(sistema)') AS usuario,
                   a.action,
                   a.details
            FROM audit_log a
            {join}
            {where_sql}
            ORDER BY a.created_at DESC, a.id DESC
        """, params)
        rows = cur.fetchall()

    c = canvas.Canvas(path, pagesize=A4)
    W, H = A4
    y = H - 2*cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, title)
    c.setFont("Helvetica", 9)
    c.drawRightString(W - 2*cm, y, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    y -= 1.0*cm

    # cabeceras
    c.setFont("Helvetica-Bold", 9)
    headers = ["Fecha", "Usuario", "Acción", "Detalles"]
    x = [1.2, 5.0, 9.0, 12.0]  # en cm (aprox)
    for i, h in enumerate(headers):
        c.drawString(x[i]*cm, y, h)
    y -= 0.35*cm
    c.setFont("Helvetica", 9)

    count = 0
    for fecha, usuario, accion, detalles in rows:
        if y < 2*cm:
            c.showPage(); y = H - 2*cm
            c.setFont("Helvetica-Bold", 9)
            for i, h in enumerate(headers): c.drawString(x[i]*cm, y, h)
            y -= 0.35*cm; c.setFont("Helvetica", 9)

        # detalles (condensados)
        try:
            d = json.loads(detalles) if detalles else {}
            det_txt = "; ".join(f"{k}={v}" for k, v in d.items())
        except Exception:
            det_txt = (detalles or "")
        det_txt = det_txt[:140]  # cortar para que no rompa el renglón

        c.drawString(x[0]*cm, y, str(fecha)[:19])
        c.drawString(x[1]*cm, y, str(usuario)[:22])
        c.drawString(x[2]*cm, y, str(accion)[:22])
        c.drawString(x[3]*cm, y, det_txt)
        y -= 0.32*cm
        count += 1

    c.save()
    return count
