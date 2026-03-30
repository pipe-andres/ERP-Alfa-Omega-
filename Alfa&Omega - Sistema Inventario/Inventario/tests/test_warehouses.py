from src.database.connection import init_db
from src.services.warehouses import create_warehouse, set_stock, get_stock, list_warehouses
from src.services.inventory import add_product


def test_create_warehouse_and_set_stock():
    init_db()
    # create product and warehouse
    add_product('WPROD','ProdW','CatW',10.0,0)
    wid = create_warehouse('Main','Local A')
    set_stock('WPROD', wid, 15)
    assert get_stock('WPROD', wid) == 15
    assert get_stock('WPROD') >= 15
    ws = list_warehouses()
    assert any(w['id'] == wid for w in ws)
