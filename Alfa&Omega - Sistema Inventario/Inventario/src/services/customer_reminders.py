from typing import Dict, List
from src.database.connection import get_connection
from src.services.notificaciones import _send, get_notif_config, _base_css

def get_clientes_sin_comprar(dias_umbral: int = 30) -> List[Dict]:
    with get_connection() as conn:
        cur = conn.cursor()
        # Clientes activos, con >= 2 ventas históricas
        # cuya máxima fecha de venta fue hace >= dias_umbral
        cur.execute("""
            SELECT 
                p.id as partner_id,
                p.name as nombre,
                p.email as email,
                MAX(d.fecha) as ultima_compra,
                CAST(julianday('now') - julianday(MAX(d.fecha)) AS INTEGER) as dias_sin_comprar,
                COUNT(DISTINCT d.id) as total_compras_historicas,
                SUM(dl.qty * dl.unit_price) as total_gastado
            FROM partners p
            JOIN documents d ON p.id = d.partner_id
            JOIN document_lines dl ON d.id = dl.doc_id
            WHERE p.kind = 'CUSTOMER' AND d.tipo = 'SALE' AND p.active = 1
            GROUP BY p.id
            HAVING COUNT(DISTINCT d.id) >= 2 
               AND CAST(julianday('now') - julianday(MAX(d.fecha)) AS INTEGER) >= ?
            ORDER BY dias_sin_comprar DESC
        """, (dias_umbral,))
        rows = cur.fetchall()
        
    res = []
    for r in rows:
        res.append({
            "partner_id": r[0],
            "nombre": r[1],
            "email": r[2],
            "ultima_compra": r[3],
            "dias_sin_comprar": r[4],
            "total_compras_historicas": r[5],
            "total_gastado": float(r[6]) if r[6] else 0.0
        })
    return res

def generar_mensaje_recordatorio(partner_id: int) -> str:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.name, MAX(d.fecha), CAST(julianday('now') - julianday(MAX(d.fecha)) AS INTEGER)
            FROM partners p
            JOIN documents d ON p.id = d.partner_id
            WHERE p.id = ? AND d.tipo = 'SALE'
        """, (partner_id,))
        row = cur.fetchone()
        
    if not row or not row[0]:
        return ""
        
    nombre = row[0]
    # La DB podría guardar la fecha en strings como ISO, pero para lectura rápida tomamos solo subcadenas si fuese necesario.
    fecha = str(row[1])[:10] if row[1] else "hace un tiempo"
    dias = row[2]
    
    return (
        f"Hola {nombre}, hace {dias} días que no te vemos...\n"
        f"Tu última compra fue el {fecha}.\n"
        f"¡Te esperamos en Alfa & Omega!"
    )

def enviar_recordatorios(dias_umbral: int = 30) -> Dict:
    clientes_elegibles = get_clientes_sin_comprar(dias_umbral)
    
    cfg = get_notif_config()
    activas = int(cfg.get("activo") or 0)
    
    enviados = 0
    sin_email = 0
    errores = []
    
    if not activas:
        return {
            "total_elegibles": len(clientes_elegibles),
            "enviados": 0,
            "sin_email": sum(1 for c in clientes_elegibles if not c["email"]),
            "errores": ["Notificaciones desactivadas (dry-run)"]
        }
        
    for c in clientes_elegibles:
        email = c["email"]
        if not email:
            sin_email += 1
            continue
            
        html_msg = generar_mensaje_recordatorio(c["partner_id"])
        
        # Envolviendo para un correo decente con firma HTML del sistema
        html_body = f"""<!DOCTYPE html>
        <html>
        <head>{_base_css()}</head>
        <body>
            <div class='wrap'>
                <div class='body'>
                    {html_msg.replace(chr(10), '<br>')}
                </div>
            </div>
        </body>
        </html>"""
        
        # Copiamos la config para sobreescribir destinos de 1x1
        client_cfg = cfg.copy()
        client_cfg["to_emails"] = email
        
        try:
            _send(client_cfg, "¡Te extrañamos en Alfa & Omega!", html_body)
            enviados += 1
        except Exception as e:
            errores.append({"partner_id": c["partner_id"], "error": str(e)})
            
    return {
        "total_elegibles": len(clientes_elegibles),
        "enviados": enviados,
        "sin_email": sin_email,
        "errores": errores
    }
