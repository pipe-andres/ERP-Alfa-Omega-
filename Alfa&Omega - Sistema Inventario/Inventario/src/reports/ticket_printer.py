import os
import datetime

def imprimir_ticket_venta(doc_id: int, products: list, total: float, payment_method: str, 
                          change: float, amount_paid: float, 
                          business_name: str = "Alfa & Omega",
                          date_str: str = None, ticket_number: str = "") -> str:
    """
    Genera un ticket de venta en formato térmico (58mm, 32 caracteres max.).
    products: lista de dicts con 'qty', 'nombre', 'unit_price'
    Retorna la ruta del archivo generado.
    """
    if date_str is None:
        date_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
    # Ancho típico de ticket 58mm: 32 caracteres
    W = 32
    
    lines = []
    lines.append(business_name.center(W))
    lines.append("=" * W)
    lines.append(f"Ticket: {ticket_number}".center(W))
    lines.append(f"Fecha: {date_str}".center(W))
    lines.append("-" * W)
    lines.append("CANT DESCRIPCION      IMPORTE")
    
    for p in products:
        qty = float(p.get('qty', 1))
        # Recortar nombre a 16 caracteres para que encaje
        name = str(p.get('nombre', 'Item'))[:16].ljust(16)
        price = float(p.get('unit_price', 0))
        subt = qty * price
        
        qty_str = f"{qty:g}".ljust(4)
        subt_str = f"${subt:.2f}".rjust(10)
        lines.append(f"{qty_str} {name} {subt_str}")
        
    lines.append("-" * W)
    lines.append(f"TOTAL:".ljust(16) + f"${total:.2f}".rjust(16))
    lines.append(f"PAGA CON:".ljust(16) + f"${amount_paid:.2f}".rjust(16))
    lines.append(f"VUELTO:".ljust(16) + f"${change:.2f}".rjust(16))
    lines.append(f"METODO: {payment_method}".center(W))
    lines.append("=" * W)
    lines.append("¡Gracias por su compra!".center(W))
    lines.append("\n\n\n\n") # Espacio para el corte de papel

    ticket_text = "\n".join(lines)
    
    # Modo Fallback Universal: Guardar a .txt
    # En producción se enviaría a: from escpos.printer import Usb; p = Usb(0x04b8,0x0202); p.text(ticket_text)
    import tempfile
    tickets_dir = os.path.join(tempfile.gettempdir(), "alfa_omega_tickets")
    os.makedirs(tickets_dir, exist_ok=True)
    
    path = os.path.join(tickets_dir, f"ticket_{ticket_number or doc_id}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(ticket_text)
        
    # Intentar mandarlo directo a impresora default en Windows (opcional, requiere win32print pero no queremos crashear si no está)
    try:
        os.startfile(path, "print")
    except Exception:
        pass
        
    return path
