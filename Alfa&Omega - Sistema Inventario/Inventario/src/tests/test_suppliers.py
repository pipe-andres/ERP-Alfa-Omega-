"""Tests for suppliers functionality."""
import sys
from pathlib import Path

# ensure project path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.partners import (
    create_partner, list_partners, get_supplier_history, get_supplier_orders,
    set_partner_active, delete_partner
)
from src.database.connection import get_connection


def test_crear_proveedor():
    """Test creating a new supplier."""
    # Create a test supplier
    supplier_id = create_partner(
        code="SUPP-TEST-001",
        name="Proveedor de Prueba S.A.",
        kind="SUPPLIER",
        tax_id="123456789",
        phone="555-0123",
        email="contacto@proveedor.com",
        address="Calle Principal 123",
        city="Ciudad de Prueba",
        notes="Proveedor de prueba para testing"
    )
    
    assert supplier_id is not None
    assert supplier_id > 0
    
    # Verify supplier was created
    suppliers = list_partners(kind="SUPPLIER", q="Proveedor de Prueba")
    assert len(suppliers) >= 1
    found = next((s for s in suppliers if s["code"] == "SUPP-TEST-001"), None)
    assert found is not None
    assert found["name"] == "Proveedor de Prueba S.A."
    assert found["tax_id"] == "123456789"
    assert found["phone"] == "555-0123"
    assert found["email"] == "contacto@proveedor.com"
    assert found["city"] == "Ciudad de Prueba"
    assert found["active"] is True
    
    # Cleanup
    delete_partner("SUPP-TEST-001", hard=True)


def test_buscar_proveedor():
    """Test searching suppliers by name, phone, and code."""
    # Create test suppliers
    create_partner(
        code="SUPP-SEARCH-001",
        name="Distribuidora ABC",
        kind="SUPPLIER",
        phone="555-1001",
        email="abc@distribuidora.com"
    )
    create_partner(
        code="SUPP-SEARCH-002", 
        name="Importadora XYZ",
        kind="SUPPLIER",
        phone="555-1002",
        email="xyz@importadora.com"
    )
    
    # Search by name
    results = list_partners(kind="SUPPLIER", q="Distribuidora")
    assert len(results) >= 1
    assert any(r["name"] == "Distribuidora ABC" for r in results)
    
    # Search by phone
    results = list_partners(kind="SUPPLIER", q="555-1001")
    assert len(results) >= 1
    assert any(r["phone"] == "555-1001" for r in results)
    
    # Search by code
    results = list_partners(kind="SUPPLIER", q="SUPP-SEARCH-001")
    assert len(results) >= 1
    assert any(r["code"] == "SUPP-SEARCH-001" for r in results)
    
    # Search non-existent
    results = list_partners(kind="SUPPLIER", q="NONEXISTENT")
    # Should not find our test suppliers in this search
    
    # Cleanup
    delete_partner("SUPP-SEARCH-001", hard=True)
    delete_partner("SUPP-SEARCH-002", hard=True)


def test_historial_compras_proveedor():
    """Test getting supplier purchase history."""
    # Create a test supplier
    supplier_id = create_partner(
        code="SUPP-HIST-001",
        name="Proveedor Historial",
        kind="SUPPLIER"
    )
    
    # Get supplier history (should be empty initially)
    history = get_supplier_history(supplier_id)
    assert isinstance(history, list)
    # Initially empty since no purchases exist
    
    # Get supplier orders (should be empty initially)  
    orders = get_supplier_orders(supplier_id)
    assert isinstance(orders, list)
    # Initially empty since no orders exist
    
    # Test with invalid supplier_id
    history_invalid = get_supplier_history(99999)
    assert isinstance(history_invalid, list)
    assert len(history_invalid) == 0
    
    orders_invalid = get_supplier_orders(99999)
    assert isinstance(orders_invalid, list)
    assert len(orders_invalid) == 0
    
    # Cleanup
    delete_partner("SUPP-HIST-001", hard=True)