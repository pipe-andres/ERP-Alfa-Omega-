# core/services.py
from __future__ import annotations
from typing import List, Tuple, Optional, Dict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import csv
import os
from typing import Any

# PRIMERO: Logging centralizado
from src.core.error_handler import logger, log_error

from src.database.connection import get_connection, DB_ENGINE
from src.services.audit import log_event
from src.services.documents import get_next_number
from src.services.partners import get_partner_by_code
from src.database import repository
from src.core import acl
from src.core.auth import has_perm

def _fetch_user_with_roles_safe(user_id: int) -> Optional[Dict]:
    """Obtener usuario con roles sin fallar si no existe."""
    try:
        from src.core.auth import _fetch_user_with_roles
        if DB_ENGINE == 'json':
            # load users and roles from json files
            from src.database import json_store
            user = json_store.find_one('users', lambda u: u.get('id') == user_id)
            if not user:
                return None
            # gather role names
            roles = []
            for ur in json_store.list_rows('user_roles', predicate=lambda r: r.get('user_id') == user_id):
                rdef = json_store.find_one('roles', lambda r: r.get('id') == ur.get('role_id'))
                if rdef:
                    roles.append(rdef.get('name'))
            return {
                'id': user.get('id'),
                'username': user.get('username'),
                'name': user.get('name'),
                'roles': roles
            }
        else:
            # Intentar obtener del usuario por ID - consulta directa
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT u.id, u.username, u.name, 
                           GROUP_CONCAT(r.name, ',') as roles
                    FROM users u
                    LEFT JOIN user_roles ur ON u.id = ur.user_id
                    LEFT JOIN roles r ON ur.role_id = r.id
                    WHERE u.id = ?
                    GROUP BY u.id
                """, (user_id,))
                row = cur.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "username": row[1],
                        "name": row[2],
                        "roles": row[3].split(',') if row[3] else []
                    }
    except Exception:
        pass
    return None

D = Decimal
FMT2 = lambda x: float(D(str(x)).quantize(D("0.01"), rounding=ROUND_HALF_UP))

# =========================
# Productos (CRUD / Listado)
# =========================

def get_product(codigo: str) -> Optional[Tuple]:
    """Devuelve producto usando repository (con caching).
    Retorna: (codigo, nombre, categoria, precio, cantidad, avg_cost)
    """
    row = repository.get_product_by_code(codigo)
    if not row:
        return None
    # Return full tuple directly (was previously sliced to 6)
    return tuple(row)

def add_product(codigo: str, nombre: str, categoria: str, precio: float, cantidad: int, avg_cost: float = 0.0, stock_minimo: int = 5, reorder_qty: int = 10, proveedor_id: Optional[int] = None, user_id: Optional[int] = None):
    # Validar entradas obligatorias
    if not codigo or not nombre:
        raise ValueError("Código y Nombre son obligatorios.")
    codigo = codigo.strip()
    nombre = nombre.strip()
    if not codigo or not nombre:
        raise ValueError("Código y Nombre no pueden estar vacíos.")
    # Validar valores numéricos
    precio = float(precio)
    cantidad = int(cantidad)
    avg_cost = float(avg_cost)
    if precio < 0:
        raise ValueError("El precio no puede ser negativo.")
    if cantidad < 0:
        raise ValueError("La cantidad no puede ser negativa.")
    if avg_cost < 0:
        raise ValueError("El costo promedio no puede ser negativo.")
    # Permission check: if user_id provided, require 'product.create' or ADMIN
    if user_id is not None:
        user = _fetch_user_with_roles_safe(user_id)
        if user and not has_perm(user, "ADMIN") and not acl.has_permission(user_id, "product.create"):
            raise PermissionError("Usuario no autorizado para crear productos.")
    
    # Check for duplicate active product
    if DB_ENGINE == 'json':
        from src.database import json_store
        existing_active = json_store.list_rows('productos', lambda r: r.get('codigo') == codigo and r.get('activo', 1) == 1)
        if existing_active:
            raise ValueError(f"El código '{codigo}' ya existe.")
        # if there is an inactive record with same code, reactivate it instead
        existing_inactive = json_store.list_rows('productos', lambda r: r.get('codigo') == codigo and r.get('activo', 1) == 0)
        if existing_inactive:
            def _updater(r):
                r.update({
                    'nombre': nombre,
                    'categoria': (categoria or '').strip(),
                    'precio': precio,
                    'cantidad': cantidad,
                    'avg_cost': avg_cost,
                    'stock_minimo': int(stock_minimo),
                    'reorder_qty': int(reorder_qty),
                    'proveedor_id': proveedor_id,
                    'activo': 1
                })
            json_store.update('productos', lambda r: r.get('codigo') == codigo and r.get('activo', 0) == 0, _updater)
            # invalidate caches and log as creation; prefer prefix API
            from src.core import caching
            caching.invalidate_prefix("src.database.repository.list_products")
            caching.invalidate_prefix("src.database.repository.count_products")
            if user_id:
                log_event(user_id, "PRODUCT_CREATE", {"codigo": codigo, "nombre": nombre})
            return
    else:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM productos WHERE codigo = ? AND activo = 1", (codigo,))
            if cur.fetchone():
                raise ValueError(f"El código '{codigo}' ya existe.")
            # check for inactive row; if found reactivate and update
            cur.execute("SELECT id FROM productos WHERE codigo = ? AND activo = 0", (codigo,))
            old = cur.fetchone()
            if old:
                cur.execute(
                    "UPDATE productos SET nombre=?, categoria=?, precio=?, cantidad=?, avg_cost=?, stock_minimo=?, reorder_qty=?, proveedor_id=?, activo=1 WHERE id=?",
                    (nombre, (categoria or '').strip(), precio, cantidad, avg_cost, int(stock_minimo), int(reorder_qty), proveedor_id, old[0])
                )
                conn.commit()
                from src.core import caching
                caching.invalidate_prefix("src.database.repository.list_products")
                caching.invalidate_prefix("src.database.repository.count_products")
                if user_id:
                    log_event(user_id, "PRODUCT_CREATE", {"codigo": codigo, "nombre": nombre})
                return
    
    if DB_ENGINE == 'json':
        from src.database import json_store
        json_store.insert('productos', {
            'codigo': codigo,
            'nombre': nombre,
            'categoria': (categoria or "").strip(),
            'precio': precio,
            'cantidad': cantidad,
            'avg_cost': avg_cost,
            'stock_minimo': int(stock_minimo),
            'reorder_qty': int(reorder_qty),
            'proveedor_id': proveedor_id
        })
    else:
        with get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO productos (codigo, nombre, categoria, precio, cantidad, avg_cost, stock_minimo, reorder_qty, proveedor_id)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (codigo, nombre, (categoria or "").strip(), precio, cantidad, avg_cost, int(stock_minimo), int(reorder_qty), proveedor_id))
                conn.commit()
            except Exception as e:
                if "UNIQUE constraint failed" in str(e) or "duplicate" in str(e).lower():
                    raise ValueError(f"El código '{codigo}' ya existe.")
                raise
    # Invalidate caches after product creation
    from src.core import caching
    caching.clear_cache("src.database.repository.list_products")
    caching.clear_cache("src.database.repository.count_products")
    caching.clear_cache("src.database.repository.get_product_by_code")
    if user_id:
        log_event(user_id, "PRODUCT_CREATE", {"codigo": codigo, "nombre": nombre})

def update_product(codigo: str, nombre: Optional[str] = None, categoria: Optional[str] = None,
                   precio: Optional[float] = None, cantidad: Optional[int] = None,
                   stock_minimo: Optional[int] = None, reorder_qty: Optional[int] = None,
                   proveedor_id: Any = False, user_id: Optional[int] = None):
    sets: List[str] = []
    params: List[Any] = []
    if nombre is not None:    
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre no puede estar vacío.")
        sets.append("nombre=?");    params.append(nombre)
    if categoria is not None: sets.append("categoria=?"); params.append((categoria or "").strip())
    if precio is not None:    
        precio = float(precio)
        if precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        sets.append("precio=?");    params.append(precio)
    if cantidad is not None:  
        cantidad = int(cantidad)
        if cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        sets.append("cantidad=?");  params.append(cantidad)
    if stock_minimo is not None:
        sets.append("stock_minimo=?"); params.append(int(stock_minimo))
    if reorder_qty is not None:
        sets.append("reorder_qty=?"); params.append(int(reorder_qty))
    if proveedor_id is not False:
        sets.append("proveedor_id=?"); params.append(proveedor_id)

    if not sets:
        return
    if user_id is not None:
        user = _fetch_user_with_roles_safe(user_id)
        if user and not has_perm(user, "ADMIN") and not acl.has_permission(user_id, "product.update"):
            raise PermissionError("Usuario no autorizado para actualizar productos.")
    
    if DB_ENGINE == 'json':
        from src.database import json_store
        def _updater(r):
            if nombre is not None:
                r['nombre'] = nombre
            if categoria is not None:
                r['categoria'] = (categoria or "").strip()
            if precio is not None:
                r['precio'] = precio
            if cantidad is not None:
                r['cantidad'] = cantidad
            if stock_minimo is not None:
                r['stock_minimo'] = int(stock_minimo)
            if reorder_qty is not None:
                r['reorder_qty'] = int(reorder_qty)
            if proveedor_id is not False:
                r['proveedor_id'] = proveedor_id
        found = json_store.update('productos', lambda r: r.get('codigo') == codigo, _updater)
        if not found:
            raise ValueError("Producto no encontrado.")
    else:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE productos SET " + ", ".join(sets) + " WHERE codigo=?", params + [codigo])
            if cur.rowcount == 0:
                raise ValueError("Producto no encontrado.")
            conn.commit()
    # Invalidate caches after product update
    from src.core import caching
    caching.invalidate_prefix("src.database.repository.list_products")
    caching.invalidate_prefix("src.database.repository.count_products")
    caching.invalidate_prefix("src.database.repository.get_product_by_code")
    # legacy calls still respected by clear_cache()
    if user_id:
        log_event(user_id, "PRODUCT_UPDATE", {"codigo": codigo})

def delete_product(codigo: str, user_id: Optional[int] = None):
    if user_id is not None:
        # Verificar si es ADMIN o tiene permiso de eliminación
        user = _fetch_user_with_roles_safe(user_id)
        if user and not has_perm(user, "ADMIN") and not acl.has_permission(user_id, "product.delete"):
            raise PermissionError("Usuario no autorizado para eliminar productos.")
    
    if DB_ENGINE == 'json':
        from src.database import json_store
        def _updater(r):
            r['activo'] = 0
        found = json_store.update('productos', lambda r: r.get('codigo') == codigo and r.get('activo', 1) == 1, _updater)
        if not found:
            raise ValueError("Producto no encontrado.")
    else:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE productos SET activo = 0 WHERE codigo=? AND activo = 1", (codigo,))
            if cur.rowcount == 0:
                raise ValueError("Producto no encontrado.")
            conn.commit()
    # Invalidate caches after product deletion
    from src.core import caching
    caching.invalidate_prefix("src.database.repository.list_products")
    caching.invalidate_prefix("src.database.repository.count_products")
    caching.invalidate_prefix("src.database.repository.get_product_by_code")
    # legacy clear_cache() calls still work
    if user_id:
        log_event(user_id, "PRODUCT_DELETE", {"codigo": codigo})

def count_products(filter_by: Optional[str] = None, q: str = "") -> int:
    if DB_ENGINE == 'json':
        from src.database import json_store
        def _match(r):
            if not q:
                return True
            q_lower = q.lower()
            codigo = str(r.get('codigo', '')).lower()
            nombre = str(r.get('nombre', '')).lower()
            categoria = str(r.get('categoria', '')).lower()
            if filter_by == "Código":
                return q_lower in codigo
            elif filter_by == "Nombre":
                return q_lower in nombre
            elif filter_by == "Categoría":
                return q_lower in categoria
            else:
                return q_lower in codigo or q_lower in nombre or q_lower in categoria
        return json_store.count('productos', _match)
    
    where, params = [], []
    if q:
        ql = f"%{q.lower()}%"
        if filter_by == "Código":
            where.append("LOWER(codigo) LIKE ?"); params.append(ql)
        elif filter_by == "Nombre":
            where.append("LOWER(nombre) LIKE ?"); params.append(ql)
        elif filter_by == "Categoría":
            where.append("LOWER(categoria) LIKE ?"); params.append(ql)
        else:
            where.append("(LOWER(codigo) LIKE ? OR LOWER(nombre) LIKE ? OR LOWER(categoria) LIKE ?)")
            params += [ql, ql, ql]
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    return repository.count_products(where_sql, params)

def list_products_page(page: int = 1, page_size: int = 25,
                       filter_by: Optional[str] = None, q: str = "",
                       order_by: str = "nombre", asc: bool = True) -> List[Tuple]:
    order_allowed = {"codigo","nombre","categoria","precio","cantidad"}
    if order_by not in order_allowed: order_by = "nombre"

    if DB_ENGINE == 'json':
        from src.database import json_store
        def _match(r):
            if not q:
                return True
            q_lower = q.lower()
            codigo = str(r.get('codigo', '')).lower()
            nombre = str(r.get('nombre', '')).lower()
            categoria = str(r.get('categoria', '')).lower()
            if filter_by == "Código":
                return q_lower in codigo
            elif filter_by == "Nombre":
                return q_lower in nombre
            elif filter_by == "Categoría":
                return q_lower in categoria
            else:
                return q_lower in codigo or q_lower in nombre or q_lower in categoria
        offset = max(0, (int(page)-1) * int(page_size))
        rows = json_store.list_rows('productos', _match, order_key=order_by, limit=page_size, offset=offset)
        return [(r.get('codigo'), r.get('nombre'), r.get('categoria',''), float(r.get('precio',0)), int(r.get('cantidad',0))) for r in rows]

    order_sql = "ASC" if asc else "DESC"
    where, params = [], []
    if q:
        ql = f"%{q.lower()}%"
        if filter_by == "Código":
            where.append("LOWER(codigo) LIKE ?"); params.append(ql)
        elif filter_by == "Nombre":
            where.append("LOWER(nombre) LIKE ?"); params.append(ql)
        elif filter_by == "Categoría":
            where.append("LOWER(categoria) LIKE ?"); params.append(ql)
        else:
            where.append("(LOWER(codigo) LIKE ? OR LOWER(nombre) LIKE ? OR LOWER(categoria) LIKE ?)")
            params += [ql, ql, ql]
    where_sql = "WHERE " + " AND ".join(where) if where else ""

    offset = max(0, (int(page)-1) * int(page_size))
    # repository.list_products handles ordering/limits; build where_sql accordingly
    return repository.list_products(limit=page_size, offset=offset, where_sql=where_sql, params=params)

def stock_global_sum() -> float:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(cantidad),0) FROM productos WHERE activo = 1")
        return float(cur.fetchone()[0] or 0)

def low_stock_count(threshold: int = 5) -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM productos WHERE cantidad <= ? AND activo = 1", (int(threshold),))
        return int(cur.fetchone()[0] or 0)

# =========================
# CSV / Excel
# =========================

def export_products_csv(path: str) -> int:
    with get_connection() as conn, open(path, "w", newline="", encoding="utf-8") as f:
        cur = conn.cursor()
        cur.execute("SELECT codigo, nombre, categoria, precio, cantidad FROM productos WHERE activo = 1 ORDER BY nombre ASC")
        rows = [tuple(r) for r in cur.fetchall()]
        w = csv.writer(f)
        w.writerow(["codigo","nombre","categoria","precio","cantidad"])
        for r in rows: w.writerow(r)
        return len(rows)

def import_products_csv(path: str, upsert: bool = True, user_id: Optional[int] = None) -> int:
    count: int = 0
    with get_connection() as conn, open(path, newline="", encoding="utf-8") as f:
        cur = conn.cursor()
        for row in csv.DictReader(f):
            codigo = (row.get("codigo") or "").strip()[:50]
            if not codigo: continue
            nombre = (row.get("nombre") or "").strip()[:200]
            categoria = (row.get("categoria") or "").strip()[:100]
            precio = float(row.get("precio") or 0.0)
            cantidad = int(float(row.get("cantidad") or 0))
            if upsert:
                cur.execute("""
                    INSERT INTO productos (codigo,nombre,categoria,precio,cantidad,avg_cost)
                    VALUES (?,?,?,?,?,?)
                    ON CONFLICT(codigo) DO UPDATE SET
                        nombre=excluded.nombre,
                        categoria=excluded.categoria,
                        precio=excluded.precio,
                        cantidad=excluded.cantidad,
                        avg_cost=excluded.precio
                """, (codigo, nombre, categoria, precio, cantidad, precio))
            else:
                cur.execute("INSERT INTO productos (codigo,nombre,categoria,precio,cantidad,avg_cost) VALUES (?,?,?,?,?,?)",
                            (codigo, nombre, categoria, precio, cantidad, precio))
            count += 1
        conn.commit()
        
    from src.core import caching
    caching.clear_cache("src.database.repository.list_products")
    caching.clear_cache("src.database.repository.count_products")
    caching.clear_cache("src.database.repository.get_product_by_code")
    
    if user_id:
        log_event(user_id, "PRODUCT_IMPORT_CSV", {"path": os.path.basename(path), "rows": count})
    return count

def export_products_xlsx(path: str) -> int:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "Productos"
    ws.append(["codigo","nombre","categoria","precio","cantidad"])
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT codigo,nombre,categoria,precio,cantidad FROM productos WHERE activo = 1 ORDER BY nombre ASC")
        rows = [tuple(r) for r in cur.fetchall()]
        for r in rows: ws.append(list(r))
    wb.save(path)
    return len(rows)

def import_products_xlsx(path: str, upsert: bool = True, user_id: Optional[int] = None) -> int:
    import openpyxl
    wb = openpyxl.load_workbook(path); ws = wb.active
    headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    idx = {h: i for i, h in enumerate(headers)}
    req = {"codigo","nombre","precio","cantidad"}
    if not req.issubset(idx.keys()):
        raise ValueError(f"Faltan columnas obligatorias: {', '.join(req-idx.keys())}")
    count = 0
    with get_connection() as conn:
        cur = conn.cursor()
        for row in ws.iter_rows(min_row=2, values_only=True):
            codigo = (str(row[idx["codigo"]] or "")).strip()[:50]
            if not codigo: continue
            nombre = (str(row[idx["nombre"]] or "")).strip()[:200]
            categoria = (str(row[idx.get("categoria", -1)] or "")).strip()[:100] if "categoria" in idx else ""
            precio = float(row[idx["precio"]] or 0.0)
            cantidad = int(float(row[idx["cantidad"]] or 0))
            if upsert:
                cur.execute("""
                    INSERT INTO productos (codigo,nombre,categoria,precio,cantidad,avg_cost)
                    VALUES (?,?,?,?,?,?)
                    ON CONFLICT(codigo) DO UPDATE SET
                        nombre=excluded.nombre,
                        categoria=excluded.categoria,
                        precio=excluded.precio,
                        cantidad=excluded.cantidad,
                        avg_cost=excluded.precio
                """, (codigo, nombre, categoria, precio, cantidad, precio))
            else:
                cur.execute("INSERT INTO productos (codigo,nombre,categoria,precio,cantidad,avg_cost) VALUES (?,?,?,?,?,?)",
                            (codigo, nombre, categoria, precio, cantidad, precio))
            count += 1
        conn.commit()
        
    from src.core import caching
    caching.clear_cache("src.database.repository.list_products")
    caching.clear_cache("src.database.repository.count_products")
    caching.clear_cache("src.database.repository.get_product_by_code")
    
    if user_id:
        log_event(user_id, "PRODUCT_IMPORT_XLSX", {"path": os.path.basename(path), "rows": count})
    return count

# =========================
# PDF Inventario / Stock Bajo
# =========================

def export_inventory_pdf(path: str, logo_path: Optional[str] = None, title: str = "Inventario"):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader

    c = canvas.Canvas(path, pagesize=A4)
    W, H = A4
    y = H - 2*cm

    if logo_path and os.path.exists(logo_path):
        try:
            img = ImageReader(logo_path)
            c.drawImage(img, 2*cm, y-2*cm, width=2.5*cm, height=2.5*cm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 14); c.drawString(5*cm, y, title)
    c.setFont("Helvetica", 9); c.drawString(5*cm, y-0.6*cm, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 2*cm

    headers = ["Código","Nombre","Categoría","Precio","Cant."]
    x = [1.5, 4.2, 10.0, 15.0, 17.0]
    c.setFont("Helvetica-Bold", 9)
    for i, h in enumerate(headers): c.drawString(x[i]*cm, y, h)
    y -= 0.35*cm
    c.setFont("Helvetica", 9)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT codigo,nombre,categoria,precio,cantidad FROM productos ORDER BY nombre ASC")
        rows = [tuple(r) for r in cur.fetchall()]
        for cod, nom, cat, pre, can in rows:
            if y < 2*cm:
                c.showPage(); y = H - 2*cm
                c.setFont("Helvetica-Bold", 9)
                for i, h in enumerate(headers): c.drawString(x[i]*cm, y, h)
                y -= 0.35*cm; c.setFont("Helvetica", 9)
            c.drawString(x[0]*cm, y, str(cod))
            c.drawString(x[1]*cm, y, str(nom)[:40])
            c.drawString(x[2]*cm, y, str(cat)[:20])
            c.drawRightString((x[3]+1.8)*cm, y, f"{pre:.2f}")
            c.drawRightString((x[4]+1.2)*cm, y, str(can))
            y -= 0.3*cm
    c.save()

def export_low_stock_pdf(path: str, threshold: int = 5, logo_path: Optional[str] = None, title: str = "Stock Bajo"):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader

    c = canvas.Canvas(path, pagesize=A4)
    W, H = A4
    y = H - 2*cm

    if logo_path and os.path.exists(logo_path):
        try:
            img = ImageReader(logo_path)
            c.drawImage(img, 2*cm, y-2*cm, width=2.5*cm, height=2.5*cm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 14); c.drawString(5*cm, y, title)
    c.setFont("Helvetica", 9); c.drawString(5*cm, y-0.6*cm, f"Umbral: ≤ {threshold} — Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 2*cm

    headers = ["Código","Nombre","Categoría","Precio","Cant."]
    x = [1.5, 4.2, 10.0, 15.0, 17.0]
    c.setFont("Helvetica-Bold", 9)
    for i, h in enumerate(headers): c.drawString(x[i]*cm, y, h)
    y -= 0.35*cm
    c.setFont("Helvetica", 9)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT codigo,nombre,categoria,precio,cantidad FROM productos WHERE cantidad <= ? ORDER BY cantidad ASC, nombre ASC", (int(threshold),))
        rows = [tuple(r) for r in cur.fetchall()]
        for cod, nom, cat, pre, can in rows:
            if y < 2*cm:
                c.showPage(); y = H - 2*cm
                c.setFont("Helvetica-Bold", 9)
                for i, h in enumerate(headers): c.drawString(x[i]*cm, y, h)
                y -= 0.35*cm; c.setFont("Helvetica", 9)
            c.drawString(x[0]*cm, y, str(cod))
            c.drawString(x[1]*cm, y, str(nom)[:40])
            c.drawString(x[2]*cm, y, str(cat)[:20])
            c.drawRightString((x[3]+1.8)*cm, y, f"{pre:.2f}")
            c.drawRightString((x[4]+1.2)*cm, y, str(can))
            y -= 0.3*cm
    c.save()

# =========================
# Movimientos: Compras/Ventas/Ajustes
# =========================

def post_purchase(numero: str | None, fecha: str | None, items: List[Dict],
                  notas: str | None = None, partner_code: str | None = None,
                  series: str | None = "C01", user_id: Optional[int] = None) -> tuple[int, str | None]:
    """Registra una compra con rollback automático en caso de error."""
    if not items:
        raise ValueError("La compra debe tener al menos una línea.")
    
    numero_final = (numero or "").strip() or get_next_number("PURCHASE", (series or "C01").strip().upper())
    partner_id = None
    if partner_code:
        pr = get_partner_by_code(partner_code)
        if not pr:
            raise ValueError(f"Proveedor '{partner_code}' no existe.")
        partner_id = pr[0]
    fecha_ok = fecha or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Validar items antes de transacción
    for it in items:
        if not it.get("codigo"):
            raise ValueError("Cada línea debe tener un código de producto.")
        qty = float(it.get("qty") or 0)
        if qty <= 0:
            raise ValueError(f"Cantidad en línea debe ser > 0, recibido: {qty}")
        unit_cost = float(it.get("unit_cost") or 0)
        if unit_cost < 0:
            raise ValueError(f"Costo unitario no puede ser negativo: {unit_cost}")

    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO documents (tipo, fecha, numero, notas, partner_id) VALUES (?,?,?,?,?) RETURNING id",
                        ("PURCHASE", fecha_ok, numero_final, notas, partner_id))
            doc_id = int(cur.fetchone()[0])

            for it in items:
                codigo = it["codigo"].strip(); qty = float(it["qty"])
                unit_cost = float(it.get("unit_cost") or 0.0)
                unit_price = it.get("unit_price")
                # Ensure product exists before inserting document_lines due to FK
                cur.execute("SELECT cantidad, avg_cost FROM productos WHERE codigo=?", (codigo,))
                row = cur.fetchone()
                if not row:
                    cur.execute("INSERT INTO productos (codigo, nombre, categoria, precio, cantidad, avg_cost) VALUES (?,?,?,?,?,?)",
                                (codigo, codigo, "", unit_cost, int(qty), unit_cost))
                else:
                    old_qty, old_cost = float(row[0] or 0), float(row[1] or 0)
                    new_qty = old_qty + qty
                    new_cost = (old_qty * old_cost + qty * unit_cost) / new_qty if new_qty > 0 else unit_cost
                    cur.execute("UPDATE productos SET cantidad=?, avg_cost=? WHERE codigo=?",
                                (int(new_qty), new_cost, codigo))

                # now safe to insert document line and stock movement
                cur.execute("""INSERT INTO document_lines (doc_id, codigo, qty, unit_cost, unit_price, reason)
                               VALUES (?,?,?,?,?,?)""", (doc_id, codigo, qty, unit_cost, unit_price, ""))
                cur.execute("""INSERT INTO stock_movements (doc_id, codigo, qty, unit_cost, unit_price, tipo, reason, created_at)
                               VALUES (?,?,?,?,?,?,?,?)""", (doc_id, codigo, qty, unit_cost, unit_price, "PURCHASE", "", fecha_ok))
                # registrar en kardex usando la misma transacción/cur
                cur.execute("SELECT cantidad, avg_cost FROM productos WHERE codigo=?", (codigo,))
                balance_qty, current_avg_cost = cur.fetchone()
                balance_qty = float(balance_qty or 0)
                current_avg_cost = float(current_avg_cost or 0)
                balance_cost = balance_qty * current_avg_cost
                cur.execute(
                    """INSERT INTO kardex_moves (product_code, type, qty, unit_cost, avg_cost, total_cost, balance_qty, balance_cost, balance_total, date, warehouse_id, ref_type, ref_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (codigo, 'IN', float(qty), unit_cost, current_avg_cost, unit_cost * qty, float(balance_qty), balance_cost, balance_cost, fecha_ok, None, 'PURCHASE', doc_id)
                )
            conn.commit()
            
            from src.core import caching
            caching.clear_cache("src.database.repository.list_products")
            caching.clear_cache("src.database.repository.count_products")
            caching.clear_cache("src.database.repository.get_product_by_code")
            
            logger.info(f"Compra {numero_final} registrada exitosamente (doc_id: {doc_id})")
            if user_id:
                log_event(user_id, "PURCHASE_CREATE", {"numero": numero_final, "doc_id": doc_id})
            log_event(None, "DOC_PURCHASE", {"doc_id": doc_id, "numero": numero_final})
            return (doc_id, numero_final)

    except Exception as e:
        log_error(e, context={"operation": "post_purchase", "numero": numero_final}, level="ERROR")
        raise

def post_sale(numero: str | None, fecha: str | None, items: List[Dict],
              notas: str | None = None, partner_code: str | None = None,
              series: str | None = "V01", allow_negative: bool = False,
              payment_method: str | None = None, amount_paid: float | None = None,
              change_given: float | None = None, cliente_id: Optional[int] = None,
              user_id: Optional[int] = None) -> tuple[int, str | None, dict]:
    """
    Registra una VENTA con líneas y afecta stock. Soporta campos POS.
    items: [{codigo, qty, unit_price}]
    Si numero es None, se asigna por serie con get_next_number('SALE', series).
    Retorna (doc_id, numero_final, totals_dict).
    """
    from src.database.settings import get_settings
    s = get_settings()
    tax_rate = float(s.get("tax_rate") or 0.0)
    tax_included = bool(s.get("tax_included"))

    numero_final = (numero or "").strip() or get_next_number("SALE", (series or "V01").strip().upper())
    partner_id = None
    if partner_code:
        pr = get_partner_by_code(partner_code)
        if not pr:
            raise ValueError(f"Cliente '{partner_code}' no existe.")
        partner_id = pr[0]
    fecha_ok = fecha or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # cálculo subtotales (ventas)
    from decimal import Decimal, ROUND_HALF_UP
    D = Decimal
    q2 = lambda x: D(str(x)).quantize(D("0.01"), rounding=ROUND_HALF_UP)

    subtotal = D("0.00")
    for it in items:
        qty = D(str(it.get("qty") or 0))
        price = D(str(it.get("unit_price") or 0))
        subtotal += (qty * price)

    # impuestos
    neto = subtotal
    tax = D("0.00")
    total = subtotal
    if tax_rate > 0:
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

    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO documents (tipo, fecha, numero, notas, partner_id, payment_method, amount_paid, change_given) VALUES (?,?,?,?,?,?,?,?) RETURNING id",
                        ("SALE", fecha_ok, numero_final, notas, partner_id, payment_method, amount_paid, change_given))
            doc_id = int(cur.fetchone()[0])

            for it in items:
                codigo = it["codigo"]; qty = float(it["qty"])
                unit_price = float(it.get("unit_price") or 0.0)
                # línea
                cur.execute("""INSERT INTO document_lines (doc_id, codigo, qty, unit_cost, unit_price, reason)
                               VALUES (?,?,?,?,?,?)""", (doc_id, codigo, qty, None, unit_price, ""))

                # salida de stock valuada al costo promedio vigente (avg_cost almacenado en productos):
                cur.execute("SELECT cantidad, avg_cost FROM productos WHERE codigo=?", (codigo,))
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Producto '{codigo}' no existe.")
                old_qty, avg_cost = float(row[0] or 0), float(row[1] or 0)
                if (old_qty - qty) < -1e-6 and not allow_negative:
                    raise ValueError(f"Stock insuficiente para '{codigo}'. Disponible: {old_qty}, requerido: {qty}")
                new_qty = old_qty - qty
                cur.execute("UPDATE productos SET cantidad=? WHERE codigo=?", (int(new_qty), codigo))
                # registrar movimiento con unit_cost = avg_cost (para kardex)
                cur.execute("""INSERT INTO stock_movements (doc_id, codigo, qty, unit_cost, unit_price, tipo, reason, created_at)
                               VALUES (?,?,?,?,?,?,?,?)""", (doc_id, codigo, -qty, avg_cost, unit_price, "SALE", "", fecha_ok))
                # registrar en kardex usando la misma transacción/cur
                cur.execute(
                    """INSERT INTO kardex_moves (product_code, type, qty, unit_cost, avg_cost, total_cost, balance_qty, balance_cost, balance_total, date, warehouse_id, ref_type, ref_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (codigo, 'OUT', -float(qty), avg_cost, avg_cost, avg_cost * qty, float(new_qty), new_qty * avg_cost, new_qty * avg_cost, fecha_ok, None, 'SALE', doc_id)
                )
            conn.commit()

            from src.core import caching
            caching.clear_cache("src.database.repository.list_products")
            caching.clear_cache("src.database.repository.count_products")
            caching.clear_cache("src.database.repository.get_product_by_code")

    except Exception as e:
        log_error(e, context={"operation": "post_sale", "numero": numero_final}, level="ERROR")
        raise
        
    # POS Registries Hook
    if user_id and payment_method == "efectivo":
        try:
            from src.services.pos_service import get_current_session, register_cash_movement
            session = get_current_session(user_id)
            if session:
                register_cash_movement(session["id"], "sale", float(total))
        except Exception as e:
            log_error(e, context={"operation": "pos_cash_registration"})
            
    if cliente_id and payment_method == "crédito":
        try:
            from src.services.clients_service import actualizar_saldo
            actualizar_saldo(cliente_id, float(total))
        except Exception as e:
            log_error(e, context={"operation": "pos_credit_registration"})

    log_event(user_id, "DOC_SALE", {"doc_id": doc_id, "numero": numero_final})

    return doc_id, numero_final, {
        "subtotal": float(q2(subtotal)),
        "neto": float(q2(neto)),
        "impuesto": float(q2(tax)),
        "total": float(q2(total)),
        "tax_included": tax_included,
        "tax_rate": float(tax_rate),
    }

def post_adjustment(fecha: Optional[str], items: List[Dict], notas: Optional[str] = None, user_id: Optional[int] = None) -> int:
    fecha_ok = fecha or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO documents (tipo, fecha, numero, notas, partner_id) VALUES (?,?,?,?,NULL) RETURNING id",
                    ("ADJUST", fecha_ok, None, notas))
        doc_id = int(cur.fetchone()[0])

        for it in items:
            codigo = it["codigo"]; qty = float(it["qty"])
            reason = (it.get("reason") or "").strip()
            unit_cost_in = it.get("unit_cost")
            cur.execute("""INSERT INTO document_lines (doc_id, codigo, qty, unit_cost, unit_price, reason)
                           VALUES (?,?,?,?,?,?)""", (doc_id, codigo, qty, unit_cost_in, None, reason))
            cur.execute("SELECT cantidad, avg_cost FROM productos WHERE codigo=?", (codigo,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Producto '{codigo}' no existe.")
            old_qty, avg_cost = float(row[0] or 0), float(row[1] or 0)
            if qty >= 0:
                if unit_cost_in is None: unit_cost_in = avg_cost
                new_qty = old_qty + qty
                new_cost = (old_qty * avg_cost + qty * float(unit_cost_in)) / new_qty if new_qty > 0 else float(unit_cost_in)
                cur.execute("UPDATE productos SET cantidad=?, avg_cost=? WHERE codigo=?", (int(new_qty), new_cost, codigo))
                cur.execute("""INSERT INTO stock_movements (doc_id, codigo, qty, unit_cost, unit_price, tipo, reason, created_at)
                               VALUES (?,?,?,?,?,?,?,?)""", (doc_id, codigo, qty, float(unit_cost_in), None, "ADJUST+", reason, fecha_ok))
                # registrar en kardex
                cur.execute(
                    """INSERT INTO kardex_moves (product_code, type, qty, unit_cost, avg_cost, total_cost, balance_qty, balance_cost, balance_total, date, warehouse_id, ref_type, ref_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (codigo, 'IN', float(qty), float(unit_cost_in), new_cost, float(unit_cost_in) * qty, float(new_qty), new_qty * new_cost, new_qty * new_cost, fecha_ok, None, 'ADJUST', doc_id)
                )
            else:
                if (old_qty + qty) < -1e-6:
                    raise ValueError(f"Stock insuficiente para ajustar '{codigo}'. Disponible: {old_qty}, salida: {-qty}")
                new_qty = old_qty + qty
                cur.execute("UPDATE productos SET cantidad=? WHERE codigo=?", (int(new_qty), codigo))
                cur.execute("""INSERT INTO stock_movements (doc_id, codigo, qty, unit_cost, unit_price, tipo, reason, created_at)
                               VALUES (?,?,?,?,?,?,?,?)""", (doc_id, codigo, qty, avg_cost, None, "ADJUST-", reason, fecha_ok))
                # registrar en kardex
                cur.execute(
                    """INSERT INTO kardex_moves (product_code, type, qty, unit_cost, avg_cost, total_cost, balance_qty, balance_cost, balance_total, date, warehouse_id, ref_type, ref_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (codigo, 'OUT', -float(qty), avg_cost, avg_cost, avg_cost * qty, float(new_qty), new_qty * avg_cost, new_qty * avg_cost, fecha_ok, None, 'ADJUST', doc_id)
                )
        conn.commit()
        
    from src.core import caching
    caching.clear_cache("src.database.repository.list_products")
    caching.clear_cache("src.database.repository.count_products")
    caching.clear_cache("src.database.repository.get_product_by_code")
    
    log_event(user_id, "DOC_ADJUST", {"doc_id": doc_id, "items": len(items)})
    return doc_id
# =========================
# FUNCIONES CRÍTICAS NUEVAS (v2.1)
# =========================

# 1. DEVOLUCIONES - post_return() (legacy wrapper)
#
# Esta implementación histórica realizaba una devolución genérica sin
# vincularla a una venta. A partir de la v2.1 la lógica completa vive en
# ``src.services.returns_service`` y maneja casuísticas como devoluciones
# parciales, múltiples devoluciones sobre la misma venta y registro de
# nota de crédito + movimientos de caja. Conservamos aquí una función de
# compatibilidad que avisa de la deprecación y redirige al nuevo servicio.

def post_return(numero: str | None, fecha: str | None, items: List[Dict],
                notas: str | None = None, partner_code: str | None = None,
                series: str | None = "D01", user_id: Optional[int] = None) -> tuple[int, str | None]:
    """Wrapper deprecado.

    Los parámetros ``numero``/``fecha`` ya no se utilizan. Para registrar
    devoluciones nuevas se debe llamar a
    :func:`src.services.returns_service.post_return` pasando el ``sale_id``
    correspondiente, la lista de artículos y el motivo.

    Esta versión siempre lanzará ``NotImplementedError`` para forzar la
    migración.
    """
    raise NotImplementedError(
        "Use src.services.returns_service.post_return(sale_id, items, reason, user_id) "
        "instead of inventory.post_return")

# 2. MARGEN DE GANANCIA - calculate_cogs()
def calculate_cogs(doc_id: int) -> Dict:
    """
    Calcula el costo de venta (COGS) para un documento.
    Retorna: {costo_total, margen_bruto, margen_pct, utilidad_neta}
    """
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Obtener líneas del documento
        cur.execute("""SELECT l.codigo, l.qty, l.unit_price, p.avg_cost 
                       FROM document_lines l
                       JOIN productos p ON p.codigo = l.codigo
                       WHERE l.doc_id = ?""", (doc_id,))
        lines = cur.fetchall()
        
        subtotal = D("0.00")
        costo_total = D("0.00")
        
        for codigo, qty, unit_price, avg_cost in lines:
            qty = D(str(qty))
            unit_price = D(str(unit_price or 0))
            avg_cost = D(str(avg_cost or 0))
            
            subtotal += (qty * unit_price)
            costo_total += (qty * avg_cost)
        
        margen_bruto = subtotal - costo_total
        margen_pct = (margen_bruto / subtotal * 100) if subtotal > 0 else D("0.00")
        
        return {
            "subtotal": float(subtotal),
            "costo_total": float(costo_total),
            "margen_bruto": float(margen_bruto),
            "margen_pct": float(margen_pct),
            "cantidad_lineas": len(lines)
        }

# 3. DESCUENTOS - apply_discount()
def apply_discount(doc_id: int, discount_pct: float, reason: str = "Descuento manual") -> Dict:
    """
    Aplica descuento a un documento.
    Retorna: {descuento_total, total_final}
    """
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Obtener total actual del documento
        cur.execute("""SELECT SUM(l.qty * l.unit_price) as total
                       FROM document_lines l
                       WHERE l.doc_id = ?""", (doc_id,))
        row = cur.fetchone()
        total = D(str(row[0] or 0))
        
        discount_amount = (total * D(str(discount_pct)) / D("100")).quantize(D("0.01"), rounding=ROUND_HALF_UP)
        total_final = total - discount_amount
        
        # Registrar descuento en auditoría
        log_event(None, "DISCOUNT_APPLIED", {"doc_id": doc_id, "discount_pct": discount_pct, "amount": float(discount_amount)})
        
        return {
            "subtotal": float(total),
            "descuento_pct": discount_pct,
            "descuento_total": float(discount_amount),
            "total_final": float(total_final)
        }

# 4. CRÉDITO - get_customer_statement()
def get_customer_statement(partner_code: str, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict:
    """
    Obtiene estado de cuenta del cliente (deuda, pagos, etc.)
    """
    pr = get_partner_by_code(partner_code)
    if not pr:
        raise ValueError(f"Cliente '{partner_code}' no existe.")
    
    partner_id = pr[0]
    
    with get_connection() as conn:
        cur = conn.cursor()
        
        where = ["d.partner_id = ?"]
        params = [partner_id]
        if date_from:
            where.append("d.fecha >= ?")
            params.append(date_from)
        if date_to:
            where.append("d.fecha <= ?")
            params.append(date_to)
        
        where_sql = " AND ".join(where)
        
        # Obtener documentos de venta
        cur.execute(f"""SELECT d.id, d.numero, d.fecha, 
                               SUM(l.qty * l.unit_price) as total
                        FROM documents d
                        LEFT JOIN document_lines l ON d.id = l.doc_id
                        WHERE d.tipo = 'SALE' AND {where_sql}
                        GROUP BY d.id
                        ORDER BY d.fecha DESC""", params)
        
        sales = cur.fetchall()
        total_facturado = sum(float(s[3] or 0) for s in sales)
        
        return {
            "cliente": pr[1],  # nombre
            "partner_code": partner_code,
            "total_facturado": float(D(str(total_facturado)).quantize(D("0.01"), rounding=ROUND_HALF_UP)),
            "documentos": len(sales),
            "facturas": [
                {
                    "numero": s[1],
                    "fecha": s[2],
                    "monto": float(D(str(s[3] or 0)).quantize(D("0.01"), rounding=ROUND_HALF_UP))
                }
                for s in sales
            ]
        }

def import_from_file(filepath: str, user_id: Optional[int] = None) -> dict:
    """
    Importa masivamente productos desde un archivo (CSV o Excel) 
    con flexibilidad semántica en la cabecera.
    """
    import os
    import csv
    from src.database.connection import get_connection
    from src.core import caching
    from src.services.audit import log_event
    
    ext = os.path.splitext(filepath)[1].lower()
    
    insertados = 0
    actualizados = 0
    errores = []
    total = 0
    rows = []
    
    if ext == '.csv':
        try:
            with open(filepath, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                headers = [h.lower().strip() for h in (reader.fieldnames or [])]
                for row_dict in reader:
                    rows.append({k.lower().strip(): v for k, v in row_dict.items() if k})
        except Exception as e:
            return {"insertados": 0, "actualizados": 0, "errores": [{"fila": 0, "error": f"Error leyendo CSV: {e}"}], "total": 0}
            
    elif ext == '.xlsx':
        try:
            import openpyxl
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
            ws = wb.active
            headers = []
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i == 0:
                    headers = [str(h).lower().strip() if h else "" for h in row]
                    continue
                row_dict = {}
                for j, val in enumerate(row):
                    if j < len(headers) and headers[j]:
                        row_dict[headers[j]] = val
                rows.append(row_dict)
        except Exception as e:
            return {"insertados": 0, "actualizados": 0, "errores": [{"fila": 0, "error": f"Error leyendo XLSX: {e}"}], "total": 0}
    else:
        return {"insertados": 0, "actualizados": 0, "errores": [{"fila": 0, "error": "Formato no soportado"}], "total": 0}
        
    with get_connection() as conn:
        cur = conn.cursor()
        for i, row in enumerate(rows, start=1):
            total += 1
            try:
                codigo = str(row.get("codigo", row.get("code", row.get("sku", "")))).strip()
                if not codigo:
                    errores.append({"fila": i, "error": "Falta código del producto"})
                    continue
                    
                nombre = str(row.get("nombre", row.get("name", row.get("producto", "")))).strip()
                if not nombre:
                    errores.append({"fila": i, "error": "Falta nombre del producto"})
                    continue
                    
                categoria = str(row.get("categoria", row.get("category", ""))).strip()
                
                try: precio = float(row.get("precio", row.get("price", 0)) or 0)
                except: precio = 0.0
                
                try: cantidad = int(float(row.get("cantidad", row.get("qty", row.get("stock", 0))) or 0))
                except: cantidad = 0
                
                try: avg_cost = float(row.get("avg_cost", row.get("costo", row.get("cost", 0))) or 0)
                except: avg_cost = 0.0
                
                try: stock_minimo = int(float(row.get("stock_minimo", row.get("min_stock", 5)) or 5))
                except: stock_minimo = 5
                
                # UPSERT paramétricamente
                cur.execute("SELECT id FROM productos WHERE codigo=? AND activo=1", (codigo,))
                existe = cur.fetchone()
                
                if existe:
                    cur.execute("""
                        UPDATE productos 
                        SET nombre=?, categoria=?, precio=?, cantidad=?, avg_cost=?, stock_minimo=?
                        WHERE codigo=?
                    """, (nombre, categoria, precio, cantidad, avg_cost, stock_minimo, codigo))
                    actualizados += 1
                else:
                    cur.execute("""
                        INSERT INTO productos (codigo, nombre, categoria, precio, cantidad, avg_cost, stock_minimo)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (codigo, nombre, categoria, precio, cantidad, avg_cost, stock_minimo))
                    insertados += 1
            except Exception as e:
                errores.append({"fila": i, "error": str(e)})
        conn.commit()
    
    # Invalidate caches
    from src.core import caching
    caching.invalidate_prefix("src.database.repository.list_products")
    caching.invalidate_prefix("src.database.repository.count_products")
    caching.invalidate_prefix("src.database.repository.get_product_by_code")
    
    if user_id and (insertados > 0 or actualizados > 0):
        log_event(user_id, "PRODUCT_IMPORT_FILE", {"path": os.path.basename(filepath), "inserts": insertados, "updates": actualizados})
        
    return {
        "insertados": insertados,
        "actualizados": actualizados,
        "errores": errores,
        "total": total
    }