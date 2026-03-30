import sys
sys.path.insert(0, '.')
from src.database.connection import get_connection

with get_connection() as conn:
    print('--- PARTNERS CUSTOMER ---')
    rows = conn.execute("SELECT id, code, name, kind FROM partners WHERE kind='CUSTOMER'").fetchall()
    for r in rows:
        print(tuple(r))
    print('--- CLIENTES LEGACY ---')
    rows2 = conn.execute('SELECT * FROM clientes').fetchall()
    for r in rows2:
        print(tuple(r))
