from src.database.connection import get_connection, init_db
from src.services.inventory import add_product, get_product, list_products_page


def test_add_and_get_product():
    init_db()
    add_product('P001','Test Product','CatA',10.5,5)
    row = get_product('P001')
    assert row is not None
    assert row[0] == 'P001'


def test_list_products():
    # make this test independent: create both products within the test
    from src.database.connection import init_db
    init_db()
    add_product('P001','Test Product','CatA',10.5,5)
    add_product('P002','Other','CatB',5.0,2)
    rows = list_products_page(page=1, page_size=10)
    codes = {r[0] for r in rows}
    assert 'P001' in codes
    assert 'P002' in codes


def test_refresh_consistency():
    """Simula el caso de UI que provocaba empty state falso.
    Después de limpiar caché, count_products y list_products_page deben
    coincidir y no ser cero si existe un producto."""
    from src.database.connection import init_db
    from src.services.inventory import count_products
    from src.core import caching

    init_db()
    add_product('T001', 'Foo', 'CatZ', 1.0, 1)
    # forzar limpieza de caches como lo hace el servicio
    caching.clear_cache("src.database.repository.list_products")
    caching.clear_cache("src.database.repository.count_products")

    ct = count_products()
    rows = list_products_page(page=1, page_size=10)
    assert ct > 0
    assert len(rows) == ct


def test_reactivate_inactive_code():
    """Si un producto con código existe pero está inactivo, un nuevo add lo reactiva."""
    from src.database.connection import init_db
    from src.database import repository
    from src.core import caching

    init_db()
    # crear inicialmente y desactivar
    add_product('Z001', 'Zap', 'CatX', 2.0, 5)
    # desactivar directamente usando servicio delete (mantiene activo=0)
    delete_product('Z001')
    # ahora debería existir como inactivo en repo
    row = repository.get_product_by_code('Z001')
    assert row is not None
    # borrar cache
    caching.clear_cache("src.database.repository.list_products")
    caching.clear_cache("src.database.repository.count_products")
    # intentar agregar de nuevo con mismo código
    add_product('Z001', 'Zap new', 'CatY', 3.0, 10)
    # se reactivó: count_products debe ser 1 y producto activo con nuevos datos
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT nombre, categoria, precio, cantidad, activo FROM productos WHERE codigo='Z001'")
        updated = cur.fetchone()
    assert updated[0] == 'Zap new'
    assert updated[1] == 'CatY'
    assert updated[2] == 3.0
    assert updated[3] == 10
    assert updated[4] == 1


def test_add_resets_filter():
    """Crear producto mientras hay filtro no debe ocultarlo."""
    from src.database.connection import init_db
    from src.services.inventory import count_products
    from src.core import caching

    init_db()
    # start with a couple items
    add_product('A1', 'Alpha', 'Cat', 1, 1)
    add_product('B2', 'Beta', 'Cat', 1, 1)
    # simulate filter by name 'Alpha' (manually count)
    cnt_filtered = count_products('Nombre', 'Alpha')
    assert cnt_filtered == 1
    # now add a product that doesn't match filter
    add_product('C3', 'Gamma', 'Cat', 1, 1)
    # after creation, global count should be 3
    assert count_products() == 3
    # filtered count remains 1 but UI would reset caches and filters
    # we don't test UI here; test that table query without filter returns all
    rows = list_products_page(page=1, page_size=10)
    assert len(rows) == 3
