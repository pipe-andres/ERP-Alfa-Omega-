"""Script para crear una base de datos limpia para distribución en .exe"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def create_dist_db():
    print("================================================================")
    print("📦 CREADOR DE BASE DE DATOS PARA DISTRIBUCIÓN (CLEAN)")
    print("================================================================\n")
    
    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dist'))
    os.makedirs(dist_dir, exist_ok=True)
    db_path = os.path.join(dist_dir, "inventario_clean.db")
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print("[*] Base de datos anterior eliminada.")
        
    print(f"[*] Inicializando nuevo schema en: {db_path}")
    
    # Redirigir la base de datos a dist
    import src.database.connection as db_conn
    from src.core.auth import _hash_password
    
    db_conn.DB_PATH = db_path
    os.environ["DB_PATH"] = db_path
    
    # Forzar reconexión limpia
    if hasattr(db_conn, '_conn'):
        db_conn._conn = None
        
    db_conn.init_db()
    print("[✓] Schema base creado exitosamente.")
    
    print("[*] Limpiando datos de prueba (si init_db generó alguno)...")
    with db_conn.get_connection() as conn:
        cur = conn.cursor()
        
        # Limpiar datos iniciales que pudo crear init_db()
        tablas_a_limpiar = [
            "document_lines", "documents", "kardex_moves", "productos",
            "partners", "cash_movements", "cash_sessions", "returns",
            "return_lines", "tenant_plans", "tenants", "_seed_tracker"
        ]
        
        for tabla in tablas_a_limpiar:
            try:
                cur.execute(f"DELETE FROM {tabla}")
            except Exception:
                pass
        
        # Secuencias
        tables = [
            'document_lines', 'documents', 'kardex_moves', 'productos', 
            'partners', 'users', 'cash_movements', 'cash_sessions', 
            'returns', 'return_lines', 'roles'
        ]
        placeholders = ','.join(['?'] * len(tables))
        cur.execute(f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})", tables)
        
        print("[✓] Tablas operacionales completamente vaciadas.")
        
        print("[*] Configurando roles y administrador sembrados...")
        
        # Roles básicos (asumiendo tabla roles si existe)
        try:
            cur.execute("DELETE FROM roles")
            cur.execute("INSERT INTO roles (id, name, description) VALUES (1, 'ADMIN', 'Acceso total')")
            cur.execute("INSERT INTO roles (id, name, description) VALUES (2, 'USER', 'Acceso estándar')")
            cur.execute("INSERT INTO roles (id, name, description) VALUES (3, 'AUDITOR', 'Solo lectura')")
            print("    - Roles: ADMIN, USER, AUDITOR creados correctamentes.")
        except Exception:
            pass
            
        # Limpiar usuarios y crear solo admin
        cur.execute("DELETE FROM users")
        hashed = _hash_password("admin123")
        try:
            cur.execute(
                "INSERT INTO users (username, name, pass_hash, role_id, active) VALUES (?, ?, ?, ?, ?)",
                ('admin', 'Administrador Principal', hashed, 1, 1)
            )
        except Exception:
            # Fallback en caso de que la tabla de auth local no tenga role_id
            cur.execute(
                "INSERT INTO users (username, name, pass_hash, active) VALUES (?, ?, ?, ?)",
                ('admin', 'Administrador Principal', hashed, 1)
            )
        print("    - Usuario 'admin' (clave: admin123) creado exitosamente.")
        
        conn.commit()
    
    # Validar
    print("\n[*] Validando estado final de base de datos de producción...")
    with db_conn.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM productos")
        p_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users")
        u_count = cur.fetchone()[0]
        cur.execute("SELECT username FROM users LIMIT 1")
        admin_usr = cur.fetchone()[0]
        
    print("\n================================================================")
    print("✅ BASE DE DATOS DE DISTRIBUCIÓN LISTA")
    print("================================================================")
    print(f"Ruta       : dist/inventario_clean.db")
    print(f"Productos  : {p_count} (Esperado: 0)")
    print(f"Usuarios   : {u_count} (Esperado: 1)")
    print(f"Login      : {admin_usr} / admin123")
    print("La base de datos se puede empaquetar dentro de un .exe.")

if __name__ == '__main__':
    create_dist_db()
