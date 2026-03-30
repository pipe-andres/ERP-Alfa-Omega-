import sys, os
sys.path.insert(0, '.')
from src.database.connection import get_connection

print("=== CASH_MOVEMENTS ===")
with get_connection() as conn:
    rows = conn.execute('PRAGMA table_info(cash_movements)').fetchall()
    for r in rows: print(tuple(r))

print("\n=== CASH_SESSIONS ===")
with get_connection() as conn:
    rows = conn.execute('PRAGMA table_info(cash_sessions)').fetchall()
    for r in rows: print(tuple(r))
