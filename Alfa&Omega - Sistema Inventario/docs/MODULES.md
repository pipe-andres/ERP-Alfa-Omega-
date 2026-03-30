# Modules

## POS
Files: src/pos/pos_window.py
Service: inventory.post_sale()
Tables: documents(SALE), document_lines, kardex_moves, cash_movements
Keys: F10=caja, F11=devolución, F12=cobrar
Status: ✅ completo

## CRM
Files: src/app/crm_window.py
Service: partners.py (kind=CUSTOMER)
Tables: partners(CUSTOMER)
Tabs: Clientes|Detalle+historial|Crédito
Status: ✅ completo

## Suppliers
Files: src/app/suppliers_window.py
Service: partners.py (kind=SUPPLIER)
Tables: partners(SUPPLIER), documents(PURCHASE)
Tabs: Proveedores|Detalle|Órdenes
Status: ✅ completo

## Purchase Orders
Files: src/app/purchase_orders_window.py
Service: purchase_orders.py
Tables: documents(PURCHASE_ORDER), document_lines
Tabs: Órdenes|Nueva OC|Recepción
Status: ✅ completo

## Cash Management
Files: src/app/cash_manager_window.py
Service: pos_service.py
Tables: cash_sessions, cash_movements
Tabs: Control|Historial
Status: ✅ completo

## Returns
Files: src/app/returns_window.py
Service: returns_service.py
Tables: returns, return_lines, documents(CREDIT_NOTE)
Status: ✅ completo

## Reports
Files: src/app/reports_window.py
Service: reports.py
Functions: kardex_rows, report_sales_by_period, report_abc_analysis,
  report_top_products, report_inventory_rotation
Tabs: P&L|ABC|Márgenes|Rotación
Status: ✅ completo

## Inventory
Files: src/app/main_window.py (tab inventario)
Service: inventory.py
Tables: productos, kardex_moves, documents
Status: ✅ completo