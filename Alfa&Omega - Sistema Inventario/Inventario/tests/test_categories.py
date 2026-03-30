from src.services.categories_service import get_categories_tree, filter_products, attach_attributes_to_product, build_breadcrumbs
from src.database.repository import ensure_schema, insert_product


def test_categories_schema_and_basic():
    ensure_schema()
    # create category and test tree structure via repository directly
    # minimal smoke test: call get_categories_tree() -> should return list
    tree = get_categories_tree()
    assert isinstance(tree, list)


def test_attach_and_filter():
    # insert product
    p = {'codigo':'C001','nombre':'Shoes','categoria':'Footwear','precio':50.0,'cantidad':10,'avg_cost':50.0}
    insert_product(p)
    # attach attr
    attach_attributes_to_product('C001', {'marca':'Nike','color':'Rojo'})
    res = filter_products(None, {'marca':['Nike']}, limit=10)
    assert any(r['codigo']=='C001' for r in res)
