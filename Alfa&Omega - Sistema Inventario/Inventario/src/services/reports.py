# core/reports.py
from __future__ import annotations
from typing import List, Dict, Optional, Tuple
import os
from src.database.connection import get_connection
from src.services.inventory import get_product
from decimal import Decimal, ROUND_HALF_UP

D = Decimal

def _fmt2(x: float | int | Decimal | None) -> float:
    if x is None: return 0.0
    return float(D(str(x)).quantize(D("0.01"), rounding=ROUND_HALF_UP))


def _periodo_fechas(periodo: str):
    """Retorna (fecha_desde: str, filtro_sql: str) para el periodo.

    - "hoy"    → DATE(d.fecha) = hoy
    - "semana" → d.fecha >= lunes de esta semana
    - "mes"    → d.fecha >= primer día del mes actual
    """
    from datetime import datetime as _dt, timedelta as _td
    hoy = _dt.now().date()
    if periodo == "hoy":
        return hoy.isoformat(), f"DATE(d.fecha) = '{hoy}'"
    elif periodo == "semana":
        lunes = hoy - _td(days=hoy.weekday())
        return lunes.isoformat(), f"d.fecha >= '{lunes}'"
    else:  # "mes"
        primer_dia = hoy.replace(day=1)
        return primer_dia.isoformat(), f"d.fecha >= '{primer_dia}'"


def kardex_rows(codigo: str, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Tuple[List[Dict], Dict]:
    """
    Devuelve (rows, summary) para un producto.
    rows: dicts ordenados por fecha con columnas:
      fecha, doc_no, tipo, qty_in, qty_out, unit_cost, unit_price, motivo, saldo_qty, saldo_cost, saldo_total
    summary: {saldo_qty, saldo_cost, saldo_total, first_date, last_date, nombre}
    """
    prod = get_product(codigo)
    if not prod:
        raise ValueError(f"Producto '{codigo}' no existe.")
    nombre = prod[1]

    where = ["l.codigo = ?"]
    params = [codigo]
    if date_from: where.append("d.fecha >= ?"); params.append(date_from)
    if date_to:   where.append("d.fecha <= ?"); params.append(date_to)
    where_sql = "WHERE " + " AND ".join(where)

    sql = f"""
    SELECT d.fecha, d.numero, d.tipo, l.qty, l.unit_cost, l.unit_price, l.reason
    FROM document_lines l
    JOIN documents d ON d.id = l.doc_id
    {where_sql}
    ORDER BY d.fecha ASC, d.id ASC, l.id ASC
    """
    rows = []
    with get_connection() as conn:
        cur = conn.cursor()
        for r in cur.execute(sql, params).fetchall():
            fecha, numero, tipo, qty, unit_cost, unit_price, reason = r
            qty = float(qty or 0.0)
            unit_cost = _fmt2(unit_cost) if unit_cost is not None else None
            unit_price = _fmt2(unit_price) if unit_price is not None else None
            rows.append(dict(
                fecha=str(fecha), doc_no=numero or "", tipo=tipo,
                qty=qty, unit_cost=unit_cost, unit_price=unit_price, motivo=reason or ""
            ))

    # Recorrido para saldos y costo promedio móvil
    saldo_qty = 0.0
    saldo_cost = 0.0  # costo promedio vigente
    out_rows: List[Dict] = []
    for r in rows:
        qty = r["qty"]
        if r["tipo"] in ("PURCHASE", "ADJUST+"):
            # entradas usan unit_cost; si viene None, usa saldo_cost actual
            cost = r["unit_cost"] if r["unit_cost"] is not None else (saldo_cost or 0.0)
            # nuevo promedio ponderado
            total_val = saldo_qty * saldo_cost + qty * cost
            saldo_qty = saldo_qty + qty
            saldo_cost = (total_val / saldo_qty) if saldo_qty > 0 else 0.0
            qty_in, qty_out = qty, 0.0
        elif r["tipo"] in ("SALE", "ADJUST-"):
            # salidas valorizadas al costo promedio vigente
            # qty puede venir negativa desde stock_movements (-qty), usar valor absoluto
            qty = abs(qty)
            if qty <= 0:
                continue  # ignorar líneas con cantidad cero
            if saldo_qty - qty < -1e-6:
                raise ValueError(f"Stock insuficiente para '{codigo}' en {r['fecha']} (sale {qty}, saldo {saldo_qty}).")
            qty_in, qty_out = 0.0, qty
            saldo_qty = saldo_qty - qty
            # saldo_cost se mantiene
        else:
            # por si a futuro
            qty_in, qty_out = (qty if qty >=0 else 0.0), (abs(qty) if qty < 0 else 0.0)

        out = dict(
            fecha=r["fecha"], doc_no=r["doc_no"], tipo=r["tipo"],
            qty_in=_fmt2(qty_in), qty_out=_fmt2(qty_out),
            unit_cost=_fmt2(r["unit_cost"]) if r["unit_cost"] is not None else _fmt2(saldo_cost),
            unit_price=_fmt2(r["unit_price"]) if r["unit_price"] is not None else None,
            motivo=r["motivo"],
            saldo_qty=_fmt2(saldo_qty), saldo_cost=_fmt2(saldo_cost),
            saldo_total=_fmt2(saldo_qty * saldo_cost)
        )
        out_rows.append(out)

    summary = dict(
        saldo_qty=_fmt2(saldo_qty),
        saldo_cost=_fmt2(saldo_cost),
        saldo_total=_fmt2(saldo_qty * saldo_cost),
        first_date=out_rows[0]["fecha"] if out_rows else None,
        last_date=out_rows[-1]["fecha"] if out_rows else None,
        nombre=nombre
    )
    return out_rows, summary

# ---------- Exportaciones ----------
def export_kardex_xlsx(path: str, codigo: str, date_from: Optional[str]=None, date_to: Optional[str]=None) -> int:
    import openpyxl
    from openpyxl.utils import get_column_letter

    rows, summary = kardex_rows(codigo, date_from, date_to)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Kardex"

    ws.append(["Kardex de producto", codigo, summary["nombre"] or "", "", "", "", ""])
    ws.append(["Rango", date_from or "-", date_to or "-", "", "", "", ""])
    ws.append([])

    headers = ["Fecha", "Doc Nº", "Tipo", "Ent.", "Sal.", "Costo u.", "Precio u.", "Motivo", "Saldo", "Costo prom.", "Valorización"]
    ws.append(headers)

    for r in rows:
        ws.append([
            r["fecha"], r["doc_no"], r["tipo"], r["qty_in"], r["qty_out"],
            r["unit_cost"], r["unit_price"] if r["unit_price"] is not None else "",
            r["motivo"], r["saldo_qty"], r["saldo_cost"], r["saldo_total"]
        ])

    ws.append([])
    ws.append(["Totales actuales", "", "", "", "", "", "", "",
               summary["saldo_qty"], summary["saldo_cost"], summary["saldo_total"]])

    # Ajuste de anchos
    for col in range(1, len(headers)+1):
        ws.column_dimensions[get_column_letter(col)].width = 14

    wb.save(path)
    return len(rows)

def export_kardex_pdf(path: str, codigo: str, date_from: Optional[str]=None, date_to: Optional[str]=None,
                      title: str="Kardex de producto", logo_path: Optional[str]=None) -> int:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.lib.utils import ImageReader
    except ImportError:
        raise RuntimeError("reportlab es requerido para exportar PDFs. Instálalo con: pip install reportlab")

    rows, summary = kardex_rows(codigo, date_from, date_to)
    c = canvas.Canvas(path, pagesize=A4)
    W, H = A4
    y = H - 2*cm

    if logo_path and os.path.exists(logo_path):
        try:
            img = ImageReader(logo_path)
            c.drawImage(img, 2*cm, y-2*cm, width=2.5*cm, height=2.5*cm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 14)
    c.drawString(5*cm, y, title)
    c.setFont("Helvetica", 9)
    c.drawString(5*cm, y-0.6*cm, f"Código: {codigo} — {summary['nombre']}")
    c.drawString(5*cm, y-1.1*cm, f"Rango: {date_from or '-'} a {date_to or '-'}")
    y -= 2*cm

    # Cabeceras
    c.setFont("Helvetica-Bold", 8)
    headers = ["Fecha","Doc","Tipo","Ent.","Sal.","Cst u.","Prc u.","Motivo","Saldo","Cst prom.","Val."]
    x_positions = [1.0, 3.8, 5.2, 6.6, 7.6, 8.6, 9.7, 10.8, 14.0, 15.5, 17.0]  # en cm
    for i, h in enumerate(headers):
        c.drawString(x_positions[i]*cm, y, h)
    y -= 0.35*cm
    c.setFont("Helvetica", 8)

    def new_page():
        nonlocal y
        c.showPage()
        y = H - 2*cm
        c.setFont("Helvetica-Bold", 8)
        for i, h in enumerate(headers):
            c.drawString(x_positions[i]*cm, y, h)
        y -= 0.35*cm
        c.setFont("Helvetica", 8)

    for r in rows:
        if y < 2*cm: new_page()
        vals = [
            r["fecha"][:19], r["doc_no"], r["tipo"], f"{r['qty_in']:.2f}", f"{r['qty_out']:.2f}",
            f"{r['unit_cost']:.2f}", f"{(r['unit_price'] or 0):.2f}" if r["unit_price"] is not None else "",
            (r["motivo"] or "")[:20], f"{r['saldo_qty']:.2f}", f"{r['saldo_cost']:.2f}", f"{r['saldo_total']:.2f}"
        ]
        for i, v in enumerate(vals):
            c.drawString(x_positions[i]*cm, y, str(v))
        y -= 0.35*cm

    # resumen
    if y < 3*cm: new_page()
    y -= 0.2*cm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(1.0*cm, y, f"Saldo: {summary['saldo_qty']:.2f} u | Costo prom.: {summary['saldo_cost']:.2f} | Valorización: {summary['saldo_total']:.2f}")
    c.save()
    return len(rows)
# ========== REPORTES AVANZADOS (NUEVOS) ==========

def report_sales_by_period(start_date: str, end_date: str, period: str = "daily") -> List[Dict]:
    """
    Retorna ventas agrupadas por período (diario, semanal, mensual).
    """
    with get_connection() as conn:
        cur = conn.cursor()
        
        if period == "daily":
            group_expr = "DATE(d.fecha)"
        elif period == "weekly":
            group_expr = "strftime('%Y-W%W', d.fecha)"
        else:  # monthly
            group_expr = "strftime('%Y-%m', d.fecha)"
        
        cur.execute(f"""
            SELECT {group_expr} as period,
                   COUNT(DISTINCT d.id) as num_sales,
                   SUM(l.qty) as total_qty,
                   SUM(l.qty * l.unit_price) as total_sales,
                   SUM(l.qty * p.avg_cost) as total_cost,
                   SUM(l.qty * (l.unit_price - p.avg_cost)) as total_margin
            FROM documents d
            LEFT JOIN document_lines l ON d.id = l.doc_id
            LEFT JOIN productos p ON p.codigo = l.codigo
            WHERE d.tipo = 'SALE' AND d.fecha BETWEEN ? AND ?
            GROUP BY period
            ORDER BY period ASC
        """, (start_date, end_date))
        
        results = []
        for row in cur.fetchall():
            results.append({
                "period": row[0],
                "num_sales": row[1] or 0,
                "total_qty": float(row[2] or 0),
                "total_sales": _fmt2(row[3] or 0),
                "total_cost": _fmt2(row[4] or 0),
                "total_margin": _fmt2(row[5] or 0),
                "margin_pct": float((row[5] / row[3] * 100) if row[3] and row[3] > 0 else 0)
            })
        
        return results

def report_abc_analysis(months: int = 12) -> Dict:
    """
    Análisis ABC (Pareto): clasifica productos por valor de ventas.
    A: Top 20%, B: Next 30%, C: Rest 50%
    """
    from datetime import timedelta, datetime as dt
    
    start_date = (dt.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Obtener ventas por producto
        cur.execute("""
            SELECT l.codigo, p.nombre,
                   SUM(l.qty) as total_qty,
                   SUM(l.qty * l.unit_price) as total_sales
            FROM document_lines l
            JOIN documents d ON d.id = l.doc_id
            JOIN productos p ON p.codigo = l.codigo
            WHERE d.tipo = 'SALE' AND d.fecha >= ?
            GROUP BY l.codigo
            ORDER BY total_sales DESC
        """, (start_date,))
        
        products = cur.fetchall()
        total_sales = sum(float(p[3] or 0) for p in products)
        
        a_products = []
        b_products = []
        c_products = []
        cumulative = 0.0
        
        for codigo, nombre, qty, sales in products:
            sales_val = float(sales or 0)
            cumulative += sales_val
            pct = (cumulative / total_sales * 100) if total_sales > 0 else 0
            
            product_info = {
                "codigo": codigo,
                "nombre": nombre,
                "qty": float(qty or 0),
                "ventas": _fmt2(sales_val),
                "pct_acumulado": round(pct, 2)
            }
            
            if pct <= 80:
                a_products.append(product_info)
            elif pct <= 95:
                b_products.append(product_info)
            else:
                c_products.append(product_info)
        
        return {
            "A": a_products,  # 80% de ventas
            "B": b_products,  # Next 15%
            "C": c_products,  # Remaining 5%
            "total_sales": _fmt2(total_sales),
            "total_products": len(products)
        }

def report_top_products(limit: int = 10, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict]:
    """
    Retorna top N productos por cantidad o ingresos.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        
        where = ["d.tipo = 'SALE'"]
        params = []
        if date_from:
            where.append("d.fecha >= ?")
            params.append(date_from)
        if date_to:
            where.append("d.fecha <= ?")
            params.append(date_to)
        
        where_sql = "WHERE " + " AND ".join(where)
        
        cur.execute(f"""
            SELECT l.codigo, p.nombre,
                   SUM(l.qty) as total_qty,
                   SUM(l.qty * l.unit_price) as total_sales,
                   COUNT(DISTINCT d.id) as num_transactions
            FROM document_lines l
            JOIN documents d ON d.id = l.doc_id
            JOIN productos p ON p.codigo = l.codigo
            {where_sql}
            GROUP BY l.codigo
            ORDER BY total_sales DESC
            LIMIT ?
        """, params + [int(limit)])
        
        results = []
        for row in cur.fetchall():
            results.append({
                "codigo": row[0],
                "nombre": row[1],
                "qty": float(row[2] or 0),
                "ventas": _fmt2(row[3] or 0),
                "num_sales": row[4] or 0
            })
        
        return results

def report_inventory_rotation(months: int = 12) -> Dict:
    """
    Análisis de rotación de inventario.
    Calcula turnover rate y productos de lenta rotación.
    """
    from datetime import timedelta, datetime as dt
    
    start_date = (dt.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Productos activos
        cur.execute("SELECT COUNT(*) FROM productos WHERE cantidad > 0")
        active_products = cur.fetchone()[0] or 0
        
        # Productos de lenta rotación (lista detallada)
        cur.execute("""
            SELECT p.codigo, p.nombre, p.cantidad as stock,
                   COALESCE((
                       SELECT SUM(l.qty) FROM document_lines l
                       JOIN documents d ON d.id = l.doc_id
                       WHERE d.tipo = 'SALE' AND l.codigo = p.codigo AND d.fecha >= ?
                   ), 0) as ventas_period,
                   CASE WHEN COALESCE((
                       SELECT SUM(l.qty)/? FROM document_lines l
                       JOIN documents d ON d.id = l.doc_id
                       WHERE d.tipo = 'SALE' AND l.codigo = p.codigo AND d.fecha >= ?
                   ), 0) > 0
                   THEN p.cantidad / (COALESCE((
                       SELECT SUM(l.qty)/? FROM document_lines l
                       JOIN documents d ON d.id = l.doc_id
                       WHERE d.tipo = 'SALE' AND l.codigo = p.codigo AND d.fecha >= ?
                   ), 0.001))
                   ELSE 9999 END as dias_cobertura
            FROM productos p
            WHERE p.cantidad > 0
            ORDER BY dias_cobertura DESC
            LIMIT 50
        """, (start_date, months*30, start_date, months*30, start_date))
        
        slow_moving = [
            {
                "codigo": r[0], "nombre": r[1], "stock": r[2],
                "ventas_period": r[3], "dias_cobertura": round(r[4], 0)
            }
            for r in cur.fetchall()
        ]
        
        # Valor del inventario usando costo promedio real
        cur.execute("""
            SELECT SUM(cantidad * avg_cost) as total_value
            FROM productos
            WHERE activo = 1
        """)
        
        total_inv_value = float(cur.fetchone()[0] or 0)
        
        # Costo de ventas en el período usando avg_cost
        cur.execute("""
            SELECT SUM(l.qty * p.avg_cost) as cogs
            FROM document_lines l
            JOIN documents d ON d.id = l.doc_id
            JOIN productos p ON p.codigo = l.codigo
            WHERE d.tipo = 'SALE' AND d.fecha >= ?
        """, (start_date,))
        
        total_cogs = float(cur.fetchone()[0] or 0)
        
        # Cálculos
        avg_inventory = total_inv_value  # Simplificado
        turnover = (total_cogs / avg_inventory) if avg_inventory > 0 else 0
        days_to_sell = (365 / turnover) if turnover > 0 else 999
        
        return {
            "total_inventory_value": _fmt2(total_inv_value),
            "total_cogs_period": _fmt2(total_cogs),
            "active_products": active_products,
            "slow_moving_products": slow_moving,
            "turnover_rate": round(turnover, 2),
            "days_to_sell": round(days_to_sell, 0),
            "period_months": months
        }


# ========== KPIs DASHBOARD (Tarea 12) ==========

def get_valor_inventario() -> float:
    """Valor total del inventario = Σ(cantidad * avg_cost) de productos activos."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COALESCE(SUM(cantidad * avg_cost), 0)
                FROM productos
                WHERE activo = 1
            """)
            row = cur.fetchone()
            return _fmt2(row[0] if row else 0.0)
    except Exception:
        return 0.0


def get_alertas_inventario() -> dict:
    """
    Retorna contadores de alertas de inventario:
      - critico: productos con cantidad = 0
      - bajo_stock: productos con 0 < cantidad < 5
      - pendientes: documentos PURCHASE con estado = 'PENDIENTE'
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM productos WHERE cantidad = 0 AND activo = 1"
            )
            critico = int(cur.fetchone()[0] or 0)

            cur.execute(
                "SELECT COUNT(*) FROM productos WHERE cantidad > 0 AND cantidad < 5 AND activo = 1"
            )
            bajo_stock = int(cur.fetchone()[0] or 0)

            try:
                cur.execute(
                    "SELECT COUNT(*) FROM documents WHERE tipo = 'PURCHASE' AND estado = 'PENDIENTE'"
                )
                pendientes = int(cur.fetchone()[0] or 0)
            except Exception:
                pendientes = 0

            return {"critico": critico, "bajo_stock": bajo_stock, "pendientes": pendientes}
    except Exception:
        return {"critico": 0, "bajo_stock": 0, "pendientes": 0}


def get_ventas_por_dia_30d(periodo: str = "mes") -> dict:
    """
    Ventas agrupadas por día del período.
    periodo: "hoy" | "semana" | "mes"
    Retorna dict{date: float_monto} con todos los días (sin ventas = 0.0).
    """
    from datetime import datetime as _dt, timedelta as _td, date as _date
    try:
        fecha_desde, _ = _periodo_fechas(periodo)
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT DATE(d.fecha) as fecha,
                       COALESCE(SUM(l.qty * l.unit_price), 0) as total
                FROM documents d
                JOIN document_lines l ON d.id = l.doc_id
                WHERE d.tipo = 'SALE' AND d.fecha >= ?
                GROUP BY DATE(d.fecha)
                ORDER BY fecha
            """, (fecha_desde,))
            resultado = {}
            for row in cur.fetchall():
                if row[0]:
                    try:
                        fecha = _dt.strptime(row[0], "%Y-%m-%d").date()
                    except Exception:
                        continue
                    resultado[fecha] = _fmt2(row[1])

        # Rellenar días sin ventas
        iter_d = _date.fromisoformat(fecha_desde)
        hoy = _dt.now().date()
        while iter_d <= hoy:
            if iter_d not in resultado:
                resultado[iter_d] = 0.0
            iter_d += _td(days=1)
        return resultado
    except Exception:
        return {}


def get_kpis_hoy(periodo: str = "hoy") -> dict:
    """
    KPIs del período:
      ventas_hoy, caja_disponible, margen_bruto_pct,
      ticket_promedio, tasa_devolucion_pct
    periodo: "hoy" | "semana" | "mes"
    """
    from datetime import datetime as _dt
    _, filtro = _periodo_fechas(periodo)
    hoy = _dt.now().strftime("%Y-%m-%d")
    try:
        with get_connection() as conn:
            cur = conn.cursor()

            # Ventas hoy (monto) y costo hoy
            cur.execute(f"""
                SELECT COALESCE(SUM(l.qty * l.unit_price), 0),
                       COALESCE(SUM(l.qty * p.avg_cost), 0),
                       COUNT(DISTINCT d.id)
                FROM documents d
                JOIN document_lines l ON d.id = l.doc_id
                JOIN productos p ON p.codigo = l.codigo
                WHERE d.tipo = 'SALE' AND {filtro}
            """)
            row = cur.fetchone()
            ventas_hoy = _fmt2(row[0])
            costo_hoy  = _fmt2(row[1])
            num_docs   = int(row[2] or 0)

            # Compras del periodo para utilidad neta
            cur.execute(f"SELECT COALESCE(SUM(amount_paid), 0) FROM documents d WHERE d.tipo = 'PURCHASE' AND {filtro}")
            compras_periodo = _fmt2(cur.fetchone()[0])
            utilidad_neta = _fmt2(ventas_hoy - costo_hoy - compras_periodo)

            # Descuentos PCT
            cur.execute("PRAGMA table_info(document_lines)")
            cols = [r[1] for r in cur.fetchall()]
            descuentos_pct = 0.0
            if 'discount' in cols and ventas_hoy > 0:
                cur.execute(f"""
                    SELECT COALESCE(SUM(l.discount), 0)
                    FROM documents d
                    JOIN document_lines l ON d.id = l.doc_id
                    WHERE d.tipo = 'SALE' AND {filtro}
                """)
                total_desc = float(cur.fetchone()[0])
                descuentos_pct = _fmt2((total_desc / ventas_hoy) * 100)

            # Margen bruto %
            margen_pct = _fmt2(
                (ventas_hoy - costo_hoy) / ventas_hoy * 100
                if ventas_hoy > 0 else 0.0
            )

            # Ticket promedio
            ticket = _fmt2(ventas_hoy / num_docs if num_docs > 0 else 0.0)

            # Caja disponible — último cash_session o Σ cash_movements hoy
            caja = 0.0
            try:
                cur.execute("""
                    SELECT closing_amount FROM cash_sessions
                    WHERE closing_amount IS NOT NULL
                    ORDER BY id DESC LIMIT 1
                """)
                r = cur.fetchone()
                if r and r[0] is not None:
                    caja = _fmt2(r[0])
                else:
                    cur.execute("""
                        SELECT COALESCE(SUM(
                            CASE WHEN type IN ('SALE','INCOME') THEN amount
                                 ELSE -amount END
                        ), 0)
                        FROM cash_movements
                        WHERE DATE(created_at) = ?
                    """, (hoy,))
                    r2 = cur.fetchone()
                    caja = _fmt2(r2[0] if r2 else 0.0)
            except Exception:
                caja = 0.0

            # Tasa de devolución %
            tasa_dev = 0.0
            try:
                cur.execute(
                    "SELECT COUNT(*) FROM documents WHERE tipo = 'CREDIT_NOTE' AND DATE(fecha) = ?",
                    (hoy,)
                )
                n_dev = int(cur.fetchone()[0] or 0)
                tasa_dev = _fmt2(n_dev / num_docs * 100 if num_docs > 0 else 0.0)
            except Exception:
                pass

            return {
                "ventas_hoy":         ventas_hoy,
                "caja_disponible":    caja,
                "margen_bruto_pct":   margen_pct,
                "utilidad_neta":      utilidad_neta,
                "ticket_promedio":    ticket,
                "tasa_devolucion_pct": tasa_dev,
                "compras_periodo":    compras_periodo,
                "descuentos_pct":     descuentos_pct,
            }
    except Exception:
        return {
            "ventas_hoy": 0.0, "caja_disponible": 0.0,
            "margen_bruto_pct": 0.0, "ticket_promedio": 0.0,
            "tasa_devolucion_pct": 0.0,
            "utilidad_neta": 0.0,
            "compras_periodo": 0.0,
            "descuentos_pct": 0.0,
        }


def get_top_rentabilidad(limit: int = 5, periodo: str = "mes") -> List[Dict]:
    """
    Top N productos por RENTABILIDAD = (unit_price - avg_cost) * qty vendida.
    Usa ventas históricas de document_lines JOIN productos.
    periodo: "hoy" | "semana" | "mes"
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            fecha_desde, _ = _periodo_fechas(periodo)
            cur.execute("""
                SELECT p.nombre,
                       SUM(l.qty) as qty,
                       AVG(l.unit_price) as avg_price,
                       p.avg_cost,
                       SUM((l.unit_price - p.avg_cost) * l.qty) as rentabilidad
                FROM document_lines l
                JOIN documents d ON d.id = l.doc_id
                JOIN productos p ON p.codigo = l.codigo
                WHERE d.tipo = 'SALE' AND d.fecha >= ?
                GROUP BY l.codigo
                ORDER BY rentabilidad DESC
                LIMIT ?
            """, (fecha_desde, int(limit)))
            results = []
            for row in cur.fetchall():
                results.append({
                    "nombre":          row[0],
                    "qty":             _fmt2(row[1]),
                    "margen_unitario": _fmt2((row[2] or 0) - (row[3] or 0)),
                    "rentabilidad":    _fmt2(row[4]),
                })
            return results
    except Exception:
        return []


def get_sin_movimiento_30d() -> int:
    """
    Cuenta productos activos sin ningún movimiento de stock en los últimos 30 días.
    """
    from datetime import datetime as _dt, timedelta as _td
    hace_30 = (_dt.now() - _td(days=30)).strftime("%Y-%m-%d")
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM productos p
                WHERE p.activo = 1
                  AND NOT EXISTS (
                      SELECT 1 FROM document_lines l
                      JOIN documents d ON d.id = l.doc_id
                      WHERE l.codigo = p.codigo AND d.fecha >= ?
                  )
            """, (hace_30,))
            row = cur.fetchone()
            return int(row[0] if row else 0)
    except Exception:
        return 0

def get_top_clientes(limit: int = 5, periodo: str = "mes") -> List[Dict]:
    """
    Top clientes por volumen de compras en el período.
    Usa _periodo_fechas() que ya existe.
    Retorna: [{nombre, transacciones, total, porcentaje}]
    Si partner_id es NULL → nombre = 'Consumidor Final'
    """
    try:
        from src.database.connection import get_connection
        with get_connection() as conn:
            cur = conn.cursor()
            fecha_desde, filtro = _periodo_fechas(periodo)
            
            # Total ventas del periodo
            cur.execute(f"""
                SELECT COALESCE(SUM(l.qty * l.unit_price), 0)
                FROM documents d
                JOIN document_lines l ON d.id = l.doc_id
                WHERE d.tipo = 'SALE' AND {filtro}
            """)
            total_ventas = float(cur.fetchone()[0] or 0)

            cur.execute(f"""
                SELECT COALESCE(p.name, 'Consumidor Final') as nombre,
                       COUNT(DISTINCT d.id) as transacciones,
                       SUM(l.qty * l.unit_price) as total
                FROM documents d
                JOIN document_lines l ON d.id = l.doc_id
                LEFT JOIN partners p ON p.id = d.partner_id
                WHERE d.tipo = 'SALE' AND {filtro}
                GROUP BY p.id
                ORDER BY total DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cur.fetchall():
                nombre = row[0]
                trans = int(row[1])
                total = float(row[2])
                pct = (total / total_ventas * 100) if total_ventas > 0 else 0
                results.append({
                    "nombre": nombre,
                    "transacciones": trans,
                    "total": total,
                    "porcentaje": pct
                })
            return results
    except Exception as e:
        import logging
        logging.warning("get_top_clientes error: %s", e)
        return []