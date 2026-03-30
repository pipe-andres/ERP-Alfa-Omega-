# src/services/inventory_safe.py
"""
Wrapper seguro para operaciones de inventario.
Implementa:
- Error handling robusto (sin silent failures)
- Transacciones ACID correctas
- Validación exhaustiva
- Auditoría de todos los errores
- Logging estructurado
"""

import logging
from typing import Optional, Tuple, List
from src.core.error_handler import (
    log_error, safe_execute, AlfaOmegaException, DataIntegrityException
)
from src.database.connection import get_connection
from src.services.audit import log_event

logger = logging.getLogger("AlfaOmega.Inventory")


def add_product_safe(
    codigo: str,
    nombre: str,
    categoria: str = "",
    precio: float = 0.0,
    cantidad: int = 0,
    user_id: Optional[int] = None
) -> bool:
    """
    Agrega producto de forma segura.
    
    Args:
        codigo: Código único de producto
        nombre: Nombre del producto
        categoria: Categoría
        precio: Precio unitario
        cantidad: Cantidad inicial
        user_id: ID del usuario que crea (para auditoría)
    
    Returns:
        True si se agregó exitosamente
    
    Raises:
        ValueError: Si hay error de validación
        DataIntegrityException: Si hay error de base de datos
    """
    # VALIDACIÓN EXHAUSTIVA
    if not codigo or not nombre:
        raise ValueError("Código y Nombre son obligatorios.")
    
    codigo = codigo.strip()
    nombre = nombre.strip()
    
    if not codigo or not nombre:
        raise ValueError("Código y Nombre no pueden estar vacíos.")
    
    # Validar longitudes
    if len(codigo) > 50:
        raise ValueError("Código no puede exceder 50 caracteres.")
    if len(nombre) > 255:
        raise ValueError("Nombre no puede exceder 255 caracteres.")
    
    # Validar números
    try:
        precio = float(precio)
        cantidad = int(cantidad)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Valores numéricos inválidos: {e}") from e
    
    if precio < 0:
        raise ValueError("El precio no puede ser negativo.")
    if cantidad < 0:
        raise ValueError("La cantidad no puede ser negativa.")
    
    # OPERACIÓN DE BD CON TRANSACCIÓN CORRECTA
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # Verificar duplicado DENTRO de la transacción
            cur.execute("SELECT id FROM productos WHERE codigo = ?", (codigo,))
            if cur.fetchone():
                raise ValueError(f"El código '{codigo}' ya existe.")
            
            # Insertar
            cur.execute("""
                INSERT INTO productos (codigo, nombre, categoria, precio, cantidad, avg_cost)
                VALUES (?,?,?,?,?,?)
            """, (codigo, nombre, (categoria or "").strip(), precio, cantidad, precio))
            
            # Commit explícito
            conn.commit()
            
            # AUDITORÍA
            if user_id:
                try:
                    log_event(user_id, "PRODUCT_CREATE", {
                        "codigo": codigo,
                        "nombre": nombre,
                        "precio": precio,
                        "cantidad": cantidad
                    })
                except Exception as e:
                    logger.warning(f"No se pudo registrar auditoría: {e}")
            
            logger.info(f"✓ Producto creado: {codigo} - {nombre}")
            return True
    
    except ValueError:
        # Re-lanzar errores de validación
        raise
    except Exception as e:
        # Error de BD - CRÍTICO
        log_error(e, context={
            "operation": "add_product",
            "codigo": codigo,
            "user_id": user_id
        }, level="ERROR")
        
        raise DataIntegrityException(
            f"Error al crear producto: {str(e)}"
        ) from e


def update_product_safe(
    codigo: str,
    nombre: Optional[str] = None,
    categoria: Optional[str] = None,
    precio: Optional[float] = None,
    cantidad: Optional[int] = None,
    user_id: Optional[int] = None
) -> bool:
    """
    Actualiza producto de forma segura.
    
    Returns:
        True si se actualizó algo, False si no había qué actualizar
    
    Raises:
        ValueError: Error de validación
        DataIntegrityException: Error de BD
    """
    # Validar que producto existe
    if not codigo or not codigo.strip():
        raise ValueError("Código es obligatorio.")
    
    codigo = codigo.strip()
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # Verificar que existe
            cur.execute("SELECT id FROM productos WHERE codigo = ?", (codigo,))
            if not cur.fetchone():
                raise ValueError(f"Producto con código '{codigo}' no existe.")
            
            # Construir actualización dinámica
            updates = []
            params = []
            
            if nombre is not None:
                nombre = nombre.strip()
                if not nombre:
                    raise ValueError("El nombre no puede estar vacío.")
                if len(nombre) > 255:
                    raise ValueError("Nombre no puede exceder 255 caracteres.")
                updates.append("nombre=?")
                params.append(nombre)
            
            if categoria is not None:
                category_clean = (categoria or "").strip()
                if len(category_clean) > 100:
                    raise ValueError("Categoría no puede exceder 100 caracteres.")
                updates.append("categoria=?")
                params.append(category_clean)
            
            if precio is not None:
                try:
                    precio = float(precio)
                except (ValueError, TypeError):
                    raise ValueError("Precio debe ser un número válido.")
                if precio < 0:
                    raise ValueError("El precio no puede ser negativo.")
                updates.append("precio=?")
                params.append(precio)
            
            if cantidad is not None:
                try:
                    cantidad = int(cantidad)
                except (ValueError, TypeError):
                    raise ValueError("Cantidad debe ser un número entero.")
                if cantidad < 0:
                    raise ValueError("La cantidad no puede ser negativa.")
                updates.append("cantidad=?")
                params.append(cantidad)
            
            if not updates:
                logger.info(f"Nada que actualizar para: {codigo}")
                return False
            
            # Ejecutar UPDATE
            sql = f"UPDATE productos SET {', '.join(updates)} WHERE codigo = ?"
            params.append(codigo)
            cur.execute(sql, params)
            conn.commit()
            
            # AUDITORÍA
            if user_id:
                try:
                    log_event(user_id, "PRODUCT_UPDATE", {
                        "codigo": codigo,
                        "cambios": {k: v for k, v in zip(
                            ["nombre", "categoria", "precio", "cantidad"],
                            [nombre, categoria, precio, cantidad]
                        ) if v is not None}
                    })
                except Exception as e:
                    logger.warning(f"No se pudo registrar auditoría: {e}")
            
            logger.info(f"✓ Producto actualizado: {codigo}")
            return True
    
    except ValueError:
        raise
    except Exception as e:
        log_error(e, context={
            "operation": "update_product",
            "codigo": codigo,
            "user_id": user_id
        }, level="ERROR")
        raise DataIntegrityException(f"Error al actualizar: {str(e)}") from e


def delete_product_safe(codigo: str, user_id: Optional[int] = None) -> bool:
    """
    Elimina producto de forma segura.
    
    Returns:
        True si se eliminó
    
    Raises:
        ValueError: Error de validación
        DataIntegrityException: Error de BD
    """
    if not codigo or not codigo.strip():
        raise ValueError("Código es obligatorio.")
    
    codigo = codigo.strip()
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # Verificar existencia
            cur.execute("SELECT id, nombre FROM productos WHERE codigo = ?", (codigo,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Producto '{codigo}' no existe.")
            
            product_name = row[1]
            
            # Verificar que no haya movimientos asociados (dependencias)
            cur.execute("""
                SELECT COUNT(*) FROM movimientos 
                WHERE codigo_producto = ?
            """, (codigo,))
            mov_count = cur.fetchone()[0]
            
            if mov_count > 0:
                logger.warning(f"Intento de eliminar producto con {mov_count} movimientos: {codigo}")
                raise ValueError(
                    f"No se puede eliminar: hay {mov_count} movimientos asociados. "
                    "Intenta marcar como inactivo en su lugar."
                )
            
            # Eliminar
            cur.execute("DELETE FROM productos WHERE codigo = ?", (codigo,))
            conn.commit()
            
            # AUDITORÍA
            if user_id:
                try:
                    log_event(user_id, "PRODUCT_DELETE", {
                        "codigo": codigo,
                        "nombre": product_name
                    })
                except Exception as e:
                    logger.warning(f"No se pudo registrar auditoría: {e}")
            
            logger.info(f"✓ Producto eliminado: {codigo}")
            return True
    
    except ValueError:
        raise
    except Exception as e:
        log_error(e, context={
            "operation": "delete_product",
            "codigo": codigo,
            "user_id": user_id
        }, level="ERROR")
        raise DataIntegrityException(f"Error al eliminar: {str(e)}") from e
