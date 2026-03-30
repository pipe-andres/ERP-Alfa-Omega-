from src.services.inventory import add_product, post_purchase, post_sale


def test_post_purchase_and_sale():
    # smoke test: add product and post purchase
    add_product('S001','ItemS','Gen',1.0,1)
    doc_id, num = post_purchase(None, None, [{'codigo':'S001','qty':2,'unit_cost':1.0}], notas='test')
    assert doc_id is not None
    # post sale
    doc_id2, num2, totals = post_sale(None, None, [{'codigo':'S001','qty':1,'unit_price':2.0}], notas='venta test')
    assert doc_id2 is not None
