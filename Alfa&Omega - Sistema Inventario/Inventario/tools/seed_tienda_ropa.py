"""Script de Semilla - Datos de Prueba: Tienda de Ropa Colombiana"""

import os
import sys

# Agregar la raíz del proyecto para importar src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import get_connection
from src.services.inventory import add_product
from src.services.partners import create_partner
import random


def seed_tienda_ropa():
    print("================================================================")
    print("🌱 INICIANDO SEED: TIENDA DE ROPA (COLOMBIA)")
    print("================================================================\n")
    
    print("[+] 1. Creando Base de Clientes...")
    
    # 3 Clientes tipo
    clientes_data = [
        {"code": "CLI-1001", "name": "María Rodríguez", "kind": "CUSTOMER", "tax_id": "101010101", "phone": "3001234567", "city": "Medellín"},
        {"code": "CLI-1002", "name": "Carlos Martínez", "kind": "CUSTOMER", "tax_id": "202020202", "phone": "3129876543", "city": "Bogotá"},
        {"code": "CLI-1003", "name": "Ana Gómez", "kind": "CUSTOMER", "tax_id": "303030303", "phone": "3154567890", "city": "Cali"}
    ]
    
    for c in clientes_data:
        try:
            create_partner(**c)
            print(f"    ✓ Cliente agregado: {c['name']}")
        except Exception as e:
            # Captura si el contacto ya existía por código
            print(f"    ⚠️ Omitido {c['name']} (Posible duplicado: {e})")

    print("\n[+] 2. Creando Proveedores...")
    proveedores_data = [
        {"code": "PROV-TXT-01", "name": "Confecciones del Valle", "kind": "SUPPLIER", "tax_id": "900111222-1", "phone": "3201112233", "city": "Cali"},
        {"code": "PROV-TXT-02", "name": "Distribuidora Textil Santa Fe", "kind": "SUPPLIER", "tax_id": "800999888-2", "phone": "3109998877", "city": "Bogotá"}
    ]
    
    for p in proveedores_data:
        try:
            create_partner(**p)
            print(f"    ✓ Proveedor agregado: {p['name']}")
        except Exception as e:
            print(f"    ⚠️ Omitido {p['name']} (Posible duplicado: {e})")

    print("\n[+] 3. Poblando Catálogo de Productos...")
    
    categorias = ["Hombre", "Mujer", "Niños", "Accesorios"]
    
    # Lista de 20 productos realistas en la moneda Colombiana COP
    productos = [
        ("TSHIRT-H-01", "Camiseta Básica Hombre (Blanca)", "Hombre", 35000),
        ("TSHIRT-H-02", "Camiseta Básica Hombre (Negra)", "Hombre", 35000),
        ("JEAN-H-01", "Jean Slim Fit Hombre", "Hombre", 120000),
        ("JEAN-M-01", "Jean Skinny Mujer Tiro Alto", "Mujer", 135000),
        ("DRESS-M-01", "Vestido Casual Otoño", "Mujer", 95000),
        ("BLUSA-M-01", "Blusa Manga Corta Estampada", "Mujer", 45000),
        ("BLUSA-M-02", "Blusa de Seda Formal", "Mujer", 85000),
        ("SPORT-U-01", "Pantalón Deportivo Jogger", "Hombre", 65000),
        ("JACKET-U-01", "Chaqueta Impermeable Cortavientos", "Hombre", 150000),
        ("JACKET-M-01", "Chaqueta de Jean Clásica", "Mujer", 140000),
        ("SOCKS-U-01", "Medias Tobilleras x3", "Accesorios", 25000),
        ("UNDW-H-01", "Bóxer Hombre x3", "Hombre", 45000),
        ("UNDW-M-01", "Set Ropa Interior Encaje", "Mujer", 60000),
        ("SWIM-M-01", "Vestido de Baño Dos Piezas", "Mujer", 95000),
        ("SHOES-H-01", "Zapatos Casuales Urbanos", "Hombre", 160000),
        ("KIDS-T-01", "Camiseta Estampada Niño", "Niños", 28000),
        ("KIDS-P-01", "Pantalón Jean Niño", "Niños", 65000),
        ("KIDS-D-01", "Vestido Niña Primaveral", "Niños", 75000),
        ("BELT-01", "Cinturón Cuero Reversible", "Accesorios", 45000),
        ("CAP-01", "Gorra Urbana Unisex", "Accesorios", 35000)
    ]
    
    agregados = 0
    for code, name, cat, price in productos:
        # Stock inicial realista aleatorio entre 5 y 30
        stock = random.randint(5, 30)
        try:
            # Utilizamos los métodos seguros del ERP para preservar el log de BD
            add_product(
                codigo=code,
                nombre=name,
                categoria=cat,
                precio=float(price),
                cantidad=stock,
                avg_cost=price * 0.60 # Margen estimado del 40%
            )
            agregados += 1
        except Exception as e:
            print(f"    ⚠️ Omitido {name} (Error: {e})")
            
    print(f"    ✓ {agregados} productos ingresados al inventario.")
    
    print("\n================================================================")
    print("✅ DATOS DE SEMILLA CARGADOS EXITOSAMENTE")
    print("================================================================")
    print("La base de datos original ahora contiene datos de ejemplo funcionales para")
    print("Punto de Venta, Catálogo, CRM y Órdenes de Compra.")

if __name__ == "__main__":
    seed_tienda_ropa()
