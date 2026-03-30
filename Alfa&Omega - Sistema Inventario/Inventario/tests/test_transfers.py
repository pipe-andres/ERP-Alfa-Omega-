from src.database.connection import init_db
from src.services.warehouses import create_warehouse, set_stock, get_stock
from src.services.transfers import transfer_stock
from src.services.inventory import add_product


def test_transfer_between_warehouses():
    init_db()
    add_product('TPROD','ProdT','CatT',5.0,0)
    w1 = create_warehouse('W1','A')
    w2 = create_warehouse('W2','B')
    set_stock('TPROD', w1, 20)
    set_stock('TPROD', w2, 5)
    transfer_id = transfer_stock('TPROD', w1, w2, 7, user_id=None, notes='test transfer')
    assert isinstance(transfer_id, int)
    assert get_stock('TPROD', w1) == 13
    assert get_stock('TPROD', w2) == 12
