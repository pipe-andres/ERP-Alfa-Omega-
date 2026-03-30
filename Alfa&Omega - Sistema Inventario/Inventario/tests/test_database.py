from src.database.connection import init_db, get_connection, DB_ENGINE


def test_db_initialization_and_tables():
    init_db()
    with get_connection() as conn:
        cur = conn.cursor()
        if DB_ENGINE == 'postgres':
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            tables = [r[0] for r in cur.fetchall()]
        else:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
        assert 'productos' in tables
