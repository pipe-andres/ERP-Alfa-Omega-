import pytest

from src.services.inventory import add_product, post_purchase, post_sale, get_product
from src.services.returns_service import post_return, get_return_by_sale, list_returns


def test_returns_workflow():
    # preparar producto y stock inicial
    add_product('RT1', 'Retorno', 'General', 5.0, 0)
    # comprar 10 unidades para poder vender
    post_purchase(None, None, [{'codigo': 'RT1', 'qty': 10, 'unit_cost': 5.0}])

    # realizar una venta de 3 unidades
    sale_id, sale_num, _ = post_sale(None, None, [{'codigo': 'RT1', 'qty': 3, 'unit_price': 8.0}])
    assert sale_id is not None

    # intentar devolver sin items falla
    with pytest.raises(ValueError):
        post_return(sale_id, [], "sin productos")

    # devolver más de lo vendido falla
    with pytest.raises(ValueError):
        post_return(sale_id, [{'codigo': 'RT1', 'qty': 4}], "exceso")

    # hacer devolución parcial válida
    ret_id, cred_id = post_return(sale_id, [{'codigo': 'RT1', 'qty': 2}], "parcial", user_id=1)
    assert ret_id is not None
    assert cred_id is not None

    # stock debe haberse incrementado en 2 (10-3+2 = 9)
    prod = get_product('RT1')
    assert prod[4] == 9

    # get_return_by_sale debe devolver la primera devolución registrada
    info = get_return_by_sale(sale_id)
    assert info and info['id'] == ret_id
    assert info['total_refund'] > 0

    # intentar devolver de nuevo 2 unidades (solo queda 1 permitido) produce error
    with pytest.raises(ValueError):
        post_return(sale_id, [{'codigo': 'RT1', 'qty': 2}], "otra")

    # devolver el resto con monto exacto debe funcionar
    ret_id2, cred_id2 = post_return(sale_id, [{'codigo': 'RT1', 'qty': 1}], "completando", user_id=1)
    assert ret_id2 is not None

    # ahora debe haber exactamente dos devoluciones asociadas a esa venta
    all_ret = [r for r in list_returns() if r['sale_id'] == sale_id]
    assert len(all_ret) == 2

    # stock final: 10-3+3 = 10
    prod = get_product('RT1')
    assert prod[4] == 10


def test_return_with_multiple_items_and_filters():
    # nuevo producto
    add_product('RT2', 'Otro', 'G', 2.0, 0)
    post_purchase(None, None, [{'codigo': 'RT2', 'qty': 5, 'unit_cost': 2.0}])
    sale2, _, _ = post_sale(None, None, [{'codigo': 'RT2', 'qty': 5, 'unit_price': 3.0}])
    # devolver todo
    post_return(sale2, [{'codigo': 'RT2', 'qty': 5}], "completa", user_id=7)
    # filtrar devoluciones por usuario
    by_user = [r for r in list_returns({'user_id': 7}) if r['sale_id'] == sale2]
    assert len(by_user) == 1
    # filtrar por producto
    by_prod = [r for r in list_returns({'product_code': 'RT2'}) if r['sale_id'] == sale2]
    assert len(by_prod) == 1
