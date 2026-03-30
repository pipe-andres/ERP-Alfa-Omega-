"""Smoke test: verificar que ORM async funciona."""
import asyncio
import os
import sys
import uuid
from pathlib import Path

# Añadir el directorio padre (raíz del proyecto) al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Asegurar que el entorno esté inicializado
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///./data/inventario_temp.db')

from src.database.orm import get_async_session
from src.database.models import Product
from sqlalchemy import select, func

async def main():
    print("=" * 60)
    print("SMOKE TEST: Verificar ORM async + Alembic")
    print("=" * 60)
    
    # Use UUID to avoid constraint violations
    test_codigo = f"TEST-{uuid.uuid4().hex[:8]}"
    
    # 1. Insertar un producto de prueba
    print(f"\n1. Insertando producto de prueba ({test_codigo})...")
    try:
        async with get_async_session() as session:
            product = Product(codigo=test_codigo, nombre="Producto Prueba", precio=99.99, cantidad=10)
            session.add(product)
            await session.commit()
            print("✓ Inserción exitosa")
    except Exception as e:
        print(f"✗ Error en inserción: {e}")
        return False
    
    # 2. Leer el producto insertado
    print("\n2. Leyendo producto...")
    try:
        async with get_async_session() as session:
            stmt = select(Product).where(Product.codigo == test_codigo)
            result = await session.execute(stmt)
            prod = result.scalar_one_or_none()
            if prod:
                print(f"✓ Lectura exitosa: {prod.codigo} - {prod.nombre} (precio: ${prod.precio})")
            else:
                print("✗ Producto no encontrado")
                return False
    except Exception as e:
        print(f"✗ Error en lectura: {e}")
        return False
    
    # 3. Contar registros
    print("\n3. Contando registros en productos...")
    try:
        async with get_async_session() as session:
            stmt = select(func.count(Product.id))
            result = await session.execute(stmt)
            count = result.scalar()
            print(f"✓ Total de productos: {count}")
    except Exception as e:
        print(f"✗ Error en count: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ TODOS LOS TESTS PASARON")
    print("=" * 60)
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
