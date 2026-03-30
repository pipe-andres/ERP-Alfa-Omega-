from src.database.connection import init_db
from src.services.inventory import post_purchase, post_sale
from src.services.kardex import get_product_kardex

print('init_db')
init_db()
print('posting purchase 1')
post_purchase(None, None, [{'codigo':'KPROD','qty':10,'unit_cost':5.0}], notas='p1')
print('posting purchase 2')
post_purchase(None, None, [{'codigo':'KPROD','qty':5,'unit_cost':6.0}], notas='p2')
print('posting sale')
post_sale(None, None, [{'codigo':'KPROD','qty':8,'unit_price':10.0}], notas='s1')
print('getting kardex')
moves = get_product_kardex('KPROD')
print('kardex len', len(moves))
for m in moves:
    print(m['type'], m.get('qty'), m.get('computed_total_cost'))
