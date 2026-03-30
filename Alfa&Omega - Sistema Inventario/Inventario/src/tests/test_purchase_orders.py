"""Tests for purchase orders functionality."""
import sys
from pathlib import Path

# ensure project path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.purchase_orders import (
    create_purchase_order, get_purchase_order, list_purchase_orders,
    receive_order, cancel_order
)
from src.services.partners import create_partner
from src.database.connection import get_connection

_TEST_PARTNER_CODES = [
    "SUPP-PO-TEST", "SUPP-LIST-TEST", "SUPP-RECV-TEST", "SUPP-CANCEL-TEST"
]

def setup_module(module):
    """Limpia y crea datos de test para evitar UNIQUE collision y FOREIGN KEY errors."""
    from src.database.connection import init_db
    init_db()  # garantiza esquema
    with get_connection() as conn:
        cur = conn.cursor()
        # Limpiar partners de test
        for code in _TEST_PARTNER_CODES:
            try:
                cur.execute("DELETE FROM partners WHERE code=?", (code,))
            except Exception:
                pass
        # Crear productos de test si no existen (necesarios para FOREIGN KEY en document_lines)
        for codigo in ("TEST001", "TEST002"):
            cur.execute("""
                INSERT INTO productos (codigo, nombre, categoria, precio, cantidad, avg_cost, activo)
                VALUES (?, ?, 'TEST', 0, 0, 0, 1)
                ON CONFLICT(codigo) DO NOTHING
            """, (codigo, f"Producto {codigo}"))
        conn.commit()


def test_crear_orden_compra():
    """Test creating a new purchase order."""
    # Create a test supplier
    supplier_id = create_partner(
        code="SUPP-PO-TEST",
        name="Proveedor para OC",
        kind="SUPPLIER"
    )

    # Create purchase order
    items = [
        {"codigo": "TEST001", "qty": 10, "unit_price": 5.50},
        {"codigo": "TEST002", "qty": 5, "unit_price": 12.00}
    ]

    doc_id, numero = create_purchase_order(
        supplier_code="SUPP-PO-TEST",
        items=items,
        notas="Orden de prueba"
    )

    assert doc_id is not None
    assert numero.startswith("OC-")

    # Verify order was created
    order = get_purchase_order(doc_id)
    assert order is not None
    assert order["numero"] == numero
    assert order["supplier_code"] == "SUPP-PO-TEST"
    assert order["estado"] == "PENDIENTE"
    assert len(order["items"]) == 2

    # Verify items
    item_codes = [item["codigo"] for item in order["items"]]
    assert "TEST001" in item_codes
    assert "TEST002" in item_codes

    # Cleanup - cancel order and delete supplier
    cancel_order(doc_id)
    # Note: supplier deletion would require removing references first


def test_listar_ordenes_compra():
    """Test listing purchase orders with filters."""
    # Create test supplier
    create_partner(
        code="SUPP-LIST-TEST",
        name="Proveedor para Listado",
        kind="SUPPLIER"
    )

    # Create some orders
    items1 = [{"codigo": "TEST001", "qty": 5, "unit_price": 10.0}]
    doc_id1, _ = create_purchase_order("SUPP-LIST-TEST", items1)

    items2 = [{"codigo": "TEST002", "qty": 3, "unit_price": 15.0}]
    doc_id2, _ = create_purchase_order("SUPP-LIST-TEST", items2)

    # List all orders
    orders = list_purchase_orders()
    assert len(orders) >= 2

    # List by supplier
    supplier_orders = list_purchase_orders(supplier_code="SUPP-LIST-TEST")
    assert len(supplier_orders) >= 2

    # List by status
    pending_orders = list_purchase_orders(estado="PENDIENTE")
    assert len(pending_orders) >= 2

    # Cleanup
    cancel_order(doc_id1)
    cancel_order(doc_id2)


def test_recibir_orden_compra():
    """Test receiving a purchase order in full."""
    # Create supplier
    create_partner(
        code="SUPP-RECV-TEST",
        name="Proveedor para Recepción",
        kind="SUPPLIER"
    )

    # Create order with 10 units
    items = [{"codigo": "TEST001", "qty": 10, "unit_price": 8.0}]
    doc_id, numero = create_purchase_order("SUPP-RECV-TEST", items)

    # Receive ALL 10 in one call → should flip to RECIBIDA
    # (service does not track cumulative receives across calls)
    items_received = [{"codigo": "TEST001", "qty_received": 10}]
    receive_order(doc_id, items_received)

    order = get_purchase_order(doc_id)
    assert order["estado"] == "RECIBIDA"


def test_cancelar_orden_compra():
    """Test canceling a purchase order."""
    # Create supplier
    create_partner(
        code="SUPP-CANCEL-TEST",
        name="Proveedor para Cancelación",
        kind="SUPPLIER"
    )

    # Create order
    items = [{"codigo": "TEST001", "qty": 5, "unit_price": 20.0}]
    doc_id, numero = create_purchase_order("SUPP-CANCEL-TEST", items)

    # Verify initial status
    order = get_purchase_order(doc_id)
    assert order["estado"] == "PENDIENTE"

    # Cancel order
    cancel_order(doc_id)

    # Verify status changed
    order = get_purchase_order(doc_id)
    assert order["estado"] == "CANCELADA"


def test_validaciones_orden_compra():
    """Test purchase order validations."""
    # Test with invalid supplier
    try:
        create_purchase_order("INVALID-SUPPLIER", [{"codigo": "TEST001", "qty": 1, "unit_price": 10.0}])
        assert False, "Should have raised ValueError for invalid supplier"
    except ValueError:
        pass  # Expected

    # Test with empty items
    try:
        create_purchase_order("SUPP-PO-TEST", [])
        assert False, "Should have raised ValueError for empty items"
    except ValueError:
        pass  # Expected

    # Test with invalid qty
    try:
        create_purchase_order("SUPP-PO-TEST", [{"codigo": "TEST001", "qty": 0, "unit_price": 10.0}])
        assert False, "Should have raised ValueError for qty <= 0"
    except ValueError:
        pass  # Expected