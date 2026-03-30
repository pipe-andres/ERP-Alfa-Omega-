"""
src/database/migrations.py - Sistema de migraciones de BD.

Proporciona funciones para crear/verificar tablas sin perder datos.
Ejecutable desde CLI o durante init.
"""
from .connection import get_connection, init_db, init_rbac


def create_tables_if_not_exist():
    """
    Crea todas las tablas necesarias si no existen.
    Seguro para ejecutar múltiples veces (no elimina datos).
    """
    with get_connection() as conn:
        # Ejecutar init_db que ya crea todo si no existe
        init_db()
        print("✓ All tables verified/created successfully")


def reset_rbac_only():
    """
    Reinicializa solo las tablas de RBAC (roles, permisos, usuarios).
    Útil para reparar permisos. NO elimina datos de otros módulos.
    """
    with get_connection() as conn:
        init_rbac(conn)
        print("✓ RBAC tables reset successfully")


def get_table_info():
    """
    Retorna información sobre las tablas existentes (debug).
    """
    from .connection import _table_exists
    
    with get_connection() as conn:
        cur = conn.cursor()
        
        tables = [
            "usuarios", "roles", "permissions", "role_permissions", "user_roles",
            "productos", "documents", "document_lines", "stock_movements",
            "partners", "doc_series", "historial", "audit_log"
        ]
        
        info = {}
        for table in tables:
            if _table_exists(conn, table):
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                info[table] = {"exists": True, "rows": count}
            else:
                info[table] = {"exists": False, "rows": 0}
        
        return info


if __name__ == "__main__":
    print("Initializing database migrations...")
    create_tables_if_not_exist()
    print("\nDatabase info:")
    info = get_table_info()
    for table, status in info.items():
        if status["exists"]:
            print(f"  ✓ {table}: {status['rows']} rows")
        else:
            print(f"  - {table}: not created")
