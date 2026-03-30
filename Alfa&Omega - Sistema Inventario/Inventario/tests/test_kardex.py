from src.database.connection import init_db
from src.services.inventory import post_purchase, post_sale
from src.services.kardex import get_product_kardex


def test_kardex_fifo_basic():
    init_db()
    # purchases
    post_purchase(None, None, [{'codigo':'KPROD','qty':10,'unit_cost':5.0}], notas='p1')
    post_purchase(None, None, [{'codigo':'KPROD','qty':5,'unit_cost':6.0}], notas='p2')
    # sale of 8 units: FIFO consumes from first purchase (10@5)
    # 8 units @ $5 each = $40
    post_sale(None, None, [{'codigo':'KPROD','qty':8,'unit_price':10.0}], notas='s1')
    moves = get_product_kardex('KPROD')
    # find the sale move
    sale_moves = [m for m in moves if m['type'].upper() in ('OUT','SALE')]
    assert sale_moves, "No sale moves found in kardex"
    # total cost for sale should be 8*5 = 40.0 for FIFO (consume from oldest layer first)
    total_cost = sum(m['computed_total_cost'] for m in sale_moves)
    assert abs(total_cost - 40.0) < 1e-6
