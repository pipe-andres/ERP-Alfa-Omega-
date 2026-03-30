# Database

## File
src/data/inventario.db (SQLite) — ÚNICA BD válida del sistema

## Schema

### Core Business
productos(id,codigo UNIQUE,nombre,categoria,precio,cantidad,avg_cost,active)
partners(id,code UNIQUE,kind CHECK('CUSTOMER','SUPPLIER'),name,tax_id,
  phone,email,address,city,notes,active,credit_limit,credit_balance)
documents(id,tipo,numero,fecha,partner_id→partners,notas,estado,payment_method)
document_lines(id,doc_id→documents,codigo,qty,unit_price)
kardex_moves(id,producto_id→productos,tipo,qty,costo,fecha,doc_id)

### Cash
cash_sessions(id,opened_by,opening_amount,opened_at,closed_at,
  closing_amount,arqueo_declared,arqueo_notes)
cash_movements(id,session_id→cash_sessions,type,amount,description,created_at)

### Returns
returns(id,sale_id,document_id→documents,reason,total_refund,
  created_by,created_at,status)
return_lines(id,return_id→returns,product_id→productos,quantity,unit_cost,subtotal)

### Auth
users(id,username UNIQUE,password_hash,role_id→roles,active)
roles(id,name UNIQUE) — ADMIN|USER|AUDITOR
permissions(id,name UNIQUE)
role_permissions(role_id,permission_id)
user_roles(user_id,role_id)
audit_log(id,fecha,usuario,accion,detalles)

## Document Types (documents.tipo)
SALE → venta POS
PURCHASE → compra a proveedor
PURCHASE_ORDER → orden de compra (estados: PENDIENTE|PARCIAL|RECIBIDA|CANCELADA)
CREDIT_NOTE → nota de crédito por devolución

## Key Relations
document_lines.doc_id → documents.id
kardex_moves.doc_id → documents.id
documents.partner_id → partners.id