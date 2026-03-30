"""
Módulo de servicios y lógica de negocio.

Async Functions (FASE 1 - Atomic Transactions):
  - post_purchase_async: Crea compra con transacción atómica
  - post_sale_async: Crea venta con transacción atómica
  - post_adjustment_async: Ajusta inventario con transacción atómica
  - transfer_stock_async: Transfiere stock entre almacenes con transacción atómica

Legacy Sync Functions (deprecated, será eliminado en FASE 2):
  - inventory.post_purchase, post_sale, post_adjustment
  - transfers.transfer_stock
"""

from .inventory_async import (
    post_purchase_async,
    post_sale_async,
    post_adjustment_async,
)
from .transfers_async import transfer_stock_async

# Legacy sync imports (for backward compatibility during transition)
# These will be marked as deprecated in FASE 2
try:
    from .inventory import post_purchase, post_sale, post_adjustment
    from .transfers import transfer_stock
except ImportError:
    # If sync versions don't exist yet, that's ok
    pass

__all__ = [
    # Async (recommended)
    'post_purchase_async',
    'post_sale_async',
    'post_adjustment_async',
    'transfer_stock_async',
    # Legacy sync (deprecated)
    'post_purchase',
    'post_sale',
    'post_adjustment',
    'transfer_stock',
]
