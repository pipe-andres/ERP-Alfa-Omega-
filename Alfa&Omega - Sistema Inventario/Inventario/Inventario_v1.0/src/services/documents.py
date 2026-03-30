# core/documents.py
from __future__ import annotations
from typing import Optional
import os
from decimal import Decimal, ROUND_HALF_UP

from src.database.connection import get_connection, DB_ENGINE

D = Decimal

# ------------------------------
# Esquema de numeración por series
# ------------------------------

def ensure_schema() -> None:
    """
    Crea tabla de series/numeradores y agrega columna 'numero' a documents si hiciera falta.
    """
    # If running against Postgres, skip inline DDL; Alembic manages schema
    if DB_ENGINE == 'postgres':
        return

    with get_connection() as conn:
        cur = conn.cursor()

        # Tabla de numeradores
        if DB_ENGINE == 'postgres':
            cur.execute("""
            CREATE TABLE IF NOT EXISTS doc_series (
                id        SERIAL PRIMARY KEY,
                doc_type  TEXT NOT NULL,
                series    TEXT NOT NULL,
                prefix    TEXT,
                next_no   INTEGER NOT NULL DEFAULT 1,
                UNIQUE(doc_type, series)
            )""")
        else:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS doc_series (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_type  TEXT NOT NULL,
                series    TEXT NOT NULL,
                prefix    TEXT,
                next_no   INTEGER NOT NULL DEFAULT 1,
                UNIQUE(doc_type, series)
            )""")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_doc_series_type ON doc_series(doc_type)")

        # Asegura columna 'numero' en documents (SQLite only, Postgres managed by Alembic)
        if DB_ENGINE != 'postgres':
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            if cur.fetchone():
                cur.execute("PRAGMA table_info(documents)")
                cols = [r[1] for r in cur.fetchall()]
                if "numero" not in cols:
                    cur.execute("ALTER TABLE documents ADD COLUMN numero TEXT")
                    cur.execute("CREATE INDEX IF NOT EXISTS ix_documents_numero ON documents(numero)")
        conn.commit()

def seed_default_series() -> None:
    """Crea series por defecto si no existen."""
    with get_connection() as conn:
        cur = conn.cursor()
        for t, s in [("PURCHASE", "C01"), ("SALE", "V01")]:
            cur.execute("INSERT INTO doc_series (doc_type, series, prefix, next_no) VALUES (?,?,?,?) ON CONFLICT(doc_type, series) DO NOTHING",
                        (t, s, s + "-", 1))
        conn.commit()

# ------------------------------
# Numeración
# ------------------------------

def get_next_number(doc_type: str, series: str) -> str:
    """
    Toma y avanza el numerador para (doc_type, series) de forma ATÓMICA.
    Retorna el número final impreso (prefix + correlativo con padding).
    Compatible con SQLite y Postgres.
    """
    doc_type = doc_type.strip().upper()
    series = series.strip().upper()
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # SELECT con LOCK para evitar race conditions
            cur.execute("SELECT id, prefix, next_no FROM doc_series WHERE doc_type=? AND series=?", 
                       (doc_type, series))
            row = cur.fetchone()
            
            if not row:
                # Crear nueva serie
                if DB_ENGINE == 'postgres':
                    cur.execute("""INSERT INTO doc_series (doc_type, series, prefix, next_no) 
                                 VALUES (?,?,?,1) RETURNING id""",
                               (doc_type, series, series + "-"))
                    ds_id = int(cur.fetchone()[0])
                else:
                    cur.execute("INSERT INTO doc_series (doc_type, series, prefix, next_no) VALUES (?,?,?,1)",
                               (doc_type, series, series + "-"))
                    ds_id = cur.lastrowid
                prefix, next_no = series + "-", 1
            else:
                ds_id, prefix, next_no = row[0], row[1] or (series + "-"), int(row[2])

            # Generar número y ACTUALIZAR EN LA MISMA TRANSACCIÓN
            numero_impreso = f"{prefix}{next_no:06d}"
            cur.execute("UPDATE doc_series SET next_no = next_no + 1 WHERE id=?", (ds_id,))
            conn.commit()
            return numero_impreso
    
    except Exception as e:
        raise

# ------------------------------
# PDFs de documentos
# ------------------------------

def _fmt2(x) -> str:
    try:
        d = D(str(x)).quantize(D("0.01"), rounding=ROUND_HALF_UP)
        return f"{d:.2f}"
    except Exception:
        return str(x)

def export_purchase_pdf(doc_id: int, path: str, *, logo_path: Optional[str]=None,
                        company_name: str="Mi Empresa", company_tax: str="NIT/RUC", company_addr: str="Dirección") -> None:
    """
    Genera PDF de Compra (PURCHASE) con cabecera simple y detalle de líneas.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        SELECT d.numero, d.fecha, d.notas,
               p.code, p.kind, p.name, p.tax_id, p.address, p.city
        FROM documents d
        LEFT JOIN partners p ON p.id = d.partner_id
        WHERE d.id=? AND d.tipo='PURCHASE'
        """, (doc_id,))
        head = cur.fetchone()
        if not head:
            raise ValueError("Documento no encontrado o no es PURCHASE.")
        numero, fecha, notas, pr_code, pr_kind, pr_name, pr_tax, pr_addr, pr_city = head

        cur.execute("""
        SELECT l.codigo, prod.nombre, l.qty, l.unit_cost, l.unit_price
        FROM document_lines l
        LEFT JOIN productos prod ON prod.codigo = l.codigo
        WHERE l.doc_id=?
        """, (doc_id,))
        lines = cur.fetchall()

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
    c.drawString(5*cm, y, "COMPROBANTE DE COMPRA")
    c.setFont("Helvetica", 9)
    c.drawString(5*cm, y-0.5*cm, f"Número: {numero or '(s/n)'}")
    c.drawString(5*cm, y-1.0*cm, f"Fecha: {str(fecha)[:19]}")
    y -= 2*cm

    # Empresa
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, company_name)
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y-0.4*cm, f"{company_tax}")
    c.drawString(2*cm, y-0.8*cm, f"{company_addr}")
    # Proveedor
    c.setFont("Helvetica-Bold", 10)
    c.drawString(10*cm, y, "Proveedor:")
    c.setFont("Helvetica", 9)
    c.drawString(10*cm, y-0.4*cm, f"{pr_name or '-'}")
    c.drawString(10*cm, y-0.8*cm, f"{(pr_tax or '')}  {pr_code or ''}")
    y -= 1.6*cm

    # Cabeceras
    c.setFont("Helvetica-Bold", 9)
    headers = ["Código","Nombre","Cant.","Costo u.","Total"]
    x = [2.0, 6.0, 14.0, 16.0, 18.0]  # cm
    for i, h in enumerate(headers): c.drawString(x[i]*cm, y, h)
    y -= 0.35*cm
    c.setFont("Helvetica", 9)

    total = D("0.00")
    for cod, nombre, qty, unit_cost, unit_price in lines:
        if y < 2*cm:
            c.showPage(); y = H - 2*cm
            c.setFont("Helvetica-Bold", 9)
            for i, h in enumerate(headers): c.drawString(x[i]*cm, y, h)
            y -= 0.35*cm
            c.setFont("Helvetica", 9)

        linea = D(str(qty)) * D(str(unit_cost or 0))
        total += linea
        vals = [str(cod), str(nombre or ""), f"{qty:.2f}", _fmt2(unit_cost), _fmt2(linea)]
        for i, v in enumerate(vals): c.drawString(x[i]*cm, y, v)
        y -= 0.32*cm

    # Totales
    if y < 3*cm: c.showPage(); y = H - 2*cm
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(19.5*cm, y, f"TOTAL COMPRA: {_fmt2(total)}")
    y -= 0.6*cm

    # Notas
    if notas:
        c.setFont("Helvetica", 9)
        c.drawString(2*cm, y, "Notas:")
        y -= 0.4*cm
        c.drawString(2*cm, y, str(notas)[:90])
    c.save()

def export_sale_pdf(doc_id: int, path: str, *, logo_path: Optional[str]=None,
                    company_name: str="Mi Empresa", company_tax: str="NIT/RUC", company_addr: str="Dirección",
                    tax_rate: Optional[float] = None, tax_included: Optional[bool] = None) -> None:
    """
    Genera PDF de Venta (SALE). Lee impuestos de settings si no se especifican.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from src.database.settings import get_settings

    # lee settings si vienen None
    s = get_settings()
    if tax_rate is None:
        tax_rate = float(s.get("tax_rate") or 0.0)
    if tax_included is None:
        tax_included = bool(s.get("tax_included"))

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        SELECT d.numero, d.fecha, d.notas,
               p.code, p.kind, p.name, p.tax_id, p.address, p.city
        FROM documents d
        LEFT JOIN partners p ON p.id = d.partner_id
        WHERE d.id=? AND d.tipo='SALE'
        """, (doc_id,))
        head = cur.fetchone()
        if not head:
            raise ValueError("Documento no encontrado o no es SALE.")
        numero, fecha, notas, pr_code, pr_kind, pr_name, pr_tax, pr_addr, pr_city = head

        cur.execute("""
        SELECT l.codigo, prod.nombre, l.qty, l.unit_price
        FROM document_lines l
        LEFT JOIN productos prod ON prod.codigo = l.codigo
        WHERE l.doc_id=?
        """, (doc_id,))
        lines = cur.fetchall()

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
    c.drawString(5*cm, y, "COMPROBANTE DE VENTA")
    c.setFont("Helvetica", 9)
    c.drawString(5*cm, y-0.5*cm, f"Número: {numero or '(s/n)'}")
    c.drawString(5*cm, y-1.0*cm, f"Fecha: {str(fecha)[:19]}")
    y -= 2*cm

    # Empresa
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, company_name)
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y-0.4*cm, f"{company_tax}")
    c.drawString(2*cm, y-0.8*cm, f"{company_addr}")
    # Cliente
    c.setFont("Helvetica-Bold", 10)
    c.drawString(10*cm, y, "Cliente:")
    c.setFont("Helvetica", 9)
    c.drawString(10*cm, y-0.4*cm, f"{pr_name or '-'}")
    c.drawString(10*cm, y-0.8*cm, f"{(pr_tax or '')}  {pr_code or ''}")
    y -= 1.6*cm

    # Cabeceras
    c.setFont("Helvetica-Bold", 9)
    headers = ["Código","Nombre","Cant.","Precio u.","Subtotal"]
    x = [2.0, 6.0, 14.0, 16.0, 18.0]  # cm
    for i, h in enumerate(headers): c.drawString(x[i]*cm, y, h)
    y -= 0.35*cm
    c.setFont("Helvetica", 9)

    from decimal import Decimal, ROUND_HALF_UP
    D = Decimal
    q2 = lambda n: D(str(n)).quantize(D("0.01"), rounding=ROUND_HALF_UP)

    subtotal = D("0.00")
    for cod, nombre, qty, unit_price in lines:
        if y < 2*cm:
            c.showPage(); y = H - 2*cm
            c.setFont("Helvetica-Bold", 9)
            for i, h in enumerate(headers): c.drawString(x[i]*cm, y, h)
            y -= 0.35*cm
            c.setFont("Helvetica", 9)

        linea = D(str(qty)) * D(str(unit_price or 0))
        subtotal += linea
        vals = [str(cod), str(nombre or ""), f"{qty:.2f}", _fmt2(unit_price), _fmt2(linea)]
        for i, v in enumerate(vals): c.drawString(x[i]*cm, y, v)
        y -= 0.32*cm

    # Impuestos
    neto = subtotal
    tax = D("0.00")
    total = subtotal
    if (tax_rate or 0) > 0:
        r = D(str(tax_rate))
        if tax_included:
            base = (subtotal / (D("1") + r)).quantize(D("0.01"), rounding=ROUND_HALF_UP)
            neto = base
            tax = (subtotal - base).quantize(D("0.01"), rounding=ROUND_HALF_UP)
            total = subtotal
        else:
            tax = (subtotal * r).quantize(D("0.01"), rounding=ROUND_HALF_UP)
            total = (subtotal + tax).quantize(D("0.01"), rounding=ROUND_HALF_UP)
            neto = subtotal

    # Totales
    if y < 3*cm: c.showPage(); y = H - 2*cm
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(19.5*cm, y, f"SUBTOTAL: {_fmt2(neto)}"); y -= 0.5*cm
    c.drawRightString(19.5*cm, y, f"IMPUESTO: {_fmt2(tax)}"); y -= 0.5*cm
    c.drawRightString(19.5*cm, y, f"TOTAL:    {_fmt2(total)}"); y -= 0.6*cm

    c.save()