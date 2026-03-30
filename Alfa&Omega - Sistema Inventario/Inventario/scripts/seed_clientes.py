import sys
sys.path.insert(0, '../')
sys.path.insert(0, './Inventario')
from src.database.connection import get_connection

clientes = [
    ('CUST-001', 'María García', '3001234567', 'maria@email.com'),
    ('CUST-002', 'Juan Pérez', '3109876543', 'juan@email.com'),
    ('CUST-003', 'Carlos López', '3205551234', None),
]

with get_connection() as conn:
    for code, name, phone, email in clientes:
        conn.execute(
            """
            INSERT OR IGNORE INTO partners
            (code, kind, name, phone, email, active, credit_limit, credit_balance)
            VALUES (?, 'CUSTOMER', ?, ?, ?, 1, 0.0, 0.0)
            """,
            (code, name, phone, email)
        )
    conn.commit()
print('Clientes de prueba insertados.')
