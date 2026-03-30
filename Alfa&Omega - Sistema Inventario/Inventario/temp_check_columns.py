from src.database.connection import get_connection
conn = get_connection()
cursor = conn.execute("PRAGMA table_info(cash_movements)")
for row in cursor.fetchall():
    print(row)