"""
SCRIPT DE ÍNDICES DE BASE DE DATOS
Optimización completa para queries críticas
"""

import sqlite3
from pathlib import Path

# Ubicación de la BD
DB_PATH = Path(__file__).parent.parent / "data" / "inventario.db"

# Índices críticos iden tificados del análisis de queries
INDEXES = [
    # Búsquedas por código (MUY FRECUENTES)
    ("CREATE INDEX IF NOT EXISTS idx_productos_codigo ON productos(codigo);",
     "Búsqueda rápida de productos por código"),
    
    # Auditoría - búsquedas por usuario y acción
    ("CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);",
     "Auditoría por usuario"),
    
    ("CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);",
     "Auditoría por acción"),
    
    ("CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);",
     "Auditoría por fecha"),
    
    # Documentos - búsquedas por fecha y tipo
    ("CREATE INDEX IF NOT EXISTS idx_documents_tipo ON documents(tipo);",
     "Búsqueda de documentos por tipo"),
    
    ("CREATE INDEX IF NOT EXISTS idx_documents_fecha ON documents(fecha);",
     "Búsqueda de documentos por fecha"),
    
    ("CREATE INDEX IF NOT EXISTS idx_documents_partner_id ON documents(partner_id);",
     "Búsqueda de documentos por proveedor"),
    
    # Usuarios - búsquedas por username
    ("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
     "Autenticación rápida"),
    
    # Líneas de documento - búsquedas por documento
    ("CREATE INDEX IF NOT EXISTS idx_document_lines_doc_id ON document_lines(doc_id);",
     "Líneas de documento"),
    
    ("CREATE INDEX IF NOT EXISTS idx_document_lines_codigo ON document_lines(codigo);",
     "Búsqueda por producto en líneas"),
    
    # Movimientos de stock
    ("CREATE INDEX IF NOT EXISTS idx_stock_movements_doc_id ON stock_movements(doc_id);",
     "Movimientos por documento"),
    
    ("CREATE INDEX IF NOT EXISTS idx_stock_movements_codigo ON stock_movements(codigo);",
     "Movimientos por producto"),
    
    ("CREATE INDEX IF NOT EXISTS idx_stock_movements_tipo ON stock_movements(tipo);",
     "Movimientos por tipo"),
    
    # Kardex
    ("CREATE INDEX IF NOT EXISTS idx_kardex_moves_product_code ON kardex_moves(product_code);",
     "Kardex por producto"),
    
    ("CREATE INDEX IF NOT EXISTS idx_kardex_moves_date ON kardex_moves(date);",
     "Kardex por fecha"),
    
    ("CREATE INDEX IF NOT EXISTS idx_kardex_moves_type ON kardex_moves(type);",
     "Kardex por tipo"),
    
    # Partners
    ("CREATE INDEX IF NOT EXISTS idx_partners_code ON partners(code);",
     "Búsqueda de proveedores por código"),
]


def create_indexes():
    """Crea todos los índices críticos."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        
        print("╔════════════════════════════════════════════════════════╗")
        print("║ CREANDO ÍNDICES DE BASE DE DATOS                      ║")
        print("╚════════════════════════════════════════════════════════╝\n")
        
        created_count = 0
        for sql, description in INDEXES:
            try:
                cur.execute(sql)
                created_count += 1
                print(f"✓ {description}")
            except sqlite3.OperationalError as e:
                if "already exists" in str(e):
                    print(f"• {description} (ya existe)")
                else:
                    print(f"✗ {description}: {e}")
        
        conn.commit()
        
        print(f"\n╔════════════════════════════════════════════════════════╗")
        print(f"║ Índices creados: {created_count}/{len(INDEXES):<35} ║")
        print(f"║ Base de datos optimizada para queries críticas        ║")
        print(f"╚════════════════════════════════════════════════════════╝")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando índices: {e}")
        return False
    finally:
        conn.close()


def verify_indexes():
    """Verifica que los índices fueron creados."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = cur.fetchall()
        
        print(f"\n✓ Total de índices en BD: {len(indexes)}")
        for idx in indexes:
            print(f"  - {idx[0]}")
        
        return True
    finally:
        conn.close()


if __name__ == "__main__":
    if DB_PATH.exists():
        if create_indexes():
            verify_indexes()
    else:
        print(f"❌ Base de datos no encontrada en {DB_PATH}")
