"""Script para resetear la base de datos a estado de producción/demo limpia."""

import sys
import os
import shutil
from datetime import datetime

# Añadir raíz al path para poder importar src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import get_connection

def perform_reset():
    db_path = os.path.join(
        os.path.dirname(__file__), '..', 'src', 'data', 'inventario.db'
    )
    db_path = os.path.abspath(db_path)

    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en '{db_path}'")
        return

    print("================================================================")
    print("⚠️  ATENCIÓN: PREPARACIÓN PARA PRODUCCIÓN / DEMO LIMPIA")
    print("================================================================")
    print("Este script ELIMINARÁ TODOS los datos operacionales de la base de datos.")
    print("Se conservará ÚNICAMENTE el usuario 'admin' y la estructura base.")
    print("Se creará un backup automático antes de proceder.\n")
    
    resp = input("Para continuar, escribe la palabra 'RESET': ")
    if resp.strip() != "RESET":
        print("🔴 Operación cancelada por el usuario.")
        return

    # 1. Backup Automático
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(db_path)), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"inventario_pre_reset_{timestamp}.db")
    
    print("\n[+] 1. Creando backup de seguridad estricto...")
    shutil.copy2(db_path, backup_path)
    print(f"    ✓ Backup asegurado en: {backup_path}")

    # 2 al 7. Borrado y reseteo
    print("[+] 2. Vaciando tablas...")
    with get_connection() as conn:
        cur = conn.cursor()
        
        try:
            # Documentos y Kardex
            cur.execute("DELETE FROM document_lines")
            cur.execute("DELETE FROM documents")
            cur.execute("DELETE FROM kardex_moves")
            print("    ✓ Movimientos de Kardex y Documentos eliminados.")
            
            # Catálogo y Contactos
            cur.execute("DELETE FROM productos")
            cur.execute("DELETE FROM partners")
            print("    ✓ Catálogo de productos y lista de contactos vaciados.")
            
            # Usuarios
            cur.execute("DELETE FROM users WHERE username != 'admin'")
            print("    ✓ Usuarios adicionales eliminados (Excepto 'admin').")
            
            # Caja y sesiones
            cur.execute("DELETE FROM cash_movements")
            cur.execute("DELETE FROM cash_sessions")
            cur.execute("DELETE FROM returns")
            cur.execute("DELETE FROM return_lines")
            print("    ✓ Movimientos de caja y devoluciones eliminados.")

            # Secuencias
            tables = [
                'document_lines', 'documents', 'kardex_moves', 'productos', 
                'partners', 'users', 'cash_movements', 'cash_sessions', 
                'returns', 'return_lines'
            ]
            placeholders = ','.join(['?'] * len(tables))
            cur.execute(f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})", tables)
            print("    ✓ IDs auto-incrementables reseteados a 0.")
            
            conn.commit()
            print("\n✅ LIMPIEZA EXITOSA. Sistema listo para cliente final.")
        except Exception as e:
            conn.rollback()
            print(f"\n❌ Ocurrió un error crítico durante el borrado: {e}")
            print("    La base de datos original ha sido restaurada (Rollback ejecutado).")

if __name__ == "__main__":
    perform_reset()
