from typing import Optional, Dict, List, Any
from src.database.connection import get_connection

def registrar_cliente(nombre: str, telefono: Optional[str] = None, saldo_inicial: float = 0.0) -> int:
    """Registra un nuevo cliente para POS y ventas a crédito."""
    if not nombre or not nombre.strip():
        raise ValueError("El nombre del cliente no puede estar vacío.")
    
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO clientes (nombre, telefono, saldo) VALUES (?, ?, ?)",
            (nombre.strip(), telefono, float(saldo_inicial))
        )
        conn.commit()
        return cur.lastrowid

def get_clientes() -> List[Dict[str, Any]]:
    """Devuelve listado de todos los clientes."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, telefono, saldo FROM clientes ORDER BY nombre ASC")
        rows = cur.fetchall()
        return [
            {"id": r[0], "nombre": r[1], "telefono": r[2], "saldo": r[3]}
            for r in rows
        ]

def get_cliente(cliente_id: int) -> Optional[Dict[str, Any]]:
    """Devuelve datos de un cliente específico."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, telefono, saldo FROM clientes WHERE id = ?", (cliente_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "nombre": row[1], "telefono": row[2], "saldo": row[3]}

def actualizar_saldo(cliente_id: int, monto_variacion: float) -> float:
    """Actualiza el saldo de un cliente (positivo aumenta la deuda, negativo la reduce)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT saldo FROM clientes WHERE id = ?", (cliente_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Cliente con id {cliente_id} no encontrado.")
            
        nuevo_saldo = row[0] + float(monto_variacion)
        cur.execute("UPDATE clientes SET saldo = ? WHERE id = ?", (nuevo_saldo, cliente_id))
        conn.commit()
        return nuevo_saldo
