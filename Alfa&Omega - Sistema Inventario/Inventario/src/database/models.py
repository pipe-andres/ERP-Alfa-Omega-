"""Declarative ORM models equivalentes a las tablas existentes.

Estas clases buscan reflejar las tablas actualmente creadas por
`src.database.connection.init_db()` y por `src.database.repository.ensure_schema()`.
Al crear las migraciones Alembic usaremos `Base.metadata` para autogenerate.
"""
from __future__ import annotations
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = 'productos'
    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    categoria = Column(String)
    precio = Column(Float, nullable=False, default=0.0)
    cantidad = Column(Integer, nullable=False, default=0)
    avg_cost = Column(Float, nullable=False, default=0.0)

class Partner(Base):
    __tablename__ = 'partners'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    kind = Column(String, nullable=False)
    name = Column(String, nullable=False)
    tax_id = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)
    city = Column(String)
    notes = Column(Text)
    active = Column(Boolean, default=True, nullable=False)

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    tipo = Column(String, nullable=False)
    numero = Column(String)
    fecha = Column(String, nullable=False)
    notas = Column(Text)
    partner_id = Column(Integer, ForeignKey('partners.id', ondelete='SET NULL'))
    partner = relationship('Partner')

class DocumentLine(Base):
    __tablename__ = 'document_lines'
    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    codigo = Column(String, ForeignKey('productos.codigo', ondelete='RESTRICT'), nullable=False)
    qty = Column(Float, nullable=False)
    unit_cost = Column(Float)
    unit_price = Column(Float)
    reason = Column(Text)

class StockMovement(Base):
    __tablename__ = 'stock_movements'
    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, ForeignKey('documents.id', ondelete='SET NULL'))
    codigo = Column(String, ForeignKey('productos.codigo', ondelete='RESTRICT'), nullable=False)
    qty = Column(Float, nullable=False)
    unit_cost = Column(Float)
    unit_price = Column(Float)
    tipo = Column(String, nullable=False)
    reason = Column(Text)
    created_at = Column(String, nullable=False)

class DocSeries(Base):
    __tablename__ = 'doc_series'
    id = Column(Integer, primary_key=True)
    doc_type = Column(String, nullable=False)
    series = Column(String, nullable=False)
    prefix = Column(String)
    next_no = Column(Integer, nullable=False, default=1)
    __table_args__ = (UniqueConstraint('doc_type', 'series', name='uq_doc_series_type_series'),)

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('categories.id'))
    name = Column(String, nullable=False, unique=True)
    slug = Column(String)

class CategoryAttribute(Base):
    __tablename__ = 'category_attributes'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    attr_name = Column(String, nullable=False)
    attr_type = Column(String, default='text')
    attr_options = Column(Text)

class ProductAttribute(Base):
    __tablename__ = 'product_attributes'
    id = Column(Integer, primary_key=True)
    product_code = Column(String, nullable=False)
    attr_name = Column(String, nullable=False)
    attr_value = Column(String)

# RBAC
class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(Text)

class RolePermission(Base):
    __tablename__ = 'role_permissions'
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    permission_id = Column(Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)

class UserRole(Base):
    __tablename__ = 'user_roles'
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    pass_hash = Column(String, nullable=False)
    active = Column(Integer, nullable=False, default=1)

class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    details = Column(Text)
    created_at = Column(String, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

# Warehouses
class Warehouse(Base):
    __tablename__ = 'warehouses'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    location = Column(String)

class WarehouseStock(Base):
    __tablename__ = 'warehouse_stock'
    id = Column(Integer, primary_key=True)
    product_code = Column(String, ForeignKey('productos.codigo', ondelete='RESTRICT'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)

class WarehouseTransfer(Base):
    __tablename__ = 'warehouse_transfers'
    id = Column(Integer, primary_key=True)
    product_code = Column(String, ForeignKey('productos.codigo'), nullable=False)
    from_wh = Column(Integer)
    to_wh = Column(Integer)
    quantity = Column(Float, nullable=False)
    date = Column(String, nullable=False)
    user_id = Column(Integer)
    notes = Column(Text)

class KardexMove(Base):
    __tablename__ = 'kardex_moves'
    id = Column(Integer, primary_key=True)
    product_code = Column(String, ForeignKey('productos.codigo'), nullable=False)
    type = Column(String, nullable=False)
    qty = Column(Float, nullable=False)
    unit_cost = Column(Float)
    total_cost = Column(Float)
    balance_qty = Column(Float)
    balance_cost = Column(Float)
    balance_total = Column(Float)
    date = Column(String, nullable=False)
    warehouse_id = Column(Integer)
    ref_type = Column(String)
    ref_id = Column(Integer)

# ----------------------
# Devoluciones (returns)
# ----------------------
class Return(Base):
    __tablename__ = 'returns'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    reason = Column(Text)
    total_refund = Column(Float, nullable=False)
    created_by = Column(Integer)
    created_at = Column(String, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    status = Column(String, nullable=False, default='active')

class ReturnLine(Base):
    __tablename__ = 'return_lines'
    id = Column(Integer, primary_key=True)
    return_id = Column(Integer, ForeignKey('returns.id', ondelete='CASCADE'), nullable=False)
    product_code = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit_cost = Column(Float)
    subtotal = Column(Float)
